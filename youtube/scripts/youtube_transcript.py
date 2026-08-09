#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any, Literal
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


SCHEMA_VERSION = "1.0"
SUBTITLE_FORMAT = "json3"
ACCEPTED_MANUAL_LANGUAGES = {"en", "fr"}
HTTP_TIMEOUT_SECONDS = 20


class TranscriptError(RuntimeError):
    """Erreur pendant l'extraction d'une vidéo ou de ses sous-titres."""


@dataclass(frozen=True)
class SubtitleTrack:
    """
    Piste de sous-titres sélectionnée.

    `language` est le code normalisé, par exemple "en".
    `youtube_language_code` conserve le code renvoyé par YouTube,
    par exemple "en-orig".
    """

    language: str
    youtube_language_code: str
    source: Literal["manual", "automatic"]
    subtitle_format: str
    url: str
    http_headers: dict[str, str]


@dataclass(frozen=True)
class TranscriptSegment:
    start_ms: int
    end_ms: int | None
    text: str


@dataclass(frozen=True)
class Chapter:
    title: str
    start_seconds: float
    end_seconds: float | None


def get_youtube_data(
    video_url: str,
    *,
    include_segments: bool = False,
    include_description: bool = False,
    include_tags: bool = False,
    include_public_statistics: bool = False,
) -> dict[str, Any]:
    """
    Extrait les informations utiles d'une vidéo YouTube.

    Règles de sélection des sous-titres :

    1. S'il existe exactement une piste manuelle et qu'elle est en français
       ou en anglais, cette piste est sélectionnée.
    2. Dans tous les autres cas, la piste automatique dont le code se termine
       par "-orig" est sélectionnée.

    Args:
        video_url:
            URL d'une vidéo YouTube.

        include_segments:
            Ajoute les segments horodatés du transcript.

        include_description:
            Ajoute la description complète de la vidéo.

        include_tags:
            Ajoute les tags YouTube.

        include_public_statistics:
            Ajoute les statistiques publiques disponibles :
            vues, likes et commentaires.

    Returns:
        Dictionnaire sérialisable en JSON.

    Raises:
        TranscriptError:
            Si la vidéo n'est pas accessible, si aucun sous-titre compatible
            n'est disponible ou si les données reçues sont invalides.
    """
    info = extract_video_info(video_url)
    track = select_subtitle_track(info)
    subtitle_json = download_subtitle_json(track)

    segments = extract_subtitle_segments(subtitle_json)

    if not segments:
        raise TranscriptError(
            "La piste de sous-titres sélectionnée ne contient aucun texte."
        )

    transcript_text = build_continuous_transcript(segments)
    chapters = extract_chapters(info)

    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "video": build_video_metadata(
            info,
            requested_url=video_url,
            include_description=include_description,
            include_tags=include_tags,
            include_public_statistics=include_public_statistics,
        ),
        "transcript": {
            "text": transcript_text,
            "language": track.language,
            "youtube_language_code": track.youtube_language_code,
            "source": track.source,
            "subtitle_format": track.subtitle_format,
            "normalized": True,
        },
        "chapters": [asdict(chapter) for chapter in chapters],
        "statistics": {
            "character_count": len(transcript_text),
            "word_count": count_words(transcript_text),
            "segment_count": len(segments),
            "chapter_count": len(chapters),
        },
    }

    if include_segments:
        result["transcript"]["segments"] = [
            asdict(segment) for segment in segments
        ]

    return result


def find_yt_dlp() -> str:
    """
    Retourne le chemin de yt-dlp.

    Ordre de recherche :
    1. binaire embarqué à côté de ce script ;
    2. exécutable disponible dans le PATH.

    Le binaire local permet notamment d'éviter les restrictions de certains
    environnements sandboxés sur les répertoires d'installation système.
    """
    script_dir = Path(__file__).resolve().parent

    local_candidates = (
        script_dir / "yt-dlp.exe",
        script_dir / "yt-dlp",
    )

    for candidate in local_candidates:
        if candidate.is_file():
            if os.name != "nt" and not os.access(candidate, os.X_OK):
                raise TranscriptError(
                    f"Le binaire yt-dlp local n'est pas exécutable : {candidate}"
                )

            return str(candidate)

    executable = shutil.which("yt-dlp")

    if executable is None:
        expected_names = "yt-dlp.exe ou yt-dlp"
        raise TranscriptError(
            "yt-dlp est requis mais aucun binaire local "
            f"({expected_names}) n'a été trouvé à côté du script et aucun "
            "exécutable 'yt-dlp' n'est disponible dans le PATH."
        )

    return executable



def create_process_temp_directory() -> tempfile.TemporaryDirectory[str]:
    """
    Crée un répertoire temporaire inscriptible pour les sous-processus.

    Le répertoire courant est essayé en priorité, car les environnements
    sandboxés accordent généralement l'écriture dans leur espace de travail.
    Si ce répertoire n'est pas utilisable, on utilise le répertoire temporaire
    système.
    """
    current_directory = Path.cwd()

    try:
        if current_directory.is_dir() and os.access(current_directory, os.W_OK):
            return tempfile.TemporaryDirectory(
                prefix=".youtube-transcript-",
                dir=current_directory,
            )
    except OSError:
        pass

    try:
        return tempfile.TemporaryDirectory(prefix="youtube-transcript-")
    except OSError as exc:
        raise TranscriptError(
            "Impossible de créer un répertoire temporaire pour yt-dlp : "
            f"{exc}"
        ) from exc


def build_subprocess_environment(temp_dir: str) -> dict[str, str]:
    """
    Construit l'environnement du sous-processus yt-dlp.

    Seul le sous-processus reçoit le répertoire temporaire dédié ; les
    variables d'environnement du processus Python et de la session parente
    ne sont pas modifiées.
    """
    environment = os.environ.copy()

    if os.name == "nt":
        environment["TEMP"] = temp_dir
        environment["TMP"] = temp_dir
    else:
        environment["TMPDIR"] = temp_dir

    return environment

def extract_video_info(video_url: str) -> dict[str, Any]:
    """Récupère les métadonnées via l'exécutable yt-dlp, sans téléchargement."""
    yt_dlp = find_yt_dlp()

    command = [
        yt_dlp,
        "--dump-single-json",
        "--skip-download",
        "--no-playlist",
        "--quiet",
        "--no-warnings",
        video_url,
    ]

    try:
        with create_process_temp_directory() as temp_dir:
            process_env = build_subprocess_environment(temp_dir)

            process = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                env=process_env,
            )
    except OSError as exc:
        raise TranscriptError(
            f"Impossible d'exécuter yt-dlp : {exc}"
        ) from exc

    if process.returncode != 0:
        error_message = process.stderr.decode(
            "utf-8", errors="replace"
        ).strip()

        if not error_message:
            error_message = (
                f"yt-dlp s'est terminé avec le code {process.returncode}."
            )

        raise TranscriptError(
            "Impossible de récupérer les informations de la vidéo avec "
            f"yt-dlp : {error_message}"
        )

    try:
        info = json.loads(process.stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TranscriptError(
            "yt-dlp n'a pas renvoyé un document JSON valide."
        ) from exc

    if not isinstance(info, dict):
        raise TranscriptError(
            "yt-dlp n'a pas renvoyé les métadonnées attendues."
        )

    return info


def select_subtitle_track(info: dict[str, Any]) -> SubtitleTrack:
    """
    Sélectionne la piste de sous-titres conformément aux règles du projet.
    """
    manual_subtitles = info.get("subtitles") or {}
    automatic_captions = info.get("automatic_captions") or {}

    if not isinstance(manual_subtitles, dict):
        manual_subtitles = {}

    if not isinstance(automatic_captions, dict):
        automatic_captions = {}

    # Une piste signifie ici une seule langue de sous-titres manuels.
    # Chaque langue peut elle-même proposer plusieurs formats.
    if len(manual_subtitles) == 1:
        language_code, formats = next(iter(manual_subtitles.items()))

        if base_language(language_code) in ACCEPTED_MANUAL_LANGUAGES:
            return make_subtitle_track(
                youtube_language_code=language_code,
                source="manual",
                formats=formats,
            )

    return select_original_automatic_track(automatic_captions)


def select_original_automatic_track(
    automatic_captions: dict[str, Any],
) -> SubtitleTrack:
    """
    Sélectionne la piste automatique correspondant à la langue originale.

    YouTube et yt-dlp exposent normalement cette piste avec un code se
    terminant par "-orig", par exemple "en-orig".
    """
    original_tracks = [
        (language_code, formats)
        for language_code, formats in automatic_captions.items()
        if language_code.lower().endswith("-orig")
    ]

    if not original_tracks:
        available_languages = ", ".join(
            sorted(automatic_captions.keys())
        )

        details = (
            f" Langues automatiques disponibles : {available_languages}."
            if available_languages
            else ""
        )

        raise TranscriptError(
            "Aucune piste automatique correspondant à la langue originale "
            f"n'a été trouvée.{details}"
        )

    if len(original_tracks) > 1:
        language_codes = ", ".join(
            language_code for language_code, _ in original_tracks
        )

        raise TranscriptError(
            "Plusieurs pistes automatiques sont marquées comme originales : "
            f"{language_codes}."
        )

    language_code, formats = original_tracks[0]

    return make_subtitle_track(
        youtube_language_code=language_code,
        source="automatic",
        formats=formats,
    )


def make_subtitle_track(
    *,
    youtube_language_code: str,
    source: Literal["manual", "automatic"],
    formats: Any,
) -> SubtitleTrack:
    """Sélectionne le format JSON3 d'une piste YouTube."""
    if not isinstance(formats, list):
        raise TranscriptError(
            f"La piste {youtube_language_code!r} possède une structure "
            "inattendue."
        )

    selected_format = next(
        (
            subtitle_format
            for subtitle_format in formats
            if isinstance(subtitle_format, dict)
            and subtitle_format.get("ext") == SUBTITLE_FORMAT
            and isinstance(subtitle_format.get("url"), str)
            and subtitle_format["url"]
        ),
        None,
    )

    if selected_format is None:
        available_formats = sorted(
            {
                str(subtitle_format["ext"])
                for subtitle_format in formats
                if isinstance(subtitle_format, dict)
                and subtitle_format.get("ext")
            }
        )

        available = ", ".join(available_formats) or "aucun"

        raise TranscriptError(
            f"La piste {youtube_language_code!r} ne propose pas le format "
            f"{SUBTITLE_FORMAT!r}. Formats disponibles : {available}."
        )

    raw_headers = selected_format.get("http_headers")
    http_headers = (
        {
            str(name): str(value)
            for name, value in raw_headers.items()
            if isinstance(name, str)
            and isinstance(value, (str, int, float))
        }
        if isinstance(raw_headers, dict)
        else {}
    )

    return SubtitleTrack(
        language=base_language(youtube_language_code),
        youtube_language_code=youtube_language_code,
        source=source,
        subtitle_format=SUBTITLE_FORMAT,
        url=selected_format["url"],
        http_headers=http_headers,
    )


def download_subtitle_json(
    track: SubtitleTrack,
) -> dict[str, Any]:
    """Télécharge et décode la piste JSON3 avec la bibliothèque standard."""
    headers = dict(track.http_headers)

    # Certains endpoints refusent les clients sans User-Agent. Si yt-dlp n'en
    # fournit pas, utiliser une valeur explicite et neutre.
    headers.setdefault("User-Agent", "Mozilla/5.0")

    request = Request(track.url, headers=headers)

    try:
        with urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            payload = response.read()
    except HTTPError as exc:
        raise TranscriptError(
            "Impossible de télécharger la piste "
            f"{track.youtube_language_code!r} : HTTP {exc.code} "
            f"{exc.reason or ''}".rstrip()
        ) from exc
    except URLError as exc:
        reason = getattr(exc, "reason", exc)
        raise TranscriptError(
            "Impossible de télécharger la piste "
            f"{track.youtube_language_code!r} : {reason}"
        ) from exc
    except (OSError, TimeoutError) as exc:
        raise TranscriptError(
            "Impossible de télécharger la piste "
            f"{track.youtube_language_code!r} : {exc}"
        ) from exc

    try:
        result = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TranscriptError(
            "La piste "
            f"{track.youtube_language_code!r} "
            "ne contient pas un JSON UTF-8 valide."
        ) from exc

    if not isinstance(result, dict):
        raise TranscriptError(
            "Le contenu de la piste "
            f"{track.youtube_language_code!r} "
            "possède une structure inattendue."
        )

    return result


def extract_subtitle_segments(
    subtitle_json: dict[str, Any],
) -> list[TranscriptSegment]:
    """
    Transforme les événements JSON3 en segments horodatés.

    Les retours à la ligne provenant de YouTube sont supprimés. Ils sont
    généralement liés à l'affichage des sous-titres et non à la structure
    logique du discours.
    """
    segments: list[TranscriptSegment] = []

    events = subtitle_json.get("events", [])

    if not isinstance(events, list):
        return segments

    for event in events:
        if not isinstance(event, dict):
            continue

        raw_segments = event.get("segs")

        # Certains événements JSON3 ne contiennent aucun texte :
        # positionnement, styles ou autres informations techniques.
        if not isinstance(raw_segments, list):
            continue

        event_start_ms = safe_int(event.get("tStartMs"), default=0)
        event_duration_ms = safe_optional_int(event.get("dDurationMs"))

        text_parts: list[str] = []

        for raw_segment in raw_segments:
            if not isinstance(raw_segment, dict):
                continue

            text = raw_segment.get("utf8")

            if not isinstance(text, str):
                continue

            # Les espaces initiaux présents dans certains segments JSON3
            # sont utiles pour reconstruire les mots et la ponctuation.
            text = text.replace("\n", " ")

            if text.strip():
                text_parts.append(text)

        if not text_parts:
            continue

        text = normalize_inline_whitespace("".join(text_parts))

        if not text:
            continue

        end_ms = (
            event_start_ms + event_duration_ms
            if event_duration_ms is not None
            else None
        )

        segments.append(
            TranscriptSegment(
                start_ms=event_start_ms,
                end_ms=end_ms,
                text=text,
            )
        )

    segments.sort(key=lambda segment: segment.start_ms)
    return segments


def build_continuous_transcript(
    segments: list[TranscriptSegment],
) -> str:
    """
    Construit un transcript continu, sans chapitres ni paragraphes ajoutés.
    """
    text = " ".join(segment.text for segment in segments)
    return normalize_transcript_text(text)


def extract_chapters(info: dict[str, Any]) -> list[Chapter]:
    """
    Extrait les chapitres sous forme de métadonnées indépendantes.

    Les timestamps d'origine sont conservés. Aucun chapitre n'est déplacé
    pour correspondre à une frontière de phrase.
    """
    raw_chapters = info.get("chapters")

    if not isinstance(raw_chapters, list):
        return []

    valid_chapters: list[tuple[float, str]] = []

    for raw_chapter in raw_chapters:
        if not isinstance(raw_chapter, dict):
            continue

        start_time = raw_chapter.get("start_time")
        title = raw_chapter.get("title")

        if not isinstance(start_time, (int, float)):
            continue

        if not isinstance(title, str) or not title.strip():
            continue

        valid_chapters.append(
            (
                float(start_time),
                normalize_inline_whitespace(title),
            )
        )

    valid_chapters.sort(key=lambda chapter: chapter[0])

    chapters: list[Chapter] = []

    for index, (start_seconds, title) in enumerate(valid_chapters):
        end_seconds = (
            valid_chapters[index + 1][0]
            if index + 1 < len(valid_chapters)
            else safe_optional_float(info.get("duration"))
        )

        chapters.append(
            Chapter(
                title=title,
                start_seconds=start_seconds,
                end_seconds=end_seconds,
            )
        )

    return chapters


def build_video_metadata(
    info: dict[str, Any],
    *,
    requested_url: str,
    include_description: bool,
    include_tags: bool,
    include_public_statistics: bool,
) -> dict[str, Any]:
    """Construit le bloc `video` du résultat."""
    video_id = optional_string(info.get("id"))

    webpage_url = (
        optional_string(info.get("webpage_url"))
        or canonical_youtube_url(video_id)
        or requested_url
    )

    channel_id = (
        optional_string(info.get("channel_id"))
        or optional_string(info.get("uploader_id"))
    )

    channel_name = (
        optional_string(info.get("channel"))
        or optional_string(info.get("uploader"))
    )

    channel_url = (
        optional_string(info.get("channel_url"))
        or optional_string(info.get("uploader_url"))
    )

    result: dict[str, Any] = {
        "id": video_id or extract_video_id_from_url(requested_url),
        "url": webpage_url,
        "title": optional_string(info.get("title")) or "Sans titre",
        "channel": {
            "id": channel_id,
            "name": channel_name,
            "url": channel_url,
        },
        "duration_seconds": safe_optional_float(info.get("duration")),
        "upload_date": normalize_upload_date(info.get("upload_date")),
    }

    if include_description:
        result["description"] = optional_string(info.get("description"))

    if include_tags:
        raw_tags = info.get("tags")

        result["tags"] = (
            [
                tag
                for tag in raw_tags
                if isinstance(tag, str) and tag.strip()
            ]
            if isinstance(raw_tags, list)
            else []
        )

    if include_public_statistics:
        result["public_statistics"] = {
            "view_count": safe_optional_int(info.get("view_count")),
            "like_count": safe_optional_int(info.get("like_count")),
            "comment_count": safe_optional_int(info.get("comment_count")),
        }

    return result


def normalize_transcript_text(text: str) -> str:
    """Normalise le transcript sans créer de paragraphes."""
    text = normalize_inline_whitespace(text)

    # Supprime les espaces placés avant la ponctuation.
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)

    # Ajoute un espace après certaines ponctuations lorsque celui-ci manque.
    text = re.sub(r"([,;:!?])(?=\S)", r"\1 ", text)

    # Évite de modifier les nombres décimaux comme 3.14.
    text = re.sub(
        r"(?<!\d)\.(?=[A-Za-zÀ-ÖØ-öø-ÿ])",
        ". ",
        text,
    )

    return normalize_inline_whitespace(text)


def normalize_inline_whitespace(text: str) -> str:
    """Remplace toute suite de caractères blancs par un espace."""
    return re.sub(r"\s+", " ", text).strip()


def count_words(text: str) -> int:
    """
    Compte approximativement les mots.

    Ce compteur convient à une statistique indicative. Ce n'est pas une
    tokenisation destinée à un modèle de langage.
    """
    return len(re.findall(r"\b[\w’'-]+\b", text, flags=re.UNICODE))


def base_language(language_code: str) -> str:
    """
    Retourne le code principal de langue.

    Exemples :
        en       -> en
        en-US    -> en
        fr-FR    -> fr
        en-orig  -> en
    """
    return language_code.lower().split("-", maxsplit=1)[0]


def normalize_upload_date(value: Any) -> str | None:
    """
    Convertit une date yt-dlp YYYYMMDD vers le format ISO YYYY-MM-DD.
    """
    if not isinstance(value, str):
        return None

    if not re.fullmatch(r"\d{8}", value):
        return None

    try:
        parsed_date = date(
            year=int(value[0:4]),
            month=int(value[4:6]),
            day=int(value[6:8]),
        )
    except ValueError:
        return None

    return parsed_date.isoformat()


def canonical_youtube_url(video_id: str | None) -> str | None:
    """Construit l'URL canonique d'une vidéo à partir de son identifiant."""
    if not video_id:
        return None

    return f"https://www.youtube.com/watch?v={video_id}"


def extract_video_id_from_url(url: str) -> str | None:
    """Essaie d'extraire l'identifiant d'une URL YouTube courante."""
    try:
        parsed = urlparse(url)
    except ValueError:
        return None

    hostname = parsed.hostname or ""

    if hostname in {"youtu.be", "www.youtu.be"}:
        candidate = parsed.path.strip("/")
        return candidate or None

    if hostname.endswith("youtube.com"):
        query = parse_qs(parsed.query)
        video_ids = query.get("v", [])

        if video_ids:
            return video_ids[0]

        path_parts = [
            part for part in parsed.path.split("/") if part
        ]

        if (
            len(path_parts) >= 2
            and path_parts[0] in {"shorts", "embed", "live"}
        ):
            return path_parts[1]

    return None


def optional_string(value: Any) -> str | None:
    """Retourne une chaîne non vide ou None."""
    if not isinstance(value, str):
        return None

    value = value.strip()
    return value or None


def safe_int(value: Any, *, default: int) -> int:
    """Convertit une valeur en entier ou renvoie la valeur par défaut."""
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return default


def safe_optional_int(value: Any) -> int | None:
    """Convertit une valeur en entier ou renvoie None."""
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return None


def safe_optional_float(value: Any) -> float | None:
    """Convertit une valeur en nombre flottant ou renvoie None."""
    try:
        return float(value)
    except (TypeError, ValueError, OverflowError):
        return None


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extrait les métadonnées et le transcript d'une vidéo YouTube "
            "dans un document JSON structuré."
        )
    )

    parser.add_argument(
        "url",
        help="URL de la vidéo YouTube",
    )

    parser.add_argument(
        "--include-segments",
        action="store_true",
        help="ajoute les segments horodatés du transcript",
    )

    parser.add_argument(
        "--include-description",
        action="store_true",
        help="ajoute la description complète de la vidéo",
    )

    parser.add_argument(
        "--include-tags",
        action="store_true",
        help="ajoute les tags YouTube",
    )

    parser.add_argument(
        "--include-public-statistics",
        action="store_true",
        help="ajoute les nombres de vues, likes et commentaires",
    )

    parser.add_argument(
        "--pretty",
        action="store_true",
        help="indente le JSON pour le rendre lisible par un humain",
    )

    parser.add_argument(
        "--output",
        type=Path,
        metavar="OUTPUT_FILE",
        help=(
            "écrit le document JSON dans ce fichier UTF-8 au lieu de "
            "l'afficher sur la sortie standard"
        ),
    )

    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()

    try:
        result = get_youtube_data(
            arguments.url,
            include_segments=arguments.include_segments,
            include_description=arguments.include_description,
            include_tags=arguments.include_tags,
            include_public_statistics=(
                arguments.include_public_statistics
            ),
        )
    except TranscriptError as exc:
        error_result = {
            "schema_version": SCHEMA_VERSION,
            "error": {
                "type": exc.__class__.__name__,
                "message": str(exc),
            },
        }

        print(
            json.dumps(
                error_result,
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 1

    indent = 2 if arguments.pretty else None

    document = json.dumps(
        result,
        ensure_ascii=False,
        indent=indent,
    )

    if arguments.output is None:
        print(document)
        return 0

    try:
        with arguments.output.open(
            "w",
            encoding="utf-8",
            newline="\n",
        ) as output_file:
            output_file.write(document)
            output_file.write("\n")
    except OSError as exc:
        error_result = {
            "schema_version": SCHEMA_VERSION,
            "error": {
                "type": exc.__class__.__name__,
                "message": (
                    f"Impossible d'écrire le fichier de sortie "
                    f"{arguments.output}: {exc}"
                ),
            },
        }
        print(
            json.dumps(
                error_result,
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

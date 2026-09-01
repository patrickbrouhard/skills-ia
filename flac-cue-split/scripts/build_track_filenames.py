#!/usr/bin/env python3
"""Construit des noms de fichiers FLAC sûrs et numérotés depuis une tracklist technique résolue."""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path


# Détecte une déclaration TRACK dans un fichier CUE.
TRACK_RE = re.compile(r"^\s*TRACK\s+(\d+)\s+(\S+)(?:\s|$)", re.IGNORECASE)

# Détecte un numéro de piste éventuellement déjà présent au début d'un titre.
NUMBERED_RE = re.compile(r"^(\d+)\s*(?:[-–—.]\s+|\s+)(.+)$")

# Caractères interdits ou problématiques dans les noms de fichiers.
FORBIDDEN_RE = re.compile(r'\s*[<>:"/\\|?*\x00-\x1f]+\s*')

# Noms de fichiers réservés sous Windows.
RESERVED = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}

# Limite conservatrice pour la taille d'un nom de fichier encodé en UTF-8.
MAX_FILENAME_BYTES = 240


class TrackNameError(ValueError):
    """Signale une erreur de validation lors de la construction des noms de pistes."""

    pass


def read_text(path: Path) -> str:
    """Lit un fichier texte en détectant les encodages pris en charge."""
    raw = path.read_bytes()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16")
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            pass
    raise TrackNameError(f"Impossible de décoder le fichier texte : {path}")


def parse_cue_track_numbers(path: Path) -> list[int]:
    """Extrait les numéros des pistes AUDIO d'un fichier CUE et vérifie leur unicité."""
    tracks: list[int] = []
    for line in read_text(path).splitlines():
        track_match = TRACK_RE.match(line)
        if not track_match or track_match.group(2).upper() != "AUDIO":
            continue
        number = int(track_match.group(1))
        if number in tracks:
            raise TrackNameError(f"Numéro de piste AUDIO dupliqué dans le CUE : {number}")
        tracks.append(number)

    if not tracks:
        raise TrackNameError("Le CUE ne contient aucune piste AUDIO.")
    return tracks


def parse_tracklist(path: Path, expected_count: int) -> list[str]:
    """Lit la tracklist et vérifie son nombre de lignes ainsi que l'absence de ligne vide."""
    lines = [line.strip() for line in read_text(path).splitlines()]
    if len(lines) != expected_count:
        raise TrackNameError(
            f"La tracklist contient {len(lines)} lignes ; {expected_count} étaient attendues."
        )
    if any(not line for line in lines):
        empty = next(index + 1 for index, line in enumerate(lines) if not line)
        raise TrackNameError(f"La ligne {empty} de la tracklist est vide.")
    return lines


def remove_supplied_number(value: str, expected_number: int) -> str:
    """Retire un numéro de piste fourni dans le titre après avoir vérifié sa cohérence."""
    match = NUMBERED_RE.match(value)
    if not match:
        return value
    supplied_number = int(match.group(1))
    if supplied_number != expected_number:
        raise TrackNameError(
            f"La tracklist indique la piste {supplied_number} à la place de {expected_number}."
        )
    return match.group(2).strip()


def truncate_utf8(value: str, byte_limit: int) -> str:
    """Tronque une chaîne à une taille UTF-8 maximale sans couper un caractère multioctet."""
    encoded = value.encode("utf-8")
    if len(encoded) <= byte_limit:
        return value
    encoded = encoded[:byte_limit]
    while encoded:
        try:
            return encoded.decode("utf-8").rstrip(" .")
        except UnicodeDecodeError as error:
            # Reculer jusqu'au début du caractère UTF-8 incomplet.
            encoded = encoded[: error.start]
    return ""


def sanitize_component(value: str) -> str:
    """Nettoie un composant de nom de fichier et évite les noms réservés sous Windows."""
    value = unicodedata.normalize("NFC", value)
    value = FORBIDDEN_RE.sub(" - ", value)
    value = re.sub(r"\s+", " ", value).strip().rstrip(" .")
    value = re.sub(r"(?:\s+-\s+){2,}", " - ", value)
    value = re.sub(r"(?:\s+-)+$", "", value).rstrip(" .")
    if not value or value in {".", ".."}:
        raise TrackNameError("Un titre devient vide après nettoyage du nom de fichier.")
    if value.split(".", 1)[0].upper() in RESERVED:
        # Préfixer les noms de périphériques réservés par Windows.
        value = f"_{value}"
    return value


def build_names(cue: Path, tracklist: Path) -> list[str]:
    """Construit et valide les noms de fichiers FLAC à partir du CUE et de la tracklist."""
    track_numbers = parse_cue_track_numbers(cue)
    titles = parse_tracklist(tracklist, len(track_numbers))
    width = max(2, len(str(max(track_numbers))))

    names: list[str] = []
    seen: dict[str, str] = {}
    for number, supplied_title in zip(track_numbers, titles, strict=True):
        title = remove_supplied_number(supplied_title, number)
        if title.lower().endswith(".flac"):
            title = title[:-5].rstrip()
        base = sanitize_component(f"{number:0{width}d} - {title}")
        base = truncate_utf8(base, MAX_FILENAME_BYTES - len(".flac"))
        if not base:
            raise TrackNameError(f"Le nom de la piste {number} est vide après troncature.")
        filename = f"{base}.flac"
        # Détecter aussi les collisions qui ne diffèrent que par la casse ou la normalisation Unicode.
        key = unicodedata.normalize("NFC", filename).casefold()
        if key in seen:
            raise TrackNameError(
                f"Deux pistes produisent le même nom de fichier : {seen[key]!r} et {filename!r}."
            )
        seen[key] = filename
        names.append(filename)

    return names


def main() -> int:
    """Analyse les arguments, construit les noms de pistes et les écrit dans le format demandé."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--cue", required=True, type=Path)
    parser.add_argument("--tracklist", required=True, type=Path)
    parser.add_argument(
        "--format", choices=("nul", "lines"), default="nul", dest="output_format"
    )
    args = parser.parse_args()

    try:
        names = build_names(args.cue, args.tracklist)
    except (OSError, TrackNameError) as error:
        print(f"ERREUR: {error}", file=sys.stderr)
        return 1

    print(f"Tracklist technique : {args.tracklist}", file=sys.stderr)
    if args.output_format == "nul":
        # Le séparateur NUL permet de transmettre sans ambiguïté des noms contenant des espaces.
        sys.stdout.buffer.write(b"\0".join(name.encode("utf-8") for name in names) + b"\0")
    else:
        print("\n".join(names))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
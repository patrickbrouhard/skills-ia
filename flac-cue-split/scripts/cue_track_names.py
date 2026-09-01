#!/usr/bin/env python3
"""Build safe, numbered FLAC filenames from a CUE sheet or tracklist."""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path


TRACK_RE = re.compile(r"^\s*TRACK\s+(\d+)\s+(\S+)(?:\s|$)", re.IGNORECASE)
TITLE_RE = re.compile(r'^\s*TITLE\s+(?:"(.*)"|([^"].*?))\s*$', re.IGNORECASE)
NUMBERED_RE = re.compile(r"^(\d+)\s*(?:[-–—.]\s+|\s+)(.+)$")
FORBIDDEN_RE = re.compile(r'\s*[<>:"/\\|?*\x00-\x1f]+\s*')
RESERVED = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}
MAX_FILENAME_BYTES = 240


class TrackNameError(ValueError):
    pass


def read_text(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16")
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            pass
    raise TrackNameError(f"Impossible de décoder le fichier texte : {path}")


def parse_cue(path: Path) -> list[tuple[int, str | None]]:
    tracks: list[tuple[int, str | None]] = []
    current_index: int | None = None

    for line in read_text(path).splitlines():
        track_match = TRACK_RE.match(line)
        if track_match:
            if track_match.group(2).upper() != "AUDIO":
                current_index = None
                continue
            number = int(track_match.group(1))
            if any(existing == number for existing, _ in tracks):
                raise TrackNameError(f"Numéro de piste AUDIO dupliqué dans le CUE : {number}")
            tracks.append((number, None))
            current_index = len(tracks) - 1
            continue

        if current_index is not None:
            title_match = TITLE_RE.match(line)
            if title_match and tracks[current_index][1] is None:
                title = (title_match.group(1) or title_match.group(2) or "").strip()
                number = tracks[current_index][0]
                tracks[current_index] = (number, title or None)

    if not tracks:
        raise TrackNameError("Le CUE ne contient aucune piste AUDIO.")
    return tracks


def parse_tracklist(path: Path, expected_count: int) -> list[str]:
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
    encoded = value.encode("utf-8")
    if len(encoded) <= byte_limit:
        return value
    encoded = encoded[:byte_limit]
    while encoded:
        try:
            return encoded.decode("utf-8").rstrip(" .")
        except UnicodeDecodeError as error:
            encoded = encoded[: error.start]
    return ""


def sanitize_component(value: str) -> str:
    value = unicodedata.normalize("NFC", value)
    value = FORBIDDEN_RE.sub(" - ", value)
    value = re.sub(r"\s+", " ", value).strip().rstrip(" .")
    value = re.sub(r"(?:\s+-\s+){2,}", " - ", value)
    value = re.sub(r"(?:\s+-)+$", "", value).rstrip(" .")
    if not value or value in {".", ".."}:
        raise TrackNameError("Un titre devient vide après nettoyage du nom de fichier.")
    if value.split(".", 1)[0].upper() in RESERVED:
        value = f"_{value}"
    return value


def build_names(cue: Path, tracklist: Path | None) -> tuple[list[str], str]:
    tracks = parse_cue(cue)
    width = max(2, len(str(max(number for number, _ in tracks))))

    if tracklist is not None:
        titles = parse_tracklist(tracklist, len(tracks))
        source = str(tracklist)
    else:
        missing = [number for number, title in tracks if not title]
        if missing:
            rendered = ", ".join(str(number) for number in missing)
            raise TrackNameError(
                f"Titre absent du CUE pour la/les piste(s) {rendered}. Fournir --tracklist."
            )
        titles = [title or "" for _, title in tracks]
        source = "titres TRACK du CUE"

    names: list[str] = []
    seen: dict[str, str] = {}
    for (number, _), supplied_title in zip(tracks, titles, strict=True):
        title = remove_supplied_number(supplied_title, number)
        if title.lower().endswith(".flac"):
            title = title[:-5].rstrip()
        base = sanitize_component(f"{number:0{width}d} - {title}")
        base = truncate_utf8(base, MAX_FILENAME_BYTES - len(".flac"))
        if not base:
            raise TrackNameError(f"Le nom de la piste {number} est vide après troncature.")
        filename = f"{base}.flac"
        key = unicodedata.normalize("NFC", filename).casefold()
        if key in seen:
            raise TrackNameError(
                f"Deux pistes produisent le même nom de fichier : {seen[key]!r} et {filename!r}."
            )
        seen[key] = filename
        names.append(filename)

    return names, source


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cue", required=True, type=Path)
    parser.add_argument("--tracklist", type=Path)
    parser.add_argument(
        "--format", choices=("nul", "lines"), default="nul", dest="output_format"
    )
    args = parser.parse_args()

    try:
        names, source = build_names(args.cue, args.tracklist)
    except (OSError, TrackNameError) as error:
        print(f"ERREUR: {error}", file=sys.stderr)
        return 1

    print(f"Source des titres : {source}", file=sys.stderr)
    if args.output_format == "nul":
        sys.stdout.buffer.write(b"\0".join(name.encode("utf-8") for name in names) + b"\0")
    else:
        print("\n".join(names))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

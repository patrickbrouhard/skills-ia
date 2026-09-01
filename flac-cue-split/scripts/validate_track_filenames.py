#!/usr/bin/env python3
"""Valide un manifeste de noms de fichiers FLAC finaux sans les modifier."""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path


FILENAME_RE = re.compile(r"^(\d+) - (.+)\.flac$")
FORBIDDEN_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
RESERVED = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}
MAX_FILENAME_BYTES = 240


class ManifestError(ValueError):
    """Signale qu'un manifeste ne peut pas être lu ou validé."""


def positive_int(value: str) -> int:
    """Convertit un argument en entier strictement positif."""
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("la valeur doit être strictement positive")
    return parsed


def read_filenames(path: Path) -> list[str]:
    """Lit un manifeste UTF-8, avec ou sans BOM, sans modifier les noms."""
    try:
        text = path.read_bytes().decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ManifestError(f"le manifeste n'est pas un fichier UTF-8 valide : {error}") from error
    return text.splitlines()


def validate_filenames(filenames: list[str], expected_count: int) -> list[str]:
    """Retourne toutes les violations détectées dans le manifeste."""
    issues: list[str] = []
    width = max(2, len(str(expected_count)))

    if len(filenames) != expected_count:
        issues.append(
            f"Manifeste : {len(filenames)} nom(s) fourni(s) ; {expected_count} attendu(s)."
        )

    seen: dict[str, int] = {}
    for index, filename in enumerate(filenames, start=1):
        prefix = f"Ligne {index}"

        if not filename:
            issues.append(f"{prefix} : le nom est vide.")
            continue
        if filename != filename.strip():
            issues.append(f"{prefix} : le nom commence ou se termine par un espace.")
        if unicodedata.normalize("NFC", filename) != filename:
            issues.append(f"{prefix} : le nom n'est pas normalisé en Unicode NFC.")
        if len(filename.encode("utf-8")) > MAX_FILENAME_BYTES:
            issues.append(
                f"{prefix} : le nom dépasse {MAX_FILENAME_BYTES} octets en UTF-8."
            )
        if FORBIDDEN_RE.search(filename):
            issues.append(f"{prefix} : le nom contient un caractère interdit sous Windows.")
        if filename in {".", ".."}:
            issues.append(f"{prefix} : ce nom de fichier est interdit.")

        match = FILENAME_RE.fullmatch(filename)
        if not match:
            issues.append(
                f"{prefix} : format attendu « {index:0{width}d} - Titre.flac »."
            )
        else:
            supplied_number, title = match.groups()
            expected_number = f"{index:0{width}d}"
            if supplied_number != expected_number:
                issues.append(
                    f"{prefix} : numéro {supplied_number!r} ; {expected_number!r} attendu."
                )
            if title != title.strip():
                issues.append(f"{prefix} : le titre commence ou se termine par un espace.")
            if title.endswith((".", " ")):
                issues.append(f"{prefix} : le titre se termine par un point ou un espace.")

        stem = filename[:-5] if filename.endswith(".flac") else filename
        device_name = stem.split(".", 1)[0].rstrip(" .").upper()
        if device_name in RESERVED:
            issues.append(f"{prefix} : {device_name!r} est un nom réservé sous Windows.")

        duplicate_key = unicodedata.normalize("NFC", filename).casefold()
        if duplicate_key in seen:
            issues.append(
                f"{prefix} : doublon du nom de la ligne {seen[duplicate_key]} "
                "après normalisation Unicode et comparaison sans casse."
            )
        else:
            seen[duplicate_key] = index

    return issues


def main() -> int:
    """Valide le manifeste ou émet ses noms inchangés avec un séparateur NUL."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--filenames", required=True, type=Path)
    parser.add_argument("--expected-count", required=True, type=positive_int)
    parser.add_argument(
        "--format", choices=("check", "nul"), default="check", dest="output_format"
    )
    args = parser.parse_args()

    try:
        filenames = read_filenames(args.filenames)
        issues = validate_filenames(filenames, args.expected_count)
    except (OSError, ManifestError) as error:
        print(f"ERREUR : {error}", file=sys.stderr)
        return 1

    if issues:
        print("ERREURS DE VALIDATION :", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1

    if args.output_format == "nul":
        print("Validation des noms de fichiers : OK", file=sys.stderr)
        sys.stdout.buffer.write(
            b"\0".join(filename.encode("utf-8") for filename in filenames) + b"\0"
        )
    else:
        print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import stat
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Literal
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


HTTP_TIMEOUT_SECONDS = 60

Channel = Literal["stable", "nightly", "master"]

CHANNEL_REPOSITORIES: dict[Channel, str] = {
    "stable": "yt-dlp/yt-dlp",
    "nightly": "yt-dlp/yt-dlp-nightly-builds",
    "master": "yt-dlp/yt-dlp-master-builds",
}


class YtDlpManagerError(RuntimeError):
    """Erreur pendant la gestion du binaire yt-dlp local."""


def script_directory() -> Path:
    return Path(__file__).resolve().parent


def local_binary_path() -> Path:
    return script_directory() / ("yt-dlp.exe" if os.name == "nt" else "yt-dlp")


def release_asset_name() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "windows":
        if machine in {"arm64", "aarch64"}:
            return "yt-dlp_arm64.exe"
        return "yt-dlp.exe"

    if system == "darwin":
        return "yt-dlp_macos"

    return "yt-dlp"


def repository_for_channel(channel: Channel) -> str:
    return CHANNEL_REPOSITORIES[channel]


def latest_release_api_url(channel: Channel) -> str:
    return f"https://api.github.com/repos/{repository_for_channel(channel)}/releases/latest"


def release_base_url(channel: Channel) -> str:
    return f"https://github.com/{repository_for_channel(channel)}/releases/latest/download"


def request_bytes(url: str) -> bytes:
    request = Request(
        url,
        headers={
            "User-Agent": "skills-yt-dlp-manager/2.0",
            "Accept": "application/vnd.github+json",
        },
    )

    try:
        with urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            return response.read()
    except HTTPError as exc:
        raise YtDlpManagerError(
            f"Requête impossible : HTTP {exc.code} pour {url}"
        ) from exc
    except URLError as exc:
        reason = getattr(exc, "reason", exc)
        raise YtDlpManagerError(
            f"Requête impossible pour {url} : {reason}"
        ) from exc
    except (OSError, TimeoutError) as exc:
        raise YtDlpManagerError(
            f"Requête impossible pour {url} : {exc}"
        ) from exc


def request_json(url: str) -> dict[str, Any]:
    payload = request_bytes(url)

    try:
        document = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise YtDlpManagerError(
            f"La réponse reçue depuis {url} n'est pas un JSON UTF-8 valide."
        ) from exc

    if not isinstance(document, dict):
        raise YtDlpManagerError(
            f"La réponse reçue depuis {url} n'est pas un objet JSON."
        )

    return document


def latest_version(channel: Channel) -> str:
    release = request_json(latest_release_api_url(channel))
    tag_name = release.get("tag_name")

    if not isinstance(tag_name, str) or not tag_name.strip():
        raise YtDlpManagerError(
            f"Impossible de déterminer la dernière version du canal {channel}."
        )

    return tag_name.strip()


def expected_sha256(checksums: bytes, asset_name: str) -> str:
    try:
        text = checksums.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise YtDlpManagerError(
            "Le fichier SHA2-256SUMS n'est pas un document UTF-8 valide."
        ) from exc

    pattern = re.compile(
        rf"^([0-9a-fA-F]{{64}})\s+\*?{re.escape(asset_name)}$",
        flags=re.MULTILINE,
    )
    match = pattern.search(text)

    if match is None:
        raise YtDlpManagerError(
            f"Impossible de trouver le checksum SHA-256 de {asset_name!r}."
        )

    return match.group(1).lower()


def verify_sha256(payload: bytes, expected: str) -> str:
    actual = hashlib.sha256(payload).hexdigest()

    if actual != expected:
        raise YtDlpManagerError(
            "Le checksum SHA-256 du binaire téléchargé ne correspond pas "
            f"à la valeur publiée. Attendu : {expected}; obtenu : {actual}."
        )

    return actual


def ensure_executable(path: Path) -> None:
    if os.name == "nt":
        return

    current_mode = path.stat().st_mode
    path.chmod(
        current_mode
        | stat.S_IXUSR
        | stat.S_IXGRP
        | stat.S_IXOTH
    )


@contextmanager
def process_temp_directory() -> Iterator[Path]:
    candidates: list[Path | None] = []

    try:
        candidates.append(Path.cwd())
    except OSError:
        pass

    candidates.append(script_directory())
    candidates.append(None)

    last_error: OSError | None = None

    for parent in candidates:
        try:
            with tempfile.TemporaryDirectory(
                prefix=".yt-dlp-temp-",
                dir=parent,
            ) as temp_dir:
                yield Path(temp_dir)
                return
        except OSError as exc:
            last_error = exc

    raise YtDlpManagerError(
        "Impossible de créer un répertoire temporaire accessible pour yt-dlp"
        + (f" : {last_error}" if last_error else ".")
    )


def subprocess_environment(temp_dir: Path) -> dict[str, str]:
    env = os.environ.copy()

    if os.name == "nt":
        env["TEMP"] = str(temp_dir)
        env["TMP"] = str(temp_dir)
    else:
        env["TMPDIR"] = str(temp_dir)

    return env


def run_binary(
    binary: Path,
    *arguments: str,
) -> subprocess.CompletedProcess[bytes]:
    try:
        with process_temp_directory() as temp_dir:
            return subprocess.run(
                [str(binary), *arguments],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                env=subprocess_environment(temp_dir),
            )
    except OSError as exc:
        raise YtDlpManagerError(
            f"Impossible d'exécuter {binary} : {exc}"
        ) from exc


def decode_output(data: bytes) -> str:
    return data.decode("utf-8", errors="replace").strip()


def get_version(binary: Path) -> str:
    process = run_binary(binary, "--version")

    if process.returncode != 0:
        stderr = decode_output(process.stderr)
        raise YtDlpManagerError(
            "Le binaire yt-dlp local ne répond pas correctement à "
            f"`--version` (code {process.returncode})"
            + (f" : {stderr}" if stderr else ".")
        )

    version = decode_output(process.stdout)

    if not version:
        raise YtDlpManagerError(
            "Le binaire yt-dlp local n'a renvoyé aucune version."
        )

    return version


def status() -> dict[str, Any]:
    binary = local_binary_path()

    if not binary.is_file():
        return {
            "status": "not_installed",
            "path": str(binary),
        }

    return {
        "status": "installed",
        "path": str(binary),
        "version": get_version(binary),
    }


def check(channel: Channel) -> dict[str, Any]:
    binary = local_binary_path()

    if not binary.is_file():
        return {
            "status": "not_installed",
            "path": str(binary),
            "channel": channel,
        }

    local = get_version(binary)
    latest = latest_version(channel)

    return {
        "status": "up_to_date" if local == latest else "update_available",
        "path": str(binary),
        "channel": channel,
        "local_version": local,
        "latest_version": latest,
    }


def install(
    channel: Channel,
    *,
    force: bool = False,
) -> dict[str, Any]:
    destination = local_binary_path()

    if destination.exists() and not force:
        return {
            "status": "already_installed",
            "path": str(destination),
            "version": get_version(destination),
            "channel_requested": channel,
        }

    asset_name = release_asset_name()
    base_url = release_base_url(channel)

    payload = request_bytes(f"{base_url}/{asset_name}")
    checksums = request_bytes(f"{base_url}/SHA2-256SUMS")

    expected_hash = expected_sha256(checksums, asset_name)
    actual_hash = verify_sha256(payload, expected_hash)

    destination.parent.mkdir(parents=True, exist_ok=True)

    backup_path: Path | None = None

    if destination.exists():
        backup_path = destination.with_name(destination.name + ".backup")
        if backup_path.exists():
            backup_path.unlink()
        os.replace(destination, backup_path)

    temporary_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=destination.name + ".",
            suffix=".tmp",
            dir=destination.parent,
            delete=False,
        ) as temporary_file:
            temporary_file.write(payload)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
            temporary_path = Path(temporary_file.name)

        ensure_executable(temporary_path)
        os.replace(temporary_path, destination)
        temporary_path = None

        version = get_version(destination)

    except Exception:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()

        if destination.exists():
            destination.unlink()

        if backup_path is not None and backup_path.exists():
            os.replace(backup_path, destination)

        raise

    if backup_path is not None and backup_path.exists():
        backup_path.unlink()

    return {
        "status": "installed",
        "path": str(destination),
        "version": version,
        "channel_requested": channel,
        "asset": asset_name,
        "sha256": actual_hash,
    }


def update(channel: Channel | None) -> dict[str, Any]:
    binary = local_binary_path()

    if not binary.is_file():
        raise YtDlpManagerError(
            "Aucun binaire yt-dlp local n'est installé. "
            "Utiliser d'abord la commande `install`."
        )

    before = get_version(binary)

    arguments = (
        ("-U",)
        if channel is None
        else ("--update-to", channel)
    )

    process = run_binary(binary, *arguments)

    stdout = decode_output(process.stdout)
    stderr = decode_output(process.stderr)

    if process.returncode != 0:
        details = stderr or stdout or "aucun détail fourni"
        raise YtDlpManagerError(
            "La mise à jour de yt-dlp a échoué "
            f"(code {process.returncode}) : {details}"
        )

    after = get_version(binary)

    return {
        "status": "updated" if after != before else "already_up_to_date",
        "path": str(binary),
        "version_before": before,
        "version_after": after,
        "channel_requested": channel or "current",
        "updater_output": stdout or None,
    }


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Installe, vérifie, met à jour ou inspecte le binaire yt-dlp "
            "local à la skill YouTube."
        )
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    subparsers.add_parser(
        "status",
        help="affiche la version du binaire yt-dlp local sans accès réseau",
    )

    check_parser = subparsers.add_parser(
        "check",
        help="compare la version locale à la dernière release officielle",
    )
    check_parser.add_argument(
        "--channel",
        choices=tuple(CHANNEL_REPOSITORIES),
        default="stable",
        help="canal à vérifier (défaut : stable)",
    )

    install_parser = subparsers.add_parser(
        "install",
        help="installe le binaire yt-dlp local",
    )
    install_parser.add_argument(
        "--channel",
        choices=tuple(CHANNEL_REPOSITORIES),
        default="stable",
        help="canal à installer (défaut : stable)",
    )
    install_parser.add_argument(
        "--force",
        action="store_true",
        help="remplace le binaire local s'il existe déjà",
    )

    update_parser = subparsers.add_parser(
        "update",
        help="met à jour le binaire yt-dlp local",
    )
    update_parser.add_argument(
        "--channel",
        choices=tuple(CHANNEL_REPOSITORIES),
        default=None,
        help=(
            "change de canal pendant la mise à jour ; "
            "sans cette option, conserve le canal courant"
        ),
    )

    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()

    try:
        if arguments.command == "status":
            result = status()
        elif arguments.command == "check":
            result = check(arguments.channel)
        elif arguments.command == "install":
            result = install(
                arguments.channel,
                force=arguments.force,
            )
        else:
            result = update(arguments.channel)

    except YtDlpManagerError as exc:
        print(
            json.dumps(
                {
                    "status": "error",
                    "error": {
                        "type": exc.__class__.__name__,
                        "message": str(exc),
                    },
                },
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 1

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

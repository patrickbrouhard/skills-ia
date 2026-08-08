#!/usr/bin/env python3

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ENV_FILE = Path(__file__).resolve().with_name(".env")


class KarakeepError(RuntimeError):
    pass


@dataclass(frozen=True)
class HttpResponse:
    status_code: int
    body: bytes

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")

    def json(self) -> Any:
        return json.loads(self.text)


def load_env_file(path: Path) -> None:
    """
    Charge un fichier .env simple sans dépendance externe.

    Les variables déjà présentes dans os.environ restent prioritaires.
    Formats pris en charge :
        KEY=value
        KEY="value"
        KEY='value'
        export KEY=value
    """
    if not path.is_file():
        return

    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except OSError as exc:
        raise KarakeepError(
            f"Impossible de lire le fichier d'environnement {path}: {exc}"
        ) from exc

    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        if line.startswith("export "):
            line = line[7:].lstrip()

        if "=" not in line:
            raise KarakeepError(
                f"Ligne .env invalide à la ligne {line_number}: {raw_line!r}"
            )

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            raise KarakeepError(
                f"Nom de variable .env invalide à la ligne {line_number}: "
                f"{key!r}"
            )

        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            quote = value[0]
            value = value[1:-1]

            if quote == '"':
                value = (
                    value.replace(r"\\n", "\n")
                    .replace(r"\\r", "\r")
                    .replace(r"\\t", "\t")
                    .replace(r'\\"', '"')
                    .replace(r"\\\\", "\\")
                )
        else:
            comment_match = re.search(r"\s+#", value)
            if comment_match:
                value = value[:comment_match.start()].rstrip()

        os.environ.setdefault(key, value)


class KarakeepClient:
    def __init__(self, base_url: str, api_key: str, timeout: int = 20) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "karakeep-cli/1.0",
        }

    def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> HttpResponse:
        params = kwargs.pop("params", None)
        json_payload = kwargs.pop("json", None)

        if kwargs:
            unsupported = ", ".join(sorted(kwargs))
            raise TypeError(f"Arguments HTTP non pris en charge : {unsupported}")

        url = f"{self.base_url}/api/v1{path}"

        if params:
            query = urlencode(params, doseq=True)
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}{query}"

        body = None
        if json_payload is not None:
            body = json.dumps(
                json_payload,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")

        request = Request(
            url,
            data=body,
            headers=self.headers,
            method=method,
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                return HttpResponse(
                    status_code=response.status,
                    body=response.read(),
                )
        except HTTPError as exc:
            error_body = exc.read()
            response = HttpResponse(
                status_code=exc.code,
                body=error_body,
            )

            try:
                details = response.json()
            except (ValueError, json.JSONDecodeError):
                details = response.text.strip()

            raise KarakeepError(
                f"Karakeep a répondu HTTP {response.status_code}: {details}"
            ) from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise KarakeepError(f"Erreur réseau : {exc}") from exc

    def check_url(self, url: str) -> str | None:
        response = self._request(
            "GET",
            "/bookmarks/check-url",
            params={"url": url},
        )
        return response.json().get("bookmarkId")

    def add_url(
        self,
        url: str,
        summary: str | None = None,
    ) -> tuple[dict[str, Any], int]:
        payload: dict[str, Any] = {
            "type": "link",
            "url": url,
            "source": "cli",
        }

        if summary is not None:
            payload["summary"] = summary

        response = self._request(
            "POST",
            "/bookmarks",
            json=payload,
        )

        return response.json(), response.status_code

    def get_bookmark(self, bookmark_id: str) -> dict[str, Any]:
        response = self._request(
            "GET",
            f"/bookmarks/{bookmark_id}",
        )
        return response.json()

    def update_summary(
        self,
        bookmark_id: str,
        summary: str,
    ) -> dict[str, Any]:
        response = self._request(
            "PATCH",
            f"/bookmarks/{bookmark_id}",
            json={"summary": summary},
        )
        return response.json()

    def attach_tags(
        self,
        bookmark_id: str,
        tags: list[str],
    ) -> dict[str, Any]:
        response = self._request(
            "POST",
            f"/bookmarks/{bookmark_id}/tags",
            json={
                "tags": [
                    {
                        "tagName": tag,
                        "attachedBy": "ai",
                    }
                    for tag in tags
                ]
            },
        )
        return response.json()

    def search(self, query: str, limit: int = 10) -> dict[str, Any]:
        response = self._request(
            "GET",
            "/bookmarks/search",
            params={
                "q": query,
                "limit": limit,
            },
        )
        return response.json()


def print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


def read_text_input(source: str) -> str:
    try:
        text = (
            sys.stdin.read()
            if source == "-"
            else Path(source).read_text(encoding="utf-8")
        )
    except OSError as exc:
        raise KarakeepError(
            f"Impossible de lire le résumé depuis {source!r} : {exc}"
        ) from exc

    text = text.strip()

    if not text:
        raise KarakeepError("Le résumé ne peut pas être vide.")

    return text


def normalize_tags(raw_tags: list[str]) -> list[str]:
    tags: list[str] = []
    seen: set[str] = set()

    for raw_tag in raw_tags:
        tag = raw_tag.strip().lstrip("#").lower()

        if not tag:
            raise KarakeepError("Un tag ne peut pas être vide.")

        if re.search(r"\s", tag):
            raise KarakeepError(
                f"Le tag {raw_tag!r} contient un espace. "
                "Utilise des tirets pour les tags composés."
            )

        if tag not in seen:
            tags.append(tag)
            seen.add(tag)

    return tags


def has_summary(bookmark: dict[str, Any]) -> bool:
    summary = bookmark.get("summary")
    return isinstance(summary, str) and bool(summary.strip())


def command_add(
    client: KarakeepClient,
    url: str,
    summary: str | None,
    tags: list[str],
) -> bool:
    bookmark, http_status = client.add_url(url, summary)
    bookmark_id = bookmark.get("id")

    if http_status == 200:
        print_json(
            {
                "status": "already_exists",
                "httpStatus": http_status,
                "bookmarkId": bookmark_id,
                "summaryPresent": has_summary(bookmark),
                "bookmark": bookmark,
            }
        )
        return True

    if http_status != 201:
        raise KarakeepError(
            "Réponse inattendue pendant la création : "
            f"HTTP {http_status}."
        )

    result: dict[str, Any] = {
        "status": "created",
        "httpStatus": http_status,
        "bookmarkId": bookmark_id,
        "summary": {
            "status": (
                "included_at_creation"
                if summary is not None
                else "not_provided"
            )
        },
        "tags": {"status": "not_requested", "names": []},
        "bookmark": bookmark,
    }

    if tags:
        if not isinstance(bookmark_id, str) or not bookmark_id:
            raise KarakeepError(
                "Karakeep n'a pas renvoyé l'identifiant du bookmark créé."
            )

        try:
            tag_result = client.attach_tags(bookmark_id, tags)
        except KarakeepError as exc:
            result["status"] = "partially_created"
            result["tags"] = {
                "status": "failed",
                "names": tags,
                "error": str(exc),
            }
            print_json(result)
            return False

        result["tags"] = {
            "status": "attached",
            "names": tags,
            "result": tag_result,
        }

    print_json(result)
    return True


def command_set_summary(
    client: KarakeepClient,
    bookmark_id: str,
    summary: str,
    replace: bool,
) -> None:
    bookmark = client.get_bookmark(bookmark_id)
    summary_already_present = has_summary(bookmark)

    if summary_already_present and not replace:
        print_json(
            {
                "status": "summary_already_present",
                "bookmarkId": bookmark_id,
                "replaced": False,
                "summaryPresent": True,
            }
        )
        return

    updated_bookmark = client.update_summary(bookmark_id, summary)

    print_json(
        {
            "status": (
                "summary_replaced"
                if summary_already_present
                else "summary_added"
            ),
            "bookmarkId": bookmark_id,
            "replaced": summary_already_present,
            "bookmark": updated_bookmark,
        }
    )


def command_search(
    client: KarakeepClient,
    query: str,
    limit: int,
) -> None:
    results = client.search(query, limit)
    print_json(results)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="CLI minimal pour Karakeep"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser(
        "add",
        help="Ajouter une URL de manière idempotente",
    )
    add_parser.add_argument("url")
    add_parser.add_argument(
        "--summary-file",
        metavar="PATH",
        help="fichier Markdown du résumé, ou - pour l'entrée standard",
    )
    add_parser.add_argument(
        "--tag",
        action="append",
        default=[],
        metavar="TAG",
        help="tag à attacher après la création (option répétable)",
    )

    summary_parser = subparsers.add_parser(
        "set-summary",
        help="Ajouter un résumé à un bookmark existant",
    )
    summary_parser.add_argument("bookmark_id")
    summary_parser.add_argument(
        "--summary-file",
        required=True,
        metavar="PATH",
        help="fichier Markdown du résumé, ou - pour l'entrée standard",
    )
    summary_parser.add_argument(
        "--replace",
        action="store_true",
        help="remplacer un résumé existant",
    )

    search_parser = subparsers.add_parser(
        "search",
        help="Rechercher dans les bookmarks",
    )
    search_parser.add_argument("query")
    search_parser.add_argument(
        "--limit",
        type=int,
        default=10,
    )

    check_parser = subparsers.add_parser(
        "check",
        help="Vérifier si une URL existe déjà",
    )
    check_parser.add_argument("url")

    return parser


def main() -> int:
    # Les variables déjà définies dans l'environnement restent prioritaires.
    load_env_file(ENV_FILE)

    parser = build_parser()
    args = parser.parse_args()

    base_url = os.environ.get("KARAKEEP_URL")
    api_key = os.environ.get("KARAKEEP_API_KEY")

    if not base_url:
        print(
            "Variable KARAKEEP_URL manquante.",
            file=sys.stderr,
        )
        return 2

    if not api_key:
        print(
            "Variable KARAKEEP_API_KEY manquante.",
            file=sys.stderr,
        )
        return 2

    client = KarakeepClient(base_url, api_key)

    try:
        if args.command == "add":
            summary = (
                read_text_input(args.summary_file)
                if args.summary_file
                else None
            )
            tags = normalize_tags(args.tag)

            if not command_add(client, args.url, summary, tags):
                return 1

        elif args.command == "set-summary":
            summary = read_text_input(args.summary_file)
            command_set_summary(
                client,
                args.bookmark_id,
                summary,
                args.replace,
            )

        elif args.command == "search":
            command_search(client, args.query, args.limit)

        elif args.command == "check":
            bookmark_id = client.check_url(args.url)
            print_json(
                {
                    "exists": bookmark_id is not None,
                    "bookmarkId": bookmark_id,
                    "url": args.url,
                }
            )

        return 0

    except KarakeepError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Find only email addresses explicitly published on a public job page."""

from __future__ import annotations

import html
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

EMAIL = re.compile(r"(?<![\w.+-])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}(?![\w.-])", re.I)
MAILTO = re.compile(r"mailto:([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})", re.I)
NON_CONTACT_DOMAINS = {"ingest.sentry.io", "example.com", "example.org", "example.net"}


def public_emails(*texts: str) -> list[str]:
    found: dict[str, str] = {}
    for text in texts:
        source = html.unescape(text or "")
        visible = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", "", source, flags=re.I | re.S)
        candidates = [*MAILTO.findall(visible), *EMAIL.findall(re.sub(r"<[^>]+>", " ", visible))]
        for match in candidates:
            domain = match.rsplit("@", 1)[-1].casefold()
            if domain in NON_CONTACT_DOMAINS:
                continue
            found.setdefault(match.casefold(), match)
    return sorted(found.values(), key=str.casefold)


def fetch_public_page(url: str) -> str:
    request = Request(url, headers={"User-Agent": "JobHuntOS/0.1 (personal job search)"})
    try:
        with urlopen(request, timeout=20) as response:  # nosec B310: public URL from an ingested post
            return response.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError, TimeoutError) as error:
        raise RuntimeError(f"Could not read the public job page: {error}") from error

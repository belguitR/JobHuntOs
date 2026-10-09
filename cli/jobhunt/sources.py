"""Public ATS board readers. No login, private data, LinkedIn scraping or browser bypasses."""

from __future__ import annotations

import hashlib
import html
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class SourceError(RuntimeError):
    """A board could not be read without bypassing access controls."""


@dataclass(frozen=True)
class Source:
    kind: str
    label: str
    board: str = ""
    pages: int = 1


def _fetch(url: str) -> dict | list:
    request = Request(url, headers={"User-Agent": "JobHuntOS/0.1 (personal job search)"})
    try:
        with urlopen(request, timeout=20) as response:  # nosec B310: fixed public HTTPS endpoints
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
        raise SourceError(f"Could not read public board: {error}") from error


def _text(value: str | None) -> str:
    unescaped = html.unescape(value or "")
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", unescaped)).strip()


def _stamp(value) -> str:
    if not value:
        return ""
    if isinstance(value, (int, float)):
        seconds = value / 1000 if value > 100_000_000_000 else value
        return datetime.fromtimestamp(seconds, UTC).date().isoformat()
    return str(value)


def _job(source: Source, external_id: str, company: str, title: str, url: str, **fields) -> dict:
    description = _text(fields.get("description", ""))
    source_key = f"{source.kind}:{source.board}:{external_id}"
    dedupe_parts = (company or "", title or "", fields.get("location") or "")
    dedupe_key = "|".join(re.sub(r"\W+", "", part.casefold()) for part in dedupe_parts)
    return {
        "source_key": source_key,
        "dedupe_key": dedupe_key,
        "source_kind": source.kind,
        "source_label": source.label,
        "external_id": external_id,
        "company_name": company or "Unknown company",
        "job_title": title or "Untitled role",
        "job_url": url or "",
        "location": fields.get("location") or "",
        "country": fields.get("country") or "",
        "workplace_type": fields.get("workplace_type") or "",
        "description": description,
        "salary_text": fields.get("salary_text") or "",
        "language_requirements": fields.get("language_requirements") or "",
        "posted_at": _stamp(fields.get("posted_at")),
        "content_hash": hashlib.sha256(description.encode("utf-8")).hexdigest(),
    }


def greenhouse(source: Source) -> list[dict]:
    data = _fetch(f"https://boards-api.greenhouse.io/v1/boards/{source.board}/jobs?content=true")
    company = source.label or source.board
    return [
        _job(
            source, str(item["id"]), company, item["title"], item["absolute_url"],
            location=(item.get("location") or {}).get("name", ""),
            description=item.get("content", ""), posted_at=item.get("updated_at", ""),
        )
        for item in data.get("jobs", [])
    ]


def lever(source: Source) -> list[dict]:
    data = _fetch(f"https://api.lever.co/v0/postings/{source.board}?mode=json")
    company = source.label or source.board
    return [
        _job(
            source, str(item["id"]), company, item["text"], item["hostedUrl"],
            location=(item.get("categories") or {}).get("location", ""),
            workplace_type=(item.get("workplaceType") or ""),
            description=item.get("descriptionPlain") or item.get("description", ""),
            salary_text=(item.get("salaryRange") or {}).get("text", ""),
            posted_at=item.get("createdAt"),
        )
        for item in data
    ]


def ashby(source: Source) -> list[dict]:
    data = _fetch(f"https://api.ashbyhq.com/posting-api/job-board/{source.board}")
    company = source.label or source.board
    return [
        _job(
            source, str(item.get("jobUrl") or item["title"]), company, item["title"], item["jobUrl"],
            location=item.get("location", ""), workplace_type=item.get("workplaceType", ""),
            description=item.get("descriptionPlain") or item.get("descriptionHtml", ""),
            posted_at=item.get("publishedAt", ""),
        )
        for item in data.get("jobs", [])
        if item.get("jobUrl")
    ]


def arbeitnow(source: Source) -> list[dict]:
    jobs: list[dict] = []
    pages = max(1, min(source.pages, 5))
    for page in range(1, pages + 1):
        data = _fetch(f"https://www.arbeitnow.com/api/job-board-api?page={page}")
        records = data.get("data", [])
        for item in records:
            jobs.append(
                _job(
                    source,
                    str(item["slug"]),
                    item.get("company_name") or "Unknown company",
                    item.get("title") or "Untitled role",
                    item.get("url") or "",
                    location=item.get("location"),
                    workplace_type="Remote" if item.get("remote") else "",
                    description=item.get("description"),
                    language_requirements=" ".join(item.get("tags") or []),
                    posted_at=item.get("created_at"),
                )
            )
        if len(records) < 250:
            break
    return jobs


def remotive(source: Source) -> list[dict]:
    data = _fetch("https://remotive.com/api/remote-jobs?category=software-dev&limit=100")
    return [
        _job(
            source,
            str(item["id"]),
            item.get("company_name") or "Unknown company",
            item.get("title") or "Untitled role",
            item.get("url") or "",
            location=item.get("candidate_required_location"),
            workplace_type="Remote",
            description=item.get("description"),
            salary_text=item.get("salary"),
            language_requirements=" ".join(item.get("tags") or []),
            posted_at=item.get("publication_date"),
        )
        for item in data.get("jobs", [])
    ]


READERS = {
    "greenhouse": greenhouse,
    "lever": lever,
    "ashby": ashby,
    "arbeitnow": arbeitnow,
    "remotive": remotive,
}


def read(source: Source) -> list[dict]:
    reader = READERS.get(source.kind)
    if reader is None:
        raise SourceError(f"Unknown source kind '{source.kind}'. Use: {', '.join(READERS)}.")
    return reader(source)

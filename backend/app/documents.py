"""Preserve DOCX formatting by replacing only text runs in its XML."""

import hashlib
import io
import re
import uuid
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

from fastapi import HTTPException

from .service import insert, now

MAX_SIZE = 15 * 1024 * 1024
TEXT = re.compile(rb"<w:t(?:\s[^>]*)?>.*?</w:t>", re.DOTALL)
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
PART = r"word/(document|header\d+|footer\d+)\.xml"


def document_parts(content):
    try:
        archive = zipfile.ZipFile(io.BytesIO(content))
        if sum(item.file_size for item in archive.infolist()) > 50 * 1024 * 1024:
            raise ValueError("Document too large")
        if "word/document.xml" not in archive.namelist() or any(
            "vbaProject" in n for n in archive.namelist()
        ):
            raise ValueError("Unsupported document")
        return archive
    except (ValueError, zipfile.BadZipFile) as exc:
        raise HTTPException(422, "Invalid or unsupported DOCX document") from exc


def editable_runs(content):
    with document_parts(content) as archive:
        result = []
        for name in archive.namelist():
            if re.fullmatch(PART, name):
                raw = archive.read(name)
                try:
                    paragraphs = ET.fromstring(raw).findall(".//w:p", NS)
                    index = 0
                    for paragraph_index, paragraph in enumerate(paragraphs):
                        for node in paragraph.findall(".//w:t", NS):
                            result.append(
                                {
                                    "id": f"{name}:{index}",
                                    "text": node.text or "",
                                    "paragraph": f"{name}:{paragraph_index}",
                                    "section": name,
                                }
                            )
                            index += 1
                    if index != len(TEXT.findall(raw)):
                        raise ValueError("Unsupported encoding")
                except (ET.ParseError, ValueError) as exc:
                    raise HTTPException(
                        422,
                        "Unsupported DOCX text layout. Download and edit this file in Word.",
                    ) from exc
        return result


def rewrite(content, changes):
    if set(changes) - {run["id"] for run in editable_runs(content)}:
        raise HTTPException(422, "Unknown document text segment")
    if any(
        len(v) > 100000 or any(ord(c) < 32 and c not in "\n\t\r" for c in v)
        for v in changes.values()
    ):
        raise HTTPException(422, "Invalid replacement text")
    output = io.BytesIO()
    with (
        document_parts(content) as source,
        zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as target,
    ):
        for info in source.infolist():
            raw = source.read(info.filename)
            index = 0

            def replace(match, part_name=info.filename):
                nonlocal index
                key = f"{part_name}:{index}"
                index += 1
                if key not in changes:
                    return match.group(0)
                return ('<w:t xml:space="preserve">' + escape(changes[key]) + "</w:t>").encode(
                    "utf-8"
                )

            if re.fullmatch(PART, info.filename):
                raw = TEXT.sub(replace, raw)
            target.writestr(info, raw)
    return output.getvalue()


def store_resume(connection, directory: Path, data, content):
    key = uuid.uuid4().hex + Path(data["filename"]).suffix.lower()
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / key
    path.write_bytes(content)
    stamp = now()
    try:
        return insert(
            connection,
            "resumes",
            {
                **data,
                "storage_key": key,
                "sha256": hashlib.sha256(content).hexdigest(),
                "created_at": stamp,
                "updated_at": stamp,
            },
        )
    except Exception:
        path.unlink(missing_ok=True)
        raise

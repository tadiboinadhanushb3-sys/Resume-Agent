from __future__ import annotations

import io
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ReadResult:
    filename: str
    text: str


def _read_pdf(data: bytes) -> str:
    import pdfplumber

    text_parts: list[str] = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            if t.strip():
                text_parts.append(t)
    return "\n".join(text_parts).strip()


def _read_docx(data: bytes) -> str:
    import docx2txt

    # docx2txt expects a path; write to a temp file in-memory isn't supported.
    # We keep it simple here and fall back to extracting plain text if installed.
    import tempfile

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as f:
        f.write(data)
        tmp_path = f.name
    try:
        return (docx2txt.process(tmp_path) or "").strip()
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def _read_txt(data: bytes) -> str:
    for enc in ("utf-8", "utf-16", "latin-1"):
        try:
            return data.decode(enc).strip()
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="ignore").strip()


def read_resume_bytes(filename: str, data: bytes) -> ReadResult:
    ext = os.path.splitext(filename.lower())[1]
    if ext == ".pdf":
        text = _read_pdf(data)
    elif ext in (".docx",):
        text = _read_docx(data)
    else:
        text = _read_txt(data)

    return ReadResult(filename=filename, text=text)


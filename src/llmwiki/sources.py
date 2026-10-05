"""Extracting text from source files for ingest. Files in raw/ are never modified or converted on disk."""

import re
from pathlib import Path

TEXT_EXTS = {".md", ".markdown", ".txt", ".rst"}
# Readable without MarkItDown (pypdf / a basic tag stripper), but MarkItDown does better when installed.
BUILTIN_EXTS = {".pdf", ".html", ".htm"}
# Readable only with MarkItDown: uv sync --extra convert
CONVERT_EXTS = {".docx", ".pptx", ".xlsx", ".xls", ".epub", ".msg", ".csv", ".json", ".xml", ".ipynb"}
SUPPORTED_EXTS = TEXT_EXTS | BUILTIN_EXTS | CONVERT_EXTS

# Binary formats and their file signatures. MarkItDown silently falls back to reading a corrupt
# or misnamed file as plain text, so check the signature before trusting the extension.
ZIP = b"PK\x03\x04"
OLE = b"\xd0\xcf\x11\xe0"
SIGNATURES = {".docx": ZIP, ".pptx": ZIP, ".xlsx": ZIP, ".epub": ZIP, ".xls": OLE, ".msg": OLE, ".pdf": b"%PDF"}


class UnsupportedSource(Exception):
    """The file can't be turned into text; the message says why and what to do."""


_converter = None


def _markitdown():
    global _converter
    if _converter is None:
        try:
            from markitdown import MarkItDown
        except ImportError:
            _converter = False
        else:
            _converter = MarkItDown()
    return _converter or None


def is_supported(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_EXTS


def read_source(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in TEXT_EXTS:
        text = path.read_text(encoding="utf-8", errors="replace")
    elif suffix not in SUPPORTED_EXTS:
        raise UnsupportedSource(
            f"{path.name}: unsupported file type '{suffix or '(none)'}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTS))}"
        )
    elif (sig := SIGNATURES.get(suffix)) and not _starts_with(path, sig):
        raise UnsupportedSource(f"{path.name}: not a valid {suffix} file (corrupt, or renamed from another format)")
    elif md := _markitdown():
        try:
            text = md.convert(str(path)).markdown
        except Exception as e:
            if suffix not in BUILTIN_EXTS:
                raise UnsupportedSource(f"{path.name}: conversion failed ({e})") from e
            text = _builtin(path)
    elif suffix in CONVERT_EXTS:
        raise UnsupportedSource(f"{path.name}: '{suffix}' files need MarkItDown: uv sync --extra convert")
    else:
        text = _builtin(path)

    if not text.strip():
        hint = " It may be a scanned PDF (image only); OCR it first." if suffix == ".pdf" else ""
        raise UnsupportedSource(f"{path.name}: no extractable text.{hint}")
    return text.strip()


def source_metadata(path: Path) -> dict[str, str]:
    """Title and author embedded in the file itself, when present. Title pages are often images,
    so this is more reliable than asking the model to infer a title from the text."""
    suffix = path.suffix.lower()
    meta: dict[str, str] = {}
    try:
        if suffix == ".pdf":
            from pypdf import PdfReader

            info = PdfReader(str(path)).metadata or {}
            meta = {"title": info.get("/Title") or "", "author": info.get("/Author") or ""}
        elif suffix in {".docx", ".pptx", ".xlsx"}:
            import zipfile

            core = zipfile.ZipFile(path).read("docProps/core.xml").decode("utf-8", errors="replace")
            for key, tag in (("title", "dc:title"), ("author", "dc:creator")):
                m = re.search(rf"<{tag}>(.*?)</{tag}>", core, re.S)
                meta[key] = m.group(1) if m else ""
    except Exception:  # missing library, no metadata, unreadable properties: fall back to the model
        return {}
    meta = {k: str(v).strip() for k, v in meta.items() if v and str(v).strip()}
    # Ignore placeholder titles that authoring tools leave behind.
    if re.fullmatch(r"(?i)(untitled.*|microsoft word.*|document\d*|presentation\d*|.*\.(docx?|pdf|indd))",
                    meta.get("title", "")):
        meta.pop("title")
    if re.fullmatch(r"(?i)(python-docx|python-pptx|openpyxl|microsoft office user|user|admin|author|owner)",
                    meta.get("author", "")):
        meta.pop("author")
    return meta


def _starts_with(path: Path, signature: bytes) -> bool:
    with path.open("rb") as fh:
        head = fh.read(1024)
    # PDFs may have junk before the header; the spec allows it within the first 1 KB.
    return signature in head if signature == b"%PDF" else head.startswith(signature)


def _builtin(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as e:
            raise UnsupportedSource(f"{path.name}: PDF support needs: uv sync --extra pdf (or --extra convert)") from e
        return "\n\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
    text = path.read_text(encoding="utf-8", errors="replace")
    text = re.sub(r"(?is)<(script|style).*?</\1>", "", text)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"[ \t]+", " ", text)

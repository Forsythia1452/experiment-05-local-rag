from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, asdict
from pathlib import Path


class DocumentError(ValueError):
    pass


@dataclass
class Chunk:
    id: str
    doc_id: str
    source: str
    text: str
    section: str = "正文"
    page: int | None = None

    def to_dict(self):
        return asdict(self)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def decode_text(data: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            pass
    raise DocumentError("文本编码无法识别，请转换为 UTF-8 或 GB18030")


def parse_document(path: str | Path) -> list[tuple[str, dict]]:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md", ".markdown"}:
        text = decode_text(path.read_bytes()).strip()
        if not text:
            raise DocumentError("文档为空，未写入索引")
        return [(text, {"source": path.name, "page": None})]
    if suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        pages = []
        for number, page in enumerate(reader.pages, 1):
            text = (page.extract_text() or "").strip()
            if text:
                pages.append((text, {"source": path.name, "page": number}))
        if not pages:
            raise DocumentError("PDF 未提取到文字，可能是扫描件，需要先进行 OCR")
        return pages
    raise DocumentError("仅支持 TXT、Markdown 和 PDF")


def _sections(text: str):
    heading = "正文"
    buffer: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            if buffer:
                yield heading, "\n".join(buffer)
                buffer = []
            continue
        if re.match(r"^#{1,6}\s+", line):
            if buffer:
                yield heading, "\n".join(buffer)
                buffer = []
            heading = re.sub(r"^#{1,6}\s+", "", line)
        else:
            buffer.append(line)
    if buffer:
        yield heading, "\n".join(buffer)


def chunk_text(text: str, target: int = 400, overlap: int = 80):
    if target <= overlap or target < 50:
        raise ValueError("target 必须大于 overlap 且至少为 50")
    for section, body in _sections(text):
        start = 0
        while start < len(body):
            end = min(start + target, len(body))
            if end < len(body):
                candidates = [body.rfind(mark, start + target // 2, end) for mark in "。！？\n"]
                boundary = max(candidates)
                if boundary >= 0:
                    end = boundary + 1
            part = body[start:end].strip()
            if part:
                yield section, part
            if end >= len(body):
                break
            start = max(start + 1, end - overlap)


def load_chunks(paths: list[str | Path], target: int = 400, overlap: int = 80):
    chunks: list[Chunk] = []
    seen: set[str] = set()
    skipped: list[dict] = []
    for item in paths:
        path = Path(item)
        data = path.read_bytes()
        doc_id = sha256_bytes(data)
        if doc_id in seen:
            skipped.append({"source": path.name, "reason": "重复文档"})
            continue
        seen.add(doc_id)
        try:
            units = parse_document(path)
        except DocumentError as exc:
            skipped.append({"source": path.name, "reason": str(exc)})
            continue
        sequence = 0
        for text, meta in units:
            for section, part in chunk_text(text, target, overlap):
                chunks.append(Chunk(f"{doc_id[:12]}-{sequence}", doc_id, meta["source"], part, section, meta["page"]))
                sequence += 1
    return chunks, skipped


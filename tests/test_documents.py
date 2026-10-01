from pathlib import Path
import pytest

from src.documents import DocumentError, chunk_text, decode_text, load_chunks, parse_document


def test_utf8_decode(): assert decode_text("中文".encode()) == "中文"
def test_gb_decode(): assert decode_text("中文".encode("gb18030")) == "中文"


def test_txt_parse(tmp_path):
    p = tmp_path / "a.txt"; p.write_text("有效内容", encoding="utf-8")
    assert parse_document(p)[0][0] == "有效内容"


def test_md_heading_chunk():
    chunks = list(chunk_text("# 标题\n这是正文内容。", 50, 10))
    assert chunks == [("标题", "这是正文内容。")]


def test_empty_rejected(tmp_path):
    p = tmp_path / "e.txt"; p.write_text("", encoding="utf-8")
    with pytest.raises(DocumentError, match="为空"): parse_document(p)


def test_unknown_type_rejected(tmp_path):
    p = tmp_path / "a.csv"; p.write_text("x", encoding="utf-8")
    with pytest.raises(DocumentError, match="仅支持"): parse_document(p)


def test_duplicate_skipped(tmp_path):
    a = tmp_path / "a.txt"; b = tmp_path / "b.txt"
    a.write_text("相同的有效文档内容", encoding="utf-8"); b.write_bytes(a.read_bytes())
    chunks, skipped = load_chunks([a, b])
    assert len(chunks) == 1 and skipped[0]["reason"] == "重复文档"


def test_invalid_chunk_parameters():
    with pytest.raises(ValueError): list(chunk_text("hello", 50, 50))


def test_long_text_overlaps():
    chunks = list(chunk_text("甲" * 120, 50, 10))
    assert len(chunks) == 3 and chunks[0][1][-10:] == chunks[1][1][:10]


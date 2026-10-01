from __future__ import annotations

from pathlib import Path
import shutil

import streamlit as st

from src.answering import answer
from src.documents import load_chunks
from src.indexing import LocalIndex, MODEL_ID

ROOT = Path(__file__).parent
UPLOADS = ROOT / "data" / "uploads"
INDEX_DIR = ROOT / "data" / "index"
KNOWLEDGE = ROOT / "knowledge"

st.set_page_config(page_title="本地知识问答", page_icon="📚", layout="wide")
st.title("📚 本地证据型知识问答")
st.caption("离线运行 · 来源可核对 · 证据不足会拒答")


def rebuild(paths):
    chunks, skipped = load_chunks(paths)
    LocalIndex().build(chunks).save(INDEX_DIR)
    st.cache_resource.clear()
    return len(chunks), skipped


@st.cache_resource
def get_index(stamp):
    return LocalIndex.load(INDEX_DIR)


with st.sidebar:
    st.header("知识库管理")
    files = st.file_uploader("上传文档", type=["txt", "md", "markdown", "pdf"], accept_multiple_files=True)
    if st.button("保存并重建索引", use_container_width=True, disabled=not files):
        UPLOADS.mkdir(parents=True, exist_ok=True)
        for file in files:
            safe_name = Path(file.name).name
            (UPLOADS / safe_name).write_bytes(file.getvalue())
        count, skipped = rebuild(list(UPLOADS.glob("*")))
        st.success(f"已建立 {count} 个文本块")
        for item in skipped:
            st.warning(f"{item['source']}：{item['reason']}")
    if st.button("使用示例知识库重建", use_container_width=True):
        count, _ = rebuild(list(KNOWLEDGE.glob("*")))
        st.success(f"示例库已建立：{count} 个文本块")
    uploaded = [p.name for p in UPLOADS.glob("*") if p.is_file()]
    st.write("已上传：", "、".join(uploaded) if uploaded else "暂无")
    if st.button("清空上传文档", use_container_width=True):
        for p in UPLOADS.glob("*"):
            if p.is_file() and p.name != ".gitkeep":
                p.unlink()
        st.success("已清空；请重新建立索引")

meta_path = INDEX_DIR / "meta.json"
if not meta_path.exists():
    st.info("尚未建立索引，请先在左侧使用示例知识库或上传文档。")
    st.stop()

index = get_index(meta_path.stat().st_mtime_ns)
c1, c2, c3 = st.columns(3)
c1.metric("文本块", len(index.chunks))
c2.metric("向量器", MODEL_ID)
c3.metric("运行模式", "CPU 离线")

question = st.text_input("请输入问题", value="实验五默认返回几条证据？")
with st.expander("检索设置"):
    top_k = st.slider("Top-k", 1, 5, 3)
    threshold = st.slider("拒答阈值", 0.0, 0.6, 0.16, 0.01)
    hybrid = st.toggle("混合检索（自主改进）", value=True)

if st.button("检索回答", type="primary", use_container_width=True):
    result = answer(index, question, top_k, threshold, hybrid)
    st.subheader("回答")
    (st.warning if result["refused"] else st.success)(result["answer"])
    st.caption(f"模式：{result['mode']}。回答为证据抽取，不是大模型生成。")
    if result.get("warning"):
        st.error(result["warning"])
    st.subheader("原始证据")
    for i, source in enumerate(result["sources"], 1):
        location = f"第 {source['page']} 页" if source.get("page") else source.get("section", "正文")
        with st.expander(f"[S{i}] {source['source']} · {location} · 得分 {source['score']:.3f}", expanded=i == 1):
            st.write(source["text"])


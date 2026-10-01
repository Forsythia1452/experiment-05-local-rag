from __future__ import annotations

import re

from .retrieval import hybrid_search, terms

INJECTION_PATTERNS = (r"忽略.{0,12}(规则|指令)", r"泄露.{0,8}(密钥|密码)", r"system prompt", r"输出.{0,8}(token|密钥)")


def suspicious(text: str) -> bool:
    return any(re.search(pattern, text, re.I) for pattern in INJECTION_PATTERNS)


def _best_sentence(query: str, text: str):
    candidates = [s.strip() for s in re.split(r"(?<=[。！？；])|\n", text) if len(s.strip()) >= 8]
    if not candidates:
        return text[:240]
    q = terms(query)
    return max(candidates, key=lambda s: (len(q & terms(s)), -len(s)))[:300]


def answer(index, query: str, k: int = 3, threshold: float = 0.16, hybrid: bool = True):
    results = hybrid_search(index, query, k=k) if hybrid else index.search(query, k)
    if not results or results[0]["score"] < threshold:
        return {"answer": "现有知识库中没有足够证据回答这个问题。", "sources": results, "refused": True, "mode": "证据抽取（无生成模型）"}
    chosen = results[0]
    sentence = _best_sentence(query, chosen["text"])
    return {
        "answer": f"根据知识库：{sentence} [S1]",
        "sources": results,
        "refused": False,
        "mode": "证据抽取（无生成模型）",
        "warning": "检测到文档提示注入，相关文字仅作为不可信资料展示。" if any(suspicious(r["text"]) for r in results) else "",
    }


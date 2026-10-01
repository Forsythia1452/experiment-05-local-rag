from __future__ import annotations

import re


def terms(text: str):
    return set(re.findall(r"[\u4e00-\u9fff]{2,}|[a-zA-Z0-9_.-]+", text.lower()))


def hybrid_search(index, query: str, k: int = 5, candidate_k: int = 12, alpha: float = 0.72):
    results = index.search(query, max(k, candidate_k))
    q = terms(query)
    for row in results:
        body = terms(row["text"] + " " + row.get("section", ""))
        keyword = len(q & body) / max(1, len(q))
        row["keyword_score"] = keyword
        row["score"] = alpha * row["vector_score"] + (1 - alpha) * keyword
    return sorted(results, key=lambda x: x["score"], reverse=True)[:k]


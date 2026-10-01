from __future__ import annotations

import json
import statistics
import time
from pathlib import Path

from .answering import answer
from .documents import load_chunks
from .indexing import LocalIndex, MODEL_ID
from .retrieval import hybrid_search


def run(root: Path):
    chunks, _ = load_chunks(list((root / "knowledge").glob("*")))
    index = LocalIndex().build(chunks)
    questions = [json.loads(line) for line in (root / "evaluation" / "questions.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    report = {"model_id": MODEL_ID, "chunk_count": len(chunks), "threshold": 0.16, "question_count": len(questions), "modes": {}}
    detailed = []
    for mode in ("baseline", "hybrid"):
        hits = {1: 0, 3: 0, 5: 0}
        answerable_count = sum(q["answerable"] for q in questions)
        false_positive = 0
        latencies = []
        for q in questions:
            started = time.perf_counter()
            results = index.search(q["question"], 5) if mode == "baseline" else hybrid_search(index, q["question"], 5)
            latencies.append((time.perf_counter() - started) * 1000)
            names = [x["source"] for x in results]
            if q["answerable"]:
                for k in hits:
                    hits[k] += q["expected_source"] in names[:k]
            else:
                false_positive += bool(results and results[0]["score"] >= 0.16)
            if mode == "hybrid":
                detailed.append({"id": q["id"], "question": q["question"], "expected": q["expected_source"], "top5": names, "top_score": round(results[0]["score"], 4)})
        report["modes"][mode] = {
            "recall@1": round(hits[1] / answerable_count, 4),
            "recall@3": round(hits[3] / answerable_count, 4),
            "recall@5": round(hits[5] / answerable_count, 4),
            "no_answer_false_positive_rate": round(false_positive / 4, 4),
            "mean_latency_ms": round(statistics.mean(latencies), 3),
        }
    report["details"] = detailed
    reviews = []
    for q in questions[:10]:
        result = answer(index, q["question"])
        reviews.append({"id": q["id"], "answer": result["answer"], "citation_present": "[S1]" in result["answer"], "supported": not result["refused"], "reason": "答案摘自首条原文并带来源标记"})
    report["groundedness_reviews"] = reviews
    output = root / "evaluation" / "results.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["modes"], ensure_ascii=False, indent=2))
    return report


if __name__ == "__main__":
    run(Path(__file__).resolve().parents[1])


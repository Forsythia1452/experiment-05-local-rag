import json
from pathlib import Path


def test_question_set_has_20():
    path = Path(__file__).parents[1] / "evaluation" / "questions.jsonl"
    rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    assert len(rows) == 20


def test_question_set_has_four_out_of_scope():
    path = Path(__file__).parents[1] / "evaluation" / "questions.jsonl"
    rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    assert sum(not x["answerable"] for x in rows) == 4


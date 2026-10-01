from __future__ import annotations

import json
import os
import pickle
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

from .documents import Chunk

MODEL_ID = "char-tfidf-2-4-v1"


class LocalIndex:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 4), min_df=1, sublinear_tf=True)
        self.vectors = None
        self.chunks: list[dict] = []
        self.faiss_index = None

    def build(self, chunks: list[Chunk]):
        if not chunks:
            raise ValueError("没有可索引的文本块")
        self.chunks = [c.to_dict() for c in chunks]
        sparse = self.vectorizer.fit_transform(c.text for c in chunks)
        self.vectors = normalize(sparse).astype("float32").toarray()
        try:
            import faiss
            self.faiss_index = faiss.IndexFlatIP(self.vectors.shape[1])
            self.faiss_index.add(self.vectors)
        except ImportError:
            self.faiss_index = None
        return self

    def search(self, query: str, k: int = 5):
        if self.vectors is None or not self.chunks:
            return []
        q = normalize(self.vectorizer.transform([query])).astype("float32").toarray()
        k = min(k, len(self.chunks))
        if self.faiss_index is not None:
            scores, ids = self.faiss_index.search(q, k)
            pairs = zip(ids[0], scores[0])
        else:
            scores = (self.vectors @ q[0]).astype(float)
            ids = np.argsort(-scores)[:k]
            pairs = ((int(i), float(scores[i])) for i in ids)
        return [{**self.chunks[int(i)], "vector_score": float(s), "score": float(s)} for i, s in pairs if int(i) >= 0]

    def save(self, directory: str | Path):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        payload = {"model_id": MODEL_ID, "count": len(self.chunks), "chunks": self.chunks}
        for name, data in (("meta.json", json.dumps(payload, ensure_ascii=False, indent=2).encode()),
                           ("vectorizer.pkl", pickle.dumps(self.vectorizer)),
                           ("vectors.npy", _npy_bytes(self.vectors))):
            tmp = directory / (name + ".tmp")
            tmp.write_bytes(data)
            os.replace(tmp, directory / name)

    @classmethod
    def load(cls, directory: str | Path):
        directory = Path(directory)
        obj = cls()
        meta = json.loads((directory / "meta.json").read_text(encoding="utf-8"))
        if meta.get("model_id") != MODEL_ID:
            raise ValueError("索引模型标识不匹配，请重建索引")
        obj.vectorizer = pickle.loads((directory / "vectorizer.pkl").read_bytes())
        obj.vectors = np.load(directory / "vectors.npy")
        obj.chunks = meta["chunks"]
        if len(obj.chunks) != len(obj.vectors) or meta["count"] != len(obj.chunks):
            raise ValueError("索引与元数据数量不一致")
        try:
            import faiss
            obj.faiss_index = faiss.IndexFlatIP(obj.vectors.shape[1])
            obj.faiss_index.add(obj.vectors)
        except ImportError:
            pass
        return obj


def _npy_bytes(array):
    import io
    buffer = io.BytesIO()
    np.save(buffer, array)
    return buffer.getvalue()


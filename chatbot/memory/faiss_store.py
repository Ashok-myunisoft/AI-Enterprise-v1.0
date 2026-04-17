import os
import pickle
import logging
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from config import FAISS_INDEX_PATH, EMBEDDING_MODEL

logger = logging.getLogger(__name__)

_model = None
_indexes: dict = {}   # tenant_id → (faiss.Index, list[str])
DIMS = 384            # all-MiniLM-L6-v2 output dims


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info("Loading embedding model: %s", EMBEDDING_MODEL)
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def _index_files(tenant_id: int):
    base = os.path.join(FAISS_INDEX_PATH, f"tenant_{tenant_id}")
    return base + ".index", base + ".pkl"


def _load(tenant_id: int):
    if tenant_id in _indexes:
        return _indexes[tenant_id]

    os.makedirs(FAISS_INDEX_PATH, exist_ok=True)
    idx_file, txt_file = _index_files(tenant_id)

    if os.path.exists(idx_file) and os.path.exists(txt_file):
        index = faiss.read_index(idx_file)
        with open(txt_file, "rb") as f:
            texts = pickle.load(f)
    else:
        index = faiss.IndexFlatIP(DIMS)
        texts = []

    _indexes[tenant_id] = (index, texts)
    return _indexes[tenant_id]


def _save(tenant_id: int):
    index, texts = _indexes[tenant_id]
    idx_file, txt_file = _index_files(tenant_id)
    faiss.write_index(index, idx_file)
    with open(txt_file, "wb") as f:
        pickle.dump(texts, f)


def add_text(tenant_id: int, text: str):
    model = _get_model()
    vec = model.encode([text], normalize_embeddings=True)
    index, texts = _load(tenant_id)
    index.add(np.array(vec, dtype=np.float32))
    texts.append(text)
    _indexes[tenant_id] = (index, texts)
    _save(tenant_id)


def search(tenant_id: int, query: str, top_k: int = 3) -> list:
    model = _get_model()
    index, texts = _load(tenant_id)

    if index.ntotal == 0:
        return []

    vec = model.encode([query], normalize_embeddings=True)
    k = min(top_k, index.ntotal)
    scores, indices = index.search(np.array(vec, dtype=np.float32), k)

    return [
        texts[i] for score, i in zip(scores[0], indices[0])
        if i >= 0 and score > 0.5
    ]

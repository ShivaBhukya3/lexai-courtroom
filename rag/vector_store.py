"""Legal vector store — brute-force cosine search (no FAISS required on free tier)."""

import pickle
from pathlib import Path
from loguru import logger
import numpy as np

from rag.legal_embedder import LegalEmbedder, EMBED_DIR

EMBED_DIR.mkdir(parents=True, exist_ok=True)
METADATA_PATH = EMBED_DIR / "index.pkl"
VECTORS_PATH  = EMBED_DIR / "vectors.npy"


class LegalVectorStore:
    """Cosine-similarity vector store backed by numpy (no FAISS dependency)."""

    def __init__(self):
        self._embedder  = LegalEmbedder()
        self._vectors: np.ndarray | None = None
        self._documents: list[dict] = []

    def build_index(self, documents: list[dict] | None = None) -> None:
        if documents is None:
            documents = self._embedder.load_legal_documents()
        if not documents:
            logger.error("No documents to index")
            return

        logger.info(f"Building index for {len(documents)} documents…")
        texts = [d.get("_text", "") for d in documents]
        vecs  = self._embedder.embed(texts)            # fits TF-IDF if needed

        # L2-normalise for cosine similarity via dot product
        norms         = np.linalg.norm(vecs, axis=1, keepdims=True)
        self._vectors = (vecs / np.maximum(norms, 1e-8)).astype(np.float32)
        self._documents = documents

        self._save()
        logger.info(f"Index built with {len(documents)} documents")

    def search(self, query: str, top_k: int = 8) -> list[dict]:
        if self._vectors is None and not self._load():
            logger.warning("Index not built — run build_index() first")
            return []

        qvec  = self._embedder.embed_single(query).reshape(1, -1).astype(np.float32)
        qnorm = np.linalg.norm(qvec)
        if qnorm > 1e-8:
            qvec /= qnorm

        scores      = (self._vectors @ qvec.T).squeeze()
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            doc = dict(self._documents[int(idx)])
            doc["relevance_score"] = float(scores[idx])
            results.append(doc)
        return results

    def is_built(self) -> bool:
        return self._vectors is not None or METADATA_PATH.exists()

    # ── Persistence ───────────────────────────────────────────────────────

    def _save(self) -> None:
        try:
            np.save(str(VECTORS_PATH), self._vectors)
            with open(METADATA_PATH, "wb") as f:
                pickle.dump(self._documents, f)
            self._embedder.save_tfidf_state()
            logger.info(f"Index saved to {EMBED_DIR}")
        except Exception as e:
            logger.error(f"Index save failed: {e}")

    def _load(self) -> bool:
        try:
            if not METADATA_PATH.exists() or not VECTORS_PATH.exists():
                return False
            with open(METADATA_PATH, "rb") as f:
                self._documents = pickle.load(f)
            self._vectors = np.load(str(VECTORS_PATH))
            logger.info(f"Index loaded: {len(self._documents)} documents")
            return True
        except Exception as e:
            logger.error(f"Index load failed: {e}")
            return False

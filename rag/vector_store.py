"""FAISS vector store for legal document retrieval."""

import json
import pickle
from pathlib import Path
from loguru import logger
import numpy as np

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("faiss-cpu not installed — using brute-force search fallback")

from rag.legal_embedder import LegalEmbedder, EMBED_DIR

EMBED_DIR.mkdir(parents=True, exist_ok=True)
INDEX_PATH = EMBED_DIR / "index.faiss"
METADATA_PATH = EMBED_DIR / "index.pkl"


class LegalVectorStore:
    """FAISS-backed vector store for legal documents."""

    def __init__(self):
        self._embedder = LegalEmbedder()
        self._index = None
        self._documents: list[dict] = []
        self._dimension = 384

    def build_index(self, documents: list[dict] | None = None) -> None:
        """Build FAISS index from legal documents."""
        if documents is None:
            documents = self._embedder.load_legal_documents()

        if not documents:
            logger.error("No documents to index")
            return

        logger.info(f"Building index for {len(documents)} documents...")
        texts = [d.get("_text", "") for d in documents]
        embeddings = self._embedder.embed(texts)

        if FAISS_AVAILABLE:
            self._index = faiss.IndexFlatIP(self._dimension)  # Inner product (cosine sim with normalized vecs)
            faiss.normalize_L2(embeddings)
            self._index.add(embeddings)
        else:
            # Fallback: store normalized embeddings for brute-force search
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            self._index = embeddings / np.maximum(norms, 1e-8)

        self._documents = documents
        self._save()
        logger.info(f"Index built with {len(documents)} documents")

    def search(self, query: str, top_k: int = 8) -> list[dict]:
        """Search for similar documents."""
        if self._index is None:
            if not self._load():
                logger.warning("Index not built — run build_index() first")
                return []

        query_vec = self._embedder.embed_single(query).reshape(1, -1)

        if FAISS_AVAILABLE:
            faiss.normalize_L2(query_vec)
            distances, indices = self._index.search(query_vec, min(top_k, len(self._documents)))
            results = []
            for score, idx in zip(distances[0], indices[0]):
                if idx < 0:
                    continue
                doc = dict(self._documents[idx])
                doc["relevance_score"] = float(score)
                results.append(doc)
        else:
            # Brute-force cosine similarity
            query_norm = query_vec / np.maximum(np.linalg.norm(query_vec), 1e-8)
            scores = (self._index @ query_norm.T).squeeze()
            top_indices = np.argsort(scores)[::-1][:top_k]
            results = []
            for idx in top_indices:
                doc = dict(self._documents[idx])
                doc["relevance_score"] = float(scores[idx])
                results.append(doc)

        return results

    def is_built(self) -> bool:
        return self._index is not None or INDEX_PATH.exists() or METADATA_PATH.exists()

    def _save(self) -> None:
        try:
            if FAISS_AVAILABLE and isinstance(self._index, faiss.Index):
                faiss.write_index(self._index, str(INDEX_PATH))
            else:
                with open(INDEX_PATH.with_suffix(".npy"), "wb") as f:
                    np.save(f, self._index)

            with open(METADATA_PATH, "wb") as f:
                pickle.dump(self._documents, f)
            logger.info(f"Index saved to {EMBED_DIR}")
        except Exception as e:
            logger.error(f"Index save failed: {e}")

    def _load(self) -> bool:
        try:
            meta_path = METADATA_PATH
            if not meta_path.exists():
                return False
            with open(meta_path, "rb") as f:
                self._documents = pickle.load(f)

            if FAISS_AVAILABLE and INDEX_PATH.exists():
                self._index = faiss.read_index(str(INDEX_PATH))
            elif INDEX_PATH.with_suffix(".npy").exists():
                self._index = np.load(str(INDEX_PATH.with_suffix(".npy")))
            else:
                return False

            logger.info(f"Index loaded: {len(self._documents)} documents")
            return True
        except Exception as e:
            logger.error(f"Index load failed: {e}")
            return False

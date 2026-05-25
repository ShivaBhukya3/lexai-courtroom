"""Embed legal documents using sentence-transformers."""

import json
from pathlib import Path
from typing import Any
from loguru import logger

try:
    from sentence_transformers import SentenceTransformer
    ST_AVAILABLE = True
except ImportError:
    ST_AVAILABLE = False

import numpy as np

BASE_DIR = Path(__file__).parent.parent
LEGAL_DB = BASE_DIR / "data" / "legal_database"
EMBED_DIR = BASE_DIR / "data" / "processed" / "embeddings" / "faiss_legal_index"


class LegalEmbedder:
    """Generate embeddings for legal documents."""

    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

    def __init__(self):
        self._model = None
        if ST_AVAILABLE:
            try:
                logger.info(f"Loading embedding model: {self.MODEL_NAME}")
                self._model = SentenceTransformer(self.MODEL_NAME)
                logger.info("Embedding model loaded")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
        else:
            logger.warning("sentence-transformers not installed — using random embeddings")

    def embed(self, texts: list[str]) -> np.ndarray:
        """Embed a list of texts."""
        if self._model:
            return self._model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        # Fallback: deterministic pseudo-embeddings based on text hash
        embeddings = []
        for text in texts:
            rng = np.random.default_rng(abs(hash(text[:50])) % (2**32))
            embeddings.append(rng.standard_normal(384).astype(np.float32))
        return np.array(embeddings, dtype=np.float32)

    def embed_single(self, text: str) -> np.ndarray:
        return self.embed([text])[0]

    def load_legal_documents(self) -> list[dict]:
        """Load all legal database JSON files."""
        documents = []
        json_files = list(LEGAL_DB.glob("*.json"))

        if not json_files:
            logger.warning(f"No JSON files found in {LEGAL_DB}. Run build_legal_database.py first.")
            return []

        for json_file in json_files:
            try:
                with open(json_file, encoding="utf-8") as f:
                    data = json.load(f)

                source = json_file.stem
                if isinstance(data, list):
                    for item in data:
                        item["_source"] = source
                        item["_text"] = self._item_to_text(item, source)
                        documents.append(item)
                else:
                    data["_source"] = source
                    data["_text"] = self._item_to_text(data, source)
                    documents.append(data)

            except Exception as e:
                logger.error(f"Failed to load {json_file}: {e}")

        logger.info(f"Loaded {len(documents)} legal documents from {len(json_files)} files")
        return documents

    def _item_to_text(self, item: dict, source: str) -> str:
        """Convert a legal item to searchable text."""
        if source == "ipc_sections" or source == "crpc_sections":
            return (
                f"{item.get('section', '')} — {item.get('title', '')}\n"
                f"{item.get('description', '')}\n"
                f"Keywords: {', '.join(item.get('keywords', []))}"
            )
        elif source in ("case_precedents", "supreme_court_judgments", "high_court_judgments"):
            return (
                f"{item.get('case_name', '')} [{item.get('citation', '')}]\n"
                f"Court: {item.get('court', '')} ({item.get('year', '')})\n"
                f"Facts: {item.get('facts', item.get('summary', ''))}\n"
                f"Held: {item.get('held', item.get('key_ratio', ''))}\n"
                f"Principle: {item.get('legal_principle', '')}\n"
                f"Keywords: {', '.join(item.get('keywords', []))}"
            )
        else:
            return json.dumps(item, ensure_ascii=False)[:500]

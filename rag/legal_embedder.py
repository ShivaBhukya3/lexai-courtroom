"""Embed legal documents — sentence-transformers when available, TF-IDF+LSA otherwise."""

import json
import pickle
from pathlib import Path
from loguru import logger

import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    ST_AVAILABLE = True
except ImportError:
    ST_AVAILABLE = False

BASE_DIR = Path(__file__).parent.parent
LEGAL_DB  = BASE_DIR / "data" / "legal_database"
EMBED_DIR = BASE_DIR / "data" / "processed" / "embeddings" / "faiss_legal_index"
TFIDF_SAVE_PATH = EMBED_DIR / "tfidf_state.pkl"

DIM = 256  # LSA components (padded to this size for brute-force search)


class LegalEmbedder:
    """Dense embeddings via sentence-transformers or TF-IDF + LSA fallback."""

    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

    def __init__(self):
        self._model   = None
        self._tfidf   = None
        self._svd     = None
        self._fitted  = False

        if ST_AVAILABLE:
            try:
                logger.info(f"Loading embedding model: {self.MODEL_NAME}")
                self._model = SentenceTransformer(self.MODEL_NAME)
                logger.info("Embedding model loaded")
            except Exception as e:
                logger.warning(f"SentenceTransformer failed: {e} — using TF-IDF+LSA")

        if not self._model:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.decomposition import TruncatedSVD
            self._tfidf = TfidfVectorizer(max_features=8000, ngram_range=(1, 2), sublinear_tf=True)
            self._svd   = TruncatedSVD(n_components=DIM, random_state=42)
            logger.info("Using TF-IDF + LSA embeddings (lightweight mode)")
            self._try_load_tfidf()

    # ── Public ────────────────────────────────────────────────────────────

    def embed(self, texts: list[str]) -> np.ndarray:
        if self._model:
            return self._model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        return self._tfidf_embed(texts, fit=not self._fitted)

    def embed_single(self, text: str) -> np.ndarray:
        return self.embed([text])[0]

    def save_tfidf_state(self) -> None:
        if self._tfidf is not None and self._fitted:
            EMBED_DIR.mkdir(parents=True, exist_ok=True)
            with open(TFIDF_SAVE_PATH, "wb") as f:
                pickle.dump({"tfidf": self._tfidf, "svd": self._svd}, f)
            logger.info("TF-IDF state saved")

    def load_legal_documents(self) -> list[dict]:
        documents  = []
        json_files = list(LEGAL_DB.glob("*.json"))
        if not json_files:
            logger.warning(f"No JSON files in {LEGAL_DB}. Run build_legal_database.py first.")
            return []
        for json_file in json_files:
            try:
                with open(json_file, encoding="utf-8") as f:
                    data = json.load(f)
                source = json_file.stem
                if isinstance(data, list):
                    for item in data:
                        item["_source"] = source
                        item["_text"]   = self._item_to_text(item, source)
                        documents.append(item)
                else:
                    data["_source"] = source
                    data["_text"]   = self._item_to_text(data, source)
                    documents.append(data)
            except Exception as e:
                logger.error(f"Failed to load {json_file}: {e}")
        logger.info(f"Loaded {len(documents)} legal documents from {len(json_files)} files")
        return documents

    # ── Internal ──────────────────────────────────────────────────────────

    def _tfidf_embed(self, texts: list[str], fit: bool = False) -> np.ndarray:
        if fit:
            matrix = self._tfidf.fit_transform(texts)
            self._svd.fit(matrix)
            self._fitted = True
            dense = self._svd.transform(matrix)
        else:
            matrix = self._tfidf.transform(texts)
            dense  = self._svd.transform(matrix)
        return dense.astype(np.float32)

    def _try_load_tfidf(self) -> None:
        if TFIDF_SAVE_PATH.exists():
            try:
                with open(TFIDF_SAVE_PATH, "rb") as f:
                    state = pickle.load(f)
                self._tfidf  = state["tfidf"]
                self._svd    = state["svd"]
                self._fitted = True
                logger.info("TF-IDF state loaded from disk")
            except Exception as e:
                logger.warning(f"Could not load TF-IDF state: {e}")

    def _item_to_text(self, item: dict, source: str) -> str:
        if source in ("ipc_sections", "crpc_sections"):
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
        return json.dumps(item, ensure_ascii=False)[:500]

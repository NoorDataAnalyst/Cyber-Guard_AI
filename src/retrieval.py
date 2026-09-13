"""
Retrieval Layer Module.
Manages three FAISS CPU vector indices using sentence-transformers (all-MiniLM-L6-v2):
1. Conversation Context Index (recent thread messages)
2. Curated Example Bank Index (precedent labeled cyberbullying examples)
3. Curated Policy & Law Corpus Index (PECA 2016, FIA Pakistan, platform safety rules)
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd

from src.config import (
    EXAMPLES_PATH,
    POLICY_PATH,
    INDEX_DIR,
    EMBEDDING_MODEL_NAME,
    RAG_TOP_K_EXAMPLES,
    RAG_TOP_K_POLICY,
    CONTEXT_HISTORY_N,
)
from src.preprocessing import clean_text

logger = logging.getLogger(__name__)


class EmbeddingEncoder:
    """Encoder wrapper for generating normalized dense sentence embeddings."""

    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        self.model_name = model_name
        self._model = None
        self.dimension = 384  # Default MiniLM embedding dimension
        self._init_encoder()

    def _init_encoder(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading sentence transformer '{self.model_name}'...")
            self._model = SentenceTransformer(self.model_name)
            if hasattr(self._model, "get_embedding_dimension"):
                self.dimension = self._model.get_embedding_dimension()
            elif hasattr(self._model, "get_sentence_embedding_dimension"):
                self.dimension = self._model.get_sentence_embedding_dimension()
            logger.info(f"Sentence transformer loaded with dimension {self.dimension}.")
        except Exception as e:
            logger.warning(f"Unable to load SentenceTransformer: {e}. Using TF-IDF/random dense fallback encoder.")
            self._model = None

    def encode(self, texts: List[str]) -> np.ndarray:
        """Encodes list of texts into L2-normalized float32 numpy embeddings."""
        cleaned_texts = [clean_text(t) if clean_text(t) else "empty" for t in texts]

        if self._model is not None:
            try:
                embeddings = self._model.encode(cleaned_texts, convert_to_numpy=True, normalize_embeddings=True)
                return embeddings.astype(np.float32)
            except Exception as e:
                logger.error(f"Encoding error with SentenceTransformer: {e}")

        # Deterministic Hash-based Fallback Embeddings if SentenceTransformer is offline
        embeddings = []
        for text in cleaned_texts:
            vec = np.zeros(self.dimension, dtype=np.float32)
            words = text.lower().split()
            for i, word in enumerate(words):
                idx = abs(hash(word)) % self.dimension
                vec[idx] += 1.0
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec /= norm
            embeddings.append(vec)

        return np.array(embeddings, dtype=np.float32)


class FAISSVectorStore:
    """Wrapper around FAISS IndexFlatIP (Inner Product on L2-normalized vectors = Cosine Similarity)."""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.index = None
        self.metadata: List[Dict[str, Any]] = []
        self._init_faiss()

    def _init_faiss(self) -> None:
        try:
            import faiss
            self.index = faiss.IndexFlatIP(self.dimension)
        except Exception as e:
            logger.warning(f"FAISS unavailable: {e}. Using numpy cosine similarity fallback.")
            self.index = None

    def add(self, embeddings: np.ndarray, metadata_items: List[Dict[str, Any]]) -> None:
        """Adds normalized embeddings and associated metadata items to index."""
        if embeddings.shape[0] != len(metadata_items):
            raise ValueError("Embeddings count must match metadata items count.")

        if self.index is not None:
            self.index.add(embeddings)
        self.metadata.extend(metadata_items)

    def search(self, query_vector: np.ndarray, top_k: int = 3) -> List[Dict[str, Any]]:
        """Searches index for top_k nearest items."""
        if len(self.metadata) == 0:
            return []

        top_k = min(top_k, len(self.metadata))

        if self.index is not None and self.index.ntotal > 0:
            distances, indices = self.index.search(query_vector, top_k)
            results = []
            for score, idx in zip(distances[0], indices[0]):
                if idx >= 0 and idx < len(self.metadata):
                    item = {k: v for k, v in self.metadata[idx].items() if not k.startswith("_")}
                    item["similarity_score"] = round(float(score), 4)
                    results.append(item)
            return results

        # Numpy fallback cosine search
        stored_vecs = np.array([m.get("_embedding", np.zeros(self.dimension)) for m in self.metadata])
        if len(stored_vecs) == 0:
            return []

        sims = np.dot(stored_vecs, query_vector.T).flatten()
        top_indices = np.argsort(sims)[::-1][:top_k]
        results = []
        for idx in top_indices:
            item = {k: v for k, v in self.metadata[idx].items() if not k.startswith("_")}
            item["similarity_score"] = round(float(sims[idx]), 4)
            results.append(item)
        return results


class RAGRetrievalManager:
    """Orchestrates FAISS indices for Context, Example Bank, and Policy Corpus."""

    def __init__(self):
        self.encoder = EmbeddingEncoder()
        self.example_store = FAISSVectorStore(self.encoder.dimension)
        self.policy_store = FAISSVectorStore(self.encoder.dimension)
        self.example_df: Optional[pd.DataFrame] = None
        self.policy_df: Optional[pd.DataFrame] = None

        self._build_example_bank_index()
        self._build_policy_corpus_index()

    def _build_example_bank_index(self) -> None:
        """Builds FAISS vector index from data/examples/example_bank.csv."""
        if not EXAMPLES_PATH.exists():
            logger.warning(f"Example bank file missing at {EXAMPLES_PATH}")
            return

        df = pd.read_csv(EXAMPLES_PATH)
        self.example_df = df
        texts = df["text"].tolist()
        embeddings = self.encoder.encode(texts)

        metadata = []
        for idx, row in df.iterrows():
            item = {
                "text": row["text"],
                "category": row["category"],
                "severity": row["severity"],
                "note": row.get("note", ""),
                "_embedding": embeddings[idx]
            }
            metadata.append(item)

        self.example_store = FAISSVectorStore(self.encoder.dimension)
        self.example_store.add(embeddings, metadata)
        logger.info(f"Indexed {len(metadata)} precedent examples in FAISS example store.")

    def _build_policy_corpus_index(self) -> None:
        """Builds FAISS vector index from data/policy_docs/policy_corpus.csv."""
        if not POLICY_PATH.exists():
            logger.warning(f"Policy corpus file missing at {POLICY_PATH}")
            return

        df = pd.read_csv(POLICY_PATH)
        self.policy_df = df
        texts = df["snippet"].tolist()
        embeddings = self.encoder.encode(texts)

        metadata = []
        for idx, row in df.iterrows():
            item = {
                "snippet": row["snippet"],
                "category_tags": row["category_tags"],
                "source": row["source"],
                "_embedding": embeddings[idx]
            }
            metadata.append(item)

        self.policy_store = FAISSVectorStore(self.encoder.dimension)
        self.policy_store.add(embeddings, metadata)
        logger.info(f"Indexed {len(metadata)} legal/policy snippets in FAISS policy store.")

    def retrieve_context(self, thread_messages: List[Dict[str, str]], n_recent: int = CONTEXT_HISTORY_N) -> List[Dict[str, str]]:
        """
        Retrieves the last N messages from the conversation thread as context.

        Args:
            thread_messages: List of message dicts [{'sender': ..., 'text': ..., 'timestamp': ...}]
            n_recent: Number of recent context messages to retrieve.

        Returns:
            List of recent context message dicts.
        """
        if not thread_messages:
            return []
        return thread_messages[-n_recent:]

    def retrieve_similar_examples(self, query_text: str, top_k: int = RAG_TOP_K_EXAMPLES) -> List[Dict[str, Any]]:
        """Retrieves top_k semantically similar precedent examples from the example bank."""
        if not query_text:
            return []
        query_vec = self.encoder.encode([query_text])
        return self.example_store.search(query_vec, top_k=top_k)

    def retrieve_policy_snippets(self, query_or_category: str, top_k: int = RAG_TOP_K_POLICY) -> List[Dict[str, Any]]:
        """Retrieves top_k relevant legal and policy snippets matching category or query."""
        if not query_or_category:
            return []
        
        # Check direct tag match first
        if self.policy_df is not None:
            tag_matches = []
            for idx, row in self.policy_df.iterrows():
                tags = [t.strip().lower() for t in str(row["category_tags"]).split(",")]
                if query_or_category.lower() in tags:
                    tag_matches.append({
                        "snippet": row["snippet"],
                        "category_tags": row["category_tags"],
                        "source": row["source"],
                        "similarity_score": 1.0
                    })
            if tag_matches:
                return tag_matches[:top_k]

        # Vector search fallback
        query_vec = self.encoder.encode([query_or_category])
        return self.policy_store.search(query_vec, top_k=top_k)

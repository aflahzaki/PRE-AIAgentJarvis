"""
Embeddings - Text similarity engine for J.A.R.V.I.S.

Supports multiple backends:
1. sentence-transformers (best quality, requires pip install sentence-transformers)
2. TF-IDF via scikit-learn (lightweight, no GPU needed) - DEFAULT
3. Keyword fallback (no dependencies)

Backend selection priority:
1. If EMBEDDING_MODEL=sentence_transformer in env, try sentence-transformers
2. Otherwise, use TF-IDF (scikit-learn)
3. Fall back to keyword matching if scikit-learn unavailable

Dependencies (all optional, graceful fallback):
    - scikit-learn: pip install scikit-learn (default)
    - sentence-transformers: pip install sentence-transformers (optional, ~90MB model)
    - numpy: pip install numpy (for sentence-transformers)
"""

import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Graceful import of scikit-learn
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning(
        "scikit-learn not installed. Embeddings will use keyword fallback. "
        "Install with: pip install scikit-learn"
    )

# Graceful import of numpy
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

# Graceful import of sentence-transformers
SENTENCE_TRANSFORMER_AVAILABLE = False
_sentence_transformer_model = None

# Only attempt sentence-transformers if explicitly configured
_embedding_model_env = os.environ.get("EMBEDDING_MODEL", "tfidf").lower()

if _embedding_model_env == "sentence_transformer":
    try:
        from sentence_transformers import SentenceTransformer
        SENTENCE_TRANSFORMER_AVAILABLE = True
        logger.info(
            "sentence-transformers available. Will use if configured."
        )
    except ImportError:
        SENTENCE_TRANSFORMER_AVAILABLE = False
        logger.info(
            "sentence-transformers not installed. "
            "Install with: pip install sentence-transformers"
        )


class SimpleEmbeddings:
    """Multi-backend text similarity engine.

    Supports sentence-transformers (high quality), TF-IDF (lightweight),
    and keyword fallback. Backend is selected automatically based on
    availability and EMBEDDING_MODEL environment variable.

    Attributes:
        engine_type: Backend type ('sentence_transformer', 'tfidf', 'keyword').
        vectorizer: TfidfVectorizer instance (for tfidf backend).
        is_fitted: Whether the engine has been fit on texts.
        use_sklearn: Whether scikit-learn is being used.
    """

    def __init__(self) -> None:
        """Initialize the embeddings engine.

        Backend selection:
        1. If EMBEDDING_MODEL=sentence_transformer and library available, use it
        2. If scikit-learn available, use TF-IDF
        3. Otherwise, use keyword fallback
        """
        self.is_fitted: bool = False
        self._texts: List[str] = []
        self._tfidf_matrix: Optional[Any] = None
        self._st_embeddings: Optional[Any] = None
        self._st_model: Optional[Any] = None

        # Determine backend
        embedding_model = os.environ.get("EMBEDDING_MODEL", "tfidf").lower()

        if embedding_model == "sentence_transformer" and SENTENCE_TRANSFORMER_AVAILABLE:
            self.engine_type = "sentence_transformer"
            self.use_sklearn = False
            self.vectorizer = None
            self._init_sentence_transformer()
        elif SKLEARN_AVAILABLE:
            self.engine_type = "tfidf"
            self.use_sklearn = True
            self.vectorizer = TfidfVectorizer(
                max_features=5000,
                stop_words="english",
                ngram_range=(1, 2),
                sublinear_tf=True,
            )
            logger.info("SimpleEmbeddings: Using TF-IDF (scikit-learn)")
        else:
            self.engine_type = "keyword"
            self.use_sklearn = False
            self.vectorizer = None
            logger.info("SimpleEmbeddings: Using keyword fallback")

    def _init_sentence_transformer(self) -> None:
        """Initialize the sentence-transformer model.

        Uses 'all-MiniLM-L6-v2' model which provides good quality
        at reasonable size (~90MB).
        """
        global _sentence_transformer_model

        try:
            if _sentence_transformer_model is None:
                from sentence_transformers import SentenceTransformer
                _sentence_transformer_model = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info(
                    "SimpleEmbeddings: Loaded sentence-transformer model "
                    "'all-MiniLM-L6-v2'"
                )
            self._st_model = _sentence_transformer_model
            logger.info("SimpleEmbeddings: Using sentence-transformers")
        except Exception as e:
            logger.error(
                "Failed to load sentence-transformer: %s. Falling back to TF-IDF.",
                str(e),
            )
            # Fallback to TF-IDF
            if SKLEARN_AVAILABLE:
                self.engine_type = "tfidf"
                self.use_sklearn = True
                self.vectorizer = TfidfVectorizer(
                    max_features=5000,
                    stop_words="english",
                    ngram_range=(1, 2),
                    sublinear_tf=True,
                )
            else:
                self.engine_type = "keyword"
                self.use_sklearn = False
                self.vectorizer = None

    def encode(self, texts: List[str]) -> Optional[Any]:
        """Encode texts to vectors.

        Uses the configured backend to produce vector representations
        of the input texts.

        Args:
            texts: List of text strings to encode.

        Returns:
            numpy array of embeddings (sentence_transformer),
            sparse matrix (tfidf), or None (keyword fallback).
        """
        if not texts:
            return None

        if self.engine_type == "sentence_transformer" and self._st_model is not None:
            try:
                embeddings = self._st_model.encode(texts, show_progress_bar=False)
                return embeddings
            except Exception as e:
                logger.error("Sentence-transformer encode error: %s", str(e))
                return None

        elif self.engine_type == "tfidf" and self.vectorizer is not None:
            try:
                matrix = self.vectorizer.fit_transform(texts)
                return matrix
            except Exception as e:
                logger.error("TF-IDF encode error: %s", str(e))
                return None

        return None

    def similarity_search(
        self, query: str, documents: List[str], top_k: int = 5
    ) -> List[Tuple[int, float]]:
        """Find most similar documents to query.

        A convenience method that fits on documents and returns
        the top-k most similar results.

        Args:
            query: Query text.
            documents: List of documents to search.
            top_k: Number of results to return.

        Returns:
            List of (index, similarity_score) tuples sorted by score.
        """
        return self.get_similar(query, texts=documents, top_k=top_k)

    def fit(self, texts: List[str]) -> None:
        """Fit the engine on a corpus of texts.

        Args:
            texts: List of text documents to build the model from.
        """
        if not texts:
            logger.warning("SimpleEmbeddings.fit(): Empty text list provided")
            return

        self._texts = texts

        if self.engine_type == "sentence_transformer" and self._st_model is not None:
            try:
                self._st_embeddings = self._st_model.encode(
                    texts, show_progress_bar=False
                )
                self.is_fitted = True
                logger.debug(
                    "SimpleEmbeddings: Encoded %d documents with sentence-transformer",
                    len(texts),
                )
            except Exception as e:
                logger.error("Sentence-transformer fit error: %s", str(e))
                self.is_fitted = False

        elif self.use_sklearn and self.vectorizer is not None:
            try:
                self._tfidf_matrix = self.vectorizer.fit_transform(texts)
                self.is_fitted = True
                logger.debug(
                    "SimpleEmbeddings: Fitted on %d documents", len(texts)
                )
            except Exception as e:
                logger.error("TF-IDF fit error: %s", str(e))
                self.is_fitted = False
        else:
            # Keyword fallback: just store texts
            self.is_fitted = True

    def get_similar(
        self, query: str, texts: Optional[List[str]] = None, top_k: int = 5
    ) -> List[Tuple[int, float]]:
        """Find texts most similar to the query.

        Args:
            query: Query text to find similar documents for.
            texts: Optional new list of texts to search. If provided,
                   refits the model. If None, uses previously fitted texts.
            top_k: Number of top results to return.

        Returns:
            List of (index, similarity_score) tuples, sorted by score descending.
            Index refers to position in the texts list.
        """
        if not query or not query.strip():
            return []

        # If new texts provided, refit
        if texts is not None:
            self.fit(texts)
        elif not self.is_fitted:
            logger.warning(
                "SimpleEmbeddings.get_similar(): Not fitted. Call fit() first."
            )
            return []

        if not self._texts:
            return []

        if self.engine_type == "sentence_transformer" and self._st_model is not None:
            return self._sentence_transformer_similarity(query, top_k)
        elif self.use_sklearn and self.vectorizer is not None and self._tfidf_matrix is not None:
            return self._sklearn_similarity(query, top_k)
        else:
            return self._keyword_similarity(query, top_k)

    def _sentence_transformer_similarity(
        self, query: str, top_k: int
    ) -> List[Tuple[int, float]]:
        """Compute similarity using sentence-transformers + cosine similarity.

        Args:
            query: Query text.
            top_k: Number of top results.

        Returns:
            List of (index, score) tuples.
        """
        try:
            if self._st_embeddings is None:
                return self._keyword_similarity(query, top_k)

            # Encode query
            query_embedding = self._st_model.encode(
                [query], show_progress_bar=False
            )

            # Compute cosine similarity
            from sklearn.metrics.pairwise import cosine_similarity as cos_sim
            similarities = cos_sim(query_embedding, self._st_embeddings).flatten()

            # Get top-k indices sorted by similarity
            indexed_scores = [
                (i, float(score))
                for i, score in enumerate(similarities)
                if score > 0.0
            ]
            indexed_scores.sort(key=lambda x: x[1], reverse=True)

            return indexed_scores[:top_k]

        except Exception as e:
            logger.error("Sentence-transformer similarity error: %s", str(e))
            return self._keyword_similarity(query, top_k)

    def _sklearn_similarity(
        self, query: str, top_k: int
    ) -> List[Tuple[int, float]]:
        """Compute similarity using TF-IDF + cosine similarity.

        Args:
            query: Query text.
            top_k: Number of top results.

        Returns:
            List of (index, score) tuples.
        """
        try:
            query_vector = self.vectorizer.transform([query])
            similarities = cosine_similarity(
                query_vector, self._tfidf_matrix
            ).flatten()

            # Get top-k indices sorted by similarity
            indexed_scores = [
                (i, float(score))
                for i, score in enumerate(similarities)
                if score > 0.0
            ]
            indexed_scores.sort(key=lambda x: x[1], reverse=True)

            return indexed_scores[:top_k]

        except Exception as e:
            logger.error("Sklearn similarity error: %s", str(e))
            # Fallback to keyword matching on error
            return self._keyword_similarity(query, top_k)

    def _keyword_similarity(
        self, query: str, top_k: int
    ) -> List[Tuple[int, float]]:
        """Compute similarity using simple keyword overlap.

        Uses Jaccard-like similarity based on word overlap between
        query and each document.

        Args:
            query: Query text.
            top_k: Number of top results.

        Returns:
            List of (index, score) tuples.
        """
        query_words = set(self._tokenize(query.lower()))

        if not query_words:
            return []

        scores = []
        for i, text in enumerate(self._texts):
            text_words = set(self._tokenize(text.lower()))
            if not text_words:
                continue

            # Jaccard similarity
            intersection = query_words & text_words
            union = query_words | text_words

            if union:
                score = len(intersection) / len(union)
            else:
                score = 0.0

            if score > 0.0:
                scores.append((i, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Simple tokenization: split on non-alphanumeric characters.

        Args:
            text: Text to tokenize.

        Returns:
            List of word tokens.
        """
        return [
            word for word in re.split(r"\W+", text)
            if word and len(word) > 1
        ]

    def __repr__(self) -> str:
        return "SimpleEmbeddings(backend='{}', fitted={}, docs={})".format(
            self.engine_type,
            self.is_fitted,
            len(self._texts),
        )

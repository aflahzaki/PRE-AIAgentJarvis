"""
Embeddings - Simple TF-IDF based text similarity for J.A.R.V.I.S.

Uses scikit-learn's TfidfVectorizer and cosine_similarity for lightweight
semantic search within the knowledge base. Falls back to keyword-based
matching when scikit-learn is unavailable.

No external API calls or GPU required - runs entirely on CPU.

Dependencies:
    - scikit-learn (optional): pip install scikit-learn
"""

import logging
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


class SimpleEmbeddings:
    """TF-IDF based text similarity engine.

    Provides lightweight semantic search using TF-IDF vectorization
    and cosine similarity. Falls back to simple keyword matching
    when scikit-learn is unavailable.

    Attributes:
        vectorizer: TfidfVectorizer instance (None if sklearn unavailable).
        is_fitted: Whether the vectorizer has been fit on texts.
        use_sklearn: Whether scikit-learn is being used.
    """

    def __init__(self) -> None:
        """Initialize the embeddings engine."""
        self.use_sklearn: bool = SKLEARN_AVAILABLE
        self.is_fitted: bool = False
        self._texts: List[str] = []
        self._tfidf_matrix: Optional[Any] = None

        if self.use_sklearn:
            self.vectorizer = TfidfVectorizer(
                max_features=5000,
                stop_words="english",
                ngram_range=(1, 2),
                sublinear_tf=True,
            )
            logger.info("SimpleEmbeddings: Using TF-IDF (scikit-learn)")
        else:
            self.vectorizer = None
            logger.info("SimpleEmbeddings: Using keyword fallback")

    def fit(self, texts: List[str]) -> None:
        """Fit the vectorizer on a corpus of texts.

        Args:
            texts: List of text documents to build the TF-IDF model from.
        """
        if not texts:
            logger.warning("SimpleEmbeddings.fit(): Empty text list provided")
            return

        self._texts = texts

        if self.use_sklearn and self.vectorizer is not None:
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

        if self.use_sklearn and self.vectorizer is not None and self._tfidf_matrix is not None:
            return self._sklearn_similarity(query, top_k)
        else:
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
            "sklearn" if self.use_sklearn else "keyword",
            self.is_fitted,
            len(self._texts),
        )

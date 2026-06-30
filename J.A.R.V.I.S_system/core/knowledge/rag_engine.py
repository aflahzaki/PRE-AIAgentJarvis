"""
RAG Engine - Retrieval-Augmented Generation for J.A.R.V.I.S.

Combines knowledge base search with context injection into LLM prompts.
Retrieves relevant knowledge entries and formats them as context for
the LLM to generate informed responses.

Features:
- Combined keyword + semantic similarity search
- Recency boost for newer entries
- Configurable top-k retrieval
- Context formatting for LLM prompt injection
- Full RAG pipeline: retrieve -> build context -> generate

Dependencies:
    - core.knowledge.knowledge_base (KnowledgeBase)
    - core.knowledge.embeddings (SimpleEmbeddings)
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_TOP_K = 5
DEFAULT_RAG_ENABLED = True


def _get_rag_config() -> Dict[str, Any]:
    """Load RAG configuration from environment variables.

    Returns:
        Dict with 'enabled', 'top_k' keys.
    """
    enabled_str = os.environ.get("RAG_ENABLED", "true").lower()
    enabled = enabled_str in ("true", "1", "yes")

    try:
        top_k = int(os.environ.get("RAG_TOP_K", str(DEFAULT_TOP_K)))
    except (ValueError, TypeError):
        top_k = DEFAULT_TOP_K

    return {"enabled": enabled, "top_k": top_k}


class RAGEngine:
    """Retrieval-Augmented Generation engine.

    Combines knowledge base search with context injection into LLM prompts.
    Retrieves the most relevant knowledge entries for a given query and
    formats them into a context block that can be prepended to messages.

    Attributes:
        kb: KnowledgeBase instance for storage and search.
        embeddings: SimpleEmbeddings instance for similarity search.
        top_k: Number of results to retrieve.
        enabled: Whether RAG is active.
    """

    def __init__(self, knowledge_base=None, embeddings=None) -> None:
        """Initialize the RAG engine.

        Args:
            knowledge_base: KnowledgeBase instance. If None, creates one.
            embeddings: SimpleEmbeddings instance. If None, uses KB's embeddings.
        """
        config = _get_rag_config()
        self.enabled = config["enabled"]
        self.top_k = config["top_k"]

        # Initialize knowledge base
        if knowledge_base is not None:
            self.kb = knowledge_base
        else:
            try:
                from core.knowledge.knowledge_base import KnowledgeBase
                self.kb = KnowledgeBase()
            except Exception as e:
                logger.error("RAGEngine: Failed to init KnowledgeBase: %s", str(e))
                self.kb = None

        # Initialize embeddings
        if embeddings is not None:
            self.embeddings = embeddings
        elif self.kb is not None:
            self.embeddings = self.kb.embeddings
        else:
            try:
                from core.knowledge.embeddings import SimpleEmbeddings
                self.embeddings = SimpleEmbeddings()
            except Exception as e:
                logger.error("RAGEngine: Failed to init embeddings: %s", str(e))
                self.embeddings = None

        logger.info(
            "RAGEngine initialized. enabled=%s, top_k=%d, kb_available=%s",
            self.enabled, self.top_k, self.kb is not None and self.kb.is_available,
        )

    def retrieve_context(
        self, query: str, top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve most relevant knowledge entries for a query.

        Combines:
        1. Keyword search (SQL LIKE)
        2. Semantic similarity (TF-IDF or sentence-transformers)
        3. Recency boost (newer entries slightly preferred)

        Args:
            query: User query to find relevant context for.
            top_k: Number of results to return. Defaults to self.top_k.

        Returns:
            List of dicts with keys: id, title, content, category,
            relevance_score, source_type.
        """
        if not self.enabled:
            return []

        if not query or not query.strip():
            return []

        if self.kb is None or not self.kb.is_available:
            logger.debug("RAGEngine: KB not available, skipping retrieval.")
            return []

        k = top_k if top_k is not None else self.top_k

        try:
            # Use KnowledgeBase search which already combines keyword + semantic
            search_result = self.kb.search(query, limit=k * 2)

            if not search_result.get("success"):
                logger.debug("RAGEngine: Search failed: %s", search_result.get("error"))
                return []

            results = search_result.get("results", [])

            # Apply recency boost and re-rank
            scored_results = []
            for item in results:
                # Base score from search
                base_score = item.get("similarity_score", 0.5)

                # Recency boost: newer entries get a small score boost
                recency_boost = self._compute_recency_boost(
                    item.get("updated_at") or item.get("created_at")
                )

                final_score = base_score + recency_boost

                scored_results.append({
                    "id": item.get("id"),
                    "title": item.get("title", ""),
                    "content": item.get("content", ""),
                    "category": item.get("category", ""),
                    "tags": item.get("tags", ""),
                    "relevance_score": round(final_score, 4),
                    "source_type": item.get("match_source", "combined"),
                })

            # Sort by relevance score descending
            scored_results.sort(key=lambda x: x["relevance_score"], reverse=True)

            return scored_results[:k]

        except Exception as e:
            logger.error("RAGEngine.retrieve_context error: %s", str(e))
            return []

    def build_context_prompt(
        self, query: str, retrieved_docs: Optional[List[Dict]] = None
    ) -> str:
        """Format retrieved documents into a context section for LLM.

        Builds a formatted context block that can be injected into the
        system prompt or prepended to user messages.

        Args:
            query: Original user query.
            retrieved_docs: Pre-retrieved documents. If None, retrieves them.

        Returns:
            Formatted context string, or empty string if no relevant docs.
        """
        if not self.enabled:
            return ""

        if retrieved_docs is None:
            retrieved_docs = self.retrieve_context(query)

        if not retrieved_docs:
            return ""

        # Build context block
        lines = ["[CONTEXT FROM KNOWLEDGE BASE]"]

        for i, doc in enumerate(retrieved_docs, 1):
            category = doc.get("category", "general")
            score = doc.get("relevance_score", 0.0)
            title = doc.get("title", "Untitled")
            content = doc.get("content", "")

            # Truncate content to keep context manageable
            if len(content) > 500:
                content = content[:500] + "..."

            lines.append(
                "Source {} - {} (category: {}, relevance: {:.2f}):".format(
                    i, title, category, score
                )
            )
            lines.append(content)
            lines.append("")

        lines.append("[END CONTEXT]")

        return "\n".join(lines)

    def query_with_rag(
        self, user_query: str, provider=None, model: Optional[str] = None
    ) -> Optional[str]:
        """Full RAG pipeline: retrieve context, build prompt, generate answer.

        This is a convenience method that performs the full RAG pipeline.
        For integration with the Orchestrator, use retrieve_context() and
        build_context_prompt() separately.

        Args:
            user_query: The user's question.
            provider: LLM provider instance with chat_completion method.
            model: Model name to use for generation.

        Returns:
            Generated response string, or None if RAG is disabled or fails.
        """
        if not self.enabled:
            return None

        if provider is None or model is None:
            logger.debug("RAGEngine: Provider or model not provided for full pipeline.")
            return None

        # Step 1: Retrieve relevant context
        retrieved_docs = self.retrieve_context(user_query)

        if not retrieved_docs:
            return None

        # Step 2: Build context prompt
        context_block = self.build_context_prompt(user_query, retrieved_docs)

        if not context_block:
            return None

        # Step 3: Generate answer with context
        system_prompt = (
            "You are J.A.R.V.I.S, a helpful AI assistant. "
            "Use the following knowledge base context to help answer the "
            "user's question. If the context is not relevant, ignore it "
            "and answer based on your general knowledge.\n\n{}"
        ).format(context_block)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query},
        ]

        try:
            response = provider.chat_completion(
                messages=messages,
                model=model,
                temperature=0.7,
                max_tokens=1024,
            )

            if response.success:
                return response.content
            else:
                logger.warning("RAGEngine: LLM call failed: %s", response.error)
                return None

        except Exception as e:
            logger.error("RAGEngine.query_with_rag error: %s", str(e))
            return None

    @staticmethod
    def _compute_recency_boost(date_str: Optional[str]) -> float:
        """Compute a recency boost score for a knowledge entry.

        Newer entries receive a small boost (max 0.1) to slightly
        prefer more recent information when relevance scores are close.

        Args:
            date_str: ISO date string of the entry's last update.

        Returns:
            Float boost value between 0.0 and 0.1.
        """
        if not date_str:
            return 0.0

        try:
            # Parse various datetime formats
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
                try:
                    entry_date = datetime.strptime(date_str.split(".")[0], fmt.split(".")[0])
                    break
                except ValueError:
                    continue
            else:
                return 0.0

            # Calculate days since entry was updated
            days_old = (datetime.now() - entry_date).days

            # Boost: max 0.1 for entries from today, decaying over 30 days
            if days_old <= 0:
                return 0.1
            elif days_old >= 30:
                return 0.0
            else:
                return 0.1 * (1.0 - days_old / 30.0)

        except Exception:
            return 0.0

    def __repr__(self) -> str:
        return "RAGEngine(enabled={}, top_k={}, kb_available={})".format(
            self.enabled, self.top_k,
            self.kb is not None and self.kb.is_available,
        )

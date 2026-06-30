"""
Knowledge - Knowledge base and semantic search for J.A.R.V.I.S system.

Available modules:
- SimpleEmbeddings: TF-IDF based text similarity (scikit-learn, CPU-only)
- KnowledgeBase: CRUD + semantic search using DatabaseManager + embeddings
"""

from core.knowledge.embeddings import SimpleEmbeddings
from core.knowledge.knowledge_base import KnowledgeBase

__all__ = [
    "SimpleEmbeddings",
    "KnowledgeBase",
]

"""
Knowledge - Knowledge base, semantic search, and RAG for J.A.R.V.I.S system.

Available modules:
- SimpleEmbeddings: Multi-backend text similarity (sentence-transformers/TF-IDF/keyword)
- KnowledgeBase: CRUD + semantic search using DatabaseManager + embeddings
- DocumentLoader: Multi-format file parser for knowledge ingestion
- RAGEngine: Retrieval-Augmented Generation for context injection
"""

from core.knowledge.embeddings import SimpleEmbeddings
from core.knowledge.knowledge_base import KnowledgeBase
from core.knowledge.document_loader import DocumentLoader
from core.knowledge.rag_engine import RAGEngine

__all__ = [
    "SimpleEmbeddings",
    "KnowledgeBase",
    "DocumentLoader",
    "RAGEngine",
]

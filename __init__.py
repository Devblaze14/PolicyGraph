"""
Core package for the Policy-Aware Graph-Enhanced RAG system for government schemes.

This package is organized into submodules:
- ingestion: document loading, parsing, and chunking
- kg: knowledge-graph schema and store
- retrieval: vector store and hybrid retrieval
- eligibility: eligibility rule representation and reasoning
- api: FastAPI-based serving layer
- ui: Streamlit-based exploration and demo
"""

__all__ = ["config"]


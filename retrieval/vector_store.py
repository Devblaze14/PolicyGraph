from __future__ import annotations

import os
import pickle
from pathlib import Path
from typing import List, Dict, Any

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

from config import config
from logging_utils import logger


class FAISSVectorStore:
    """
    Production-ready hybrid vector store using FAISS, BM25, and LangChain HuggingFaceEmbeddings.
    """

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or config.model_name
        logger.info(f"Initializing embedding model: {self.model_name}")
        self.embeddings = HuggingFaceEmbeddings(model_name=self.model_name)
        self.vector_store: FAISS | None = None
        self.bm25_retriever: BM25Retriever | None = None
        self.index_path = config.paths.data_indices / "faiss_index"
        self.bm25_path = config.paths.data_indices / "bm25.pkl"
        self.all_docs: List[Document] = []

    def add_documents(self, documents: List[Document]) -> None:
        if not documents:
            return
        logger.info(f"Adding {len(documents)} documents to FAISS & BM25 index.")
        self.all_docs.extend(documents)
        
        # Add to FAISS
        if self.vector_store is None:
            self.vector_store = FAISS.from_documents(documents, self.embeddings)
        else:
            self.vector_store.add_documents(documents)
            
        # Add to BM25
        self.bm25_retriever = BM25Retriever.from_documents(self.all_docs)

    def load_index(self) -> None:
        # Load FAISS
        if self.index_path.exists() and (self.index_path / "index.faiss").exists():
            logger.info(f"Loading local FAISS index from {self.index_path}")
            self.vector_store = FAISS.load_local(str(self.index_path), self.embeddings, allow_dangerous_deserialization=True)
        else:
            logger.warning(f"FAISS index not found at {self.index_path}. It will be empty.")
            
        # Load BM25
        if self.bm25_path.exists():
            logger.info(f"Loading local BM25 index from {self.bm25_path}")
            with self.bm25_path.open("rb") as f:
                self.bm25_retriever = pickle.load(f)

    def save_index(self) -> None:
        # Save FAISS
        if self.vector_store is not None:
            logger.info(f"Saving FAISS index to {self.index_path}")
            self.vector_store.save_local(str(self.index_path))
            
        # Save BM25
        if self.bm25_retriever is not None:
            logger.info(f"Saving BM25 index to {self.bm25_path}")
            with self.bm25_path.open("wb") as f:
                pickle.dump(self.bm25_retriever, f)

    def similarity_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        if self.vector_store is None and self.bm25_retriever is None:
            return []
            
        def reciprocal_rank_fusion(faiss_results, bm25_results, k=60):
            fusion_scores = {}
            for rank, (doc, score) in enumerate(faiss_results):
                doc_id = doc.page_content
                fusion_scores[doc_id] = fusion_scores.get(doc_id, {"metadata": doc.metadata, "score": 0})
                fusion_scores[doc_id]["score"] += 1 / (rank + k)
                
            for rank, doc in enumerate(bm25_results):
                doc_id = doc.page_content
                fusion_scores[doc_id] = fusion_scores.get(doc_id, {"metadata": doc.metadata, "score": 0})
                fusion_scores[doc_id]["score"] += 1 / (rank + k)
                
            sorted_docs = sorted(fusion_scores.items(), key=lambda x: x[1]["score"], reverse=True)
            return sorted_docs

        if self.vector_store and self.bm25_retriever:
            faiss_res = self.vector_store.similarity_search_with_score(query, k=k)
            self.bm25_retriever.k = k
            bm25_res = self.bm25_retriever.invoke(query)
            
            fused = reciprocal_rank_fusion(faiss_res, bm25_res)
            
            ret = []
            for doc_text, info in fused[:k]:
                ret.append({
                    "score": info["score"], 
                    "text": doc_text,
                    "metadata": info["metadata"]
                })
            return ret
            
        elif self.vector_store:
            # Fallback to pure FAISS
            results = self.vector_store.similarity_search_with_score(query, k=k)
            ret = []
            for doc, score in results:
                ret.append({
                    "score": float(score),
                    "text": doc.page_content,
                    "metadata": doc.metadata
                })
            return ret

__all__ = ["FAISSVectorStore", "Document"]

"""
Hybrid Retriever Module
Combines dense (semantic) and sparse (keyword) retrieval
"""

import numpy as np
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from sklearn.feature_extraction.text import TfidfVectorizer

from .dense_retriever import DenseRetriever, RetrievalResult


@dataclass
class HybridResult:
    """Result from hybrid retrieval"""
    chunk_id: str
    fund_name: str
    text: str
    dense_score: float
    sparse_score: float
    combined_score: float
    metadata: Dict[str, Any]
    source_url: str


class HybridRetriever:
    """
    Hybrid retriever combining dense and sparse retrieval
    - Dense: Semantic similarity using embeddings
    - Sparse: Keyword matching using TF-IDF
    """
    
    def __init__(self, 
                 dense_retriever: Optional[DenseRetriever] = None,
                 alpha: float = 0.7):
        """
        Initialize hybrid retriever
        
        Args:
            dense_retriever: DenseRetriever instance
            alpha: Weight for dense score (1-alpha for sparse)
        """
        self.dense_retriever = dense_retriever or DenseRetriever()
        self.alpha = alpha
        
        # Build sparse index
        self.tfidf = TfidfVectorizer(
            lowercase=True,
            stop_words='english',
            max_features=5000,
            ngram_range=(1, 2)
        )
        self.sparse_matrix = None
        self._build_sparse_index()
    
    def _build_sparse_index(self):
        """Build TF-IDF sparse index from metadata"""
        print("Building sparse (TF-IDF) index...")
        
        # Extract texts from metadata
        texts = []
        for meta in self.dense_retriever.metadata:
            # Combine text and metadata for better keyword matching
            text_parts = [
                meta['text'],
                meta['fund_name'],
                meta['metadata'].get('category', ''),
                meta['metadata'].get('amc', '')
            ]
            texts.append(' '.join(text_parts))
        
        # Fit TF-IDF
        self.sparse_matrix = self.tfidf.fit_transform(texts)
        print(f"✓ Built sparse index with {len(self.tfidf.vocabulary_)} terms")
    
    def retrieve(self,
                 query_embedding: np.ndarray,
                 query_text: str,
                 top_k: int = 5,
                 filters: Optional[Dict[str, Any]] = None) -> List[HybridResult]:
        """
        Hybrid retrieval combining dense and sparse scores
        
        Args:
            query_embedding: Dense query vector
            query_text: Raw query text for sparse retrieval
            top_k: Number of results
            filters: Optional metadata filters
            
        Returns:
            List of HybridResult objects
        """
        # Dense retrieval - get more candidates for reranking
        dense_results = self.dense_retriever.retrieve(
            query_embedding, 
            top_k=top_k * 3,
            filters=filters
        )
        
        # Sparse retrieval
        sparse_scores = self._sparse_retrieve(query_text)
        
        # Combine scores
        combined_results = self._combine_scores(
            dense_results, 
            sparse_scores,
            top_k
        )
        
        return combined_results
    
    def _sparse_retrieve(self, query_text: str) -> Dict[str, float]:
        """
        Perform sparse retrieval using TF-IDF
        
        Returns:
            Dictionary mapping chunk_id to sparse score
        """
        # Transform query
        query_vec = self.tfidf.transform([query_text.lower()])
        
        # Compute cosine similarity
        from sklearn.metrics.pairwise import cosine_similarity
        similarities = cosine_similarity(query_vec, self.sparse_matrix).flatten()
        
        # Map to chunk_ids
        scores = {}
        for i, meta in enumerate(self.dense_retriever.metadata):
            scores[meta['chunk_id']] = float(similarities[i])
        
        return scores
    
    def _combine_scores(self,
                       dense_results: List[RetrievalResult],
                       sparse_scores: Dict[str, float],
                       top_k: int) -> List[HybridResult]:
        """
        Combine dense and sparse scores
        
        Uses Reciprocal Rank Fusion (RRF) style combination
        """
        # Create lookup for dense scores
        dense_scores = {r.chunk_id: r.score for r in dense_results}
        
        # Get all candidate chunk_ids
        all_chunk_ids = set(dense_scores.keys()) | set(sparse_scores.keys())
        
        # Combine scores
        combined = []
        for chunk_id in all_chunk_ids:
            dense_score = dense_scores.get(chunk_id, 0.0)
            sparse_score = sparse_scores.get(chunk_id, 0.0)
            
            # Weighted combination
            combined_score = (self.alpha * dense_score + 
                            (1 - self.alpha) * sparse_score)
            
            # Get metadata from dense retriever
            meta = self._get_metadata(chunk_id)
            
            combined.append(HybridResult(
                chunk_id=chunk_id,
                fund_name=meta['fund_name'],
                text=meta['text'],
                dense_score=dense_score,
                sparse_score=sparse_score,
                combined_score=combined_score,
                metadata=meta['metadata'],
                source_url=meta['source_url']
            ))
        
        # Sort by combined score and return top_k
        combined.sort(key=lambda x: x.combined_score, reverse=True)
        return combined[:top_k]
    
    def _get_metadata(self, chunk_id: str) -> Dict:
        """Get metadata for a chunk_id"""
        for meta in self.dense_retriever.metadata:
            if meta['chunk_id'] == chunk_id:
                return meta
        return {}
    
    def retrieve_with_reranking(self,
                                query_embedding: np.ndarray,
                                query_text: str,
                                top_k: int = 5,
                                filters: Optional[Dict[str, Any]] = None,
                                rerank_top_k: int = 20) -> List[HybridResult]:
        """
        Retrieve with additional cross-encoder style reranking
        
        This is a simplified version that boosts exact matches
        """
        # Get initial results
        results = self.retrieve(
            query_embedding,
            query_text,
            top_k=rerank_top_k,
            filters=filters
        )
        
        # Simple reranking: boost exact fund name matches
        query_lower = query_text.lower()
        for r in results:
            # Boost if query contains fund name
            if r.fund_name.lower() in query_lower:
                r.combined_score *= 1.2
            
            # Boost if query contains category
            category = r.metadata.get('category', '').lower()
            if category and category in query_lower:
                r.combined_score *= 1.1
        
        # Re-sort and return top_k
        results.sort(key=lambda x: x.combined_score, reverse=True)
        return results[:top_k]


if __name__ == "__main__":
    # Test hybrid retriever
    print("Testing Hybrid Retriever")
    print("=" * 70)
    
    try:
        retriever = HybridRetriever()
        
        # Test with random embedding and sample query
        query_text = "ELSS tax saver fund with low expense ratio"
        query_emb = np.random.randn(384)
        query_emb = query_emb / np.linalg.norm(query_emb)
        
        print(f"\nQuery: {query_text}")
        print("\nResults:")
        
        results = retriever.retrieve(query_emb, query_text, top_k=5)
        
        for i, r in enumerate(results, 1):
            print(f"\n{i}. {r.fund_name}")
            print(f"   Combined: {r.combined_score:.4f} "
                  f"(Dense: {r.dense_score:.4f}, Sparse: {r.sparse_score:.4f})")
            print(f"   Text: {r.text[:80]}...")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

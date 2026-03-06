"""
Dense Retriever Module
Performs semantic search using vector similarity
"""

import numpy as np
import json
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RetrievalResult:
    """Single retrieval result"""
    chunk_id: str
    fund_name: str
    text: str
    score: float
    metadata: Dict[str, Any]
    source_url: str


class DenseRetriever:
    """
    Dense retriever for semantic search
    Uses cosine similarity on pre-computed embeddings
    """
    
    def __init__(self, 
                 embeddings_path: str = "../phase2_embedding_indexing/data/embeddings/fund_embeddings.npy",
                 metadata_path: str = "../phase2_embedding_indexing/data/embeddings/fund_embeddings_metadata.json"):
        """
        Initialize retriever with embeddings and metadata
        
        Args:
            embeddings_path: Path to .npy file with embeddings
            metadata_path: Path to JSON file with metadata
        """
        self.embeddings = None
        self.metadata = []
        self.dimension = None
        
        # Load data
        self._load_data(embeddings_path, metadata_path)
    
    def _load_data(self, embeddings_path: str, metadata_path: str):
        """Load embeddings and metadata from files"""
        # Try to find files
        paths_to_try = [
            (embeddings_path, metadata_path),
            ("data/embeddings/fund_embeddings.npy", "data/embeddings/fund_embeddings_metadata.json"),
            ("../phase2_embedding_indexing/data/embeddings/fund_embeddings.npy", 
             "../phase2_embedding_indexing/data/embeddings/fund_embeddings_metadata.json")
        ]
        
        for emb_path, meta_path in paths_to_try:
            if Path(emb_path).exists() and Path(meta_path).exists():
                print(f"Loading embeddings from: {emb_path}")
                self.embeddings = np.load(emb_path)
                
                print(f"Loading metadata from: {meta_path}")
                with open(meta_path, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
                
                self.dimension = self.embeddings.shape[1]
                print(f"✓ Loaded {len(self.metadata)} chunks with {self.dimension}-dim embeddings")
                return
        
        raise FileNotFoundError(f"Could not find embeddings or metadata files")
    
    def retrieve(self, 
                 query_embedding: np.ndarray,
                 top_k: int = 5,
                 filters: Optional[Dict[str, Any]] = None) -> List[RetrievalResult]:
        """
        Retrieve most similar chunks for a query
        
        Args:
            query_embedding: Query vector (must match embedding dimension)
            top_k: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            List of RetrievalResult objects
        """
        if self.embeddings is None:
            raise RuntimeError("Embeddings not loaded")
        
        # Ensure query is normalized
        query_embedding = query_embedding / np.linalg.norm(query_embedding)
        
        # Compute cosine similarity (dot product of normalized vectors)
        similarities = np.dot(self.embeddings, query_embedding)
        
        # Apply filters if provided
        if filters:
            mask = self._apply_filters(filters)
            # Set similarity to -1 for filtered out items
            similarities = np.where(mask, similarities, -1)
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Build results
        results = []
        for idx in top_indices:
            if similarities[idx] > -0.5:  # Only include if not filtered out
                meta = self.metadata[idx]
                results.append(RetrievalResult(
                    chunk_id=meta['chunk_id'],
                    fund_name=meta['fund_name'],
                    text=meta['text'],
                    score=float(similarities[idx]),
                    metadata=meta['metadata'],
                    source_url=meta['source_url']
                ))
        
        return results
    
    def _apply_filters(self, filters: Dict[str, Any]) -> np.ndarray:
        """
        Apply metadata filters to create a boolean mask
        
        Supports:
        - Exact match: {'category': 'ELSS'}
        - Contains: {'fund_name': {'$contains': 'SBI'}}
        - Boolean: {'is_elss': True}
        """
        mask = np.ones(len(self.metadata), dtype=bool)
        
        for key, value in filters.items():
            if isinstance(value, dict):
                # Complex filter (e.g., $contains)
                if '$contains' in value:
                    search_term = value['$contains'].lower()
                    key_mask = np.array([
                        search_term in str(m['metadata'].get(key, '')).lower() or
                        search_term in str(m.get(key, '')).lower()
                        for m in self.metadata
                    ])
                    mask &= key_mask
            else:
                # Simple exact match
                key_mask = np.array([
                    str(m['metadata'].get(key, '')).lower() == str(value).lower() or
                    str(m.get(key, '')).lower() == str(value).lower()
                    for m in self.metadata
                ])
                mask &= key_mask
        
        return mask
    
    def search_by_text(self, 
                       query_text: str,
                       query_embedder=None,
                       top_k: int = 5,
                       filters: Optional[Dict[str, Any]] = None) -> List[RetrievalResult]:
        """
        Search by text query (requires embedder)
        
        Args:
            query_text: Text query
            query_embedder: Object with embed_single_text method
            top_k: Number of results
            filters: Optional metadata filters
            
        Returns:
            List of RetrievalResult objects
        """
        if query_embedder is None:
            raise ValueError("query_embedder required for text search")
        
        # Generate query embedding
        query_embedding = query_embedder.embed_single_text(query_text)
        
        # Retrieve
        return self.retrieve(query_embedding, top_k, filters)
    
    def get_fund_chunks(self, fund_name: str) -> List[RetrievalResult]:
        """Get all chunks for a specific fund"""
        results = []
        for i, meta in enumerate(self.metadata):
            if fund_name.lower() in meta['fund_name'].lower():
                results.append(RetrievalResult(
                    chunk_id=meta['chunk_id'],
                    fund_name=meta['fund_name'],
                    text=meta['text'],
                    score=1.0,  # Exact match
                    metadata=meta['metadata'],
                    source_url=meta['source_url']
                ))
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get retriever statistics"""
        return {
            'total_chunks': len(self.metadata),
            'embedding_dimension': self.dimension,
            'fund_names': list(set(m['fund_name'] for m in self.metadata)),
            'chunk_types': list(set(m['chunk_type'] for m in self.metadata))
        }


if __name__ == "__main__":
    # Test the retriever
    print("Testing Dense Retriever")
    print("=" * 70)
    
    try:
        retriever = DenseRetriever()
        
        # Show stats
        stats = retriever.get_stats()
        print(f"\nStats:")
        print(f"  Total chunks: {stats['total_chunks']}")
        print(f"  Dimension: {stats['embedding_dimension']}")
        print(f"  Funds: {len(stats['fund_names'])}")
        print(f"  Chunk types: {stats['chunk_types']}")
        
        # Test with random embedding (in real use, would use query embedder)
        print("\n\nTest retrieval with random query embedding:")
        query_emb = np.random.randn(stats['embedding_dimension'])
        query_emb = query_emb / np.linalg.norm(query_emb)
        
        results = retriever.retrieve(query_emb, top_k=3)
        
        for i, r in enumerate(results, 1):
            print(f"\n{i}. {r.fund_name} (score: {r.score:.4f})")
            print(f"   Text: {r.text[:100]}...")
            print(f"   Type: {r.metadata.get('chunk_type', 'unknown')}")
        
        # Test filtering
        print("\n\nTest with ELSS filter:")
        results = retriever.retrieve(query_emb, top_k=3, filters={'is_elss': True})
        
        for i, r in enumerate(results, 1):
            print(f"\n{i}. {r.fund_name} (score: {r.score:.4f})")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nMake sure Phase 2 has been run and embeddings are available.")

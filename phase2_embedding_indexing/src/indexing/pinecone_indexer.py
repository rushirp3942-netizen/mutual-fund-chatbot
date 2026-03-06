"""
Pinecone Vector Database Indexer
Indexes fund embeddings in Pinecone for semantic search
"""

import os
from typing import List, Dict, Optional
from dataclasses import dataclass
import json
import numpy as np

try:
    from pinecone import Pinecone, ServerlessSpec
except ImportError:
    print("Warning: pinecone-client not installed. Run: pip install pinecone-client")
    Pinecone = None
    ServerlessSpec = None


@dataclass
class IndexConfig:
    """Configuration for Pinecone index"""
    index_name: str = "mutual-funds"
    dimension: int = 384  # all-MiniLM-L6-v2 produces 384-dim vectors
    metric: str = "cosine"  # or "euclidean", "dotproduct"
    cloud: str = "aws"  # or "gcp", "azure"
    region: str = "us-east-1"
    namespace: str = "fund_info"


class PineconeIndexer:
    """
    Manages Pinecone vector database operations
    Creates index, upserts vectors, and handles queries
    """
    
    def __init__(self, api_key: Optional[str] = None, config: IndexConfig = None):
        self.config = config or IndexConfig()
        self.api_key = api_key or os.getenv('PINECONE_API_KEY')
        self.pc = None
        self.index = None
        
        if Pinecone is not None and self.api_key:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Pinecone client"""
        if not self.api_key:
            raise ValueError("Pinecone API key required. Set PINECONE_API_KEY environment variable.")
        
        print("Initializing Pinecone client...")
        try:
            self.pc = Pinecone(api_key=self.api_key)
            print("✓ Pinecone client initialized")
        except Exception as e:
            print(f"✗ Error initializing Pinecone: {e}")
            raise
    
    def create_index(self, force_recreate: bool = False):
        """
        Create Pinecone index if it doesn't exist
        
        Args:
            force_recreate: If True, delete existing index and recreate
        """
        if self.pc is None:
            raise RuntimeError("Pinecone client not initialized")
        
        index_name = self.config.index_name
        
        # Check if index exists
        existing_indexes = self.pc.list_indexes().names()
        
        if index_name in existing_indexes:
            if force_recreate:
                print(f"Deleting existing index: {index_name}")
                self.pc.delete_index(index_name)
                print(f"✓ Deleted index: {index_name}")
            else:
                print(f"Index '{index_name}' already exists. Using existing index.")
                self.index = self.pc.Index(index_name)
                return
        
        # Create new index
        print(f"Creating index: {index_name}")
        print(f"  Dimension: {self.config.dimension}")
        print(f"  Metric: {self.config.metric}")
        print(f"  Cloud: {self.config.cloud}")
        print(f"  Region: {self.config.region}")
        
        try:
            self.pc.create_index(
                name=index_name,
                dimension=self.config.dimension,
                metric=self.config.metric,
                spec=ServerlessSpec(
                    cloud=self.config.cloud,
                    region=self.config.region
                )
            )
            print(f"✓ Created index: {index_name}")
            
            # Connect to index
            self.index = self.pc.Index(index_name)
            
        except Exception as e:
            print(f"✗ Error creating index: {e}")
            raise
    
    def connect_to_index(self):
        """Connect to existing index"""
        if self.pc is None:
            raise RuntimeError("Pinecone client not initialized")
        
        index_name = self.config.index_name
        print(f"Connecting to index: {index_name}")
        
        try:
            self.index = self.pc.Index(index_name)
            # Get index stats
            stats = self.index.describe_index_stats()
            print(f"✓ Connected to index")
            print(f"  Total vectors: {stats.total_vector_count}")
            print(f"  Dimension: {stats.dimension}")
        except Exception as e:
            print(f"✗ Error connecting to index: {e}")
            raise
    
    def upsert_vectors(self, embedded_chunks: List[Dict], batch_size: int = 100):
        """
        Upsert vector embeddings to Pinecone
        
        Args:
            embedded_chunks: List of dictionaries with 'chunk_id', 'embedding', and metadata
            batch_size: Number of vectors to upsert in each batch
        """
        if self.index is None:
            raise RuntimeError("Not connected to index. Call create_index() or connect_to_index() first.")
        
        namespace = self.config.namespace
        total_chunks = len(embedded_chunks)
        
        print(f"Upserting {total_chunks} vectors to namespace '{namespace}'...")
        
        # Process in batches
        for i in range(0, total_chunks, batch_size):
            batch = embedded_chunks[i:i + batch_size]
            
            # Prepare vectors for upsert
            vectors = []
            for chunk in batch:
                vector = {
                    'id': chunk['chunk_id'],
                    'values': chunk['embedding'] if isinstance(chunk['embedding'], list) else chunk['embedding'].tolist(),
                    'metadata': {
                        'fund_name': chunk['fund_name'],
                        'text': chunk['text'][:1000],  # Truncate for metadata size limit
                        'chunk_type': chunk['chunk_type'],
                        'source_url': chunk['source_url'],
                        **{k: v for k, v in chunk['metadata'].items() if v is not None}
                    }
                }
                vectors.append(vector)
            
            # Upsert batch
            try:
                self.index.upsert(vectors=vectors, namespace=namespace)
                print(f"  ✓ Upserted batch {i//batch_size + 1}/{(total_chunks-1)//batch_size + 1} ({len(batch)} vectors)")
            except Exception as e:
                print(f"  ✗ Error upserting batch: {e}")
                raise
        
        print(f"✓ Upserted all {total_chunks} vectors")
        
        # Get final stats
        stats = self.index.describe_index_stats()
        print(f"  Total vectors in index: {stats.total_vector_count}")
    
    def query(self, query_vector: List[float], top_k: int = 5, filter_dict: Optional[Dict] = None):
        """
        Query the index for similar vectors
        
        Args:
            query_vector: The query embedding vector
            top_k: Number of results to return
            filter_dict: Optional metadata filter
            
        Returns:
            Query results
        """
        if self.index is None:
            raise RuntimeError("Not connected to index")
        
        namespace = self.config.namespace
        
        try:
            results = self.index.query(
                namespace=namespace,
                vector=query_vector,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict
            )
            return results
        except Exception as e:
            print(f"✗ Error querying index: {e}")
            raise
    
    def delete_all_vectors(self):
        """Delete all vectors from the namespace"""
        if self.index is None:
            raise RuntimeError("Not connected to index")
        
        namespace = self.config.namespace
        print(f"Deleting all vectors from namespace '{namespace}'...")
        
        try:
            self.index.delete(delete_all=True, namespace=namespace)
            print(f"✓ Deleted all vectors from namespace '{namespace}'")
        except Exception as e:
            print(f"✗ Error deleting vectors: {e}")
            raise
    
    def get_index_stats(self):
        """Get index statistics"""
        if self.index is None:
            raise RuntimeError("Not connected to index")
        
        return self.index.describe_index_stats()


if __name__ == "__main__":
    # Example usage (requires PINECONE_API_KEY environment variable)
    import os
    
    api_key = os.getenv('PINECONE_API_KEY')
    
    if api_key:
        indexer = PineconeIndexer(api_key=api_key)
        
        # Create or connect to index
        try:
            indexer.create_index()
        except:
            indexer.connect_to_index()
        
        # Example: Get index stats
        stats = indexer.get_index_stats()
        print(f"\nIndex Stats:")
        print(f"  Total vectors: {stats.total_vector_count}")
        print(f"  Dimension: {stats.dimension}")
    else:
        print("Set PINECONE_API_KEY environment variable to test Pinecone indexing")

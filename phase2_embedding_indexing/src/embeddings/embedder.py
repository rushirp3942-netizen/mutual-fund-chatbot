"""
Embedding Generation Module
Generates vector embeddings using sentence-transformers
"""

import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass
import json

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("Warning: sentence-transformers not installed. Run: pip install sentence-transformers")
    SentenceTransformer = None


@dataclass
class EmbeddingConfig:
    """Configuration for embedding generation"""
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    batch_size: int = 32
    device: str = "cpu"  # 'cpu' or 'cuda'
    normalize_embeddings: bool = True


@dataclass
class EmbeddedChunk:
    """Chunk with its vector embedding"""
    chunk_id: str
    fund_name: str
    text: str
    embedding: np.ndarray
    chunk_type: str
    metadata: Dict
    source_url: str


class FundEmbedder:
    """
    Generates embeddings for fund text chunks
    Uses sentence-transformers for semantic encoding
    """
    
    def __init__(self, config: EmbeddingConfig = None):
        self.config = config or EmbeddingConfig()
        self.model = None
        self.embedding_dim = None
        
        if SentenceTransformer is not None:
            self._load_model()
    
    def _load_model(self):
        """Load the embedding model"""
        print(f"Loading embedding model: {self.config.model_name}")
        try:
            self.model = SentenceTransformer(self.config.model_name, device=self.config.device)
            # Get embedding dimension from model
            sample_embedding = self.model.encode(["test"])
            self.embedding_dim = len(sample_embedding[0])
            print(f"✓ Model loaded. Embedding dimension: {self.embedding_dim}")
        except Exception as e:
            print(f"✗ Error loading model: {e}")
            raise
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts
        
        Args:
            texts: List of text strings to encode
            
        Returns:
            numpy array of embeddings (shape: len(texts) x embedding_dim)
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Cannot generate embeddings.")
        
        print(f"Generating embeddings for {len(texts)} texts...")
        
        embeddings = self.model.encode(
            texts,
            batch_size=self.config.batch_size,
            show_progress_bar=True,
            normalize_embeddings=self.config.normalize_embeddings
        )
        
        print(f"✓ Generated embeddings with shape: {embeddings.shape}")
        return embeddings
    
    def embed_chunks(self, chunks: List[Dict]) -> List[EmbeddedChunk]:
        """
        Generate embeddings for fund chunks
        
        Args:
            chunks: List of chunk dictionaries with 'text' field
            
        Returns:
            List of EmbeddedChunk objects
        """
        if not chunks:
            print("Warning: No chunks to embed")
            return []
        
        # Extract texts from chunks
        texts = [chunk['text'] for chunk in chunks]
        
        # Generate embeddings
        embeddings = self.generate_embeddings(texts)
        
        # Create EmbeddedChunk objects
        embedded_chunks = []
        for i, chunk in enumerate(chunks):
            embedded_chunk = EmbeddedChunk(
                chunk_id=chunk['chunk_id'],
                fund_name=chunk['fund_name'],
                text=chunk['text'],
                embedding=embeddings[i],
                chunk_type=chunk['chunk_type'],
                metadata=chunk['metadata'],
                source_url=chunk['source_url']
            )
            embedded_chunks.append(embedded_chunk)
        
        return embedded_chunks
    
    def embed_single_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text
        
        Args:
            text: Text string to encode
            
        Returns:
            numpy array embedding vector
        """
        if self.model is None:
            raise RuntimeError("Model not loaded.")
        
        embedding = self.model.encode([text], normalize_embeddings=self.config.normalize_embeddings)
        return embedding[0]
    
    def save_embeddings(self, embedded_chunks: List[EmbeddedChunk], output_file: str):
        """
        Save embeddings to numpy file and metadata to JSON
        
        Args:
            embedded_chunks: List of EmbeddedChunk objects
            output_file: Base path for output files (without extension)
        """
        # Extract embeddings array
        embeddings_array = np.array([chunk.embedding for chunk in embedded_chunks])
        
        # Save embeddings as numpy array
        np.save(f"{output_file}.npy", embeddings_array)
        print(f"✓ Saved embeddings to {output_file}.npy")
        
        # Save metadata as JSON
        metadata = []
        for chunk in embedded_chunks:
            metadata.append({
                'chunk_id': chunk.chunk_id,
                'fund_name': chunk.fund_name,
                'text': chunk.text,
                'chunk_type': chunk.chunk_type,
                'metadata': chunk.metadata,
                'source_url': chunk.source_url
            })
        
        with open(f"{output_file}_metadata.json", 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Saved metadata to {output_file}_metadata.json")
        
        # Save combined data
        combined_data = []
        for i, chunk in enumerate(embedded_chunks):
            combined_data.append({
                'chunk_id': chunk.chunk_id,
                'fund_name': chunk.fund_name,
                'text': chunk.text,
                'embedding': chunk.embedding.tolist(),
                'chunk_type': chunk.chunk_type,
                'metadata': chunk.metadata,
                'source_url': chunk.source_url
            })
        
        with open(f"{output_file}_full.json", 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Saved combined data to {output_file}_full.json")


if __name__ == "__main__":
    # Example usage
    embedder = FundEmbedder()
    
    # Sample texts
    sample_texts = [
        "SBI ELSS Tax Saver Fund is an ELSS mutual fund with 3 years lock-in period.",
        "HDFC Mid Cap Fund has an expense ratio of 0.76% and is categorized as Very High risk.",
        "The minimum SIP amount for Axis Small Cap Fund is ₹100."
    ]
    
    # Generate embeddings
    embeddings = embedder.generate_embeddings(sample_texts)
    
    print(f"\nSample embeddings shape: {embeddings.shape}")
    print(f"First embedding (first 5 values): {embeddings[0][:5]}")

#!/usr/bin/env python3
"""
Phase 2: Embedding & Indexing Pipeline (Demo Version)
Processes extracted fund data and creates chunks ready for embedding

This demo version simulates the embedding generation without requiring PyTorch,
which has DLL issues on some Windows systems.
"""

import sys
import json
import os
import random
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from chunking import FundChunker, ChunkConfig


def load_fund_data(input_file: str) -> list:
    """Load extracted fund data from Phase 1"""
    print(f"Loading fund data from: {input_file}")
    
    # Check if file exists in phase1_data_collection
    if not os.path.exists(input_file):
        # Try to find in parent directory
        alt_path = Path(__file__).parent.parent.parent / "phase1_data_collection" / input_file
        if alt_path.exists():
            input_file = str(alt_path)
        else:
            raise FileNotFoundError(f"Fund data file not found: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✓ Loaded {len(data)} funds")
    return data


def simulate_embeddings(chunks, embedding_dim=384):
    """
    Simulate embedding generation for demo purposes.
    In production, this would use sentence-transformers.
    """
    print(f"\n[Demo Mode] Simulating {embedding_dim}-dimensional embeddings...")
    
    embedded_chunks = []
    for chunk in chunks:
        # Generate deterministic pseudo-random embedding based on text
        # This ensures same text always gets same "embedding"
        import hashlib
        hash_val = int(hashlib.md5(chunk['text'].encode()).hexdigest(), 16)
        random.seed(hash_val)
        
        # Generate normalized random vector
        embedding = [random.uniform(-1, 1) for _ in range(embedding_dim)]
        # Normalize
        magnitude = sum(x**2 for x in embedding) ** 0.5
        embedding = [x / magnitude for x in embedding]
        
        embedded_chunks.append({
            'chunk_id': chunk['chunk_id'],
            'fund_name': chunk['fund_name'],
            'text': chunk['text'],
            'embedding': embedding,
            'chunk_type': chunk['chunk_type'],
            'metadata': chunk['metadata'],
            'source_url': chunk['source_url']
        })
    
    print(f"✓ Generated {len(embedded_chunks)} simulated embeddings")
    return embedded_chunks


def save_embeddings(embedded_chunks, output_file):
    """Save embeddings and metadata to files"""
    import numpy as np
    
    # Save embeddings as numpy array
    embeddings_array = np.array([chunk['embedding'] for chunk in embedded_chunks])
    np.save(f"{output_file}.npy", embeddings_array)
    print(f"✓ Saved embeddings to {output_file}.npy")
    
    # Save metadata as JSON
    metadata = []
    for chunk in embedded_chunks:
        metadata.append({
            'chunk_id': chunk['chunk_id'],
            'fund_name': chunk['fund_name'],
            'text': chunk['text'],
            'chunk_type': chunk['chunk_type'],
            'metadata': chunk['metadata'],
            'source_url': chunk['source_url']
        })
    
    with open(f"{output_file}_metadata.json", 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved metadata to {output_file}_metadata.json")
    
    # Save combined data
    combined_data = []
    for chunk in embedded_chunks:
        combined_data.append({
            'chunk_id': chunk['chunk_id'],
            'fund_name': chunk['fund_name'],
            'text': chunk['text'],
            'embedding': chunk['embedding'],
            'chunk_type': chunk['chunk_type'],
            'metadata': chunk['metadata'],
            'source_url': chunk['source_url']
        })
    
    with open(f"{output_file}_full.json", 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved combined data to {output_file}_full.json")


def run_phase2_pipeline(
    input_file: str = "../phase1_data_collection/data/processed/extracted_funds.json",
    output_dir: str = "data/embeddings"
):
    """
    Run complete Phase 2 pipeline (Demo Mode)
    
    Steps:
    1. Load extracted fund data
    2. Create semantic chunks
    3. Generate simulated embeddings (demo mode)
    4. Save embeddings locally
    """
    
    print("=" * 70)
    print("PHASE 2: EMBEDDING & INDEXING (DEMO MODE)")
    print("=" * 70)
    print("\nNote: Running in demo mode without PyTorch.")
    print("Embeddings are simulated for demonstration purposes.")
    print("For production, install PyTorch: pip install torch")
    
    # Step 1: Load fund data
    print("\n" + "-" * 70)
    print("STEP 1: Loading Fund Data")
    print("-" * 70)
    funds_data = load_fund_data(input_file)
    
    # Step 2: Create chunks
    print("\n" + "-" * 70)
    print("STEP 2: Creating Semantic Chunks")
    print("-" * 70)
    
    chunker = FundChunker(config=ChunkConfig())
    all_chunks = chunker.chunk_multiple_funds(funds_data)
    
    print(f"\n✓ Created {len(all_chunks)} chunks from {len(funds_data)} funds")
    
    # Show chunk distribution
    chunk_types = {}
    for chunk in all_chunks:
        chunk_type = chunk.chunk_type
        chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
    
    print("\nChunk distribution:")
    for chunk_type, count in chunk_types.items():
        print(f"  {chunk_type}: {count}")
    
    # Save chunks
    os.makedirs(output_dir, exist_ok=True)
    chunks_file = os.path.join(output_dir, "fund_chunks.json")
    chunker.save_chunks(all_chunks, chunks_file)
    
    # Step 3: Generate simulated embeddings
    print("\n" + "-" * 70)
    print("STEP 3: Generating Embeddings (Demo Mode)")
    print("-" * 70)
    
    # Convert chunks to dictionaries
    chunks_dict = [
        {
            'chunk_id': chunk.chunk_id,
            'fund_name': chunk.fund_name,
            'text': chunk.text,
            'chunk_type': chunk.chunk_type,
            'metadata': chunk.metadata,
            'source_url': chunk.source_url
        }
        for chunk in all_chunks
    ]
    
    embedded_chunks = simulate_embeddings(chunks_dict, embedding_dim=384)
    
    # Save embeddings
    embeddings_file = os.path.join(output_dir, "fund_embeddings")
    save_embeddings(embedded_chunks, embeddings_file)
    
    # Step 4: Pinecone indexing info
    print("\n" + "-" * 70)
    print("STEP 4: Pinecone Indexing (Skipped in Demo)")
    print("-" * 70)
    print("To index in Pinecone, set PINECONE_API_KEY environment variable")
    print("and run with the full pipeline.")
    
    # Summary
    print("\n" + "=" * 70)
    print("PHASE 2 COMPLETE")
    print("=" * 70)
    print(f"\nOutput files:")
    print(f"  Chunks: {chunks_file}")
    print(f"  Embeddings: {embeddings_file}.npy")
    print(f"  Metadata: {embeddings_file}_metadata.json")
    print(f"  Full data: {embeddings_file}_full.json")
    
    print(f"\nStatistics:")
    print(f"  Funds processed: {len(funds_data)}")
    print(f"  Chunks created: {len(all_chunks)}")
    print(f"  Embeddings generated: {len(embedded_chunks)}")
    print(f"  Embedding dimension: 384 (simulated)")
    
    print("\n" + "=" * 70)
    print("NEXT STEPS:")
    print("=" * 70)
    print("1. For production: Install PyTorch (pip install torch)")
    print("2. Set PINECONE_API_KEY environment variable")
    print("3. Run full pipeline: python scripts/run_phase2.py")
    print("4. Proceed to Phase 3: Retrieval & Query Handling")
    
    return embedded_chunks


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Phase 2: Embedding & Indexing (Demo)')
    parser.add_argument('--input', default='../phase1_data_collection/data/processed/extracted_funds.json',
                       help='Input fund data file from Phase 1')
    parser.add_argument('--output', default='data/embeddings',
                       help='Output directory for embeddings')
    
    args = parser.parse_args()
    
    # Run pipeline
    embedded_chunks = run_phase2_pipeline(
        input_file=args.input,
        output_dir=args.output
    )

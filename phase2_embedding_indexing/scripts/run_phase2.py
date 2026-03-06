#!/usr/bin/env python3
"""
Phase 2: Embedding & Indexing Pipeline
Processes extracted fund data and indexes in Pinecone
"""

import sys
import json
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from chunking import FundChunker, ChunkConfig
from embeddings import FundEmbedder, EmbeddingConfig
from indexing import PineconeIndexer, IndexConfig


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


def run_phase2_pipeline(
    input_file: str = "../phase1_data_collection/data/processed/extracted_funds.json",
    output_dir: str = "data/embeddings",
    pinecone_api_key: str = None,
    skip_pinecone: bool = False
):
    """
    Run complete Phase 2 pipeline
    
    Steps:
    1. Load extracted fund data
    2. Create semantic chunks
    3. Generate embeddings
    4. Index in Pinecone (optional)
    """
    
    print("=" * 70)
    print("PHASE 2: EMBEDDING & INDEXING")
    print("=" * 70)
    
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
    
    # Step 3: Generate embeddings
    print("\n" + "-" * 70)
    print("STEP 3: Generating Embeddings")
    print("-" * 70)
    
    embedder = FundEmbedder(config=EmbeddingConfig())
    
    # Convert chunks to dictionaries for embedder
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
    
    embedded_chunks = embedder.embed_chunks(chunks_dict)
    
    # Save embeddings
    embeddings_file = os.path.join(output_dir, "fund_embeddings")
    embedder.save_embeddings(embedded_chunks, embeddings_file)
    
    # Step 4: Index in Pinecone (optional)
    if not skip_pinecone and pinecone_api_key:
        print("\n" + "-" * 70)
        print("STEP 4: Indexing in Pinecone")
        print("-" * 70)
        
        indexer = PineconeIndexer(
            api_key=pinecone_api_key,
            config=IndexConfig(
                index_name="mutual-funds",
                dimension=embedder.embedding_dim,
                namespace="fund_info"
            )
        )
        
        # Create or connect to index
        try:
            indexer.create_index()
        except Exception as e:
            print(f"Index may already exist, connecting... ({e})")
            indexer.connect_to_index()
        
        # Prepare chunks for upsert
        chunks_for_upsert = [
            {
                'chunk_id': chunk.chunk_id,
                'fund_name': chunk.fund_name,
                'text': chunk.text,
                'embedding': chunk.embedding,
                'chunk_type': chunk.chunk_type,
                'metadata': chunk.metadata,
                'source_url': chunk.source_url
            }
            for chunk in embedded_chunks
        ]
        
        # Upsert to Pinecone
        indexer.upsert_vectors(chunks_for_upsert)
        
        # Get final stats
        stats = indexer.get_index_stats()
        print(f"\n✓ Indexing complete")
        print(f"  Total vectors in index: {stats.total_vector_count}")
    elif skip_pinecone:
        print("\n" + "-" * 70)
        print("STEP 4: Skipping Pinecone indexing (skip_pinecone=True)")
        print("-" * 70)
    else:
        print("\n" + "-" * 70)
        print("STEP 4: Skipping Pinecone indexing (no API key)")
        print("-" * 70)
        print("To enable Pinecone indexing, set PINECONE_API_KEY environment variable")
    
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
    print(f"  Embedding dimension: {embedder.embedding_dim}")
    
    return embedded_chunks


def test_query(pinecone_api_key: str = None):
    """Test querying the indexed data"""
    if not pinecone_api_key:
        pinecone_api_key = os.getenv('PINECONE_API_KEY')
    
    if not pinecone_api_key:
        print("PINECONE_API_KEY not set. Cannot test query.")
        return
    
    print("\n" + "=" * 70)
    print("TESTING VECTOR SEARCH")
    print("=" * 70)
    
    # Initialize embedder and indexer
    embedder = FundEmbedder()
    indexer = PineconeIndexer(api_key=pinecone_api_key)
    indexer.connect_to_index()
    
    # Test queries
    test_queries = [
        "Which ELSS funds have 3 year lock-in?",
        "Show me funds with low expense ratio",
        "What is the risk level of SBI Small Cap Fund?",
        "Funds with minimum SIP of 500 rupees"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        
        # Generate query embedding
        query_embedding = embedder.embed_single_text(query)
        
        # Query Pinecone
        results = indexer.query(
            query_vector=query_embedding.tolist(),
            top_k=3
        )
        
        print("  Top results:")
        for i, match in enumerate(results.matches, 1):
            print(f"    {i}. {match.metadata.get('fund_name', 'Unknown')}")
            print(f"       Score: {match.score:.4f}")
            print(f"       Type: {match.metadata.get('chunk_type', 'Unknown')}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Phase 2: Embedding & Indexing')
    parser.add_argument('--input', default='../phase1_data_collection/data/processed/extracted_funds.json',
                       help='Input fund data file from Phase 1')
    parser.add_argument('--output', default='data/embeddings',
                       help='Output directory for embeddings')
    parser.add_argument('--skip-pinecone', action='store_true',
                       help='Skip Pinecone indexing')
    parser.add_argument('--test-query', action='store_true',
                       help='Test querying after indexing')
    
    args = parser.parse_args()
    
    # Get Pinecone API key from environment
    pinecone_api_key = os.getenv('PINECONE_API_KEY')
    
    # Run pipeline
    embedded_chunks = run_phase2_pipeline(
        input_file=args.input,
        output_dir=args.output,
        pinecone_api_key=pinecone_api_key,
        skip_pinecone=args.skip_pinecone
    )
    
    # Test query if requested
    if args.test_query and pinecone_api_key and not args.skip_pinecone:
        test_query(pinecone_api_key)

#!/usr/bin/env python3
"""
Phase 3: Retrieval & Query Handling Pipeline
Processes queries and retrieves relevant fund information
"""

import sys
import json
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "phase2_embedding_indexing" / "src"))

from query_processing import QueryProcessor, QueryIntent
from retrieval import DenseRetriever, HybridRetriever


def simulate_query_embedding(query_text: str, dimension: int = 384) -> np.ndarray:
    """
    Simulate query embedding for demo purposes
    In production, this would use the same embedder as Phase 2
    """
    import hashlib
    hash_val = int(hashlib.md5(query_text.encode()).hexdigest(), 16) % (2**32)
    np.random.seed(hash_val)
    
    embedding = np.random.randn(dimension)
    embedding = embedding / np.linalg.norm(embedding)
    
    return embedding


def format_results(results, intent):
    """Format retrieval results for display"""
    output = []
    
    for i, r in enumerate(results, 1):
        result_text = f"\n{i}. {r.fund_name}"
        
        if hasattr(r, 'combined_score'):
            result_text += f" (score: {r.combined_score:.4f})"
        elif hasattr(r, 'score'):
            result_text += f" (score: {r.score:.4f})"
        
        result_text += f"\n   Text: {r.text[:120]}..."
        result_text += f"\n   Source: {r.source_url}"
        
        output.append(result_text)
    
    return '\n'.join(output)


def run_phase3_pipeline(query: str = None):
    """
    Run Phase 3 retrieval pipeline
    
    Args:
        query: Optional query string. If None, runs test queries.
    """
    print("=" * 70)
    print("PHASE 3: RETRIEVAL & QUERY HANDLING")
    print("=" * 70)
    
    # Initialize components
    print("\n[1/4] Initializing Query Processor...")
    query_processor = QueryProcessor()
    
    print("[2/4] Initializing Dense Retriever...")
    try:
        dense_retriever = DenseRetriever()
        stats = dense_retriever.get_stats()
        print(f"      ✓ Loaded {stats['total_chunks']} chunks")
    except FileNotFoundError:
        print("      ✗ Embeddings not found. Run Phase 2 first.")
        return
    
    print("[3/4] Initializing Hybrid Retriever...")
    hybrid_retriever = HybridRetriever(dense_retriever)
    print("      ✓ Hybrid retriever ready")
    
    # Test queries
    test_queries = [
        "What is the expense ratio of SBI ELSS Tax Saver Fund?",
        "Show me ELSS funds with 3 year lock-in",
        "Compare HDFC Mid Cap vs Nippon Small Cap",
        "How to download mutual fund statements?",
        "Best large cap funds",
        "What is the risk level of Axis Small Cap Fund?",
        "Funds with minimum SIP of 100 rupees"
    ]
    
    queries_to_run = [query] if query else test_queries
    
    print(f"\n[4/4] Processing {len(queries_to_run)} queries...")
    print("=" * 70)
    
    all_results = []
    
    for query_text in queries_to_run:
        print(f"\n{'='*70}")
        print(f"QUERY: {query_text}")
        print("=" * 70)
        
        # Step 1: Process query
        print("\n[Query Processing]")
        processed = query_processor.process(query_text)
        
        print(f"  Intent: {processed.intent.value} (confidence: {processed.confidence:.2f})")
        print(f"  Entities: {json.dumps(processed.entities, indent=4)}")
        print(f"  Filters: {json.dumps(processed.filters, indent=4)}")
        
        # Step 2: Generate query embedding (simulated)
        query_embedding = simulate_query_embedding(query_text)
        
        # Step 3: Retrieve results
        print("\n[Retrieval]")
        
        # Use hybrid retrieval for most intents
        if processed.intent in [QueryIntent.FUND_SPECIFIC, QueryIntent.ATTRIBUTE_BASED]:
            print("  Using Hybrid Retrieval (Dense + Sparse)...")
            results = hybrid_retriever.retrieve(
                query_embedding,
                query_text,
                top_k=5,
                filters=processed.filters if processed.filters else None
            )
        else:
            print("  Using Dense Retrieval...")
            results = dense_retriever.retrieve(
                query_embedding,
                top_k=5,
                filters=processed.filters if processed.filters else None
            )
        
        # Display results
        print("\n[Top Results]")
        print(format_results(results, processed.intent))
        
        all_results.append({
            'query': query_text,
            'processed': processed.to_dict(),
            'results': [
                {
                    'fund_name': r.fund_name,
                    'text': r.text,
                    'score': r.combined_score if hasattr(r, 'combined_score') else r.score,
                    'source_url': r.source_url
                }
                for r in results[:3]
            ]
        })
    
    # Summary
    print("\n" + "=" * 70)
    print("PHASE 3 COMPLETE")
    print("=" * 70)
    print(f"\nProcessed {len(queries_to_run)} queries")
    print(f"Retrieval methods used:")
    print(f"  - Hybrid (Dense + Sparse): For fund-specific and attribute queries")
    print(f"  - Dense (Semantic): For general and document queries")
    
    # Save results
    output_file = Path(__file__).parent.parent / "data" / "retrieval_results.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {output_file}")
    
    print("\n" + "=" * 70)
    print("NEXT STEPS:")
    print("=" * 70)
    print("1. Review retrieval results")
    print("2. Tune alpha parameter for hybrid scoring")
    print("3. Add more sophisticated reranking")
    print("4. Proceed to Phase 4: LLM Integration")
    
    return all_results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Phase 3: Retrieval & Query Handling')
    parser.add_argument('--query', type=str, help='Single query to process')
    
    args = parser.parse_args()
    
    # Run pipeline
    results = run_phase3_pipeline(args.query)

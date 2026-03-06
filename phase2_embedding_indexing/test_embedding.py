#!/usr/bin/env python3
"""Test script to verify sentence-transformers is working"""

print("Testing sentence-transformers...")

try:
    from sentence_transformers import SentenceTransformer
    print("✓ Import successful")
    
    print("Loading model (this may take a moment)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("✓ Model loaded!")
    
    test_texts = [
        "SBI ELSS Tax Saver Fund is an ELSS mutual fund",
        "HDFC Mid Cap Fund has expense ratio of 0.76%"
    ]
    
    print("Generating embeddings...")
    embeddings = model.encode(test_texts)
    print(f"✓ Embeddings generated!")
    print(f"  Shape: {embeddings.shape}")
    print(f"  Dimension: {embeddings.shape[1]}")
    print(f"  First 5 values of first embedding: {embeddings[0][:5]}")
    
    print("\n✅ All tests passed! Phase 2 embedding is ready.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

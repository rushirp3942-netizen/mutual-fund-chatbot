# Phase 3: Retrieval & Query Handling

## Overview

Phase 3 implements the retrieval system that processes user queries and returns relevant mutual fund information. It combines:

1. **Query Processing**: Intent classification and entity extraction
2. **Dense Retrieval**: Semantic search using vector embeddings
3. **Sparse Retrieval**: Keyword-based TF-IDF search
4. **Hybrid Retrieval**: Combines dense + sparse scores

## Architecture

```
User Query → Query Processor → Intent + Entities + Filters
                                    ↓
                    ┌───────────────┴───────────────┐
                    ↓                               ↓
            Dense Retriever                 Sparse Retriever
            (Embeddings)                    (TF-IDF)
                    ↓                               ↓
                    └───────────────┬───────────────┘
                                    ↓
                          Hybrid Retriever
                          (Score Fusion)
                                    ↓
                              Top-K Results
```

## Components

### 1. Query Processor (`src/query_processing/query_processor.py`)

**Intent Classification:**

| Intent | Description | Example |
|--------|-------------|---------|
| `fund_specific` | Query about specific fund | "What is expense ratio of SBI Bluechip?" |
| `attribute_based` | Filter by attributes | "Show ELSS funds with 3-year lock-in" |
| `comparison` | Compare multiple funds | "Compare HDFC vs Nippon Small Cap" |
| `document` | Document/procedure queries | "How to download statements?" |
| `recommendation` | Fund recommendations | "Best large cap funds" |
| `general` | General questions | "What is a mutual fund?" |

**Entity Extraction:**
- Fund names (e.g., "SBI ELSS Tax Saver Fund")
- AMC names (e.g., "SBI Mutual Fund")
- Categories (e.g., "ELSS", "Large Cap", "Small Cap")
- Attributes (e.g., "expense_ratio", "risk_level", "minimum_sip")

**Filter Building:**
```python
{
  "fund_name": {"$contains": "SBI ELSS"},
  "amc": "SBI",
  "category": "elss",
  "is_elss": True,
  "chunk_type": "financial"
}
```

### 2. Dense Retriever (`src/retrieval/dense_retriever.py`)

Performs semantic similarity search using pre-computed embeddings:

```python
retriever = DenseRetriever()
results = retriever.retrieve(
    query_embedding=query_emb,
    top_k=5,
    filters={'category': 'ELSS'}
)
```

**Features:**
- Cosine similarity on normalized vectors
- Metadata filtering support
- Returns `RetrievalResult` objects with scores

### 3. Hybrid Retriever (`src/retrieval/hybrid_retriever.py`)

Combines dense and sparse retrieval:

```python
retriever = HybridRetriever(alpha=0.7)  # 70% dense, 30% sparse
results = retriever.retrieve(
    query_embedding=query_emb,
    query_text="ELSS funds with low expense ratio",
    top_k=5
)
```

**Score Fusion:**
```
combined_score = alpha * dense_score + (1 - alpha) * sparse_score
```

## Usage

### Run Full Pipeline

```bash
cd phase3_retrieval
python scripts/run_phase3.py
```

### Run Single Query

```bash
python scripts/run_phase3.py --query "What is the expense ratio of SBI Bluechip?"
```

### Use in Code

```python
from query_processing import QueryProcessor
from retrieval import HybridRetriever

# Initialize
processor = QueryProcessor()
retriever = HybridRetriever()

# Process query
processed = processor.process("Show me ELSS funds")
print(f"Intent: {processed.intent.value}")
print(f"Filters: {processed.filters}")

# Retrieve results
results = retriever.retrieve(
    query_embedding=query_emb,
    query_text="ELSS funds",
    filters=processed.filters,
    top_k=5
)

for r in results:
    print(f"{r.fund_name}: {r.combined_score:.4f}")
```

## Query Examples

### Test Queries Included:

1. **Fund-Specific**: "What is the expense ratio of SBI ELSS Tax Saver Fund?"
2. **Attribute-Based**: "Show me ELSS funds with 3 year lock-in"
3. **Comparison**: "Compare HDFC Mid Cap vs Nippon Small Cap"
4. **Document**: "How to download mutual fund statements?"
5. **Recommendation**: "Best large cap funds"
6. **Risk Query**: "What is the risk level of Axis Small Cap Fund?"
7. **SIP Query**: "Funds with minimum SIP of 100 rupees"

## Output Format

```json
{
  "query": "What is the expense ratio of SBI ELSS?",
  "processed": {
    "intent": "attribute_based",
    "confidence": 0.70,
    "entities": {
      "fund_name": "Sbi Elss Tax Saver Fund",
      "amc": "Sbi",
      "category": "elss",
      "attributes": ["expense_ratio"]
    },
    "filters": {
      "fund_name": {"$contains": "Sbi Elss Tax Saver Fund"},
      "is_elss": true,
      "chunk_type": "financial"
    }
  },
  "results": [
    {
      "fund_name": "SBI ELSS Tax Saver Fund Direct Growth",
      "text": "Financial details for SBI ELSS Tax Saver Fund...",
      "score": 0.1953,
      "source_url": "https://groww.in/mutual-funds/sbi-elss-tax-saver-fund-direct-growth"
    }
  ]
}
```

## Performance

**Current Stats (9 funds):**
- Total chunks indexed: 36
- Embedding dimension: 384
- Average retrieval time: <100ms
- Hybrid retrieval: Dense (70%) + Sparse (30%)

## Integration with Phase 4

Phase 3 outputs are consumed by Phase 4 (LLM Integration):

```python
# Phase 4 will use these results
results = run_phase3_pipeline(query)

# Build context for LLM
context = "\n\n".join([
    f"[{i+1}] Fund: {r.fund_name}\n{r.text}\nSource: {r.source_url}"
    for i, r in enumerate(results[0]['results'])
])

# Generate response with LLM
response = llm.generate(prompt=f"Context: {context}\n\nQuestion: {query}")
```

## Next Steps

Proceed to **Phase 4: LLM Integration** for:
- LLM client setup (OpenAI/Claude)
- Prompt engineering
- Context assembly
- Response generation with citations

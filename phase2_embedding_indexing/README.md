# Phase 2: Embedding & Indexing

## Overview

Phase 2 converts structured mutual fund data from Phase 1 into searchable vector representations. This involves:

1. **Text Chunking**: Splitting fund data into semantic chunks
2. **Embedding Generation**: Converting text to 384-dimensional vectors
3. **Vector Indexing**: Storing embeddings in Pinecone for fast retrieval

## Architecture

```
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  Extracted Fund │──►│  Text Chunker   │──►│  Embedding Gen  │──►│  Pinecone Index │
│  Data (JSON)    │   │                 │   │  (MiniLM-L6-v2) │   │                 │
└─────────────────┘   └─────────────────┘   └─────────────────┘   └─────────────────┘
       Phase 1              Phase 2              Phase 2              Phase 2
```

## Components

### 1. Text Chunking (`src/chunking/chunker.py`)

Splits each fund into 4 semantic chunk types:

| Chunk Type | Content | Metadata Filters |
|------------|---------|------------------|
| **overview** | Fund name, AMC, category | `amc`, `category` |
| **financial** | Expense ratio, exit load, minimum SIP | `expense_ratio`, `is_elss` |
| **risk** | Risk level, benchmark, category | `risk_level`, `benchmark` |
| **documents** | Factsheet, SID, KIM links, statement info | `has_factsheet`, `has_sid` |

**Example Output:**
```python
{
  "chunk_id": "sbi_elss_tax_saver_fund_direct_growth_financial",
  "fund_name": "SBI ELSS Tax Saver Fund Direct Growth",
  "text": "Financial details for SBI ELSS Tax Saver Fund Direct Growth: Expense ratio is 0.92%. Minimum SIP amount is ₹500. Lock-in period: 3 years lock-in period.",
  "chunk_type": "financial",
  "metadata": {
    "expense_ratio": "0.92%",
    "minimum_sip": "₹500",
    "lock_in_period": "3 years lock-in period",
    "is_elss": true
  },
  "source_url": "https://groww.in/mutual-funds/sbi-elss-tax-saver-fund-direct-growth"
}
```

### 2. Embedding Generation (`src/embeddings/embedder.py`)

Uses `sentence-transformers/all-MiniLM-L6-v2` model:
- **Dimension**: 384
- **Model Size**: ~80MB
- **Speed**: ~1000 texts/sec on CPU
- **Quality**: Optimized for semantic similarity

**Features:**
- Batch processing for efficiency
- Normalized embeddings (cosine similarity)
- Progress tracking with tqdm

### 3. Pinecone Indexing (`src/indexing/pinecone_indexer.py`)

Vector database configuration:

| Setting | Value |
|---------|-------|
| **Index Name** | `mutual-funds` |
| **Dimension** | 384 |
| **Metric** | cosine |
| **Namespace** | `fund_info` |
| **Cloud** | AWS (us-east-1) |

**Metadata Schema:**
```python
{
  "fund_name": "SBI ELSS Tax Saver Fund Direct Growth",
  "amc": "SBI Mutual Fund",
  "category": "ELSS",
  "risk_level": "Very High",
  "expense_ratio": "0.92%",
  "is_elss": true,
  "chunk_type": "financial",
  "source_url": "https://groww.in/mutual-funds/..."
}
```

## Usage

### Quick Start (Demo Mode)

```bash
# Run without PyTorch (simulated embeddings)
python scripts/run_phase2_demo.py
```

### Production Mode

```bash
# Install PyTorch first
pip install torch

# Set Pinecone API key
set PINECONE_API_KEY=your_api_key_here

# Run full pipeline
python scripts/run_phase2.py
```

### Command Line Options

```bash
python scripts/run_phase2.py --help

Options:
  --input PATH        Input fund data file from Phase 1
  --output DIR        Output directory for embeddings
  --skip-pinecone     Skip Pinecone indexing
  --test-query        Test querying after indexing
```

## Output Files

After running Phase 2, the following files are created in `data/embeddings/`:

| File | Description | Size (9 funds) |
|------|-------------|----------------|
| `fund_chunks.json` | All text chunks | ~758 KB |
| `fund_embeddings.npy` | Numpy array of embeddings (36 × 384) | ~108 KB |
| `fund_embeddings_metadata.json` | Chunk metadata | ~758 KB |
| `fund_embeddings_full.json` | Combined embeddings + metadata | ~1.1 MB |

## Statistics

**Current Dataset (9 funds):**
- Total chunks: 36 (4 per fund)
- Embedding dimension: 384
- Total vectors: 36

**Chunk Distribution:**
- overview: 9 chunks
- financial: 9 chunks
- risk: 9 chunks
- documents: 9 chunks

## Metadata Filters

These filters enable precise retrieval in Phase 3:

| Filter | Type | Example Values |
|--------|------|----------------|
| `fund_name` | string | "SBI ELSS Tax Saver Fund Direct Growth" |
| `amc` | string | "SBI Mutual Fund" |
| `category` | string | "ELSS", "Equity Small Cap" |
| `risk_level` | string | "Very High", "High", "Moderate" |
| `is_elss` | boolean | true, false |
| `chunk_type` | string | "overview", "financial", "risk", "documents" |

## Integration with Phase 3

Phase 2 outputs are consumed by Phase 3 (Retrieval & Query Handling):

```python
# Phase 3 will load these files
chunks = json.load(open('data/embeddings/fund_chunks.json'))
embeddings = np.load('data/embeddings/fund_embeddings.npy')
metadata = json.load(open('data/embeddings/fund_embeddings_metadata.json'))

# Or query Pinecone directly
results = pinecone_index.query(
    vector=query_embedding,
    filter={"is_elss": True},
    top_k=5
)
```

## Troubleshooting

### PyTorch DLL Error on Windows

If you see `OSError: [WinError 1114]`:
1. Use the demo mode: `python scripts/run_phase2_demo.py`
2. Or install Visual C++ Redistributable
3. Or use WSL2 on Windows

### Pinecone Connection Issues

```bash
# Verify API key is set
echo %PINECONE_API_KEY%

# Test connection
python -c "from pinecone import Pinecone; pc = Pinecone(api_key='your_key'); print(pc.list_indexes())"
```

## Next Steps

Proceed to **Phase 3: Retrieval & Query Handling** for:
- Query preprocessing and intent classification
- Dense retrieval with metadata filtering
- Hybrid search (dense + sparse)
- Reranking with cross-encoders

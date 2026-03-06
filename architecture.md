# AI Mutual Fund RAG Chatbot - System Architecture

## Project Overview
A Retrieval-Augmented Generation (RAG) based chatbot that answers user queries about Indian mutual funds using data scraped from Groww's public pages. The system supports fund-specific, attribute-based, and document-based queries.

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    USER INTERFACE LAYER                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │
│  │   Web Chat UI   │  │  Mobile App     │  │  API Endpoint   │  │  Voice Interface│    │
│  │   (React/Vue)   │  │  (Future)       │  │  (REST/GraphQL) │  │  (Future)       │    │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘    │
└───────────┼────────────────────┼────────────────────┼────────────────────┼─────────────┘
            │                    │                    │                    │
            └────────────────────┴────────┬───────────┴────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                   QUERY PROCESSING LAYER                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐    │
│  │                         Query Router & Intent Classifier                         │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │    │
│  │  │ Fund-Specific│  │  Attribute   │  │  Document    │  │   Fallback/General   │ │    │
│  │  │   Queries    │  │   Queries    │  │   Queries    │  │      Queries         │ │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────────────────────┘    │
│                                          │                                              │
│  ┌───────────────────────────────────────┴───────────────────────────────────────────┐  │
│  │                         Query Preprocessor                                         │  │
│  │  • Entity Extraction (Fund Names, AMC, Category)                                  │  │
│  │  • Query Expansion (Synonyms, Related Terms)                                      │  │
│  │  • Query Normalization (Standardize fund names, handle abbreviations)             │  │
│  │  • Context Management (Conversation History)                                      │  │
│  └───────────────────────────────────────┬───────────────────────────────────────────┘  │
└──────────────────────────────────────────┼──────────────────────────────────────────────┘
                                           │
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                   RETRIEVAL LAYER                                        │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐    │
│  │                         Hybrid Retriever                                         │    │
│  │  ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐  │    │
│  │  │   Dense Retrieval   │    │  Sparse Retrieval   │    │  Knowledge Graph    │  │    │
│  │  │   (Vector Search)   │◄──►│  (BM25/TF-IDF)      │◄──►│  (Relationships)    │  │    │
│  │  │                     │    │                     │    │                     │  │    │
│  │  │  • Semantic Search  │    │  • Keyword Search   │    │  • Fund-AMC Links   │  │    │
│  │  │  • Embedding Match  │    │  • Exact Match      │    │  • Category Tree    │  │    │
│  │  │  • Similarity Score │    │  • Token Matching   │    │  • Risk Connections │  │    │
│  │  └──────────┬──────────┘    └──────────┬──────────┘    └──────────┬──────────┘  │    │
│  │             └─────────────────────────┬┴──────────────────────────┘             │    │
│  │                                       ▼                                        │    │
│  │                         ┌─────────────────────────┐                            │    │
│  │                         │    Reranking Engine     │                            │    │
│  │                         │  • Cross-Encoder Model  │                            │    │
│  │                         │  • Recency Boost        │                            │    │
│  │                         │  • Authority Score      │                            │    │
│  │                         └───────────┬─────────────┘                            │    │
│  └─────────────────────────────────────┼──────────────────────────────────────────┘    │
└────────────────────────────────────────┼────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              GENERATION LAYER (LLM)                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐    │
│  │                         Prompt Engineering                                       │    │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐    │    │
│  │  │ System Prompt + Context + Retrieved Chunks + User Query → LLM           │    │    │
│  │  │                                                                         │    │    │
│  │  │ Template:                                                               │    │    │
│  │  │ "You are a mutual fund expert. Answer based ONLY on provided context.   │    │    │
│  │  │  If information is insufficient, say so clearly.                        │    │    │
│  │  │  Context: {retrieved_chunks}                                            │    │    │
│  │  │  Question: {user_query}                                                 │    │    │
│  │  │  Answer:"                                                               │    │    │
│  │  └─────────────────────────────────────────────────────────────────────────┘    │    │
│  │                                                                                  │    │
│  │  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐      │    │
│  │  │   Response Format   │  │   Citation Engine   │  │  Hallucination      │      │    │
│  │  │   • Structured JSON │  │   • Source Links    │  │  Guardrails         │      │    │
│  │  │   • Tabular Data    │  │   • Confidence Score│  │  • Fact Checking    │      │    │
│  │  │   • Natural Language│  │   • Timestamp       │  │  • Uncertainty Flag │      │    │
│  │  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘      │    │
│  └─────────────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              DATA & KNOWLEDGE LAYER                                      │
│                                                                                          │
│  ┌─────────────────────────────┐  ┌─────────────────────────────┐  ┌─────────────────┐  │
│  │    VECTOR DATABASE          │  │    DOCUMENT STORE           │  │   KNOWLEDGE     │  │
│  │    (Pinecone/Weaviate)      │  │    (MongoDB/PostgreSQL)     │  │   GRAPH         │  │
│  │                             │  │                             │  │   (Neo4j)       │  │
│  │  ┌─────────────────────┐    │  │  ┌─────────────────────┐    │  │                 │  │
│  │  │  Fund Embeddings    │    │  │  │  Fund Metadata      │    │  │  • AMC Nodes    │  │
│  │  │  • Dense vectors    │    │  │  │  • Raw HTML/JSON    │    │  │  • Fund Nodes   │  │
│  │  │  • Metadata filters │    │  │  │  • Document chunks  │    │  │  • Category     │  │
│  │  │  • Namespace: funds │    │  │  │  • FAQ documents    │    │  │    Hierarchy    │  │
│  │  ├─────────────────────┤    │  │  ├─────────────────────┤    │  │  • Risk Links   │  │
│  │  │  Doc Embeddings     │    │  │  │  Crawl History      │    │  │                 │  │
│  │  │  • Procedure docs   │    │  │  │  • Update Logs      │    │  └─────────────────┘  │
│  │  │  • FAQ embeddings   │    │  │  └─────────────────────┘    │                       │
│  │  │  • Namespace: docs  │    │  │                             │                       │
│  │  └─────────────────────┘    │  └─────────────────────────────┘                       │
│  └─────────────────────────────┘                                                        │
│                                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐    │
│  │                         EMBEDDING MODEL                                          │    │
│  │  • Primary: sentence-transformers/all-MiniLM-L6-v2 (384d) - Fast, good quality  │    │
│  │  • Alternative: BAAI/bge-large-en (1024d) - Higher quality, slower              │    │
│  │  • Fine-tuned option: Domain-specific on financial corpus                       │    │
│  └─────────────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                         ▲
                                         │
┌────────────────────────────────────────┼────────────────────────────────────────────────┐
│                              DATA PIPELINE LAYER                                         │
│                                         │                                                │
│  ┌─────────────────────────────────────┴────────────────────────────────────────────┐   │
│  │                         PHASE 1: DATA COLLECTION & PROCESSING                     │   │
│  │                                                                                   │   │
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐               │   │
│  │  │  Web Scraper    │───►│  HTML Parser    │───►│  Data Cleaner   │               │   │
│  │  │  (Scrapy/BS4)   │    │  (BeautifulSoup)│    │  (Pandas/Regex) │               │   │
│  │  │                 │    │                 │    │                 │               │   │
│  │  │ • Respect       │    │ • Extract fund  │    │ • Normalize     │               │   │
│  │  │   robots.txt    │    │   attributes    │    │   fund names    │               │   │
│  │  │ • Rate limiting │    │ • Handle        │    │ • Standardize   │               │   │
│  │  │ • Retry logic   │    │   dynamic JS    │    │   numbers       │               │   │
│  │  │ • Proxy rotation│    │ • Parse tables  │    │ • Remove        │               │   │
│  │  │                 │    │                 │    │   duplicates    │               │   │
│  │  └─────────────────┘    └─────────────────┘    └────────┬────────┘               │   │
│  │                                                         │                        │   │
│  │  ┌──────────────────────────────────────────────────────┘                        │   │
│  │  │                                                                              │   │
│  │  ▼                                                                              │   │
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐               │   │
│  │  │  Schema Design  │───►│  Data Validator │───►│  Structured DB  │               │   │
│  │  │  (Pydantic)     │    │  (Cerberus)     │    │  (PostgreSQL)   │               │   │
│  │  │                 │    │                 │    │                 │               │   │
│  │  │ • Fund schema   │    │ • Type checking │    │ • Relational    │               │   │
│  │  │ • AMC schema    │    │ • Range checks  │    │   schema        │               │   │
│  │  │ • Category      │    │ • Missing data  │    │ • Indexed       │               │   │
│  │  │   schema        │    │   detection     │    │   columns       │               │   │
│  │  └─────────────────┘    └─────────────────┘    └─────────────────┘               │   │
│  │                                                                                   │   │
│  └───────────────────────────────────────────────────────────────────────────────────┘   │
│                                         │                                                │
│  ┌─────────────────────────────────────┴────────────────────────────────────────────┐   │
│  │                         PHASE 2: EMBEDDING & INDEXING                             │   │
│  │                                                                                   │   │
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐               │   │
│  │  │  Text Chunker   │───►│  Embedding      │───►│  Vector Store   │               │   │
│  │  │  (LangChain)    │    │  Generator      │    │  Upsert         │               │   │
│  │  │                 │    │                 │    │                 │               │   │
│  │  │ • Semantic      │    │ • Batch         │    │ • Bulk insert   │               │   │
│  │  │   chunking      │    │   processing    │    │ • Metadata      │               │   │
│  │  │ • Overlap       │    │ • GPU           │    │   attachment    │               │   │
│  │  │   windows       │    │   acceleration  │    │ • Index         │               │   │
│  │  │ • Fund vs doc   │    │                 │    │   optimization  │               │   │
│  │  │   separation    │    │                 │    │                 │               │   │
│  │  └─────────────────┘    └─────────────────┘    └─────────────────┘               │   │
│  │                                                                                   │   │
│  └───────────────────────────────────────────────────────────────────────────────────┘   │
│                                         │                                                │
│  ┌─────────────────────────────────────┴────────────────────────────────────────────┐   │
│  │                         PHASE 3: RETRIEVAL & QUERY HANDLING                       │   │
│  │                                                                                   │   │
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐               │   │
│  │  │  Query Parser   │───►│  Retriever      │───►│  Result         │               │   │
│  │  │                 │    │  Orchestrator   │    │  Post-Processor │               │   │
│  │  │ • Intent        │    │                 │    │                 │               │   │
│  │  │   classification│    │ • Multi-index   │    │ • Deduplication │               │   │
│  │  │ • Entity        │    │   search        │    │ • Score         │               │   │
│  │  │   extraction    │    │ • Hybrid        │    │   normalization │               │   │
│  │  │ • Query         │    │   scoring       │    │ • Top-k         │               │   │
│  │  │   expansion     │    │ • Filter        │    │   selection     │               │   │
│  │  │                 │    │   application   │    │                 │               │   │
│  │  └─────────────────┘    └─────────────────┘    └─────────────────┘               │   │
│  │                                                                                   │   │
│  └───────────────────────────────────────────────────────────────────────────────────┘   │
│                                         │                                                │
│  ┌─────────────────────────────────────┴────────────────────────────────────────────┐   │
│  │                         PHASE 4: LLM INTEGRATION                                  │   │
│  │                                                                                   │   │
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐               │   │
│  │  │  Context        │───►│  LLM API        │───►│  Response       │               │   │
│  │  │  Assembler      │    │  Client         │    │  Formatter      │               │   │
│  │  │                 │    │                 │    │                 │               │   │
│  │  │ • Prompt        │    │ • OpenAI/       │    │ • JSON schema   │               │   │
│  │  │   construction  │    │   Anthropic/    │    │ • Citation      │               │   │
│  │  │ • Token         │    │   Local LLM     │    │   injection     │               │   │
│  │  │   management    │    │ • Retry logic   │    │ • Confidence    │               │   │
│  │  │ • Context       │    │ • Streaming     │    │   scoring       │               │   │
│  │  │   window opt    │    │                 │    │                 │               │   │
│  │  └─────────────────┘    └─────────────────┘    └─────────────────┘               │   │
│  │                                                                                   │   │
│  └───────────────────────────────────────────────────────────────────────────────────┘   │
│                                         │                                                │
│  ┌─────────────────────────────────────┴────────────────────────────────────────────┐   │
│  │                         PHASE 5: TESTING & EVALUATION                             │   │
│  │                                                                                   │   │
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐               │   │
│  │  │  Test Suite     │    │  Evaluation     │    │  Feedback Loop  │               │   │
│  │  │                 │    │  Metrics        │    │                 │               │   │
│  │  │ • Unit tests    │    │ • Retrieval     │    │ • User feedback │               │   │
│  │  │ • Integration   │    │   accuracy      │    │ • A/B testing   │               │   │
│  │  │ • Load tests    │    │ • Answer        │    │ • Continuous    │               │   │
│  │  │ • Edge cases    │    │   relevance     │    │   improvement   │               │   │
│  │  │                 │    │ • Latency       │    │                 │               │   │
│  │  └─────────────────┘    └─────────────────┘    └─────────────────┘               │   │
│  │                                                                                   │   │
│  └───────────────────────────────────────────────────────────────────────────────────┘   │
│                                         │                                                │
│  ┌─────────────────────────────────────┴────────────────────────────────────────────┐   │
│  │                         PHASE 6: CHAT APPLICATION                                 │   │
│  │                                                                                   │   │
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐               │   │
│  │  │  FastAPI        │    │  Next.js        │    │  WebSocket      │               │   │
│  │  │  Backend        │    │  Frontend       │    │  Real-time      │               │   │
│  │  │                 │    │                 │    │                 │               │   │
│  │  │ • /chat endpoint│    │ • Chat UI       │    │ • Streaming     │               │   │
│  │  │ • /funds API    │    │ • Fund browser  │    │   responses     │               │   │
│  │  │ • Session mgmt  │    │ • Components    │    │ • Live updates  │               │   │
│  │  │ • Rate limiting │    │ • State mgmt    │    │                 │               │   │
│  │  └─────────────────┘    └─────────────────┘    └─────────────────┘               │   │
│  │                                                                                   │   │
│  └───────────────────────────────────────────────────────────────────────────────────┘   │
│                                         │                                                │
│  ┌─────────────────────────────────────┴────────────────────────────────────────────┐   │
│  │                         PHASE 7: DATA UPDATE SCHEDULER                            │   │
│  │                                                                                   │   │
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐               │   │
│  │  │  Apache         │    │  Change         │    │  Pipeline       │               │   │
│  │  │  Airflow        │    │  Detector       │    │  Orchestrator   │               │   │
│  │  │                 │    │                 │    │                 │               │   │
│  │  │ • Daily DAG     │    │ • Hash compare  │    │ • Trigger P1-3  │               │   │
│  │  │ • Retry logic   │    │ • Detect new    │    │ • Cache refresh │               │   │
│  │  │ • Alerts        │    │ • Track changes │    │ • Notifications │               │   │
│  │  └─────────────────┘    └─────────────────┘    └─────────────────┘               │   │
│  │                                                                                   │   │
│  │  Schedule: Daily at 2:00 AM IST                                                   │   │
│  │  Action: Auto-trigger Phase 1 → Phase 2 → Phase 3 on data changes                 │   │
│  │                                                                                   │   │
│  └───────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Explanation

### 1. User Interface Layer
| Component | Purpose | Technology Options |
|-----------|---------|-------------------|
| Web Chat UI | Primary interaction interface | React, Vue.js, Next.js |
| API Endpoint | Programmatic access | FastAPI, Flask, Express |
| Mobile App | Future mobile support | React Native, Flutter |
| Voice Interface | Accessibility feature | Whisper, Speech-to-Text APIs |

### 2. Query Processing Layer
| Component | Purpose | Details |
|-----------|---------|---------|
| **Query Router** | Classifies query type | Uses lightweight classifier (DistilBERT) or rule-based |
| **Intent Classifier** | Determines user intent | Categories: fund_info, comparison, procedure, recommendation |
| **Query Preprocessor** | Normalizes and enriches queries | Entity extraction, synonym expansion, abbreviation handling |
| **Context Manager** | Maintains conversation state | Redis/Memory for session management |

### 3. Retrieval Layer
| Component | Purpose | Implementation |
|-----------|---------|----------------|
| **Dense Retriever** | Semantic similarity search | Vector DB with cosine similarity |
| **Sparse Retriever** | Keyword-based search | BM25, TF-IDF on inverted index |
| **Knowledge Graph** | Relationship-based retrieval | Neo4j for fund-AMC-category connections |
| **Reranking Engine** | Improves result relevance | Cross-encoder model (ms-marco-MiniLM) |

### 4. Generation Layer
| Component | Purpose | Details |
|-----------|---------|---------|
| **Prompt Engineering** | Crafts effective prompts | Template-based with dynamic context |
| **Response Formatter** | Structures output | JSON for structured data, markdown for prose |
| **Citation Engine** | Sources attribution | Links back to Groww pages |
| **Hallucination Guardrails** | Prevents false information | Confidence thresholds, fact-checking |

### 5. Data Pipeline Layer
Detailed in Phase sections below.

---

## Tech Stack Suggestions

### Core Framework
| Layer | Recommended | Alternatives | Rationale |
|-------|-------------|--------------|-----------|
| **Backend** | Python 3.11+ | Node.js | Rich ML ecosystem |
| **Web Framework** | FastAPI | Flask, Django | Async support, auto-docs |
| **LLM Orchestration** | LangChain | LlamaIndex, Haystack | Mature, well-documented |
| **Data Processing** | Pandas, NumPy | Polars | Industry standard |

### Data Storage
| Component | Recommended | Alternatives | Rationale |
|-----------|-------------|--------------|-----------|
| **Vector Database** | Pinecone | Weaviate, Chroma, Qdrant | Managed, scalable, metadata filtering |
| **Document Store** | PostgreSQL + JSONB | MongoDB | ACID compliance, JSON flexibility |
| **Cache** | Redis | Memcached | Session management, rate limiting |
| **Knowledge Graph** | Neo4j (optional) | Amazon Neptune | Relationship queries |

### ML/AI Components
| Component | Recommended | Alternatives | Rationale |
|-----------|-------------|--------------|-----------|
| **Embedding Model** | sentence-transformers/all-MiniLM-L6-v2 | BAAI/bge-large-en | Speed vs quality tradeoff |
| **Reranker** | cross-encoder/ms-marco-MiniLM-L-6-v2 | Cohere Rerank | Improved retrieval accuracy |
| **LLM** | GPT-4 / Claude 3 | Llama 2, Mistral | Quality vs cost tradeoff |
| **Intent Classifier** | DistilBERT fine-tuned | Rule-based | Lightweight, fast |

### Data Collection
| Component | Recommended | Alternatives | Rationale |
|-----------|-------------|--------------|-----------|
| **Web Scraping** | Scrapy + Playwright | Selenium, BeautifulSoup | Handles dynamic content |
| **Scheduling** | Apache Airflow | Cron, Prefect | Orchestration, monitoring |
| **Data Validation** | Pydantic, Cerberus | JSON Schema | Type safety |

### Infrastructure
| Component | Recommended | Alternatives |
|-----------|-------------|--------------|
| **Containerization** | Docker | Podman |
| **Orchestration** | Docker Compose (local) | Kubernetes (production) |
| **Monitoring** | Prometheus + Grafana | Datadog, New Relic |
| **Logging** | ELK Stack | Splunk, CloudWatch |

---

## Folder Structure

```
mutual-fund-rag-chatbot/
│
├── 📁 .github/
│   └── workflows/
│       ├── ci.yml
│       └── data-update.yml
│
├── 📁 config/
│   ├── __init__.py
│   ├── settings.py              # Central configuration
│   ├── logging.yaml             # Logging configuration
│   ├── prompts/                 # LLM prompt templates
│   │   ├── fund_query.txt
│   │   ├── comparison_query.txt
│   │   ├── procedure_query.txt
│   │   └── system_prompt.txt
│   └── schemas/                 # Data validation schemas
│       ├── fund_schema.json
│       └── amc_schema.json
│
├── 📁 data/
│   ├── raw/                     # Raw scraped data
│   │   └── groww/
│   ├── processed/               # Cleaned structured data
│   │   ├── funds.parquet
│   │   ├── amcs.parquet
│   │   └── categories.parquet
│   ├── embeddings/              # Pre-computed embeddings
│   │   ├── fund_embeddings.npy
│   │   └── doc_embeddings.npy
│   └── knowledge_graph/         # Graph data
│       └── graph_export.cypher
│
├── 📁 src/
│   ├── __init__.py
│   │
│   ├── 📁 api/                  # FastAPI application
│   │   ├── __init__.py
│   │   ├── main.py              # Application entry point
│   │   ├── dependencies.py      # FastAPI dependencies
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── chat.py          # Chat endpoints
│   │   │   ├── funds.py         # Fund data endpoints
│   │   │   └── health.py        # Health check
│   │   └── models/
│   │       ├── __init__.py
│   │       ├── requests.py      # API request models
│   │       └── responses.py     # API response models
│   │
│   ├── 📁 chatbot/              # Core chatbot logic
│   │   ├── __init__.py
│   │   ├── engine.py            # Main chatbot orchestrator
│   │   ├── query_processor.py   # Query preprocessing
│   │   ├── retriever.py         # Retrieval logic
│   │   ├── generator.py         # LLM response generation
│   │   └── memory.py            # Conversation memory
│   │
│   ├── 📁 data_pipeline/        # Phase 1: Data Collection
│   │   ├── __init__.py
│   │   ├── scraper/
│   │   │   ├── __init__.py
│   │   │   ├── base.py          # Base scraper class
│   │   │   ├── groww_scraper.py # Groww-specific scraper
│   │   │   └── utils.py         # Scraping utilities
│   │   ├── parser/
│   │   │   ├── __init__.py
│   │   │   ├── html_parser.py   # HTML extraction
│   │   │   └── fund_extractor.py # Fund data extraction
│   │   ├── cleaner/
│   │   │   ├── __init__.py
│   │   │   ├── normalizer.py    # Data normalization
│   │   │   └── validator.py     # Data validation
│   │   └── schema/
│   │       ├── __init__.py
│   │       ├── fund.py          # Fund Pydantic models
│   │       ├── amc.py           # AMC Pydantic models
│   │       └── enums.py         # Enumerations
│   │
│   ├── 📁 embedding/            # Phase 2: Embedding & Indexing
│   │   ├── __init__.py
│   │   ├── chunker.py           # Text chunking strategies
│   │   ├── embedder.py          # Embedding generation
│   │   ├── indexer.py           # Vector DB indexing
│   │   └── metadata.py          # Metadata management
│   │
│   ├── 📁 retrieval/            # Phase 3: Retrieval
│   │   ├── __init__.py
│   │   ├── dense_retriever.py   # Vector search
│   │   ├── sparse_retriever.py  # BM25/keyword search
│   │   ├── hybrid_retriever.py  # Combined retrieval
│   │   ├── reranker.py          # Result reranking
│   │   └── filters.py           # Metadata filters
│   │
│   ├── 📁 llm/                  # Phase 4: LLM Integration
│   │   ├── __init__.py
│   │   ├── client.py            # LLM API client
│   │   ├── prompt_builder.py    # Dynamic prompt construction
│   │   ├── response_parser.py   # Output parsing
│   │   └── guardrails.py        # Safety checks
│   │
│   ├── 📁 evaluation/           # Phase 5: Testing
│   │   ├── __init__.py
│   │   ├── metrics.py           # Evaluation metrics
│   │   ├── test_cases.py        # Test case definitions
│   │   ├── benchmark.py         # Benchmark runner
│   │   └── feedback.py          # User feedback collection
│   │
│   └── 📁 utils/
│       ├── __init__.py
│       ├── logging.py
│       ├── exceptions.py
│       └── helpers.py
│
├── 📁 tests/
│   ├── __init__.py
│   ├── conftest.py              # Pytest configuration
│   ├── unit/
│   │   ├── test_scraper.py
│   │   ├── test_parser.py
│   │   ├── test_retriever.py
│   │   └── test_generator.py
│   ├── integration/
│   │   ├── test_api.py
│   │   ├── test_pipeline.py
│   │   └── test_end_to_end.py
│   └── fixtures/
│       ├── sample_funds.json
│       └── sample_queries.json
│
├── 📁 notebooks/                # Exploration & analysis
│   ├── 01_data_exploration.ipynb
│   ├── 02_embedding_analysis.ipynb
│   └── 03_retrieval_evaluation.ipynb
│
├── 📁 scripts/                  # Utility scripts
│   ├── scrape_groww.py          # Manual scrape trigger
│   ├── update_embeddings.py     # Embedding update
│   ├── evaluate_retrieval.py    # Retrieval evaluation
│   └── seed_database.py         # Database seeding
│
├── 📁 docs/                     # Documentation
│   ├── architecture.md          # This file
│   ├── api_spec.md              # API specification
│   └── data_dictionary.md       # Field definitions
│
├── 📁 frontend/                 # Phase 6: Frontend Application
│   ├── 📁 app/
│   │   ├── 📁 (routes)/
│   │   │   ├── page.tsx         # Chat interface (home)
│   │   │   ├── 📁 funds/
│   │   │   │   ├── page.tsx     # Fund browser
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx # Fund detail
│   │   │   └── layout.tsx
│   │   ├── 📁 api/              # Next.js API routes (if needed)
│   │   └── globals.css
│   ├── 📁 components/
│   │   ├── 📁 chat/
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   ├── MessageList.tsx
│   │   │   ├── ChatInput.tsx
│   │   │   ├── SourceCard.tsx
│   │   │   ├── SuggestionChips.tsx
│   │   │   └── TypingIndicator.tsx
│   │   ├── 📁 funds/
│   │   │   ├── FundCard.tsx
│   │   │   ├── FundDetail.tsx
│   │   │   ├── FundList.tsx
│   │   │   └── FilterPanel.tsx
│   │   └── ui/                  # shadcn/ui components
│   ├── 📁 hooks/
│   │   ├── useChat.ts           # WebSocket hook
│   │   ├── useFunds.ts          # Fund data fetching
│   │   ├── useSearch.ts         # Search with debounce
│   │   └── useWebSocket.ts      # WebSocket connection
│   ├── 📁 stores/
│   │   ├── chatStore.ts         # Zustand chat state
│   │   ├── fundStore.ts         # Fund state
│   │   └── userStore.ts         # User preferences
│   ├── 📁 lib/
│   │   ├── api.ts               # API client
│   │   ├── utils.ts
│   │   └── constants.ts
│   ├── 📁 types/
│   │   ├── fund.ts
│   │   ├── chat.ts
│   │   └── api.ts
│   ├── next.config.js
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── package.json
│
├── 📁 scheduler/                # Phase 7: Data Update Scheduler
│   ├── 📁 dags/
│   │   └── mutual_fund_update.py    # Airflow DAG
│   ├── 📁 plugins/
│   │   └── custom_operators.py
│   ├── change_detector.py       # Detect data changes
│   ├── orchestrator.py          # Pipeline orchestration
│   ├── notifier.py              # Alert notifications
│   ├── monitor.py               # Health monitoring
│   └── config.yaml              # Scheduler configuration
│
├── 📁 deployment/
│   ├── docker/
│   │   ├── Dockerfile.backend
│   │   ├── Dockerfile.frontend
│   │   ├── Dockerfile.scheduler
│   │   ├── docker-compose.yml
│   │   └── .dockerignore
│   └── k8s/                     # Kubernetes manifests (future)
│
├── .env.example                 # Environment variables template
├── .env.backend.example
├── .env.frontend.example
├── .gitignore
├── requirements.txt             # Python dependencies
├── requirements-dev.txt         # Dev dependencies
├── pyproject.toml               # Project metadata
├── setup.py                     # Package setup
└── README.md
```

---

## Data Flow

### 1. Data Ingestion Flow (Phase 1 - Enhanced)

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              PHASE 1: DATA COLLECTION & PROCESSING                       │
│                                                                                          │
│  SEED URLs:                                                                              │
│  • bandhan-small-cap-fund-direct-growth                                                  │
│  • parag-parikh-long-term-value-fund-direct-growth                                       │
│  • hdfc-mid-cap-fund-direct-growth                                                       │
│  • nippon-india-small-cap-fund-direct-growth                                             │
│  • icici-prudential-large-cap-fund-direct-growth                                         │
│  • tata-small-cap-fund-direct-growth                                                     │
│  • axis-small-cap-fund-direct-growth                                                     │
│  • sbi-small-midcap-fund-direct-growth                                                   │
│                                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐    │
│  │  STEP 1: WEB CRAWLING                                                            │    │
│  │  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐   │    │
│  │  │   Groww     │────►│    URL      │────►│   Crawler   │────►│   HTML      │   │    │
│  │  │   Listing   │     │  Discovery  │     │ (Playwright)│     │   Cache     │   │    │
│  │  │   Page      │     │             │     │             │     │             │   │    │
│  │  └─────────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘   │    │
│  │  https://groww.in/mutual-funds/                                     │          │    │
│  └─────────────────────────────────────────────────────────────────────┼──────────┘    │
│                                                                        │                │
│                                                                        ▼                │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐    │
│  │  STEP 2: DATA EXTRACTION                                                         │    │
│  │  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐   │    │
│  │  │   HTML      │────►│   Parser    │────►│   Fund      │────►│   Raw       │   │    │
│  │  │   Cache     │     │(BeautifulSoup)│    │  Extractor  │     │   JSON      │   │    │
│  │  │             │     │             │     │             │     │             │   │    │
│  │  └─────────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘   │    │
│  │  Extract: fund_name, amc, category, expense_ratio,                  │          │    │
│  │           exit_load, min_sip, lock_in, risk_level,                  │          │    │
│  │           benchmark, description, factsheet/sid/kim urls            │          │    │
│  └─────────────────────────────────────────────────────────────────────┼──────────┘    │
│                                                                        │                │
│                                                                        ▼                │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐    │
│  │  STEP 3: DATA PROCESSING                                                         │    │
│  │  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐   │    │
│  │  │   Raw       │────►│   Cleaner   │────►│  Normalizer │────►│  Validator  │   │    │
│  │  │   JSON      │     │             │     │             │     │ (Pydantic)  │   │    │
│  │  │             │     │ • Missing   │     │ • Standard  │     │             │   │    │
│  │  │             │     │   values    │     │   formats   │     │ • Type check│   │    │
│  │  │             │     │ • Outliers  │     │ • Normalize │     │ • Range     │   │    │
│  │  │             │     │             │     │   text      │     │   validate  │   │    │
│  │  └─────────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘   │    │
│  └─────────────────────────────────────────────────────────────────────┼──────────┘    │
│                                                                        │                │
│                                                                        ▼                │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐    │
│  │  STEP 4: STORAGE                                                                 │    │
│  │  ┌─────────────────────────────┐     ┌─────────────────────────────┐           │    │
│  │  │   PostgreSQL                │     │   JSON Backup               │           │    │
│  │  │   (Structured)              │     │   (Raw + Processed)         │           │    │
│  │  │                             │     │                             │           │    │
│  │  │  funds table                │     │  • raw_extractions/         │           │    │
│  │  │  ├── fund_name              │     │  • processed_funds/         │           │    │
│  │  │  ├── amc                    │     │  • extraction_logs/         │           │    │
│  │  │  ├── category               │     │                             │           │    │
│  │  │  ├── expense_ratio          │     │                             │           │    │
│  │  │  ├── exit_load              │     │                             │           │    │
│  │  │  ├── minimum_sip            │     │                             │           │    │
│  │  │  ├── lock_in_period         │     │                             │           │    │
│  │  │  ├── risk_level             │     │                             │           │    │
│  │  │  ├── benchmark              │     │                             │           │    │
│  │  │  ├── description            │     │                             │           │    │
│  │  │  ├── factsheet_url          │     │                             │           │    │
│  │  │  ├── sid_url                │     │                             │           │    │
│  │  │  ├── kim_url                │     │                             │           │    │
│  │  │  ├── source_url             │     │                             │           │    │
│  │  │  ├── scraped_at             │     │                             │           │    │
│  │  │  └── is_elss                │     │                             │           │    │
│  │  │                             │     │                             │           │    │
│  │  │  Indexes:                   │     │                             │           │    │
│  │  │  ├── idx_fund_name          │     │                             │           │    │
│  │  │  ├── idx_amc                │     │                             │           │    │
│  │  │  ├── idx_category           │     │                             │           │    │
│  │  │  └── idx_risk_level         │     │                             │           │    │
│  │  └─────────────────────────────┘     └─────────────────────────────┘           │    │
│  └─────────────────────────────────────────────────────────────────────────────────┘    │
│                                                                        │                │
│                                                                        ▼                │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐    │
│  │  STEP 5: RAG PREPARATION                                                         │    │
│  │  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐   │    │
│  │  │  PostgreSQL │────►│   Chunker   │────►│  Embedding  │────►│   Vector    │   │    │
│  │  │   (Data)    │     │             │     │  Generator  │     │    Store    │   │    │
│  │  │             │     │ • Fund info │     │             │     │             │   │    │
│  │  │             │     │ • Desc      │     │ • MiniLM    │     │ • Pinecone  │   │    │
│  │  │             │     │ • Attrs     │     │ • 384-dim   │     │ • Metadata  │   │    │
│  │  └─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘   │    │
│  │                                                                                  │    │
│  │  Metadata Filters: fund_name, amc, category, risk_level, is_elss                 │    │
│  └─────────────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

**Detailed Steps:**
1. **URL Discovery**: Scraper discovers fund URLs from `groww.in/mutual-funds/` listing page
2. **Seed URL Testing**: Validate extraction pipeline on 8 provided seed URLs
3. **Crawling**: Downloads HTML pages using Playwright with rate limiting (1 req/sec)
4. **Caching**: Stores raw HTML for reprocessing and debugging
5. **Extraction**: Extracts fund attributes using CSS selectors (fund_name, amc, category, expense_ratio, exit_load, minimum_sip, lock_in_period, risk_level, benchmark, description, factsheet_url, sid_url, kim_url)
6. **Cleaning**: Handles missing values, removes outliers, validates URLs
7. **Normalization**: Standardizes formats (expense ratio %, amounts, risk levels)
8. **Validation**: Validates against Pydantic schema with type and range checks
9. **Storage**: Saves to PostgreSQL with JSONB for flexibility + JSON backup
10. **Chunking**: Splits fund data into semantic chunks (overview, attributes, risk, documents)
11. **Embedding**: Generates 384-dimensional vectors using sentence-transformers/all-MiniLM-L6-v2
12. **Indexing**: Upserts to Pinecone with metadata filters (fund_name, amc, category, risk_level, is_elss)

### 2. Query Processing Flow (Phases 3-4)

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   User      │────►│   Query     │────►│   Intent    │────►│   Entity    │
│   Query     │     │Preprocessor │     │ Classifier  │     │ Extractor   │
└─────────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                                   │
                                                                   ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Formatted │◄────│     LLM     │◄────│   Context   │◄────│  Retriever  │
│   Response  │     │   (GPT-4)   │     │  Assembler  │     │  (Hybrid)   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

**Detailed Steps:**
1. **Receive**: API receives query + conversation ID
2. **Preprocess**: Normalize text, expand abbreviations
3. **Classify**: Determine query type (fund_info/comparison/procedure)
4. **Extract**: Identify fund names, AMCs, categories using NER
5. **Retrieve**: Hybrid search (dense + sparse) with metadata filters
6. **Rerank**: Cross-encoder reranks top 100 to top 10
7. **Assemble**: Build prompt with context + query
8. **Generate**: LLM generates response with citations
9. **Format**: Structure as JSON with confidence scores
10. **Return**: Send to user with source links

---

## Phase-wise Implementation Plan

### Phase 1: Data Collection & Processing

**Objective**: Build robust data pipeline from Groww to structured storage with comprehensive extraction, cleaning, and RAG preparation.

---

#### 1.1 Web Crawling Strategy

**Primary Data Source:**
- **Listing Page**: `https://groww.in/mutual-funds/` - For discovering all available fund URLs
- **Individual Pages**: Fund-specific pages for detailed attribute extraction

**Seed URLs for Testing & Schema Validation:**
```
https://groww.in/mutual-funds/bandhan-small-cap-fund-direct-growth
https://groww.in/mutual-funds/parag-parikh-long-term-value-fund-direct-growth
https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth
https://groww.in/mutual-funds/nippon-india-small-cap-fund-direct-growth
https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth
https://groww.in/mutual-funds/tata-small-cap-fund-direct-growth
https://groww.in/mutual-funds/axis-small-cap-fund-direct-growth
https://groww.in/mutual-funds/sbi-small-midcap-fund-direct-growth
```

**Crawling Architecture:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         WEB CRAWLING PIPELINE                                │
│                                                                              │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐       │
│  │   URL Discovery │────►│   URL Queue     │────►│   Page Fetcher  │       │
│  │                 │     │                 │     │                 │       │
│  │ • Listing page  │     │ • Priority:     │     │ • Playwright    │       │
│  │   scraping      │     │   Seed URLs     │     │   for JS render │       │
│  │ • Pagination    │     │ • Deduplication │     │ • Rate limit:   │       │
│  │ • Sitemap parse │     │ • Retry queue   │     │   1 req/sec     │       │
│  └─────────────────┘     └─────────────────┘     └─────────────────┘       │
│                                                              │               │
│                                                              ▼               │
│                                                   ┌─────────────────┐       │
│                                                   │   HTML Storage  │       │
│                                                   │   (Raw Cache)   │       │
│                                                   └─────────────────┘       │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Crawling Components:**

| Component | Purpose | Implementation |
|-----------|---------|----------------|
| **URL Discovery** | Extract all fund URLs from listing page | Scrapy spider with pagination handling |
| **Seed URL Loader** | Priority processing of test URLs | Configuration-driven URL list |
| **Page Fetcher** | Download fund pages with JavaScript rendering | Playwright/Scrapy-Playwright |
| **Rate Limiter** | Respect server resources | Token bucket algorithm (1 req/sec) |
| **Retry Handler** | Handle transient failures | Exponential backoff (max 3 retries) |
| **HTML Cache** | Store raw HTML for reprocessing | Local filesystem / S3 |

---

#### 1.2 Data Extraction

**Target Fields to Extract:**

| Field | Description | Example | Extraction Method |
|-------|-------------|---------|-------------------|
| **Fund Name** | Complete fund name with plan type | "Bandhan Small Cap Fund Direct Plan Growth" | CSS Selector: `h1` or `[data-testid="fund-name"]` |
| **AMC** | Asset Management Company | "Bandhan Mutual Fund" | CSS Selector: `.amc-name` or header parsing |
| **Fund Category** | SEBI category classification | "Small Cap Fund" | CSS Selector: `.category-tag` |
| **Expense Ratio** | Annual expense ratio percentage | "0.69%" | CSS Selector: `.expense-ratio .value` |
| **Exit Load** | Exit load structure | "0-365 days: 1%, >365 days: 0%" | CSS Selector: `.exit-load .value` |
| **Minimum SIP** | Minimum SIP amount | "₹100" | CSS Selector: `.min-sip .value` |
| **Lock-in Period** | Lock-in period for ELSS (years) | "3" | CSS Selector: `.lock-in .value` or null |
| **Riskometer** | Risk level indicator | "Very High" | CSS Selector: `.riskometer .level` |
| **Benchmark Index** | Fund's benchmark | "NIFTY Smallcap 250 Total Return Index" | CSS Selector: `.benchmark .value` |
| **Fund Description** | Investment objective/description | "The fund seeks to generate..." | CSS Selector: `.fund-description` |
| **Factsheet URL** | Link to factsheet PDF | Document download link | CSS Selector: `a[href*="factsheet"]` |
| **SID URL** | Scheme Information Document | Document download link | CSS Selector: `a[href*="sid"]` |
| **KIM URL** | Key Information Memorandum | Document download link | CSS Selector: `a[href*="kim"]` |

**Extraction Architecture:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA EXTRACTION PIPELINE                             │
│                                                                              │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐       │
│  │   Raw HTML      │────►│   HTML Parser   │────►│   Fund Extractor│       │
│  │                 │     │                 │     │                 │       │
│  │ Cached pages    │     │ • BeautifulSoup │     │ • CSS selectors │       │
│  │ from crawler    │     │ • XPath support │     │ • Regex patterns│       │
│  │                 │     │ • Error handling│     │ • Multi-field   │       │
│  └─────────────────┘     └─────────────────┘     └────────┬────────┘       │
│                                                           │                  │
│                                                           ▼                  │
│                                                ┌─────────────────┐          │
│                                                │  Extracted Data │          │
│                                                │  (Raw JSON)     │          │
│                                                └─────────────────┘          │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Extraction Modules:**

| Module | File | Purpose |
|--------|------|---------|
| **HTML Parser** | `html_parser.py` | Parse HTML structure, handle dynamic content |
| **Fund Extractor** | `fund_extractor.py` | Extract specific fund fields using selectors |
| **Document Extractor** | `document_extractor.py` | Extract download links for Factsheet/SID/KIM |
| **Selector Config** | `selectors.yaml` | Centralized CSS/XPath selectors for maintainability |

---

#### 1.3 Data Processing

**Processing Pipeline:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA PROCESSING PIPELINE                             │
│                                                                              │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐  │
│  │   Raw Data   │──►│   Cleaner    │──►│  Normalizer  │──►│  Validator   │  │
│  │              │   │              │   │              │   │              │  │
│  │ • Strings    │   │ • Handle     │   │ • Standardize│   │ • Type check │  │
│  │ • Numbers    │   │   missing    │   │   formats    │   │ • Range check│  │
│  │ • Dates      │   │ • Remove     │   │ • Normalize  │   │ • Schema     │  │
│  │ • URLs       │   │   outliers   │   │   text       │   │   validation │  │
│  └──────────────┘   └──────────────┘   └──────────────┘   └──────┬───────┘  │
│                                                                  │          │
│                                                                  ▼          │
│                                                       ┌──────────────────┐  │
│                                                       │  Processed Data  │  │
│                                                       │  (Clean JSON)    │  │
│                                                       └──────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Cleaning Operations:**

| Operation | Input | Output | Rule |
|-----------|-------|--------|------|
| **Fund Name Normalization** | "Bandhan Small Cap Fund Direct Plan Growth" | Same | Title case, remove extra spaces |
| **Expense Ratio Parsing** | "0.69%" | 0.69 | Float, remove % symbol |
| **Amount Parsing** | "₹100" | 100 | Integer, remove ₹ and commas |
| **Exit Load Standardization** | "1% on or before 365 days" | "0-365 days: 1%, >365 days: 0%" | Structured format |
| **Risk Level Mapping** | "Very High Risk" | "Very High" | Standardized enum values |
| **Missing Value Handling** | "" or null | null | Consistent null representation |
| **URL Validation** | Relative URL | Absolute URL | Prefix with groww.in |

**Missing Value Strategy:**

| Field | If Missing | Action |
|-------|------------|--------|
| Expense Ratio | null | Flag as incomplete, exclude from expense queries |
| Exit Load | null | Set to "Not Available" |
| Lock-in Period | null | Set to 0 (no lock-in) |
| Fund Description | null | Use category + AMC as fallback |
| Document URLs | null | Log warning, continue processing |

---

#### 1.4 Schema Design

**Fund Schema (Pydantic Model):**
```python
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime
from enum import Enum

class RiskLevel(str, Enum):
    VERY_HIGH = "Very High"
    HIGH = "High"
    MODERATE = "Moderate"
    LOW = "Low"
    VERY_LOW = "Very Low"

class FundCategory(str, Enum):
    LARGE_CAP = "Large Cap Fund"
    MID_CAP = "Mid Cap Fund"
    SMALL_CAP = "Small Cap Fund"
    ELSS = "ELSS (Tax Saver)"
    # ... other SEBI categories

class MutualFund(BaseModel):
    # Identification
    fund_name: str = Field(..., description="Complete fund name")
    amc: str = Field(..., description="Asset Management Company")
    category: FundCategory = Field(..., description="SEBI fund category")
    
    # Financial Attributes
    expense_ratio: Optional[float] = Field(None, ge=0, le=5, description="Annual expense ratio %")
    exit_load: Optional[str] = Field(None, description="Exit load structure")
    minimum_sip: Optional[int] = Field(None, ge=0, description="Minimum SIP amount in INR")
    minimum_lumpsum: Optional[int] = Field(None, ge=0, description="Minimum lumpsum amount")
    lock_in_period: Optional[int] = Field(None, ge=0, description="Lock-in period in years")
    
    # Risk & Benchmark
    risk_level: Optional[RiskLevel] = Field(None, description="Riskometer level")
    benchmark: Optional[str] = Field(None, description="Benchmark index")
    
    # Descriptive
    description: Optional[str] = Field(None, description="Investment objective")
    
    # Document Links
    factsheet_url: Optional[HttpUrl] = Field(None, description="Factsheet PDF URL")
    sid_url: Optional[HttpUrl] = Field(None, description="Scheme Information Document URL")
    kim_url: Optional[HttpUrl] = Field(None, description="Key Information Memorandum URL")
    
    # Metadata
    source_url: HttpUrl = Field(..., description="Groww page URL")
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(default="1.0", description="Schema version")
    
    # Computed Fields
    is_elss: bool = Field(default=False, description="Is ELSS fund")
    
    class Config:
        json_schema_extra = {
            "example": {
                "fund_name": "Bandhan Small Cap Fund Direct Plan Growth",
                "amc": "Bandhan Mutual Fund",
                "category": "Small Cap Fund",
                "expense_ratio": 0.69,
                "exit_load": "0-365 days: 1%, >365 days: 0%",
                "minimum_sip": 100,
                "lock_in_period": None,
                "risk_level": "Very High",
                "benchmark": "NIFTY Smallcap 250 Total Return Index",
                "description": "The fund seeks to generate long-term capital appreciation...",
                "factsheet_url": "https://groww.in/...",
                "source_url": "https://groww.in/mutual-funds/bandhan-small-cap-fund-direct-growth",
                "is_elss": False
            }
        }
```

---

#### 1.5 Storage Strategy

**Dual Storage Architecture:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            STORAGE LAYER                                     │
│                                                                              │
│  ┌─────────────────────────────┐  ┌─────────────────────────────┐          │
│  │   STRUCTURED STORAGE        │  │   DOCUMENT STORE            │          │
│  │   (PostgreSQL)              │  │   (JSON Files / MongoDB)    │          │
│  │                             │  │                             │          │
│  │  funds table                │  │  Raw extracted data         │          │
│  │  ├── id (PK)                │  │  ├── fund_name              │          │
│  │  ├── fund_name              │  │  ├── extracted_fields       │          │
│  │  ├── amc                    │  │  ├── source_url             │          │
│  │  ├── category               │  │  ├── scraped_at             │          │
│  │  ├── expense_ratio          │  │  └── raw_html_ref           │          │
│  │  ├── exit_load              │  │                             │          │
│  │  ├── minimum_sip            │  │  Processing logs            │          │
│  │  ├── lock_in_period         │  │  └── extraction_metadata    │          │
│  │  ├── risk_level             │  │                             │          │
│  │  ├── benchmark              │  │                             │          │
│  │  ├── description            │  │                             │          │
│  │  ├── factsheet_url          │  │                             │          │
│  │  ├── source_url             │  │                             │          │
│  │  ├── scraped_at             │  │                             │          │
│  │  └── is_elss                │  │                             │          │
│  │                             │  │                             │          │
│  │  Indexes:                   │  │                             │          │
│  │  ├── idx_fund_name (GIN)    │  │                             │          │
│  │  ├── idx_amc                │  │                             │          │
│  │  ├── idx_category           │  │                             │          │
│  │  └── idx_risk_level         │  │                             │          │
│  └─────────────────────────────┘  └─────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Storage Specifications:**

| Aspect | Implementation | Rationale |
|--------|----------------|-----------|
| **Primary Store** | PostgreSQL 15+ | ACID compliance, complex queries |
| **JSON Support** | JSONB columns | Flexible schema evolution |
| **Raw Data** | File system / S3 | Preserve original HTML for debugging |
| **Metadata** | Included in records | Source URL, scrape timestamp, version |

---

#### 1.6 RAG Preparation

**Embedding Generation Pipeline:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      RAG PREPARATION PIPELINE                                │
│                                                                              │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐           │
│  │  Cleaned Data   │──►│  Text Chunker   │──►│  Embedding Gen  │           │
│  │  (PostgreSQL)   │   │                 │   │                 │           │
│  │                 │   │ • Fund info     │   │ • MiniLM-L6-v2  │           │
│  │                 │   │ • Description   │   │ • 384-dim vec   │           │
│  │                 │   │ • Attributes    │   │ • Batch process │           │
│  └─────────────────┘   └─────────────────┘   └────────┬────────┘           │
│                                                       │                      │
│                                                       ▼                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         VECTOR DATABASE                              │   │
│  │                                                                      │   │
│  │  Pinecone Index: "mutual-funds"                                      │   │
│  │  ├── Namespace: "fund_info" - Fund descriptions & attributes         │   │
│  │  └── Namespace: "documents" - Factsheets, procedures (future)        │   │
│  │                                                                      │   │
│  │  Vector Record:                                                      │   │
│  │  {                                                                   │   │
│  │    "id": "fund_bandhan_small_cap_001",                               │   │
│  │    "values": [0.023, -0.045, ...],  // 384 dimensions                │   │
│  │    "metadata": {                                                     │   │
│  │      "fund_name": "Bandhan Small Cap Fund Direct Plan Growth",       │   │
│  │      "amc": "Bandhan Mutual Fund",                                   │   │
│  │      "category": "Small Cap Fund",                                   │   │
│  │      "risk_level": "Very High",                                      │   │
│  │      "expense_ratio": 0.69,                                          │   │
│  │      "is_elss": false,                                               │   │
│  │      "source_url": "https://groww.in/mutual-funds/...",              │   │
│  │      "chunk_type": "fund_attributes"                                 │   │
│  │    }                                                                 │   │
│  │  }                                                                   │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Chunking Strategy:**

| Chunk Type | Content | Metadata Filters |
|------------|---------|------------------|
| **Fund Overview** | Fund name, AMC, category, description | fund_name, amc, category |
| **Financial Attributes** | Expense ratio, exit load, minimums | expense_ratio_bucket, has_lock_in |
| **Risk Profile** | Risk level, benchmark, category | risk_level, category |
| **Document References** | Factsheet, SID, KIM links | has_factsheet, has_sid |

**Metadata Filter Design:**

| Filter | Type | Values | Use Case |
|--------|------|--------|----------|
| `fund_name` | string | Full fund name | Exact fund queries |
| `amc` | string | AMC name | AMC-specific filters |
| `category` | string | SEBI category | Category-based search |
| `risk_level` | string | "Very High" to "Very Low" | Risk-based filtering |
| `is_elss` | boolean | true/false | Tax-saver queries |
| `expense_ratio` | float | 0.0 - 5.0 | Cost comparison |
| `chunk_type` | string | "fund_attributes", "description" | Content type filtering |

---

#### 1.7 Phase 1 Task Summary

| Task ID | Task | Description | Output | Dependencies |
|---------|------|-------------|--------|--------------|
| 1.1 | URL Discovery | Scrape listing page, extract all fund URLs | URL list | - |
| 1.2 | Seed URL Testing | Validate extraction on 8 seed URLs | Test results | 1.1 |
| 1.3 | Crawler Development | Build Playwright-based crawler with rate limiting | `groww_crawler.py` | 1.1 |
| 1.4 | HTML Extraction | Build CSS selector-based extractor | `fund_extractor.py` | 1.2 |
| 1.5 | Data Cleaning | Implement normalization rules | `normalizer.py` | 1.4 |
| 1.6 | Schema Definition | Create Pydantic models | `fund.py`, `enums.py` | 1.5 |
| 1.7 | Data Validation | Build validation pipeline | `validator.py` | 1.6 |
| 1.8 | PostgreSQL Setup | Create tables and indexes | Migration scripts | 1.6 |
| 1.9 | Data Ingestion | Store cleaned data in PostgreSQL | Populated DB | 1.7, 1.8 |
| 1.10 | Chunking | Implement text chunking | `chunker.py` | 1.9 |
| 1.11 | Embedding | Generate embeddings | `embedder.py` | 1.10 |
| 1.12 | Vector Indexing | Index in Pinecone | Indexed vectors | 1.11 |
| 1.13 | Pipeline Orchestration | Schedule and monitor pipeline | Airflow DAG | All |

---

#### 1.8 Key Data Fields Summary

```python
Fund Schema (Phase 1 Focus):
- fund_name: str                    # "Bandhan Small Cap Fund Direct Plan Growth"
- amc: str                          # "Bandhan Mutual Fund"
- category: str                     # "Small Cap Fund"
- expense_ratio: Optional[float]    # 0.69
- exit_load: Optional[str]          # "0-365 days: 1%, >365 days: 0%"
- minimum_sip: Optional[int]        # 100
- lock_in_period: Optional[int]     # null (or 3 for ELSS)
- risk_level: Optional[str]         # "Very High"
- benchmark: Optional[str]          # "NIFTY Smallcap 250 Total Return Index"
- description: Optional[str]        # "The fund seeks to generate..."
- factsheet_url: Optional[str]      # Document download link
- sid_url: Optional[str]            # Scheme Information Document
- kim_url: Optional[str]            # Key Information Memorandum
- source_url: str                   # "https://groww.in/mutual-funds/..."
- scraped_at: datetime              # Timestamp
- is_elss: bool                     # Computed field
```

### Phase 2: Embedding & Indexing

**Objective**: Convert structured data to searchable vector representations

| Task | Description | Output |
|------|-------------|--------|
| 2.1 Text Chunking | Implement semantic chunking strategies | `chunker.py` |
| 2.2 Embedding Model | Integrate sentence-transformers | `embedder.py` |
| 2.3 Vector DB Setup | Configure Pinecone/Weaviate | Index schema |
| 2.4 Bulk Indexing | Process and index all funds | Indexed vectors |
| 2.5 Metadata Design | Design filterable metadata schema | Metadata config |
| 2.6 Document Indexing | Index FAQ/procedure documents | Doc namespace |

**Chunking Strategy:**
```
Fund Record → Multiple Chunks:
1. "SBI Bluechip Fund is a Large Cap fund managed by Sohini Andani..."
2. "Expense ratio: 0.84%, Minimum SIP: ₹500, Exit load: 1% for first year..."
3. "1-year return: 15.2%, 3-year return: 12.8%, Benchmark: NIFTY 100..."
```

**Pinecone Index Schema:**
```python
{
    "id": "fund_sbi_bluechip_001",
    "values": [0.023, -0.045, ...],  # 384-dim vector
    "metadata": {
        "fund_name": "SBI Bluechip Fund Direct Plan Growth",
        "amc": "SBI Mutual Fund",
        "category": "Large Cap",
        "risk_level": "Very High",
        "is_elss": False,
        "expense_ratio_bucket": "0.5-1.0",
        "chunk_type": "fund_attributes",
        "source_url": "https://groww.in/mutual-funds/..."
    }
}
```

### Phase 3: Retrieval & Query Handling

**Objective**: Build efficient multi-strategy retrieval system

| Task | Description | Output |
|------|-------------|--------|
| 3.1 Query Parser | Build intent classification + NER | `query_processor.py` |
| 3.2 Dense Retriever | Implement vector similarity search | `dense_retriever.py` |
| 3.3 Sparse Retriever | Implement BM25/TF-IDF search | `sparse_retriever.py` |
| 3.4 Hybrid Retriever | Combine dense + sparse scores | `hybrid_retriever.py` |
| 3.5 Reranking | Integrate cross-encoder model | `reranker.py` |
| 3.6 Metadata Filters | Build filter query builder | `filters.py` |

**Query Type Handling:**

| Query Type | Example | Retrieval Strategy |
|------------|---------|-------------------|
| Fund-Specific | "Expense ratio of SBI Bluechip" | Exact name match → Vector search with fund_name filter |
| Attribute-Based | "ELSS funds with 3-year lock-in" | Metadata filter (is_elss=true) + Vector search |
| Comparison | "Compare SBI Bluechip vs Nifty 50" | Retrieve both funds → Structured comparison |
| Document | "How to download statements?" | Search doc namespace only |
| Recommendation | "Best large cap funds" | Category filter + Return ranking |

### Phase 4: LLM Integration (Groq)

**Objective**: Generate accurate, cited responses using retrieved context with strict RAG-only policy

**LLM Provider**: Groq (https://groq.com/)
- **Model**: llama-3.1-70b-versatile or mixtral-8x7b-32768
- **API**: Groq Cloud API
- **Rationale**: Fast inference, competitive pricing, supports large context windows

---

#### 4.1 RAG-Only Response Policy

**Strict Rule**: The chatbot MUST ONLY use information from the retrieved context. It is explicitly forbidden from using its own general knowledge.

| Scenario | Behavior |
|----------|----------|
| **Information in context** | Answer using retrieved data with citation |
| **Information NOT in context** | Respond: "I don't have enough information in my knowledge base to answer that question." |
| **Partial information** | Answer with available information, clearly state what's missing |
| **Contradictory information** | Present both facts with their sources, let user decide |

**Enforcement Mechanism:**
```python
# System prompt enforces RAG-only policy
SYSTEM_PROMPT = """
You are a mutual fund information assistant with STRICT limitations:

1. ONLY use information from the provided CONTEXT section below
2. NEVER use your general knowledge about mutual funds
3. If the answer is not in the CONTEXT, say: "I don't have enough information in my knowledge base to answer that."
4. ALWAYS cite sources using [1], [2], etc. format
5. Be concise and factual

CONTEXT:
{context}

If the CONTEXT is empty or doesn't contain relevant information, 
you MUST decline to answer.
"""
```

---

#### 4.2 Scope Guardrails

**Allowed Topics (In-Scope):**
- Mutual fund information from the Groww dataset
- Fund attributes: expense ratio, exit load, minimum SIP, lock-in period
- Risk profiles and benchmark indices
- Fund categories: ELSS, Large Cap, Mid Cap, Small Cap, etc.
- Document download procedures (factsheets, statements)
- AMC (Asset Management Company) information

**Out-of-Scope Topics (Must Decline):**
- Personal financial advice ("Should I invest in X?")
- Investment recommendations ("Which fund will give highest returns?")
- Market predictions ("Will the market go up next month?")
- Personal information requests
- Non-mutual fund topics (stocks, crypto, real estate, etc.)
- Tax advice beyond basic ELSS 80C information

**Out-of-Scope Response Template:**
```
"I'm designed to provide information about mutual funds in my dataset. 
I can't answer questions about [topic]. 

I can help you with:
- Fund details (expense ratio, risk level, minimum investment)
- Fund categories and comparisons
- How to download documents

Is there a specific mutual fund you'd like to know about?"
```

---

#### 4.3 Safety Guardrails

| Guardrail | Implementation | Trigger |
|-----------|---------------|---------|
| **Scope Checker** | Keyword/regex matching | Query classification |
| **Context Validator** | Minimum context threshold | < 2 relevant chunks |
| **Citation Enforcer** | Post-process response | Missing [N] citations |
| **Hallucination Detector** | Self-consistency check | Facts vs context mismatch |
| **Investment Advice Blocker** | Pattern matching | "should I", "recommend", "buy", "sell" |

**Guardrail Flow:**
```
User Query
    ↓
[Scope Checker] → Out of scope? → Return decline message
    ↓
[Query Processor] → Intent + Entities
    ↓
[Retriever] → Get relevant chunks
    ↓
[Context Validator] → Chunks < threshold? → Return "insufficient info"
    ↓
[LLM with RAG Prompt] → Generate response
    ↓
[Citation Enforcer] → Missing citations? → Add or flag
    ↓
[Response Validator] → Pass? → Return to user
```

---

#### 4.4 Citation Requirements

**MANDATORY**: Every factual statement must include a citation.

**Citation Format:**
```
"The expense ratio of SBI ELSS Tax Saver Fund is 0.92% [1]."

"ELSS funds have a 3-year lock-in period [1][2]."
```

**Source Link Inclusion:**
```python
response = {
    "answer": "The expense ratio is 0.92% [1].",
    "sources": [
        {
            "id": 1,
            "fund_name": "SBI ELSS Tax Saver Fund Direct Growth",
            "url": "https://groww.in/mutual-funds/sbi-elss-tax-saver-fund-direct-growth",
            "chunk_type": "financial"
        }
    ]
}
```

---

#### 4.5 Implementation Components

| Component | File | Purpose |
|-----------|------|---------|
| **Groq Client** | `llm/groq_client.py` | API client for Groq LLM |
| **Prompt Builder** | `prompts/prompt_builder.py` | RAG-enforcing prompt templates |
| **Context Assembler** | `context/assembler.py` | Format retrieved chunks for LLM |
| **Guardrails** | `guardrails/validator.py` | Scope and safety checks |
| **Citation Engine** | `citations/citation_manager.py` | Extract and verify citations |
| **Response Parser** | `response/parser.py` | Parse structured output |

---

#### 4.6 Prompt Template (Strict RAG)

```
SYSTEM PROMPT:
═══════════════════════════════════════════════════════════════
You are a mutual fund information assistant operating under 
STRICT constraints:

RULES:
1. ONLY use information from the CONTEXT section below
2. NEVER use external knowledge or general information
3. If information is missing, say: "I don't have enough 
   information in my knowledge base to answer that."
4. ALWAYS cite sources with [1], [2], [3] format
5. Keep answers concise and factual
6. NEVER give investment advice

CONTEXT:
{formatted_context}

If CONTEXT is empty or irrelevant, you MUST decline to answer.
═══════════════════════════════════════════════════════════════

USER QUESTION: {question}

Answer using ONLY the context above. Include citations.
```

---

#### 4.7 Response Examples

**✅ Good Response (In-scope, with citation):**
```
Q: What is the expense ratio of SBI ELSS Tax Saver Fund?

A: The expense ratio of SBI ELSS Tax Saver Fund Direct Growth 
is 0.92% [1].

[1] Source: https://groww.in/mutual-funds/sbi-elss-tax-saver-fund-direct-growth
```

**✅ Good Response (Insufficient information):**
```
Q: What is the fund manager's name for HDFC Mid Cap Fund?

A: I don't have enough information in my knowledge base to 
answer that. The available data doesn't include fund manager 
details for HDFC Mid Cap Fund.
```

**✅ Good Response (Out-of-scope declined):**
```
Q: Should I invest in SBI Bluechip Fund?

A: I can't provide investment advice or recommendations. I'm 
designed to share factual information about mutual funds in 
my dataset.

I can tell you about:
- Expense ratios and fees
- Risk levels and benchmarks
- Minimum investment amounts
- Fund categories

Would you like specific information about any fund?
```

**❌ Bad Response (Hallucination - NOT ALLOWED):**
```
Q: What is the expense ratio of XYZ Fund?

A: The expense ratio of XYZ Fund is typically around 1.5% 
for most mutual funds.  ← WRONG: Using general knowledge
```

---

#### 4.8 Phase 4 Task Summary

| Task ID | Task | Description | Output |
|---------|------|-------------|--------|
| 4.1 | Groq Client | Implement Groq API client with error handling | `groq_client.py` |
| 4.2 | Prompt Builder | Create RAG-enforcing prompt templates | `prompt_builder.py` |
| 4.3 | Context Assembler | Format retrieved chunks for LLM input | `assembler.py` |
| 4.4 | Scope Guardrails | Implement topic validation | `scope_checker.py` |
| 4.5 | Citation Engine | Enforce and validate source citations | `citation_manager.py` |
| 4.6 | Response Validator | Verify RAG compliance | `response_validator.py` |
| 4.7 | Integration | Connect with Phase 3 retrieval | `llm_integration.py` |
| 4.8 | Testing | Test guardrails and RAG compliance | Test suite |

---

#### 4.9 Environment Variables

```bash
# Required
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxx

# Optional
GROQ_MODEL=llama-3.1-70b-versatile  # or mixtral-8x7b-32768
GROQ_TEMPERATURE=0.1                # Low for factual responses
GROQ_MAX_TOKENS=1024
```

### Phase 5: Testing & Evaluation

**Objective**: Ensure system accuracy, reliability, and performance

| Task | Description | Output |
|------|-------------|--------|
| 5.1 Unit Tests | Test individual components | Test suite |
| 5.2 Integration Tests | Test component interactions | Integration suite |
| 5.3 Retrieval Evaluation | Measure recall@k, MRR | Evaluation report |
| 5.4 End-to-End Tests | Full query-response flow | E2E suite |
| 5.5 Load Testing | Performance under load | Load test results |
| 5.6 Feedback Loop | Collect and incorporate feedback | Feedback pipeline |

**Evaluation Metrics:**

| Metric | Description | Target |
|--------|-------------|--------|
| **Retrieval Recall@5** | % of relevant docs in top 5 | > 90% |
| **Retrieval Precision@5** | % of top 5 that are relevant | > 85% |
| **Answer Relevance** | LLM-judged relevance score | > 4.0/5 |
| **Citation Accuracy** | Correct source attribution | > 95% |
| **Latency (p95)** | 95th percentile response time | < 2s |
| **Hallucination Rate** | False information rate | < 2% |

---

### Phase 6: Chat Application Development

**Objective**: Build user-facing frontend and backend API for the chatbot application

---

#### 6.1 Backend API Development

**Architecture:**
```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              CHAT APPLICATION BACKEND                                    │
│                                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐    │
│  │                         FastAPI Application Layer                                │    │
│  │                                                                                  │    │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │    │
│  │  │   /chat         │  │   /funds        │  │   /health       │  │   /feedback │ │    │
│  │  │   (WebSocket)   │  │   (REST)        │  │   (Health)      │  │   (POST)    │ │    │
│  │  │                 │  │                 │  │                 │  │             │ │    │
│  │  │ • Send message  │  │ • List funds    │  │ • System status │  │ • Rate      │ │    │
│  │  │ • Stream resp   │  │ • Get details   │  │ • DB conn       │  │   response  │ │    │
│  │  │ • History       │  │ • Search        │  │ • Vector DB     │  │ • Report    │ │    │
│  │  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  └──────┬──────┘ │    │
│  │           │                    │                    │                   │        │    │
│  │           └────────────────────┴────────┬───────────┴───────────────────┘        │    │
│  │                                         │                                        │    │
│  │  ┌──────────────────────────────────────┴──────────────────────────────────────┐ │    │
│  │  │                         Middleware Layer                                     │ │    │
│  │  │  • Authentication (API Keys/JWT)                                             │ │    │
│  │  │  • Rate Limiting (Redis-based)                                               │ │    │
│  │  │  • Request Validation (Pydantic)                                             │ │    │
│  │  │  • CORS Handling                                                             │ │    │
│  │  │  • Error Handling                                                            │ │    │
│  │  └──────────────────────────────────────────────────────────────────────────────┘ │    │
│  │                                                                                  │    │
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐  │    │
│  │  │                         Service Layer                                        │  │    │
│  │  │                                                                              │  │    │
│  │  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │  │    │
│  │  │  │   Chat Service  │───►│   RAG Engine    │───►│   LLM Service   │         │  │    │
│  │  │  │                 │    │   (Phase 3-4)   │    │   (Phase 4)     │         │  │    │
│  │  │  │ • Session mgmt  │    │                 │    │                 │         │  │    │
│  │  │  │ • Context track │    │ • Retrieve      │    │ • Generate      │         │  │    │
│  │  │  │ • History store │    │ • Rerank        │    │ • Stream        │         │  │    │
│  │  │  └─────────────────┘    └─────────────────┘    └─────────────────┘         │  │    │
│  │  │                                                                              │  │    │
│  │  └─────────────────────────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

**API Endpoints:**

| Endpoint | Method | Description | Request | Response |
|----------|--------|-------------|---------|----------|
| `/chat` | WebSocket | Real-time chat | `{"message": "...", "session_id": "..."}` | Streamed response |
| `/chat` | POST | Single message | `{"message": "...", "history": []}` | `{"response": "...", "sources": []}` |
| `/funds` | GET | List all funds | Query params: `category`, `amc`, `page` | Paginated fund list |
| `/funds/{id}` | GET | Fund details | Path param: fund ID | Fund details JSON |
| `/funds/search` | GET | Search funds | Query: `q`, filters | Matching funds |
| `/health` | GET | System health | - | Status of all services |
| `/feedback` | POST | Submit feedback | `{"message_id": "...", "rating": 5}` | Confirmation |

**Backend Components:**

| Component | File | Purpose |
|-----------|------|---------|
| **Main App** | `main.py` | FastAPI application setup |
| **Chat Router** | `routers/chat.py` | Chat WebSocket and REST endpoints |
| **Funds Router** | `routers/funds.py` | Fund data endpoints |
| **Chat Service** | `services/chat_service.py` | Business logic for chat |
| **Session Manager** | `services/session_manager.py` | Conversation state management |
| **Rate Limiter** | `middleware/rate_limiter.py` | Request throttling |
| **Auth Handler** | `middleware/auth.py` | API key validation |

---

#### 6.2 Frontend Development

**Architecture:**
```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              CHAT APPLICATION FRONTEND                                   │
│                                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐    │
│  │                         React Application (Next.js)                              │    │
│  │                                                                                  │    │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐    │    │
│  │  │                         Page Components                                  │    │    │
│  │  │                                                                          │    │    │
│  │  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │    │    │
│  │  │  │   Chat Page     │  │   Fund Browser  │  │   Fund Detail   │         │    │    │
│  │  │  │   (/)           │  │   (/funds)      │  │   (/funds/:id)  │         │    │    │
│  │  │  │                 │  │                 │  │                 │         │    │    │
│  │  │  │ • Chat interface│  │ • Filter panel  │  │ • Fund metrics  │         │    │    │
│  │  │  │ • Message hist  │  │ • Fund cards    │  │ • Charts        │         │    │    │
│  │  │  │ • Quick actions │  │ • Pagination    │  │ • Compare btn   │         │    │    │
│  │  │  └─────────────────┘  └─────────────────┘  └─────────────────┘         │    │    │
│  │  └─────────────────────────────────────────────────────────────────────────┘    │    │
│  │                                                                                  │    │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐    │    │
│  │  │                         Shared Components                                │    │    │
│  │  │                                                                          │    │    │
│  │  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │    │    │
│  │  │  │  ChatInput   │ │  MessageBubble│ │  SourceCard  │ │  LoadingSpinner│   │    │    │
│  │  │  │  MessageList │ │  SuggestionChip│ │  FundCard    │ │  ErrorBoundary │   │    │    │
│  │  │  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘   │    │    │
│  │  └─────────────────────────────────────────────────────────────────────────┘    │    │
│  │                                                                                  │    │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐    │    │
│  │  │                         State Management (Zustand/Redux)                 │    │    │
│  │  │                                                                          │    │    │
│  │  │  • chatStore: messages, session, loading state                          │    │    │
│  │  │  • fundStore: fund list, filters, selected fund                         │    │    │
│  │  │  • userStore: preferences, history                                      │    │    │
│  │  └─────────────────────────────────────────────────────────────────────────┘    │    │
│  │                                                                                  │    │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐    │    │
│  │  │                         API Integration (React Query/SWR)                │    │    │
│  │  │                                                                          │    │    │
│  │  │  • useChat: WebSocket hook for real-time chat                           │    │    │
│  │  │  • useFunds: REST API for fund data                                     │    │    │
│  │  │  • useSearch: Fund search with debouncing                               │    │    │
│  │  └─────────────────────────────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

**UI Components:**

| Component | Purpose | Features |
|-----------|---------|----------|
| **ChatInterface** | Main chat UI | Message list, input box, send button |
| **MessageBubble** | Display messages | User/bot styling, timestamps, citations |
| **SourceCard** | Show information sources | Clickable links to Groww, confidence badges |
| **SuggestionChips** | Quick query suggestions | Common questions as clickable chips |
| **FundCard** | Fund summary display | Key metrics, risk badge, category tag |
| **FundDetail** | Detailed fund view | All attributes, charts, comparison tools |
| **FilterPanel** | Search filters | Category, AMC, risk level, expense ratio sliders |
| **TypingIndicator** | Bot is typing | Animated dots while waiting for response |

**Tech Stack:**

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Framework** | Next.js 14 | SSR, API routes, optimized performance |
| **Language** | TypeScript | Type safety, better DX |
| **Styling** | Tailwind CSS | Rapid UI development, consistency |
| **Components** | shadcn/ui | Accessible, customizable components |
| **State** | Zustand | Lightweight, simple API |
| **Data Fetching** | React Query | Caching, background updates |
| **WebSocket** | Socket.io-client | Real-time bidirectional communication |
| **Charts** | Recharts | React-friendly charting library |

---

#### 6.3 Phase 6 Task Summary

| Task ID | Task | Description | Output |
|---------|------|-------------|--------|
| 6.1 | Backend Setup | Initialize FastAPI project structure | `backend/` directory |
| 6.2 | API Design | Define OpenAPI specification | `api_spec.yaml` |
| 6.3 | Chat Endpoint | Implement WebSocket and REST chat endpoints | `routers/chat.py` |
| 6.4 | Fund Endpoints | Implement fund listing and search APIs | `routers/funds.py` |
| 6.5 | Session Management | Build conversation state storage | `session_manager.py` |
| 6.6 | Middleware | Add auth, rate limiting, CORS | `middleware/` |
| 6.7 | Frontend Setup | Initialize Next.js project | `frontend/` directory |
| 6.8 | Chat UI | Build chat interface components | `components/chat/` |
| 6.9 | Fund Browser | Build fund listing and detail pages | `app/funds/` |
| 6.10 | API Integration | Connect frontend to backend APIs | `hooks/useChat.ts`, `hooks/useFunds.ts` |
| 6.11 | Real-time | Implement WebSocket for streaming | `hooks/useWebSocket.ts` |
| 6.12 | Polish | Add loading states, error handling, responsiveness | Styled components |

---

### Phase 7: Data Update Scheduler & Pipeline Orchestration

**Objective**: Automate periodic data updates to ensure the system always operates with the most current mutual fund information

---

#### 7.1 Scheduler Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                         DATA UPDATE SCHEDULER & PIPELINE                                 │
│                                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐    │
│  │                         Scheduling Layer (Apache Airflow)                        │    │
│  │                                                                                  │    │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐    │    │
│  │  │  DAG: mutual_fund_data_update                                            │    │    │
│  │  │                                                                          │    │    │
│  │  │  Schedule: Daily at 02:00 AM IST (after market close)                    │    │    │
│  │  │  Retry Policy: 3 retries with exponential backoff                        │    │    │
│  │  │  Alerting: Email/Slack on failure                                        │    │    │
│  │  │                                                                          │    │    │
│  │  │  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐          │    │    │
│  │  │  │  extract │───►│  process │───►│  embed   │───►│  notify  │          │    │    │
│  │  │  │  _data   │    │  _data   │    │  _index  │    │  _update │          │    │    │
│  │  │  └──────────┘    └──────────┘    └──────────┘    └──────────┘          │    │    │
│  │  │       │               │               │               │                │    │    │
│  │  │       ▼               ▼               ▼               ▼                │    │    │
│  │  │  ┌──────────────────────────────────────────────────────────────────┐   │    │    │
│  │  │  │  Trigger: Phase 1 (Data Collection)                              │   │    │    │
│  │  │  │  Trigger: Phase 2 (Embedding)                                    │   │    │    │
│  │  │  │  Trigger: Phase 3 (Retrieval - if schema changes)                │   │    │    │
│  │  │  └──────────────────────────────────────────────────────────────────┘   │    │    │
│  │  └─────────────────────────────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐    │
│  │                         Pipeline Execution Flow                                  │    │
│  │                                                                                  │    │
│  │  ┌───────────────┐   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐  │    │
│  │  │  Phase 1      │──►│  Phase 2      │──►│  Phase 3      │──►│  Cache        │  │    │
│  │  │  (Data        │   │  (Embedding   │   │  (Retrieval   │   │  Refresh      │  │    │
│  │  │   Collection) │   │   & Indexing) │   │   Update)     │   │               │  │    │
│  │  │               │   │               │   │               │   │               │  │    │
│  │  │ • Crawl       │   │ • Chunk new   │   │ • Update      │   │ • Clear       │  │    │
│  │  │   Groww       │   │   data        │   │   search      │   │   stale       │  │    │
│  │  │ • Extract     │   │ • Generate    │   │   indexes     │   │   caches      │  │    │
│  │  │   fields      │   │   embeddings  │   │ • Warm        │   │ • Notify      │  │    │
│  │  │ • Validate    │   │ • Upsert to   │   │   caches      │   │   users       │  │    │
│  │  │ • Store in    │   │   Pinecone    │   │               │   │               │  │    │
│  │  │   PostgreSQL  │   │               │   │               │   │               │  │    │
│  │  └───────────────┘   └───────────────┘   └───────────────┘   └───────────────┘  │    │
│  │                                                                                  │    │
│  └─────────────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

#### 7.2 Update Detection & Change Management

**Change Detection Strategy:**

| Aspect | Implementation | Details |
|--------|----------------|---------|
| **Hash Comparison** | MD5/SHA256 of fund data | Detect any field changes |
| **Version Tracking** | Incremental version numbers | Track data evolution |
| **Timestamp Comparison** | `scraped_at` vs `last_updated` | Identify stale records |
| **Selective Updates** | Only changed funds | Minimize processing time |

**Change Types & Actions:**

| Change Type | Example | Action |
|-------------|---------|--------|
| **New Fund** | New fund launch | Full ingestion pipeline |
| **Attribute Update** | Expense ratio changed | Update DB + regenerate embeddings |
| **NAV Update** | Daily NAV change | Update only PostgreSQL (no re-embed) |
| **Fund Merger** | Fund A merged into B | Archive A, redirect queries to B |
| **Fund Closure** | Fund discontinued | Mark as closed, exclude from search |

---

#### 7.3 Incremental Update Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                         INCREMENTAL UPDATE WORKFLOW                                      │
│                                                                                          │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐                    │
│  │   Fetch Current │────►│   Crawl Groww   │────►│   Compare &     │                    │
│  │   State (DB)    │     │   (All Funds)   │     │   Detect Changes│                    │
│  │                 │     │                 │     │                 │                    │
│  │ • fund_count    │     │ • All fund URLs │     │ • New funds     │                    │
│  │ • last_scraped  │     │ • Fresh data    │     │ • Modified      │                    │
│  │ • content_hash  │     │                 │     │ • Deleted       │                    │
│  └─────────────────┘     └─────────────────┘     └────────┬────────┘                    │
│                                                           │                              │
│                              ┌────────────────────────────┼─────────────────────────┐   │
│                              │                            │                         │   │
│                              ▼                            ▼                         ▼   │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐                  │   │
│  │   NEW FUNDS     │     │   MODIFIED      │     │   DELETED       │                  │   │
│  │                 │     │   FUNDS         │     │   FUNDS         │                  │   │
│  │ • Full Phase 1  │     │ • Update fields │     │ • Mark closed   │                  │   │
│  │ • Full Phase 2  │     │ • Re-embed if   │     │ • Remove from   │                  │   │
│  │ • Add to index  │     │   text changed  │     │   vector index  │                  │   │
│  └─────────────────┘     └─────────────────┘     └─────────────────┘                  │   │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

#### 7.4 Scheduler Components

| Component | File | Purpose |
|-----------|------|---------|
| **DAG Definition** | `dags/mutual_fund_update.py` | Airflow DAG configuration |
| **Change Detector** | `scheduler/change_detector.py` | Compare old vs new data |
| **Update Orchestrator** | `scheduler/orchestrator.py` | Trigger phase pipelines |
| **Notification Service** | `scheduler/notifier.py` | Send success/failure alerts |
| **Health Monitor** | `scheduler/monitor.py` | Track pipeline health metrics |

---

#### 7.5 Scheduling Configuration

**DAG Schedule:**
```python
# Airflow DAG Configuration
dag = DAG(
    'mutual_fund_data_update',
    default_args={
        'owner': 'data-engineering',
        'depends_on_past': False,
        'email': ['admin@example.com'],
        'email_on_failure': True,
        'email_on_retry': False,
        'retries': 3,
        'retry_delay': timedelta(minutes=10),
    },
    description='Daily mutual fund data update pipeline',
    schedule_interval='0 2 * * *',  # Daily at 2:00 AM IST
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['mutual-funds', 'rag', 'data-pipeline'],
)
```

**Task Dependencies:**
```
extract_data ──► process_data ──► generate_embeddings ──► update_vector_db
                                                    │
                                                    ▼
                                              refresh_caches ──► notify_completion
```

---

#### 7.6 Error Handling & Recovery

| Scenario | Detection | Recovery Action |
|----------|-----------|-----------------|
| **Partial Extraction** | Missing fields in output | Retry specific URLs, log warnings |
| **Vector DB Failure** | Connection timeout | Queue for retry, use stale data |
| **Schema Drift** | Validation errors | Alert team, skip invalid records |
| **Groww Unavailable** | HTTP 5xx errors | Exponential backoff, notify on persistent failure |
| **Embeddings Timeout** | GPU/CPU resource issue | Scale workers, queue jobs |

---

#### 7.7 Monitoring & Alerting

| Metric | Threshold | Alert Channel |
|--------|-----------|---------------|
| **Pipeline Duration** | > 2 hours | Slack + Email |
| **Success Rate** | < 95% | PagerDuty |
| **New Funds Added** | > 50 in one run | Slack (info) |
| **Modified Funds** | > 30% of total | Slack (warning) |
| **Failed Extractions** | > 10 funds | Email |
| **Data Freshness** | > 48 hours old | PagerDuty |

---

#### 7.8 Phase 7 Task Summary

| Task ID | Task | Description | Output |
|---------|------|-------------|--------|
| 7.1 | Airflow Setup | Install and configure Apache Airflow | Airflow instance |
| 7.2 | DAG Definition | Create mutual fund update DAG | `dags/mutual_fund_update.py` |
| 7.3 | Change Detection | Build hash-based change detector | `change_detector.py` |
| 7.4 | Pipeline Integration | Connect Phase 1-3 to scheduler | Orchestrated pipeline |
| 7.5 | Incremental Updates | Implement selective update logic | Incremental processor |
| 7.6 | Cache Management | Add cache invalidation on updates | Cache refresh logic |
| 7.7 | Alerting | Configure email/Slack notifications | Alert rules |
| 7.8 | Monitoring Dashboard | Build pipeline health dashboard | Grafana dashboard |
| 7.9 | Manual Trigger | Add API endpoint for manual updates | `/admin/trigger-update` |
| 7.10 | Rollback | Implement rollback on failure | Rollback scripts |

---

## Updated Phase Summary

| Phase | Name | Purpose | Key Outputs |
|-------|------|---------|-------------|
| **Phase 1** | Data Collection & Processing | Extract and clean mutual fund data | PostgreSQL DB with fund data |
| **Phase 2** | Embedding & Indexing | Create searchable vectors | Pinecone vector index |
| **Phase 3** | Retrieval & Query Handling | Find relevant information | Hybrid retriever |
| **Phase 4** | LLM Integration | Generate natural language responses | Response generator |
| **Phase 5** | Testing & Evaluation | Ensure quality and reliability | Test suites, metrics |
| **Phase 6** | Chat Application Development | Build user-facing application | FastAPI backend + Next.js frontend |
| **Phase 7** | Data Update Scheduler | Automate data freshness | Airflow DAG, incremental updates |

---

## Edge Cases & Handling

### 1. Data Quality Edge Cases

| Edge Case | Example | Handling Strategy |
|-----------|---------|-------------------|
| **Missing Fields** | Fund with no expense ratio data | Flag as incomplete, exclude from certain queries |
| **Inconsistent Naming** | "SBI Bluechip" vs "SBI BLUECHIP FUND" | Normalize using fuzzy matching + canonical names |
| **Stale Data** | NAV from 3 days ago | Timestamp all data, show "last updated" |
| **Duplicate Funds** | Same fund, different plans | Deduplicate using ISIN or unique identifier |
| **New Fund Launch** | Recently launched fund | Handle missing historical returns gracefully |
| **Merged Funds** | Fund that underwent merger | Track merger history, redirect queries |

### 2. Query Edge Cases

| Edge Case | Example | Handling Strategy |
|-----------|---------|-------------------|
| **Ambiguous Fund Names** | "HDFC Fund" (AMC or specific fund?) | Ask clarifying question or return all matches |
| **Typos** | "SBI Bleuchip" | Fuzzy string matching in retrieval |
| **Abbreviations** | "SBI MF", "ELSS" | Maintain abbreviation mapping |
| **Vague Queries** | "Best mutual fund" | Ask for criteria (risk, category, horizon) |
| **Multi-part Queries** | "Compare expense ratio and returns of X and Y" | Decompose into sub-queries, aggregate results |
| **Out-of-scope** | "What's the stock price of Reliance?" | Politely decline, suggest scope |
| **Time-sensitive** | "What was NAV yesterday?" | Indicate data freshness limitations |

### 3. System Edge Cases

| Edge Case | Scenario | Handling Strategy |
|-----------|----------|-------------------|
| **Scraper Failure** | Groww blocks scraping | Implement exponential backoff, proxy rotation |
| **Vector DB Outage** | Pinecone unavailable | Fallback to PostgreSQL full-text search |
| **LLM Rate Limit** | OpenAI API throttling | Queue requests, fallback to cached responses |
| **Large Context** | Query matching 100+ funds | Truncate to top-k, summarize before LLM |
| **Concurrent Updates** | Scraping while querying | Read replicas, eventual consistency |

---

## Scalability Considerations

### 1. Data Volume Scaling

| Current | Future | Strategy |
|---------|--------|----------|
| ~3,000 funds | 10,000+ funds | Sharded vector indices by category |
| Daily updates | Hourly updates | Incremental updates, change detection |
| 1 data source | Multiple sources | Pluggable scraper architecture |
| 1 year history | 5 year history | Tiered storage (hot/warm/cold) |

### 2. Query Volume Scaling

| Current | Future | Strategy |
|---------|--------|----------|
| 100 QPS | 10,000 QPS | Horizontal scaling with load balancer |
| Synchronous | Async processing | Queue-based architecture (Celery/RQ) |
| Single region | Multi-region | CDN for static data, regional LLM endpoints |
| No caching | Aggressive caching | Redis for query results, embedding cache |

### 3. Architecture Scaling Patterns

```
Current (Monolithic):
┌─────────────────────────────────────┐
│  Single FastAPI Instance            │
│  - Scraping                         │
│  - Embedding                        │
│  - Retrieval                        │
│  - Generation                       │
└─────────────────────────────────────┘

Future (Microservices):
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│   Scraper   │ │  Embedding  │ │  Retrieval  │ │   LLM API   │
│   Service   │ │   Service   │ │   Service   │ │   Service   │
│  (Celery)   │ │  (GPU Node) │ │  (FastAPI)  │ │  (FastAPI)  │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
       │               │               │               │
       └───────────────┴───────────────┴───────────────┘
                           │
                    ┌─────────────┐
                    │ API Gateway │
                    │  (Kong/AWS) │
                    └─────────────┘
```

### 4. Performance Optimizations

| Layer | Optimization | Impact |
|-------|--------------|--------|
| **Embedding** | Batch processing, GPU acceleration | 10x throughput |
| **Vector DB** | Metadata filtering before search | 5x faster queries |
| **Retrieval** | Caching frequent queries | 100x for popular queries |
| **LLM** | Response streaming | Improved perceived latency |
| **Database** | Connection pooling, read replicas | Handle 10x load |

### 5. Cost Optimization

| Component | Current Cost | Optimization | Savings |
|-----------|--------------|--------------|---------|
| **LLM API** | $0.03/query | Cache similar queries | 60% |
| **Vector DB** | $70/month | Optimize index size | 30% |
| **Embedding** | $0.001/fund | Batch processing | 50% |
| **Scraping** | Proxy costs | Smart scheduling | 40% |

---

## Security Considerations

| Concern | Mitigation |
|---------|------------|
| **Prompt Injection** | Input sanitization, output filtering |
| **Data Poisoning** | Validation, source verification |
| **Rate Limiting** | Tiered limits per API key |
| **PII Handling** | No PII storage, anonymization |
| **Scraping Ethics** | Respect robots.txt, rate limits |

---

## Monitoring & Observability

| Component | Metrics | Tools |
|-----------|---------|-------|
| **API** | Request rate, latency, errors | Prometheus + Grafana |
| **Retrieval** | Recall, precision, query distribution | Custom dashboards |
| **LLM** | Token usage, cost, response quality | LangSmith/Weights & Biases |
| **Data Pipeline** | Success rate, data freshness | Airflow UI |
| **User Feedback** | Satisfaction, correction rate | Feedback collector |

---

## Summary

This architecture provides a solid foundation for building an AI-powered mutual fund chatbot with the following key characteristics:

1. **Modular Design**: Clear separation of concerns across 5 phases
2. **Scalable**: Can handle increasing data and query volumes
3. **Reliable**: Multiple fallback mechanisms and error handling
4. **Maintainable**: Well-organized codebase with clear interfaces
5. **Extensible**: Easy to add new data sources or query types

The Phase 1 focus on data collection and processing is critical - high-quality structured data is the foundation of effective RAG. Subsequent phases build upon this foundation to deliver accurate, helpful responses to users.

# Phase 4: LLM Integration (Groq)

## Overview

Phase 4 integrates Groq LLM to generate responses with **strict RAG-only policy**. The system enforces that responses are based **ONLY** on retrieved context, never on the LLM's general knowledge.

## RAG-Only Policy

### Core Rules

1. **Context-Only**: Use ONLY information from retrieved chunks
2. **No External Knowledge**: Never use LLM's general knowledge about mutual funds
3. **Mandatory Decline**: If answer not in context, MUST say: *"I don't have enough information in my knowledge base to answer that question."*
4. **Source Citations**: Every fact must include citation [1], [2], etc.
5. **No Investment Advice**: Decline all recommendation requests

### Allowed vs Blocked

| Type | Example | Action |
|------|---------|--------|
| ✅ In-Scope | "What is expense ratio of SBI ELSS?" | Answer with citation |
| ❌ Investment Advice | "Should I invest in X?" | Block with decline message |
| ❌ Prediction | "Will this fund go up?" | Block with decline message |
| ❌ Non-Financial | "What is the weather?" | Block with decline message |
| ❌ No Context | Query about unknown fund | Decline - insufficient info |

## Architecture

```
User Query
    ↓
[Scope Checker] → Block if out-of-scope
    ↓
[Context Validator] → Block if insufficient context
    ↓
[Prompt Builder] → Build RAG-enforcing prompt
    ↓
[Groq LLM] → Generate response
    ↓
[Citation Validator] → Verify citations present
    ↓
Response to User
```

## Components

### 1. Groq Client (`src/llm/groq_client.py`)

```python
from llm import GroqClient

client = GroqClient(
    api_key="gsk_...",  # or set GROQ_API_KEY
    model="llama-3.1-70b-versatile",
    temperature=0.1  # Low for factual responses
)

response = client.generate(
    system_prompt=system_prompt,
    user_message="What is the expense ratio?",
    context=retrieved_chunks
)

print(response.content)  # Response with citations
print(response.rag_compliant)  # True/False
print(response.citations)  # Source links
```

### 2. Prompt Builder (`src/prompts/prompt_builder.py`)

Builds strict RAG-enforcing prompts:

```python
from prompts import PromptBuilder

builder = PromptBuilder()

# Build system prompt with context
system_prompt = builder.build_system_prompt(
    context_chunks=retrieved_chunks
)

# Get standardized decline responses
out_of_scope = builder.get_out_of_scope_response()
insufficient = builder.get_insufficient_context_response()
```

### 3. Guardrails (`src/guardrails/scope_checker.py`)

Enforces scope boundaries:

```python
from guardrails import ScopeChecker, GuardrailAction

checker = ScopeChecker()

# Check query scope
result = checker.check_query("Should I invest in X?")
if result.action == GuardrailAction.BLOCK:
    print(result.response)  # Decline message

# Check context sufficiency
result = checker.check_context_sufficiency(retrieved_chunks, query)
```

## Usage

### Run Pipeline (Test Mode)

```bash
cd phase4_llm_integration
python scripts/run_phase4.py --skip-llm
```

### Run with Live LLM

```bash
# Set API key
set GROQ_API_KEY=gsk_your_key_here

# Run pipeline
python scripts/run_phase4.py
```

### Run Single Query

```python
from llm import GroqClient
from prompts import PromptBuilder
from guardrails import ScopeChecker

# Initialize
scope_checker = ScopeChecker()
prompt_builder = PromptBuilder()
llm_client = GroqClient()

# Query
query = "What is the expense ratio of SBI ELSS?"

# Check guardrails
result = scope_checker.check_query(query)
if result.action == GuardrailAction.BLOCK:
    print(result.response)
else:
    # Build prompt with retrieved context
    system_prompt = prompt_builder.build_system_prompt(retrieved_chunks)
    
    # Generate response
    response = llm_client.generate(
        system_prompt=system_prompt,
        user_message=query,
        context=retrieved_chunks
    )
    
    print(response.content)
    print("Sources:", response.citations)
```

## Environment Variables

```bash
# Required for live LLM
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxx

# Optional
GROQ_MODEL=llama-3.1-70b-versatile
GROQ_TEMPERATURE=0.1
GROQ_MAX_TOKENS=1024
```

## Prompt Template

```
You are a mutual fund information assistant operating under STRICT constraints.

ABSOLUTE RULES:
1. ONLY use information from the CONTEXT section below
2. NEVER use your general knowledge
3. If answer NOT in CONTEXT, say: "I don't have enough information..."
4. ALWAYS cite sources with [1], [2], [3]
5. NEVER provide investment advice

CONTEXT:
[1] Fund: SBI ELSS Tax Saver Fund
    Information: Expense ratio is 0.92%
    Source: https://groww.in/mutual-funds/...

Remember: If CONTEXT doesn't contain the answer, you MUST decline.
```

## Response Examples

### ✅ Good Response

```
Q: What is the expense ratio of SBI ELSS?

A: The expense ratio of SBI ELSS Tax Saver Fund Direct Growth 
is 0.92% [1].

[1] Source: https://groww.in/mutual-funds/sbi-elss-tax-saver-fund-direct-growth
```

### ✅ Good Decline (Insufficient Info)

```
Q: What is the fund manager's name?

A: I don't have enough information in my knowledge base to 
answer that question.
```

### ✅ Good Decline (Investment Advice)

```
Q: Should I invest in SBI Bluechip?

A: I can't provide investment advice. I'm designed to share 
factual information about mutual funds.

I can tell you about:
- Expense ratios and fees
- Risk levels and benchmarks
- Minimum investment amounts
```

### ❌ Bad Response (Hallucination - NOT ALLOWED)

```
Q: What is expense ratio of XYZ Fund?

A: The expense ratio is typically around 1.5% for most funds.
     ^ WRONG: Using general knowledge instead of context
```

## Guardrail Triggers

| Pattern | Action | Response |
|---------|--------|----------|
| "should I invest" | BLOCK | Investment advice decline |
| "recommend a fund" | BLOCK | Investment advice decline |
| "will fund go up" | BLOCK | Prediction decline |
| "what is your name" | BLOCK | Personal info decline |
| "weather/stocks/crypto" | BLOCK | Non-financial decline |
| No context retrieved | BLOCK | Insufficient info |
| Low relevance score | BLOCK | Low relevance message |

## Integration with Phase 3

Connect Phase 3 retrieval to Phase 4 LLM:

```python
# Phase 3: Retrieve
from phase3_retrieval import run_phase3_pipeline
retrieval_results = run_phase3_pipeline(query)

# Phase 4: Generate response
from phase4_llm_integration import run_phase4_pipeline
llm_results = run_phase4_pipeline(
    query=query,
    context=retrieval_results[0]['results']
)
```

## Next Steps

Proceed to **Phase 5: Testing & Evaluation** for:
- RAG compliance testing
- Guardrail effectiveness evaluation
- Response quality metrics
- End-to-end pipeline testing

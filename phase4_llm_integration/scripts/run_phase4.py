#!/usr/bin/env python3
"""
Phase 4: LLM Integration Pipeline
Generates RAG-based responses using Groq LLM
"""

import sys
import json
import os
from pathlib import Path
from typing import List, Dict, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "phase3_retrieval" / "src"))

from llm import GroqClient
from prompts import PromptBuilder
from guardrails import ScopeChecker, GuardrailAction


def load_test_queries() -> List[Dict]:
    """Load test queries"""
    return [
        {
            "query": "What is the expense ratio of SBI ELSS Tax Saver Fund?",
            "context": [
                {
                    "fund_name": "SBI ELSS Tax Saver Fund Direct Growth",
                    "text": "Expense ratio is 0.92%",
                    "source_url": "https://groww.in/mutual-funds/sbi-elss-tax-saver-fund-direct-growth",
                    "chunk_type": "financial"
                }
            ]
        },
        {
            "query": "Should I invest in HDFC Mid Cap Fund?",
            "context": [
                {
                    "fund_name": "HDFC Mid Cap Fund Direct Growth",
                    "text": "Expense ratio is 0.76%. Risk level is Very High.",
                    "source_url": "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
                    "chunk_type": "financial"
                }
            ]
        },
        {
            "query": "What is the lock-in period for ELSS funds?",
            "context": [
                {
                    "fund_name": "SBI ELSS Tax Saver Fund Direct Growth",
                    "text": "Lock-in period: 3 years lock-in period",
                    "source_url": "https://groww.in/mutual-funds/sbi-elss-tax-saver-fund-direct-growth",
                    "chunk_type": "financial"
                }
            ]
        },
        {
            "query": "How to download mutual fund statements?",
            "context": [
                {
                    "fund_name": "SBI ELSS Tax Saver Fund Direct Growth",
                    "text": "Log in to Groww → Profile → Reports → Select Mutual Fund report → Choose date range → Download statement.",
                    "source_url": "https://groww.in/mutual-funds/sbi-elss-tax-saver-fund-direct-growth",
                    "chunk_type": "documents"
                }
            ]
        },
        {
            "query": "What is the weather today?",
            "context": []
        }
    ]


def run_phase4_pipeline(
    query: str = None,
    context: List[Dict] = None,
    skip_llm: bool = False
):
    """
    Run Phase 4 LLM integration pipeline
    
    Args:
        query: User query (optional, runs tests if None)
        context: Retrieved context chunks
        skip_llm: Skip actual LLM call (for testing without API key)
    """
    print("=" * 70)
    print("PHASE 4: LLM INTEGRATION (Groq)")
    print("=" * 70)
    print("\nPolicy: STRICT RAG-ONLY")
    print("- Only use retrieved context")
    print("- No external knowledge")
    print("- Mandatory source citations")
    print("- Decline out-of-scope queries")
    
    # Initialize components
    print("\n[1/4] Initializing Guardrails...")
    scope_checker = ScopeChecker()
    print("      ✓ Scope checker ready")
    
    print("[2/4] Initializing Prompt Builder...")
    prompt_builder = PromptBuilder()
    print("      ✓ Prompt builder ready")
    
    print("[3/4] Initializing Groq Client...")
    groq_api_key = os.getenv('GROQ_API_KEY')
    if groq_api_key and not skip_llm:
        try:
            llm_client = GroqClient(api_key=groq_api_key)
            print("      ✓ Groq client ready")
            llm_available = True
        except Exception as e:
            print(f"      ⚠ Groq client error: {e}")
            print("      ⚠ Running in test mode (no LLM calls)")
            llm_available = False
    else:
        if skip_llm:
            print("      ⚠ LLM calls skipped (skip_llm=True)")
        else:
            print("      ⚠ GROQ_API_KEY not set - running in test mode")
        llm_available = False
    
    # Load queries
    if query and context is not None:
        queries = [{"query": query, "context": context}]
    else:
        queries = load_test_queries()
    
    print(f"\n[4/4] Processing {len(queries)} queries...")
    print("=" * 70)
    
    results = []
    
    for i, item in enumerate(queries, 1):
        q = item["query"]
        ctx = item.get("context", [])
        
        print(f"\n{'='*70}")
        print(f"QUERY {i}: {q}")
        print("=" * 70)
        
        # Step 1: Guardrail check
        print("\n[Guardrail Check]")
        guardrail_result = scope_checker.check_query(q)
        print(f"  Action: {guardrail_result.action.value}")
        print(f"  Reason: {guardrail_result.reason}")
        
        if guardrail_result.action == GuardrailAction.BLOCK:
            print(f"\n[BLOCKED - Out of Scope]")
            print(f"Response: {guardrail_result.response}")
            results.append({
                "query": q,
                "blocked": True,
                "reason": guardrail_result.reason,
                "response": guardrail_result.response
            })
            continue
        
        # Step 2: Check context sufficiency
        if ctx:
            context_check = scope_checker.check_context_sufficiency(ctx, q)
            if context_check.action == GuardrailAction.BLOCK:
                print(f"\n[BLOCKED - Insufficient Context]")
                print(f"Response: {context_check.response}")
                results.append({
                    "query": q,
                    "blocked": True,
                    "reason": context_check.reason,
                    "response": context_check.response
                })
                continue
        
        # Step 3: Build prompt
        print("\n[Prompt Building]")
        system_prompt = prompt_builder.build_system_prompt(ctx)
        user_message = prompt_builder.build_user_message(q)
        
        print(f"  Context chunks: {len(ctx)}")
        print(f"  System prompt length: {len(system_prompt)} chars")
        
        # Step 4: Generate response
        print("\n[LLM Generation]")
        
        if llm_available and not skip_llm:
            try:
                llm_response = llm_client.generate(
                    system_prompt=system_prompt,
                    user_message=user_message,
                    context=ctx
                )
                
                response_text = llm_response.content
                rag_compliant = llm_response.rag_compliant
                citations = llm_response.citations
                
                print(f"  ✓ Response generated")
                print(f"  RAG Compliant: {rag_compliant}")
                print(f"  Citations: {len(citations)}")
                print(f"  Tokens used: {llm_response.usage.get('total_tokens', 'N/A')}")
                
            except Exception as e:
                print(f"  ✗ LLM error: {e}")
                response_text = "[Error generating response]"
                rag_compliant = False
                citations = []
        else:
            # Simulate response for testing
            print("  ⚠ Test mode - simulating response")
            
            if not ctx:
                response_text = prompt_builder.get_insufficient_context_response()
                rag_compliant = True
            else:
                # Generate a mock RAG-compliant response
                fund_info = ctx[0].get('text', '')
                fund_name = ctx[0].get('fund_name', 'the fund')
                response_text = f"Based on the available information, {fund_name} has the following details: {fund_info} [1]"
                rag_compliant = True
            
            citations = [
                {
                    'id': '1',
                    'fund_name': chunk.get('fund_name', ''),
                    'source_url': chunk.get('source_url', '')
                }
                for chunk in ctx[:1]
            ]
        
        # Display results
        print(f"\n[Response]")
        print(f"{response_text}")
        
        if citations:
            print(f"\n[Sources]")
            for cit in citations:
                print(f"  [{cit['id']}] {cit['fund_name']}")
                print(f"      {cit['source_url']}")
        
        results.append({
            "query": q,
            "blocked": False,
            "response": response_text,
            "rag_compliant": rag_compliant,
            "citations": citations,
            "context_chunks": len(ctx)
        })
    
    # Summary
    print("\n" + "=" * 70)
    print("PHASE 4 COMPLETE")
    print("=" * 70)
    
    blocked_count = sum(1 for r in results if r.get('blocked'))
    allowed_count = len(results) - blocked_count
    
    print(f"\nResults:")
    print(f"  Total queries: {len(results)}")
    print(f"  Allowed: {allowed_count}")
    print(f"  Blocked by guardrails: {blocked_count}")
    
    if not skip_llm and llm_available:
        print(f"  LLM: Groq API used")
    else:
        print(f"  LLM: Test mode (simulated)")
    
    # Save results
    output_file = Path(__file__).parent.parent / "data" / "llm_results.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {output_file}")
    
    print("\n" + "=" * 70)
    print("NEXT STEPS:")
    print("=" * 70)
    print("1. Set GROQ_API_KEY environment variable for live LLM")
    print("2. Test with actual retrieved context from Phase 3")
    print("3. Tune guardrail thresholds")
    print("4. Proceed to Phase 5: Testing & Evaluation")
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Phase 4: LLM Integration')
    parser.add_argument('--query', type=str, help='Single query to process')
    parser.add_argument('--skip-llm', action='store_true', 
                       help='Skip LLM calls (test mode)')
    
    args = parser.parse_args()
    
    # Run pipeline
    results = run_phase4_pipeline(
        query=args.query,
        skip_llm=args.skip_llm
    )

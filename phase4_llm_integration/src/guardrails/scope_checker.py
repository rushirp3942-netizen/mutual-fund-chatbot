"""
Guardrails for Mutual Fund RAG Chatbot
Enforces scope boundaries and safety checks
"""

import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class GuardrailAction(Enum):
    """Actions guardrails can take"""
    ALLOW = "allow"
    BLOCK = "block"
    WARN = "warn"


@dataclass
class GuardrailResult:
    """Result of guardrail check"""
    action: GuardrailAction
    reason: str
    response: Optional[str] = None
    metadata: Dict[str, Any] = None


class ScopeChecker:
    """
    Checks if queries are within the chatbot's scope
    
    Enforces:
    - Topic boundaries (mutual funds only)
    - No investment advice
    - No personal information requests
    """
    
    def __init__(self):
        # In-scope keywords
        self.in_scope_keywords = [
            'fund', 'mutual fund', 'amc', 'expense ratio', 'exit load',
            'sip', 'systematic investment', 'nav', 'aum', 'benchmark',
            'risk', 'riskometer', 'large cap', 'mid cap', 'small cap',
            'elss', 'tax saver', 'debt fund', 'equity fund', 'hybrid',
            'growth', 'dividend', 'direct plan', 'regular plan',
            'lock-in', 'lockin', 'factsheet', 'statement', 'download'
        ]
        
        # Out-of-scope patterns
        self.out_of_scope_patterns = {
            'investment_advice': [
                r'should\s+i\s+(?:invest|buy|sell)',
                r'recommend\s+(?:me\s+)?(?:a\s+)?fund',
                r'which\s+fund\s+(?:should|to)\s+i',
                r'is\s+it\s+(?:good|bad)\s+to\s+invest',
                r'will\s+(?:this|the)\s+fund\s+(?:go\s+up|increase|double)',
                r'future\s+(?:returns?|performance)',
                r'expected\s+returns?',
                r'best\s+fund\s+for\s+(?:me|2024|next\s+year)'
            ],
            'personal_info': [
                r'(?:my|your)\s+(?:name|age|email|phone|address)',
                r'personal\s+(?:information|details|data)',
                r'who\s+are\s+you\s+(?:really|actually)',
                r'contact\s+(?:you|me)'
            ],
            'non_financial': [
                r'\b(?:stock|share|crypto|bitcoin|nft|real\s+estate|gold)\b',
                r'\b(?:insurance|loan|credit\s+card|bank\s+account)\b',
                r'weather|news|sports|politics|movie|food'
            ]
        }
        
        # Minimum context threshold
        self.min_context_score = 0.1
    
    def check_query(self, query: str, query_intent: Optional[str] = None) -> GuardrailResult:
        """
        Check if query is within scope
        
        Args:
            query: User query string
            query_intent: Optional intent from query processor
            
        Returns:
            GuardrailResult with action and optional response
        """
        query_lower = query.lower()
        
        # Check 1: Investment advice patterns
        for pattern in self.out_of_scope_patterns['investment_advice']:
            if re.search(pattern, query_lower):
                return GuardrailResult(
                    action=GuardrailAction.BLOCK,
                    reason="investment_advice",
                    response=self._get_investment_advice_response(),
                    metadata={'pattern': pattern}
                )
        
        # Check 2: Personal information
        for pattern in self.out_of_scope_patterns['personal_info']:
            if re.search(pattern, query_lower):
                return GuardrailResult(
                    action=GuardrailAction.BLOCK,
                    reason="personal_info",
                    response=self._get_personal_info_response(),
                    metadata={'pattern': pattern}
                )
        
        # Check 3: Non-financial topics
        for pattern in self.out_of_scope_patterns['non_financial']:
            if re.search(pattern, query_lower):
                return GuardrailResult(
                    action=GuardrailAction.BLOCK,
                    reason="non_financial",
                    response=self._get_non_financial_response(),
                    metadata={'pattern': pattern}
                )
        
        # Check 4: Has in-scope keywords
        has_in_scope = any(keyword in query_lower for keyword in self.in_scope_keywords)
        
        if not has_in_scope and query_intent not in ['fund_specific', 'attribute_based', 'comparison']:
            return GuardrailResult(
                action=GuardrailAction.BLOCK,
                reason="out_of_scope",
                response=self._get_out_of_scope_response(),
                metadata={'query': query}
            )
        
        # All checks passed
        return GuardrailResult(
            action=GuardrailAction.ALLOW,
            reason="in_scope",
            metadata={'query': query}
        )
    
    def check_context_sufficiency(
        self,
        retrieved_chunks: List[Dict],
        query: str
    ) -> GuardrailResult:
        """
        Check if retrieved context is sufficient to answer
        
        Args:
            retrieved_chunks: Chunks from retriever
            query: Original query
            
        Returns:
            GuardrailResult
        """
        if not retrieved_chunks:
            return GuardrailResult(
                action=GuardrailAction.BLOCK,
                reason="no_context",
                response=self._get_no_context_response(),
                metadata={'chunk_count': 0}
            )
        
        # Check if top chunk has reasonable score
        top_chunk = retrieved_chunks[0]
        top_score = top_chunk.get('score', 0) if isinstance(top_chunk, dict) else getattr(top_chunk, 'score', 0)
        
        if top_score < self.min_context_score:
            return GuardrailResult(
                action=GuardrailAction.BLOCK,
                reason="low_relevance",
                response=self._get_low_relevance_response(),
                metadata={'top_score': top_score}
            )
        
        return GuardrailResult(
            action=GuardrailAction.ALLOW,
            reason="sufficient_context",
            metadata={'chunk_count': len(retrieved_chunks), 'top_score': top_score}
        )
    
    def _get_investment_advice_response(self) -> str:
        """Response for investment advice requests"""
        return """I can't provide investment advice or recommendations. I'm designed to share factual information about mutual funds in my knowledge base.

I can tell you about:
• Expense ratios and fees
• Risk levels and benchmarks
• Minimum investment amounts
• Fund categories and types

For investment advice, please consult a SEBI-registered investment advisor.

Is there specific fund information I can help you with?"""
    
    def _get_personal_info_response(self) -> str:
        """Response for personal information requests"""
        return """I don't collect or share personal information. I'm a mutual fund information assistant that only answers questions about funds in my knowledge base.

How can I help you with mutual fund information today?"""
    
    def _get_non_financial_response(self) -> str:
        """Response for non-financial topics"""
        return """I can only answer questions about mutual funds in my knowledge base. I don't have information about stocks, crypto, real estate, or other investment types.

I can help you with:
• Mutual fund details and comparisons
• Fund categories (ELSS, Large Cap, Mid Cap, Small Cap)
• Expense ratios, risk levels, and benchmarks
• How to download fund documents

Is there a mutual fund you'd like to know about?"""
    
    def _get_out_of_scope_response(self) -> str:
        """Generic out-of-scope response"""
        return """I apologize, but I can only answer questions about mutual funds in my knowledge base.

I can help you with:
• Fund details (expense ratio, risk level, minimum investment)
• Fund categories (ELSS, Large Cap, Mid Cap, Small Cap)
• Benchmark indices and risk profiles
• How to download statements and documents

I cannot provide:
• Investment advice or recommendations
• Future performance predictions
• Personal financial planning
• Information about topics outside my dataset

Is there a specific mutual fund you'd like to know about?"""
    
    def _get_no_context_response(self) -> str:
        """Response when no context is retrieved"""
        return """I don't have enough information in my knowledge base to answer that question.

The query doesn't match any funds in my dataset. I have information about:
• Bandhan Small Cap Fund
• Parag Parikh Long Term Value Fund
• HDFC Mid Cap Fund
• Nippon India Small Cap Fund
• ICICI Prudential Large Cap Fund
• Tata Small Cap Fund
• Axis Small Cap Fund
• SBI Small Cap Fund
• SBI ELSS Tax Saver Fund

Would you like to know about one of these funds?"""
    
    def _get_low_relevance_response(self) -> str:
        """Response when context relevance is too low"""
        return """I don't have enough relevant information to answer that question accurately.

The available data doesn't seem to contain the specific details you're looking for.

I can tell you about:
• Expense ratios, exit loads, and minimum SIP amounts
• Risk levels and benchmark indices
• Fund categories and AMC information

Would you like to ask about a different aspect?"""


if __name__ == "__main__":
    # Test guardrails
    checker = ScopeChecker()
    
    test_queries = [
        "What is the expense ratio of SBI ELSS?",  # Should ALLOW
        "Should I invest in HDFC Mid Cap?",  # Should BLOCK - investment advice
        "What is your name?",  # Should BLOCK - personal info
        "How is the weather today?",  # Should BLOCK - non-financial
        "Will SBI Bluechip double my money?",  # Should BLOCK - prediction
    ]
    
    print("Guardrail Tests:")
    print("=" * 70)
    
    for query in test_queries:
        result = checker.check_query(query)
        print(f"\nQuery: {query}")
        print(f"Action: {result.action.value}")
        print(f"Reason: {result.reason}")
        if result.response:
            print(f"Response: {result.response[:100]}...")

"""
Query Processing Module for Mutual Fund RAG Chatbot
Handles intent classification, entity extraction, and query preprocessing
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import json


class QueryIntent(Enum):
    """Types of user queries"""
    FUND_SPECIFIC = "fund_specific"  # "What is expense ratio of SBI Bluechip?"
    ATTRIBUTE_BASED = "attribute_based"  # "Show ELSS funds with 3-year lock-in"
    COMPARISON = "comparison"  # "Compare SBI Bluechip vs HDFC Midcap"
    DOCUMENT = "document"  # "How to download statements?"
    RECOMMENDATION = "recommendation"  # "Best large cap funds"
    GENERAL = "general"  # "What is a mutual fund?"


@dataclass
class ProcessedQuery:
    """Processed query with intent and entities"""
    original_query: str
    normalized_query: str
    intent: QueryIntent
    confidence: float
    entities: Dict[str, Any] = field(default_factory=dict)
    filters: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'original_query': self.original_query,
            'normalized_query': self.normalized_query,
            'intent': self.intent.value,
            'confidence': self.confidence,
            'entities': self.entities,
            'filters': self.filters
        }


class QueryProcessor:
    """
    Processes user queries for the mutual fund chatbot
    - Classifies intent
    - Extracts entities (fund names, AMCs, categories)
    - Builds metadata filters
    """
    
    def __init__(self):
        # Common fund name patterns
        self.fund_keywords = [
            'fund', 'scheme', 'plan', 'growth', 'direct', 'regular',
            'equity', 'debt', 'hybrid', 'elss', 'tax saver'
        ]
        
        # AMC names (expandable)
        self.amc_list = [
            'sbi', 'hdfc', 'icici', 'axis', 'bandhan', 'nippon',
            'tata', 'parag parikh', 'canara robeco', 'dsp', 'franklin'
        ]
        
        # Category keywords
        self.category_keywords = {
            'large cap': ['large cap', 'largecap', 'bluechip'],
            'mid cap': ['mid cap', 'midcap'],
            'small cap': ['small cap', 'smallcap'],
            'elss': ['elss', 'tax saver', 'tax saving', '80c'],
            'flexi cap': ['flexi cap', 'flexicap', 'multi cap', 'multicap'],
            'debt': ['debt', 'bond', 'gilt'],
            'hybrid': ['hybrid', 'balanced', 'allocation']
        }
        
        # Attribute keywords
        self.attribute_keywords = {
            'expense_ratio': ['expense ratio', 'expense', 'cost', 'fee'],
            'exit_load': ['exit load', 'redemption', 'penalty'],
            'minimum_sip': ['minimum sip', 'min sip', 'sip amount'],
            'lock_in': ['lock in', 'lock-in', 'lockin', 'lockin period'],
            'risk_level': ['risk', 'riskometer', 'risk level'],
            'benchmark': ['benchmark', 'index']
        }
        
        # Intent patterns
        self.intent_patterns = {
            QueryIntent.COMPARISON: [
                r'compare\s+(.+?)\s+(?:vs|versus|and|with)\s+(.+)',
                r'difference\s+between\s+(.+?)\s+and\s+(.+)',
                r'which\s+(?:is\s+)?better',
                r'vs\s+|versus\s+'
            ],
            QueryIntent.DOCUMENT: [
                r'how\s+to\s+(?:download|get|access)',
                r'statement|report|document|factsheet|sid|kim',
                r'where\s+(?:can|do)\s+i\s+(?:find|get|download)'
            ],
            QueryIntent.RECOMMENDATION: [
                r'best\s+(?:mutual\s+)?fund',
                r'top\s+\d*\s*(?:mutual\s+)?fund',
                r'recommend|suggestion|which\s+(?:fund|one)\s+(?:should|to)',
                r'good\s+(?:mutual\s+)?fund'
            ],
            QueryIntent.ATTRIBUTE_BASED: [
                r'show\s+(?:me\s+)?(?:all\s+)?(.+?)\s+(?:fund|with)',
                r'fund\s+with\s+(.+)',
                r'elss|tax\s+saver|lock.in',
                r'low\s+expense|high\s+return|minimum\s+sip'
            ],
            QueryIntent.FUND_SPECIFIC: [
                r'what\s+(?:is|are)\s+(?:the\s+)?(.+?)\s+of\s+(.+)',
                r'tell\s+me\s+about\s+(.+)',
                r'(?:expense|risk|return|performance)\s+(?:of|for)\s+(.+)'
            ]
        }
    
    def process(self, query: str) -> ProcessedQuery:
        """
        Main entry point: process a user query
        
        Args:
            query: Raw user query string
            
        Returns:
            ProcessedQuery with intent, entities, and filters
        """
        # Normalize query
        normalized = self._normalize_query(query)
        
        # Classify intent
        intent, confidence = self._classify_intent(normalized)
        
        # Extract entities
        entities = self._extract_entities(normalized)
        
        # Build filters
        filters = self._build_filters(entities, intent)
        
        return ProcessedQuery(
            original_query=query,
            normalized_query=normalized,
            intent=intent,
            confidence=confidence,
            entities=entities,
            filters=filters
        )
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query text"""
        # Convert to lowercase
        normalized = query.lower()
        
        # Remove extra whitespace
        normalized = ' '.join(normalized.split())
        
        # Expand common abbreviations
        abbreviations = {
            'sip': 'systematic investment plan',
            'nav': 'net asset value',
            'amc': 'asset management company',
            'aum': 'assets under management'
        }
        
        for abbr, full in abbreviations.items():
            # Only expand if it's a standalone word
            normalized = re.sub(rf'\b{abbr}\b', full, normalized)
        
        return normalized
    
    def _classify_intent(self, query: str) -> tuple:
        """
        Classify query intent using pattern matching
        Returns: (intent, confidence)
        """
        scores = {intent: 0 for intent in QueryIntent}
        
        # Check each intent pattern
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    scores[intent] += 1
        
        # Additional heuristics
        if 'how to' in query or 'download' in query:
            scores[QueryIntent.DOCUMENT] += 0.5
        
        if any(word in query for word in ['best', 'top', 'recommend']):
            scores[QueryIntent.RECOMMENDATION] += 0.5
        
        if 'compare' in query or ' vs ' in query or 'versus' in query:
            scores[QueryIntent.COMPARISON] += 0.5
        
        if any(cat in query for cat in ['elss', 'large cap', 'small cap', 'mid cap']):
            scores[QueryIntent.ATTRIBUTE_BASED] += 0.3
        
        # Get highest scoring intent
        max_intent = max(scores, key=scores.get)
        max_score = scores[max_intent]
        
        # Calculate confidence
        if max_score > 0:
            confidence = min(0.95, 0.5 + max_score * 0.15)
        else:
            # Default to FUND_SPECIFIC if no pattern matches but fund name detected
            if self._extract_fund_name(query):
                max_intent = QueryIntent.FUND_SPECIFIC
                confidence = 0.6
            else:
                max_intent = QueryIntent.GENERAL
                confidence = 0.5
        
        return max_intent, confidence
    
    def _extract_entities(self, query: str) -> Dict[str, Any]:
        """Extract entities from query"""
        entities = {
            'fund_name': self._extract_fund_name(query),
            'amc': self._extract_amc(query),
            'category': self._extract_category(query),
            'attributes': self._extract_attributes(query),
            'comparison_funds': self._extract_comparison_funds(query)
        }
        return {k: v for k, v in entities.items() if v}
    
    def _extract_fund_name(self, query: str) -> Optional[str]:
        """Extract fund name from query"""
        # Pattern: "... of [Fund Name]" or "about [Fund Name]"
        patterns = [
            r'(?:of|for|about)\s+([a-z]+\s+(?:small|mid|large)?\s*(?:cap)?\s*(?:fund|elss)[a-z\s]*)',
            r'([a-z]+\s+(?:small|mid|large)?\s*(?:cap)?\s*(?:fund|elss)[a-z\s]*)(?:\?|$)',
            r'(sbi|hdfc|icici|axis|bandhan|nippon|tata|parag parikh)[a-z\s]*(?:fund|elss)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                fund_name = match.group(1).strip()
                # Clean up fund name
                fund_name = re.sub(r'\s+', ' ', fund_name)
                if len(fund_name) > 3:  # Minimum length check
                    return fund_name.title()
        
        return None
    
    def _extract_amc(self, query: str) -> Optional[str]:
        """Extract AMC name from query"""
        for amc in self.amc_list:
            if amc.lower() in query:
                return amc.title()
        return None
    
    def _extract_category(self, query: str) -> Optional[str]:
        """Extract fund category from query"""
        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    return category
        return None
    
    def _extract_attributes(self, query: str) -> List[str]:
        """Extract attribute mentions from query"""
        attributes = []
        for attr, keywords in self.attribute_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    attributes.append(attr)
                    break
        return attributes
    
    def _extract_comparison_funds(self, query: str) -> List[str]:
        """Extract fund names for comparison queries"""
        funds = []
        
        # Pattern: "Compare X vs Y" or "X vs Y"
        patterns = [
            r'compare\s+(.+?)\s+(?:vs|versus|and|with)\s+(.+)',
            r'(.+?)\s+(?:vs|versus)\s+(.+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                fund1 = match.group(1).strip()
                fund2 = match.group(2).strip()
                
                # Clean up
                fund1 = re.sub(r'\s+', ' ', fund1).title()
                fund2 = re.sub(r'\s+', ' ', fund2).title()
                
                funds = [fund1, fund2]
                break
        
        return funds
    
    def _build_filters(self, entities: Dict, intent: QueryIntent) -> Dict[str, Any]:
        """Build metadata filters based on entities and intent"""
        filters = {}
        
        # Add fund name filter if specific fund mentioned
        if entities.get('fund_name'):
            filters['fund_name'] = {'$contains': entities['fund_name']}
        
        # Add AMC filter
        if entities.get('amc'):
            filters['amc'] = entities['amc']
        
        # Add category filter
        if entities.get('category'):
            filters['category'] = entities['category']
        
        # Add ELSS filter
        if intent == QueryIntent.ATTRIBUTE_BASED and entities.get('category') == 'elss':
            filters['is_elss'] = True
        
        # Add chunk type filter based on attributes
        if entities.get('attributes'):
            attr = entities['attributes'][0]
            chunk_type_map = {
                'expense_ratio': 'financial',
                'exit_load': 'financial',
                'minimum_sip': 'financial',
                'lock_in': 'financial',
                'risk_level': 'risk',
                'benchmark': 'risk'
            }
            if attr in chunk_type_map:
                filters['chunk_type'] = chunk_type_map[attr]
        
        return filters


if __name__ == "__main__":
    # Test the query processor
    processor = QueryProcessor()
    
    test_queries = [
        "What is the expense ratio of SBI Bluechip Fund?",
        "Show me ELSS funds with 3 year lock-in",
        "Compare HDFC Mid Cap vs Nippon Small Cap",
        "How to download mutual fund statements?",
        "Best large cap funds for 2024",
        "What is the risk level of Axis Small Cap Fund?",
        "Funds with minimum SIP of 500 rupees"
    ]
    
    print("Query Processing Tests:")
    print("=" * 70)
    
    for query in test_queries:
        result = processor.process(query)
        print(f"\nQuery: {query}")
        print(f"Intent: {result.intent.value} (confidence: {result.confidence:.2f})")
        print(f"Entities: {result.entities}")
        print(f"Filters: {result.filters}")

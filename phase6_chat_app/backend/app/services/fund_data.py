"""
Fund Data Loader and Query Handler

Loads all 9 mutual funds and provides query matching capabilities.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Load fund data
FUND_DATA = []
FUND_NAMES = []
FUND_LOOKUP = {}

def load_fund_data():
    """Load fund data from Phase 1"""
    global FUND_DATA, FUND_NAMES, FUND_LOOKUP
    
    try:
        fund_file = Path(__file__).parent.parent.parent.parent.parent / "phase1_data_collection" / "data" / "processed" / "extracted_funds.json"
        with open(fund_file, 'r', encoding='utf-8') as f:
            FUND_DATA = json.load(f)
        
        FUND_NAMES = [f['fund_name'] for f in FUND_DATA]
        
        # Create lookup by various name formats
        for fund in FUND_DATA:
            name = fund['fund_name']
            # Original name
            FUND_LOOKUP[name.lower()] = fund
            # Short name (without "Direct Growth")
            short_name = name.replace(' Direct Growth', '').lower()
            FUND_LOOKUP[short_name] = fund
            # Just the main name parts
            parts = name.lower().replace(' direct growth', '').split()
            for i in range(len(parts)):
                key = ' '.join(parts[i:])
                if len(key) > 5:  # Avoid very short keys
                    FUND_LOOKUP[key] = fund
        
        print(f"✓ Loaded {len(FUND_DATA)} funds into lookup")
    except Exception as e:
        print(f"⚠ Could not load fund data: {e}")
        FUND_DATA = []

# Load on module import
load_fund_data()


def identify_fund(query: str) -> Optional[Dict]:
    """
    Identify which fund the user is asking about.
    
    Args:
        query: User's query string
        
    Returns:
        Fund data dictionary or None
    """
    query_lower = query.lower()
    
    # Priority 1: Check for exact full name matches first
    for fund in FUND_DATA:
        fund_name = fund['fund_name'].lower()
        short_name = fund_name.replace(' direct growth', '').lower()
        
        # Check full name (most specific)
        if fund_name in query_lower or short_name in query_lower:
            return fund
    
    # Priority 2: Check for specific fund name patterns
    # Create a scoring system for partial matches
    best_match = None
    best_score = 0
    
    for fund in FUND_DATA:
        fund_name = fund['fund_name'].lower().replace(' direct growth', '')
        parts = fund_name.split()
        
        # Calculate match score
        score = 0
        matched_parts = []
        
        for part in parts:
            if len(part) <= 2:  # Skip very short words
                continue
            if part in query_lower:
                score += len(part)  # Weight by length of matched word
                matched_parts.append(part)
        
        # Require at least 2 significant words to match
        if len(matched_parts) >= 2 and score > best_score:
            best_score = score
            best_match = fund
    
    return best_match


def identify_query_type(query: str) -> str:
    """
    Identify what type of information the user is asking for.
    
    Returns:
        Query type: 'expense_ratio', 'exit_load', 'minimum_sip', 
        'lock_in', 'risk_level', 'benchmark', 'download', 'general'
    """
    query_lower = query.lower()
    
    # Expense ratio queries
    if any(phrase in query_lower for phrase in [
        'expense ratio', 'expense', 'cost', 'fee', 'charges'
    ]):
        return 'expense_ratio'
    
    # Exit load queries
    if any(phrase in query_lower for phrase in [
        'exit load', 'exit', 'redemption', 'withdrawal charge'
    ]):
        return 'exit_load'
    
    # Minimum SIP queries
    if any(phrase in query_lower for phrase in [
        'minimum sip', 'min sip', 'sip amount', 'minimum investment',
        'least amount', 'smallest sip'
    ]):
        return 'minimum_sip'
    
    # Lock-in period queries
    if any(phrase in query_lower for phrase in [
        'lock-in', 'lock in', 'locking period', 'locked', 'elss period'
    ]):
        return 'lock_in'
    
    # Risk level queries
    if any(phrase in query_lower for phrase in [
        'risk', 'riskometer', 'risk level', 'risky', 'safe', 'danger'
    ]):
        return 'risk_level'
    
    # Benchmark queries
    if any(phrase in query_lower for phrase in [
        'benchmark', 'index', 'compares to', 'tracks', 'follows'
    ]):
        return 'benchmark'
    
    # Download/statement queries
    if any(phrase in query_lower for phrase in [
        'download', 'statement', 'report', 'get document', 'how to get'
    ]):
        return 'download'
    
    return 'general'


def is_out_of_scope(query: str) -> bool:
    """
    Check if the query is outside the chatbot's scope.
    
    Returns:
        True if out of scope, False otherwise
    """
    query_lower = query.lower()
    
    # Non-financial topics
    non_financial = [
        'weather', 'sports', 'movie', 'food', 'restaurant', 'hotel',
        'travel', 'politics', 'news', 'music', 'game', 'crypto',
        'bitcoin', 'stock', 'share price', 'ipo', 'insurance',
        'loan', 'credit card', 'bank account'
    ]
    
    for topic in non_financial:
        if topic in query_lower:
            return True
    
    # Personal advice requests (these should be handled by guardrails, but double-check)
    if any(phrase in query_lower for phrase in [
        'should i invest', 'should i buy', 'recommend', 'good idea',
        'will it go up', 'future price', 'prediction'
    ]):
        return True
    
    return False


def get_fund_response(fund: Dict, query_type: str) -> Tuple[str, List[Dict]]:
    """
    Generate a response for a specific fund and query type.
    
    Args:
        fund: Fund data dictionary
        query_type: Type of query
        
    Returns:
        Tuple of (response_text, sources)
    """
    fund_name = fund['fund_name']
    source = {
        'id': '1',
        'fund_name': fund_name,
        'source_url': fund.get('source_url', ''),
        'display_name': fund_name.replace(' Direct Growth', '')
    }
    
    if query_type == 'expense_ratio':
        value = fund.get('expense_ratio', 'Not available')
        return (
            f"The expense ratio of {fund_name} is {value}.",
            [source]
        )
    
    elif query_type == 'exit_load':
        value = fund.get('exit_load', 'Not available')
        if value == 'Not available' or not value:
            # For ELSS funds
            if 'ELSS' in fund_name:
                return (
                    f"{fund_name} does not have an exit load. ELSS funds have a mandatory 3-year lock-in period instead.",
                    [source]
                )
            value = 'No exit load information available'
        return (
            f"The exit load for {fund_name} is: {value}",
            [source]
        )
    
    elif query_type == 'minimum_sip':
        value = fund.get('minimum_sip', 'Not available')
        return (
            f"The minimum SIP amount for {fund_name} is {value}.",
            [source]
        )
    
    elif query_type == 'lock_in':
        value = fund.get('lock_in_period', 'Not available')
        if 'ELSS' in fund_name:
            return (
                f"{fund_name} has a lock-in period of 3 years, as required for ELSS tax-saving funds under Section 80C.",
                [source]
            )
        return (
            f"The lock-in period for {fund_name} is: {value}",
            [source]
        )
    
    elif query_type == 'risk_level':
        value = fund.get('risk_level', 'Not available')
        return (
            f"{fund_name} has a risk level of '{value}' according to the Riskometer.",
            [source]
        )
    
    elif query_type == 'benchmark':
        value = fund.get('benchmark', 'Not available')
        return (
            f"The benchmark for {fund_name} is {value}.",
            [source]
        )
    
    elif query_type == 'download':
        return (
            f"To download statements for {fund_name}, please visit the fund page on Groww: {fund.get('source_url', 'https://groww.in/mutual-funds')}",
            [source]
        )
    
    else:  # general
        # Provide a summary
        return (
            f"Here is the information for {fund_name}:\n\n"
            f"• Expense Ratio: {fund.get('expense_ratio', 'N/A')}\n"
            f"• Risk Level: {fund.get('risk_level', 'N/A')}\n"
            f"• Minimum SIP: {fund.get('minimum_sip', 'N/A')}\n"
            f"• Exit Load: {fund.get('exit_load', 'N/A')}\n"
            f"• Benchmark: {fund.get('benchmark', 'N/A')}",
            [source]
        )


def get_all_funds_summary() -> str:
    """Get a summary of all available funds."""
    fund_list = '\n'.join([f"• {f['fund_name']}" for f in FUND_DATA])
    return (
        f"I have information about {len(FUND_DATA)} mutual funds:\n\n"
        f"{fund_list}\n\n"
        "You can ask me about:\n"
        "• Expense ratios\n"
        "• Exit loads\n"
        "• Minimum SIP amounts\n"
        "• Lock-in periods\n"
        "• Risk levels\n"
        "• Benchmark indices\n\n"
        "What would you like to know?"
    )


def get_out_of_scope_response() -> str:
    """Get the standard out-of-scope response."""
    return (
        "That question is outside my scope. I can only assist with general information "
        "related to mutual funds and financial concepts.\n\n"
        "I can help you with:\n"
        "• Expense ratios and fees\n"
        "• Exit loads and redemption charges\n"
        "• Minimum SIP amounts\n"
        "• Lock-in periods (especially for ELSS)\n"
        "• Risk levels and benchmarks\n"
        "• Fund comparisons\n\n"
        "Please ask me about one of the mutual funds in my database."
    )

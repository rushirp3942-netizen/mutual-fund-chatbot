"""
Flask API Backend for Mutual Fund RAG Chatbot
Deploy this to Render.com or PythonAnywhere for free API hosting
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import sys
from pathlib import Path
from typing import List, Dict, Optional, Any
import os

app = Flask(__name__)
CORS(app, origins=["*"])  # Allow all origins for now

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "phase1_data_collection"))
sys.path.insert(0, str(Path(__file__).parent / "phase6_chat_app" / "backend"))

# Load fund data
def load_funds_data():
    """Load fund data from Phase 1"""
    try:
        fund_file = Path(__file__).parent / "phase1_data_collection" / "data" / "processed" / "extracted_funds.json"
        with open(fund_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Could not load fund data: {e}")
        return []

FUNDS_DATA = load_funds_data()

# Import chat logic
try:
    from app.services.fund_data import (
        identify_fund, identify_query_type, get_fund_response,
        get_all_funds_summary, is_out_of_scope
    )
    print("✓ Fund data service loaded")
except Exception as e:
    print(f"⚠ Could not load fund data service: {e}")
    # Fallback functions
    def identify_fund(query):
        query_lower = query.lower()
        for fund in FUNDS_DATA:
            if fund['fund_name'].lower() in query_lower:
                return fund
        return None
    
    def identify_query_type(query):
        query_lower = query.lower()
        if 'expense ratio' in query_lower:
            return 'expense_ratio'
        if 'exit load' in query_lower:
            return 'exit_load'
        if 'sip' in query_lower:
            return 'minimum_sip'
        if 'lock' in query_lower:
            return 'lock_in'
        if 'risk' in query_lower:
            return 'risk_level'
        if 'benchmark' in query_lower:
            return 'benchmark'
        if 'download' in query_lower or 'statement' in query_lower:
            return 'download'
        return 'general'
    
    def get_fund_response(fund, query_type):
        return f"Information for {fund['fund_name']}", []
    
    def get_all_funds_summary():
        return f"Available funds: {len(FUNDS_DATA)}"
    
    def is_out_of_scope(query):
        return False

@app.route('/')
def home():
    """API home"""
    return jsonify({
        "status": "online",
        "service": "Mutual Fund RAG Chatbot API",
        "version": "1.0.0",
        "funds_loaded": len(FUNDS_DATA)
    })

@app.route('/funds', methods=['GET'])
def list_funds():
    """List all funds"""
    return jsonify({
        "funds": FUNDS_DATA,
        "total": len(FUNDS_DATA)
    })

@app.route('/funds/<fund_name>', methods=['GET'])
def get_fund(fund_name):
    """Get specific fund details"""
    fund_name_normalized = fund_name.replace('-', ' ').lower()
    
    for fund in FUNDS_DATA:
        if fund.get('fund_name', '').lower() == fund_name_normalized or \
           fund_name_normalized in fund.get('fund_name', '').lower():
            return jsonify(fund)
    
    return jsonify({"error": "Fund not found"}), 404

@app.route('/chat', methods=['POST'])
def chat():
    """Process chat message"""
    data = request.json
    message = data.get('message', '')
    
    if not message:
        return jsonify({"error": "No message provided"}), 400
    
    # Check if out of scope
    if is_out_of_scope(message):
        return jsonify({
            "message": {
                "role": "assistant",
                "content": "That question is outside my scope. I can only assist with general information related to mutual funds and financial concepts.",
                "timestamp": "2024-01-01T00:00:00"
            },
            "sources": [],
            "rag_compliant": True
        })
    
    # Check for investment advice
    message_lower = message.lower()
    if any(phrase in message_lower for phrase in ['should i invest', 'recommend', 'should i buy', 'good investment']):
        return jsonify({
            "message": {
                "role": "assistant",
                "content": "I can't provide investment advice or recommendations. I'm designed to share factual information about mutual funds in my knowledge base.\n\nI can tell you about:\n• Expense ratios and fees\n• Risk levels and benchmarks\n• Minimum investment amounts\n• Fund categories and types\n\nFor investment advice, please consult a SEBI-registered investment advisor.",
                "timestamp": "2024-01-01T00:00:00"
            },
            "sources": [],
            "rag_compliant": True
        })
    
    # Identify fund and get response
    fund = identify_fund(message)
    
    if fund:
        query_type = identify_query_type(message)
        content, sources = get_fund_response(fund, query_type)
        
        return jsonify({
            "message": {
                "role": "assistant",
                "content": content,
                "timestamp": "2024-01-01T00:00:00"
            },
            "sources": sources,
            "rag_compliant": True
        })
    
    # General response
    return jsonify({
        "message": {
            "role": "assistant",
            "content": get_all_funds_summary(),
            "timestamp": "2024-01-01T00:00:00"
        },
        "sources": [],
        "rag_compliant": True
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        "status": "healthy",
        "funds_loaded": len(FUNDS_DATA)
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

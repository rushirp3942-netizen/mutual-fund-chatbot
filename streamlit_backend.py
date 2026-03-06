"""
Streamlit Backend for Mutual Fund RAG Chatbot
Deploy this to Streamlit Cloud
"""

import streamlit as st
import json
import sys
from pathlib import Path
from typing import List, Dict, Optional, Any
import os

# Add phase1 to path for fund data
sys.path.insert(0, str(Path(__file__).parent / "phase1_data_collection"))

# Page config
st.set_page_config(
    page_title="Mutual Fund RAG API",
    page_icon="📊",
    layout="wide"
)

# Load fund data
@st.cache_data
def load_funds_data():
    """Load fund data from Phase 1"""
    try:
        fund_file = Path(__file__).parent / "phase1_data_collection" / "data" / "processed" / "extracted_funds.json"
        with open(fund_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Could not load fund data: {e}")
        return []

_funds_data = load_funds_data()

# Initialize Groq client (if API key is set)
@st.cache_resource
def get_llm_client():
    """Initialize Groq client"""
    try:
        from groq import Groq
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            return Groq(api_key=api_key)
    except:
        pass
    return None

# Sidebar
st.sidebar.title("📊 Mutual Fund RAG API")
st.sidebar.markdown("---")
st.sidebar.info("Backend API for Mutual Fund Chatbot")

# Main content
st.title("Mutual Fund RAG Chatbot Backend")
st.markdown("---")

# Health check endpoint simulation
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Funds", len(_funds_data))
with col2:
    st.metric("API Status", "✅ Online")
with col3:
    st.metric("Version", "1.0.0")

st.markdown("---")

# API Documentation
st.header("📚 API Endpoints")

with st.expander("GET /funds - List all funds"):
    st.code("""
    Response:
    {
        "funds": [...],
        "total": 9,
        "page": 1,
        "page_size": 10
    }
    """, language="json")
    if st.button("Test /funds"):
        st.json({
            "funds": _funds_data,
            "total": len(_funds_data),
            "page": 1,
            "page_size": 10
        })

with st.expander("GET /funds/{fund_name} - Get fund details"):
    fund_names = [f['fund_name'] for f in _funds_data]
    selected_fund = st.selectbox("Select a fund", fund_names)
    if st.button("Get Fund Details"):
        for fund in _funds_data:
            if fund['fund_name'] == selected_fund:
                st.json(fund)
                break

with st.expander("POST /chat - Send message"):
    st.code("""
    Request:
    {
        "message": "What is the expense ratio of SBI ELSS?",
        "session_id": "optional-session-id"
    }
    
    Response:
    {
        "message": {
            "role": "assistant",
            "content": "The expense ratio...",
            "timestamp": "..."
        },
        "sources": [...]
    }
    """, language="json")
    
    test_message = st.text_input("Test message", "What is the expense ratio of SBI ELSS?")
    if st.button("Send Test Message"):
        with st.spinner("Processing..."):
            # Simple response logic (same as fallback)
            from phase6_chat_app.backend.app.services.fund_data import (
                identify_fund, identify_query_type, get_fund_response
            )
            
            fund = identify_fund(test_message)
            if fund:
                query_type = identify_query_type(test_message)
                content, sources = get_fund_response(fund, query_type)
                response = {
                    "message": {
                        "role": "assistant",
                        "content": content,
                        "timestamp": "2024-01-01T00:00:00"
                    },
                    "sources": sources,
                    "session_id": "test-session"
                }
            else:
                response = {
                    "message": {
                        "role": "assistant",
                        "content": "I can help you with information about mutual funds. Please specify which fund you're interested in.",
                        "timestamp": "2024-01-01T00:00:00"
                    },
                    "sources": [],
                    "session_id": "test-session"
                }
            st.json(response)

# Fund Browser
st.markdown("---")
st.header("🔍 Fund Browser")

if _funds_data:
    cols = st.columns(3)
    for i, fund in enumerate(_funds_data):
        with cols[i % 3]:
            with st.container(border=True):
                st.subheader(fund['fund_name'][:30] + "..." if len(fund['fund_name']) > 30 else fund['fund_name'])
                st.write(f"**Category:** {fund.get('category', 'N/A')}")
                st.write(f"**NAV:** {fund.get('nav', 'N/A')}")
                st.write(f"**Expense Ratio:** {fund.get('expense_ratio', 'N/A')}")
                st.write(f"**Risk:** {fund.get('risk_level', 'N/A')}")
                
                # Clean exit load
                exit_load = fund.get('exit_load', '')
                if exit_load and isinstance(exit_load, str):
                    # Truncate at JSON markers
                    for marker in ['","', '":"', '"sub_category"']:
                        if marker in exit_load:
                            exit_load = exit_load.split(marker)[0]
                    exit_load = exit_load.rstrip('",').strip()
                    if exit_load:
                        st.write(f"**Exit Load:** {exit_load[:100]}...")

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using Streamlit | [View on GitHub](https://github.com)")

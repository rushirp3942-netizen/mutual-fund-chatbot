"""
Mutual Fund RAG Chatbot - Full App (Frontend + Backend)
Deploy to Streamlit Cloud only - no Vercel/Render needed
"""

import streamlit as st
import json
import sys
import os
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "phase1_data_collection"))
sys.path.insert(0, str(Path(__file__).parent / "phase6_chat_app" / "backend"))

# Page config
st.set_page_config(
    page_title="Mutual Fund Assistant",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── Custom CSS ───────────────────────────────────────────────
st.markdown("""
<style>
    /* Hide default streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* App background */
    .stApp { background-color: #f0f4f8; }

    /* Navbar */
    .navbar {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 15px 30px;
        border-radius: 12px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .navbar-brand { color: white; font-size: 22px; font-weight: 700; }
    .navbar-sub { color: #a0aec0; font-size: 13px; }

    /* Chat message styles */
    .user-msg {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 12px 18px;
        border-radius: 18px 18px 4px 18px;
        margin: 8px 0;
        max-width: 75%;
        margin-left: auto;
        text-align: right;
    }
    .bot-msg {
        background: white;
        color: #2d3748;
        padding: 12px 18px;
        border-radius: 18px 18px 18px 4px;
        margin: 8px 0;
        max-width: 75%;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.06);
    }
    .msg-time { font-size: 11px; color: #a0aec0; margin-top: 4px; }

    /* Fund card */
    .fund-card {
        background: white;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 14px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        transition: transform 0.2s;
    }
    .fund-name { font-weight: 700; font-size: 15px; color: #1a1a2e; }
    .fund-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        background: #ebf4ff;
        color: #3182ce;
        margin-bottom: 8px;
    }
    .fund-metric { font-size: 13px; color: #4a5568; margin: 3px 0; }

    /* Input area */
    .stTextInput > div > div > input {
        border-radius: 25px !important;
        border: 2px solid #e2e8f0 !important;
        padding: 12px 20px !important;
        font-size: 15px !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102,126,234,0.2) !important;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 25px !important;
        background: linear-gradient(135deg, #667eea, #764ba2) !important;
        color: white !important;
        border: none !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(102,126,234,0.4) !important;
    }

    /* Suggestion chips */
    .suggestion-chip {
        display: inline-block;
        padding: 6px 14px;
        background: #ebf4ff;
        color: #3182ce;
        border-radius: 20px;
        font-size: 13px;
        margin: 4px;
        cursor: pointer;
        border: 1px solid #bee3f8;
    }
</style>
""", unsafe_allow_html=True)

# ─── Load Fund Data ───────────────────────────────────────────
@st.cache_data
def load_funds_data():
    try:
        fund_file = Path(__file__).parent / "phase1_data_collection" / "data" / "processed" / "extracted_funds.json"
        with open(fund_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return []

FUNDS_DATA = load_funds_data()

# ─── Chat Logic ───────────────────────────────────────────────
try:
    from app.services.fund_data import (
        identify_fund, identify_query_type, get_fund_response,
        get_all_funds_summary, is_out_of_scope, get_out_of_scope_response
    )
except:
    def identify_fund(query):
        query_lower = query.lower()
        for fund in FUNDS_DATA:
            name = fund.get('fund_name', '').lower()
            parts = [p for p in name.split() if len(p) > 3]
            matched = sum(1 for p in parts if p in query_lower)
            if matched >= 2:
                return fund
        return None

    def identify_query_type(query):
        q = query.lower()
        if any(x in q for x in ['expense ratio', 'expense', 'cost', 'fee']): return 'expense_ratio'
        if any(x in q for x in ['exit load', 'exit', 'redemption']): return 'exit_load'
        if any(x in q for x in ['minimum sip', 'min sip', 'sip']): return 'minimum_sip'
        if any(x in q for x in ['lock-in', 'lock in', 'locking']): return 'lock_in'
        if any(x in q for x in ['risk', 'riskometer']): return 'risk_level'
        if any(x in q for x in ['benchmark', 'index']): return 'benchmark'
        if any(x in q for x in ['download', 'statement', 'how to get']): return 'download'
        return 'general'

    def get_fund_response(fund, query_type):
        name = fund.get('fund_name', '')
        source_url = fund.get('source_url', f'https://groww.in/mutual-funds/{name.replace(" ", "-").lower()}')
        if query_type == 'expense_ratio':
            return f"The expense ratio of **{name}** is **{fund.get('expense_ratio', 'N/A')}**.\n\n📊 [View on Groww]({source_url})", []
        elif query_type == 'exit_load':
            return f"The exit load for **{name}** is: {fund.get('exit_load', 'N/A')}\n\n📊 [View on Groww]({source_url})", []
        elif query_type == 'minimum_sip':
            return f"The minimum SIP amount for **{name}** is **{fund.get('minimum_sip', 'N/A')}**.\n\n📊 [View on Groww]({source_url})", []
        elif query_type == 'lock_in':
            if 'ELSS' in name:
                return f"**{name}** has a mandatory **3-year lock-in period** under Section 80C.\n\n📊 [View on Groww]({source_url})", []
            return f"**{name}** has no lock-in period.\n\n📊 [View on Groww]({source_url})", []
        elif query_type == 'risk_level':
            return f"**{name}** has a risk level of **'{fund.get('risk_level', 'N/A')}'** according to the Riskometer.\n\n📊 [View on Groww]({source_url})", []
        elif query_type == 'benchmark':
            return f"The benchmark for **{name}** is **{fund.get('benchmark', 'N/A')}**.\n\n📊 [View on Groww]({source_url})", []
        elif query_type == 'download':
            return get_download_response(), []
        else:
            return (f"Here is the information for **{name}**:\n\n"
                    f"• **Expense Ratio:** {fund.get('expense_ratio', 'N/A')}\n"
                    f"• **Risk Level:** {fund.get('risk_level', 'N/A')}\n"
                    f"• **Minimum SIP:** {fund.get('minimum_sip', 'N/A')}\n"
                    f"• **Exit Load:** {fund.get('exit_load', 'N/A')}\n"
                    f"• **Benchmark:** {fund.get('benchmark', 'N/A')}\n\n"
                    f"📊 [View on Groww]({source_url})"), []

    def get_all_funds_summary():
        fund_list = '\n'.join([f"• {f['fund_name']}" for f in FUNDS_DATA])
        return (f"I have information about **{len(FUNDS_DATA)} mutual funds**:\n\n{fund_list}\n\n"
                "You can ask me about expense ratios, exit loads, minimum SIP, lock-in periods, risk levels, or benchmarks.")

    def is_out_of_scope(query):
        q = query.lower()
        return any(t in q for t in ['weather', 'sports', 'movie', 'food', 'crypto', 'bitcoin', 'stock price'])

    def get_out_of_scope_response():
        return "That question is outside my scope. I can only assist with mutual fund information."


def get_download_response():
    return """You can download your mutual fund statement through the following methods:

**Through the AMC Website**
Visit the Asset Management Company (AMC) website where you invested, log in to your account, and download your account statement from the portfolio or statement section.

**Through Registrar Websites (CAMS or KFintech)**
If your fund is serviced by a registrar such as CAMS or KFintech, you can request a consolidated account statement by entering your registered email ID and PAN.

**Through Your Investment Platform**
If you invested using a platform such as a broker or investment app, you can download the statement from the portfolio or reports section of that platform.

Statements are usually available in PDF format and include details such as transactions, holdings, and NAV history."""


def get_bot_response(message):
    msg_lower = message.lower()

    # Out of scope
    if is_out_of_scope(message):
        return get_out_of_scope_response()

    # Investment advice guard
    if any(p in msg_lower for p in ['should i invest', 'recommend', 'should i buy', 'good investment', 'best fund']):
        return ("I can't provide investment advice or recommendations. I'm designed to share factual information about mutual funds.\n\n"
                "I can tell you about:\n• Expense ratios and fees\n• Risk levels and benchmarks\n• Minimum SIP amounts\n• Fund categories\n\n"
                "For investment advice, please consult a SEBI-registered investment advisor.")

    # Download/statement query (no fund needed)
    if any(p in msg_lower for p in ['download', 'statement', 'how to get statement', 'get document']):
        return get_download_response()

    # Fund-specific query
    fund = identify_fund(message)
    if fund:
        query_type = identify_query_type(message)
        content, _ = get_fund_response(fund, query_type)
        return content

    # General
    return get_all_funds_summary()


# ─── Session State ────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "page" not in st.session_state:
    st.session_state.page = "chat"

# ─── Navbar ───────────────────────────────────────────────────
st.markdown("""
<div class="navbar">
    <div>
        <div class="navbar-brand">📊 Mutual Fund Assistant</div>
        <div class="navbar-sub">Your AI-powered mutual fund information guide</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── Page Navigation ──────────────────────────────────────────
col_chat, col_funds = st.columns([1, 1])
with col_chat:
    if st.button("💬 Chat", use_container_width=True):
        st.session_state.page = "chat"
with col_funds:
    if st.button("🔍 Browse Funds", use_container_width=True):
        st.session_state.page = "funds"

st.markdown("---")

# ════════════════════════════════════════════════════════════
# CHAT PAGE
# ════════════════════════════════════════════════════════════
if st.session_state.page == "chat":

    # Welcome message
    if not st.session_state.messages:
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown("""Hello! I'm your **Mutual Fund Assistant**. I can help you with:
- 💰 Expense ratios and fees
- ⚠️ Risk levels and benchmarks
- 📅 Minimum SIP amounts
- 🔒 Lock-in periods
- 📥 How to download statements

**What would you like to know?**""")

        # Suggestion chips
        st.markdown("**Quick questions:**")
        suggestions = [
            "What is the expense ratio of SBI ELSS?",
            "Show me all available funds",
            "How to download mutual fund statement?",
            "What is the minimum SIP for Bandhan Small Cap?"
        ]
        cols = st.columns(2)
        for i, suggestion in enumerate(suggestions):
            with cols[i % 2]:
                if st.button(suggestion, key=f"sug_{i}", use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": suggestion})
                    response = get_bot_response(suggestion)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.rerun()

    # Display chat history
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(msg["content"])

    # Chat input
    user_input = st.chat_input("Ask me about mutual funds...")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Thinking..."):
                response = get_bot_response(user_input)
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

    # Clear chat button
    if st.session_state.messages:
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.rerun()

# ════════════════════════════════════════════════════════════
# FUND BROWSER PAGE
# ════════════════════════════════════════════════════════════
elif st.session_state.page == "funds":

    st.subheader(f"📋 Available Funds ({len(FUNDS_DATA)} total)")

    # Search
    search = st.text_input("🔍 Search funds...", placeholder="e.g. SBI, ELSS, Small Cap")

    # Filter
    categories = list(set(f.get('category', 'N/A') for f in FUNDS_DATA))
    selected_cat = st.selectbox("Filter by Category", ["All"] + sorted(categories))

    # Apply filters
    filtered = FUNDS_DATA
    if search:
        filtered = [f for f in filtered if search.lower() in f.get('fund_name', '').lower()]
    if selected_cat != "All":
        filtered = [f for f in filtered if f.get('category') == selected_cat]

    st.markdown(f"Showing **{len(filtered)}** funds")
    st.markdown("---")

    # Display fund cards
    if filtered:
        cols = st.columns(2)
        for i, fund in enumerate(filtered):
            with cols[i % 2]:
                exit_load = fund.get('exit_load', 'N/A')
                if isinstance(exit_load, str):
                    for marker in ['","', '":"', '"sub_category"']:
                        if marker in exit_load:
                            exit_load = exit_load.split(marker)[0]
                    exit_load = exit_load.rstrip('",').strip()[:80]

                risk = fund.get('risk_level', 'N/A')
                risk_color = {"Very High": "🔴", "High": "🟠", "Moderate": "🟡", "Low": "🟢"}.get(risk, "⚪")

                with st.container(border=True):
                    st.markdown(f"**{fund.get('fund_name', 'N/A')}**")
                    st.caption(f"🏢 {fund.get('amc', 'N/A')} | 📂 {fund.get('category', 'N/A')}")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.metric("NAV", fund.get('nav', 'N/A'))
                        st.metric("Expense Ratio", fund.get('expense_ratio', 'N/A'))
                    with c2:
                        st.metric("Min SIP", fund.get('minimum_sip', 'N/A'))
                        st.metric(f"Risk {risk_color}", risk)
                    st.caption(f"📊 Benchmark: {fund.get('benchmark', 'N/A')}")
                    if exit_load:
                        st.caption(f"💸 Exit Load: {exit_load}")
    else:
        st.info("No funds found matching your search.")

# ─── Footer ───────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:#a0aec0; font-size:13px;'>"
    "📊 Mutual Fund Assistant | For informational purposes only | "
    "Not investment advice | Consult a SEBI-registered advisor"
    "</div>",
    unsafe_allow_html=True
)

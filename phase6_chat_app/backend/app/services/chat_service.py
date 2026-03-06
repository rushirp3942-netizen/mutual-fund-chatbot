"""
Chat Service - Core business logic for chat interactions.

Integrates with Phase 3 (Retrieval) and Phase 4 (LLM) components.
"""

import time
import sys
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

# Add paths to previous phases
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "phase3_retrieval"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "phase4_llm_integration"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "config"))

from .session_manager import session_manager
from .fund_data import (
    identify_fund, identify_query_type, is_out_of_scope,
    get_fund_response, get_all_funds_summary, get_out_of_scope_response
)


class ChatService:
    """
    Main chat service that orchestrates the RAG pipeline.
    
    Flow:
    1. Receive user message
    2. Check guardrails (Phase 4)
    3. Retrieve relevant chunks (Phase 3)
    4. Generate response with LLM (Phase 4)
    5. Return formatted response
    """
    
    def __init__(self):
        self.session_manager = session_manager
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize RAG components from previous phases"""
        try:
            # Import Phase 3 components
            from src.retrieval.hybrid_retriever import HybridRetriever
            self.retriever = HybridRetriever()
            print("✓ Retriever initialized")
        except Exception as e:
            print(f"⚠ Retriever not available: {e}")
            self.retriever = None
        
        try:
            # Import Phase 4 components
            from src.llm.groq_client import GroqClient
            from src.prompts.prompt_builder import PromptBuilder
            from src.guardrails.scope_checker import ScopeChecker
            
            self.llm_client = GroqClient()
            self.prompt_builder = PromptBuilder()
            self.scope_checker = ScopeChecker()
            print("✓ LLM components initialized")
        except Exception as e:
            print(f"⚠ LLM components not available: {e}")
            self.llm_client = None
            self.prompt_builder = None
            self.scope_checker = None
    
    async def process_message(
        self,
        message: str,
        session_id: Optional[str] = None,
        history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Process a user message and generate a response.
        
        Args:
            message: User's message
            session_id: Optional session ID
            history: Optional conversation history
            
        Returns:
            Response dictionary with message, sources, and metadata
        """
        start_time = time.time()
        
        # Create or get session
        if not session_id:
            session_id = self.session_manager.create_session()
        
        # Add user message to session
        self.session_manager.add_message(session_id, 'user', message)
        
        # Check if RAG components are available
        if not all([self.retriever, self.llm_client, self.prompt_builder]):
            # Fallback response when components not available
            response = self._fallback_response(message)
        else:
            # Full RAG pipeline
            response = await self._rag_pipeline(message, session_id)
        
        # Add assistant response to session
        self.session_manager.add_message(
            session_id,
            'assistant',
            response['content'],
            citations=response.get('sources', [])
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        return {
            'message': {
                'role': 'assistant',
                'content': response['content'],
                'timestamp': datetime.now().isoformat(),
                'citations': response.get('sources', [])
            },
            'session_id': session_id,
            'sources': response.get('sources', []),
            'rag_compliant': response.get('rag_compliant', True),
            'processing_time_ms': processing_time
        }
    
    async def _rag_pipeline(self, message: str, session_id: str) -> Dict[str, Any]:
        """
        Execute the full RAG pipeline.
        """
        # Step 1: Check guardrails
        guardrail_result = self.scope_checker.check_query(message)
        
        if guardrail_result.action.value == 'block':
            return {
                'content': guardrail_result.response,
                'sources': [],
                'rag_compliant': True
            }
        
        # Step 2: Retrieve relevant chunks
        try:
            retrieved_chunks = self.retriever.retrieve(message, top_k=5)
        except Exception as e:
            print(f"Retrieval error: {e}")
            retrieved_chunks = []
        
        # Step 3: Check context sufficiency
        context_check = self.scope_checker.check_context_sufficiency(
            retrieved_chunks, message
        )
        
        if context_check.action.value == 'block':
            return {
                'content': context_check.response,
                'sources': [],
                'rag_compliant': True
            }
        
        # Step 4: Build prompt with context
        system_prompt = self.prompt_builder.build_system_prompt(retrieved_chunks)
        user_message = self.prompt_builder.build_user_message(message)
        
        # Step 5: Generate response with LLM
        try:
            llm_response = self.llm_client.generate(
                system_prompt=system_prompt,
                user_message=user_message,
                context=retrieved_chunks
            )
            
            return {
                'content': llm_response.content,
                'sources': llm_response.citations,
                'rag_compliant': llm_response.rag_compliant
            }
            
        except Exception as e:
            print(f"LLM error: {e}")
            return {
                'content': "I apologize, but I'm having trouble generating a response right now. Please try again.",
                'sources': [],
                'rag_compliant': True
            }
    
    def _fallback_response(self, message: str) -> Dict[str, Any]:
        """
        Enhanced fallback response that handles all 9 funds properly.
        """
        message_lower = message.lower()
        
        # Check for investment advice (should be blocked)
        if 'should i invest' in message_lower or 'recommend' in message_lower or \
           'should i buy' in message_lower or 'good investment' in message_lower:
            return {
                'content': "I can't provide investment advice or recommendations. I'm designed to share factual information about mutual funds in my knowledge base.\n\nI can tell you about:\n• Expense ratios and fees\n• Risk levels and benchmarks\n• Minimum investment amounts\n• Fund categories and types\n\nFor investment advice, please consult a SEBI-registered investment advisor.",
                'sources': [],
                'rag_compliant': True
            }
        
        # Check if out of scope
        if is_out_of_scope(message):
            return {
                'content': get_out_of_scope_response(),
                'sources': [],
                'rag_compliant': True
            }
        
        # Try to identify the fund
        fund = identify_fund(message)
        
        if fund:
            # Identify query type and get response
            query_type = identify_query_type(message)
            content, sources = get_fund_response(fund, query_type)
            
            # Format sources with display names
            formatted_sources = []
            for src in sources:
                formatted_sources.append({
                    'id': src['id'],
                    'fund_name': src['display_name'],
                    'source_url': src['source_url']
                })
            
            return {
                'content': content,
                'sources': formatted_sources,
                'rag_compliant': True
            }
        
        # If no specific fund identified, check if it's a general question
        query_type = identify_query_type(message)
        
        if query_type == 'general':
            # Return list of all funds
            return {
                'content': get_all_funds_summary(),
                'sources': [],
                'rag_compliant': True
            }
        else:
            # They asked about a specific attribute but didn't specify fund
            return {
                'content': f"I can help you with {query_type.replace('_', ' ')} information. Please specify which fund you're interested in.\n\n" + get_all_funds_summary(),
                'sources': [],
                'rag_compliant': True
            }
    
    def get_session_history(self, session_id: str) -> List[Dict]:
        """Get chat history for a session"""
        return self.session_manager.get_history(session_id)
    
    def clear_session(self, session_id: str):
        """Clear a chat session"""
        self.session_manager.delete_session(session_id)


# Global chat service instance
chat_service = ChatService()

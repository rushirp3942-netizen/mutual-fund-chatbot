"""
Prompt Builder for Mutual Fund RAG Chatbot
Builds strict RAG-enforcing prompts
"""

from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class RAGPromptTemplates:
    """Collection of RAG-enforcing prompt templates"""
    
    # Strict RAG system prompt - ENFORCES context-only responses
    STRICT_RAG_SYSTEM = """You are a mutual fund information assistant operating under STRICT constraints.

ABSOLUTE RULES (Violating these is forbidden):
1. ONLY use information from the CONTEXT section below
2. NEVER use your general knowledge about mutual funds, finance, or investing
3. If the answer is NOT in the CONTEXT, you MUST say: "I don't have enough information in my knowledge base to answer that question."
4. ALWAYS cite sources using [1], [2], [3] format immediately after each fact
5. Be concise and factual - no opinions, no advice
6. NEVER provide investment advice or recommendations
7. If CONTEXT is empty, you CANNOT answer - you must decline

WHAT YOU CAN ANSWER:
- Fund details (expense ratio, risk level, minimum SIP, exit load)
- Fund categories and types (ELSS, Large Cap, Mid Cap, Small Cap)
- Benchmark indices and risk profiles
- Document download procedures

WHAT YOU CANNOT ANSWER (Decline these):
- Investment advice ("Should I invest in X?")
- Future performance predictions ("Will this fund go up?")
- Personal financial planning
- Non-mutual fund topics
- Questions about funds not in the CONTEXT

CITATION FORMAT:
- Use [1] for first source, [2] for second, etc.
- Place citation immediately after the fact: "The expense ratio is 0.92% [1]."
- Multiple citations: "ELSS funds have 3-year lock-in [1][2]."

CONTEXT:
{context}

Remember: If the CONTEXT doesn't contain the answer, you MUST decline."""
    
    # Out-of-scope response template
    OUT_OF_SCOPE_RESPONSE = """I apologize, but I can only answer questions about mutual funds in my knowledge base.

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
    
    # Insufficient context response
    INSUFFICIENT_CONTEXT = """I don't have enough information in my knowledge base to answer that question.

The retrieved context doesn't contain details about {topic}.

I can tell you about:
• Expense ratios, exit loads, and minimum SIP amounts
• Risk levels and benchmark indices
• Fund categories and AMC information

Would you like to know about a different aspect of this fund or another fund?"""


class PromptBuilder:
    """Builds prompts with strict RAG enforcement"""
    
    def __init__(self):
        self.templates = RAGPromptTemplates()
    
    def build_system_prompt(
        self,
        context_chunks: List[Dict[str, str]],
        query_intent: Optional[str] = None
    ) -> str:
        """
        Build RAG-enforcing system prompt with context
        
        Args:
            context_chunks: Retrieved chunks with fund_name, text, source_url
            query_intent: Optional intent classification
            
        Returns:
            Formatted system prompt
        """
        # Format context
        formatted_context = self._format_context(context_chunks)
        
        # Build prompt
        system_prompt = self.templates.STRICT_RAG_SYSTEM.format(
            context=formatted_context
        )
        
        return system_prompt
    
    def _format_context(self, chunks: List[Dict[str, str]]) -> str:
        """Format retrieved chunks for prompt"""
        if not chunks:
            return "[NO CONTEXT AVAILABLE - You MUST decline to answer]"
        
        formatted = []
        for i, chunk in enumerate(chunks, 1):
            fund_name = chunk.get('fund_name', 'Unknown Fund')
            text = chunk.get('text', '')
            source_url = chunk.get('source_url', '')
            chunk_type = chunk.get('chunk_type', 'general')
            
            formatted.append(
                f"[{i}] Fund: {fund_name}\n"
                f"    Type: {chunk_type}\n"
                f"    Information: {text}\n"
                f"    Source: {source_url}"
            )
        
        return "\n\n".join(formatted)
    
    def build_user_message(
        self,
        query: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        Build user message with optional conversation history
        
        Args:
            query: Current user query
            conversation_history: Previous messages (optional)
            
        Returns:
            Formatted user message
        """
        if not conversation_history:
            return query
        
        # Include recent history for context
        history_text = []
        for msg in conversation_history[-3:]:  # Last 3 messages
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            history_text.append(f"{role.upper()}: {content}")
        
        history_str = "\n".join(history_text)
        
        return f"{history_str}\n\nUSER: {query}"
    
    def get_out_of_scope_response(self) -> str:
        """Get standardized out-of-scope response"""
        return self.templates.OUT_OF_SCOPE_RESPONSE
    
    def get_insufficient_context_response(self, topic: str = "this") -> str:
        """Get standardized insufficient context response"""
        return self.templates.INSUFFICIENT_CONTEXT.format(topic=topic)


if __name__ == "__main__":
    # Test prompt builder
    builder = PromptBuilder()
    
    # Sample context
    test_chunks = [
        {
            'fund_name': 'SBI ELSS Tax Saver Fund Direct Growth',
            'text': 'Expense ratio is 0.92%. Minimum SIP is ₹500.',
            'source_url': 'https://groww.in/mutual-funds/sbi-elss-tax-saver-fund',
            'chunk_type': 'financial'
        },
        {
            'fund_name': 'SBI ELSS Tax Saver Fund Direct Growth',
            'text': 'Risk level is Very High. Benchmark is Nifty 500.',
            'source_url': 'https://groww.in/mutual-funds/sbi-elss-tax-saver-fund',
            'chunk_type': 'risk'
        }
    ]
    
    system_prompt = builder.build_system_prompt(test_chunks)
    print("=" * 70)
    print("SYSTEM PROMPT:")
    print("=" * 70)
    print(system_prompt)
    print("\n" + "=" * 70)
    print("USER MESSAGE:")
    print("=" * 70)
    print(builder.build_user_message("What is the expense ratio?"))

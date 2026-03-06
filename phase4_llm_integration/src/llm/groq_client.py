"""
Groq LLM Client for Mutual Fund RAG Chatbot
Strict RAG-only policy enforcement
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from groq import Groq

# Add config to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "config"))
from settings import get_settings, get_groq_api_key, Settings


@dataclass
class LLMResponse:
    """Structured LLM response"""
    content: str
    model: str
    usage: Dict[str, int]
    citations: List[Dict[str, str]]
    rag_compliant: bool = True


class GroqClient:
    """
    Groq LLM client with strict RAG-only policy
    
    Enforces:
    - Responses based ONLY on provided context
    - No external knowledge usage
    - Source citations mandatory
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "llama-3.1-70b-versatile",
        temperature: float = 0.1,
        max_tokens: int = 1024
    ):
        """
        Initialize Groq client
        
        Args:
            api_key: Groq API key (or set GROQ_API_KEY env var)
            model: Model name (llama-3.1-70b-versatile or mixtral-8x7b-32768)
            temperature: Sampling temperature (low for factual)
            max_tokens: Maximum response tokens
        """
        # Get API key from parameter or centralized config
        settings = get_settings()
        self.api_key = api_key or settings.GROQ_API_KEY
        if not self.api_key:
            raise ValueError(
                "Groq API key required. Set GROQ_API_KEY in .env file or environment variable."
            )
        
        self.client = Groq(api_key=self.api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        print(f"✓ Groq client initialized (model: {model})")
        # API key is never logged - security best practice
    
    def generate(
        self,
        system_prompt: str,
        user_message: str,
        context: Optional[List[Dict]] = None
    ) -> LLMResponse:
        """
        Generate response with strict RAG enforcement
        
        Args:
            system_prompt: System instructions (must include RAG rules)
            user_message: User question
            context: Retrieved context chunks with sources
            
        Returns:
            LLMResponse with content and metadata
        """
        # Build messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        try:
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # Extract response
            content = response.choices[0].message.content
            
            # Check for RAG compliance indicators
            rag_compliant = self._check_rag_compliance(content, context)
            
            # Extract citations
            citations = self._extract_citations(content, context)
            
            return LLMResponse(
                content=content,
                model=self.model,
                usage={
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                },
                citations=citations,
                rag_compliant=rag_compliant
            )
            
        except Exception as e:
            raise RuntimeError(f"Groq API error: {e}")
    
    def _check_rag_compliance(
        self,
        content: str,
        context: Optional[List[Dict]]
    ) -> bool:
        """
        Check if response follows RAG-only policy
        
        Returns False if response appears to use external knowledge
        """
        # Check for refusal phrases (good)
        refusal_phrases = [
            "don't have enough information",
            "not in my knowledge base",
            "cannot answer",
            "don't have information about"
        ]
        
        has_refusal = any(phrase in content.lower() for phrase in refusal_phrases)
        
        # Check for citations (should have them if answering)
        has_citations = '[' in content and ']' in content
        
        # If no context and no refusal, might be hallucinating
        if not context and not has_refusal:
            return False
        
        # If has context but no citations, might be using external knowledge
        if context and not has_citations and not has_refusal:
            return False
        
        return True
    
    def _extract_citations(
        self,
        content: str,
        context: Optional[List[Dict]]
    ) -> List[Dict[str, str]]:
        """Extract citations from response content"""
        citations = []
        
        if not context:
            return citations
        
        # Find citation markers like [1], [2], etc.
        import re
        citation_markers = re.findall(r'\[(\d+)\]', content)
        
        for marker in citation_markers:
            idx = int(marker) - 1  # Convert to 0-based index
            if 0 <= idx < len(context):
                chunk = context[idx]
                citations.append({
                    'id': marker,
                    'fund_name': chunk.get('fund_name', 'Unknown'),
                    'source_url': chunk.get('source_url', ''),
                    'text': chunk.get('text', '')[:200] + '...'
                })
        
        return citations
    
    def generate_with_retry(
        self,
        system_prompt: str,
        user_message: str,
        context: Optional[List[Dict]] = None,
        max_retries: int = 3
    ) -> LLMResponse:
        """Generate with retry logic for reliability"""
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return self.generate(system_prompt, user_message, context)
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)  # Exponential backoff
        
        raise RuntimeError(f"Failed after {max_retries} attempts: {last_error}")


if __name__ == "__main__":
    # Test the client using centralized config
    try:
        api_key = get_groq_api_key()
    except ValueError as e:
        print(f"Configuration error: {e}")
        api_key = None
    
    if api_key:
        client = GroqClient()  # Uses config automatically
        
        # Test with sample context
        test_context = [
            {
                'fund_name': 'SBI ELSS Tax Saver Fund',
                'text': 'Expense ratio is 0.92%',
                'source_url': 'https://groww.in/mutual-funds/sbi-elss-tax-saver-fund'
            }
        ]
        
        system_prompt = """You are a helpful assistant. Use ONLY the provided context.
If information is missing, say "I don't have enough information."
Always cite sources with [1], [2], etc."""
        
        try:
            response = client.generate(
                system_prompt=system_prompt,
                user_message="What is the expense ratio?",
                context=test_context
            )
            
            print(f"\nResponse: {response.content}")
            print(f"RAG Compliant: {response.rag_compliant}")
            print(f"Citations: {response.citations}")
            
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Create a .env file with GROQ_API_KEY=your_api_key to test")

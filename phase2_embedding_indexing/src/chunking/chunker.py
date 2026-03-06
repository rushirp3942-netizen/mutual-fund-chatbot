"""
Text Chunking Module for Mutual Fund Data
Splits fund data into semantic chunks for embedding
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
import json


@dataclass
class ChunkConfig:
    """Configuration for chunking strategies"""
    chunk_size: int = 512
    chunk_overlap: int = 50
    separator: str = "\n"


@dataclass
class FundChunk:
    """Represents a single chunk of fund data"""
    chunk_id: str
    fund_name: str
    text: str
    chunk_type: str  # 'overview', 'financial', 'risk', 'documents'
    metadata: Dict
    source_url: str


class FundChunker:
    """
    Chunker for mutual fund data
    Creates semantic chunks optimized for RAG retrieval
    """
    
    def __init__(self, config: ChunkConfig = None):
        self.config = config or ChunkConfig()
    
    def chunk_fund(self, fund_data: Dict) -> List[FundChunk]:
        """
        Create multiple semantic chunks from a single fund record
        
        Args:
            fund_data: Dictionary containing fund information
            
        Returns:
            List of FundChunk objects
        """
        chunks = []
        fund_name = fund_data.get('fund_name', 'Unknown Fund')
        source_url = fund_data.get('source_url', '')
        
        # Chunk 1: Fund Overview
        overview_chunk = self._create_overview_chunk(fund_data)
        if overview_chunk:
            chunks.append(overview_chunk)
        
        # Chunk 2: Financial Attributes
        financial_chunk = self._create_financial_chunk(fund_data)
        if financial_chunk:
            chunks.append(financial_chunk)
        
        # Chunk 3: Risk Profile
        risk_chunk = self._create_risk_chunk(fund_data)
        if risk_chunk:
            chunks.append(risk_chunk)
        
        # Chunk 4: Documents & Procedures
        documents_chunk = self._create_documents_chunk(fund_data)
        if documents_chunk:
            chunks.append(documents_chunk)
        
        return chunks
    
    def _create_overview_chunk(self, fund_data: Dict) -> Optional[FundChunk]:
        """Create overview chunk with basic fund information"""
        fund_name = fund_data.get('fund_name', '')
        amc = fund_data.get('amc', '')
        category = fund_data.get('category', '')
        
        if not fund_name:
            return None
        
        text_parts = [f"{fund_name} is a mutual fund"]
        
        if amc:
            text_parts.append(f"managed by {amc}")
        
        if category:
            text_parts.append(f"in the {category} category")
        
        text = " ".join(text_parts) + "."
        
        metadata = {
            'amc': amc,
            'category': category,
            'chunk_type': 'overview'
        }
        
        return FundChunk(
            chunk_id=f"{self._sanitize_id(fund_name)}_overview",
            fund_name=fund_name,
            text=text,
            chunk_type='overview',
            metadata=metadata,
            source_url=fund_data.get('source_url', '')
        )
    
    def _create_financial_chunk(self, fund_data: Dict) -> Optional[FundChunk]:
        """Create chunk with financial attributes"""
        fund_name = fund_data.get('fund_name', '')
        
        text_parts = [f"Financial details for {fund_name}:"]
        
        if fund_data.get('expense_ratio'):
            text_parts.append(f"Expense ratio is {fund_data['expense_ratio']}.")
        
        if fund_data.get('exit_load'):
            text_parts.append(f"Exit load: {fund_data['exit_load']}.")
        
        if fund_data.get('minimum_sip'):
            text_parts.append(f"Minimum SIP amount is {fund_data['minimum_sip']}.")
        
        if fund_data.get('lock_in_period'):
            text_parts.append(f"Lock-in period: {fund_data['lock_in_period']}.")
        
        if len(text_parts) == 1:  # Only header, no actual data
            return None
        
        text = " ".join(text_parts)
        
        metadata = {
            'expense_ratio': fund_data.get('expense_ratio'),
            'exit_load': fund_data.get('exit_load'),
            'minimum_sip': fund_data.get('minimum_sip'),
            'lock_in_period': fund_data.get('lock_in_period'),
            'is_elss': 'ELSS' in fund_data.get('category', ''),
            'chunk_type': 'financial'
        }
        
        return FundChunk(
            chunk_id=f"{self._sanitize_id(fund_name)}_financial",
            fund_name=fund_name,
            text=text,
            chunk_type='financial',
            metadata=metadata,
            source_url=fund_data.get('source_url', '')
        )
    
    def _create_risk_chunk(self, fund_data: Dict) -> Optional[FundChunk]:
        """Create chunk with risk profile information"""
        fund_name = fund_data.get('fund_name', '')
        risk_level = fund_data.get('risk_level')
        benchmark = fund_data.get('benchmark')
        category = fund_data.get('category', '')
        
        if not risk_level and not benchmark:
            return None
        
        text_parts = [f"Risk profile for {fund_name}:"]
        
        if risk_level:
            text_parts.append(f"Risk level is {risk_level}.")
        
        if benchmark:
            text_parts.append(f"Benchmark index is {benchmark}.")
        
        if category:
            text_parts.append(f"Fund category: {category}.")
        
        text = " ".join(text_parts)
        
        metadata = {
            'risk_level': risk_level,
            'benchmark': benchmark,
            'category': category,
            'chunk_type': 'risk'
        }
        
        return FundChunk(
            chunk_id=f"{self._sanitize_id(fund_name)}_risk",
            fund_name=fund_name,
            text=text,
            chunk_type='risk',
            metadata=metadata,
            source_url=fund_data.get('source_url', '')
        )
    
    def _create_documents_chunk(self, fund_data: Dict) -> Optional[FundChunk]:
        """Create chunk with document and procedure information"""
        fund_name = fund_data.get('fund_name', '')
        statement_info = fund_data.get('statement_download_info', '')
        
        text = f"Documents and procedures for {fund_name}. {statement_info}"
        
        metadata = {
            'has_factsheet': bool(fund_data.get('factsheet_url')),
            'has_sid': bool(fund_data.get('sid_url')),
            'has_kim': bool(fund_data.get('kim_url')),
            'chunk_type': 'documents'
        }
        
        return FundChunk(
            chunk_id=f"{self._sanitize_id(fund_name)}_documents",
            fund_name=fund_name,
            text=text,
            chunk_type='documents',
            metadata=metadata,
            source_url=fund_data.get('source_url', '')
        )
    
    def _sanitize_id(self, text: str) -> str:
        """Create a safe ID from fund name"""
        return text.lower().replace(' ', '_').replace('-', '_')[:50]
    
    def chunk_multiple_funds(self, funds_data: List[Dict]) -> List[FundChunk]:
        """
        Create chunks for multiple funds
        
        Args:
            funds_data: List of fund data dictionaries
            
        Returns:
            List of all FundChunk objects
        """
        all_chunks = []
        
        for fund_data in funds_data:
            chunks = self.chunk_fund(fund_data)
            all_chunks.extend(chunks)
        
        return all_chunks
    
    def save_chunks(self, chunks: List[FundChunk], output_file: str):
        """Save chunks to JSON file"""
        chunks_data = []
        for chunk in chunks:
            chunks_data.append({
                'chunk_id': chunk.chunk_id,
                'fund_name': chunk.fund_name,
                'text': chunk.text,
                'chunk_type': chunk.chunk_type,
                'metadata': chunk.metadata,
                'source_url': chunk.source_url
            })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chunks_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Saved {len(chunks)} chunks to {output_file}")


if __name__ == "__main__":
    # Example usage
    chunker = FundChunker()
    
    # Sample fund data
    sample_fund = {
        "fund_name": "SBI ELSS Tax Saver Fund Direct Growth",
        "amc": "SBI Mutual Fund",
        "category": "ELSS",
        "expense_ratio": "0.92%",
        "exit_load": None,
        "minimum_sip": "₹500",
        "lock_in_period": "3 years lock-in period",
        "risk_level": "Very High",
        "benchmark": "Nifty Smallcap 250 Index",
        "statement_download_info": "Log in to Groww → Profile → Reports → Select Mutual Fund report → Choose date range → Download statement.",
        "source_url": "https://groww.in/mutual-funds/sbi-elss-tax-saver-fund-direct-growth"
    }
    
    chunks = chunker.chunk_fund(sample_fund)
    
    print(f"Created {len(chunks)} chunks for {sample_fund['fund_name']}:")
    for chunk in chunks:
        print(f"\n--- {chunk.chunk_type.upper()} ---")
        print(f"ID: {chunk.chunk_id}")
        print(f"Text: {chunk.text[:100]}...")
        print(f"Metadata: {chunk.metadata}")

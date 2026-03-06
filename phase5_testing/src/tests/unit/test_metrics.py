"""
Unit tests for evaluation metrics.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import unittest
from src.evaluation.metrics import (
    RetrievalMetrics,
    ResponseMetrics,
    SystemMetrics,
    RetrievalResult,
    ResponseResult
)


class TestRetrievalMetrics(unittest.TestCase):
    """Test retrieval evaluation metrics"""
    
    def setUp(self):
        self.metrics = RetrievalMetrics()
    
    def test_recall_at_k(self):
        """Test Recall@K calculation"""
        retrieved = ["doc1", "doc2", "doc3", "doc4", "doc5"]
        relevant = ["doc1", "doc3"]
        
        # Recall@5 should be 100% (both relevant docs in top 5)
        self.assertEqual(self.metrics.recall_at_k(retrieved, relevant, 5), 1.0)
        
        # Recall@1 should be 50% (only doc1 in top 1)
        self.assertEqual(self.metrics.recall_at_k(retrieved, relevant, 1), 0.5)
    
    def test_precision_at_k(self):
        """Test Precision@K calculation"""
        retrieved = ["doc1", "doc2", "doc3", "doc4", "doc5"]
        relevant = ["doc1", "doc3"]
        
        # Precision@5 should be 40% (2 relevant out of 5)
        self.assertEqual(self.metrics.precision_at_k(retrieved, relevant, 5), 0.4)
        
        # Precision@1 should be 100% (doc1 is relevant)
        self.assertEqual(self.metrics.precision_at_k(retrieved, relevant, 1), 1.0)
    
    def test_mean_reciprocal_rank(self):
        """Test MRR calculation"""
        # First relevant doc at position 1
        retrieved = ["doc1", "doc2", "doc3"]
        relevant = ["doc1"]
        self.assertEqual(self.metrics.mean_reciprocal_rank(retrieved, relevant), 1.0)
        
        # First relevant doc at position 3
        retrieved = ["doc2", "doc4", "doc1"]
        relevant = ["doc1"]
        self.assertEqual(self.metrics.mean_reciprocal_rank(retrieved, relevant), 1/3)
    
    def test_empty_inputs(self):
        """Test metrics with empty inputs"""
        self.assertEqual(self.metrics.recall_at_k([], ["doc1"], 5), 0.0)
        self.assertEqual(self.metrics.recall_at_k(["doc1"], [], 5), 0.0)


class TestResponseMetrics(unittest.TestCase):
    """Test response evaluation metrics"""
    
    def setUp(self):
        self.metrics = ResponseMetrics()
    
    def test_citation_accuracy(self):
        """Test citation accuracy calculation"""
        citations = [
            {'id': '1', 'source_url': 'https://groww.in/fund1'}
        ]
        context = [
            {'source_url': 'https://groww.in/fund1', 'text': 'Info'}
        ]
        
        accuracy = self.metrics.citation_accuracy("Response [1]", citations, context)
        self.assertEqual(accuracy, 1.0)
    
    def test_citation_accuracy_invalid(self):
        """Test citation accuracy with invalid citation"""
        citations = [
            {'id': '1', 'source_url': 'https://invalid.com'}
        ]
        context = [
            {'source_url': 'https://groww.in/fund1', 'text': 'Info'}
        ]
        
        accuracy = self.metrics.citation_accuracy("Response [1]", citations, context)
        self.assertEqual(accuracy, 0.0)
    
    def test_hallucination_detection(self):
        """Test hallucination detection"""
        context = [{'text': 'Expense ratio is 0.92%'}]
        
        # Should detect uncertainty
        has_hall, conf = self.metrics.has_hallucination("Probably 0.92%", context)
        self.assertTrue(has_hall)
        
        # Should not detect hallucination in factual statement
        has_hall, conf = self.metrics.has_hallucination("The expense ratio is 0.92%", context)
        self.assertFalse(has_hall)
    
    def test_rag_compliance(self):
        """Test RAG compliance scoring"""
        self.assertEqual(self.metrics.rag_compliance_score("Response", True), 1.0)
        self.assertEqual(self.metrics.rag_compliance_score("Response", False), 0.0)


class TestSystemMetrics(unittest.TestCase):
    """Test system performance metrics"""
    
    def setUp(self):
        self.metrics = SystemMetrics()
    
    def test_record_request(self):
        """Test recording request metrics"""
        self.metrics.record_request(100.0, success=True)
        self.metrics.record_request(200.0, success=False, error_type="timeout")
        
        stats = self.metrics.get_metrics()
        self.assertEqual(stats['total_requests'], 2)
        self.assertEqual(stats['error_rate'], 0.5)
    
    def test_latency_stats(self):
        """Test latency statistics"""
        for i in range(10):
            self.metrics.record_request(float(i * 10))
        
        stats = self.metrics.get_metrics()
        self.assertEqual(stats['total_requests'], 10)
        self.assertGreater(stats['avg_latency_ms'], 0)


if __name__ == "__main__":
    unittest.main()

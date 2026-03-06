"""
Evaluation Metrics for RAG System

Implements metrics for:
- Retrieval accuracy (Recall@K, Precision@K, MRR, NDCG)
- Response quality (Relevance, Citation accuracy, Hallucination detection)
- System performance (Latency, Throughput)
"""

import time
import statistics
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import json


@dataclass
class RetrievalResult:
    """Result of a retrieval operation"""
    query: str
    retrieved_ids: List[str]
    relevant_ids: List[str]  # Ground truth
    scores: List[float]
    latency_ms: float


@dataclass
class ResponseResult:
    """Result of a response generation"""
    query: str
    response: str
    context: List[Dict]
    citations: List[Dict]
    rag_compliant: bool
    latency_ms: float
    relevance_score: Optional[float] = None


class RetrievalMetrics:
    """
    Metrics for evaluating retrieval performance.
    
    Targets (from architecture):
    - Recall@5: > 90%
    - Precision@5: > 85%
    """
    
    @staticmethod
    def recall_at_k(retrieved_ids: List[str], relevant_ids: List[str], k: int = 5) -> float:
        """
        Calculate Recall@K
        
        Recall@K = (# of relevant docs in top K) / (total # of relevant docs)
        """
        if not relevant_ids:
            return 0.0
        
        retrieved_k = set(retrieved_ids[:k])
        relevant = set(relevant_ids)
        
        return len(retrieved_k & relevant) / len(relevant)
    
    @staticmethod
    def precision_at_k(retrieved_ids: List[str], relevant_ids: List[str], k: int = 5) -> float:
        """
        Calculate Precision@K
        
        Precision@K = (# of relevant docs in top K) / K
        """
        if k == 0:
            return 0.0
        
        retrieved_k = set(retrieved_ids[:k])
        relevant = set(relevant_ids)
        
        return len(retrieved_k & relevant) / k
    
    @staticmethod
    def mean_reciprocal_rank(retrieved_ids: List[str], relevant_ids: List[str]) -> float:
        """
        Calculate Mean Reciprocal Rank (MRR)
        
        MRR = 1 / rank of first relevant document
        """
        if not relevant_ids:
            return 0.0
        
        relevant_set = set(relevant_ids)
        
        for rank, doc_id in enumerate(retrieved_ids, 1):
            if doc_id in relevant_set:
                return 1.0 / rank
        
        return 0.0
    
    @staticmethod
    def ndcg_at_k(retrieved_ids: List[str], relevant_ids: List[str], k: int = 5) -> float:
        """
        Calculate Normalized Discounted Cumulative Gain (NDCG@K)
        
        Measures ranking quality considering position of relevant docs.
        """
        if not relevant_ids or not retrieved_ids:
            return 0.0
        
        relevant_set = set(relevant_ids)
        
        # Calculate DCG
        dcg = 0.0
        for i, doc_id in enumerate(retrieved_ids[:k], 1):
            if doc_id in relevant_set:
                # Relevance score is binary (1 if relevant)
                dcg += 1.0 / (1 + i)
        
        # Calculate ideal DCG (all relevant docs at top)
        ideal_relevances = [1.0] * min(len(relevant_ids), k)
        idcg = sum(rel / (1 + i) for i, rel in enumerate(ideal_relevances, 1))
        
        return dcg / idcg if idcg > 0 else 0.0
    
    @staticmethod
    def average_precision(retrieved_ids: List[str], relevant_ids: List[str]) -> float:
        """Calculate Average Precision (AP)"""
        if not relevant_ids:
            return 0.0
        
        relevant_set = set(relevant_ids)
        precisions = []
        
        for k, doc_id in enumerate(retrieved_ids, 1):
            if doc_id in relevant_set:
                precisions.append(RetrievalMetrics.precision_at_k(retrieved_ids, relevant_ids, k))
        
        return sum(precisions) / len(relevant_ids) if relevant_ids else 0.0
    
    def evaluate_batch(self, results: List[RetrievalResult]) -> Dict[str, float]:
        """
        Evaluate a batch of retrieval results.
        
        Returns:
            Dictionary with aggregated metrics
        """
        metrics = {
            'recall@1': [],
            'recall@3': [],
            'recall@5': [],
            'precision@1': [],
            'precision@3': [],
            'precision@5': [],
            'mrr': [],
            'ndcg@5': [],
            'map': [],  # Mean Average Precision
            'latency_ms': []
        }
        
        for result in results:
            metrics['recall@1'].append(self.recall_at_k(result.retrieved_ids, result.relevant_ids, 1))
            metrics['recall@3'].append(self.recall_at_k(result.retrieved_ids, result.relevant_ids, 3))
            metrics['recall@5'].append(self.recall_at_k(result.retrieved_ids, result.relevant_ids, 5))
            metrics['precision@1'].append(self.precision_at_k(result.retrieved_ids, result.relevant_ids, 1))
            metrics['precision@3'].append(self.precision_at_k(result.retrieved_ids, result.relevant_ids, 3))
            metrics['precision@5'].append(self.precision_at_k(result.retrieved_ids, result.relevant_ids, 5))
            metrics['mrr'].append(self.mean_reciprocal_rank(result.retrieved_ids, result.relevant_ids))
            metrics['ndcg@5'].append(self.ndcg_at_k(result.retrieved_ids, result.relevant_ids, 5))
            metrics['map'].append(self.average_precision(result.retrieved_ids, result.relevant_ids))
            metrics['latency_ms'].append(result.latency_ms)
        
        # Calculate averages
        return {
            'recall@1': statistics.mean(metrics['recall@1']),
            'recall@3': statistics.mean(metrics['recall@3']),
            'recall@5': statistics.mean(metrics['recall@5']),
            'precision@1': statistics.mean(metrics['precision@1']),
            'precision@3': statistics.mean(metrics['precision@3']),
            'precision@5': statistics.mean(metrics['precision@5']),
            'mrr': statistics.mean(metrics['mrr']),
            'ndcg@5': statistics.mean(metrics['ndcg@5']),
            'map': statistics.mean(metrics['map']),
            'avg_latency_ms': statistics.mean(metrics['latency_ms']),
            'p95_latency_ms': statistics.quantiles(metrics['latency_ms'], n=20)[18] if len(metrics['latency_ms']) >= 20 else max(metrics['latency_ms']),
            'num_queries': len(results)
        }


class ResponseMetrics:
    """
    Metrics for evaluating LLM response quality.
    
    Targets (from architecture):
    - Answer Relevance: > 4.0/5
    - Citation Accuracy: > 95%
    - Hallucination Rate: < 2%
    """
    
    @staticmethod
    def citation_accuracy(response: str, citations: List[Dict], context: List[Dict]) -> float:
        """
        Calculate citation accuracy.
        
        Checks if citations in response match the provided context.
        """
        if not citations:
            # No citations provided - check if response claims to have info
            return 0.0 if '[' in response and ']' in response else 1.0
        
        accurate_count = 0
        for citation in citations:
            # Check if citation references valid context
            citation_id = citation.get('id')
            source_url = citation.get('source_url', '')
            
            # Validate against context
            valid = False
            for ctx in context:
                if ctx.get('source_url') == source_url:
                    valid = True
                    break
            
            if valid:
                accurate_count += 1
        
        return accurate_count / len(citations)
    
    @staticmethod
    def has_hallucination(response: str, context: List[Dict]) -> Tuple[bool, float]:
        """
        Detect potential hallucinations in response.
        
        Returns:
            (has_hallucination, confidence_score)
        """
        # Simple heuristic-based detection
        hallucination_indicators = [
            "i think",
            "probably",
            "maybe",
            "i believe",
            "it seems",
            "appears to be"
        ]
        
        # Check for uncertainty phrases (potential hallucination)
        response_lower = response.lower()
        uncertainty_count = sum(1 for indicator in hallucination_indicators if indicator in response_lower)
        
        # Check for specific numbers/facts not in context
        # This is a simplified check - in production, use more sophisticated methods
        has_uncertainty = uncertainty_count > 0
        
        # Confidence score (lower is more confident)
        confidence = 1.0 - (uncertainty_count * 0.2)
        
        return has_uncertainty, max(0.0, confidence)
    
    @staticmethod
    def rag_compliance_score(response: str, rag_compliant: bool) -> float:
        """
        Score RAG compliance of response.
        
        Returns 1.0 if compliant, 0.0 if not.
        """
        return 1.0 if rag_compliant else 0.0
    
    @staticmethod
    def response_length_score(response: str, optimal_range: Tuple[int, int] = (50, 500)) -> float:
        """
        Score response length appropriateness.
        
        Optimal range: 50-500 characters for concise answers.
        """
        length = len(response)
        min_len, max_len = optimal_range
        
        if min_len <= length <= max_len:
            return 1.0
        elif length < min_len:
            return length / min_len
        else:
            return max(0.0, 1.0 - (length - max_len) / max_len)
    
    def evaluate_batch(self, results: List[ResponseResult]) -> Dict[str, float]:
        """
        Evaluate a batch of response results.
        
        Returns:
            Dictionary with aggregated metrics
        """
        metrics = {
            'citation_accuracy': [],
            'hallucination_rate': [],
            'rag_compliance': [],
            'response_length': [],
            'latency_ms': []
        }
        
        for result in results:
            # Citation accuracy
            metrics['citation_accuracy'].append(
                self.citation_accuracy(result.response, result.citations, result.context)
            )
            
            # Hallucination detection
            has_hall, _ = self.has_hallucination(result.response, result.context)
            metrics['hallucination_rate'].append(1.0 if has_hall else 0.0)
            
            # RAG compliance
            metrics['rag_compliance'].append(
                self.rag_compliance_score(result.response, result.rag_compliant)
            )
            
            # Response length
            metrics['response_length'].append(
                self.response_length_score(result.response)
            )
            
            # Latency
            metrics['latency_ms'].append(result.latency_ms)
        
        return {
            'citation_accuracy': statistics.mean(metrics['citation_accuracy']),
            'hallucination_rate': statistics.mean(metrics['hallucination_rate']),
            'rag_compliance': statistics.mean(metrics['rag_compliance']),
            'response_length_score': statistics.mean(metrics['response_length']),
            'avg_latency_ms': statistics.mean(metrics['latency_ms']),
            'p95_latency_ms': statistics.quantiles(metrics['latency_ms'], n=20)[18] if len(metrics['latency_ms']) >= 20 else max(metrics['latency_ms']),
            'num_responses': len(results)
        }


class SystemMetrics:
    """
    System-level performance metrics.
    """
    
    def __init__(self):
        self.request_times: List[float] = []
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.total_requests: int = 0
    
    def record_request(self, latency_ms: float, success: bool = True, error_type: Optional[str] = None):
        """Record a request metric"""
        self.total_requests += 1
        self.request_times.append(latency_ms)
        
        if not success and error_type:
            self.error_counts[error_type] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get aggregated system metrics"""
        if not self.request_times:
            return {
                'total_requests': 0,
                'avg_latency_ms': 0.0,
                'p95_latency_ms': 0.0,
                'p99_latency_ms': 0.0,
                'error_rate': 0.0,
                'errors': {}
            }
        
        sorted_times = sorted(self.request_times)
        n = len(sorted_times)
        
        return {
            'total_requests': self.total_requests,
            'avg_latency_ms': statistics.mean(self.request_times),
            'p95_latency_ms': sorted_times[int(n * 0.95)] if n >= 20 else sorted_times[-1],
            'p99_latency_ms': sorted_times[int(n * 0.99)] if n >= 100 else sorted_times[-1],
            'min_latency_ms': min(self.request_times),
            'max_latency_ms': max(self.request_times),
            'error_rate': sum(self.error_counts.values()) / self.total_requests if self.total_requests > 0 else 0.0,
            'errors': dict(self.error_counts)
        }
    
    def reset(self):
        """Reset all metrics"""
        self.request_times.clear()
        self.error_counts.clear()
        self.total_requests = 0


if __name__ == "__main__":
    # Test metrics
    print("Testing Retrieval Metrics")
    print("=" * 50)
    
    retrieval = RetrievalMetrics()
    
    # Test case
    result = RetrievalResult(
        query="expense ratio of SBI ELSS",
        retrieved_ids=["doc1", "doc2", "doc3", "doc4", "doc5"],
        relevant_ids=["doc1", "doc3"],
        scores=[0.95, 0.87, 0.82, 0.75, 0.70],
        latency_ms=150.0
    )
    
    print(f"Recall@5: {retrieval.recall_at_k(result.retrieved_ids, result.relevant_ids, 5):.2%}")
    print(f"Precision@5: {retrieval.precision_at_k(result.retrieved_ids, result.relevant_ids, 5):.2%}")
    print(f"MRR: {retrieval.mean_reciprocal_rank(result.retrieved_ids, result.relevant_ids):.2%}")
    print(f"NDCG@5: {retrieval.ndcg_at_k(result.retrieved_ids, result.relevant_ids, 5):.2%}")
    
    print("\nTesting Response Metrics")
    print("=" * 50)
    
    response = ResponseMetrics()
    
    citations = [
        {'id': '1', 'source_url': 'https://groww.in/mutual-funds/sbi-elss-tax-saver-fund'}
    ]
    context = [
        {'source_url': 'https://groww.in/mutual-funds/sbi-elss-tax-saver-fund', 'text': 'Expense ratio is 0.92%'}
    ]
    
    print(f"Citation Accuracy: {response.citation_accuracy('Response [1]', citations, context):.2%}")
    
    has_hall, conf = response.has_hallucination("The expense ratio is probably around 0.9%", context)
    print(f"Hallucination detected: {has_hall}, confidence: {conf:.2f}")

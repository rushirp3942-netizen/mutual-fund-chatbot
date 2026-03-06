"""
Feedback Collection Module

Collects and manages user feedback for continuous improvement.
Supports explicit feedback (ratings) and implicit feedback (metrics).
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from collections import defaultdict
import statistics


@dataclass
class UserFeedback:
    """Individual user feedback entry"""
    feedback_id: str
    query: str
    response: str
    rating: Optional[int] = None  # 1-5 scale
    helpful: Optional[bool] = None
    comments: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResponseMetrics:
    """Implicit feedback metrics from response"""
    query_id: str
    query: str
    retrieval_time_ms: float
    generation_time_ms: float
    total_time_ms: float
    num_chunks_retrieved: int
    response_length: int
    citations_count: int
    rag_compliant: bool
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class FeedbackCollector:
    """
    Collects and manages user feedback for the RAG system.
    
    Features:
    - Explicit feedback (ratings, comments)
    - Implicit feedback (response metrics, timing)
    - Feedback aggregation and reporting
    - Export for analysis
    """
    
    def __init__(self, storage_dir: str = "phase5_testing/data/feedback"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.feedback_file = self.storage_dir / "user_feedback.jsonl"
        self.metrics_file = self.storage_dir / "response_metrics.jsonl"
        
        # In-memory cache
        self.feedback_cache: List[UserFeedback] = []
        self.metrics_cache: List[ResponseMetrics] = []
    
    def record_feedback(
        self,
        query: str,
        response: str,
        rating: Optional[int] = None,
        helpful: Optional[bool] = None,
        comments: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Record explicit user feedback.
        
        Args:
            query: User's query
            response: System's response
            rating: Rating from 1-5 (optional)
            helpful: Whether response was helpful (optional)
            comments: Free-form comments (optional)
            session_id: Session identifier (optional)
            user_id: User identifier (optional)
            metadata: Additional metadata (optional)
            
        Returns:
            feedback_id: Unique identifier for this feedback
        """
        feedback_id = f"fb_{int(time.time() * 1000)}"
        
        feedback = UserFeedback(
            feedback_id=feedback_id,
            query=query,
            response=response,
            rating=rating,
            helpful=helpful,
            comments=comments,
            session_id=session_id,
            user_id=user_id,
            metadata=metadata or {}
        )
        
        # Add to cache
        self.feedback_cache.append(feedback)
        
        # Append to file
        with open(self.feedback_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(asdict(feedback), ensure_ascii=False) + '\n')
        
        return feedback_id
    
    def record_metrics(
        self,
        query_id: str,
        query: str,
        retrieval_time_ms: float,
        generation_time_ms: float,
        num_chunks_retrieved: int,
        response_length: int,
        citations_count: int,
        rag_compliant: bool
    ) -> None:
        """
        Record implicit feedback metrics.
        
        Args:
            query_id: Unique query identifier
            query: User's query
            retrieval_time_ms: Time taken for retrieval
            generation_time_ms: Time taken for LLM generation
            num_chunks_retrieved: Number of chunks retrieved
            response_length: Length of generated response
            citations_count: Number of citations in response
            rag_compliant: Whether response is RAG compliant
        """
        metrics = ResponseMetrics(
            query_id=query_id,
            query=query,
            retrieval_time_ms=retrieval_time_ms,
            generation_time_ms=generation_time_ms,
            total_time_ms=retrieval_time_ms + generation_time_ms,
            num_chunks_retrieved=num_chunks_retrieved,
            response_length=response_length,
            citations_count=citations_count,
            rag_compliant=rag_compliant
        )
        
        # Add to cache
        self.metrics_cache.append(metrics)
        
        # Append to file
        with open(self.metrics_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(asdict(metrics), ensure_ascii=False) + '\n')
    
    def load_feedback(self) -> List[UserFeedback]:
        """Load all feedback from storage"""
        feedback_list = []
        
        if self.feedback_file.exists():
            with open(self.feedback_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        feedback_list.append(UserFeedback(**data))
        
        return feedback_list
    
    def load_metrics(self) -> List[ResponseMetrics]:
        """Load all metrics from storage"""
        metrics_list = []
        
        if self.metrics_file.exists():
            with open(self.metrics_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        metrics_list.append(ResponseMetrics(**data))
        
        return metrics_list
    
    def get_feedback_stats(self) -> Dict[str, Any]:
        """Get statistics about collected feedback"""
        feedback_list = self.load_feedback()
        
        if not feedback_list:
            return {
                'total_feedback': 0,
                'avg_rating': 0.0,
                'helpful_rate': 0.0
            }
        
        # Calculate statistics
        ratings = [f.rating for f in feedback_list if f.rating is not None]
        helpfuls = [f.helpful for f in feedback_list if f.helpful is not None]
        
        return {
            'total_feedback': len(feedback_list),
            'avg_rating': statistics.mean(ratings) if ratings else 0.0,
            'rating_distribution': {
                str(i): sum(1 for r in ratings if r == i) for i in range(1, 6)
            } if ratings else {},
            'helpful_rate': sum(helpfuls) / len(helpfuls) if helpfuls else 0.0,
            'with_comments': sum(1 for f in feedback_list if f.comments)
        }
    
    def get_metrics_stats(self) -> Dict[str, Any]:
        """Get statistics about collected metrics"""
        metrics_list = self.load_metrics()
        
        if not metrics_list:
            return {
                'total_responses': 0,
                'avg_total_time_ms': 0.0
            }
        
        # Calculate statistics
        total_times = [m.total_time_ms for m in metrics_list]
        retrieval_times = [m.retrieval_time_ms for m in metrics_list]
        generation_times = [m.generation_time_ms for m in metrics_list]
        response_lengths = [m.response_length for m in metrics_list]
        citations = [m.citations_count for m in metrics_list]
        
        rag_compliant_count = sum(1 for m in metrics_list if m.rag_compliant)
        
        return {
            'total_responses': len(metrics_list),
            'avg_total_time_ms': statistics.mean(total_times),
            'p95_total_time_ms': statistics.quantiles(total_times, n=20)[18] if len(total_times) >= 20 else max(total_times),
            'avg_retrieval_time_ms': statistics.mean(retrieval_times),
            'avg_generation_time_ms': statistics.mean(generation_times),
            'avg_response_length': statistics.mean(response_lengths),
            'avg_citations': statistics.mean(citations),
            'rag_compliance_rate': rag_compliant_count / len(metrics_list)
        }
    
    def generate_report(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate comprehensive feedback report.
        
        Returns:
            Dictionary with feedback and metrics statistics
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'feedback_stats': self.get_feedback_stats(),
            'metrics_stats': self.get_metrics_stats()
        }
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
        
        return report
    
    def print_summary(self):
        """Print feedback collection summary"""
        print("=" * 80)
        print("FEEDBACK COLLECTION SUMMARY")
        print("=" * 80)
        
        feedback_stats = self.get_feedback_stats()
        print("\nUser Feedback:")
        print(f"  Total feedback entries: {feedback_stats['total_feedback']}")
        if feedback_stats['total_feedback'] > 0:
            print(f"  Average rating: {feedback_stats['avg_rating']:.2f}/5")
            print(f"  Helpful rate: {feedback_stats['helpful_rate']:.1%}")
            print(f"  With comments: {feedback_stats['with_comments']}")
        
        metrics_stats = self.get_metrics_stats()
        print("\nResponse Metrics:")
        print(f"  Total responses: {metrics_stats['total_responses']}")
        if metrics_stats['total_responses'] > 0:
            print(f"  Avg total time: {metrics_stats['avg_total_time_ms']:.1f}ms")
            print(f"  P95 total time: {metrics_stats['p95_total_time_ms']:.1f}ms")
            print(f"  RAG compliance: {metrics_stats['rag_compliance_rate']:.1%}")
        
        print("\n" + "=" * 80)


if __name__ == "__main__":
    # Example usage
    collector = FeedbackCollector()
    
    # Record some sample feedback
    collector.record_feedback(
        query="What is the expense ratio of SBI ELSS?",
        response="The expense ratio is 0.92% [1].",
        rating=5,
        helpful=True,
        comments="Very helpful!"
    )
    
    collector.record_metrics(
        query_id="q_123",
        query="What is the expense ratio of SBI ELSS?",
        retrieval_time_ms=45.2,
        generation_time_ms=850.5,
        num_chunks_retrieved=3,
        response_length=45,
        citations_count=1,
        rag_compliant=True
    )
    
    # Print summary
    collector.print_summary()
    
    # Generate report
    report = collector.generate_report("phase5_testing/reports/feedback_report.json")
    print("\nReport saved to: phase5_testing/reports/feedback_report.json")

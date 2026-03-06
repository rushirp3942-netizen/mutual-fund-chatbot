"""
Benchmark Runner for RAG System Evaluation

Runs test suites and generates evaluation reports with metrics.
"""

import json
import time
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
import statistics

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from .metrics import (
    RetrievalMetrics, 
    ResponseMetrics, 
    SystemMetrics,
    RetrievalResult,
    ResponseResult
)
from .test_cases import TestSuite, TestCase, TestCategory, TestPriority


@dataclass
class BenchmarkResult:
    """Result of a benchmark run"""
    test_id: str
    test_category: str
    passed: bool
    actual_output: str
    expected_output: str
    execution_time_ms: float
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkReport:
    """Complete benchmark report"""
    timestamp: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    overall_score: float
    retrieval_metrics: Dict[str, float] = field(default_factory=dict)
    response_metrics: Dict[str, float] = field(default_factory=dict)
    system_metrics: Dict[str, Any] = field(default_factory=dict)
    results: List[BenchmarkResult] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary"""
        return {
            'timestamp': self.timestamp,
            'total_tests': self.total_tests,
            'passed_tests': self.passed_tests,
            'failed_tests': self.failed_tests,
            'overall_score': self.overall_score,
            'retrieval_metrics': self.retrieval_metrics,
            'response_metrics': self.response_metrics,
            'system_metrics': self.system_metrics,
            'results': [asdict(r) for r in self.results]
        }
    
    def save(self, filepath: str):
        """Save report to JSON file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)


class BenchmarkRunner:
    """
    Runs benchmarks against the RAG system.
    
    Supports:
    - Unit test execution
    - Integration test execution
    - End-to-end test execution
    - Metric collection and reporting
    """
    
    def __init__(self, output_dir: str = "phase5_testing/reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.test_suite = TestSuite()
        self.retrieval_metrics = RetrievalMetrics()
        self.response_metrics = ResponseMetrics()
        self.system_metrics = SystemMetrics()
        
        self.results: List[BenchmarkResult] = []
    
    def run_test(
        self,
        test_case: TestCase,
        test_function: Optional[Callable] = None
    ) -> BenchmarkResult:
        """
        Run a single test case.
        
        Args:
            test_case: The test case to run
            test_function: Optional custom test function
            
        Returns:
            BenchmarkResult with test outcome
        """
        start_time = time.time()
        
        try:
            if test_function:
                # Run custom test function
                passed, actual_output, metadata = test_function(test_case)
            else:
                # Default test execution (placeholder)
                passed, actual_output, metadata = self._default_test_execution(test_case)
            
            execution_time = (time.time() - start_time) * 1000
            
            return BenchmarkResult(
                test_id=test_case.id,
                test_category=test_case.category.value,
                passed=passed,
                actual_output=actual_output,
                expected_output=test_case.expected_output,
                execution_time_ms=execution_time,
                metadata=metadata
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return BenchmarkResult(
                test_id=test_case.id,
                test_category=test_case.category.value,
                passed=False,
                actual_output="",
                expected_output=test_case.expected_output,
                execution_time_ms=execution_time,
                error_message=str(e),
                metadata={'error': str(e)}
            )
    
    def _default_test_execution(
        self,
        test_case: TestCase
    ) -> tuple[bool, str, Dict[str, Any]]:
        """
        Default test execution logic.
        
        This is a placeholder - in production, this would integrate
        with the actual RAG system components.
        """
        # Placeholder implementation
        # In real implementation, this would:
        # 1. Send query to the system
        # 2. Get response
        # 3. Compare with expected output
        # 4. Return result
        
        return True, "Placeholder response", {'status': 'placeholder'}
    
    def run_category(
        self,
        category: TestCategory,
        test_function: Optional[Callable] = None
    ) -> List[BenchmarkResult]:
        """Run all tests in a category"""
        tests = self.test_suite.get_tests_by_category(category)
        print(f"\nRunning {len(tests)} tests in category: {category.value}")
        print("-" * 60)
        
        results = []
        for test in tests:
            result = self.run_test(test, test_function)
            results.append(result)
            status = "✓ PASS" if result.passed else "✗ FAIL"
            print(f"{status} | {test.id}: {test.scenario[:50]}...")
        
        return results
    
    def run_priority(
        self,
        priority: TestPriority,
        test_function: Optional[Callable] = None
    ) -> List[BenchmarkResult]:
        """Run all tests with a specific priority"""
        tests = self.test_suite.get_tests_by_priority(priority)
        print(f"\nRunning {len(tests)} tests with priority: {priority.value}")
        print("-" * 60)
        
        results = []
        for test in tests:
            result = self.run_test(test, test_function)
            results.append(result)
            status = "✓ PASS" if result.passed else "✗ FAIL"
            print(f"{status} | {test.id}: {test.scenario[:50]}...")
        
        return results
    
    def run_all(
        self,
        test_function: Optional[Callable] = None
    ) -> BenchmarkReport:
        """Run all tests and generate report"""
        print("=" * 80)
        print("BENCHMARK RUNNER - Starting Test Execution")
        print("=" * 80)
        
        self.results = []
        
        # Run tests by category
        for category in TestCategory:
            results = self.run_category(category, test_function)
            self.results.extend(results)
        
        # Generate report
        report = self._generate_report()
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"benchmark_report_{timestamp}.json"
        report.save(str(report_file))
        
        # Print summary
        self._print_summary(report)
        
        return report
    
    def _generate_report(self) -> BenchmarkReport:
        """Generate benchmark report from results"""
        passed = sum(1 for r in self.results if r.passed)
        failed = len(self.results) - passed
        
        # Calculate overall score
        overall_score = (passed / len(self.results) * 100) if self.results else 0.0
        
        # Calculate execution time stats
        execution_times = [r.execution_time_ms for r in self.results]
        
        return BenchmarkReport(
            timestamp=datetime.now().isoformat(),
            total_tests=len(self.results),
            passed_tests=passed,
            failed_tests=failed,
            overall_score=overall_score,
            retrieval_metrics=self.system_metrics.get_metrics(),
            response_metrics={
                'avg_execution_time_ms': statistics.mean(execution_times) if execution_times else 0.0,
                'p95_execution_time_ms': statistics.quantiles(execution_times, n=20)[18] if len(execution_times) >= 20 else max(execution_times) if execution_times else 0.0
            },
            system_metrics=self.system_metrics.get_metrics(),
            results=self.results
        )
    
    def _print_summary(self, report: BenchmarkReport):
        """Print benchmark summary"""
        print("\n" + "=" * 80)
        print("BENCHMARK SUMMARY")
        print("=" * 80)
        print(f"\nTimestamp: {report.timestamp}")
        print(f"Total Tests: {report.total_tests}")
        print(f"Passed: {report.passed_tests} ({report.passed_tests/report.total_tests*100:.1f}%)")
        print(f"Failed: {report.failed_tests} ({report.failed_tests/report.total_tests*100:.1f}%)")
        print(f"Overall Score: {report.overall_score:.1f}%")
        
        print("\nBy Category:")
        for category in TestCategory:
            cat_results = [r for r in self.results if r.test_category == category.value]
            cat_passed = sum(1 for r in cat_results if r.passed)
            print(f"  {category.value}: {cat_passed}/{len(cat_results)} passed")
        
        print("\nFailed Tests:")
        failed_tests = [r for r in self.results if not r.passed]
        if failed_tests:
            for r in failed_tests:
                print(f"  - {r.test_id}: {r.error_message or 'Output mismatch'}")
        else:
            print("  None")
        
        print("\n" + "=" * 80)


if __name__ == "__main__":
    # Example usage
    runner = BenchmarkRunner()
    
    # Print test suite summary
    runner.test_suite.print_summary()
    
    # Run all tests (with placeholder execution)
    print("\n\nRunning benchmark with placeholder execution...")
    print("(In production, this would execute against the actual RAG system)")
    report = runner.run_all()

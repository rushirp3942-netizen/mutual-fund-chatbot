"""
Phase 5 Test Runner

Runs all tests and generates evaluation reports.
Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --unit             # Run unit tests only
    python run_tests.py --integration      # Run integration tests only
    python run_tests.py --e2e              # Run e2e tests only
    python run_tests.py --benchmark        # Run benchmark suite
"""

import sys
import argparse
import unittest
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.evaluation.test_cases import TestSuite
from src.evaluation.benchmark import BenchmarkRunner


def run_unit_tests():
    """Run unit tests"""
    print("=" * 80)
    print("RUNNING UNIT TESTS")
    print("=" * 80)
    
    loader = unittest.TestLoader()
    start_dir = "src/tests/unit"
    suite = loader.discover(start_dir, pattern="test_*.py")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def run_integration_tests():
    """Run integration tests"""
    print("=" * 80)
    print("RUNNING INTEGRATION TESTS")
    print("=" * 80)
    
    loader = unittest.TestLoader()
    start_dir = "src/tests/integration"
    suite = loader.discover(start_dir, pattern="test_*.py")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def run_e2e_tests():
    """Run end-to-end tests"""
    print("=" * 80)
    print("RUNNING END-TO-END TESTS")
    print("=" * 80)
    
    loader = unittest.TestLoader()
    start_dir = "src/tests/e2e"
    suite = loader.discover(start_dir, pattern="test_*.py")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def run_benchmark():
    """Run benchmark suite"""
    print("=" * 80)
    print("RUNNING BENCHMARK SUITE")
    print("=" * 80)
    
    runner = BenchmarkRunner()
    report = runner.run_all()
    
    return report.overall_score >= 80.0  # Pass if 80%+ score


def export_test_cases():
    """Export test cases to JSON"""
    suite = TestSuite()
    output_file = "data/test_data/test_cases.json"
    suite.export_to_json(output_file)
    print(f"Test cases exported to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Phase 5 Test Runner")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--e2e", action="store_true", help="Run e2e tests only")
    parser.add_argument("--benchmark", action="store_true", help="Run benchmark suite")
    parser.add_argument("--export", action="store_true", help="Export test cases to JSON")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    
    args = parser.parse_args()
    
    # If no args specified, show help
    if not any([args.unit, args.integration, args.e2e, args.benchmark, args.export, args.all]):
        parser.print_help()
        return
    
    results = []
    
    if args.export:
        export_test_cases()
        return
    
    if args.unit or args.all:
        results.append(("Unit Tests", run_unit_tests()))
    
    if args.integration or args.all:
        results.append(("Integration Tests", run_integration_tests()))
    
    if args.e2e or args.all:
        results.append(("E2E Tests", run_e2e_tests()))
    
    if args.benchmark or args.all:
        results.append(("Benchmark", run_benchmark()))
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(passed for _, passed in results)
    
    print("\n" + "=" * 80)
    if all_passed:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED")
    print("=" * 80)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

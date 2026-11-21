#!/usr/bin/env python
"""Run full RAG evaluation with all 100 questions."""
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(message)s')

sys.path.insert(0, str(Path(__file__).parent))

from tests.evaluation.rag_evaluator import RAGEvaluator
from tests.evaluation.run_evaluation import generate_evaluation_reports

def main():
    evaluator = RAGEvaluator()
    print(f"Loaded {len(evaluator.dataset.get('questions', []))} questions")
    
    # Run evaluation on all questions
    results = evaluator.evaluate_all(max_questions=100)
    
    print("\nEvaluation Complete!")
    summary = results.get('summary', {})
    print(f"Total: {summary.get('total_questions', 0)} | Passed: {summary.get('passed', 0)} | Failed: {summary.get('failed', 0)}")
    
    # Generate reports
    generate_evaluation_reports(results)
    
    print("\nReports generated successfully!")
    print("Files created:")
    print("  - RAG_EVALUATION_RESULTS.md")
    print("  - RAG_FAILED_EXAMPLES.md")
    print("  - RAG_RECOMMENDATIONS.md")
    print("  - evaluation_results.json")

if __name__ == "__main__":
    main()

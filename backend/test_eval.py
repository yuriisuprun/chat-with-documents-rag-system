#!/usr/bin/env python
"""Quick test of evaluation."""
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(message)s')

sys.path.insert(0, str(Path(__file__).parent))

from tests.evaluation.rag_evaluator import RAGEvaluator

def main():
    evaluator = RAGEvaluator()
    print(f"Loaded {len(evaluator.dataset.get('questions', []))} questions")
    
    results = evaluator.evaluate_all(max_questions=10)
    
    print("\nEvaluation Results:")
    print(f"Summary: {results.get('summary', {})}")
    print(f"Categories: {list(results.get('category_breakdown', {}).keys())}")
    
    # Export
    evaluator.export_results("tests/evaluation/evaluation_results.json")
    
    # Generate reports
    from tests.evaluation.run_evaluation import generate_evaluation_reports
    generate_evaluation_reports(results)
    
    print("\nReports generated successfully!")

if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""Debug evaluation."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from tests.evaluation.rag_evaluator import RAGEvaluator

evaluator = RAGEvaluator()
print(f"Loaded {len(evaluator.dataset.get('questions', []))} questions")

# Test one question
questions = evaluator.dataset.get('questions', [])[:1]
print(f"\nEvaluating first question: {questions[0]['id']}")

result = evaluator._evaluate_question(questions[0])
print(f"Result: {result}")
print(f"Result is None: {result is None}")
print(f"Result.overall_score: {result.overall_score if result else 'N/A'}")

evaluator.results.append(result)
print(f"\nResults list: {len(evaluator.results)} items")
print(f"First item: {evaluator.results[0]}")

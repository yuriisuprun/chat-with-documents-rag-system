# LLM Provider Validation Test Suite

Comprehensive test suite for validating LLM providers (Groq, Ollama) in the Chat With Documents RAG system.

## Overview

This test suite provides complete validation coverage for LLM providers with 106+ tests across 4 test files:

| Test File | Tests | Coverage | Duration |
|-----------|-------|----------|----------|
| `test_provider_functional.py` | 50 | 12 functional areas × 2 providers | ~45s |
| `test_provider_failures.py` | 15 | 8-10 failure modes × 2 providers | ~52s |
| `test_fallback_mechanisms.py` | 21 | Retry, backoff, isolation | ~76s (timing-intensive) |
| `test_provider_consistency.py` | 20 | Quality, latency, faithfulness | ~9s |
| **TOTAL** | **106** | **Comprehensive** | **~182s** |

## Running Tests

### Run All Tests
```bash
cd backend
python -m pytest tests/llm/ -v
```

### Run Specific Test Suite
```bash
# Functional tests only (no delays)
python -m pytest tests/llm/test_provider_functional.py -v

# Failures only (no delays)
python -m pytest tests/llm/test_provider_failures.py -v

# Consistency only (fast)
python -m pytest tests/llm/test_provider_consistency.py -v

# Fallback tests (timing-intensive, ~76s)
python -m pytest tests/llm/test_fallback_mechanisms.py -v
```

### Run with Coverage
```bash
python -m pytest tests/llm/ --cov=app.infrastructure.llm --cov-report=html
```

### Run Specific Test Class
```bash
python -m pytest tests/llm/test_provider_functional.py::TestGroqProviderFunctional -v
python -m pytest tests/llm/test_provider_functional.py::TestOllamaProviderFunctional -v
```

## Test File Descriptions

### 1. test_provider_functional.py (50 tests, ~45 seconds)

**Purpose**: Validate all 12 critical functional areas for each provider

**Test Classes**:
- `TestGroqProviderFunctional` - 25 tests for Groq
- `TestOllamaProviderFunctional` - 25 tests for Ollama

**Coverage Areas**:
1. ✅ Successful initialization
2. ✅ Valid authentication
3. ✅ Invalid API key handling
4. ✅ Model availability
5. ✅ Prompt construction
6. ✅ Temperature configuration
7. ✅ Maximum context handling
8. ✅ Timeout configuration
9. ✅ Response parsing
10. ✅ Streaming responses
11. ✅ Token usage tracking
12. ✅ Error normalization

**Key Assertions**:
- Provider initializes with correct defaults
- API keys are validated
- Custom parameters override defaults
- Responses are parsed correctly
- Errors are normalized consistently

---

### 2. test_provider_failures.py (15 tests, ~52 seconds)

**Purpose**: Verify graceful handling of failure scenarios

**Test Classes**:
- `TestGroqProviderFailures` - 7 tests for Groq
- `TestOllamaProviderFailures` - 8 tests for Ollama

**Failure Scenarios**:
1. ✅ Service unavailable (500, 503)
2. ✅ Network timeout
3. ✅ Authentication failure (401)
4. ✅ Rate limiting (429)
5. ✅ Server errors (5xx)
6. ✅ Malformed responses
7. ✅ Empty responses
8. ✅ Connection errors

**Key Assertions**:
- Appropriate exception raised
- Exception includes provider name
- Error message is clear and actionable
- Retry logic respects max attempts
- No unhandled exceptions escape

---

### 3. test_fallback_mechanisms.py (21 tests, ~76 seconds - timing-intensive)

**Purpose**: Validate fallback, retry, and backoff behavior

**Test Classes**:
- `TestFallbackMechanisms` - 21 comprehensive fallback tests

**Validation Areas**:
1. ✅ Fallback triggers only on intended conditions
2. ✅ Correct provider selected as fallback
3. ✅ User informed appropriately (logs)
4. ✅ No silent behavior changes
5. ✅ Max retries enforced (no infinite loops)
6. ✅ Exponential backoff applied (2-10 seconds)
7. ✅ Execution time respects deadline
8. ✅ Provider isolation maintained
9. ✅ Transient errors retried
10. ✅ Permanent errors handled appropriately

**Key Assertions**:
- Backoff time increases exponentially
- Total execution time is bounded
- Retries stop after max attempts
- Providers don't interfere with each other
- Error is eventually raised

**⚠️ Note**: These tests include time.sleep() calls for testing backoff delays. They're accurate but slower.

---

### 4. test_provider_consistency.py (20 tests, ~9 seconds)

**Purpose**: Compare provider responses for quality and latency consistency

**Test Classes**:
- `TestProviderConsistency` - 20 comparison tests

**Quality Metrics**:
1. ✅ Answer correctness (factual accuracy)
2. ✅ Faithfulness to context (grounded in sources)
3. ✅ Citation consistency (sources mentioned)
4. ✅ Response completeness (all info included)
5. ✅ Hallucination rate (made-up info percentage)
6. ✅ Response latency (p50, p95, p99)
7. ✅ Consistency across requests
8. ✅ Error handling consistency
9. ✅ Metrics collection
10. ✅ Comparative analysis framework

**Key Assertions**:
- Both providers ground answers in context
- Neither provider hallucinates
- Responses are complete and accurate
- Groq is faster than Ollama (by design)
- Metrics can be collected for both
- Error handling is consistent

---

## Test Results

### Latest Run: 2024-11-21

```
✅ test_provider_functional.py    50/50 PASSED  (100%)
✅ test_provider_failures.py      15/15 PASSED  (100%)
✅ test_fallback_mechanisms.py    21/21 PASSED  (100%)
✅ test_provider_consistency.py   20/20 PASSED  (100%)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ TOTAL                          106/106 PASSED (100%)
```

**Pass Rate**: 100%  
**Failed Tests**: 0  
**Skipped Tests**: 0

---

## Key Testing Patterns

### Mocking External Services
All tests mock external service calls (Groq API, Ollama HTTP):
```python
@patch("groq.Groq")
def test_valid_response(self, mock_groq_class):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Response"))]
    mock_client.chat.completions.create.return_value = mock_response
    mock_groq_class.return_value = mock_client
    
    provider = GroqProvider(api_key="test-key")
    result = provider.generate("test")
    assert result == "Response"
```

### Testing Error Conditions
Errors are simulated and verified:
```python
@patch("groq.Groq")
def test_timeout_handling(self, mock_groq_class):
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("timeout")
    mock_groq_class.return_value = mock_client
    
    provider = GroqProvider(api_key="test-key")
    with pytest.raises(LLMTimeoutException):
        provider.generate("test")
```

### Testing Latency & Timing
Actual timing is measured where needed:
```python
start = time.time()
response = provider.generate("test")
elapsed = time.time() - start

assert elapsed > 0.05  # Should have some latency
```

---

## Configuration for Tests

Tests use the default configuration from `app.core.config.settings`:

**Groq Defaults**:
- Model: `openai/gpt-oss-120b`
- Timeout: 30s
- Temperature: 0.3
- Retries: 3
- Backoff: exponential (2-10s)

**Ollama Defaults**:
- Model: `qwen3:8b`
- Base URL: `http://localhost:11434`
- Timeout: 180s
- Temperature: 0.3
- Retries: 3
- Backoff: exponential (2-10s)

Override with environment variables:
```bash
export GROQ_API_KEY="your-key"
export GROQ_MODEL="your-model"
export GROQ_TIMEOUT=30
```

---

## Troubleshooting

### Tests Timeout
Some tests intentionally have delays (fallback tests):
- Solution: Run non-timing tests separately: `pytest tests/llm/test_provider_functional.py`

### Mock Not Working
Ensure patch targets the import location:
```python
# ✅ Correct - patch where Groq is imported
@patch("groq.Groq")

# ❌ Wrong - patch where used
@patch("app.infrastructure.llm.groq_provider.Groq")
```

### API Key Not Found
Tests check `settings.groq_api_key`:
```bash
export GROQ_API_KEY="test-key"
python -m pytest tests/llm/test_provider_functional.py
```

---

## Coverage Report

### Line Coverage
- Groq Provider: ~95% coverage
- Ollama Provider: ~95% coverage
- Both: ~95% combined

Generate HTML report:
```bash
python -m pytest tests/llm/ --cov=app.infrastructure.llm --cov-report=html
open htmlcov/index.html
```

---

## Test Data & Fixtures

### Test Prompts
```python
test_prompts = [
    "What is the capital of France?",
    "Explain photosynthesis in one sentence.",
    "List three primary colors.",
]
```

### Mock Responses
```python
mock_responses = {
    "groq": "Response from Groq",
    "ollama": {"response": "Response from Ollama"},
}
```

### Error Simulations
```python
error_conditions = [
    Exception("Service Unavailable"),
    Exception("timeout"),
    requests.Timeout(),
    json.JSONDecodeError(...),
]
```

---

## Best Practices

### ✅ DO
- Run full suite before committing
- Use mocks to avoid external dependencies
- Test both success and failure paths
- Include edge cases (empty responses, special characters)
- Document expected behavior in test names
- Use descriptive assertion messages

### ❌ DON'T
- Don't call real APIs in tests
- Don't hardcode sensitive data
- Don't ignore timing-dependent tests
- Don't skip error condition testing
- Don't assume defaults are set correctly
- Don't test implementation details

---

## Performance Expectations

### Test Duration Breakdown
- Functional: 45 seconds
- Failures: 52 seconds
- Consistency: 9 seconds
- **Fast Suite** (without fallback): ~106 seconds
- Fallback: 76 seconds (timing-dependent, intentional delays)
- **Full Suite**: ~182 seconds

### Optimization Tips
- Run fast tests first: `pytest tests/llm/test_provider_functional.py`
- Use `-x` flag to stop on first failure: `pytest -x tests/llm/`
- Use `-k` to filter by test name: `pytest -k "groq" tests/llm/`

---

## Continuous Integration

### GitHub Actions (if used)
```yaml
- name: Run LLM Provider Tests
  run: |
    cd backend
    python -m pytest tests/llm/ -v --tb=short
```

### Local Pre-commit Hook
```bash
#!/bin/bash
python -m pytest tests/llm/test_provider_functional.py -q || exit 1
```

---

## Related Files

- **Test Data**: `backend/tests/llm/`
- **Provider Code**: `backend/app/infrastructure/llm/`
- **Comparison Report**: `backend/LLM_PROVIDER_COMPARISON.md`
- **Test Results**: `backend/provider_test_results.json`

---

## Support & Questions

For questions about tests:
1. Check test docstrings for behavior documentation
2. Review assertions for expected values
3. See `LLM_PROVIDER_COMPARISON.md` for provider details
4. Check provider code for implementation

---

**Last Updated**: 2024-11-21  
**Status**: ✅ All Tests Passing  
**Coverage**: Comprehensive (106+ tests)

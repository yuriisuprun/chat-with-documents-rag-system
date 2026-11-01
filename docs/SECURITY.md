# Security Implementation – Phase 8

This document describes the security features implemented in Phase 8 of the RAG system.

## Overview

Phase 8 adds production-grade security controls to protect the system from common attacks:

- **Rate Limiting**: Prevent abuse and resource exhaustion
- **API Key Authentication**: Restrict access to authorized clients
- **Input Validation**: Reject malformed and malicious requests
- **Prompt Injection Defense**: Detect and log suspicious queries
- **Security Headers**: Protect against XSS, clickjacking, and MIME sniffing
- **HSTS**: Enforce HTTPS in production

## Architecture

```
Request Flow:
   ↓
[HSTS / Security Headers Middleware]
   ↓
[API Key Authentication Middleware]
   ↓
[Rate Limiting Middleware]
   ↓
[Route Handler]
   ↓
[Input Validation]
[Prompt Injection Defense]
   ↓
[Response]
   ↓
[Security Headers Added]
   ↓
Client
```

---

## Features

### 1. Rate Limiting

**Purpose**: Prevent abuse by limiting requests per client.

**Implementation**:
- Token bucket algorithm with per-endpoint limits
- In-memory storage (suitable for single-server deployments)
- Per-IP client tracking
- Configurable limits for global, upload, and chat endpoints

**Configuration** (`.env`):
```env
RATE_LIMIT_ENABLED=true
RATE_LIMIT_GLOBAL=100      # requests per minute
RATE_LIMIT_UPLOAD=10       # requests per minute
RATE_LIMIT_CHAT=30         # requests per minute
```

**Behavior**:
- Returns HTTP 429 Too Many Requests when limit exceeded
- Includes `Retry-After` header with reset time
- Bypasses health check endpoint (`/api/v1/health`)
- Fails gracefully if rate limiter has internal errors

**Example**:
```bash
# Global limit: 100 req/min
curl http://localhost:8000/api/v1/chat -d '{"query":"test"}'
# After 100 requests in a minute:
# 429 Too Many Requests
# Retry-After: 12
```

---

### 2. API Key Authentication

**Purpose**: Restrict access to authorized API consumers.

**Implementation**:
- Bearer token validation via `Authorization` header
- Optional (disabled by default for development)
- Automatic bypass for health and documentation endpoints

**Configuration** (`.env`):
```env
API_KEY_ENABLED=false
API_KEY=your-secure-api-key-here
```

**Enable in Production**:
```env
API_KEY_ENABLED=true
API_KEY=secure-random-key-min-32-chars
```

**Behavior**:
- Checks `Authorization: Bearer <token>` header
- Returns HTTP 401 Unauthorized if invalid or missing
- Bypasses: `/api/v1/health`, `/docs`, `/redoc`, `/openapi.json`
- Case-insensitive `Bearer` prefix

**Example**:
```bash
# Without API key
curl http://localhost:8000/api/v1/documents
# 401 Unauthorized

# With valid API key
curl -H "Authorization: Bearer your-api-key" http://localhost:8000/api/v1/documents
# 200 OK
```

---

### 3. Input Validation

**Purpose**: Prevent malformed and injection attacks.

**Validators**:
- **Query Length**: Max 500 characters (configurable)
- **Document ID**: UUID or alphanumeric format
- **Filename**: Path traversal protection, safe character whitelist
- **Text Sanitization**: Removes null bytes, normalizes newlines
- **SQL Injection Detection**: Pattern-based flagging (passive)
- **Prompt Injection Detection**: Pattern-based flagging (passive)

**Configuration** (`.env`):
```env
MAX_QUERY_LENGTH=500
MAX_DOCUMENT_ID_LENGTH=36
```

**Examples**:

**Query validation**:
```python
from app.core.validators import validate_query_length

# Valid
validate_query_length("What is in this document?")  # ✓

# Invalid
validate_query_length("")  # ✗ ValidationException: empty
validate_query_length("a" * 501)  # ✗ ValidationException: too long
```

**Document ID validation**:
```python
from app.core.validators import validate_document_id

validate_document_id("550e8400-e29b-41d4-a716-446655440000")  # ✓ UUID
validate_document_id("doc_12345")  # ✓ Alphanumeric
validate_document_id("doc@#$%")  # ✗ ValidationException: invalid chars
```

**Filename validation**:
```python
from app.core.validators import validate_filename

validate_filename("report.pdf")  # ✓
validate_filename("../../etc/passwd")  # ✗ ValidationException: path traversal
filename = validate_filename("file@#$.pdf")  # Sanitizes to "file_____.pdf"
```

---

### 4. Prompt Injection Defense

**Purpose**: Detect suspicious queries that attempt to override system instructions.

**Implementation**:
- Pattern-based detection of common injection attempts
- Severity levels: LOW, MEDIUM, HIGH, CRITICAL
- Passive logging (does NOT block by default)
- Safe context assembly to prevent instruction leakage

**Detection Patterns**:
- Ignore/forget instructions
- System prompt extraction attempts
- Role-play redirection
- Context escape attempts
- Explicit jailbreak attempts
- Token smuggling (encoded instructions)

**Behavior**:
- Logs suspicious queries for analysis
- Calculates severity score (0.0-1.0)
- Does NOT block requests (detection-only mode)
- Can be configured to block in `block_on_detection=True` mode

**Example**:
```python
from app.core.prompt_defense import get_prompt_defense

defense = get_prompt_defense()

# Suspicious query
result = defense.detect("ignore previous instructions")
# Result:
# - is_suspicious: True
# - level: CRITICAL
# - patterns_matched: ['ignore_instructions']
# - severity_score: 0.5

# Clean query
result = defense.detect("What are the contents of this document?")
# Result:
# - is_suspicious: False
```

**Logged Example**:
```
WARNING  app.core.prompt_defense:prompt_defense.py:68
Prompt injection detected: patterns=['ignore_instructions'],
level=critical, score=0.50
```

---

### 5. Security Headers

**Purpose**: Protect against common web attacks (XSS, clickjacking, MIME sniffing).

**Headers**:
- `Content-Security-Policy`: Restrict script loading
- `X-Frame-Options: DENY`: Prevent clickjacking
- `X-Content-Type-Options: nosniff`: Prevent MIME sniffing
- `X-XSS-Protection`: XSS protection in older browsers
- `Referrer-Policy`: Control referrer leakage
- `Permissions-Policy`: Disable unnecessary browser features
- `Strict-Transport-Security`: HTTPS enforcement (production only)

**Configuration** (`.env`):
```env
ENABLE_SECURITY_HEADERS=true
ENABLE_HSTS=false  # Only set to true in production
```

**Content-Security-Policy**:
```
default-src 'self'            # Only same-origin by default
script-src 'self'              # Only same-origin scripts (no inline)
style-src 'self' 'unsafe-inline'  # Allow inline styles (for frameworks)
img-src 'self' data:           # Allow data URIs for images
frame-ancestors 'none'         # Prevent framing (clickjacking)
base-uri 'self'                # Restrict base tag
form-action 'self'             # Only same-origin forms
```

**Example Response**:
```
HTTP/1.1 200 OK
Content-Security-Policy: default-src 'self'; script-src 'self'; ...
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```

---

## Configuration

### Development (Default)

```env
# .env (development mode)
ENVIRONMENT=development
API_KEY_ENABLED=false
RATE_LIMIT_ENABLED=true
ENABLE_SECURITY_HEADERS=true
ENABLE_HSTS=false
```

**Effect**:
- No API key required
- Rate limiting active (safe for testing)
- Security headers present
- No HSTS (not needed for localhost)

### Production

```env
# .env (production mode)
ENVIRONMENT=production
API_KEY_ENABLED=true
API_KEY=<generate-secure-random-key>
RATE_LIMIT_ENABLED=true
ENABLE_SECURITY_HEADERS=true
ENABLE_HSTS=true
```

**Recommended API Key Generation**:
```bash
# Generate 32-character random key
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Output: dF5aB_cD8eF9g-H0iJ1kL2mN3oP4qR5s
```

---

## Testing

### Phase 8 Test Coverage

**121+ new tests**, organized by component:

**Rate Limiting** (13 tests):
- Token bucket mechanics
- Per-client isolation
- Endpoint-specific limits
- Reset time calculation
- Bucket cleanup

**Input Validation** (45 tests):
- Query length validation
- Document ID format validation
- Filename sanitization and path traversal
- Text sanitization
- SQL injection detection
- Prompt injection detection
- JSON validation

**Prompt Injection Defense** (25 tests):
- Injection pattern detection
- Severity scoring
- Query sanitization
- Safe context assembly
- Global instance management

**Middleware** (38 tests):
- Rate limiting middleware
- API key authentication middleware
- Security headers middleware
- Integration tests

**Running Tests**:
```bash
# All Phase 8 tests
pytest tests/unit/core/test_rate_limiter.py \
        tests/unit/core/test_validators.py \
        tests/unit/core/test_prompt_defense.py \
        tests/unit/middleware/ -v

# Specific test class
pytest tests/unit/middleware/test_rate_limiting.py::TestRateLimitingMiddleware -v

# With coverage
pytest tests/unit/ --cov=app.core.rate_limiter \
                   --cov=app.core.validators \
                   --cov=app.core.prompt_defense \
                   --cov=app.middleware --cov-report=term-missing
```

---

## Threat Model & Mitigations

| Threat | Risk | Mitigation |
|--------|------|-----------|
| **Abuse/DoS** | Resource exhaustion, server unavailability | Rate limiting per-IP, endpoint-specific limits |
| **Unauthorized Access** | Data breach, API misuse | API key authentication, bypass only for health |
| **Malformed Input** | Crashes, data corruption, injection | Input validation, length limits, sanitization |
| **Prompt Injection** | System instruction override, context escape | Pattern detection, safe context assembly, logging |
| **XSS** | Session hijacking, credential theft | Content-Security-Policy, no inline scripts |
| **Clickjacking** | User tricked into unwanted actions | X-Frame-Options: DENY |
| **MIME Sniffing** | Wrong content type interpretation | X-Content-Type-Options: nosniff |
| **Unencrypted Transport** | Man-in-the-middle, credential interception | HSTS in production (enforces HTTPS) |
| **Server Fingerprinting** | Reconnaissance for targeted attacks | Remove server header, generic error messages |
| **SQL Injection** | Database compromise (ORM default protection) | Parameterized queries via SQLAlchemy |

---

## Best Practices

### For Operators

1. **Enable API Keys in Production**:
   ```env
   API_KEY_ENABLED=true
   API_KEY=<strong-random-key>
   ```

2. **Use HTTPS**:
   - Deploy behind a reverse proxy (nginx, HAProxy)
   - Obtain TLS certificate (Let's Encrypt)
   - Set `ENABLE_HSTS=true` in production

3. **Adjust Rate Limits for Your Workload**:
   ```env
   # High-volume API
   RATE_LIMIT_GLOBAL=1000
   RATE_LIMIT_CHAT=200
   
   # Strict (development)
   RATE_LIMIT_GLOBAL=10
   RATE_LIMIT_CHAT=5
   ```

4. **Monitor Logs for Security Events**:
   ```bash
   # Watch for rate limit breaches
   grep "Rate limit exceeded" logs/app.log
   
   # Watch for prompt injections
   grep "Prompt injection detected" logs/app.log
   
   # Watch for auth failures
   grep "Invalid API key" logs/app.log
   ```

### For Developers

1. **Always Validate User Input**:
   ```python
   from app.core.validators import validate_query_length, sanitize_text
   
   query = sanitize_text(user_input)
   validate_query_length(query, max_length=500)
   ```

2. **Use Prompt Defense for Sensitive Operations**:
   ```python
   from app.core.prompt_defense import get_prompt_defense
   
   defense = get_prompt_defense()
   result = defense.detect(user_query)
   if result.is_suspicious:
       logger.warning(f"Suspicious query: {result}")
       # Can still proceed (detection-only) or block based on severity
   ```

3. **Never Log Sensitive Data**:
   - API keys are filtered from logs
   - User data should be minimized in logs
   - Passwords are never logged

---

## Known Limitations

1. **Rate Limiter**: In-memory storage means limits are per-process. For distributed deployments, use Redis backend (not yet implemented).

2. **Prompt Injection**: Pattern-based detection can have false positives/negatives. Consider ML-based detection for production.

3. **API Keys**: Simple string comparison. For enterprise, consider:
   - OAuth2 with external identity provider
   - JWT tokens with expiration
   - API key rotation

4. **Input Validation**: Basic regex patterns. For complex validation, consider:
   - Custom validators per endpoint
   - Machine learning-based anomaly detection
   - WAF (Web Application Firewall) in front

---

## Future Enhancements (Phase 9+)

- [ ] Redis-backed rate limiting for distributed deployments
- [ ] OAuth2 / OpenID Connect support
- [ ] JWT token generation and validation
- [ ] API key management dashboard
- [ ] Security audit logging
- [ ] ML-based anomaly detection
- [ ] Request signing (HMAC)
- [ ] Encrypted request/response payloads
- [ ] TLS certificate pinning
- [ ] Security vulnerability scanning in CI/CD

---

## Compliance

### Standards & References

- **OWASP Top 10**: Addresses injection, broken auth, XSS, etc.
- **CWE** (Common Weakness Enumeration): Follows CWE mitigations
- **NIST Cybersecurity Framework**: Aligns with secure configuration

### Audit Trail

All security events are logged:
- Rate limit breaches
- Failed authentication attempts
- Prompt injection detection
- Input validation failures

---

## Support

For security questions or to report vulnerabilities:

1. **Development**: Check logs at `logs/app.log` and `logs/error.log`
2. **Testing**: Run security test suite:
   ```bash
   pytest tests/unit/core/test_validators.py -v
   pytest tests/unit/middleware/ -v
   ```
3. **Documentation**: See this file for configuration details

---

## Version

**Phase 8 - Security Implementation**
- **Date**: November 2026
- **Tests**: 121+ passing
- **Coverage**: Rate limiting, validation, prompt defense, headers

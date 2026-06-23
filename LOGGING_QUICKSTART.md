# Logging Quick Start Guide

## Enable Logging in Your Application

The logging system is already configured and ready to use. Here's how to work with it.

## Basic Setup (Already Done)

In `backend/app/main.py`:

```python
import structlog

# Configure logging (already done)
configure_logging()
logger = structlog.get_logger(__name__)

# Middleware added (already done)
app.add_middleware(RequestLoggingMiddleware)
```

## Using Logging in Your Code

### 1. Basic Logging

```python
import structlog

logger = structlog.get_logger(__name__)

# Log an event
logger.info("operation_completed", user_id=123, duration_ms=45)

# Log an error
logger.error("operation_failed", error=str(e), exc_info=True)
```

### 2. With Request Context

```python
from fastapi import Request

@router.get("/items")
def get_items(request: Request):
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.info(
        "getting_items",
        request_id=request_id,
        user_id=user.id
    )
    # ... your code ...
```

### 3. Using Decorators

```python
from app.logging_utils import log_operation, log_external_api_call

@log_operation("user_authentication")
def authenticate(username: str, password: str):
    # Automatically logs: started, completed, error, duration_ms
    ...

@log_external_api_call("openai", "/chat/completions")
def call_openai(prompt: str):
    # Automatically logs API calls and timing
    ...
```

### 4. Using Context Manager

```python
from app.logging_utils import OperationContext

with OperationContext("send_email", email=user.email) as ctx:
    ctx.log_step("fetching_template")
    template = get_template()
    
    ctx.log_checkpoint("rendering_email")
    content = render(template)
    
    ctx.log_step("sending")
    send(content)
```

## Configuration

### Environment Variables

```bash
# Development - detailed logs
export LOG_LEVEL=DEBUG

# Production - JSON logs for aggregation
export LOG_LEVEL=INFO

# Quiet - only errors
export LOG_LEVEL=ERROR
```

### Docker

```dockerfile
# In Dockerfile or docker-compose.yml
ENV LOG_LEVEL=INFO
```

## Log Output Examples

### Development (LOG_LEVEL=DEBUG)

```
2026-06-23 14:30:45.123 - whatsapp_assistant - INFO - operation_completed request_id=abc123 duration_ms=45 user_id=123
2026-06-23 14:30:46.456 - whatsapp_assistant - ERROR - operation_failed request_id=def456 error=Connection timeout
```

### Production (LOG_LEVEL=INFO)

```json
{"event":"operation_completed","log_level":"info","timestamp":"2026-06-23T14:30:45.123Z","request_id":"abc123","duration_ms":45,"user_id":123}
{"event":"operation_failed","log_level":"error","timestamp":"2026-06-23T14:30:46.456Z","request_id":"def456","error":"Connection timeout"}
```

## Common Patterns

### Pattern 1: Request Handler

```python
@router.post("/conversations")
def create_conversation(
    data: ConversationCreate,
    db: Session = Depends(get_db),
    request: Request = None,
):
    request_id = getattr(request.state, "request_id", "unknown") if request else "unknown"
    
    logger.info(
        "create_conversation_started",
        request_id=request_id,
        phone=data.phone_number,
    )
    
    try:
        # ... your logic ...
        logger.info(
            "conversation_created",
            request_id=request_id,
            conversation_id=conv.id,
        )
        return conv
    except Exception as e:
        logger.error(
            "create_conversation_error",
            request_id=request_id,
            error=str(e),
            exc_info=True,
        )
        raise
```

### Pattern 2: Service Method

```python
class UserService:
    def create_user(self, email: str, name: str):
        logger.info(
            "create_user_started",
            email=email,
            name=name,
        )
        
        try:
            user = User(email=email, name=name)
            db.add(user)
            db.commit()
            
            logger.info(
                "user_created",
                user_id=user.id,
                email=email,
            )
            return user
        except Exception as e:
            logger.error(
                "user_creation_failed",
                email=email,
                error=str(e),
                exc_info=True,
            )
            raise
```

### Pattern 3: Background Task

```python
@celery_app.task(bind=True)
def process_data(self, item_id: str):
    start_time = time.time()
    
    logger.info(
        "process_data_started",
        item_id=item_id,
        task_id=self.request.id,
    )
    
    try:
        # ... your logic ...
        duration = time.time() - start_time
        logger.info(
            "process_data_completed",
            item_id=item_id,
            duration_ms=round(duration * 1000, 2),
        )
        return {"status": "success"}
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            "process_data_error",
            item_id=item_id,
            error=str(e),
            duration_ms=round(duration * 1000, 2),
            exc_info=True,
        )
        raise
```

## Log Levels

| Level | When to Use | Example |
|-------|------------|---------|
| DEBUG | Detailed information for debugging | Function arguments, intermediate values |
| INFO | General informational messages | Operation started, completed, business events |
| WARNING | Warning messages for recoverable issues | Missing optional data, retries, fallbacks |
| ERROR | Error messages for exceptions | Failed operations, API errors, exceptions |

## Tips & Tricks

### 1. Always Include Context

❌ Bad:
```python
logger.info("user logged in")
```

✅ Good:
```python
logger.info("user_logged_in", user_id=123, ip=request.client.host)
```

### 2. Use Timing for Performance

```python
start = time.time()
# ... do work ...
duration = time.time() - start

logger.info(
    "operation_completed",
    duration_ms=round(duration * 1000, 2),
)
```

### 3. Include Full Exception Context

```python
try:
    # ... code ...
except Exception as e:
    logger.error(
        "operation_failed",
        error=str(e),
        exc_info=True,  # Always include this!
    )
```

### 4. Use Consistent Field Names

```python
# Conversation-related
conversation_id, client_phone, client_email

# Message-related
message_id, message_type, content_length

# User-related
user_id, username, email

# Request-related
request_id, method, path, status_code

# Timing
duration_ms, elapsed_ms, latency_ms

# API calls
api_name, endpoint, status_code, response_time_ms
```

### 5. Avoid Logging Sensitive Data

```python
# ❌ Don't log passwords, tokens, API keys
logger.info(f"Token: {api_token}")

# ✅ Log reference, not value
logger.info("using_api_token", token_length=len(api_token))
```

## Debugging with Logs

### Find all errors for a conversation

```bash
jq 'select(.conversation_id == "conv_123")' logs.jsonl | grep "error"
```

### Find slow operations (>1000ms)

```bash
jq 'select(.duration_ms > 1000)' logs.jsonl
```

### Find all API errors

```bash
jq 'select(.api != null and .status_code >= 400)' logs.jsonl
```

### Find operations by request ID

```bash
jq 'select(.request_id == "abc-123")' logs.jsonl
```

## Monitoring & Alerts

Example metrics to track:

```
- API response times (p50, p95, p99)
- Error rates by endpoint
- Database query performance
- External API failures
- Task execution duration
- Task failure rates
```

## Integration with Monitoring Tools

### Datadog

```python
# Logs automatically sent to Datadog if configured
# Just use the logger as normal
```

### CloudWatch

```python
# Configure CloudWatch log group in deployment
# structlog outputs to stdout/stderr automatically
```

### ELK Stack

```bash
# Parse JSON logs from stdout
# filebeat → logstash → elasticsearch → kibana
```

## Troubleshooting

### Q: I don't see any logs
A: Check LOG_LEVEL environment variable
```bash
export LOG_LEVEL=DEBUG
```

### Q: Logs are not structured (not JSON)
A: Check if you're in development mode
```bash
export LOG_LEVEL=INFO  # Forces JSON in structlog
```

### Q: I see "request_id=unknown"
A: Make sure you're passing the Request object to the function
```python
def my_endpoint(request: Request):  # Add Request parameter
    request_id = getattr(request.state, "request_id", "unknown")
```

### Q: How do I trace a specific user's activity?
A: Use request_id or add user_id to all relevant logs
```python
logger.info(
    "user_action",
    request_id=request.state.request_id,
    user_id=current_user.id,
    action="logged_in",
)
```

## Next Steps

1. **Start small**: Add logging to new code first
2. **Review existing**: Check examples in `api/conversations.py`
3. **Use utilities**: Leverage decorators from `logging_utils.py`
4. **Monitor**: Set up dashboards for key metrics
5. **Iterate**: Refine logging based on what you need

## Resources

- **Full Guide**: `LOGGING_GUIDE.md`
- **Summary**: `LOGGING_REFACTOR_SUMMARY.md`
- **Inventory**: `LOGGING_INVENTORY.md`
- **Utilities**: `backend/app/logging_utils.py`
- **Examples**: Look at `backend/app/api/conversations.py`

## Questions?

Refer to the comprehensive documentation in `LOGGING_GUIDE.md` for:
- Best practices
- Log aggregation setup
- Advanced patterns
- Real-world examples

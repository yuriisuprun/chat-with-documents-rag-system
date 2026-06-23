# Logging Guide - WhatsApp AI Assistant

This guide describes the logging infrastructure and best practices for the WhatsApp AI Assistant system.

## Overview

The system uses **structured logging** with `structlog` to provide consistent, queryable logs across all components. Logs are JSON-formatted in production and human-readable in development mode.

## Architecture

### Logging Stack

- **structlog**: Structured logging library for consistent log formatting
- **Python logging**: Standard library integration for stdlib compatibility
- **Request correlation**: Unique request IDs propagated through request context
- **Middleware logging**: HTTP request/response timing and correlation

### Configuration

Logging is configured in `backend/app/main.py`:

```python
def configure_logging():
    """Configure structured logging with structlog and stdlib logging."""
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer() if settings.LOG_LEVEL == "DEBUG" else structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
```

**Log Level**: Configured via `LOG_LEVEL` environment variable (default: `INFO`)

## Request Correlation

All HTTP requests are assigned a unique `request_id` by the `RequestLoggingMiddleware`:

```python
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        logger.info(
            "http_request_received",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            ...
        )
```

The `request_id` is:
- Generated for each HTTP request
- Stored in `request.state.request_id`
- Included in all related logs
- Useful for tracing requests across multiple calls

## Logging Patterns

### 1. API Endpoints

All API endpoints log their operations with request correlation:

```python
@router.get("/conversations")
def list_conversations(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    request: Request = None,
) -> list[ConversationResponse]:
    """List all conversations."""
    request_id = getattr(request.state, "request_id", "unknown") if request else "unknown"
    
    logger.info(
        "list_conversations_started",
        request_id=request_id,
        skip=skip,
        limit=limit,
    )
    
    try:
        # ... operation logic ...
        logger.info(
            "list_conversations_success",
            request_id=request_id,
            count=len(conversations),
        )
        return conversations
    except Exception as e:
        logger.error(
            "list_conversations_error",
            request_id=request_id,
            error=str(e),
            exc_info=True,
        )
        raise
```

**Pattern**: `{operation}_{status}` with request correlation

### 2. Services

Services log external API calls, processing steps, and timing:

```python
def detect_language_and_intent(self, message: str) -> Tuple[str, Intent, float]:
    """Detect message language and intent using AI."""
    if not message:
        logger.warning(
            "empty_message_received",
            operation="language_intent_detection"
        )
        return settings.TENANT_DEFAULT_LANGUAGE, Intent.OTHER, 0.0
    
    try:
        logger.debug(
            "language_intent_detection_started",
            message_length=len(message)
        )
        
        # ... detection logic ...
        
        logger.info(
            "language_intent_detection_completed",
            language=detected_lang,
            intent=intent.value,
            confidence=round(lang_confidence, 3)
        )
        return detected_lang, intent, lang_confidence
        
    except Exception as e:
        logger.error(
            "language_intent_detection_error",
            error=str(e),
            exc_info=True
        )
        raise
```

**Pattern**: Structured context fields, consistent naming

### 3. Celery Tasks

Background tasks log execution with timing:

```python
@celery_app.task(bind=True, autoretry_for=(Exception,))
def send_auto_reply(self, conversation_id: str) -> dict:
    """Send automatic AI reply."""
    start_time = time.time()
    
    try:
        logger.info(
            "auto_reply_task_started",
            conversation_id=conversation_id,
            task_id=self.request.id,
            attempt=self.request.retries + 1,
        )
        
        # ... task logic ...
        
        duration = time.time() - start_time
        logger.info(
            "auto_reply_sent_successfully",
            conversation_id=conversation_id,
            message_id=ai_message.id,
            language=conversation_language,
            duration_ms=round(duration * 1000, 2),
        )
        return {"status": "success", "message_id": ai_message.id}
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            "auto_reply_task_error",
            conversation_id=conversation_id,
            error=str(e),
            duration_ms=round(duration * 1000, 2),
            exc_info=True,
        )
        raise
    finally:
        db.close()
```

**Pattern**: Task start/completion, timing, attempt tracking

## Log Levels

### ERROR
- Exceptions and failures
- API errors and timeouts
- Database connection failures
- External service errors

Example:
```python
logger.error(
    "whatsapp_send_api_error",
    conversation_id=conversation_id,
    status_code=response.status_code,
    response_text=response.text,
    exc_info=True,
)
```

### WARNING
- Retries and fallbacks
- Missing optional data
- Unconfirmed but acceptable conditions
- Configuration issues

Example:
```python
logger.warning(
    "conversation_not_found_for_update",
    request_id=request_id,
    conversation_id=conversation_id,
)
```

### INFO
- Operation start/completion
- State transitions
- Business events
- Successful integrations

Example:
```python
logger.info(
    "whatsapp_message_sent_successfully",
    conversation_id=conversation_id,
    whatsapp_message_id=message_id,
    recipient_phone=phone_number,
)
```

### DEBUG
- Detailed operation steps
- Data processing details
- Performance checkpoints
- Verbose context

Example:
```python
logger.debug(
    "whatsapp_send_message_started",
    conversation_id=conversation_id,
    recipient_phone=phone_number,
    message_length=len(message_content),
)
```

## Logging Utilities

### Decorators

Located in `backend/app/logging_utils.py`, several decorators simplify logging:

#### @log_operation

```python
from app.logging_utils import log_operation

@log_operation("user_authentication", include_args=False)
def authenticate_user(username: str, password: str) -> bool:
    # Automatically logs start, completion, duration, and errors
    ...
```

#### @log_database_operation

```python
from app.logging_utils import log_database_operation

@log_database_operation("create", "conversation")
def create_conversation(phone_number: str) -> Conversation:
    # Automatically logs db_create_conversation_started/completed/error
    ...
```

#### @log_external_api_call

```python
from app.logging_utils import log_external_api_call

@log_external_api_call("openai", "/chat/completions")
def generate_response(prompt: str) -> str:
    # Automatically logs API call timing and errors
    ...
```

### Context Manager

```python
from app.logging_utils import OperationContext

with OperationContext("appointment_creation", client_id="123") as ctx:
    ctx.log_step("fetching_calendar", calendar_id="abc")
    # ... do work ...
    ctx.log_checkpoint("calendar_fetched", event_count=5)
    # ... more work ...
```

## Standard Log Fields

All logs should include relevant context fields:

| Field | Description | Example |
|-------|-------------|---------|
| `request_id` | HTTP request correlation ID | `"f47ac10b-58cc-4372-a567-0e02b2c3d479"` |
| `conversation_id` | Conversation being processed | `"conv_abc123"` |
| `user_id` | Authenticated user | `"user_456"` |
| `tenant_id` | Tenant/organization | `"tenant_789"` |
| `operation` | Operation name | `"language_detection"` |
| `error` | Error message | `"Failed to reach API"` |
| `duration_ms` | Operation duration | `1234.56` |
| `status_code` | HTTP status or service status | `200`, `"success"`, `"failed"` |
| `message_length` | Content size | `256` |
| `language` | Detected language | `"en"`, `"it"`, `"ru"` |
| `intent` | Detected intent | `"appointment_request"` |

## Best Practices

### 1. Use Structured Fields

❌ **Bad**: Avoid string interpolation
```python
logger.info(f"Processing conversation {conv_id} for user {user_id}")
```

✅ **Good**: Use structured fields
```python
logger.info(
    "processing_conversation",
    conversation_id=conv_id,
    user_id=user_id
)
```

### 2. Include Context for Errors

❌ **Bad**: Minimal error info
```python
logger.error("Something went wrong")
```

✅ **Good**: Include context and traceback
```python
logger.error(
    "appointment_creation_failed",
    conversation_id=conv_id,
    error=str(e),
    exc_info=True,
)
```

### 3. Log Timing for Performance

```python
start_time = time.time()
try:
    # ... operation ...
    duration = time.time() - start_time
    logger.info(
        "operation_completed",
        duration_ms=round(duration * 1000, 2),
    )
except Exception as e:
    duration = time.time() - start_time
    logger.error(
        "operation_error",
        duration_ms=round(duration * 1000, 2),
        error=str(e),
        exc_info=True,
    )
```

### 4. Use Consistent Naming

- Operation events: `{operation}_{status}` (e.g., `send_message_started`, `send_message_completed`)
- External APIs: `{service}_{operation}_{status}` (e.g., `whatsapp_send_message_started`)
- Database: `db_{operation}_{entity}_{status}` (e.g., `db_create_conversation_success`)
- Tasks: `task_{name}_{status}` (e.g., `task_send_auto_reply_completed`)

### 5. Don't Log Sensitive Data

❌ **Bad**: Log passwords, tokens, secrets
```python
logger.info(f"Authenticating user with password: {password}")
```

✅ **Good**: Log only necessary identifying info
```python
logger.info(
    "user_authentication_started",
    username=username,
    ip_address=request.client.host
)
```

## Environment Variables

Configure logging behavior with:

```bash
# Log level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# For development (console output)
LOG_LEVEL=DEBUG

# For production (JSON output)
LOG_LEVEL=INFO
```

## Monitoring and Analysis

### Querying Logs

In production with JSON logs, you can query structured fields:

```bash
# Find all failed operations
jq 'select(.status == "error")' logs.jsonl

# Find slow requests (>1000ms)
jq 'select(.duration_ms > 1000)' logs.jsonl

# Find specific conversation
jq 'select(.conversation_id == "conv_123")' logs.jsonl
```

### Log Aggregation

For centralized logging (ELK, Datadog, CloudWatch):

1. Configure log shipping in deployment
2. Use request IDs for distributed tracing
3. Create dashboards for key metrics:
   - API response times
   - Error rates
   - External API failures
   - Task execution times

## Examples

### Complete Request Flow

```
INFO http_request_received request_id=f47ac10b method=POST path=/api/v1/webhooks/whatsapp
DEBUG whatsapp_webhook_message_parsed message_type=text sender_phone=+1234567890
INFO auto_reply_task_started conversation_id=conv_123 attempt=1
DEBUG language_intent_detection_started message_length=45
INFO language_detected language=en confidence=0.95
INFO intent_detected intent=appointment_request language=en
DEBUG whatsapp_send_message_started recipient_phone=+1234567890 message_length=156
INFO whatsapp_message_sent_successfully whatsapp_message_id=wamid.abc123
INFO auto_reply_sent_successfully message_id=msg_xyz duration_ms=2341
INFO http_response_sent request_id=f47ac10b status_code=200 duration_ms=2350
```

### Error Handling

```
INFO appointment_creation_started conversation_id=conv_456
DEBUG extracting_appointment_details language=it
INFO auto_appointment_creation_enabled
DEBUG google_calendar_api_call_started endpoint=/calendars/list
ERROR google_calendar_api_call_error error=401 Unauthorized duration_ms=156
WARNING appointment_creation_skipped_api_error reason=calendar_unavailable
INFO auto_reply_sent_successfully message_id=msg_789 duration_ms=3200
```

## Troubleshooting

### No logs appearing?
- Check `LOG_LEVEL` environment variable
- Ensure `structlog` is imported: `import structlog`
- Check application is running (not in import error state)

### Logs not structured?
- Verify structlog configuration in `main.py`
- Check for mixed stdlib logging (use structlog consistently)
- Ensure JSON renderer is enabled in production

### Missing request_id in logs?
- Verify middleware is added before routes
- Check request object is passed to handlers
- Verify `getattr(request.state, "request_id", "unknown")`

## Summary

The logging system provides:
- **Structured logs**: JSON-formatted for easy parsing
- **Request correlation**: Track requests across components
- **Timing information**: Monitor performance
- **Error context**: Comprehensive troubleshooting
- **Multi-level details**: DEBUG to ERROR as needed

For questions or improvements, contribute to this guide or discuss with the team.

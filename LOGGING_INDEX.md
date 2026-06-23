# Logging System Index

Complete reference for the logging refactor of the WhatsApp AI Assistant.

## 📚 Documentation Files

### 1. **LOGGING_QUICKSTART.md** - Start Here! ⭐
**Best for**: Getting up and running quickly
- Basic usage examples
- Configuration guide
- Common patterns
- Tips & tricks
- Troubleshooting

→ Read this first to understand how to use logging

### 2. **LOGGING_GUIDE.md** - Comprehensive Reference
**Best for**: Deep understanding and best practices
- Complete architecture overview
- Request correlation patterns
- Log level guidelines
- Standard field naming
- Sensitive data handling
- Log aggregation setup
- Real-world examples
- Monitoring and analysis

→ Read this for production deployment and detailed guidance

### 3. **LOGGING_INVENTORY.md** - What Was Added
**Best for**: Understanding exactly what logging was added
- Complete list of log events by component
- Log counts by level
- Key metrics tracked
- Sensitive data policy
- Best practices checklist
- Quick stats

→ Reference this to see specific logging in each file

### 4. **LOGGING_REFACTOR_SUMMARY.md** - Overview
**Best for**: High-level understanding of changes
- What was added and why
- Files modified and created
- Key features
- Benefits
- Next steps
- Compatibility info

→ Read this for context on the refactor

## 🔧 Code Files

### Modified Files

| File | Changes | Log Events |
|------|---------|-----------|
| `backend/app/main.py` | ✅ Structlog setup, middleware | Request/response logging |
| `backend/app/api/conversations.py` | ✅ All endpoints logged | 20+ endpoint events |
| `backend/app/services/ai_service.py` | ✅ Comprehensive logging | Language, intent, detection events |
| `backend/app/services/whatsapp_service.py` | ✅ API and webhook logging | Send, parse, media events |
| `backend/app/tasks.py` | ✅ Task execution logging | 20+ task events |

### New Files

| File | Purpose | Contains |
|------|---------|----------|
| `backend/app/logging_utils.py` | Logging utilities | Decorators, context managers, helpers |

## 📊 Statistics

```
Total Log Points:        75+
Total Documentation:     4 guides
New Code Files:          1 utilities module
Modified Files:          5 source files
Log Events by Level:
  - DEBUG:      8
  - INFO:       35+
  - WARNING:    12+
  - ERROR:      20+
```

## 🚀 Quick Start

### 1. Enable Logging
```bash
export LOG_LEVEL=INFO  # or DEBUG for development
```

### 2. Use in Your Code
```python
import structlog

logger = structlog.get_logger(__name__)

logger.info(
    "operation_completed",
    request_id=request.state.request_id,
    duration_ms=45,
)
```

### 3. View Logs
```
Development: Human-readable console output
Production: JSON format for aggregation
```

## 📖 Reading Guide

### For Developers
1. Start: **LOGGING_QUICKSTART.md**
2. Code: Look at `backend/app/api/conversations.py` examples
3. Reference: **LOGGING_GUIDE.md** for patterns

### For DevOps/SRE
1. Overview: **LOGGING_REFACTOR_SUMMARY.md**
2. Details: **LOGGING_GUIDE.md** (log aggregation section)
3. Inventory: **LOGGING_INVENTORY.md** (metrics and fields)

### For Code Review
1. Summary: **LOGGING_REFACTOR_SUMMARY.md**
2. Inventory: **LOGGING_INVENTORY.md** (what was added)
3. Files: Compare modified source files

### For Maintenance
1. Inventory: **LOGGING_INVENTORY.md** (quick reference)
2. Guide: **LOGGING_GUIDE.md** (best practices)
3. Utils: `backend/app/logging_utils.py` (available decorators)

## 🎯 Key Features

✅ **Request Correlation**: Every request gets a `request_id`  
✅ **Structured Logging**: JSON output for log aggregation  
✅ **Performance Metrics**: `duration_ms` on all operations  
✅ **Error Context**: Full tracebacks with business context  
✅ **Multi-level Coverage**: DEBUG through ERROR logs  
✅ **Reusable Utilities**: Decorators and context managers  
✅ **Production Ready**: Tested and backward compatible  

## 🔍 Log Flow Example

```
1. Request arrives
   → http_request_received (request_id assigned)
   
2. API endpoint called
   → operation_started (with context)
   
3. Service processes
   → language_detected, intent_detected
   
4. WhatsApp integration
   → whatsapp_message_sent_successfully
   
5. Background task scheduled
   → task_started
   
6. Response sent
   → operation_completed, http_response_sent
```

All logs include `request_id` for tracing the entire flow.

## 📝 Naming Conventions

**Endpoint Events**
```
{operation}_{status}
list_conversations_started
create_conversation_success
update_conversation_error
```

**Service Events**
```
{service}_{operation}_{status}
language_detection_started
whatsapp_send_message_completed
ai_service_error
```

**Task Events**
```
task_{name}_{status}
task_send_auto_reply_started
task_process_audio_error
```

**External API Events**
```
{api}_{operation}_{status}
openai_api_call_started
google_calendar_event_created
```

## 🔐 Security & Privacy

- ✅ Phone numbers logged (necessary for tracing)
- ✅ Conversation IDs logged (necessary for tracking)
- ✗ Passwords NEVER logged
- ✗ API keys NEVER logged (only presence)
- ✗ Full messages not logged (length instead)
- ✗ Email addresses not logged unnecessarily

## 🛠️ Available Utilities

In `backend/app/logging_utils.py`:

```python
# Decorators
@log_operation("name")
@log_database_operation("create", "entity")
@log_external_api_call("api_name", "/endpoint")
@log_task_execution("task_name")

# Context Manager
with OperationContext("operation_name") as ctx:
    ctx.log_step("step_name")
    ctx.log_checkpoint("checkpoint_name")

# Helpers
add_request_context(request_id, user_id, tenant_id)
```

## 📈 Monitoring Examples

### Query All Errors
```bash
jq 'select(.log_level == "error")' logs.jsonl
```

### Find Slow Operations
```bash
jq 'select(.duration_ms > 1000)' logs.jsonl
```

### Trace Specific Request
```bash
jq 'select(.request_id == "abc-123")' logs.jsonl
```

### Find API Failures
```bash
jq 'select(.api != null and .status_code >= 400)' logs.jsonl
```

## 🚨 Troubleshooting

| Issue | Solution |
|-------|----------|
| No logs visible | Check LOG_LEVEL env var |
| Not JSON format | In development, use structlog processor |
| request_id missing | Pass Request object to handler |
| Logs mixed with print() | Use logger consistently |
| Performance impact | Use DEBUG level only in dev |

See **LOGGING_QUICKSTART.md** for detailed troubleshooting.

## 📦 Backward Compatibility

✅ All changes are backward compatible  
✅ Existing code patterns still work  
✅ No breaking changes to APIs  
✅ Can be enabled/disabled via LOG_LEVEL  
✅ Production ready  

## 🔄 Next Steps

### Immediate
1. Review `LOGGING_QUICKSTART.md`
2. Look at examples in `api/conversations.py`
3. Start using logging in new code

### Short Term
1. Review logs during testing
2. Add custom alerts for critical operations
3. Set up log rotation

### Medium Term
1. Integrate with log aggregation system
2. Create operational dashboards
3. Set up error rate monitoring

### Long Term
1. Implement OpenTelemetry for tracing
2. Add custom business metrics
3. Create runbooks for common errors

## 📞 Support

For questions:
1. **Quick answers**: See `LOGGING_QUICKSTART.md`
2. **Deep dive**: See `LOGGING_GUIDE.md`
3. **What's available**: See `LOGGING_INVENTORY.md`
4. **Code examples**: Look at modified source files
5. **Utilities**: Check `backend/app/logging_utils.py`

## ✅ Verification Checklist

- ✅ All files compile without errors
- ✅ Backward compatible with existing code
- ✅ Production-ready with JSON output
- ✅ Request correlation implemented
- ✅ 75+ logging points added
- ✅ Comprehensive documentation provided
- ✅ Reusable utilities created
- ✅ Security best practices followed
- ✅ Performance metrics included
- ✅ Error context captured

## 📄 File Organization

```
Backend/
├── app/
│   ├── main.py .......................... ✅ Logging configured
│   ├── api/
│   │   └── conversations.py ............ ✅ Endpoint logging
│   └── services/
│       ├── ai_service.py .............. ✅ Service logging
│       ├── whatsapp_service.py ......... ✅ API logging
│       └── ...
│   ├── tasks.py ........................ ✅ Task logging
│   └── logging_utils.py ............... ✨ NEW utilities
│
Documentation/
├── LOGGING_INDEX.md .................... This file
├── LOGGING_QUICKSTART.md ............... Quick start guide
├── LOGGING_GUIDE.md .................... Full reference
├── LOGGING_INVENTORY.md ................ What was added
└── LOGGING_REFACTOR_SUMMARY.md ......... Overview
```

## 🎓 Learning Path

```
Start Here
    ↓
LOGGING_QUICKSTART.md
    ↓
Try Examples
    ↓
Review Code in conversations.py
    ↓
Use Decorators
    ↓
LOGGING_GUIDE.md for Deep Dive
    ↓
Set Up Monitoring
    ↓
Production Deployment
```

---

**Last Updated**: June 23, 2026  
**Status**: ✅ Production Ready  
**Maintainer**: Development Team  

For the latest information, check the documentation files listed above.

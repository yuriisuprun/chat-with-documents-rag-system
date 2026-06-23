# Architecture Overview

## System Design

WhatsApp AI Auto-Responder is built as a modular monolith with clear separation of concerns, designed for simplicity, scalability, and maintainability. It uses a **single-tenant architecture** with environment-based configuration, allowing easy deployment for different professionals without code changes.

```
┌─────────────────────────────────────────────────────────────┐
│                      WhatsApp Business API                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                           │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Webhook Handler                           │ │
│  │  - Message Reception                                  │ │
│  │  - Message Parsing                                    │ │
│  │  - Conversation Management                            │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              API Routes                                │ │
│  │  - Conversations, Documents                           │ │
│  │  - Tenant Configuration (/info/tenant)                │ │
│  │  - Admin Dashboard                                    │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Services Layer                            │ │
│  │  - AI Service (OpenAI)                                │ │
│  │  - WhatsApp Service                                   │ │
│  │  - RAG Service (Vector Search)                        │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Configuration                             │ │
│  │  - Read from environment variables                    │ │
│  │  - Professional details (TENANT_*)                    │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────┬──────────────────────────────────────────────────┘
           │
    ┌──────┴──────────────────────────┐
    │                                 │
    ▼                                 ▼
┌─────────────────┐          ┌──────────────────┐
│  PostgreSQL DB  │          │  Redis Queue     │
│  with pgvector  │          │  & Cache         │
└─────────────────┘          └──────┬───────────┘
                                    │
                                    ▼
                          ┌──────────────────────┐
                          │  Celery Workers      │
                          │  - Auto-reply Tasks  │
                          │  - Transcription     │
                          │  - Embeddings Gen.   │
                          └──────────────────────┘
    ▼
┌─────────────────────────────────────────┐
│      React Admin Dashboard              │
│  - Conversation Monitoring              │
│  - Document Management                  │
│  - Configuration View                   │
└─────────────────────────────────────────┘
```

## Component Architecture

### 1. FastAPI Backend (`app/main.py`)

**Responsibility**: HTTP request routing, middleware, and application setup.

**Primary Entry Point**: WhatsApp Webhook
- `/api/v1/webhooks/whatsapp` - **Primary**: Message reception from WhatsApp (creates conversations automatically)

**Supporting Routes**:
- `/health` - Health checks
- `/ready` - Readiness checks
- `/api/v1/auth` - Authentication
- `/api/v1/info/tenant` - Get tenant configuration
- `/api/v1/conversations` - View conversations (read-only from WhatsApp), or create for testing only
- `/api/v1/documents` - Knowledge base management
- `/api/v1/webhooks/whatsapp` - Message reception from WhatsApp Business API

### 2. Configuration Layer

**Environment Variables** (`app/config.py`):

All professional/tenant settings come from environment variables:
```
TENANT_BUSINESS_NAME          # Your business name
TENANT_PROFESSIONAL_NAME      # Your name
TENANT_WHATSAPP_NUMBER        # Your WhatsApp number
TENANT_AUTO_REPLY_DELAY_MINUTES
TENANT_BOOKING_URL
TENANT_OFFICE_HOURS
TENANT_DISCLAIMER
```

No database-level multi-tenancy needed. Configuration is managed through `.env` files.

### 3. Database Layer

**Models** (`app/models.py`):

```
Conversation (no tenant_id)
  ├── Message (1:N)
  │   └── Detected Intent
  └── AuditLog (1:N)

KnowledgeDocument
  └── DocumentChunk (1:N) with Vector Embeddings
```

**Key Tables** (simplified):
- `conversations` - Chat sessions (client_phone identifies conversation)
- `messages` - Individual messages with intent detection
- `knowledge_documents` - Uploaded files
- `document_chunks` - RAG chunks with embeddings
- `audit_logs` - Compliance trail

### 4. Services Layer

#### AI Service (`app/services/ai_service.py`)

Handles OpenAI interactions:
- Intent detection (text classification)
- Response generation (with RAG context)
- Audio transcription (speech-to-text)
- Embedding generation (for vector search)
- Professional info from environment configuration

**Safety Guardrails**:
- Legal question detection → escalation only
- Response includes configurable disclaimer (from `TENANT_DISCLAIMER`)
- No professional advice generation
- Confidence scoring for responses

#### WhatsApp Service (`app/services/whatsapp_service.py`)

Manages WhatsApp Business API:
- Message sending
- Media retrieval
- Webhook verification
- Status updates
- Uses `TENANT_WHATSAPP_NUMBER` from configuration

#### RAG Service (`app/services/rag_service.py`)

Retrieval-Augmented Generation:
- Document text extraction (PDF, DOCX, TXT)
- Text chunking (500 chars with 100 char overlap)
- Vector embedding generation
- Similarity search using pgvector
- No tenant filtering (single tenant only)

### 5. Task Queue (Celery + Redis)

**Purpose**: Asynchronous processing without blocking HTTP requests.

**Tasks** (`app/tasks.py`):

1. **send_auto_reply** (delayed)
   - Scheduled for N minutes after client message (configurable via `TENANT_AUTO_REPLY_DELAY_MINUTES`)
   - Checks if professional already replied
   - Generates AI response if needed
   - Sends via WhatsApp
   - Idempotent (same task ID prevents duplicates)

2. **process_audio_transcription** (async)
   - Downloads audio from WhatsApp
   - Transcribes using OpenAI Whisper
   - Stores transcript in message record
   - Detects intent from transcribed text

3. **generate_embeddings_for_document** (async)
   - Chunks document into overlapping segments
   - Generates embeddings for each chunk
   - Stores in pgvector for similarity search

### 6. Webhook Flow

```
WhatsApp Message Arrives
    ↓
[Webhook Handler - /api/v1/webhooks/whatsapp]
    ├─ Verify token
    ├─ Parse message (text/audio/etc)
    ├─ Find/create conversation
    ├─ Create message record
    ├─ Detect intent
    └─ Schedule auto-reply task (using TENANT_AUTO_REPLY_DELAY_MINUTES)
    ↓
[After configured delay - default 30 minutes]
    ├─ Check if professional replied
    ├─ If yes → Stop
    ├─ If no → Generate AI response
    │  ├─ Retrieve RAG context from knowledge base
    │  ├─ Call OpenAI GPT
    │  └─ Add disclaimer (TENANT_DISCLAIMER)
    └─ Send via WhatsApp

## Data Flow Examples

### ✅ Correct Flow: WhatsApp is Source of Truth

```
WhatsApp Client Message
    ↓
[Webhook Handler - /api/v1/webhooks/whatsapp]
    ├─ Verify webhook token
    ├─ Parse message (from WhatsApp Business API)
    ├─ Auto-create conversation (if first message)
    ├─ Create message record
    ├─ Detect language & intent
    └─ Schedule auto-reply task
    ↓
[Dashboard - Auto-Updates]
    ├─ Show conversation
    ├─ Show message from client
    └─ Show AI response (after delay)
    ↓
[Professional - Sees on Both Channels]
    ├─ Message visible in WhatsApp
    ├─ AI auto-reply visible in WhatsApp
    └─ Dashboard reflects the same conversation
```

### ❌ Incorrect Flow: Manual Input (Deprecated)

```
Dashboard "Create Conversation"
    ↓
[API Endpoint - Manual Creation]
    ├─ Creates conversation in database
    └─ But NO message from WhatsApp
    ↓
[Problem: Inconsistent State]
    ├─ Dashboard shows conversation
    ├─ WhatsApp shows nothing
    ├─ AI has no context for response
    └─ Professional confused about origin
```

**Note:** Manual creation endpoints exist for testing/development but should never be used in production. Always test with actual WhatsApp messages via webhook.

### Example 1: Text Message with Auto-Reply

```
1. Client sends: "What are your office hours?"
2. Webhook receives and creates Conversation + Message
3. Intent detected: "office_hours"
4. Auto-reply scheduled for 30 minutes
5. Professional doesn't reply
6. AI Service retrieves office hours from knowledge base (language-specific)
7. AI generates: "Our office hours are Mon-Fri 9:00-17:00 CET" (in user's language)
8. Response sent via WhatsApp with disclaimer
```

### Example 2: Audio Message

```
1. Client sends voice note (3 seconds)
2. Webhook receives audio, creates Message with media_url
3. Transcription task scheduled
4. Audio downloaded and transcribed: "Can you help with my case?"
5. Intent detected: "legal_question"
6. Auto-reply scheduled
7. Professional doesn't reply
8. AI Service detects legal question
9. Escalation message sent: "A professional will contact you shortly"
```

### Example 3: Professional Replies Before Timeout

```
1. Client: "I need to reschedule"
2. Professional replies (within 30 mins): "Sure, here's my calendar link"
3. Auto-reply task executes
4. Conversation.last_professional_message_at is checked
5. AI skips response (professional already handled it)
6. Task completes successfully
```

## Security Architecture

### Authentication & Authorization

```
┌──────────────────┐
│  Admin Login     │
│  (username/pass) │
└────────┬─────────┘
         │
         ▼
┌──────────────────────┐
│ JWT Token Generated  │
│ (24 hour expiry)     │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│ Sent in Authorization header             │
│ Authorization: Bearer <jwt_token>        │
└────────┬─────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│ Verified on each protected endpoint      │
│ Invalid/expired → 401 Unauthorized       │
└──────────────────────────────────────────┘
```

### Professional Configuration Isolation

- All professional settings loaded from environment
- Configuration is single-instance (no multi-tenant routing)
- WhatsApp number uniquely identifies the professional
- All conversations belong to the configured professional
- No cross-professional data possible by design

### Secrets Management

```
Environment Variables (.env)
    ├─ Database credentials (never in code)
    ├─ API keys (OpenAI, WhatsApp)
    ├─ JWT secret (for token signing)
    ├─ Professional settings (TENANT_*)
    └─ Admin password (hashed with bcrypt)
```

## Scalability Considerations

### Current (MVP - Single Tenant Instance)

- Single backend instance per professional
- Database shared for same professional (but could be separate)
- Synchronous database queries
- Single Celery worker
- In-memory task queue (Redis)

### Scale-Up Path

1. **Multiple Instances for Multiple Professionals**
   - Run separate Docker Compose for each professional
   - Each has its own .env configuration
   - Can use separate databases or shared with filtering
   - Independent scaling per professional

2. **Single Tenant Horizontal Scaling**
   - Add Celery workers: `docker-compose up -d --scale celery_worker=5`
   - Load balance with nginx
   - Database read replicas

3. **Performance**
   - Add caching layer (Redis)
   - Batch process embeddings
   - Optimize vector search indices
   - Connection pooling

4. **Async Improvements**
   - Stream large document uploads
   - Batch webhook processing
   - Background task optimization

## Compliance & Audit

### Message Flow Audit Trail

```
All interactions logged:
    ├─ audit_logs table
    ├─ Action: message_received, ai_response_sent, etc.
    ├─ Timestamp: precise UTC
    ├─ Details: context-specific metadata
    └─ Retention: indefinite (for compliance)
```

### Legal Compliance

```
AI Response Generation:
    ├─ Intent check
    │  └─ legal_question → Escalation only
    ├─ Context retrieval
    │  └─ Only approved FAQ/service info
    ├─ Response generation
    │  └─ Temperature: 0.7 (consistency)
    └─ Disclaimer mandatory
       └─ From TENANT_DISCLAIMER environment variable
```

## Deployment Architecture

### Docker Compose (Development & MVP Production)

```
docker-compose.yml
├─ PostgreSQL (database)
├─ Redis (queue)
├─ FastAPI Backend (port 8000)
├─ Celery Worker
├─ Celery Beat (scheduler)
└─ React Frontend (port 3000)

Single VPS deployment:
    └─ nginx (reverse proxy, SSL)
        ├─ :443 → FastAPI/Frontend
        └─ :80 → Redirect to HTTPS
```

### Future (Kubernetes)

If scaling beyond single VPS:
- Separate services per container
- StatefulSet for database
- ConfigMap for settings
- Secrets for credentials

## Error Handling & Resilience

### Retries

```python
# Celery auto-retry with exponential backoff
@celery_app.task(
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3},
    default_retry_delay=60,
)
```

### Idempotency

- Auto-reply tasks use `task_id=f"auto_reply_{conversation_id}"`
- Prevents duplicate responses if task retries
- Database checks before processing

### Fallbacks

- WhatsApp send fails → Task retries
- AI Service unavailable → Escalation message
- Database down → 500 error, alerts

## Performance Targets

- API response: <200ms (p95)
- Auto-reply generation: <5s
- Webhook processing: <100ms
- Vector search: <500ms (p95)

## Monitoring Stack (Future)

```
Prometheus (metrics)
    ├─ Request latency
    ├─ Task completion rate
    ├─ DB connection pool
    └─ Queue depth

Grafana (dashboards)
    ├─ System health
    ├─ Message throughput
    ├─ Error rates
    └─ AI response quality

ELK Stack (logging)
    ├─ Application logs
    ├─ Task execution logs
    ├─ Error tracking
    └─ Audit trail queries
```

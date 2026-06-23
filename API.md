# API Documentation

Base URL: `http://localhost:8000/api/v1`

All endpoints (except `/auth/login` and webhook verification) require JWT authentication in the `Authorization` header:

```
Authorization: Bearer <token>
```

## Authentication

### Login

```http
POST /auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "your_password"
}
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

## Information Endpoints

### Get Tenant Information

```http
GET /api/v1/info/tenant
```

Response:
```json
{
  "business_name": "My Law Firm",
  "professional_name": "Jane Smith",
  "whatsapp_number": "+1234567890",
  "auto_reply_delay_minutes": 30,
  "booking_url": "https://example.com/booking",
  "office_hours_en": "Mon-Fri 9:00-17:00 CET",
  "office_hours_ru": "Пн-Пт 9:00-17:00 CET",
  "office_hours_it": "Lun-Ven 9:00-17:00 CET",
  "disclaimer": "This is an automated assistant. This message is not legal advice.",
  "enable_auto_appointment": true,
  "appointment_api_type": "google_calendar",
  "appointment_default_duration": 30
}
```

The response includes appointment automation settings:
- `enable_auto_appointment`: Whether automatic appointment creation is enabled
- `appointment_api_type`: Type of calendar service (google_calendar, custom)
- `appointment_default_duration`: Default appointment duration in minutes

### Health Check

```http
GET /health
```

Response:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "business_name": "My Law Firm",
  "professional_name": "Jane Smith"
}
```

### Readiness Check

```http
GET /ready
```

Response:
```json
{
  "ready": true
}
```

## Conversations

### ⚠️ IMPORTANT: WhatsApp-Only Architecture

**All conversations must originate from WhatsApp messages.** The dashboard reflects what happens in WhatsApp, not the other way around.

Conversations are automatically created when a client sends the first message via WhatsApp Business API webhook. This ensures:
- Single source of truth (WhatsApp)
- Accurate audit trail tied to actual messages
- Compliance with message history
- No artificial/inconsistent conversations

### List Conversations

```http
GET /api/v1/conversations?skip=0&limit=50
```

Response:
```json
[
  {
    "id": "conv_abc123",
    "client_phone": "+1987654321",
    "status": "active",
    "last_client_message_at": "2024-01-15T10:30:00Z",
    "last_professional_message_at": null,
    "last_ai_message_at": "2024-01-15T10:35:00Z",
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-01-15T10:35:00Z"
  }
]
```

### Create Conversation (Testing Only ⚠️)

```http
POST /api/v1/conversations
Content-Type: application/json

{
  "client_phone": "+1987654321"
}
```

**⚠️ WARNING:** This endpoint is for development/testing only. In production:
- Conversations are automatically created by WhatsApp webhook
- Manual conversation creation breaks audit trail
- Dashboard should not create conversations
- Use WhatsApp simulator or real WhatsApp to test message flow

Response: `201 Created`
```json
{
  "id": "conv_abc123",
  "client_phone": "+1987654321",
  "status": "active",
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z"
}
```

**For testing**, preferred flow:
1. Use WhatsApp Business Simulator: https://developers.facebook.com/
2. Send test message to webhook
3. Conversation auto-created in database
4. Appears in dashboard automatically

### Get Conversation with Messages

```http
GET /api/v1/conversations/{conversation_id}
```

Response:
```json
{
  "id": "conv_abc123",
  "client_phone": "+1987654321",
  "status": "active",
  "messages": [
    {
      "id": "msg_001",
      "sender": "client",
      "content": "Hi, I need help with...",
      "media_type": null,
      "transcript": null,
      "detected_intent": "legal_question",
      "is_auto_reply": false,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### Get Messages

```http
GET /api/v1/conversations/{conversation_id}/messages?skip=0&limit=100
```

### Update Conversation

```http
PUT /api/v1/conversations/{conversation_id}
Content-Type: application/json

{
  "status": "closed"
}
```

### Get Conversation Summary

```http
GET /api/v1/conversations/{conversation_id}/summary
```

Response:
```json
{
  "conversation_id": "conv_abc123",
  "client_phone": "+1987654321",
  "status": "active",
  "total_messages": 5,
  "client_messages": 2,
  "ai_messages": 2,
  "professional_messages": 1,
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:35:00Z"
}
```

## Appointments

### Create Appointment

**Requires**: `TENANT_ENABLE_AUTO_APPOINTMENT=true` in environment

```http
POST /api/v1/appointments
Content-Type: application/json
Authorization: Bearer <token>

{
  "client_phone": "+1987654321",
  "client_name": "John Smith",
  "preferred_date": "2024-01-20",
  "preferred_time": "14:00",
  "notes": "Interested in consultation"
}
```

Response: `200 OK`
```json
{
  "appointment_id": "appt_abc123",
  "client_phone": "+1987654321",
  "scheduled_at": "2024-01-20T14:00:00Z",
  "confirmation_url": "https://calendar.example.com/appt/abc123",
  "status": "confirmed",
  "message": "Your appointment has been scheduled! You'll receive a confirmation at +1987654321."
}
```

**Response Status Values**:
- `confirmed`: Appointment successfully created
- `pending`: Appointment request submitted, awaiting confirmation
- `failed`: Appointment creation failed

**Note**: When `TENANT_ENABLE_AUTO_APPOINTMENT=false`, this endpoint returns `400 Bad Request`.

**Appointment API Types**:
- `google_calendar`: Creates events directly in Google Calendar (requires service account credentials) - RECOMMENDED
- `custom`: Posts appointment data to custom API endpoint

## Documents

### Upload Document

```http
POST /api/v1/documents
Content-Type: multipart/form-data

file: <binary file>
section_title: "FAQ"
```

Response: `201 Created`
```json
{
  "id": "doc_abc123",
  "filename": "faq.pdf",
  "file_type": "pdf",
  "file_size_bytes": 102400,
  "section_title": "FAQ",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### List Documents

```http
GET /api/v1/documents?skip=0&limit=50
```

Response:
```json
[
  {
    "id": "doc_abc123",
    "filename": "faq.pdf",
    "file_type": "pdf",
    "file_size_bytes": 102400,
    "section_title": "FAQ",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

### Get Document

```http
GET /api/v1/documents/{document_id}
```

### Toggle Document Status

```http
PATCH /api/v1/documents/{document_id}
Content-Type: application/json

{
  "is_active": false
}
```

### Delete Document

```http
DELETE /api/v1/documents/{document_id}
```

Response: `204 No Content`

## WhatsApp Webhooks

### Verify Webhook

WhatsApp sends a GET request:

```http
GET /api/v1/webhooks/whatsapp?hub.mode=subscribe&hub.challenge=<challenge>&hub.verify_token=<token>
```

Response returns the challenge string if token matches.

### Receive Message

WhatsApp sends POST requests when messages arrive:

```http
POST /api/v1/webhooks/whatsapp
Content-Type: application/json

{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "changes": [
        {
          "value": {
            "messaging_product": "whatsapp",
            "contacts": [
              {
                "profile": { "name": "John" },
                "wa_id": "1987654321"
              }
            ],
            "messages": [
              {
                "from": "1987654321",
                "type": "text",
                "text": { "body": "Hello" }
              }
            ]
          }
        }
      ]
    }
  ]
}
```

Response:
```json
{
  "status": "ok"
}
```

## Error Responses

### 401 Unauthorized

```json
{
  "detail": "Not authenticated"
}
```

### 404 Not Found

```json
{
  "detail": "Conversation not found"
}
```

### 422 Validation Error

```json
{
  "detail": [
    {
      "loc": ["body", "client_phone"],
      "msg": "value is not a valid phone number",
      "type": "value_error"
    }
  ]
}
```

## API Examples

### cURL

```bash
# Get tenant info
curl http://localhost:8000/api/v1/info/tenant \
  -H "Authorization: Bearer $TOKEN"

# List conversations
curl http://localhost:8000/api/v1/conversations \
  -H "Authorization: Bearer $TOKEN"

# Create appointment (if enabled)
curl -X POST http://localhost:8000/api/v1/appointments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "client_phone": "+1987654321",
    "client_name": "John Smith",
    "preferred_date": "2024-01-20",
    "preferred_time": "14:00"
  }'

# Upload document
curl -X POST http://localhost:8000/api/v1/documents \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@document.pdf" \
  -F "section_title=FAQ"

# Update conversation status
curl -X PUT http://localhost:8000/api/v1/conversations/conv_abc123 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "closed"}'
```

### Python

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Login
response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"username": "admin", "password": "your_password"}
)
token = response.json()["access_token"]

headers = {"Authorization": f"Bearer {token}"}

# Get tenant info
response = requests.get(f"{BASE_URL}/info/tenant", headers=headers)
tenant = response.json()
print(f"Business: {tenant['business_name']}")
print(f"Auto-appointment enabled: {tenant['enable_auto_appointment']}")

# List conversations
response = requests.get(f"{BASE_URL}/conversations", headers=headers)
conversations = response.json()
print(f"Total conversations: {len(conversations)}")

# Create appointment (if enabled)
if tenant['enable_auto_appointment']:
    response = requests.post(
        f"{BASE_URL}/appointments",
        headers=headers,
        json={
            "client_phone": "+1987654321",
            "client_name": "John Smith",
            "preferred_date": "2024-01-20",
            "preferred_time": "14:00"
        }
    )
    appointment = response.json()
    print(f"Appointment created: {appointment['appointment_id']}")

# Upload document
with open("faq.pdf", "rb") as f:
    files = {"file": f}
    data = {"section_title": "FAQ"}
    response = requests.post(
        f"{BASE_URL}/documents",
        headers=headers,
        files=files,
        data=data
    )
print(f"Uploaded: {response.json()['filename']}")
```

## Configuration

All professional information is configured via environment variables - no API endpoints for tenant management. This keeps the system simple and secure for single-tenant deployments.

To change configuration:
1. Edit `.env`
2. Restart backend: `docker-compose restart backend`
3. Check with `GET /api/v1/info/tenant`

**Appointment Configuration**:
- Set `TENANT_ENABLE_AUTO_APPOINTMENT=true` to enable automatic appointment scheduling
- Configure calendar integration type: `TENANT_APPOINTMENT_API_TYPE` (google_calendar, custom)
- Provide API credentials if needed: `TENANT_APPOINTMENT_API_KEY`, `TENANT_APPOINTMENT_API_URL`
- When client sends appointment request message, AI automatically attempts to schedule if enabled

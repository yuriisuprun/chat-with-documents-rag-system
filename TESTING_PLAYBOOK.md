# Testing Playbook
## Complete Testing Guide for WhatsApp AI Auto-Responder

---

## ✅ Status Update (June 25, 2026)

**Test Endpoint is NOW WORKING!** ✅

The test message endpoint (`POST /api/v1/webhooks/whatsapp/test-message`) has been successfully implemented and verified working. All 3 test messages have been successfully processed and stored in the database.

**Known Phone Number for Testing:** `+393513082792`

See **Test 4.2** below for verified working examples.

---

## 🎯 Testing Objectives

This document provides step-by-step instructions for comprehensive testing:

1. **Local Environment Verification** - Ensure all services are running
2. **Basic Functionality Testing** - Test core features work as expected
3. **AI Response Testing** - Verify response quality and intent detection
4. **Multi-Language Testing** - Test language detection and responses (if configured)
5. **Error Handling** - Test error scenarios and edge cases
6. **Performance Testing** - Verify response times and system stability

---

## Prerequisites

Before testing, ensure:

- ✅ All services running: `docker-compose ps` (all should show "Up")
- ✅ Backend is healthy: `curl http://localhost:8000/health`
- ✅ Dashboard accessible: http://localhost:3000
- ✅ Can login with `admin` / `change_me_in_production`
- ✅ AI provider configured in `.env`:
  - **Ollama** (default, local/offline): No API key needed
  - **OpenAI** (if using): Valid API key in `.env`
  - **Gemini** (if using): Valid API key in `.env`

**If any of the above fail, check setup or restart services:**
```bash
docker-compose down
docker-compose up -d
docker-compose ps
```

### Publishing Note

**For testing purposes, you do NOT need to publish your app to Meta.** 
- Use test phone numbers provided by Meta (free)
- Full API access without app review
- Unlimited messages to test numbers
- Perfect for development and testing

See [WHATSAPP_APP_PUBLISHING_GUIDE.md](./WHATSAPP_APP_PUBLISHING_GUIDE.md) if you plan to deploy to production.

---

## AI Provider Selection Guide

This system supports three AI providers. Choose one based on your needs:

### Ollama (Recommended for Development)
- **Setup**: Local machine or Docker container
- **Cost**: Free
- **Speed**: Fast (local)
- **Internet**: Not required
- **Configuration**: 
  ```env
  AI_PROVIDER=ollama
  OLLAMA_BASE_URL=http://localhost:11434
  OLLAMA_MODEL=mistral
  OLLAMA_EMBEDDING_MODEL=nomic-embed-text
  ```
- **Best for**: Development, testing, offline use, no API costs

### OpenAI (Recommended for Production)
- **Setup**: Requires OpenAI API account
- **Cost**: Paid (usage-based)
- **Speed**: Fast
- **Internet**: Required
- **Configuration**:
  ```env
  AI_PROVIDER=openai
  OPENAI_API_KEY=sk-your_key_here
  OPENAI_MODEL=gpt-4
  OPENAI_EMBEDDING_MODEL=text-embedding-3-small
  ```
- **Best for**: Production, high quality responses, professional use

### Google Gemini (Alternative Cloud Option)
- **Setup**: Requires Google Cloud API account
- **Cost**: Free tier available
- **Speed**: Fast
- **Internet**: Required
- **Configuration**:
  ```env
  AI_PROVIDER=gemini
  GOOGLE_API_KEY=your_key_here
  GEMINI_MODEL=gemini-pro
  ```
- **Best for**: Budget-conscious production use, Google integration preference

**To change providers**: Update `.env` and restart backend (`docker-compose restart backend`)

---

## Test Suite 1: Environment Verification

### Test 1.1: Docker Services Status

**Objective:** Verify all required services are running

**Steps:**
```bash
# Check service status
docker-compose ps

# Expected output:
# NAME         STATUS
# backend      Up X minutes
# frontend     Up X minutes
# db           Up X minutes
# redis        Up X minutes
```

**Pass Criteria:**
- ✅ All services show "Up"
- ✅ No "Exit" or "Exited" statuses
- ✅ No port conflicts

**If failed:**
```bash
docker-compose logs | grep -i error
# Fix: See SIMPLE_SETUP_GUIDE.md troubleshooting
```

### Test 1.2: Backend Health Check

**Objective:** Verify backend API is responding

**Steps:**
```bash
# Test health endpoint
curl http://localhost:8000/health
```

**Expected Response:**
```json
{"status":"ok"}
```

**Pass Criteria:**
- ✅ HTTP 200 response
- ✅ Returns `{"status":"ok"}`

**If failed:**
```bash
docker-compose logs backend | tail -50
```

### Test 1.3: Database Connectivity

**Objective:** Verify database is accessible

**Steps:**
```bash
# Test database connection
docker-compose exec db psql -U assistant_user -d whatsapp_assistant -c "SELECT 1"

# Expected output: "1"
```

**Pass Criteria:**
- ✅ Command succeeds without error
- ✅ Returns "1"

### Test 1.4: API Accessibility

**Objective:** Verify API endpoints respond

**Steps:**
```bash
# Test API endpoint
curl http://localhost:8000/api/v1/conversations

# Should return JSON (possibly empty list)
```

**Expected Response:**
```json
[]  # or list of conversations if any exist
```

**Pass Criteria:**
- ✅ HTTP 200 response
- ✅ Valid JSON returned

---

## Test Suite 2: Dashboard & UI

### Test 2.1: Dashboard Access

**Objective:** Verify frontend loads and is usable

**Steps:**
1. Open http://localhost:3000 in your browser
2. Observe the login page

**Pass Criteria:**
- ✅ Page loads without errors
- ✅ Shows login form with "Username" and "Password" fields
- ✅ Has "Login" button

### Test 2.2: Login Functionality

**Objective:** Verify authentication works

**Steps:**
1. Enter username: `admin`
2. Enter password: `change_me_in_production`
3. Click "Login"

**Pass Criteria:**
- ✅ Successfully redirected to dashboard
- ✅ Shows sidebar with "Conversations" and "Documents"
- ✅ No error messages
- ✅ Can navigate to different tabs

**If failed:**
```bash
docker-compose logs backend | grep -i "auth"
```

### Test 2.3: Dashboard Navigation

**Objective:** Verify UI navigation works

**Steps:**
1. Click "Documents" tab
   - Should show document upload area
   - Show "Upload Document" button

2. Click "Conversations" tab
   - Should show "New Conversation" button
   - Show conversation list (empty if first time)

**Pass Criteria:**
- ✅ Can navigate between tabs without errors
- ✅ Each tab loads and displays expected content

### Test 2.4: UI Responsiveness

**Objective:** Verify UI is responsive

**Steps:**
1. In browser, open Developer Tools (F12)
2. Click "Toggle device toolbar" (mobile view)
3. Navigate between pages

**Pass Criteria:**
- ✅ UI resizes properly on mobile view
- ✅ All buttons and inputs remain accessible
- ✅ No layout breaks

---

## Test Suite 3: Document Management

### Test 3.1: Document Upload - Text File

**Objective:** Test uploading a plain text document

**Steps:**
1. Create file `test_document.txt` with content:
   ```
   OFFICE HOURS
   Monday-Friday: 9:00 AM - 5:00 PM
   Saturday: 10:00 AM - 2:00 PM
   Closed Sundays

   SERVICES
   - Initial consultation: Free
   - Document review: $150/hour
   - Legal drafting: $250/hour

   BOOKING
   https://calendar.google.com/calendar

   PRICING
   Retainer agreements: $500/month minimum
   ```

2. Go to Dashboard → Documents tab
3. Click "Upload Document"
4. Select `test_document.txt`
5. Click "Upload"

**Pass Criteria:**
- ✅ Document appears in the list
- ✅ Shows filename
- ✅ Shows upload date/time
- ✅ No error messages

### Test 3.2: Document Upload - PDF File

**Objective:** Test uploading a PDF document

**Steps:**
1. Create a simple PDF (or use existing)
   - Can use online converter: https://word2pdf.com
   
2. Go to Dashboard → Documents tab
3. Upload the PDF file

**Pass Criteria:**
- ✅ PDF uploads successfully
- ✅ Appears in document list
- ✅ Can see file size

### Test 3.3: Multiple Documents

**Objective:** Test uploading multiple documents

**Steps:**
1. Create 3 different text files with different content
2. Upload all three
3. Verify all appear in the list

**Pass Criteria:**
- ✅ All three documents appear in list
- ✅ Can distinguish between them by filename

---

## Test Suite 4: Conversation Management (WhatsApp-Only Flow)

### ⚠️ IMPORTANT: Conversation Source of Truth

**All conversations must originate from WhatsApp messages.** The dashboard reflects what happens in WhatsApp, not the other way around. This ensures:
- Single source of truth (WhatsApp Business API)
- Accurate audit trail
- Compliance with message history
- No artificial/manual conversations in production

**The "Create Conversation" API endpoint is deprecated and should only be used for testing purposes.**

### Test 4.1: Receive WhatsApp Message (Primary Flow)

**Objective:** Test conversation creation via WhatsApp webhook

**Prerequisites:**
- WhatsApp Business Account configured
- Webhook URL pointing to `/api/v1/webhooks/whatsapp`
- Test number added to WhatsApp Business Account

**Steps:**
1. Send a message to your WhatsApp Business number from test phone: `+15551234567`
   - Use WhatsApp mobile app or WhatsApp Business simulator
   - Message: `"What are your office hours?"`
2. Wait for webhook processing (usually <1 second)
3. Go to Dashboard → Conversations tab
4. Verify conversation appears with correct phone number

**Pass Criteria:**
- ✅ Conversation automatically appears in dashboard
- ✅ Phone number matches sender
- ✅ Conversation status is "active"
- ✅ Message appears with "Client" as sender
- ✅ Timestamp shows message receipt time

**If conversation doesn't appear:**
```bash
# Check webhook logs
docker-compose logs backend | grep -i "webhook\|receive_whatsapp"

# Verify webhook URL configuration
docker-compose logs backend | grep -i "whatsapp"

# Check database directly
docker-compose exec db psql -U assistant_user -d whatsapp_assistant -c "SELECT * FROM conversations;"
```

### Test 4.2: Send Test Messages (Using Test Endpoint) ✅ VERIFIED WORKING

**Objective:** Test conversation creation and message flow using test endpoint

**Prerequisites:**
- Backend running at http://localhost:8000
- Dashboard accessible at http://localhost:3000
- Already logged in with admin credentials

**🧪 Using Test Endpoint (Recommended for Development)**

This is the easiest way to test message flows without sending actual WhatsApp messages.

**Option A: Using cURL (Command Line)**

**Steps:**
1. Open command prompt/terminal
2. Send 3 messages in sequence using the test endpoint:

```bash
# Message 1: Simple greeting
curl "http://localhost:8000/api/v1/webhooks/whatsapp/test-message?phone_number=%2B393513082792&message_text=Hello" -X POST

# Message 2: Help request  
curl "http://localhost:8000/api/v1/webhooks/whatsapp/test-message?phone_number=%2B393513082792&message_text=I%20need%20help" -X POST

# Message 3: Appointment request
curl "http://localhost:8000/api/v1/webhooks/whatsapp/test-message?phone_number=%2B393513082792&message_text=Can%20you%20schedule%20an%20appointment%3F" -X POST
```

**For PowerShell (Windows):**
```powershell
# Message 1: Simple greeting
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/webhooks/whatsapp/test-message?phone_number=%2B393513082792&message_text=Hello" -Method Post

# Message 2: Help request
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/webhooks/whatsapp/test-message?phone_number=%2B393513082792&message_text=I%20need%20help" -Method Post

# Message 3: Appointment request
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/webhooks/whatsapp/test-message?phone_number=%2B393513082792&message_text=Can%20you%20schedule%20an%20appointment%3F" -Method Post
```

3. After each request, observe:
   - Response should include `conversation_id` and `message_id`
   - Status should be `"ok"`
   - Check console logs: `docker-compose logs -f backend`

**Expected Response (Verified Working):**
```json
{
  "status": "ok",
  "message": "Test message processed successfully",
  "conversation_id": "conv_test001",
  "message_id": "msg_0fc9ab4a5566",
  "phone_number": "+393513082792",
  "detected_language": "en",
  "detected_intent": "other",
  "auto_reply_in_seconds": 1800
}
```

**Note:** `auto_reply_in_seconds` is 1800 (30 minutes) based on your `.env` setting:
```env
TENANT_AUTO_REPLY_DELAY_MINUTES=30
```

**Option B: Using Postman**

1. Download and open Postman
2. Create new POST request to:
   ```
   http://localhost:8000/api/v1/webhooks/whatsapp/test-message
   ```
3. Add Query Params:
   - `phone_number`: `+393513082792` (or your actual phone number)
   - `message_text`: `Hello`
4. Click Send
5. Repeat with different messages

**Option C: Using Python Script**

Create file `test_messages.py`:
```python
import requests
import time

BASE_URL = "http://localhost:8000/api/v1/webhooks/whatsapp/test-message"

# Test sequence - use your actual phone number
messages = [
    ("Hello", "+393513082792"),
    ("I need help", "+393513082792"),
    ("Can you schedule an appointment?", "+393513082792"),
]

for message_text, phone_number in messages:
    response = requests.post(
        BASE_URL,
        params={
            "phone_number": phone_number,
            "message_text": message_text
        }
    )
    print(f"Message: {message_text}")
    print(f"Response: {response.json()}")
    print("---")
    time.sleep(1)  # Wait 1 second between messages
```

Run with: `python test_messages.py`

**Database Verification (Verified Working):**

Check messages directly in database:
```bash
docker-compose exec db psql -U assistant_user -d whatsapp_assistant -c \
  "SELECT id, content, sender, detected_language, detected_intent FROM messages \
   WHERE conversation_id = 'conv_test001' ORDER BY created_at;"
```

**Actual Test Results (June 25, 2026):**
```
                id        |             content              | sender | detected_language | detected_intent
------------------+----------------------------------+--------+-----------+--------+-----------------
 msg_eb8203fc222f | Can you schedule an appointment? | client | en        | other
 msg_b4601f23707c | I need help                      | client | en        | other
 msg_0fc9ab4a5566 | Hello                            | client | en        | other
(3 rows)
```

**Dashboard Verification:**

1. Open Dashboard: http://localhost:3000
2. Refresh the page or wait for auto-updates
3. Go to "Conversations" tab
4. Click on conversation with phone number `+393513082792`

**Pass Criteria (✅ All Verified):**
- ✅ All 3 messages appear automatically in the list
- ✅ Conversation shows phone number `+393513082792`
- ✅ Messages in chronological order (Hello → I need help → Can you schedule?)
- ✅ Each message shows timestamp
- ✅ Each message shows "client" as sender
- ✅ Message content is exactly what you sent
- ✅ Database stores messages with correct lowercase enum values
- ✅ Auto-reply scheduled for 30 minutes from now

**If messages don't appear:**
```bash
# Check backend logs
docker-compose logs backend | tail -50

# Verify database has messages
docker-compose exec db psql -U assistant_user -d whatsapp_assistant -c "SELECT * FROM messages LIMIT 5;"

# Check conversation exists
docker-compose exec db psql -U assistant_user -d whatsapp_assistant -c "SELECT * FROM conversations LIMIT 5;"
```

**Known Issue - RESOLVED ✅**

Previous issue: Enum values were being stored as uppercase ('CLIENT', 'OTHER') causing PostgreSQL enum validation errors.

**Solution Applied:** Changed ORM model columns from `SQLEnum(MessageSender)` to plain `String` columns, bypassing SQLAlchemy's enum type conversion that was causing the uppercase serialization.

---

### Test 4.2b: Dashboard Reflects Real WhatsApp State

**Objective:** Verify dashboard is read-only reflection of WhatsApp

**Steps (Real WhatsApp - Optional):**
1. If you have actual WhatsApp Business Account set up:
   - Send 3 messages from test phone in sequence:
   - Message 1: `"Hello"`
   - Message 2: `"I need help"`
   - Message 3: `"Can you schedule an appointment?"`
2. Each message arrives ~1-5 seconds apart
3. Refresh dashboard or watch for auto-updates
4. Verify all 3 messages appear in correct order

**Pass Criteria:**
- ✅ All messages appear automatically
- ✅ Messages in chronological order
- ✅ No manual dashboard input needed
- ✅ Each message shows timestamp
- ✅ Sender correctly identified as "Client"

### Test 4.3: AI Auto-Reply Generation

**Objective:** Test AI response generation after delay

**Setup:**
- Upload document with office hours (Test 3.1)
- Ensure `TENANT_AUTO_REPLY_DELAY_MINUTES=2` in `.env`

**Steps:**
1. Send message from WhatsApp: `"What are your office hours?"`
2. Conversation automatically created in dashboard
3. Message appears immediately
4. Wait 2+ minutes (configured delay)
5. Refresh dashboard or monitor for updates

**Pass Criteria:**
- ✅ After delay, AI response appears as "AI" sender
- ✅ Response is relevant to office hours question
- ✅ Response includes disclaimer (if configured)
- ✅ Response sent back to WhatsApp
- ✅ Check WhatsApp phone: message received on test number

**If no auto-reply:**
```bash
# Check if Celery worker is running
docker-compose logs celery_worker | tail -50

# Verify task was scheduled
docker-compose logs backend | grep "auto_reply"

# Check Redis queue
docker-compose exec redis redis-cli LLEN celery
```

### Test 4.4: Message List View

**Objective:** Test viewing complete message history

**Steps:**
1. In dashboard, click on a conversation with multiple messages
2. Observe all messages displayed with full history
3. Use pagination if available

**Pass Criteria:**
- ✅ All messages show in chronological order
- ✅ Client messages show with "Client" sender
- ✅ AI messages show with "AI" sender
- ✅ Professional messages (if any) show with "Professional" sender
- ✅ Each message shows timestamp
- ✅ Messages easily distinguishable by sender and style

---

## Test Suite 5: AI Response Generation

### Test 5.1: Auto-Reply Generation

**Objective:** Test AI automatically generates response after delay

**Setup:**
- Uploaded test document with office hours (Test 3.1)
- Created conversation with test message (Test 4.2)
- Set `TENANT_AUTO_REPLY_DELAY_MINUTES=2` in `.env`

**Steps:**
1. Note the current time
2. Send message: `"What are your office hours?"`
3. Wait 2 minutes (or configured delay)
4. Refresh page or wait for auto-refresh
5. Check if AI response appears

**Pass Criteria:**
- ✅ AI response appears after delay
- ✅ Response is relevant to the message
- ✅ References office hours from document
- ✅ Response is in English (if configured)

**If no response after 5 minutes:**
```bash
# Check worker logs
docker-compose logs backend | grep -i "celery\|task"
```

### Test 5.2: Response Quality - Different Message Types

**Objective:** Test AI handles different message types appropriately

**Test Cases:**

**Case 1: Office Hours Query**
```
Message: "When are you open?"
Expected: AI should respond with office hours from uploaded document
```

**Case 2: Pricing Query**
```
Message: "How much do you charge?"
Expected: AI should respond with pricing information from document
```

**Case 3: Appointment Request**
```
Message: "I need an appointment tomorrow at 2pm"
Expected: AI should offer to help schedule or ask for more details
```

**Case 4: Out-of-Scope Question**
```
Message: "Can you help me sue someone?"
Expected: AI should decline and suggest professional consultation
```

**Case 5: General Question**
```
Message: "Do you speak English?"
Expected: AI should confirm and offer assistance
```

**Steps for each test case:**
1. Create new conversation or use existing
2. Add message
3. Wait for auto-reply (2 minutes by default)
4. Review response quality

**Pass Criteria:**
- ✅ Responses are relevant and helpful
- ✅ Responses reference information from documents when applicable
- ✅ Responses follow professional tone
- ✅ Responses include disclaimer (if configured)
- ✅ Out-of-scope questions are appropriately declined

### Test 5.3: Response Timing

**Objective:** Verify response generation takes reasonable time

**Steps:**
1. Monitor logs while waiting for response:
   ```bash
   docker-compose logs -f backend
   ```
2. Note time from message to response
3. Check response appears within 2-5 minutes (depending on delay)

**Pass Criteria:**
- ✅ Response generation takes < 30 seconds (after delay period)
- ✅ No timeouts in logs
- ✅ Response appears within reasonable time

---

## Test Suite 6: Multi-Language Support (Optional)

**Prerequisites:** Multi-language configured in `.env`
```env
# Supported languages (ISO 639-1 codes)
SUPPORTED_LANGUAGES=en,ru,it

# Language-specific office hours
TENANT_OFFICE_HOURS_EN=Mon-Fri 9:00-17:00 CET
TENANT_OFFICE_HOURS_RU=Пн-Пт 9:00-17:00 CET
TENANT_OFFICE_HOURS_IT=Lun-Ven 9:00-17:00 CET

# Language-specific disclaimers
TENANT_DISCLAIMER_EN=This is an automated assistant. This message is not professional advice.
TENANT_DISCLAIMER_RU=Это автоматический помощник. Это сообщение не является профессиональной консультацией.
TENANT_DISCLAIMER_IT=Questo è un assistente automatico. Questo messaggio non è una consulenza professionale.

# Default language
TENANT_DEFAULT_LANGUAGE=en
```

### Test 6.1: English Message

**Steps:**
1. Send message in English: `"What are your office hours?"`
2. Wait for response
3. Verify response is in English

**Pass Criteria:**
- ✅ Response generated in English
- ✅ Uses `TENANT_OFFICE_HOURS_EN` if configured
- ✅ Includes `TENANT_DISCLAIMER_EN`

### Test 6.2: Russian Message

**Steps:**
1. Send message in Russian: `"Какие у вас часы работы?"`
2. Wait for response
3. Verify response is in Russian

**Pass Criteria:**
- ✅ Language detected as Russian
- ✅ Response generated in Russian
- ✅ Uses `TENANT_OFFICE_HOURS_RU` if configured
- ✅ Includes `TENANT_DISCLAIMER_RU`

### Test 6.3: Italian Message

**Steps:**
1. Send message in Italian: `"Quali sono i vostri orari di ufficio?"`
2. Wait for response
3. Verify response is in Italian

**Pass Criteria:**
- ✅ Language detected as Italian
- ✅ Response generated in Italian
- ✅ Uses `TENANT_OFFICE_HOURS_IT` if configured
- ✅ Includes `TENANT_DISCLAIMER_IT`

### Test 6.4: Unsupported Language Fallback

**Setup:**
```env
SUPPORTED_LANGUAGES=en,ru,it
TENANT_DEFAULT_LANGUAGE=en
```

**Steps:**
1. Send message in unsupported language (e.g., French): `"Quelles sont vos heures de travail?"`
2. Wait for response
3. Observe fallback behavior

**Pass Criteria:**
- ✅ Response generated in default language (`TENANT_DEFAULT_LANGUAGE`)
- ✅ System falls back gracefully to English
- ✅ No error thrown

---

## Test Suite 7: Appointment Automation (Optional Feature)

**Prerequisites:** Feature is enabled in `.env`
```env
TENANT_ENABLE_AUTO_APPOINTMENT=true
TENANT_APPOINTMENT_API_TYPE=google_calendar

# For Google Calendar:
TENANT_APPOINTMENT_API_KEY=<your_service_account_json>

# For Custom API:
# TENANT_APPOINTMENT_API_TYPE=custom
# TENANT_APPOINTMENT_API_URL=https://api.example.com/appointments

# Appointment settings
TENANT_APPOINTMENT_DEFAULT_DURATION=60
TENANT_APPOINTMENT_WORKING_HOURS_START=9      # 9 AM
TENANT_APPOINTMENT_WORKING_HOURS_END=17       # 5 PM
TENANT_BOOKING_URL=https://calendar.google.com
```

### Test 7.1: Appointment Request Detection

**Objective:** Test system detects appointment requests

**Setup:**
- Upload document mentioning booking link (Test 3.1)
- Enable appointment automation in `.env`
- Restart backend

**Steps:**
1. Send message: `"I'd like to schedule an appointment for tomorrow at 2pm"`
2. Wait for response (2 minutes default)

**Pass Criteria:**
- ✅ System detects appointment request (intent detection)
- ✅ Extracts date/time information if possible
- ✅ Generates appropriate response
- ✅ Includes booking link or confirmation if appointment created

### Test 7.2: Automatic Appointment Creation (Google Calendar)

**Objective:** Test automatic appointment creation with Google Calendar

**Setup:**
```env
TENANT_ENABLE_AUTO_APPOINTMENT=true
TENANT_APPOINTMENT_API_TYPE=google_calendar
TENANT_APPOINTMENT_API_KEY=<service_account_json>
```

**Steps:**
1. Send clear appointment request: `"Can I book a 1-hour consultation next Monday at 10am?"`
2. Wait for auto-reply (2 minutes default)
3. Check Google Calendar for new event

**Pass Criteria:**
- ✅ Appointment created in Google Calendar
- ✅ Event title shows client and purpose
- ✅ Correct date and time in calendar
- ✅ Duration matches `TENANT_APPOINTMENT_DEFAULT_DURATION`
- ✅ Response sent to client via WhatsApp
- ✅ Response includes appointment confirmation details

### Test 7.3: Appointment Fallback to Booking Link

**Objective:** Test fallback to booking link when auto-creation fails

**Setup:**
```env
TENANT_ENABLE_AUTO_APPOINTMENT=true
TENANT_BOOKING_URL=https://calendar.google.com/calendar/u/0/r
```

**Steps:**
1. Send ambiguous appointment request: `"Can you fit me in sometime soon?"`
2. Wait for response
3. Observe fallback behavior

**Pass Criteria:**
- ✅ System cannot auto-create (insufficient detail)
- ✅ Response includes booking link from `TENANT_BOOKING_URL`
- ✅ Client gets helpful response with self-service option
- ✅ No errors in logs

### Test 7.4: Appointment Outside Working Hours

**Objective:** Test handling of after-hours appointment requests

**Setup:**
```env
TENANT_APPOINTMENT_WORKING_HOURS_START=9
TENANT_APPOINTMENT_WORKING_HOURS_END=17
```

**Steps:**
1. Note current time (simulate off-hours for test)
2. Send appointment request for 8 PM: `"Can I book at 8 PM today?"`
3. Wait for response

**Pass Criteria:**
- ✅ System recognizes time is outside working hours
- ✅ Response redirects to booking link or next available time
- ✅ No appointment created for that time slot
- ✅ Graceful message to client

### Test 7.5: Appointment Confirmation Message Customization

**Objective:** Test custom confirmation message

**Setup:**
```env
TENANT_APPOINTMENT_CONFIRMATION_MESSAGE=Thank you! Your appointment is confirmed. We'll see you then. Reply with any questions.
```

**Steps:**
1. Create appointment via WhatsApp
2. Observe confirmation message sent to client

**Pass Criteria:**
- ✅ Custom message used instead of default
- ✅ Message is sent via WhatsApp
- ✅ No errors in logs

**If not set:** Uses default confirmation message automatically

---

## Test Suite 8: Error Handling

### Test 7.1: Invalid Phone Number

**Objective:** Test system handles invalid phone numbers

**Steps:**
1. Try to create conversation with invalid phone: `invalid123`
2. Observe error handling

**Pass Criteria:**
- ✅ Shows user-friendly error message
- ✅ Doesn't crash
- ✅ Allows user to correct and retry

### Test 7.2: Missing AI Provider Configuration

**Objective:** Test system handles missing AI provider setup gracefully

**Setup - if using OpenAI:**
```
AI_PROVIDER=openai
OPENAI_API_KEY=  # Empty or missing
```

**Setup - if using Ollama:**
```
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434  # Must be running
OLLAMA_MODEL=mistral
```

**Steps:**
1. Ensure AI provider is misconfigured (or service unavailable)
2. Try to send message
3. Observe error handling

**Pass Criteria:**
- ✅ Shows meaningful error in logs
- ✅ Dashboard still works
- ✅ Graceful degradation (returns escalation message)

**To restore:** 
- For Ollama: Ensure ollama service is running
- For OpenAI: Add valid API key and restart backend
- For Gemini: Add valid API key and restart backend

### Test 7.3: Large Document Upload

**Objective:** Test system handles large files

**Steps:**
1. Create large text file (10+ MB)
2. Try to upload
3. Observe behavior

**Pass Criteria:**
- ✅ Either succeeds or shows clear error
- ✅ Doesn't crash system
- ✅ Shows progress if uploading

### Test 7.4: Rapid Message Sending

**Objective:** Test system handles rapid requests

**Steps:**
1. Send 5 messages in quick succession
2. Wait for responses

**Pass Criteria:**
- ✅ All messages are processed
- ✅ Responses generated for all (in order)
- ✅ System doesn't crash or lag excessively

---

## Test Suite 9: API Testing

### Test 8.1: Get All Conversations

**Steps:**
```bash
curl http://localhost:8000/api/v1/conversations
```

**Expected Response:**
```json
[
  {
    "phone_number": "+15551234567",
    "message_count": 2,
    "last_message_time": "2024-06-22T10:30:00Z"
  }
]
```

**Pass Criteria:**
- ✅ HTTP 200 response
- ✅ Returns list of conversations
- ✅ Each has required fields

### Test 8.2: Get Specific Conversation

**Steps:**
```bash
curl http://localhost:8000/api/v1/conversations/+15551234567
```

**Expected Response:**
```json
{
  "phone_number": "+15551234567",
  "messages": [
    {
      "text": "What are your office hours?",
      "sender": "client",
      "timestamp": "2024-06-22T10:30:00Z"
    }
  ]
}
```

**Pass Criteria:**
- ✅ HTTP 200 response
- ✅ Shows conversation details
- ✅ Shows message history

### Test 8.3: Get Documents

**Steps:**
```bash
curl http://localhost:8000/api/v1/documents
```

**Expected Response:**
```json
[
  {
    "id": "doc-123",
    "filename": "test_document.txt",
    "uploaded_at": "2024-06-22T10:00:00Z"
  }
]
```

**Pass Criteria:**
- ✅ HTTP 200 response
- ✅ Lists all uploaded documents

### Test 8.4: Get Tenant Info

**Steps:**
```bash
curl http://localhost:8000/api/v1/info/tenant
```

**Expected Response:**
```json
{
  "business_name": "My Professional Services",
  "professional_name": "John Doe",
  "whatsapp_number": "+1234567890"
}
```

**Pass Criteria:**
- ✅ HTTP 200 response
- ✅ Shows configured tenant information

---

## Test Suite 10: Performance & Load

### Test 9.1: Dashboard Load Time

**Objective:** Measure dashboard performance

**Steps:**
1. Open Developer Tools (F12)
2. Go to Network tab
3. Refresh http://localhost:3000
4. Note time to fully load

**Pass Criteria:**
- ✅ Initial page load < 3 seconds
- ✅ All resources load successfully
- ✅ No failed requests

### Test 9.2: API Response Time

**Objective:** Measure API performance

**Steps:**
```bash
# Measure time to respond
time curl http://localhost:8000/api/v1/conversations
```

**Pass Criteria:**
- ✅ Response time < 500ms
- ✅ Consistent performance

### Test 9.3: Database Query Performance

**Objective:** Verify database queries are efficient

**Steps:**
```bash
# Check slow queries in logs
docker-compose logs backend | grep -i "slow\|duration"
```

**Pass Criteria:**
- ✅ No slow query warnings
- ✅ Database operations complete quickly

---

## Test Execution Template

Use this template for each test:

```
TEST: [Test Name]
Objective: [What are you testing?]

Setup:
- [ ] Prerequisites met
- [ ] System ready

Steps:
1. [Step 1]
2. [Step 2]
3. [Step 3]

Expected Result:
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

Actual Result:
[What actually happened]

Status: ☐ PASS ☐ FAIL ☐ BLOCKED

Notes:
[Any observations, errors, etc.]
```

---

## Reporting Issues

When tests fail, gather information:

```bash
# 1. Collect logs
docker-compose logs backend > logs.txt

# 2. Check system status
docker-compose ps

# 3. Check resource usage
docker stats

# 4. Get environment info
echo "Environment:" && cat .env | grep -v OPENAI_API_KEY
```

Then create an issue with:
- Test case that failed
- Steps to reproduce
- Expected vs actual result
- Logs from above
- Screenshots if UI issue

---

## Test Report Template

Document your test results:

```
Test Session: [Date and Time]
Tester: [Your name]
Version: [Project version]

Environment:
- Docker version: [version]
- OS: [Windows/Mac/Linux]
- Browser: [if UI testing]

Test Suites Executed:
- [x] Suite 1: Environment Verification
- [x] Suite 2: Dashboard & UI
- [x] Suite 3: Document Management
- [ ] Suite 4: Conversation Management
- [ ] Suite 5: AI Response Generation

Results:
- Total Tests: 42
- Passed: 39
- Failed: 2
- Blocked: 1

Failed Tests:
1. Test 5.1 - Auto-Reply Generation
   Issue: Response takes > 5 minutes
   Logs: [attached]

2. Test 7.2 - Missing OpenAI Key
   Issue: Crashes instead of graceful error
   Logs: [attached]

Recommendations:
- Check API rate limits for issue #1
- Add better error handling for issue #2
```

---

## Automation

To automate testing, see [CONTRIBUTING.md](./CONTRIBUTING.md) for CI/CD setup.

---

## Quick Test Checklist

**5-minute verification that everything works:**

- [ ] `docker-compose ps` shows all services up
- [ ] `curl http://localhost:8000/health` returns ok
- [ ] Login to http://localhost:3000 successful
- [ ] AI provider configured correctly (`AI_PROVIDER` set and validated)
- [ ] Can upload a document
- [ ] Can create a conversation via WhatsApp webhook
- [ ] Can add a message
- [ ] Response appears after configured delay (default 2 minutes)
- [ ] Multi-language responses work (if configured)
- [ ] Appointment automation enabled and test booking works (if feature enabled)

If all checks pass ✅, your setup is working!

---

## Quick Message Testing Guide

**Send test messages quickly to verify everything works:**

### Using Test Endpoint (✅ Verified Working)

**Windows CMD:**
```cmd
REM Message 1
curl "http://localhost:8000/api/v1/webhooks/whatsapp/test-message?phone_number=%%2B393513082792&message_text=Hello" -X POST

REM Message 2
curl "http://localhost:8000/api/v1/webhooks/whatsapp/test-message?phone_number=%%2B393513082792&message_text=I%%20need%%20help" -X POST

REM Message 3
curl "http://localhost:8000/api/v1/webhooks/whatsapp/test-message?phone_number=%%2B393513082792&message_text=Can%%20you%%20schedule%%20an%%20appointment%%3F" -X POST
```

**Windows PowerShell:**
```powershell
# Message 1
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/webhooks/whatsapp/test-message?phone_number=%2B393513082792&message_text=Hello" -Method Post

# Message 2
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/webhooks/whatsapp/test-message?phone_number=%2B393513082792&message_text=I%20need%20help" -Method Post

# Message 3
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/webhooks/whatsapp/test-message?phone_number=%2B393513082792&message_text=Can%20you%20schedule%20an%20appointment%3F" -Method Post
```

**Linux/Mac:**
```bash
# Message 1
curl "http://localhost:8000/api/v1/webhooks/whatsapp/test-message?phone_number=%2B393513082792&message_text=Hello" -X POST

# Message 2
curl "http://localhost:8000/api/v1/webhooks/whatsapp/test-message?phone_number=%2B393513082792&message_text=I%20need%20help" -X POST

# Message 3
curl "http://localhost:8000/api/v1/webhooks/whatsapp/test-message?phone_number=%2B393513082792&message_text=Can%20you%20schedule%20an%20appointment%3F" -X POST
```

**Then verify:**
1. Check dashboard: http://localhost:3000 (refresh if needed)
2. Should see conversation with phone `+393513082792`
3. Should see all 3 messages in order
4. Wait 30+ minutes for auto-reply (based on `TENANT_AUTO_REPLY_DELAY_MINUTES=30`)

**Verify in Database:**
```bash
docker-compose exec db psql -U assistant_user -d whatsapp_assistant -c \
  "SELECT content, sender, detected_language FROM messages \
   WHERE conversation_id = 'conv_test001' ORDER BY created_at DESC LIMIT 3;"
```

### Test Sequences

**Sequence 1: Basic Flow (5 minutes)**
```
1. Send: "Hello"
2. Send: "I need help"  
3. Send: "Can you schedule an appointment?"
4. Wait 30 minutes for AI responses (or check TENANT_AUTO_REPLY_DELAY_MINUTES setting)
5. Check dashboard for auto-reply
```

**Sequence 2: Language Detection (5 minutes)**
```
1. Send (English): "What are your office hours?"
2. Send (Russian): "Какие у вас часы работы?"
3. Send (Italian): "Quali sono i vostri orari?"
4. Wait for responses
5. Verify each response is in correct language
```

**Sequence 3: Different Intents (5 minutes)**
```
1. Send: "Hello, how are you?" (greeting)
2. Send: "How much do you charge?" (pricing inquiry)
3. Send: "Can I book an appointment?" (appointment request)
4. Verify AI responds to each appropriately
```

**Sequence 4: Multi-Phone Testing (5 minutes)**
```
1. Send from +15551234567: "Hello from first client"
2. Send from +15559876543: "Hello from second client"
3. Send from +15551234567: "Back to first client"
4. Verify dashboard shows 2 separate conversations
5. Verify message order is correct
```

---

## Troubleshooting Common Test Failures

| Test Failure | Likely Cause | Solution |
|--------------|--------------|----------|
| Services not starting | Docker issue | Restart Docker, check `docker-compose logs` |
| Can't login | Auth issue | Check admin credentials in `.env` |
| API returns 500 | Backend error | Check backend logs: `docker-compose logs backend` |
| No AI response | AI provider issue | Check AI provider config and API key validity |
| Ollama not responding | Service unavailable | Ensure Ollama running: `ollama pull mistral` then `ollama serve` |
| Document upload fails | File format | Use .txt, .pdf, or .docx files |
| Slow responses | System resources | Check `docker stats` |
| Database errors | DB not ready | Wait 60 seconds, then restart |
| Multi-language detection fails | Language not supported | Check `SUPPORTED_LANGUAGES` in `.env` |
| Appointment not created | API credentials | Verify `TENANT_APPOINTMENT_API_KEY` and permissions |
| Appointment outside hours | Time zone issue | Check `TENANT_APPOINTMENT_WORKING_HOURS_*` settings

---

**Last Updated:** June 2026  
**Version:** 2.0  
**Changes:** Updated for Ollama as primary AI provider, added multi-language support details, added Appointment Automation test suite

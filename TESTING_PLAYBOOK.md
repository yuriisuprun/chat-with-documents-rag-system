# Testing Playbook
## Complete Testing Guide for WhatsApp AI Auto-Responder

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
- ✅ OpenAI API key is valid (check in `.env`)

**If any of the above fail, see [SIMPLE_SETUP_GUIDE.md](./SIMPLE_SETUP_GUIDE.md) troubleshooting section first.**

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

### Test 4.2: Dashboard Reflects Real WhatsApp State

**Objective:** Verify dashboard is read-only reflection of WhatsApp

**Steps:**
1. Send 3 messages from test phone in sequence:
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
SUPPORTED_LANGUAGES=en,ru,it
TENANT_OFFICE_HOURS_RU=Пн-Пт: 9:00-17:00 CET
TENANT_OFFICE_HOURS_IT=Lun-Ven: 9:00-17:00 CET
```

### Test 6.1: English Message

**Steps:**
1. Send message in English: `"What are your office hours?"`
2. Wait for response
3. Verify response is in English

**Pass Criteria:**
- ✅ Response generated in English
- ✅ Uses English office hours if configured

### Test 6.2: Russian Message

**Steps:**
1. Send message in Russian: `"Какие у вас часы работы?"`
2. Wait for response
3. Verify response is in Russian

**Pass Criteria:**
- ✅ Language detected as Russian
- ✅ Response generated in Russian
- ✅ Uses Russian office hours if configured

### Test 6.3: Italian Message

**Steps:**
1. Send message in Italian: `"Quali sono i vostri orari di ufficio?"`
2. Wait for response
3. Verify response is in Italian

**Pass Criteria:**
- ✅ Language detected as Italian
- ✅ Response generated in Italian
- ✅ Uses Italian office hours if configured

---

## Test Suite 7: Error Handling

### Test 7.1: Invalid Phone Number

**Objective:** Test system handles invalid phone numbers

**Steps:**
1. Try to create conversation with invalid phone: `invalid123`
2. Observe error handling

**Pass Criteria:**
- ✅ Shows user-friendly error message
- ✅ Doesn't crash
- ✅ Allows user to correct and retry

### Test 7.2: Missing OpenAI Key

**Objective:** Test system handles missing API key

**Steps:**
1. Remove `OPENAI_API_KEY` from `.env`
2. Restart backend: `docker-compose restart backend`
3. Try to send message
4. Observe error handling

**Pass Criteria:**
- ✅ Shows meaningful error in logs
- ✅ Dashboard still works
- ✅ Graceful degradation

**To restore:** Add key back and restart backend

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

## Test Suite 8: API Testing

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

## Test Suite 9: Performance & Load

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
- [ ] Can upload a document
- [ ] Can create a conversation
- [ ] Can add a message
- [ ] Response appears after 2 minutes

If all checks pass ✅, your setup is working!

---

## Troubleshooting Common Test Failures

| Test Failure | Likely Cause | Solution |
|--------------|--------------|----------|
| Services not starting | Docker issue | Restart Docker, check `docker-compose logs` |
| Can't login | Auth issue | Check admin credentials in `.env` |
| API returns 500 | Backend error | Check backend logs: `docker-compose logs backend` |
| No AI response | OpenAI issue | Check API key validity and billing |
| Document upload fails | File format | Use .txt, .pdf, or .docx files |
| Slow responses | System resources | Check `docker stats` |
| Database errors | DB not ready | Wait 60 seconds, then restart |

---

**Last Updated:** June 2024  
**Version:** 1.0

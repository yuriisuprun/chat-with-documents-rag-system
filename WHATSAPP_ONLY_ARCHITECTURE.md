# WhatsApp-Only Architecture
## Quick Reference Guide

**TL;DR:** All conversations originate from WhatsApp webhooks. Dashboard is read-only. Use WhatsApp simulator for testing.

---

## The Golden Rule

> 💡 **Conversations start from WhatsApp. Dashboard reflects WhatsApp. Nothing else.**

---

## Message Flow

```
┌─────────────────────┐
│  WhatsApp Client    │
│  Sends Message      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  WhatsApp Business API              │
│  /api/v1/webhooks/whatsapp ✅       │
│  ↓                                  │
│  • Parse message                    │
│  • Auto-create conversation         │
│  • Store message                    │
│  • Schedule auto-reply              │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────┐
│  Database           │
│  (Single source     │
│   of truth)         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Dashboard          │
│  (Read-only view)   │
│  • Shows messages   │
│  • Shows AI replies │
│  • Cannot create    │
└─────────────────────┘
```

---

## API Endpoints

### ✅ Primary Entry Point
```
POST /api/v1/webhooks/whatsapp
```
- **Purpose:** Receive messages from WhatsApp
- **When:** Messages arrive from WhatsApp Business API
- **Auto-creates:** Conversations on first message
- **Stores:** All message metadata
- **Triggers:** Auto-reply task scheduling

### ⚠️ Testing Only
```
POST /api/v1/conversations
```
- **Purpose:** Manual conversation creation (development/testing)
- **When:** Only in test environments
- **Warning:** Breaks audit trail in production
- **Alternative:** Use WhatsApp simulator instead

---

## Frontend Behavior

### Conversations Page

**Shows:**
- ✅ List of conversations from WhatsApp
- ✅ Messages from all senders (client, AI, professional)
- ✅ Timestamps and metadata
- ✅ Helpful info banner ("Conversations start from WhatsApp")

**Does NOT Show:**
- ❌ "Create Conversation" button
- ❌ "Add Message" input
- ❌ Manual message creation UI

**Info Banner:**
- Appears when no conversations exist
- Explains: "Conversations appear automatically when clients message WhatsApp"
- Guides users to WhatsApp for starting conversations

---

## For Developers

### Testing Conversations

**❌ Wrong (Don't do this):**
```bash
# This creates a conversation NOT from WhatsApp
curl -X POST http://localhost:8000/api/v1/conversations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"client_phone": "+15551234567"}'
```

**✅ Right (Do this instead):**
```bash
# 1. Go to developers.facebook.com
# 2. Use WhatsApp Business Simulator
# 3. Send test message to webhook
# 4. Dashboard auto-updates
# 5. Conversation created automatically
```

### Code Locations

**Webhook Handler (Primary):**
- File: `backend/app/api/webhooks.py`
- Function: `receive_whatsapp_message()`
- Marker: "✅ PRIMARY ENTRY POINT FOR CONVERSATIONS"

**Conversation Management:**
- File: `backend/app/api/conversations.py`
- Function: `create_conversation()`
- Marker: "⚠️ TESTING ONLY"

**Frontend UI:**
- File: `frontend/src/pages/Conversations.tsx`
- Shows info banner for empty state
- No manual input controls

---

## For DevOps/Deployment

### Prerequisites

Before conversations will appear:

1. **Configure WhatsApp:**
   ```env
   WHATSAPP_PHONE_NUMBER_ID="123456789"
   WHATSAPP_API_VERSION="v18.0"
   WHATSAPP_WEBHOOK_VERIFY_TOKEN="your_secure_token"
   TENANT_WHATSAPP_NUMBER="+1234567890"
   ```

2. **Verify Webhook URL:**
   - Must be accessible from WhatsApp servers
   - Must support HTTPS in production
   - Test endpoint returns 200 for verification

3. **Test with Simulator:**
   ```bash
   # Send test message
   # Check backend logs for webhook processing
   # Verify conversation appears in dashboard
   ```

### Troubleshooting

| Issue | Check |
|-------|-------|
| Conversations don't appear | Check webhook logs: `docker-compose logs backend \| grep webhook` |
| Webhook returns 403 | Verify `WHATSAPP_WEBHOOK_VERIFY_TOKEN` matches |
| No auto-reply | Check Celery worker: `docker-compose logs celery_worker` |
| Database empty | Verify webhook was actually called: `docker-compose logs backend` |

---

## For QA/Testing

### Test Procedure

1. **Setup:**
   - Backend running
   - Database initialized
   - WhatsApp simulator configured

2. **Send Message:**
   - Use WhatsApp Business Simulator
   - Send: "What are your office hours?"

3. **Verify:**
   - Wait <1 second
   - Open dashboard
   - Conversation appears automatically
   - Message shows with "Client" sender

4. **Wait for Auto-Reply:**
   - Wait configured delay (default 30 min, can set to 1 min for testing)
   - Refresh dashboard
   - AI response appears with "AI" sender
   - Message sent back to WhatsApp

### Key Assertions

- ✅ Conversation never manually created (always from webhook)
- ✅ Dashboard shows only WhatsApp messages
- ✅ Message timestamps accurate
- ✅ Senders correctly identified
- ✅ Auto-reply appears after delay
- ✅ No manual input UI visible

---

## Common Questions

### Q: Can I create conversations from the dashboard?
**A:** No. Conversations must originate from WhatsApp. Use the WhatsApp simulator for testing.

### Q: What if I need to test locally without WhatsApp?
**A:** Use the `POST /api/v1/conversations` API directly (for development only). Note: This is not production-ready.

### Q: Why not allow manual conversation creation?
**A:** Keeps audit trail clean and system compliant. Ensures dashboard always reflects true WhatsApp state.

### Q: Can professional manually reply from dashboard?
**A:** No. Professional replies via WhatsApp. Dashboard shows the conversation automatically.

### Q: Where do conversations come from then?
**A:** From WhatsApp Business API webhook. Every time a client sends a message, it arrives here and auto-creates/updates the conversation.

### Q: What if WhatsApp webhook fails?
**A:** Message is never stored in dashboard. System relies on webhook success. Retry logic is automatic.

---

## Compliance & Audit Trail

### What's Tracked
```
✅ Every message from WhatsApp
✅ Message timestamp (from WhatsApp)
✅ Sender (client/professional)
✅ AI-generated responses
✅ Auto-reply task execution
✅ Language detection
✅ Intent classification
```

### What's NOT Tracked (Good)
```
❌ Manual dashboard conversation creation
❌ Fake messages added via UI
❌ Test conversations in production
```

### Why This Matters
```
Legal/Compliance:
• Audit shows only real WhatsApp conversations
• Timestamps match WhatsApp delivery
• No artificial conversations created
• Compliance-ready for legal review
```

---

## Documentation Map

| Document | Purpose | For Whom |
|----------|---------|----------|
| TESTING_PLAYBOOK.md | Step-by-step test procedures | QA, Developers |
| API.md | Endpoint documentation | Developers, DevOps |
| ARCHITECTURE.md | System design overview | Architects, Senior Devs |
| ARCHITECTURE_REFACTORING_GUIDE.md | Deep dive on design rationale | Architects |
| QUICK_FIX_CHECKLIST.md | Implementation steps | DevOps |
| PHASE_1_IMPLEMENTATION_SUMMARY.md | What changed and why | Project Leads |
| WHATSAPP_ONLY_ARCHITECTURE.md | This quick reference | Everyone |

---

## Key Files to Know

### Frontend
- `frontend/src/pages/Conversations.tsx` - Main conversation UI
- `frontend/src/api/client.ts` - API calls

### Backend
- `backend/app/api/webhooks.py` - ✅ PRIMARY ENTRY POINT
- `backend/app/api/conversations.py` - Conversation CRUD
- `backend/app/services/ai_service.py` - AI response generation
- `backend/app/services/whatsapp_service.py` - WhatsApp integration
- `backend/app/tasks.py` - Auto-reply task scheduling

### Database
- `backend/app/models.py` - Data models
- `backend/migrations/versions/001_initial_schema.py` - Database schema

---

## Quick Checklist for New Developers

- [ ] I understand webhook is PRIMARY entry point
- [ ] I understand conversations auto-create from WhatsApp
- [ ] I understand dashboard is read-only
- [ ] I know to use WhatsApp simulator for testing
- [ ] I know manual API endpoints are testing-only
- [ ] I've reviewed TESTING_PLAYBOOK.md Test 4
- [ ] I've seen the message flow diagram above
- [ ] I understand compliance implications

---

## One-Minute Summary

```
WhatsApp Message Arrives
    ↓
Webhook processes it (/api/v1/webhooks/whatsapp)
    ↓
Conversation auto-created (if first message)
    ↓
Message stored in database
    ↓
Auto-reply scheduled (if not professional-replied)
    ↓
After delay...
    ↓
AI generates response (if professional didn't reply)
    ↓
Response sent back to WhatsApp
    ↓
Dashboard shows the conversation (auto-updated)
    ↓
Professional sees on both WhatsApp AND dashboard
```

That's the flow. Everything else is just details.

---

**Version:** 1.0  
**Last Updated:** June 23, 2024  
**Status:** Complete

For more details, see the other documentation files.

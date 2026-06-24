# Comprehensive Credentials Guide
## Getting API Keys & Credentials for WhatsApp AI Auto-Responder

---

## 📋 Overview

This project requires AI and WhatsApp credentials:

| Component | Status | Cost | Time | Section |
|-----------|--------|------|------|---------|
| **AI API Key** | ✅ Required | **$0-50/mo** | 5 min | [Section 1](#1-ai-api-key-multiple-options-available) |
| **WhatsApp Business API** | ⚠️ Optional (production only) | $0 (sandbox) | 30 min | [Section 2](#2-whatsapp-business-api) |
| **Admin Credentials** | ✅ Pre-configured | - | - | [Section 3](#3-admin-credentials) |

**For local testing:** Only need AI API key (use FREE Google Gemini for testing!)
**For production:** Need AI key + WhatsApp credentials

### Free Options Available! 🎉

- ✅ **Google Gemini**: FREE API (1,000 calls/day, no credit card)
- ✅ **Local LLMs**: FREE (Ollama, offline, no API costs)
- 💰 **OpenAI**: Cheapest is $0.00015 per 1K input tokens (~$1-5/month for light testing)

See [Section 1.2](#12-option-b-google-gemini-free---recommended-for-testing) for free options!

---

## 1. AI API Key (Multiple Options Available)

### Quick Decision: Which AI Provider?

| Provider | Cost | Setup | Best For | Notes |
|----------|------|-------|----------|-------|
| **OpenAI (GPT-4)** | $0.01-0.05/request | 5 min | Production, best quality | Paid only, no free tier |
| **Google Gemini** | **FREE** (limited) | 5 min | Testing, development | Free tier: 1,000 req/day |
| **Claude (Anthropic)** | ~$0.01-0.03/request | 5 min | Good reasoning | Free trial: $5 credits |
| **Groq (Meta Llama)** | **FREE** (limited) | 5 min | Fast responses | Free tier: rate-limited |
| **Local LLMs** | **FREE** | 30 min | Offline testing | No API costs, slower |

**TL;DR for starting:**
- **Want to start immediately?** → Use Google Gemini (free)
- **Need production quality?** → Use OpenAI (paid)
- **Want to test cheap first?** → Use Groq (free tier)

---

## 1.1 Option A: OpenAI (Best Quality - Paid)

### What is it?
Your authentication token for OpenAI services:
- GPT-4 / GPT-4o for intent detection and responses
- Whisper for audio transcription
- Embeddings for knowledge base search

### Why use it?
Best quality AI responses, production-grade reliability, most accurate intent detection.

### Pricing

**Current models (2026):**
- **GPT-4o mini**: $0.00015 per 1K input tokens + $0.0006 per 1K output tokens (cheapest)
- **GPT-4o**: $0.003 per 1K input + $0.006 per 1K output
- **GPT-4.5**: Higher cost, better quality
- **Embeddings**: $0.02 per 1M tokens
- **Whisper**: $0.006 per minute

**Real-world estimates:**
- **Light testing**: $0-2/month
- **Development**: $5-15/month  
- **Small business**: $20-50/month
- **High volume**: $100-500/month

### How to Get It - OpenAI

#### Step 1: Create Account
1. Go to [https://platform.openai.com](https://platform.openai.com)
2. Click "Sign up"
3. Enter email, create password
4. Verify email

#### Step 2: Add Payment Method
1. Go to [https://platform.openai.com/account/billing/overview](https://platform.openai.com/account/billing/overview)
2. Click "Set up paid account"
3. Add credit/debit card
4. **Optional**: Set spending limits to avoid surprises

#### Step 3: Generate API Key
1. Go to [https://platform.openai.com/account/api-keys](https://platform.openai.com/account/api-keys)
2. Click **"+ Create new secret key"**
3. Name it "WhatsApp Assistant"
4. **Copy immediately!** (won't show again)

**Key format:**
```
sk-proj-aBcDefGhIjKlMnOpQrStUvWxYz123456789...
```

#### Step 4: Add to `.env`
```env
OPENAI_API_KEY=sk-proj-YOUR_FULL_KEY_HERE
```

### Monitoring & Safety

**Check spending:**
1. Go to [https://platform.openai.com/account/usage/overview](https://platform.openai.com/account/usage/overview)

**Set limits:**
1. Go to [https://platform.openai.com/account/billing/limits](https://platform.openai.com/account/billing/limits)
2. Set "Hard limit" (automatic cutoff when reached)
3. Set "Soft limit" (warning email)

⚠️ **Security:**
- Never commit key to Git
- Treat like a password
- If exposed, delete immediately and regenerate

---

## 1.2 Option B: Google Gemini (FREE - Recommended for Testing)

### ✅ FREE with no credit card required!

**Advantages:**
- ✅ Completely free
- ✅ No credit card needed
- ✅ 1,000 API calls/day free
- ✅ Good quality for testing
- ✅ Instant setup (no billing)

**Limitations:**
- ⚠️ Rate limited (1,000/day)
- ⚠️ Lower quality than GPT-4o
- ⚠️ No audio transcription (Whisper alternative needed)
- ⚠️ Slower responses

**Best for:** Development, testing, learning

### How to Get Google Gemini API Key

#### Step 1: Get Free API Key
1. Go to [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Click **"Get API Key"**
3. Click **"Create API key in new project"**
4. **Copy the key immediately**

**Key format:**
```
AIzaSy...aBcDefGhIjKlMnOpQrStUvWxYz
```

#### Step 2: Add to `.env`

⚠️ **Project uses OpenAI by default**, so we need to modify it for Gemini.

For now, you have two options:
1. **Use OpenAI** (recommended for production)
2. **Fork project** to use Gemini instead

To use Gemini, you'll need to:
1. Install additional package: `pip install google-generativeai`
2. Modify `backend/app/services/ai_service.py` to use Gemini
3. Update `.env`:
```env
GOOGLE_API_KEY=AIzaSy...aBcDefGhIjKlMnOpQrStUvWxYz
```

**Note:** This requires code modification. Consider for:
- Proof of concept
- Testing before committing to paid OpenAI
- Learning/development

---

## 1.3 Option C: Other Free/Cheap Alternatives

### Groq API (FREE - Fast)

**Free tier:**
- ✅ No credit card
- ✅ Fast inference
- ✅ Meta Llama 3 models
- ⚠️ Rate limited

**Setup:** [https://console.groq.com](https://console.groq.com)

**Cons:** 
- Requires code modification to use
- Less accurate than GPT-4o

---

### Local LLM (Completely Free - Offline)

**Options:**
- **Ollama**: Run LLMs locally
  - Setup: 15 minutes
  - Cost: $0
  - Quality: Good for testing
  - Speed: Depends on CPU

**Commands:**
```bash
# Install Ollama: https://ollama.ai
ollama pull mistral
ollama serve
```

**In code:**
```python
# Use local Ollama instead of OpenAI
# Requires modification to ai_service.py
```

---

## 1.4 Recommendation for Different Use Cases

| Use Case | Provider | Cost | Effort |
|----------|----------|------|--------|
| **Quick test** | Google Gemini (free) | $0 | 5 min |
| **Development** | Google Gemini (free) | $0 | 5 min |
| **Production** | OpenAI GPT-4o mini | $5-20/mo | 5 min |
| **High volume** | OpenAI (enterprise) | Custom | Contact sales |
| **Offline** | Local LLM | $0 | 30 min |

---

## 1.5 Setting Up OpenAI (Step by Step with Screenshots)

### Important Security Notes

⚠️ **SECURITY CRITICAL:**
- **NEVER commit this key to Git**
- **NEVER share this key with anyone**
- **NEVER expose it in client-side code**
- Treat it like a password

**If you accidentally expose it:**
1. Go to [https://platform.openai.com/account/api-keys](https://platform.openai.com/account/api-keys)
2. Delete the exposed key immediately
3. Generate a new one

### Troubleshooting OpenAI

| Problem | Solution |
|---------|----------|
| "Invalid API key" | Key doesn't start with `sk-`, regenerate |
| "Quota exceeded" | Check spending at usage/overview, upgrade if needed |
| "API unreachable" | Check [status.openai.com](https://status.openai.com) |
| "Rate limited" | Too many requests, implement retry logic |
| "Account disabled" | Check email from OpenAI, verify account |

---

## 2. WhatsApp Business API

### ⚠️ Important Notes

**For local testing:** You DON'T need these credentials. You can test the AI logic without WhatsApp.

**For production:** You NEED these credentials to send/receive real WhatsApp messages.

### What You'll Need

Three pieces of information:

| Credential | Format | Example | Source |
|-----------|--------|---------|--------|
| **Access Token** | Starts with `EAAB...` | `EAAB1234567890ABCDefGhIjKlMnOp...` | Meta Developers Console |
| **Phone Number ID** | 15-17 digits | `120362666111111` | Meta Business Manager |
| **Webhook Token** | Any string you create | `my_super_secret_token_12345` | You decide |

### How to Get WhatsApp Credentials

#### Option 1: Using Free Test Credentials (Recommended for learning)

**Requirements:**
- Facebook account
- 5 minutes

**Steps:**

1. **Go to Meta Developers**
   - Visit [https://developers.facebook.com](https://developers.facebook.com)
   - Sign in with your Facebook account
   - If first time: Accept terms and create developer account

2. **Create App**
   - Click "My Apps"
   - Click "Create App"
   - Choose app type: "Business"
   - App name: "WhatsApp Assistant"
   - Click "Create App"

3. **Add WhatsApp Product**
   - In your app dashboard, click "Add Product"
   - Search for "WhatsApp"
   - Click "Set Up"
   - Choose "WhatsApp Business Account"

4. **Get Test Credentials**
   - Go to "WhatsApp" → "Getting Started"
   - You'll see test credentials (temporary, valid 6 months)
   - Copy:
     ```
     Access Token: EAAB...
     Phone Number ID: 120362...
     ```

5. **Create Webhook Token** (you decide what this is)
   - Example: `my_test_webhook_token_12345`
   - Remember it, you'll need it later

#### Option 2: Using Real WhatsApp Business Account (for production)

**Requirements:**
- Existing Facebook Business account
- Business verification (ID, tax number, etc.)
- 30 minutes to 1 hour

**Steps:**

1. **Go to Facebook Business Manager**
   - Visit [https://business.facebook.com](https://business.facebook.com)
   - Log in with your business account

2. **Create WhatsApp Business Account**
   - Go to "Accounts" → "WhatsApp Business Accounts"
   - Click "Create Account"
   - Fill in your business details
   - Verify your business

3. **Get Credentials**
   - Go to "Accounts" → "WhatsApp Business Accounts"
   - Select your account
   - Go to "System Users"
   - Create system user with `whatsapp_business_messaging` permission
   - Generate access token for this user

4. **Get Phone Number**
   - Go to your WhatsApp account settings
   - Note your Phone Number ID
   - Format: 15-17 digits

5. **Get Webhook Token**
   - Create any random string for webhook verification
   - Example: `xyz_webhook_verification_token_2024`
   - Keep it secret

### Setting Up in Your Project

Once you have credentials, add to `.env`:

```env
WHATSAPP_ACCESS_TOKEN=EAAB1234567890ABCDefGhIjKlMnOp...
WHATSAPP_PHONE_NUMBER_ID=120362666111111
WHATSAPP_WEBHOOK_VERIFY_TOKEN=my_super_secret_token_12345
```

### Webhook Setup

When you deploy to production, you need to tell WhatsApp where to send messages:

1. **Go to WhatsApp Settings in Meta Developers Console**
2. **Webhook Configuration**
   - URL: `https://your-domain.com/api/v1/webhooks/whatsapp`
   - Verify Token: Same as `WHATSAPP_WEBHOOK_VERIFY_TOKEN`
3. **Subscribe to**
   - `messages`
   - `message_status` (optional)
4. **Test Webhook**
   - Send test message from real WhatsApp number
   - Verify you receive it

### Testing WhatsApp Integration Locally

For local testing without real WhatsApp:

1. Create test conversation in dashboard
2. Add simulated messages
3. Observe AI responses
4. No real WhatsApp number needed

### WhatsApp API Limits

**Free tier (test credentials):**
- 1,000 messages per day
- Limited to 5 test phone numbers
- Expires after 6 months

**Production tier:**
- Unlimited messages (pay per message)
- Your real phone number
- No expiration

**Typical pricing:** $0.004 - $0.01 per message (depending on region)

### Troubleshooting WhatsApp

| Problem | Solution |
|---------|----------|
| "Invalid token" | Regenerate access token in Meta console |
| "Phone number not found" | Use Phone Number ID, not the phone number itself |
| "Webhook not reachable" | Ensure domain is public (not localhost), check firewall |
| "Webhook test fails" | Verify token matches exactly |
| "Messages not delivering" | Check API rate limits, check message format |

---

## 3. Admin Credentials

### Default Credentials

These are pre-configured:

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change_me_in_production
```

### How to Change

Edit `.env`:

```env
ADMIN_USERNAME=your_username
ADMIN_PASSWORD=your_secure_password
```

Then restart backend:

```bash
docker-compose restart backend
```

### JWT Secret

For security, the system also uses a JWT secret:

```env
JWT_SECRET=your_jwt_secret_change_me_with_random_string
```

**Generate a random JWT secret:**

```bash
# On any terminal:
# Using Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Using Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"

# Using OpenSSL
openssl rand -hex 32
```

---

## 📋 Complete Credentials Checklist

### Local Testing Setup

- [ ] **AI API Key chosen** (Free Google Gemini OR paid OpenAI)
- [ ] API key obtained and added to `.env`
- [ ] Admin credentials created (or using defaults)
- [ ] `.env` file created from `.env.example`
- [ ] All other fields in `.env` filled in

**Example minimum `.env` (for testing):**
```env
# Choose ONE:
# Option A: OpenAI (paid, best quality)
OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE

# Option B: Google Gemini (free, for testing - requires code changes)
# GOOGLE_API_KEY=AIzaSy...YOUR_KEY_HERE

TENANT_BUSINESS_NAME=My Business
TENANT_PROFESSIONAL_NAME=Your Name
TENANT_WHATSAPP_NUMBER=+1234567890
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change_me_in_production
JWT_SECRET=random_string_here
```

### Production Deployment Checklist

- [ ] OpenAI API key set (with billing enabled)
- [ ] WhatsApp Access Token obtained
- [ ] WhatsApp Phone Number ID obtained
- [ ] Webhook verify token created
- [ ] Admin password changed (not default)
- [ ] JWT secret set to random string
- [ ] All multi-language settings configured
- [ ] SSL certificate obtained (for HTTPS webhook)
- [ ] Domain name points to server
- [ ] Webhook URL configured in Meta console

---

## 🔐 Security Best Practices

1. **Environment Variables Only**
   - Never hardcode credentials
   - Always use `.env` files
   - Never commit `.env` to Git

2. **Separate Dev/Prod Keys**
   - Use test API keys for development
   - Use production API keys for production
   - Different credentials per environment

3. **Key Rotation**
   - Rotate keys every 90 days
   - Delete old unused keys
   - Use temporary keys for contractor access

4. **Access Control**
   - Only give credentials to needed team members
   - Never share credentials via email/chat
   - Use secure password manager

5. **Monitoring**
   - Watch API usage for anomalies
   - Set spending alerts
   - Check access logs regularly

---

## 🆘 Common Issues & Solutions

### "Invalid credentials when starting"

```bash
# Check credentials are in .env
cat .env | grep OPENAI

# Restart after fixing
docker-compose restart backend
```

### "OpenAI says invalid API key but I just created it"

1. Wait 5 minutes for key to propagate
2. Verify key starts exactly with `sk-`
3. Check you copied the ENTIRE key
4. Try regenerating the key

### "WhatsApp webhook keeps failing"

1. Ensure `https://` (not `http://`)
2. Check domain is publicly accessible
3. Verify token matches exactly
4. Check firewall allows port 443

### "Too many OpenAI API errors"

1. Check your API quota: [https://platform.openai.com/account/billing/limits](https://platform.openai.com/account/billing/limits)
2. Check spending: [https://platform.openai.com/account/billing/usage/overview](https://platform.openai.com/account/billing/usage/overview)
3. Might have exceeded monthly quota
4. Upgrade billing or wait for next month

---

## 📚 Related Documentation

- [SIMPLE_SETUP_GUIDE.md](./SIMPLE_SETUP_GUIDE.md) - Complete setup walkthrough
- [QUICK_START.md](./QUICK_START.md) - 5-minute quick start
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Production deployment
- [API.md](./API.md) - API documentation

---

## ✅ Summary

### For Local Testing (5 minutes) - FREE Option Available!

**Option A: Start with FREE Google Gemini (Recommended)**
1. No credit card needed
2. Go to [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)
3. Click "Get API Key"
4. Add to `.env` (Note: requires code modification to use)
5. Run `docker-compose up -d`
6. Done! (Free 1,000 API calls/day)

**Option B: Use OpenAI GPT-4o mini**
1. Go to [https://platform.openai.com](https://platform.openai.com)
2. Create account, add payment method
3. Get API key from [https://platform.openai.com/account/api-keys](https://platform.openai.com/account/api-keys)
4. Add to `.env`: `OPENAI_API_KEY=sk-proj-...`
5. Run `docker-compose up -d`
6. Done! (Costs ~$0.00015 per 1K input tokens)

### For Production (30-45 minutes)

1. Complete local testing setup above with OpenAI
2. Get WhatsApp credentials from Meta Developers Console:
   - Access Token (starts with EAAB...)
   - Phone Number ID
   - Webhook verify token
3. Add to `.env`
4. Deploy to server (see DEPLOYMENT.md)
5. Configure webhook in Meta console
6. Test with real WhatsApp number

### Cost Estimate Comparison

| Scenario | Provider | Cost/Month | Setup |
|----------|----------|-----------|-------|
| **Just testing AI responses** | Google Gemini | **$0** | 5 min |
| **Development** | OpenAI GPT-4o mini | $1-5 | 5 min |
| **Small business** | OpenAI GPT-4o mini | $20-50 | 30 min |
| **High volume** | OpenAI GPT-4 | $100-500+ | 1 hour |

---

**Last Updated:** June 2024  
**Version:** 1.0

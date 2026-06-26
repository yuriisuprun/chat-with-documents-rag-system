"""WhatsApp webhook endpoints."""

import uuid
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.config import settings
from app.models import Conversation, Message, MessageSender, Intent
from app.services.whatsapp_service import WhatsAppService
from app.services.ai_service import AIService
from app.tasks import send_auto_reply, process_audio_transcription

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.get("/whatsapp")
async def verify_webhook(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
    hub_verify_token: str = Query(..., alias="hub.verify_token")
) -> str:
    """Verify WhatsApp webhook."""
    whatsapp_service = WhatsAppService()
    
    if not whatsapp_service.verify_webhook_token(hub_verify_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid verification token"
        )
    
    if hub_mode != "subscribe":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid mode"
        )
    
    return hub_challenge


@router.post("/whatsapp")
async def receive_whatsapp_message(request: Request) -> dict:
    """
    ✅ PRIMARY ENTRY POINT FOR CONVERSATIONS
    
    Receive WhatsApp messages via Meta WhatsApp Business API.
    
    This webhook is the ONLY legitimate source for creating conversations.
    Conversations are automatically created here when the first message arrives.
    
    This webhook:
    1. Parses incoming message from WhatsApp Cloud API
    2. Auto-creates conversation in database (if first message)
    3. Stores message with metadata (language, intent, etc.)
    4. Schedules auto-reply task
    5. Transcribes audio if needed
    
    Message Flow:
    Client sends message → WhatsApp API → This webhook → Database → Dashboard auto-updates
    
    Webhook format from WhatsApp Business API v18.0:
    https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/payload-examples
    """
    db = SessionLocal()
    try:
        # Parse webhook from WhatsApp Business API
        whatsapp_service = WhatsAppService()
        data = await request.json()
        
        # Log webhook receipt (but not sensitive data)
        logger.info(f"Received WhatsApp webhook event")
        
        # Parse message using WhatsApp Business API format
        parsed = whatsapp_service.parse_webhook_message(data)
        if not parsed or not parsed.get("from"):
            logger.info("Skipping non-message event or invalid format")
            return {"status": "ok"}
        
        # Extract client phone from WhatsApp API response
        client_phone = f"+{parsed['from']}"  # WhatsApp API returns without +
        message_type = parsed.get("type", "text")  # text, audio, image, document
        
        # Validate WhatsApp is configured
        if not settings.WHATSAPP_PHONE_NUMBER_ID:
            logger.warning("WhatsApp not configured - skipping message")
            return {"status": "ok"}
        
        # In single-tenant mode, log if message from different number
        if client_phone != settings.TENANT_WHATSAPP_NUMBER:
            logger.info(f"Message from {client_phone} (different from configured {settings.TENANT_WHATSAPP_NUMBER})")
            # Still process for flexibility
        
        # Find or create conversation in database
        conversation = db.query(Conversation).filter(
            Conversation.client_phone == client_phone
        ).first()
        
        if not conversation:
            conversation = Conversation(
                id=f"conv_{uuid.uuid4().hex[:12]}",
                client_phone=client_phone,
                status="active",
            )
            db.add(conversation)
            logger.info(f"Created new conversation for {client_phone}")
        
        # Extract message content based on type
        message_content = ""
        media_url = None
        
        if message_type == "text":
            message_content = parsed.get("text", "")
        elif message_type == "audio":
            # Get media URL from WhatsApp
            media_info = parsed.get("audio", {})
            if media_info:
                media_id = media_info.get("id")
                media_url = whatsapp_service.get_media_url(media_id)
                message_content = "[Voice message]"
                logger.info(f"Processing audio message: {media_id}")
        elif message_type == "image":
            # Handle image messages
            media_info = parsed.get("image", {})
            if media_info:
                media_id = media_info.get("id")
                media_url = whatsapp_service.get_media_url(media_id)
                message_content = "[Image message]"
        elif message_type == "document":
            # Handle document messages
            media_info = parsed.get("document", {})
            if media_info:
                media_id = media_info.get("id")
                media_url = whatsapp_service.get_media_url(media_id)
                message_content = f"[Document: {media_info.get('filename', 'document')}]"
        else:
            logger.info(f"Unsupported message type: {message_type}")
            return {"status": "ok"}
        
        # Detect language and intent from message content
        ai_service = AIService()
        detected_language, detected_intent, lang_confidence = ai_service.detect_language_and_intent(message_content)
        
        # Update conversation language if this is the first message or from same language
        if not conversation.detected_language or conversation.detected_language == settings.TENANT_DEFAULT_LANGUAGE:
            conversation.detected_language = detected_language
            conversation.language_confidence = lang_confidence
        
        # Store message in database with language info  
        message = Message(
            id=f"msg_{uuid.uuid4().hex[:12]}",
            conversation_id=conversation.id,
            sender="client",
            content=message_content,
            detected_language=detected_language,
            language_confidence=lang_confidence,
            media_type=message_type,
            media_url=media_url,
            detected_intent="other" if not detected_intent else detected_intent.value,
            created_at=datetime.utcnow(),  # Explicitly set to current time
        )
        
        db.add(message)
        
        # Update conversation metadata
        conversation.last_client_message_at = datetime.utcnow()
        conversation.updated_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"Created message {message.id} with language={detected_language} (confidence={lang_confidence:.2f}), intent={detected_intent.value} for conversation {conversation.id}")
        
        # Queue audio transcription if needed (with language hint)
        if message_type == "audio" and media_url:
            process_audio_transcription.delay(message.id, language=detected_language)
            logger.info(f"Queued audio transcription for message {message.id} in language {detected_language}")
        
        # Schedule auto-reply task with configurable delay
        delay_seconds = settings.TENANT_AUTO_REPLY_DELAY_MINUTES * 60
        send_auto_reply.apply_async(
            args=[conversation.id],
            countdown=delay_seconds,
            task_id=f"auto_reply_{conversation.id}"  # Idempotent - prevents duplicate tasks
        )
        
        logger.info(f"Scheduled auto-reply for conversation {conversation.id} in {delay_seconds}s")
        
        # Acknowledge receipt to WhatsApp (prevents retry)
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {str(e)}", exc_info=True)
        # Return ok anyway to prevent WhatsApp retry
        return {"status": "ok"}
    finally:
        db.close()


@router.post("/whatsapp/status")
async def whatsapp_status_update(request: Request) -> dict:
    """Handle WhatsApp message status updates."""
    try:
        data = await request.json()
        # Could log delivery status, read receipts, etc.
        logger.info(f"Received status update")
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error processing status update: {str(e)}")
        return {"status": "error"}


@router.post("/whatsapp/test-message")
async def test_whatsapp_message(
    phone_number: str = Query(...),
    message_text: str = Query(...)
) -> dict:
    """
    🧪 TEST ENDPOINT ONLY - Simulate WhatsApp message for testing
    
    This endpoint allows you to test the WhatsApp message flow without sending 
    an actual WhatsApp message. It simulates what happens when WhatsApp sends 
    a webhook notification.
    
    Use this to test:
    - Message reception and parsing
    - Conversation creation
    - AI response generation
    - Language detection
    - Document context usage
    
    IMPORTANT: This is for development/testing only. In production, messages 
    come from actual WhatsApp users via the WhatsApp Business API webhook.
    
    Args:
        phone_number: Phone number in format "+1234567890" or "1234567890"
        message_text: The message text to send
        
    Example:
        curl "http://localhost:8000/api/v1/webhooks/whatsapp/test-message?phone_number=%2B15551234567&message_text=Hello"
        
    Returns:
        Status and created conversation/message IDs
    """
    # Normalize phone number (ensure it has + prefix)
    if not phone_number.startswith("+"):
        phone_number = f"+{phone_number}"
    
    # Remove + for WhatsApp API format (it doesn't include +)
    phone_without_plus = phone_number.lstrip("+")
    
    # Build webhook payload that matches WhatsApp Business API format
    # Reference: https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/payload-examples
    test_webhook_payload = {
        "entry": [
            {
                "id": "123456789",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": settings.WHATSAPP_PHONE_NUMBER_ID,
                                "phone_number_id": settings.WHATSAPP_PHONE_NUMBER_ID,
            },
                            "messages": [
                                {
                                    "from": phone_without_plus,
                                    "id": f"wamid.{uuid.uuid4().hex[:20]}",
                                    "timestamp": str(int(datetime.utcnow().timestamp())),
                                    "type": "text",
                                    "text": {
                                        "body": message_text
                                    }
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ],
                "time": int(datetime.utcnow().timestamp())
            }
        ]
    }
    
    db = SessionLocal()
    try:
        # Process the test webhook like a real one
        whatsapp_service = WhatsAppService()
        parsed = whatsapp_service.parse_webhook_message(test_webhook_payload)
        
        if not parsed or not parsed.get("from"):
            logger.warning(f"Failed to parse test webhook payload")
            return {"status": "error", "message": "Failed to parse message"}
        
        client_phone = f"+{parsed['from']}"
        message_content = parsed.get("text", "")
        
        # Find or create conversation
        conversation = db.query(Conversation).filter(
            Conversation.client_phone == client_phone
        ).first()
        
        if not conversation:
            conversation = Conversation(
                id=f"conv_{uuid.uuid4().hex[:12]}",
                client_phone=client_phone,
                status="active",
            )
            db.add(conversation)
            logger.info(f"[TEST] Created new conversation for {client_phone}")
        
        # Detect language and intent
        ai_service = AIService()
        detected_language, detected_intent, lang_confidence = ai_service.detect_language_and_intent(message_content)
        
        # Update conversation language if needed
        if not conversation.detected_language or conversation.detected_language == settings.TENANT_DEFAULT_LANGUAGE:
            conversation.detected_language = detected_language
            conversation.language_confidence = lang_confidence
        
        # Create message
        message = Message(
            id=f"msg_{uuid.uuid4().hex[:12]}",
            conversation_id=conversation.id,
            sender="client",
            content=message_content,
            detected_language=detected_language,
            language_confidence=lang_confidence,
            detected_intent="other" if not detected_intent else detected_intent.value,
            created_at=datetime.utcnow(),  # Explicitly set to current time
        )
        
        db.add(message)
        
        # Update conversation
        conversation.last_client_message_at = datetime.utcnow()
        conversation.updated_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"[TEST] Created message {message.id} for conversation {conversation.id}")
        
        # Schedule auto-reply like normal
        delay_seconds = settings.TENANT_AUTO_REPLY_DELAY_MINUTES * 60
        send_auto_reply.apply_async(
            args=[conversation.id],
            countdown=delay_seconds,
            task_id=f"auto_reply_{conversation.id}"
        )
        
        logger.info(f"[TEST] Scheduled auto-reply for {conversation.id} in {delay_seconds}s")
        
        return {
            "status": "ok",
            "message": "Test message processed successfully",
            "conversation_id": conversation.id,
            "message_id": message.id,
            "phone_number": client_phone,
            "detected_language": detected_language,
            "detected_intent": detected_intent.value,
            "auto_reply_in_seconds": delay_seconds
        }
        
    except Exception as e:
        logger.error(f"[TEST] Error processing test webhook: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

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
    hub_mode: str = Query(...),
    hub_challenge: str = Query(...),
    hub_verify_token: str = Query(...)
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
    Receive WhatsApp messages via Meta WhatsApp Business API.
    
    This webhook:
    1. Parses incoming message from WhatsApp Cloud API
    2. Creates/updates conversation in database
    3. Stores message with metadata
    4. Schedules auto-reply task
    5. Transcribes audio if needed
    
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
            sender=MessageSender.CLIENT,
            content=message_content,
            detected_language=detected_language,
            language_confidence=lang_confidence,
            media_type=message_type,
            media_url=media_url,
            detected_intent=detected_intent,
            timestamp=datetime.utcfromtimestamp(int(parsed.get("timestamp", 0))) if parsed.get("timestamp") else datetime.utcnow(),
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

"""Celery task definitions."""

import logging
from datetime import datetime, timedelta
from celery import Celery
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.config import settings
from app.models import Conversation, Message, MessageSender, Intent
from app.services.ai_service import AIService
from app.services.whatsapp_service import WhatsAppService

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    "whatsapp_assistant",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=28 * 60,  # 28 minutes
)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3},
    default_retry_delay=60,
)
def send_auto_reply(self, conversation_id: str) -> dict:
    """
    Send automatic AI reply if no professional response within timeout (language-aware).
    
    Args:
        conversation_id: ID of the conversation
        
    Returns:
        Task result dict
    """
    db = SessionLocal()
    try:
        logger.info(f"Processing auto-reply for conversation: {conversation_id}")
        
        # Get conversation
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            logger.warning(f"Conversation not found: {conversation_id}")
            return {"status": "failed", "reason": "conversation_not_found"}
        
        # Check if professional has already replied
        last_message = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.desc()).first()
        
        if last_message:
            if last_message.sender == MessageSender.PROFESSIONAL:
                logger.info(f"Professional already replied to {conversation_id}")
                return {"status": "skipped", "reason": "professional_replied"}
            
            if last_message.sender == MessageSender.AI:
                logger.info(f"AI already replied to {conversation_id}")
                return {"status": "skipped", "reason": "ai_already_replied"}
        
        # Get latest client message
        client_messages = db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.sender == MessageSender.CLIENT
        ).order_by(Message.created_at.desc()).first()
        
        if not client_messages:
            logger.warning(f"No client messages found for {conversation_id}")
            return {"status": "failed", "reason": "no_client_messages"}
        
        # Get conversation language
        conversation_language = conversation.detected_language or settings.TENANT_DEFAULT_LANGUAGE
        
        # Generate AI response (language-aware)
        ai_service = AIService()
        response_content = ai_service.generate_response(
            conversation_id=conversation_id,
            message_content=client_messages.content,
            detected_intent=client_messages.detected_intent or Intent.OTHER,
            detected_language=conversation_language,
            db=db
        )
        
        if not response_content:
            logger.error(f"Failed to generate response for {conversation_id}")
            return {"status": "failed", "reason": "generation_failed"}
        
        # Send via WhatsApp
        whatsapp_service = WhatsAppService()
        success = whatsapp_service.send_message(
            phone_number=conversation.client_phone,
            message_content=response_content,
            conversation_id=conversation_id
        )
        
        if success:
            # Create AI message record
            ai_message = Message(
                id=f"msg_{datetime.utcnow().timestamp()}",
                conversation_id=conversation_id,
                sender=MessageSender.AI,
                content=response_content,
                detected_language=conversation_language,
                is_auto_reply=True,
                detected_intent=Intent.OTHER,
            )
            db.add(ai_message)
            
            # Update conversation
            conversation.last_ai_message_at = datetime.utcnow()
            conversation.updated_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Auto-reply sent successfully for {conversation_id} in {conversation_language}")
            return {"status": "success", "message_id": ai_message.id}
        else:
            logger.error(f"Failed to send WhatsApp message for {conversation_id}")
            return {"status": "failed", "reason": "whatsapp_send_failed"}
            
    except Exception as e:
        logger.error(f"Error in send_auto_reply: {str(e)}", exc_info=True)
        raise
    finally:
        db.close()


@celery_app.task
def process_audio_transcription(message_id: str, language: str = None) -> dict:
    """
    Transcribe audio message with language awareness.
    
    Args:
        message_id: ID of the message with audio
        language: Optional ISO 639-1 language code for transcription hint
        
    Returns:
        Task result dict
    """
    db = SessionLocal()
    try:
        logger.info(f"Transcribing audio for message: {message_id} (language hint: {language})")
        
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            logger.warning(f"Message not found: {message_id}")
            return {"status": "failed", "reason": "message_not_found"}
        
        if not message.media_url or message.media_type != "audio":
            logger.warning(f"Message {message_id} is not an audio message")
            return {"status": "skipped", "reason": "not_audio"}
        
        # Transcribe with language hint
        ai_service = AIService()
        transcript, detected_language = ai_service.transcribe_audio(
            message.media_url,
            language=language
        )
        
        if transcript:
            message.transcript = transcript
            message.detected_language = detected_language
            
            # Detect intent from transcript (language-aware)
            message.detected_intent = ai_service.detect_intent(transcript, detected_language)
            db.commit()
            
            logger.info(f"Audio transcribed for message: {message_id}, language: {detected_language}")
            return {"status": "success", "transcript": transcript, "language": detected_language}
        else:
            logger.error(f"Failed to transcribe audio for {message_id}")
            return {"status": "failed", "reason": "transcription_failed"}
            
    except Exception as e:
        logger.error(f"Error in process_audio_transcription: {str(e)}", exc_info=True)
        return {"status": "failed", "reason": str(e)}
    finally:
        db.close()


@celery_app.task
def generate_embeddings_for_document(document_id: str) -> dict:
    """
    Generate embeddings for a newly uploaded document with language detection.
    
    Args:
        document_id: ID of the document
        
    Returns:
        Task result dict
    """
    db = SessionLocal()
    try:
        logger.info(f"Generating embeddings for document: {document_id}")
        
        from app.models import KnowledgeDocument, DocumentChunk
        from app.services.rag_service import RAGService
        
        document = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == document_id
        ).first()
        
        if not document:
            logger.warning(f"Document not found: {document_id}")
            return {"status": "failed", "reason": "document_not_found"}
        
        # Generate embeddings (with language detection)
        rag_service = RAGService()
        chunks = rag_service.chunk_text(document.content, detect_language=True)
        
        chunk_count = 0
        languages_found = set()
        for idx, chunk_obj in enumerate(chunks):
            embedding = rag_service.generate_embedding(chunk_obj["content"])
            if embedding:
                doc_chunk = DocumentChunk(
                    id=f"chunk_{document_id}_{idx}",
                    document_id=document_id,
                    chunk_index=idx,
                    content=chunk_obj["content"],
                    detected_language=chunk_obj["language"],
                    embedding=embedding,
                )
                db.add(doc_chunk)
                chunk_count += 1
                languages_found.add(chunk_obj["language"])
        
        db.commit()
        logger.info(f"Generated {chunk_count} chunks for document {document_id} in languages: {languages_found}")
        return {"status": "success", "chunk_count": chunk_count, "languages": list(languages_found)}
        
    except Exception as e:
        logger.error(f"Error in generate_embeddings_for_document: {str(e)}", exc_info=True)
        return {"status": "failed", "reason": str(e)}
    finally:
        db.close()


@celery_app.task
def cleanup_old_conversations() -> dict:
    """Clean up old conversations (older than 90 days)."""
    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        deleted_count = db.query(Conversation).filter(
            Conversation.updated_at < cutoff_date,
            Conversation.status == "closed"
        ).delete()
        db.commit()
        logger.info(f"Cleaned up {deleted_count} old conversations")
        return {"status": "success", "deleted_count": deleted_count}
    except Exception as e:
        logger.error(f"Error in cleanup_old_conversations: {str(e)}", exc_info=True)
        return {"status": "failed", "reason": str(e)}
    finally:
        db.close()

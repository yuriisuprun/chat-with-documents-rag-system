"""Celery task definitions."""

import logging
import time
import uuid
from datetime import datetime, timedelta

import structlog
from celery import Celery
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.config import settings
from app.models import Conversation, Message, MessageSender, Intent
from app.services.ai_service import AIService
from app.services.whatsapp_service import WhatsAppService

logger = structlog.get_logger(__name__)

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
    start_time = time.time()
    
    try:
        logger.info(
            "auto_reply_task_started",
            conversation_id=conversation_id,
            task_id=self.request.id,
            attempt=self.request.retries + 1,
        )
        
        # Get conversation
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            logger.warning(
                "auto_reply_conversation_not_found",
                conversation_id=conversation_id,
            )
            return {"status": "failed", "reason": "conversation_not_found"}
        
        # Check if professional has already replied
        last_message = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.desc()).first()
        
        if last_message:
            if last_message.sender == MessageSender.PROFESSIONAL:
                logger.info(
                    "auto_reply_skipped_professional_replied",
                    conversation_id=conversation_id,
                )
                return {"status": "skipped", "reason": "professional_replied"}
            
            if last_message.sender == MessageSender.AI:
                logger.info(
                    "auto_reply_skipped_already_replied",
                    conversation_id=conversation_id,
                )
                return {"status": "skipped", "reason": "ai_already_replied"}
        
        # Get latest client message
        client_messages = db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.sender == MessageSender.CLIENT
        ).order_by(Message.created_at.desc()).first()
        
        if not client_messages:
            logger.warning(
                "auto_reply_no_client_messages",
                conversation_id=conversation_id,
            )
            return {"status": "failed", "reason": "no_client_messages"}
        
        # Get conversation language
        conversation_language = conversation.detected_language or settings.TENANT_DEFAULT_LANGUAGE
        
        logger.info(
            "auto_reply_processing",
            conversation_id=conversation_id,
            language=conversation_language,
            detected_intent=client_messages.detected_intent if client_messages.detected_intent else "unknown",
        )
        
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
            logger.error(
                "auto_reply_generation_failed",
                conversation_id=conversation_id,
            )
            return {"status": "failed", "reason": "generation_failed"}
        
        logger.debug(
            "auto_reply_response_generated",
            conversation_id=conversation_id,
            response_length=len(response_content),
        )
        
        # Create AI message record FIRST (before sending to WhatsApp)
        ai_message = Message(
            id=f"msg_{uuid.uuid4().hex[:12]}",  # Use UUID for consistency with other messages
            conversation_id=conversation_id,
            sender=MessageSender.AI,
            content=response_content,
            detected_language=conversation_language,
            is_auto_reply=True,
            detected_intent=Intent.OTHER,
            created_at=datetime.utcnow(),  # Explicitly set to current time
        )
        db.add(ai_message)
        
        # Update conversation
        conversation.last_ai_message_at = datetime.utcnow()
        conversation.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(
            "auto_reply_message_stored",
            conversation_id=conversation_id,
            message_id=ai_message.id,
        )
        
        # Send via WhatsApp
        whatsapp_service = WhatsAppService()
        success = whatsapp_service.send_message(
            phone_number=conversation.client_phone,
            message_content=response_content,
            conversation_id=conversation_id
        )
        
        if success:
            logger.info(
                "auto_reply_sent_successfully",
                conversation_id=conversation_id,
                message_id=ai_message.id,
                language=conversation_language,
            )
            return {"status": "success", "message_id": ai_message.id}
        else:
            logger.error(
                "auto_reply_whatsapp_send_failed",
                conversation_id=conversation_id,
                phone_number=conversation.client_phone,
            )
            # Message is still saved in DB even if WhatsApp send fails
            return {"status": "partial_success", "reason": "whatsapp_send_failed", "message_id": ai_message.id}
            
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            "auto_reply_task_error",
            conversation_id=conversation_id,
            error=str(e),
            duration_ms=round(duration * 1000, 2),
            exc_info=True,
        )
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
    start_time = time.time()
    
    try:
        logger.info(
            "audio_transcription_task_started",
            message_id=message_id,
            language_hint=language,
        )
        
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            logger.warning(
                "audio_transcription_message_not_found",
                message_id=message_id,
            )
            return {"status": "failed", "reason": "message_not_found"}
        
        if not message.media_url or message.media_type != "audio":
            logger.warning(
                "audio_transcription_not_audio",
                message_id=message_id,
                media_type=message.media_type,
            )
            return {"status": "skipped", "reason": "not_audio"}
        
        logger.debug(
            "audio_transcription_downloading",
            message_id=message_id,
            media_url=message.media_url[:50] + "..." if len(message.media_url) > 50 else message.media_url,
        )
        
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
            
            duration = time.time() - start_time
            logger.info(
                "audio_transcription_completed",
                message_id=message_id,
                detected_language=detected_language,
                transcript_length=len(transcript),
                duration_ms=round(duration * 1000, 2),
            )
            return {
                "status": "success",
                "transcript": transcript,
                "language": detected_language
            }
        else:
            logger.error(
                "audio_transcription_failed",
                message_id=message_id,
            )
            return {"status": "failed", "reason": "transcription_failed"}
            
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            "audio_transcription_error",
            message_id=message_id,
            error=str(e),
            duration_ms=round(duration * 1000, 2),
            exc_info=True,
        )
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
    start_time = time.time()
    
    try:
        logger.info(
            "embedding_generation_task_started",
            document_id=document_id,
        )
        
        from app.models import KnowledgeDocument, DocumentChunk
        from app.services.rag_service import RAGService
        
        document = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == document_id
        ).first()
        
        if not document:
            logger.warning(
                "embedding_generation_document_not_found",
                document_id=document_id,
            )
            return {"status": "failed", "reason": "document_not_found"}
        
        logger.debug(
            "embedding_generation_chunking",
            document_id=document_id,
            content_length=len(document.content),
        )
        
        # Generate embeddings (with language detection)
        rag_service = RAGService()
        chunks = rag_service.chunk_text(document.content, detect_language=True)
        
        chunk_count = 0
        languages_found = set()
        failed_chunks = 0
        
        for idx, chunk_obj in enumerate(chunks):
            try:
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
                else:
                    failed_chunks += 1
                    logger.warning(
                        "embedding_generation_chunk_embedding_failed",
                        document_id=document_id,
                        chunk_index=idx,
                    )
            except Exception as chunk_error:
                failed_chunks += 1
                logger.error(
                    "embedding_generation_chunk_error",
                    document_id=document_id,
                    chunk_index=idx,
                    error=str(chunk_error),
                )
        
        db.commit()
        
        duration = time.time() - start_time
        logger.info(
            "embedding_generation_completed",
            document_id=document_id,
            chunk_count=chunk_count,
            failed_chunks=failed_chunks,
            languages=sorted(list(languages_found)),
            duration_ms=round(duration * 1000, 2),
        )
        
        return {
            "status": "success",
            "chunk_count": chunk_count,
            "languages": sorted(list(languages_found))
        }
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            "embedding_generation_error",
            document_id=document_id,
            error=str(e),
            duration_ms=round(duration * 1000, 2),
            exc_info=True,
        )
        return {"status": "failed", "reason": str(e)}
    finally:
        db.close()


@celery_app.task
def cleanup_old_conversations() -> dict:
    """Clean up old conversations (older than 90 days)."""
    db = SessionLocal()
    start_time = time.time()
    
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        
        logger.info(
            "cleanup_conversations_started",
            cutoff_date=cutoff_date.isoformat(),
        )
        
        deleted_count = db.query(Conversation).filter(
            Conversation.updated_at < cutoff_date,
            Conversation.status == "closed"
        ).delete()
        db.commit()
        
        duration = time.time() - start_time
        logger.info(
            "cleanup_conversations_completed",
            deleted_count=deleted_count,
            cutoff_date=cutoff_date.isoformat(),
            duration_ms=round(duration * 1000, 2),
        )
        
        return {"status": "success", "deleted_count": deleted_count}
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            "cleanup_conversations_error",
            error=str(e),
            duration_ms=round(duration * 1000, 2),
            exc_info=True,
        )
        return {"status": "failed", "reason": str(e)}
    finally:
        db.close()

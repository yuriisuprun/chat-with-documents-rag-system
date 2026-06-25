"""Conversation endpoints."""

import logging
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
import structlog
from app.database import get_db
from app.models import Conversation, Message, MessageSender
from app.schemas import ConversationResponse, ConversationDetailResponse, MessageResponse, ConversationCreate, ConversationUpdate

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationResponse])
def list_conversations(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    request: Request = None,
) -> list[ConversationResponse]:
    """List all conversations."""
    request_id = getattr(request.state, "request_id", "unknown") if request else "unknown"
    
    logger.info(
        "list_conversations_started",
        request_id=request_id,
        skip=skip,
        limit=limit,
    )
    
    try:
        conversations = db.query(Conversation).order_by(
            Conversation.updated_at.desc()
        ).offset(skip).limit(limit).all()
        
        logger.info(
            "list_conversations_success",
            request_id=request_id,
            count=len(conversations),
        )
        
        return [ConversationResponse.from_orm(c) for c in conversations]
    except Exception as e:
        logger.error(
            "list_conversations_error",
            request_id=request_id,
            error=str(e),
            exc_info=True,
        )
        raise


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    request_data: ConversationCreate,
    db: Session = Depends(get_db),
    request: Request = None,
) -> ConversationResponse:
    """
    ⚠️ TESTING ONLY: Create or get conversation by phone number.
    
    IMPORTANT: In production, conversations are automatically created when
    the first WhatsApp message arrives via the webhook at /api/v1/webhooks/whatsapp.
    
    This endpoint exists for development and testing purposes only.
    Manual conversation creation breaks the audit trail and creates
    inconsistent state between the dashboard and actual WhatsApp messages.
    
    For production testing, use the WhatsApp Business API simulator instead:
    https://developers.facebook.com/
    
    See ARCHITECTURE_REFACTORING_GUIDE.md for details.
    """
    request_id = getattr(request.state, "request_id", "unknown") if request else "unknown"
    
    logger.info(
        "create_conversation_started",
        request_id=request_id,
        client_phone=request_data.client_phone,
    )
    
    try:
        # Find or create conversation
        conversation = db.query(Conversation).filter(
            Conversation.client_phone == request_data.client_phone
        ).first()
        
        if not conversation:
            conversation = Conversation(
                id=f"conv_{uuid.uuid4().hex[:12]}",
                client_phone=request_data.client_phone,
                status="active",
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            logger.info(
                "conversation_created",
                request_id=request_id,
                conversation_id=conversation.id,
                client_phone=request_data.client_phone,
            )
        else:
            logger.info(
                "conversation_already_exists",
                request_id=request_id,
                conversation_id=conversation.id,
                client_phone=request_data.client_phone,
            )
        
        return ConversationResponse.from_orm(conversation)
    except Exception as e:
        logger.error(
            "create_conversation_error",
            request_id=request_id,
            client_phone=request_data.client_phone,
            error=str(e),
            exc_info=True,
        )
        raise


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    request: Request = None,
) -> ConversationDetailResponse:
    """Get conversation with all messages."""
    request_id = getattr(request.state, "request_id", "unknown") if request else "unknown"
    
    logger.info(
        "get_conversation_started",
        request_id=request_id,
        conversation_id=conversation_id,
    )
    
    try:
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            logger.warning(
                "conversation_not_found",
                request_id=request_id,
                conversation_id=conversation_id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.asc()).all()
        
        logger.info(
            "get_conversation_success",
            request_id=request_id,
            conversation_id=conversation_id,
            message_count=len(messages),
        )
        
        response = ConversationDetailResponse.from_orm(conversation)
        response.messages = [MessageResponse.from_orm(m) for m in messages]
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "get_conversation_error",
            request_id=request_id,
            conversation_id=conversation_id,
            error=str(e),
            exc_info=True,
        )
        raise


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
def get_messages(
    conversation_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    request: Request = None,
) -> list[MessageResponse]:
    """Get messages in a conversation."""
    request_id = getattr(request.state, "request_id", "unknown") if request else "unknown"
    
    logger.info(
        "get_messages_started",
        request_id=request_id,
        conversation_id=conversation_id,
        skip=skip,
        limit=limit,
    )
    
    try:
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.asc()).offset(skip).limit(limit).all()
        
        logger.info(
            "get_messages_success",
            request_id=request_id,
            conversation_id=conversation_id,
            message_count=len(messages),
        )
        
        return [MessageResponse.from_orm(m) for m in messages]
    except Exception as e:
        logger.error(
            "get_messages_error",
            request_id=request_id,
            conversation_id=conversation_id,
            error=str(e),
            exc_info=True,
        )
        raise


@router.post("/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def send_message(
    conversation_id: str,
    content: str = Query(..., description="Message content to send"),
    db: Session = Depends(get_db),
    request: Request = None,
) -> MessageResponse:
    """
    Send a message from dashboard/professional to WhatsApp client.
    
    This endpoint:
    1. Cancels any pending auto-reply tasks (prevents duplicates)
    2. Sends the message to WhatsApp via the Business API
    3. Creates a professional message record in the database
    4. Returns the message record
    
    Args:
        conversation_id: ID of the conversation
        content: Message text to send
        
    Returns:
        MessageResponse with the created message
    """
    request_id = getattr(request.state, "request_id", "unknown") if request else "unknown"
    
    logger.info(
        "send_message_started",
        request_id=request_id,
        conversation_id=conversation_id,
        message_length=len(content),
    )
    
    try:
        # Find conversation
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            logger.warning(
                "send_message_conversation_not_found",
                request_id=request_id,
                conversation_id=conversation_id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Validate message content
        if not content or not content.strip():
            logger.warning(
                "send_message_empty_content",
                request_id=request_id,
                conversation_id=conversation_id,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message content cannot be empty"
            )
        
        # Cancel any pending auto-reply tasks to prevent duplicate responses
        from app.tasks import celery_app
        task_id = f"auto_reply_{conversation_id}"
        try:
            celery_app.control.revoke(task_id, terminate=True)
            logger.debug(
                "send_message_cancelled_pending_autoreply",
                request_id=request_id,
                conversation_id=conversation_id,
                task_id=task_id,
            )
        except Exception as e:
            logger.warning(
                "send_message_cancel_autoreply_failed",
                request_id=request_id,
                conversation_id=conversation_id,
                error=str(e),
            )
        
        # Send to WhatsApp
        from app.services.whatsapp_service import WhatsAppService
        whatsapp_service = WhatsAppService()
        
        success = whatsapp_service.send_message(
            phone_number=conversation.client_phone,
            message_content=content,
            conversation_id=conversation_id,
        )
        
        if not success:
            logger.error(
                "send_message_whatsapp_failed",
                request_id=request_id,
                conversation_id=conversation_id,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send message to WhatsApp"
            )
        
        # Create message record in database
        message = Message(
            id=f"msg_{uuid.uuid4().hex[:12]}",
            conversation_id=conversation_id,
            sender=MessageSender.PROFESSIONAL,
            content=content,
        )
        db.add(message)
        
        # Update conversation timestamp
        conversation.last_professional_message_at = datetime.utcnow()
        conversation.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(message)
        
        logger.info(
            "send_message_success",
            request_id=request_id,
            conversation_id=conversation_id,
            message_id=message.id,
            client_phone=conversation.client_phone,
        )
        
        return MessageResponse.from_orm(message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "send_message_error",
            request_id=request_id,
            conversation_id=conversation_id,
            error=str(e),
            exc_info=True,
        )
        raise


@router.put("/{conversation_id}", response_model=ConversationResponse)
def update_conversation(
    conversation_id: str,
    request_data: ConversationUpdate,
    db: Session = Depends(get_db),
    request: Request = None,
) -> ConversationResponse:
    """Update conversation status."""
    request_id = getattr(request.state, "request_id", "unknown") if request else "unknown"
    
    logger.info(
        "update_conversation_started",
        request_id=request_id,
        conversation_id=conversation_id,
        new_status=request_data.status,
    )
    
    try:
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            logger.warning(
                "conversation_not_found_for_update",
                request_id=request_id,
                conversation_id=conversation_id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        if request_data.status:
            old_status = conversation.status
            conversation.status = request_data.status
        
        conversation.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(conversation)
        
        logger.info(
            "conversation_updated",
            request_id=request_id,
            conversation_id=conversation_id,
            old_status=old_status if request_data.status else None,
            new_status=request_data.status,
        )
        
        return ConversationResponse.from_orm(conversation)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "update_conversation_error",
            request_id=request_id,
            conversation_id=conversation_id,
            error=str(e),
            exc_info=True,
        )
        raise


@router.get("/{conversation_id}/summary")
def get_conversation_summary(
    conversation_id: str,
    db: Session = Depends(get_db),
    request: Request = None,
) -> dict:
    """Get conversation summary."""
    request_id = getattr(request.state, "request_id", "unknown") if request else "unknown"
    
    logger.info(
        "get_conversation_summary_started",
        request_id=request_id,
        conversation_id=conversation_id,
    )
    
    try:
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            logger.warning(
                "conversation_not_found_for_summary",
                request_id=request_id,
                conversation_id=conversation_id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        message_count = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).count()
        
        client_messages = db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.sender == MessageSender.CLIENT
        ).count()
        
        ai_messages = db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.sender == MessageSender.AI
        ).count()
        
        prof_messages = db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.sender == MessageSender.PROFESSIONAL
        ).count()
        
        summary = {
            "conversation_id": conversation_id,
            "client_phone": conversation.client_phone,
            "status": conversation.status,
            "total_messages": message_count,
            "client_messages": client_messages,
            "ai_messages": ai_messages,
            "professional_messages": prof_messages,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
        }
        
        logger.info(
            "get_conversation_summary_success",
            request_id=request_id,
            conversation_id=conversation_id,
            total_messages=message_count,
        )
        
        return summary
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "get_conversation_summary_error",
            request_id=request_id,
            conversation_id=conversation_id,
            error=str(e),
            exc_info=True,
        )
        raise

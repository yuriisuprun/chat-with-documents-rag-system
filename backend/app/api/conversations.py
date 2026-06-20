"""Conversation endpoints."""

import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Conversation, Message, MessageSender
from app.schemas import ConversationResponse, ConversationDetailResponse, MessageResponse, ConversationCreate, ConversationUpdate

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationResponse])
def list_conversations(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
) -> list[ConversationResponse]:
    """List all conversations."""
    
    conversations = db.query(Conversation).order_by(
        Conversation.updated_at.desc()
    ).offset(skip).limit(limit).all()
    
    return [ConversationResponse.from_orm(c) for c in conversations]


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    request: ConversationCreate,
    db: Session = Depends(get_db)
) -> ConversationResponse:
    """Create or get conversation."""
    # Find or create conversation
    conversation = db.query(Conversation).filter(
        Conversation.client_phone == request.client_phone
    ).first()
    
    if not conversation:
        conversation = Conversation(
            id=f"conv_{uuid.uuid4().hex[:12]}",
            client_phone=request.client_phone,
            status="active",
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    
    return ConversationResponse.from_orm(conversation)


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
) -> ConversationDetailResponse:
    """Get conversation with all messages."""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at.asc()).all()
    
    response = ConversationDetailResponse.from_orm(conversation)
    response.messages = [MessageResponse.from_orm(m) for m in messages]
    
    return response


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
def get_messages(
    conversation_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> list[MessageResponse]:
    """Get messages in a conversation."""
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at.asc()).offset(skip).limit(limit).all()
    
    return [MessageResponse.from_orm(m) for m in messages]


@router.put("/{conversation_id}", response_model=ConversationResponse)
def update_conversation(
    conversation_id: str,
    request: ConversationUpdate,
    db: Session = Depends(get_db)
) -> ConversationResponse:
    """Update conversation status."""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    if request.status:
        conversation.status = request.status
    
    conversation.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(conversation)
    
    return ConversationResponse.from_orm(conversation)


@router.get("/{conversation_id}/summary")
def get_conversation_summary(
    conversation_id: str,
    db: Session = Depends(get_db)
) -> dict:
    """Get conversation summary."""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()
    
    if not conversation:
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
    
    return {
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

# agent/api/conversations.py — Panel de conversaciones
import uuid
from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from agent.database import get_db
from agent.models import Conversation, Message, ConversationStatus
from agent.middleware.auth import get_current_tenant_id

router = APIRouter(prefix="/conversations", tags=["conversations"])


class ConversationSummary(BaseModel):
    id: str
    phone_number: str
    contact_name: Optional[str]
    status: str
    is_ai_active: bool
    last_message: Optional[str]
    last_message_at: Optional[str]
    message_count: int


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: str


class ConversationDetailResponse(BaseModel):
    id: str
    phone_number: str
    contact_name: Optional[str]
    status: str
    is_ai_active: bool
    created_at: str
    messages: List[MessageResponse]


@router.get("", response_model=list[ConversationSummary])
async def list_conversations(
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Lista las conversaciones del tenant con resumen."""
    query = select(Conversation).where(Conversation.tenant_id == tenant_id)

    if status:
        query = query.where(Conversation.status == status)
    if search:
        query = query.where(
            Conversation.phone_number.ilike(f"%{search}%")
            | Conversation.contact_name.ilike(f"%{search}%")
        )

    query = query.order_by(desc(Conversation.last_message_at)).offset(offset).limit(limit)
    result = await db.execute(query)
    conversations = result.scalars().all()

    summaries = []
    for conv in conversations:
        # Obtener ultimo mensaje y count
        msg_query = select(Message).where(
            Message.conversation_id == conv.id
        ).order_by(desc(Message.created_at)).limit(1)
        msg_result = await db.execute(msg_query)
        last_msg = msg_result.scalar_one_or_none()

        count_query = select(func.count()).select_from(Message).where(
            Message.conversation_id == conv.id
        )
        count_result = await db.execute(count_query)
        count = count_result.scalar()

        summaries.append(ConversationSummary(
            id=str(conv.id),
            phone_number=conv.phone_number,
            contact_name=conv.contact_name,
            status=conv.status.value,
            is_ai_active=conv.is_ai_active,
            last_message=last_msg.content[:100] if last_msg else None,
            last_message_at=conv.last_message_at.isoformat() if conv.last_message_at else None,
            message_count=count,
        ))

    return summaries


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: uuid.UUID,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Retorna una conversacion con sus mensajes."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.tenant_id == tenant_id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversacion no encontrada")

    msg_query = (
        select(Message)
        .where(Message.conversation_id == conv.id)
        .order_by(Message.created_at)
        .offset(offset)
        .limit(limit)
    )
    msg_result = await db.execute(msg_query)
    messages = msg_result.scalars().all()

    return ConversationDetailResponse(
        id=str(conv.id),
        phone_number=conv.phone_number,
        contact_name=conv.contact_name,
        status=conv.status.value,
        is_ai_active=conv.is_ai_active,
        created_at=conv.created_at.isoformat(),
        messages=[
            MessageResponse(
                id=str(m.id),
                role=m.role,
                content=m.content,
                created_at=m.created_at.isoformat(),
            )
            for m in messages
        ],
    )


@router.patch("/{conversation_id}/toggle-ai")
async def toggle_ai(
    conversation_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Activa/desactiva la IA en una conversacion (tomar el control manual)."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.tenant_id == tenant_id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversacion no encontrada")

    conv.is_ai_active = not conv.is_ai_active
    await db.commit()

    return {"status": "ok", "is_ai_active": conv.is_ai_active}


@router.patch("/{conversation_id}/archive")
async def archive_conversation(
    conversation_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Archiva una conversacion."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.tenant_id == tenant_id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversacion no encontrada")

    conv.status = ConversationStatus.archived
    await db.commit()

    return {"status": "ok"}

# agent/api/analytics.py — Estadisticas y metricas del tenant
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from pydantic import BaseModel
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from agent.database import get_db
from agent.models import Conversation, Message, UsageTracking
from agent.middleware.auth import get_current_tenant_id

router = APIRouter(prefix="/analytics", tags=["analytics"])


class DailyUsage(BaseModel):
    date: str
    messages_received: int
    messages_sent: int
    ai_tokens_input: int
    ai_tokens_output: int


class AnalyticsSummary(BaseModel):
    total_conversations: int
    active_conversations: int
    total_messages_today: int
    total_messages_week: int
    total_messages_month: int
    daily_usage: list[DailyUsage]


@router.get("/summary", response_model=AnalyticsSummary)
async def get_summary(
    days: int = Query(default=30, le=90),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Resumen de metricas del tenant."""
    now = datetime.utcnow()
    today = now.date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # Total conversaciones
    total_conv = await db.execute(
        select(func.count()).select_from(Conversation).where(
            Conversation.tenant_id == tenant_id
        )
    )
    total_conversations = total_conv.scalar()

    # Conversaciones activas (con mensaje en ultimos 7 dias)
    active_conv = await db.execute(
        select(func.count()).select_from(Conversation).where(
            Conversation.tenant_id == tenant_id,
            Conversation.last_message_at >= datetime.combine(week_ago, datetime.min.time()),
        )
    )
    active_conversations = active_conv.scalar()

    # Mensajes hoy
    today_start = datetime.combine(today, datetime.min.time())
    msgs_today = await db.execute(
        select(func.count()).select_from(Message).where(
            Message.tenant_id == tenant_id,
            Message.created_at >= today_start,
        )
    )
    total_messages_today = msgs_today.scalar()

    # Mensajes semana
    week_start = datetime.combine(week_ago, datetime.min.time())
    msgs_week = await db.execute(
        select(func.count()).select_from(Message).where(
            Message.tenant_id == tenant_id,
            Message.created_at >= week_start,
        )
    )
    total_messages_week = msgs_week.scalar()

    # Mensajes mes
    month_start = datetime.combine(month_ago, datetime.min.time())
    msgs_month = await db.execute(
        select(func.count()).select_from(Message).where(
            Message.tenant_id == tenant_id,
            Message.created_at >= month_start,
        )
    )
    total_messages_month = msgs_month.scalar()

    # Usage diario
    usage_start = today - timedelta(days=days)
    usage_query = await db.execute(
        select(UsageTracking).where(
            UsageTracking.tenant_id == tenant_id,
            UsageTracking.date >= usage_start,
        ).order_by(UsageTracking.date)
    )
    usage_records = usage_query.scalars().all()

    daily_usage = [
        DailyUsage(
            date=str(u.date),
            messages_received=u.messages_received,
            messages_sent=u.messages_sent,
            ai_tokens_input=u.ai_tokens_input,
            ai_tokens_output=u.ai_tokens_output,
        )
        for u in usage_records
    ]

    return AnalyticsSummary(
        total_conversations=total_conversations,
        active_conversations=active_conversations,
        total_messages_today=total_messages_today,
        total_messages_week=total_messages_week,
        total_messages_month=total_messages_month,
        daily_usage=daily_usage,
    )

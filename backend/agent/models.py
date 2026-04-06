# agent/models.py — Modelos multi-tenant para AgentKit SaaS

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    String, Text, DateTime, Integer, Boolean, ForeignKey, Date, Index, JSON,
    Enum as SAEnum,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum


class Base(DeclarativeBase):
    pass


# ════════════════════════════════════════════════════════════
# Enums
# ════════════════════════════════════════════════════════════

class PlanType(str, enum.Enum):
    free = "free"
    pro = "pro"
    enterprise = "enterprise"


class UserRole(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    viewer = "viewer"


class WhatsAppProvider(str, enum.Enum):
    whapi = "whapi"
    meta = "meta"
    twilio = "twilio"


class ConversationStatus(str, enum.Enum):
    active = "active"
    archived = "archived"
    blocked = "blocked"


# ════════════════════════════════════════════════════════════
# Tenant — Cada negocio registrado
# ════════════════════════════════════════════════════════════

class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    plan: Mapped[PlanType] = mapped_column(SAEnum(PlanType), default=PlanType.free)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    users: Mapped[list["User"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    config: Mapped["TenantConfig"] = relationship(back_populates="tenant", uselist=False, cascade="all, delete-orphan")
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    usage_records: Mapped[list["UsageTracking"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")


# ════════════════════════════════════════════════════════════
# User — Usuarios de la plataforma
# ════════════════════════════════════════════════════════════

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(200))
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.owner)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    tenant: Mapped["Tenant"] = relationship(back_populates="users")


# ════════════════════════════════════════════════════════════
# TenantConfig — Configuracion completa del agente
# ════════════════════════════════════════════════════════════

class TenantConfig(Base):
    __tablename__ = "tenant_configs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), unique=True, index=True)

    # Datos del negocio
    business_name: Mapped[str] = mapped_column(String(200), default="")
    business_description: Mapped[str] = mapped_column(Text, default="")
    business_address: Mapped[str] = mapped_column(String(500), default="")
    business_phone: Mapped[str] = mapped_column(String(50), default="")
    business_website: Mapped[str] = mapped_column(String(300), default="")
    business_hours: Mapped[dict] = mapped_column(JSON, default=dict)

    # Configuracion del agente
    agent_name: Mapped[str] = mapped_column(String(100), default="Asistente")
    agent_tone: Mapped[str] = mapped_column(String(50), default="amigable")
    use_cases: Mapped[list] = mapped_column(JSON, default=list)
    system_prompt: Mapped[str] = mapped_column(Text, default="")
    fallback_message: Mapped[str] = mapped_column(Text, default="Disculpa, no entendi tu mensaje. Podrias reformularlo?")
    error_message: Mapped[str] = mapped_column(Text, default="Lo siento, estoy teniendo problemas tecnicos. Por favor intenta de nuevo en unos minutos.")
    knowledge_base: Mapped[str] = mapped_column(Text, default="")

    # Proveedor de WhatsApp
    whatsapp_provider: Mapped[str] = mapped_column(String(20), default="whapi")
    whatsapp_credentials: Mapped[dict] = mapped_column(JSON, default=dict)
    webhook_secret: Mapped[str] = mapped_column(String(100), default="")

    # IA
    ai_provider: Mapped[str] = mapped_column(String(20), default="openai")
    ai_api_key_encrypted: Mapped[str] = mapped_column(Text, default="")
    ai_model: Mapped[str] = mapped_column(String(50), default="gpt-4o-mini")

    # Integraciones externas
    external_api_config: Mapped[dict] = mapped_column(JSON, default=dict)
    custom_tools: Mapped[list] = mapped_column(JSON, default=list)

    # Estado
    is_setup_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant: Mapped["Tenant"] = relationship(back_populates="config")


# ════════════════════════════════════════════════════════════
# Conversation — Conversaciones por telefono por tenant
# ════════════════════════════════════════════════════════════

class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True)
    phone_number: Mapped[str] = mapped_column(String(50), index=True)
    contact_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    status: Mapped[ConversationStatus] = mapped_column(SAEnum(ConversationStatus), default=ConversationStatus.active)
    is_ai_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_message_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    tenant: Mapped["Tenant"] = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_conversations_tenant_phone", "tenant_id", "phone_number", unique=True),
    )


# ════════════════════════════════════════════════════════════
# Message — Mensajes con tenant_id
# ════════════════════════════════════════════════════════════

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id"), index=True)
    role: Mapped[str] = mapped_column(String(20))  # user, assistant, system
    content: Mapped[str] = mapped_column(Text)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")

    __table_args__ = (
        Index("ix_messages_tenant_created", "tenant_id", "created_at"),
    )


# ════════════════════════════════════════════════════════════
# UsageTracking — Metricas de uso por tenant por dia
# ════════════════════════════════════════════════════════════

class UsageTracking(Base):
    __tablename__ = "usage_tracking"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True)
    date: Mapped[datetime] = mapped_column(Date, index=True)
    messages_received: Mapped[int] = mapped_column(Integer, default=0)
    messages_sent: Mapped[int] = mapped_column(Integer, default=0)
    ai_tokens_input: Mapped[int] = mapped_column(Integer, default=0)
    ai_tokens_output: Mapped[int] = mapped_column(Integer, default=0)
    whatsapp_api_calls: Mapped[int] = mapped_column(Integer, default=0)

    tenant: Mapped["Tenant"] = relationship(back_populates="usage_records")

    __table_args__ = (
        Index("ix_usage_tenant_date", "tenant_id", "date", unique=True),
    )


# ════════════════════════════════════════════════════════════
# WebhookLog — Debug de webhooks entrantes
# ════════════════════════════════════════════════════════════

class WebhookLog(Base):
    __tablename__ = "webhook_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    provider: Mapped[str] = mapped_column(String(20))
    payload: Mapped[dict] = mapped_column(JSON)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

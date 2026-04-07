"""add whatsapp numbers pool

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-04-07 15:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('whatsapp_numbers',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('phone_number', sa.String(50), nullable=False),
        sa.Column('label', sa.String(100), nullable=False, server_default=''),
        sa.Column('provider', sa.String(20), nullable=False, server_default='whapi'),
        sa.Column('credentials', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('tenant_id', sa.UUID(), nullable=True),
        sa.Column('assigned_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_whatsapp_numbers_tenant_id', 'whatsapp_numbers', ['tenant_id'])


def downgrade() -> None:
    op.drop_table('whatsapp_numbers')

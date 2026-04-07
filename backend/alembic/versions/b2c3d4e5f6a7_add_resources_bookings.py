"""add resources and bookings

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-07 12:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Niche en tenant_configs
    op.add_column('tenant_configs', sa.Column('niche', sa.String(20), nullable=False, server_default='custom'))

    # Resources
    op.create_table('resources',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.Enum('table', 'room', 'slot', 'custom', name='resourcetype'), nullable=False),
        sa.Column('capacity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('duration_minutes', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_resources_tenant_id', 'resources', ['tenant_id'])

    # Bookings
    op.create_table('bookings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('resource_id', sa.UUID(), nullable=False),
        sa.Column('conversation_id', sa.UUID(), nullable=True),
        sa.Column('contact_phone', sa.String(50), nullable=False),
        sa.Column('contact_name', sa.String(200), nullable=False, server_default=''),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('time_start', sa.String(5), nullable=False),
        sa.Column('time_end', sa.String(5), nullable=False),
        sa.Column('guests', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.Enum('pending', 'confirmed', 'cancelled', 'completed', name='bookingstatus'), nullable=False),
        sa.Column('notes', sa.Text(), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['resource_id'], ['resources.id']),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_bookings_tenant_id', 'bookings', ['tenant_id'])
    op.create_index('ix_bookings_tenant_date', 'bookings', ['tenant_id', 'date'])
    op.create_index('ix_bookings_resource_id', 'bookings', ['resource_id'])


def downgrade() -> None:
    op.drop_table('bookings')
    op.drop_table('resources')
    op.drop_column('tenant_configs', 'niche')

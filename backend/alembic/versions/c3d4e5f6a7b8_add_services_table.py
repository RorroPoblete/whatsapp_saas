"""add services table and link resources

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-04-07 14:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('services',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('niche', sa.String(20), nullable=False, server_default='custom'),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_services_tenant_id', 'services', ['tenant_id'])

    op.add_column('resources', sa.Column('service_id', sa.UUID(), nullable=True))
    op.create_foreign_key('fk_resources_service', 'resources', 'services', ['service_id'], ['id'])
    op.create_index('ix_resources_service_id', 'resources', ['service_id'])


def downgrade() -> None:
    op.drop_index('ix_resources_service_id', table_name='resources')
    op.drop_constraint('fk_resources_service', 'resources', type_='foreignkey')
    op.drop_column('resources', 'service_id')
    op.drop_table('services')

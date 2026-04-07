"""add onboarding fields

Revision ID: a1b2c3d4e5f6
Revises: 652c888efd62
Create Date: 2026-04-06 20:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '652c888efd62'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # TenantConfig: preguntas de onboarding
    op.add_column('tenant_configs', sa.Column('onboarding_questions', sa.JSON(), nullable=False, server_default='[]'))

    # Conversation: estado de onboarding y contexto del contacto
    op.add_column('conversations', sa.Column('onboarding_step', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('conversations', sa.Column('onboarding_complete', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('conversations', sa.Column('contact_context', sa.JSON(), nullable=False, server_default='{}'))


def downgrade() -> None:
    op.drop_column('conversations', 'contact_context')
    op.drop_column('conversations', 'onboarding_complete')
    op.drop_column('conversations', 'onboarding_step')
    op.drop_column('tenant_configs', 'onboarding_questions')

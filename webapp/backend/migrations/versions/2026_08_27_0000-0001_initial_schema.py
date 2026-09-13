"""initial_schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-08-27 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # ── users table ──
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # ── predictions table ──
    op.create_table(
        'predictions',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('item_name', sa.String(length=100), nullable=False),
        sa.Column('image_path', sa.String(length=500), nullable=False),
        sa.Column('temperature', sa.Float(), nullable=False),
        sa.Column('humidity', sa.Float(), nullable=False),
        sa.Column('environment', sa.String(length=50), nullable=False),
        sa.Column('predicted_days', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_predictions_created_at', 'predictions', ['created_at'])
    op.create_index('ix_predictions_user_id', 'predictions', ['user_id'])

def downgrade() -> None:
    op.drop_table('predictions')
    op.drop_table('users')

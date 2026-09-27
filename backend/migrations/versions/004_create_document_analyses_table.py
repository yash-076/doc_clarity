"""create document_analyses table

Revision ID: 004_create_document_analyses
Revises: 003_add_embedding_status
Create Date: 2026-09-27 19:20:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '004_create_document_analyses'
down_revision: Union[str, None] = '003_add_embedding_status'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if 'document_analyses' not in tables:
        uuid_type = postgresql.UUID(as_uuid=True) if conn.dialect.name == 'postgresql' else sa.CHAR(36)
        json_type = postgresql.JSONB() if conn.dialect.name == 'postgresql' else sa.JSON()

        op.create_table(
            'document_analyses',
            sa.Column('id', uuid_type, primary_key=True, nullable=False),
            sa.Column('document_id', uuid_type, sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
            sa.Column('analysis_version', sa.Integer(), server_default='1', nullable=False),
            sa.Column('summary', sa.Text(), nullable=False),
            sa.Column('analysis_json', json_type, nullable=False),
            sa.Column('embedding_model', sa.String(length=100), nullable=True),
            sa.Column('llm_model', sa.String(length=100), nullable=True),
            sa.Column('is_stale', sa.Boolean(), server_default='false', nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        )
        op.create_index(op.f('ix_document_analyses_document_id'), 'document_analyses', ['document_id'], unique=False)

def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if 'document_analyses' in tables:
        op.drop_index(op.f('ix_document_analyses_document_id'), table_name='document_analyses')
        op.drop_table('document_analyses')

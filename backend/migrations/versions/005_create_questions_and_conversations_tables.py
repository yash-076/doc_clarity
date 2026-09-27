"""create questions and conversations tables

Revision ID: 005_create_phase6_tables
Revises: 004_create_document_analyses
Create Date: 2026-09-27 20:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '005_create_phase6_tables'
down_revision: Union[str, None] = '004_create_document_analyses'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    uuid_type = postgresql.UUID(as_uuid=True) if conn.dialect.name == 'postgresql' else sa.CHAR(36)
    json_type = postgresql.JSONB() if conn.dialect.name == 'postgresql' else sa.JSON()

    if 'document_questions' not in tables:
        op.create_table(
            'document_questions',
            sa.Column('id', uuid_type, primary_key=True, nullable=False),
            sa.Column('document_id', uuid_type, sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
            sa.Column('question', sa.Text(), nullable=False),
            sa.Column('category', sa.String(length=50), nullable=False),
            sa.Column('position', sa.Integer(), server_default='0', nullable=False),
            sa.Column('analysis_version', sa.Integer(), server_default='1', nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        )
        op.create_index(op.f('ix_document_questions_document_id'), 'document_questions', ['document_id'], unique=False)

    if 'conversations' not in tables:
        op.create_table(
            'conversations',
            sa.Column('id', uuid_type, primary_key=True, nullable=False),
            sa.Column('document_id', uuid_type, sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        )
        op.create_index(op.f('ix_conversations_document_id'), 'conversations', ['document_id'], unique=False)

    if 'conversation_messages' not in tables:
        op.create_table(
            'conversation_messages',
            sa.Column('id', uuid_type, primary_key=True, nullable=False),
            sa.Column('conversation_id', uuid_type, sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False),
            sa.Column('role', sa.String(length=20), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('citations_json', json_type, nullable=True),
            sa.Column('confidence', sa.String(length=20), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        )
        op.create_index(op.f('ix_conversation_messages_conversation_id'), 'conversation_messages', ['conversation_id'], unique=False)

def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if 'conversation_messages' in tables:
        op.drop_index(op.f('ix_conversation_messages_conversation_id'), table_name='conversation_messages')
        op.drop_table('conversation_messages')
    if 'conversations' in tables:
        op.drop_index(op.f('ix_conversations_document_id'), table_name='conversations')
        op.drop_table('conversations')
    if 'document_questions' in tables:
        op.drop_index(op.f('ix_document_questions_document_id'), table_name='document_questions')
        op.drop_table('document_questions')

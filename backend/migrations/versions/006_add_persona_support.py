"""add persona support and persona_responses cache table

Revision ID: 006_add_persona_support
Revises: 005_create_phase6_tables
Create Date: 2026-09-28 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '006_add_persona_support'
down_revision: Union[str, None] = '005_create_phase6_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    uuid_type = postgresql.UUID(as_uuid=True) if conn.dialect.name == 'postgresql' else sa.CHAR(36)
    json_type = postgresql.JSONB() if conn.dialect.name == 'postgresql' else sa.JSON()

    if 'conversations' in tables:
        columns = [c['name'] for c in inspector.get_columns('conversations')]
        if 'persona' not in columns:
            op.add_column(
                'conversations',
                sa.Column('persona', sa.String(length=30), server_default='consumer', nullable=False)
            )

    if 'conversation_messages' in tables:
        columns = [c['name'] for c in inspector.get_columns('conversation_messages')]
        if 'persona' not in columns:
            op.add_column(
                'conversation_messages',
                sa.Column('persona', sa.String(length=30), server_default='consumer', nullable=True)
            )

    if 'persona_responses' not in tables:
        op.create_table(
            'persona_responses',
            sa.Column('id', uuid_type, primary_key=True, nullable=False),
            sa.Column('document_id', uuid_type, sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
            sa.Column('question_hash', sa.String(length=64), nullable=False),
            sa.Column('persona', sa.String(length=30), nullable=False),
            sa.Column('answer', sa.Text(), nullable=False),
            sa.Column('citations_json', json_type, nullable=True),
            sa.Column('confidence', sa.String(length=20), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        )
        op.create_index(op.f('ix_persona_responses_document_id'), 'persona_responses', ['document_id'], unique=False)
        op.create_index(op.f('ix_persona_responses_question_hash'), 'persona_responses', ['question_hash'], unique=False)
        op.create_index(op.f('ix_persona_responses_persona'), 'persona_responses', ['persona'], unique=False)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if 'persona_responses' in tables:
        op.drop_index(op.f('ix_persona_responses_persona'), table_name='persona_responses')
        op.drop_index(op.f('ix_persona_responses_question_hash'), table_name='persona_responses')
        op.drop_index(op.f('ix_persona_responses_document_id'), table_name='persona_responses')
        op.drop_table('persona_responses')

    if 'conversation_messages' in tables:
        columns = [c['name'] for c in inspector.get_columns('conversation_messages')]
        if 'persona' in columns:
            op.drop_column('conversation_messages', 'persona')

    if 'conversations' in tables:
        columns = [c['name'] for c in inspector.get_columns('conversations')]
        if 'persona' in columns:
            op.drop_column('conversations', 'persona')

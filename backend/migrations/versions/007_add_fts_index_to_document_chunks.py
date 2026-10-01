"""add full text search index to document_chunks

Revision ID: 007_add_fts_index
Revises: 006_add_persona_support
Create Date: 2026-09-28 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '007_add_fts_index'
down_revision: Union[str, None] = '006_add_persona_support'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if 'document_chunks' in tables:
        if conn.dialect.name == 'postgresql':
            # Create PostgreSQL GIN index for Full-Text Search
            op.execute(
                """
                CREATE INDEX IF NOT EXISTS ix_document_chunks_fts 
                ON document_chunks 
                USING gin (to_tsvector('english', coalesce(text, '') || ' ' || coalesce(section, '')));
                """
            )
        else:
            # Fallback index for non-postgresql environments (e.g. SQLite test DB)
            indexes = [idx['name'] for idx in inspector.get_indexes('document_chunks')]
            if 'ix_document_chunks_doc_sec' not in indexes:
                op.create_index(
                    'ix_document_chunks_doc_sec',
                    'document_chunks',
                    ['document_id', 'section'],
                    unique=False
                )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if 'document_chunks' in tables:
        if conn.dialect.name == 'postgresql':
            op.execute("DROP INDEX IF EXISTS ix_document_chunks_fts;")
        else:
            indexes = [idx['name'] for idx in inspector.get_indexes('document_chunks')]
            if 'ix_document_chunks_doc_sec' in indexes:
                op.drop_index('ix_document_chunks_doc_sec', table_name='document_chunks')

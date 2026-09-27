"""add embedding status columns to documents table

Revision ID: 003_add_embedding_status
Revises: 002_create_document_chunks_table
Create Date: 2026-09-27 15:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '003_add_embedding_status'
down_revision: Union[str, None] = '002_create_document_chunks_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    columns = [c['name'] for c in inspector.get_columns('documents')]
    
    # Create enum type if on Postgres and not present
    if conn.dialect.name == 'postgresql':
        op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'embedding_status_enum') THEN CREATE TYPE embedding_status_enum AS ENUM ('pending', 'indexing', 'indexed', 'failed'); END IF; END $$;")

    if 'embedding_status' not in columns:
        op.add_column('documents', sa.Column(
            'embedding_status',
            sa.Enum('pending', 'indexing', 'indexed', 'failed', name='embedding_status_enum'),
            server_default='pending',
            nullable=False
        ))
    if 'embedding_error' not in columns:
        op.add_column('documents', sa.Column('embedding_error', sa.Text(), nullable=True))
    if 'embedding_model' not in columns:
        op.add_column('documents', sa.Column('embedding_model', sa.String(length=100), nullable=True))
    if 'indexed_at' not in columns:
        op.add_column('documents', sa.Column('indexed_at', sa.DateTime(timezone=True), nullable=True))

def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('documents')]
    
    if 'indexed_at' in columns:
        op.drop_column('documents', 'indexed_at')
    if 'embedding_model' in columns:
        op.drop_column('documents', 'embedding_model')
    if 'embedding_error' in columns:
        op.drop_column('documents', 'embedding_error')
    if 'embedding_status' in columns:
        op.drop_column('documents', 'embedding_status')
    
    if conn.dialect.name == 'postgresql':
        op.execute('DROP TYPE IF EXISTS embedding_status_enum;')

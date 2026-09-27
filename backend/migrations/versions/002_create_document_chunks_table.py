"""create document_chunks table and add processing_error to documents

Revision ID: 002_create_document_chunks_table
Revises: 001_create_documents_table
Create Date: 2026-09-27 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_create_document_chunks_table'
down_revision: Union[str, None] = '001_create_documents_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # 1. Add processing_error column if not present
    columns = [c['name'] for c in inspector.get_columns('documents')]
    if 'processing_error' not in columns:
        op.add_column('documents', sa.Column('processing_error', sa.Text(), nullable=True))

    # 2. Create document_chunks table if not present
    tables = inspector.get_table_names()
    if 'document_chunks' not in tables:
        op.create_table(
            'document_chunks',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('document_id', sa.UUID(), nullable=False),
            sa.Column('chunk_index', sa.Integer(), nullable=False),
            sa.Column('text', sa.Text(), nullable=False),
            sa.Column('page_number', sa.Integer(), nullable=True),
            sa.Column('section', sa.String(length=255), nullable=True),
            sa.Column('document_type', sa.String(length=50), nullable=False),
            sa.Column('extraction_method', sa.String(length=50), nullable=False),
            sa.Column('metadata_payload', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_document_chunks_document_id'), 'document_chunks', ['document_id'], unique=False)
        op.create_index(op.f('ix_document_chunks_chunk_index'), 'document_chunks', ['chunk_index'], unique=False)

def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    tables = inspector.get_table_names()
    if 'document_chunks' in tables:
        op.drop_index(op.f('ix_document_chunks_chunk_index'), table_name='document_chunks')
        op.drop_index(op.f('ix_document_chunks_document_id'), table_name='document_chunks')
        op.drop_table('document_chunks')
        
    columns = [c['name'] for c in inspector.get_columns('documents')]
    if 'processing_error' in columns:
        op.drop_column('documents', 'processing_error')

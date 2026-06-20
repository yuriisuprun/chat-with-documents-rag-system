"""Add multi-language support to conversations and messages.

Revision ID: 002
Revises: 001_initial_schema
Create Date: 2026-06-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema for multi-language support."""
    
    # Add language fields to conversations table
    op.add_column(
        'conversations',
        sa.Column('detected_language', sa.String(10), server_default='en', nullable=False)
    )
    op.add_column(
        'conversations',
        sa.Column('language_confidence', sa.Float(), nullable=True)
    )
    op.create_index(
        'ix_conversations_language',
        'conversations',
        ['detected_language']
    )
    
    # Add language fields to messages table
    op.add_column(
        'messages',
        sa.Column('detected_language', sa.String(10), nullable=True)
    )
    op.add_column(
        'messages',
        sa.Column('language_confidence', sa.Float(), nullable=True)
    )
    op.create_index(
        'ix_messages_language',
        'messages',
        ['detected_language']
    )
    
    # Add language field to document_chunks table
    op.add_column(
        'document_chunks',
        sa.Column('detected_language', sa.String(10), nullable=True)
    )
    op.create_index(
        'ix_document_chunks_language',
        'document_chunks',
        ['detected_language']
    )


def downgrade() -> None:
    """Downgrade database schema (remove language fields)."""
    
    # Remove from document_chunks
    op.drop_index('ix_document_chunks_language', table_name='document_chunks')
    op.drop_column('document_chunks', 'detected_language')
    
    # Remove from messages
    op.drop_index('ix_messages_language', table_name='messages')
    op.drop_column('messages', 'language_confidence')
    op.drop_column('messages', 'detected_language')
    
    # Remove from conversations
    op.drop_index('ix_conversations_language', table_name='conversations')
    op.drop_column('conversations', 'language_confidence')
    op.drop_column('conversations', 'detected_language')

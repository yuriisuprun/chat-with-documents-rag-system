"""Initial schema migration."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial schema for single-tenant system."""
    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('client_phone', sa.String(20), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('last_client_message_at', sa.DateTime()),
        sa.Column('last_professional_message_at', sa.DateTime()),
        sa.Column('last_ai_message_at', sa.DateTime()),
        sa.Column('metadata', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_conversations_client_phone', 'conversations', ['client_phone'])
    op.create_index('ix_conversations_status', 'conversations', ['status'])
    op.create_index('ix_conversations_phone_created', 'conversations', ['client_phone', 'created_at'])

    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('conversation_id', sa.String(), nullable=False),
        sa.Column('sender', sa.Enum('client', 'professional', 'ai', name='messagesender'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('media_type', sa.String(50)),
        sa.Column('media_url', sa.String(500)),
        sa.Column('transcript', sa.Text()),
        sa.Column('detected_intent', sa.Enum('appointment_request', 'office_hours', 'fee_question', 'service_information', 'document_submission', 'legal_question', 'other', name='intent'), nullable=True),
        sa.Column('is_auto_reply', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('metadata', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_messages_conversation_id', 'messages', ['conversation_id'])
    op.create_index('ix_messages_sender', 'messages', ['sender'])
    op.create_index('ix_messages_is_auto_reply', 'messages', ['is_auto_reply'])
    op.create_index('ix_messages_conversation_created', 'messages', ['conversation_id', 'created_at'])
    op.create_index('ix_messages_sender_intent', 'messages', ['sender', 'detected_intent'])

    # Create knowledge_documents table
    op.create_table(
        'knowledge_documents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('file_type', sa.String(50), nullable=False),
        sa.Column('file_size_bytes', sa.Integer()),
        sa.Column('section_title', sa.String(255)),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_knowledge_documents_is_active', 'knowledge_documents', ['is_active'])

    # Create document_chunks table
    op.create_table(
        'document_chunks',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('document_id', sa.String(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', postgresql.UUID(as_uuid=False)),  # Will be Vector type
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['knowledge_documents.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_document_chunks_document', 'document_chunks', ['document_id'])

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('conversation_id', sa.String()),
        sa.Column('action', sa.String(255), nullable=False),
        sa.Column('details', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_audit_logs_created', 'audit_logs', ['created_at'])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index('ix_audit_logs_created', table_name='audit_logs')
    op.drop_table('audit_logs')
    op.drop_index('ix_document_chunks_document', table_name='document_chunks')
    op.drop_table('document_chunks')
    op.drop_index('ix_knowledge_documents_is_active', table_name='knowledge_documents')
    op.drop_table('knowledge_documents')
    op.drop_index('ix_messages_sender_intent', table_name='messages')
    op.drop_index('ix_messages_conversation_created', table_name='messages')
    op.drop_index('ix_messages_is_auto_reply', table_name='messages')
    op.drop_index('ix_messages_sender', table_name='messages')
    op.drop_index('ix_messages_conversation_id', table_name='messages')
    op.drop_table('messages')
    op.drop_index('ix_conversations_phone_created', table_name='conversations')
    op.drop_index('ix_conversations_status', table_name='conversations')
    op.drop_index('ix_conversations_client_phone', table_name='conversations')
    op.drop_table('conversations')

"""initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-05 22:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'customers',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('account_created_at', sa.DateTime(), nullable=False),
        sa.Column('total_orders', sa.Numeric(precision=10, scale=0), nullable=True),
        sa.Column('historical_disputes', sa.Numeric(precision=10, scale=0), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_customers_email', 'customers', ['email'], unique=False)

    op.create_table(
        'transactions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('customer_id', sa.String(length=36), nullable=False),
        sa.Column('razorpay_payment_id', sa.String(length=100), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('payment_method', sa.String(length=50), nullable=False),
        sa.Column('device_fingerprint', sa.String(length=100), nullable=False),
        sa.Column('ip_country', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('razorpay_payment_id')
    )
    op.create_index('ix_transactions_customer_id', 'transactions', ['customer_id'], unique=False)
    op.create_index('ix_transactions_razorpay_payment_id', 'transactions', ['razorpay_payment_id'], unique=True)

    op.create_table(
        'orders',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('transaction_id', sa.String(length=36), nullable=False),
        sa.Column('delivery_status', sa.String(length=50), nullable=False),
        sa.Column('tracking_number', sa.String(length=100), nullable=True),
        sa.Column('carrier_delivered_at', sa.DateTime(), nullable=True),
        sa.Column('shipping_address_hash', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('transaction_id')
    )

    op.create_table(
        'disputes',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('transaction_id', sa.String(length=36), nullable=False),
        sa.Column('razorpay_dispute_id', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('dispute_amount', sa.Float(), nullable=False),
        sa.Column('reason_code', sa.String(length=100), nullable=False),
        sa.Column('respond_by', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('razorpay_dispute_id')
    )
    op.create_index('ix_disputes_razorpay_dispute_id', 'disputes', ['razorpay_dispute_id'], unique=True)
    op.create_index('ix_disputes_status', 'disputes', ['status'], unique=False)

    op.create_table(
        'risk_scores',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('dispute_id', sa.String(length=36), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('risk_level', sa.String(length=20), nullable=False),
        sa.Column('feature_contributions', sa.JSON(), nullable=True),
        sa.Column('model_version', sa.String(length=50), nullable=False),
        sa.Column('calculated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['dispute_id'], ['disputes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'evidence',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('dispute_id', sa.String(length=36), nullable=False),
        sa.Column('evidence_type', sa.String(length=50), nullable=False),
        sa.Column('evidence_metadata', sa.JSON(), nullable=True),
        sa.Column('verified', sa.Boolean(), nullable=False),
        sa.Column('assembled_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['dispute_id'], ['disputes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'decisions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('dispute_id', sa.String(length=36), nullable=False),
        sa.Column('recommendation', sa.String(length=20), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('executive_summary', sa.Text(), nullable=False),
        sa.Column('supporting_evidence', sa.JSON(), nullable=True),
        sa.Column('contradicting_evidence', sa.JSON(), nullable=True),
        sa.Column('human_approval_required', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['dispute_id'], ['disputes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('dispute_id', sa.String(length=36), nullable=True),
        sa.Column('actor_type', sa.String(length=50), nullable=False),
        sa.Column('actor_id', sa.String(length=100), nullable=False),
        sa.Column('action_taken', sa.String(length=100), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['dispute_id'], ['disputes.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'webhook_events',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('event_id', sa.String(length=100), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('processed', sa.Boolean(), nullable=False),
        sa.Column('received_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id')
    )

def downgrade() -> None:
    op.drop_table('webhook_events')
    op.drop_table('audit_logs')
    op.drop_table('decisions')
    op.drop_table('evidence')
    op.drop_table('risk_scores')
    op.drop_table('disputes')
    op.drop_table('orders')
    op.drop_table('transactions')
    op.drop_table('customers')

"""Add certificates_count and servers table

Revision ID: 004
Revises: 003
Create Date: 2024-12-17 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('certificates_count', sa.Integer(), nullable=True, server_default='1'))
    op.execute("UPDATE users SET certificates_count = 1 WHERE certificates_count IS NULL")
    op.alter_column('users', 'certificates_count', nullable=False)
    
    op.create_table(
        'servers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_servers_id'), 'servers', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_servers_id'), table_name='servers')
    op.drop_table('servers')
    op.drop_column('users', 'certificates_count')


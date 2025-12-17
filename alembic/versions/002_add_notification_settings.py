"""Add notification settings to users

Revision ID: 002
Revises: 001
Create Date: 2024-12-17 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Добавляем поля для настроек уведомлений
    op.add_column('users', sa.Column('enable_billing_notifications', sa.Boolean(), nullable=True, server_default='true'))
    op.add_column('users', sa.Column('notify_before_billing_days', sa.Integer(), nullable=True, server_default='2'))
    
    # Обновляем существующие записи, устанавливая значения по умолчанию
    op.execute("UPDATE users SET enable_billing_notifications = true WHERE enable_billing_notifications IS NULL")
    op.execute("UPDATE users SET notify_before_billing_days = 2 WHERE notify_before_billing_days IS NULL")
    
    # Делаем поля NOT NULL после установки значений по умолчанию
    op.alter_column('users', 'enable_billing_notifications', nullable=False)
    op.alter_column('users', 'notify_before_billing_days', nullable=False)


def downgrade() -> None:
    # Удаляем поля при откате миграции
    op.drop_column('users', 'notify_before_billing_days')
    op.drop_column('users', 'enable_billing_notifications')


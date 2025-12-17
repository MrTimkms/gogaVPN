"""Add negative balance notification setting

Revision ID: 003
Revises: 002
Create Date: 2024-12-17 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Добавляем поле для настройки уведомлений об отрицательном балансе
    op.add_column('users', sa.Column('enable_negative_balance_notifications', sa.Boolean(), nullable=True, server_default='true'))
    
    # Обновляем существующие записи
    op.execute("UPDATE users SET enable_negative_balance_notifications = true WHERE enable_negative_balance_notifications IS NULL")
    
    # Делаем поле NOT NULL после установки значений по умолчанию
    op.alter_column('users', 'enable_negative_balance_notifications', nullable=False)


def downgrade() -> None:
    # Удаляем поле при откате миграции
    op.drop_column('users', 'enable_negative_balance_notifications')


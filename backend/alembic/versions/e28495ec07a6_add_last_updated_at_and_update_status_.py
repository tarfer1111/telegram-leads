# backend/alembic/versions/e28495ec07a6_add_last_updated_at_and_update_status_values.py

"""add_last_updated_at_and_update_status_values

Revision ID: e28495ec07a6
Revises: 0000cf35a290
Create Date: 2025-10-26 15:47:03.552154

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e28495ec07a6'
down_revision: Union[str, None] = '0000cf35a290'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем колонку last_updated_at
    op.add_column('leads', sa.Column('last_updated_at', sa.DateTime(), nullable=True))
    
    # Заполняем существующие записи значением created_at
    op.execute("UPDATE leads SET last_updated_at = created_at WHERE last_updated_at IS NULL")
    
    # Делаем колонку NOT NULL после заполнения
    op.alter_column('leads', 'last_updated_at', nullable=False)
    
    # Обновляем существующие статусы: 'active' -> 'new'
    op.execute("UPDATE leads SET status = 'new' WHERE status = 'active'")


def downgrade() -> None:
    # Откатываем статусы обратно
    op.execute("UPDATE leads SET status = 'active' WHERE status = 'new' OR status = 'in_progress'")
    
    # Удаляем колонку
    op.drop_column('leads', 'last_updated_at')
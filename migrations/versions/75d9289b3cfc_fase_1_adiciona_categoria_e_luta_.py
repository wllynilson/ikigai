"""FASE 1: Adiciona Categoria e Luta, categoria_id é opcional

Revision ID: 75d9289b3cfc
Revises: 1ad9b881ed05
Create Date: 2025-06-26 20:45:38.613798

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '75d9289b3cfc'
down_revision = '1ad9b881ed05'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('inscricoes', schema=None) as batch_op:
        batch_op.alter_column('categoria_id',
               existing_type=sa.INTEGER(),
               nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('inscricoes', schema=None) as batch_op:
        batch_op.alter_column('categoria_id',
               existing_type=sa.INTEGER(),
               nullable=False)

    # ### end Alembic commands ###

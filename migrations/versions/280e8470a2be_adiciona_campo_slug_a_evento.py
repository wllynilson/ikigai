"""Adiciona campo slug a Evento

Revision ID: 280e8470a2be
Revises: 810d4d776afb
Create Date: 2025-07-04 10:20:59.068012

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '280e8470a2be'
down_revision = '810d4d776afb'
branch_labels = None
depends_on = None


def upgrade():
    # Etapa A: Adiciona a coluna como OPCIONAL. Isto funciona sem batch no SQLite.
    op.add_column('eventos', sa.Column('slug', sa.String(length=255), nullable=True))

    # Etapa B: Preenche os dados para as linhas que já existem.
    op.execute("UPDATE eventos SET slug = lower(replace(nome_evento, ' ', '-')) || '-' || id")

    # Etapa C e D: Usa o 'batch_alter_table' para as operações que o SQLite não suporta nativamente.
    with op.batch_alter_table('eventos', schema=None) as batch_op:
        # Torna a coluna obrigatória
        batch_op.alter_column('slug',
                              existing_type=sa.VARCHAR(length=255),
                              nullable=False)
        # Cria o índice de unicidade
        batch_op.create_index(batch_op.f('ix_eventos_slug'), ['slug'], unique=True)



def downgrade():
    with op.batch_alter_table('eventos', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_eventos_slug'))

    op.drop_column('eventos', 'slug')
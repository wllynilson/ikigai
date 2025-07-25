"""Versão 2.0 - Refatoração do banco de dados com Participantes e Pagamentos

Revision ID: b911b310c0a9
Revises: 
Create Date: 2025-06-29 17:14:22.945023

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b911b310c0a9'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('equipes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nome_equipe', sa.String(length=100), nullable=False),
    sa.Column('professor_responsavel', sa.String(length=100), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('nome_equipe')
    )
    op.create_table('eventos',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nome_evento', sa.String(length=200), nullable=False),
    sa.Column('data_hora_evento', sa.DateTime(), nullable=False),
    sa.Column('palestrante', sa.String(length=100), nullable=True),
    sa.Column('imagem_palestrante', sa.String(length=300), nullable=True),
    sa.Column('descricao', sa.Text(), nullable=True),
    sa.Column('local_evento', sa.String(length=200), nullable=True),
    sa.Column('preco', sa.Float(), nullable=True),
    sa.Column('numero_vagas', sa.Integer(), nullable=False),
    sa.Column('pix_copia_e_cola', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=64), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('password_hash', sa.String(length=256), nullable=True),
    sa.Column('role', sa.String(length=20), nullable=False),
    sa.Column('nome_completo', sa.String(length=150), nullable=True),
    sa.Column('bio', sa.Text(), nullable=True),
    sa.Column('imagem_perfil', sa.String(length=300), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_users_email'), ['email'], unique=True)
        batch_op.create_index(batch_op.f('ix_users_username'), ['username'], unique=True)

    op.create_table('categorias',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nome', sa.String(length=100), nullable=False),
    sa.Column('evento_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['evento_id'], ['eventos.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('membros_equipe',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('equipe_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['equipe_id'], ['equipes.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('user_id', 'equipe_id')
    )
    op.create_table('participantes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nome_completo', sa.String(length=150), nullable=False),
    sa.Column('data_nascimento', sa.Date(), nullable=True),
    sa.Column('cpf', sa.String(length=14), nullable=False),
    sa.Column('telefone', sa.String(length=20), nullable=True),
    sa.Column('graduacao', sa.String(length=50), nullable=True),
    sa.Column('peso', sa.Float(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('equipe_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['equipe_id'], ['equipes.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('cpf'),
    sa.UniqueConstraint('user_id')
    )
    op.create_table('inscricoes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('data_inscricao', sa.DateTime(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('participante_id', sa.Integer(), nullable=False),
    sa.Column('categoria_id', sa.Integer(), nullable=False),
    sa.Column('registrado_por_user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['categoria_id'], ['categorias.id'], ),
    sa.ForeignKeyConstraint(['participante_id'], ['participantes.id'], ),
    sa.ForeignKeyConstraint(['registrado_por_user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('participante_id', 'categoria_id', name='uq_participante_categoria')
    )
    op.create_table('lutas',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('round', sa.Integer(), nullable=False),
    sa.Column('ordem_na_chave', sa.Integer(), nullable=False),
    sa.Column('categoria_id', sa.Integer(), nullable=False),
    sa.Column('competidor1_id', sa.Integer(), nullable=True),
    sa.Column('competidor2_id', sa.Integer(), nullable=True),
    sa.Column('vencedor_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['categoria_id'], ['categorias.id'], ),
    sa.ForeignKeyConstraint(['competidor1_id'], ['participantes.id'], ),
    sa.ForeignKeyConstraint(['competidor2_id'], ['participantes.id'], ),
    sa.ForeignKeyConstraint(['vencedor_id'], ['participantes.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('pagamentos',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('valor', sa.Float(), nullable=False),
    sa.Column('data_pagamento', sa.DateTime(), nullable=True),
    sa.Column('metodo', sa.String(length=50), nullable=False),
    sa.Column('status_pagamento', sa.String(length=30), nullable=False),
    sa.Column('id_transacao_externa', sa.String(length=200), nullable=True),
    sa.Column('inscricao_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['inscricao_id'], ['inscricoes.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('inscricao_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('pagamentos')
    op.drop_table('lutas')
    op.drop_table('inscricoes')
    op.drop_table('participantes')
    op.drop_table('membros_equipe')
    op.drop_table('categorias')
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_username'))
        batch_op.drop_index(batch_op.f('ix_users_email'))

    op.drop_table('users')
    op.drop_table('eventos')
    op.drop_table('equipes')
    # ### end Alembic commands ###

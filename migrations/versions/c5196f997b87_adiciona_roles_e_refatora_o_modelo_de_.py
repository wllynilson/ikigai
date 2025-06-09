# Ficheiro: migrations/versions/c5196f997b87_....py

"""Adiciona roles e refatora o modelo de inscrição"""
from alembic import op
import sqlalchemy as sa


# ### início das etiquetas de identificação ###
# Substitua os valores abaixo se necessário

revision = 'c5196f997b87'
down_revision = '28615c698124' # ID da migração ANTERIOR
branch_labels = None
depends_on = None

# ... (revision identifiers) ...

def upgrade():
    # ### Início dos comandos corrigidos ###

    # Agrupa todas as alterações para a tabela 'users'
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('role', sa.String(length=20), nullable=False, server_default='user'))
        batch_op.add_column(sa.Column('cpf', sa.String(length=14), nullable=True))
        batch_op.add_column(sa.Column('telefone', sa.String(length=20), nullable=True))
        batch_op.create_unique_constraint('uq_users_cpf', ['cpf'])

    # Agrupa todas as alterações para a tabela 'inscricao'
    # NOTA: O nome da sua tabela de Inscrição pode ser 'inscricoes'. Verifique no seu modelo.
    with op.batch_alter_table('inscricoes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=False))
        # Ajuste 'fk_inscricoes_user_id_users' se quiser um nome diferente para a chave estrangeira
        batch_op.create_foreign_key('fk_inscricoes_user_id_users', 'users', ['user_id'], ['id'])
        batch_op.drop_column('nome_participante')
        batch_op.drop_column('sobrenome_participante')
        batch_op.drop_column('idade')
        batch_op.drop_column('cpf')
        batch_op.drop_column('telefone')

    # ### Fim dos comandos corrigidos ###

def downgrade():
    # ### Início dos comandos corrigidos ###

    # Reverte as alterações na tabela 'inscricoes'
    with op.batch_alter_table('inscricoes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('telefone', sa.VARCHAR(length=20), nullable=False))
        batch_op.add_column(sa.Column('cpf', sa.VARCHAR(length=14), nullable=False))
        batch_op.add_column(sa.Column('nome_participante', sa.VARCHAR(length=100), nullable=False))
        batch_op.add_column(sa.Column('sobrenome_participante', sa.VARCHAR(length=100), nullable=False))
        batch_op.add_column(sa.Column('idade', sa.INTEGER(), nullable=False))
        batch_op.drop_constraint('fk_inscricoes_user_id_users', type_='foreignkey')
        batch_op.drop_column('user_id')

    # Reverte as alterações na tabela 'users'
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint('uq_users_cpf', type_='unique')
        batch_op.drop_column('telefone')
        batch_op.drop_column('cpf')
        batch_op.drop_column('role')

    # ### Fim dos comandos corrigidos ###
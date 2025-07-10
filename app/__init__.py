import locale
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
import click
import csv
from sqlalchemy import text

from config import Config  # Importa a classe de configuração

# Define o locale para Português do Brasil
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
    print("Locale configurado para pt_BR.UTF-8")
except locale.Error:
    print("Locale pt_BR.UTF-8 não encontrado, usando o padrão do sistema.")
    locale.setlocale(locale.LC_ALL, '')

# 1. Instanciação das Extensões (a nível global, sem app)
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

# 2. Configuração do LoginManager
login_manager.login_view = 'auth.login'
login_manager.login_message = "Por favor, faça login para acessar a esta página."
login_manager.login_message_category = "info"


def create_app(config_class=Config):
    """
    Função 'Application Factory' para criar e configurar a aplicação Flask.

    Args:
        config_class: Classe de configuração a ser utilizada (padrão: Config)

    Returns:
        Uma instância configurada da aplicação Flask
    """
    # 3. Criação e Configuração da Aplicação
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 4. Inicialização das Extensões
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    app.logger.info('Aplicação inicializada com sucesso')

    # 5. Importar e Registar as Blueprints
    with app.app_context():
        # Importamos as blueprints aqui para evitar importações circulares
        from . import routes as public_bp
        app.register_blueprint(public_bp.public_bp)

        from .admin import routes as admin_routes
        app.register_blueprint(admin_routes.bp, url_prefix='/admin')

        from .auth import routes as auth_routes
        app.register_blueprint(auth_routes.auth_bp)

        from app.errors import bp as errors_bp
        app.register_blueprint(errors_bp)

        # 6. Registar Comandos CLI Personalizados
        @app.cli.command("init-db")
        def init_db_command():
            """Cria todas as tabelas do banco de dados."""
            try:
                db.create_all()
                click.echo("Banco de dados inicializado com sucesso.")
                app.logger.info("Banco de dados inicializado com sucesso.")
            except Exception as e:
                click.echo(f"Erro ao inicializar o banco de dados: {e}")
                app.logger.error(f"Erro ao inicializar o banco de dados: {e}")

        # --- Injetor de Contexto para o Ano Atual ---
        @app.context_processor
        def inject_current_year():
            from datetime import timezone
            return {'current_year': datetime.now(timezone.utc).year}
        # --- Fim do Injetor ---

        @app.cli.command("import-data")
        def import_data_command():
            """Importa dados dos ficheiros CSV para o novo schema refatorado."""
            from .models import User, Participante, Equipe, Evento, Categoria, Inscricao, Pagamento

            try:
                # Usaremos um dicionário para mapear o ID antigo do user para o ID do novo participante
                old_user_to_new_participant = {}

                # --- 1. Importar EQUIPES (se tiver um export_equipes.csv) ---
                # (Pode adicionar a lógica aqui se tiver exportado as equipes)
                print("A verificar equipes...")

                # --- 2. Importar USUARIOS e criar PARTICIPANTES com limpeza de dados ---
                print("A importar Utilizadores e a criar Perfis de Participante...")
                with open('export_users.csv', 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Cria o User com os dados do CSV
                        user = User(
                            id=row['id'],  # Mantém o ID original
                            username=row['username'],
                            email=row['email'],
                            password_hash=row['password_hash'],
                            role=row['role'],
                            nome_completo=row.get('nome_completo') or row['username']
                        )

                        # --- INÍCIO DA LÓGICA DE LIMPEZA DO CPF ---
                        cpf_bruto = row.get('cpf') or ''  # Pega o CPF do CSV

                        # 1. Extrai apenas os dígitos do CPF
                        digitos_cpf = ''.join(c for c in cpf_bruto if c.isdigit())

                        # 2. Se tiver exatamente 11 dígitos, formata-o. Senão, cria um valor de placeholder.
                        if len(digitos_cpf) == 11:
                            cpf_formatado = f"{digitos_cpf[:3]}.{digitos_cpf[3:6]}.{digitos_cpf[6:9]}-{digitos_cpf[9:]}"
                        else:
                            # Se o CPF no CSV for inválido, gera um valor temporário para não quebrar a importação
                            # E avisa no console para que você possa corrigir manualmente depois
                            cpf_formatado = f"INVALIDO-{row['id']}"
                            print(
                                f"AVISO: CPF inválido ou em branco encontrado para o utilizador '{row['username']}'. Usando valor temporário: {cpf_formatado}")
                        # --- FIM DA LÓGICA DE LIMPEZA ---

                        # Encontra a equipe (ou usa uma padrão)
                        equipe = Equipe.query.filter_by(nome_equipe='Equipe Padrão').first()
                        if not equipe:
                            equipe = Equipe(nome_equipe='Equipe Padrão', professor_responsavel='Admin')
                            db.session.add(equipe)
                            db.session.flush()

                        # Cria o Participante correspondente usando o CPF formatado
                        participante = Participante(
                            nome_completo=row.get('nome_completo') or row['username'],
                            cpf=cpf_formatado,  # <-- Usa a variável limpa e formatada
                            telefone=row.get('telefone') or '(00)0000-0000',
                            equipe_id=equipe.id,
                            user_id=user.id  # Liga o participante ao user
                        )

                        # Usamos merge para inserir ou atualizar, o que é mais seguro
                        db.session.merge(user)
                        db.session.merge(participante)

                db.session.commit()
                print(f"-> Utilizadores e Participantes importados/atualizados.")

                # --- 3. Importar INSCRIÇÕES ---
                print("A importar Inscrições antigas...")
                with open('export_inscricoes.csv', 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Encontra o ID do novo participante a partir do ID do user antigo
                        participante_id = old_user_to_new_participant.get(row['user_id_antigo'])
                        if participante_id:
                            # Para cada inscrição antiga, atribui a uma categoria "Geral" do evento
                            evento_id = row['evento_id']
                            categoria_geral = Categoria.query.filter_by(evento_id=evento_id, nome='Geral').first()
                            if not categoria_geral:
                                categoria_geral = Categoria(nome='Geral', evento_id=evento_id)
                                db.session.add(categoria_geral)
                                db.session.flush()

                            nova_inscricao = Inscricao(
                                id=row['id'],  # Mantém o ID antigo se possível
                                status=row['status'],
                                participante_id=participante_id,
                                categoria_id=categoria_geral.id,
                                registrado_por_user_id=row['user_id_antigo']
                            )
                            db.session.merge(nova_inscricao)  # Usa merge para inserir ou atualizar

                db.session.commit()
                print("-> Inscrições importadas com sucesso.")
                click.echo("Importação de dados concluída!")

            except FileNotFoundError as e:
                click.echo(
                    f"Erro: Ficheiro não encontrado - {e}. Certifique-se que os ficheiros CSV estão na pasta raiz do projeto.")
            except Exception as e:
                db.session.rollback()
                click.echo(f"Ocorreu um erro durante a importação: {e}")

    return app


# 7. Importar modelos e definir o user_loader
from . import models


@login_manager.user_loader
def load_user(user_id):
    """
    Carrega o utilizador a partir do ID para o Flask-Login.

    Args:
        user_id: ID do usuário a ser carregado

    Returns:
        Objeto User correspondente ao ID ou None se não existir
    """
    return models.User.query.get(int(user_id))
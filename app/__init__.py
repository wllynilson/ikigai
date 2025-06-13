import locale

try:
    # Define o locale para Português do Brasil para toda a aplicação
    # Isto irá afetar a formatação de datas, moedas, etc.
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    # Fallback para o locale padrão do sistema se pt_BR.UTF-8 não estiver instalado
    print("Locale pt_BR.UTF-8 não encontrado, usando o padrão do sistema.")
    locale.setlocale(locale.LC_ALL, '')


from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import click

from config import Config  # Importa a classe de configuração

# 1. Instanciação das Extensões (a nível global, sem app)
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

# 2. Configuração do LoginManager (as configurações que não dependem da 'app' podem ser feitas aqui)
login_manager.login_view = 'auth.login'
login_manager.login_message = "Por favor, faça login para acessar a esta página."
login_manager.login_message_category = "info"


def create_app(config_class=Config):
    """
    Função 'Application Factory' para criar e configurar a aplicação Flask.
    """
    # 3. Criação e Configuração da Aplicação
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 4. Inicialização das Extensões (ligando-as à instância 'app')
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # 5. Importar e Registar as Blueprints
    with app.app_context():
        # Importamos as blueprints aqui para evitar importações circulares
        from . import routes as public_bp
        app.register_blueprint(public_bp.public_bp)

        from .admin import routes as admin_routes
        app.register_blueprint(admin_routes.bp, url_prefix='/admin')

        from .auth import routes as auth_routes
        app.register_blueprint(auth_routes.auth_bp)

        # 6. Registar Comandos CLI Personalizados
        @app.cli.command("init-db")
        def init_db_command():
            """Cria todas as tabelas do banco de dados."""
            db.create_all()
            click.echo("Banco de dados inicializado com sucesso.")

        # --- Injetor de Contexto para o Ano Atual ---
        @app.context_processor
        def inject_current_year():
            from datetime import datetime
            return {'current_year': datetime.utcnow().year}
        # --- Fim do Injetor ---

    return app

# 7. Importar modelos e definir o user_loader (fora da factory)
from . import models

@login_manager.user_loader
def load_user(user_id):
    """Carrega o utilizador a partir do ID para o Flask-Login."""
    return models.User.query.get(int(user_id))
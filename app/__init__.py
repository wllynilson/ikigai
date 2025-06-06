# app/__init__.py (ATUALIZADO)
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import click # Importe a biblioteca Click

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../academia.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'sua_chave_secreta_muito_segura_aqui'

    db.init_app(app)

    from . import models

    from .routes import public_bp
    app.register_blueprint(public_bp)

    from .admin.routes import bp as admin_blueprint
    app.register_blueprint(admin_blueprint)

    # --- NOVO CÓDIGO AQUI ---
    # Adiciona um novo comando de terminal ao flask
    @app.cli.command("init-db")
    def init_db_command():
        """Limpa os dados existentes e cria novas tabelas."""
        db.create_all()
        click.echo("Banco de dados inicializado.")
    # --- FIM DO NOVO CÓDIGO ---

    return app
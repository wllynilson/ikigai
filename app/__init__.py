from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import click
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Por favor, faça login para aceder a esta página."
    login_manager.login_message_category = "info"
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../academia.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'sua_chave_secreta_muito_segura_aqui'

    db.init_app(app)
    migrate.init_app(app, db)

    from . import models
    from .models import User  # Importe aqui, após o db estar inicializado

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .routes import public_bp
    app.register_blueprint(public_bp)

    from .admin.routes import bp as admin_blueprint
    app.register_blueprint(admin_blueprint)

    from app.auth.routes import auth_bp
    app.register_blueprint(auth_bp)

    @app.cli.command("init-db")
    def init_db_command():
        db.create_all()
        click.echo("Banco de dados inicializado.")

    return app
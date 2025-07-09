# Ficheiro: app/errors/__init__.py
from flask import Blueprint

# Cria a blueprint para os erros
bp = Blueprint('errors', __name__)

# Importa os manipuladores para que sejam registados
from app.errors import handlers
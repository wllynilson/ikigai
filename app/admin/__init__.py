from flask import Blueprint

# O url_prefix='/admin' já foi adicionado na rota principal do blueprint
bp = Blueprint('admin', __name__, template_folder='templates')

# Importação relativa: o '.' significa 'do mesmo pacote'
from . import routes
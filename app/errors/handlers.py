# Ficheiro: app/errors/handlers.py
from flask import render_template
from app.errors import bp

# Manipulador para o erro 403 (Acesso Proibido)
@bp.app_errorhandler(403)
def forbidden_error(error):
    return render_template('errors/403.html'), 403

# Manipulador para o erro 404 (Página Não Encontrada)
@bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404
# Ficheiro: app/decorators.py

from functools import wraps
from flask import abort
from flask_login import current_user

def admin_required(f):
    """
    Decorador que verifica se o utilizador está logado E se tem o papel 'admin'.
    Se não for o caso, retorna um erro 403 (Forbidden).
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403) # O erro 403 significa 'Acesso Proibido'
        return f(*args, **kwargs)
    return decorated_function
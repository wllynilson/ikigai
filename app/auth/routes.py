# Ficheiro: app/auth/routes.py
from flask import render_template, flash, redirect, url_for, Blueprint, request
from flask_login import login_user, logout_user, current_user
from app.auth.forms import LoginForm
from app.models import User
from app import db # Certifique-se que o db está acessível
import uuid # Importa a biblioteca uuid

auth_bp = Blueprint('auth', __name__, template_folder='templates')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.rota_dashboard')) # Já está logado, vai para o dashboard

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Nome de utilizador ou palavra-passe inválida.', 'danger')
            return redirect(url_for('auth.login'))

        login_user(user, remember=form.remember_me.data)
        flash('Login efetuado com sucesso!', 'success')
        return redirect(url_for('admin.rota_dashboard'))

    return render_template('auth/login.html', title='Login', form=form)

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('public.index'))

# ROTA TEMPORÁRIA E SECRETA PARA CRIAR O PRIMEIRO ADMIN
# IMPORTANTE: REMOVA ESTA ROTA APÓS USÁ-LA PELA PRIMEIRA VEZ
@auth_bp.route('/criar-admin-inicial/<secret_key>')
def criar_admin_inicial(secret_key):
    # Para um pouco mais de segurança, use uma chave que só você sabe
    # O ideal seria ler esta chave de uma variável de ambiente
    if secret_key != 'meu-segredo-super-secreto':
        return "Acesso negado", 403

    # Verifica se o admin já não existe para não dar erro
    if User.query.filter_by(username='admin').first():
        return "O utilizador 'admin' já existe."

    try:
        # Cria o utilizador com os dados desejados
        user = User(username='admin', email='wllynilson@gmail.com')
        user.set_password('@@123@@abc') # TROQUE ESTA SENHA
        db.session.add(user)
        db.session.commit()
        return "Utilizador admin criado com sucesso!"
    except Exception as e:
        db.session.rollback()
        return f"Erro ao criar utilizador: {e}", 500

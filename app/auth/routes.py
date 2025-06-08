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

# Ficheiro: app/auth/routes.py
from flask import render_template, flash, redirect, url_for, Blueprint, request
from flask_login import login_user, logout_user, current_user, login_required

from app import db  # Importe o db
from app.auth.forms import EditarPerfilForm
from app.auth.forms import LoginForm, RegistrationForm
from app.models import User

auth_bp = Blueprint('auth', __name__, template_folder='templates')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('public.index')) # Já está logado, vai para o dashboard

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Nome de usuário ou senha inválida.', 'danger')
            return redirect(url_for('auth.login'))

        login_user(user, remember=form.remember_me.data)
        flash('Login efetuado com sucesso!', 'success')
        return redirect(url_for('public.index'))

    return render_template('auth/login.html', title='Login', form=form)

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('public.index'))

@auth_bp.route('/perfil')
@login_required
def perfil():
    """Exibe a página de perfil do utilizador atualmente logado."""
    return render_template('auth/perfil.html', title='Meu Perfil')


@auth_bp.route('/perfil/editar', methods=['GET', 'POST'])
@login_required
def editar_perfil():
    """Exibe e processa o formulário de edição de perfil."""
    form = EditarPerfilForm()

    # Se o formulário for submetido e for válido
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.nome_completo = form.nome_completo.data
        current_user.bio = form.bio.data
        current_user.imagem_perfil = form.imagem_perfil.data
        db.session.commit()
        flash('O seu perfil foi atualizado com sucesso!', 'success')
        return redirect(url_for('auth.perfil'))

    # Se a página for carregada pela primeira vez (GET)
    elif request.method == 'GET':
        # Preenche o formulário com os dados atuais do utilizador
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.nome_completo.data = current_user.nome_completo
        form.bio.data = current_user.bio
        form.imagem_perfil.data = current_user.imagem_perfil

    return render_template('auth/editar_perfil.html', title='Editar Perfil', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # Se o utilizador já estiver logado, não deve poder registar-se novamente
    if current_user.is_authenticated:
        return redirect(url_for('public.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        # Cria a nova instância de User com os dados do formulário
        user = User(
            username=form.username.data,
            email=form.email.data,
            nome_completo=form.nome_completo.data,
            cpf=form.cpf.data,
            telefone=form.telefone.data
        )
        user.set_password(form.password.data)  # Cifra a palavra-passe

        # O 'role' será 'user' por defeito, como definimos no modelo
        db.session.add(user)
        db.session.commit()

        flash('Parabéns, o seu registo foi efetuado com sucesso!', 'success')
        return redirect(url_for('auth.login'))  # Redireciona para a página de login

    return render_template('auth/register.html', title='Registar', form=form)

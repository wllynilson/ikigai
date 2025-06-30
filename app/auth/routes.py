# Ficheiro: app/auth/routes.py
from flask import render_template, flash, redirect, url_for, Blueprint, request
from flask_login import login_user, logout_user, current_user, login_required

from app import db  # Importe o db
from app.auth.forms import EditarPerfilForm
from app.auth.forms import LoginForm, RegistrationForm
from app.models import User, Participante, Equipe  # Importe todos os modelos necessários

auth_bp = Blueprint('auth', __name__, template_folder='templates')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # Se um utilizador já logado aceder à página de login, redireciona-o
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('public.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user is None or not user.check_password(form.password.data):
            flash('Email ou senha inválida.', 'danger')
            return redirect(url_for('auth.login'))

        login_user(user, remember=form.remember_me.data)
        flash('Login efetuado com sucesso!', 'success')

        # --- LÓGICA DE REDIRECIONAMENTO CORRIGIDA ---
        next_page = request.args.get('next')
        # Se não houver uma página 'next' ou se for um link inseguro, decidimos para onde ir
        if not next_page or not next_page.startswith('/'):
            # Se o utilizador for admin, o destino padrão é o dashboard de admin
            if user.role == 'admin':
                next_page = url_for('admin.dashboard')
            # Se for um utilizador normal, o destino padrão é a página de perfil
            else:
                next_page = url_for('auth.perfil')

        return redirect(next_page)

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
    if current_user.is_authenticated:
        return redirect(url_for('public.index'))

    form = RegistrationForm()
    # Popula o menu dropdown com as equipas existentes
    form.equipe_id.choices = [(e.id, e.nome_equipe) for e in Equipe.query.order_by('nome_equipe').all()]

    if form.validate_on_submit():
        # Cria primeiro o objeto User
        user = User(
            username=form.username.data,
            email=form.email.data,
            nome_completo=form.nome_completo.data,
            role='user'  # Garante que o papel padrão é 'user'
        )
        user.set_password(form.password.data)

        # Cria o objeto Participante com os dados restantes
        participante = Participante(
            nome_completo=form.nome_completo.data,
            cpf=form.cpf.data,
            telefone=form.telefone.data,
            data_nascimento=form.data_nascimento.data,
            peso=form.peso.data,
            graduacao=form.graduacao.data,
            equipe_id=form.equipe_id.data
        )

        # Liga os dois objetos através da relação que definimos no modelo
        user.participante = participante

        try:
            # Ao adicionar o user, a relação com o participante (se configurada com cascade)
            # pode adicioná-lo automaticamente, mas adicionamos ambos para garantir.
            db.session.add(user)
            db.session.add(participante)
            db.session.commit()

            flash('Parabéns, a sua conta de usuário e perfil de atleta foram criados com sucesso!', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ocorreu um erro ao criar a sua conta: {e}', 'danger')

    return render_template('auth/register.html', title='Registar', form=form)
# Ficheiro: app/auth/forms.py
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import StringField, PasswordField, SubmitField, SelectField, FloatField
from wtforms.fields import EmailField, DateField
from wtforms.fields.simple import TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, Optional
from wtforms.validators import URL

from app.models import Participante
from app.models import User


class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email(message="Por favor, insira um email válido.")])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember_me = BooleanField('Lembrar-me')
    submit = SubmitField('Entrar')

class EditarPerfilForm(FlaskForm):
    """Formulário para o utilizador editar o seu perfil."""
    username = StringField('Usuário', validators=[DataRequired(), Length(min=2, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    nome_completo = StringField('Nome Completo', validators=[Optional(), Length(max=150)])
    bio = TextAreaField('Biografia', validators=[Optional(), Length(max=500)])
    imagem_perfil = StringField('URL da Imagem de Perfil', validators=[Optional(), URL()])
    submit = SubmitField('Salvar Alterações')

    def validate_username(self, username):
        """Verifica se o novo nome de utilizador já não está em uso por outra pessoa."""
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Este nome de utilizador já está em uso. Por favor, escolha outro.')

    def validate_email(self, email):
        """Verifica se o novo email já não está em uso por outra pessoa."""
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Este email já está em uso. Por favor, escolha outro.')


class RegistrationForm(FlaskForm):
    """Formulário para novos utilizadores se registarem, criando um User e um Participante."""
    # Campos para o modelo User
    username = StringField('Nome do usuário (para login)', validators=[DataRequired(), Length(min=3, max=64)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Palavra-passe', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField(
        'Repetir Palavra-passe',
        validators=[DataRequired(), EqualTo('password', message='As palavras-passe devem ser iguais.')])

    # Campos para o modelo Participante
    nome_completo = StringField('Nome Completo (do atleta)', validators=[DataRequired(), Length(max=150)])
    cpf = StringField('CPF', validators=[DataRequired()])
    telefone = StringField('Telefone', validators=[DataRequired()])
    data_nascimento = DateField('Nascimento', validators=[Optional()])
    peso = FloatField('Peso (kg)', validators=[Optional()])
    graduacao = StringField('Graduação', validators=[DataRequired()])
    equipe_id = SelectField('Sua Equipe', coerce=int, validators=[DataRequired()])

    submit = SubmitField('Criar Minha Conta')

    def validate_username(self, username):
        if User.query.filter_by(username=username.data).first():
            raise ValidationError('Este nome do usuário já existe. Por favor, escolha outro.')

    def validate_email(self, email):
        if User.query.filter_by(email=email.data).first():
            raise ValidationError('Este email já está a ser utilizado. Por favor, escolha outro.')

    def validate_cpf(self, cpf):
        if Participante.query.filter_by(cpf=cpf.data).first():
            raise ValidationError('Este CPF já está registado na nossa base de atletas.')
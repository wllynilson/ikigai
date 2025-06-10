# Ficheiro: app/auth/forms.py
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import StringField, PasswordField, SubmitField
from wtforms.fields.simple import TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from wtforms.validators import Length, Optional, URL

from app.models import User


class LoginForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired()])
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
    """Formulário para novos utilizadores se registarem."""
    username = StringField('Nome de Utilizador', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    nome_completo = StringField('Nome Completo', validators=[DataRequired(), Length(max=150)])
    cpf = StringField('CPF', validators=[DataRequired(), Length(min=11, max=14)])
    telefone = StringField('Telefone', validators=[DataRequired(), Length(min=8, max=20)])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField(
        'Repetir Senha', validators=[DataRequired(), EqualTo('password', message='As Senhas devem ser iguais.')])
    submit = SubmitField('Registar')

    # Validador personalizado para garantir que o username não existe
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Este nome de utilizador já existe. Por favor, escolha outro.')

    # Validador personalizado para garantir que o email não existe
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Este email já está a ser utilizado. Por favor, escolha outro.')

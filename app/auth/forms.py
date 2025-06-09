# Ficheiro: app/auth/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.fields.simple import TextAreaField
from wtforms.validators import DataRequired, ValidationError
from wtforms.validators import Length, Email, Optional, URL
from app.models import User
from flask_login import current_user


class LoginForm(FlaskForm):
    username = StringField('Nome de Utilizador', validators=[DataRequired()])
    password = PasswordField('Palavra-passe', validators=[DataRequired()])
    remember_me = BooleanField('Lembrar-me')
    submit = SubmitField('Entrar')

class EditarPerfilForm(FlaskForm):
    """Formulário para o utilizador editar o seu perfil."""
    username = StringField('Nome de Utilizador', validators=[DataRequired(), Length(min=2, max=64)])
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

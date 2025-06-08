# Ficheiro: app/admin/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange


class EditarInscricaoForm(FlaskForm):
    """
    Formulário para editar os dados de uma inscrição existente.
    """
    nome_participante = StringField('Nome do Participante',
                                    validators=[DataRequired(), Length(min=2, max=100)])

    sobrenome_participante = StringField('Sobrenome do Participante',
                                         validators=[DataRequired(), Length(min=2, max=100)])

    idade = IntegerField('Idade',
                         validators=[DataRequired(), NumberRange(min=5, max=120, message="Idade inválida.")])

    cpf = StringField('CPF',
                      validators=[DataRequired(), Length(min=11, max=14, message="CPF inválido.")])

    telefone = StringField('Telefone',
                           validators=[DataRequired(), Length(min=8, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Length(min=5, max=100)])

    submit = SubmitField('Salvar Alterações')
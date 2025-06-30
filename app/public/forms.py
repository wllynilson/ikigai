# Ficheiro: app/public/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange


class InscricaoEventoForm(FlaskForm):
    """Formulário simplificado para um utilizador logado se inscrever num evento."""
    categoria_id = SelectField('Selecione a Categoria para competir', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Confirmar Minha Inscrição')

class InscricaoTerceiroForm(FlaskForm):
    """Formulário para um utilizador logado inscrever outra pessoa."""
    nome_participante = StringField('Nome do Participante', validators=[DataRequired(), Length(max=100)])
    sobrenome_participante = StringField('Sobrenome', validators=[DataRequired(), Length(max=100)])
    idade = IntegerField('Idade', validators=[DataRequired(), NumberRange(min=1)])
    peso = FloatField('Peso (kg)', validators=[DataRequired(), NumberRange(min=0)], description="Use ponto como separador decimal, ex: 75.5")
    graduacao = StringField('Graduação', validators=[DataRequired(), Length(max=50)])
    cpf = StringField('CPF', validators=[DataRequired()])
    telefone = StringField('Telefone', validators=[DataRequired()])
    equipe_id = SelectField('Equipe', coerce=int, validators=[DataRequired()])
    categoria_id = SelectField('Categoria', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Finalizar Inscrição')

# Ficheiro: app/public/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange


class InscricaoEventoForm(FlaskForm):
    # Usamos 'coerce=int' para garantir que o valor enviado seja um número inteiro
    nome_participante = StringField('Nome', validators=[DataRequired()])
    sobrenome_participante = StringField('Sobrenome', validators=[DataRequired()])
    idade = IntegerField('Idade', validators=[DataRequired()])
    peso = IntegerField('Peso', validators=[DataRequired()])
    graduacao = StringField('Graduação', validators=[DataRequired()])
    cpf = StringField('CPF', validators=[DataRequired()])
    telefone = StringField('Telefone', validators=[DataRequired()])
    equipe_id = SelectField('Equipe', coerce=int, validators=[DataRequired()])
    categoria_id = SelectField('Categoria', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Inscrever-se')

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

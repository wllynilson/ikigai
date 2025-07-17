# Ficheiro: app/public/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, SelectField, SubmitField
from wtforms.fields.datetime import DateField
from wtforms.validators import DataRequired, Length, NumberRange, ValidationError, Optional
from app.models import Participante


class InscricaoEventoForm(FlaskForm):
    """Formulário simplificado para um utilizador logado se inscrever num evento."""
    categoria_id = SelectField('Selecione a Categoria para competir', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Confirmar Minha Inscrição')

class InscricaoTerceiroForm(FlaskForm):
    """Formulário para um utilizador logado inscrever um terceiro."""
    nome_completo = StringField('Nome Completo do Participante', validators=[DataRequired(), Length(max=150)])
    cpf = StringField('CPF do Participante', validators=[DataRequired()])
    telefone = StringField('Telefone', validators=[DataRequired()])
    data_nascimento = DateField('Nascimento', validators=[Optional()])
    peso = FloatField('Peso (kg)', validators=[DataRequired(), NumberRange(min=0)], description="Use ponto como separador decimal, ex: 75.5")
    graduacao = StringField('Graduação', validators=[DataRequired(), Length(max=50)])
    equipe_id = SelectField('Equipe', coerce=int, validators=[DataRequired(message="Por favor, selecione uma equipe.")])
    categoria_id = SelectField('Categoria', coerce=int, validators=[DataRequired(message="Por favor, selecione uma categoria.")])
    submit = SubmitField('Finalizar Inscrição')

    def validate_cpf(self, cpf):
        participante = Participante.query.filter_by(cpf=cpf.data).first()
        if participante:
            raise ValidationError(f'Um participante com este CPF já existe no sistema com o nome "{participante.nome_completo}".')
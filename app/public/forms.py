# Ficheiro: app/public/forms.py
from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired

class InscricaoEventoForm(FlaskForm):
    # Usamos 'coerce=int' para garantir que o valor enviado seja um número inteiro
    equipe_id = SelectField('Selecione a sua equipe', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Confirmar Inscrição')
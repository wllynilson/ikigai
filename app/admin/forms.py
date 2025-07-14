# Ficheiro: app/admin/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, FloatField, IntegerField, SelectField
from wtforms.fields import DateTimeLocalField
from wtforms.fields.datetime import DateField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, URL


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


class EventoForm(FlaskForm):
    """Formulário completo para criar e editar eventos."""
    nome_evento = StringField('Nome do Evento', validators=[DataRequired(), Length(max=200)])
    data_hora_evento = DateTimeLocalField('Data e Hora do Evento', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    palestrante = StringField('Palestrante', validators=[Optional(), Length(max=100)])
    imagem_palestrante = StringField('URL da Imagem do Palestrante',
                                     validators=[Optional(), URL(message="Por favor, insira uma URL válida.")])
    descricao = TextAreaField('Descrição', validators=[Optional()])
    local_evento = StringField('Local do Evento', validators=[Optional(), Length(max=200)])
    preco = FloatField('Preço (R$)', default=0.0, validators=[Optional(), NumberRange(min=0)])
    numero_vagas = IntegerField('Número de Vagas', validators=[DataRequired(), NumberRange(min=0)])
    pix_copia_e_cola = TextAreaField('Pix Copia e Cola',
                                     validators=[Optional()],
                                     description="Insira o código Pix 'copia e cola' para eventos pagos.")
    submit = SubmitField('Salvar Evento')

class AdminEditarInscricaoForm(FlaskForm):
    """Formulário para o Admin editar os detalhes de um participante numa inscrição."""
    nome_participante = StringField('Nome do Participante', validators=[DataRequired(), Length(max=100)])
    sobrenome_participante = StringField('Sobrenome', validators=[DataRequired(), Length(max=100)])
    idade = IntegerField('Idade', validators=[DataRequired(), NumberRange(min=1)])
    peso = FloatField('Peso (kg)', validators=[Optional(), NumberRange(min=0)])
    graduacao = StringField('Graduação', validators=[Optional(), Length(max=50)])
    professor_responsavel = StringField('Professor Responsável', validators=[Optional(), Length(max=100)])
    cpf = StringField('CPF', validators=[DataRequired(), Length(min=11, max=14)])
    telefone = StringField('Telefone', validators=[DataRequired(), Length(min=8, max=20)])
    categoria_id = SelectField('Categoria do Atleta', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Salvar Alterações')

class CategoriaForm(FlaskForm):
    """Formulário para criar ou editar uma Categoria de evento."""
    nome = StringField('Nome da Categoria',
                       validators=[DataRequired(), Length(max=100)],
                       description="Ex: Faixa Branca / Adulto / Peso Pena")
    submit = SubmitField('Salvar Categoria')

class EditarParticipanteForm(FlaskForm):
    """Formulário para o Admin editar os detalhes de um Participante."""
    nome_completo = StringField('Nome Completo', validators=[DataRequired(), Length(max=150)])
    cpf = StringField('CPF', validators=[DataRequired()])
    telefone = StringField('Telefone', validators=[DataRequired()])
    data_nascimento = DateField('Data de Nascimento', format='%Y-%m-%d', validators=[Optional()])
    peso = FloatField('Peso (kg)', validators=[Optional(), NumberRange(min=0)])
    graduacao = StringField('Graduação', validators=[DataRequired()])
    equipe_id = SelectField('Equipe', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Salvar Alterações')

class EquipeForm(FlaskForm):
    """Formulário para criar e editar Equipes."""
    nome_equipe = StringField('Nome da Equipe', validators=[DataRequired(), Length(max=100)])
    professor_responsavel = StringField('Professor Responsável', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Salvar Equipe')

class EmptyForm(FlaskForm):
    """Um formulário vazio usado para ações POST protegidas por CSRF, como exclusão."""
    submit = SubmitField('Submit')

class LoteVendaForm(FlaskForm):
    """Formulário para criar ou editar um Lote de Venda."""
    nome = StringField('Nome do Lote',
                       validators=[DataRequired(), Length(max=100)],
                       description="Ex: Lote 1, Lote Promocional, Virada de Lote")
    preco = FloatField('Preço (R$)',
                       validators=[DataRequired(), NumberRange(min=0)])
    data_final = DateTimeLocalField('Data e Hora Final do Lote',
                                    format='%Y-%m-%dT%H:%M',
                                    validators=[DataRequired()])
    submit = SubmitField('Salvar Lote')
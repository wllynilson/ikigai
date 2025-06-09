from flask import Blueprint, render_template, request, redirect, url_for, flash
from . import db # Importação relativa para o 'db' do __init__.py
from .models import Evento, Equipe, Inscricao # Importação relativa para os modelos
from datetime import datetime

public_bp = Blueprint('public', __name__)

@public_bp.route('/')
def index():
    # Cole aqui a lógica da função 'index' que tínhamos antes
    eventos = Evento.query.filter(Evento.data_hora_evento >= datetime.utcnow()).order_by(Evento.data_hora_evento).all()
    return render_template('index.html', eventos=eventos)

@public_bp.route('/inscrever/<int:evento_id>', methods=['GET', 'POST'])
def inscrever_evento(evento_id):
    evento = Evento.query.get_or_404(evento_id)
    equipes = Equipe.query.order_by(Equipe.nome_equipe).all()

    if request.method == 'POST':
        if evento.numero_vagas <= 0:
            flash('Inscrições encerradas para este evento (vagas esgotadas).', 'danger')
            return redirect(url_for('rota_inscrever_evento', evento_id=evento.id))

        nome_participante = request.form['nome_participante']
        sobrenome_participante = request.form['sobrenome_participante']
        try:
            idade = int(request.form['idade'])
        except ValueError:
            flash('Idade inválida.', 'danger')
            return render_template('inscrever_evento.html', evento=evento, equipes=equipes)

        cpf = request.form['cpf']
        telefone = request.form['telefone']
        try:
            equipe_id = int(request.form['equipe_id'])
        except ValueError:
            flash('Seleção de equipe inválida.', 'danger')
            return render_template('inscrever_evento.html', evento=evento, equipes=equipes)

        if idade <= 0:
            flash('Idade deve ser um valor positivo.', 'danger')
            return render_template('inscrever_evento.html', evento=evento, equipes=equipes)
        email = request.form['email']
        if not email or '@' not in email:
            flash('Email inválido.', 'danger')
            return render_template('inscrever_evento.html', evento=evento, equipes=equipes)

        inscricao_existente = Inscricao.query.filter_by(cpf=cpf, evento_id=evento.id).first()
        if inscricao_existente:
            flash('Este CPF já está inscrito neste evento.', 'warning')
            return render_template('inscrever_evento.html', evento=evento, equipes=equipes)

        nova_inscricao = Inscricao(
            nome_participante=nome_participante,
            sobrenome_participante=sobrenome_participante,
            idade=idade,
            cpf=cpf,
            telefone=telefone,
            email=email,
            evento_id=evento.id,
            equipe_id=equipe_id
        )

        try:
            db.session.add(nova_inscricao)
            evento.numero_vagas -= 1
            db.session.commit()
            flash(f'Inscrição no {evento.nome_evento} concluída com sucesso! \n Para garantir sua participação, finalize o pagamento o quanto antes.', 'success')
            return redirect(url_for('public.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao processar inscrição: {str(e)}', 'danger')  # Usar str(e) para a mensagem
            return render_template('inscrever_evento.html', evento=evento, equipes=equipes)

    return render_template('inscrever_evento.html', evento=evento, equipes=equipes)

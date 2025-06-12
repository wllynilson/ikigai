from datetime import datetime

from flask import Blueprint
from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from app import db
from app.models import Evento, Equipe, Inscricao
from app.public.forms import InscricaoEventoForm  # Importa o novo formulário

public_bp = Blueprint('public', __name__)

@public_bp.route('/')
def index():
    # Cole aqui a lógica da função 'index' que tínhamos antes
    eventos = Evento.query.filter(Evento.data_hora_evento >= datetime.utcnow()).order_by(Evento.data_hora_evento).all()
    return render_template('index.html', eventos=eventos)


@public_bp.route('/inscrever/<int:evento_id>', methods=['GET', 'POST'])
@login_required  # Garante que apenas utilizadores logados podem aceder
def inscrever_evento(evento_id):
    evento = Evento.query.get_or_404(evento_id)

    # Verifica se o utilizador já está inscrito neste evento
    inscricao_existente = Inscricao.query.filter_by(user_id=current_user.id, evento_id=evento.id).first()
    if inscricao_existente:
        flash('Você já está inscrito neste evento.', 'info')
        return redirect(url_for('public.index'))

    if evento.numero_vagas <= 0:  # Uma verificação extra
        flash('As inscrições para este evento estão encerradas (vagas esgotadas).', 'warning')
        return redirect(url_for('public.index'))

    form = InscricaoEventoForm()
    # Popula o menu dropdown com as equipas existentes
    form.equipe_id.choices = [(e.id, f"{e.nome_equipe} (Prof. {e.professor_responsavel})") for e in
                              Equipe.query.order_by('nome_equipe').all()]

    if form.validate_on_submit():
        # --- INÍCIO DA LÓGICA ALTERADA ---

        # Primeiro, criamos e salvamos a inscrição
        nova_inscricao = Inscricao(
            user_id=current_user.id,
            evento_id=evento.id,
            equipe_id=form.equipe_id.data
        )
        db.session.add(nova_inscricao)
        db.session.commit()

        # Agora, verificamos se o evento é pago e tem uma chave Pix
        if evento.preco > 0 and evento.pix_copia_e_cola:
            # Se sim, usamos uma categoria especial no flash para ativar o JavaScript
            # A mensagem do flash será a própria chave Pix!
            flash(evento.pix_copia_e_cola, 'show_pix_modal')
        else:
            # Se não, mostramos uma mensagem de sucesso normal
            flash(f'Inscrição no evento "{evento.nome_evento}" realizada com sucesso!', 'success')

        return redirect(url_for('public.index'))
        # --- FIM DA LÓGICA ALTERADA ---

    return render_template('inscrever_evento.html', title=f"Inscrição: {evento.nome_evento}", form=form, evento=evento)

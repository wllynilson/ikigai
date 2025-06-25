from collections import defaultdict
from datetime import datetime

from flask import Blueprint
from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from app import db
from app.models import Equipe, Inscricao
from app.models import Evento, Categoria, Luta  # Certifique-se que Categoria e Luta estão importados
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
    form.categoria_id.choices = [(c.id, c.nome) for c in
                                 Categoria.query.filter_by(evento_id=evento.id).order_by('nome').all()]

    if form.validate_on_submit():
        # --- INÍCIO DA LÓGICA ALTERADA ---

        # Verifica se a equipe selecionada ainda existe
        equipe_selecionada = Equipe.query.get(form.equipe_id.data)
        if not equipe_selecionada:
            flash('A equipe selecionada não foi encontrada. Por favor, selecione outra equipe.', 'danger')

        # Primeiro, criamos e salvamos a inscrição
        nova_inscricao = Inscricao(
            user_id=current_user.id,
            nome_participante=form.nome_participante.data,
            sobrenome_participante=form.sobrenome_participante.data,
            idade=form.idade.data,
            peso=form.peso.data,
            graduacao=form.graduacao.data,
            cpf=form.cpf.data,
            telefone=form.telefone.data,
            evento_id=evento.id,
            equipe_id=form.equipe_id.data,
            professor_responsavel=equipe_selecionada.professor_responsavel,
            categoria_id=form.categoria_id.data
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

@public_bp.route('/evento/<int:evento_id>')
def detalhe_evento(evento_id):
    """Exibe a página de detalhes para um único evento."""
    evento = Evento.query.get_or_404(evento_id)
    return render_template('detalhe_evento.html', titulo=evento.nome_evento, evento=evento)


@public_bp.route('/evento/<int:evento_id>/categoria/<int:categoria_id>/chave')
def visualizar_chave_publica(evento_id, categoria_id):
    """Exibe a página pública da chave de competição para uma categoria."""
    categoria = Categoria.query.filter_by(id=categoria_id, evento_id=evento_id).first_or_404()

    # Busca todas as lutas da categoria, ordenadas
    lutas = Luta.query.filter_by(categoria_id=categoria_id).order_by(Luta.round, Luta.ordem_na_chave).all()

    # Se não houver lutas, informa ao utilizador
    if not lutas:
        flash('A chave para esta categoria ainda não está disponível.', 'info')
        return redirect(url_for('public.detalhe_evento', evento_id=evento_id))

    # Organiza as lutas num dicionário por round
    rounds = defaultdict(list)
    for luta in lutas:
        rounds[luta.round].append(luta)

    return render_template('chave_publica.html',
                           titulo=f"Chave: {categoria.nome}",
                           categoria=categoria,
                           rounds=rounds)
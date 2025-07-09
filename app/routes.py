from collections import defaultdict
from datetime import datetime

from flask import Blueprint
from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from app import db
from app.models import Equipe, Inscricao, User
from app.models import Evento, Categoria, Luta  # Certifique-se que Categoria e Luta estão importados
from app.public.forms import InscricaoEventoForm  # Importa o novo formulário

public_bp = Blueprint('public', __name__)

@public_bp.route('/')
def index():
    # Busca TODOS os eventos, ordenando pelos mais recentes primeiro
    eventos = Evento.query.order_by(Evento.data_hora_evento.desc()).all()

    # Passa os eventos e a data/hora atual para o template
    return render_template('index.html',
                           eventos=eventos,
                           now=datetime.now())

@public_bp.route('/inscrever/<string:slug>', methods=['GET', 'POST'])
@login_required
def inscrever_evento(slug):
    evento = Evento.query.filter_by(slug=slug).first_or_404()
    # Pega o perfil de participante associado ao utilizador logado
    participante = current_user.participante

    # Verificação 1: Garante que o utilizador tem um perfil de participante completo
    if not participante or not participante.cpf:
        flash('Para se inscrever, por favor, complete primeiro o seu perfil de atleta.', 'warning')
        return redirect(url_for('auth.editar_perfil'))

    # Verificação 2: Redireciona se o evento estiver esgotado
    if evento.numero_vagas <= 0:
        flash('As inscrições para este evento estão encerradas (vagas esgotadas).', 'warning')
        return redirect(url_for('public.detalhe_evento', slug=evento.slug))

    form = InscricaoEventoForm()
    # Popula o dropdown apenas com as categorias do evento atual
    form.categoria_id.choices = [(c.id, c.nome) for c in evento.categorias]

    if form.validate_on_submit():
        categoria_id_selecionada = form.categoria_id.data

        # Verificação 3: Garante que o participante já não está inscrito nesta categoria
        inscricao_existente = Inscricao.query.filter_by(
            participante_id=participante.id,
            categoria_id=categoria_id_selecionada
        ).first()
        if inscricao_existente:
            flash('Você já está inscrito nesta categoria.', 'info')
            return redirect(url_for('public.detalhe_evento', slug=evento.slug))

        # Cria a nova inscrição
        nova_inscricao = Inscricao(
            participante_id=participante.id,
            categoria_id=categoria_id_selecionada,
            registrado_por_user_id=current_user.id
        )
        db.session.add(nova_inscricao)
        db.session.commit()

        if evento.preco > 0 and evento.pix_copia_e_cola:
            flash(evento.pix_copia_e_cola, 'show_pix_modal')
        else:
            flash(f'Inscrição no evento "{evento.nome_evento}" realizada com sucesso!', 'success')

        return redirect(url_for('public.index'))

    return render_template('inscrever_evento.html',
                         title=f"Inscrição: {evento.nome_evento}",
                         form=form,
                         evento=evento)


@public_bp.route('/evento/<string:slug>')
def detalhe_evento(slug):
    # Agora busca pelo campo 'slug'
    evento = Evento.query.filter_by(slug=slug).first_or_404()
    return render_template('detalhe_evento.html', titulo=evento.nome_evento, evento=evento, now=datetime.now())


@public_bp.route('/evento/<string:slug>/categoria/<int:categoria_id>/chave')
def visualizar_chave_publica(slug, categoria_id):
   """Exibe a página pública da chave de competição para uma categoria."""
   evento = Evento.query.filter_by(slug=slug).first_or_404()
   categoria = Categoria.query.filter_by(id=categoria_id, evento_id=evento.id).first_or_404()

   lutas = Luta.query.filter_by(categoria_id=categoria_id).order_by(Luta.round, Luta.ordem_na_chave).all()

   if not lutas:
       flash('A chave para esta categoria ainda não está disponível.', 'info')
       return redirect(url_for('public.detalhe_evento', slug=slug))

   rounds = defaultdict(list)
   for luta in lutas:
       rounds[luta.round].append(luta)

   # --- NOVA LÓGICA PARA DETERMINAR O PÓDIO ---
   podio = None
   if rounds:
       max_round = max(rounds.keys())
       lutas_da_ultima_ronda = rounds.get(max_round, [])

       # Procura pela final (ordem 1) e pela disputa de 3º lugar (ordem > 1)
       final = next((l for l in lutas_da_ultima_ronda if l.ordem_na_chave == 1), None)
       luta_terceiro = next((l for l in lutas_da_ultima_ronda if l.ordem_na_chave > 1), None)

       # Verifica se ambas as lutas decisivas (final e 3º lugar) têm um vencedor
       if final and final.vencedor_id and luta_terceiro and luta_terceiro.vencedor_id:
           # Determina o 1º e 2º lugar a partir da final
           vencedor_final = User.query.get(final.vencedor_id)
           # O segundo lugar é o competidor que não é o vencedor
           segundo_lugar = final.competidor1 if final.vencedor_id == final.competidor2_id else final.competidor2

           # O 3º lugar é o vencedor da outra luta
           terceiro_lugar = User.query.get(luta_terceiro.vencedor_id)

           podio = {
               'primeiro': vencedor_final,
               'segundo': segundo_lugar,
               'terceiro': terceiro_lugar
           }
   # --- FIM DA LÓGICA DO PÓDIO ---

   return render_template('chave_publica.html',
                          titulo=f"Chave: {categoria.nome}",
                          categoria=categoria,
                          rounds=rounds,
                          podio=podio)  # Passa o dicionário do pódio para o template
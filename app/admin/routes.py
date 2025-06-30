import math
from datetime import datetime

from flask import jsonify
from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user, login_user
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from app.decorators import admin_required
from . import bp  # Importa o 'bp' do __init__.py do admin
from .forms import CategoriaForm, AdminEditarInscricaoForm, EditarParticipanteForm
from .forms import EditarInscricaoForm, EventoForm  # 'from .' pois assumo que forms.py está na mesma pasta admin
from .. import db  # '..' sobe um nível para o pacote 'app' para pegar o 'db'
from ..models import Categoria, Participante, Pagamento
from ..models import Evento, Equipe, Inscricao, User, Luta
from app.services import gerar_chave_eliminatoria_simples
from collections import defaultdict

# --- LOGIN AUTOMÁTICO EM DESENVOLVIMENTO ---
@bp.before_request
def before_request_handler():
    # Verifica se a app está em modo DEBUG (local) E se ninguém está logado
    if current_app.config.get('DEBUG') and not current_user.is_authenticated:
        # Encontra o primeiro utilizador na tabela (que deve ser o seu admin)
        user = User.query.first()
        if user:
            # Faz o login desse utilizador automaticamente
            login_user(user)
# --- FIM DO BLOCO DE LOGIN AUTOMÁTICO ---

@bp.route('/dashboard')  # Ou @bp.route('/') se quiser que seja a página inicial do admin
@admin_required
def dashboard():
    """
    Calcula várias estatísticas e exibe-as num painel de controlo.
    """
    # 1. Contar Inscrições por Status
    contagem_pendentes = Inscricao.query.filter_by(status='Pendente').count()
    contagem_aprovadas = Inscricao.query.filter_by(status='Aprovada').count()

    # 2. Contar Próximos Eventos (data do evento é no futuro)
    agora = datetime.utcnow()
    contagem_proximos_eventos = Evento.query.filter(Evento.data_hora_evento >= agora).count()

    # 3. Contagens Totais
    contagem_total_eventos = Evento.query.count()
    contagem_total_equipes = Equipe.query.count()
    contagem_total_inscricoes = Inscricao.query.count()

    # Dicionário com todas as estatísticas para passar ao template
    stats = {
        'pendentes': contagem_pendentes,
        'aprovadas': contagem_aprovadas,
        'proximos_eventos': contagem_proximos_eventos,
        'total_eventos': contagem_total_eventos,
        'total_equipes': contagem_total_equipes,
        'total_inscricoes': contagem_total_inscricoes
    }

    return render_template('admin/dashboard.html', titulo='Dashboard', stats=stats)


# --- Gerenciamento de Equipes (já feito, agora dentro do blueprint) ---
@bp.route('/equipes')
@admin_required
def gerenciar_equipes():
    equipes = Equipe.query.order_by(Equipe.nome_equipe).all()
    return render_template('admin/admin_gerenciar_equipes.html', equipes=equipes)


@bp.route('/equipes/nova', methods=['GET', 'POST'])
@admin_required
def nova_equipe():
    if request.method == 'POST':
        nome_equipe = request.form['nome_equipe']
        professor_responsavel = request.form['professor_responsavel']

        equipe_existente = Equipe.query.filter_by(nome_equipe=nome_equipe).first()
        if equipe_existente:
            flash('Uma equipe com este nome já existe.', 'warning')
        else:
            nova_equipe = Equipe(nome_equipe=nome_equipe, professor_responsavel=professor_responsavel)
            try:
                db.session.add(nova_equipe)
                db.session.commit()
                flash('Equipe cadastrada com sucesso!', 'success')
                return redirect(url_for('admin.gerenciar_equipes'))
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao cadastrar equipe: {str(e)}', 'danger')
        # Se houve erro ou equipe existente, renderiza o form novamente
        # Passando os dados que o usuário tentou submeter para repreencher (opcional)
        return render_template('admin/admin_form_equipe.html',
                               titulo_form="Nova Equipe",
                               equipe_dados={'nome_equipe': nome_equipe,
                                             'professor_responsavel': professor_responsavel},
                               action_url=url_for('admin.nova_equipe'))

    # Se GET, apenas mostra o formulário vazio
    return render_template('admin/admin_form_equipe.html',
                           titulo_form="Nova Equipe",
                           action_url=url_for('admin.nova_equipe'))


@bp.route('/equipes/<int:equipe_id>/editar', methods=['GET', 'POST'])
@admin_required
def editar_equipe(equipe_id):
    equipe_para_editar = Equipe.query.get_or_404(equipe_id)

    if request.method == 'POST':
        novo_nome_equipe = request.form['nome_equipe']
        novo_professor_responsavel = request.form['professor_responsavel']

        # Verifica se o novo nome já existe em OUTRA equipe
        equipe_existente_com_mesmo_nome = Equipe.query.filter(Equipe.nome_equipe == novo_nome_equipe,
                                                              Equipe.id != equipe_id).first()
        if equipe_existente_com_mesmo_nome:
            flash('Já existe outra equipe cadastrada com este nome.', 'warning')
            # Re-renderiza o formulário com os dados que o usuário tentou submeter
            return render_template('admin/admin_form_equipe.html',
                                   titulo_form=f"Editar Equipe: {equipe_para_editar.nome_equipe}",
                                   action_url=url_for('admin.editar_equipe', equipe_id=equipe_id),
                                   equipe_dados={'nome_equipe': novo_nome_equipe,
                                                 'professor_responsavel': novo_professor_responsavel})  # Passa os dados tentados
        else:
            equipe_para_editar.nome_equipe = novo_nome_equipe
            equipe_para_editar.professor_responsavel = novo_professor_responsavel
            try:
                db.session.commit()
                flash('Equipe atualizada com sucesso!', 'success')
                return redirect(url_for('admin.gerenciar_equipes'))
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao atualizar equipe: {str(e)}', 'danger')

    # Se GET, mostra o formulário preenchido com os dados da equipe
    return render_template('admin/admin_form_equipe.html',
                           titulo_form=f"Editar Equipe: {equipe_para_editar.nome_equipe}",
                           action_url=url_for('admin.editar_equipe', equipe_id=equipe_id),
                           equipe_dados=equipe_para_editar)  # Passa o objeto equipe para preencher o form


@bp.route('/equipes/<int:equipe_id>/excluir', methods=['POST'])
@admin_required
def excluir_equipe(equipe_id):
    equipe_para_excluir = Equipe.query.get_or_404(equipe_id)

    # Verificar se a equipe tem inscrições associadas
    if equipe_para_excluir.inscricoes:  # Se a lista de inscrições não estiver vazia
        flash(
            f'Não é possível excluir a equipe "{equipe_para_excluir.nome_equipe}", pois ela possui participantes inscritos associados a ela.',
            'danger')
        return redirect(url_for('admin.gerenciar_equipes'))

    try:
        db.session.delete(equipe_para_excluir)
        db.session.commit()
        flash(f'Equipe "{equipe_para_excluir.nome_equipe}" excluída com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir equipe: {str(e)}', 'danger')

    return redirect(url_for('admin.gerenciar_equipes'))


# --- Gerenciamento de Eventos (Onde vamos trabalhar agora) ---
@bp.route('/eventos')
@admin_required
def gerenciar_eventos():
    eventos = Evento.query.order_by(Evento.data_hora_evento.desc()).all()
    # Note o 'admin/' no caminho do template
    return render_template('admin/admin_gerenciar_eventos.html', eventos=eventos)


@bp.route('/eventos/<int:evento_id>/inscricoes')
@admin_required
def listar_inscricoes_evento(evento_id):
    evento = Evento.query.get_or_404(evento_id)

    # --- CONSULTA OTIMIZADA COM JOIN ---
    inscricoes = Inscricao.query.options(
        joinedload(Inscricao.participante),  # Junta a tabela 'users' através da relação 'participante'
        joinedload(Inscricao.equipe)  # Junta a tabela 'equipes' através da relação 'equipe'
    ).filter_by(evento_id=evento.id).order_by(Inscricao.data_inscricao).all()

    return render_template('admin/admin_listar_inscricoes_evento.html', evento=evento, inscricoes=inscricoes)


@bp.route('/eventos/novo', methods=['GET', 'POST'])
@login_required
def novo_evento():
    form = EventoForm()
    if form.validate_on_submit():
        novo_evento = Evento()
        form.populate_obj(novo_evento)  # Popula o objeto com os dados do form
        try:
            db.session.add(novo_evento)
            db.session.commit()
            flash('Evento cadastrado com sucesso!', 'success')
            return redirect(url_for('admin.gerenciar_eventos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar evento: {e}', 'danger')

    return render_template('admin/admin_form_evento.html', titulo_form="Novo Evento", form=form)


@bp.route('/eventos/editar/<int:evento_id>', methods=['GET', 'POST'])
@login_required
def editar_evento(evento_id):
    evento = Evento.query.get_or_404(evento_id)
    # Passamos obj=evento para que o WTForms preencha o formulário com os dados do evento automaticamente
    form = EventoForm(obj=evento)

    if form.validate_on_submit():
        form.populate_obj(evento)  # Atualiza o objeto com os dados do form
        try:
            db.session.commit()
            flash('Evento atualizado com sucesso!', 'success')
            return redirect(url_for('admin.gerenciar_eventos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar evento: {e}', 'danger')

    return render_template('admin/admin_form_evento.html', titulo_form="Editar Evento", form=form)


@bp.route('/eventos/<int:evento_id>/excluir', methods=['POST'])
@admin_required
def excluir_evento(evento_id):
    evento = Evento.query.get_or_404(evento_id)
    if evento.inscricoes:
        flash('Não é possível excluir um evento que já possui inscritos.', 'danger')
        return redirect(url_for('admin.gerenciar_eventos'))

    db.session.delete(evento)
    db.session.commit()
    flash('Evento excluído com sucesso!', 'success')
    return redirect(url_for('admin.gerenciar_eventos'))


@bp.route('/gerenciar_inscricoes')
@admin_required
def gerenciar_inscricoes():
    page = request.args.get('page', 1, type=int)
    termo_pesquisa = request.args.get('q')
    evento_filtro_id = request.args.get('evento_id')

    query = Inscricao.query.options(
        joinedload(Inscricao.participante).joinedload(Participante.equipe),
        joinedload(Inscricao.categoria).joinedload(Categoria.evento)
    )

    if termo_pesquisa:
        # Corrigido para não usar ILIKE em campo inteiro
        query = query.join(Inscricao.participante).filter(
            or_(
                Participante.nome_completo.ilike(f'%{termo_pesquisa}%'),
                Participante.cpf.ilike(f'%{termo_pesquisa}%')
            )
        )

    if evento_filtro_id:
        query = query.join(Inscricao.categoria).filter(Categoria.evento_id == evento_filtro_id)

    inscricoes_paginadas = query.order_by(Inscricao.data_inscricao.desc()).paginate(
        page=page, per_page=10, error_out=False
    )

    eventos_para_filtro = Evento.query.order_by(Evento.nome_evento).all()

    return render_template('admin/admin_gerenciar_inscricoes.html',
                           inscricoes_paginadas=inscricoes_paginadas,
                           eventos_para_filtro=eventos_para_filtro,
                           titulo='Gerenciar Inscrições')

@bp.route('/inscricao/cancelar/<int:inscricao_id>', methods=['POST'])  # 'bp' é o nome da sua blueprint
@admin_required
def cancelar_inscricao(inscricao_id):
    """
    Esta rota encontra uma inscrição pelo seu ID e a remove do banco de dados.
    Aceita apenas pedidos POST por segurança.
    """
    # 1. Busca a inscrição no banco de dados. Se não encontrar, retorna um erro 404 (Not Found).
    inscricao = Inscricao.query.get_or_404(inscricao_id)
    try:
        db.session.delete(inscricao)
        db.session.commit()
        # A resposta de sucesso agora diz ao JavaScript para 'remover' a linha
        return jsonify({'status': 'success', 'action': 'delete', 'message': 'Inscrição excluída com sucesso!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Ocorreu um erro ao excluir a inscrição: {str(e)}'}), 500


@bp.route('/inscricao/aprovar/<int:inscricao_id>', methods=['POST'])
@admin_required
def aprovar_inscricao(inscricao_id):
    inscricao = Inscricao.query.get_or_404(inscricao_id)
    if inscricao.status != 'Pendente':
        return jsonify({'status': 'info', 'message': 'Esta inscrição já foi processada.'}), 200

    try:
        # 1. Muda o status da inscrição
        inscricao.status = 'Aprovada'

        # 2. Cria o registo de pagamento correspondente
        novo_pagamento = Pagamento(
            valor=inscricao.categoria.evento.preco,
            metodo='Confirmacao Manual',  # Pode ser 'Pix', 'Dinheiro', etc.
            status_pagamento='Concluido',
            inscricao_id=inscricao.id  # Liga o pagamento a esta inscrição
        )
        db.session.add(novo_pagamento)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Inscrição aprovada com sucesso!',
            'novo_status_html': '<span class="badge badge-success">Aprovada</span>'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Ocorreu um erro: {str(e)}'}), 500


@bp.route('/inscricao/rejeitar/<int:inscricao_id>', methods=['POST'])
@admin_required
def rejeitar_inscricao(inscricao_id):
    inscricao = Inscricao.query.get_or_404(inscricao_id)
    if inscricao.status != 'Pendente':
        return jsonify({'status': 'info', 'message': 'Esta inscrição já foi processada.'}), 200

    try:
        inscricao.status = 'Rejeitada'
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': 'Inscrição rejeitada.',
            'novo_status_html': '<span class="badge badge-danger">Rejeitada</span>'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Ocorreu um erro: {str(e)}'}), 500

@bp.route('/inscricao/editar/<int:inscricao_id>', methods=['GET', 'POST'])
@admin_required
def editar_inscricao(inscricao_id):
    inscricao = Inscricao.query.get_or_404(inscricao_id)
    participante = inscricao.participante

    if not participante:
        flash('Erro: Inscrição sem participante associado.', 'danger')
        return redirect(url_for('admin.gerenciar_inscricoes'))

    form = EditarParticipanteForm(obj=participante)
    # Popula o dropdown de equipes
    form.equipe_id.choices = [(e.id, e.nome_equipe) for e in Equipe.query.order_by('nome_equipe').all()]

    if form.validate_on_submit():
        try:
            # Pega os dados do formulário e atualiza o objeto 'participante'
            form.populate_obj(participante)
            db.session.commit()
            flash(f'Dados do participante {participante.nome_completo} atualizados com sucesso!', 'success')
            return redirect(url_for('admin.gerenciar_inscricoes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar participante: {e}', 'danger')

    return render_template('admin/admin_editar_inscricao.html',
                           titulo=f"Editar Participante",
                           form=form,
                           inscricao=inscricao)

@bp.route('/usuarios')
@admin_required
def gerenciar_usuarios():
    """Lista todos os utilizadores para gerenciamento, agora com paginação."""

    # 1. Pega o número da página a partir da URL (ex: /admin/usuarios?page=2)
    #    O '1' é o valor padrão, e 'type=int' garante que é um número.
    page = request.args.get('page', 1, type=int)

    # 2. Usa .paginate() em vez de .all() para buscar os utilizadores
    #    'per_page=15': define quantos utilizadores queremos mostrar por página.
    usuarios_paginados = User.query.order_by(User.username).paginate(
        page=page, per_page=15, error_out=False
    )

    return render_template('admin/admin_gerenciar_usuarios.html',
                               titulo="Administração de Usuários",
                               usuarios_paginados=usuarios_paginados)


@bp.route('/usuario/<int:user_id>/resetar-senha', methods=['POST'])
@admin_required
def resetar_senha_usuario(user_id):
    user = User.query.get_or_404(user_id)

    # Evita que um admin resete a própria senha por esta rota
    if user == current_user:
        flash('Não pode resetar a sua própria senha por este método.', 'warning')
        return redirect(url_for('admin.gerenciar_usuarios'))

    try:
        # Gera uma nova senha segura e temporária
        nova_senha = f"ikigai@"

        user.set_password(nova_senha)
        db.session.commit()

        # CRÍTICO: Informa ao admin a nova senha para que ele possa passá-la ao utilizador
        flash(f"A senha para o utilizador '{user.username}' foi resetada para: {nova_senha}", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Ocorreu um erro ao resetar a senha: {str(e)}", 'danger')

    return redirect(url_for('admin.gerenciar_usuarios'))


@bp.route('/evento/<int:evento_id>/categorias', methods=['GET', 'POST'])
@admin_required
def categorias_evento(evento_id):
    evento = Evento.query.get_or_404(evento_id)
    form = CategoriaForm()

    if form.validate_on_submit():
        # Lógica para criar uma nova categoria
        nome_categoria = form.nome.data
        categoria_existente = Categoria.query.filter_by(evento_id=evento.id, nome=nome_categoria).first()

        if categoria_existente:
            flash('Uma categoria com este nome já existe para este evento.', 'warning')
        else:
            nova_categoria = Categoria(nome=nome_categoria, evento_id=evento.id)
            db.session.add(nova_categoria)
            db.session.commit()
            flash('Nova categoria adicionada com sucesso!', 'success')

        # Redireciona para a mesma página para limpar o formulário e mostrar a nova lista
        return redirect(url_for('admin.categorias_evento', evento_id=evento.id))

    # Lógica para exibir as categorias existentes
    categorias_do_evento = Categoria.query.filter_by(evento_id=evento.id).order_by(Categoria.nome).all()

    return render_template('admin/admin_gerenciar_categorias.html',
                           titulo=f"Categorias de {evento.nome_evento}",
                           evento=evento,
                           form=form,
                           categorias=categorias_do_evento)


@bp.route('/categoria/<int:categoria_id>/editar', methods=['GET', 'POST'])
@admin_required
def editar_categoria(categoria_id):
    categoria = Categoria.query.get_or_404(categoria_id)
    # Reutilizamos o mesmo CategoriaForm que já temos
    form = CategoriaForm()

    if form.validate_on_submit():
        # Verifica se o novo nome já existe para este evento
        novo_nome = form.nome.data
        categoria_existente = Categoria.query.filter(
            Categoria.evento_id == categoria.evento_id,
            Categoria.nome == novo_nome,
            Categoria.id != categoria_id # Exclui a própria categoria da verificação
        ).first()

        if categoria_existente:
            flash('Outra categoria com este nome já existe para este evento.', 'warning')
        else:
            categoria.nome = novo_nome
            db.session.commit()
            flash('Categoria atualizada com sucesso!', 'success')
            return redirect(url_for('admin.categorias_evento', evento_id=categoria.evento_id))

    # No GET, pré-preenche o formulário com o nome atual da categoria
    elif request.method == 'GET':
        form.nome.data = categoria.nome

    return render_template('admin/admin_form_categoria.html',
                           titulo=f"Editar Categoria: {categoria.nome}",
                           form=form)


@bp.route('/categoria/<int:categoria_id>/excluir', methods=['POST'])
@admin_required
def excluir_categoria(categoria_id):
    categoria = Categoria.query.get_or_404(categoria_id)

    # Verificação de segurança: a categoria tem inscrições?
    if categoria.inscricoes.count() > 0:
        flash('Não é possível excluir uma categoria que já possui participantes inscritos.', 'danger')
        return redirect(url_for('admin.gerenciar_categorias_evento', evento_id=categoria.evento_id))

    try:
        evento_id = categoria.evento_id  # Guarda o ID do evento antes de apagar
        db.session.delete(categoria)
        db.session.commit()
        flash('Categoria excluída com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Ocorreu um erro ao excluir a categoria: {str(e)}", 'danger')

    return redirect(url_for('admin.gerenciar_categorias_evento', evento_id=evento_id))


@bp.route('/categoria/<int:categoria_id>/gerar-chave', methods=['POST'])
@admin_required
def gerar_chave(categoria_id):
    categoria = Categoria.query.get_or_404(categoria_id)

    # Passo de segurança: apaga qualquer chave antiga para esta categoria
    # para evitar duplicados se o admin gerar novamente.
    Luta.query.filter_by(categoria_id=categoria_id).delete()
    db.session.commit()

    # Chama a nossa função de serviço para fazer a magia
    sucesso, mensagem = gerar_chave_eliminatoria_simples(
        categoria_id=categoria.id,
        evento_id=categoria.evento_id
    )

    if sucesso:
        flash(mensagem, 'success')
    else:
        flash(mensagem, 'danger')

    return redirect(url_for('admin.categorias_evento', evento_id=categoria.evento_id))


@bp.route('/categoria/<int:categoria_id>/chave')
@admin_required
def visualizar_chave(categoria_id):
    """Exibe a chave de competição para uma dada categoria."""
    categoria = Categoria.query.get_or_404(categoria_id)

    lutas = Luta.query.filter_by(categoria_id=categoria_id).order_by(Luta.round, Luta.ordem_na_chave).all()

    if not lutas:
        flash('A chave para esta categoria ainda não foi gerada.', 'warning')
        return redirect(url_for('admin.categorias_evento', evento_id=categoria.evento_id))

    rounds = defaultdict(list)
    for luta in lutas:
        rounds[luta.round].append(luta)

    # --- LÓGICA DE VERIFICAÇÃO CORRIGIDA ---
    mostrar_botao_terceiro = False
    # A final é a ronda com o número mais alto
    max_round = max(rounds.keys()) if rounds else 0

    # Só pode haver disputa de 3º se houver pelo menos uma final e uma semi-final
    if max_round > 1:
        semi_finais = rounds.get(max_round - 1, [])
        lutas_na_ronda_final = rounds.get(max_round, [])

        # Condições para mostrar o botão:
        # 1. As duas semi-finais devem ter um vencedor.
        # 2. Só deve existir UMA luta na ronda final (a própria final, antes da disputa de 3º ser criada).
        if len(semi_finais) == 2 and all(l.vencedor_id for l in semi_finais) and len(lutas_na_ronda_final) == 1:
            mostrar_botao_terceiro = True
    # --- FIM DA LÓGICA CORRIGIDA ---

    return render_template('admin/admin_visualizar_chave.html',
                           titulo=f"Chave: {categoria.nome}",
                           categoria=categoria,
                           rounds=rounds,
                           mostrar_botao_terceiro=mostrar_botao_terceiro)  # Passa a variável corrigida

@bp.route('/luta/<int:luta_id>/set-vencedor', methods=['POST'])
@admin_required
def declarar_vencedor(luta_id):
    # 1. Obter os dados enviados pelo JavaScript
    data = request.get_json()
    vencedor_id = data.get('vencedor_id')

    if not vencedor_id:
        return jsonify({'status': 'error', 'message': 'ID do vencedor não fornecido.'}), 400

    luta_atual = Luta.query.get_or_404(luta_id)
    # Garante que o vencedor é um dos competidores da luta
    if vencedor_id not in [luta_atual.competidor1_id, luta_atual.competidor2_id]:
        return jsonify({'status': 'error', 'message': 'Vencedor inválido para esta luta.'}), 400

    # 2. Atualiza a luta atual
    luta_atual.vencedor_id = vencedor_id

    # 3. Lógica para avançar o vencedor para a próxima ronda
    # Encontra todas as lutas da mesma categoria e ronda
    lutas_da_ronda_atual = Luta.query.filter_by(
        categoria_id=luta_atual.categoria_id,
        round=luta_atual.round
    ).order_by(Luta.ordem_na_chave).all()

    # Encontra todas as lutas da próxima ronda
    lutas_da_proxima_ronda = Luta.query.filter_by(
        categoria_id=luta_atual.categoria_id,
        round=luta_atual.round + 1
    ).order_by(Luta.ordem_na_chave).all()

    # Se houver uma próxima ronda
    if lutas_da_proxima_ronda:
        # Descobre o índice da luta atual na sua ronda (0, 1, 2, 3...)
        indice_da_luta_atual = [l.id for l in lutas_da_ronda_atual].index(luta_atual.id)

        # O vencedor irá para a luta de índice (indice_da_luta_atual / 2) na próxima ronda
        indice_da_proxima_luta = math.floor(indice_da_luta_atual / 2)
        proxima_luta = lutas_da_proxima_ronda[indice_da_proxima_luta]

        # Decide se ele será o competidor 1 ou 2 na próxima luta
        if indice_da_luta_atual % 2 == 0:  # Lutas pares (0, 2, 4...) preenchem o competidor 1
            proxima_luta.competidor1_id = vencedor_id
        else:  # Lutas ímpares (1, 3, 5...) preenchem o competidor 2
            proxima_luta.competidor2_id = vencedor_id

    try:
        db.session.commit()
        # Retorna uma resposta de sucesso para o JavaScript
        return jsonify({
            'status': 'success',
            'message': 'Vencedor registado e avançado com sucesso!',
            'proxima_luta_id': proxima_luta.id if 'proxima_luta' in locals() else None,
            'vencedor_id': vencedor_id,
            'vencedor_nome': User.query.get(vencedor_id).nome_completo
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Ocorreu um erro: {str(e)}'}), 500


@bp.route('/categoria/<int:categoria_id>/gerar-terceiro-lugar', methods=['POST'])
@admin_required
def gerar_disputa_terceiro_lugar(categoria_id):
    categoria = Categoria.query.get_or_404(categoria_id)

    # 1. Encontrar o número do round da final
    max_round = db.session.query(db.func.max(Luta.round)).filter_by(categoria_id=categoria_id).scalar()

    if not max_round or max_round < 2:
        flash('Não é possível gerar a disputa de 3º lugar antes das semi-finais.', 'danger')
        return redirect(url_for('admin.visualizar_chave', categoria_id=categoria_id))

    # 2. Encontrar as lutas da semi-final (round anterior à final)
    semi_finais = Luta.query.filter_by(categoria_id=categoria_id, round=max_round - 1).all()

    # 3. Validar se as semi-finais estão concluídas
    if len(semi_finais) != 2 or not all(l.vencedor_id for l in semi_finais):
        flash('Ambas as lutas da semi-final precisam de ter um vencedor declarado.', 'warning')
        return redirect(url_for('admin.visualizar_chave', categoria_id=categoria_id))

    # 4. Identificar os perdedores das semi-finais
    perdedores = []
    for sf in semi_finais:
        if sf.vencedor_id == sf.competidor1_id:
            perdedores.append(sf.competidor2)
        else:
            perdedores.append(sf.competidor1)

    # 5. Criar a luta pelo terceiro lugar
    # Usamos um número de round especial ou o mesmo da final para agrupá-la
    ordem_final = Luta.query.filter_by(categoria_id=categoria_id, round=max_round).first().ordem_na_chave

    luta_terceiro_lugar = Luta(
        round=max_round,  # Coloca a disputa no mesmo nível da final
        ordem_na_chave=ordem_final + 1,  # Garante que apareça depois da final
        categoria_id=categoria_id,
        evento_id=categoria.evento_id,
        competidor1_id=perdedores[0].id,
        competidor2_id=perdedores[1].id
    )

    db.session.add(luta_terceiro_lugar)
    db.session.commit()

    flash('Disputa de 3º lugar gerada com sucesso!', 'success')
    return redirect(url_for('admin.visualizar_chave', categoria_id=categoria_id))


@bp.route('/ferramentas/atribuir-categorias', methods=['GET', 'POST'])
@admin_required
def atribuir_categorias_antigas():
    """
    Ferramenta de uso único para encontrar inscrições antigas sem categoria,
    criar uma categoria 'Geral' para o seu respectivo evento (se não existir)
    e atribuí-la a essas inscrições.
    """
    if request.method == 'POST':
        try:
            # 1. Encontra todas as inscrições que não têm categoria (são as antigas)
            inscricoes_sem_categoria = Inscricao.query.filter(Inscricao.categoria_id.is_(None)).all()

            if not inscricoes_sem_categoria:
                flash('Não foram encontradas inscrições antigas para atualizar.', 'info')
                return redirect(url_for('admin.dashboard'))

            # Usamos um dicionário para não ter de procurar a categoria 'Geral' repetidamente
            categorias_gerais_cache = {}
            count = 0

            for inscricao in inscricoes_sem_categoria:
                evento_id = inscricao.evento_id

                # Verifica se já encontrámos ou criámos a categoria 'Geral' para este evento
                if evento_id not in categorias_gerais_cache:
                    categoria_geral = Categoria.query.filter_by(evento_id=evento_id, nome='Geral').first()

                    if not categoria_geral:
                        # Se não existir, cria-a agora
                        categoria_geral = Categoria(nome='Geral', evento_id=evento_id)
                        db.session.add(categoria_geral)
                        # O 'flush' atribui um ID à nova categoria antes do commit final
                        db.session.flush()

                        # Guarda o ID da categoria no nosso cache
                    categorias_gerais_cache[evento_id] = categoria_geral.id

                # Atribui o ID da categoria padrão à inscrição
                inscricao.categoria_id = categorias_gerais_cache[evento_id]
                count += 1

            db.session.commit()
            flash(f'{count} inscrições antigas foram atribuídas a uma categoria "Geral" com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Ocorreu um erro ao atualizar as inscrições: {e}', 'danger')

        return redirect(url_for('admin.dashboard'))

    # Para um pedido GET, apenas mostra a página com o botão de confirmação
    return render_template('admin/admin_ferramenta_atribuicao.html',
                           titulo="Atribuir Categorias a Inscrições Antigas")

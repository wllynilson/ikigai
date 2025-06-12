from app.decorators import admin_required
from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user, login_user
from sqlalchemy import or_
from datetime import datetime

from . import bp  # Importa o 'bp' do __init__.py do admin
from .. import db  # '..' sobe um nível para o pacote 'app' para pegar o 'db'
from ..models import Evento, Equipe, Inscricao, User
from .forms import EditarInscricaoForm, EventoForm # 'from .' pois assumo que forms.py está na mesma pasta admin
from flask import jsonify
from sqlalchemy.orm import joinedload


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
    return render_template('/admin_form_equipe.html',
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
    inscricoes = Inscricao.query.filter_by(evento_id=evento.id).order_by(Inscricao.data_inscricao).all()
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
    # 1. Lê o número da página a partir da URL (ex: /gerenciar_inscricoes?page=2)
    # O '1' é o valor padrão, e 'type=int' garante que é um número.
    page = request.args.get('page', 1, type=int)

    # Pega os parâmetros de pesquisa que já tínhamos
    termo_pesquisa = request.args.get('q')
    evento_filtro_id = request.args.get('evento_id')

    # A lógica de construção da query permanece a mesma
    # query = Inscricao.query
    query = Inscricao.query.options(
        joinedload(Inscricao.participante),
        joinedload(Inscricao.evento),
        joinedload(Inscricao.equipe)
    )
    if termo_pesquisa:
        query = query.filter(or_(
            Inscricao.user_id.ilike(f'%{termo_pesquisa}%'),  # Busca pelo ID do usuário
            User.username.ilike(f'%{termo_pesquisa}%'),  # Busca pelo nome de usuário
            User.nome_completo.ilike(f'%{termo_pesquisa}%'),  # Busca pelo nome completo do usuário
            User.cpf.ilike(f'%{termo_pesquisa}%'),  # Busca pelo CPF do usuário
            User.email.ilike(f'%{termo_pesquisa}%')  # Busca pelo email do usuário
        ))
    if evento_filtro_id:
        query = query.filter(Inscricao.evento_id == evento_filtro_id)

    inscricoes_paginadas = query.order_by(Inscricao.data_inscricao.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    print(inscricoes_paginadas.items)

    # A busca de eventos para o filtro continua igual
    eventos_para_filtro = Evento.query.order_by(Evento.nome_evento).all()

    # 3. Passamos o objeto de paginação para o template
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

    if inscricao.status == 'Aprovada':
        # Se já estiver aprovada, apenas informa. Código de sucesso 200.
        return jsonify({'status': 'info', 'message': 'Esta inscrição já estava aprovada.'}), 200
    try:
        inscricao.status = 'Aprovada'
        db.session.commit()
        # A resposta de sucesso agora é em JSON
        return jsonify({'status': 'success', 'message': 'Inscrição aprovada com sucesso!', 'novo_status_html': '<span class="badge badge-success">Aprovada</span>'})
    except Exception as e:
        db.session.rollback()
        # A resposta de erro também é em JSON. Código de erro 500.
        return jsonify({'status': 'error', 'message': f'Ocorreu um erro: {str(e)}'}), 500


@bp.route('/inscricao/rejeitar/<int:inscricao_id>', methods=['POST'])
@admin_required
def rejeitar_inscricao(inscricao_id):
    """
    Encontra uma inscrição e altera o seu status para 'Rejeitada'.
    """
    inscricao = Inscricao.query.get_or_404(inscricao_id)
    if inscricao.status == 'Rejeitada':
        return jsonify({'status': 'info', 'message': 'Esta inscrição já estava rejeitada.'}), 200
    try:
        inscricao.status = 'Rejeitada'
        db.session.commit()
        # A resposta de sucesso é em JSON com o novo HTML do badge
        return jsonify({'status': 'success', 'message': 'Inscrição rejeitada.',
                        'novo_status_html': '<span class="badge badge-danger">Rejeitada</span>'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Ocorreu um erro: {str(e)}'}), 500


@bp.route('/inscricao/editar/<int:inscricao_id>', methods=['GET', 'POST'])
@admin_required
def editar_inscricao(inscricao_id):
    """
    Rota para editar uma inscrição existente.
    GET: Exibe o formulário preenchido com os dados atuais.
    POST: Valida e salva as alterações no banco de dados.
    """
    # 1. Busca a inscrição que queremos editar. Erro 404 se não existir.
    inscricao = Inscricao.query.get_or_404(inscricao_id)
    user = User.query.get_or_404(inscricao.user_id)  # Pega o usuário associado à inscrição

    # 2. Instancia o nosso formulário de edição.
    form = EditarInscricaoForm()

    # 3. Lógica para quando o formulário é submetido (POST)
    if form.validate_on_submit():
        # Atualiza os dados do objeto 'inscricao' com os dados do formulário
        inscricao.nome_participante = form.nome_participante.data
        inscricao.sobrenome_participante = form.sobrenome_participante.data
        inscricao.idade = form.idade.data
        inscricao.cpf = form.cpf.data
        inscricao.telefone = form.telefone.data
        inscricao.email = form.email.data

        try:
            # Salva as alterações no banco de dados
            db.session.commit()
            flash('Inscrição atualizada com sucesso!', 'success')
            # Redireciona de volta para a página de gerenciamento
            return redirect(url_for('admin.gerenciar_inscricoes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ocorreu um erro ao atualizar a inscrição: {e}', 'danger')

    # 4. Lógica para quando a página é carregada pela primeira vez (GET)
    elif request.method == 'GET':
        # Preenche o formulário com os dados que já existem no banco de dados
        form.nome_participante.data = user.username
        form.sobrenome_participante.data = user.nome_completo
        # form.idade.data = inscricao.idade
        form.cpf.data = user.cpf
        form.telefone.data = user.telefone
        form.email.data = user.email

    # 5. Renderiza o template, passando o formulário para ele
    return render_template('admin/admin_editar_inscricao.html',
                           titulo='Editar Inscrição',
                           form=form)
from flask import render_template, redirect, url_for, flash, request
from . import bp  # Importa o 'bp' do __init__.py do admin
from .. import db # '..' sobe um nível para o pacote 'app' para pegar o 'db'
from ..models import Evento, Equipe, Inscricao # '..' sobe um nível para pegar os modelos
from datetime import datetime
from flask import request # ... outros imports do flask
from app.admin.forms import EditarInscricaoForm # Importa a classe do formulário que criámos



@bp.route('/')
@bp.route('/dashboard')
def dashboard():
    total_eventos = Evento.query.count()
    total_equipes = Equipe.query.count()
    total_inscricoes = Inscricao.query.count()
    proximos_eventos = Evento.query.filter(
        Evento.data_hora_evento >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)).order_by(
        Evento.data_hora_evento).limit(5).all()
    return render_template('admin/admin_dashboard.html',
                           total_eventos=total_eventos,
                           total_equipes=total_equipes,
                           total_inscricoes=total_inscricoes,
                           proximos_eventos=proximos_eventos)


# --- Gerenciamento de Equipes (já feito, agora dentro do blueprint) ---
@bp.route('/equipes')
def gerenciar_equipes():
    equipes = Equipe.query.order_by(Equipe.nome_equipe).all()
    return render_template('admin/admin_gerenciar_equipes.html', equipes=equipes)


@bp.route('/equipes/nova', methods=['GET', 'POST'])
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
    return render_template('/admin/admin_form_equipe.html',
                           titulo_form=f"Editar Equipe: {equipe_para_editar.nome_equipe}",
                           action_url=url_for('admin.editar_equipe', equipe_id=equipe_id),
                           equipe_dados=equipe_para_editar)  # Passa o objeto equipe para preencher o form


@bp.route('/equipes/<int:equipe_id>/excluir', methods=['POST'])
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
def gerenciar_eventos():
    eventos = Evento.query.order_by(Evento.data_hora_evento.desc()).all()
    # Note o 'admin/' no caminho do template
    return render_template('admin/admin_gerenciar_eventos.html', eventos=eventos)


@bp.route('/eventos/<int:evento_id>/inscricoes')
def listar_inscricoes_evento(evento_id):
    evento = Evento.query.get_or_404(evento_id)
    inscricoes = Inscricao.query.filter_by(evento_id=evento.id).order_by(Inscricao.data_inscricao).all()
    return render_template('admin/admin_listar_inscricoes_evento.html', evento=evento, inscricoes=inscricoes)


@bp.route('/eventos/novo', methods=['GET', 'POST'])
def novo_evento():
    if request.method == 'POST':
        # Pega os dados do formulário
        nome_evento = request.form['nome_evento']
        data_hora_string = request.form['data_hora_evento']
        palestrante = request.form.get('palestrante')
        descricao = request.form.get('descricao')
        local_evento = request.form.get('local_evento')

        # Validações e conversões
        try:
            data_hora_evento = datetime.strptime(data_hora_string, '%Y-%m-%dT%H:%M')
            preco = float(request.form.get('preco', '0').replace(',', '.'))
            numero_vagas = int(request.form['numero_vagas'])
        except ValueError:
            flash('Dados numéricos ou de data inválidos.', 'danger')
            return render_template('admin/admin_form_evento.html', titulo_form="Novo Evento")

        novo_evento = Evento(
            nome_evento=nome_evento, data_hora_evento=data_hora_evento, palestrante=palestrante,
            descricao=descricao, local_evento=local_evento, preco=preco, numero_vagas=numero_vagas
        )
        db.session.add(novo_evento)
        db.session.commit()
        flash('Evento cadastrado com sucesso!', 'success')
        return redirect(url_for('admin.gerenciar_eventos'))

    # Se GET, apenas mostra o formulário
    return render_template('admin/admin_form_evento.html', titulo_form="Novo Evento")


@bp.route('/eventos/<int:evento_id>/editar', methods=['GET', 'POST'])
def editar_evento(evento_id):
    evento = Evento.query.get_or_404(evento_id)
    if request.method == 'POST':
        # Atualiza os dados do objeto 'evento' com os dados do formulário
        evento.nome_evento = request.form['nome_evento']
        evento.data_hora_evento = datetime.strptime(request.form['data_hora_evento'], '%Y-%m-%dT%H:%M')
        evento.palestrante = request.form.get('palestrante')
        evento.descricao = request.form.get('descricao')
        evento.local_evento = request.form.get('local_evento')
        evento.preco = float(request.form.get('preco', '0').replace(',', '.'))
        evento.numero_vagas = int(request.form['numero_vagas'])

        db.session.commit()
        flash('Evento atualizado com sucesso!', 'success')
        return redirect(url_for('admin.gerenciar_eventos'))

    # No GET, formata a data para preencher o campo datetime-local corretamente
    data_para_form = evento.data_hora_evento.strftime('%Y-%m-%dT%H:%M')
    return render_template('admin/admin_form_evento.html', titulo_form="Editar Evento", evento_dados=evento,
                           data_para_form=data_para_form)


@bp.route('/eventos/<int:evento_id>/excluir', methods=['POST'])
def excluir_evento(evento_id):
    evento = Evento.query.get_or_404(evento_id)
    if evento.inscricoes:
        flash('Não é possível excluir um evento que já possui inscritos.', 'danger')
        return redirect(url_for('admin.gerenciar_eventos'))

    db.session.delete(evento)
    db.session.commit()
    flash('Evento excluído com sucesso!', 'success')
    return redirect(url_for('admin.gerenciar_eventos'))



@bp.route('/inscricoes')
#@login_required  # Se quiser que apenas utilizadores logados vejam
def gerenciar_inscricoes():
    """
    Esta rota busca TODAS as inscrições feitas no sistema e as exibe.
    As inscrições são ordenadas por data para mostrar as mais recentes primeiro.
    """
    # 1. Busca todas as inscrições no banco de dados.
    # Usamos .order_by() para organizar os resultados. Aqui, ordenamos
    # pela data de inscrição, da mais nova para a mais antiga (desc).
    todas_as_inscricoes = Inscricao.query.order_by(Inscricao.data_inscricao.desc()).all()

    # 2. Renderiza o template, passando a lista de inscrições para ele.
    return render_template('admin/admin_gerenciar_inscricoes.html',
                           inscricoes=todas_as_inscricoes,
                           titulo='Gerenciar Todas as Inscrições')


@bp.route('/inscricao/cancelar/<int:inscricao_id>', methods=['POST'])  # 'bp' é o nome da sua blueprint
# @login_required
def cancelar_inscricao(inscricao_id):
    """
    Esta rota encontra uma inscrição pelo seu ID e a remove do banco de dados.
    Aceita apenas pedidos POST por segurança.
    """
    # 1. Busca a inscrição no banco de dados. Se não encontrar, retorna um erro 404 (Not Found).
    inscricao_para_cancelar = Inscricao.query.get_or_404(inscricao_id)

    try:
        # 2. Remove o objeto da sessão do banco de dados.
        db.session.delete(inscricao_para_cancelar)

        # 3. Confirma (commit) a transação para salvar a mudança permanentemente.
        db.session.commit()

        # 4. Cria uma mensagem flash para dar feedback ao utilizador.
        flash('Inscrição cancelada com sucesso!', 'success')

    except Exception as e:
        # Em caso de erro, desfaz a transação e mostra uma mensagem de erro.
        db.session.rollback()
        flash(f'Ocorreu um erro ao cancelar a inscrição: {e}', 'danger')

    # 5. Redireciona o utilizador de volta para a página de gerenciamento.
    return redirect(url_for('admin.gerenciar_inscricoes'))


@bp.route('/inscricao/aprovar/<int:inscricao_id>', methods=['POST'])
# @login_required
def aprovar_inscricao(inscricao_id):
    """
    Encontra uma inscrição e altera o seu status para 'Aprovada'.
    """
    inscricao = Inscricao.query.get_or_404(inscricao_id)
    try:
        inscricao.status = 'Aprovada'
        db.session.commit()
        flash('Inscrição APROVADA com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ocorreu um erro ao aprovar a inscrição: {e}', 'danger')

    return redirect(url_for('admin.gerenciar_inscricoes'))


@bp.route('/inscricao/rejeitar/<int:inscricao_id>', methods=['POST'])
# @login_required
def rejeitar_inscricao(inscricao_id):
    """
    Encontra uma inscrição e altera o seu status para 'Rejeitada'.
    """
    inscricao = Inscricao.query.get_or_404(inscricao_id)
    try:
        inscricao.status = 'Rejeitada'
        db.session.commit()
        flash('Inscrição foi Rejeitada.', 'info')  # Usamos 'info' para um tom neutro
    except Exception as e:
        db.session.rollback()
        flash(f'Ocorreu um erro ao rejeitar a inscrição: {e}', 'danger')

    return redirect(url_for('admin.gerenciar_inscricoes'))


@bp.route('/inscricao/editar/<int:inscricao_id>', methods=['GET', 'POST'])
# @login_required
def editar_inscricao(inscricao_id):
    """
    Rota para editar uma inscrição existente.
    GET: Exibe o formulário preenchido com os dados atuais.
    POST: Valida e salva as alterações no banco de dados.
    """
    # 1. Busca a inscrição que queremos editar. Erro 404 se não existir.
    inscricao = Inscricao.query.get_or_404(inscricao_id)

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
        form.nome_participante.data = inscricao.nome_participante
        form.sobrenome_participante.data = inscricao.sobrenome_participante
        form.idade.data = inscricao.idade
        form.cpf.data = inscricao.cpf
        form.telefone.data = inscricao.telefone

    # 5. Renderiza o template, passando o formulário para ele
    return render_template('admin/admin_editar_inscricao.html',
                           titulo='Editar Inscrição',
                           form=form)
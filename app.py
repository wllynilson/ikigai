# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# 1. Configuração Inicial do Aplicativo Flask
app = Flask(__name__)  # Cria uma instância da aplicação Flask

# 2. Configuração do Banco de Dados SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///academia.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'sua_chave_secreta_muito_segura_aqui'  # Mude isso para produção!

db = SQLAlchemy(app)  # Cria uma instância do SQLAlchemy ligada ao nosso app Flask


# 3. Definição dos Modelos do Banco de Dados (Tabelas)

class Equipe(db.Model):
    __tablename__ = 'equipes'
    id = db.Column(db.Integer, primary_key=True)
    nome_equipe = db.Column(db.String(100), nullable=False, unique=True)
    professor_responsavel = db.Column(db.String(100), nullable=False)
    # Relacionamento: Uma equipe pode ter várias inscrições
    inscricoes = db.relationship('Inscricao', backref='equipe', lazy=True)

    def __repr__(self):
        return f'<Equipe {self.nome_equipe}>'


class Evento(db.Model):
    __tablename__ = 'eventos'
    id = db.Column(db.Integer, primary_key=True)
    nome_evento = db.Column(db.String(200), nullable=False)
    data_hora_evento = db.Column(db.DateTime, nullable=False)
    palestrante = db.Column(db.String(100))
    descricao = db.Column(db.Text)
    local_evento = db.Column(db.String(200))
    preco = db.Column(db.Float, default=0.0)
    numero_vagas = db.Column(db.Integer, nullable=False)
    # Relacionamento: Um evento pode ter várias inscrições
    inscricoes = db.relationship('Inscricao', backref='evento', lazy=True)

    def __repr__(self):
        return f'<Evento {self.nome_evento}>'


class Inscricao(db.Model):
    __tablename__ = 'inscricoes'
    id = db.Column(db.Integer, primary_key=True)
    nome_participante = db.Column(db.String(100), nullable=False)
    sobrenome_participante = db.Column(db.String(100), nullable=False)
    idade = db.Column(db.Integer, nullable=False)
    cpf = db.Column(db.String(14), nullable=False)  # Não é mais unique aqui, mas na combinação evento+cpf
    telefone = db.Column(db.String(20), nullable=False)
    data_inscricao = db.Column(db.DateTime, default=datetime.utcnow)
    evento_id = db.Column(db.Integer, db.ForeignKey('eventos.id'), nullable=False)
    equipe_id = db.Column(db.Integer, db.ForeignKey('equipes.id'), nullable=False)

    # Para garantir que um CPF não se inscreva múltiplas vezes no MESMO evento.
    __table_args__ = (db.UniqueConstraint('cpf', 'evento_id', name='uq_cpf_evento'),)

    def __repr__(self):
        return f'<Inscricao {self.nome_participante} no evento {self.evento_id}>'


# --- ROTAS PÚBLICAS (CLIENTE) ---

@app.route('/')
def index():
    eventos = Evento.query.filter(Evento.data_hora_evento >= datetime.utcnow()).order_by(Evento.data_hora_evento).all()
    return render_template('index.html', eventos=eventos)


@app.route('/inscrever/<int:evento_id>', methods=['GET', 'POST'])
def rota_inscrever_evento(evento_id):
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
            evento_id=evento.id,
            equipe_id=equipe_id
        )

        try:
            db.session.add(nova_inscricao)
            evento.numero_vagas -= 1
            db.session.commit()
            flash(f'Inscrição para {evento.nome_evento} realizada com sucesso!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao processar inscrição: {str(e)}', 'danger')  # Usar str(e) para a mensagem
            return render_template('inscrever_evento.html', evento=evento, equipes=equipes)

    return render_template('inscrever_evento.html', evento=evento, equipes=equipes)


# --- ROTAS DE CADASTRO SIMPLES (SERÃO INTEGRADAS/SUBSTITUÍDAS PELA ÁREA ADMIN) ---

@app.route('/cadastrar-equipe', methods=['GET', 'POST'])
def rota_cadastrar_equipe():
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
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao cadastrar equipe: {str(e)}', 'danger')
        return redirect(url_for('rota_cadastrar_equipe'))
    equipes = Equipe.query.order_by(Equipe.nome_equipe).all()
    return render_template('cadastrar_equipe.html', equipes=equipes)


@app.route('/cadastrar-evento', methods=['GET', 'POST'])
def rota_cadastrar_evento():
    if request.method == 'POST':
        nome_evento = request.form['nome_evento']
        data_hora_string = request.form['data_hora_evento']
        try:
            data_hora_evento = datetime.strptime(data_hora_string, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Formato de data e hora inválido. Use o formato esperado.', 'danger')
            return redirect(url_for('rota_cadastrar_evento'))

        palestrante = request.form.get('palestrante')
        descricao = request.form.get('descricao')
        local_evento = request.form.get('local_evento')
        try:
            preco_str = request.form.get('preco', '0').replace(',', '.')
            preco = float(preco_str if preco_str else 0)
            numero_vagas = int(request.form['numero_vagas'])
        except ValueError:
            flash('Preço ou número de vagas inválido. Verifique os valores numéricos.', 'danger')
            return redirect(url_for('rota_cadastrar_evento'))

        if numero_vagas <= 0:
            flash('Número de vagas deve ser positivo.', 'danger')
            return redirect(url_for('rota_cadastrar_evento'))

        novo_evento = Evento(
            nome_evento=nome_evento, data_hora_evento=data_hora_evento, palestrante=palestrante,
            descricao=descricao, local_evento=local_evento, preco=preco, numero_vagas=numero_vagas
        )
        try:
            db.session.add(novo_evento)
            db.session.commit()
            flash('Evento cadastrado com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar evento: {str(e)}', 'danger')
        return redirect(url_for('rota_cadastrar_evento'))
    return render_template('cadastrar_evento.html')


# --- ROTAS DA ÁREA ADMINISTRATIVA ---

@app.route('/admin/')
@app.route('/admin/dashboard')
def admin_dashboard():
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


@app.route('/admin/eventos')
def admin_gerenciar_eventos():  # Anteriormente admin_listar_eventos
    eventos = Evento.query.order_by(Evento.data_hora_evento.desc()).all()
    return render_template('admin/admin_gerenciar_eventos.html', eventos=eventos)


@app.route('/admin/eventos/<int:evento_id>/inscricoes')
def admin_listar_inscricoes_evento(evento_id):
    evento = Evento.query.get_or_404(evento_id)
    inscricoes = Inscricao.query.filter_by(evento_id=evento.id).order_by(Inscricao.data_inscricao).all()
    return render_template('admin/admin_listar_inscricoes_evento.html', evento=evento, inscricoes=inscricoes)


# --- FIM DAS ROTAS DA ÁREA ADMINISTRATIVA ---


if __name__ == '__main__':
    with app.app_context():
        # db.drop_all() # Use com cuidado para apagar tudo e recomeçar
        db.create_all()  # Cria as tabelas se não existirem
    app.run(debug=True)  # Inicia o servidor de desenvolvimento do Flask
from . import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Relação N-para-N entre Usuarios e Equipas (opcional, mas bom ter)
# Um utilizador pode ser membro de várias equipas, e uma equipa tem vários Usuarios
membros_equipe = db.Table('membros_equipe',
                          db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
                          db.Column('equipe_id', db.Integer, db.ForeignKey('equipes.id'), primary_key=True)
                          )


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), nullable=False, default='user')
    nome_completo = db.Column(db.String(150))
    bio = db.Column(db.Text)
    imagem_perfil = db.Column(db.String(300))
    # --- NOVO CAMPO PARA O FUTURO LOGIN COM GOOGLE ---
    google_id = db.Column(db.String(30), nullable=True, unique=True, index=True)

    # Relação para saber quais inscrições um utilizador registou
    inscricoes_registradas = db.relationship('Inscricao', backref='registrado_por', lazy='dynamic',
                                             foreign_keys='Inscricao.registrado_por_user_id')
    # Relação para associar uma conta de utilizador a um perfil de participante
    participante = db.relationship('Participante', backref='conta_user', uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Equipe(db.Model):
    __tablename__ = 'equipes'
    id = db.Column(db.Integer, primary_key=True)
    nome_equipe = db.Column(db.String(100), nullable=False, unique=True)
    professor_responsavel = db.Column(db.String(100))
    membros = db.relationship('User', secondary=membros_equipe, backref=db.backref('equipes', lazy='dynamic'),
                              lazy='dynamic')
    participantes = db.relationship('Participante', backref='equipe', lazy='dynamic')

    def __repr__(self):
        return f'<Equipe {self.nome_equipe}>'


class Participante(db.Model):
    __tablename__ = 'participantes'
    id = db.Column(db.Integer, primary_key=True)
    nome_completo = db.Column(db.String(150), nullable=False)
    data_nascimento = db.Column(db.Date, nullable=True)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    telefone = db.Column(db.String(20))
    graduacao = db.Column(db.String(50))
    peso = db.Column(db.Float)

    # Ligação opcional a uma conta de utilizador
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, unique=True)
    # Ligação obrigatória a uma equipe
    equipe_id = db.Column(db.Integer, db.ForeignKey('equipes.id'), nullable=False)

    inscricoes = db.relationship('Inscricao', backref='participante', lazy='dynamic')

    def __repr__(self):
        return f'<Participante {self.nome_completo}>'


class Evento(db.Model):
    __tablename__ = 'eventos'
    id = db.Column(db.Integer, primary_key=True)
    nome_evento = db.Column(db.String(200), nullable=False)
    data_hora_evento = db.Column(db.DateTime, nullable=False)
    palestrante = db.Column(db.String(100))
    imagem_palestrante = db.Column(db.String(300))
    descricao = db.Column(db.Text)
    local_evento = db.Column(db.String(200))
    preco = db.Column(db.Float, default=0.0)
    numero_vagas = db.Column(db.Integer, nullable=False)
    pix_copia_e_cola = db.Column(db.Text)
    slug = db.Column(db.String(255), unique=True, index=True, nullable=False)

    categorias = db.relationship('Categoria', backref='evento', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Evento {self.nome_evento}>'


class Categoria(db.Model):
    __tablename__ = 'categorias'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    evento_id = db.Column(db.Integer, db.ForeignKey('eventos.id'), nullable=False)
    inscricoes = db.relationship('Inscricao', backref='categoria', lazy='dynamic')
    lutas = db.relationship('Luta', backref='categoria', lazy='dynamic')

    def __repr__(self):
        return f'<Categoria {self.nome}>'


class Inscricao(db.Model):
    __tablename__ = 'inscricoes'
    id = db.Column(db.Integer, primary_key=True)
    data_inscricao = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='Pendente')

    participante_id = db.Column(db.Integer, db.ForeignKey('participantes.id'), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=False)
    registrado_por_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    pagamento = db.relationship('Pagamento', backref='inscricao', uselist=False, cascade="all, delete-orphan")

    __table_args__ = (db.UniqueConstraint('participante_id', 'categoria_id', name='uq_participante_categoria'),)

    def __repr__(self):
        return f'<Inscricao do participante {self.participante_id} na categoria {self.categoria_id}>'


class Pagamento(db.Model):
    __tablename__ = 'pagamentos'
    id = db.Column(db.Integer, primary_key=True)
    valor = db.Column(db.Float, nullable=False)
    data_pagamento = db.Column(db.DateTime, default=datetime.utcnow)
    metodo = db.Column(db.String(50), nullable=False)  # Ex: 'Pix', 'PayPal'
    status_pagamento = db.Column(db.String(30), nullable=False, default='Concluido')  # Ex: 'Concluido', 'Reembolsado'
    id_transacao_externa = db.Column(db.String(200))  # ID do PayPal, etc.
    inscricao_id = db.Column(db.Integer, db.ForeignKey('inscricoes.id'), nullable=False, unique=True)

    def __repr__(self):
        return f'<Pagamento {self.id} para a inscrição {self.inscricao_id}>'


class Luta(db.Model):
    __tablename__ = 'lutas'
    id = db.Column(db.Integer, primary_key=True)
    round = db.Column(db.Integer, nullable=False)
    ordem_na_chave = db.Column(db.Integer, nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=False)

    competidor1_id = db.Column(db.Integer, db.ForeignKey('participantes.id'), nullable=True)
    competidor2_id = db.Column(db.Integer, db.ForeignKey('participantes.id'), nullable=True)
    vencedor_id = db.Column(db.Integer, db.ForeignKey('participantes.id'), nullable=True)

    competidor1 = db.relationship('Participante', foreign_keys=[competidor1_id])
    competidor2 = db.relationship('Participante', foreign_keys=[competidor2_id])
    vencedor = db.relationship('Participante', foreign_keys=[vencedor_id])

    def __repr__(self):
        return f'<Luta {self.id}>'
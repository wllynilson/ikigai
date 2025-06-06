from app import db  # Importa a instância 'db' do app principal
from datetime import datetime


class Equipe(db.Model):
    # ... (código da classe Equipe)
    __tablename__ = 'equipes'
    id = db.Column(db.Integer, primary_key=True)
    nome_equipe = db.Column(db.String(100), nullable=False, unique=True)
    professor_responsavel = db.Column(db.String(100), nullable=False)
    inscricoes = db.relationship('Inscricao', backref='equipe', lazy=True)

    def __repr__(self):
        return f'<Equipe {self.nome_equipe}>'


class Evento(db.Model):
    # ... (código da classe Evento)
    __tablename__ = 'eventos'
    id = db.Column(db.Integer, primary_key=True)
    nome_evento = db.Column(db.String(200), nullable=False)
    data_hora_evento = db.Column(db.DateTime, nullable=False)
    palestrante = db.Column(db.String(100))
    descricao = db.Column(db.Text)
    local_evento = db.Column(db.String(200))
    preco = db.Column(db.Float, default=0.0)
    numero_vagas = db.Column(db.Integer, nullable=False)
    inscricoes = db.relationship('Inscricao', backref='evento', lazy=True)

    def __repr__(self):
        return f'<Evento {self.nome_evento}>'


class Inscricao(db.Model):
    # ... (código da classe Inscricao)
    __tablename__ = 'inscricoes'
    id = db.Column(db.Integer, primary_key=True)
    nome_participante = db.Column(db.String(100), nullable=False)
    sobrenome_participante = db.Column(db.String(100), nullable=False)
    idade = db.Column(db.Integer, nullable=False)
    cpf = db.Column(db.String(14), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    data_inscricao = db.Column(db.DateTime, default=datetime.utcnow)
    evento_id = db.Column(db.Integer, db.ForeignKey('eventos.id'), nullable=False)
    equipe_id = db.Column(db.Integer, db.ForeignKey('equipes.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Pendente')
    __table_args__ = (db.UniqueConstraint('cpf', 'evento_id', name='uq_cpf_evento'),)

    def __repr__(self):
        return f'<Inscricao {self.nome_participante} no evento {self.evento_id}>'

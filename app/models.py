from app import db
from datetime import datetime
from flask_login import UserMixin # Importa o UserMixin
from werkzeug.security import generate_password_hash, check_password_hash # Importa as funções de hash



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
    imagem_palestrante = db.Column(db.String(300), nullable=True) # URL para a imagem
    descricao = db.Column(db.Text)
    local_evento = db.Column(db.String(200))
    preco = db.Column(db.Float, default=0.0)
    numero_vagas = db.Column(db.Integer, nullable=False)
    pix_copia_e_cola = db.Column(db.Text, nullable=True)  # Campo para o Pix

    inscricoes = db.relationship('Inscricao', backref='evento', lazy=True)

    def __repr__(self):
        return f'<Evento {self.nome_evento}>'


class Inscricao(db.Model):
    __tablename__ = 'inscricoes'
    id = db.Column(db.Integer, primary_key=True)
    data_inscricao = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='Pendente')

    nome_participante = db.Column(db.String(100), nullable=True)
    sobrenome_participante = db.Column(db.String(100), nullable=True)
    idade = db.Column(db.Integer, nullable=True)
    cpf = db.Column(db.String(14), nullable=True)
    telefone = db.Column(db.String(20), nullable=True)
    # ----------------------------------------------------------------
    # --- As 3 conexões essenciais ---
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    evento_id = db.Column(db.Integer, db.ForeignKey('eventos.id'), nullable=False)
    equipe_id = db.Column(db.Integer, db.ForeignKey('equipes.id'), nullable=False)
    # Reintroduz a regra de negócio para evitar duplicados
    # __table_args__ = (db.UniqueConstraint('cpf', 'evento_id', name='uq_cpf_por_evento'),)

    def __repr__(self):
        return f'<Inscricao de {self.nome_participante or self.id}>'

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    nome_completo = db.Column(db.String(150), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    imagem_perfil = db.Column(db.String(300), nullable=True)  # URL para a imagem de perfil
    role = db.Column(db.String(20), nullable=False, default='user')  # Papel do utilizador
    cpf = db.Column(db.String(14), unique=True, nullable=True)  # CPF será único e opcional no início
    telefone = db.Column(db.String(20), nullable=True)  # Telefone também opcional
    inscricoes = db.relationship('Inscricao', backref='participante', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

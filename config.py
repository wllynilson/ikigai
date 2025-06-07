import os

class Config:
    # A chave secreta será lida da variável de ambiente. Se não existir, usa a chave de desenvolvimento (NÃO USE ESTA EM PRODUÇÃO)
    SECRET_KEY = os.environ.get('SECRET_KEY') or '0jUWMP1TLSS7EUJPVzV51ewNCC493mKU'

    # Configuração do Banco de Dados
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
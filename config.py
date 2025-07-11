# Ficheiro: config.py (VERSÃO ATUALIZADA)

import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env')) # 2. A chamada para carregar o ficheiro está aqui?

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'uma-chave-secreta-muito-dificil-de-adivinhar'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Linha para verificar o modo DEBUG
    # O '1' significa 'True'. No Render, esta variável não existe, então será False.
    DEBUG = os.environ.get('FLASK_DEBUG') == '1'

    # LÓGICA DE CORREÇÃO DA DATABASE URL
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    # A configuração final usa a URL corrigida ou a de desenvolvimento (sqlite)
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'sqlite:///' + os.path.join(basedir, 'app.db')

    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY')
    STRIPE_ENDPOINT_SECRET = os.environ.get('STRIPE_ENDPOINT_SECRET')
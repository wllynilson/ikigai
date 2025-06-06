from app import create_app, db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # Descomente a linha abaixo com MUITO CUIDADO.
        # Ela apagará todo o seu banco de dados.
        # db.drop_all()

        # Garante que o banco de dados e as tabelas sejam criados se não existirem.
        db.create_all()

    app.run(debug=True)
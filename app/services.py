# Ficheiro: app/services.py

import math
import random
from . import db
from .models import Inscricao, Luta, User

def gerar_chave_eliminatoria_simples(categoria_id: int, evento_id: int):
    """
    Gera uma chave de eliminatória simples para uma dada categoria de um evento.
    1. Calcula o tamanho da chave e o número de 'byes' (isenções na 1ª ronda).
    2. Sorteia a ordem dos competidores.
    3. Cria as lutas da primeira ronda.
    4. Cria as lutas subsequentes como placeholders.
    """
    try:
        # 1. Obter todos os competidores aprovados para a categoria
        inscricoes_aprovadas = Inscricao.query.filter_by(
            categoria_id=categoria_id,
            status='Aprovada'
        ).all()

        if len(inscricoes_aprovadas) < 2:
            return False, "São necessários pelo menos 2 competidores aprovados para gerar uma chave."

        # Extrai os objetos User das inscrições
        competidores = [i.participante for i in inscricoes_aprovadas]
        # Embaralha a lista para um sorteio aleatório
        random.shuffle(competidores)

        num_competidores = len(competidores)

        # 2. Calcular o tamanho da chave e os 'byes'
        # Encontra a próxima potência de 2 (ex: para 13 competidores, a chave é de 16)
        next_power_of_2 = 2**math.ceil(math.log2(num_competidores))
        num_byes = next_power_of_2 - num_competidores
        num_lutas_ronda_1 = num_competidores - num_byes

        # Separa os que lutam na 1ª ronda e os que ficam de 'bye'
        competidores_com_bye = competidores[:num_byes]
        competidores_ronda_1 = competidores[num_byes:]

        # 3. Criar e salvar as lutas da primeira ronda
        lutas_criadas = []
        ordem = 1
        for i in range(0, num_lutas_ronda_1, 2):
            luta = Luta(
                round=1,
                ordem_na_chave=ordem,
                categoria_id=categoria_id,
                evento_id=evento_id,
                competidor1_id=competidores_ronda_1[i].id,
                competidor2_id=competidores_ronda_1[i+1].id,
            )
            lutas_criadas.append(luta)
            db.session.add(luta)
            ordem += 1

        # 4. Criar as lutas das rondas seguintes como placeholders
        num_rondas = int(math.log2(next_power_of_2))

        # A ronda 2 terá os vencedores da ronda 1 e os competidores com 'bye'
        num_competidores_ronda_2 = num_lutas_ronda_1 + num_byes
        num_lutas_ronda_2 = num_competidores_ronda_2 // 2

        for r in range(2, num_rondas + 1):
            num_lutas_nesta_ronda = next_power_of_2 // (2**r)
            for _ in range(num_lutas_nesta_ronda):
                luta = Luta(
                    round=r,
                    ordem_na_chave=ordem,
                    categoria_id=categoria_id,
                    evento_id=evento_id,
                    # Competidores e vencedor são nulos, serão preenchidos depois
                )
                lutas_criadas.append(luta)
                db.session.add(luta)
                ordem += 1

        db.session.commit()
        return True, f"Chave gerada com sucesso para {num_competidores} competidores."

    except Exception as e:
        db.session.rollback()
        return False, f"Ocorreu um erro ao gerar a chave: {e}"
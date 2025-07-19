import stripe
from flask import Blueprint
from flask import request, current_app, jsonify

from app import csrf
from app import db
from app.models import Inscricao, Pagamento

public_bp = Blueprint('public', __name__)


@public_bp.route('/stripe-webhook', methods=['POST'])
@csrf.exempt
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = current_app.config.get('STRIPE_ENDPOINT_SECRET')

    if not sig_header or not endpoint_secret:
        return 'Configuração de webhook em falta', 400

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except Exception as e:
        return str(e), 400


    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        inscricao_id = session.get('metadata', {}).get('inscricao_id')

        if inscricao_id:
            # Usamos with_for_update() para garantir que lemos os dados mais recentes e bloqueamos a linha
            inscricao = Inscricao.query.with_for_update().get(inscricao_id)

            if inscricao:

                if inscricao.status == 'Pendente':
                    try:
                        inscricao.status = 'Aprovada'
                        pagamento = Pagamento(
                            valor=(session.get('amount_total', 0) / 100.0),
                            metodo='Stripe',
                            status_pagamento='Concluido',
                            id_transacao_externa=session.get('payment_intent'),
                            inscricao_id=inscricao.id
                        )
                        pagamento_existente = Pagamento.query.filter_by(inscricao_id=inscricao.id).first()
                        if not pagamento_existente:
                            # insere novo pagamento
                            db.session.add(pagamento)
                            db.session.commit()
                        else:
                            print('Pagamento já existe para a inscrição:', inscricao.id)
                    except Exception as e:
                        db.session.rollback()
                        print(f"Erro ao processar pagamento: {str(e)}")
                        return jsonify(error=str(e)), 500

    return jsonify(success=True)
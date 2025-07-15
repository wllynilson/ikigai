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
    except ValueError:
        return 'Payload inválido', 400
    except stripe.error.SignatureVerificationError:
        return 'Assinatura inválida', 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        inscricao_id = session.get('metadata', {}).get('inscricao_id')

        if inscricao_id:
            inscricao = Inscricao.query.get(inscricao_id)
            # Verifica se a inscrição existe e está pendente
            if inscricao and inscricao.status == 'Pendente':
                # Verifica se já existe um pagamento para esta inscrição
                pagamento_existente = Pagamento.query.filter_by(inscricao_id=inscricao.id).first()

                if not pagamento_existente:
                    inscricao.status = 'Aprovada'
                    pagamento = Pagamento(
                        valor=(session.get('amount_total', 0) / 100.0),
                        metodo='Stripe',
                        status_pagamento='Concluido',
                        id_transacao_externa=session.get('payment_intent'),
                        inscricao_id=inscricao.id
                    )
                    db.session.add(pagamento)
                    try:
                        db.session.commit()
                        print(f"Webhook processado: Inscrição {inscricao_id} aprovada e pagamento registado.")
                    except Exception as e:
                        db.session.rollback()
                        print(f"Erro ao processar pagamento: {str(e)}")
                        return jsonify(error=str(e)), 500

    return jsonify(success=True)

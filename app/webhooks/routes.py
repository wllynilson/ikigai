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
    # Obtém o corpo do pedido (os dados do evento)
    payload = request.data
    # Obtém a assinatura enviada pelo Stripe no cabeçalho
    sig_header = request.headers.get('Stripe-Signature')
    # Obtém a nossa "senha secreta" do webhook a partir das configurações
    endpoint_secret = current_app.config.get('STRIPE_ENDPOINT_SECRET')

    if not sig_header or not endpoint_secret:
        # Se não tivermos a assinatura ou a nossa senha secreta, não podemos continuar
        return 'Configuração de webhook em falta', 400

    try:
        # 1. Verifica se o evento é genuíno e veio mesmo do Stripe
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Payload inválido
        return 'Payload inválido', 400
    except stripe.error.SignatureVerificationError as e:
        # Assinatura inválida
        return 'Assinatura inválida', 400

    # 2. Lida com o evento se a assinatura for válida
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        # Recupera o ID da nossa inscrição que guardamos nos metadados
        inscricao_id = session.get('metadata', {}).get('inscricao_id')

        if inscricao_id:
            inscricao = Inscricao.query.get(inscricao_id)
            # Apenas atualiza se a inscrição ainda estiver pendente
            if inscricao and inscricao.status == 'Pendente':
                # ATUALIZA O STATUS E CRIA O PAGAMENTO
                inscricao.status = 'Aprovada'

                pagamento = Pagamento(
                    valor=(session.get('amount_total', 0) / 100.0),  # Stripe usa centavos
                    metodo='Stripe',
                    status_pagamento='Concluido',
                    id_transacao_externa=session.get('payment_intent'),
                    inscricao_id=inscricao.id
                )
                db.session.add(pagamento)
                db.session.commit()
                print(f"Webhook processado: Inscrição {inscricao_id} aprovada e pagamento registado.")

    # 3. Retorna uma resposta de sucesso para o Stripe saber que recebemos a notificação
    return jsonify(success=True)

import time
import random


def generate_request_id() -> str:
    """Gera um request_id numérico dinâmico idêntico ao do navegador."""
    return str(random.randint(100, 999))


def get_auth_payload(ssid: str) -> dict:
    """Gera a mensagem de autenticação (ssid)."""
    return {
        "name": "authenticate",
        "msg": {
            "ssid": ssid,
            "protocol": 3,
            "session_id": "",
            "client_name": "frontend"
        }
    }


def get_subscribe_positions_state_payload() -> dict:
    """Gera o payload para subscrever ao estado de posições ativas do portfólio."""
    return {
        "name": "subscribeMessage",
        "request_id": generate_request_id(),
        "msg": {
            "name": "positions-state"
        }
    }


def handle_authenticated(router, data: dict):
    """Manipula a resposta de autenticação recebida do servidor e solicita saldos, posições e comissões/payouts."""
    is_successful = data.get("msg", False)
    if is_successful:
        print("[+] Autenticado no WebSocket com sucesso!")
        if router.api:
            router.api.is_connected = True
            
            from .balances import get_balances_payload
            from .instruments import get_initialization_data_payload
            
            router.send(get_balances_payload())
            router.send(get_initialization_data_payload())
            router.send(get_subscribe_positions_state_payload())
    else:
        print("[-] Falha na autenticação do WebSocket.")

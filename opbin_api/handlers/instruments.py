import time
from .auth import generate_request_id


def get_instruments_payload(instrument_type: str = "turbo-option") -> dict:
    return {
        "name": "sendMessage",
        "request_id": generate_request_id(),
        "local_time": int(time.time() * 1000) % 100000,
        "msg": {
            "name": "get-instruments",
            "version": "4.0",
            "body": {
                "type": instrument_type
            }
        }
    }


def get_initialization_data_payload() -> dict:
    """Gera o payload para obter os dados de inicialização e comissões/payouts dos ativos."""
    return {
        "name": "sendMessage",
        "request_id": generate_request_id(),
        "local_time": int(time.time() * 1000) % 100000,
        "msg": {
            "name": "get-initialization-data",
            "version": "4.0",
            "body": {}
        }
    }


def handle_initialization_data(router, data: dict):
    """
    Processa initialization-data retornado pela corretora e calcula automaticamente
    o profit_percent em tempo real para cada modalidade (turbo, binary, blitz):
    profit_percent = 100 - commission
    """
    init_data = data.get("msg", {})
    if router.api and isinstance(init_data, dict):
        for cat in ["turbo", "binary", "blitz"]:
            actives = init_data.get(cat, {}).get("actives", {})
            if isinstance(actives, dict):
                for act_id_str, act_info in actives.items():
                    try:
                        act_id = int(act_id_str)
                    except (ValueError, TypeError):
                        act_id = act_info.get("id")
                    
                    commission = act_info.get("option", {}).get("profit", {}).get("commission")
                    if commission is not None and act_id:
                        payout = 100 - int(commission)
                        if cat == "blitz":
                            router.api.blitz_payouts[act_id] = payout
                        else:
                            router.api.payouts[act_id] = payout
                        router.api.commissions[act_id] = float(commission)


def handle_instruments(router, data: dict):
    instruments = data.get("msg", {})
    if router.api:
        router.api.instruments = instruments
        if isinstance(instruments, dict) and "instruments" in instruments:
            for inst in instruments.get("instruments", []):
                act_id = inst.get("active_id")
                commission = inst.get("option", {}).get("profit", {}).get("commission")
                if commission is not None and act_id:
                    payout = 100.0 - float(commission)
                    router.api.payouts[act_id] = payout
                    router.api.commissions[act_id] = float(commission)


def handle_traders_mood(router, data: dict):
    mood = data.get("msg", {})
    if router.api:
        router.api.traders_mood = mood


def handle_top_assets(router, data: dict):
    assets = data.get("msg", {})
    if router.api:
        router.api.top_assets = assets


def handle_underlying_list(router, data: dict):
    underlyings = data.get("msg", {})
    if router.api:
        router.api.underlyings = underlyings

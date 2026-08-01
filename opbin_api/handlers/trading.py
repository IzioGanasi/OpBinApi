import time
from .auth import generate_request_id


def get_buy_binary_payload(active_id: int, amount: float, direction: str, duration: int = 1, option_type_id: int = 3) -> dict:
    return {
        "name": "sendMessage",
        "request_id": generate_request_id(),
        "local_time": int(time.time() * 1000) % 100000,
        "msg": {
            "name": "binary-options.open-option",
            "version": "1.0",
            "body": {
                "active_id": active_id,
                "amount": amount,
                "direction": direction.lower(),
                "option_type_id": option_type_id,
                "user_balance_id": None
            }
        }
    }


def get_buy_digital_payload(instrument_id: str, amount: float) -> dict:
    return {
        "name": "sendMessage",
        "request_id": generate_request_id(),
        "local_time": int(time.time() * 1000) % 100000,
        "msg": {
            "name": "digital-options.place-digital-option",
            "version": "1.0",
            "body": {
                "instrument_id": instrument_id,
                "amount": str(amount)
            }
        }
    }


def handle_position_changed(router, data: dict):
    pos_data = data.get("msg", {})
    if router.api:
        router.api._emit_position(pos_data)


def handle_option(router, data: dict):
    option_data = data.get("msg", {})
    if router.api:
        router.api.last_option_event = option_data


def handle_digital_option_placed(router, data: dict):
    digital_data = data.get("msg", {})
    if router.api:
        router.api.last_digital_placed = digital_data


def handle_history_positions(router, data: dict):
    history = data.get("msg", {})
    if router.api:
        router.api.positions_history = history

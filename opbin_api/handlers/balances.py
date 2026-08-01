import time
from .auth import generate_request_id


def get_balances_payload() -> dict:
    return {
        "name": "sendMessage",
        "request_id": generate_request_id(),
        "local_time": int(time.time() * 1000) % 100000,
        "msg": {
            "name": "get-balances",
            "version": "1.0"
        }
    }


def get_select_active_balance_payload(balance_id: int) -> dict:
    return {
        "name": "sendMessage",
        "request_id": generate_request_id(),
        "local_time": int(time.time() * 1000) % 100000,
        "msg": {
            "name": "profile.change-active-balance",
            "version": "1.0",
            "body": {
                "balance_id": balance_id
            }
        }
    }


def handle_balances(router, data: dict):
    balances_data = data.get("msg", [])
    if isinstance(balances_data, list) and router.api:
        router.api.balances = balances_data

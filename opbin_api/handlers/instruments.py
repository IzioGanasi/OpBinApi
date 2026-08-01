import time
from .auth import generate_request_id


def get_instruments_payload(instrument_type: str = "digital-option") -> dict:
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


def handle_instruments(router, data: dict):
    instruments = data.get("msg", {})
    if router.api:
        router.api.instruments = instruments


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

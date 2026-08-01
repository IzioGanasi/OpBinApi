import time
from .auth import generate_request_id


def get_candles_payload(active_id: int, size: int = 60, count: int = 10) -> dict:
    return {
        "name": "sendMessage",
        "request_id": generate_request_id(),
        "local_time": int(time.time() * 1000) % 100000,
        "msg": {
            "name": "get-candles",
            "version": "2.0",
            "body": {
                "active_id": active_id,
                "size": size,
                "to": int(time.time()),
                "count": count
            }
        }
    }


def get_subscribe_candle_payload(active_id: int, size: int = 60) -> dict:
    return {
        "name": "subscribeMessage",
        "request_id": generate_request_id(),
        "local_time": int(time.time() * 1000) % 100000,
        "msg": {
            "name": "candle-generated",
            "params": {
                "routingFilters": {
                    "active_id": active_id,
                    "size": size
                }
            }
        }
    }


def handle_candles(router, data: dict):
    candles = data.get("msg", {}).get("candles", [])
    if router.api:
        router.api.last_candles = candles


def handle_candle_generated(router, data: dict):
    candle = data.get("msg", {})
    if router.api:
        router.api._emit_candle(candle)

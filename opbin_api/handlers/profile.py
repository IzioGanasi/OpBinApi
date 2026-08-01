import time
from .auth import generate_request_id


def get_profile_payload() -> dict:
    return {
        "name": "sendMessage",
        "request_id": generate_request_id(),
        "local_time": int(time.time() * 1000) % 100000,
        "msg": {
            "name": "get-profile",
            "version": "1.0"
        }
    }


def handle_profile(router, data: dict):
    profile_data = data.get("msg", {})
    if router.api:
        router.api.profile_info = profile_data

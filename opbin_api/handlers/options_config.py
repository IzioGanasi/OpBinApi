import time
from .auth import generate_request_id


def get_set_options_payload(send_results: bool = True) -> dict:
    return {
        "name": "setOptions",
        "request_id": f"request_{generate_request_id()}",
        "local_time": int(time.time() * 1000) % 100000,
        "msg": {
            "sendResults": send_results
        }
    }


def get_set_lang_payload(lang: str = "pt_PT") -> dict:
    return {
        "name": "setLang",
        "request_id": f"request_{generate_request_id()}",
        "local_time": int(time.time() * 1000) % 100000,
        "msg": {
            "lang": lang
        }
    }


def send_initial_client_settings(router):
    router.send(get_set_options_payload(send_results=True))
    router.send(get_set_lang_payload(lang="pt_PT"))

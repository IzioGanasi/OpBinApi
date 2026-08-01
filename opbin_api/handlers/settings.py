def handle_user_settings(router, data: dict):
    configs = data.get("msg", {}).get("configs", [])
    if router.api:
        router.api.user_settings = configs


def handle_user_availability(router, data: dict):
    availability = data.get("msg", {})
    if router.api:
        router.api.user_availability = availability

def handle_bonus(router, data: dict):
    bonus_info = data.get("msg", {})
    if router.api:
        router.api.bonus_info = bonus_info


def handle_promo_codes(router, data: dict):
    promos = data.get("msg", [])
    if router.api:
        router.api.promo_codes = promos

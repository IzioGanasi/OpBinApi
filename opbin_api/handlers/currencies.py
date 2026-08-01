def handle_currencies_list(router, data: dict):
    currencies = data.get("msg", {}).get("currencies", [])
    if router.api:
        router.api.currencies = currencies

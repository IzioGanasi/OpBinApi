def handle_chat_message(router, data: dict):
    msg = data.get("msg", {})
    if router.api:
        router.api.last_chat_message = msg


def handle_leaderboard(router, data: dict):
    leaderboard_data = data.get("msg", {})
    if router.api:
        router.api.leaderboard = leaderboard_data

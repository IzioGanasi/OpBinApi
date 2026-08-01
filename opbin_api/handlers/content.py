def handle_faq(router, data: dict):
    faq_data = data.get("msg", {})
    if router.api:
        router.api.faq = faq_data


def handle_videos(router, data: dict):
    videos = data.get("msg", {})
    if router.api:
        router.api.videos = videos


def handle_script_indicators(router, data: dict):
    indicators = data.get("msg", {})
    if router.api:
        router.api.indicators = indicators

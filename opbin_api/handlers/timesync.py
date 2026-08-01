def handle_timesync(router, data: dict):
    timestamp_ms = data.get("msg")
    if router.api and timestamp_ms:
        router.api.server_timestamp = timestamp_ms

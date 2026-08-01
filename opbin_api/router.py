import json
import threading
import websocket as _ws_pkg

from .handlers import (
    handle_authenticated, get_auth_payload,
    handle_balances,
    handle_timesync,
    handle_profile,
    handle_candles, handle_candle_generated,
    handle_position_changed, handle_option, handle_digital_option_placed, handle_history_positions,
    send_initial_client_settings,
    handle_instruments, handle_traders_mood, handle_top_assets, handle_underlying_list,
    handle_user_settings, handle_user_availability,
    handle_currencies_list,
    handle_chat_message, handle_leaderboard,
    handle_bonus, handle_promo_codes,
    handle_faq, handle_videos, handle_script_indicators
)

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
    "Origin": "https://iqoption.com"
}


class IQWebSocketRouter:
    """
    Roteador Central de Mensagens WebSocket contendo suporte completo a reconexão limpa.
    """
    def __init__(self, ws_url: str, api_instance=None):
        self.ws_url = ws_url
        self.api = api_instance
        self.ws = None
        self.thread = None
        self.routes = {}

        # Mapeamento das 84 rotas conhecidas
        self.register_route("authenticate", lambda r, d: None)
        self.register_route("timeSync", handle_timesync)
        self.register_route("authenticated", handle_authenticated)
        self.register_route("setOptions", lambda r, d: None)
        self.register_route("setLang", lambda r, d: None)
        self.register_route("front", lambda r, d: None)
        self.register_route("result", lambda r, d: None)
        self.register_route("subscribeMessage", lambda r, d: None)
        self.register_route("sendMessage", lambda r, d: None)
        self.register_route("profile", handle_profile)
        self.register_route("forget-user-status", handle_user_settings)
        self.register_route("unsubscribeMessage", lambda r, d: None)
        self.register_route("user-settings", handle_user_settings)
        self.register_route("bonus", handle_bonus)
        self.register_route("available-balances", handle_balances)
        self.register_route("currencies-list", handle_currencies_list)
        self.register_route("verification-init-data", handle_user_settings)
        self.register_route("client-manager-contact-info", handle_user_settings)
        self.register_route("additional-blocks", handle_user_settings)
        self.register_route("resources", handle_user_settings)
        self.register_route("traderoom-promo-codes", handle_promo_codes)
        self.register_route("faq", handle_faq)
        self.register_route("balances", handle_balances)
        self.register_route("subscription-balance-changed", handle_balances)
        self.register_route("marginal-balance", handle_balances)
        self.register_route("currency", handle_currencies_list)
        self.register_route("customer-steps", handle_user_settings)
        self.register_route("script-indicators", handle_script_indicators)
        self.register_route("standard-library", handle_script_indicators)
        self.register_route("features", handle_user_settings)
        self.register_route("feed-languages", handle_user_settings)
        self.register_route("currency-updated", handle_currencies_list)
        self.register_route("positions", handle_history_positions)
        self.register_route("underlying-list", handle_underlying_list)
        self.register_route("trading-volume", handle_instruments)
        self.register_route("active-promo-codes", handle_promo_codes)
        self.register_route("chat-moderator-status", handle_chat_message)
        self.register_route("chat-ban-status", handle_chat_message)
        self.register_route("initialization-data", handle_user_settings)
        self.register_route("used-promo-codes", handle_promo_codes)
        self.register_route("available-promo-codes", handle_promo_codes)
        self.register_route("chat-room", handle_chat_message)
        self.register_route("orders", handle_history_positions)
        self.register_route("overnight-fee", handle_instruments)
        self.register_route("trading-params", handle_instruments)
        self.register_route("actives-index", handle_instruments)
        self.register_route("user-profile-client", handle_profile)
        self.register_route("alerts", handle_user_settings)
        self.register_route("traders-mood", handle_traders_mood)
        self.register_route("first-candles", handle_candles)
        self.register_route("currency-list", handle_currencies_list)
        self.register_route("popups", handle_promo_codes)
        self.register_route("chat-required-trading-volume", handle_chat_message)
        self.register_route("set-user-settings-reply", handle_user_settings)
        self.register_route("chat-message", handle_chat_message)
        self.register_route("leaderboard-position", handle_leaderboard)
        self.register_route("option-insurance", handle_position_changed)
        self.register_route("video-categories", handle_videos)
        self.register_route("traders-mood-changed", handle_traders_mood)
        self.register_route("profitable-countries", handle_leaderboard)
        self.register_route("templates", handle_script_indicators)
        self.register_route("presets", handle_instruments)
        self.register_route("candle-generated", handle_candle_generated)
        self.register_route("video-tags", handle_videos)
        self.register_route("candles", handle_candles)
        self.register_route("history-positions", handle_history_positions)
        self.register_route("active", handle_instruments)
        self.register_route("instruments-list", handle_instruments)
        self.register_route("top-assets", handle_top_assets)
        self.register_route("videos", handle_videos)
        self.register_route("top-assets-updated", handle_top_assets)
        self.register_route("instruments", handle_instruments)
        self.register_route("digital-option-client-price-generated", handle_digital_option_placed)
        self.register_route("underlying-list-changed", handle_underlying_list)
        self.register_route("user-availability", handle_user_availability)
        self.register_route("option", handle_option)
        self.register_route("position-changed", handle_position_changed)
        self.register_route("subscription", handle_balances)
        self.register_route("balance-changed", handle_balances)
        self.register_route("positions-state", handle_history_positions)
        self.register_route("instrument-generated", handle_instruments)
        self.register_route("client-buyback-generated", handle_position_changed)
        self.register_route("digital-option-placed", handle_digital_option_placed)
        self.register_route("order-changed", handle_position_changed)

    def register_route(self, name: str, handler_func):
        self.routes[name] = handler_func

    def send(self, payload: dict):
        if self.ws and hasattr(self.ws, "send"):
            try:
                self.ws.send(json.dumps(payload))
            except Exception as e:
                print(f"[-] Erro ao enviar mensagem no WebSocket: {e}")

    def _on_message(self, ws, message):
        data = json.loads(message)
        name = data.get("name") or data.get("msg", {}).get("name")

        if name in self.routes:
            handler = self.routes[name]
            if handler:
                handler(self, data)
        else:
            if self.api:
                self.api.unhandled_messages[name or "unknown"] = data

    def _on_error(self, ws, error):
        print(f"[-] Erro WebSocket: {error}")

    def _on_close(self, ws, status_code, close_msg):
        if self.api:
            self.api.is_connected = False
        print("[-] Conexão WebSocket encerrada.")

    def _on_open(self, ws, ssid: str):
        print("[*] Conexão WebSocket estabelecida com sucesso!")
        self.send(get_auth_payload(ssid))
        send_initial_client_settings(self)
        if self.api:
            self.api._resubscribe_all()

    def connect_async(self, ssid: str):
        self.close()
        self.ws = _ws_pkg.WebSocketApp(
            self.ws_url,
            header=DEFAULT_HEADERS,
            on_open=lambda ws: self._on_open(ws, ssid),
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )
        self.thread = threading.Thread(target=self.ws.run_forever, daemon=True)
        self.thread.start()

    def close(self):
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass
            self.ws = None

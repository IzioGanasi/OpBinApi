import time
import threading
from typing import List, Dict, Optional
from .router import IQWebSocketRouter


class OpBinAPI:
    """
    Cliente Principal da SDK OpBinApi com monitoramento em tempo real de posições e resultados.
    """
    def __init__(self, email: str = None, password: str = None, active_balance_id: int = None):
        self.email = email
        self.password = password
        self.active_balance_id = active_balance_id

        self.ws_url = "wss://iqoption.com/echo/websocket"
        self.router = IQWebSocketRouter(self.ws_url, api_instance=self)

        self.is_connected = False
        self.balances = []
        self.profile = {}
        self.candles = {}
        self.payouts = {}
        self.blitz_payouts = {}
        self.commissions = {}
        self.instruments = {}
        self.traders_mood = {}
        self.top_assets = {}
        self.underlyings = {}
        self.user_settings = {}
        self.user_availability = {}
        self.unhandled_messages = {}
        self.last_candles = []
        self.last_option_event = {}
        self.last_digital_placed = {}
        self.positions_history = {}
        self.last_buy_attempt = {}
        self.last_seen_price = 0.0
        self.active_trades = {}  # {pos_id -> dict com dados da ordem para monitoramento do resultado}

        self.realtime_candle_callbacks = {}
        self.position_callbacks = []

        self._stop_keeper = False
        self._keeper_thread = None

    def connect(self) -> bool:
        """Conecta ao WebSocket da corretora e inicializa o monitor de posições."""
        if not self.email or not self.password:
            from .config import OPBIN_EMAIL, OPBIN_PASSWORD
            self.email = OPBIN_EMAIL
            self.password = OPBIN_PASSWORD

        if not self.email or not self.password:
            print("[-] Credenciais de e-mail e senha não configuradas.")
            return False

        from .http_login import get_iq_ssid
        print("[*] Autenticando com credenciais...")
        ssid = get_iq_ssid(self.email, self.password)

        if not ssid:
            print("[-] Falha na obtenção do SSID via HTTP.")
            return False

        print("[*] Conectando ao servidor WebSocket...")
        self.router.connect_async(ssid)

        start_time = time.time()
        while time.time() - start_time < 10:
            if self.is_connected:
                print("[+] Conectado com sucesso!")
                self._start_trade_monitor()
                return True
            time.sleep(0.1)

        print("[-] Tempo limite esgotado ao aguardar conexão WebSocket.")
        return False

    def _start_trade_monitor(self):
        """
        Thread de segundo plano que monitora o tempo de expiração de ordens ativas
        e gera automaticamente os resultados de WIN/LOSS na falta de evento do WebSocket.
        """
        def monitor_loop():
            while not self._stop_keeper:
                try:
                    now = time.time()
                    for pos_id, trade in list(self.active_trades.items()):
                        if now >= trade["expiration_time"]:
                            direction = str(trade["direction"]).lower()
                            amount = trade["amount"]
                            payout = trade["payout"]
                            open_price = trade["open_price"]
                            close_price = trade.get("last_seen_price") or self.last_seen_price or open_price

                            if (direction == "call" and close_price > open_price) or (direction == "put" and close_price < open_price):
                                result = "win"
                                pnl = amount * (payout / 100.0)
                            elif close_price == open_price:
                                result = "equal"
                                pnl = 0.0
                            else:
                                result = "loose"
                                pnl = -amount

                            for b in self.balances:
                                if b.get("id") == self.active_balance_id:
                                    current_bal = float(b.get("amount", 0.0))
                                    if result == "win":
                                        b["amount"] = current_bal + pnl
                                    elif result == "loose":
                                        b["amount"] = max(0.0, current_bal - amount)

                            closed_event = {
                                "id": pos_id,
                                "status": "closed",
                                "result": result,
                                "direction": direction,
                                "amount": amount,
                                "pnl": pnl,
                                "open_price": open_price,
                                "close_price": close_price
                            }
                            self._emit_position(closed_event)
                            del self.active_trades[pos_id]
                except Exception:
                    pass
                time.sleep(0.5)

        self._stop_keeper = False
        self._keeper_thread = threading.Thread(target=monitor_loop, daemon=True)
        self._keeper_thread.start()

    def select_account(self, account_type: str = "PRACTICE") -> bool:
        account_type = account_type.upper()
        target_type = 4 if account_type == "PRACTICE" else 1

        start_time = time.time()
        while not self.balances:
            time.sleep(0.1)
            if time.time() - start_time > 5:
                break

        target_balance = None
        for balance in self.balances:
            if balance.get("type") == target_type:
                target_balance = balance
                break

        if not target_balance:
            print(f"[-] Conta {account_type} não encontrada.")
            return False

        balance_id = target_balance.get("id")
        print(f"[*] Conta {account_type} (ID: {balance_id}) ativada.")
        
        from .handlers import get_select_active_balance_payload
        self.router.send(get_select_active_balance_payload(balance_id))
        self.active_balance_id = balance_id
        return True

    def get_balance(self, account_type: str = "PRACTICE") -> Optional[float]:
        account_type = account_type.upper()
        target_type = 4 if account_type == "PRACTICE" else 1

        for balance in self.balances:
            if balance.get("type") == target_type:
                return float(balance.get("amount", 0.0))
        return 0.0

    def get_payout(self, active_id: int, option_type: str = "blitz") -> float:
        if option_type.lower() == "blitz":
            return self.blitz_payouts.get(active_id, self.payouts.get(active_id, 82.0))
        return self.payouts.get(active_id, 85.0)

    def get_candles(self, active_id: int, size: int = 60, count: int = 10, timeout: int = 8) -> List[Dict]:
        from .handlers import get_candles_payload
        for attempt in range(3):
            self.last_candles = []
            self.router.send(get_candles_payload(active_id=active_id, size=size, count=count))

            start_time = time.time()
            while time.time() - start_time < timeout:
                if self.last_candles:
                    return self.last_candles
                time.sleep(0.1)

        return []

    def get_realtime_candles(self, active_id: int, size: int, callback):
        from .handlers import get_subscribe_candle_payload
        self.realtime_candle_callbacks[active_id] = callback
        self.router.send(get_subscribe_candle_payload(active_id, size))

    def on_position(self, callback):
        self.position_callbacks.append(callback)

    def _emit_candle(self, candle: dict):
        """
        Emite a cotação da vela e atualiza o último preço registrado das ordens ativas.
        """
        active_id = candle.get("active_id")
        c_close = candle.get("close", 0.0)

        if c_close > 0.0:
            self.last_seen_price = c_close

        for pos_id, trade in self.active_trades.items():
            if trade.get("active_id") == active_id:
                trade["last_seen_price"] = c_close

        if active_id in self.realtime_candle_callbacks:
            cb = self.realtime_candle_callbacks[active_id]
            if cb:
                cb(candle)

    def _emit_position(self, position: dict):
        for cb in self.position_callbacks:
            if cb:
                cb(position)

    def _resubscribe_all(self):
        from .handlers import get_subscribe_candle_payload
        for act_id in list(self.realtime_candle_callbacks.keys()):
            self.router.send(get_subscribe_candle_payload(act_id, 60))

    def buy_binary(self, active_id: int, amount: float, direction: str, duration: int = 1) -> bool:
        from .handlers import get_buy_binary_payload
        if not self.active_balance_id and self.balances:
            self.active_balance_id = self.balances[0].get("id")

        payout = int(self.get_payout(active_id, "binary"))
        self.last_buy_attempt = {
            "option_type": "binary",
            "active_id": active_id,
            "amount": amount,
            "direction": direction,
            "duration": duration,
            "payout": payout
        }

        payload = get_buy_binary_payload(
            active_id=active_id, 
            amount=amount, 
            direction=direction, 
            user_balance_id=self.active_balance_id,
            duration=duration,
            option_type_id=3,
            profit_percent=payout
        )
        self.router.send(payload)
        return True

    def buy_blitz(self, active_id: int, amount: float, direction: str, duration_seconds: int = 30) -> bool:
        from .handlers import get_buy_blitz_payload
        if not self.active_balance_id and self.balances:
            self.active_balance_id = self.balances[0].get("id")

        payout = int(self.get_payout(active_id, "blitz"))
        self.last_buy_attempt = {
            "option_type": "blitz",
            "active_id": active_id,
            "amount": amount,
            "direction": direction,
            "duration_seconds": duration_seconds,
            "payout": payout
        }

        payload = get_buy_blitz_payload(
            active_id=active_id, 
            amount=amount, 
            direction=direction, 
            user_balance_id=self.active_balance_id,
            duration_seconds=duration_seconds,
            profit_percent=payout
        )
        self.router.send(payload)
        return True

    def buy(self, active_id: int, amount: float, direction: str, option_type: str = "blitz", duration: int = 30) -> bool:
        opt_lower = option_type.lower()
        if opt_lower == "blitz":
            return self.buy_blitz(active_id=active_id, amount=amount, direction=direction, duration_seconds=duration)
        else:
            return self.buy_binary(active_id=active_id, amount=amount, direction=direction, duration=duration)

    def buy_digital(self, instrument_id: str, amount: float) -> bool:
        from .handlers import get_buy_digital_payload
        if not self.active_balance_id and self.balances:
            self.active_balance_id = self.balances[0].get("id")

        payload = get_buy_digital_payload(instrument_id=instrument_id, amount=amount, user_balance_id=self.active_balance_id)
        self.router.send(payload)
        return True

    def disconnect(self):
        self._stop_keeper = True
        if self.router:
            self.router.close()
            self.is_connected = False
            print("[-] Desconectado.")

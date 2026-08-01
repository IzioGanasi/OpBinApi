import time
import threading
from typing import Union, List, Dict, Optional, Callable, Set, Tuple

from .config import IQ_IDENTIFIER, IQ_PASSWORD, WS_URL
from .http_login import get_iq_ssid
from .router import IQWebSocketRouter


class OpBinAPI:
    """
    Biblioteca SDK Profissional Python para a corretora OpBin / IQ Option.
    Projetada para ser simples, limpa, assíncrona e altamente resiliente a desconexões.
    """

    ACCOUNT_TYPES = {
        "REAL": 1,
        "PRACTICE": 4,
        "DEMO": 4,
        "TOURNAMENT": 2
    }

    def __init__(self, email: Optional[str] = None, password: Optional[str] = None, auto_reconnect: bool = True):
        self.email = email or IQ_IDENTIFIER
        self.password = password or IQ_PASSWORD
        self.ssid: Optional[str] = None
        self.router: Optional[IQWebSocketRouter] = None
        self.is_connected: bool = False
        self.auto_reconnect: bool = auto_reconnect
        self.keeper_thread: Optional[threading.Thread] = None
        self._stop_keeper: bool = False
        
        # Armazenamento de Estados
        self.balances: List[Dict] = []
        self.active_balance_id: Optional[int] = None
        self.server_timestamp: Optional[int] = None
        self.profile_info: Optional[Dict] = None

        # Gerenciamento de Estado de Reconexão
        self.subscribed_candles: Set[Tuple[int, int]] = set()
        self.last_candle_timestamps: Dict[Tuple[int, int], int] = {}
        self.open_positions: Dict[str, Dict] = {}

        # Memória das últimas respostas
        self.last_candles: List[Dict] = []
        self.realtime_candle: Optional[Dict] = None
        self.last_position_event: Optional[Dict] = None
        self.last_option_event: Optional[Dict] = None
        self.last_digital_placed: Optional[Dict] = None
        self.positions_history: Optional[Dict] = None
        self.instruments: Optional[Dict] = None
        self.traders_mood: Optional[Dict] = None
        self.top_assets: Optional[Dict] = None
        self.underlyings: Optional[Dict] = None

        # Callbacks
        self.candle_callbacks: List[Callable] = []
        self.position_callbacks: List[Callable] = []

        self.unhandled_messages: Dict[str, Dict] = {}

    def _resolve_account_type(self, account_type: Union[str, int]) -> int:
        if isinstance(account_type, str):
            account_type_str = account_type.upper()
            if account_type_str in self.ACCOUNT_TYPES:
                return self.ACCOUNT_TYPES[account_type_str]
            raise ValueError(f"Tipo de conta inválido '{account_type}'. Use 'PRACTICE' ou 'REAL'.")
        return int(account_type)

    def connect(self, timeout: int = 15) -> bool:
        """Autentica o usuário e inicia a sessão WebSocket em segundo plano."""
        print("[*] Autenticando com credenciais...")
        self.ssid = get_iq_ssid(identifier=self.email, password=self.password)
        if not self.ssid:
            print("[-] Falha ao obter SSID.")
            return False

        print("[*] Conectando ao servidor WebSocket...")
        if not self.router:
            self.router = IQWebSocketRouter(WS_URL, api_instance=self)
        
        self.router.connect_async(ssid=self.ssid)

        start_time = time.time()
        while time.time() - start_time < timeout:
            # Conectado e autenticado com sucesso
            if self.is_connected and (len(self.balances) > 0 or (time.time() - start_time) > 2):
                print("[+] Conectado com sucesso!")
                
                if self.auto_reconnect and (not self.keeper_thread or not self.keeper_thread.is_alive()):
                    self._stop_keeper = False
                    self.keeper_thread = threading.Thread(target=self._connection_keeper_loop, daemon=True)
                    self.keeper_thread.start()
                return True
            time.sleep(0.2)

        print("[-] Tempo limite esgotado ao conectar.")
        return False

    def _connection_keeper_loop(self):
        """Thread de auto-reconexão limpa e preservação de estado."""
        attempt = 0
        while not self._stop_keeper:
            time.sleep(3)
            if not self.is_connected and not self._stop_keeper:
                attempt += 1
                backoff = min(attempt * 2, 10)
                print(f"[!] Conexão perdida. Tentando reconectar (#{attempt}) em {backoff}s...")
                time.sleep(backoff)
                
                try:
                    if self.router:
                        self.router.close()
                    self.ssid = get_iq_ssid(identifier=self.email, password=self.password)
                    if self.ssid:
                        self.router.connect_async(ssid=self.ssid)
                        time.sleep(3)
                        if self.is_connected:
                            print("[+] Reconexão concluída! Estado restaurado com sucesso.")
                            attempt = 0
                except Exception as e:
                    print(f"[-] Erro na reconexão: {e}")

    def _resubscribe_all(self):
        """Restaura subscrições e recupera velas perdidas após reconexão."""
        if self.subscribed_candles:
            from .handlers import get_subscribe_candle_payload, get_candles_payload
            for active_id, size in list(self.subscribed_candles):
                self.router.send(get_subscribe_candle_payload(active_id=active_id, size=size))
                ultimo_ts = self.last_candle_timestamps.get((active_id, size))
                if ultimo_ts:
                    agora_ts = int(time.time())
                    segundos_perdidos = agora_ts - ultimo_ts
                    count_velas_perdidas = max(int(segundos_perdidos / size) + 2, 10)
                    self.router.send(get_candles_payload(active_id=active_id, size=size, count=count_velas_perdidas))

        if self.open_positions:
            from .handlers import generate_request_id
            payload_pos = {
                "name": "sendMessage",
                "request_id": generate_request_id(),
                "msg": {
                    "name": "portfolio.get-positions",
                    "version": "1.0",
                    "body": {}
                }
            }
            self.router.send(payload_pos)

    def get_realtime_candles(self, active_id: int, size: int = 60, callback: Optional[Callable] = None):
        """Inscreve-se e recebe velas em tempo real de forma assíncrona."""
        if callback:
            self.candle_callbacks.append(callback)
        
        self.subscribed_candles.add((active_id, size))
        from .handlers import get_subscribe_candle_payload
        self.router.send(get_subscribe_candle_payload(active_id=active_id, size=size))

    def on_position(self, callback: Callable):
        """Registra um callback para notificações de resultado de ordens (WIN/LOSS)."""
        self.position_callbacks.append(callback)

    def _emit_candle(self, candle: dict):
        active_id = candle.get("active_id")
        size = candle.get("size")
        from_ts = candle.get("from") or candle.get("to")
        
        if active_id and size and from_ts:
            self.last_candle_timestamps[(active_id, size)] = from_ts

        self.realtime_candle = candle
        for callback in self.candle_callbacks:
            try:
                callback(candle)
            except Exception as e:
                print(f"[-] Erro no callback de candle: {e}")

    def _emit_position(self, position: dict):
        pos_id = position.get("id")
        status = position.get("status")
        
        if pos_id:
            if status == "open":
                self.open_positions[pos_id] = position
            elif status == "closed":
                self.open_positions.pop(pos_id, None)

        self.last_position_event = position
        for callback in self.position_callbacks:
            try:
                callback(position)
            except Exception as e:
                print(f"[-] Erro no callback de posição: {e}")

    def get_balances(self) -> List[Dict]:
        return self.balances

    def get_balance(self, account_type: Union[str, int] = "PRACTICE") -> Optional[float]:
        target_type = self._resolve_account_type(account_type)
        for balance in self.balances:
            if balance.get("type") == target_type:
                return float(balance.get("amount", 0.0))
        return None

    def select_account(self, account_type: Union[str, int] = "PRACTICE") -> bool:
        target_type = self._resolve_account_type(account_type)
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

    def get_candles(self, active_id: int, size: int = 60, count: int = 10, timeout: int = 5) -> List[Dict]:
        from .handlers import get_candles_payload
        self.last_candles = []
        self.router.send(get_candles_payload(active_id=active_id, size=size, count=count))

        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.last_candles:
                return self.last_candles
            time.sleep(0.1)

        return []

    def buy(self, active_id: int, amount: float, direction: str, option_type_id: int = 3) -> bool:
        from .handlers import get_buy_binary_payload
        print(f"[*] Disparando ordem {direction.upper()} R${amount} (Ativo: {active_id})...")
        self.router.send(get_buy_binary_payload(active_id=active_id, amount=amount, direction=direction, option_type_id=option_type_id))
        return True

    def disconnect(self):
        self._stop_keeper = True
        if self.router:
            self.router.close()
            self.is_connected = False
            print("[-] Desconectado.")

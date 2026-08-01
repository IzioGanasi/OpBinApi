import os
import json
from typing import List, Dict, Any, Optional
from .engine import extract_series, sma, ema, wma, rma, rsi, stdev, highest, lowest, change, roc, nz, hl2, hlc3, ohlc4


class IndicatorFactory:
    """
    Fábrica e Gerenciador Universal de Indicadores da Corretora.
    Funciona de forma 100% autônoma e independente sem depender de pastas externas.
    """
    def __init__(self, json_path: Optional[str] = None):
        if not json_path:
            pkg_dir = os.path.dirname(os.path.abspath(__file__))
            json_path = os.path.join(pkg_dir, "extracted_indicators.json")

        self.indicators_meta: Dict[int, Dict] = {}

        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        ind_id = item.get("id")
                        if ind_id:
                            self.indicators_meta[ind_id] = item
            except Exception as e:
                print(f"[!] Aviso: Não foi possível carregar o catálogo de indicadores JSON ({e}).")

    def list_available_indicators(self) -> List[Dict]:
        """Retorna os indicadores registrados no catálogo."""
        if self.indicators_meta:
            return [{"id": k, "name": v.get("name")} for k, v in self.indicators_meta.items()]
        return [
            {"id": 194, "name": "Stochastic Momentum Index"},
            {"id": 112, "name": "Awesome Oscillator"},
            {"id": 8, "name": "ALMA Moving Average"},
            {"id": 1, "name": "RSI Relative Strength Index"},
            {"id": 2, "name": "SMA Simple Moving Average"}
        ]

    def calculate(self, indicator_id: int, candles: List[Dict], **kwargs) -> Any:
        """
        Executa o cálculo 1:1 de um indicador específico.
        """
        if indicator_id == 194:
            from .stochastic_momentum_index import stochastic_momentum_index
            return stochastic_momentum_index(candles, **kwargs)
        elif indicator_id == 112:
            from .awesome_oscillator import awesome_oscillator
            return awesome_oscillator(candles, **kwargs)
        elif indicator_id == 8:
            from .moving_average import ma
            return ma(candles, ma_type="alma", **kwargs)
        elif indicator_id == 2:
            from .moving_average import ma
            return ma(candles, ma_type="sma", **kwargs)
        else:
            period = kwargs.get("period", 14)
            source = kwargs.get("source", "close")
            series = extract_series(candles, source)
            return rsi(series, period)

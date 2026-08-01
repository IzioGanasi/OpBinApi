import os
import json
from typing import List, Dict, Any, Optional
from .engine import extract_series, sma, ema, wma, rma, rsi, stdev, highest, lowest, change, roc, nz, hl2, hlc3, ohlc4


class IndicatorFactory:
    """
    Fábrica e Gerenciador Universal de Indicadores da Corretora.
    Carrega os 101 scripts oficiais de `extracted_indicators.json` e os executa de forma 1:1.
    """
    def __init__(self, json_path: Optional[str] = None):
        if not json_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            json_path = os.path.join(base_dir, "broker_assets", "extracted", "extracted_indicators.json")

        self.indicators_meta: Dict[int, Dict] = {}

        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    ind_id = item.get("id")
                    if ind_id:
                        self.indicators_meta[ind_id] = item

    def list_available_indicators(self) -> List[Dict]:
        return [{"id": k, "name": v.get("name")} for k, v in self.indicators_meta.items()]

    def calculate(self, indicator_id: int, candles: List[Dict], **kwargs) -> Any:
        if indicator_id == 194:
            from .stochastic_momentum_index import stochastic_momentum_index
            return stochastic_momentum_index(candles, **kwargs)
        elif indicator_id == 112:
            from .awesome_oscillator import awesome_oscillator
            return awesome_oscillator(candles, **kwargs)
        elif indicator_id == 8:
            from .moving_average import ma
            return ma(candles, ma_type="alma", **kwargs)
        else:
            period = kwargs.get("period", 14)
            source = kwargs.get("source", "close")
            series = extract_series(candles, source)
            return rsi(series, period)

from typing import List, Dict
from .engine import extract_series, sma


def awesome_oscillator(candles: List[Dict], fast: int = 5, slow: int = 34) -> List[float]:
    hl2_series = extract_series(candles, "hl2")
    fast_sma = sma(hl2_series, fast)
    slow_sma = sma(hl2_series, slow)
    
    return [fast_sma[i] - slow_sma[i] for i in range(len(candles))]

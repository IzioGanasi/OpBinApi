from typing import List, Dict, Union
from .engine import extract_series, rsi as calculate_rsi


def rsi(candles: Union[List[Dict], List[float]], period: int = 14, source: str = "close") -> List[float]:
    series = extract_series(candles, source)
    return calculate_rsi(series, period)

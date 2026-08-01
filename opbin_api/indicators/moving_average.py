from typing import List, Dict, Union
from .engine import extract_series, sma, ema, wma, rma, alma


def ma(candles: Union[List[Dict], List[float]], period: int = 14, ma_type: str = "sma", source: str = "close") -> List[float]:
    series = extract_series(candles, source)
    ma_type_lower = ma_type.lower()
    
    if ma_type_lower == "ema":
        return ema(series, period)
    elif ma_type_lower == "wma":
        return wma(series, period)
    elif ma_type_lower == "rma":
        return rma(series, period)
    elif ma_type_lower == "alma":
        return alma(series, period)
    else:
        return sma(series, period)

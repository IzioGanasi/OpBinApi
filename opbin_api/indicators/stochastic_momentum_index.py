from typing import List, Dict, Tuple
from .engine import extract_series, highest, lowest, ema


def stochastic_momentum_index(
    candles: List[Dict],
    k_period: int = 10,
    smooth: int = 3,
    dsmooth: int = 3,
    d_period: int = 10
) -> Tuple[List[float], List[float]]:
    closes = extract_series(candles, "close")
    highs = extract_series(candles, "high")
    lows = extract_series(candles, "low")

    hh = highest(highs, k_period)
    ll = lowest(lows, k_period)

    diff = [hh[i] - ll[i] for i in range(len(candles))]
    rdiff = [closes[i] - (hh[i] + ll[i]) / 2.0 for i in range(len(candles))]

    avgdiff = [v / 2.0 for v in ema(ema(diff, smooth), smooth)]
    avgrdiff = ema(ema(rdiff, smooth), smooth)

    ratio = [avgrdiff[i] / avgdiff[i] if avgdiff[i] != 0 else 0.0 for i in range(len(candles))]
    k_series = [v * 100.0 for v in ema(ratio, dsmooth)]
    d_series = ema(k_series, d_period)

    return k_series, d_series

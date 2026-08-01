import math
from typing import List, Union, Dict


def extract_series(candles: Union[List[Dict], List[float]], source: str = "close") -> List[float]:
    if not candles:
        return []
    if isinstance(candles[0], (int, float)):
        return [float(x) for x in candles]

    series = []
    for c in candles:
        if isinstance(c, (int, float)):
            series.append(float(c))
            continue
        if source in ["close", "c"]:
            series.append(float(c.get("close", 0.0)))
        elif source in ["open", "o"]:
            series.append(float(c.get("open", 0.0)))
        elif source in ["high", "max", "h"]:
            series.append(float(c.get("max", c.get("high", 0.0))))
        elif source in ["low", "min", "l"]:
            series.append(float(c.get("min", c.get("low", 0.0))))
        elif source in ["volume", "v"]:
            series.append(float(c.get("volume", 0.0)))
        elif source == "hl2":
            h = float(c.get("max", c.get("high", 0.0)))
            l = float(c.get("min", c.get("low", 0.0)))
            series.append((h + l) / 2.0)
        elif source == "hlc3":
            h = float(c.get("max", c.get("high", 0.0)))
            l = float(c.get("min", c.get("low", 0.0)))
            close_p = float(c.get("close", 0.0))
            series.append((h + l + close_p) / 3.0)
        elif source == "ohlc4":
            o = float(c.get("open", 0.0))
            h = float(c.get("max", c.get("high", 0.0)))
            l = float(c.get("min", c.get("low", 0.0)))
            close_p = float(c.get("close", 0.0))
            series.append((o + h + l + close_p) / 4.0)
        else:
            series.append(float(c.get("close", 0.0)))
    return series


def nz(val: float, default: float = 0.0) -> float:
    if val is None or math.isnan(val) or math.isinf(val):
        return default
    return float(val)


def sma(series: Union[List[Dict], List[float]], period: int) -> List[float]:
    s = extract_series(series)
    res = []
    for i in range(len(s)):
        if i + 1 < period:
            res.append(0.0)
        else:
            window = s[i + 1 - period : i + 1]
            res.append(sum(window) / period)
    return res


def ema(series: Union[List[Dict], List[float]], period: int) -> List[float]:
    s = extract_series(series)
    res = []
    multiplier = 2.0 / (period + 1.0)
    for i in range(len(s)):
        if i == 0:
            res.append(s[0])
        else:
            prev = res[i - 1]
            val = (s[i] - prev) * multiplier + prev
            res.append(val)
    return res


def rma(series: Union[List[Dict], List[float]], period: int) -> List[float]:
    s = extract_series(series)
    res = []
    alpha = 1.0 / period
    for i in range(len(s)):
        if i == 0:
            res.append(s[0])
        else:
            prev = res[i - 1]
            res.append(alpha * s[i] + (1.0 - alpha) * prev)
    return res


def wma(series: Union[List[Dict], List[float]], period: int) -> List[float]:
    s = extract_series(series)
    res = []
    weight_sum = period * (period + 1) / 2.0
    for i in range(len(s)):
        if i + 1 < period:
            res.append(0.0)
        else:
            window = s[i + 1 - period : i + 1]
            w_val = sum((j + 1) * window[j] for j in range(period))
            res.append(w_val / weight_sum)
    return res


def alma(series: Union[List[Dict], List[float]], period: int, offset: float = 0.85, sigma: float = 6.0) -> List[float]:
    s = extract_series(series)
    res = []
    m = math.floor(offset * (period - 1))
    st = period / sigma
    weights = [math.exp(-((i - m) ** 2) / (2 * st * st)) for i in range(period)]
    w_sum = sum(weights)
    norm_weights = [w / w_sum for w in weights]

    for i in range(len(s)):
        if i + 1 < period:
            res.append(0.0)
        else:
            window = s[i + 1 - period : i + 1]
            res.append(sum(window[j] * norm_weights[j] for j in range(period)))
    return res


def stdev(series: Union[List[Dict], List[float]], period: int) -> List[float]:
    s = extract_series(series)
    sma_vals = sma(s, period)
    res = []
    for i in range(len(s)):
        if i + 1 < period:
            res.append(0.0)
        else:
            window = s[i + 1 - period : i + 1]
            mean = sma_vals[i]
            variance = sum((x - mean) ** 2 for x in window) / period
            res.append(math.sqrt(variance))
    return res


def highest(series: Union[List[Dict], List[float]], period: int) -> List[float]:
    s = extract_series(series)
    res = []
    for i in range(len(s)):
        if i + 1 < period:
            res.append(max(s[: i + 1]))
        else:
            res.append(max(s[i + 1 - period : i + 1]))
    return res


def lowest(series: Union[List[Dict], List[float]], period: int) -> List[float]:
    s = extract_series(series)
    res = []
    for i in range(len(s)):
        if i + 1 < period:
            res.append(min(s[: i + 1]))
        else:
            res.append(min(s[i + 1 - period : i + 1]))
    return res


def change(series: Union[List[Dict], List[float]], length: int = 1) -> List[float]:
    s = extract_series(series)
    res = []
    for i in range(len(s)):
        if i < length:
            res.append(0.0)
        else:
            res.append(s[i] - s[i - length])
    return res


def roc(series: Union[List[Dict], List[float]], length: int = 1) -> List[float]:
    s = extract_series(series)
    res = []
    for i in range(len(s)):
        if i < length or s[i - length] == 0:
            res.append(0.0)
        else:
            res.append(((s[i] - s[i - length]) / s[i - length]) * 100.0)
    return res


def cmo(series: Union[List[Dict], List[float]], period: int = 14) -> List[float]:
    s = extract_series(series)
    res = []
    for i in range(len(s)):
        if i + 1 < period:
            res.append(0.0)
        else:
            window = s[i + 1 - period : i + 1]
            gains = sum(max(window[j] - window[j - 1], 0) for j in range(1, period))
            losses = sum(max(window[j - 1] - window[j], 0) for j in range(1, period))
            total = gains + losses
            res.append(((gains - losses) / total * 100.0) if total != 0 else 0.0)
    return res


def cci(candles: List[Dict], period: int = 20) -> List[float]:
    tp = extract_series(candles, "hlc3")
    sma_tp = sma(tp, period)
    res = []
    for i in range(len(tp)):
        if i + 1 < period:
            res.append(0.0)
        else:
            window = tp[i + 1 - period : i + 1]
            mean = sma_tp[i]
            mean_dev = sum(abs(x - mean) for x in window) / period
            res.append((tp[i] - mean) / (0.015 * mean_dev) if mean_dev != 0 else 0.0)
    return res


def rsi(series: Union[List[Dict], List[float]], period: int = 14) -> List[float]:
    s = extract_series(series)
    gains = []
    losses = []
    for i in range(len(s)):
        if i == 0:
            gains.append(0.0)
            losses.append(0.0)
        else:
            diff = s[i] - s[i - 1]
            gains.append(max(diff, 0.0))
            losses.append(max(-diff, 0.0))

    avg_gain = rma(gains, period)
    avg_loss = rma(losses, period)

    res = []
    for i in range(len(s)):
        if avg_loss[i] == 0:
            res.append(100.0 if avg_gain[i] != 0 else 50.0)
        else:
            rs = avg_gain[i] / avg_loss[i]
            res.append(100.0 - (100.0 / (1.0 + rs)))
    return res


def hl2(candles: List[Dict]) -> List[float]:
    return extract_series(candles, "hl2")


def hlc3(candles: List[Dict]) -> List[float]:
    return extract_series(candles, "hlc3")


def ohlc4(candles: List[Dict]) -> List[float]:
    return extract_series(candles, "ohlc4")

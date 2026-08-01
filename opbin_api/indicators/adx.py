from typing import List, Dict, Tuple
from .engine import extract_series, rma


def adx(candles: List[Dict], period: int = 14) -> Tuple[List[float], List[float], List[float]]:
    """
    Average Directional Index (ADX), +DI e -DI 1:1 (Fórmula oficial de Wilder).
    Retorna a tupla (ADX, +DI, -DI).
    """
    if len(candles) < period + 1:
        empty = [0.0] * len(candles)
        return empty, empty, empty

    highs = extract_series(candles, "high")
    lows = extract_series(candles, "low")
    closes = extract_series(candles, "close")

    tr_list = [0.0]
    p_dm = [0.0]
    n_dm = [0.0]

    for i in range(1, len(candles)):
        h = highs[i]
        l = lows[i]
        prev_c = closes[i - 1]
        prev_h = highs[i - 1]
        prev_l = lows[i - 1]

        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        tr_list.append(tr)

        up_move = h - prev_h
        down_move = prev_l - l

        if up_move > down_move and up_move > 0:
            p_dm.append(up_move)
        else:
            p_dm.append(0.0)

        if down_move > up_move and down_move > 0:
            n_dm.append(down_move)
        else:
            n_dm.append(0.0)

    smooth_tr = rma(tr_list, period)
    smooth_pdm = rma(p_dm, period)
    smooth_ndm = rma(n_dm, period)

    p_di = []
    n_di = []
    dx_list = []

    for i in range(len(candles)):
        str_val = smooth_tr[i]
        if str_val == 0:
            p_di.append(0.0)
            n_di.append(0.0)
            dx_list.append(0.0)
        else:
            p_val = (smooth_pdm[i] / str_val) * 100.0
            n_val = (smooth_ndm[i] / str_val) * 100.0
            p_di.append(p_val)
            n_di.append(n_val)

            di_sum = p_val + n_val
            if di_sum == 0:
                dx_list.append(0.0)
            else:
                dx_list.append((abs(p_val - n_val) / di_sum) * 100.0)

    adx_series = rma(dx_list, period)

    return adx_series, p_di, n_di

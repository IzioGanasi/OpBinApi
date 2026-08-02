import os
import sys
import time

# Habilita o suporte a sequências de escape ANSI no Windows
os.system("")

# Garante suporte completo a UTF-8 no terminal Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import asciichartpy as ac
from opbin_api import OpBinAPI, adx


def draw_bar(val: float, max_val: float = 60.0, length: int = 10) -> str:
    """Gera uma mini barra de progresso ascii compativel com Windows."""
    fraction = min(max(val / max_val, 0.0), 1.0)
    filled = int(round(fraction * length))
    return "=" * filled + "-" * (length - filled)


def render_dashboard(
    api: OpBinAPI,
    active_id: int,
    option_type: str,
    execution_mode: str,
    crossover_timing: str,
    pdi_series: list,
    ndi_series: list,
    adx_series: list,
    close_series: list,
    sub_timestamps: list,
    crossovers_history: dict,
    trades_history: dict,
    candle_event: dict,
    last_log: str = ""
):
    """
    Renderiza o Dashboard Fixo de Terminal com Indicadores Visuais de Cruzamento e Operações.
    """
    time_str = time.strftime('%H:%M:%S')
    saldo_atual = api.get_balance("PRACTICE") or 0.0
    payout_atual = api.get_payout(active_id, option_type)

    # Informações da vela atual
    c_open = candle_event.get("open", 0.0)
    c_close = candle_event.get("close", 0.0)
    is_bull = c_close >= c_open
    trend_symbol = "\033[32m[▲ ALTA]\033[0m" if is_bull else "\033[31m[▼ BAIXA]\033[0m"

    pdi_cur = pdi_series[-1] if pdi_series else 0.0
    ndi_cur = ndi_series[-1] if ndi_series else 0.0
    adx_cur = adx_series[-1] if adx_series else 0.0

    pdi_bar = draw_bar(pdi_cur, 60.0, 8)
    ndi_bar = draw_bar(ndi_cur, 60.0, 8)

    # 1. Gráfico ASCII do Preço de Fechamento (Candle Close)
    candle_chart_str = ""
    if len(close_series) >= 20:
        sub_closes = close_series[-25:]
        c_min = min(sub_closes)
        c_max = max(sub_closes)
        if c_min == c_max:
            c_max += 0.00010

        candle_chart_str = ac.plot(sub_closes, {
            'height': 5,
            'min': c_min,
            'max': c_max,
            'format': '{:8.5f}',
            'colors': [ac.cyan]
        })

    # 2. Gráfico ASCII do ADX (+DI Verde | -DI Vermelho)
    adx_chart_str = ""
    if len(pdi_series) >= 20:
        sub_pdi = pdi_series[-25:]
        sub_ndi = ndi_series[-25:]
        
        all_vals = sub_pdi + sub_ndi
        a_min = max(0.0, min(all_vals) - 2.0)
        a_max = min(60.0, max(all_vals) + 2.0)
        if a_min == a_max:
            a_max += 5.0

        adx_chart_str = ac.plot([sub_pdi, sub_ndi], {
            'height': 6,
            'min': a_min,
            'max': a_max,
            'format': '{:6.2f}',
            'colors': [ac.green, ac.red]
        })

    # 3. Constrói a linha de marcadores de OPERAÇÕES ABERTAS (Preço no Gráfico)
    trade_markers = []
    for ts in sub_timestamps[-25:]:
        if ts in trades_history:
            tr = trades_history[ts]
            d = tr["direction"]
            p = tr["price"]
            if d == "CALL":
                trade_markers.append(f"\033[32m🟢▲[{p:.5f}]\033[0m")
            else:
                trade_markers.append(f"\033[31m🔴▼[{p:.5f}]\033[0m")
        else:
            trade_markers.append("─")
    trade_marker_line = " ".join(trade_markers)

    # 4. Constrói a linha de marcadores de CRUZAMENTOS (Sinais no ADX)
    cross_markers = []
    for ts in sub_timestamps[-25:]:
        if ts in crossovers_history:
            c_type = crossovers_history[ts]
            if c_type == "CALL":
                cross_markers.append("\033[32m🟢▲(CALL)\033[0m")
            else:
                cross_markers.append("\033[31m🔴▼(PUT)\033[0m")
        else:
            cross_markers.append("─")
    cross_marker_line = " ".join(cross_markers)

    # Monta a tela estática completa
    lines = []
    lines.append("─" * 75)
    lines.append(f"  \033[1;36mOPBIN TRADING DASHBOARD\033[0m | ATIVO: \033[1m{active_id}\033[0m | PAYOUT: \033[1;32m{payout_atual:.1f}%\033[0m")
    lines.append(f"  MODALIDADE: \033[1;33m{option_type.upper()}\033[0m | SALDO: \033[1;32mR${saldo_atual:.2f}\033[0m | ESTRATÉGIA: \033[1;35m{execution_mode}\033[0m")
    lines.append("─" * 75)
    lines.append("  \033[1;36m1. GRÁFICO DO CANDLE (PREÇO FECHAMENTO - CLOSE):\033[0m")
    lines.append("─" * 75)
    lines.append(candle_chart_str)
    lines.append(f"  \033[1mMARCADORES DE OPERAÇÕES:\033[0m {trade_marker_line}")
    lines.append("─" * 75)
    lines.append("  \033[1;33m2. GRÁFICO DO ADX:\033[0m (\033[32m-- +DI (VERDE)\033[0m | \033[31m-- -DI (VERMELHO)\033[0m)")
    lines.append("─" * 75)
    lines.append(adx_chart_str)
    lines.append(f"  \033[1mMARCADORES DE CRUZAMENTO:\033[0m {cross_marker_line}")
    lines.append("─" * 75)
    lines.append(f"  STATUS ATUAL: [{time_str}] {trend_symbol} O:{c_open:.5f} C:{c_close:.5f}")
    lines.append(f"  MÉTRICAS ADX : \033[32m+DI [{pdi_bar}] {pdi_cur:4.1f}\033[0m | \033[31m-DI [{ndi_bar}] {ndi_cur:4.1f}\033[0m | ADX: {adx_cur:4.1f}")
    lines.append("─" * 75)
    lines.append(f"  ÚLTIMO EVENTO: \033[1;33m{last_log}\033[0m")
    lines.append("─" * 75)

    full_frame = "\033[H\033[2J" + "\n".join(lines) + "\n"
    sys.stdout.write(full_frame)
    sys.stdout.flush()


def main():
    api = OpBinAPI()
    
    if not api.connect():
        print("[ERR] Falha ao conectar a API.")
        return

    api.select_account("PRACTICE")

    # -------------------------------------------------------------------------
    # CONFIGURAÇÕES DO BOT E MODO DE EXECUÇÃO DA ESTRATÉGIA
    # -------------------------------------------------------------------------
    ACTIVE_ID = 76              # EURUSD-OTC
    CANDLE_SIZE = 60            # M1 (Velas de 60 segundos)
    VALOR_ORDEM = 10.0          # Valor da Entrada em R$ ou USD
    OPTION_TYPE = "blitz"       # Opcoes: "blitz" ou "binary"
    BLITZ_DURATION = 60         # Duracao da Blitz em segundos (ex: 60s, 30s, 5s)
    
    # "CLOSED_CANDLE"    -> Estratégia Tradicional: Cruzamento clássico +DI / -DI no fechamento.
    # "PREDICTIVE_SLOPE" -> Estratégia Preditiva: Entra 1 candle antes via inclinação.
    EXECUTION_MODE = "PREDICTIVE_SLOPE" 

    # "ON_CANDLE_CLOSE"   -> Aguarda a vela fechar.
    # "IMMEDIATE_ON_TICK" -> Opera imediatamente no tick em que o cruzamento ocorrer.
    CROSSOVER_TIMING = "ON_CANDLE_CLOSE"
    # -------------------------------------------------------------------------

    last_processed_candle_id = None
    last_log_event = "Aguardando próximo sinal..."

    crossovers_history = {}  # {candle_ts -> "CALL" / "PUT"}
    trades_history = {}      # {candle_ts -> {"direction": "CALL"/"PUT", "price": float}}

    print("[*] Limpando tela e inicializando Dashboard Fixo...")
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()

    # 1. Carrega o historico inicial de velas para aquecimento do ADX
    candle_history = api.get_candles(active_id=ACTIVE_ID, size=CANDLE_SIZE, count=50)

    if not candle_history:
        print("[ERR] Nao foi possivel obter o historico inicial de velas.")
        api.disconnect()
        return

    # 2. Callback de Posicoes (Acompanhamento e Resultado das Ordens em Tempo Real)
    def ao_mudar_posicao(position):
        nonlocal last_log_event
        status = position.get("status")
        pos_id = position.get("id")
        direction = str(position.get("direction", "")).upper()
        amount = position.get("amount", VALOR_ORDEM)
        time_str = time.strftime('%H:%M:%S')

        if status == "open":
            last_log_event = f"\033[32m🟢 ORDEM {OPTION_TYPE.upper()} ACEITA! ID: {pos_id} | DIREÇÃO: {direction} | R${amount:.2f} [{time_str}]\033[0m"

        elif status == "closed":
            win_state = str(position.get("result", "")).lower()
            pnl = float(position.get("pnl", 0.0))
            saldo_atual = api.get_balance("PRACTICE") or 0.0

            if win_state in ["win", "loose_equal"] or pnl > 0:
                last_log_event = f"\033[1;32m🎉 RESULTADO: WIN! | Lucro: +R${pnl:.2f} | Saldo Atual: R${saldo_atual:.2f} [{time_str}]\033[0m"
            elif win_state in ["equal", "tie"] or (pnl == 0 and win_state != "loose"):
                last_log_event = f"\033[1;33m⚪ RESULTADO: EMPATE | Reembolso: R${amount:.2f} | Saldo Atual: R${saldo_atual:.2f} [{time_str}]\033[0m"
            else:
                last_log_event = f"\033[1;31m🔻 RESULTADO: LOSS! | Perda: -R${abs(amount):.2f} | Saldo Atual: R${saldo_atual:.2f} [{time_str}]\033[0m"

    api.on_position(ao_mudar_posicao)

    # 3. Callback de Cotacao em Tempo Real
    def ao_receber_vela(candle_event):
        nonlocal last_processed_candle_id, last_log_event, candle_history, crossovers_history, trades_history

        candle_from = candle_event.get("from") or candle_event.get("id")
        if not candle_from:
            return

        if candle_history:
            last_hist_from = candle_history[-1].get("from") or candle_history[-1].get("id")
            if candle_from == last_hist_from:
                candle_history[-1] = candle_event
            elif candle_from > last_hist_from:
                candle_history.append(candle_event)
                if len(candle_history) > 100:
                    candle_history.pop(0)

        if len(candle_history) < 20:
            return

        if CROSSOVER_TIMING == "IMMEDIATE_ON_TICK":
            eval_candles = candle_history
            closed_ts = candle_from
        else:
            eval_candles = candle_history[:-1]
            last_closed = candle_history[-2]
            closed_ts = last_closed.get("from") or last_closed.get("id")

        adx_series, pdi_series, ndi_series = adx(eval_candles, period=14)
        close_series = [c.get("close", 0.0) for c in eval_candles]
        sub_timestamps = [c.get("from") or c.get("id") for c in eval_candles]

        if len(pdi_series) < 3:
            return

        pdi_ant, pdi_cur = pdi_series[-2], pdi_series[-1]
        ndi_ant, ndi_cur = ndi_series[-2], ndi_series[-1]
        time_str = time.strftime('%H:%M:%S')

        c_close = candle_event.get("close", 0.0)

        # ---------------------------------------------------------------------
        # SELEÇÃO E EXECUÇÃO DA ESTRATÉGIA COM REGISTRO DE MARCADORES
        # ---------------------------------------------------------------------
        if EXECUTION_MODE == "PREDICTIVE_SLOPE":
            if last_processed_candle_id != closed_ts:
                delta_ant = abs(pdi_ant - ndi_ant)
                delta_cur = abs(pdi_cur - ndi_cur)

                if delta_cur <= 3.0 and delta_cur < delta_ant:
                    if pdi_cur < ndi_cur and (pdi_cur - pdi_ant) > (ndi_cur - ndi_ant):
                        last_log_event = f"⚡ PREDITIVO: CONVERGÊNCIA CALL DETECTADA [{time_str}] -> Transmitindo Ordem..."
                        crossovers_history[closed_ts] = "CALL"
                        trades_history[closed_ts] = {"direction": "CALL", "price": c_close}
                        api.buy(active_id=ACTIVE_ID, amount=VALOR_ORDEM, direction="call", option_type=OPTION_TYPE, duration=BLITZ_DURATION)
                        last_processed_candle_id = closed_ts

                    elif ndi_cur < pdi_cur and (ndi_cur - ndi_ant) > (pdi_cur - pdi_ant):
                        last_log_event = f"⚡ PREDITIVO: CONVERGÊNCIA PUT DETECTADA [{time_str}] -> Transmitindo Ordem..."
                        crossovers_history[closed_ts] = "PUT"
                        trades_history[closed_ts] = {"direction": "PUT", "price": c_close}
                        api.buy(active_id=ACTIVE_ID, amount=VALOR_ORDEM, direction="put", option_type=OPTION_TYPE, duration=BLITZ_DURATION)
                        last_processed_candle_id = closed_ts

        else:
            # ESTRATÉGIA TRADICIONAL (CONFIRMAÇÃO DE CRUZAMENTO)
            if last_processed_candle_id != closed_ts:
                # REGRA 1: +DI cruza -DI de baixo para cima -> CALL
                if pdi_ant <= ndi_ant and pdi_cur > ndi_cur:
                    last_log_event = f"SINAL CALL CONFIRMADO [{time_str}] -> Transmitindo Ordem..."
                    crossovers_history[closed_ts] = "CALL"
                    trades_history[closed_ts] = {"direction": "CALL", "price": c_close}
                    api.buy(active_id=ACTIVE_ID, amount=VALOR_ORDEM, direction="call", option_type=OPTION_TYPE, duration=BLITZ_DURATION)
                    last_processed_candle_id = closed_ts

                # REGRA 2: -DI cruza +DI de baixo para cima -> PUT
                elif ndi_ant <= pdi_ant and ndi_cur > pdi_cur:
                    last_log_event = f"SINAL PUT CONFIRMADO [{time_str}] -> Transmitindo Ordem..."
                    crossovers_history[closed_ts] = "PUT"
                    trades_history[closed_ts] = {"direction": "PUT", "price": c_close}
                    api.buy(active_id=ACTIVE_ID, amount=VALOR_ORDEM, direction="put", option_type=OPTION_TYPE, duration=BLITZ_DURATION)
                    last_processed_candle_id = closed_ts

        # Renderiza o Dashboard Fixo com Marcadores Visuais
        render_dashboard(
            api=api,
            active_id=ACTIVE_ID,
            option_type=OPTION_TYPE,
            execution_mode=EXECUTION_MODE,
            crossover_timing=CROSSOVER_TIMING,
            pdi_series=pdi_series,
            ndi_series=ndi_series,
            adx_series=adx_series,
            close_series=close_series,
            sub_timestamps=sub_timestamps,
            crossovers_history=crossovers_history,
            trades_history=trades_history,
            candle_event=candle_event,
            last_log=last_log_event
        )

    api.get_realtime_candles(active_id=ACTIVE_ID, size=CANDLE_SIZE, callback=ao_receber_vela)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n[-] Bot encerrado pelo usuario.")
        api.disconnect()


if __name__ == "__main__":
    main()

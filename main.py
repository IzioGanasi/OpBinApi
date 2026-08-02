import os
import sys
import time

# Habilita o suporte a sequências de escape ANSI no Windows
os.system("")

# Garante suporte completo a UTF-8 no terminal Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from opbin_api import OpBinAPI, adx, AsciiChart


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
    Renderiza o Dashboard Fixo de Terminal de Alta Resolução com Indicadores Visuais de Cruzamento e Operações.
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

    sub_count = 35
    sub_closes = close_series[-sub_count:] if len(close_series) >= sub_count else close_series
    sub_pdi = pdi_series[-sub_count:] if len(pdi_series) >= sub_count else pdi_series
    sub_ndi = ndi_series[-sub_count:] if len(ndi_series) >= sub_count else ndi_series
    sub_ts = sub_timestamps[-sub_count:] if len(sub_timestamps) >= sub_count else sub_timestamps

    # Prepara marcadores operacionais e linha de preço de ordem para o gráfico de PREÇO
    price_markers = []
    h_lines = []
    
    last_trade_price = None
    for i, ts in enumerate(sub_ts):
        if ts in trades_history:
            tr = trades_history[ts]
            dir_str = tr.get("direction", "CALL")
            price_val = tr.get("price", c_close)
            last_trade_price = price_val

            price_markers.append({
                "index": i,
                "value": price_val,
                "direction": dir_str.lower(),
                "color": AsciiChart.GREEN if dir_str == "CALL" else AsciiChart.RED
            })

    if last_trade_price is not None:
        h_lines.append({
            "value": last_trade_price,
            "color": AsciiChart.YELLOW,
            "label": f"Entrada ({last_trade_price:.5f})"
        })

    # 1. Renderiza o Gráfico do PREÇO
    candle_chart_str = AsciiChart.render(
        series={"Preço": (sub_closes, AsciiChart.CYAN)},
        height=8,
        width=55,
        markers=price_markers,
        h_lines=h_lines,
        title="  \033[1;36m1. GRÁFICO DO CANDLE (PREÇO FECHAMENTO - CLOSE):\033[0m"
    )

    # Prepara marcadores de cruzamento para o gráfico do ADX
    adx_markers = []
    for i, ts in enumerate(sub_ts):
        if ts in crossovers_history:
            c_type = crossovers_history[ts]
            val = sub_pdi[i] if i < len(sub_pdi) else 30.0
            adx_markers.append({
                "index": i,
                "value": val,
                "direction": c_type.lower(),
                "color": AsciiChart.GREEN if c_type == "CALL" else AsciiChart.RED
            })

    # 2. Renderiza o Gráfico do ADX apenas com +DI (Verde) e -DI (Vermelho)
    adx_chart_str = AsciiChart.render(
        series={
            "+DI": (sub_pdi, AsciiChart.GREEN),
            "-DI": (sub_ndi, AsciiChart.RED)
        },
        height=8,
        width=55,
        markers=adx_markers,
        title="  \033[1;33m2. GRÁFICO DO ADX (+DI Verde | -DI Vermelho):\033[0m"
    )

    # Monta a tela estática completa
    lines = []
    lines.append("─" * 78)
    lines.append(f"  \033[1;36mOPBIN TRADING DASHBOARD\033[0m | ATIVO: \033[1m{active_id}\033[0m | PAYOUT: \033[1;32m{payout_atual:.1f}%\033[0m")
    lines.append(f"  MODALIDADE: \033[1;33m{option_type.upper()}\033[0m | SALDO: \033[1;32mR${saldo_atual:.2f}\033[0m | ESTRATÉGIA: \033[1;35m{execution_mode}\033[0m")
    lines.append("─" * 78)
    lines.append(candle_chart_str)
    lines.append("─" * 78)
    lines.append(adx_chart_str)
    lines.append("─" * 78)
    lines.append(f"  STATUS ATUAL: [{time_str}] {trend_symbol} O:{c_open:.5f} C:{c_close:.5f}")
    lines.append(f"  MÉTRICAS ADX : \033[32m+DI [{pdi_bar}] {pdi_cur:4.1f}\033[0m | \033[31m-DI [{ndi_bar}] {ndi_cur:4.1f}\033[0m | ADX: {adx_cur:4.1f}")
    lines.append("─" * 78)
    lines.append(f"  ÚLTIMO EVENTO: \033[1;33m{last_log}\033[0m")
    lines.append("─" * 78)

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
    VALOR_ORDEM = 2.0           # Valor da Entrada em R$ ou USD
    OPTION_TYPE = "blitz"       # Opcoes: "blitz" ou "binary"
    BLITZ_DURATION = 60         # Duracao da Blitz em segundos (ex: 60s, 30s, 5s)
    
    # "CLOSED_CANDLE"    -> Estratégia Tradicional: Cruzamento clássico +DI / -DI no fechamento.
    # "PREDICTIVE_SLOPE" -> Estratégia Preditiva: Entra 1 candle antes via inclinação.
    EXECUTION_MODE = "CLOSE_CANDLE" 

    # "ON_CANDLE_CLOSE"   -> Aguarda a vela fechar.
    # "IMMEDIATE_ON_TICK" -> Opera imediatamente no tick em que o cruzamento ocorrer.
    CROSSOVER_TIMING = "ON_CANDLE_CLOSE"
    # -------------------------------------------------------------------------

    last_processed_candle_id = None
    last_log_event = "Aguardando primeiro tick de cotação..."
    crossovers_history = {}
    trades_history = {}

    # 1. Coleta Histórico Inicial de Velas com Retry Resiliente
    print(f"[*] Carregando histórico inicial de velas para o ativo {ACTIVE_ID}...")
    candle_history = []
    for attempt in range(3):
        candle_history = api.get_candles(active_id=ACTIVE_ID, size=CANDLE_SIZE, count=60, timeout=8)
        if candle_history:
            break
        time.sleep(1)

    if not candle_history:
        print("[ERR] Não foi possível obter o histórico inicial de velas.")
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

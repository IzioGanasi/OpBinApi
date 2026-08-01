import time
from opbin_api import OpBinAPI, adx


def draw_bar(val: float, max_val: float = 60.0, length: int = 10) -> str:
    """Gera uma mini barra de progresso ascii minimalista para o terminal."""
    fraction = min(max(val / max_val, 0.0), 1.0)
    filled = int(round(fraction * length))
    return "█" * filled + "░" * (length - filled)


def main():
    api = OpBinAPI()
    
    if not api.connect():
        print("[ERR] Falha ao conectar à API.")
        return

    api.select_account("PRACTICE")
    saldo_inicial = api.get_balance("PRACTICE")

    ACTIVE_ID = 76   # EURUSD-OTC (Blitz)
    CANDLE_SIZE = 60 # M1
    VALOR_ORDEM = 5.0
    last_processed_candle_id = None

    print("\n" + "=" * 75)
    print(f"  OPBIN REALTIME BOT | ATIVO: {ACTIVE_ID} (M1) | SALDO INICIAL: R${saldo_inicial:.2f}")
    print("  ESTRATÉGIA: CRUZAMENTO ADX (+DI / -DI)")
    print("=" * 75 + "\n")

    # 1. Aquecimento: Coleta o histórico inicial de 50 velas para alimentar o ADX
    print("[*] Coletando histórico de 50 velas para aquecimento do ADX...")
    candle_history = api.get_candles(active_id=ACTIVE_ID, size=CANDLE_SIZE, count=50)

    if not candle_history:
        print("[ERR] Não foi possível obter o histórico inicial de velas.")
        api.disconnect()
        return

    print(f"[+] Aquecimento concluído! {len(candle_history)} velas históricas carregadas na memória.")
    print("[*] Iniciando fluxo de cotações em TEMPO REAL...\n")

    # 2. Callback de Posições (Acompanhamento e Resultado das Ordens)
    def ao_mudar_posicao(position):
        status = position.get("status")
        pos_id = position.get("id")
        direction = str(position.get("dir") or position.get("direction", "")).upper()
        amount = position.get("amount", VALOR_ORDEM)
        time_str = time.strftime('%H:%M:%S')

        if status == "open":
            print(f"\n >>> [ORDEM ATIVA] ID: {pos_id} | DIREÇÃO: {direction} | VALOR: R${amount:.2f} ({time_str})")

        elif status == "closed":
            win_state = position.get("win") or position.get("result")
            win_amount = float(position.get("win_amount", 0.0))
            profit = win_amount - amount
            saldo_atual = api.get_balance("PRACTICE") or 0.0

            if win_state == "win" or win_amount > amount:
                print(f"\n [+] [RESULTADO] WIN! Lucro: +R${profit:.2f} | Saldo Atual: R${saldo_atual:.2f} ({time_str})\n")
            elif win_state == "equal" or win_amount == amount:
                print(f"\n [=] [RESULTADO] EMPATE! Reembolso: R${amount:.2f} | Saldo Atual: R${saldo_atual:.2f} ({time_str})\n")
            else:
                print(f"\n [-] [RESULTADO] LOSS! Perda: -R${amount:.2f} | Saldo Atual: R${saldo_atual:.2f} ({time_str})\n")

    api.on_position(ao_mudar_posicao)

    # 3. Callback de Cotação em Tempo Real (Zero latência de rede)
    def ao_receber_vela(candle_event):
        nonlocal last_processed_candle_id, candle_history

        # Atualiza o histórico local na memória com o candle recebido via WebSocket
        candle_from = candle_event.get("from") or candle_event.get("id")
        if not candle_from:
            return

        if candle_history:
            last_hist_from = candle_history[-1].get("from") or candle_history[-1].get("id")
            if candle_from == last_hist_from:
                # Atualiza a vela atual em formação
                candle_history[-1] = candle_event
            elif candle_from > last_hist_from:
                # Nova vela iniciada! Adiciona ao histórico e mantém o tamanho fixo
                candle_history.append(candle_event)
                if len(candle_history) > 100:
                    candle_history.pop(0)

        # A vela imediatamente anterior (candle_history[-2]) é a última vela FECHADA
        if len(candle_history) < 20:
            return

        last_closed = candle_history[-2]
        closed_ts = last_closed.get("from") or last_closed.get("id")

        # 4. Cálculo instantâneo do ADX em memória (< 0.01ms)
        adx_series, pdi_series, ndi_series = adx(candle_history[:-1], period=14)
        if len(pdi_series) < 3:
            return

        pdi_ant, pdi_cur = pdi_series[-2], pdi_series[-1]
        ndi_ant, ndi_cur = ndi_series[-2], ndi_series[-1]
        adx_cur = adx_series[-1]

        c_open = candle_event.get("open", 0.0)
        c_close = candle_event.get("close", 0.0)
        is_bull = c_close >= c_open
        trend_symbol = "[▲ ALTA]" if is_bull else "[▼ BAIXA]"
        time_str = time.strftime('%H:%M:%S')

        pdi_bar = draw_bar(pdi_cur, 60.0, 10)
        ndi_bar = draw_bar(ndi_cur, 60.0, 10)

        # Exibição instantânea no terminal
        status_line = (
            f"[{time_str}] {trend_symbol} O:{c_open:.5f} C:{c_close:.5f} | "
            f"+DI [{pdi_bar}] {pdi_cur:4.1f} | "
            f"-DI [{ndi_bar}] {ndi_cur:4.1f} | "
            f"ADX: {adx_cur:4.1f}"
        )
        print(status_line)

        # 5. Avaliação de Sinal no Fechamento da Vela
        if last_processed_candle_id != closed_ts:

            # Sinal CALL (+DI cruza -DI para cima)
            if pdi_ant <= ndi_ant and pdi_cur > ndi_cur:
                print(f"\n >>> SINAL [CALL] DETECTADO NO FECHAMENTO ({time_str}) <<<")
                api.buy(active_id=ACTIVE_ID, amount=VALOR_ORDEM, direction="call", option_type_id=3)
                last_processed_candle_id = closed_ts

            # Sinal PUT (-DI cruza +DI para cima)
            elif ndi_ant <= pdi_ant and ndi_cur > pdi_cur:
                print(f"\n >>> SINAL [PUT] DETECTADO NO FECHAMENTO ({time_str}) <<<")
                api.buy(active_id=ACTIVE_ID, amount=VALOR_ORDEM, direction="put", option_type_id=3)
                last_processed_candle_id = closed_ts

    # Inicia a escuta das velas em tempo real
    api.get_realtime_candles(active_id=ACTIVE_ID, size=CANDLE_SIZE, callback=ao_receber_vela)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[-] Bot encerrado pelo usuário.")
        api.disconnect()


if __name__ == "__main__":
    main()

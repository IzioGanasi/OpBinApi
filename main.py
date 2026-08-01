import time
from opbin_api import OpBinAPI, rsi, sma, IndicatorFactory


def main():
    api = OpBinAPI()
    if not api.connect():
        return

    print("[*] Buscando histórico de 30 velas do Ativo 76 (M1) via opbin_api...")
    candles = api.get_candles(active_id=76, size=60, count=30)

    if candles:
        # 1. Indicador RSI 1:1
        rsi_valores = rsi(candles, period=14)
        print(f"\n[+] RSI (14) Último Valor: {rsi_valores[-1]:.2f}")

        # 2. Indicador SMA 1:1
        sma_valores = sma(candles, period=10)
        print(f"[+] SMA (10) Último Valor: {sma_valores[-1]:.5f}")

        # 3. IndicatorFactory (101 Indicadores)
        factory = IndicatorFactory()
        smi_k, smi_d = factory.calculate(indicator_id=194, candles=candles)
        print(f"[+] Stochastic Momentum Index (ID 194) %K: {smi_k[-1]:.2f} | %D: {smi_d[-1]:.2f}")

    api.disconnect()


if __name__ == "__main__":
    main()

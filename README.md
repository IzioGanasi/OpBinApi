# 🚀 OpBinAPI - Python SDK & Engine de Indicadores 1:1

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/status-production_ready-brightgreen.svg)]()

Biblioteca SDK em Python projetada para automação de negociação, coleta de cotações em tempo real e cálculo de indicadores técnicos de precisão **1:1** na corretora OpBin / IQ Option.

---

## 💡 Funcionalidades Principais

- ⚡ **Cobertura 100% de Mensagens WebSocket (84 Roteamentos Mapeados)**: Suporte completo para cotações, ordens binárias/turbo/blitz/digitais, saldos, históricos, perfis e chat.
- 📊 **Motor de Indicadores 1:1 Nativo**: Reconstrução exata dos **101 scripts de indicadores** extraídos da plataforma WebAssembly/Lua da corretora (RSI, SMA, EMA, SMI, AO, TRIX, ALMA, DeMarker, etc.).
- 🔄 **Reconexão Automática & Preservação de Estado**: Gerenciamento de reconexão de rede que preserva ordens ativas, restaura subscrições de velas em tempo real e realiza *gap-filling* de histórico de cotações perfeitamente.
- 📦 **Pronto para GitHub & PyPA (`pip install git+...`)**: Arquitetura modular de pacotes pronta para distribuição.

---

## 💻 Instalação

### Instalação via Git / GitHub:
```bash
pip install git+https://github.com/SeuUsuario/OpBinApi.git
```

### Instalação em Modo de Desenvolvimento Local:
```bash
git clone https://github.com/SeuUsuario/OpBinApi.git
cd OpBinApi
pip install -e .
```

---

## ⚡ Exemplo Rápido de Uso (`main.py`)

```python
import time
from opbin_api import OpBinAPI, rsi, sma, IndicatorFactory

def main():
    # Instancia a API
    api = OpBinAPI()
    
    # Conecta e autentica na corretora
    if not api.connect():
        print("Erro ao conectar.")
        return

    # Seleciona a conta de treinamento (Practice)
    api.select_account("PRACTICE")
    saldo = api.get_balance("PRACTICE")
    print(f"[+] Saldo Atual: R${saldo:.2f}")

    # Coleta 30 velas M1 do Ativo 76 (EURUSD-OTC)
    candles = api.get_candles(active_id=76, size=60, count=30)

    if candles:
        # Cálculo de RSI (14) 1:1
        valor_rsi = rsi(candles, period=14)[-1]
        print(f"[+] RSI (14): {valor_rsi:.2f}")

        # Cálculo de SMA (10) 1:1
        valor_sma = sma(candles, period=10)[-1]
        print(f"[+] SMA (10): {valor_sma:.5f}")

        # Execução de Indicador Oficial via Fábrica Universal (Script ID 194 - SMI)
        factory = IndicatorFactory()
        smi_k, smi_d = factory.calculate(indicator_id=194, candles=candles)
        print(f"[+] SMI %K: {smi_k[-1]:.2f} | %D: {smi_d[-1]:.2f}")

    # Desconecta
    api.disconnect()

if __name__ == "__main__":
    main()
```

---

## 📚 Documentação Técnica

- 📖 **[Documentação de Mensagens WebSocket](DOCUMENTACAO_MENSAGENS.md)**: Detalhamento de todas as 84 mensagens, estruturas JSON e exemplos de respostas.
- 📊 **[Documentação de Indicadores 1:1](DOCUMENTACAO_INDICADORES.md)**: Fórmulas matemáticas, sinais operacionais e exemplos para cada um dos indicadores.

---

## ⚖️ Licença

Este projeto é disponibilizado sob a licença MIT.

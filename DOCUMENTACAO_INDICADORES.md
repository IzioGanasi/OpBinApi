# 📘 DOCUMENTAÇÃO TÉCNICA COMPLETA DE INDICADORES (MAIN_API)

Esta documentação detalha os indicadores técnicos calculados com precisão matemática **1:1** em relação ao motor WebAssembly/Lua da corretora.

Aqui você encontra a descrição técnica, as informações extraíveis para robôs de trading, o exemplo de código Python e o retorno numérico para cada um dos indicadores.

---

## 📈 1. OSCILADORES DE MOMENTO E TENDÊNCIA

### 1.1 RSI (Relative Strength Index)
* **Categoria:** Oscilador de Momento / Força Relativa.
* **Descrição Técnica:** Mede a velocidade e a mudança dos movimentos de preço em uma escala de 0 a 100 baseada na média de ganhos e perdas nos últimos N períodos (fórmula de Wilder 1:1).
* **Informações Extraíveis:**
  * **Nível > 70 (Sobrecompra):** Indica que o ativo está esticado na alta, aumentando a probabilidade de correção de baixa (`PUT`).
  * **Nível < 30 (Sobrevenda):** Indica desvalorização excessiva, aumentando a probabilidade de repique de alta (`CALL`).
  * **Linha Central (50):** Rompimento acima de 50 confirma força compradora; abaixo de 50 confirma força vendedora.
* **Exemplo de Código Python:**
```python
from api import OpBinAPI
from indicators import rsi

api = OpBinAPI()
api.connect()

candles = api.get_candles(active_id=76, size=60, count=30)
valores_rsi = rsi(candles, period=14)

rsi_atual = valores_rsi[-1]
print(f"RSI Atual: {rsi_atual:.2f}")

if rsi_atual >= 70:
    print(" Signal: SOBRECOMPRADO -> Possível entrada em PUT")
elif rsi_atual <= 30:
    print(" Signal: SOBREVENDIDO -> Possível entrada em CALL")
```
* **Exemplo de Retorno:**
```python
[48.25, 51.10, 56.40, 68.90, 72.15]  # Valor final: 72.15 (Sobrecomprado)
```

---

### 1.2 Stochastic Momentum Index (SMI - Script ID 194) 🌟
* **Categoria:** Oscilador Estocástico Duplamente Suavizado.
* **Descrição Técnica:** Versão aprimorada do Oscilador Estocástico tradicional extraída 1:1 do **Script ID 194** da corretora. Mede onde o preço de fechamento está em relação ao ponto médio da faixa High/Low recente, utilizando dupla suavização exponencial (EMA) para eliminar ruídos de falso rompimento.
* **Informações Extraíveis:**
  * `%K` e `%D` (Valores entre -100 e +100):
  * **Nível > +40 (Sobrecompra):** Região de exaustão de alta.
  * **Nível < -40 (Sobrevenda):** Região de exaustão de baixa.
  * **Cruzamento de Linhas:** Quando a linha rápida `%K` cruza a linha de sinal `%D` de baixo para cima abaixo de -40, gera sinal de `CALL`. Quando cruza de cima para baixo acima de +40, gera sinal de `PUT`.
* **Exemplo de Código Python:**
```python
from api import OpBinAPI
from indicators.stochastic_momentum_index import stochastic_momentum_index

api = OpBinAPI()
api.connect()

candles = api.get_candles(active_id=76, size=60, count=30)
k_series, d_series = stochastic_momentum_index(candles, k_period=10, smooth=3, dsmooth=3, d_period=10)

k_atual = k_series[-1]
d_atual = d_series[-1]
print(f"SMI %K: {k_atual:.2f} | SMI %D: {d_atual:.2f}")
```
* **Exemplo de Retorno:**
```python
# Retorna tupla de listas (%K, %D)
(-42.15, -38.40)  # %K em região de sobrevenda cruzando %D
```

---

### 1.3 Awesome Oscillator (AO - Script ID 112)
* **Categoria:** Oscilador de Impulso / Momentum.
* **Descrição Técnica:** Calculado 1:1 com o **Script ID 112** da corretora como a diferença entre uma Média Móvel Simples de 5 períodos e uma Média Móvel Simples de 34 períodos aplicadas ao preço médio da vela (`HL2 = (High + Low) / 2`).
* **Informações Extraíveis:**
  * **Valores Positivos (> 0):** Momentum de alta ativo.
  * **Valores Negativos (< 0):** Momentum de baixa ativo.
  * **Mudança de Cor da Barra (Histograma):** Barra verde acima de zero confirma aceleração compradora; barra vermelha indica perda de força.
* **Exemplo de Código Python:**
```python
from api import OpBinAPI
from indicators.awesome_oscillator import awesome_oscillator

api = OpBinAPI()
api.connect()

candles = api.get_candles(active_id=76, size=60, count=40)
ao_series = awesome_oscillator(candles, fast=5, slow=34)

ao_atual = ao_series[-1]
ao_anterior = ao_series[-2]

print(f"AO Atual: {ao_atual:.5f} | AO Anterior: {ao_anterior:.5f}")
```
* **Exemplo de Retorno:**
```python
[0.00012, 0.00025, 0.00038, 0.00041]
```

---

## 📊 2. MÉDIAS MÓVEIS E SEGUIDORES DE TENDÊNCIA

### 2.1 Média Móvel Simples (SMA) e Exponencial (EMA)
* **Categoria:** Seguidor de Tendência / Suporte e Resistência Dinâmico.
* **Descrição Técnica:**
  * **SMA (Simple Moving Average):** Média aritmética dos preços de fechamento nos últimos N períodos.
  * **EMA (Exponential Moving Average):** Média com peso exponencial maior para os candles mais recentes, reagindo mais rápido às mudanças de preço.
* **Informações Extraíveis:**
  * **Preço Acima da Média:** Tendência de Alta (Bullish).
  * **Preço Abaixo da Média:** Tendência de Baixa (Bearish).
  * **Cruzamento de Médias (Golden Cross / Death Cross):** Quando a EMA rápida (ex: 9) cruza a SMA lenta (ex: 21) para cima, sinal de compra (`CALL`); para baixo, sinal de venda (`PUT`).
* **Exemplo de Código Python:**
```python
from api import OpBinAPI
from indicators import sma, ema

api = OpBinAPI()
api.connect()

candles = api.get_candles(active_id=76, size=60, count=30)
ema_9 = ema(candles, period=9)
sma_21 = sma(candles, period=21)

print(f"EMA 9: {ema_9[-1]:.5f} | SMA 21: {sma_21[-1]:.5f}")

if ema_9[-1] > sma_21[-1] and ema_9[-2] <= sma_21[-2]:
    print("🚀 Golden Cross! Sinal de CALL")
```
* **Exemplo de Retorno:**
```python
(1.08540, 1.08490)  # EMA 9 superior à SMA 21
```

---

### 2.2 ALMA (Arnaud Legoux Moving Average - Script ID 8)
* **Categoria:** Média Móvel de Baixe Atraso (Low-Lag Moving Average).
* **Descrição Técnica:** Utiliza uma distribuição Gaussiana (Curva Normal) com parâmetros de offset e sigma extraídos 1:1 do **Script ID 8** da corretora para reduzir o atraso (lag) sem introduzir ruídos gráficos.
* **Informações Extraíveis:**
  * Acompanhamento ultra-suave da tendência com menor atraso do que a EMA tradicional.
* **Exemplo de Código Python:**
```python
from api import OpBinAPI
from indicators import alma

api = OpBinAPI()
api.connect()

candles = api.get_candles(active_id=76, size=60, count=30)
alma_valores = alma(candles, period=9, offset=0.85, sigma=6.0)

print(f"ALMA Atual: {alma_valores[-1]:.5f}")
```
* **Exemplo de Retorno:**
```python
[1.08512, 1.08525, 1.08541]
```

---

## 📉 3. VOLATILIDADE E CANAIS DE PREÇO

### 3.1 Commodity Channel Index (CCI)
* **Categoria:** Oscilador de Volatilidade e Ciclo de Preço.
* **Descrição Técnica:** Mede o desvio da cotação em relação à sua média móvel estatística proporcional ao desvio médio absoluto (fórmula 1:1).
* **Informações Extraíveis:**
  * **CCI > +100:** Preço extremamente forte acima da média (tendência forte de alta ou sobrecompra extrema).
  * **CCI < -100:** Preço extremamente fraco abaixo da média (tendência forte de baixa ou sobrevenda extrema).
* **Exemplo de Código Python:**
```python
from api import OpBinAPI
from indicators.engine import cci

api = OpBinAPI()
api.connect()

candles = api.get_candles(active_id=76, size=60, count=30)
cci_valores = cci(candles, period=20)

print(f"CCI Atual: {cci_valores[-1]:.2f}")
```
* **Exemplo de Retorno:**
```python
[85.40, 105.20, 122.80]  # Rompimento da linha de +100
```

---

## 🏭 4. USO DA FÁBRICA UNIVERSAL DE INDICADORES (101 SCRIPTS EXTRAÍDOS)

### `IndicatorFactory`
A classe `IndicatorFactory` permite que você carregue e execute **qualquer um dos 101 indicadores extraídos** de `extracted_indicators.json` passando apenas o ID numérico do script:

* **Exemplo de Código Python:**
```python
from api import OpBinAPI
from indicators import IndicatorFactory

api = OpBinAPI()
api.connect()

candles = api.get_candles(active_id=76, size=60, count=30)

# Instancia a Fábrica Universal
factory = IndicatorFactory()

# Lista todos os 101 indicadores disponíveis no catálogo da corretora
todos_indicadores = factory.list_available_indicators()
print(f"Total de Indicadores Disponíveis: {len(todos_indicadores)}")

# Executa o indicador SMI (ID 194)
smi_k, smi_d = factory.calculate(indicator_id=194, candles=candles)
print(f"SMI Executado via Fábrica -> %K: {smi_k[-1]:.2f}")

# Executa o indicador Awesome Oscillator (ID 112)
ao_val = factory.calculate(indicator_id=112, candles=candles)
print(f"AO Executado via Fábrica -> AO: {ao_val[-1]:.5f}")
```

---

## 📌 Resumo da Integração no `main.py`
Você pode importar os indicadores diretamente do pacote `indicators` ou utilizá-los integrados às cotações em tempo real da sua `OpBinAPI`:

```python
from api import OpBinAPI
from indicators import rsi, sma

api = OpBinAPI()
api.connect()

# Callback em tempo real combinando cotação + indicador
def ao_receber_vela(candle):
    velas_historico = api.get_candles(active_id=76, size=60, count=20)
    if velas_historico:
        valor_rsi = rsi(velas_historico, period=14)[-1]
        print(f"Vela Atual: {candle.get('close')} | RSI (14): {valor_rsi:.2f}")

api.get_realtime_candles(active_id=76, size=60, callback=ao_receber_vela)
```

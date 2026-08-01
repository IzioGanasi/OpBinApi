# 📘 DOCUMENTAÇÃO COMPLETA, DETALHADA E GUIA DE CÓDIGO PYTHON (MAIN_API)

Esta documentação fornece a explicação técnica exaustiva, a lista detalhada de campos extraíveis, os casos de uso práticos, o **exemplo de código Python** para chamada através da biblioteca `OpBinAPI` e o **exemplo exato do retorno JSON** para cada uma das mensagens do protocolo WebSocket.

---

## 🟢 1. AUTENTICAÇÃO E CONEXÃO DE SESSÃO

### `authenticate` / `authenticated`
* **Descrição:** Realiza a validação da chave SSID gerada pelo login HTTP e estabelece a sessão autorizada no WebSocket.
* **Informações Extraíveis:**
  * `msg` (`True`/`False`): Status de sucesso da autenticação.
  * `client_session_id`: Identificador único de sessão do cliente mantido entre reconexões.
  * `request_id`: ID sequencial atribuído à requisição de login.
* **Casos de Uso:** Confirmar que a conexão foi aceita antes de enviar ordens ou solicitar saldos.
* **Exemplo de Código Python:**
```python
from api import OpBinAPI

api = OpBinAPI()
conectado = api.connect()

if conectado:
    print("[+] Conexão autenticada com sucesso!")
```
* **Exemplo de Retorno da Corretora:**
```json
{
  "name": "authenticated",
  "msg": true,
  "client_session_id": "9b128f7a01cd4591a",
  "request_id": "101"
}
```

---

### `timeSync`
* **Descrição:** Retorna o horário sincronizado do servidor da corretora em milissegundos.
* **Informações Extraíveis:**
  * `msg` (Timestamp Unix em milissegundos, ex: `1785548258171`).
* **Casos de Uso:** Sincronizar o relógio local do robô para disparar ordens no segundo exato `00.000` do fechamento da vela.
* **Exemplo de Código Python:**
```python
from api import OpBinAPI

api = OpBinAPI()
api.connect()

timestamp_servidor = api.server_timestamp
print(f"Horário do Servidor (ms): {timestamp_servidor}")
```
* **Exemplo de Retorno da Corretora:**
```json
{
  "name": "timeSync",
  "msg": 1785548258171
}
```

---

### `setOptions` / `setLang`
* **Descrição:** Envia as configurações iniciais do cliente e preferências de idioma para o servidor da corretora.
* **Informações Extraíveis:**
  * `lang`: Idioma ativo (`pt_PT`, `en_US`).
  * `sendResults`: Define se o servidor deve enviar resultados de ordens automaticamente.
* **Casos de Uso:** Configuração inicial de sessão ao abrir o socket.
* **Exemplo de Código Python:**
```python
from ws_options_config import get_set_options_payload, get_set_lang_payload

payload_opcoes = get_set_options_payload(send_results=True)
payload_idioma = get_set_lang_payload(lang="pt_PT")
```
* **Exemplo de Retorno da Corretora:**
```json
{
  "name": "result",
  "request_id": "request_4",
  "msg": {
    "success": true
  }
}
```

---

## 💰 2. GERENCIAMENTO DE CONTAS E SALDOS

### `get-balances` / `balances` / `available-balances` / `balance-changed`
* **Descrição:** Retorna ou atualiza em tempo real a lista de todas as contas associadas ao usuário.
* **Informações Extraíveis:**
  * `id`: ID único do saldo (`user_balance_id`).
  * `type`: Tipo de conta (`1` = Real, `4` = Prática/Demo, `2` = Torneio).
  * `amount`: Saldo numérico disponível na conta.
  * `currency`: Moeda da conta (`BRL`, `USD`, `EUR`).
  * `bonus_amount`: Valor de bônus acumulado.
* **Casos de Uso:** Verificar se há margem antes de abrir ordens, monitorar lucros acumulados.
* **Exemplo de Código Python:**
```python
from api import OpBinAPI

api = OpBinAPI()
api.connect()

# Obter valor numérico da conta de Prática (Demo)
saldo_pratica = api.get_balance(account_type="PRACTICE")
print(f"Saldo Prática: ${saldo_pratica}")

# Obter a lista bruta de todos os saldos
todos_saldos = api.get_balances()
print(todos_saldos)
```
* **Exemplo de Retorno da Corretora:**
```json
{
  "name": "balances",
  "request_id": "7",
  "msg": [
    {
      "id": 1067401181,
      "user_id": 136879853,
      "type": 1,
      "amount": 0.00,
      "currency": "USD",
      "bonus_amount": 0
    },
    {
      "id": 1067401182,
      "user_id": 136879853,
      "type": 4,
      "amount": 2580.37,
      "currency": "USD",
      "bonus_amount": 0
    }
  ]
}
```

---

### `profile.change-active-balance` / `subscription-balance-changed`
* **Descrição:** Seleciona e define qual conta será utilizada para a abertura de novas operações.
* **Informações Extraíveis:**
  * `active_balance_id`: ID da conta que passou a ser a ativa no perfil.
* **Casos de Uso:** Alternar dinamicamente entre a Conta Prática e a Conta Real na sua API.
* **Exemplo de Código Python:**
```python
from api import OpBinAPI

api = OpBinAPI()
api.connect()

# Alterna para a conta de Prática (type: 4)
api.select_account(account_type="PRACTICE")

# Alterna para a conta Real (type: 1)
# api.select_account(account_type="REAL")
```
* **Exemplo de Retorno da Corretora:**
```json
{
  "name": "subscription-balance-changed",
  "request_id": "8",
  "msg": {
    "id": 1067401182
  },
  "status": 2000
}
```

---

## 📈 3. GRÁFICOS, VELAS (CANDLES) E COTAÇÕES

### `get-candles` / `candles` / `first-candles`
* **Descrição:** Retorna o histórico de velas de um ativo para análise técnica.
* **Informações Extraíveis:**
  * `open`: Preço de abertura da vela.
  * `close`: Preço de fechamento da vela.
  * `max` / `high`: Preço máximo atingido.
  * `min` / `low`: Preço mínimo atingido.
  * `volume`: Volume negociado.
  * `at` / `from` / `to`: Timestamps de início e fim da vela.
  * `id`: ID do candle.
* **Casos de Uso:** Cálculo de indicadores técnicos (RSI, ADX, Médias Móveis, Suporte e Resistência).
* **Exemplo de Código Python:**
```python
from api import OpBinAPI

api = OpBinAPI()
api.connect()

# Busca 10 velas do ativo ID 76 (EUR/USD OTC) de timeframe 60s (M1)
velas = api.get_candles(active_id=76, size=60, count=10)

for v in velas:
    print(f"Vela {v['id']} | Abertura: {v['open']} | Fechamento: {v['close']} | Máx: {v['max']} | Mín: {v['min']}")
```
* **Exemplo de Retorno da Corretora:**
```json
{
  "name": "candles",
  "request_id": "105",
  "msg": {
    "candles": [
      {
        "id": 4575050,
        "from": 1785548460,
        "to": 1785548520,
        "open": 0.981575,
        "close": 0.981655,
        "min": 0.981545,
        "max": 0.981655,
        "volume": 12
      }
    ]
  }
}
```

---

### `candle-generated`
* **Descrição:** Transmissão em tempo real (tick a tick) da vela em formação no momento atual.
* **Informações Extraíveis:**
  * `active_id`: ID do ativo (ex: `1` = EUR/USD).
  * `size`: Timeframe da vela em segundos (`60` = M1, `300` = M5).
  * `close` / `bid` / `ask`: Cotação em tempo real a cada segundo.
  * `phase`: Fase da vela (`T` = em negociação).
* **Casos de Uso:** Robôs de alta velocidade que detectam cruzamentos de médias dentro do próprio candle antes do fechamento.
* **Exemplo de Código Python:**
```python
import time
from api import OpBinAPI

api = OpBinAPI()
api.connect()

# Inscreve-se nas atualizações do EUR/USD (ID 76) M1
api.subscribe_candle(active_id=76, size=60)

# Monitora a vela em tempo real
for _ in range(5):
    print("Vela Atual:", api.realtime_candle)
    time.sleep(1)
```
* **Exemplo de Retorno da Corretora:**
```json
{
  "name": "candle-generated",
  "microserviceName": "quotes",
  "msg": {
    "active_id": 76,
    "size": 60,
    "at": 1785548508000000000,
    "from": 1785548460,
    "to": 1785548520,
    "id": 4575050,
    "open": 0.981575,
    "close": 0.981665,
    "min": 0.981545,
    "max": 0.981665,
    "ask": 0.98167,
    "bid": 0.98166,
    "phase": "T"
  }
}
```

---

## 🎯 4. OPERAÇÕES, ORDENS E POSIÇÕES (TRADING)

### `binary-options.open-option` / `option`
* **Descrição:** Confirmação da abertura de ordens em Opções Binárias, Turbo ou Blitz.
* **Informações Extraíveis:**
  * `option_id`: ID único da operação gerada.
  * `active_id`: Ativo negociado.
  * `direction`: Direção escolhida (`call` para compra ou `put` para venda).
  * `amount`: Valor investido na operação.
  * `created_at` / `open_time`: Horário exato da abertura.
  * `expiration_time`: Horário limite do fechamento da ordem.
* **Casos de Uso:** Confirmar se a ordem foi aceita pela corretora sem erros de rejeição.
* **Exemplo de Código Python:**
```python
from api import OpBinAPI

api = OpBinAPI()
api.connect()

# Entra com R$ 10.00 em CALL no EUR/USD (ID 76)
api.buy(active_id=76, amount=10.0, direction="call", option_type_id=3)
```
* **Exemplo de Retorno da Corretora:**
```json
{
  "name": "option",
  "request_id": "110",
  "msg": {
    "id": 14124648287,
    "active_id": 76,
    "amount": 10.0,
    "direction": "call",
    "created_at": 1785548360,
    "expiration_time": 1785548400,
    "profit_percent": 87
  }
}
```

---

### `digital-options.place-digital-option` / `digital-option-placed`
* **Descrição:** Abertura e confirmação de ordens do tipo Opções Digitais.
* **Informações Extraíveis:**
  * `instrument_id`: Código do instrumento digital com strike e expiração.
  * `amount`: Valor da operação.
  * `strike_value`: Preço do strike selecionado.
* **Casos de Uso:** Operações na modalidade Digital.
* **Exemplo de Código Python:**
```python
from ws_trading import get_buy_digital_payload

# Gera payload para compra de Opção Digital
payload_digital = get_buy_digital_payload(instrument_id="do1857A20260801D013900T1MC4031F094488", amount=10.0)
```
* **Exemplo de Retorno da Corretora:**
```json
{
  "name": "digital-option-placed",
  "msg": {
    "id": 20166393735,
    "user_id": 136879853,
    "instrument_id": "do1857A20260801D013900T1MC4031F094488"
  }
}
```

---

### `position-changed` / `positions-state` ⭐ (MENSAGEM CRÍTICA DA OPERAÇÃO)
* **Descrição:** Transmite em tempo real a evolução e o encerramento final de qualquer operação aberta (Binária ou Digital).
* **Informações Extraíveis:**
  * `status`: Status da ordem (`"open"` para em andamento ou `"closed"` para encerrada).
  * `close_reason`: Resultado final (`"win"`, `"loose"`, `"equal"`, `"expired"`).
  * `invest` / `amount`: Valor total aplicado na operação.
  * `close_profit` / `pnl`: Lucro líquido obtido (se `win`) ou perda (se `loose`).
  * `open_quote` / `close_quote`: Taxa de entrada e taxa final de fechamento.
  * `open_time` / `close_time` / `expiration_time`: Timestamps e contagem regressiva.
  * `profit_percent`: Porcentagem de rendimento (Payout no momento da entrada).
  * `direction`: Direção operada (`call` / `put`).
* **Casos de Uso:** 
  * Gestão de Banca e Martingale automático.
  * Notificações de WIN / LOSS em tempo real no Telegram/Discord.
  * Verificação exata do Payout recebido no trade.
* **Exemplo de Código Python:**
```python
from api import OpBinAPI

api = OpBinAPI()
api.connect()

# Acessa o último resultado de operação registrado
evento = api.last_position_event

if evento:
    dados = evento.get("msg", {})
    status = dados.get("status")
    resultado = dados.get("close_reason")
    lucro = dados.get("close_profit")
    
    print(f"Status: {status} | Resultado: {resultado} | Lucro: R${lucro}")
```
* **Exemplo de Retorno da Corretora:**
```json
{
  "name": "position-changed",
  "microserviceName": "portfolio",
  "msg": {
    "id": "62479a2172d2c862eedd7d7634d5278e",
    "user_id": 136879853,
    "active_id": 76,
    "status": "closed",
    "close_reason": "win",
    "invest": 10.0,
    "close_profit": 18.70,
    "pnl": 8.70,
    "open_quote": 0.981575,
    "close_quote": 0.981685,
    "open_time": 1785548360000,
    "close_time": 1785548400000
  }
}
```

---

### `history-positions` / `positions` / `orders` / `order-changed`
* **Descrição:** Retorna o histórico de todas as operações antigas realizadas pelo usuário.
* **Informações Extraíveis:**
  * Lista de operações com todas as métricas financeiras acumuladas (taxa de acerto, lucro total, prejuízo acumulado).
* **Casos de Uso:** Relatório diário de performance e auditoria do robô.
* **Exemplo de Código Python:**
```python
from api import OpBinAPI

api = OpBinAPI()
api.connect()

historico = api.positions_history
print("Histórico Posições:", historico)
```
* **Exemplo de Retorno da Corretora:**
```json
{
  "name": "history-positions",
  "msg": {
    "positions": [
      {
        "id": "62479a2172d2c862eedd7d7634d5278e",
        "active_id": 76,
        "invest": 10.0,
        "close_profit": 18.70,
        "status": "closed"
      }
    ]
  }
}
```

---

## 📊 5. MERCADO, ATIVOS E PAYOUTS (DETALHADO E COMPLETO)

### `get-instruments` / `instruments` / `instruments-list`
* **Descrição:** Retorna o catálogo detalhado e atualizado de todos os instrumentos negociáveis da plataforma (Opções Digitais, Opções Binárias, Forex, Criptomoedas, Commodities e Ações).
* **Informações Extraíveis:**
  * `asset_id` / `active_id`: ID numérico do ativo (ex: `1` = EURUSD, `76` = EURUSD-OTC, `1857` = XAUUSD-OTC/Ouro).
  * `instrument_type`: Categoria do instrumento (`"digital-option"`, `"binary-option"`, `"turbo-option"`, `"marginal-forex"`, `"marginal-crypto"`).
  * `expiration`: Timestamp Unix com o momento exato de expiração do lote de opções (ex: `1785548340`).
  * `period`: Duração da opção em segundos (`60` = M1, `300` = M5, `900` = M15).
  * `quote`: Preço/cotação atual de referência do ativo no servidor.
  * `volatility`: Índice de volatilidade instantânea do mercado.
  * `digital_option_trading_group_id`: Identificador do grupo de negociação de opções digitais (ex: `"191_0"`).
  * `data` (Array de Strikes):
    * `strike`: Valor exato do preço de exercício (Strike Price), ex: `"4031.094488"`.
    * `symbol`: Código alfanumérico único para envio da ordem (ex: `"do1857A20260801D013900T1MC4031F094488"`).
    * `direction`: Direção associada ao symbol (`"call"` para alta ou `"put"` para baixa).
* **Casos de Uso:** 
  * Descobrir a lista de símbolos de ordens (`symbol`) ativos necessários para disparar entradas em Opções Digitais.
  * Mapear todos os Strikes disponíveis ao redor do preço atual (`spot price`) para escolher o melhor Strike (At The Money ou In The Money).
* **Exemplo de Código Python:**
```python
from api import OpBinAPI

api = OpBinAPI()
api.connect()

instrumentos = api.instruments
print(instrumentos)
```
* **Exemplo de Retorno da Corretora:**
```json
{
  "name": "instruments",
  "msg": {
    "instruments": [
      {
        "asset_id": 1857,
        "instrument_type": "digital-option",
        "expiration": 1785548340,
        "period": 60,
        "quote": 4038.8103,
        "volatility": 2.5719,
        "data": [
          {
            "strike": "4031.094488",
            "symbol": "do1857A20260801D013900T1MC4031F094488",
            "direction": "call"
          }
        ]
      }
    ]
  }
}
```

---

### `underlying-list` / `underlying-list-changed`
* **Descrição:** Estrutura completa de ativos subjacentes com informações de precisão decimal, horários de abertura/fechamento e ícones.
* **Informações Extraíveis:**
  * `active_id`: ID numérico do ativo.
  * `name`: Nome amigável da paridade/ativo (ex: `"EURUSD"`, `"BTCUSD"`, `"AMAZON"`).
  * `active_type`: Tipo do ativo (`"marginal-forex"`, `"marginal-crypto"`, `"marginal-cfd"`, `"digital-option"`).
  * `active_group_id`: Grupo do ativo (`1` = Forex, `2` = Ações, `4` = Índices, `16` = Cripto).
  * `is_suspended` (`True`/`False`): Indica se o mercado está suspenso ou bloqueado no momento.
  * `precision` / `display_precision` / `calculation_precision`: Número de casas decimais para exibição e cálculos (ex: `5` casas para EURUSD, `3` casas para BTCUSD).
  * `schedule` (Matriz de Horários de Funcionamento):
    * `open`: Timestamp Unix de abertura da sessão de negociação.
    * `close`: Timestamp Unix de encerramento da sessão de negociação.
  * `image` / `image_prefix`: Caminho e URL para o ícone/bandeira do ativo.
  * `localization_key`: Chave de tradução do nome do ativo na interface.
* **Casos de Uso:**
  * **Verificação de Mercado Aberto/Fechado:** Checar a matriz `schedule` e `is_suspended` para impedir que o robô tente operar em um ativo fora do horário comercial.
  * **Formatação de Preços:** Utilizar a `precision` exata para arredondamento de preços antes de calcular stop loss ou take profit.
* **Exemplo de Código Python:**
```python
from api import OpBinAPI

api = OpBinAPI()
api.connect()

lista_ativos = api.underlyings
print(lista_ativos)
```
* **Exemplo de Retorno da Corretora:**
```json
{
  "name": "underlying-list",
  "msg": {
    "items": [
      {
        "active_id": 1,
        "name": "EURUSD",
        "active_type": "marginal-forex",
        "precision": 5,
        "display_precision": 5,
        "calculation_precision": 6,
        "is_suspended": false,
        "schedule": [
          {
            "open": 1785704461,
            "close": 1785715200
          }
        ]
      }
    ]
  }
}
```

---

### `active`
* **Descrição:** Mensagem individual de atualização para um ativo específico com status de visibilidade e provedor de cotações.
* **Informações Extraíveis:**
  * `id`: ID do ativo.
  * `name`: Nome comercial do ativo (ex: `"EURUSD-OTC"`, `"USDJPY-OTC"`, `"APPLE-OTC"`).
  * `group_name`: Nome da categoria.
  * `description`: Descrição legível completa (ex: `"Euro / US Dollar (OTC)"`).
  * `is_visible` (`True`/`False`): Se o ativo está visível na barra de seleção da plataforma.
  * `is_paused` (`True`/`False`): Se as negociações foram pausadas temporariamente por alta volatilidade/notícias.
  * `priority`: Ordem de prioridade na listagem da interface.
  * `quote_provider_id` / `quote_provider_name`: ID e nome do provedor de liquidez da cotação.
  * `top_traders_enabled` (`True`/`False`): Se permite a exibição do ranking dos melhores traders neste ativo.
* **Casos de Uso:**
  * Filtrar e remover ativos pausados (`is_paused == True`) ou ocultos da lista de monitoramento do robô.
* **Exemplo de Código Python:**
```python
from ws_instruments import handle_instruments

# Acessa os detalhes individuais do ativo retornado
# Ativo 76 = EURUSD-OTC
```
* **Exemplo de Retorno da Corretora:**
```json
{
  "name": "active",
  "request_id": "244",
  "msg": {
    "id": 76,
    "name": "EURUSD-OTC",
    "group_name": "Forex",
    "description": "EUR/USD (OTC)",
    "is_visible": true,
    "is_paused": false,
    "active_group_id": 1,
    "priority": 0,
    "quote_provider_id": 111,
    "top_traders_enabled": true
  }
}
```

---

### `digital-option-client-price-generated` ⭐ (CÁLCULO EM TEMPO REAL DE PAYOUT DIGITAL)
* **Descrição:** Transmissão em tempo real a cada segundo dos preços e Payouts (% de rendimento) atualizados das Opções Digitais.
* **Informações Extraíveis:**
  * `asset_id`: ID do ativo (ex: `1857`).
  * `quote_time`: Timestamp exato da cotação em nanossegundos (ex: `"1785548455000000000"`).
  * `instrument_index`: Índice de versão do catálogo de cotação.
  * `prices` (Lista com todos os Strikes e Payouts no segundo atual):
    * `strike`: Valor do strike (ex: `"4030.444335"`).
    * `call` / `put`:
      * `symbol`: Código do instrumento para execução da ordem.
      * `price` (Preço de compra do contrato de 0 a 100):
        * **Fórmula do Payout:** $$\text{Payout \%} = \frac{100 - \text{price}}{\text{price}} \times 100$$
* **Casos de Uso:**
  * **Cálculo de Payout Dinâmico:** Descobrir exatamente quanto a corretora está pagando (% rendimento) em cada Strike no milissegundo exato antes de clicar.
  * **Filtro de Payout Mínimo:** Configurar o robô para só efetuar a entrada se o Payout da Opção Digital for superior a um valor pré-definido (ex: mínimo 80%).
* **Exemplo de Código Python:**
```python
# Cálculo do Payout com base na resposta de preço da opção digital
preco_contrato = 54.43
payout_calculado = ((100 - preco_contrato) / preco_contrato) * 100
print(f"Payout Atual: {payout_calculado:.2f}%")
```
* **Exemplo de Retorno da Corretora:**
```json
{
  "name": "digital-option-client-price-generated",
  "msg": {
    "asset_id": 1857,
    "prices": [
      {
        "strike": "4030.444335",
        "call": {
          "symbol": "do1857A20260801D013900T1MC4030F444335",
          "price": 54.43
        }
      }
    ]
  }
}
```

---

### `top-assets` / `top-assets-updated`
* **Descrição:** Transmite em tempo real os ativos mais negociados e populares da plataforma.
* **Informações Extraíveis:**
  * Lista dos ativos ordenados por popularidade, volume negociado e maior número de operações abertas.
* **Casos de Uso:**
  * Seleção automática inteligente: Escolher automaticamente os 3 ativos mais negociados no momento para aplicar a estratégia.
* **Exemplo de Código Python:**
```python
from api import OpBinAPI

api = OpBinAPI()
api.connect()

top_ativos = api.top_assets
print("Top Ativos:", top_ativos)
```
* **Exemplo de Retorno da Corretora:**
```json
{
  "name": "top-assets",
  "msg": {
    "assets": [
      {
        "active_id": 76,
        "volume": 1250400,
        "popularity": 1
      }
    ]
  }
}
```

---

### `trading-params` / `overnight-fee` / `presets`
* **Descrição:** Parâmetros operacionais e limites financeiros aplicados pela corretora.
* **Informações Extraíveis:**
  * `min_deal_amount`: Valor mínimo permitido para abertura de ordem na moeda da conta (ex: R$ 2,00 ou $ 1,00).
  * `max_deal_amount`: Valor máximo permitido por operação.
  * `leverage` / `multipliers`: Alavancagens permitidas (x50, x100, x500) para Forex/Cripto.
  * `overnight_fee`: Taxas de overnight/swap cobradas por manter posições abertas de um dia para o outro.
* **Casos de Uso:**
  * Validar o valor do lote/entrada do robô antes do disparo para evitar rejeições por valor abaixo do mínimo ou acima do limite da conta.
* **Exemplo de Retorno da Corretora:**
```json
{
  "name": "trading-params",
  "msg": {
    "min_deal_amount": 1.0,
    "max_deal_amount": 20000.0,
    "default_leverage": 100
  }
}
```

---

## 👤 6. PERFIL E CONFIGURAÇÕES DE USUÁRIO

### `get-profile` / `profile` / `user-profile-client`
* **Descrição:** Retorna todos os dados da conta do usuário logado.
* **Informações Extraíveis:**
  * `id`: ID do usuário.
  * `email`, `first_name`, `last_name`: Dados cadastrais.
  * `currency`: Moeda nativa da conta.
  * `kyc_confirmed`: Status de verificação de documentos.
* **Casos de Uso:** Exibir o nome do usuário e validar o status da conta.
* **Exemplo de Código Python:**
```python
from api import OpBinAPI

api = OpBinAPI()
api.connect()

perfil = api.profile_info
print("Dados do Usuário:", perfil)
```
* **Exemplo de Retorno da Corretora:**
```json
{
  "name": "profile",
  "msg": {
    "isSuccessful": true,
    "result": {
      "id": 136879853,
      "email": "izio.silva@outlook.com",
      "first_name": "Manoel",
      "currency": "USD",
      "kyc_confirmed": true
    }
  }
}
```

---

## 💬 7. CHAT E CONTEÚDO AUXILIAR

### `chat-message` / `chat-room` / `leaderboard-position`
* **Descrição:** Atualizações do chat público e classificação no ranking da corretora.
* **Informações Extraíveis:**
  * Ranking semanal de lucro no Leaderboard mundial ou do Brasil.
  * Mensagens do chat oficial.
* **Casos de Uso:** Exibir a posição do robô ou usuário no ranking da corretora.
* **Exemplo de Código Python:**
```python
from api import OpBinAPI

api = OpBinAPI()
api.connect()

ranking = api.leaderboard
print("Leaderboard:", ranking)
```
* **Exemplo de Retorno da Corretora:**
```json
{
  "name": "leaderboard-position",
  "msg": {
    "user_id": 136879853,
    "position": 1420,
    "score": 250.00
  }
}
```

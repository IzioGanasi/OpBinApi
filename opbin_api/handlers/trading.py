import time
from .auth import generate_request_id


def get_buy_binary_payload(
    active_id: int, 
    amount: float, 
    direction: str, 
    user_balance_id: int, 
    duration: int = 1, 
    option_type_id: int = 3,
    profit_percent: int = 85
) -> dict:
    now = int(time.time())
    expired = ((now // 60) + duration) * 60

    return {
        "name": "sendMessage",
        "request_id": generate_request_id(),
        "local_time": int(time.time() * 1000) % 100000,
        "msg": {
            "name": "binary-options.open-option",
            "version": "2.0",
            "body": {
                "user_balance_id": user_balance_id,
                "active_id": active_id,
                "option_type_id": option_type_id,
                "direction": direction.lower(),
                "expired": expired,
                "refund_value": 0,
                "price": float(amount),
                "value": float(amount),
                "profit_percent": profit_percent
            }
        }
    }


def get_buy_blitz_payload(
    active_id: int, 
    amount: float, 
    direction: str, 
    user_balance_id: int, 
    duration_seconds: int = 30,
    profit_percent: int = 82
) -> dict:
    now = int(time.time())
    expired = now + duration_seconds

    return {
        "name": "sendMessage",
        "request_id": generate_request_id(),
        "local_time": int(time.time() * 1000) % 100000,
        "msg": {
            "name": "binary-options.open-option",
            "version": "2.0",
            "body": {
                "user_balance_id": user_balance_id,
                "active_id": active_id,
                "option_type_id": 12,
                "direction": direction.lower(),
                "expired": expired,
                "refund_value": 0,
                "price": float(amount),
                "value": float(amount),
                "profit_percent": profit_percent,
                "expiration_size": duration_seconds
            }
        }
    }


def get_subscribe_positions_payload(position_id: str) -> dict:
    """Subscreve ao streaming de atualizações de uma posição específica do portfólio."""
    return {
        "name": "sendMessage",
        "request_id": generate_request_id(),
        "local_time": int(time.time() * 1000) % 100000,
        "msg": {
            "name": "subscribe-positions",
            "version": "1.0",
            "body": {
                "frequency": "frequent",
                "ids": [position_id]
            }
        }
    }


def get_buy_digital_payload(instrument_id: str, amount: float, user_balance_id: int) -> dict:
    return {
        "name": "sendMessage",
        "request_id": generate_request_id(),
        "local_time": int(time.time() * 1000) % 100000,
        "msg": {
            "name": "digital-options.place-digital-option",
            "version": "1.0",
            "body": {
                "instrument_id": instrument_id,
                "amount": str(amount),
                "user_balance_id": user_balance_id
            }
        }
    }


def handle_position_changed(router, data: dict):
    """
    Normaliza e transmite eventos de mudança de posição recebidos do WebSocket.
    Subscreve ao streaming da ordem aberta e notifica o encerramento oficial (WIN/LOSS/EMPATE).
    """
    pos_msg = data.get("msg", {})
    if not isinstance(pos_msg, dict):
        return

    raw_evt = pos_msg.get("raw_event", {})
    bo_evt = raw_evt.get("binary_options_option_changed1") or raw_evt.get("digital_option_changed1") or {}

    status = pos_msg.get("status") or bo_evt.get("status")
    pos_id = pos_msg.get("id") or pos_msg.get("external_id") or bo_evt.get("option_id")
    direction = pos_msg.get("direction") or bo_evt.get("direction")
    amount = pos_msg.get("invest") or bo_evt.get("amount") or 10.0
    result = pos_msg.get("close_reason") or bo_evt.get("result")
    pnl = pos_msg.get("pnl") if pos_msg.get("pnl") is not None else bo_evt.get("profit_amount", 0.0)

    open_price = float(pos_msg.get("open_quote") or bo_evt.get("value") or 0.0)
    close_price = float(pos_msg.get("close_quote") or bo_evt.get("expiration_value") or 0.0)

    # Se a ordem acabou de ser aberta, envia a subscrição de monitoramento de portfólio
    if status == "open" and pos_msg.get("id"):
        router.send(get_subscribe_positions_payload(pos_msg.get("id")))

    normalized_position = {
        "id": pos_id,
        "status": status,          # "open" ou "closed"
        "result": result,          # "win", "loose" ou "equal"
        "direction": direction,    # "call" ou "put"
        "amount": amount,
        "pnl": pnl,
        "open_price": open_price,
        "close_price": close_price,
        "raw": pos_msg
    }

    if router.api:
        if status == "closed" and pos_id in router.api.active_trades:
            del router.api.active_trades[pos_id]

        router.api._emit_position(normalized_position)


def handle_option(router, data: dict):
    """
    Processa mensagens relativas a ordens (option / option-rejected).
    Notifica a abertura imediata e registra a ordem ativa para monitoramento de vencimento.
    """
    option_msg = data.get("msg", {})
    status = data.get("status")
    
    if router.api:
        router.api.last_option_event = data
        
        # Notifica e registra a abertura da ordem (Status 2000 ou "2000")
        if (status == 2000 or str(status) == "2000") and isinstance(option_msg, dict):
            pos_id = option_msg.get("id")
            direction = option_msg.get("direction")
            price = float(option_msg.get("price", 10.0))

            val = option_msg.get("value")
            exp_val = option_msg.get("exp_value")

            open_price = 0.0
            if isinstance(val, (int, float)) and val > 100:
                open_price = float(val)
            elif isinstance(val, (int, float)) and val > 0 and float(val) != price:
                open_price = float(val)
            elif isinstance(exp_val, (int, float)) and exp_val > 1000:
                open_price = float(exp_val) / 100000.0 if exp_val > 100000 else float(exp_val)

            if open_price <= 0.0 or open_price == price:
                open_price = getattr(router.api, "last_seen_price", 0.0)
            
            last_att = getattr(router.api, "last_buy_attempt", {})
            opt_mode = last_att.get("option_type", "blitz")
            dur = last_att.get("duration_seconds", 30) if opt_mode == "blitz" else (last_att.get("duration", 1) * 60)
            payout = last_att.get("payout") or router.api.get_payout(option_msg.get("act", 76), opt_mode)

            # Registra a ordem no rastreador em tempo real da API
            router.api.active_trades[pos_id] = {
                "id": pos_id,
                "active_id": option_msg.get("act", 76),
                "direction": direction,
                "amount": price,
                "open_price": open_price,
                "expiration_time": time.time() + dur,
                "payout": payout
            }

            router.api._emit_position({
                "id": pos_id,
                "status": "open",
                "direction": direction,
                "amount": price,
                "open_price": open_price,
                "result": None
            })

        # Se a ordem foi recusada por alteração da taxa de comissão/lucro da corretora (Status 4117)
        elif (status == 4117 or str(status) == "4117") and isinstance(option_msg, dict):
            result = option_msg.get("result", {})
            actual_comm = result.get("actual_commission", {})
            act_id = actual_comm.get("active_id")
            comm = actual_comm.get("commission")
            opt_type_id = actual_comm.get("option_type")

            if act_id and comm is not None:
                new_payout = 100 - int(comm)
                if opt_type_id == 12:
                    router.api.blitz_payouts[act_id] = new_payout
                else:
                    router.api.payouts[act_id] = new_payout
                
                # Auto-Retry Instantâneo
                last_attempt = getattr(router.api, "last_buy_attempt", {})
                if last_attempt:
                    opt_mode = last_attempt.get("option_type", "blitz")
                    amt = last_attempt.get("amount", 10.0)
                    dir_str = last_attempt.get("direction", "call")
                    dur = last_attempt.get("duration_seconds", 30) if opt_mode == "blitz" else last_attempt.get("duration", 1)
                    
                    router.api.buy(active_id=act_id, amount=amt, direction=dir_str, option_type=opt_mode, duration=dur)

        elif isinstance(option_msg, dict):
            is_successful = option_msg.get("isSuccessful", True)
            if not is_successful:
                reason = option_msg.get("reason") or option_msg.get("message") or "Motivo desconhecido"
                print(f"\n[!] REJEITADO PELA CORRETORA: {reason}\n")


def handle_digital_option_placed(router, data: dict):
    digital_data = data.get("msg", {})
    if router.api:
        router.api.last_digital_placed = digital_data


def handle_history_positions(router, data: dict):
    """
    Processa posições enviadas pelo serviço portfolio (positions-state ou positions).
    """
    history = data.get("msg", {})
    if router.api:
        router.api.positions_history = history
        if isinstance(history, dict) and "positions" in history:
            for pos in history.get("positions", []):
                pos_id = pos.get("id")
                status = pos.get("status") or ("closed" if pos.get("expires_in") == 0 else "open")
                result = pos.get("close_reason") or ("win" if float(pos.get("pnl", 0)) > 0 else ("loose" if float(pos.get("pnl", 0)) < 0 else None))
                if status == "closed" and pos_id:
                    if pos_id in router.api.active_trades:
                        del router.api.active_trades[pos_id]
                    router.api._emit_position({
                        "id": pos_id,
                        "status": "closed",
                        "result": result,
                        "pnl": float(pos.get("pnl", 0.0)),
                        "amount": float(pos.get("margin", 10.0))
                    })

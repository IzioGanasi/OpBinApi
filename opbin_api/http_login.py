import requests
from typing import Optional
from .config import IQ_IDENTIFIER, IQ_PASSWORD, IQ_LOGIN_URL


def get_iq_ssid(identifier: Optional[str] = None, password: Optional[str] = None) -> Optional[str]:
    """
    Efetua a autenticação HTTP na corretora com headers de navegador e retorna o token SSID.
    """
    email = identifier or IQ_IDENTIFIER
    pwd = password or IQ_PASSWORD

    if not email or not pwd:
        raise ValueError("Identificador (e-mail) e senha devem ser fornecidos ou configurados no .env")

    session = requests.Session()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "Accept": "*/*",
        "Origin": "https://iqoption.com",
        "Referer": "https://iqoption.com/"
    }

    payload = {
        "identifier": email,
        "password": pwd
    }

    try:
        response = session.post(IQ_LOGIN_URL, json=payload, headers=headers, timeout=15)
        response.raise_for_status()

        data = response.json()
        ssid = data.get("ssid")

        if not ssid:
            ssid = session.cookies.get("ssid") or response.cookies.get("ssid")

        if ssid:
            print("[+] Autenticação realizada com sucesso!")
            return ssid
        else:
            print("[-] Falha ao obter SSID. Resposta do servidor:", data)
            return None

    except requests.exceptions.RequestException as e:
        print(f"[-] Erro de conexão durante o login: {e}")
        return None

import os
from pathlib import Path
from dotenv import load_dotenv

# Procura o arquivo .env em múltiplas localizações possíveis
possible_env_paths = [
    Path(__file__).resolve().parent.parent / ".env",
    Path.cwd() / ".env",
    Path.cwd() / "main_api" / ".env"
]

env_loaded = False
for p in possible_env_paths:
    if p.exists():
        load_dotenv(dotenv_path=p)
        env_loaded = True
        break

if not env_loaded:
    load_dotenv()

IQ_IDENTIFIER = os.getenv("IQ_IDENTIFIER", "")
IQ_PASSWORD = os.getenv("IQ_PASSWORD", "")
IQ_LOGIN_URL = os.getenv("IQ_LOGIN_URL", "https://auth.iqoption.com/api/v2/login")
WS_URL = os.getenv("WS_URL", "wss://ws.iqoption.com/echo/websocket")

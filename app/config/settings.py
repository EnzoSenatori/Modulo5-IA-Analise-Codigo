import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
LLM_MODELO: str = os.getenv("LLM_MODELO", "gemini-2.0-flash")
LLM_TIMEOUT_S: int = int(os.getenv("LLM_TIMEOUT_S", "20"))

# Webhook + integracao GitHub (US IA-11)
GITHUB_WEBHOOK_SECRET: str = os.getenv("GITHUB_WEBHOOK_SECRET", "")
GITHUB_API_BASE: str = os.getenv("GITHUB_API_BASE", "https://api.github.com")
GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")  # token PAT para chamar Issues e Contents API
GITHUB_TIMEOUT_S: int = int(os.getenv("GITHUB_TIMEOUT_S", "10"))
WEBHOOKS_SQLITE_PATH: str = os.getenv("WEBHOOKS_SQLITE_PATH", "ia_webhooks.db")
# "github" = chama API real; "fake" = adapter local pra testes/dev sem rede.
ADAPTADOR_GITHUB: str = os.getenv("ADAPTADOR_GITHUB", "github")
ADAPTADOR_NOTIFICADOR_PR: str = os.getenv("ADAPTADOR_NOTIFICADOR_PR", "github")

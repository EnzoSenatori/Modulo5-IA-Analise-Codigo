import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
LLM_MODELO: str = os.getenv("LLM_MODELO", "gemini-2.0-flash")
LLM_TIMEOUT_S: int = int(os.getenv("LLM_TIMEOUT_S", "20"))

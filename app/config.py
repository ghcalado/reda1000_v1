"""
config.py — Configuracoes centralizadas do RedacaoAI.
"""

import os
from typing import Final
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY: Final[str] = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL: Final[str] = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TEMPERATURE: Final[float] = float(os.getenv("OPENAI_TEMPERATURE", "0.4"))

MAX_CORRECOES_SISTEMA_DIA: Final[int] = int(os.getenv("MAX_CORRECOES_SISTEMA_DIA", "50"))
MAX_CORRECOES_USUARIO_DIA: Final[int] = int(os.getenv("MAX_CORRECOES_USUARIO_DIA", "3"))

CHROMA_PATH: Final[str] = os.getenv("CHROMA_PATH", "./chroma_db")
COLLECTION_NAME: Final[str] = os.getenv("COLLECTION_NAME", "criterios_enem")
EMBED_MODEL: Final[str] = os.getenv("EMBED_MODEL", "text-embedding-3-small")
TOP_K: Final[int] = int(os.getenv("TOP_K", "4"))

BASE_DIR: Final[str] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR: Final[str] = os.path.join(BASE_DIR, "data")
CRITERIA_DIR: Final[str] = os.path.join(DATA_DIR, "criteria")

def validar_configuracoes() -> None:
    if not OPENAI_API_KEY:
        raise ValueError("ERRO CRITICO: OPENAI_API_KEY ausente nas variaveis de ambiente.")

validar_configuracoes()

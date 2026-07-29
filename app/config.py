"""
config.py — Configuracoes centralizadas do RedacaoAI (Groq + HuggingFace).
"""

import os
from typing import Final
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY: Final[str] = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL: Final[str] = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_VISION_MODEL: Final[str] = os.getenv("GROQ_VISION_MODEL", "llama-3.2-90b-vision-preview")
LLM_TEMPERATURE: Final[float] = float(os.getenv("LLM_TEMPERATURE", "0.4"))

MAX_CORRECOES_SISTEMA_DIA: Final[int] = int(os.getenv("MAX_CORRECOES_SISTEMA_DIA", "50"))
MAX_CORRECOES_USUARIO_DIA: Final[int] = int(os.getenv("MAX_CORRECOES_USUARIO_DIA", "3"))

CHROMA_PATH: Final[str] = os.getenv("CHROMA_PATH", "./chroma_db")
COLLECTION_NAME: Final[str] = os.getenv("COLLECTION_NAME", "criterios_enem")
EMBED_MODEL: Final[str] = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")
TOP_K: Final[int] = int(os.getenv("TOP_K", "4"))

BASE_DIR: Final[str] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR: Final[str] = os.path.join(BASE_DIR, "data")
CRITERIA_DIR: Final[str] = os.path.join(DATA_DIR, "criteria")

def validar_configuracoes() -> None:
    if not GROQ_API_KEY:
        raise ValueError("ERRO CRITICO: GROQ_API_KEY ausente nas variaveis de ambiente.")

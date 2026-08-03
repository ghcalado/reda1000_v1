
import os
import sys
from pathlib import Path

import pytest

# Garante variáveis de ambiente mínimas ANTES de qualquer import de app.*,
# já que app/config.py lê o ambiente no momento do import (load_dotenv()).
os.environ.setdefault("GROQ_API_KEY", "chave-de-teste-fake")
os.environ.setdefault("GROQ_MODEL", "llama-3.3-70b-versatile")
os.environ.setdefault("GROQ_VISION_MODEL", "llama-3.2-90b-vision-preview")
os.environ.setdefault("SUPABASE_URL", "")
os.environ.setdefault("SUPABASE_ANON_KEY", "")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "")
os.environ.setdefault("SUPABASE_JWT_SECRET", "segredo-de-teste-fake")
os.environ.setdefault("MAX_CORRECOES_USUARIO_DIA", "3")
os.environ.setdefault("MAX_CORRECOES_SISTEMA_DIA", "50")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def resultado_correcao_valido() -> dict:
    """Um JSON de correção plausível, no formato que o LLM deveria devolver."""
    return {
        "nota_total": 880,
        "fuga_tema": False,
        "condicao_anulacao": "Nenhuma",
        "analise_geral": "Redação bem estruturada, com bons argumentos.",
        "notas": {
            "C1": {"nota": 160, "pontos_fortes": ["Boa norma culta"], "pontos_melhorar": []},
            "C2": {"nota": 180, "pontos_fortes": ["Compreendeu o tema"], "pontos_melhorar": []},
            "C3": {"nota": 180, "pontos_fortes": ["Boa organização"], "pontos_melhorar": []},
            "C4": {"nota": 180, "pontos_fortes": ["Coesão adequada"], "pontos_melhorar": []},
            "C5": {"nota": 180, "pontos_fortes": ["Proposta de intervenção clara"], "pontos_melhorar": []},
        },
        "prioridade_estudo": "C1",
    }

"""
server.py — Ponto de entrada do backend Web (FastAPI) para o RedacaoAI.
Execute com: uvicorn server:app --reload
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

app = FastAPI(
    title="RedaçãoAI API",
    description="Motor de correção de redações ENEM com LangGraph e LLaMA 3",
    version="1.0.0"
)

# Configuração CORS Segura
# Permite acesso do localhost no desenvolvimento. Em producao, exige o dominio oficial.
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
origens_permitidas = [frontend_url]
if frontend_url != "http://localhost:3000":
    origens_permitidas.append("http://localhost:3000") # Mantem dev rodando

app.add_middleware(
    CORSMiddleware,
    allow_origins=origens_permitidas,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra as rotas (inclui o /api/v1/corrigir/texto e /api/v1/corrigir/foto)
app.include_router(router)

@app.get("/health")
async def health_check():
    return {
        "status": "online",
        "message": "O motor RedacaoAI está ativo e aguardando submissões.",
        "modelos": {
            "texto": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            "visao": os.getenv("GROQ_VISION_MODEL", "llama-3.2-90b-vision-preview")
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)

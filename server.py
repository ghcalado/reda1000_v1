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
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:8000")
origens_permitidas = [frontend_url]
if frontend_url != "http://localhost:8000":
    origens_permitidas.append("http://localhost:8000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origens_permitidas,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra as rotas (inclui o /api/v1/corrigir/texto e /api/v1/corrigir/foto)
app.include_router(router)

from fastapi.responses import FileResponse

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

# Servindo o Frontend de forma explicita (Evita erro 404 do StaticFiles puro)
@app.get("/")
async def serve_index():
    response = FileResponse("frontend/index.html")
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.get("/{file_name}")
async def serve_file(file_name: str):
    # Protecao contra path traversal
    if ".." in file_name or "/" in file_name:
        return FileResponse("frontend/index.html")
        
    if os.path.exists(f"frontend/{file_name}"):
        media_type = "text/html"
        if file_name.endswith(".js"):
            media_type = "application/javascript"
        elif file_name.endswith(".css"):
            media_type = "text/css"
            
        response = FileResponse(f"frontend/{file_name}", media_type=media_type)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return response
    
    response = FileResponse("frontend/index.html")
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)

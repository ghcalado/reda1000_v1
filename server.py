import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse

from app.api.routes import router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.corrector import ServicoCorrecao
    from app.ocr import ExtratorVisao

    app.state.servico_correcao = None
    app.state.extrator_visao = None

    try:
        app.state.servico_correcao = ServicoCorrecao()
        app.state.extrator_visao = ExtratorVisao()
    except Exception as e:
        logger.error("Falha na inicializacao dos servicos: %s", e)

    yield


app = FastAPI(
    title="RedaçãoAI API",
    description="Motor de correção de redações ENEM com LangGraph e LLaMA 3",
    version="1.0.0",
    lifespan=lifespan,
)

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

app.include_router(router)


@app.get("/health")
async def health_check():

    servicos_ok = (
        app.state.servico_correcao is not None
        and app.state.extrator_visao is not None
    )

    return {
        "status": "online" if servicos_ok else "degraded",
        "message": (
            "O motor RedacaoAI está ativo e aguardando submissões."
            if servicos_ok
            else "O servidor está de pé, mas os serviços de correção/OCR falharam "
            "ao iniciar (verifique GROQ_API_KEY nas variáveis de ambiente)."
        ),
        "servicos": {
            "correcao": app.state.servico_correcao is not None,
            "ocr": app.state.extrator_visao is not None,
        },
        "modelos": {
            "texto": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            "visao": os.getenv("GROQ_VISION_MODEL", "llama-3.2-90b-vision-preview"),
        },
    }


@app.get("/")
async def serve_index():
    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY", "")

    with open("frontend/index.html", "r", encoding="utf-8") as f:
        html = f.read()

    meta_tags = (
        f'<meta name="supabase-url" content="{supabase_url}">\n'
        f'    <meta name="supabase-anon-key" content="{supabase_anon_key}">'
    )
    html = html.replace("</head>", f"    {meta_tags}\n</head>", 1)

    response = HTMLResponse(content=html)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.get("/{file_path:path}")
async def serve_static(file_path: str):
    if ".." in file_path:
        response = FileResponse("frontend/index.html")
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return response

    candidate = os.path.join("frontend", file_path)
    if os.path.isfile(candidate):
        ext = os.path.splitext(file_path)[1].lower()
        mime_map = {
            ".js": "application/javascript",
            ".css": "text/css",
            ".html": "text/html",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
            ".svg": "image/svg+xml",
            ".ico": "image/x-icon",
        }
        media_type = mime_map.get(ext, "application/octet-stream")
        response = FileResponse(candidate, media_type=media_type)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return response

    response = FileResponse("frontend/index.html")
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)

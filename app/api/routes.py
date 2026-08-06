import tempfile
import os
import re
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Query, Request
from app.api.schemas import RedacaoRequest, RedacaoResponse, FotoCorrecaoResponse
from app.ocr import EXTENSOES_SUPORTADAS
from app.auth import verificar_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1")

_TAMANHO_MAX_UPLOAD_BYTES = 20 * 1024 * 1024


@router.post("/corrigir/texto", response_model=RedacaoResponse)
async def corrigir_texto(
    request_data: RedacaoRequest,
    request: Request,
    usuario_id: str = Depends(verificar_token),
):
    servico_correcao = request.app.state.servico_correcao
    if servico_correcao is None:
        raise HTTPException(status_code=503, detail="Servico de correcao indisponivel. Verifique a GROQ_API_KEY.")

    if not request_data.texto_redacao.strip():
        raise HTTPException(status_code=400, detail="O texto da redação não pode ser vazio.")

    try:
        resultado_json = servico_correcao.corrigir_redacao(request_data.tema, request_data.texto_redacao, usuario_id)
        return resultado_json
    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        logger.exception("Erro interno ao processar redacao de texto: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao processar a redação. Tente novamente em instantes.",
        )


@router.post("/corrigir/foto", response_model=FotoCorrecaoResponse)
async def corrigir_foto(
    request: Request,
    tema: str = Form(..., description="O tema da redação"),
    arquivo: UploadFile = File(..., description="Foto da redação manuscrita (JPG, PNG)"),
    usuario_id: str = Depends(verificar_token),
):
    servico_correcao = request.app.state.servico_correcao
    extrator_visao = request.app.state.extrator_visao

    if servico_correcao is None or extrator_visao is None:
        raise HTTPException(status_code=503, detail="Servico de correcao indisponivel. Verifique a GROQ_API_KEY.")

    extensao_original = Path(arquivo.filename or "").suffix.lower()
    extensao_segura = re.sub(r"[^a-z0-9.]", "", extensao_original)
    if extensao_segura not in EXTENSOES_SUPORTADAS:
        raise HTTPException(
            status_code=400,
            detail=f"Formato de arquivo não suportado. Use: {', '.join(sorted(EXTENSOES_SUPORTADAS))}",
        )

    if arquivo.size is not None and arquivo.size > _TAMANHO_MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Arquivo muito grande ({arquivo.size / 1024 / 1024:.1f} MB). Máximo: 20 MB.",
        )

    tmp_path = None
    try:
        conteudo = await arquivo.read()
        if len(conteudo) > _TAMANHO_MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"Arquivo muito grande ({len(conteudo) / 1024 / 1024:.1f} MB). Máximo: 20 MB.",
            )

        with tempfile.NamedTemporaryFile(delete=False, suffix=extensao_segura) as tmp:
            tmp.write(conteudo)
            tmp_path = tmp.name

        texto_transcrito = extrator_visao.transcrever(tmp_path)

        if not texto_transcrito.strip():
            raise HTTPException(status_code=400, detail="Não foi possível ler nenhum texto na imagem.")

        resultado_json = servico_correcao.corrigir_redacao(tema, texto_transcrito, usuario_id)

        return {
            "texto_reconhecido": texto_transcrito,
            "correcao": resultado_json,
        }

    except HTTPException:
        raise
    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        logger.exception("Erro no processamento da foto: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Erro ao processar a imagem enviada. Tente novamente em instantes.",
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.get("/historico")
async def buscar_historico(
    request: Request,
    limite: int = Query(default=10, ge=1, le=100),
    usuario_id: str = Depends(verificar_token),
):
    servico_correcao = request.app.state.servico_correcao
    if servico_correcao is None or servico_correcao.db.cliente is None:
        raise HTTPException(status_code=503, detail="Banco de dados indisponível no momento.")

    return servico_correcao.db.buscar_historico(usuario_id, limite)

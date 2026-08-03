import tempfile
import os
import re
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from app.api.schemas import RedacaoRequest, RedacaoResponse, FotoCorrecaoResponse
from app.corrector import ServicoCorrecao
from app.ocr import ExtratorVisao, EXTENSOES_SUPORTADAS
from app.auth import verificar_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1")

servico_correcao = None
extrator_visao = None

try:
    servico_correcao = ServicoCorrecao()
    extrator_visao = ExtratorVisao()
except Exception as e:
    logger.error("Falha na inicializacao dos servicos: %s", e)

@router.post("/corrigir/texto", response_model=RedacaoResponse)
async def corrigir_texto(request: RedacaoRequest, usuario_id: str = Depends(verificar_token)):
    """
    Recebe uma redação em formato de texto digitado e devolve o JSON com a correção estruturada.
    """
    if servico_correcao is None:
        raise HTTPException(status_code=503, detail="Servico de correcao indisponivel. Verifique a GROQ_API_KEY.")

    if not request.texto_redacao.strip():
        raise HTTPException(status_code=400, detail="O texto da redação não pode ser vazio.")
        
    try:
        resultado_json = servico_correcao.corrigir_redacao(request.tema, request.texto_redacao, usuario_id)
        return resultado_json
    except RuntimeError as e:
        # Erros esperados (ex: limite diário atingido) podem ser expostos ao usuário.
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        # Nunca expor detalhes internos (stack trace, mensagens de libs) ao cliente.
        logger.exception("Erro interno ao processar redacao de texto: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao processar a redação. Tente novamente em instantes."
        )

@router.post("/corrigir/foto", response_model=FotoCorrecaoResponse)
async def corrigir_foto(
    tema: str = Form(..., description="O tema da redação"),
    arquivo: UploadFile = File(..., description="Foto da redação manuscrita (JPG, PNG)"),
    usuario_id: str = Depends(verificar_token)
):
    """
    Recebe uma foto da redação (upload), usa OCR multimodal para transcrever e envia para correção.
    """
    if servico_correcao is None or extrator_visao is None:
        raise HTTPException(status_code=503, detail="Servico de correcao indisponivel. Verifique a GROQ_API_KEY.")

    # Sanitiza a extensao do arquivo enviado: nunca confiar no nome bruto do cliente
    # (poderia conter "/", ".." ou outros caracteres para escapar do diretorio temporario).
    extensao_original = Path(arquivo.filename or "").suffix.lower()
    extensao_segura = re.sub(r"[^a-z0-9.]", "", extensao_original)
    if extensao_segura not in EXTENSOES_SUPORTADAS:
        raise HTTPException(
            status_code=400,
            detail=f"Formato de arquivo não suportado. Use: {', '.join(sorted(EXTENSOES_SUPORTADAS))}"
        )

    tmp_path = None
    try:
        # Salva o arquivo temporariamente para a Groq Vision conseguir ler o path local.
        # O sufixo usado é controlado (apenas a extensão validada), nunca o nome bruto do cliente.
        with tempfile.NamedTemporaryFile(delete=False, suffix=extensao_segura) as tmp:
            conteudo = await arquivo.read()
            tmp.write(conteudo)
            tmp_path = tmp.name

        # Transcreve a caligrafia
        texto_transcrito = extrator_visao.transcrever(tmp_path)
        
        # Realiza a correcao
        if not texto_transcrito.strip():
            raise HTTPException(status_code=400, detail="Não foi possível ler nenhum texto na imagem.")
            
        resultado_json = servico_correcao.corrigir_redacao(tema, texto_transcrito, usuario_id)
        
        return {
            "texto_reconhecido": texto_transcrito,
            "correcao": resultado_json
        }
        
    except HTTPException:
        raise
    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        logger.exception("Erro no processamento da foto: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Erro ao processar a imagem enviada. Tente novamente em instantes."
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

@router.get("/historico")
async def buscar_historico(limite: int = 10, usuario_id: str = Depends(verificar_token)):
    """
    Retorna as últimas redações enviadas pelo aluno.
    """
    if servico_correcao is None or servico_correcao.db.cliente is None:
        raise HTTPException(status_code=503, detail="Banco de dados indisponível no momento.")
        
    return servico_correcao.db.buscar_historico(usuario_id, limite)

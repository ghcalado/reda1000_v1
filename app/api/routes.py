import tempfile
import os
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from app.api.schemas import RedacaoRequest, RedacaoResponse, FotoCorrecaoResponse
from app.corrector import ServicoCorrecao
from app.ocr import ExtratorVisao
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno ao processar redação: {str(e)}")

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

    tmp_path = None
    try:
        # Salva o arquivo temporariamente para a Groq Vision conseguir ler o path local
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{arquivo.filename}") as tmp:
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no processamento da foto: {str(e)}")
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

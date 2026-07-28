"""
rag.py — Pipeline de Recuperacao de Informacao.
"""

import logging
from typing import Optional

from app.config import COLLECTION_NAME, TOP_K
from app.prompts import INSTRUCOES_COMPETENCIAS

logger = logging.getLogger(__name__)

class PipelineRAG:
    def __init__(self) -> None:
        logger.info("Inicializando Pipeline RAG...")
        self._vectordb_conectado = False
        
    def recuperar_criterios_oficiais(self, tema: str) -> str:
        if self._vectordb_conectado:
            pass
            
        logger.info("Recuperando criterios base (Fallback estrutural RAG)")
        contexto_base = "\n\n".join(INSTRUCOES_COMPETENCIAS.values())
        return contexto_base

    def recuperar_exemplos_similares(self, texto_redacao: str) -> Optional[str]:
        if self._vectordb_conectado:
            pass
        return None

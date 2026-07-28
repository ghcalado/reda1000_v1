"""
rag.py — Pipeline de Recuperacao de Informacao (Retrieval-Augmented Generation).
"""

import os
import logging
from typing import Optional

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from app.config import CHROMA_PATH, COLLECTION_NAME, EMBED_MODEL, TOP_K
from app.prompts import COMPETENCIA_INSTRUCTIONS

logger = logging.getLogger(__name__)

class PipelineRAG:
    def __init__(self) -> None:
        logger.info("Inicializando conexao com ChromaDB usando HuggingFace Embeddings...")
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=EMBED_MODEL
            )
            
            # Inicializa o cliente persistente do Chroma
            self.vector_store = Chroma(
                collection_name=COLLECTION_NAME,
                embedding_function=self.embeddings,
                persist_directory=CHROMA_PATH
            )
            
            # Verifica se o banco tem documentos
            count = len(self.vector_store.get()["ids"])
            self._vectordb_conectado = True
            logger.info(f"ChromaDB conectado com sucesso. Documentos na colecao: {count}")
            
        except Exception as e:
            logger.error(f"Falha ao conectar no ChromaDB: {e}")
            self._vectordb_conectado = False
        
    def recuperar_criterios_oficiais(self, tema: str) -> str:
        """
        No padrao ENEM, todas as 5 competencias sao obrigatorias, entao o RAG 
        retorna o fallback estrutural para garantir que o prompt tenha a rubrica completa.
        O ChromaDB sera usado primariamente para buscar exemplos de redacoes nota 1000
        ou regras especificas baseadas no tema.
        """
        # Sempre precisamos das 5 competencias, entao unimos os valores estaticos.
        contexto_base = "\n\n".join(COMPETENCIA_INSTRUCTIONS.values())
        return contexto_base

    def recuperar_exemplos_similares(self, texto_redacao: str) -> str:
        """
        Recupera trechos de redacoes nota 1000 similares do banco para servir de
        parametrizacao ou few-shot prompt para o modelo.
        """
        if not self._vectordb_conectado:
            return ""
            
        try:
            # Busca os TOP_K fragmentos mais similares semantica ou tematicamente
            docs = self.vector_store.similarity_search(texto_redacao, k=TOP_K)
            if not docs:
                return ""
                
            contexto_recuperado = "\n\n---\n\n".join([doc.page_content for doc in docs])
            logger.info("Exemplos recuperados do ChromaDB com sucesso.")
            return f"\n\nEXEMPLOS DE EXCELENCIA (NOTA 1000) RECUPERADOS PELO RAG:\n{contexto_recuperado}"
            
        except Exception as e:
            logger.error(f"Erro durante a busca no ChromaDB: {e}")
            return ""

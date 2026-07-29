"""
seed_db.py — Script utilitario para popular o ChromaDB com Redacoes Nota 1000.
"""

import os
import logging
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

from app.config import CHROMA_PATH, COLLECTION_NAME, EMBED_MODEL, OPENAI_API_KEY, DATA_DIR

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def popular_banco_vetorial():
    logger.info("Inicializando populacao do ChromaDB...")
    
    if not OPENAI_API_KEY:
        logger.error("Chave OPENAI_API_KEY nao encontrada. Impossivel gerar embeddings.")
        return

    embeddings = OpenAIEmbeddings(
        model=EMBED_MODEL,
        api_key=OPENAI_API_KEY
    )
    
    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_PATH
    )

    exemplos_dir = os.path.join(DATA_DIR, "redacoes_nota_1000")
    os.makedirs(exemplos_dir, exist_ok=True)
    
    arquivos = [f for f in os.listdir(exemplos_dir) if f.endswith(".txt")]
    
    if not arquivos:
        logger.warning(f"Nenhum arquivo .txt encontrado em {exemplos_dir}.")
        logger.warning("Crie arquivos .txt com redacoes nota 1000 reais para que o RAG possa recuperar exemplos.")
        return

    documentos = []
    for arquivo in arquivos:
        caminho = os.path.join(exemplos_dir, arquivo)
        with open(caminho, 'r', encoding='utf-8') as f:
            conteudo = f.read()
            # Usando o nome do arquivo (sem extensao) como tema aproximado
            tema = arquivo.replace(".txt", "").replace("_", " ").title()
            
            # Adiciona metadados uteis para filtros futuros
            doc = Document(
                page_content=f"TEMA: {tema}\n\nTEXTO NOTA 1000:\n{conteudo}",
                metadata={"tema": tema, "fonte": "oficial_inep"}
            )
            documentos.append(doc)
            
    if documentos:
        logger.info(f"Gerando embeddings para {len(documentos)} redacoes e salvando no ChromaDB...")
        vector_store.add_documents(documentos)
        logger.info("Banco populado com sucesso!")
        
if __name__ == "__main__":
    popular_banco_vetorial()

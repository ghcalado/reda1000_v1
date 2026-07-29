"""
seed.py — Utilitario de Ingestao de Dados (Ingest) no ChromaDB.
Processa cartilhas e converte PDFs para Markdown nativamente para garantir a semantica estrutural.
Usa HuggingFaceEmbeddings para vetorizacao local gratuita.
"""

import os
import logging
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import CHROMA_PATH, COLLECTION_NAME, EMBED_MODEL, DATA_DIR, CRITERIA_DIR

# Import do conversor especializado de PDF para Markdown
try:
    import pymupdf4llm
except ImportError:
    pymupdf4llm = None

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def popular_banco_vetorial():
    logger.info("Inicializando Pipeline de Ingestao do ChromaDB com HuggingFace...")
    
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    
    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_PATH
    )

    documentos_para_ingestao = []
    
    # Text Splitter otimizado para Markdown
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""]
    )

    if os.path.exists(CRITERIA_DIR):
        # 1. Processa arquivos Markdown (.md)
        arquivos_md = [f for f in os.listdir(CRITERIA_DIR) if f.endswith(".md") and not f.endswith("_convertido.md")]
        for arquivo in arquivos_md:
            caminho = os.path.join(CRITERIA_DIR, arquivo)
            with open(caminho, 'r', encoding='utf-8') as f:
                conteudo = f.read()
                chunks = text_splitter.split_text(conteudo)
                for chunk in chunks:
                    doc = Document(
                        page_content=chunk,
                        metadata={"tipo": "criterio_oficial", "arquivo": arquivo, "formato": "md"}
                    )
                    documentos_para_ingestao.append(doc)

        # 2. Processa arquivos PDF (.pdf) convertendo-os para Markdown em memoria
        arquivos_pdf = [f for f in os.listdir(CRITERIA_DIR) if f.endswith(".pdf")]
        for arquivo in arquivos_pdf:
            if not pymupdf4llm:
                logger.error("pymupdf4llm nao esta instalado. Pulo conversao de PDF.")
                continue
                
            caminho = os.path.join(CRITERIA_DIR, arquivo)
            logger.info(f"Convertendo PDF para Markdown: {arquivo}...")
            
            md_text = pymupdf4llm.to_markdown(caminho)
            caminho_backup = caminho.replace(".pdf", "_convertido.md")
            with open(caminho_backup, 'w', encoding='utf-8') as f:
                f.write(md_text)
                
            chunks = text_splitter.split_text(md_text)
            for chunk in chunks:
                doc = Document(
                    page_content=chunk,
                    metadata={"tipo": "cartilha_oficial", "arquivo": arquivo, "formato": "pdf_to_md"}
                )
                documentos_para_ingestao.append(doc)
                
        logger.info(f"Processados {len(arquivos_md)} arquivos .md e {len(arquivos_pdf)} arquivos .pdf do INEP.")
    else:
        logger.warning(f"Diretorio de criterios nao encontrado: {CRITERIA_DIR}")

    # TODO: Ingestao de Redacoes Nota 1000
    # Quando houver arquivos .txt reais em data/redacoes_nota_1000/,
    # descomentar o bloco abaixo para ingerir os exemplos no ChromaDB.
    # exemplos_dir = os.path.join(DATA_DIR, "redacoes_nota_1000")
    # arquivos_txt = [f for f in os.listdir(exemplos_dir) if f.endswith(".txt")]
    # for arquivo in arquivos_txt:
    #     caminho = os.path.join(exemplos_dir, arquivo)
    #     with open(caminho, 'r', encoding='utf-8') as f:
    #         conteudo = f.read()
    #         tema = arquivo.replace(".txt", "").replace("_", " ").title()
    #         doc = Document(
    #             page_content=f"TEMA: {tema}\n\nTEXTO NOTA 1000:\n{conteudo}",
    #             metadata={"tipo": "exemplo_1000", "tema": tema}
    #         )
    #         documentos_para_ingestao.append(doc)

    if documentos_para_ingestao:
        logger.info(f"Gerando embeddings locais (HuggingFace) para {len(documentos_para_ingestao)} blocos. Aguarde...")
        vector_store.add_documents(documentos_para_ingestao)
        logger.info("Processo de Ingestao concluido com sucesso!")
    else:
        logger.warning("Nenhum documento encontrado para ingestao.")
        
if __name__ == "__main__":
    popular_banco_vetorial()

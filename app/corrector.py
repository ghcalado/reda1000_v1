"""
corrector.py — Servico central de Correcao de Redacao.
"""

import json
import logging
from typing import Dict, Any

from langchain_core.messages import SystemMessage, HumanMessage

from app.llm import MotorConversacional
from app.rag import PipelineRAG
from app.prompts import build_prompt_correcao, SYSTEM_PROMPT_AUTOCRITICA_FEEDBACK

logger = logging.getLogger(__name__)

class ServicoCorrecao:
    def __init__(self) -> None:
        logger.info("Inicializando Servico de Correcao (com modulo de Autocritica)...")
        self.motor_llm = MotorConversacional()
        self.pipeline_rag = PipelineRAG()

    def corrigir_redacao(self, tema: str, texto_redacao: str) -> Dict[str, Any]:
        logger.info(f"Iniciando PASSO 1: Correcao base. Tema: '{tema}'")
        
        prompt_sistema = build_prompt_correcao()
        
        # Recupera exemplos similares do ChromaDB (Redacoes Nota 1000) se existirem
        exemplos_rag = self.pipeline_rag.recuperar_exemplos_similares(texto_redacao)
        
        prompt_usuario = (
            f"TEMA DA REDACAO: {tema}\n\n"
            f"TEXTO DO ALUNO:\n\"\"\"{texto_redacao}\"\"\"\n"
            f"{exemplos_rag}\n\n"
            "Avalie o texto acima e retorne o JSON estruturado."
        )

        mensagens_passo_1 = [
            SystemMessage(content=prompt_sistema),
            HumanMessage(content=prompt_usuario)
        ]

        resposta_bruta_1 = self.motor_llm.llm.invoke(mensagens_passo_1).content
        json_limpo_1 = self._limpar_markdown_json(resposta_bruta_1)
        
        logger.info("PASSO 1 Concluido. Iniciando PASSO 2: Autocritica e Refinamento...")

        prompt_reflexao = (
            "Aqui esta o JSON gerado na correcao inicial.\n"
            f"{json_limpo_1}\n\n"
            "Revise este JSON aplicando as regras de Autocritica. "
            "Se houver feedbacks sem citacao, adicione a citacao ou remova a frase generica. "
            "Retorne APENAS o novo JSON consolidado."
        )

        mensagens_passo_2 = [
            SystemMessage(content=SYSTEM_PROMPT_AUTOCRITICA_FEEDBACK),
            HumanMessage(content=prompt_reflexao)
        ]

        resposta_bruta_2 = self.motor_llm.llm.invoke(mensagens_passo_2).content
        
        return self._extrair_e_validar_json(resposta_bruta_2)

    def _limpar_markdown_json(self, texto: str) -> str:
        texto = texto.strip()
        if texto.startswith("```json"):
            texto = texto[7:]
        elif texto.startswith("```"):
            texto = texto[3:]
        if texto.endswith("```"):
            texto = texto[:-3]
        return texto.strip()

    def _extrair_e_validar_json(self, resposta_llm: str) -> Dict[str, Any]:
        texto_limpo = self._limpar_markdown_json(resposta_llm)
        try:
            dicionario = json.loads(texto_limpo)
            if "nota_total" not in dicionario or "notas" not in dicionario:
                raise ValueError("JSON retornado nao contem as chaves obrigatorias.")
            return dicionario
            
        except json.JSONDecodeError as e:
            logger.error(f"Falha ao realizar parse do JSON apos autocritica:\n{texto_limpo}")
            raise RuntimeError(f"O modelo nao retornou um JSON valido. Erro interno: {e}")

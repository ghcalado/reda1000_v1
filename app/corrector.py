"""
corrector.py — Servico central de Correcao de Redacao.
"""

import json
import logging
import time
from typing import Dict, Any

from app.llm import MotorConversacional
from app.rag import PipelineRAG
from app.prompts import build_prompt_correcao, SYSTEM_PROMPT_AUTOCRITICA_FEEDBACK

from app.database import DatabaseService

logger = logging.getLogger(__name__)

class ServicoCorrecao:
    def __init__(self) -> None:
        logger.info("Inicializando Servico de Correcao (com modulo de Autocritica)...")
        self.motor_llm = MotorConversacional()
        self.pipeline_rag = PipelineRAG()
        self.db = DatabaseService()

    def _verificar_limite(self, usuario_id: str) -> None:
        if self.db.cliente:
            self.db.verificar_limite_diario(usuario_id)
            self.db.verificar_limite_sistema()
        else:
            logger.warning("Banco offline. Rate limit ignorado.")

    def corrigir_redacao(self, tema: str, texto_redacao: str, usuario_id: str = "terminal") -> Dict[str, Any]:
        self._verificar_limite(usuario_id)

        logger.info("Iniciando correcao via LangGraph. Tema: '%s'", tema)
        inicio = time.time()

        prompt_sistema = build_prompt_correcao()
        exemplos_rag = self.pipeline_rag.recuperar_exemplos_similares(texto_redacao)

        prompt_usuario = (
            f"TEMA DA REDACAO: {tema}\n\n"
            f"TEXTO DO ALUNO:\n\"\"\"{texto_redacao}\"\"\"\n"
            f"{exemplos_rag}\n\n"
            "Avalie o texto acima e retorne o JSON estruturado."
        )

        resposta_json = self.motor_llm.executar_correcao(
            prompt_usuario=prompt_usuario,
            prompt_sistema_correcao=prompt_sistema,
            prompt_sistema_autocritica=SYSTEM_PROMPT_AUTOCRITICA_FEEDBACK
        )

        duracao = time.time() - inicio
        logger.info("Correcao finalizada em %.2f segundos.", duracao)

        resultado = self._extrair_e_validar_json(resposta_json)
        
        if self.db.cliente:
            self.db.salvar_redacao(usuario_id, tema, texto_redacao, resultado)
            
        return resultado

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
            logger.error("Falha ao realizar parse do JSON apos autocritica:\n%s", texto_limpo)
            raise RuntimeError(f"O modelo nao retornou um JSON valido. Erro interno: {e}")

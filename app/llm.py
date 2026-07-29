"""
llm.py — Modulo de abstracao do LLM e orquestracao via LangGraph (Groq).
"""

import logging
from typing import Annotated, TypedDict, Any

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from app.config import GROQ_MODEL, LLM_TEMPERATURE, GROQ_API_KEY, validar_configuracoes

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(asctime)s - %(name)s - %(message)s")
logger = logging.getLogger(__name__)

class EstadoCorrecao(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    prompt_sistema_correcao: str
    prompt_sistema_autocritica: str
    json_correcao_bruto: str
    json_final: str
    etapa: str

PROMPT_SISTEMA: str = """
Voce e o RedacaoAI, um assistente especialista em redacoes no formato ENEM/INEP.
Sua tarefa e orientar o estudante sobre as cinco competencias e os criterios de correcao.

REGRAS ESTABELECIDAS:
1. Responda exclusivamente em portugues do Brasil.
2. Seja didatico, tecnico e claro, como um professor humano experiente.
3. Se o usuario pedir para corrigir uma redacao, peca que envie o texto e o tema.
4. Jamais forneca respostas prontas de licao de casa; oriente o raciocinio.
5. Evite formatacoes desnecessarias e nao utilize emoticons em suas respostas.
"""

class MotorConversacional:
    def __init__(self) -> None:
        logger.info("Inicializando o modulo conversacional LLM (Groq)...")
        try:
            validar_configuracoes()
            self.llm = ChatGroq(
                model=GROQ_MODEL,
                temperature=LLM_TEMPERATURE,
                api_key=GROQ_API_KEY
            )
        except ValueError as e:
            logger.error("Configuracao invalida: %s", e)
            raise RuntimeError(str(e)) from e
        except Exception as e:
            logger.error("Falha ao instanciar ChatGroq.")
            raise RuntimeError(f"Erro de integracao Groq: {e}") from e

        self.grafo_correcao = self._compilar_grafo_correcao()
        logger.info("Grafo de correcao compilado com sucesso.")

    def _no_correcao(self, estado: EstadoCorrecao) -> dict[str, Any]:
        prompt_sistema = estado["prompt_sistema_correcao"]
        mensagem_usuario = estado["messages"][-1]

        mensagens = [
            SystemMessage(content=prompt_sistema),
            mensagem_usuario
        ]

        resposta = self.llm.invoke(mensagens)
        json_bruto = resposta.content

        return {
            "messages": [resposta],
            "json_correcao_bruto": json_bruto,
            "etapa": "autocritica"
        }

    def _no_autocritica(self, estado: EstadoCorrecao) -> dict[str, Any]:
        prompt_autocritica = estado["prompt_sistema_autocritica"]
        json_bruto = estado["json_correcao_bruto"]

        prompt_reflexao = (
            "Aqui esta o JSON gerado na correcao inicial.\n"
            f"{json_bruto}\n\n"
            "Revise este JSON aplicando as regras de Autocritica. "
            "Se houver feedbacks sem citacao, adicione a citacao ou remova a frase generica. "
            "Retorne APENAS o novo JSON consolidado."
        )

        mensagens = [
            SystemMessage(content=prompt_autocritica),
            HumanMessage(content=prompt_reflexao)
        ]

        resposta = self.llm.invoke(mensagens)

        return {
            "messages": [resposta],
            "json_final": resposta.content,
            "etapa": "finalizado"
        }

    def _compilar_grafo_correcao(self):
        construtor = StateGraph(EstadoCorrecao)
        construtor.add_node("correcao", self._no_correcao)
        construtor.add_node("autocritica", self._no_autocritica)
        construtor.add_edge(START, "correcao")
        construtor.add_edge("correcao", "autocritica")
        construtor.add_edge("autocritica", END)
        return construtor.compile()

    def executar_correcao(
        self,
        prompt_usuario: str,
        prompt_sistema_correcao: str,
        prompt_sistema_autocritica: str
    ) -> str:
        estado_inicial: EstadoCorrecao = {
            "messages": [HumanMessage(content=prompt_usuario)],
            "prompt_sistema_correcao": prompt_sistema_correcao,
            "prompt_sistema_autocritica": prompt_sistema_autocritica,
            "json_correcao_bruto": "",
            "json_final": "",
            "etapa": "correcao"
        }
        estado_final = self.grafo_correcao.invoke(estado_inicial)
        return estado_final["json_final"]

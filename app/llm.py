"""
llm.py — Modulo de abstracao do LLM e orquestracao conversacional.
"""

import logging
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from app.config import OPENAI_MODEL, OPENAI_TEMPERATURE, OPENAI_API_KEY

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(asctime)s - %(name)s - %(message)s")
logger = logging.getLogger(__name__)

class EstadoConversa(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

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
        logger.info("Inicializando o modulo conversacional LLM...")
        try:
            self.llm = ChatOpenAI(
                model=OPENAI_MODEL,
                temperature=OPENAI_TEMPERATURE,
                api_key=OPENAI_API_KEY
            )
        except Exception as e:
            logger.error("Falha ao instanciar ChatOpenAI.")
            raise RuntimeError(f"Erro de integracao OpenAI: {e}") from e

        self.grafo = self._compilar_grafo()
        logger.info("Grafo conversacional compilado com sucesso.")

    def _processar_interacao(self, estado: EstadoConversa) -> dict[str, list[BaseMessage]]:
        historico = estado.get("messages", [])
        
        if not historico or not isinstance(historico[0], SystemMessage):
            mensagens = [SystemMessage(content=PROMPT_SISTEMA)] + historico
        else:
            mensagens = historico

        try:
            resposta = self.llm.invoke(mensagens)
            return {"messages": [resposta]}
        except Exception as erro:
            logger.error("Erro na inferencia do LLM: %s", erro)
            falha = BaseMessage(
                content="Lamento, mas ocorreu um erro interno na comunicacao com a inteligencia artificial.",
                type="ai"
            )
            return {"messages": [falha]}

    def _compilar_grafo(self):
        construtor = StateGraph(EstadoConversa)
        construtor.add_node("chat", self._processar_interacao)
        construtor.add_edge(START, "chat")
        construtor.add_edge("chat", END)
        return construtor.compile()

    def conversar(self, entrada_usuario: str, historico_previo: list[BaseMessage] = None) -> list[BaseMessage]:
        contexto = historico_previo if historico_previo else []
        estado_inicial: EstadoConversa = {
            "messages": contexto + [HumanMessage(content=entrada_usuario)]
        }
        estado_final = self.grafo.invoke(estado_inicial)
        return estado_final["messages"]

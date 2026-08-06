import os
import logging
from typing import Optional, List, Dict, Any
from supabase import create_client, Client
from app.config import MAX_CORRECOES_USUARIO_DIA, MAX_CORRECOES_SISTEMA_DIA
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_CHAVE_LIMITE_SISTEMA = "__sistema__"

class DatabaseService:
    def __init__(self) -> None:
        url: str = os.getenv("SUPABASE_URL", "")
        key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SUPABASE_ANON_KEY", ""))
        
        if not url or not key:
            logger.warning("Supabase URL ou Key nao encontrados. Banco inativo.")
            self.cliente = None
        else:
            try:
                self.cliente: Optional[Client] = create_client(url, key)
            except Exception as e:
                logger.error("Erro ao inicializar cliente Supabase: %s", e)
                self.cliente = None

    def salvar_redacao(self, usuario_id: str, tema: str, texto: str, resultado: Dict[str, Any]) -> None:
        """Persiste a redacao e o resultado JSON no banco Supabase."""
        if not self.cliente:
            logger.warning("Supabase inativo. Redacao nao sera salva.")
            return

        dados = {
            "usuario_id": usuario_id,
            "tema": tema,
            "texto_redacao": texto,
            "resultado_json": resultado,
            "nota_final": resultado.get("nota_total", 0)
        }

        try:
            self.cliente.table("redacoes").insert(dados).execute()
            logger.info("Redacao %s salva com sucesso para o usuario %s", tema, usuario_id)
        except Exception as e:
            logger.error("Erro ao salvar redacao no banco: %s", e)

    def _registrar_tentativa_atomica(self, chave: str, limite: int) -> Optional[bool]:
        """
        Chama a funcao SQL 'registrar_tentativa_redacao' (ver scripts/sql/rate_limit.sql),
        que incrementa o contador do dia de forma ATOMICA no Postgres (via
        INSERT ... ON CONFLICT DO UPDATE ... WHERE contagem < limite) e retorna
        se a tentativa foi aceita. Isso elimina a race condition (TOCTOU) do
        modelo antigo de "contar depois decidir".

        Retorna:
            True  -> tentativa registrada, dentro do limite.
            False -> limite atingido, tentativa NAO registrada.
            None  -> a funcao RPC nao existe no banco (migracao nao aplicada);
                     caller deve decidir um fallback.
        """
        try:
            resposta = self.cliente.rpc(
                "registrar_tentativa_redacao",
                {"p_chave": chave, "p_limite": limite}
            ).execute()
            return bool(resposta.data)
        except Exception as e:
            mensagem = str(e).lower()
            if "could not find" in mensagem or "does not exist" in mensagem or "pgrst" in mensagem:
                logger.warning(
                    "Funcao RPC 'registrar_tentativa_redacao' nao encontrada no Supabase. "
                    "Aplique scripts/sql/rate_limit.sql para ter contagem atomica. "
                    "Usando fallback nao-atomico por enquanto."
                )
                return None
            logger.error("Erro ao registrar tentativa (rpc) para chave '%s': %s", chave, e)
            raise RuntimeError("Nao foi possivel verificar seu limite de uso. Tente novamente.")

    def _verificar_limite_fallback(self, chave: str, limite: int) -> None:
        hoje = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        try:
            if chave == _CHAVE_LIMITE_SISTEMA:
                resposta = self.cliente.table("redacoes")\
                    .select("id")\
                    .gte("criado_em", f"{hoje}T00:00:00Z")\
                    .execute()
            else:
                resposta = self.cliente.table("redacoes")\
                    .select("id")\
                    .eq("usuario_id", chave)\
                    .gte("criado_em", f"{hoje}T00:00:00Z")\
                    .execute()
            contagem = len(resposta.data)
        except Exception as e:
            logger.error("Erro ao verificar limite diario (fallback) no banco: %s", e)
            raise RuntimeError("Nao foi possivel verificar seu limite de uso. Tente novamente.")

        if contagem >= limite:
            raise RuntimeError(
                f"Limite diario de {limite} correcoes atingido. Tente novamente amanha."
            )

    def verificar_limite_diario(self, usuario_id: str) -> None:
        if not self.cliente:
            return

        aceito = self._registrar_tentativa_atomica(usuario_id, MAX_CORRECOES_USUARIO_DIA)
        if aceito is False:
            raise RuntimeError(
                f"Limite diario de {MAX_CORRECOES_USUARIO_DIA} correcoes atingido. "
                "Tente novamente amanha."
            )
        if aceito is None:
            self._verificar_limite_fallback(usuario_id, MAX_CORRECOES_USUARIO_DIA)

    def verificar_limite_sistema(self) -> None:
        if not self.cliente:
            return

        aceito = self._registrar_tentativa_atomica(_CHAVE_LIMITE_SISTEMA, MAX_CORRECOES_SISTEMA_DIA)
        if aceito is False:
            raise RuntimeError(
                "O sistema atingiu o limite diario de correcoes. Tente novamente amanha."
            )
        if aceito is None:
            self._verificar_limite_fallback(_CHAVE_LIMITE_SISTEMA, MAX_CORRECOES_SISTEMA_DIA)

    def buscar_historico(self, usuario_id: str, limite: int = 10) -> List[Dict[str, Any]]:
        if not self.cliente:
            return []

        try:
            resposta = self.cliente.table("redacoes")\
                .select("*")\
                .eq("usuario_id", usuario_id)\
                .order("criado_em", desc=True)\
                .limit(limite)\
                .execute()
            
            return resposta.data
        except Exception as e:
            logger.error("Erro ao buscar historico: %s", e)
            return []

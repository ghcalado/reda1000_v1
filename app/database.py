import os
import logging
from typing import Optional, List, Dict, Any
from supabase import create_client, Client
from app.config import MAX_CORRECOES_USUARIO_DIA
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self) -> None:
        url: str = os.getenv("SUPABASE_URL", "")
        # Tenta usar a Service Role Key (que ignora RLS), senao cai para a Anon Key
        key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SUPABASE_ANON_KEY", ""))
        
        if not url or not key:
            logger.warning("Supabase URL ou Key nao encontrados. Banco inativo.")
            self.cliente = None
        else:
            try:
                self.cliente: Optional[Client] = create_client(url, key)
            except Exception as e:
                logger.error(f"Erro ao inicializar cliente Supabase: {e}")
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

    def verificar_limite_diario(self, usuario_id: str) -> None:
        """Consulta quantas redacoes o usuario enviou HOJE via banco de dados."""
        if not self.cliente:
            return

        hoje = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        try:
            # Filtra pela data maior ou igual as 00:00 de hoje (UTC)
            resposta = self.cliente.table("redacoes")\
                .select("id")\
                .eq("usuario_id", usuario_id)\
                .gte("criado_em", f"{hoje}T00:00:00Z")\
                .execute()

            contagem = len(resposta.data)

            if contagem >= MAX_CORRECOES_USUARIO_DIA:
                raise RuntimeError(
                    f"Limite diario de {MAX_CORRECOES_USUARIO_DIA} correcoes atingido. "
                    "Tente novamente amanha."
                )
        except RuntimeError:
            raise
        except Exception as e:
            logger.error("Erro ao verificar limite diario no banco: %s", e)
            raise RuntimeError("Nao foi possivel verificar seu limite de uso. Tente novamente.")

    def buscar_historico(self, usuario_id: str, limite: int = 10) -> List[Dict[str, Any]]:
        """Retorna as ultimas correcoes do usuario ordenadas da mais recente para a mais antiga."""
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

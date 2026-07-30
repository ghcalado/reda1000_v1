import jwt
import os
import logging
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client

logger = logging.getLogger(__name__)

# Configura o Bearer Token no Swagger UI
security = HTTPBearer(auto_error=False)

def verificar_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Decodifica o token JWT (gerado pelo Supabase) enviado pelo frontend.
    Retorna o ID unico do usuario (UUID).
    """
    if not credentials:
        # Se nao mandou o header Authorization
        raise HTTPException(
            status_code=401, 
            detail="Acesso negado. Faca login para continuar (Token ausente)."
        )

    token = credentials.credentials
    
    try:
        jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
        token_alg = jwt.get_unverified_header(token).get("alg")
        
        if jwt_secret and token_alg == "HS256":
            payload = jwt.decode(
                token,
                jwt_secret,
                algorithms=["HS256"],
                audience="authenticated"
            )
            usuario_id = payload.get("sub")
        elif os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_ANON_KEY"):
            try:
                supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))
                user_response = supabase.auth.get_user(token)
                usuario_id = user_response.user.id if user_response and user_response.user else None
            except Exception as e:
                logger.error("Falha ao validar token no Supabase Auth: %s", e)
                raise HTTPException(status_code=401, detail="Sessao invalida. Faca login novamente.")
        else:
            logger.error("ATENCAO: SUPABASE_JWT_SECRET ausente e credentials invalidas.")
            raise HTTPException(status_code=401, detail="Configuracao de seguranca do servidor incompleta. Token rejeitado.")

        if not usuario_id:
            raise HTTPException(status_code=401, detail="Token invalido: Identificacao de usuario ausente.")
            
        return usuario_id

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Sessao expirada. Faca login novamente.")
    except jwt.InvalidTokenError as e:
        logger.error("Falha ao decodificar token: %s", e)
        raise HTTPException(status_code=401, detail="Token invalido ou malformado.")

import jwt
import os
import logging
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

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
        
        if not jwt_secret:
            logger.warning("ATENCAO: SUPABASE_JWT_SECRET ausente. Validando token sem checar assinatura. (Inseguro para Producao)")
            payload = jwt.decode(token, options={"verify_signature": False})
        else:
            payload = jwt.decode(
                token, 
                jwt_secret, 
                algorithms=["HS256"], 
                audience="authenticated"
            )
            
        usuario_id = payload.get("sub")
        if not usuario_id:
            raise HTTPException(status_code=401, detail="Token invalido: Identificacao de usuario ausente.")
            
        return usuario_id

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Sessao expirada. Faca login novamente.")
    except jwt.InvalidTokenError as e:
        logger.error("Falha ao decodificar token: %s", e)
        raise HTTPException(status_code=401, detail="Token invalido ou malformado.")

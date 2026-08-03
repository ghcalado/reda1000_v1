
import time

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.auth import verificar_token

SEGREDO = "segredo-de-teste-fake"  # mesmo valor setado em tests/conftest.py


def _gerar_token(usuario_id: str = "user-123", expira_em_segundos: int = 3600, **claims_extra) -> str:
    payload = {
        "sub": usuario_id,
        "aud": "authenticated",
        "iat": int(time.time()),
        "exp": int(time.time()) + expira_em_segundos,
        **claims_extra,
    }
    return jwt.encode(payload, SEGREDO, algorithm="HS256")


def _credenciais(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def test_token_valido_retorna_usuario_id():
    token = _gerar_token(usuario_id="aluno-abc")
    usuario_id = verificar_token(_credenciais(token))
    assert usuario_id == "aluno-abc"


def test_sem_credenciais_retorna_401():
    with pytest.raises(HTTPException) as exc_info:
        verificar_token(None)
    assert exc_info.value.status_code == 401


def test_token_expirado_retorna_401():
    token = _gerar_token(expira_em_segundos=-10)
    with pytest.raises(HTTPException) as exc_info:
        verificar_token(_credenciais(token))
    assert exc_info.value.status_code == 401


def test_token_malformado_retorna_401():
    with pytest.raises(HTTPException) as exc_info:
        verificar_token(_credenciais("isto-nao-e-um-jwt"))
    assert exc_info.value.status_code == 401


def test_token_assinado_com_segredo_errado_retorna_401():
    token = jwt.encode(
        {"sub": "user-123", "aud": "authenticated", "exp": int(time.time()) + 3600},
        "segredo-errado",
        algorithm="HS256",
    )
    with pytest.raises(HTTPException) as exc_info:
        verificar_token(_credenciais(token))
    assert exc_info.value.status_code == 401


def test_token_sem_claim_sub_retorna_401():
    token = jwt.encode(
        {"aud": "authenticated", "exp": int(time.time()) + 3600},
        SEGREDO,
        algorithm="HS256",
    )
    with pytest.raises(HTTPException) as exc_info:
        verificar_token(_credenciais(token))
    assert exc_info.value.status_code == 401


import pytest
from pydantic import ValidationError

from app.api.schemas import RedacaoRequest


def test_aceita_payload_valido():
    req = RedacaoRequest(tema="Desafios da IA no Brasil", texto_redacao="Um texto qualquer com conteúdo.")
    assert req.tema == "Desafios da IA no Brasil"


def test_rejeita_texto_redacao_vazio():
    with pytest.raises(ValidationError):
        RedacaoRequest(tema="Tema válido", texto_redacao="")


def test_rejeita_texto_redacao_acima_do_limite():
    texto_gigante = "a" * 15001
    with pytest.raises(ValidationError):
        RedacaoRequest(tema="Tema válido", texto_redacao=texto_gigante)


def test_aceita_texto_redacao_no_limite():
    texto_no_limite = "a" * 15000
    req = RedacaoRequest(tema="Tema válido", texto_redacao=texto_no_limite)
    assert len(req.texto_redacao) == 15000


def test_rejeita_tema_muito_curto():
    with pytest.raises(ValidationError):
        RedacaoRequest(tema="ab", texto_redacao="Texto válido")


def test_rejeita_tema_acima_do_limite():
    with pytest.raises(ValidationError):
        RedacaoRequest(tema="a" * 301, texto_redacao="Texto válido")

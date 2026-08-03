
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api import routes as routes_module
from app.auth import verificar_token
from server import app

USUARIO_TESTE = "usuario-teste-123"


@pytest.fixture(autouse=True)
def _override_auth():
    """Todas as rotas exigem token; para os testes, sempre 'autentica' o mesmo usuário."""
    app.dependency_overrides[verificar_token] = lambda: USUARIO_TESTE
    yield
    app.dependency_overrides.pop(verificar_token, None)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def servico_mock(monkeypatch, resultado_correcao_valido):
    """Substitui o singleton global `servico_correcao` do módulo de rotas por um mock."""
    mock = MagicMock()
    mock.corrigir_redacao.return_value = resultado_correcao_valido
    mock.db.cliente = MagicMock()
    mock.db.buscar_historico.return_value = []
    monkeypatch.setattr(routes_module, "servico_correcao", mock)
    return mock


@pytest.fixture
def extrator_mock(monkeypatch):
    mock = MagicMock()
    mock.transcrever.return_value = "Texto transcrito da imagem."
    monkeypatch.setattr(routes_module, "extrator_visao", mock)
    return mock


class TestCorrigirTexto:
    def test_sucesso_retorna_200(self, client, servico_mock):
        resposta = client.post(
            "/api/v1/corrigir/texto",
            json={"tema": "Tema válido", "texto_redacao": "Um texto de redação qualquer."},
        )
        assert resposta.status_code == 200
        assert resposta.json()["nota_total"] == 880

    def test_servico_indisponivel_retorna_503(self, client, monkeypatch):
        monkeypatch.setattr(routes_module, "servico_correcao", None)
        resposta = client.post(
            "/api/v1/corrigir/texto",
            json={"tema": "Tema válido", "texto_redacao": "Um texto de redação qualquer."},
        )
        assert resposta.status_code == 503

    def test_texto_vazio_retorna_422_validacao(self, client, servico_mock):
        # Pydantic (min_length=1) já barra antes de chegar na lógica de negócio.
        resposta = client.post(
            "/api/v1/corrigir/texto",
            json={"tema": "Tema válido", "texto_redacao": ""},
        )
        assert resposta.status_code == 422

    def test_texto_muito_longo_retorna_422(self, client, servico_mock):
        resposta = client.post(
            "/api/v1/corrigir/texto",
            json={"tema": "Tema válido", "texto_redacao": "a" * 20000},
        )
        assert resposta.status_code == 422

    def test_limite_diario_atingido_retorna_429(self, client, servico_mock):
        servico_mock.corrigir_redacao.side_effect = RuntimeError("Limite diario de 3 correcoes atingido.")
        resposta = client.post(
            "/api/v1/corrigir/texto",
            json={"tema": "Tema válido", "texto_redacao": "Um texto qualquer."},
        )
        assert resposta.status_code == 429

    def test_erro_interno_nao_vaza_detalhes(self, client, servico_mock):
        """Regressão do bug de vazamento: erros genéricos não devem expor a
        exceção interna crua na resposta ao cliente."""
        servico_mock.corrigir_redacao.side_effect = ValueError("segredo interno da stack trace")
        resposta = client.post(
            "/api/v1/corrigir/texto",
            json={"tema": "Tema válido", "texto_redacao": "Um texto qualquer."},
        )
        assert resposta.status_code == 500
        assert "segredo interno da stack trace" not in resposta.text

    def test_sem_token_retorna_401(self, client, servico_mock):
        app.dependency_overrides.pop(verificar_token, None)
        try:
            resposta = client.post(
                "/api/v1/corrigir/texto",
                json={"tema": "Tema válido", "texto_redacao": "Um texto qualquer."},
            )
            assert resposta.status_code == 401
        finally:
            app.dependency_overrides[verificar_token] = lambda: USUARIO_TESTE


class TestCorrigirFoto:
    def test_extensao_nao_suportada_retorna_400(self, client, servico_mock, extrator_mock):
        resposta = client.post(
            "/api/v1/corrigir/foto",
            data={"tema": "Tema válido"},
            files={"arquivo": ("redacao.txt", b"conteudo qualquer", "text/plain")},
        )
        assert resposta.status_code == 400

    def test_nome_de_arquivo_malicioso_nao_quebra_e_e_rejeitado(self, client, servico_mock, extrator_mock):
        """Regressão do bug de path traversal: nomes de arquivo com '/' ou '..'
        não devem ser usados como sufixo do arquivo temporário."""
        resposta = client.post(
            "/api/v1/corrigir/foto",
            data={"tema": "Tema válido"},
            files={"arquivo": ("../../etc/passwd.jpg", b"fake-jpeg-bytes", "image/jpeg")},
        )
        # Extensao .jpg e valida, entao deve seguir o fluxo normal (nao 500/crash)
        assert resposta.status_code == 200
        extrator_mock.transcrever.assert_called_once()

    def test_sucesso_retorna_texto_e_correcao(self, client, servico_mock, extrator_mock):
        resposta = client.post(
            "/api/v1/corrigir/foto",
            data={"tema": "Tema válido"},
            files={"arquivo": ("redacao.jpg", b"fake-jpeg-bytes", "image/jpeg")},
        )
        assert resposta.status_code == 200
        corpo = resposta.json()
        assert corpo["texto_reconhecido"] == "Texto transcrito da imagem."
        assert corpo["correcao"]["nota_total"] == 880


class TestHistorico:
    def test_retorna_lista_vazia_quando_sem_historico(self, client, servico_mock):
        resposta = client.get("/api/v1/historico")
        assert resposta.status_code == 200
        assert resposta.json() == []

    def test_banco_indisponivel_retorna_503(self, client, servico_mock):
        servico_mock.db.cliente = None
        resposta = client.get("/api/v1/historico")
        assert resposta.status_code == 503


class TestHealthCheck:
    def test_health_reflete_servicos_disponiveis(self, client, servico_mock, extrator_mock):
        resposta = client.get("/health")
        assert resposta.status_code == 200
        assert resposta.json()["status"] == "online"

    def test_health_reporta_degraded_sem_servicos(self, client, monkeypatch):
        monkeypatch.setattr(routes_module, "servico_correcao", None)
        monkeypatch.setattr(routes_module, "extrator_visao", None)
        resposta = client.get("/health")
        assert resposta.status_code == 200
        assert resposta.json()["status"] == "degraded"

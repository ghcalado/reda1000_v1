
from unittest.mock import MagicMock

import pytest

from app.database import DatabaseService, _CHAVE_LIMITE_SISTEMA


def _servico_com_cliente_mockado() -> DatabaseService:
    """Instância de DatabaseService pulando o __init__ (evita create_client real)."""
    servico = DatabaseService.__new__(DatabaseService)
    servico.cliente = MagicMock()
    return servico


class TestRegistrarTentativaAtomica:
    def test_rpc_aceita_tentativa(self):
        servico = _servico_com_cliente_mockado()
        servico.cliente.rpc.return_value.execute.return_value.data = True

        aceito = servico._registrar_tentativa_atomica("usuario-1", limite=3)

        assert aceito is True
        servico.cliente.rpc.assert_called_once_with(
            "registrar_tentativa_redacao",
            {"p_chave": "usuario-1", "p_limite": 3},
        )

    def test_rpc_rejeita_tentativa_limite_atingido(self):
        servico = _servico_com_cliente_mockado()
        servico.cliente.rpc.return_value.execute.return_value.data = False

        aceito = servico._registrar_tentativa_atomica("usuario-1", limite=3)

        assert aceito is False

    def test_rpc_inexistente_retorna_none_para_fallback(self):
        servico = _servico_com_cliente_mockado()
        servico.cliente.rpc.side_effect = Exception(
            "Could not find the function public.registrar_tentativa_redacao"
        )

        aceito = servico._registrar_tentativa_atomica("usuario-1", limite=3)

        assert aceito is None

    def test_erro_generico_do_banco_vira_runtime_error(self):
        servico = _servico_com_cliente_mockado()
        servico.cliente.rpc.side_effect = Exception("timeout de conexao")

        with pytest.raises(RuntimeError):
            servico._registrar_tentativa_atomica("usuario-1", limite=3)


class TestVerificarLimiteDiario:
    def test_dentro_do_limite_nao_levanta_erro(self):
        servico = _servico_com_cliente_mockado()
        servico.cliente.rpc.return_value.execute.return_value.data = True

        servico.verificar_limite_diario("usuario-1")  # nao deve levantar

    def test_limite_atingido_levanta_runtime_error(self):
        servico = _servico_com_cliente_mockado()
        servico.cliente.rpc.return_value.execute.return_value.data = False

        with pytest.raises(RuntimeError, match="Limite diario"):
            servico.verificar_limite_diario("usuario-1")

    def test_sem_cliente_nao_faz_nada(self):
        servico = DatabaseService.__new__(DatabaseService)
        servico.cliente = None

        servico.verificar_limite_diario("usuario-1")  # nao deve levantar nem chamar nada


class TestVerificarLimiteSistema:
    def test_usa_chave_especial_do_sistema(self):
        servico = _servico_com_cliente_mockado()
        servico.cliente.rpc.return_value.execute.return_value.data = True

        servico.verificar_limite_sistema()

        args, _ = servico.cliente.rpc.call_args
        assert args[1]["p_chave"] == _CHAVE_LIMITE_SISTEMA

    def test_limite_do_sistema_atingido_levanta_erro(self):
        servico = _servico_com_cliente_mockado()
        servico.cliente.rpc.return_value.execute.return_value.data = False

        with pytest.raises(RuntimeError, match="sistema atingiu"):
            servico.verificar_limite_sistema()

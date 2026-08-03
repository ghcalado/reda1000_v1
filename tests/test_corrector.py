
import json

import pytest

from app.corrector import ServicoCorrecao


@pytest.fixture
def servico() -> ServicoCorrecao:
    """Instância 'vazia', sem chamar __init__ (evita side effects de rede)."""
    return ServicoCorrecao.__new__(ServicoCorrecao)


class TestLimparMarkdownJson:
    def test_remove_fence_com_linguagem(self, servico):
        entrada = '```json\n{"a": 1}\n```'
        assert servico._limpar_markdown_json(entrada) == '{"a": 1}'

    def test_remove_fence_sem_linguagem(self, servico):
        entrada = '```\n{"a": 1}\n```'
        assert servico._limpar_markdown_json(entrada) == '{"a": 1}'

    def test_json_puro_permanece_igual(self, servico):
        entrada = '{"a": 1}'
        assert servico._limpar_markdown_json(entrada) == '{"a": 1}'

    def test_remove_espacos_nas_bordas(self, servico):
        entrada = '   \n{"a": 1}\n   '
        assert servico._limpar_markdown_json(entrada) == '{"a": 1}'


class TestExtrairEValidarJson:
    def test_extrai_json_valido(self, servico, resultado_correcao_valido):
        bruto = json.dumps(resultado_correcao_valido)
        resultado = servico._extrair_e_validar_json(bruto)
        assert resultado["nota_total"] == 880

    def test_extrai_json_com_fence_markdown(self, servico, resultado_correcao_valido):
        bruto = f"```json\n{json.dumps(resultado_correcao_valido)}\n```"
        resultado = servico._extrair_e_validar_json(bruto)
        assert resultado["nota_total"] == 880

    def test_erro_se_json_invalido(self, servico):
        with pytest.raises(RuntimeError, match="JSON valido"):
            servico._extrair_e_validar_json("isto nao e um json {")

    def test_erro_se_faltar_chave_nota_total(self, servico):
        bruto = json.dumps({"notas": {}})
        with pytest.raises(ValueError):
            servico._extrair_e_validar_json(bruto)

    def test_erro_se_faltar_chave_notas(self, servico):
        bruto = json.dumps({"nota_total": 500})
        with pytest.raises(ValueError):
            servico._extrair_e_validar_json(bruto)

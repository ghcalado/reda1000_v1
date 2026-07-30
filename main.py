"""
main.py — Ponto de entrada via terminal para a correcao de redacoes.
Suporta entrada por texto digitado ou por foto de redacao manuscrita (OCR).
"""

import os
import sys
from app.corrector import ServicoCorrecao
from app.ocr import ExtratorVisao


def _ler_texto_digitado() -> str:
    print("\nCole o TEXTO da redacao abaixo.")
    print("Dica: Pressione ENTER duas vezes seguidas numa linha vazia para finalizar.")
    print("-" * 70)

    linhas_texto = []
    linhas_vazias_consecutivas = 0

    while True:
        linha = input()
        if not linha.strip():
            linhas_vazias_consecutivas += 1
            if linhas_vazias_consecutivas >= 2:
                break
        else:
            linhas_vazias_consecutivas = 0
        linhas_texto.append(linha)

    return "\n".join(linhas_texto).strip()


def _ler_texto_por_foto(extrator: ExtratorVisao) -> str:
    caminho = input("Digite o caminho da imagem (ex: /Users/.../redacao.jpg): ").strip()

    if not caminho:
        print("Caminho vazio. Operacao cancelada.")
        return ""

    print("\n[Sistema] Processando imagem com IA de Visao. Aguarde...")
    texto = extrator.transcrever(caminho)

    print("\n" + "=" * 70)
    print("TEXTO EXTRAIDO DA IMAGEM:")
    print("=" * 70)
    print(texto)
    print("=" * 70)

    confirma = input("\nO texto acima esta correto? (s/n): ").strip().lower()
    if confirma not in ["s", "sim", "y", "yes"]:
        print("Transcricao rejeitada. Voce pode tentar novamente.")
        return ""

    return texto


def _exibir_resultado(resultado: dict) -> None:
    print("\n" + "=" * 70)
    print(f"RESULTADO DA CORRECAO - NOTA FINAL: {resultado.get('nota_total', 0)}")
    print("=" * 70)
    print(f"Analise Geral: {resultado.get('analise_geral', '')}\n")

    notas = resultado.get("notas", {})
    for comp in ["C1", "C2", "C3", "C4", "C5"]:
        dados = notas.get(comp, {})
        nota_comp = dados.get("nota", 0)
        print(f"[{comp}] Nota: {nota_comp}")

        fortes = dados.get("pontos_fortes", [])
        if fortes:
            print("  [+] Pontos Fortes:")
            for f in fortes:
                print(f"      - {f}")

        melhorar = dados.get("pontos_melhorar", [])
        if melhorar:
            print("  [-] Pontos a Melhorar:")
            for m in melhorar:
                print(f"      - {m}")

        reescrita = dados.get("reescrita_sugerida", "")
        if reescrita:
            print(f"  [Reescrita] Sugestao: {reescrita}")

        print()

    if resultado.get("fuga_tema") or resultado.get("condicao_anulacao", "Nenhuma") != "Nenhuma":
        print(f"ATENCAO: Condicao de Anulacao Detectada - {resultado.get('condicao_anulacao')}\n")

    prioridade = resultado.get("prioridade_estudo", "")
    if prioridade:
        print("-" * 70)
        print(f"PRIORIDADE DE ESTUDO: {prioridade}")
        print("-" * 70)


def iniciar_terminal() -> None:
    print("=" * 70)
    print("RedacaoAI - Motor de Correcao Avancado (Terminal)")
    print("=" * 70)

    try:
        servico = ServicoCorrecao()
        extrator = ExtratorVisao()
    except RuntimeError as e:
        print(f"\n[ERRO FATAL] Nao foi possivel iniciar o motor: {e}")
        sys.exit(1)

    while True:
        try:
            print("\n" + "-" * 70)
            tema = input("Digite o TEMA da redacao (ou 'sair' para encerrar): ").strip()

            if tema.lower() in ["sair", "quit", "exit"]:
                print("\nEncerrando o RedacaoAI. Ate logo!")
                break

            if not tema:
                print("O tema nao pode ser vazio.")
                continue

            print("\nComo deseja enviar a redacao?")
            print("  (1) Digitar/colar o texto")
            print("  (2) Enviar foto de redacao manuscrita")
            print("  (3) Ler de um arquivo .txt")
            opcao = input("Escolha [1/2/3]: ").strip()

            if opcao == "2":
                texto_redacao = _ler_texto_por_foto(extrator)
            elif opcao == "3":
                caminho_txt = input("Caminho do arquivo .txt: ").strip()
                if not caminho_txt or not os.path.isfile(caminho_txt):
                    print("Arquivo nao encontrado.")
                    continue
                with open(caminho_txt, "r", encoding="utf-8") as f:
                    texto_redacao = f.read().strip()
                print(f"\n[Sistema] Texto carregado ({len(texto_redacao)} caracteres).")
            else:
                texto_redacao = _ler_texto_digitado()

            if not texto_redacao:
                print("\nErro: O texto da redacao esta vazio.")
                continue

            print("\n[Sistema] Iniciando analise profunda (Passo 1: Correcao | Passo 2: Autocritica)...")

            resultado = servico.corrigir_redacao(tema, texto_redacao)
            _exibir_resultado(resultado)

        except KeyboardInterrupt:
            print("\n\nSessao interrompida pelo usuario. Ate logo!")
            break
        except Exception as e:
            print(f"\n[ERRO INESPERADO] Falha durante o processamento: {e}")


if __name__ == "__main__":
    iniciar_terminal()

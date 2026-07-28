"""
app.py — Ponto de entrada via terminal para a correcao de redacoes.
"""

import sys
from app.corrector import ServicoCorrecao

def iniciar_terminal() -> None:
    print("=" * 70)
    print("RedacaoAI - Motor de Correcao Avancado (Terminal)")
    print("=" * 70)

    try:
        servico = ServicoCorrecao()
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

            print("\nCole o TEXTO da redacao abaixo.")
            print("Dica: Pressione ENTER duas vezes seguidas numa linha vazia para finalizar a submissao.")
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
                
            texto_redacao = "\n".join(linhas_texto).strip()
            
            if not texto_redacao:
                print("\nErro: O texto da redacao esta vazio.")
                continue

            print("\n[Sistema] Iniciando analise profunda (Passo 1: Correcao | Passo 2: Autocritica)...")
            
            resultado = servico.corrigir_redacao(tema, texto_redacao)
            
            print("\n" + "=" * 70)
            print(f"RESULTADO DA CORRECAO - NOTA FINAL: {resultado.get('nota_total', 0)}")
            print("=" * 70)
            print(f"Analise Geral: {resultado.get('analise_geral', '')}\n")
            
            notas = resultado.get('notas', {})
            for comp in ["C1", "C2", "C3", "C4", "C5"]:
                dados = notas.get(comp, {})
                nota_comp = dados.get('nota', 0)
                print(f"[{comp}] Nota: {nota_comp}")
                
                fortes = dados.get('pontos_fortes', [])
                if fortes:
                    print("  [+] Pontos Fortes:")
                    for f in fortes: print(f"      - {f}")
                        
                melhorar = dados.get('pontos_melhorar', [])
                if melhorar:
                    print("  [-] Pontos a Melhorar:")
                    for m in melhorar: print(f"      - {m}")
                        
                reescrita = dados.get('reescrita_sugerida', '')
                if reescrita:
                    print(f"  [Reescrita] Sugestao: {reescrita}")
                    
                print()
                
            if resultado.get('fuga_tema') or resultado.get('condicao_anulacao', 'Nenhuma') != 'Nenhuma':
                print(f"ATENCAO: Condicao de Anulacao Detectada - {resultado.get('condicao_anulacao')}\n")
                
            prioridade = resultado.get('prioridade_estudo', '')
            if prioridade:
                print("-" * 70)
                print(f"PRIORIDADE DE ESTUDO: {prioridade}")
                print("-" * 70)
                
        except KeyboardInterrupt:
            print("\n\nSessao interrompida pelo usuario. Ate logo!")
            break
        except Exception as e:
            print(f"\n[ERRO INESPERADO] Falha durante o processamento: {e}")

if __name__ == "__main__":
    iniciar_terminal()

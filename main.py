import subprocess
import sys
from pathlib import Path
from datetime import datetime

# ==========================================
# FUNÇÃO DE EXECUÇÃO
# ==========================================

def executar(script):
    print()
    print("=" * 60)
    print(f"EXECUTANDO: {script}")
    print("=" * 60)
    print()
    
    # Chama o script usando o mesmo executável Python atual
    resultado = subprocess.run([sys.executable, script])
    
    if resultado.returncode != 0:
        print(f"\n❌ ERRO: {script} falhou.")
    else:
        print(f"\n✓ {script} concluído.")


# ==========================================
# VERIFICAR IDADE DA BASE DE DADOS
# ==========================================

def verificar_atualizacao():
    arquivo_dados = Path("dados/filmes_final.csv")
    
    if not arquivo_dados.exists():
        print("\n⚠ AVISO: A base de dados principal não foi encontrada.")
        print("Recomendado: Execute 'atualizar.py' para baixar e processar os dados iniciais.")
        return

    # Verifica a data de modificação do arquivo
    timestamp_modificacao = arquivo_dados.stat().st_mtime
    data_modificacao = datetime.fromtimestamp(timestamp_modificacao)
    dias_passados = (datetime.now() - data_modificacao).days

    if dias_passados > 30:
        print(f"\n⚠ AVISO: Sua base de dados foi atualizada há {dias_passados} dias.")
        print("Considere rodar a atualização (atualizar.py) para garantir que você tenha as notas e filmes mais recentes do IMDb.")
    elif dias_passados == 0:
        print("\n✓ Base de dados atualizada (Hoje).")
    else:
        print(f"\n✓ Base de dados atualizada ({dias_passados} dias atrás).")


# ==========================================
# MENU INTERATIVO
# ==========================================

def menu():
    # Verifica a atualização apenas uma vez ao iniciar
    print("\n" + "=" * 60)
    print("🎬 INICIALIZANDO FILMES GLOBAL")
    print("=" * 60)
    verificar_atualizacao()
    
    while True:
        print("\n" + "=" * 60)
        print("🎬 MENU PRINCIPAL")
        print("=" * 60)
        print("Escolha uma opção:")
        print("1 - Realizar um sorteio (País ou Filme)")
        print("2 - Ver Ranking (Melhor filme de cada país)")
        print("0 - Sair")
        print("=" * 60)

        opcao = input("\nDigite o número da opção desejada: ").strip()

        if opcao == "1":
            # Chama o script de sorteio que acabamos de atualizar
            executar("sorteio.py")
            
        elif opcao == "2":
            # Chama o script que gera e mostra o ranking
            executar("analisar_base.py")
            
        elif opcao == "0":
            print("\nSaindo... Até a próxima e bons filmes!\n")
            break
            
        else:
            print("\n❌ Opção inválida. Tente novamente.")

# ==========================================
# EXECUÇÃO
# ==========================================

if __name__ == "__main__":
    menu()

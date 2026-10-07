import subprocess
import sys


# ==========================================
# SCRIPTS DA PIPELINE
# ==========================================

SCRIPTS = [
    "atualizar_bases.py",
    "preparar_dados.py",
    "consultar_paises.py",
    "normalizar_paises.py"
]


# ==========================================
# EXECUTAR SCRIPT
# ==========================================

def executar(script):

    print()
    print("=" * 60)
    print(f"EXECUTANDO: {script}")
    print("=" * 60)
    print()

    resultado = subprocess.run(
        [sys.executable, script]
    )

    if resultado.returncode != 0:

        print()
        print(
            f"❌ ERRO: {script} falhou."
        )

        print(
            "\nA atualização foi interrompida."
        )

        sys.exit(
            resultado.returncode
        )

    print()
    print(
        f"✓ {script} concluído."
    )


# ==========================================
# PIPELINE
# ==========================================

print()
print("=" * 60)
print("FILMES GLOBAL — ATUALIZAÇÃO")
print("=" * 60)

for script in SCRIPTS:
    executar(script)


print()
print("=" * 60)
print("✓ ATUALIZAÇÃO CONCLUÍDA")
print("=" * 60)
print()

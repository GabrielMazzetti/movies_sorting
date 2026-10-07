import pandas as pd

def listar_paises():
    try:
        filmes = pd.read_csv("dados/filmes_final.csv")
    except FileNotFoundError:
        print("❌ Arquivo filmes_final.csv não encontrado!")
        return

    # Pega todos os países únicos, remove valores nulos e coloca em ordem alfabética
    paises_unicos = sorted(filmes["pais_sorteavel"].dropna().unique())
    
    print("=========================================")
    print(f"🎬 TOTAL DE PAÍSES NA BASE: {len(paises_unicos)}")
    print("=========================================")
    
    for pais in paises_unicos:
        print(f"- {pais}")

if __name__ == "__main__":
    listar_paises()

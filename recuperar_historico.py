import pandas as pd
from pathlib import Path

def sortear_obrigatorios():
    ARQUIVO_FILMES = Path("dados/filmes_final.csv")
    PASTA_SORTEIOS = Path("sorteios")

    filmes = pd.read_csv(ARQUIVO_FILMES)

    # Agora usamos os nomes EXATOS que o seu terminal acabou de nos mostrar!
    alvos = {
        "Áustria": "Áustria",
        "Suíça": "Suíça",
        "Estônia": "Estónia" # Escrito com 'ó' conforme a sua base
    }

    for nome_antigo, nome_real_csv in alvos.items():
        print(f"\nProcurando por: {nome_real_csv}...")
        
        # Busca exata: a coluna tem que ser 100% igual à palavra
        filmes_pais = filmes[filmes["pais_sorteavel"] == nome_real_csv]
        
        if filmes_pais.empty:
            print(f"❌ Erro: {nome_real_csv} não encontrado. Isso não deveria acontecer!")
            continue

        # Pega o melhor filme desse país
        escolhido = filmes_pais.sort_values(["indice", "averageRating", "numVotes"], ascending=False).iloc[0]

        # Monta o TXT no padrão do app novo
        conteudo = f"""========================================
FILMES GLOBAL
========================================
MODO DO SORTEIO: MELHOR FILME: {nome_real_csv.upper()}
PAÍS: {nome_real_csv}

FILME: {escolhido['primaryTitle']}
ANO: {int(escolhido['startYear'])}

NOTA IMDb: {float(escolhido['averageRating'])}
AVALIAÇÕES: {int(escolhido['numVotes']):,}
ÍNDICE: {float(escolhido['indice']):.6f}

IMDb ID: {escolhido['tconst']}
"""
        novo_arquivo = PASTA_SORTEIOS / f"{nome_real_csv}_{escolhido['tconst']}.txt"
        with open(novo_arquivo, "w", encoding="utf-8") as f:
            f.write(conteudo.strip())
        
        print(f"🎬 Sorteio salvo: {escolhido['primaryTitle']}")
        
        # Faxina: apaga os arquivos vazios/antigos para não sujar o histórico
        for txt in PASTA_SORTEIOS.glob(f"*{nome_antigo}*.txt"):
            if txt.name != novo_arquivo.name: 
                txt.unlink()
                print(f"🗑️ Arquivo antigo '{txt.name}' limpo.")

    print("\nProcesso finalizado com sucesso! Pode abrir o app.py.")

if __name__ == "__main__":
    sortear_obrigatorios()

import pandas as pd
from pathlib import Path

ARQUIVO = Path("dados/filmes_com_paises.csv")

filmes = pd.read_csv(ARQUIVO)

# Remover filmes sem país
filmes = filmes.dropna(subset=["countryLabel"]).copy()

# Encontrar o filme de maior nota dentro de cada país
melhores = (
    filmes
    .sort_values(
        ["countryLabel", "averageRating", "numVotes"],
        ascending=[True, False, False]
    )
    .groupby("countryLabel", as_index=False)
    .first()
)

# Contagem de filmes por país
quantidade = (
    filmes
    .groupby("countryLabel")
    .size()
    .reset_index(name="quantidade_filmes")
)

# Juntar informações
ranking = melhores.merge(
    quantidade,
    on="countryLabel"
)

# Organizar
ranking = ranking[
    [
        "countryLabel",
        "quantidade_filmes",
        "primaryTitle",
        "startYear",
        "averageRating",
        "numVotes"
    ]
].sort_values(
    "averageRating",
    ascending=False
)

print("\n==============================================")
print("MELHOR FILME DE CADA PAÍS")
print("==============================================\n")

print(ranking.to_string(index=False))

ranking.to_csv(
    "dados/ranking_paises.csv",
    index=False,
    encoding="utf-8"
)

print("\n✓ Ranking salvo em dados/ranking_paises.csv")

import pandas as pd
from pathlib import Path


# Diretório onde estão as bases
DADOS = Path("dados")


# Localiza automaticamente a versão mais recente da base
basics = max(DADOS.glob("title.basics_*.tsv"))
ratings = max(DADOS.glob("title.ratings_*.tsv"))

print(f"Base de títulos: {basics}")
print(f"Base de avaliações: {ratings}")


# Colunas que realmente precisamos
colunas_basics = [
    "tconst",
    "titleType",
    "primaryTitle",
    "originalTitle",
    "startYear",
    "genres"
]

colunas_ratings = [
    "tconst",
    "averageRating",
    "numVotes"
]


# Lê somente as colunas necessárias
filmes = pd.read_csv(
    basics,
    sep="\t",
    usecols=colunas_basics,
    dtype=str,
    na_values="\\N"
)

ratings_df = pd.read_csv(
    ratings,
    sep="\t",
    usecols=colunas_ratings,
    dtype={
        "tconst": "string",
        "averageRating": "float32",
        "numVotes": "int32"
    },
    na_values="\\N"
)


print("\n✓ Bases carregadas!")

print(f"Filmes/títulos: {len(filmes):,}")
print(f"Avaliações: {len(ratings_df):,}")


# Verifica algumas linhas
print("\nPrimeiros títulos:")
print(filmes.head())

print("\nPrimeiras avaliações:")
print(ratings_df.head())

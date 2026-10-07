import pandas as pd
from pathlib import Path


DADOS = Path("dados")


# Encontrar as bases
basics = max(DADOS.glob("title.basics_*.tsv"))
ratings = max(DADOS.glob("title.ratings_*.tsv"))

print(f"Base de títulos: {basics}")
print(f"Base de avaliações: {ratings}")


# -----------------------------
# 1. Ler informações dos filmes
# -----------------------------

filmes = pd.read_csv(
    basics,
    sep="\t",
    usecols=[
        "tconst",
        "titleType",
        "primaryTitle",
        "originalTitle",
        "startYear",
        "genres",
        "runtimeMinutes"
    ],
    dtype=str,
    na_values="\\N"
)


# -----------------------------
# 2. Manter somente filmes
# -----------------------------

filmes = filmes[filmes["titleType"] == "movie"].copy()

print(f"\nFilmes encontrados: {len(filmes):,}")


# -----------------------------
# 3. Ler avaliações
# -----------------------------

ratings_df = pd.read_csv(
    ratings,
    sep="\t",
    usecols=[
        "tconst",
        "averageRating",
        "numVotes"
    ],
    dtype={
        "tconst": "string",
        "averageRating": "float32",
        "numVotes": "int32"
    }
)


# -----------------------------
# 4. Juntar filmes + avaliações
# -----------------------------

filmes = filmes.merge(
    ratings_df,
    on="tconst",
    how="inner"
)


# -----------------------------
# 5. Aplicar mínimo de votos
# -----------------------------

MIN_VOTOS = 500

filmes = filmes[
    filmes["numVotes"] >= MIN_VOTOS
].copy()


print(f"Filmes com pelo menos {MIN_VOTOS:,} votos: {len(filmes):,}")


# -----------------------------
# 6. Salvar
# -----------------------------

saida = DADOS / "filmes_filtrados.csv"

filmes.to_csv(
    saida,
    index=False,
    encoding="utf-8"
)

print(f"\n✓ Base salva em: {saida}")

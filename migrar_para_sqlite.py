import pandas as pd
import sqlite3
from pathlib import Path

DADOS = Path("dados")
BANCO = DADOS / "filmes_global.db"

basics = max(DADOS.glob("title.basics_*.tsv"))
ratings = max(DADOS.glob("title.ratings_*.tsv"))

print(f"Base de títulos: {basics}")
print(f"Base de avaliações: {ratings}")

# -----------------------------
# 1. Ler títulos (mantém o filtro de tipo, que é uma regra de negócio
#    real: só nos interessa titleType == 'movie')
# -----------------------------
filmes = pd.read_csv(
    basics,
    sep="\t",
    usecols=["tconst", "titleType", "primaryTitle", "originalTitle", "startYear", "genres", "runtimeMinutes"],
    dtype=str,
    na_values="\\N"
)
filmes = filmes[filmes["titleType"] == "movie"].copy()
filmes["startYear"] = pd.to_numeric(filmes["startYear"], errors="coerce").astype("Int64")
filmes["runtimeMinutes"] = pd.to_numeric(filmes["runtimeMinutes"], errors="coerce").astype("Int64")

print(f"✓ Filmes (titleType=movie): {len(filmes):,}")

# -----------------------------
# 2. Ler avaliações (SEM filtro de votos aqui — isso agora é
#    responsabilidade das consultas, não da ingestão)
# -----------------------------
ratings_df = pd.read_csv(
    ratings,
    sep="\t",
    usecols=["tconst", "averageRating", "numVotes"],
    dtype={"tconst": "string", "averageRating": "float32", "numVotes": "int32"},
    na_values="\\N"
)

print(f"✓ Avaliações: {len(ratings_df):,}")

# -----------------------------
# 3. Manter só ratings de filmes que existem na base de títulos
# -----------------------------
ratings_df = ratings_df[ratings_df["tconst"].isin(filmes["tconst"])].copy()

# -----------------------------
# 4. Gravar no SQLite
# -----------------------------
conn = sqlite3.connect(BANCO)

filmes.to_sql("filmes", conn, if_exists="replace", index=False)
ratings_df.to_sql("ratings", conn, if_exists="replace", index=False)

conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_filmes_tconst ON filmes(tconst)")
conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_ratings_tconst ON ratings(tconst)")

conn.commit()
conn.close()

print(f"\n✓ Banco atualizado em: {BANCO}")
print(f"  filmes: {len(filmes):,} linhas | ratings: {len(ratings_df):,} linhas")
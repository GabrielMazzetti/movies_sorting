import pandas as pd
import numpy as np
from pathlib import Path
from normalizar_pais import normalizar_pais


# ==========================================
# CONFIGURAÇÕES
# ==========================================

ARQUIVO = Path("dados/filmes_com_paises.csv")

SAIDA_FILMES = Path("dados/filmes_final.csv")
SAIDA_PAISES = Path("dados/paises.csv")

MIN_VOTOS = 500

# Um país só entra na lista de "sorteáveis" se tiver pelo menos essa
# quantidade de filmes elegíveis (após o filtro de votos). Isso substitui
# a lista fixa de nomes e se ajusta sozinho conforme a base cresce.
MIN_FILMES_POR_PAIS = 5

# Caso algum país específico precise ser excluído manualmente por algum
# motivo pontual (dado ruim, país que não faz sentido no sorteio, etc.),
# adicione aqui. Fica vazio por padrão.
PAISES_EXCLUIR_MANUALMENTE = set()


# ==========================================
# CARREGAR DADOS
# ==========================================

print("Carregando base...")

filmes = pd.read_csv(ARQUIVO)

print(f"✓ {len(filmes):,} relações carregadas")


# ==========================================
# FILTRAR VOTOS
# ==========================================

filmes = filmes[
    filmes["numVotes"] >= MIN_VOTOS
].copy()

print(
    f"✓ {len(filmes):,} relações após "
    f"filtro de {MIN_VOTOS:,} votos"
)


# ==========================================
# NORMALIZAR RÓTULO DE PAÍS
# Usa o módulo central: unifica traduções (Turkey -> Turquia), nomes
# históricos (União Soviética -> Rússia) e descarta lixo (frases da IA,
# "Desconhecido", etc.) tudo de uma vez.
# ==========================================

filmes["countryLabel"] = filmes["countryLabel"].apply(normalizar_pais)
# normalizar_pais devolve None para valores inválidos -> vira NaN de verdade
filmes["countryLabel"] = filmes["countryLabel"].where(filmes["countryLabel"].notna())


# ==========================================
# DEFINIR PAÍSES SORTEÁVEIS A PARTIR DOS DADOS
# ==========================================

contagem_paises = (
    filmes["countryLabel"]
    .dropna()
    .value_counts()
)

paises_sorteaveis = set(
    contagem_paises[contagem_paises >= MIN_FILMES_POR_PAIS].index
) - PAISES_EXCLUIR_MANUALMENTE

paises_descartados = set(contagem_paises.index) - paises_sorteaveis

print(
    f"\n✓ {len(paises_sorteaveis)} países sorteáveis "
    f"(≥ {MIN_FILMES_POR_PAIS} filmes elegíveis)"
)

if paises_descartados:
    print(
        f"⚠ {len(paises_descartados)} países descartados por terem "
        f"menos de {MIN_FILMES_POR_PAIS} filmes:"
    )
    for pais in sorted(paises_descartados):
        print(f"    {pais}: {contagem_paises[pais]} filme(s)")


# ==========================================
# NORMALIZAR PAÍS (marcar sorteável)
# ==========================================

filmes["pais_sorteavel"] = filmes["countryLabel"].where(
    filmes["countryLabel"].isin(paises_sorteaveis)
)


# ==========================================
# CALCULAR ÍNDICE
# ==========================================

max_votos = filmes["numVotes"].max()

filmes["popularidade"] = (
    np.log10(filmes["numVotes"])
    / np.log10(max_votos)
)

filmes["indice"] = (
    0.7 * (filmes["averageRating"] / 10)
    +
    0.3 * filmes["popularidade"]
)


# ==========================================
# MANTER SOMENTE PAÍSES SORTEÁVEIS
# ==========================================

filmes_final = filmes.dropna(
    subset=["pais_sorteavel"]
).copy()


# ==========================================
# GERAR LISTA DE PAÍSES
# ==========================================

paises = pd.DataFrame({
    "pais": sorted(
        filmes_final["pais_sorteavel"].unique()
    )
})


# ==========================================
# SALVAR BASES
# ==========================================

filmes_final.to_csv(
    SAIDA_FILMES,
    index=False,
    encoding="utf-8"
)

paises.to_csv(
    SAIDA_PAISES,
    index=False,
    encoding="utf-8"
)

# Salvar no SQLite também
import sqlite3
BANCO = Path("dados/filmes_global.db")
with sqlite3.connect(BANCO) as conn:
    filmes_final.to_sql("filmes_final", conn, if_exists="replace", index=False)
    paises.to_sql("paises_sorteaveis", conn, if_exists="replace", index=False)



# ==========================================
# RELATÓRIO
# ==========================================

print("\n==============================================")
print("RESULTADO")
print("==============================================")

print(
    f"\nFilmes/relações elegíveis: "
    f"{len(filmes_final):,}"
)

print(
    f"Países sorteáveis encontrados: "
    f"{len(paises):,}"
)

print("\nPaíses:")

for pais in paises["pais"]:
    quantidade = (
        filmes_final["pais_sorteavel"] == pais
    ).sum()

    print(f"  {pais}: {quantidade} filmes")


print("\n✓ Base salva em:")
print(f"  {SAIDA_FILMES}")

print("\n✓ Lista de países salva em:")
print(f"  {SAIDA_PAISES}")

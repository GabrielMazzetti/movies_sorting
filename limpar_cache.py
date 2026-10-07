"""
limpar_cache_paises.py

Aplica a normalização central (normalizar_pais.py) em cima do
cache_paises.csv já existente, sem precisar rebuscar nada nas fontes.

Corrige de uma vez:
- Nomes duplicados por tradução (Turkey / Turquia)
- Nomes históricos (União Soviética -> Rússia)
- Lixo salvo por bugs antigos (frases de recusa da IA, etc.)

Rode isso ANTES do consultar_paises.py sempre que atualizar o
normalizar_pais.py com novas regras, ou pontualmente para saneiar
dados antigos já salvos no cache.
"""

import pandas as pd
from pathlib import Path
from normalizar_pais import normalizar_pais

DADOS = Path("dados")
ARQUIVO_CACHE = DADOS / "cache_paises.csv"


def main():
    if not ARQUIVO_CACHE.exists():
        print(f"✗ Cache não encontrado em {ARQUIVO_CACHE}. Nada a fazer.")
        return

    print("Carregando cache de países...")
    cache = pd.read_csv(
        ARQUIVO_CACHE,
        dtype={"tconst": "string", "country": "string", "countryLabel": "string", "fonte": "string"},
    )
    print(f"✓ {len(cache):,} relações carregadas")

    antes = cache["countryLabel"].value_counts()

    print("\nNormalizando countryLabel de todas as linhas...")
    cache["countryLabel"] = cache["countryLabel"].apply(
        lambda x: normalizar_pais(x) or "Desconhecido"
    )

    depois = cache["countryLabel"].value_counts()

    # Mostra quais rótulos sumiram/mudaram, pra você conferir o que foi corrigido
    rotulos_antigos = set(antes.index)
    rotulos_novos = set(depois.index)
    rotulos_corrigidos = rotulos_antigos - rotulos_novos

    if rotulos_corrigidos:
        print(f"\n✓ {len(rotulos_corrigidos)} rótulos diferentes foram unificados/corrigidos:")
        for rotulo in sorted(rotulos_corrigidos):
            print(f"    '{rotulo}' ({antes[rotulo]} filme(s)) -> normalizado")
    else:
        print("\n✓ Nenhum rótulo precisou de correção — cache já estava limpo.")

    # Remove duplicatas que podem ter surgido (ex: tconst com 'Turkey' e
    # 'Turquia' separados, agora ambos viram 'Turquia' e colidem)
    linhas_antes = len(cache)
    cache = cache.drop_duplicates(subset=["tconst", "country", "countryLabel"])
    linhas_depois = len(cache)

    if linhas_antes != linhas_depois:
        print(f"\n✓ Removidas {linhas_antes - linhas_depois:,} linhas duplicadas após normalização.")

    cache.to_csv(ARQUIVO_CACHE, index=False, encoding="utf-8")
    print(f"\n✓ Cache limpo e salvo em: {ARQUIVO_CACHE}")
    print(f"✓ Total de {len(cache):,} relações no cache")

    # Quantos ficaram "Desconhecido" após a limpeza (candidatos a reprocessar
    # no consultar_paises.py, se ainda não tiverem passado pelas 3 etapas)
    total_desconhecidos = (cache["countryLabel"] == "Desconhecido").sum()
    print(f"\n⚠ {total_desconhecidos:,} relações ficaram 'Desconhecido' após a limpeza.")
    print("  Rode consultar_paises.py em seguida para tentar recuperá-los via TMDb/akas.")


if __name__ == "__main__":
    main()

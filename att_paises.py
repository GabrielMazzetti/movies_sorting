import os
import sqlite3
import pandas as pd
import requests
import time
from pathlib import Path
from dotenv import load_dotenv
from normalizar_pais import normalizar_pais
import tratar_paises  # Módulo de tratamento (limpeza + IA como último recurso)

load_dotenv()

# ==========================================
# CONFIGURAÇÕES
# ==========================================
DADOS = Path("dados")
BANCO = DADOS / "filmes_global.db"

# Backups em CSV (não usados como fonte de leitura, só como cópia de segurança)
BACKUP_CACHE = DADOS / "cache_paises.csv"
BACKUP_SAIDA = DADOS / "filmes_com_paises.csv"

# Dataset oficial do IMDb com regiões de lançamento (baixe periodicamente em
# https://datasets.imdbws.com/title.akas.tsv.gz e descompacte na pasta dados/)
ARQUIVO_AKAS = DADOS / "title.akas.tsv.gz"

ENDPOINT_WIKIDATA = "https://query.wikidata.org/sparql"
TAMANHO_LOTE = 100
INTERVALO = 1
HEADERS = {"User-Agent": "FilmesGlobal/1.0 (projeto pessoal)"}

MIN_VOTOS = 500  # Só rastreamos país para o recorte usado nos sorteios por país/melhores

TMDB_API_KEY = os.environ.get("TMDB_API_KEY")
TMDB_INTERVALO = 0.05

# ==========================================
# CONECTAR AO BANCO
# ==========================================
conn = sqlite3.connect(BANCO)

conn.execute("""
CREATE TABLE IF NOT EXISTS cache_paises (
    tconst TEXT,
    country TEXT,
    countryLabel TEXT,
    fonte TEXT,
    PRIMARY KEY (tconst, country)
)
""")
conn.commit()

# ==========================================
# CARREGAR DADOS (filmes com >= 500 votos, que é o recorte
# usado nos sorteios por país e nos melhores filmes)
# ==========================================
print("Carregando base de filmes (>= 500 votos) do banco...")
filmes = pd.read_sql(
    f"""
    SELECT f.tconst, f.primaryTitle, f.originalTitle, f.startYear, f.genres,
           r.averageRating, r.numVotes
    FROM filmes f
    JOIN ratings r ON f.tconst = r.tconst
    WHERE r.numVotes >= {MIN_VOTOS}
    """,
    conn,
    dtype={"tconst": "string"},
)
print(f"✓ {len(filmes):,} filmes carregados")

print("\nCarregando cache de países do banco...")
cache = pd.read_sql("SELECT * FROM cache_paises", conn, dtype={"tconst": "string"})
print(f"✓ {len(cache):,} relações carregadas do cache")

ids = filmes["tconst"].dropna().unique()
ids_cache = set(cache["tconst"].dropna().unique())
ids_novos = [id_ for id_ in ids if id_ not in ids_cache]

mascara_pendente_cache = cache["countryLabel"].isin(["Desconhecido", None]) | cache["country"].isin(["N/A", None])
ids_pendentes_cache = list(cache.loc[mascara_pendente_cache, "tconst"].dropna().unique())
ids_pendentes_cache = [id_ for id_ in ids_pendentes_cache if id_ in set(ids)]

print(f"\nTotal de filmes: {len(ids):,}")
print(f"Já no cache com país definido: {len(ids) - len(ids_novos) - len(ids_pendentes_cache):,}")
print(f"Novos para consultar: {len(ids_novos):,}")
print(f"No cache mas sem país (serão reprocessados): {len(ids_pendentes_cache):,}")


# ==========================================
# ETAPA 1: WIKIDATA (só para filmes realmente novos)
# ==========================================
def consultar_wikidata(ids):
    valores = " ".join(f'"{id_}"' for id_ in ids)
    query = f"""
    SELECT ?imdb ?country ?countryLabel WHERE {{
        VALUES ?imdb {{ {valores} }}
        ?film wdt:P345 ?imdb .
        ?film wdt:P495|wdt:P17 ?country .
        SERVICE wikibase:label {{ bd:serviceParam wikibase:language "pt,en" . }}
    }}
    """
    response = requests.post(
        ENDPOINT_WIKIDATA, data={"query": query, "format": "json"}, headers=HEADERS, timeout=60
    )
    response.raise_for_status()
    dados = response.json()

    resultados = []
    for item in dados["results"]["bindings"]:
        nome_original = item["countryLabel"]["value"]
        nome_corrigido = normalizar_pais(nome_original) or "Desconhecido"
        resultados.append({
            "tconst": item["imdb"]["value"],
            "country": item["country"]["value"].split("/")[-1],
            "countryLabel": nome_corrigido,
            "fonte": "wikidata",
        })
    return resultados


resultados_wikidata = []
total = len(ids_novos)

if total > 0:
    print(f"\n[1/3] Consultando países de {total:,} filmes novos na Wikidata...", flush=True)
    total_lotes = (total + TAMANHO_LOTE - 1) // TAMANHO_LOTE

    for inicio in range(0, total, TAMANHO_LOTE):
        fim = min(inicio + TAMANHO_LOTE, total)
        lote = ids_novos[inicio:fim]
        numero_lote = inicio // TAMANHO_LOTE + 1
        print(f"Lote {numero_lote}/{total_lotes} ({inicio + 1:,}-{fim:,})...", end=" ", flush=True)

        try:
            dados = consultar_wikidata(lote)
            ids_encontrados = {item["tconst"] for item in dados}
            resultados_wikidata.extend(dados)

            vazios = sum(1 for id_lote in lote if id_lote not in ids_encontrados)
            print(f"✓ {len(dados)} encontrados | ✗ {vazios} sem dados", flush=True)
        except Exception as erro:
            print(f"✗ Erro: {erro}", flush=True)

        time.sleep(INTERVALO)
else:
    print("\n[1/3] Nenhum filme novo para consultar na Wikidata.")

ids_achados_wikidata = {r["tconst"] for r in resultados_wikidata}
ids_novos_sem_pais = [id_ for id_ in ids_novos if id_ not in ids_achados_wikidata]
ids_sem_pais = ids_novos_sem_pais + ids_pendentes_cache


# ==========================================
# ETAPA 2: TMDB (melhor cobertura para filmes raros/B-movies)
# Paralelizado com ThreadPoolExecutor — o TMDb aguenta múltiplas
# requisições simultâneas, e fazer uma por vez deixava essa etapa
# extremamente lenta (horas em vez de minutos).
# ==========================================
from concurrent.futures import ThreadPoolExecutor, as_completed

TMDB_WORKERS = 10  # quantidade de requisições simultâneas

# Sessão reaproveitada entre as chamadas (evita reabrir conexão TLS
# a cada requisição)
sessao_tmdb = requests.Session()


def consultar_tmdb(tconst):
    """Retorna (tconst, country_code, country_label) ou (tconst, None, None)."""
    try:
        r = sessao_tmdb.get(
            f"https://api.themoviedb.org/3/find/{tconst}",
            params={"api_key": TMDB_API_KEY, "external_source": "imdb_id"},
            timeout=(5, 10),  # (timeout de conexão, timeout de leitura)
        )
        if r.status_code == 429:
            time.sleep(1)  # respeita rate limit e tenta só mais uma vez
            r = sessao_tmdb.get(
                f"https://api.themoviedb.org/3/find/{tconst}",
                params={"api_key": TMDB_API_KEY, "external_source": "imdb_id"},
                timeout=(5, 10),
            )
        r.raise_for_status()
        dados = r.json()
        achados = dados.get("movie_results") or dados.get("tv_results")
        if not achados:
            return (tconst, None, None)

        tmdb_id = achados[0]["id"]
        eh_tv = bool(dados.get("tv_results")) and not dados.get("movie_results")
        tipo = "tv" if eh_tv else "movie"

        detalhes = sessao_tmdb.get(
            f"https://api.themoviedb.org/3/{tipo}/{tmdb_id}",
            params={"api_key": TMDB_API_KEY},
            timeout=(5, 10),
        ).json()

        paises = detalhes.get("production_countries") or []
        if not paises:
            return (tconst, None, None)

        pais = paises[0]
        return (tconst, pais.get("iso_3166_1", ""), pais.get("name", ""))
    except Exception:
        return (tconst, None, None)


resultados_tmdb = []

if ids_sem_pais and TMDB_API_KEY:
    print(f"\n[2/3] Consultando {len(ids_sem_pais):,} filmes sem país via TMDb "
          f"({TMDB_WORKERS} em paralelo)...", flush=True)
    inicio_tmdb = time.time()
    concluidos = 0

    with ThreadPoolExecutor(max_workers=TMDB_WORKERS) as executor:
        futuros = {executor.submit(consultar_tmdb, tconst): tconst for tconst in ids_sem_pais}

        for futuro in as_completed(futuros):
            tconst, codigo, nome = futuro.result()
            concluidos += 1

            if codigo and nome:
                nome_corrigido = normalizar_pais(nome) or "Desconhecido"
                resultados_tmdb.append({
                    "tconst": tconst,
                    "country": codigo,
                    "countryLabel": nome_corrigido,
                    "fonte": "tmdb",
                })

            if concluidos % 100 == 0 or concluidos == len(ids_sem_pais):
                decorrido = time.time() - inicio_tmdb
                por_item = decorrido / concluidos
                restante = por_item * (len(ids_sem_pais) - concluidos)
                print(
                    f"   Progresso TMDb: {concluidos}/{len(ids_sem_pais)} "
                    f"({decorrido:.0f}s decorridos, ~{restante:.0f}s restantes)...",
                    flush=True
                )

    print(f"\n✓ TMDb encontrou {len(resultados_tmdb):,} de {len(ids_sem_pais):,}", flush=True)
else:
    if not TMDB_API_KEY:
        print("\n[2/3] Etapa TMDb pulada — TMDB_API_KEY não encontrada no arquivo .env.")
    else:
        print("\n[2/3] Etapa TMDb pulada (sem filmes pendentes).")

ids_achados_tmdb = {r["tconst"] for r in resultados_tmdb}
ids_ainda_sem_pais = [id_ for id_ in ids_sem_pais if id_ not in ids_achados_tmdb]


# ==========================================
# ETAPA 3: title.akas.tsv (offline, fallback do próprio IMDb)
# ==========================================
resultados_akas = []

if ids_ainda_sem_pais and ARQUIVO_AKAS.exists():
    print(f"\n[3/3] Consultando {len(ids_ainda_sem_pais):,} filmes restantes no title.akas.tsv local...")
    akas = pd.read_csv(
        ARQUIVO_AKAS,
        sep="\t",
        dtype=str,
        na_values="\\N",
        usecols=["titleId", "region"],
    )
    akas = akas[akas["titleId"].isin(ids_ainda_sem_pais) & akas["region"].notna()]

    akas_validos = akas[akas["region"] != "XWW"]
    primeira_regiao = akas_validos.drop_duplicates(subset="titleId", keep="first")

    for _, linha in primeira_regiao.iterrows():
        codigo = linha["region"]
        nome = normalizar_pais(codigo) or "Desconhecido"
        resultados_akas.append({
            "tconst": linha["titleId"],
            "country": codigo,
            "countryLabel": nome,
            "fonte": "akas",
        })
    print(f"✓ title.akas.tsv encontrou {len(resultados_akas):,} de {len(ids_ainda_sem_pais):,}")
elif ids_ainda_sem_pais:
    print(f"\n[3/3] Etapa akas pulada — arquivo não encontrado em {ARQUIVO_AKAS}.")
    print("      Baixe em https://datasets.imdbws.com/title.akas.tsv.gz e salve na pasta dados/.")
else:
    print("\n[3/3] Nenhum filme restante para consultar no title.akas.tsv.")


# ==========================================
# CONSOLIDAR RESULTADOS DAS 3 ETAPAS E GRAVAR NO BANCO
# ==========================================
todos_novos = resultados_wikidata + resultados_tmdb + resultados_akas

ids_com_fonte = {r["tconst"] for r in todos_novos}
ids_a_marcar_desconhecido = ids_novos_sem_pais + [
    id_ for id_ in ids_pendentes_cache if id_ not in ids_com_fonte
]
for id_ in set(ids_a_marcar_desconhecido) - ids_com_fonte:
    todos_novos.append({
        "tconst": id_,
        "country": "N/A",
        "countryLabel": "Desconhecido",
        "fonte": "nenhuma",
    })

if todos_novos:
    novos_df = pd.DataFrame(todos_novos)
    ids_atualizados = set(novos_df["tconst"])

    # Remove do cache em memória as linhas antigas dos IDs reprocessados
    cache = cache[~cache["tconst"].isin(ids_atualizados)]
    cache = pd.concat([cache, novos_df], ignore_index=True)

cache = cache.drop_duplicates(subset=["tconst", "country"])

# Grava a tabela inteira de volta no banco (substituindo a versão anterior)
cache.to_sql("cache_paises", conn, if_exists="replace", index=False)
conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_cache_tconst_country ON cache_paises(tconst, country)")
conn.commit()

print(f"\n✓ Cache atualizado no banco: {BANCO}")
print(f"✓ Total de {len(cache):,} relações no cache")
print("\nResumo por fonte (apenas filmes reprocessados nesta execução):")
if todos_novos:
    print(pd.DataFrame(todos_novos)["fonte"].value_counts().to_string())

# Backup em CSV do cache
cache.to_csv(BACKUP_CACHE, index=False, encoding="utf-8")
print(f"✓ Backup do cache salvo em: {BACKUP_CACHE}")

# ==========================================
# MESCLAR COM A BASE PRINCIPAL
# ==========================================
filmes_com_paises = filmes.merge(cache, on="tconst", how="left")

# ==========================================
# TRATAMENTO FINAL + IA (último recurso, só para o que sobrou)
# ==========================================
filmes_com_paises = tratar_paises.aplicar_tratamento_paises(filmes_com_paises)

# ==========================================
# GRAVAR RESULTADO DA IA DE VOLTA NO cache_paises
# (a IA pode ter resolvido países que ficaram "Desconhecido" antes)
# ==========================================
atualizacoes_ia = filmes_com_paises[["tconst", "countryLabel"]].dropna(subset=["tconst"]).copy()
atualizacoes_ia["country"] = "IA"
atualizacoes_ia["fonte"] = "ia"

# Só grava as que realmente vieram de uma resolução da IA (estavam
# pendentes antes desta execução)
ids_processados_pela_ia = set(ids_a_marcar_desconhecido)
atualizacoes_ia = atualizacoes_ia[atualizacoes_ia["tconst"].isin(ids_processados_pela_ia)]

if not atualizacoes_ia.empty:
    cache_atual = pd.read_sql("SELECT * FROM cache_paises", conn, dtype={"tconst": "string"})
    cache_atual = cache_atual[~cache_atual["tconst"].isin(atualizacoes_ia["tconst"])]
    cache_atual = pd.concat([cache_atual, atualizacoes_ia], ignore_index=True)
    cache_atual = cache_atual.drop_duplicates(subset=["tconst", "country"])
    cache_atual.to_sql("cache_paises", conn, if_exists="replace", index=False)
    conn.commit()
    print(f"\n✓ {len(atualizacoes_ia):,} resoluções da IA gravadas no cache_paises.")

conn.close()

# Backup em CSV do resultado final
filmes_com_paises.to_csv(BACKUP_SAIDA, index=False, encoding="utf-8")
print(f"\n✓ Processo completo! Backup salvo em: {BACKUP_SAIDA}")
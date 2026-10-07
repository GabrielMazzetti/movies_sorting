import sqlite3
import random
import unicodedata
from pathlib import Path
import pandas as pd

def normalizar_texto(texto):
    if not texto: return ""
    texto = texto.lower().strip()
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return texto

MAPEAMENTO_GENEROS = {
    "acao": "Action",
    "aventura": "Adventure",
    "animacao": "Animation",
    "desenho": "Animation",
    "biografia": "Biography",
    "comedia": "Comedy",
    "crime": "Crime",
    "policial": "Crime",
    "documentario": "Documentary",
    "drama": "Drama",
    "familia": "Family",
    "fantasia": "Fantasy",
    "historia": "History",
    "historico": "History",
    "terror": "Horror",
    "horror": "Horror",
    "musica": "Music",
    "musical": "Musical",
    "misterio": "Mystery",
    "romance": "Romance",
    "romantica": "Romance",
    "ficcao": "Sci-Fi",
    "ficcao cientifica": "Sci-Fi",
    "sci-fi": "Sci-Fi",
    "esporte": "Sport",
    "suspense": "Thriller",
    "thriller": "Thriller",
    "guerra": "War",
    "faroeste": "Western",
    "western": "Western"
}

def construir_where(filtros):
    clausulas = []
    params = []
    
    if not filtros:
        return "", []
        
    if "genero" in filtros and filtros["genero"]:
        # Tira acentos e minúsculas
        gen_input = normalizar_texto(filtros["genero"])
        # Traduz para o inglês do IMDb (se não achar, tenta usar a palavra original)
        gen_ingles = MAPEAMENTO_GENEROS.get(gen_input, filtros["genero"])
        
        clausulas.append("genres LIKE ?")
        params.append(f"%{gen_ingles}%")

        
    if "ano_min" in filtros and filtros["ano_min"]:
        clausulas.append("startYear >= ?")
        params.append(int(filtros["ano_min"]))
        
    if "ano_max" in filtros and filtros["ano_max"]:
        clausulas.append("startYear <= ?")
        params.append(int(filtros["ano_max"]))
        
    if "duracao_min" in filtros and filtros["duracao_min"]:
        clausulas.append("runtimeMinutes >= ?")
        params.append(int(filtros["duracao_min"]))
        
    if "duracao_max" in filtros and filtros["duracao_max"]:
        clausulas.append("runtimeMinutes <= ?")
        params.append(int(filtros["duracao_max"]))

    if "nota_min" in filtros and filtros["nota_min"]:
        clausulas.append("averageRating >= ?")
        params.append(float(filtros["nota_min"]))
        
    if "votos_min" in filtros and filtros["votos_min"]:
        clausulas.append("numVotes >= ?")
        params.append(int(filtros["votos_min"]))

    if clausulas:
        return " AND " + " AND ".join(clausulas), params
    return "", []


def realizar_sorteio(opcao="1", filtros=None):
    """
    Executa a lógica de sorteio baseada na opção (1, 2 ou 3) e filtros adicionais.
    Retorna um dicionário com as informações do filme sorteado ou None em caso de erro.
    """
    BANCO = Path("dados/filmes_global.db")
    PASTA_SORTEIOS = Path("sorteios")
    PASTA_SORTEIOS.mkdir(exist_ok=True)

    if not BANCO.exists():
        return None

    where_sql, params = construir_where(filtros)

    with sqlite3.connect(BANCO) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if str(opcao) == "3":
            # 3. Filme totalmente aleatório
            query = f"SELECT * FROM filmes_final WHERE 1=1 {where_sql} ORDER BY RANDOM() LIMIT 1"
            cursor.execute(query, params)
            escolhido = cursor.fetchone()
            
            if not escolhido:
                return {"error": "Nenhum filme encontrado com esses filtros."}
                
            pais = escolhido["pais_sorteavel"]
            tipo_sorteio = "FILME TOTALMENTE ALEATÓRIO"
            
        else:
            # Sorteia o país primeiro baseado nos filmes que passam nos filtros!
            # Para não sortear um país que não tem nenhum filme compatível com o filtro.
            query_pais = f"SELECT DISTINCT pais_sorteavel FROM filmes_final WHERE 1=1 {where_sql} ORDER BY RANDOM() LIMIT 1"
            cursor.execute(query_pais, params)
            pais_row = cursor.fetchone()
            
            if not pais_row:
                return {"error": "Nenhum filme encontrado com esses filtros em nenhum país."}
                
            pais = pais_row["pais_sorteavel"]
            
            if str(opcao) == "2":
                # 2. Filme aleatório do país
                query = f"SELECT * FROM filmes_final WHERE pais_sorteavel = ? {where_sql} ORDER BY RANDOM() LIMIT 1"
                cursor.execute(query, [pais] + params)
                escolhido = cursor.fetchone()
                tipo_sorteio = f"FILME ALEATÓRIO: {pais.upper()}"
            else:
                # 1. Melhor filme do país (Padrão)
                query = f"SELECT * FROM filmes_final WHERE pais_sorteavel = ? {where_sql} ORDER BY indice DESC, averageRating DESC, numVotes DESC LIMIT 1"
                cursor.execute(query, [pais] + params)
                escolhido = cursor.fetchone()
                tipo_sorteio = f"MELHOR FILME: {pais.upper()}"

    # ==========================
    # BUSCAR POSTER NO TMDB E COORDENADAS DO PAÍS
    # ==========================
    import os
    import requests
    from dotenv import load_dotenv
    from geopy.geocoders import Nominatim
    
    load_dotenv()
    tmdb_key = os.environ.get("TMDB_API_KEY")
    poster_url = ""
    
    if tmdb_key:
        try:
            r = requests.get(
                f"https://api.themoviedb.org/3/find/{escolhido['tconst']}?api_key={tmdb_key}&external_source=imdb_id",
                timeout=5
            )
            if r.status_code == 200:
                dados_tmdb = r.json()
                resultados_tmdb = dados_tmdb.get("movie_results") or dados_tmdb.get("tv_results")
                if resultados_tmdb and resultados_tmdb[0].get("poster_path"):
                    poster_url = f"https://image.tmdb.org/t/p/w500{resultados_tmdb[0]['poster_path']}"
        except Exception as e:
            print("Erro ao buscar poster:", e)

    coords = None
    try:
        geolocator = Nominatim(user_agent="filmes_global_app")
        location = geolocator.geocode(pais)
        if location:
            coords = {"lat": location.latitude, "lon": location.longitude}
    except Exception:
        pass

    # Monta o dicionário de resultados para devolver à interface
    resultado = {
        "tipo": tipo_sorteio,
        "pais": pais,
        "titulo": escolhido["primaryTitle"],
        "ano": int(escolhido["startYear"]) if escolhido["startYear"] else "Desconhecido",
        "nota": float(escolhido["averageRating"]),
        "votos": int(escolhido["numVotes"]),
        "indice": float(escolhido["indice"]),
        "imdb_id": escolhido["tconst"],
        "duracao": int(escolhido["runtimeMinutes"]) if escolhido["runtimeMinutes"] else "Desconhecido",
        "generos": escolhido["genres"],
        "poster_url": poster_url,
        "coordenadas": coords
    }

    # Salva o arquivo TXT do histórico
    arquivo_txt = PASTA_SORTEIOS / f"{pais}_{resultado['imdb_id']}.txt"
    conteudo = f"""
========================================
KINOMAP
========================================
MODO DO SORTEIO: {resultado['tipo']}
PAÍS: {resultado['pais']}

FILME: {resultado['titulo']}
ANO: {resultado['ano']}
DURAÇÃO: {resultado['duracao']} min
GÊNEROS: {resultado['generos']}

NOTA IMDb: {resultado['nota']}
AVALIAÇÕES: {resultado['votos']:,}
ÍNDICE: {resultado['indice']:.6f}

IMDb ID: {resultado['imdb_id']}
POSTER URL: {resultado['poster_url']}
"""
    with open(arquivo_txt, "w", encoding="utf-8") as arquivo:
        arquivo.write(conteudo.strip())

    return resultado

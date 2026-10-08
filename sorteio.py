import sqlite3
import random
import unicodedata
from pathlib import Path

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

    if "pais" in filtros and filtros["pais"]:
        try:
            from normalizar_pais import normalizar_pais
            pais_norm = normalizar_pais(filtros["pais"])
            if pais_norm:
                clausulas.append("pais_sorteavel = ?")
                params.append(pais_norm)
            else:
                clausulas.append("pais_sorteavel LIKE ?")
                params.append(f"%{filtros['pais']}%")
        except:
            clausulas.append("pais_sorteavel LIKE ?")
            params.append(f"%{filtros['pais']}%")

    if "diretor" in filtros and filtros["diretor"]:
        import os
        import requests
        from concurrent.futures import ThreadPoolExecutor
        
        tmdb_key = os.environ.get("TMDB_API_KEY")
        if tmdb_key:
            res = requests.get(f"https://api.themoviedb.org/3/search/person?api_key={tmdb_key}&query={filtros['diretor']}", timeout=5)
            if res.status_code == 200 and res.json().get("results"):
                person_id = res.json()["results"][0]["id"]
                res_cred = requests.get(f"https://api.themoviedb.org/3/person/{person_id}/movie_credits?api_key={tmdb_key}", timeout=5)
                if res_cred.status_code == 200:
                    crew = res_cred.json().get("crew", [])
                    directed_ids = [m["id"] for m in crew if m.get("job") == "Director"]
                    
                    def get_imdb(tmdb_id):
                        try:
                            r = requests.get(f"https://api.themoviedb.org/3/movie/{tmdb_id}/external_ids?api_key={tmdb_key}", timeout=5)
                            if r.status_code == 200: return r.json().get("imdb_id")
                        except: pass
                        return None
                        
                    imdb_ids = []
                    if directed_ids:
                        with ThreadPoolExecutor(max_workers=10) as executor:
                            imdb_ids = [i for i in executor.map(get_imdb, directed_ids) if i]
                            
                    if imdb_ids:
                        placeholders = ",".join(["?"] * len(imdb_ids))
                        clausulas.append(f"tconst IN ({placeholders})")
                        params.extend(imdb_ids)
                    else:
                        clausulas.append("tconst = 'NO_MATCH'")
            else:
                clausulas.append("tconst = 'NO_MATCH'")
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

        if filtros and filtros.get("titulo"):
            query = "SELECT * FROM filmes_final WHERE primaryTitle LIKE ? COLLATE NOCASE ORDER BY numVotes DESC LIMIT 1"
            cursor.execute(query, [f"%{filtros['titulo']}%"])
            escolhido = cursor.fetchone()
            
            if not escolhido:
                return {"error": "Nenhum filme encontrado com esse título e filtros."}
                
            pais = escolhido["pais_sorteavel"]
            tipo_sorteio = "BUSCA POR TÍTULO"
        
        elif str(opcao) == "3":
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
        "indice": round(float(escolhido["indice"]), 2),
        "imdb_id": escolhido["tconst"],
        "duracao": int(escolhido["runtimeMinutes"]) if escolhido["runtimeMinutes"] else "Desconhecido",
        "generos": escolhido["genres"],
        "poster_url": poster_url,
        "coordenadas": coords
    }

    return resultado

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
            from normalizar_pais import normalizar_pais, MAPA_NORMALIZACAO
            pais_norm = normalizar_pais(filtros["pais"])
            if pais_norm:
                variantes = [k for k, v in MAPA_NORMALIZACAO.items() if v == pais_norm]
                variantes.append(pais_norm)
                placeholders = ', '.join(['?'] * len(variantes))
                clausulas.append(f"pais_sorteavel IN ({placeholders})")
                params.extend(variantes)
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

        if filtros and (filtros.get("titulo") or filtros.get("imdb_id")):
            import os, requests, re
            from dotenv import load_dotenv
            load_dotenv()
            tmdb_key = os.environ.get("TMDB_API_KEY")
            escolhido = None
            geral = None

            imdb_id_val = str(filtros.get("imdb_id") or "").strip()
            if imdb_id_val.startswith("tmdb_") and tmdb_key:
                tmdb_num = imdb_id_val.replace("tmdb_", "")
                try:
                    r_ext = requests.get(f"https://api.themoviedb.org/3/movie/{tmdb_num}/external_ids", params={"api_key": tmdb_key}, timeout=4)
                    if r_ext.status_code == 200 and r_ext.json().get("imdb_id"):
                        imdb_id_val = r_ext.json()["imdb_id"]
                        filtros["imdb_id"] = imdb_id_val
                except Exception:
                    pass

            if imdb_id_val and imdb_id_val.startswith("tt"):
                query = f"SELECT * FROM filmes_final WHERE tconst = ? {where_sql} LIMIT 1"
                cursor.execute(query, [imdb_id_val] + params)
                escolhido = cursor.fetchone()
                if not escolhido:
                    cursor.execute("SELECT * FROM filmes_final WHERE tconst = ? LIMIT 1", [imdb_id_val])
                    escolhido = cursor.fetchone()
                if not escolhido:
                    query_global = """
                        SELECT f.*, r.averageRating, r.numVotes 
                        FROM filmes f 
                        LEFT JOIN ratings r ON f.tconst = r.tconst 
                        WHERE f.tconst = ? 
                        LIMIT 1
                    """
                    cursor.execute(query_global, [imdb_id_val])
                    geral = cursor.fetchone()
            elif not imdb_id_val.startswith("tmdb_"):
                titulo_limpo = re.sub(r" \(\d{4}\)$", "", (filtros.get("titulo") or "").strip())
                titulo_limpo = re.sub(r" \([^)]+\)$", "", titulo_limpo).strip()
                filtros["titulo"] = titulo_limpo
                query = f"SELECT * FROM filmes_final WHERE (primaryTitle LIKE ? OR originalTitle LIKE ?) COLLATE NOCASE {where_sql} ORDER BY numVotes DESC LIMIT 1"
                cursor.execute(query, [f"%{titulo_limpo}%", f"%{titulo_limpo}%"] + params)
                escolhido = cursor.fetchone()
                
                if not escolhido:
                    query_global = """
                        SELECT f.*, r.averageRating, r.numVotes 
                        FROM filmes f 
                        LEFT JOIN ratings r ON f.tconst = r.tconst 
                        WHERE (f.primaryTitle LIKE ? OR f.originalTitle LIKE ?) COLLATE NOCASE 
                        ORDER BY COALESCE(r.numVotes, 0) DESC LIMIT 1
                    """
                    cursor.execute(query_global, [f"%{titulo_limpo}%", f"%{titulo_limpo}%"])
                    geral = cursor.fetchone()

            if not escolhido and geral:
                # Tenta descobrir o país no cache_paises ou via TMDb
                pais_geral = "Desconhecido"
                try:
                    c_pais = cursor.execute("SELECT countryLabel FROM cache_paises WHERE tconst = ? AND countryLabel != 'Desconhecido' LIMIT 1", [geral["tconst"]]).fetchone()
                    if c_pais and c_pais[0]:
                        from normalizar_pais import normalizar_pais
                        pais_geral = normalizar_pais(c_pais[0]) or c_pais[0]
                except Exception:
                    pass
                escolhido = {
                    "tconst": geral["tconst"],
                    "primaryTitle": geral["primaryTitle"],
                    "startYear": geral["startYear"],
                    "runtimeMinutes": geral["runtimeMinutes"],
                    "genres": geral["genres"],
                    "averageRating": geral["averageRating"] or 0.0,
                    "numVotes": geral["numVotes"] or 0,
                    "indice": float(geral["averageRating"] or 0.0),
                    "pais_sorteavel": pais_geral
                }

            if not escolhido and tmdb_key:
                # Fallback direto na API do TMDb (encontra títulos em português e filmes raríssimos fora do dump)
                try:
                    tmdb_id_lookup = None
                    if imdb_id_val.startswith("tmdb_"):
                        tmdb_id_lookup = imdb_id_val.replace("tmdb_", "")
                    else:
                        q_str = filtros.get("titulo", "")
                        r_s = requests.get("https://api.themoviedb.org/3/search/movie", params={"api_key": tmdb_key, "query": q_str, "language": "pt-BR"}, timeout=4)
                        if r_s.status_code == 200 and r_s.json().get("results"):
                            tmdb_id_lookup = r_s.json()["results"][0]["id"]
                    if tmdb_id_lookup:
                        r_det = requests.get(f"https://api.themoviedb.org/3/movie/{tmdb_id_lookup}", params={"api_key": tmdb_key, "language": "pt-BR"}, timeout=4)
                        if r_det.status_code == 200:
                            det = r_det.json()
                            tconst_tmdb = det.get("imdb_id") or f"tmdb_{tmdb_id_lookup}"
                            # Se tiver imdb_id e estiver no banco local, aproveita os votos/notas do IMDb!
                            if tconst_tmdb.startswith("tt"):
                                cursor.execute("SELECT * FROM filmes_final WHERE tconst = ? LIMIT 1", [tconst_tmdb])
                                row_ff = cursor.fetchone()
                                if row_ff:
                                    escolhido = row_ff
                                else:
                                    cursor.execute("SELECT f.*, r.averageRating, r.numVotes FROM filmes f LEFT JOIN ratings r ON f.tconst = r.tconst WHERE f.tconst = ? LIMIT 1", [tconst_tmdb])
                                    row_f = cursor.fetchone()
                                    if row_f:
                                        escolhido = {
                                            "tconst": row_f["tconst"],
                                            "primaryTitle": det.get("title") or row_f["primaryTitle"],
                                            "startYear": row_f["startYear"],
                                            "runtimeMinutes": row_f["runtimeMinutes"],
                                            "genres": row_f["genres"],
                                            "averageRating": row_f["averageRating"] or det.get("vote_average") or 0.0,
                                            "numVotes": row_f["numVotes"] or det.get("vote_count") or 0,
                                            "indice": float(row_f["averageRating"] or det.get("vote_average") or 0.0),
                                            "pais_sorteavel": "Desconhecido"
                                        }
                            if not escolhido:
                                from normalizar_pais import normalizar_pais
                                orig_countries = det.get("origin_country") or [c.get("iso_3166_1") for c in (det.get("production_countries") or []) if c.get("iso_3166_1")]
                                pais_tmdb = normalizar_pais(orig_countries[0]) if orig_countries else "Desconhecido"
                                escolhido = {
                                    "tconst": tconst_tmdb,
                                    "primaryTitle": det.get("title") or det.get("original_title"),
                                    "startYear": (det.get("release_date") or "")[:4] or None,
                                    "runtimeMinutes": det.get("runtime"),
                                    "genres": ", ".join(g["name"] for g in (det.get("genres") or [])),
                                    "averageRating": det.get("vote_average") or 0.0,
                                    "numVotes": det.get("vote_count") or 0,
                                    "indice": float(det.get("vote_average") or 0.0),
                                    "pais_sorteavel": pais_tmdb or "Desconhecido"
                                }
                            elif escolhido["pais_sorteavel"] == "Desconhecido":
                                from normalizar_pais import normalizar_pais
                                orig_countries = det.get("origin_country") or [c.get("iso_3166_1") for c in (det.get("production_countries") or []) if c.get("iso_3166_1")]
                                if orig_countries:
                                    escolhido["pais_sorteavel"] = normalizar_pais(orig_countries[0]) or orig_countries[0]
                except Exception:
                    pass

            if not escolhido:
                return {"error": "Nenhum filme encontrado com esse título."}
                
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
    
    duracao_val = escolhido["runtimeMinutes"] if "runtimeMinutes" in escolhido.keys() and escolhido["runtimeMinutes"] else None

    if tmdb_key:
        try:
            tconst_str = str(escolhido["tconst"])
            tmdb_movie = None
            if tconst_str.startswith("tmdb_"):
                tmdb_id_direct = tconst_str.replace("tmdb_", "")
                r_det = requests.get(f"https://api.themoviedb.org/3/movie/{tmdb_id_direct}?api_key={tmdb_key}&language=pt-BR", timeout=5)
                if r_det.status_code == 200:
                    tmdb_movie = r_det.json()
            else:
                r = requests.get(
                    f"https://api.themoviedb.org/3/find/{tconst_str}?api_key={tmdb_key}&external_source=imdb_id&language=pt-BR",
                    timeout=5
                )
                if r.status_code == 200:
                    dados_tmdb = r.json()
                    resultados_tmdb = dados_tmdb.get("movie_results") or dados_tmdb.get("tv_results")
                    if resultados_tmdb:
                        tmdb_movie = resultados_tmdb[0]
                        if not duracao_val or not pais or pais == "Desconhecido":
                            r_det = requests.get(f"https://api.themoviedb.org/3/movie/{tmdb_movie['id']}?api_key={tmdb_key}&language=pt-BR", timeout=5)
                            if r_det.status_code == 200:
                                tmdb_movie = r_det.json()

            if tmdb_movie:
                if tmdb_movie.get("poster_path"):
                    poster_url = f"https://image.tmdb.org/t/p/w500{tmdb_movie['poster_path']}"
                if not duracao_val and tmdb_movie.get("runtime"):
                    duracao_val = tmdb_movie.get("runtime")
                if (not pais or pais == "Desconhecido"):
                    from normalizar_pais import normalizar_pais
                    orig_c = tmdb_movie.get("origin_country") or [c.get("iso_3166_1") for c in (tmdb_movie.get("production_countries") or []) if c.get("iso_3166_1")]
                    if orig_c:
                        pais = normalizar_pais(orig_c[0]) or orig_c[0]
        except Exception as e:
            print("Erro ao buscar poster/detalhes:", e)

    coords = None
    try:
        if pais and pais != "Desconhecido":
            geolocator = Nominatim(user_agent="filmes_global_app")
            location = geolocator.geocode(pais)
            if location:
                coords = {"lat": location.latitude, "lon": location.longitude}
    except Exception:
        pass

    # Monta o dicionário de resultados para devolver à interface
    resultado = {
        "tipo": tipo_sorteio,
        "pais": pais or "Desconhecido",
        "titulo": escolhido["primaryTitle"],
        "ano": int(escolhido["startYear"]) if escolhido["startYear"] else "Desconhecido",
        "nota": round(float(escolhido["averageRating"] or 0.0), 1),
        "votos": int(escolhido["numVotes"] or 0),
        "indice": round(float(escolhido["indice"] or 0.0), 2),
        "imdb_id": escolhido["tconst"],
        "duracao": int(duracao_val) if duracao_val else "Desconhecido",
        "generos": escolhido["genres"],
        "poster_url": poster_url,
        "coordenadas": coords
    }

    return resultado

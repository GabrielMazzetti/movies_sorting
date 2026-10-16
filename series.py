import sqlite3
import random
import requests
import os
from dotenv import load_dotenv
from pathlib import Path
from geopy.geocoders import Nominatim

load_dotenv()
TMDB_KEY = os.environ.get("TMDB_API_KEY")

DB_PATH = Path("dados/series.db")
_cache_countries = []

def get_tmdb_countries():
    global _cache_countries
    if not _cache_countries:
        try:
            r = requests.get(f"https://api.themoviedb.org/3/configuration/countries?api_key={TMDB_KEY}&language=pt-BR", timeout=5)
            if r.status_code == 200:
                _cache_countries.extend(r.json())
        except:
            pass
    return _cache_countries

def realizar_sorteio_serie(opcao="1", filtros=None):
    if filtros is None:
        filtros = {}
        
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            
            import re
            titulo_filtro = re.sub(r" \([^)]+\)$", "", filtros.get("titulo", "").strip()).strip()
            imdb_id = filtros.get("imdb_id", "").strip()
            genero_filtro = filtros.get("genero", "").strip()
            ano_min = filtros.get("ano_min", "").strip()
            ano_max = filtros.get("ano_max", "").strip()
            nota_min = filtros.get("nota_min", "").strip()
            
            tmdb_id_direct = ""
            if imdb_id.startswith("tmdb_") and TMDB_KEY:
                tmdb_id_direct = imdb_id.replace("tmdb_", "")
                try:
                    r_ext = requests.get(f"https://api.themoviedb.org/3/tv/{tmdb_id_direct}/external_ids", params={"api_key": TMDB_KEY}, timeout=4)
                    if r_ext.status_code == 200 and r_ext.json().get("imdb_id"):
                        imdb_id = r_ext.json()["imdb_id"]
                except Exception:
                    pass

            query_conditions = []
            params = []
            
            if imdb_id and imdb_id.startswith("tt"):
                query_conditions.append("s.tconst = ?")
                params.append(imdb_id)
            elif titulo_filtro and not tmdb_id_direct:
                query_conditions.append("(s.primaryTitle LIKE ? OR s.originalTitle LIKE ?)")
                params.extend([f"%{titulo_filtro}%", f"%{titulo_filtro}%"])
            if genero_filtro:
                query_conditions.append("s.genres LIKE ?")
                params.append(f"%{genero_filtro}%")
            if ano_min:
                try:
                    query_conditions.append("s.startYear >= ?")
                    params.append(int(ano_min))
                except: pass
            if ano_max:
                try:
                    query_conditions.append("s.startYear <= ?")
                    params.append(int(ano_max))
                except: pass
            if nota_min:
                try:
                    query_conditions.append("r.averageRating >= ?")
                    params.append(float(nota_min))
                except: pass
                
            resultados = []
            if not tmdb_id_direct:
                base_sql = """
                    SELECT s.tconst, s.primaryTitle, s.startYear, s.genres, r.averageRating, r.numVotes 
                    FROM series s
                    LEFT JOIN series_ratings r ON s.tconst = r.tconst
                """
                if query_conditions:
                    base_sql += " WHERE " + " AND ".join(query_conditions)
                if imdb_id or titulo_filtro:
                    base_sql += " ORDER BY COALESCE(r.numVotes, 0) DESC LIMIT 20"
                else:
                    base_sql += " ORDER BY RANDOM() LIMIT 100"
                c.execute(base_sql, tuple(params))
                resultados = c.fetchall()

            if not resultados and TMDB_KEY and (titulo_filtro or tmdb_id_direct):
                try:
                    if not tmdb_id_direct:
                        r_s = requests.get("https://api.themoviedb.org/3/search/tv", params={"api_key": TMDB_KEY, "query": titulo_filtro, "language": "pt-BR"}, timeout=4)
                        if r_s.status_code == 200 and r_s.json().get("results"):
                            tmdb_id_direct = str(r_s.json()["results"][0]["id"])
                    if tmdb_id_direct:
                        r_det = requests.get(f"https://api.themoviedb.org/3/tv/{tmdb_id_direct}", params={"api_key": TMDB_KEY, "language": "pt-BR"}, timeout=4)
                        if r_det.status_code == 200:
                            det = r_det.json()
                            resultados = [(
                                f"tmdb_{tmdb_id_direct}",
                                det.get("name") or det.get("original_name"),
                                (det.get("first_air_date") or "")[:4],
                                ", ".join(g["name"] for g in (det.get("genres") or [])),
                                det.get("vote_average") or 0.0,
                                det.get("vote_count") or 0
                            )]
                except Exception:
                    pass
            
            if not resultados:
                return {"error": "Nenhuma série encontrada com esses filtros no banco de dados."}
                
            # Select top match if searching by title/id, otherwise random
            serie = resultados[0] if (imdb_id or titulo_filtro or tmdb_id_direct) else random.choice(resultados)
            tconst, title, year, genres, rating, votes = serie
            
            # Now we fetch details from TMDb API using the IMDb ID (tconst) or tmdb_id
            poster_url = ""
            nome_pais = "Desconhecido"
            duracao = "Desconhecido"
            tmdb_id = tmdb_id_direct
            coords = None
            
            if TMDB_KEY:
                try:
                    if not tmdb_id and str(tconst).startswith("tt"):
                        r_find = requests.get(f"https://api.themoviedb.org/3/find/{tconst}?api_key={TMDB_KEY}&external_source=imdb_id&language=pt-BR", timeout=5)
                        if r_find.status_code == 200:
                            tv_results = r_find.json().get("tv_results", [])
                            if tv_results:
                                tmdb_id = tv_results[0]["id"]
                    if tmdb_id:
                        r_det = requests.get(f"https://api.themoviedb.org/3/tv/{tmdb_id}?api_key={TMDB_KEY}&language=pt-BR", timeout=5)
                        if r_det.status_code == 200:
                            det = r_det.json()
                            poster_path = det.get("poster_path")
                            if poster_path:
                                poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
                                
                            eps = det.get("number_of_episodes", "Desconhecido")
                            temps = det.get("number_of_seasons", "Desconhecido")
                            duracao = f"{temps} Temp. / {eps} Eps."
                            
                            pais_iso = det.get("origin_country", [""])[0] if det.get("origin_country") else ""
                            if pais_iso:
                                for p in get_tmdb_countries():
                                    if p.get("iso_3166_1") == pais_iso:
                                        nome_pais = p.get("native_name", p.get("english_name", pais_iso))
                                        break
                except:
                    pass
                    
            if nome_pais != "Desconhecido":
                try:
                    geolocator = Nominatim(user_agent="filmes_global_app")
                    location = geolocator.geocode(nome_pais)
                    if location:
                        coords = {"lat": location.latitude, "lon": location.longitude}
                except:
                    pass

            return {
                "tipo": "BUSCA DE SÉRIE" if titulo_filtro else "SÉRIE ALEATÓRIA",
                "pais": nome_pais,
                "titulo": title,
                "ano": str(year) if year else "Desconhecido",
                "nota": round(float(rating), 1) if rating else "N/A",
                "votos": int(votes) if votes else 0,
                "indice": round(float(rating), 2) if rating else 0,
                "imdb_id": tconst,
                "duracao": duracao,
                "generos": genres if genres else "Sem categoria",
                "poster_url": poster_url,
                "coordenadas": coords,
                "tmdb_id": tmdb_id
            }

    except Exception as e:
        return {"error": f"Erro interno ao buscar série: {str(e)}"}

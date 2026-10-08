import os
import random
import requests
from dotenv import load_dotenv

load_dotenv()
TMDB_KEY = os.environ.get("TMDB_API_KEY")

_cache_genres = {}
_cache_countries = []

def get_tmdb_genres():
    if not _cache_genres:
        try:
            r = requests.get(f"https://api.themoviedb.org/3/genre/tv/list?api_key={TMDB_KEY}&language=pt-BR", timeout=5)
            if r.status_code == 200:
                for g in r.json().get("genres", []):
                    _cache_genres[g["name"].lower()] = g["id"]
        except:
            pass
    return _cache_genres

def get_tmdb_countries():
    if not _cache_countries:
        try:
            r = requests.get(f"https://api.themoviedb.org/3/configuration/countries?api_key={TMDB_KEY}&language=pt-BR", timeout=5)
            if r.status_code == 200:
                _cache_countries.extend(r.json())
        except:
            pass
    return _cache_countries

def realizar_sorteio_serie(opcao="1", filtros=None):
    if not TMDB_KEY:
        return {"error": "Chave da API do TMDB não configurada."}
    
    if filtros is None:
        filtros = {}
        
    params = {
        "api_key": TMDB_KEY,
        "language": "pt-BR",
        "include_null_first_air_dates": "false"
    }

    # Tratamento de gênero
    if filtros.get("genero"):
        generos_dict = get_tmdb_genres()
        gen_input = filtros["genero"].lower().strip()
        gen_id = None
        for name, gid in generos_dict.items():
            if gen_input in name:
                gen_id = gid
                break
        if gen_id:
            params["with_genres"] = str(gen_id)

    # Tratamento de país
    country_name = "Desconhecido"
    if filtros.get("pais"):
        paises_list = get_tmdb_countries()
        pais_input = filtros["pais"].lower().strip()
        iso = None
        for p in paises_list:
            native = p.get("native_name", "").lower()
            english = p.get("english_name", "").lower()
            iso_code = p.get("iso_3166_1", "").lower()
            if pais_input == native or pais_input == english or pais_input == iso_code:
                iso = p.get("iso_3166_1")
                country_name = p.get("native_name")
                break
        if iso:
            params["with_origin_country"] = iso
            
    if filtros.get("ano_min"): params["first_air_date.gte"] = f"{filtros['ano_min']}-01-01"
    if filtros.get("ano_max"): params["first_air_date.lte"] = f"{filtros['ano_max']}-12-31"
    if filtros.get("nota_min"): params["vote_average.gte"] = float(filtros["nota_min"])
    
    tipo_sorteio = "SÉRIE GLOBAL"
    if str(opcao) == "3":
        params["sort_by"] = "popularity.desc"
    elif str(opcao) == "2":
        params["sort_by"] = "popularity.desc"
        tipo_sorteio = f"SÉRIE ALEATÓRIA: {country_name.upper()}" if params.get("with_origin_country") else "SÉRIE ALEATÓRIA"
    else: # 1 (Melhor)
        params["sort_by"] = "vote_average.desc"
        params["vote_count.gte"] = 200
        tipo_sorteio = f"MELHOR SÉRIE: {country_name.upper()}" if params.get("with_origin_country") else "MELHOR SÉRIE"
        
    try:
        if filtros.get("titulo"):
            query_titulo = filtros["titulo"].strip()
            r = requests.get(f"https://api.themoviedb.org/3/search/tv?api_key={TMDB_KEY}&query={query_titulo}&language=pt-BR", timeout=10)
            if r.status_code == 200 and r.json().get("results"):
                serie_escolhida = r.json()["results"][0]
                tipo_sorteio = "BUSCA POR TÍTULO"
            else:
                return {"error": "Nenhuma série encontrada com esse título."}
        elif filtros.get("diretor"):
            diretor_nome = filtros["diretor"].strip()
            r_person = requests.get(f"https://api.themoviedb.org/3/search/person?api_key={TMDB_KEY}&query={diretor_nome}", timeout=10)
            if r_person.status_code == 200 and r_person.json().get("results"):
                person_id = r_person.json()["results"][0]["id"]
                r_cred = requests.get(f"https://api.themoviedb.org/3/person/{person_id}/tv_credits?api_key={TMDB_KEY}", timeout=10)
                if r_cred.status_code == 200:
                    crew = r_cred.json().get("crew", [])
                    shows = {}
                    for c in crew:
                        job = c.get("job", "")
                        if job in ["Director", "Creator", "Executive Producer", "Writer", "Producer", "Showrunner"]:
                            shows[c["id"]] = c
                    
                    resultados = list(shows.values())
                    
                    if params.get("with_genres"):
                        gen = int(params["with_genres"])
                        resultados = [s for s in resultados if gen in s.get("genre_ids", [])]
                    if params.get("with_origin_country"):
                        iso = params["with_origin_country"]
                        resultados = [s for s in resultados if iso in s.get("origin_country", [])]
                    if params.get("first_air_date.gte"):
                        ano_min = params["first_air_date.gte"]
                        resultados = [s for s in resultados if s.get("first_air_date") and s["first_air_date"] >= ano_min]
                    if params.get("first_air_date.lte"):
                        ano_max = params["first_air_date.lte"]
                        resultados = [s for s in resultados if s.get("first_air_date") and s["first_air_date"] <= ano_max]
                    if params.get("vote_average.gte"):
                        nota_min = params["vote_average.gte"]
                        resultados = [s for s in resultados if s.get("vote_average", 0) >= nota_min]
                        
                    if not resultados:
                        return {"error": f"Nenhuma série encontrada para o diretor/criador '{diretor_nome}' com os filtros aplicados."}
                    
                    if str(opcao) == "1":
                        resultados = sorted(resultados, key=lambda x: x.get("vote_average", 0), reverse=True)
                        serie_escolhida = resultados[0]
                    else:
                        serie_escolhida = random.choice(resultados)
                else:
                    return {"error": "Erro ao buscar créditos do diretor."}
            else:
                return {"error": f"Diretor/Criador '{diretor_nome}' não encontrado."}
        else:
            r = requests.get("https://api.themoviedb.org/3/discover/tv", params=params, timeout=10)
            if r.status_code != 200:
                return {"error": "Erro ao consultar TMDb para descobrir séries."}
                
            dados = r.json()
            total_pages = min(dados.get("total_pages", 1), 500)
            resultados = dados.get("results", [])
            
            if not resultados:
                return {"error": "Nenhuma série encontrada com esses filtros."}
                
            if str(opcao) in ["2", "3"] and total_pages > 1:
                page = random.randint(1, total_pages)
                params["page"] = page
                r2 = requests.get("https://api.themoviedb.org/3/discover/tv", params=params, timeout=10)
                if r2.status_code == 200:
                    resultados = r2.json().get("results", resultados)
                    
            serie_escolhida = random.choice(resultados)

        serie_id = serie_escolhida["id"]
        
        r_det = requests.get(f"https://api.themoviedb.org/3/tv/{serie_id}?api_key={TMDB_KEY}&language=pt-BR", timeout=10)
        if r_det.status_code == 200:
            detalhes = r_det.json()
        else:
            detalhes = serie_escolhida
            
        titulo = detalhes.get("name", "Título Desconhecido")
        data_lanc = detalhes.get("first_air_date", "")
        ano = data_lanc[:4] if data_lanc else "Desconhecido"
        nota = detalhes.get("vote_average", 0.0)
        votos = detalhes.get("vote_count", 0)
        
        pais_iso = detalhes.get("origin_country", [""])[0] if detalhes.get("origin_country") else ""
        nome_pais = country_name
        if pais_iso and nome_pais == "Desconhecido":
            for p in get_tmdb_countries():
                if p.get("iso_3166_1") == pais_iso:
                    nome_pais = p.get("native_name", p.get("english_name", pais_iso))
                    break
        
        eps = detalhes.get("number_of_episodes", "Desconhecido")
        temps = detalhes.get("number_of_seasons", "Desconhecido")
        duracao = f"{temps} Temp. / {eps} Eps."
        
        gens = [g["name"] for g in detalhes.get("genres", [])]
        generos_str = ", ".join(gens) if gens else "Sem categoria"
        
        poster_path = detalhes.get("poster_path")
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else ""
        
        coords = None
        if nome_pais and nome_pais != "Desconhecido":
            try:
                from geopy.geocoders import Nominatim
                geolocator = Nominatim(user_agent="filmes_global_app")
                location = geolocator.geocode(nome_pais)
                if location:
                    coords = {"lat": location.latitude, "lon": location.longitude}
            except:
                pass
                
        imdb_id = ""
        try:
            r_ext = requests.get(f"https://api.themoviedb.org/3/tv/{serie_id}/external_ids?api_key={TMDB_KEY}", timeout=5)
            if r_ext.status_code == 200:
                imdb_id = r_ext.json().get("imdb_id", "")
        except:
            pass

        return {
            "tipo": tipo_sorteio,
            "pais": nome_pais,
            "titulo": titulo,
            "ano": ano,
            "nota": round(float(nota), 1),
            "votos": int(votos),
            "indice": round(float(nota), 2),
            "imdb_id": imdb_id,
            "duracao": duracao,
            "generos": generos_str,
            "poster_url": poster_url,
            "coordenadas": coords,
            "tmdb_id": serie_id
        }

    except Exception as e:
        return {"error": f"Erro ao buscar série: {str(e)}"}


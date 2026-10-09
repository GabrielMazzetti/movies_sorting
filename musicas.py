import requests
import random
from geopy.geocoders import Nominatim
from urllib.parse import quote

PAISES_COMUNS_MUSICA = [
    "BR", "US", "GB", "FR", "DE", "IT", "ES", "JP", "KR", "RU", "SE", "NO", "FI", 
    "IE", "AR", "MX", "CO", "ZA", "NG", "AU", "NZ", "CA", "NL", "BE", "CH", "PT"
]

def map_country_code_to_name(code):
    import pycountry
    try:
        country = pycountry.countries.get(alpha_2=code)
        if country: return country.name
    except: pass
    return code

def realizar_sorteio_musica(opcao="1", filtros=None):
    if filtros is None:
        filtros = {}

    artista = filtros.get("artista", "").strip()
    pais_filtro = filtros.get("pais", "").strip().upper()
    epoca_min = filtros.get("epoca_min", "").strip()
    epoca_max = filtros.get("epoca_max", "").strip()

    # opcao 1 = Música, opcao 2 = Álbum
    sortear_album = (str(opcao) == "2")

    queries = []
    
    if artista:
        queries.append(f'artist:"{artista}"')
    
    if epoca_min or epoca_max:
        e_min = epoca_min if epoca_min else "*"
        e_max = epoca_max if epoca_max else "*"
        queries.append(f'date:[{e_min} TO {e_max}]')
        
    pais_escolhido = None
    if pais_filtro:
        queries.append(f'country:{pais_filtro}')
        pais_escolhido = pais_filtro
    else:
        # Se não tem artista, forçamos um país para não ficar muito lento
        if not artista:
            pais_escolhido = random.choice(PAISES_COMUNS_MUSICA)
            queries.append(f'country:{pais_escolhido}')

    # Adiciona type album para evitar singles se sorteando album
    if sortear_album:
        queries.append('type:album')

    query_str = " AND ".join(queries) if queries else "type:album"

    mb_url = "https://musicbrainz.org/ws/2/release/"
    params = {
        "query": query_str,
        "fmt": "json",
        "limit": 50,
        "offset": random.randint(0, 100) if not artista else 0
    }
    
    headers = {"User-Agent": "KinoMap/1.0"}

    try:
        res = requests.get(mb_url, params=params, headers=headers, timeout=15)
        if res.status_code != 200:
            return {"error": "Erro na API do MusicBrainz."}
        
        releases = res.json().get("releases", [])
        if not releases:
            # Se usou offset, tenta denovo sem offset
            if params["offset"] > 0:
                params["offset"] = 0
                res = requests.get(mb_url, params=params, headers=headers, timeout=15)
                releases = res.json().get("releases", [])
            
            if not releases:
                return {"error": "Nenhuma música/álbum encontrado com esses filtros."}

        # Filtra para evitar os que não tem artista
        valid_releases = [r for r in releases if r.get('artist-credit') and r.get('title')]
        if not valid_releases:
            valid_releases = releases
            
        release = random.choice(valid_releases)
        
        album = release.get("title", "Álbum Desconhecido")
        artist_credit = release.get("artist-credit", [{}])[0]
        artista_nome = artist_credit.get("name", "Artista Desconhecido")
        artist_item = artist_credit.get("artist", {})
        artist_id = artist_item.get("id")
        
        ano = release.get("date", "Desconhecido")[:4] if release.get("date") else "Desconhecido"
        mbid = release.get("id")
        
        country_code = release.get("country", pais_escolhido)
        
        # Obter o país real do artista
        if artist_id:
            try:
                r_art = requests.get(f"https://musicbrainz.org/ws/2/artist/{artist_id}?fmt=json", headers=headers, timeout=5)
                if r_art.status_code == 200:
                    art_data = r_art.json()
                    if art_data.get("country"):
                        country_code = art_data.get("country")
            except:
                pass
                
        if not country_code:
            country_code = "US"
        
        pais_nome = map_country_code_to_name(country_code)

        musica = ""
        # Se opção for música, buscar as tracks do release
        if not sortear_album and mbid:
            try:
                rec_url = f"https://musicbrainz.org/ws/2/release/{mbid}?inc=recordings&fmt=json"
                rec_res = requests.get(rec_url, headers=headers, timeout=5)
                if rec_res.status_code == 200:
                    media = rec_res.json().get("media", [])
                    if media:
                        tracks = media[0].get("tracks", [])
                        if tracks:
                            track = random.choice(tracks)
                            musica = track.get("title", "")
            except:
                pass
                
        if not sortear_album and not musica:
            musica = album # Fallback

        tipo_str = "ÁLBUM ALEATÓRIO" if sortear_album else "MÚSICA ALEATÓRIA"

        # Buscar Capa no iTunes
        capa = ""
        try:
            itunes_url = 'https://itunes.apple.com/search'
            itunes_params = {'term': f'{artista_nome} {album}', 'entity': 'album', 'limit': 1}
            itunes_res = requests.get(itunes_url, params=itunes_params, timeout=5)
            if itunes_res.status_code == 200:
                results = itunes_res.json().get('results', [])
                if results:
                    capa = results[0].get('artworkUrl100', '').replace('100x100bb', '600x600bb')
        except:
            pass

        # Buscar coordenadas
        coords = None
        if pais_nome and pais_nome != "Desconhecido":
            try:
                geolocator = Nominatim(user_agent="filmes_global_app")
                location = geolocator.geocode(pais_nome)
                if location:
                    coords = {"lat": location.latitude, "lon": location.longitude}
            except:
                pass

        # Link Spotify
        query_spotify = f"{musica} {artista_nome}" if not sortear_album else f"{album} {artista_nome}"
        spotify_link = f"https://open.spotify.com/search/{quote(query_spotify)}"

        return {
            "tipo": tipo_str,
            "titulo": musica if not sortear_album else album,
            "artista": artista_nome,
            "album": album,
            "ano": ano,
            "pais": pais_nome,
            "capa_url": capa,
            "link": spotify_link,
            "coordenadas": coords,
            "is_music": not sortear_album,
            "is_album": sortear_album
        }

    except Exception as e:
        return {"error": f"Erro interno ao buscar música: {str(e)}"}


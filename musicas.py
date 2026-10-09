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
    genero = filtros.get("genero", "").strip().lower()

    sortear_album = (str(opcao) == "2")
    headers = {"User-Agent": "KinoMap/1.0"}

    # ==========================================
    # PASSO 1: ENCONTRAR O ARTISTA
    # ==========================================
    artist_queries = []
    
    if artista:
        artist_queries.append(f'artist:"{artista}"')
        
    if genero:
        MAPA_GENEROS = {
            "rock": ['tag:"rock"', 'tag:"grunge"', 'tag:"metal"', 'tag:"heavy metal"', 'tag:"punk"', 'tag:"hard rock"', 'tag:"indie rock"', 'tag:"alternative rock"'],
            "eletronica": ['tag:"electronic"', 'tag:"techno"', 'tag:"trance"', 'tag:"house"', 'tag:"dance"', 'tag:"edm"'],
            "eletrônica": ['tag:"electronic"', 'tag:"techno"', 'tag:"trance"', 'tag:"house"', 'tag:"dance"', 'tag:"edm"'],
            "hip hop": ['tag:"hip hop"', 'tag:"rap"', 'tag:"trap"'],
            "rap": ['tag:"hip hop"', 'tag:"rap"', 'tag:"trap"'],
            "pop": ['tag:"pop"', 'tag:"k-pop"', 'tag:"synthpop"', 'tag:"indie pop"'],
            "metal": ['tag:"metal"', 'tag:"heavy metal"', 'tag:"death metal"', 'tag:"black metal"', 'tag:"thrash metal"', 'tag:"doom metal"'],
            "samba": ['tag:"samba"', 'tag:"pagode"'],
            "mpb": ['tag:"mpb"', 'tag:"bossa nova"'],
            "pagode": ['tag:"pagode"', 'tag:"samba"']
        }
        
        if genero in MAPA_GENEROS:
            tags_or = " OR ".join(MAPA_GENEROS[genero])
            artist_queries.append(f'({tags_or})')
        else:
            artist_queries.append(f'tag:"{genero}"')
            
    pais_escolhido = pais_filtro if pais_filtro else None
    if pais_filtro:
        artist_queries.append(f'country:{pais_filtro}')

    artist_id = None
    artista_nome_found = None

    try:
        if not artist_queries:
            # Sem filtros de artista, genero ou país -> País aleatório
            pais_escolhido = random.choice(PAISES_COMUNS_MUSICA)
            query_str = f'country:{pais_escolhido}'
        else:
            query_str = " AND ".join(artist_queries)

        mb_url_artist = "https://musicbrainz.org/ws/2/artist/"
        offset = random.randint(0, 50) if not artista else 0
        
        res_art = requests.get(mb_url_artist, params={"query": query_str, "fmt": "json", "limit": 20, "offset": offset}, headers=headers, timeout=10)
        if res_art.status_code != 200:
            return {"error": "Erro ao buscar artista no MusicBrainz."}
            
        artists = res_art.json().get("artists", [])
        
        if not artists and offset > 0:
            # Tenta sem offset
            res_art = requests.get(mb_url_artist, params={"query": query_str, "fmt": "json", "limit": 20, "offset": 0}, headers=headers, timeout=10)
            artists = res_art.json().get("artists", [])
            
        if not artists:
            return {"error": "Nenhum artista encontrado com esses filtros de gênero/país/nome."}
            
        artist_obj = random.choice(artists)
        artist_id = artist_obj["id"]
        artista_nome_found = artist_obj.get("name", "Artista Desconhecido")
        
        if artist_obj.get("country"):
            pais_escolhido = artist_obj.get("country")
        elif not pais_escolhido:
            pais_escolhido = "US"

        # ==========================================
        # PASSO 2: BUSCAR RELEASE DO ARTISTA
        # ==========================================
        release_queries = [f'arid:{artist_id}']
        
        if epoca_min or epoca_max:
            e_min = epoca_min if epoca_min else "*"
            e_max = epoca_max if epoca_max else "*"
            release_queries.append(f'date:[{e_min} TO {e_max}]')
            
        if sortear_album:
            release_queries.append('type:album')
            
        query_str_rel = " AND ".join(release_queries)
        
        mb_url_rel = "https://musicbrainz.org/ws/2/release/"
        res_rel = requests.get(mb_url_rel, params={"query": query_str_rel, "fmt": "json", "limit": 50}, headers=headers, timeout=10)
        
        releases = res_rel.json().get("releases", [])
        
        if not releases:
            return {"error": f"Nenhum álbum/música de {artista_nome_found} encontrado(a) para essa época."}
            
        valid_releases = [r for r in releases if r.get('title')]
        release = random.choice(valid_releases if valid_releases else releases)
        
        album = release.get("title", "Álbum Desconhecido")
        ano = release.get("date", "Desconhecido")[:4] if release.get("date") else "Desconhecido"
        mbid = release.get("id")
        pais_nome = map_country_code_to_name(pais_escolhido)

        musica = ""
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
            musica = album

        tipo_str = "ÁLBUM ALEATÓRIO" if sortear_album else "MÚSICA ALEATÓRIA"

        # Buscar Capa no iTunes
        capa = ""
        try:
            itunes_url = 'https://itunes.apple.com/search'
            itunes_params = {'term': f'{artista_nome_found} {album}', 'entity': 'album', 'limit': 1}
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

        query_spotify = f"{musica} {artista_nome_found}" if not sortear_album else f"{album} {artista_nome_found}"
        spotify_link = f"https://open.spotify.com/search/{quote(query_spotify)}"

        return {
            "tipo": tipo_str,
            "titulo": musica if not sortear_album else album,
            "artista": artista_nome_found,
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


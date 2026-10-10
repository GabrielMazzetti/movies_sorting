import sqlite3
import random
from pathlib import Path

DB_PATH = Path("dados/musicas.db")

def realizar_sorteio_musica(opcao="1", filtros=None):
    if filtros is None:
        filtros = {}
        
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            query_conditions = []
            params = []
            
            artista = filtros.get("artista", "").strip()
            energia = filtros.get("energia", "").strip()
            dancabilidade = filtros.get("dancabilidade", "").strip()
            epoca_min = filtros.get("epoca_min", "").strip()
            epoca_max = filtros.get("epoca_max", "").strip()
            titulo_filtro = filtros.get("titulo", "").strip()
            musica_id = filtros.get("id", "").strip()
            
            if musica_id:
                query_conditions.append("id = ?")
                params.append(musica_id)
            elif titulo_filtro:
                query_conditions.append("name LIKE ?")
                params.append(f"%{titulo_filtro}%")
            if artista:
                query_conditions.append("artists LIKE ?")
                params.append(f"%{artista}%")
            if energia:
                try:
                    e_val = float(energia)
                    query_conditions.append("energy >= ?")
                    params.append(e_val)
                except: pass
            if dancabilidade:
                try:
                    d_val = float(dancabilidade)
                    query_conditions.append("danceability >= ?")
                    params.append(d_val)
                except: pass
            if epoca_min:
                try:
                    query_conditions.append("year >= ?")
                    params.append(int(epoca_min))
                except: pass
            if epoca_max:
                try:
                    query_conditions.append("year <= ?")
                    params.append(int(epoca_max))
                except: pass
                
            base_sql = "SELECT id, name, album, artists, year, duration_ms FROM musicas"
            if query_conditions:
                base_sql += " WHERE " + " AND ".join(query_conditions)
                
            base_sql += " ORDER BY RANDOM() LIMIT 100"
            
            c.execute(base_sql, tuple(params))
            resultados = c.fetchall()
            
            if not resultados:
                return {"error": "Nenhuma música encontrada com esses filtros."}
                
            musica = random.choice(resultados)
            sid, name, album, artists, year, duration_ms = musica
            
            # Since Spotify API needs auth and this is offline dump, we won't get cover from iTunes or Spotify for now.
            # But wait, earlier I used iTunes for cover. We can still try that if we want.
            capa = ""
            try:
                import requests
                itunes_url = 'https://itunes.apple.com/search'
                itunes_params = {'term': f'{artists} {name}', 'entity': 'song', 'limit': 1}
                itunes_res = requests.get(itunes_url, params=itunes_params, timeout=3)
                if itunes_res.status_code == 200:
                    res_json = itunes_res.json().get('results', [])
                    if res_json:
                        capa = res_json[0].get('artworkUrl100', '').replace('100x100bb', '600x600bb')
            except:
                pass
                
            link = f"https://open.spotify.com/track/{sid}" if sid else "#"
            
            return {
                "tipo": "BUSCA POR TÍTULO" if titulo_filtro else "MÚSICA ALEATÓRIA",
                "titulo": name,
                "artista": artists,
                "album": album,
                "ano": year if year else "N/A",
                "pais": "Desconhecido", # No country for Spotify dump
                "capa_url": capa,
                "link": link,
                "coordenadas": None,
                "is_music": True,
                "is_album": False
            }
            
    except Exception as e:
        return {"error": f"Erro interno ao buscar música no banco: {str(e)}"}

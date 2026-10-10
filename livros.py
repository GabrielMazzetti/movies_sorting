import sqlite3
import random
import requests
from geopy.geocoders import Nominatim
from pathlib import Path

DB_PATH = Path("dados/livros.db")

def realizar_sorteio_livro(opcao="1", filtros=None):
    if filtros is None:
        filtros = {}
        
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            query_conditions = []
            params = []
            
            titulo_filtro = filtros.get("titulo", "").strip()
            livro_id = filtros.get("id", "").strip()
            assunto_filtro = filtros.get("assunto", "").strip()
            autor_filtro = filtros.get("autor", "").strip()
            
            if livro_id:
                query_conditions.append("key = ?")
                params.append(livro_id)
            elif titulo_filtro:
                query_conditions.append("title LIKE ?")
                params.append(f"%{titulo_filtro}%")
            if assunto_filtro:
                query_conditions.append("subjects LIKE ?")
                params.append(f"%{assunto_filtro}%")
            # authors are stored as keys in DB, which is a bit tricky if we search by name.
            # But the user typed the name, we don't have author names in DB, only keys.
            # The prompt says: "Books (ol_dump_works.txt.gz): Has title, subjects (genres), and cover_id, but authors are just keys (/authors/OL...), not string names."
            # So searching by author name in DB is not possible. We will ignore author filter for DB query.

            base_sql = "SELECT key, title, authors, subjects, cover_id FROM livros"
            if query_conditions:
                base_sql += " WHERE " + " AND ".join(query_conditions)
                
            # SQLite doesn't have an efficient way to pick random row with WHERE clause.
            # We'll just fetch up to 1000 matching rows and pick one randomly.
            base_sql += " ORDER BY RANDOM() LIMIT 100"
            
            c.execute(base_sql, tuple(params))
            resultados = c.fetchall()
            
            if not resultados:
                return {"error": "Nenhum livro encontrado com esses filtros."}
                
            livro = random.choice(resultados)
            key, title, authors, subjects, cover_id = livro
            
            # Fetch author name from OpenLibrary API since we only have keys
            autor_nome = "Desconhecido"
            if authors:
                try:
                    # 'authors' is a comma separated string of keys e.g. "OL123A, OL456A"
                    first_author_key = authors.split(",")[0].strip()
                    r = requests.get(f"https://openlibrary.org/authors/{first_author_key}.json", timeout=3)
                    if r.status_code == 200:
                        autor_nome = r.json().get("name", "Desconhecido")
                except:
                    pass
            
            # Fetch synopsis and other details from OpenLibrary
            sinopse = "Nenhuma sinopse disponível."
            try:
                work_url = f"https://openlibrary.org/works/{key}.json"
                work_res = requests.get(work_url, timeout=3)
                if work_res.status_code == 200:
                    work_data = work_res.json()
                    desc = work_data.get("description")
                    if desc:
                        if isinstance(desc, dict) and "value" in desc:
                            sinopse = desc["value"]
                        elif isinstance(desc, str):
                            sinopse = desc
            except:
                pass
                
            if len(sinopse) > 300:
                sinopse = sinopse[:297] + "..."
                
            capa_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg" if cover_id else ""
            link = f"https://openlibrary.org/works/{key}"
            
            # País doesn't exist in OpenLibrary DB for books natively, we can just return what they asked
            pais_escolhido = filtros.get("pais", "Desconhecido")
            coords = None
            
            if pais_escolhido and pais_escolhido != "Desconhecido":
                try:
                    geolocator = Nominatim(user_agent="filmes_global_app")
                    location = geolocator.geocode(pais_escolhido)
                    if location:
                        coords = {"lat": location.latitude, "lon": location.longitude}
                except:
                    pass
                    
            return {
                "titulo": title,
                "autor": autor_nome,
                "ano": "N/A", # not in our DB
                "paginas": "N/A",
                "categorias": subjects[:50] + "..." if len(subjects) > 50 else subjects,
                "nota": "N/A",
                "sinopse": sinopse,
                "link": link,
                "capa_url": capa_url,
                "tipo": "BUSCA DE LIVRO" if query_conditions else "LIVRO ALEATÓRIO",
                "pais": pais_escolhido,
                "coordenadas": coords
            }
            
    except Exception as e:
        return {"error": f"Erro ao buscar livro no banco: {str(e)}"}

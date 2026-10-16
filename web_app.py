from flask import Flask, render_template, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests_cache
from pathlib import Path
import sorteio
import gzip
import shutil
import os
import sqlite3

requests_cache.install_cache(
    'kinomap_cache', 
    backend='sqlite', 
    expire_after=86400,
    allowable_methods=('GET',)
)

DB_PATH = Path("dados/filmes_global.db")
GZ_PATH = Path("dados/filmes_global.db.gz")

if not DB_PATH.exists() and GZ_PATH.exists():
    print("Extraindo banco de dados de filmes...")
    with gzip.open(GZ_PATH, 'rb') as f_in:
        with open(DB_PATH, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    print("Banco de filmes extraído com sucesso.")

SERIES_DB_PATH = Path("dados/series.db")
SERIES_GZ_PATH = Path("dados/series.db.gz")
if not SERIES_DB_PATH.exists() and SERIES_GZ_PATH.exists():
    print("Extraindo banco de dados de séries...")
    with gzip.open(SERIES_GZ_PATH, 'rb') as f_in:
        with open(SERIES_DB_PATH, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    print("Banco de séries extraído com sucesso.")

MUSICAS_DB_PATH = Path("dados/musicas.db")
MUSICAS_GZ_PATH = Path("dados/musicas.db.gz")
if not MUSICAS_DB_PATH.exists() and MUSICAS_GZ_PATH.exists():
    print("Extraindo banco de dados de músicas...")
    with gzip.open(MUSICAS_GZ_PATH, 'rb') as f_in:
        with open(MUSICAS_DB_PATH, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    print("Banco de músicas extraído com sucesso.")

app = Flask(__name__)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

@app.route('/api/autocomplete')
def autocomplete():
    query = request.args.get('q', '').strip()
    tipo = request.args.get('tipo', 'movie') # movie, serie, livro, musica
    if len(query) < 1:
        return jsonify([])
    
    try:
        resp = []
        seen_ids = set()
        if tipo == 'movie' or tipo == 'serie':
            from dotenv import load_dotenv
            import requests
            load_dotenv()
            tmdb_key = os.environ.get("TMDB_API_KEY")

            if tipo == 'serie':
                db_path = "dados/series.db"
                if os.path.exists(db_path):
                    with sqlite3.connect(db_path) as conn:
                        c = conn.cursor()
                        sql = """
                            SELECT tconst, primaryTitle, originalTitle, startYear, MAX(v) as votes FROM (
                                SELECT s.tconst, s.primaryTitle, s.originalTitle, s.startYear, COALESCE(r.numVotes, 0) as v
                                FROM (SELECT tconst, primaryTitle, originalTitle, startYear FROM series WHERE primaryTitle LIKE ? COLLATE NOCASE LIMIT 150) s
                                LEFT JOIN series_ratings r ON s.tconst = r.tconst
                                UNION ALL
                                SELECT s.tconst, s.primaryTitle, s.originalTitle, s.startYear, COALESCE(r.numVotes, 0) as v
                                FROM (SELECT tconst, primaryTitle, originalTitle, startYear FROM series WHERE originalTitle LIKE ? COLLATE NOCASE LIMIT 150) s
                                LEFT JOIN series_ratings r ON s.tconst = r.tconst
                            ) GROUP BY tconst ORDER BY votes DESC LIMIT 10
                        """
                        c.execute(sql, (query + "%", query + "%"))
                        resultados = c.fetchall()
                        for r in resultados:
                            display_title = r[2] if r[2] and query.lower() in str(r[2]).lower() and query.lower() not in str(r[1]).lower() else r[1]
                            resp.append({"id": r[0], "title": display_title, "year": r[3], "votes": r[4] or 0})
                            seen_ids.add(r[0])

                if tmdb_key and len(query) >= 2:
                    try:
                        r_tmdb = requests.get(
                            "https://api.themoviedb.org/3/search/tv",
                            params={"api_key": tmdb_key, "query": query, "language": "pt-BR"},
                            timeout=2
                        )
                        if r_tmdb.status_code == 200:
                            for item in r_tmdb.json().get("results", [])[:5]:
                                pt_title = item.get("name") or ""
                                orig_title = item.get("original_name") or ""
                                year = (item.get("first_air_date") or "")[:4] or "N/A"
                                title_disp = f"{pt_title} ({orig_title})" if orig_title and orig_title.lower() != pt_title.lower() else pt_title
                                if not any(orig_title.lower() == x["title"].lower() or pt_title.lower() == x["title"].lower() for x in resp):
                                    resp.append({
                                        "id": f"tmdb_{item['id']}",
                                        "title": title_disp,
                                        "year": year,
                                        "votes": int(item.get("vote_count", 0) * 10)
                                    })
                    except Exception:
                        pass

                resp.sort(key=lambda x: x.get("votes", 0), reverse=True)
                resp = resp[:12]

            else:
                db_path = "dados/filmes_global.db"
                if os.path.exists(db_path):
                    with sqlite3.connect(db_path) as conn:
                        c = conn.cursor()
                        sql = """
                            SELECT tconst, primaryTitle, originalTitle, startYear, MAX(v) as votes FROM (
                                SELECT tconst, primaryTitle, originalTitle, startYear, numVotes as v
                                FROM filmes_final
                                WHERE (primaryTitle LIKE ? OR originalTitle LIKE ?) COLLATE NOCASE
                                UNION ALL
                                SELECT f.tconst, f.primaryTitle, f.originalTitle, f.startYear, COALESCE(r.numVotes, 0) as v
                                FROM (SELECT tconst, primaryTitle, originalTitle, startYear FROM filmes WHERE primaryTitle LIKE ? COLLATE NOCASE LIMIT 150) f
                                LEFT JOIN ratings r ON f.tconst = r.tconst
                                UNION ALL
                                SELECT f.tconst, f.primaryTitle, f.originalTitle, f.startYear, COALESCE(r.numVotes, 0) as v
                                FROM (SELECT tconst, primaryTitle, originalTitle, startYear FROM filmes WHERE originalTitle LIKE ? COLLATE NOCASE LIMIT 150) f
                                LEFT JOIN ratings r ON f.tconst = r.tconst
                            ) GROUP BY tconst ORDER BY votes DESC LIMIT 10
                        """
                        c.execute(sql, ("%" + query + "%", "%" + query + "%", query + "%", query + "%"))
                        resultados = c.fetchall()
                        if len(resultados) < 5 and len(query) >= 3:
                            sql_sub = """
                                SELECT f.tconst, f.primaryTitle, f.originalTitle, f.startYear, COALESCE(r.numVotes, 0) as v
                                FROM filmes f
                                LEFT JOIN ratings r ON f.tconst = r.tconst
                                WHERE (f.primaryTitle LIKE ? OR f.originalTitle LIKE ?) COLLATE NOCASE
                                ORDER BY v DESC LIMIT 10
                            """
                            c.execute(sql_sub, ("%" + query + "%", "%" + query + "%"))
                            for row in c.fetchall():
                                if row[0] not in {r[0] for r in resultados}:
                                    resultados.append(row)

                        for r in resultados:
                            display_title = r[2] if r[2] and query.lower() in str(r[2]).lower() and query.lower() not in str(r[1]).lower() else r[1]
                            resp.append({"id": r[0], "title": display_title, "year": r[3], "votes": r[4] or 0})
                            seen_ids.add(r[0])

                if tmdb_key and len(query) >= 2:
                    try:
                        r_tmdb = requests.get(
                            "https://api.themoviedb.org/3/search/movie",
                            params={"api_key": tmdb_key, "query": query, "language": "pt-BR"},
                            timeout=2
                        )
                        if r_tmdb.status_code == 200:
                            for item in r_tmdb.json().get("results", [])[:5]:
                                pt_title = item.get("title") or ""
                                orig_title = item.get("original_title") or ""
                                year = (item.get("release_date") or "")[:4] or "N/A"
                                title_disp = f"{pt_title} ({orig_title})" if orig_title and orig_title.lower() != pt_title.lower() else pt_title
                                if not any(orig_title.lower() == x["title"].lower() or pt_title.lower() == x["title"].lower() for x in resp):
                                    resp.append({
                                        "id": f"tmdb_{item['id']}",
                                        "title": title_disp,
                                        "year": year,
                                        "votes": int(item.get("vote_count", 0) * 10)
                                    })
                    except Exception:
                        pass

                resp.sort(key=lambda x: x.get("votes", 0), reverse=True)
                resp = resp[:12]

        elif tipo == 'livro':
            db_path = "dados/livros.db"
            if os.path.exists(db_path):
                with sqlite3.connect(db_path) as conn:
                    c = conn.cursor()
                    sql = "SELECT key, title FROM livros WHERE title LIKE ? COLLATE NOCASE LIMIT 10"
                    c.execute(sql, (query + "%",))
                    resultados = c.fetchall()
                    if len(resultados) < 10:
                        sql2 = "SELECT key, title FROM livros WHERE title LIKE ? COLLATE NOCASE LIMIT ?"
                        c.execute(sql2, ("%" + query + "%", 10 - len(resultados)))
                        for row in c.fetchall():
                            if row not in resultados:
                                resultados.append(row)
                    for r in resultados:
                        resp.append({"id": r[0], "title": r[1], "year": "LIVRO"})
                    
        elif tipo == 'musica':
            db_path = "dados/musicas.db"
            if os.path.exists(db_path):
                with sqlite3.connect(db_path) as conn:
                    c = conn.cursor()
                    sql = "SELECT id, name, artists, year FROM musicas WHERE name LIKE ? COLLATE NOCASE LIMIT 10"
                    c.execute(sql, (query + "%",))
                    resultados = c.fetchall()
                    if len(resultados) < 10:
                        sql2 = "SELECT id, name, artists, year FROM musicas WHERE name LIKE ? COLLATE NOCASE LIMIT ?"
                        c.execute(sql2, ("%" + query + "%", 10 - len(resultados)))
                        for row in c.fetchall():
                            if row not in resultados:
                                resultados.append(row)
                    for r in resultados:
                        title = f"{r[1]} ({r[2]})"
                        resp.append({"id": r[0], "title": title, "year": r[3]})
                    
        return jsonify(resp)
    except Exception as e:
        print("Error in autocomplete:", e)
        return jsonify([])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/sortear', methods=['POST'])
@limiter.limit("15 per minute")
def sortear():
    data = request.json or {}
    opcao = str(data.get('opcao', '1'))
    filtros = data.get('filtros', {})
    
    resultado = sorteio.realizar_sorteio(opcao, filtros)
    if resultado is None:
        return jsonify({"error": "Base de dados não encontrada."}), 404
    if "error" in resultado:
        return jsonify(resultado), 400
        
    return jsonify(resultado)

@app.route('/api/sortear_livro', methods=['POST'])
@limiter.limit("15 per minute")
def sortear_livro():
    import livros
    data = request.json or {}
    opcao = str(data.get('opcao', '1'))
    filtros = data.get('filtros', {})
    
    resultado = livros.realizar_sorteio_livro(opcao, filtros)
    if resultado is None:
        return jsonify({"error": "Erro desconhecido ao buscar livro."}), 500
    if "error" in resultado:
        return jsonify(resultado), 400
        
    return jsonify(resultado)

@app.route('/api/sortear_musica', methods=['POST'])
@limiter.limit("15 per minute")
def sortear_musica():
    import musicas
    data = request.json or {}
    opcao = str(data.get('opcao', '1'))
    filtros = data.get('filtros', {})
    
    resultado = musicas.realizar_sorteio_musica(opcao, filtros)
    if resultado is None:
        return jsonify({"error": "Erro desconhecido ao buscar música."}), 500
    if "error" in resultado:
        return jsonify(resultado), 400
        
    return jsonify(resultado)

@app.route('/api/sortear_serie', methods=['POST'])
@limiter.limit("15 per minute")
def sortear_serie():
    import series
    data = request.json or {}
    opcao = str(data.get('opcao', '1'))
    filtros = data.get('filtros', {})
    
    resultado = series.realizar_sorteio_serie(opcao, filtros)
    if resultado is None:
        return jsonify({"error": "Erro desconhecido ao buscar série."}), 500
    if "error" in resultado:
        return jsonify(resultado), 400
        
    return jsonify(resultado)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

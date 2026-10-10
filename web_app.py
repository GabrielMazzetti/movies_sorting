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
        if tipo == 'movie' or tipo == 'serie':
            if tipo == 'serie':
                db_path = "dados/series.db"
                with sqlite3.connect(db_path) as conn:
                    c = conn.cursor()
                    sql = "SELECT tconst, primaryTitle, originalTitle, startYear FROM series WHERE (primaryTitle LIKE ? OR originalTitle LIKE ?) COLLATE NOCASE LIMIT 10"
                    c.execute(sql, (query + "%", query + "%"))
                    resultados = c.fetchall()
                    if len(resultados) < 10:
                        sql2 = "SELECT tconst, primaryTitle, originalTitle, startYear FROM series WHERE (primaryTitle LIKE ? OR originalTitle LIKE ?) COLLATE NOCASE LIMIT ?"
                        c.execute(sql2, ("%" + query + "%", "%" + query + "%", 10 - len(resultados)))
                        for row in c.fetchall():
                            if row not in resultados:
                                resultados.append(row)
                    for r in resultados:
                        display_title = r[2] if r[2] and query.lower() in str(r[2]).lower() else r[1]
                        resp.append({"id": r[0], "title": display_title, "year": r[3]})
            else:
                db_path = "dados/filmes_global.db"
                with sqlite3.connect(db_path) as conn:
                    c = conn.cursor()
                    sql = "SELECT tconst, primaryTitle, originalTitle, startYear FROM filmes WHERE titleType = 'movie' AND (primaryTitle LIKE ? OR originalTitle LIKE ?) COLLATE NOCASE LIMIT 10"
                    c.execute(sql, (query + "%", query + "%"))
                    resultados = c.fetchall()
                    if len(resultados) < 10:
                        sql2 = "SELECT tconst, primaryTitle, originalTitle, startYear FROM filmes WHERE titleType = 'movie' AND (primaryTitle LIKE ? OR originalTitle LIKE ?) COLLATE NOCASE LIMIT ?"
                        c.execute(sql2, ("%" + query + "%", "%" + query + "%", 10 - len(resultados)))
                        for row in c.fetchall():
                            if row not in resultados:
                                resultados.append(row)
                    for r in resultados:
                        display_title = r[2] if r[2] and query.lower() in str(r[2]).lower() else r[1]
                        resp.append({"id": r[0], "title": display_title, "year": r[3]})
        
        elif tipo == 'livro':
            db_path = "dados/livros.db"
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

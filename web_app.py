from flask import Flask, render_template, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests_cache
from pathlib import Path
import sorteio

# Configura o Cache das APIs externas (TMDb e OpenLibrary)
# Salva respostas em um arquivo local kinomap_cache.sqlite por 24 horas
requests_cache.install_cache(
    'kinomap_cache', 
    backend='sqlite', 
    expire_after=86400,
    allowable_methods=('GET',)
)

import gzip
import shutil
import os

DB_PATH = Path("dados/filmes_global.db")
GZ_PATH = Path("dados/filmes_global.db.gz")

if not DB_PATH.exists() and GZ_PATH.exists():
    print("Extraindo banco de dados...")
    with gzip.open(GZ_PATH, 'rb') as f_in:
        with open(DB_PATH, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    print("Banco extraído com sucesso.")

app = Flask(__name__)

# Configura o Rate Limiter para prevenir abuso (DDoS e esgotamento de APIs)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

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


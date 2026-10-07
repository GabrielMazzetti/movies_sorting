from flask import Flask, render_template, jsonify, request
from pathlib import Path
import sorteio

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/sortear', methods=['POST'])
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

@app.route('/api/historico', methods=['GET'])
def historico():
    pasta_sorteios = Path("sorteios")
    if not pasta_sorteios.exists():
        return jsonify([])

    arquivos = list(pasta_sorteios.glob("*.txt"))
    if not arquivos:
        return jsonify([])
    
    historico_lista = []
    
    import os
    import requests
    from dotenv import load_dotenv
    load_dotenv()
    tmdb_key = os.environ.get("TMDB_API_KEY")

    # Lendo na ordem reversa para mostrar os mais recentes primeiro
    for arquivo in reversed(arquivos):
        modo_txt = pais_txt = filme_txt = nota_txt = indice_txt = imdb_id_txt = ano_txt = poster_url_txt = ""
        linhas_arquivo = []
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                linhas_arquivo = f.readlines()
                for linha in linhas_arquivo:
                    linha = linha.strip()
                    if linha.startswith("PAÍS:"): pais_txt = linha.replace("PAÍS:", "").strip()
                    elif linha.startswith("FILME:"): filme_txt = linha.replace("FILME:", "").strip()
                    elif linha.startswith("ANO:"): ano_txt = linha.replace("ANO:", "").strip()
                    elif linha.startswith("NOTA IMDb:"): nota_txt = linha.replace("NOTA IMDb:", "").strip()
                    elif linha.startswith("ÍNDICE:"): indice_txt = linha.replace("ÍNDICE:", "").strip()
                    elif linha.startswith("MODO DO SORTEIO:"): modo_txt = linha.replace("MODO DO SORTEIO:", "").strip().upper()
                    elif linha.startswith("IMDb ID:"): imdb_id_txt = linha.replace("IMDb ID:", "").strip()
                    elif linha.startswith("POSTER URL:"): poster_url_txt = linha.replace("POSTER URL:", "").strip()
            
            # Se é um arquivo antigo que já tem IMDb ID mas não tem poster
            if imdb_id_txt and not poster_url_txt and tmdb_key:
                try:
                    r = requests.get(f"https://api.themoviedb.org/3/find/{imdb_id_txt}?api_key={tmdb_key}&external_source=imdb_id", timeout=5)
                    if r.status_code == 200:
                        dados_tmdb = r.json()
                        res_tmdb = dados_tmdb.get("movie_results") or dados_tmdb.get("tv_results")
                        if res_tmdb and res_tmdb[0].get("poster_path"):
                            poster_url_txt = f"https://image.tmdb.org/t/p/w500{res_tmdb[0]['poster_path']}"
                            # Reescreve o arquivo incluindo o poster
                            linhas_arquivo.append(f"POSTER URL: {poster_url_txt}\n")
                            with open(arquivo, 'w', encoding='utf-8') as f2:
                                f2.writelines(linhas_arquivo)
                except Exception:
                    pass

            # Formatação do card compatível com o sistema anterior
            if not filme_txt or not pais_txt:
                pais_txt = arquivo.stem.replace('_', ' | ')
                filme_txt = "Registro Antigo"

            historico_lista.append({
                "id": arquivo.stem,
                "modo": modo_txt,
                "pais": pais_txt,
                "titulo": filme_txt,
                "ano": ano_txt,
                "nota": nota_txt,
                "indice": indice_txt,
                "imdb_id": imdb_id_txt,
                "poster_url": poster_url_txt
            })
        except Exception:
            continue
            
    return jsonify(historico_lista)

if __name__ == '__main__':
    app.run(debug=True, port=5000)


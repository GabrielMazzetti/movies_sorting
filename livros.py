import requests
import random

def realizar_sorteio_livro(filtros=None):
    """
    Realiza o sorteio de um livro usando a API do OpenLibrary.
    """
    if filtros is None:
        filtros = {}

    assunto = filtros.get("assunto", "").strip().lower()
    autor = filtros.get("autor", "").strip().lower()

    params = {}
    is_title_search = False
    
    if filtros.get("titulo"):
        params["title"] = filtros["titulo"].strip()
        is_title_search = True
    else:
        if assunto:
            params["subject"] = assunto
        if autor:
            params["author"] = autor

        if not params:
            temas = ["fiction", "history", "science", "fantasy", "mystery", "philosophy", "biography", "adventure"]
            params["subject"] = random.choice(temas)

    # Pegamos os primeiros resultados
    params["limit"] = 10 if is_title_search else 100

    url = "https://openlibrary.org/search.json"

    headers = {
        "User-Agent": "KinoMap/1.0 (seu_email_ou_site_aqui)"
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        if response.status_code != 200:
            return {"error": "Erro de comunicação com a OpenLibrary."}

        dados = response.json()
        items = dados.get("docs", [])
        
        if not items:
            return {"error": "Nenhum livro encontrado com esses filtros na OpenLibrary."}

        if is_title_search:
            livro_escolhido = items[0]
        else:
            livro_escolhido = random.choice(items)
        
        titulo = livro_escolhido.get("title", "Título Desconhecido")
        
        autores_list = livro_escolhido.get("author_name", [])
        autores = ", ".join(autores_list) if autores_list else "Autor Desconhecido"
        
        ano = str(livro_escolhido.get("first_publish_year", "Desconhecido"))
        paginas = str(livro_escolhido.get("number_of_pages_median", "Desconhecido"))
        
        categorias_list = livro_escolhido.get("subject", [])
        categorias = ", ".join(categorias_list[:3]) if categorias_list else "Sem categoria"
        
        nota = livro_escolhido.get("ratings_average")
        if nota is not None:
            nota = f"{nota:.1f}"
        else:
            nota = "N/A"
            
        key = livro_escolhido.get("key", "")
        link = f"https://openlibrary.org{key}" if key else "#"
        
        # Buscar sinopse fazendo uma request adicional para os detalhes da obra
        sinopse = "Nenhuma sinopse disponível."
        if key:
            try:
                work_url = f"https://openlibrary.org{key}.json"
                work_res = requests.get(work_url, headers=headers, timeout=5)
                if work_res.status_code == 200:
                    work_data = work_res.json()
                    desc = work_data.get("description")
                    if desc:
                        if isinstance(desc, dict) and "value" in desc:
                            sinopse = desc["value"]
                        elif isinstance(desc, str):
                            sinopse = desc
            except:
                pass # Ignora erro de fetch da sinopse e mantém a default

        if len(sinopse) > 300:
            sinopse = sinopse[:297] + "..."

        cover_i = livro_escolhido.get("cover_i")
        if cover_i:
            capa = f"https://covers.openlibrary.org/b/id/{cover_i}-L.jpg"
        else:
            capa = ""

        return {
            "titulo": titulo,
            "autor": autores,
            "ano": ano,
            "paginas": paginas,
            "categorias": categorias,
            "nota": nota,
            "sinopse": sinopse,
            "link": link,
            "capa_url": capa,
            "tipo": "BUSCA POR TÍTULO" if is_title_search else "LIVRO ALEATÓRIO"
        }

    except Exception as e:
        return {"error": f"Erro ao buscar livro: {str(e)}"}


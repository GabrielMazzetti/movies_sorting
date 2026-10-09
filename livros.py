import requests
import random
from geopy.geocoders import Nominatim

PAISES_COMUNS = [
    "Brazil", "United States", "United Kingdom", "France", "Germany", 
    "Italy", "Spain", "Japan", "Russia", "China", "India", "Mexico", 
    "Argentina", "Canada", "Australia", "South Africa", "Egypt", 
    "Greece", "Turkey", "Portugal", "Sweden", "Norway", "Colombia",
    "Chile", "Peru", "Ireland", "Netherlands", "Belgium", "Poland"
]

def realizar_sorteio_livro(opcao="1", filtros=None):
    """
    Realiza o sorteio de um livro usando a API do OpenLibrary com suporte a país e mapa.
    opcao:
      1: Livro Aleatório (do país sorteado/escolhido)
      2: Livro Global (Qualquer país, aleatório)
    """
    if filtros is None:
        filtros = {}

    assunto = filtros.get("assunto", "").strip().lower()
    autor = filtros.get("autor", "").strip().lower()
    pais_filtro = filtros.get("pais", "").strip()

    params = {}
    is_title_search = False
    
    if filtros.get("titulo"):
        params["title"] = filtros["titulo"].strip()
        is_title_search = True
        tipo_sorteio = "BUSCA POR TÍTULO"
        pais_escolhido = pais_filtro if pais_filtro else "Desconhecido"
    else:
        if assunto:
            params["subject"] = assunto
        if autor:
            params["author"] = autor

        # Tratar a opção de sorteio (1 ou 2)
        if str(opcao) == "2":
            # Global
            tipo_sorteio = "LIVRO GLOBAL"
            pais_escolhido = "Desconhecido"
            if not params:
                temas = ["fiction", "history", "science", "fantasy", "mystery", "philosophy", "biography", "adventure"]
                params["subject"] = random.choice(temas)
        else:
            # Opção 1 (País)
            if pais_filtro:
                pais_escolhido = pais_filtro
            else:
                pais_escolhido = random.choice(PAISES_COMUNS)
                
            params["place"] = pais_escolhido
            tipo_sorteio = f"LIVRO ALEATÓRIO: {pais_escolhido.upper()}"

    # Pegamos um conjunto de resultados para sortear um aleatoriamente
    params["limit"] = 50

    url = "https://openlibrary.org/search.json"

    headers = {
        "User-Agent": "KinoMap/1.0"
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        if response.status_code != 200:
            return {"error": "Erro de comunicação com a OpenLibrary."}

        dados = response.json()
        items = dados.get("docs", [])
        
        if not items:
            return {"error": "Nenhum livro encontrado com esses filtros."}

        # Seleciona o livro
        if is_title_search:
            livro_escolhido = items[0]
        else:
            # Aleatório ou Global
            livro_escolhido = random.choice(items)
            
        # Se Global, tentar adivinhar o país baseado no 'place' se disponível
        if str(opcao) == "2" and "place" in livro_escolhido and livro_escolhido["place"]:
            pais_escolhido = livro_escolhido["place"][0]
        
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
                pass 

        if len(sinopse) > 300:
            sinopse = sinopse[:297] + "..."

        cover_i = livro_escolhido.get("cover_i")
        capa = ""
        if cover_i:
            capa = f"https://covers.openlibrary.org/b/id/{cover_i}-L.jpg"
        else:
            # Fallback para o Google Books API se não tiver capa
            try:
                gb_url = "https://www.googleapis.com/books/v1/volumes"
                gb_params = {"q": f"intitle:{titulo} inauthor:{autores.split(',')[0]}", "maxResults": 1}
                gb_res = requests.get(gb_url, params=gb_params, timeout=5)
                if gb_res.status_code == 200:
                    gb_items = gb_res.json().get("items", [])
                    if gb_items:
                        image_links = gb_items[0].get("volumeInfo", {}).get("imageLinks", {})
                        # Tentar pegar um tamanho maior se possível, senão thumbnail
                        capa = image_links.get("thumbnail", "").replace("http:", "https:")
            except Exception:
                pass
            
        # Buscar coordenadas do país para o mapa
        coords = None
        if pais_escolhido and pais_escolhido != "Desconhecido":
            try:
                geolocator = Nominatim(user_agent="filmes_global_app")
                location = geolocator.geocode(pais_escolhido)
                if location:
                    coords = {"lat": location.latitude, "lon": location.longitude}
            except Exception:
                pass

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
            "tipo": tipo_sorteio,
            "pais": pais_escolhido,
            "coordenadas": coords
        }

    except Exception as e:
        return {"error": f"Erro ao buscar livro: {str(e)}"}


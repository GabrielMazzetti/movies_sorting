"""
Módulo central de normalização de nomes de país.

Usado por consultar_paises.py, tratar_paises.py e normalizar_paises.py
para garantir que o mesmo país nunca apareça sob nomes diferentes
(traduções, grafias antigas, nomes históricos, erros de digitação).
"""

import unicodedata

# ==========================================
# MAPA DE NORMALIZAÇÃO
# Chave: qualquer variante que pode aparecer nas fontes (Wikidata, TMDb,
#        akas, IA, digitação manual)
# Valor: nome canônico em português que o projeto deve usar
# ==========================================
MAPA_NORMALIZACAO = {
    # --- Códigos de região do title.akas (ISO 3166-1) ---
    "US": "Estados Unidos", "GB": "Reino Unido", "FR": "França",
    "DE": "Alemanha", "IT": "Itália", "ES": "Espanha", "JP": "Japão",
    "CN": "China", "BR": "Brasil", "CA": "Canadá", "MX": "México",
    "KR": "Coreia do Sul", "IN": "Índia", "AU": "Austrália",
    "SU": "Rússia", "RU": "Rússia",  
    # --- Nomes em inglês vindos do TMDb ---
    "Turkey": "Turquia",
    "Romania": "Roménia",
    "Romênia": "Roménia",
    "Serbia": "Sérvia",
    "Latvia": "Letónia",
    "Hungary": "Hungria",
    "Lithuania": "Lituânia",
    "South Africa": "África do Sul",
    "Iran": "Irão",
    "Egypt": "Egito",
    "Georgia": "Geórgia",
    "Estonia": "Estónia",
    "Iceland": "Islândia",
    "United Arab Emirates": "Emirados Árabes Unidos",
    "New Zealand": "Nova Zelândia",
    "Afghanistan": "Afeganistão",
    "Vietnam": "Vietname",
    "Sweden": "Suécia",
    "Netherlands": "Países Baixos",
    "Singapore": "Singapura",
    "Philippines": "Filipinas",
    "Greece": "Grécia",
    "Bulgaria": "Bulgária",
    "Poland": "Polónia",
    "Belgium": "Bélgica",
    "Malaysia": "Malásia",
    "Morocco": "Marrocos",
    "Azerbaijan": "Azerbaijão",
    "Croatia": "Croácia",
    "Ireland": "Irlanda",
    "Panama": "Panamá",
    "Thailand": "Tailândia",
    "Austria": "Áustria",
    "Indonesia": "Indonésia",
    "Saudi Arabia": "Arábia Saudita",
    "Colombia": "Colômbia",
    "Dominican Republic": "República Dominicana",
    "Luxembourg": "Luxemburgo",
    "Macedonia": "Macedónia do Norte",
    "Denmark": "Dinamarca",
    "Kazakhstan": "Cazaquistão",
    "Switzerland": "Suíça",
    "Czech Republic": "Chéquia",
    "Norway": "Noruega",
    "Cyprus": "Chipre",
    "Finland": "Finlândia",
    "Cambodia": "Camboja",
    "Puerto Rico": "Porto Rico",
    "Ukraine": "Ucrânia",
    "Slovenia": "Eslovénia",
    "Lebanon": "Líbano",
    "Iraq": "Iraque",

    # --- Nomes históricos / regimes antigos -> país atual ---
    "União Soviética": "Rússia",
    "República Socialista Federativa Soviética Russa": "Rússia",
    "Império Russo": "Rússia",
    "Jugoslávia": "Sérvia",
    "Iugoslávia": "Sérvia",
    "República Federal da Jugoslávia": "Sérvia",
    "República Socialista Federativa da Jugoslávia": "Sérvia",
    "União Estatal da Sérvia e Montenegro": "Sérvia",
    "Sérvia e Montenegro": "Sérvia",
    "Checoslováquia": "Chéquia",
    "Tchecoslováquia": "Chéquia",
    "República Socialista da Tchecoslováquia": "Chéquia",
    "Protetorado da Boêmia e Morávia": "Chéquia",
    "Alemanha Ocidental": "Alemanha",
    "Alemanha Oriental": "Alemanha",
    "República Democrática Alemã": "Alemanha",
    "República de Weimar": "Alemanha",
    "Reich Alemão": "Alemanha",
    "Alemanha Nazi": "Alemanha",
    "República Popular da Bulgária": "Bulgária",
    "República Popular da Romênia": "Roménia",
    "República Socialista da Romênia": "Roménia",
    "República Popular da Hungria": "Hungria",
    "República Popular da Polônia": "Polónia",
    "República Socialista Soviética Geórgia": "Geórgia",
    "República Socialista Soviética Azeri": "Azerbaijão",
    "República Socialista Soviética Moldava": "Moldávia",
    "República Socialista da Eslovénia": "Eslovénia",
    "Reino da Itália": "Itália",
    "Reino da Grã-Bretanha": "Reino Unido",
    "Império do Japão": "Japão",
    "República da China": "Taiwan",
    "Ilha Formosa": "Taiwan",
    "Reino dos Países Baixos": "Países Baixos",
    "Império Otomano": "Turquia",
    "Raj Britânico": "Índia",

    # --- Territórios / regiões do Reino Unido -> Reino Unido ---
    "Inglaterra": "Reino Unido",
    "Escócia": "Reino Unido",
    "Irlanda do Norte": "Reino Unido",
    "Hong Kong britânico": "Hong Kong",

    # --- Palestina: unificar variantes ---
    "Palestina": "Estado da Palestina",
    "Territórios palestinianos": "Estado da Palestina",

    # --- Cidades/territórios usados por engano como país ---
    "Vilnius": "Lituânia",
    "China continental": "China",

    # --- Erros de digitação / grafia inconsistente ---
    "Países Baixes": "Países Baixos",

    # --- Frases inválidas da IA (nunca são um país) ---
    "Por favor, forneça as informações sobre o filme Estou pronto para responder": None,
    "Não há informações suficientes para determinar o país de origem principal do filme": None,

    # --- Não são países soberanos / dados sem valor pro sorteio ---
    "Antarctica": None,
}


def _normalizar_chave(texto: str) -> str:
    """Remove espaços extras nas pontas, mantendo acentos e maiúsculas
    (o mapa é indexado com o texto 'como aparece' nas fontes)."""
    return " ".join(str(texto).strip().split())


def normalizar_pais(nome):
    """
    Recebe um nome de país (de qualquer fonte) e devolve o nome canônico
    em português, ou None se o valor não representa um país válido.

    Se o nome não estiver no mapa, devolve ele mesmo sem alteração
    (assume que já está no formato correto).
    """
    if nome is None:
        return None

    nome_limpo = _normalizar_chave(nome)

    if nome_limpo == "" or nome_limpo.lower() in {"nan", "none", "n/a", "desconhecido"}:
        return None

    if nome_limpo in MAPA_NORMALIZACAO:
        return MAPA_NORMALIZACAO[nome_limpo]

    return nome_limpo


# ==========================================
# LISTA DE REFERÊNCIA PARA VALIDAR RESPOSTAS DA IA
# Todo país canônico que o pipeline reconhece. Usado para rejeitar
# respostas da IA que não sejam um nome de país de verdade.
# ==========================================
PAISES_CANONICOS = {
    v for v in MAPA_NORMALIZACAO.values() if v is not None
} | {
    "Alemanha", "Argentina", "Argélia", "Arménia", "Arábia Saudita", "Austrália",
    "Azerbaijão", "Bahamas", "Bangladesh", "Bielorrússia", "Bolívia", "Botsuana",
    "Brasil", "Bulgária", "Bélgica", "Bósnia e Herzegovina", "Camboja", "Canadá",
    "Catar", "Cazaquistão", "Chile", "China", "Chipre", "Chéquia", "Colômbia",
    "Coreia do Sul", "Coreia do Norte", "Croácia", "Cuba", "Dinamarca", "Egito",
    "Emirados Árabes Unidos", "Equador", "Eslováquia", "Eslovénia", "Espanha",
    "Estado da Palestina", "Estados Unidos", "Estónia", "Filipinas", "Finlândia",
    "França", "Geórgia", "Grécia", "Gâmbia", "Hungria", "Indonésia", "Iraque",
    "Irlanda", "Irão", "Islândia", "Israel", "Itália", "Jamaica", "Japão",
    "Jordânia", "Letónia", "Liechtenstein", "Lituânia", "Luxemburgo", "Líbano",
    "Líbia", "Macedónia do Norte", "Malta", "Malásia", "Marrocos", "Mauritânia",
    "Montenegro", "Myanmar", "México", "Mónaco", "Noruega", "Nova Zelândia",
    "Panamá", "Paquistão", "Países Baixos", "Peru", "Polónia", "Portugal",
    "Quénia", "Roménia", "Rússia", "Senegal", "Singapura", "Suécia", "Suíça",
    "Sérvia", "Síria", "Tailândia", "Taiwan", "Tunísia", "Turquia", "Ucrânia",
    "Uganda", "Uruguai", "Venezuela", "Vietname", "África do Sul", "Áustria",
    "Índia", "Hong Kong", "Sri Lanka", "Nepal", "Camarões", "Sudão", "Kosovo",
    "Etiópia", "Zâmbia", "Papua-Nova Guiné", "Paraguai", "Nicarágua", "Gana",
    "Somália", "Angola", "Namíbia", "Zimbábue", "Honduras", "Trindade e Tobago",
    "Haiti", "Usbequistão", "Maurícia", "Tanzânia", "República Centro-Africana",
    "St. Kitts and Nevis", "Costa Rica", "Kuwait", "Ruanda", "Andorra", "Curaçau",
    "Guatemala", "Moldávia", "Butão", "Chade", "Costa do Marfim", "Lesoto",
    "Nigéria", "Vaticano", "Tajiquistão", "Mongólia", "Burquina Fasso",
    "Quirguistão", "Mali", "Laos", "Moçambique", "Benim", "República Dominicana",
    "Albânia", "Uganda", "Turks and Caicos Islands", "Gronelândia",
}

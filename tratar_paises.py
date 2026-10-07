import os
import pandas as pd
from dotenv import load_dotenv
from groq import Groq
from normalizar_pais import normalizar_pais, PAISES_CANONICOS

# ==========================================
# CONFIGURAÇÕES DA IA (GROQ - 100% GRATUITO)
# ==========================================
load_dotenv()
CHAVE_API_GROQ = os.environ.get("GROQ_API_KEY")

# Nome do modelo usado nas chamadas à Groq. A Groq descontinua modelos
# periodicamente — se voltar a dar erro "model_not_found", confira os
# modelos ativos em: https://console.groq.com/docs/models
MODELO_IA = "openai/gpt-oss-20b"

def configurar_ia():
    """Inicializa o cliente da Groq."""
    if CHAVE_API_GROQ and CHAVE_API_GROQ.startswith("gsk_"):
        try:
            return Groq(api_key=CHAVE_API_GROQ)
        except Exception as e:
            print(f"Erro ao inicializar cliente Groq: {e}")
            return None
    return None

def limpar_pais_existente(pais):
    """Padroniza nomes de países que já existem na base, usando o
    módulo central de normalização."""
    if pd.isna(pais) or str(pais).strip() == "" or str(pais).lower() == 'nan':
        return 'Desconhecido'

    pais_str = str(pais).strip()

    if ',' in pais_str:
        pais_str = pais_str.split(',')[0].strip()
    elif '/' in pais_str:
        pais_str = pais_str.split('/')[0].strip()

    normalizado = normalizar_pais(pais_str)
    return normalizado if normalizado else 'Desconhecido'

def adivinhar_pais_com_ia(cliente_ia, titulo, idioma):
    """Pede para a IA (Groq) inferir o país com base no título e idioma.
    Valida a resposta contra a lista de países conhecidos antes de aceitar —
    isso evita salvar frases de recusa/explicação como se fossem um país."""
    if not cliente_ia or pd.isna(titulo) or str(titulo).strip() == "":
        return 'Desconhecido'

    prompt = f"""Você é um especialista em cinema.
Baseado nas seguintes informações sobre um filme, retorne APENAS o nome do país de origem principal em português (exemplo: Estados Unidos, França, Japão, Brasil).
Responda com o nome do país e mais nada — sem frases, sem explicações.
Se você realmente não souber, responda exatamente 'Desconhecido'.

Título: {titulo}
Idioma Original: {idioma}"""

    try:
        response = cliente_ia.chat.completions.create(
            model=MODELO_IA,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=30,
            temperature=0.0
        )
        resultado = response.choices[0].message.content.strip().replace(".", "")

        if not resultado:
            return 'Desconhecido'

        # Validação: a resposta precisa ser curta (nome de país, não frase)
        # e precisa bater com um país conhecido depois de normalizada.
        if len(resultado.split()) > 5:
            return 'Desconhecido'

        normalizado = normalizar_pais(resultado)

        if normalizado and normalizado in PAISES_CANONICOS:
            return normalizado

        return 'Desconhecido'
    except Exception as e:
        print(f"\n[ERRO IA] Falha ao consultar filme '{titulo}': {e}")
        return 'Desconhecido'

def aplicar_tratamento_paises(df_mesclado):
    """Função principal de tratamento e inferência de países."""
    print("\n==========================================")
    print("INICIANDO ETAPA DE TRATAMENTO E IA (GROQ)")
    print("==========================================")
    
    df = df_mesclado.copy()
    
    col_pais = 'countryLabel' if 'countryLabel' in df.columns else None
    colunas_titulo = ['primaryTitle', 'originalTitle', 'movie_title', 'titulo', 'title']
    col_titulo = next((c for c in colunas_titulo if c in df.columns), None)
    
    colunas_idioma = ['originalLanguage', 'original_language', 'idioma', 'lang']
    col_idioma = next((c for c in colunas_idioma if c in df.columns), None)

    if not col_pais or not col_titulo:
        print("✗ Colunas necessárias não encontradas no DataFrame.")
        return df

    # Step 1: Limpeza nos nomes já existentes
    print("1/2. Padronizando países já identificados...")
    df['countryLabel'] = df[col_pais].apply(limpar_pais_existente)
    
    # Step 2: Tratamento de Desconhecidos via IA
    mascara_desconhecidos = (df['countryLabel'] == 'Desconhecido')
    total_desconhecidos = mascara_desconhecidos.sum()
    
    print(f"2/2. Filmes sem país ('Desconhecido'): {total_desconhecidos:,}")
    
    if total_desconhecidos > 0:
        cliente_ia = configurar_ia()
        
        if cliente_ia:
            print(f"→ Enviando {total_desconhecidos:,} filmes para consulta via Groq ({MODELO_IA})...")
            
            contador = 0
            def processar_linha(row):
                nonlocal contador
                contador += 1
                if contador % 25 == 0 or contador == total_desconhecidos:
                    print(f"   Progresso da IA: {contador}/{total_desconhecidos}...", end="\r")
                
                titulo = row.get(col_titulo, '')
                idioma = row.get(col_idioma, '') if col_idioma else ''
                return adivinhar_pais_com_ia(cliente_ia, titulo, idioma)

            df.loc[mascara_desconhecidos, 'countryLabel'] = df[mascara_desconhecidos].apply(processar_linha, axis=1)
            
            recuperados = (df.loc[mascara_desconhecidos, 'countryLabel'] != 'Desconhecido').sum()
            print(f"\n✓ IA finalizada! Países recuperados: {recuperados:,} de {total_desconhecidos:,}")
        else:
            print("⚠ Chave da API da Groq não encontrada. Verifique se GROQ_API_KEY está definida no arquivo .env.")

    print("✓ Tratamento concluído com sucesso!")
    return df

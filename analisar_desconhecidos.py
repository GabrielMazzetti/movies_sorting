import pandas as pd
from pathlib import Path

def analisar_desconhecidos(arquivo_entrada):
    print("==========================================")
    print("  DIAGNÓSTICO DE FILMES DESCONHECIDOS     ")
    print("==========================================\n")

    # 1. Carregar a base de dados
    caminho = Path(arquivo_entrada)
    if not caminho.exists():
        print(f"Erro: O arquivo '{arquivo_entrada}' não foi encontrado.")
        print("Verifique se o script anterior (junção) foi executado com sucesso.")
        return

    try:
        df = pd.read_csv(caminho, low_memory=False)
    except Exception as e:
        print(f"Erro ao ler o arquivo: {e}")
        return

    # Mapeamento dinâmico das colunas
    col_pais = 'countryLabel' if 'countryLabel' in df.columns else None
    colunas_idioma = ['originalLanguage', 'original_language', 'idioma', 'lang']
    col_idioma = next((c for c in colunas_idioma if c in df.columns), None)
    
    colunas_ano = ['startYear', 'release_year', 'ano', 'year']
    col_ano = next((c for c in colunas_ano if c in df.columns), None)

    if not col_pais:
        print("Erro: Coluna de país ('countryLabel') não encontrada na base.")
        return

    # 2. Filtrar os desconhecidos (pegando vazios, nulos, NaN e variações de texto)
    mascara_vazios = (
        df[col_pais].isna() | 
        (df[col_pais].astype(str).str.strip() == "") | 
        (df[col_pais].astype(str).str.lower().isin(['desconhecido', 'nan', 'none', 'null', 'n/a']))
    )
    
    df_desconhecidos = df[mascara_vazios].copy()
    total_desconhecidos = len(df_desconhecidos)
    total_geral = len(df)

    print(f"Total de filmes na base: {total_geral:,}")
    print(f"Total de 'Desconhecidos' / Sem país: {total_desconhecidos:,} ({(total_desconhecidos/total_geral)*100:.1f}% da base)\n")

    if total_desconhecidos == 0:
        print("Boas notícias: Nenhum filme desconhecido encontrado!")
        return

    # 3. Análise Rápida de Idiomas
    if col_idioma:
        print(f"--> Top 10 Idiomas entre os Desconhecidos (Coluna: {col_idioma}):")
        print(df_desconhecidos[col_idioma].value_counts(dropna=False).head(10))
        print("-" * 40)

    # 4. Análise Rápida de Anos
    if col_ano:
        print(f"--> Top 5 Anos de Lançamento com mais Desconhecidos (Coluna: {col_ano}):")
        print(df_desconhecidos[col_ano].value_counts(dropna=False).head(5))
        print("-" * 40)

    # 5. Exportar para análise manual
    arquivo_saida = "filmes_desconhecidos_foco.csv"
    
    colunas_exportacao = df_desconhecidos.columns.tolist()
    colunas_prioritarias = [c for c in ['primaryTitle', 'originalTitle', col_idioma, col_ano] if c in colunas_exportacao]
    outras_colunas = [c for c in colunas_exportacao if c not in colunas_prioritarias]
    
    df_desconhecidos = df_desconhecidos[colunas_prioritarias + outras_colunas]
    
    df_desconhecidos.to_csv(arquivo_saida, index=False, encoding='utf-8-sig')
    print(f"✓ Base de foco exportada com sucesso: {arquivo_saida}")
    print("Abra este arquivo no Excel para procurarmos padrões visuais!")

if __name__ == "__main__":
    analisar_desconhecidos("dados/filmes_com_paises.csv")

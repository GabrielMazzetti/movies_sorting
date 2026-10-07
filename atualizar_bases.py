import requests
import gzip
import shutil
import json
from pathlib import Path


# ==========================================
# CONFIGURAÇÕES
# ==========================================

DADOS = Path("dados")

URLS = {
    "title.basics": "https://datasets.imdbws.com/title.basics.tsv.gz",
    "title.ratings": "https://datasets.imdbws.com/title.ratings.tsv.gz"
}

ARQUIVO_CONTROLE = DADOS / "controle_atualizacao.json"


# ==========================================
# CONTROLE DE ATUALIZAÇÃO
# ==========================================

def carregar_controle():

    if not ARQUIVO_CONTROLE.exists():
        return {}

    try:

        with open(
            ARQUIVO_CONTROLE,
            "r",
            encoding="utf-8"
        ) as arquivo:

            return json.load(arquivo)

    except Exception:

        print(
            "⚠ Não foi possível ler o "
            "controle de atualização."
        )

        return {}


def salvar_controle(controle):

    with open(
        ARQUIVO_CONTROLE,
        "w",
        encoding="utf-8"
    ) as arquivo:

        json.dump(
            controle,
            arquivo,
            indent=4,
            ensure_ascii=False
        )


# ==========================================
# LOCALIZAR BASE ATUAL
# ==========================================

def encontrar_base(nome):

    arquivos = list(
        DADOS.glob(f"{nome}_*.tsv")
    )

    if not arquivos:
        return None

    return max(
        arquivos,
        key=lambda arquivo: int(
            arquivo.stem.split("_")[-1]
        )
    )


# ==========================================
# DOWNLOAD
# ==========================================

def baixar_base(url, arquivo_saida):

    arquivo_gz = arquivo_saida.with_suffix(
        ".tsv.gz"
    )

    print(f"  Baixando: {url}")

    with requests.get(
        url,
        stream=True,
        timeout=300
    ) as response:

        response.raise_for_status()

        with open(
            arquivo_gz,
            "wb"
        ) as arquivo:

            for bloco in response.iter_content(
                chunk_size=1024 * 1024
            ):

                if bloco:
                    arquivo.write(bloco)

    print("  ✓ Download concluído")

    print("  Extraindo...")

    with gzip.open(
        arquivo_gz,
        "rb"
    ) as entrada:

        with open(
            arquivo_saida,
            "wb"
        ) as saida:

            shutil.copyfileobj(
                entrada,
                saida
            )

    print("  ✓ Extração concluída")

    arquivo_gz.unlink()

    print("  ✓ Arquivo .gz removido")


# ==========================================
# ATUALIZAR UMA BASE
# ==========================================

def atualizar_base(
    nome,
    url,
    controle
):

    print()
    print("=" * 50)
    print(f"VERIFICANDO {nome}")
    print("=" * 50)

    atual = encontrar_base(nome)

    if atual:

        print(
            f"Base local: {atual}"
        )

    else:

        print(
            "⚠ Nenhuma base local encontrada."
        )


    # ======================================
    # VERIFICAR DATA NO IMDb
    # ======================================

    try:

        response = requests.head(
            url,
            allow_redirects=True,
            timeout=30
        )

        response.raise_for_status()

        data_remota = response.headers.get(
            "Last-Modified"
        )

    except Exception as erro:

        print(
            f"❌ Erro ao verificar IMDb: {erro}"
        )

        return False


    data_local = controle.get(nome)

    print(
        f"Última modificação no IMDb: "
        f"{data_remota}"
    )

    print(
        f"Última modificação registrada: "
        f"{data_local}"
    )


    # ======================================
    # VERIFICAR SE JÁ ESTÁ ATUALIZADO
    # ======================================

    if (
        atual is not None
        and data_local is not None
        and data_remota == data_local
    ):

        print(
            "✓ Base já está atualizada."
        )

        return False


    # ======================================
    # DETERMINAR NOVA VERSÃO
    # ======================================

    if atual:

        try:

            versao_atual = int(
                atual.stem.split("_")[-1]
            )

        except ValueError:

            versao_atual = 0

    else:

        versao_atual = 0


    nova_versao = versao_atual + 1

    arquivo_novo = (
        DADOS /
        f"{nome}_{nova_versao}.tsv"
    )


    print(
        f"\nNova versão: {arquivo_novo}"
    )


    # ======================================
    # BAIXAR
    # ======================================

    try:

        baixar_base(
            url,
            arquivo_novo
        )

    except Exception as erro:

        print(
            f"\n❌ Erro durante download:"
            f" {erro}"
        )

        if arquivo_novo.exists():
            arquivo_novo.unlink()

        return False


    # ======================================
    # ATUALIZAR CONTROLE
    # ======================================

    controle[nome] = data_remota

    salvar_controle(controle)


    # ======================================
    # REMOVER VERSÃO ANTERIOR
    # ======================================

    if atual and atual != arquivo_novo:

        print(
            f"Removendo versão anterior:"
            f" {atual}"
        )

        atual.unlink()


    print(
        f"\n✓ {nome} atualizado!"
    )

    return True


# ==========================================
# EXECUÇÃO
# ==========================================

DADOS.mkdir(
    exist_ok=True
)

print()
print("=" * 50)
print("ATUALIZAÇÃO DAS BASES IMDb")
print("=" * 50)


controle = carregar_controle()


atualizou = False


for nome, url in URLS.items():

    resultado = atualizar_base(
        nome,
        url,
        controle
    )

    if resultado:
        atualizou = True


print()
print("=" * 50)
print("RESULTADO")
print("=" * 50)


if atualizou:

    print(
        "✓ Pelo menos uma base foi atualizada."
    )

else:

    print(
        "✓ Nenhuma atualização necessária."
    )

print()

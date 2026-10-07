import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()
chave = os.environ.get('TMDB_API_KEY')

print(f"Chave carregada: {chave[:6]}..." if chave else "✗ Chave NÃO encontrada no .env")

t0 = time.time()
try:
    r = requests.get(
        'https://api.themoviedb.org/3/configuration',
        timeout=10,
        params={'api_key': chave}
    )
    print('Status:', r.status_code, '| Tempo:', round(time.time() - t0, 2), 's')
except Exception as e:
    print('Erro:', type(e).__name__, e, '| Tempo:', round(time.time() - t0, 2), 's')
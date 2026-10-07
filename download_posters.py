import os
import requests

urls = [
    "https://image.tmdb.org/t/p/w300/qJ2tW6WMUDux911r6m7haRef0WH.jpg", # Dark Knight
    "https://image.tmdb.org/t/p/w300/ow3wq89wM8qd5X7hWKxiRfsFf9C.jpg", # 12 Angry Men
    "https://image.tmdb.org/t/p/w300/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg", # Interstellar
    "https://image.tmdb.org/t/p/w300/7IiTTgloJzvGI1TAYymCfbfl3vT.jpg", # Parasite
    "https://image.tmdb.org/t/p/w300/ty8TGRuvJLPUmAR1H1nRIsgwvim.jpg", # Gladiator
    "https://image.tmdb.org/t/p/w300/arw2vcBveWOVZr6pxd9XTd1TdQa.jpg", # Forrest Gump
    "https://image.tmdb.org/t/p/w300/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg", # Fight Club
    "https://image.tmdb.org/t/p/w300/q6y0Go1tsGEsmtFryDOJo3dEmqu.jpg", # Shawshank
    "https://image.tmdb.org/t/p/w300/3bhkrj58Vtu7enYsRolD1fZdja1.jpg", # Godfather
    "https://image.tmdb.org/t/p/w300/d5iIlFn5s0ImszYzBPb8SPCPGtx.jpg", # Pulp Fiction
    "https://image.tmdb.org/t/p/w300/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg", # Inception
    "https://image.tmdb.org/t/p/w300/gLhWXqKAibHqKxcA3Mmd0rQ4D1h.jpg", # City of God
    "https://image.tmdb.org/t/p/w300/39wmItIWsg5sZMyRU84glV60gO.jpg", # Spirited Away
    "https://image.tmdb.org/t/p/w300/mfnkSeeVOBVheuyn2lo4tfmOPQb.jpg", # Life is Beautiful
    "https://image.tmdb.org/t/p/w300/7gu1TqgO48Z122V36T9dJEqbEbw.jpg"  # Whiplash
]

os.makedirs('static/images/posters', exist_ok=True)
for i, url in enumerate(urls):
    try:
        r = requests.get(url)
        if r.status_code == 200:
            with open(f'static/images/posters/poster_{i}.jpg', 'wb') as f:
                f.write(r.content)
    except Exception as e:
        print(f"Failed {url}: {e}")


"""
Busca os 2 canais "perdidos" no YouTube Search API
Talvez eles mudaram de URL/handle
"""

import os
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("YOUTUBE_API_KEY_3")

if not API_KEY:
    print("[ERRO] API KEY nao configurada!")
    exit(1)

# Canais perdidos
SEARCH_QUERIES = [
    "Abandoned History",
    "AbandonedHistoryy",
    "The Sharpline",
    "Sharpline"
]


async def search_youtube(query):
    """Busca canal no YouTube"""
    print(f"\nBuscando: '{query}'")

    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        'part': 'snippet',
        'q': query,
        'type': 'channel',
        'maxResults': 5,
        'key': API_KEY
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    items = data.get('items', [])

                    if items:
                        print(f"  Encontrados {len(items)} resultados:")
                        for i, item in enumerate(items, 1):
                            channel_id = item['id']['channelId']
                            snippet = item['snippet']

                            print(f"\n  [{i}] {snippet['title']}")
                            print(f"      Channel ID: {channel_id}")
                            print(f"      URL: https://www.youtube.com/channel/{channel_id}")
                            print(f"      Descricao: {snippet.get('description', 'N/A')[:80]}...")
                    else:
                        print("  [X] Nenhum resultado encontrado")

                else:
                    print(f"  [ERRO] Status {response.status}")

    except Exception as e:
        print(f"  [EXCECAO] {e}")

    await asyncio.sleep(1)


async def main():
    print("=" * 80)
    print("BUSCA DOS 2 CANAIS PERDIDOS NO YOUTUBE")
    print("=" * 80)

    for query in SEARCH_QUERIES:
        await search_youtube(query)

    print("\n" + "=" * 80)
    print("BUSCA CONCLUIDA")
    print("=" * 80)
    print("\nSe encontrou algum resultado, verifique:")
    print("1. Channel ID e URL")
    print("2. Se e realmente o canal que procuramos")
    print("3. Atualizar URL no banco se necessario")


if __name__ == "__main__":
    asyncio.run(main())

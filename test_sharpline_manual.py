"""
Teste MANUAL detalhado do canal The Sharpline
Simula exatamente o que o collector faz
"""

import os
import asyncio
import aiohttp
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

# The Sharpline - Canal com 1.5M views/mês que está falhando!
CANAL_URL = "https://www.youtube.com/channel/UCBUHz55XNkm2PKwF_QdMCJQ"
CANAL_NOME = "The Sharpline"
CHANNEL_ID = "UCBUHz55XNkm2PKwF_QdMCJQ"

# Usar KEY_3 (primeira key)
API_KEY = os.environ.get("YOUTUBE_API_KEY_3")

if not API_KEY:
    print("[ERRO] YOUTUBE_API_KEY_3 nao configurada!")
    print("Configure no .env para testar localmente")
    exit(1)


async def test_channel_info():
    """Testa busca de informações do canal"""
    print("=" * 80)
    print("TESTE 1: BUSCAR INFORMACOES DO CANAL")
    print("=" * 80)
    print("")

    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        'part': 'statistics,snippet',
        'id': CHANNEL_ID,
        'key': API_KEY
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                print(f"Status HTTP: {response.status}")

                if response.status == 200:
                    data = await response.json()

                    if data.get('items'):
                        channel = data['items'][0]
                        stats = channel.get('statistics', {})
                        snippet = channel.get('snippet', {})

                        print(f"[OK] Canal encontrado!")
                        print(f"  Nome: {snippet.get('title')}")
                        print(f"  Inscritos: {int(stats.get('subscriberCount', 0)):,}")
                        print(f"  Videos: {int(stats.get('videoCount', 0)):,}")
                        print(f"  Views totais: {int(stats.get('viewCount', 0)):,}")
                        print("")
                        return True
                    else:
                        print("[ERRO] Response vazio - sem 'items'!")
                        print(f"Response: {data}")
                        return False
                else:
                    error_text = await response.text()
                    print(f"[ERRO] Status {response.status}")
                    print(f"Response: {error_text}")
                    return False

    except Exception as e:
        print(f"[EXCECAO] {e}")
        return False


async def test_video_search():
    """Testa busca de vídeos (últimos 30 dias)"""
    print("=" * 80)
    print("TESTE 2: BUSCAR VIDEOS (ULTIMOS 30 DIAS)")
    print("=" * 80)
    print("")

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
    print(f"Buscando videos desde: {cutoff_date.isoformat()}")
    print("")

    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        'part': 'id,snippet',
        'channelId': CHANNEL_ID,
        'type': 'video',
        'order': 'date',
        'maxResults': 50,
        'publishedAfter': cutoff_date.isoformat(),
        'key': API_KEY
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                print(f"Status HTTP: {response.status}")

                if response.status == 200:
                    data = await response.json()

                    total_results = data.get('pageInfo', {}).get('totalResults', 0)
                    items = data.get('items', [])

                    print(f"[OK] Total de videos encontrados: {total_results}")
                    print(f"[OK] Videos nesta pagina: {len(items)}")
                    print("")

                    if items:
                        print("Primeiros 5 videos:")
                        for i, item in enumerate(items[:5], 1):
                            video_id = item['id']['videoId']
                            titulo = item['snippet']['title']
                            pub_date = item['snippet']['publishedAt']

                            print(f"  [{i}] {titulo}")
                            print(f"      Video ID: {video_id}")
                            print(f"      Publicado: {pub_date}")
                            print("")

                        return len(items)
                    else:
                        print("[ALERTA] NENHUM video encontrado nos ultimos 30 dias!")
                        print("")
                        print("POSSIVEIS CAUSAS:")
                        print("1. Canal nao publicou videos nos ultimos 30 dias")
                        print("2. Todos os videos sao 'unlisted' ou privados")
                        print("3. publishedAfter esta incorreto")
                        print("4. API esta sendo throttled (soft limit)")
                        print("")
                        return 0

                elif response.status == 403:
                    error_data = await response.json()
                    error_msg = error_data.get('error', {}).get('message', 'Unknown')

                    print(f"[ERRO 403] {error_msg}")
                    print("")

                    if 'quota' in error_msg.lower():
                        print("CAUSA: Quota da API key esgotada!")
                    elif 'ratelimit' in error_msg.lower():
                        print("CAUSA: Rate limit atingido!")
                    else:
                        print("CAUSA: Key suspensa ou outro erro 403")

                    return -1

                else:
                    error_text = await response.text()
                    print(f"[ERRO] Status {response.status}")
                    print(f"Response: {error_text}")
                    return -1

    except Exception as e:
        print(f"[EXCECAO] {e}")
        return -1


async def test_video_details():
    """Testa busca de detalhes de 1 vídeo específico"""
    print("=" * 80)
    print("TESTE 3: BUSCAR DETALHES DE UM VIDEO ESPECIFICO")
    print("=" * 80)
    print("")

    # Vídeo mais recente do The Sharpline (manual check no YouTube)
    # Você pode trocar por um ID real do canal
    video_id = "dQw4w9WgXcQ"  # Placeholder - trocar por real

    print(f"[INFO] Usando video ID placeholder: {video_id}")
    print("[INFO] Para teste real, substituir por ID de video do canal")
    print("")

    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        'part': 'statistics,contentDetails',
        'id': video_id,
        'key': API_KEY
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                print(f"Status HTTP: {response.status}")

                if response.status == 200:
                    data = await response.json()

                    if data.get('items'):
                        video = data['items'][0]
                        stats = video.get('statistics', {})

                        print(f"[OK] Video encontrado!")
                        print(f"  Views: {int(stats.get('viewCount', 0)):,}")
                        print(f"  Likes: {int(stats.get('likeCount', 0)):,}")
                        print(f"  Comentarios: {int(stats.get('commentCount', 0)):,}")
                        return True
                    else:
                        print("[ERRO] Video nao encontrado")
                        return False
                else:
                    print(f"[ERRO] Status {response.status}")
                    return False

    except Exception as e:
        print(f"[EXCECAO] {e}")
        return False


async def main():
    print("")
    print("=" * 80)
    print("TESTE MANUAL DETALHADO - THE SHARPLINE")
    print(f"Canal: {CANAL_NOME}")
    print(f"URL: {CANAL_URL}")
    print(f"Channel ID: {CHANNEL_ID}")
    print("=" * 80)
    print("")

    # Teste 1: Info do canal
    result1 = await test_channel_info()

    if not result1:
        print("[CRITICO] Falhou em buscar info do canal!")
        print("Nao adianta continuar os outros testes...")
        return

    # Teste 2: Busca de vídeos
    videos_found = await test_video_search()

    if videos_found < 0:
        print("[CRITICO] Erro na API ao buscar videos!")
    elif videos_found == 0:
        print("[PROBLEMA IDENTIFICADO!]")
        print("API retorna 0 videos mesmo canal tendo conteudo!")
        print("Isso explica por que views_30d = 0!")
    else:
        print(f"[OK] Encontrou {videos_found} videos")

    # Teste 3: Detalhes de vídeo (opcional)
    # await test_video_details()

    print("")
    print("=" * 80)
    print("TESTE CONCLUIDO")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

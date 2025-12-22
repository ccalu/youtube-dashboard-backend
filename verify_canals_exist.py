"""
Verifica se os 9 canais problemáticos EXISTEM no YouTube
Testa TODOS os formatos de URL
"""

import os
import asyncio
import aiohttp
import re
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("YOUTUBE_API_KEY_3")

if not API_KEY:
    print("[ERRO] YOUTUBE_API_KEY_3 nao configurada!")
    exit(1)

# Os 9 canais problemáticos com suas URLs
CANAIS_TESTE = [
    {
        'id': 837,
        'nome': 'Alan Watts Way',
        'url': 'https://www.youtube.com/@alanwattsway'
    },
    {
        'id': 376,
        'nome': 'The Exploring Mind',
        'url': 'https://www.youtube.com/channel/UCDPpru_Zh7WWtLnOKS7NRIg'
    },
    {
        'id': 167,
        'nome': 'Letters Never Sent',
        'url': 'https://www.youtube.com/channel/UC-HUF3P94Z9ySLIfq3nndwg'
    },
    {
        'id': 416,
        'nome': 'Abandoned History',
        'url': 'https://www.youtube.com/@AbandonedHistoryy'
    },
    {
        'id': 222,
        'nome': 'Legacy of Rome',
        'url': 'https://www.youtube.com/channel/UCPFsHREvRqWUgrcOCL1sHhg'
    },
    {
        'id': 16,
        'nome': 'The Medieval Scroll',
        'url': 'https://www.youtube.com/channel/UCX3YyEUofyj5_Hmv3-JhgJQ'
    },
    {
        'id': 711,
        'nome': 'The Sharpline',
        'url': 'https://www.youtube.com/channel/UCBUHz55XNkm2PKwF_QdMCJQ'
    },
    {
        'id': 715,
        'nome': 'Legado de Lujo',
        'url': 'https://www.youtube.com/@LegadoLujo/featured'
    }
]


def extract_channel_id(url):
    """Extrai channel ID da URL"""
    match = re.search(r'youtube\.com/channel/([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1)
    return None


def extract_handle(url):
    """Extrai handle da URL"""
    match = re.search(r'youtube\.com/@([^/?&#]+)', url)
    if match:
        return match.group(1)
    return None


async def test_channel_by_id(channel_id, canal_nome):
    """Testa busca por channel ID"""
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        'part': 'snippet,statistics',
        'id': channel_id,
        'key': API_KEY
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('items'):
                        channel = data['items'][0]
                        snippet = channel.get('snippet', {})
                        stats = channel.get('statistics', {})

                        return {
                            'existe': True,
                            'metodo': 'channel_id',
                            'nome_real': snippet.get('title'),
                            'inscritos': int(stats.get('subscriberCount', 0))
                        }

                return {'existe': False, 'metodo': 'channel_id', 'erro': 'Nao encontrado'}

    except Exception as e:
        return {'existe': False, 'metodo': 'channel_id', 'erro': str(e)}


async def test_channel_by_handle(handle, canal_nome):
    """Testa busca por handle"""
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        'part': 'snippet,statistics',
        'forHandle': handle,
        'key': API_KEY
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('items'):
                        channel = data['items'][0]
                        snippet = channel.get('snippet', {})
                        stats = channel.get('statistics', {})

                        return {
                            'existe': True,
                            'metodo': 'forHandle',
                            'nome_real': snippet.get('title'),
                            'inscritos': int(stats.get('subscriberCount', 0)),
                            'channel_id': channel.get('id')
                        }

                return {'existe': False, 'metodo': 'forHandle', 'erro': 'Nao encontrado'}

    except Exception as e:
        return {'existe': False, 'metodo': 'forHandle', 'erro': str(e)}


async def verify_canal(canal_info):
    """Verifica se um canal existe"""
    print(f"\nTestando: {canal_info['nome']} (ID {canal_info['id']})")
    print(f"URL: {canal_info['url']}")

    # Tentar por channel ID primeiro (se disponível)
    channel_id = extract_channel_id(canal_info['url'])
    if channel_id:
        print(f"  Tentando por channel_id: {channel_id}")
        result = await test_channel_by_id(channel_id, canal_info['nome'])

        if result['existe']:
            print(f"  [OK] Canal ENCONTRADO via channel_id!")
            print(f"       Nome: {result['nome_real']}")
            print(f"       Inscritos: {result['inscritos']:,}")
            return result
        else:
            print(f"  [X] Nao encontrado via channel_id")

    # Tentar por handle (se disponível)
    handle = extract_handle(canal_info['url'])
    if handle:
        print(f"  Tentando por handle: @{handle}")
        result = await test_channel_by_handle(handle, canal_info['nome'])

        if result['existe']:
            print(f"  [OK] Canal ENCONTRADO via handle!")
            print(f"       Nome: {result['nome_real']}")
            print(f"       Inscritos: {result['inscritos']:,}")
            print(f"       Channel ID: {result['channel_id']}")
            return result
        else:
            print(f"  [X] Nao encontrado via handle")

    print(f"  [ERRO] Canal NAO ENCONTRADO por nenhum metodo!")
    return {'existe': False}


async def main():
    print("=" * 80)
    print("VERIFICACAO DE EXISTENCIA DOS 9 CANAIS PROBLEMATICOS")
    print("=" * 80)

    resultados = []

    for canal in CANAIS_TESTE:
        resultado = await verify_canal(canal)
        resultados.append({
            **canal,
            **resultado
        })

        # Delay entre requests (rate limiting)
        await asyncio.sleep(1)

    # Relatório final
    print("\n" + "=" * 80)
    print("RELATORIO FINAL")
    print("=" * 80)

    canais_existem = sum(1 for r in resultados if r['existe'])
    canais_nao_existem = len(resultados) - canais_existem

    print(f"\nCanais que EXISTEM: {canais_existem}/{len(resultados)}")
    print(f"Canais que NAO EXISTEM: {canais_nao_existem}/{len(resultados)}")

    if canais_nao_existem > 0:
        print("\n[PROBLEMA IDENTIFICADO!]")
        print("Canais que NAO existem:")
        for r in resultados:
            if not r['existe']:
                print(f"  - {r['nome']} (ID {r['id']})")
                print(f"    URL: {r['url']}")

        print("\nCAUSA RAIZ:")
        print("- Canais foram deletados/suspensos pelo YouTube")
        print("- Ou URLs estao incorretas/desatualizadas")
        print("\nSOLUCAO:")
        print("- Marcar esses canais como 'inativo' no banco")
        print("- Ou atualizar URLs se estiverem incorretas")

    else:
        print("\n[OK] Todos os canais existem!")
        print("Causa raiz do bug DEVE ser outra...")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

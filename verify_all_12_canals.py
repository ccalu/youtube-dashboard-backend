"""
Verifica TODOS os 12 canais com erro:
- 6 que nunca coletaram
- 6 que tinham dados mas pararam
"""

import os
import asyncio
import aiohttp
import re
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("YOUTUBE_API_KEY_3")

if not API_KEY:
    print("[ERRO] API KEY nao configurada!")
    exit(1)

# TODOS os 12 canais
CANAIS_TESTE = [
    # CATEGORIA B - Nunca coletaram (6)
    {
        'id': 751,
        'nome': 'Dusunen InsanX',
        'url': 'https://www.youtube.com/@dusunen.insanx',
        'categoria': 'B_NUNCA_COLETOU'
    },
    {
        'id': 757,
        'nome': 'Canal 757 (cirílico)',
        'url': 'https://www.youtube.com/@Криминалъные-Тайны-t7s',
        'categoria': 'B_NUNCA_COLETOU'
    },
    {
        'id': 836,
        'nome': 'Al-Asatir Al-Muharrama',
        'url': 'https://www.youtube.com/@Al-AsatirAl-Muharrama',
        'categoria': 'B_NUNCA_COLETOU'
    },
    {
        'id': 860,
        'nome': 'Financial Dynasties',
        'url': 'https://www.youtube.com/@FinancialDynasties',
        'categoria': 'B_NUNCA_COLETOU'
    },
    {
        'id': 863,
        'nome': 'Dynasties Financieres',
        'url': 'https://www.youtube.com/@DynastiesFinancières',
        'categoria': 'B_NUNCA_COLETOU'
    },
    {
        'id': 866,
        'nome': 'Neraskrytyje Tajny',
        'url': 'https://www.youtube.com/@НераскрытыеТайны',
        'categoria': 'B_NUNCA_COLETOU'
    },

    # CATEGORIA C - Tinham dados mas pararam (6)
    {
        'id': 16,
        'nome': 'The Medieval Scroll',
        'url': 'https://www.youtube.com/channel/UCX3YyEUofyj5_Hmv3-JhgJQ',
        'categoria': 'C_TINHA_DADOS'
    },
    {
        'id': 167,
        'nome': 'Letters Never Sent',
        'url': 'https://www.youtube.com/channel/UC-HUF3P94Z9ySLIfq3nndwg',
        'categoria': 'C_TINHA_DADOS'
    },
    {
        'id': 222,
        'nome': 'Legacy of Rome',
        'url': 'https://www.youtube.com/channel/UCPFsHREvRqWUgrcOCL1sHhg',
        'categoria': 'C_TINHA_DADOS'
    },
    {
        'id': 376,
        'nome': 'The Exploring Mind',
        'url': 'https://www.youtube.com/channel/UCDPpru_Zh7WWtLnOKS7NRIg',
        'categoria': 'C_TINHA_DADOS'
    },
    {
        'id': 715,
        'nome': 'Legado de Lujo',
        'url': 'https://www.youtube.com/@LegadoLujo',
        'categoria': 'C_TINHA_DADOS'
    },
    {
        'id': 837,
        'nome': 'Alan Watts Way',
        'url': 'https://www.youtube.com/@alanwattsway',
        'categoria': 'C_TINHA_DADOS'
    }
]


def extract_channel_id(url):
    """Extrai channel ID da URL"""
    match = re.search(r'youtube\.com/channel/([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1)
    return None


def extract_handle(url):
    """Extrai handle da URL - SUPORTA UNICODE"""
    match = re.search(r'youtube\.com/@([^/?&#]+)', url)
    if match:
        handle = match.group(1)
        # Decodifica URL encoding se necessário
        handle = urllib.parse.unquote(handle)
        return handle
    return None


async def test_channel_by_id(channel_id):
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
                            'inscritos': int(stats.get('subscriberCount', 0)),
                            'channel_id': channel.get('id')
                        }

                return {'existe': False, 'metodo': 'channel_id'}

    except Exception as e:
        return {'existe': False, 'metodo': 'channel_id', 'erro': str(e)}


async def test_channel_by_handle(handle):
    """Testa busca por handle - SUPORTA UNICODE"""
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

                return {'existe': False, 'metodo': 'forHandle'}

    except Exception as e:
        return {'existe': False, 'metodo': 'forHandle', 'erro': str(e)}


async def verify_canal(canal_info):
    """Verifica se um canal existe"""
    result = {'existe': False}

    # Tentar por channel ID primeiro
    channel_id = extract_channel_id(canal_info['url'])
    if channel_id:
        result = await test_channel_by_id(channel_id)
        if result['existe']:
            return result

    # Tentar por handle
    handle = extract_handle(canal_info['url'])
    if handle:
        result = await test_channel_by_handle(handle)
        if result['existe']:
            return result

    return result


async def main():
    print("=" * 80)
    print("VERIFICACAO COMPLETA - 12 CANAIS COM ERRO")
    print("=" * 80)
    print("")

    resultados_b = []  # Nunca coletaram
    resultados_c = []  # Tinham dados mas pararam

    for i, canal in enumerate(CANAIS_TESTE, 1):
        print(f"[{i}/12] Testando: {canal['nome']} (ID {canal['id']})")
        print(f"        Categoria: {canal['categoria']}")

        resultado = await verify_canal(canal)

        resultado_completo = {
            **canal,
            **resultado
        }

        if canal['categoria'] == 'B_NUNCA_COLETOU':
            resultados_b.append(resultado_completo)
        else:
            resultados_c.append(resultado_completo)

        if resultado['existe']:
            nome_safe = resultado['nome_real'].encode('ascii', 'replace').decode('ascii')
            print(f"        [OK] EXISTE - {nome_safe}")
            print(f"        Inscritos: {resultado['inscritos']:,}")
            if resultado.get('channel_id'):
                print(f"        Channel ID: {resultado['channel_id']}")
        else:
            print(f"        [X] NAO EXISTE")

        print("")

        # Delay para rate limiting
        await asyncio.sleep(1)

    # Relatório final
    print("=" * 80)
    print("RELATORIO FINAL")
    print("=" * 80)
    print("")

    # CATEGORIA B
    print("=" * 80)
    print("[B] CANAIS QUE NUNCA COLETARAM (6):")
    print("=" * 80)
    print("")

    existem_b = sum(1 for r in resultados_b if r['existe'])
    nao_existem_b = len(resultados_b) - existem_b

    print(f"Existem: {existem_b}/6")
    print(f"Nao existem: {nao_existem_b}/6")
    print("")

    if nao_existem_b > 0:
        print("Canais que NAO EXISTEM:")
        for r in resultados_b:
            if not r['existe']:
                print(f"  - {r['nome']} (ID {r['id']})")
                print(f"    URL: {r['url']}")
                print(f"    ACAO: Marcar como 'inativo'")
        print("")

    if existem_b > 0:
        print("Canais que EXISTEM (mas nunca coletaram):")
        for r in resultados_b:
            if r['existe']:
                nome_safe = r['nome_real'].encode('ascii', 'replace').decode('ascii')
                print(f"  - {r['nome']} (ID {r['id']})")
                print(f"    Nome real: {nome_safe}")
                print(f"    Inscritos: {r['inscritos']:,}")
                print(f"    Channel ID: {r.get('channel_id', 'N/A')}")
                print(f"    ACAO: URL pode estar incorreta - verificar")
        print("")

    # CATEGORIA C
    print("=" * 80)
    print("[C] CANAIS COM HISTORICO QUE PARARAM (6):")
    print("=" * 80)
    print("")

    existem_c = sum(1 for r in resultados_c if r['existe'])
    nao_existem_c = len(resultados_c) - existem_c

    print(f"Existem: {existem_c}/6")
    print(f"Nao existem: {nao_existem_c}/6")
    print("")

    if nao_existem_c > 0:
        print("Canais que NAO EXISTEM:")
        for r in resultados_c:
            if not r['existe']:
                print(f"  - {r['nome']} (ID {r['id']})")
                print(f"    URL: {r['url']}")
                print(f"    ACAO: Marcar como 'inativo'")
        print("")

    if existem_c > 0:
        print("Canais que EXISTEM (problema temporario):")
        for r in resultados_c:
            if r['existe']:
                nome_safe = r['nome_real'].encode('ascii', 'replace').decode('ascii')
                print(f"  - {r['nome']} (ID {r['id']})")
                print(f"    Nome real: {nome_safe}")
                print(f"    Inscritos: {r['inscritos']:,}")
                print(f"    PROBLEMA: Throttling, timeout ou response vazio")
                print(f"    ACAO: Rate limiting + retry vai resolver")
        print("")

    print("=" * 80)
    print("CONCLUSAO:")
    print("=" * 80)
    total_existem = existem_b + existem_c
    total_nao_existem = nao_existem_b + nao_existem_c

    print(f"\nDos 12 canais com erro:")
    print(f"  - {total_existem} EXISTEM (problema e temporario/configuracao)")
    print(f"  - {total_nao_existem} NAO EXISTEM (marcar como inativo)")
    print("")
    print(f"Com 2 ja removidos anteriormente:")
    print(f"  Total a marcar como inativo: {total_nao_existem + 2}")
    print(f"  Total que podem voltar a funcionar: {total_existem}")
    print("")


if __name__ == "__main__":
    asyncio.run(main())

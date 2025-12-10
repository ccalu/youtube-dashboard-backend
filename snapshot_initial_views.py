"""
Script para capturar snapshot inicial de total_views dos canais monetizados
Roda UMA VEZ para ter ponto de partida
A partir de amanhã, coleta diária calcula views_24h automaticamente
"""
import os
import requests
import asyncio
import aiohttp
from datetime import datetime

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://prvkmzstyedepvlbppyo.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBydmttenN0eWVkZXB2bGJwcHlvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQxNDY3MTQsImV4cCI6MjA1OTcyMjcxNH0.T0aspHrF0tz1G6iVOBIO3zgvs1g5vvQcb25jhGriQGo")

# YouTube API Keys (mesmas do dashboard)
API_KEYS = [
    os.environ.get("YOUTUBE_API_KEY_3"),
    os.environ.get("YOUTUBE_API_KEY_4"),
    os.environ.get("YOUTUBE_API_KEY_5"),
    os.environ.get("YOUTUBE_API_KEY_6"),
    os.environ.get("YOUTUBE_API_KEY_7"),
]

# Remover chaves None
API_KEYS = [k for k in API_KEYS if k]

if not API_KEYS:
    print("⚠️ ERRO: Nenhuma YouTube API Key configurada!")
    print("Configure pelo menos YOUTUBE_API_KEY_3 no .env")
    exit(1)

current_key_index = 0

def get_next_api_key():
    """Rotaciona entre as chaves disponíveis"""
    global current_key_index
    key = API_KEYS[current_key_index]
    current_key_index = (current_key_index + 1) % len(API_KEYS)
    return key

def get_supabase_headers():
    return {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json'
    }

async def get_monetized_channels():
    """Busca canais monetizados do Supabase"""
    url = f'{SUPABASE_URL}/rest/v1/yt_channels?select=channel_id,channel_name&is_monetized=eq.true'

    response = requests.get(url, headers=get_supabase_headers())

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erro ao buscar canais: {response.status_code}")
        return []

async def get_channel_statistics(channel_id, session):
    """Busca statistics do canal via YouTube Data API v3"""
    api_key = get_next_api_key()

    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        'part': 'statistics',
        'id': channel_id,
        'key': api_key
    }

    try:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()

                if 'items' in data and len(data['items']) > 0:
                    stats = data['items'][0]['statistics']
                    return {
                        'viewCount': int(stats.get('viewCount', 0)),
                        'subscriberCount': int(stats.get('subscriberCount', 0)),
                        'videoCount': int(stats.get('videoCount', 0))
                    }

            print(f"⚠️ Erro API para {channel_id}: Status {response.status}")
            return None

    except Exception as e:
        print(f"⚠️ Exceção ao buscar {channel_id}: {e}")
        return None

def save_snapshot_to_supabase(canal_id, channel_name, total_views):
    """Salva snapshot em dados_canais_historico"""

    # Primeiro, buscar o ID interno do canal
    url = f'{SUPABASE_URL}/rest/v1/canais_monitorados?select=id&nome_canal=ilike.%{channel_name}%'
    response = requests.get(url, headers=get_supabase_headers())

    if response.status_code != 200 or not response.json():
        print(f"  ⚠️ Canal {channel_name} não encontrado em canais_monitorados")
        return False

    internal_id = response.json()[0]['id']
    data_coleta = datetime.now().date().isoformat()

    # Salvar snapshot
    url = f'{SUPABASE_URL}/rest/v1/dados_canais_historico'

    payload = {
        'canal_id': internal_id,
        'data_coleta': data_coleta,
        'total_views': total_views
    }

    # Tentar upsert (se já existe snapshot de hoje, atualiza)
    headers = get_supabase_headers()
    headers['Prefer'] = 'resolution=merge-duplicates'

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code in [200, 201, 204]:
        return True
    else:
        print(f"  ⚠️ Erro ao salvar: {response.status_code} - {response.text[:200]}")
        return False

async def main():
    print("=" * 70)
    print("SNAPSHOT INICIAL DE TOTAL_VIEWS")
    print("=" * 70)
    print()
    print(f"YouTube API Keys disponíveis: {len(API_KEYS)}")
    print()

    # Buscar canais monetizados
    channels = await get_monetized_channels()

    if not channels:
        print("⚠️ Nenhum canal monetizado encontrado!")
        return

    print(f"Canais monetizados: {len(channels)}")
    print()

    # Buscar statistics de cada canal
    async with aiohttp.ClientSession() as session:
        success_count = 0

        for canal in channels:
            channel_id = canal['channel_id']
            channel_name = canal['channel_name']

            print(f"📊 {channel_name}")
            print(f"   ID: {channel_id}")

            stats = await get_channel_statistics(channel_id, session)

            if stats:
                total_views = stats['viewCount']
                subscribers = stats['subscriberCount']

                print(f"   Total Views: {total_views:,}")
                print(f"   Inscritos: {subscribers:,}")

                # Salvar no Supabase
                if save_snapshot_to_supabase(channel_id, channel_name, total_views):
                    print(f"   ✅ Snapshot salvo!")
                    success_count += 1
                else:
                    print(f"   ❌ Erro ao salvar")
            else:
                print(f"   ❌ Erro ao buscar statistics")

            print()

            # Aguardar um pouco entre requests
            await asyncio.sleep(0.5)

    print()
    print("=" * 70)
    print(f"CONCLUÍDO: {success_count}/{len(channels)} snapshots salvos")
    print("=" * 70)
    print()
    print("✅ A partir de amanhã (5 AM), coleta diária vai calcular views_24h automaticamente!")

if __name__ == "__main__":
    asyncio.run(main())

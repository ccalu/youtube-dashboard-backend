"""
Script para corrigir 20 canais via Search API
Busca Channel ID correto e atualiza URL no banco
Executado em 11/12/2025
"""
import os
import sys
import io
import time
import requests
from dotenv import load_dotenv
from supabase import create_client, Client

# Fix encoding Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY_3")  # Usar uma das chaves

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# IDs dos 20 canais para corrigir
canais_corrigir = [762, 744, 351, 702, 745, 747, 750, 751, 757, 719, 720, 746, 748, 749, 752, 753, 754, 755, 760, 756]

print("=" * 80)
print("CORRIGINDO 20 CANAIS VIA SEARCH API")
print("=" * 80)
print()

def search_channel_id(canal_name: str) -> str:
    """Busca Channel ID via Search API"""
    try:
        resp = requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                "part": "snippet",
                "type": "channel",
                "q": canal_name,
                "maxResults": 1,
                "key": YOUTUBE_API_KEY
            },
            timeout=10
        )

        if resp.status_code == 200:
            data = resp.json()
            if data.get("items"):
                channel_id = data["items"][0]["id"]["channelId"]
                return channel_id
        else:
            print(f"     API Error: {resp.status_code}")
            return None

    except Exception as e:
        print(f"     Exception: {str(e)}")
        return None

success_count = 0
error_count = 0

for canal_id in canais_corrigir:
    # Buscar info atual
    canal = supabase.table("canais_monitorados")\
        .select("id, nome_canal, url_canal")\
        .eq("id", canal_id)\
        .execute()

    if not canal.data:
        print(f"[{canal_id}] NAO ENCONTRADO no banco")
        error_count += 1
        continue

    info = canal.data[0]
    print(f"[{info['id']}] {info['nome_canal']}")
    print(f"     URL atual: {info['url_canal']}")

    # Buscar Channel ID via Search API
    channel_id = search_channel_id(info['nome_canal'])

    if channel_id:
        # Criar nova URL
        new_url = f"https://www.youtube.com/channel/{channel_id}"
        print(f"     Channel ID: {channel_id}")
        print(f"     Nova URL: {new_url}")

        # Atualizar no banco
        result = supabase.table("canais_monitorados")\
            .update({"url_canal": new_url})\
            .eq("id", canal_id)\
            .execute()

        print(f"     Status: CORRIGIDO ✓")
        success_count += 1
    else:
        print(f"     Status: FALHA - Channel ID nao encontrado")
        error_count += 1

    print()

    # Rate limit: 90 req/100s
    time.sleep(1.2)

print("=" * 80)
print(f"CORRECAO COMPLETA - Sucesso: {success_count} | Erros: {error_count}")
print("=" * 80)

"""
Testa chamada REAL à YouTube Analytics API para verificar traffic sources
"""
import os
import requests
from dotenv import load_dotenv
from supabase import create_client
from monetization_oauth_collector import get_tokens, get_proxy_credentials, refresh_access_token
from datetime import datetime, timedelta

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

print("=" * 80)
print("TESTE DIRETO - YOUTUBE ANALYTICS API (TRAFFIC SOURCES)")
print("=" * 80)

# Pegar um canal
result = supabase.table("yt_channels")\
    .select("channel_id, channel_name, proxy_name")\
    .eq("is_monetized", True)\
    .limit(1)\
    .execute()

if not result.data:
    print("Nenhum canal encontrado!")
    exit(1)

channel = result.data[0]
channel_id = channel['channel_id']
channel_name = channel['channel_name']
proxy_name = channel.get('proxy_name', 'C000.1')

print(f"\nCanal: {channel_name}")
print(f"Channel ID: {channel_id}")

# Renovar token
tokens = get_tokens(channel_id)
if not tokens:
    print("Erro: Sem tokens!")
    exit(1)

credentials = get_proxy_credentials(proxy_name)
if not credentials:
    print(f"Erro: Sem credenciais do proxy {proxy_name}!")
    exit(1)

access_token = refresh_access_token(
    tokens['refresh_token'],
    credentials['client_id'],
    credentials['client_secret']
)

if not access_token:
    print("Erro: Falha ao renovar token!")
    exit(1)

print("Token renovado com sucesso!")

# Testar API - últimos 3 dias
end_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
start_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")

print(f"\nPeriodo de teste: {start_date} ate {end_date}")

headers = {"Authorization": f"Bearer {access_token}"}

print("\n" + "=" * 80)
print("CHAMANDO YOUTUBE ANALYTICS API")
print("=" * 80)

params = {
    "ids": f"channel=={channel_id}",
    "startDate": start_date,
    "endDate": end_date,
    "metrics": "views,estimatedMinutesWatched",
    "dimensions": "insightTrafficSourceType",
    "sort": "-views"
}

print("\nParametros:")
for key, value in params.items():
    print(f"  {key}: {value}")

resp = requests.get(
    "https://youtubeanalytics.googleapis.com/v2/reports",
    params=params,
    headers=headers
)

print(f"\nStatus Code: {resp.status_code}")

if resp.status_code != 200:
    print(f"ERRO: {resp.text}")
    exit(1)

data = resp.json()

print("\n" + "=" * 80)
print("RESPOSTA DA API")
print("=" * 80)

# Mostrar column headers
if 'columnHeaders' in data:
    print("\nColumn Headers:")
    for i, header in enumerate(data['columnHeaders']):
        print(f"  [{i}] {header['name']} ({header['columnType']})")

# Mostrar rows
if 'rows' in data:
    rows = data['rows']
    print(f"\nTotal de rows: {len(rows)}")

    total_views = sum(int(row[1]) for row in rows)
    print(f"Total de views: {total_views:,}")

    print("\nDetalhes por source_type:")
    for row in rows:
        source_type = row[0]
        views = int(row[1])
        watch_time = int(row[2]) if len(row) > 2 else 0
        percentage = (views / total_views) * 100 if total_views > 0 else 0

        print(f"\n  {source_type}:")
        print(f"    Views: {views:,} ({percentage:.2f}%)")
        print(f"    Watch Time: {watch_time} min")
        print(f"    Raw row: {row}")
else:
    print("\nNenhum dado retornado!")

print("\n" + "=" * 80)

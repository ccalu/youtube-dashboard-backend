"""
Salva canal e tokens no Supabase
"""
import requests
import json
from datetime import datetime

# Supabase config
SUPABASE_URL = "https://prvkmzstyedepvlbppyo.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBydmttenN0eWVkZXB2bGJwcHlvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQxNDY3MTQsImV4cCI6MjA1OTcyMjcxNH0.T0aspHrF0tz1G6iVOBIO3zgvs1g5vvQcb25jhGriQGo"

# Carregar tokens
with open("C:/Users/User-OEM/Desktop/content-factory/tokens_brand_account.json") as f:
    tokens = json.load(f)

# Dados do canal
channel_id = "UCV9aMsA0swcuExud2tZSlUg"
channel_name = "Reis Perversos"
proxy_name = "C000.1"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

# 1. Salvar canal
print("[1] Salvando canal no Supabase...")
resp = requests.post(
    f"{SUPABASE_URL}/rest/v1/yt_channels",
    headers=headers,
    json={
        "channel_id": channel_id,
        "channel_name": channel_name,
        "proxy_name": proxy_name,
        "is_monetized": True
    }
)
print(f"    Status: {resp.status_code}")
if resp.status_code >= 400:
    print(f"    Erro: {resp.text}")

# 2. Salvar tokens
print("[2] Salvando tokens no Supabase...")
resp = requests.post(
    f"{SUPABASE_URL}/rest/v1/yt_oauth_tokens",
    headers=headers,
    json={
        "channel_id": channel_id,
        "access_token": tokens["access_token"],
        "refresh_token": tokens.get("refresh_token", "")
    }
)
print(f"    Status: {resp.status_code}")
if resp.status_code >= 400:
    print(f"    Erro: {resp.text}")

# 3. Buscar metricas e salvar
print("[3] Buscando metricas e salvando...")
access_token = tokens["access_token"]

resp = requests.get(
    "https://youtubeanalytics.googleapis.com/v2/reports",
    params={
        "ids": f"channel=={channel_id}",
        "startDate": "2025-12-01",
        "endDate": "2025-12-08",
        "metrics": "estimatedRevenue,views,estimatedMinutesWatched,averageViewDuration,subscribersGained,subscribersLost",
        "dimensions": "day"
    },
    headers={"Authorization": f"Bearer {access_token}"}
)

if resp.status_code == 200:
    data = resp.json()
    rows = data.get("rows", [])
    print(f"    {len(rows)} dias de dados")

    for row in rows:
        date = row[0]
        revenue = float(row[1])
        views = int(row[2])
        watch_minutes = int(row[3])
        avg_duration = float(row[4])
        subs_gained = int(row[5])
        subs_lost = int(row[6])

        # Calcular RPM
        rpm = (revenue / views * 1000) if views > 0 else 0

        metric_data = {
            "channel_id": channel_id,
            "date": date,
            "revenue": revenue,
            "views": views,
            "rpm": rpm,
            "watch_time_minutes": watch_minutes,
            "avg_view_duration": avg_duration,
            "subscribers_gained": subs_gained,
            "subscribers_lost": subs_lost
        }

        resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/yt_daily_metrics",
            headers=headers,
            json=metric_data
        )

        status_icon = "OK" if resp.status_code < 400 else "ERRO"
        print(f"    {date}: ${revenue:.2f} | {views:,} views | RPM ${rpm:.2f} [{status_icon}]")
else:
    print(f"    ERRO: {resp.status_code} - {resp.text}")

# 4. Log de coleta
print("[4] Salvando log de coleta...")
resp = requests.post(
    f"{SUPABASE_URL}/rest/v1/yt_collection_logs",
    headers=headers,
    json={
        "channel_id": channel_id,
        "status": "success",
        "message": f"Coletados {len(rows)} dias de metricas"
    }
)
print(f"    Status: {resp.status_code}")

print("\n" + "=" * 50)
print("CONCLUIDO! Dados salvos no Supabase.")
print("=" * 50)

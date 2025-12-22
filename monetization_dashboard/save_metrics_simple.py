"""
Salva metricas no Supabase (versao simplificada)
"""
import requests
import json

SUPABASE_URL = "https://prvkmzstyedepvlbppyo.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBydmttenN0eWVkZXB2bGJwcHlvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQxNDY3MTQsImV4cCI6MjA1OTcyMjcxNH0.T0aspHrF0tz1G6iVOBIO3zgvs1g5vvQcb25jhGriQGo"

# Carregar tokens
with open("C:/Users/User-OEM/Desktop/content-factory/tokens_brand_account.json") as f:
    tokens = json.load(f)

channel_id = "UCV9aMsA0swcuExud2tZSlUg"
access_token = tokens["access_token"]

headers_supabase = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

# Buscar metricas
print("[1] Buscando metricas da API do YouTube...")
resp = requests.get(
    "https://youtubeanalytics.googleapis.com/v2/reports",
    params={
        "ids": f"channel=={channel_id}",
        "startDate": "2025-11-01",
        "endDate": "2025-12-08",
        "metrics": "estimatedRevenue,views",
        "dimensions": "day"
    },
    headers={"Authorization": f"Bearer {access_token}"}
)

if resp.status_code != 200:
    print(f"ERRO: {resp.text}")
    exit(1)

data = resp.json()
rows = data.get("rows", [])
print(f"    {len(rows)} dias de dados")

# Salvar cada dia (usando apenas colunas basicas)
print("\n[2] Salvando metricas no Supabase...")
success = 0
errors = 0

for row in rows:
    date = row[0]
    revenue = float(row[1])
    views = int(row[2])
    rpm = (revenue / views * 1000) if views > 0 else 0

    # Apenas campos basicos
    metric_data = {
        "channel_id": channel_id,
        "date": date,
        "revenue": revenue,
        "views": views,
        "rpm": rpm
    }

    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/yt_daily_metrics",
        headers=headers_supabase,
        json=metric_data
    )

    if resp.status_code < 400:
        success += 1
        print(f"    {date}: ${revenue:.2f} | {views:,} views [OK]")
    else:
        errors += 1
        print(f"    {date}: ERRO - {resp.text[:100]}")

print(f"\n[3] Resultado: {success} salvos, {errors} erros")

# Verificar dados salvos
print("\n[4] Verificando dados no Supabase...")
resp = requests.get(
    f"{SUPABASE_URL}/rest/v1/yt_daily_metrics",
    params={"channel_id": f"eq.{channel_id}", "order": "date.desc", "limit": "5"},
    headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
)

if resp.status_code == 200:
    saved = resp.json()
    print(f"    Ultimos {len(saved)} registros:")
    for m in saved:
        print(f"    {m['date']}: ${m['revenue']:.2f} | {m['views']:,} views")
else:
    print(f"    Erro ao verificar: {resp.text}")

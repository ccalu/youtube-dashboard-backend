"""
Debug - ver erro das metricas
"""
import requests
import json

SUPABASE_URL = "https://prvkmzstyedepvlbppyo.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBydmttenN0eWVkZXB2bGJwcHlvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQxNDY3MTQsImV4cCI6MjA1OTcyMjcxNH0.T0aspHrF0tz1G6iVOBIO3zgvs1g5vvQcb25jhGriQGo"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

# Tentar inserir uma metrica de teste
metric_data = {
    "channel_id": "UCV9aMsA0swcuExud2tZSlUg",
    "date": "2025-12-01",
    "revenue": 15.86,
    "views": 16449,
    "rpm": 0.96,
    "watch_time_minutes": 1000,
    "avg_view_duration": 60.5,
    "subscribers_gained": 10,
    "subscribers_lost": 2
}

print("Tentando inserir metrica de teste...")
print(f"Dados: {json.dumps(metric_data, indent=2)}")

resp = requests.post(
    f"{SUPABASE_URL}/rest/v1/yt_daily_metrics",
    headers=headers,
    json=metric_data
)

print(f"\nStatus: {resp.status_code}")
print(f"Resposta: {resp.text}")

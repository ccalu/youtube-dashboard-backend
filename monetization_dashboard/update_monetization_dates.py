"""
Atualiza data de monetizacao de cada canal no Supabase
"""
import requests

SUPABASE_URL = "https://prvkmzstyedepvlbppyo.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBydmttenN0eWVkZXB2bGJwcHlvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQxNDY3MTQsImV4cCI6MjA1OTcyMjcxNH0.T0aspHrF0tz1G6iVOBIO3zgvs1g5vvQcb25jhGriQGo"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# Buscar canais
resp = requests.get(f"{SUPABASE_URL}/rest/v1/yt_channels", headers=headers)
channels = resp.json()

print("Atualizando datas de monetizacao...")

for channel in channels:
    channel_id = channel["channel_id"]
    channel_name = channel["channel_name"]

    # Buscar primeiro dia com receita > 0
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/yt_daily_metrics",
        params={
            "channel_id": f"eq.{channel_id}",
            "revenue": "gt.0",
            "order": "date.asc",
            "limit": "1"
        },
        headers=headers
    )

    data = resp.json()

    if data:
        first_date = data[0]["date"]

        # Atualizar canal
        resp = requests.patch(
            f"{SUPABASE_URL}/rest/v1/yt_channels",
            params={"channel_id": f"eq.{channel_id}"},
            headers=headers,
            json={"monetization_start_date": first_date}
        )

        print(f"  {channel_name}: {first_date} [OK]")
    else:
        print(f"  {channel_name}: sem receita ainda")

print("\nConcluido!")

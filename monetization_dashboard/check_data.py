"""
Verifica dados no Supabase
"""
import requests

SUPABASE_URL = "https://prvkmzstyedepvlbppyo.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBydmttenN0eWVkZXB2bGJwcHlvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQxNDY3MTQsImV4cCI6MjA1OTcyMjcxNH0.T0aspHrF0tz1G6iVOBIO3zgvs1g5vvQcb25jhGriQGo"
headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}

print("=" * 60)
print("DADOS NO SUPABASE")
print("=" * 60)

# Canais
resp = requests.get(f"{SUPABASE_URL}/rest/v1/yt_channels", headers=headers)
channels = resp.json()
print(f"\n[1] CANAIS: {len(channels)}")
for c in channels:
    print(f"    - {c['channel_name']} ({c['channel_id'][:15]}...)")
    print(f"      Subs: {c.get('total_subscribers', 'N/A')} | Videos: {c.get('total_videos', 'N/A')}")

# Metricas diarias
resp = requests.get(
    f"{SUPABASE_URL}/rest/v1/yt_daily_metrics",
    params={"order": "date.desc", "limit": "5"},
    headers=headers
)
metrics = resp.json()
print(f"\n[2] METRICAS DIARIAS (ultimos 5 dias):")
for m in metrics:
    print(f"    {m['date']}: ${m['revenue']:.2f} | {m['views']:,} views | +{m.get('subscribers_gained', 0)} subs")

# Total de registros
resp = requests.get(
    f"{SUPABASE_URL}/rest/v1/yt_daily_metrics",
    params={"select": "count"},
    headers={**headers, "Prefer": "count=exact"}
)
print(f"\n    Total de registros: {resp.headers.get('content-range', 'N/A')}")

# Videos
resp = requests.get(
    f"{SUPABASE_URL}/rest/v1/yt_video_metrics",
    params={"order": "views.desc", "limit": "5"},
    headers=headers
)
videos = resp.json()
print(f"\n[3] TOP 5 VIDEOS:")
for v in videos:
    title = v.get('title', '')[:40]
    print(f"    {v['views']:,} views | ${v['revenue']:.2f} | {title}...")

# Country metrics
resp = requests.get(
    f"{SUPABASE_URL}/rest/v1/yt_country_metrics",
    params={"order": "views.desc", "limit": "5"},
    headers=headers
)
countries = resp.json()
print(f"\n[4] TOP PAISES:")
for c in countries:
    print(f"    {c['country_code']}: {c['views']:,} views | ${c['revenue']:.2f}")

print("\n" + "=" * 60)

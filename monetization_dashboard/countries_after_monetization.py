"""
Paises - apenas periodo monetizado (01/12 - 08/12)
"""
import requests
import json

with open("C:/Users/User-OEM/Desktop/content-factory/tokens_brand_account.json") as f:
    tokens = json.load(f)

access_token = tokens["access_token"]
channel_id = "UCV9aMsA0swcuExud2tZSlUg"
headers = {"Authorization": f"Bearer {access_token}"}

print("=" * 60)
print("TOP PAISES - PERIODO MONETIZADO (01/12 - 08/12)")
print("=" * 60)

resp = requests.get(
    "https://youtubeanalytics.googleapis.com/v2/reports",
    params={
        "ids": f"channel=={channel_id}",
        "startDate": "2025-12-01",
        "endDate": "2025-12-08",
        "metrics": "views,estimatedRevenue",
        "dimensions": "country",
        "sort": "-estimatedRevenue",
        "maxResults": "15"
    },
    headers=headers
)

if resp.status_code == 200:
    data = resp.json()
    rows = data.get("rows", [])

    total_views = sum(int(r[1]) for r in rows)
    total_revenue = sum(float(r[2]) for r in rows)

    print(f"\n{'Pais':<10} {'Views':>12} {'Receita':>12} {'RPM':>10} {'% Views':>10}")
    print("-" * 60)

    for row in rows:
        country = row[0]
        views = int(row[1])
        revenue = float(row[2])
        rpm = (revenue / views * 1000) if views > 0 else 0
        pct = (views / total_views * 100) if total_views > 0 else 0

        print(f"{country:<10} {views:>12,} ${revenue:>11.2f} ${rpm:>9.2f} {pct:>9.1f}%")

    print("-" * 60)
    print(f"{'TOTAL':<10} {total_views:>12,} ${total_revenue:>11.2f}")

    avg_rpm = (total_revenue / total_views * 1000) if total_views > 0 else 0
    print(f"\nRPM Medio Global: ${avg_rpm:.2f}")
else:
    print(f"ERRO: {resp.status_code} - {resp.text}")

"""
Explora TODOS os dados disponiveis da YouTube Analytics API
"""
import requests
import json

# Carregar tokens
with open("C:/Users/User-OEM/Desktop/content-factory/tokens_brand_account.json") as f:
    tokens = json.load(f)

access_token = tokens["access_token"]
channel_id = "UCV9aMsA0swcuExud2tZSlUg"
headers = {"Authorization": f"Bearer {access_token}"}

print("=" * 70)
print("EXPLORANDO DADOS DO CANAL REIS PERVERSOS")
print("=" * 70)

# 1. METRICAS DIARIAS COMPLETAS
print("\n[1] METRICAS DIARIAS (Nov-Dez 2025)")
print("-" * 70)
resp = requests.get(
    "https://youtubeanalytics.googleapis.com/v2/reports",
    params={
        "ids": f"channel=={channel_id}",
        "startDate": "2025-11-01",
        "endDate": "2025-12-08",
        "metrics": "estimatedRevenue,views,likes,comments,shares,subscribersGained,subscribersLost,estimatedMinutesWatched,averageViewDuration",
        "dimensions": "day",
        "sort": "day"
    },
    headers=headers
)

if resp.status_code == 200:
    data = resp.json()
    rows = data.get("rows", [])

    print(f"{'Data':<12} {'Receita':>10} {'Views':>10} {'Likes':>7} {'Coments':>7} {'Shares':>7} {'+Subs':>7} {'-Subs':>7} {'WatchMin':>10}")
    print("-" * 90)

    total_revenue = 0
    total_views = 0
    total_subs_gained = 0
    total_subs_lost = 0

    for row in rows:
        date = row[0]
        revenue = float(row[1])
        views = int(row[2])
        likes = int(row[3])
        comments = int(row[4])
        shares = int(row[5])
        subs_gained = int(row[6])
        subs_lost = int(row[7])
        watch_min = int(row[8])

        total_revenue += revenue
        total_views += views
        total_subs_gained += subs_gained
        total_subs_lost += subs_lost

        print(f"{date:<12} ${revenue:>9.2f} {views:>10,} {likes:>7,} {comments:>7,} {shares:>7,} {subs_gained:>7,} {subs_lost:>7,} {watch_min:>10,}")

    print("-" * 90)
    print(f"{'TOTAL':<12} ${total_revenue:>9.2f} {total_views:>10,} {' ':>7} {' ':>7} {' ':>7} {total_subs_gained:>7,} {total_subs_lost:>7,}")
    print(f"\nCrescimento liquido de inscritos: {total_subs_gained - total_subs_lost:,}")
else:
    print(f"ERRO: {resp.status_code} - {resp.text[:200]}")

# 2. DADOS POR VIDEO
print("\n\n[2] PERFORMANCE POR VIDEO (Top 20)")
print("-" * 70)
resp = requests.get(
    "https://youtubeanalytics.googleapis.com/v2/reports",
    params={
        "ids": f"channel=={channel_id}",
        "startDate": "2025-11-01",
        "endDate": "2025-12-08",
        "metrics": "estimatedRevenue,views,likes,comments,averageViewDuration,subscribersGained",
        "dimensions": "video",
        "sort": "-views",
        "maxResults": "20"
    },
    headers=headers
)

if resp.status_code == 200:
    data = resp.json()
    rows = data.get("rows", [])

    # Buscar titulos dos videos
    video_ids = [row[0] for row in rows]

    print(f"\n{'Video ID':<15} {'Receita':>10} {'Views':>10} {'Likes':>7} {'Coments':>7} {'AvgDur':>7} {'+Subs':>7}")
    print("-" * 70)

    for row in rows:
        video_id = row[0]
        revenue = float(row[1])
        views = int(row[2])
        likes = int(row[3])
        comments = int(row[4])
        avg_dur = float(row[5])
        subs = int(row[6])

        print(f"{video_id:<15} ${revenue:>9.2f} {views:>10,} {likes:>7,} {comments:>7,} {avg_dur:>7.0f}s {subs:>7,}")

    # Buscar titulos via YouTube Data API
    print("\n\n[3] TITULOS DOS VIDEOS")
    print("-" * 70)

    if video_ids:
        resp2 = requests.get(
            "https://www.googleapis.com/youtube/v3/videos",
            params={
                "part": "snippet,statistics",
                "id": ",".join(video_ids[:10])
            },
            headers=headers
        )

        if resp2.status_code == 200:
            videos = resp2.json().get("items", [])
            for v in videos:
                title = v["snippet"]["title"][:50]
                vid = v["id"]
                views = v["statistics"].get("viewCount", "N/A")
                print(f"{vid}: {title}...")
                print(f"   Views totais: {int(views):,}")
                print()
        else:
            print(f"Erro ao buscar titulos: {resp2.status_code}")
else:
    print(f"ERRO: {resp.status_code} - {resp.text[:200]}")

# 3. FONTES DE TRAFEGO
print("\n\n[4] FONTES DE TRAFEGO")
print("-" * 70)
resp = requests.get(
    "https://youtubeanalytics.googleapis.com/v2/reports",
    params={
        "ids": f"channel=={channel_id}",
        "startDate": "2025-11-01",
        "endDate": "2025-12-08",
        "metrics": "views,estimatedMinutesWatched",
        "dimensions": "insightTrafficSourceType",
        "sort": "-views"
    },
    headers=headers
)

if resp.status_code == 200:
    data = resp.json()
    rows = data.get("rows", [])

    print(f"{'Fonte':<30} {'Views':>12} {'Watch Minutes':>15}")
    print("-" * 60)
    for row in rows:
        source = row[0]
        views = int(row[1])
        watch_min = int(row[2])
        print(f"{source:<30} {views:>12,} {watch_min:>15,}")
else:
    print(f"ERRO: {resp.status_code}")

# 4. DISPOSITIVOS
print("\n\n[5] DISPOSITIVOS")
print("-" * 70)
resp = requests.get(
    "https://youtubeanalytics.googleapis.com/v2/reports",
    params={
        "ids": f"channel=={channel_id}",
        "startDate": "2025-11-01",
        "endDate": "2025-12-08",
        "metrics": "views,estimatedMinutesWatched",
        "dimensions": "deviceType",
        "sort": "-views"
    },
    headers=headers
)

if resp.status_code == 200:
    data = resp.json()
    rows = data.get("rows", [])

    print(f"{'Dispositivo':<20} {'Views':>12} {'Watch Minutes':>15}")
    print("-" * 50)
    for row in rows:
        device = row[0]
        views = int(row[1])
        watch_min = int(row[2])
        print(f"{device:<20} {views:>12,} {watch_min:>15,}")
else:
    print(f"ERRO: {resp.status_code}")

# 5. PAISES
print("\n\n[6] TOP 10 PAISES")
print("-" * 70)
resp = requests.get(
    "https://youtubeanalytics.googleapis.com/v2/reports",
    params={
        "ids": f"channel=={channel_id}",
        "startDate": "2025-11-01",
        "endDate": "2025-12-08",
        "metrics": "views,estimatedRevenue",
        "dimensions": "country",
        "sort": "-views",
        "maxResults": "10"
    },
    headers=headers
)

if resp.status_code == 200:
    data = resp.json()
    rows = data.get("rows", [])

    print(f"{'Pais':<10} {'Views':>12} {'Receita':>12}")
    print("-" * 40)
    for row in rows:
        country = row[0]
        views = int(row[1])
        revenue = float(row[2])
        print(f"{country:<10} {views:>12,} ${revenue:>11.2f}")
else:
    print(f"ERRO: {resp.status_code}")

print("\n" + "=" * 70)
print("FIM DA EXPLORACAO")
print("=" * 70)

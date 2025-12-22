"""
Investiga possível bug em Traffic Sources
"""
import os
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime, timedelta

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

print("=" * 80)
print("INVESTIGACAO DE BUG - TRAFFIC SOURCES")
print("=" * 80)

# Pegar um canal
result = supabase.table("yt_channels")\
    .select("channel_id, channel_name, total_subscribers")\
    .eq("is_monetized", True)\
    .limit(1)\
    .execute()

if not result.data:
    print("Nenhum canal encontrado!")
    exit(1)

channel = result.data[0]
channel_id = channel['channel_id']
channel_name = channel['channel_name']
subscribers = channel.get('total_subscribers', 0)

print(f"\nCanal: {channel_name}")
print(f"Channel ID: {channel_id}")
print(f"Inscritos: {subscribers:,}")

# Buscar dados dos últimos 30 dias
end_date = datetime.now().date()
start_date = end_date - timedelta(days=30)

print(f"\nPeriodo: {start_date} ate {end_date}")

# 1. Consultar dados brutos
print("\n" + "=" * 80)
print("[1] DADOS BRUTOS DO BANCO")
print("=" * 80)

result = supabase.table("yt_traffic_summary")\
    .select("*")\
    .eq("channel_id", channel_id)\
    .gte("date", str(start_date))\
    .lte("date", str(end_date))\
    .execute()

if not result.data:
    print("Nenhum dado encontrado!")
else:
    print(f"\nTotal de registros: {len(result.data)}")

    # Agrupar por source_type
    sources = {}
    for item in result.data:
        src = item['source_type']
        sources[src] = sources.get(src, 0) + item['views']

    total_views = sum(sources.values())

    print(f"\nTotal de views (traffic): {total_views:,}")
    print(f"\nDistribuicao por source_type:")

    for src, views in sorted(sources.items(), key=lambda x: x[1], reverse=True):
        percentage = (views / total_views) * 100 if total_views > 0 else 0
        print(f"  {src}: {views:,} views ({percentage:.2f}%)")

# 2. Comparar com total de views do canal
print("\n" + "=" * 80)
print("[2] VALIDACAO - VIEWS vs INSCRITOS")
print("=" * 80)

result = supabase.table("yt_daily_metrics")\
    .select("views")\
    .eq("channel_id", channel_id)\
    .gte("date", str(start_date))\
    .lte("date", str(end_date))\
    .execute()

if result.data:
    total_daily_views = sum(item['views'] or 0 for item in result.data)
    print(f"\nTotal de views (daily metrics): {total_daily_views:,}")
    print(f"Total de views (traffic sources): {total_views:,}")

    diff = abs(total_daily_views - total_views)
    if diff > 1000:
        print(f"  [AVISO] Diferenca de {diff:,} views!")
    else:
        print(f"  [OK] Diferenca aceitavel: {diff:,} views")

# 3. Calcular se faz sentido
subscriber_views = sources.get('SUBSCRIBER', 0)
if subscribers > 0 and subscriber_views > 0:
    views_per_subscriber = subscriber_views / subscribers
    print(f"\nAnalise de SUBSCRIBER:")
    print(f"  Inscritos: {subscribers:,}")
    print(f"  Views de inscritos: {subscriber_views:,}")
    print(f"  Views por inscrito: {views_per_subscriber:.2f}")

    if views_per_subscriber > 10:
        print(f"  [SUSPEITO] Cada inscrito assistiu {views_per_subscriber:.0f} videos?!")
        print(f"  [CONCLUSAO] Provavelmente ha um BUG!")
    elif views_per_subscriber > 3:
        print(f"  [IMPROVAVEL] Muitas views por inscrito")
    else:
        print(f"  [OK] Razoavel")

# 4. Mostrar amostra de registros brutos
print("\n" + "=" * 80)
print("[3] AMOSTRA DE REGISTROS BRUTOS (ultimos 5)")
print("=" * 80)

result = supabase.table("yt_traffic_summary")\
    .select("*")\
    .eq("channel_id", channel_id)\
    .gte("date", str(start_date))\
    .lte("date", str(end_date))\
    .order("date", desc=True)\
    .limit(5)\
    .execute()

if result.data:
    for item in result.data:
        print(f"\nData: {item['date']}")
        print(f"  Source: {item['source_type']}")
        print(f"  Views: {item['views']:,}")

print("\n" + "=" * 80)

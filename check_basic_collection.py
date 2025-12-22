"""
Verifica coleta básica (revenue/views/RPM) em yt_daily_metrics
"""
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

print("=" * 80)
print("VERIFICACAO COLETA BASICA - yt_daily_metrics")
print("=" * 80)

# Buscar últimos 3 dias de dados
end_date = datetime.now().date()
start_date = end_date - timedelta(days=3)

print(f"\nPeriodo: {start_date} a {end_date}\n")

# Buscar canais monetizados
channels_result = supabase.table("yt_channels")\
    .select("channel_id, channel_name")\
    .eq("is_monetized", True)\
    .execute()

channels = {c['channel_id']: c['channel_name'] for c in channels_result.data}

print(f"Canais monetizados: {len(channels)}\n")
print("-" * 80)

# Buscar dados por canal
for channel_id, channel_name in channels.items():
    print(f"\n{channel_name}:")

    result = supabase.table("yt_daily_metrics")\
        .select("date, revenue, views, rpm")\
        .eq("channel_id", channel_id)\
        .gte("date", str(start_date))\
        .lte("date", str(end_date))\
        .order("date", desc=True)\
        .execute()

    if not result.data:
        print("  [ATENCAO] Sem dados nos ultimos 3 dias")
        continue

    print(f"  Registros encontrados: {len(result.data)}")

    for row in result.data:
        date = row['date']
        revenue = row.get('revenue', 0) or 0
        views = row.get('views', 0) or 0
        rpm = row.get('rpm', 0) or 0

        print(f"    {date}: ${revenue:.2f} | {views:,} views | RPM ${rpm:.2f}")

# Resumo geral
print("\n" + "=" * 80)
print("RESUMO GERAL")
print("=" * 80)

result = supabase.table("yt_daily_metrics")\
    .select("date, channel_id")\
    .gte("date", str(start_date))\
    .execute()

total_records = len(result.data)
dates_with_data = set(r['date'] for r in result.data)

print(f"\nTotal de registros (ultimos 3 dias): {total_records}")
print(f"Datas com dados: {sorted(dates_with_data)}")
print(f"Canais com dados recentes: {len(set(r['channel_id'] for r in result.data))}/{len(channels)}")

# Verificar última coleta
result = supabase.table("yt_daily_metrics")\
    .select("date")\
    .order("date", desc=True)\
    .limit(1)\
    .execute()

if result.data:
    last_date = result.data[0]['date']
    print(f"\nUltima data coletada: {last_date}")

    days_ago = (end_date - datetime.fromisoformat(last_date).date()).days
    if days_ago == 0:
        print("  [OK] Dados atualizados hoje!")
    elif days_ago == 1:
        print("  [OK] Dados de ontem")
    else:
        print(f"  [ATENCAO] Ultima coleta foi ha {days_ago} dias")

print("\n" + "=" * 80)

"""
Verifica se há dados de analytics avançado no banco
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
print("VERIFICACAO DE DADOS - ANALYTICS AVANCADO")
print("=" * 80)

# Pegar um canal monetizado
result = supabase.table("yt_channels")\
    .select("channel_id, channel_name")\
    .eq("is_monetized", True)\
    .limit(1)\
    .execute()

if not result.data:
    print("Nenhum canal encontrado!")
    exit(1)

channel = result.data[0]
channel_id = channel['channel_id']
channel_name = channel['channel_name']

print(f"\nCanal: {channel_name}")
print(f"Channel ID: {channel_id}")

# Verificar dados nas 5 tabelas
tables = [
    ('yt_traffic_summary', 'Traffic Sources'),
    ('yt_search_analytics', 'Search Terms'),
    ('yt_suggested_sources', 'Suggested Videos'),
    ('yt_demographics', 'Demographics'),
    ('yt_device_metrics', 'Device Metrics')
]

print("\n" + "-" * 80)

for table_name, description in tables:
    result = supabase.table(table_name)\
        .select("*", count="exact")\
        .eq("channel_id", channel_id)\
        .execute()

    count = result.count if hasattr(result, 'count') else len(result.data)

    print(f"\n{description} ({table_name}):")
    print(f"  Total de registros: {count}")

    if count > 0:
        # Mostrar datas disponíveis
        dates_result = supabase.table(table_name)\
            .select("date")\
            .eq("channel_id", channel_id)\
            .order("date", desc=False)\
            .execute()

        if dates_result.data:
            dates = sorted(set(item['date'] for item in dates_result.data))
            print(f"  Primeira data: {dates[0]}")
            print(f"  Ultima data: {dates[-1]}")
            print(f"  Dias com dados: {len(dates)}")

            # Mostrar amostra dos últimos 30 dias
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)

            recent_result = supabase.table(table_name)\
                .select("*", count="exact")\
                .eq("channel_id", channel_id)\
                .gte("date", str(start_date))\
                .lte("date", str(end_date))\
                .execute()

            recent_count = recent_result.count if hasattr(recent_result, 'count') else len(recent_result.data)
            print(f"  Registros ultimos 30 dias: {recent_count}")

print("\n" + "=" * 80)

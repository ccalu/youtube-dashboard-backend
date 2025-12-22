"""
Script para monitorar o progresso da coleta histórica em tempo real
"""
import os
import time
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

# Carregar variáveis de ambiente
load_dotenv()

# Configurar Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def monitor_progress():
    """Monitora o progresso da coleta em tempo real"""

    print("=" * 70)
    print("MONITORANDO COLETA HISTORICA - ANALYTICS AVANCADO")
    print("=" * 70)

    tables = [
        'yt_traffic_summary',
        'yt_search_analytics',
        'yt_suggested_sources',
        'yt_demographics',
        'yt_device_metrics'
    ]

    # Dados iniciais
    initial_counts = {}
    for table in tables:
        result = supabase.table(table).select("*", count="exact").execute()
        initial_counts[table] = result.count if hasattr(result, 'count') else len(result.data)

    print("\nContagem inicial:")
    for table, count in initial_counts.items():
        print(f"  {table}: {count} registros")

    print("\n" + "-" * 70)
    print("Monitorando progresso (Ctrl+C para sair)...")
    print("-" * 70)

    try:
        while True:
            time.sleep(10)  # Aguardar 10 segundos

            # Verificar progresso
            current_time = datetime.now().strftime('%H:%M:%S')
            print(f"\n[{current_time}] Verificando...")

            changes = False
            for table in tables:
                result = supabase.table(table).select("*", count="exact").execute()
                current_count = result.count if hasattr(result, 'count') else len(result.data)

                if current_count > initial_counts[table]:
                    diff = current_count - initial_counts[table]
                    print(f"  {table}: {current_count} (+{diff})")
                    changes = True
                    initial_counts[table] = current_count

            if not changes:
                print("  Sem mudancas...")

            # Verificar última data coletada
            traffic_result = supabase.table('yt_traffic_summary')\
                .select("date")\
                .order("date", desc=True)\
                .limit(1)\
                .execute()

            if traffic_result.data:
                latest_date = traffic_result.data[0]['date']
                print(f"  Ultima data: {latest_date}")

                # Verificar quantos canais já foram processados para essa data
                count_result = supabase.table('yt_traffic_summary')\
                    .select("channel_id")\
                    .eq("date", latest_date)\
                    .execute()

                unique_channels = set()
                if count_result.data:
                    for record in count_result.data:
                        unique_channels.add(record['channel_id'])

                print(f"  Canais processados para {latest_date}: {len(unique_channels)}/7")

    except KeyboardInterrupt:
        print("\n\nMonitoramento interrompido!")

        # Estatísticas finais
        print("\n" + "=" * 70)
        print("ESTATISTICAS FINAIS")
        print("=" * 70)

        for table in tables:
            result = supabase.table(table).select("*", count="exact").execute()
            final_count = result.count if hasattr(result, 'count') else len(result.data)
            print(f"  {table}: {final_count} registros")

        # Verificar período total
        min_date_result = supabase.table('yt_traffic_summary')\
            .select("date")\
            .order("date")\
            .limit(1)\
            .execute()

        max_date_result = supabase.table('yt_traffic_summary')\
            .select("date")\
            .order("date", desc=True)\
            .limit(1)\
            .execute()

        if min_date_result.data and max_date_result.data:
            print(f"\nPeriodo coletado: {min_date_result.data[0]['date']} ate {max_date_result.data[0]['date']}")

if __name__ == "__main__":
    monitor_progress()
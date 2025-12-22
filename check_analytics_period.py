"""
Script para verificar o período de dados disponível nas tabelas de analytics avançado
"""
import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

# Carregar variáveis de ambiente
load_dotenv()

# Configurar Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def check_analytics_period():
    """Verifica o período de dados em cada tabela de analytics"""

    print("=" * 70)
    print("VERIFICAÇÃO DE DADOS - ANALYTICS AVANÇADO")
    print("=" * 70)

    tables = [
        'yt_traffic_summary',
        'yt_search_analytics',
        'yt_suggested_sources',
        'yt_demographics',
        'yt_device_metrics'
    ]

    for table in tables:
        print(f"\n[{table.upper()}]")
        print("-" * 50)

        min_date_result = None
        max_date_result = None
        min_dt = None
        max_dt = None
        min_date = None
        max_date = None

        try:
            # Buscar data mínima
            min_date_result = supabase.table(table)\
                .select("date")\
                .order("date")\
                .limit(1)\
                .execute()

            # Buscar data máxima
            max_date_result = supabase.table(table)\
                .select("date")\
                .order("date", desc=True)\
                .limit(1)\
                .execute()

            # Contar total de registros
            all_records = supabase.table(table)\
                .select("*", count="exact")\
                .execute()

            total_count = all_records.count if hasattr(all_records, 'count') else len(all_records.data)

            # Contar canais únicos
            unique_channels = supabase.table(table)\
                .select("channel_id")\
                .execute()

            unique_channel_ids = set()
            if unique_channels.data:
                for record in unique_channels.data:
                    unique_channel_ids.add(record['channel_id'])

            # Exibir resultados
            if min_date_result.data and max_date_result.data:
                min_date = min_date_result.data[0]['date']
                max_date = max_date_result.data[0]['date']

                # Calcular período
                min_dt = datetime.strptime(min_date, '%Y-%m-%d')
                max_dt = datetime.strptime(max_date, '%Y-%m-%d')
                days_span = (max_dt - min_dt).days + 1

                print(f"  Periodo: {min_date} ate {max_date} ({days_span} dias)")
                print(f"  Total de registros: {total_count:,}")
                print(f"  Canais unicos: {len(unique_channel_ids)}")

                # Calcular média de registros por dia
                if days_span > 0:
                    avg_per_day = total_count / days_span
                    print(f"  Media por dia: {avg_per_day:.1f} registros")
            else:
                print(f"  [VAZIO] Tabela vazia")

        except Exception as e:
            print(f"  [ERRO] {str(e)}")

    # Análise de cobertura temporal
    print("\n" + "=" * 70)
    print("ANÁLISE DE COBERTURA TEMPORAL")
    print("=" * 70)

    # Verificar distribuição por data (últimos 10 dias)
    print("\nDistribuicao dos ultimos 10 dias:")

    # Pegar traffic_summary como referência (tabela principal)
    dates_result = supabase.table('yt_traffic_summary')\
        .select("date")\
        .order("date", desc=True)\
        .limit(100)\
        .execute()

    if dates_result.data:
        date_counts = {}
        for record in dates_result.data:
            date = record['date']
            if date not in date_counts:
                date_counts[date] = 0
            date_counts[date] += 1

        # Ordenar e mostrar últimas 10 datas
        sorted_dates = sorted(date_counts.items(), reverse=True)[:10]
        for date, count in sorted_dates:
            bar = "#" * min(count, 50)
            print(f"  {date}: {bar} ({count})")

    # Verificar gaps de dados
    print("\nVerificando gaps de dados...")

    if min_date_result.data and max_date_result.data:
        # Buscar todas as datas únicas
        all_dates_result = supabase.table('yt_traffic_summary')\
            .select("date")\
            .execute()

        if all_dates_result.data:
            unique_dates = set()
            for record in all_dates_result.data:
                unique_dates.add(record['date'])

            # Verificar continuidade
            current_date = min_dt
            gaps = []

            while current_date <= max_dt:
                date_str = current_date.strftime('%Y-%m-%d')
                if date_str not in unique_dates:
                    gaps.append(date_str)
                current_date = current_date + timedelta(days=1)

            if gaps:
                print(f"  [AVISO] Encontrados {len(gaps)} dias sem dados:")
                for gap_date in gaps[:10]:  # Mostrar apenas primeiros 10
                    print(f"    - {gap_date}")
                if len(gaps) > 10:
                    print(f"    ... e mais {len(gaps) - 10} dias")
            else:
                print(f"  [OK] Sem gaps! Dados continuos de {min_date} ate {max_date}")

if __name__ == "__main__":
    from datetime import timedelta
    check_analytics_period()

    print("\n" + "=" * 70)
    print("RECOMENDACAO")
    print("=" * 70)

    # Buscar data de criação dos canais
    channels_result = supabase.table("yt_channels")\
        .select("channel_name, created_at")\
        .eq("is_monetized", True)\
        .order("created_at", asc=True)\
        .limit(1)\
        .execute()

    if channels_result.data:
        oldest_channel = channels_result.data[0]
        created_date = oldest_channel['created_at'].split('T')[0]

        print(f"\n[INFO] Canal mais antigo criado em: {created_date}")
        print(f"[DICA] Recomendacao: Coletar dados desde {created_date}")

        # Calcular dias faltantes
        today = datetime.now().date()
        created_dt = datetime.strptime(created_date, '%Y-%m-%d').date()
        total_days = (today - created_dt).days

        print(f"[DADOS] Total de dias possiveis: {total_days}")
        print(f"\n[EXECUTAR] Para coletar historico completo:")
        print(f"   python collect_historical_analytics.py {total_days}")

    print("\n" + "=" * 70)
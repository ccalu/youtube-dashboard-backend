from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print('='*80)
print('DIAGNÓSTICO: Dados de Monetização')
print('='*80)

# 1. Total de registros
result = sb.table('yt_daily_metrics').select('*', count='exact').execute()
print(f'\n1. TOTAL DE REGISTROS: {result.count}')

# 2. Dados reais vs estimados
real = sb.table('yt_daily_metrics').select('*', count='exact').eq('is_estimate', False).execute()
estimate = sb.table('yt_daily_metrics').select('*', count='exact').eq('is_estimate', True).execute()
print(f'\n2. TIPO DE DADOS:')
print(f'   Reais (is_estimate=False): {real.count}')
print(f'   Estimados (is_estimate=True): {estimate.count}')

# 3. Canais únicos com dados
all_data = sb.table('yt_daily_metrics').select('channel_id, is_estimate').execute()
real_channels = set([r['channel_id'] for r in all_data.data if not r['is_estimate']])
estimate_channels = set([r['channel_id'] for r in all_data.data if r['is_estimate']])
print(f'\n3. CANAIS ÚNICOS COM DADOS:')
print(f'   Com dados reais: {len(real_channels)}')
print(f'   Com dados estimados: {len(estimate_channels)}')

# 4. Range de datas
dates = sb.table('yt_daily_metrics').select('date').order('date').execute()
if dates.data:
    print(f'\n4. PERÍODO DOS DADOS:')
    print(f'   Data mais antiga: {dates.data[0]["date"]}')
    print(f'   Data mais recente: {dates.data[-1]["date"]}')

# 5. Canais monetizados na tabela yt_channels
monetized = sb.table('yt_channels').select('channel_id, channel_name').eq('is_monetized', True).execute()
print(f'\n5. CANAIS MARCADOS COMO MONETIZADOS:')
print(f'   Total: {len(monetized.data)}')
if monetized.data:
    print(f'\n   Primeiros 5:')
    for ch in monetized.data[:5]:
        print(f'   - {ch["channel_name"]}')
        print(f'     ID: {ch["channel_id"]}')

# 6. Cross-check: canais monetizados COM dados
print(f'\n6. CROSS-CHECK:')
monetized_ids = set([ch['channel_id'] for ch in monetized.data])
print(f'   Canais monetizados: {len(monetized_ids)}')
print(f'   Canais com dados reais: {len(real_channels)}')
print(f'   Canais SEM dados: {len(monetized_ids - real_channels)}')

if monetized_ids - real_channels:
    print(f'\n   Canais sem dados (primeiros 5):')
    missing = list(monetized_ids - real_channels)[:5]
    for cid in missing:
        ch_info = next((ch for ch in monetized.data if ch['channel_id'] == cid), None)
        if ch_info:
            print(f'   - {ch_info["channel_name"]} ({cid[:20]}...)')

# 7. Sample de dados salvos
print(f'\n7. AMOSTRA DE DADOS REAIS:')
sample = sb.table('yt_daily_metrics').select('*').eq('is_estimate', False).limit(3).execute()
for item in sample.data:
    print(f'\n   Canal: {item["channel_id"][:20]}...')
    print(f'   Data: {item["date"]}')
    print(f'   Revenue: ${item["revenue"]:.2f}')
    print(f'   Views: {item["views"]:,}')
    print(f'   RPM: ${item["rpm"]:.2f}')

print('\n' + '='*80)

import requests
from datetime import datetime, timedelta

SUPABASE_URL = 'https://prvkmzstyedepvlbppyo.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBydmttenN0eWVkZXB2bGJwcHlvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQxNDY3MTQsImV4cCI6MjA1OTcyMjcxNH0.T0aspHrF0tz1G6iVOBIO3zgvs1g5vvQcb25jhGriQGo'

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}'
}

print('=== VERIFICANDO HISTORICO DOS 41 CANAIS ===\n')

# 1. Buscar todos os canais com tipo=nosso
response = requests.get(
    f'{SUPABASE_URL}/rest/v1/canais_monitorados',
    headers=headers,
    params={'tipo': 'eq.nosso', 'select': 'id'}
)
nossos_canais = response.json()
print(f'Total de canais tipo=nosso: {len(nossos_canais)}\n')

# 2. Buscar histórico dos últimos 2 dias
dois_dias_atras = (datetime.now() - timedelta(days=2)).date().isoformat()
print(f'Buscando historico desde: {dois_dias_atras}\n')

response = requests.get(
    f'{SUPABASE_URL}/rest/v1/dados_canais_historico',
    headers=headers,
    params={'select': 'canal_id,data_coleta', 'data_coleta': f'gte.{dois_dias_atras}'}
)

print(f'Status code: {response.status_code}')
historico = response.json()
print(f'Type: {type(historico)}')

if isinstance(historico, list):
    print(f'Registros de historico encontrados: {len(historico)}\n')
    
    # Extrair canal_ids únicos do histórico
    canal_ids_com_historico = set(h['canal_id'] for h in historico)
    print(f'Canais unicos com historico recente: {len(canal_ids_com_historico)}\n')
    
    # 3. Verificar quais dos 41 canais têm histórico
    canais_ids_nossos = set(c['id'] for c in nossos_canais)
    canais_com_dados = canais_ids_nossos.intersection(canal_ids_com_historico)
    canais_sem_dados = canais_ids_nossos - canal_ids_com_historico
    
    print(f'=== RESULTADO ===')
    print(f'Canais COM historico: {len(canais_com_dados)}')
    print(f'Canais SEM historico: {len(canais_sem_dados)}')
    
    if canais_sem_dados:
        print(f'\nIDs dos canais sem historico:')
        print(sorted(list(canais_sem_dados)))
else:
    print(f'Erro na resposta: {historico}')

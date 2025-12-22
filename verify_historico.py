import requests
from datetime import datetime, timedelta

SUPABASE_URL = 'https://prvkmzstyedepvlbppyo.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBydmttenN0eWVkZXB2bGJwcHlvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQxNDY3MTQsImV4cCI6MjA1OTcyMjcxNH0.T0aspHrF0tz1G6iVOBIO3zgvs1g5vvQcb25jhGriQGo'

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}'
}

print('=== VERIFICANDO HISTÓRICO DOS 41 CANAIS ===\n')

# 1. Buscar todos os canais com tipo=nosso
response = requests.get(
    f'{SUPABASE_URL}/rest/v1/canais_monitorados',
    headers=headers,
    params={'tipo': 'eq.nosso', 'select': 'id,nome_canal,ultima_coleta'}
)
nossos_canais = response.json()
print(f'Total de canais tipo=nosso: {len(nossos_canais)}\n')

# 2. Buscar histórico dos últimos 2 dias
dois_dias_atras = (datetime.now() - timedelta(days=2)).date().isoformat()
print(f'Buscando histórico desde: {dois_dias_atras}\n')

response = requests.get(
    f'{SUPABASE_URL}/rest/v1/dados_canais_historico',
    headers=headers,
    params={'select': 'canal_id', 'gte': f'data_coleta.{dois_dias_atras}'}
)
historico = response.json()

# Extrair canal_ids únicos do histórico
canal_ids_com_historico = set(h['canal_id'] for h in historico)
print(f'Canais com histórico recente: {len(canal_ids_com_historico)}\n')

# 3. Verificar quais dos 41 canais têm histórico
canais_com_dados = []
canais_sem_dados = []

for canal in nossos_canais:
    canal_id = canal['id']
    if canal_id in canal_ids_com_historico:
        canais_com_dados.append(canal)
    else:
        canais_sem_dados.append(canal)

print(f'=== RESULTADO ===')
print(f'Canais COM histórico: {len(canais_com_dados)}')
print(f'Canais SEM histórico: {len(canais_sem_dados)}\n')

if canais_sem_dados:
    print('Canais SEM histórico (primeiros 10):')
    for canal in canais_sem_dados[:10]:
        ultima = canal.get('ultima_coleta', 'Nunca')
        print(f'  - ID {canal["id"]} | ultima_coleta: {ultima}')

import requests
import json

SUPABASE_URL = 'https://prvkmzstyedepvlbppyo.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBydmttenN0eWVkZXB2bGJwcHlvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQxNDY3MTQsImV4cCI6MjA1OTcyMjcxNH0.T0aspHrF0tz1G6iVOBIO3zgvs1g5vvQcb25jhGriQGo'

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Prefer': 'count=exact'
}

print('=== 1. TOTAL DE CANAIS NA TABELA canais_monitorados ===')
response = requests.get(
    f'{SUPABASE_URL}/rest/v1/canais_monitorados',
    headers=headers,
    params={'select': 'id'}
)
all_canais = response.json()
print(f'Total de canais: {len(all_canais)}')

print('\n=== 2. DISTRIBUIÇÃO POR CAMPO tipo ===')
response = requests.get(
    f'{SUPABASE_URL}/rest/v1/canais_monitorados',
    headers=headers,
    params={'select': 'tipo'}
)
all_tipos = response.json()
tipos_count = {}
for canal in all_tipos:
    tipo = canal.get('tipo', 'NULL')
    tipo_str = str(tipo) if tipo else 'NULL'
    tipos_count[tipo_str] = tipos_count.get(tipo_str, 0) + 1

print('Valores encontrados no campo tipo:')
for tipo, count in sorted(tipos_count.items(), key=lambda x: x[1], reverse=True):
    print(f'  - tipo="{tipo}": {count} canais')

print('\n=== 3. CANAIS COM tipo=nosso ===')
response = requests.get(
    f'{SUPABASE_URL}/rest/v1/canais_monitorados',
    headers=headers,
    params={'tipo': 'eq.nosso', 'select': 'nome_canal,subnicho'}
)
nossos = response.json()
print(f'Total com tipo=nosso: {len(nossos)}')
if nossos:
    print('Lista completa:')
    for canal in nossos:
        print(f'  - {canal.get("nome_canal", "N/A")} | subnicho: {canal.get("subnicho", "N/A")}')

print('\n=== 4. CANAIS COM tipo diferente de nosso (ou NULL) ===')
response = requests.get(
    f'{SUPABASE_URL}/rest/v1/canais_monitorados',
    headers=headers,
    params={'select': 'nome_canal,tipo,subnicho', 'limit': '50'}
)
todos = response.json()
outros = [c for c in todos if c.get('tipo') != 'nosso']
print(f'Total com tipo != nosso: {len(outros)}')
if outros:
    print('Exemplos (primeiros 15):')
    for canal in outros[:15]:
        print(f'  - {canal.get("nome_canal", "N/A")} | tipo: {canal.get("tipo", "NULL")} | subnicho: {canal.get("subnicho", "N/A")}')

print('\n=== 5. STATUS DOS CANAIS ===')
response = requests.get(
    f'{SUPABASE_URL}/rest/v1/canais_monitorados',
    headers=headers,
    params={'select': 'status'}
)
all_status = response.json()
status_count = {}
for canal in all_status:
    status = canal.get('status', 'NULL')
    status_str = str(status) if status else 'NULL'
    status_count[status_str] = status_count.get(status_str, 0) + 1

print('Valores encontrados no campo status:')
for status, count in sorted(status_count.items(), key=lambda x: x[1], reverse=True):
    print(f'  - status="{status}": {count} canais')

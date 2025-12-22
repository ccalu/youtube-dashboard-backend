import requests

# Tentar descobrir a URL do Railway
print('=== TESTANDO ENDPOINT RAILWAY ===\n')

# URL do Railway (você precisa fornecer a URL correta)
railway_url = input('Digite a URL do Railway (ex: https://youtube-dashboard-backend-production.up.railway.app): ').strip()

if not railway_url:
    print('URL não fornecida. Saindo...')
    exit()

# Testar endpoint
response = requests.get(f'{railway_url}/api/canais-tabela')

print(f'\nStatus Code: {response.status_code}')

if response.status_code == 200:
    data = response.json()
    print(f'\nTotal de grupos: {len(data.get("grupos", []))}')
    
    total_canais = 0
    for grupo in data.get("grupos", []):
        num_canais = len(grupo.get("canais", []))
        total_canais += num_canais
        print(f'  - {grupo.get("subnicho", "N/A")}: {num_canais} canais')
    
    print(f'\nTotal de canais: {total_canais}')
else:
    print(f'\nErro: {response.text}')

"""
Testa a API de Analytics diretamente com o channel_id conhecido
"""
import requests
import json

# Ler tokens salvos
with open('C:/Users/User-OEM/Desktop/content-factory/tokens_temp.json') as f:
    tokens = json.load(f)

access_token = tokens['access_token']
refresh_token = tokens.get('refresh_token', '')

print(f'Access Token: {access_token[:50]}...')
print(f'Refresh Token: {refresh_token[:50]}...')

# ID do canal do screenshot (Reis Perversos)
channel_id = 'UCV9aMsA0swcuExud2tZSlUg'

print(f'\nTestando Analytics API para canal {channel_id}...')

resp = requests.get(
    'https://youtubeanalytics.googleapis.com/v2/reports',
    params={
        'ids': f'channel=={channel_id}',
        'startDate': '2025-11-01',
        'endDate': '2025-12-08',
        'metrics': 'estimatedRevenue,views',
        'dimensions': 'day'
    },
    headers={'Authorization': f'Bearer {access_token}'}
)

print(f'Status: {resp.status_code}')

if resp.status_code == 200:
    data = resp.json()
    rows = data.get('rows', [])
    print(f'Dias de dados: {len(rows)}')
    if rows:
        total_revenue = sum(float(r[1]) for r in rows)
        total_views = sum(int(r[2]) for r in rows)
        print(f'Receita total (Nov-Dez): ${total_revenue:.2f}')
        print(f'Views total: {total_views:,}')
        print(f'\nUltimos 5 dias:')
        for row in rows[-5:]:
            print(f'  {row[0]}: ${float(row[1]):.2f} | {int(row[2]):,} views')
else:
    print(f'Erro: {resp.text[:500]}')

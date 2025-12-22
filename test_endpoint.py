import sys
sys.path.insert(0, '/d/ContentFactory/youtube-dashboard-backend')

import asyncio
from database import SupabaseClient

async def test():
    db = SupabaseClient()
    
    print('=== TESTANDO get_canais_with_filters ===\n')
    
    canais = await db.get_canais_with_filters(
        tipo="nosso",
        limit=1000,
        offset=0
    )
    
    print(f'Total de canais retornados: {len(canais)}\n')
    
    if canais:
        print('Primeiros 5 canais:')
        for canal in canais[:5]:
            print(f'  - ID {canal["id"]}: {canal["nome_canal"]} | inscritos: {canal["inscritos"]} | diff: {canal.get("inscritos_diff", "N/A")}')

asyncio.run(test())

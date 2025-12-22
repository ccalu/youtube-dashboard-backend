import sys
import os
sys.path.insert(0, '/d/ContentFactory/youtube-dashboard-backend')

# Configurar variáveis de ambiente
os.environ['SUPABASE_URL'] = 'https://prvkmzstyedepvlbppyo.supabase.co'
os.environ['SUPABASE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBydmttenN0eWVkZXB2bGJwcHlvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQxNDY3MTQsImV4cCI6MjA1OTcyMjcxNH0.T0aspHrF0tz1G6iVOBIO3zgvs1g5vvQcb25jhGriQGo'

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
        print('Primeiros 10 canais:')
        for canal in canais[:10]:
            print(f'  - ID {canal["id"]}: inscritos={canal["inscritos"]}, diff={canal.get("inscritos_diff", "N/A")}')

asyncio.run(test())

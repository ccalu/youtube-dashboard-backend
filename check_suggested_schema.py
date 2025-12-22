"""
Verifica estrutura da tabela yt_suggested_sources
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# Buscar um registro para ver a estrutura
result = supabase.table("yt_suggested_sources")\
    .select("*")\
    .limit(1)\
    .execute()

if result.data:
    print("Estrutura da tabela yt_suggested_sources:")
    print()
    for key, value in result.data[0].items():
        print(f"  {key}: {type(value).__name__} = {value}")
else:
    print("Nenhum dado encontrado")

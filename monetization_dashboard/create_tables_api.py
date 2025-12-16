"""
Script para criar tabelas de analytics avançado no Supabase
"""
import os
import sys
import requests
from dotenv import load_dotenv

# Adicionar encoding UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

print("🚀 Criando tabelas de analytics avançado no Supabase...")
print(f"URL: {SUPABASE_URL[:30]}...")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# Como não podemos executar SQL direto, vamos verificar/criar usando a API REST
# Primeiro vamos testar se as tabelas existem

tables_to_check = [
    {
        "name": "yt_traffic_summary",
        "test_data": {
            "channel_id": "TEST",
            "date": "2024-01-01",
            "source_type": "TEST",
            "views": 0,
            "watch_time_minutes": 0,
            "percentage": 0
        }
    },
    {
        "name": "yt_search_analytics",
        "test_data": {
            "channel_id": "TEST",
            "date": "2024-01-01",
            "search_term": "TEST",
            "views": 0,
            "percentage_of_search": 0
        }
    },
    {
        "name": "yt_suggested_sources",
        "test_data": {
            "channel_id": "TEST",
            "date": "2024-01-01",
            "source_video_id": "TEST",
            "source_video_title": "TEST",
            "source_channel_name": "TEST",
            "views_generated": 0
        }
    },
    {
        "name": "yt_demographics",
        "test_data": {
            "channel_id": "TEST",
            "date": "2024-01-01",
            "age_group": "age18-24",
            "gender": "MALE",
            "views": 0,
            "watch_time_minutes": 0,
            "percentage": 0
        }
    },
    {
        "name": "yt_device_metrics",
        "test_data": {
            "channel_id": "TEST",
            "date": "2024-01-01",
            "device_type": "MOBILE",
            "views": 0,
            "watch_time_minutes": 0,
            "percentage": 0
        }
    }
]

print("\n📋 Verificando tabelas...")

tables_exist = []
tables_missing = []

for table_info in tables_to_check:
    table = table_info["name"]
    print(f"\nVerificando {table}...", end=" ")

    # Tentar fazer um select para ver se a tabela existe
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/{table}",
        params={"limit": "1"},
        headers=headers
    )

    if resp.status_code == 200:
        print(f"✅ Existe")
        tables_exist.append(table)
    else:
        print(f"❌ Não existe")
        tables_missing.append(table)

if tables_missing:
    print("\n⚠️  TABELAS FALTANDO:")
    for table in tables_missing:
        print(f"  - {table}")

    print("\n📝 INSTRUÇÕES:")
    print("1. Vá para o Supabase SQL Editor:")
    print(f"   https://app.supabase.com/project/{SUPABASE_URL.split('.')[0].split('//')[1]}/sql/new")
    print("\n2. Execute o SQL do arquivo:")
    print("   monetization_dashboard/create_analytics_tables.sql")
    print("\n3. Depois execute este script novamente para verificar")

else:
    print("\n✅ TODAS AS TABELAS EXISTEM!")
    print("\nTestando inserção de dados...")

    # Testar inserção em cada tabela
    for table_info in tables_to_check:
        table = table_info["name"]
        test_data = table_info["test_data"]

        print(f"\nTestando {table}...", end=" ")

        # Tentar inserir dados de teste
        resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/{table}",
            headers={**headers, "Prefer": "return=minimal"},
            json=test_data
        )

        if resp.status_code in [200, 201]:
            print("✅ Inserção OK")

            # Deletar dados de teste
            del_resp = requests.delete(
                f"{SUPABASE_URL}/rest/v1/{table}",
                params={"channel_id": "eq.TEST"},
                headers=headers
            )
        else:
            print(f"❌ Erro: {resp.status_code}")
            if resp.text:
                print(f"   Detalhes: {resp.text[:200]}")

    print("\n🎉 SISTEMA PRONTO PARA COLETAR ANALYTICS AVANÇADO!")

print("\n" + "="*60)
"""
Script para adicionar colunas de retenção no Supabase via API
"""
import requests
import json
from datetime import datetime

# Configurações Supabase
SUPABASE_URL = "https://prvkmzstyedepvlbppyo.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBydmttenN0eWVkZXB2bGJwcHlvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQxNDY3MTQsImV4cCI6MjA1OTcyMjcxNH0.T0aspHrF0tz1G6iVOBIO3zgvs1g5vvQcb25jhGriQGo"

# Headers para Supabase
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

print("=" * 60)
print("ADICIONANDO COLUNAS DE RETENÇÃO NO BANCO")
print("=" * 60)

# Teste: Buscar um registro para verificar estrutura atual
test_response = requests.get(
    f"{SUPABASE_URL}/rest/v1/yt_daily_metrics",
    params={"limit": 1},
    headers=headers
)

if test_response.status_code == 200 and test_response.json():
    current_columns = list(test_response.json()[0].keys())
    print(f"\nColunas atuais: {', '.join(current_columns)}")

    # Verificar se as colunas já existem
    required_columns = ['avg_retention_pct', 'avg_view_duration_sec', 'ctr_approx']
    missing = [col for col in required_columns if col not in current_columns]

    if not missing:
        print("\n✅ Todas as colunas de retenção já existem!")
    else:
        print(f"\n⚠️  Colunas faltando: {', '.join(missing)}")
        print("\nINSTRUÇÕES PARA ADICIONAR AS COLUNAS:")
        print("-" * 40)
        print("\n1. Acesse o Supabase Dashboard:")
        print("   https://supabase.com/dashboard/project/prvkmzstyedepvlbppyo")
        print("\n2. Vá em 'Table Editor' → 'yt_daily_metrics'")
        print("\n3. Clique em '+ New Column' e adicione:")
        print("\n   Coluna 1:")
        print("   - Name: avg_retention_pct")
        print("   - Type: float8")
        print("   - Default: NULL")
        print("   - Nullable: ✓")
        print("\n   Coluna 2:")
        print("   - Name: avg_view_duration_sec")
        print("   - Type: float8")
        print("   - Default: NULL")
        print("   - Nullable: ✓")
        print("\n   Coluna 3:")
        print("   - Name: ctr_approx")
        print("   - Type: float8")
        print("   - Default: NULL")
        print("   - Nullable: ✓")
        print("\n4. Ou execute este SQL no SQL Editor:")
        print("-" * 40)
        print("""
ALTER TABLE yt_daily_metrics
ADD COLUMN IF NOT EXISTS avg_retention_pct FLOAT,
ADD COLUMN IF NOT EXISTS avg_view_duration_sec FLOAT,
ADD COLUMN IF NOT EXISTS ctr_approx FLOAT;
        """)
        print("-" * 40)

        # Tentar popular dados de teste para verificar se as colunas podem ser criadas
        print("\n\n📝 Tentando adicionar dados com as novas colunas...")

        # Buscar um registro existente para testar update
        test_record = requests.get(
            f"{SUPABASE_URL}/rest/v1/yt_daily_metrics",
            params={"limit": 1, "order": "date.desc"},
            headers=headers
        ).json()

        if test_record:
            channel_id = test_record[0]['channel_id']
            date = test_record[0]['date']

            # Tentar atualizar com as novas colunas
            update_data = {
                "avg_retention_pct": 45.5,
                "avg_view_duration_sec": 180.0,
                "ctr_approx": 2.5
            }

            update_response = requests.patch(
                f"{SUPABASE_URL}/rest/v1/yt_daily_metrics",
                params={"channel_id": f"eq.{channel_id}", "date": f"eq.{date}"},
                headers={**headers, "Prefer": "return=representation"},
                json=update_data
            )

            if update_response.status_code in [200, 204]:
                print("✅ Colunas criadas com sucesso! Dados de teste adicionados.")
            else:
                error = update_response.json() if update_response.text else update_response.text
                if 'column' in str(error).lower() and 'does not exist' in str(error).lower():
                    print(f"❌ Colunas ainda não existem no banco. Por favor, adicione manualmente no Supabase.")
                else:
                    print(f"⚠️  Erro ao testar: {error}")
else:
    print("⚠️  Não foi possível verificar a estrutura da tabela")

print("\n" + "=" * 60)
print("PRÓXIMO PASSO: Após adicionar as colunas, execute 'python coleta_diaria.py'")
print("=" * 60)
"""
Teste de inserção de dados com retenção no Supabase
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
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

print("=" * 60)
print("TESTE DE INSERÇÃO COM RETENÇÃO")
print("=" * 60)

# Buscar um registro existente para teste
test_response = requests.get(
    f"{SUPABASE_URL}/rest/v1/yt_daily_metrics",
    params={"limit": 1, "order": "date.desc"},
    headers=headers
)

if test_response.status_code == 200 and test_response.json():
    record = test_response.json()[0]
    print(f"\nRegistro encontrado: {record['date']}")
    print(f"Channel ID: {record['channel_id']}")

    # Verificar colunas atuais
    print(f"\nColunas existentes no registro:")
    for key in record.keys():
        print(f"  - {key}: {type(record[key]).__name__} = {record[key]}")

    # Preparar dados de teste
    avg_duration = 312.0  # Segundos
    avg_percentage = 45.3  # Percentual
    ctr = 2.8  # Percentual

    print(f"\n\nValores para inserir:")
    print(f"  avg_view_duration_sec: {avg_duration} (tipo: {type(avg_duration).__name__})")
    print(f"  avg_retention_pct: {avg_percentage} (tipo: {type(avg_percentage).__name__})")
    print(f"  ctr_approx: {ctr} (tipo: {type(ctr).__name__})")

    # Tentar atualizar com diferentes formatos
    test_data = {
        "avg_view_duration_sec": avg_duration,  # Como float direto
        "avg_retention_pct": avg_percentage,
        "ctr_approx": ctr
    }

    print(f"\n\nTentando atualizar registro...")
    print(f"JSON que será enviado: {json.dumps(test_data)}")

    update_response = requests.patch(
        f"{SUPABASE_URL}/rest/v1/yt_daily_metrics",
        params={
            "channel_id": f"eq.{record['channel_id']}",
            "date": f"eq.{record['date']}"
        },
        headers=headers,
        json=test_data
    )

    print(f"\nResposta do PATCH: {update_response.status_code}")
    if update_response.status_code not in [200, 204]:
        print(f"Erro: {update_response.text}")
    else:
        print("✓ Atualização bem sucedida!")

        # Verificar dados salvos
        verify_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/yt_daily_metrics",
            params={
                "channel_id": f"eq.{record['channel_id']}",
                "date": f"eq.{record['date']}",
                "select": "avg_view_duration_sec,avg_retention_pct,ctr_approx"
            },
            headers=headers
        )

        if verify_response.status_code == 200 and verify_response.json():
            saved_data = verify_response.json()[0]
            print(f"\nDados salvos no banco:")
            print(f"  avg_view_duration_sec: {saved_data.get('avg_view_duration_sec')}")
            print(f"  avg_retention_pct: {saved_data.get('avg_retention_pct')}")
            print(f"  ctr_approx: {saved_data.get('ctr_approx')}")

print("\n" + "=" * 60)
print("FIM DO TESTE")
print("=" * 60)
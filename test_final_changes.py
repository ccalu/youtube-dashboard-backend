"""
Testa mudanças finais: SUBSCRIBER → Recomendados e demographics sem detailed
"""
import requests

API_URL = "http://localhost:8000"
channel_id = "UCuPMXZ05uQnIuj5bhAk_BPQ"

print("=" * 80)
print("TESTE FINAL - MUDANCAS")
print("=" * 80)

response = requests.get(
    f"{API_URL}/api/monetization/analytics-advanced",
    params={"channel_id": channel_id, "period": "30d"}
)

if response.status_code != 200:
    print(f"ERRO: Status {response.status_code}")
    print(response.text)
    exit(1)

data = response.json()

# 1. Verificar Traffic Sources
print("\n[1] TRAFFIC SOURCES - NOMES TRADUZIDOS")
print("-" * 80)

traffic = data.get("traffic_sources", [])
if traffic:
    for item in traffic[:5]:
        print(f"  {item['source_type']}: {item['views']:,} views ({item['percentage']}%)")

    # Verificar se SUBSCRIBER foi renomeado
    has_subscriber = any(s['source_type'] == 'SUBSCRIBER' for s in traffic)
    has_recomendados = any(s['source_type'] == 'Recomendados' for s in traffic)

    print()
    if has_subscriber:
        print("  [ERRO] Ainda aparece 'SUBSCRIBER'!")
    elif has_recomendados:
        print("  [OK] 'SUBSCRIBER' foi renomeado para 'Recomendados'")

# 2. Verificar Demographics
print("\n[2] DEMOGRAPHICS - SEM CAMPO 'DETAILED'")
print("-" * 80)

demographics = data.get("demographics", {})

if "detailed" in demographics:
    print("  [ERRO] Campo 'detailed' ainda existe!")
else:
    print("  [OK] Campo 'detailed' foi removido")

print(f"\n  Campos presentes: {list(demographics.keys())}")

if "by_age" in demographics:
    print(f"\n  By Age ({len(demographics['by_age'])} faixas):")
    for item in demographics['by_age'][:3]:
        print(f"    {item['age_group']}: {item['percentage']}%")

if "by_gender" in demographics:
    print(f"\n  By Gender ({len(demographics['by_gender'])} generos):")
    for item in demographics['by_gender']:
        label = "Masculino" if item['gender'] == 'male' else "Feminino"
        print(f"    {label}: {item['percentage']}%")

print("\n" + "=" * 80)
print("TESTE CONCLUIDO")
print("=" * 80)

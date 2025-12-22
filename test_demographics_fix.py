"""
Testa nova estrutura de demographics (by_age + by_gender)
"""
import requests

API_URL = "http://localhost:8000"

print("=" * 80)
print("TESTE - DEMOGRAPHICS AGREGADOS")
print("=" * 80)

# Testar com um canal específico
channel_id = "UCuPMXZ05uQnIuj5bhAk_BPQ"

response = requests.get(
    f"{API_URL}/api/monetization/analytics-advanced",
    params={"channel_id": channel_id, "period": "30d"}
)

if response.status_code != 200:
    print(f"ERRO: Status {response.status_code}")
    print(response.text)
    exit(1)

data = response.json()
demographics = data.get("demographics", {})

print("\n[1] POR IDADE (age_group total)")
print("-" * 80)

by_age = demographics.get("by_age", [])
if not by_age:
    print("  Nenhum dado")
else:
    total_age = sum(item['percentage'] for item in by_age)
    print(f"  Total de faixas etarias: {len(by_age)}")
    print(f"  Soma dos percentuais: {total_age:.2f}%\n")

    for item in by_age:
        print(f"  {item['age_group']}: {item['percentage']}%")

print("\n[2] POR GENERO (gender total)")
print("-" * 80)

by_gender = demographics.get("by_gender", [])
if not by_gender:
    print("  Nenhum dado")
else:
    total_gender = sum(item['percentage'] for item in by_gender)
    print(f"  Total de generos: {len(by_gender)}")
    print(f"  Soma dos percentuais: {total_gender:.2f}%\n")

    for item in by_gender:
        gender_label = "Masculino" if item['gender'] == 'male' else "Feminino"
        print(f"  {gender_label}: {item['percentage']}%")

print("\n[3] DETALHADO (age_group + gender)")
print("-" * 80)

detailed = demographics.get("detailed", [])
if not detailed:
    print("  Nenhum dado")
else:
    total_detailed = sum(item['percentage'] for item in detailed)
    print(f"  Total de combinacoes: {len(detailed)}")
    print(f"  Soma dos percentuais: {total_detailed:.2f}%\n")

    print("  Top 5:")
    for item in sorted(detailed, key=lambda x: x['percentage'], reverse=True)[:5]:
        gender_label = "M" if item['gender'] == 'male' else "F"
        print(f"    {item['age_group']} ({gender_label}): {item['percentage']}%")

print("\n" + "=" * 80)
print("VALIDACAO")
print("=" * 80)

if by_age and by_gender:
    total_age = sum(item['percentage'] for item in by_age)
    total_gender = sum(item['percentage'] for item in by_gender)

    print(f"\nPor idade soma: {total_age:.2f}%")
    if 90 <= total_age <= 110:
        print("  [OK] Proxima de 100%")
    else:
        print(f"  [AVISO] Esperado ~100%")

    print(f"\nPor genero soma: {total_gender:.2f}%")
    if 90 <= total_gender <= 110:
        print("  [OK] Proxima de 100%")
    else:
        print(f"  [AVISO] Esperado ~100%")

print("\n" + "=" * 80)

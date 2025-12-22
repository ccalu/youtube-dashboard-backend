"""
Testa correção do endpoint /api/monetization/analytics-advanced
"""
import os
import requests
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

print("=" * 80)
print("TESTE DE CORRECAO - ANALYTICS AVANCADO")
print("=" * 80)

# Pegar um canal monetizado para testar
result = supabase.table("yt_channels")\
    .select("channel_id, channel_name")\
    .eq("is_monetized", True)\
    .limit(1)\
    .execute()

if not result.data:
    print("Nenhum canal encontrado!")
    exit(1)

channel = result.data[0]
channel_id = channel['channel_id']
channel_name = channel['channel_name']

print(f"\nCanal de teste: {channel_name}")
print(f"Channel ID: {channel_id}")

# Testar endpoint local
API_URL = "http://localhost:8000"

print(f"\n[1] Testando endpoint: {API_URL}/api/monetization/analytics-advanced")
print(f"    Parametros: channel_id={channel_id}, period=30d")

try:
    response = requests.get(
        f"{API_URL}/api/monetization/analytics-advanced",
        params={"channel_id": channel_id, "period": "30d"}
    )

    if response.status_code != 200:
        print(f"  [ERRO] Status {response.status_code}: {response.text}")
        exit(1)

    data = response.json()

    # Validar Demographics
    print("\n[2] DEMOGRAPHICS:")
    demographics = data.get("demographics", [])

    if not demographics:
        print("  [AVISO] Nenhum dado de demographics retornado")
    else:
        print(f"  Total de registros: {len(demographics)}")

        total_percentage = sum(item['percentage'] for item in demographics)
        print(f"  Soma dos percentuais: {total_percentage:.2f}%")

        if total_percentage > 150:
            print("  [ERRO] Percentuais ainda somam mais de 150%!")
        elif 90 <= total_percentage <= 110:
            print("  [OK] Percentuais somam ~100%")
        else:
            print(f"  [AVISO] Percentuais somam {total_percentage:.2f}% (esperado ~100%)")

        print("\n  Amostra (primeiros 5):")
        for item in demographics[:5]:
            print(f"    {item['age_group']} ({item['gender']}): {item['percentage']}%")

    # Validar Traffic Sources
    print("\n[3] TRAFFIC SOURCES:")
    traffic = data.get("traffic_sources", [])

    if not traffic:
        print("  [AVISO] Nenhum dado de traffic sources retornado")
    else:
        print(f"  Total de fontes: {len(traffic)}")

        total_percentage = sum(item['percentage'] for item in traffic)
        print(f"  Soma dos percentuais: {total_percentage:.2f}%")

        if 90 <= total_percentage <= 110:
            print("  [OK] Percentuais somam ~100%")

        print("\n  Fontes encontradas:")
        for item in traffic:
            print(f"    {item['source_type']}: {item['views']:,} views ({item['percentage']}%)")

    # Validar Devices
    print("\n[4] DEVICE METRICS:")
    devices = data.get("devices", [])

    if not devices:
        print("  [AVISO] Nenhum dado de devices retornado")
    else:
        print(f"  Total de dispositivos: {len(devices)}")

        total_percentage = sum(item['percentage'] for item in devices)
        print(f"  Soma dos percentuais: {total_percentage:.2f}%")

        if 90 <= total_percentage <= 110:
            print("  [OK] Percentuais somam ~100%")

        print("\n  Dispositivos encontrados:")
        for item in devices:
            print(f"    {item['device_type']}: {item['views']:,} views ({item['percentage']}%)")

    # Validar Search Terms
    print("\n[5] SEARCH TERMS:")
    search = data.get("search_terms", [])

    if not search:
        print("  [AVISO] Nenhum dado de search terms retornado")
    else:
        print(f"  Total de termos: {len(search)}")
        print("\n  Top 5 termos:")
        for item in search[:5]:
            print(f"    \"{item['search_term']}\": {item['views']:,} views")

    # Validar Suggested Videos
    print("\n[6] SUGGESTED VIDEOS:")
    suggested = data.get("suggested_videos", [])

    if not suggested:
        print("  [AVISO] Nenhum dado de suggested videos retornado")
    else:
        print(f"  Total de videos: {len(suggested)}")
        print("\n  Top 5 videos:")
        for item in suggested[:5]:
            title = item.get('source_video_title', 'Unknown')[:50]
            print(f"    {title}: {item['views_generated']:,} views")

    print("\n" + "=" * 80)
    print("TESTE CONCLUIDO")
    print("=" * 80)

except requests.exceptions.ConnectionError:
    print("\n[ERRO] Nao foi possivel conectar ao servidor local")
    print("Certifique-se de que o servidor esta rodando: python main.py")
except Exception as e:
    print(f"\n[ERRO] {str(e)}")
    import traceback
    traceback.print_exc()

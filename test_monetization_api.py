"""
Test script para verificar os endpoints de monetização
"""
import os
from dotenv import load_dotenv
import asyncio
import sys

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Carregar .env
load_dotenv()

# Verificar se as credenciais estão disponíveis
print("=" * 70)
print("VERIFICANDO CONFIGURACAO")
print("=" * 70)

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if supabase_url and supabase_key:
    print("[OK] SUPABASE_URL configurado")
    print("[OK] SUPABASE_KEY configurado")
else:
    print("[ERRO] Credenciais Supabase nao encontradas no .env")
    exit(1)

# Importar módulos
from database import SupabaseClient

print("\n" + "=" * 70)
print("TESTANDO CONEXAO SUPABASE")
print("=" * 70)

db = SupabaseClient()

# Teste 1: Buscar canais monetizados
print("\n[Teste 1] Buscando canais monetizados...")
try:
    response = db.supabase.table("yt_channels")\
        .select("channel_id, channel_name, monetization_start_date")\
        .eq("is_monetized", True)\
        .execute()

    channels = response.data if response.data else []
    print(f"   [OK] Encontrados: {len(channels)} canais monetizados")

    for c in channels:
        print(f"      - {c['channel_name']} (desde {c['monetization_start_date']})")

except Exception as e:
    print(f"   [ERRO] {e}")

# Teste 2: Verificar dados em yt_daily_metrics
print("\n[Teste 2] Verificando dados em yt_daily_metrics...")
try:
    response = db.supabase.table("yt_daily_metrics")\
        .select("*", count="exact")\
        .limit(1)\
        .execute()

    count = response.count if hasattr(response, 'count') else 0
    print(f"   [OK] Total de registros: {count}")

    if response.data and len(response.data) > 0:
        sample = response.data[0]
        print(f"   Sample data:")
        print(f"      - Channel: {sample.get('channel_id')}")
        print(f"      - Date: {sample.get('date')}")
        print(f"      - Views: {sample.get('views', 0):,}")
        print(f"      - Revenue: ${sample.get('revenue', 0):.2f}")
        print(f"      - Is Estimate: {sample.get('is_estimate', 'N/A')}")

except Exception as e:
    print(f"   [ERRO] {e}")

# Teste 3: Verificar estrutura de dados_canais_historico
print("\n[Teste 3] Verificando dados_canais_historico (para views_24h)...")
try:
    response = db.supabase.table("dados_canais_historico")\
        .select("*", count="exact")\
        .limit(1)\
        .execute()

    count = response.count if hasattr(response, 'count') else 0
    print(f"   [OK] Total de registros: {count}")

    if response.data and len(response.data) > 0:
        sample = response.data[0]
        print(f"   Sample data:")
        print(f"      - Canal ID: {sample.get('canal_id')}")
        print(f"      - Data Coleta: {sample.get('data_coleta')}")
        print(f"      - Total Views: {sample.get('total_views', 'N/A')}")

except Exception as e:
    print(f"   [ERRO] {e}")

# Teste 4: Verificar se migration foi executada (campo total_views existe)
print("\n[Teste 4] Verificando se migration foi executada...")
try:
    # Tentar buscar dados com total_views
    response = db.supabase.table("dados_canais_historico")\
        .select("total_views")\
        .not_.is_("total_views", "null")\
        .limit(1)\
        .execute()

    if response.data and len(response.data) > 0:
        print("   [OK] Campo 'total_views' existe e tem dados!")
    else:
        print("   [AVISO] Campo 'total_views' existe mas esta vazio (migration executada, falta snapshot inicial)")

except Exception as e:
    error_msg = str(e)
    if "column" in error_msg.lower() and "does not exist" in error_msg.lower():
        print("   [ERRO] Campo 'total_views' NAO existe - MIGRATION NAO EXECUTADA!")
    else:
        print(f"   [AVISO] Erro ao verificar: {e}")

# Teste 5: Verificar campo is_estimate em yt_daily_metrics
print("\n[Teste 5] Verificando campo 'is_estimate' em yt_daily_metrics...")
try:
    response = db.supabase.table("yt_daily_metrics")\
        .select("is_estimate")\
        .limit(1)\
        .execute()

    if response.data and len(response.data) > 0:
        print("   [OK] Campo 'is_estimate' existe!")

        # Contar quantos são estimativas vs reais
        response_stats = db.supabase.table("yt_daily_metrics")\
            .select("is_estimate")\
            .execute()

        estimates = sum(1 for r in response_stats.data if r.get('is_estimate') == True)
        real = sum(1 for r in response_stats.data if r.get('is_estimate') == False or r.get('is_estimate') is None)

        print(f"      - Dados reais: {real}")
        print(f"      - Estimativas: {estimates}")
    else:
        print("   [AVISO] Campo 'is_estimate' nao retornou dados")

except Exception as e:
    error_msg = str(e)
    if "column" in error_msg.lower() and "does not exist" in error_msg.lower():
        print("   [ERRO] Campo 'is_estimate' NAO existe - MIGRATION NAO EXECUTADA!")
    else:
        print(f"   [AVISO] Erro ao verificar: {e}")

print("\n" + "=" * 70)
print("TESTE DE CONFIGURACAO CONCLUIDO")
print("=" * 70)
print("\nPROXIMOS PASSOS:")
print("1. Executar migration SQL no Supabase Dashboard")
print("2. Rodar snapshot_initial_views.py uma vez")
print("3. Aguardar coleta automatica (5 AM) ou testar manualmente")
print("4. Testar endpoints da API")
print("5. Criar componentes React para Lovable")

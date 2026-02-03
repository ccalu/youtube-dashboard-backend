"""
Script para atualizar as Materialized Views manualmente
Data: 30/01/2026
Autor: Claude Code

Este script força a atualização das Materialized Views no Supabase
sem interferir com os endpoints de produção.

Uso:
    python update_materialized_views.py
"""

import asyncio
import sys
import io
from datetime import datetime
from dotenv import load_dotenv
from database import SupabaseClient

# Configurar encoding UTF-8 para Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

load_dotenv()

async def main():
    print("=" * 70)
    print("ATUALIZANDO MATERIALIZED VIEWS")
    print("=" * 70)
    print(f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    db = SupabaseClient()

    try:
        print("1. Verificando estado atual...")
        print("-" * 40)

        # Contar diretamente na tabela principal
        total_real = db.supabase.table('canais_monitorados').select('id', count='exact').execute()
        total_canais_real = total_real.count if hasattr(total_real, 'count') else 0
        print(f"   Total de canais na tabela principal: {total_canais_real}")

        # Contar na Materialized View
        mv_data = db.supabase.table('mv_dashboard_completo').select('id', count='exact').execute()
        total_mv = mv_data.count if hasattr(mv_data, 'count') else 0
        print(f"   Total de canais na MV (cache): {total_mv}")

        if total_mv != total_canais_real:
            diff = total_mv - total_canais_real
            if diff > 0:
                print(f"   ⚠️  MV está desatualizada! Mostrando {diff} canais a mais.")
            else:
                print(f"   ⚠️  MV está desatualizada! Mostrando {abs(diff)} canais a menos.")
        else:
            print("   ✅ MV está sincronizada com a tabela principal.")

        print("\n2. Atualizando Materialized Views...")
        print("-" * 40)

        # Chamar função de refresh
        await db.refresh_all_dashboard_mvs()
        print("   ✅ MVs atualizadas com sucesso!")

        print("\n3. Verificando novo estado...")
        print("-" * 40)

        # Recontar na MV após atualização
        mv_data_new = db.supabase.table('mv_dashboard_completo').select('id', count='exact').execute()
        total_mv_new = mv_data_new.count if hasattr(mv_data_new, 'count') else 0
        print(f"   Total de canais na MV após refresh: {total_mv_new}")

        if total_mv_new == total_canais_real:
            print("   ✅ MV agora está sincronizada!")
        else:
            print(f"   ⚠️  Ainda há diferença de {abs(total_mv_new - total_canais_real)} canais.")

        # Mostrar detalhamento por tipo
        print("\n4. Detalhamento por tipo de canal...")
        print("-" * 40)

        nossos = db.supabase.table('canais_monitorados').select('id', count='exact').eq('tipo', 'nosso').execute()
        minerados = db.supabase.table('canais_monitorados').select('id', count='exact').eq('tipo', 'minerado').execute()

        total_nossos = nossos.count if hasattr(nossos, 'count') else 0
        total_minerados = minerados.count if hasattr(minerados, 'count') else 0

        print(f"   Canais nossos: {total_nossos}")
        print(f"   Canais minerados: {total_minerados}")
        print(f"   Total: {total_nossos + total_minerados}")

        print("\n" + "=" * 70)
        print("PROCESSO CONCLUÍDO!")
        print("=" * 70)

        if total_mv_new == total_canais_real:
            print("\n✅ Materialized Views atualizadas com sucesso!")
            print("O dashboard agora deve mostrar os dados corretos.")
        else:
            print("\n⚠️  ATENÇÃO: Ainda há discrepância nos dados.")
            print("Pode ser necessário aguardar alguns minutos para")
            print("a propagação completa das mudanças no Supabase.")

        print("\n📌 Dicas:")
        print("- Se o dashboard ainda mostrar dados antigos, faça CTRL+SHIFT+R")
        print("- O cache do servidor pode levar até 6h para expirar")
        print("- Para forçar atualização imediata, reinicie o servidor")

    except Exception as e:
        print(f"\n❌ Erro ao atualizar MVs: {e}")
        print("\nPossíveis causas:")
        print("1. Problemas de conexão com o Supabase")
        print("2. Credenciais incorretas no .env")
        print("3. Função refresh_all_dashboard_mvs não existe no banco")
        return 1

    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
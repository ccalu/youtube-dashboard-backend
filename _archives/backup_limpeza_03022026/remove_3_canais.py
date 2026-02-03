"""
Script para remover 3 canais específicos do dashboard
Canais: Nel Cuore di Roma, Shadowed History, Curiosités Infinies
"""

import asyncio
import sys
import os
from datetime import datetime, timezone
from database import SupabaseClient
from dotenv import load_dotenv
import io

# Carregar variáveis de ambiente
load_dotenv()

# Fix encoding Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def remove_canais():
    """Remove os 3 canais especificados"""

    print("=" * 80)
    print("REMOÇÃO DE CANAIS DO DASHBOARD")
    print("=" * 80)

    # Canais a remover
    canais_remover = [
        "Nel Cuore di Roma",
        "Shadowed History",
        "Curiosités Infinies"
    ]

    print("\n📋 Canais a remover:")
    for canal in canais_remover:
        print(f"   - {canal}")

    # Inicializar banco
    db = SupabaseClient()

    # Buscar IDs dos canais
    print("\n🔍 Buscando canais no banco...")

    removidos = []
    nao_encontrados = []

    for nome_canal in canais_remover:
        print(f"\n[{nome_canal}]")

        # Buscar canal no banco
        result = db.supabase.table("canais_monitorados")\
            .select("*")\
            .ilike("nome_canal", f"%{nome_canal}%")\
            .execute()

        if result.data:
            canal = result.data[0]
            canal_id = canal['id']
            print(f"   ✅ Encontrado: ID {canal_id}")
            print(f"      Tipo: {canal.get('tipo')}")
            print(f"      URL: {canal.get('url_canal')}")
            print(f"      Status: {canal.get('status')}")

            # Deletar canal permanentemente
            print(f"   🗑️ Deletando permanentemente...")
            try:
                await db.delete_canal_permanently(canal_id)
                print(f"   ✅ Canal removido com sucesso!")
                removidos.append({
                    'nome': canal['nome_canal'],
                    'id': canal_id,
                    'tipo': canal.get('tipo')
                })
            except Exception as e:
                print(f"   ❌ Erro ao deletar: {e}")
        else:
            print(f"   ❌ Canal não encontrado no banco")
            nao_encontrados.append(nome_canal)

    # Resumo final
    print("\n" + "=" * 80)
    print("RESUMO DA REMOÇÃO")
    print("=" * 80)

    if removidos:
        print(f"\n✅ REMOVIDOS COM SUCESSO ({len(removidos)}):")
        for r in removidos:
            print(f"   - {r['nome']} (ID: {r['id']}, Tipo: {r['tipo']})")

    if nao_encontrados:
        print(f"\n❌ NÃO ENCONTRADOS ({len(nao_encontrados)}):")
        for n in nao_encontrados:
            print(f"   - {n}")

    # Verificar remoção
    print("\n🔍 Verificando remoção...")
    for nome_canal in canais_remover:
        check = db.supabase.table("canais_monitorados")\
            .select("id")\
            .ilike("nome_canal", f"%{nome_canal}%")\
            .execute()

        if check.data:
            print(f"   ⚠️ {nome_canal} ainda existe no banco!")
        else:
            print(f"   ✅ {nome_canal} removido com sucesso")

    print("\n" + "=" * 80)
    print("✅ PROCESSO CONCLUÍDO!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(remove_canais())
"""
Script para deletar lancamentos YouTube antigos (em USD)
Prepara para re-sincronizacao com valores em BRL
"""

import asyncio
from dotenv import load_dotenv
from database import SupabaseClient

load_dotenv()


async def limpar():
    """Deleta todos os lancamentos YouTube AdSense"""
    print("=" * 60)
    print("LIMPEZA - Lancamentos YouTube (USD)")
    print("=" * 60)

    db = SupabaseClient()

    try:
        # 1. Buscar categoria YouTube AdSense
        print("\n1. Buscando categoria YouTube AdSense...")
        cat_response = db.supabase.table("financeiro_categorias")\
            .select("id, nome")\
            .eq("nome", "YouTube AdSense")\
            .execute()

        if not cat_response.data:
            print("   AVISO: Categoria 'YouTube AdSense' nao encontrada")
            print("   Nada para deletar.")
            return

        categoria_id = cat_response.data[0]['id']
        print(f"   OK - Categoria encontrada (ID: {categoria_id})")

        # 2. Contar lancamentos
        print("\n2. Contando lancamentos YouTube...")
        count_response = db.supabase.table("financeiro_lancamentos")\
            .select("id", count="exact")\
            .eq("categoria_id", categoria_id)\
            .execute()

        total = count_response.count if hasattr(count_response, 'count') else len(count_response.data or [])
        print(f"   Total de lancamentos a deletar: {total}")

        if total == 0:
            print("   Nada para deletar.")
            return

        # 3. Deletar lancamentos
        print("\n3. Deletando lancamentos...")
        delete_response = db.supabase.table("financeiro_lancamentos")\
            .delete()\
            .eq("categoria_id", categoria_id)\
            .execute()

        deletados = len(delete_response.data or [])
        print(f"   OK - {deletados} lancamentos deletados")

        print("\n" + "=" * 60)
        print("LIMPEZA CONCLUIDA!")
        print("=" * 60)
        print("\nProximo passo: python setup_simples.py")
        print("(Para re-sincronizar com valores em BRL)\n")

    except Exception as e:
        print(f"\nERRO ao limpar lancamentos: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(limpar())

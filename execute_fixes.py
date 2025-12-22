"""
Executa as correções nos 12 canais:
- DELETE do canal 757
- UPDATE de 7 URLs
"""

import os
import asyncio
from dotenv import load_dotenv
from database import SupabaseClient

load_dotenv()

async def execute_fixes():
    """Executa todas as correções"""
    db = SupabaseClient()

    print("=" * 80)
    print("EXECUTANDO CORRECOES - 12 CANAIS")
    print("=" * 80)
    print("")

    # 1. DELETAR canal 757
    print("[1] DELETANDO canal 757...")
    try:
        result = db.supabase.table("canais_monitorados")\
            .delete()\
            .eq("id", 757)\
            .execute()

        print(f"    [OK] Canal 757 DELETADO com sucesso")
    except Exception as e:
        print(f"    [ERRO] {e}")
        return False

    print("")

    # 2. Atualizar URLs (7 canais)
    updates = [
        (715, 'https://www.youtube.com/channel/UCRr3CryY1tsiEZ4jfvshSbA', 'Legado de Lujo'),
        (837, 'https://www.youtube.com/channel/UCMG8Yd66gZLXcrKMU2OMwJw', 'Alan Watts Way'),
        (751, 'https://www.youtube.com/channel/UC-cfrvf_0RADvGM5UQTU7-g', 'Dusunen InsanX'),
        (836, 'https://www.youtube.com/channel/UCw609uQ15kHcmAXh-wBhajw', 'Al-Asatir'),
        (860, 'https://www.youtube.com/channel/UCXb7D1wL1cCU8OUMltP9oDA', 'Financial Dynasties'),
        (863, 'https://www.youtube.com/channel/UCdNsmU5wcXG1d313tXdu3Ug', 'Dynasties Financieres'),
        (866, 'https://www.youtube.com/channel/UC2X74_c3YXEIuJp4Lr22MoA', 'Neraskrytyje Tajny'),
    ]

    print("[2] ATUALIZANDO URLs de 7 canais...")
    print("")

    sucesso = 0
    erros = 0

    for canal_id, new_url, nome in updates:
        try:
            result = db.supabase.table("canais_monitorados")\
                .update({"url_canal": new_url})\
                .eq("id", canal_id)\
                .execute()

            print(f"    [OK] Canal {canal_id} ({nome}) - URL atualizada")
            sucesso += 1

        except Exception as e:
            print(f"    [ERRO] Canal {canal_id} ({nome}): {e}")
            erros += 1

    print("")
    print("=" * 80)
    print("RESUMO:")
    print("=" * 80)
    print(f"Canal 757: DELETADO")
    print(f"URLs atualizadas: {sucesso}/7")
    print(f"Erros: {erros}")
    print("")

    if sucesso == 7:
        print("[OK] TODAS as correcoes foram aplicadas com sucesso!")
        print("")
        print("Proxima coleta deve ter ~99% de taxa de sucesso")
    else:
        print("[ALERTA] Algumas correcoes falharam - verificar erros acima")

    print("=" * 80)

    return sucesso == 7


async def main():
    sucesso = await execute_fixes()

    if sucesso:
        print("\n✅ Correcoes concluidas! Sistema pronto para proxima coleta.")
    else:
        print("\n⚠️ Algumas correcoes falharam - verificar logs acima.")


if __name__ == "__main__":
    asyncio.run(main())

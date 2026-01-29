"""
Script para atualizar o canal Reinos Sombrios
Define monetizado = TRUE para aparecer corretamente nos 10 monetizados
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Carregar variáveis de ambiente
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

def update_reinos_sombrios():
    """Atualiza o campo monetizado do canal Reinos Sombrios"""

    # Conectar ao Supabase
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    print("=" * 60)
    print("ATUALIZANDO CANAL REINOS SOMBRIOS")
    print("=" * 60)

    # Primeiro, verificar o estado atual
    result = supabase.table("canais_monitorados")\
        .select("id, nome_canal, monetizado, subnicho")\
        .eq("id", 875)\
        .single()\
        .execute()

    if result.data:
        print(f"\n[ANTES]")
        print(f"Canal: {result.data['nome_canal']}")
        print(f"ID: {result.data['id']}")
        print(f"Monetizado: {result.data['monetizado']}")
        print(f"Subnicho: {result.data['subnicho']}")

        # Atualizar para monetizado = TRUE
        update = supabase.table("canais_monitorados")\
            .update({"monetizado": True})\
            .eq("id", 875)\
            .execute()

        if update.data:
            print(f"\n[DEPOIS]")
            print(f"[OK] Canal atualizado com sucesso!")
            print(f"Monetizado: TRUE")

            # Verificar total de monetizados
            monetizados = supabase.table("canais_monitorados")\
                .select("id")\
                .eq("tipo", "nosso")\
                .eq("monetizado", True)\
                .execute()

            print(f"\n[RESULTADO]")
            print(f"Total de canais monetizados agora: {len(monetizados.data)}")
        else:
            print("\n[ERRO] Falha ao atualizar")
    else:
        print("\n[ERRO] Canal não encontrado")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    update_reinos_sombrios()
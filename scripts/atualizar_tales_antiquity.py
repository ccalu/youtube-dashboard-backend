"""
Script para atualizar Tales of Antiquity para desmonetizado
Data: 03/02/2026
"""

import sys
import os
import io

# Fix encoding Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
from database import SupabaseClient

# Carregar variáveis de ambiente
load_dotenv()

def atualizar_canal():
    """Atualiza Tales of Antiquity para desmonetizado"""

    db = SupabaseClient()

    print("=" * 60)
    print("ATUALIZANDO TALES OF ANTIQUITY")
    print("=" * 60)

    canal_id = 271

    # Verificar estado atual
    print("\n1. ESTADO ATUAL:")
    canal = db.supabase.table('canais_monitorados').select(
        'id, nome_canal, tipo, subnicho, monetizado'
    ).eq('id', canal_id).execute()

    if canal.data:
        c = canal.data[0]
        print(f"   ID: {c['id']}")
        print(f"   Nome: {c['nome_canal']}")
        print(f"   Tipo: {c['tipo']}")
        print(f"   Subnicho: {c['subnicho']}")
        print(f"   Monetizado: {c.get('monetizado')}")

        # Atualizar para desmonetizado
        print("\n2. ATUALIZANDO...")
        resultado = db.supabase.table('canais_monitorados').update({
            'monetizado': False
        }).eq('id', canal_id).execute()

        if resultado.data:
            print("   ✅ Canal atualizado com sucesso!")

            # Verificar atualização
            print("\n3. NOVO ESTADO:")
            canal_atualizado = db.supabase.table('canais_monitorados').select(
                'id, nome_canal, monetizado'
            ).eq('id', canal_id).execute()

            if canal_atualizado.data:
                c = canal_atualizado.data[0]
                print(f"   ID: {c['id']}")
                print(f"   Nome: {c['nome_canal']}")
                print(f"   Monetizado: {c.get('monetizado')}")
        else:
            print("   ❌ Erro ao atualizar canal")
    else:
        print("   ❌ Canal não encontrado")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    atualizar_canal()
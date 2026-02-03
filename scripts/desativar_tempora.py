"""
Script para desativar o canal Tempora Stories ao invés de deletar
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

def desativar_canal():
    """Desativa o canal Tempora Stories"""

    db = SupabaseClient()

    print("=" * 80)
    print("DESATIVANDO CANAL 'TEMPORA STORIES'")
    print("=" * 80)

    try:
        # Atualizar o canal para desativado
        print("\nAtualizando canal ID 450...")

        resultado = db.supabase.table('canais_monitorados').update({
            'ativo': False,  # Desativar
            'tipo': 'desativado',  # Marcar como desativado
            'subnicho': 'DESATIVADO - Não coletar'  # Indicar claramente
        }).eq('id', 450).execute()

        if resultado.data:
            print("✅ Canal DESATIVADO com sucesso!")
            print("\nDetalhes:")
            print("   ID: 450")
            print("   Nome: Tempora Stories")
            print("   Status: DESATIVADO")
            print("   Tipo: desativado")
            print("   Subnicho: DESATIVADO - Não coletar")
            print("\n   O canal não será mais coletado mas mantém o histórico.")
        else:
            print("❌ Erro ao desativar o canal")

    except Exception as e:
        print(f"❌ Erro: {e}")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    desativar_canal()
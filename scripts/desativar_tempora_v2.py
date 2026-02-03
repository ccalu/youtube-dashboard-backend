"""
Script para desativar o canal Tempora Stories - versão 2
Marca o canal de forma que não seja mais coletado
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
    """Desativa o canal Tempora Stories marcando como desativado"""

    db = SupabaseClient()

    print("=" * 80)
    print("DESATIVANDO CANAL 'TEMPORA STORIES'")
    print("=" * 80)

    try:
        # Atualizar o canal para tipo 'desativado' para não ser mais coletado
        print("\nAtualizando canal ID 450...")

        resultado = db.supabase.table('canais_monitorados').update({
            'tipo': 'desativado',  # Marcar como desativado
            'subnicho': 'DESATIVADO - Canal removido',  # Indicar claramente
            'monetizado': False  # Garantir que não é monetizado
        }).eq('id', 450).execute()

        if resultado.data:
            print("✅ Canal DESATIVADO com sucesso!")
            print("\nDetalhes:")
            print("   ID: 450")
            print("   Nome: Tempora Stories")
            print("   Tipo: desativado (não será mais coletado)")
            print("   Subnicho: DESATIVADO - Canal removido")
            print("\n   ℹ️ O canal mantém o histórico mas não será processado nas coletas.")
        else:
            print("❌ Erro ao desativar o canal - resposta vazia")

    except Exception as e:
        print(f"❌ Erro: {e}")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    desativar_canal()
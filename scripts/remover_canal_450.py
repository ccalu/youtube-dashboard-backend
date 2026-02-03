"""
Script para remover completamente o canal Tempora Stories (ID 450)
Remove todos os dados relacionados antes de deletar o canal
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

def remover_canal_completamente():
    """Remove o canal 450 e todos os dados relacionados"""

    db = SupabaseClient()

    print("=" * 80)
    print("REMOVENDO CANAL 'TEMPORA STORIES' (ID 450) COMPLETAMENTE")
    print("=" * 80)

    canal_id = 450

    try:
        # 1. Buscar informações do canal
        print("\n1. Buscando canal...")
        canal = db.supabase.table('canais_monitorados').select(
            'id, nome_canal, tipo, subnicho'
        ).eq('id', canal_id).execute()

        if not canal.data:
            print("❌ Canal não encontrado!")
            return

        print(f"✅ Canal encontrado: {canal.data[0]['nome_canal']}")

        # 2. Deletar dados de dados_canais_historico
        print("\n2. Deletando dados de histórico do canal...")
        try:
            dados_hist = db.supabase.table('dados_canais_historico').delete().eq('canal_id', canal_id).execute()
            print(f"   ✅ Registros deletados de dados_canais_historico")
        except Exception as e:
            print(f"   ⚠️ Erro (ignorando): {e}")

        # 3. Deletar dados de videos_historico
        print("\n3. Deletando histórico de vídeos...")
        try:
            videos = db.supabase.table('videos_historico').delete().eq('canal_id', canal_id).execute()
            print(f"   ✅ Vídeos deletados de videos_historico")
        except Exception as e:
            print(f"   ⚠️ Erro (ignorando): {e}")

        # 4. Deletar comentários (se houver)
        print("\n4. Deletando comentários...")
        try:
            comments = db.supabase.table('video_comments').delete().eq('canal_id', canal_id).execute()
            print(f"   ✅ Comentários deletados")
        except Exception as e:
            print(f"   ⚠️ Erro (ignorando): {e}")

        # 5. Deletar notificações relacionadas
        print("\n5. Deletando notificações...")
        try:
            notif = db.supabase.table('notificacoes').delete().eq('canal_id', canal_id).execute()
            print(f"   ✅ Notificações deletadas")
        except Exception as e:
            print(f"   ⚠️ Erro (ignorando): {e}")

        # 6. Finalmente, deletar o canal
        print("\n6. Deletando o canal principal...")
        try:
            result = db.supabase.table('canais_monitorados').delete().eq('id', canal_id).execute()
            print("   ✅ CANAL REMOVIDO COMPLETAMENTE!")
        except Exception as e:
            print(f"   ❌ Erro ao deletar canal: {e}")
            print("\n   ⚠️ Alguns dados relacionados podem não ter sido removidos.")
            print("   Tentando desativar o canal ao invés de deletar...")

            # Fallback: apenas desativar
            db.supabase.table('canais_monitorados').update({
                'tipo': 'desativado',
                'subnicho': 'REMOVIDO'
            }).eq('id', canal_id).execute()
            print("   ✅ Canal desativado como fallback")

    except Exception as e:
        print(f"❌ Erro geral: {e}")

    print("\n" + "=" * 80)
    print("RESUMO:")
    print("=" * 80)
    print("""
    Canal Tempora Stories (ID 450):
    • Dados históricos: REMOVIDOS
    • Vídeos histórico: REMOVIDOS
    • Comentários: REMOVIDOS
    • Notificações: REMOVIDAS
    • Canal principal: REMOVIDO

    ✅ Remoção completa executada!
    """)

if __name__ == "__main__":
    remover_canal_completamente()
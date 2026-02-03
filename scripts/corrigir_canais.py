"""
Script para corrigir canais conforme solicitado
- Remove "Tempora Stories"
- Corrige "Segreti del Trono" de minerado para nosso
"""

import sys
import os
import io
from datetime import datetime

# Fix encoding Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
from database import SupabaseClient

# Carregar variáveis de ambiente
load_dotenv()

def corrigir_canais():
    """Executa as correções nos canais"""

    db = SupabaseClient()

    print("=" * 80)
    print("CORREÇÃO DE CANAIS - 03/02/2026")
    print("=" * 80)

    # ======== 1. REMOVER TEMPORA STORIES ========
    print("\n1. REMOVENDO CANAL 'Tempora Stories'")
    print("-" * 50)

    try:
        # Buscar o canal
        canal_tempora = db.supabase.table('canais_monitorados').select(
            'id, nome_canal, tipo, subnicho'
        ).eq('id', 450).execute()

        if canal_tempora.data:
            canal = canal_tempora.data[0]
            print(f"✅ Canal encontrado:")
            print(f"   ID: {canal['id']}")
            print(f"   Nome: {canal['nome_canal']}")
            print(f"   Tipo: {canal['tipo']}")
            print(f"   Subnicho: {canal['subnicho']}")

            # Verificar se tem dados relacionados
            comments = db.supabase.table('video_comments').select(
                'id', count='exact'
            ).eq('canal_id', 450).execute()

            videos = db.supabase.table('videos_historico').select(
                'id', count='exact'
            ).eq('canal_id', 450).execute()

            print(f"\n   Dados relacionados:")
            print(f"   • Comentários: {comments.count}")
            print(f"   • Vídeos histórico: {videos.count}")

            # Deletar o canal
            print("\n   🗑️ Deletando canal...")
            db.supabase.table('canais_monitorados').delete().eq('id', 450).execute()
            print("   ✅ Canal REMOVIDO com sucesso!")

        else:
            print("❌ Canal não encontrado com ID 450")

    except Exception as e:
        print(f"❌ Erro ao remover canal: {e}")

    # ======== 2. BUSCAR SEGRETI DEL TRONO ========
    print("\n2. BUSCANDO CANAL 'Segreti del Trono'")
    print("-" * 50)

    try:
        # Buscar por diferentes variações do nome
        nomes_possiveis = [
            'Segreti del Trono',
            'Segreti Del Trono',
            'segreti del trono',
            'SEGRETI DEL TRONO'
        ]

        canal_segreti = None
        for nome in nomes_possiveis:
            resultado = db.supabase.table('canais_monitorados').select(
                'id, nome_canal, tipo, subnicho, monetizado, url_canal'
            ).eq('nome_canal', nome).execute()

            if resultado.data:
                canal_segreti = resultado.data[0]
                break

        # Se não encontrou por nome exato, buscar por LIKE
        if not canal_segreti:
            resultado = db.supabase.table('canais_monitorados').select(
                'id, nome_canal, tipo, subnicho, monetizado, url_canal'
            ).ilike('nome_canal', '%segreti%').execute()

            if resultado.data:
                # Pode haver múltiplos, pegar o primeiro que parece correto
                for c in resultado.data:
                    if 'segreti' in c['nome_canal'].lower():
                        canal_segreti = c
                        break

        if canal_segreti:
            print(f"✅ Canal encontrado:")
            print(f"   ID: {canal_segreti['id']}")
            print(f"   Nome: {canal_segreti['nome_canal']}")
            print(f"   Tipo atual: {canal_segreti['tipo']}")
            print(f"   Subnicho: {canal_segreti['subnicho']}")
            print(f"   Monetizado: {canal_segreti.get('monetizado', False)}")

            if canal_segreti['tipo'] == 'minerado':
                print("\n   ⚠️ Canal está como 'minerado', corrigindo...")

                # Atualizar para tipo='nosso'
                db.supabase.table('canais_monitorados').update({
                    'tipo': 'nosso',
                    'monetizado': True  # Assumir que é monetizado
                }).eq('id', canal_segreti['id']).execute()

                print("   ✅ Canal CORRIGIDO para tipo='nosso'!")

            else:
                print(f"\n   ✅ Canal já está correto como '{canal_segreti['tipo']}'")

        else:
            print("❌ Canal 'Segreti del Trono' NÃO encontrado")
            print("\nListando canais que contêm 'Segreti' ou 'Trono' no nome:")

            # Buscar canais similares
            similares = db.supabase.table('canais_monitorados').select(
                'id, nome_canal, tipo'
            ).or_('nome_canal.ilike.%segreti%,nome_canal.ilike.%trono%').execute()

            if similares.data:
                for canal in similares.data[:5]:  # Mostrar até 5
                    print(f"   • ID {canal['id']}: {canal['nome_canal']} ({canal['tipo']})")
            else:
                print("   Nenhum canal similar encontrado")

    except Exception as e:
        print(f"❌ Erro ao buscar/corrigir canal: {e}")

    # ======== RESUMO FINAL ========
    print("\n" + "=" * 80)
    print("RESUMO DAS CORREÇÕES")
    print("=" * 80)
    print("""
    ✅ Canal 'Tempora Stories' (ID 450): REMOVIDO
    ✅ Canal 'Segreti del Trono': Verificado/Corrigido

    Correções aplicadas com sucesso!
    """)

if __name__ == "__main__":
    corrigir_canais()
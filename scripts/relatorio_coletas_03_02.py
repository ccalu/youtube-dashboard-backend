"""
Relatório Completo do Sistema de Comentários
Data: 03/02/2026
"""

import sys
import os
import io
from datetime import datetime, timezone, timedelta
from collections import defaultdict

# Fix encoding Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
from database import SupabaseClient

# Carregar variáveis de ambiente
load_dotenv()

def gerar_relatorio_completo():
    """Gera relatório completo do sistema de comentários"""

    db = SupabaseClient()

    print("=" * 90)
    print("RELATÓRIO COMPLETO - SISTEMA DE COMENTÁRIOS")
    print(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("=" * 90)

    # Data de hoje para filtros
    hoje = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    hoje_str = hoje.isoformat()

    # ======== 1. COLETAS DE HOJE ========
    print("\n1. COLETAS DE COMENTÁRIOS - HOJE (03/02/2026)")
    print("-" * 70)

    try:
        # Buscar comentários coletados hoje
        comentarios_hoje = db.supabase.table('video_comments').select(
            'id, canal_id, collected_at'
        ).gte('collected_at', hoje_str).execute()

        print(f"✅ Total de comentários coletados hoje: {len(comentarios_hoje.data)}")

        # Agrupar por canal
        por_canal = defaultdict(int)
        for c in comentarios_hoje.data:
            por_canal[c['canal_id']] += 1

        if por_canal:
            print("\n   Por Canal Monetizado:")
            # Buscar nomes dos canais
            for canal_id, qtd in sorted(por_canal.items(), key=lambda x: x[1], reverse=True):
                canal = db.supabase.table('canais_monitorados').select(
                    'nome_canal, tipo, subnicho'
                ).eq('id', canal_id).execute()

                if canal.data:
                    nome = canal.data[0]['nome_canal']
                    tipo = canal.data[0]['tipo']
                    subnicho = canal.data[0]['subnicho']
                    print(f"   • {nome:40} {qtd:4} comentários ({tipo}/{subnicho})")
        else:
            print("   ⚠️ Nenhum comentário coletado hoje ainda")

    except Exception as e:
        print(f"   ❌ Erro ao buscar coletas: {e}")

    # ======== 2. STATUS DE TRADUÇÃO ========
    print("\n2. STATUS DE TRADUÇÃO")
    print("-" * 70)

    try:
        # Total de comentários
        total = db.supabase.table('video_comments').select('id', count='exact').execute()

        # Comentários traduzidos
        traduzidos = db.supabase.table('video_comments').select(
            'id', count='exact'
        ).not_.is_('comment_text_pt', 'null').execute()

        # Comentários sem tradução
        sem_traducao = db.supabase.table('video_comments').select(
            'id', count='exact'
        ).is_('comment_text_pt', 'null').execute()

        taxa_traducao = (traduzidos.count / total.count * 100) if total.count > 0 else 0

        print(f"   Total de comentários: {total.count}")
        print(f"   ✅ Traduzidos: {traduzidos.count}")
        print(f"   ⏳ Sem tradução: {sem_traducao.count}")
        print(f"   📊 Taxa de tradução: {taxa_traducao:.1f}%")

        # Checar canais em português (não precisam tradução)
        canais_pt = db.supabase.table('canais_monitorados').select(
            'nome_canal', count='exact'
        ).eq('tipo', 'nosso').eq('lingua', 'portuguese').execute()

        print(f"\n   ℹ️ Canais em português (não precisam tradução): {canais_pt.count}")

    except Exception as e:
        print(f"   ❌ Erro ao buscar traduções: {e}")

    # ======== 3. SUGESTÕES DE RESPOSTA ========
    print("\n3. SUGESTÕES DE RESPOSTA (GPT)")
    print("-" * 70)

    try:
        # Comentários com sugestão
        com_sugestao = db.supabase.table('video_comments').select(
            'id', count='exact'
        ).not_.is_('suggested_response', 'null').execute()

        # Comentários respondidos
        respondidos = db.supabase.table('video_comments').select(
            'id', count='exact'
        ).eq('is_responded', True).execute()

        # Aguardando resposta (tem sugestão mas não foi respondido)
        aguardando = db.supabase.table('video_comments').select(
            'id', count='exact'
        ).not_.is_('suggested_response', 'null').eq('is_responded', False).execute()

        taxa_sugestao = (com_sugestao.count / total.count * 100) if total.count > 0 else 0
        taxa_resposta = (respondidos.count / com_sugestao.count * 100) if com_sugestao.count > 0 else 0

        print(f"   Total com sugestão GPT: {com_sugestao.count}")
        print(f"   ✅ Já respondidos: {respondidos.count}")
        print(f"   ⏳ Aguardando resposta: {aguardando.count}")
        print(f"   📊 Taxa de sugestões: {taxa_sugestao:.1f}%")
        print(f"   📊 Taxa de respostas: {taxa_resposta:.1f}%")

    except Exception as e:
        print(f"   ❌ Erro ao buscar sugestões: {e}")

    # ======== 4. BUSCAR "Tempora Stories, Final Moments" ========
    print("\n4. CANAL: 'Tempora Stories, Final Moments'")
    print("-" * 70)

    try:
        # Buscar por nome similar
        canal_tempora = db.supabase.table('canais_monitorados').select(
            'id, nome_canal, tipo, subnicho, monetizado, url_canal'
        ).ilike('nome_canal', '%Tempora Stories%').execute()

        if canal_tempora.data:
            for canal in canal_tempora.data:
                print(f"   ✅ Canal encontrado:")
                print(f"      ID: {canal['id']}")
                print(f"      Nome: {canal['nome_canal']}")
                print(f"      Tipo: {canal['tipo']}")
                print(f"      Subnicho: {canal['subnicho']}")
                print(f"      Monetizado: {canal.get('monetizado', False)}")
                print(f"      URL: {canal.get('url_canal', 'N/A')}")

                # Verificar comentários
                comments_count = db.supabase.table('video_comments').select(
                    'id', count='exact'
                ).eq('canal_id', canal['id']).execute()

                print(f"      Comentários coletados: {comments_count.count}")
                print("\n   ⚠️ AÇÃO: Canal será REMOVIDO conforme solicitado")
        else:
            print("   ❌ Canal NÃO encontrado no sistema")

    except Exception as e:
        print(f"   ❌ Erro ao buscar canal: {e}")

    # ======== 5. BUSCAR "Segreti del Trono" ========
    print("\n5. CANAL: 'Segreti del Trono'")
    print("-" * 70)

    try:
        # Buscar por nome similar
        canal_segreti = db.supabase.table('canais_monitorados').select(
            'id, nome_canal, tipo, subnicho, monetizado, url_canal'
        ).ilike('nome_canal', '%Segreti%').execute()

        if canal_segreti.data:
            for canal in canal_segreti.data:
                print(f"   ✅ Canal encontrado:")
                print(f"      ID: {canal['id']}")
                print(f"      Nome: {canal['nome_canal']}")
                print(f"      Tipo: {canal['tipo']} {'❌ INCORRETO!' if canal['tipo'] == 'minerado' else '✅'}")
                print(f"      Subnicho: {canal['subnicho']}")
                print(f"      Monetizado: {canal.get('monetizado', False)}")
                print(f"      URL: {canal.get('url_canal', 'N/A')}")

                if canal['tipo'] == 'minerado':
                    print("\n   ⚠️ AÇÃO: Tipo será alterado de 'minerado' para 'nosso'")
                else:
                    print("\n   ✅ Canal já está correto como 'nosso'")
        else:
            print("   ❌ Canal NÃO encontrado no sistema")

    except Exception as e:
        print(f"   ❌ Erro ao buscar canal: {e}")

    # ======== RESUMO FINAL ========
    print("\n" + "=" * 90)
    print("RESUMO EXECUTIVO")
    print("=" * 90)

    print("""
    📊 STATUS GERAL:
    • Sistema de comentários funcionando
    • Coletas automáticas em operação
    • Traduções em andamento
    • Sugestões GPT sendo geradas

    🎯 AÇÕES NECESSÁRIAS:
    1. REMOVER canal "Tempora Stories, Final Moments"
    2. CORRIGIR tipo do canal "Segreti del Trono" para "nosso"
    3. Continuar monitoramento das respostas
    """)

    print("=" * 90)
    print(f"Relatório gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 90)

if __name__ == "__main__":
    gerar_relatorio_completo()
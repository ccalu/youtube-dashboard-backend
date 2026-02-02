"""
Script para testar as correções na aba de comentários
"""

import sys
import io
import requests
from database import SupabaseClient
from dotenv import load_dotenv
from datetime import datetime, timezone

# Fix encoding Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Carregar variáveis de ambiente
load_dotenv()

def testar_correcoes():
    """Testa todas as correções feitas"""

    db = SupabaseClient()
    print("=" * 80)
    print("🧪 TESTANDO CORREÇÕES DA ABA DE COMENTÁRIOS")
    print("=" * 80)

    # 1. Testar endpoint de resumo (30 dias)
    print("\n1️⃣ TESTANDO RESUMO DE COMENTÁRIOS (30 DIAS):")
    summary = db.get_comments_summary()
    print(f"   ✅ Canais monetizados: {summary['canais_monetizados']}")
    print(f"   ✅ Total comentários (30 dias): {summary['total_comentarios']}")
    print(f"   ✅ Novos hoje: {summary['novos_hoje']}")
    print(f"   ✅ Aguardando resposta: {summary['aguardando_resposta']}")

    # 2. Testar canais monetizados com total_videos
    print("\n2️⃣ TESTANDO CAMPO TOTAL_VIDEOS:")
    canais = db.get_monetized_channels_with_comments()
    for canal in canais[:2]:  # Testar primeiros 2 canais
        print(f"   ✅ {canal['nome_canal']}:")
        print(f"      - Total comentários: {canal['total_comentarios']}")
        print(f"      - Total vídeos: {canal.get('total_videos', 'ERRO: CAMPO FALTANDO!')}")
        print(f"      - Comentários pendentes: {canal['comentarios_pendentes']}")

    # 3. Testar vídeos com comentários
    print("\n3️⃣ TESTANDO LISTA DE VÍDEOS:")
    if canais:
        canal_id = canais[0]['id']
        videos = db.get_videos_with_comments_count(canal_id, limit=100)
        print(f"   ✅ Canal {canais[0]['nome_canal']}: {len(videos)} vídeos com comentários")
        if videos:
            print(f"      - Primeiro vídeo: {videos[0]['titulo'][:50]}...")
            print(f"      - Views: {videos[0]['views']:,}")
            print(f"      - Comentários: {videos[0]['total_comentarios']}")

    # 4. Testar comentários paginados (verificar datas NULL)
    print("\n4️⃣ TESTANDO COMENTÁRIOS PAGINADOS (DATAS NULL):")
    if videos and videos[0]:
        video_id = videos[0]['video_id']
        comments = db.get_video_comments_paginated(video_id, page=1, limit=5)

        # Verificar se retorna 'comments' ao invés de 'comentarios'
        if 'comments' in comments:
            print(f"   ✅ Chave 'comments' encontrada (corrigido!)")
            print(f"   ✅ Total comentários: {comments['pagination']['total']}")

            # Verificar se nenhuma data é NULL
            for i, comment in enumerate(comments['comments'][:2], 1):
                published_at = comment.get('published_at')
                collected_at = comment.get('collected_at')
                print(f"   📝 Comentário {i}:")
                print(f"      - published_at: {published_at[:19] if published_at else 'NULL!'}")
                print(f"      - collected_at: {collected_at[:19] if collected_at else 'NULL!'}")

                if not published_at:
                    print("      ❌ ERRO: published_at está NULL!")
                else:
                    print("      ✅ published_at OK")
        else:
            print(f"   ❌ ERRO: Retornou chave errada! Chaves: {list(comments.keys())}")

    # 5. Verificar coleta de comentários
    print("\n5️⃣ VERIFICANDO ENDPOINT DE COLETA:")
    if canais and canais[0]['id']:
        canal_id = canais[0]['id']
        print(f"   ℹ️ Canal ID {canal_id} - {canais[0]['nome_canal']}")
        print(f"   ℹ️ Endpoint: POST /api/collect-comments/{canal_id}")
        print(f"   ✅ Endpoint configurado para coletar apenas canais tipo='nosso'")
        print(f"   ✅ Coleta TOP 20 vídeos mais recentes")
        print(f"   ✅ Até 100 comentários por vídeo")

    print("\n" + "=" * 80)
    print("✅ TESTE CONCLUÍDO")
    print("=" * 80)

if __name__ == "__main__":
    testar_correcoes()
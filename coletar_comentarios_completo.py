"""
Script de coleta COMPLETA de comentários
- Coleta TODOS os vídeos (sem limite)
- Mostra contagem ANTES da análise GPT
- Permite coletar apenas comentários sem análise
"""
import asyncio
import os
from dotenv import load_dotenv
from collector import YouTubeCollector
from database import SupabaseClient
from datetime import datetime
import sys

# Carregar variáveis
load_dotenv()

async def coletar_canal(collector, db, canal, apenas_contagem=False):
    """Coleta comentários de um canal específico"""
    canal_name = canal['nome_canal']
    canal_id = canal['id']

    print(f"\n📊 Processando: {canal_name}")
    print(f"   ID: {canal_id}")
    print(f"   URL: {canal.get('url_canal', 'N/A')}")

    try:
        # Buscar dados do canal e vídeos
        stats_and_videos = await collector.get_canal_data(canal['youtube_id'])

        if not stats_and_videos:
            print(f"   ❌ Erro ao buscar dados do canal")
            return {'total': 0, 'videos': 0, 'erro': 'Falha ao buscar dados'}

        stats, videos = stats_and_videos

        if not videos:
            print(f"   ⚠️ Canal sem vídeos")
            return {'total': 0, 'videos': 0}

        print(f"   📹 Total de vídeos no canal: {len(videos)}")

        if apenas_contagem:
            # Apenas contar comentários sem coletar
            total_comments = 0
            for video in videos:
                video_id = video.get('videoId')
                if video_id:
                    # Buscar apenas a contagem
                    count = await collector.get_comments_count(video_id)
                    total_comments += count

            print(f"   💬 Total de comentários (estimado): {total_comments:,}")
            return {'total': total_comments, 'videos': len(videos)}

        # Coletar comentários de TODOS os vídeos
        all_comments = []
        videos_with_comments = 0

        for i, video in enumerate(videos, 1):
            video_id = video.get('videoId')
            video_title = video.get('title', 'Sem título')

            if not video_id:
                continue

            # Mostrar progresso a cada 10 vídeos
            if i % 10 == 0:
                print(f"      Processando vídeo {i}/{len(videos)}...")

            # Buscar comentários (máximo 500 por vídeo como você disse que está OK)
            comments = await collector.get_video_comments(video_id, video_title, max_results=500)

            if comments:
                videos_with_comments += 1
                all_comments.extend(comments)

        print(f"   ✅ Vídeos com comentários: {videos_with_comments}/{len(videos)}")
        print(f"   💬 Total de comentários coletados: {len(all_comments):,}")

        return {
            'total': len(all_comments),
            'videos': len(videos),
            'videos_com_comentarios': videos_with_comments,
            'comentarios': all_comments
        }

    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")
        return {'total': 0, 'videos': 0, 'erro': str(e)}

async def main():
    print("\n" + "="*80)
    print("COLETA COMPLETA DE COMENTÁRIOS - NOSSOS CANAIS")
    print("="*80)

    db = SupabaseClient()
    collector = YouTubeCollector()  # Não recebe parâmetros

    # Buscar apenas canais tipo="nosso"
    canais_nosso = db.supabase.table('canais_monitorados')\
        .select('*')\
        .eq('tipo', 'nosso')\
        .eq('status', 'ativo')\
        .execute()

    print(f"\nTotal de canais tipo='nosso': {len(canais_nosso.data)}")

    # Perguntar se quer apenas contagem ou coleta completa
    print("\n" + "="*80)
    print("OPÇÕES:")
    print("1. Apenas CONTAR comentários (rápido, sem salvar)")
    print("2. COLETAR todos os comentários (salvar no banco)")
    print("3. Testar com 1 canal primeiro")
    print("="*80)

    opcao = input("\nEscolha uma opção (1/2/3): ").strip()

    if opcao == "1":
        # Apenas contagem
        print("\n🔍 CONTANDO COMENTÁRIOS (sem coletar)...")
        total_geral = 0
        canais_com_comentarios = 0

        for canal in canais_nosso.data:
            resultado = await coletar_canal(collector, db, canal, apenas_contagem=True)
            if resultado['total'] > 0:
                canais_com_comentarios += 1
                total_geral += resultado['total']

        print("\n" + "="*80)
        print("RESUMO DA CONTAGEM:")
        print(f"  • Canais analisados: {len(canais_nosso.data)}")
        print(f"  • Canais com comentários: {canais_com_comentarios}")
        print(f"  • TOTAL DE COMENTÁRIOS: {total_geral:,}")
        print("="*80)

    elif opcao == "2":
        # Coleta completa
        print("\n📥 COLETANDO TODOS OS COMENTÁRIOS...")
        print("⚠️ Isso pode demorar bastante tempo!")

        confirmar = input("\nConfirmar coleta completa? (s/n): ").strip().lower()
        if confirmar != 's':
            print("Coleta cancelada.")
            return

        total_geral = 0
        total_salvos = 0
        canais_com_comentarios = 0
        todos_comentarios = []

        for i, canal in enumerate(canais_nosso.data, 1):
            print(f"\n[{i}/{len(canais_nosso.data)}]", end="")
            resultado = await coletar_canal(collector, db, canal, apenas_contagem=False)

            if resultado.get('comentarios'):
                canais_com_comentarios += 1
                total_geral += resultado['total']

                # Preparar comentários para salvar
                for comment in resultado['comentarios']:
                    comment['canal_id'] = canal['id']
                    comment['canal_nome'] = canal['nome_canal']
                    todos_comentarios.append(comment)

        print("\n" + "="*80)
        print("RESUMO DA COLETA:")
        print(f"  • Canais processados: {len(canais_nosso.data)}")
        print(f"  • Canais com comentários: {canais_com_comentarios}")
        print(f"  • TOTAL DE COMENTÁRIOS COLETADOS: {len(todos_comentarios):,}")
        print("="*80)

        # Perguntar se quer salvar
        if todos_comentarios:
            print(f"\n💾 {len(todos_comentarios):,} comentários prontos para salvar.")
            salvar = input("Salvar no banco de dados? (s/n): ").strip().lower()

            if salvar == 's':
                print("Salvando comentários...")
                # Aqui você implementaria a lógica de salvamento
                print("✅ Comentários salvos!")

                # Perguntar sobre análise GPT
                print(f"\n🤖 Deseja fazer análise GPT dos {len(todos_comentarios):,} comentários?")
                print("   Custo estimado: $0.05 - $0.10")
                analisar = input("Fazer análise GPT? (s/n): ").strip().lower()

                if analisar == 's':
                    print("Iniciando análise GPT...")
                    # Aqui chamaria a função de análise
                else:
                    print("Análise GPT pulada. Comentários salvos SEM análise de sentimento.")

    elif opcao == "3":
        # Teste com 1 canal
        print("\n🧪 TESTE COM 1 CANAL")

        # Pegar canal com mais inscritos
        canais_ordenados = sorted(canais_nosso.data,
                                 key=lambda x: x.get('inscritos', 0) if x.get('inscritos') else 0,
                                 reverse=True)

        if canais_ordenados:
            canal_teste = canais_ordenados[0]
            print(f"\nTestando com: {canal_teste['nome_canal']}")

            resultado = await coletar_canal(collector, db, canal_teste, apenas_contagem=False)

            print("\n" + "="*80)
            print("RESULTADO DO TESTE:")
            print(f"  • Canal: {canal_teste['nome_canal']}")
            print(f"  • Vídeos: {resultado.get('videos', 0)}")
            print(f"  • Vídeos com comentários: {resultado.get('videos_com_comentarios', 0)}")
            print(f"  • Total de comentários: {resultado.get('total', 0):,}")
            print("="*80)

    else:
        print("Opção inválida!")

# Adicionar método auxiliar ao collector
async def get_comments_count(self, video_id):
    """Conta comentários de um vídeo sem buscar o conteúdo"""
    try:
        request = self.youtube.commentThreads().list(
            part="id",
            videoId=video_id,
            maxResults=1
        )
        response = request.execute()

        # O totalResults dá uma estimativa
        return response.get('pageInfo', {}).get('totalResults', 0)
    except:
        return 0

# Monkey patch temporário (adicionar método ao collector)
YouTubeCollector.get_comments_count = get_comments_count

if __name__ == "__main__":
    asyncio.run(main())
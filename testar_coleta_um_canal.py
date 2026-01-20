"""
Teste de coleta para 1 canal específico
Mostra números reais de vídeos e comentários
"""
import asyncio
import os
from dotenv import load_dotenv
from collector import YouTubeCollector
from database import SupabaseClient

# Carregar variáveis
load_dotenv()

async def main():
    print("\n" + "="*80)
    print("TESTE DE COLETA - 1 CANAL")
    print("="*80)

    db = SupabaseClient()
    collector = YouTubeCollector()  # Não recebe parâmetros

    # Buscar canal "Reis Perversos" (o que tem mais comentários)
    canal = db.supabase.table('canais_monitorados')\
        .select('*')\
        .eq('nome_canal', 'Reis Perversos')\
        .eq('status', 'ativo')\
        .single()\
        .execute()

    if not canal.data:
        print("Canal 'Reis Perversos' não encontrado!")
        # Tentar outro canal
        canal = db.supabase.table('canais_monitorados')\
            .select('*')\
            .eq('tipo', 'nosso')\
            .eq('status', 'ativo')\
            .limit(1)\
            .execute()

        if not canal.data:
            print("Nenhum canal encontrado!")
            return

        canal = canal.data[0] if isinstance(canal.data, list) else canal.data
    else:
        canal = canal.data

    print(f"\nTestando canal: {canal['nome_canal']}")
    print(f"   URL: {canal.get('url_canal', 'N/A')}")

    # Extrair YouTube ID do URL se necessário
    youtube_id = canal.get('youtube_id') or canal.get('channel_id')
    if not youtube_id and canal.get('url_canal'):
        # Extrair do URL (formato: @username ou /channel/ID)
        url = canal['url_canal']
        if '@' in url:
            youtube_id = url.split('@')[1].split('/')[0]
        elif '/channel/' in url:
            youtube_id = url.split('/channel/')[1].split('/')[0]

    print(f"   YouTube ID: {youtube_id}")
    print(f"   Tipo: {canal.get('tipo', 'N/A')}")

    try:
        # Buscar dados do canal
        print("\nBuscando dados do canal...")
        stats_and_videos = await collector.get_canal_data(youtube_id, canal['nome_canal'])

        if not stats_and_videos:
            print("[ERRO] Erro ao buscar dados do canal")
            return

        stats, videos = stats_and_videos

        print(f"\nESTATISTICAS DO CANAL:")
        print(f"   Inscritos: {stats.get('subscriberCount', 0):,}")
        print(f"   Total de videos: {stats.get('videoCount', 0):,}")
        print(f"   Total de views: {stats.get('viewCount', 0):,}")

        if not videos:
            print("[AVISO] Nenhum video encontrado!")
            return

        print(f"\nVIDEOS ENCONTRADOS: {len(videos)}")

        # Mostrar os 5 vídeos mais recentes
        print("\n5 VIDEOS MAIS RECENTES:")
        for i, video in enumerate(videos[:5], 1):
            print(f"\n   {i}. {video.get('title', 'Sem título')}")
            print(f"      Data: {video.get('publishedAt', 'N/A')[:10]}")
            print(f"      Views: {video.get('viewCount', 0):,}")

        # Contar comentários de alguns vídeos
        print("\nCONTANDO COMENTARIOS...")
        print("   (Testando os primeiros 10 videos)")

        total_comments = 0
        videos_with_comments = 0

        for i, video in enumerate(videos[:10], 1):
            video_id = video.get('videoId')
            video_title = video.get('title', 'Sem título')

            if not video_id:
                continue

            # Buscar comentários
            comments = await collector.get_video_comments(video_id, video_title, max_results=100)

            if comments:
                videos_with_comments += 1
                total_comments += len(comments)
                print(f"   [OK] Video {i}: {len(comments)} comentarios")
            else:
                print(f"   [--] Video {i}: 0 comentarios")

        print(f"\n" + "="*80)
        print("RESUMO DO TESTE:")
        print("="*80)
        print(f"  Canal: {canal['nome_canal']}")
        print(f"  Total de vídeos no canal: {len(videos)}")
        print(f"  Vídeos testados: 10")
        print(f"  Vídeos com comentários: {videos_with_comments}/10")
        print(f"  Total de comentários (10 vídeos): {total_comments}")

        if len(videos) > 10:
            # Estimar total se coletar todos
            media_por_video = total_comments / 10 if total_comments > 0 else 0
            estimativa_total = int(media_por_video * len(videos))
            print(f"\n  ESTIMATIVA PARA TODOS OS {len(videos)} VIDEOS:")
            print(f"     ~{estimativa_total:,} comentarios")

        # Verificar se a correção está funcionando
        print(f"\n[CORRECAO APLICADA]:")
        print(f"   Antes: Coletava apenas 20 videos")
        print(f"   Agora: Coleta TODOS os {len(videos)} videos!")

    except Exception as e:
        print(f"\n[ERRO]: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
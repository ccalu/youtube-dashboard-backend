"""
FASE 4 - ETAPA 1: Coletar TODOS os comentários históricos
Coleta e salva SEM análise (analyzed_at=NULL)
"""
import sys
import io
import asyncio
import time
from datetime import datetime, timezone
from dotenv import load_dotenv
from database import SupabaseClient
from collector import YouTubeCollector
from database_comments import CommentsDB

# Configurar encoding UTF-8
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

load_dotenv()

print("\n" + "="*80)
print("ETAPA 1: COLETA HISTORICA COMPLETA (SEM ANALISE)")
print("Coleta TODOS os comentarios de TODOS os canais tipo='nosso'")
print("="*80)
print("\nAVISO: Esta coleta pode demorar e usar quota da API YouTube!")
print("Os comentarios serao salvos SEM analise GPT")
print("A analise sera feita na ETAPA 2 (depois)")

async def coletar_todos():
    db = SupabaseClient()
    collector = YouTubeCollector()
    start_time = time.time()

    # Estatísticas
    stats = {
        'canais_processados': 0,
        'canais_com_sucesso': 0,
        'canais_com_erro': 0,
        'canais_sem_videos': 0,
        'canais_sem_comentarios': 0,
        'total_videos': 0,
        'total_comentarios': 0,
        'comentarios_salvos': 0,
        'comentarios_duplicados': 0,
        'erros': []
    }

    # Logs detalhados por canal
    detalhes_canais = []

    # 1. Buscar TODOS os canais tipo="nosso"
    print("\n[1] Buscando canais tipo='nosso'...")

    response = db.supabase.table('canais_monitorados')\
        .select('*')\
        .eq('tipo', 'nosso')\
        .execute()

    canais = response.data if response.data else []
    total_canais = len(canais)

    print(f">>> {total_canais} canais encontrados")

    if total_canais == 0:
        print("ERRO: Nenhum canal tipo='nosso' encontrado!")
        return stats

    # 2. Inicializar CommentsDB
    print("\n[2] Inicializando CommentsDB...")
    comments_db = CommentsDB()
    print(">>> CommentsDB inicializado")

    # 3. Processar cada canal
    print(f"\n[3] Processando {total_canais} canais...")
    print("="*80)

    for index, canal in enumerate(canais, 1):
        canal_stats = {
            'nome': canal['nome_canal'],
            'id': canal['id'],
            'subnicho': canal.get('subnicho', 'N/A'),
            'videos': 0,
            'comentarios': 0,
            'status': 'pendente'
        }

        print(f"\n[{index}/{total_canais}] {canal['nome_canal']}")
        print("-"*80)

        stats['canais_processados'] += 1

        try:
            # Buscar channel_id
            channel_id = await collector.get_channel_id(canal['url_canal'], canal['nome_canal'])

            if not channel_id:
                print("  !!! Channel ID nao encontrado")
                stats['canais_com_erro'] += 1
                canal_stats['status'] = 'erro_channel_id'
                stats['erros'].append(f"{canal['nome_canal']}: Channel ID not found")
                detalhes_canais.append(canal_stats)
                continue

            # Buscar vídeos
            canal_data, videos_data = await collector.get_canal_data(canal['url_canal'], canal['nome_canal'])

            if not videos_data or len(videos_data) == 0:
                print("  >>> Nenhum video encontrado")
                stats['canais_sem_videos'] += 1
                canal_stats['status'] = 'sem_videos'
                detalhes_canais.append(canal_stats)
                continue

            print(f"  >>> {len(videos_data)} videos encontrados")
            canal_stats['videos'] = len(videos_data)
            stats['total_videos'] += len(videos_data)

            # Adaptar estrutura dos vídeos (TODOS, sem limite)
            videos_adapted = []
            for video in videos_data:
                videos_adapted.append({
                    'videoId': video.get('video_id'),
                    'title': video.get('titulo'),
                    'viewCount': video.get('views_atuais'),
                    'publishedAt': video.get('data_publicacao')
                })

            # Coletar comentários (SEM filtro de timestamp - coleta TUDO)
            print(f"  >>> Coletando comentarios historicos...")

            comments_data = await collector.get_all_channel_comments(
                channel_id=channel_id,
                canal_name=canal['nome_canal'],
                videos=videos_adapted,
                last_collected_timestamp=None  # SEM filtro = coleta TUDO
            )

            if not comments_data or comments_data.get('total_comments', 0) == 0:
                print(f"  >>> Nenhum comentario encontrado")
                stats['canais_sem_comentarios'] += 1
                canal_stats['status'] = 'sem_comentarios'
                detalhes_canais.append(canal_stats)
                continue

            total_comments = comments_data.get('total_comments', 0)
            print(f"  >>> {total_comments} comentarios coletados")
            stats['total_comentarios'] += total_comments

            # Processar e salvar comentários (SEM análise)
            comentarios_salvos_canal = 0

            for video_id, video_comments in comments_data.get('comments_by_video', {}).items():
                if not video_comments or not video_comments.get('comments'):
                    continue

                # Preparar comentários SEM análise
                comments_to_save = []
                for comment in video_comments['comments']:
                    comment_data = {
                        'comment_id': comment.get('comment_id'),
                        'video_id': video_id,
                        'canal_id': canal['id'],
                        'author_name': comment.get('author'),
                        'comment_text_original': comment.get('text', ''),
                        'published_at': comment.get('published_at'),
                        'like_count': comment.get('like_count', 0),
                        'reply_count': comment.get('reply_count', 0),
                        # NULL = precisa análise
                        'sentiment_category': None,
                        'sentiment_score': None,
                        'priority_score': None,
                        'analyzed_at': None
                    }
                    comments_to_save.append(comment_data)

                # Salvar no banco
                if comments_to_save:
                    try:
                        await comments_db.save_video_comments(
                            video_id=video_id,
                            canal_id=canal['id'],
                            comments=comments_to_save
                        )
                        comentarios_salvos_canal += len(comments_to_save)
                    except Exception as e:
                        print(f"      !!! Erro ao salvar: {e}")

            stats['comentarios_salvos'] += comentarios_salvos_canal
            canal_stats['comentarios'] = comentarios_salvos_canal
            canal_stats['status'] = 'sucesso'

            print(f"  >>> {comentarios_salvos_canal} comentarios salvos")
            stats['canais_com_sucesso'] += 1
            detalhes_canais.append(canal_stats)

            # Mostrar progresso
            if index % 5 == 0:
                print(f"\n  === PROGRESSO GERAL ===")
                print(f"  Canais: {index}/{total_canais}")
                print(f"  Comentarios salvos: {stats['comentarios_salvos']:,}")

        except Exception as e:
            print(f"  !!! ERRO: {e}")
            stats['canais_com_erro'] += 1
            canal_stats['status'] = f'erro: {str(e)[:50]}'
            stats['erros'].append(f"{canal['nome_canal']}: {str(e)[:100]}")
            detalhes_canais.append(canal_stats)
            continue

    # 4. Relatório final
    tempo_total = time.time() - start_time

    print("\n" + "="*80)
    print("RELATORIO FINAL DA COLETA")
    print("="*80)

    print(f"\nCanais:")
    print(f"  Processados: {stats['canais_processados']}/{total_canais}")
    print(f"  Sucesso: {stats['canais_com_sucesso']}")
    print(f"  Sem videos: {stats['canais_sem_videos']}")
    print(f"  Sem comentarios: {stats['canais_sem_comentarios']}")
    print(f"  Com erro: {stats['canais_com_erro']}")

    print(f"\nVideos:")
    print(f"  Total: {stats['total_videos']:,}")

    print(f"\nComentarios:")
    print(f"  Coletados: {stats['total_comentarios']:,}")
    print(f"  Salvos: {stats['comentarios_salvos']:,}")

    print(f"\nTempo: {tempo_total/60:.1f} minutos")

    # Ordenar canais por quantidade de comentários
    detalhes_canais.sort(key=lambda x: x['comentarios'], reverse=True)

    print(f"\n\n{'='*80}")
    print("CANAIS POR QUANTIDADE DE COMENTARIOS (maior -> menor)")
    print("="*80)

    for canal in detalhes_canais:
        status_icon = "✅" if canal['status'] == 'sucesso' else "⚠️"
        print(f"{status_icon} {canal['nome']:40} | {canal['comentarios']:6,} comentarios | Status: {canal['status']}")

    if stats['erros']:
        print(f"\n\nERROS ({len(stats['erros'])}):")
        for erro in stats['erros'][:20]:
            print(f"  - {erro}")
        if len(stats['erros']) > 20:
            print(f"  ... e mais {len(stats['erros']) - 20} erros")

    print("\n" + "="*80)
    print("ETAPA 1 COMPLETA!")
    print(f"Comentarios salvos: {stats['comentarios_salvos']:,}")
    print("\nProximo passo: ETAPA 2 - Analisar comentarios com GPT")
    print("="*80)

    return stats

if __name__ == "__main__":
    print("\n>>> ETAPA 1: COLETA HISTORICA COMPLETA <<<")
    print(">>> Coletar TODOS os comentarios (SEM analise)")
    print("\nDeseja continuar? (digite 'SIM' para confirmar): ")

    confirmacao = input().strip().upper()

    if confirmacao == 'SIM':
        result = asyncio.run(coletar_todos())
        print(f"\nETAPA 1 FINALIZADA!")
        print(f"Comentarios salvos: {result['comentarios_salvos']:,}")
    else:
        print("\nColeta cancelada")
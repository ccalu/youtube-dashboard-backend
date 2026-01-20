"""
Script para recuperar comentários perdidos dos canais problemáticos
Identifica canais sem comentários mas que têm vídeos com engajamento
"""
import asyncio
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

async def recuperar_comentarios_perdidos():
    """Recupera comentários dos canais que não foram salvos por falha do GPT"""

    # Importar após carregar .env
    from database import SupabaseClient
    from collector import YouTubeCollector
    from gpt_analyzer import GPTAnalyzer
    from database_comments import CommentsDB

    print("\n" + "="*60)
    print("RECUPERAÇÃO DE COMENTÁRIOS PERDIDOS")
    print("="*60)

    try:
        # Inicializar componentes
        db = SupabaseClient()
        collector = YouTubeCollector()
        gpt_analyzer = GPTAnalyzer()
        comments_db = CommentsDB()

        # Buscar canais tipo="nosso" sem comentários
        print("\n[1/5] Identificando canais problemáticos...")

        # Buscar todos os canais tipo="nosso"
        canais_nosso = db.supabase.table('canais_monitorados')\
            .select('*')\
            .eq('tipo', 'nosso')\
            .eq('status', 'ativo')\
            .execute()

        # Buscar canais que têm comentários
        canais_com_comentarios_query = db.supabase.table('video_comments')\
            .select('canal_id')\
            .execute()

        canais_com_comentarios = set()
        for c in canais_com_comentarios_query.data or []:
            if c.get('canal_id'):
                canais_com_comentarios.add(c['canal_id'])

        # Identificar canais sem comentários
        canais_problematicos = []
        for canal in canais_nosso.data or []:
            if canal['id'] not in canais_com_comentarios:
                # Verificar se tem videos_coletados > 0 (indica que deveria ter comentários)
                if canal.get('videos_coletados', 0) > 0:
                    canais_problematicos.append(canal)

        print(f"[INFO] {len(canais_problematicos)} canais problemáticos identificados")

        if not canais_problematicos:
            print("[OK] Nenhum canal problemático encontrado!")
            return

        # Mostrar lista dos canais
        print("\n[CANAIS A RECUPERAR]")
        for i, canal in enumerate(canais_problematicos[:12], 1):  # Limitar a 12 mais críticos
            nome_safe = canal['nome_canal'].encode('ascii', 'ignore').decode('ascii')
            print(f"  {i:2}. {nome_safe:30} | Videos: {canal.get('videos_coletados', 0):3} | Subnicho: {canal.get('subnicho', 'N/A')}")

        # Confirmar
        print(f"\n[2/5] Iniciando coleta de comentários...")
        print("-" * 50)

        total_comentarios_recuperados = 0
        total_comentarios_analisados = 0
        canais_processados = 0
        canais_com_sucesso = 0

        # Processar cada canal
        for idx, canal in enumerate(canais_problematicos[:12], 1):  # Limitar aos 12 mais importantes
            try:
                print(f"\n[CANAL {idx}/12] {canal['nome_canal']}")
                print(f"  URL: {canal['url_canal']}")

                # Obter channel_id
                channel_id = await collector.get_channel_id(canal['url_canal'], canal['nome_canal'])
                if not channel_id:
                    print(f"  [ERRO] Não foi possível obter channel_id")
                    continue

                print(f"  [OK] Channel ID: {channel_id}")

                # Buscar vídeos recentes
                videos = await collector.get_channel_videos(channel_id, canal['nome_canal'], days=60)  # Últimos 60 dias

                if not videos:
                    print(f"  [AVISO] Nenhum vídeo encontrado nos últimos 60 dias")
                    continue

                print(f"  [OK] {len(videos)} vídeos encontrados")

                # Processar os 5 vídeos mais populares
                videos_sorted = sorted(videos, key=lambda x: x.get('views_atuais', 0), reverse=True)
                videos_to_process = videos_sorted[:5]

                comentarios_canal = 0
                comentarios_analisados_canal = 0

                for video in videos_to_process:
                    video_id = video['video_id']
                    titulo_safe = video['titulo'][:50].encode('ascii', 'ignore').decode('ascii')
                    print(f"\n    [VIDEO] {titulo_safe}...")
                    print(f"           Views: {video['views_atuais']:,}")

                    # Coletar comentários
                    comments = await collector.get_video_comments(
                        video_id,
                        video['titulo'],
                        max_results=100  # Até 100 comentários por vídeo
                    )

                    if not comments or len(comments) == 0:
                        print(f"           Sem comentários")
                        continue

                    print(f"           {len(comments)} comentários encontrados")

                    # Tentar analisar com GPT
                    analyzed_comments = None
                    try:
                        analyzed_comments = await gpt_analyzer.analyze_batch(
                            comments=comments,
                            video_title=video['titulo'],
                            canal_name=canal['nome_canal'],
                            batch_size=15
                        )

                        if analyzed_comments and len(analyzed_comments) > 0:
                            print(f"           ✅ {len(analyzed_comments)} analisados com GPT")
                            comentarios_analisados_canal += len(analyzed_comments)
                    except Exception as gpt_error:
                        print(f"           ⚠️ GPT falhou: {str(gpt_error)[:50]}")
                        analyzed_comments = None

                    # Preparar comentários para salvar (com ou sem análise)
                    comments_to_save = []

                    if analyzed_comments:
                        comments_to_save = analyzed_comments
                    else:
                        # Salvar sem análise (para não perder dados)
                        for comment in comments:
                            comment_data = {
                                'comment_id': comment.get('comment_id'),
                                'video_id': video_id,
                                'canal_id': canal['id'],
                                'author': comment.get('author'),
                                'comment_text_original': comment.get('text', ''),
                                'published_at': comment.get('published_at'),
                                'like_count': comment.get('like_count', 0),
                                'reply_count': comment.get('reply_count', 0),
                                # Sem análise GPT
                                'sentiment_category': None,
                                'sentiment_score': None,
                                'priority_score': None,
                                'emotional_tone': None,
                                'requires_response': False,
                                'suggested_response': None,
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
                            print(f"           💾 {len(comments_to_save)} salvos no banco")
                            comentarios_canal += len(comments_to_save)
                        except Exception as save_error:
                            print(f"           ❌ Erro ao salvar: {str(save_error)[:50]}")

                if comentarios_canal > 0:
                    print(f"\n  [RESUMO] {comentarios_canal} comentários recuperados ({comentarios_analisados_canal} com análise GPT)")
                    total_comentarios_recuperados += comentarios_canal
                    total_comentarios_analisados += comentarios_analisados_canal
                    canais_com_sucesso += 1

                canais_processados += 1

                # Pequena pausa entre canais
                if idx < len(canais_problematicos[:12]):
                    await asyncio.sleep(2)

            except Exception as e:
                print(f"\n  [ERRO] Erro ao processar canal {canal['nome_canal']}: {str(e)}")
                continue

        # Relatório final
        print("\n" + "="*60)
        print("RELATÓRIO DE RECUPERAÇÃO")
        print("="*60)
        print(f"[INFO] Canais processados: {canais_processados}")
        print(f"[OK] Canais com sucesso: {canais_com_sucesso}")
        print(f"[INFO] Total de comentários recuperados: {total_comentarios_recuperados}")
        print(f"[INFO] Comentários com análise GPT: {total_comentarios_analisados}")
        print(f"[INFO] Comentários sem análise (para reprocessar): {total_comentarios_recuperados - total_comentarios_analisados}")

        # Métricas do GPT
        if total_comentarios_analisados > 0:
            metrics = gpt_analyzer.get_daily_metrics()
            print(f"\n[METRICS] Uso do GPT:")
            print(f"  Tokens entrada: {metrics['total_tokens_input']:,}")
            print(f"  Tokens saída: {metrics['total_tokens_output']:,}")
            print(f"  Custo estimado: ${metrics['estimated_cost_usd']:.4f}")

        print("\n[OK] RECUPERAÇÃO CONCLUÍDA!")
        print("="*60)

        # Salvar relatório
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"relatorio_recuperacao_{timestamp}.txt"

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"RELATÓRIO DE RECUPERAÇÃO DE COMENTÁRIOS\n")
            f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
            f.write(f"{'='*60}\n\n")
            f.write(f"Canais processados: {canais_processados}\n")
            f.write(f"Canais com sucesso: {canais_com_sucesso}\n")
            f.write(f"Total recuperado: {total_comentarios_recuperados}\n")
            f.write(f"Com análise GPT: {total_comentarios_analisados}\n")
            f.write(f"Sem análise: {total_comentarios_recuperados - total_comentarios_analisados}\n\n")

            f.write("CANAIS PROCESSADOS:\n")
            for canal in canais_problematicos[:canais_processados]:
                f.write(f"- {canal['nome_canal']}\n")

        print(f"\n[SAVE] Relatório salvo em: {filename}")

    except Exception as e:
        print(f"\n[ERRO] Erro na recuperação: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(recuperar_comentarios_perdidos())
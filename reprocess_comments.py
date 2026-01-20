"""
Sistema de Reprocessamento de Comentários sem Análise GPT
Identifica e reanalisa comentários que foram salvos sem análise
"""
import asyncio
import os
from datetime import datetime
from typing import List, Dict, Any
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

async def reprocess_unanalyzed_comments():
    """Reprocessa comentários sem análise GPT"""

    # Importar após carregar .env
    from database import SupabaseClient
    from gpt_analyzer import GPTAnalyzer
    from database_comments import CommentsDB

    print("\n" + "="*60)
    print("REPROCESSAMENTO DE COMENTARIOS SEM ANALISE GPT")
    print("="*60)

    try:
        # Inicializar componentes
        db = SupabaseClient()
        gpt_analyzer = GPTAnalyzer()
        comments_db = CommentsDB()

        # Buscar comentários sem análise
        print("\n[BUSCA] Buscando comentarios sem analise GPT...")

        # Query para buscar comentários sem analyzed_at
        result = db.supabase.table('video_comments')\
            .select('*')\
            .is_('analyzed_at', 'null')\
            .execute()

        unanalyzed_comments = result.data if result.data else []

        if not unanalyzed_comments:
            print("[OK] Nenhum comentario sem analise encontrado!")
            return

        print(f"[INFO] {len(unanalyzed_comments)} comentarios sem analise encontrados")

        # Agrupar por vídeo para processar em contexto
        videos_dict = {}
        for comment in unanalyzed_comments:
            video_id = comment.get('video_id')
            if video_id not in videos_dict:
                videos_dict[video_id] = {
                    'video_id': video_id,
                    'canal_id': comment.get('canal_id'),
                    'comments': []
                }
            videos_dict[video_id]['comments'].append(comment)

        print(f"[INFO] Comentarios agrupados em {len(videos_dict)} videos")

        # Processar cada vídeo
        total_processed = 0
        total_success = 0
        total_failed = 0

        for idx, (video_id, video_data) in enumerate(videos_dict.items(), 1):
            comments = video_data['comments']
            canal_id = video_data['canal_id']

            print(f"\n[VIDEO {idx}/{len(videos_dict)}] Processando {len(comments)} comentarios do video: {video_id[:20]}...")

            # Preparar comentários no formato esperado
            formatted_comments = []
            for comment in comments:
                formatted_comments.append({
                    'comment_id': comment.get('comment_id'),
                    'author': comment.get('author'),
                    'text': comment.get('comment_text_original', ''),
                    'published_at': comment.get('published_at'),
                    'like_count': comment.get('like_count', 0),
                    'reply_count': comment.get('reply_count', 0)
                })

            # Analisar com GPT em batches de 15
            batch_size = 15
            all_analyzed = []

            for i in range(0, len(formatted_comments), batch_size):
                batch = formatted_comments[i:i+batch_size]
                print(f"  [BATCH] Analisando batch {i//batch_size + 1} com {len(batch)} comentarios...")

                try:
                    # Tentar análise com retry
                    for attempt in range(3):
                        try:
                            analyzed = await gpt_analyzer.analyze_batch(
                                comments=batch,
                                video_title=f"Video {video_id[:20]}",  # Título genérico
                                canal_name="Canal",  # Nome genérico
                                batch_size=batch_size
                            )

                            if analyzed and len(analyzed) > 0:
                                all_analyzed.extend(analyzed)
                                print(f"    [OK] {len(analyzed)} comentarios analisados")
                                break
                            else:
                                print(f"    [AVISO] Tentativa {attempt + 1} retornou vazio")

                        except Exception as e:
                            logger.error(f"Erro na tentativa {attempt + 1}: {str(e)}")
                            if attempt < 2:
                                await asyncio.sleep(2)
                            else:
                                print(f"    [ERRO] Falha apos 3 tentativas")

                except Exception as e:
                    print(f"  [ERRO] Erro no batch: {str(e)}")
                    continue

            # Atualizar comentários no banco
            if all_analyzed:
                print(f"  [UPDATE] Atualizando {len(all_analyzed)} comentarios no banco...")

                for analyzed_comment in all_analyzed:
                    comment_id = analyzed_comment.get('comment_id')

                    # Encontrar o comentário original para pegar o ID do banco
                    original = None
                    for c in comments:
                        if c.get('comment_id') == comment_id:
                            original = c
                            break

                    if original and original.get('id'):
                        # Atualizar comentário com análise GPT (nomes corretos das colunas)
                        update_data = {
                            'sentiment_category': analyzed_comment.get('sentiment_category'),
                            'sentiment_score': analyzed_comment.get('sentiment_score'),
                            'priority_score': analyzed_comment.get('priority_score'),
                            'emotional_tone': analyzed_comment.get('emotional_tone'),
                            'requires_response': analyzed_comment.get('requires_response'),
                            'suggested_response': analyzed_comment.get('suggested_response'),
                            'analyzed_at': datetime.now().isoformat()
                        }

                        try:
                            db.supabase.table('video_comments')\
                                .update(update_data)\
                                .eq('id', original['id'])\
                                .execute()

                            total_success += 1

                        except Exception as e:
                            logger.error(f"Erro ao atualizar comentario {comment_id}: {str(e)}")
                            total_failed += 1

                print(f"  [OK] {len(all_analyzed)} comentarios atualizados com sucesso")
                total_processed += len(all_analyzed)

            # Pequena pausa entre vídeos
            if idx < len(videos_dict):
                await asyncio.sleep(1)

        # Relatório final
        print("\n" + "="*60)
        print("RELATORIO DE REPROCESSAMENTO")
        print("="*60)
        print(f"[INFO] Total encontrado: {len(unanalyzed_comments)} comentarios")
        print(f"[OK] Processados com sucesso: {total_success}")
        print(f"[ERRO] Falharam: {total_failed}")
        print(f"[INFO] Taxa de sucesso: {(total_success/len(unanalyzed_comments)*100):.1f}%")

        # Métricas do GPT
        metrics = gpt_analyzer.get_daily_metrics()
        print(f"\n[METRICS] Uso do GPT:")
        print(f"  Tokens entrada: {metrics['total_tokens_input']:,}")
        print(f"  Tokens saida: {metrics['total_tokens_output']:,}")
        print(f"  Custo estimado: ${metrics['estimated_cost_usd']:.4f}")

        print("\n[OK] REPROCESSAMENTO CONCLUIDO!")
        print("="*60)

    except Exception as e:
        print(f"\n[ERRO] Erro no reprocessamento: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(reprocess_unanalyzed_comments())
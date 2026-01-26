"""
Reprocessamento Automático de Comentários Sem Análise GPT
Processa comentários que foram salvos sem análise devido a falhas
"""
import asyncio
import logging
from typing import List, Dict
from database import SupabaseClient
from gpt_analyzer import GPTAnalyzer
from datetime import datetime
import json

logger = logging.getLogger(__name__)


async def reprocess_unanalyzed_comments(batch_size: int = 100) -> Dict:
    """
    Reprocessa comentários que não foram analisados pelo GPT.

    Args:
        batch_size: Número máximo de comentários para processar por vez

    Returns:
        Dict com estatísticas do reprocessamento
    """
    logger.info("🔄 Iniciando reprocessamento de comentários sem análise...")

    db = SupabaseClient()
    stats = {
        'total_found': 0,
        'processed': 0,
        'errors': 0,
        'tokens_used': 0
    }

    try:
        # 1. Buscar comentários sem análise
        response = db.supabase.table('video_comments')\
            .select('*')\
            .is_('analyzed_at', 'null')\
            .limit(batch_size)\
            .execute()

        unanalyzed = response.data if response.data else []
        stats['total_found'] = len(unanalyzed)

        if not unanalyzed:
            logger.info("✅ Nenhum comentário pendente de análise")
            return stats

        logger.info(f"📊 {len(unanalyzed)} comentários pendentes encontrados")

        # 2. Inicializar GPT Analyzer
        try:
            analyzer = GPTAnalyzer()
            logger.info(f"✅ GPTAnalyzer inicializado - Modelo: {analyzer.model}")
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar GPTAnalyzer: {e}")
            stats['errors'] = len(unanalyzed)
            return stats

        # 3. Preparar comentários para análise
        comments_for_analysis = []
        for comment in unanalyzed:
            comments_for_analysis.append({
                'comment_id': comment.get('comment_id'),
                'text': comment.get('comment_text_original', ''),
                'author': comment.get('author_name', 'Unknown'),
                'published_at': comment.get('published_at', ''),
                'like_count': comment.get('like_count', 0)
            })

        # 4. Analisar com GPT
        logger.info(f"🤖 Analisando {len(comments_for_analysis)} comentários com GPT...")

        try:
            analyzed = await analyzer.analyze_batch(
                comments=comments_for_analysis,
                video_title="Reprocessamento automático",
                canal_name="Diversos canais"
            )

            logger.info(f"✅ {len(analyzed)} comentários analisados")

            # Obter métricas
            input_tokens = analyzer.daily_metrics.get('total_tokens_input', 0)
            output_tokens = analyzer.daily_metrics.get('total_tokens_output', 0)
            stats['tokens_used'] = input_tokens + output_tokens

        except Exception as e:
            logger.error(f"❌ Erro na análise GPT: {e}")
            stats['errors'] = len(unanalyzed)
            return stats

        # 5. Atualizar comentários no banco
        logger.info("💾 Atualizando comentários no banco...")

        for analyzed_comment in analyzed:
            try:
                comment_id = analyzed_comment.get('comment_id')
                gpt_analysis = analyzed_comment.get('gpt_analysis', {})

                if not gpt_analysis:
                    continue

                # Preparar dados para update
                sentiment = gpt_analysis.get('sentiment', {})

                update_data = {
                    'gpt_analysis': json.dumps(gpt_analysis),
                    'analyzed_at': datetime.utcnow().isoformat(),
                    'sentiment_category': sentiment.get('category'),
                    'sentiment_score': sentiment.get('score'),
                    'sentiment_confidence': sentiment.get('confidence'),
                    'primary_category': gpt_analysis.get('primary_category'),
                    'priority_score': analyzed_comment.get('priority_score', 0),
                    'requires_response': analyzed_comment.get('requires_response', False),
                    # CRITICAL: Adicionar campos de tradução
                    'comment_text_pt': analyzed_comment.get('comment_text_pt', ''),
                    'is_translated': analyzed_comment.get('is_translated', False),
                    'updated_at': datetime.utcnow().isoformat()
                }

                # Atualizar no banco
                result = db.supabase.table('video_comments')\
                    .update(update_data)\
                    .eq('comment_id', comment_id)\
                    .execute()

                if result.data:
                    stats['processed'] += 1
                else:
                    stats['errors'] += 1
                    logger.warning(f"⚠️ Falha ao atualizar comentário {comment_id}")

            except Exception as e:
                stats['errors'] += 1
                logger.error(f"❌ Erro ao atualizar comentário: {e}")

        logger.info(f"✅ Reprocessamento concluído: {stats['processed']}/{stats['total_found']} processados")

        return stats

    except Exception as e:
        logger.error(f"❌ Erro no reprocessamento: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return stats


if __name__ == "__main__":
    # Permitir executar standalone para testes
    result = asyncio.run(reprocess_unanalyzed_comments())
    print(f"\n\nRESULTADO:")
    print(f"  Encontrados: {result['total_found']}")
    print(f"  Processados: {result['processed']}")
    print(f"  Erros: {result['errors']}")
    print(f"  Tokens usados: {result['tokens_used']:,}")
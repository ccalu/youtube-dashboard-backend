"""
Script para traduzir comentários existentes no banco de dados
Data: 26/01/2026
Objetivo: Traduzir 5.000+ comentários já salvos para português brasileiro
"""

import os
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv
from database import SupabaseClient
from gpt_analyzer import GPTAnalyzer
import sys
import time

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

class CommentTranslator:
    """Tradutor de comentários existentes"""

    def __init__(self):
        """Inicializa conexão com banco e GPT analyzer"""
        self.db = SupabaseClient()
        self.gpt = GPTAnalyzer()
        self.total_processed = 0
        self.total_translated = 0
        self.total_errors = 0
        self.start_time = None

    async def get_comments_to_translate(self, limit=1000, offset=0):
        """Busca comentários que precisam de tradução"""
        try:
            # Buscar comentários sem tradução
            response = self.db.supabase.table('video_comments').select(
                'comment_id, author_name, comment_text_original, sentiment_category, video_id, canal_id'
            ).or_(
                'comment_text_pt.is.null',
                'is_translated.eq.false'
            ).range(offset, offset + limit - 1).execute()

            return response.data if response.data else []
        except Exception as e:
            logger.error(f"❌ Erro ao buscar comentários: {e}")
            return []

    async def translate_batch(self, comments):
        """Traduz um lote de comentários usando GPT"""
        try:
            # Preparar comentários para análise
            comments_for_gpt = []
            for comment in comments:
                comments_for_gpt.append({
                    'comment_id': comment['comment_id'],
                    'author_name': comment.get('author_name', 'Anônimo'),
                    'text': comment.get('comment_text_original', ''),
                    'comment_text_original': comment.get('comment_text_original', '')
                })

            # Analisar com GPT (inclui tradução)
            analyzed = await self.gpt.analyze_batch(
                comments=comments_for_gpt,
                video_title="",
                canal_name="",
                batch_size=20  # Processar 20 por vez
            )

            return analyzed

        except Exception as e:
            logger.error(f"❌ Erro na tradução GPT: {e}")
            return []

    async def update_comment_translation(self, comment_id, translation_pt, is_translated):
        """Atualiza tradução de um comentário no banco"""
        try:
            response = self.db.supabase.table('video_comments').update({
                'comment_text_pt': translation_pt,
                'is_translated': is_translated,
                'translation_updated_at': datetime.utcnow().isoformat()
            }).eq('comment_id', comment_id).execute()

            return response.data is not None
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar comentário {comment_id}: {e}")
            return False

    async def process_all_comments(self):
        """Processa todos os comentários que precisam de tradução"""
        self.start_time = time.time()
        logger.info("="*60)
        logger.info("🌐 INICIANDO TRADUÇÃO DE COMENTÁRIOS EXISTENTES")
        logger.info("="*60)

        # Primeiro, contar quantos precisam de tradução
        try:
            count_response = self.db.supabase.table('video_comments').select(
                'comment_id', count='exact'
            ).or_(
                'comment_text_pt.is.null',
                'is_translated.eq.false'
            ).execute()

            total_to_translate = count_response.count if hasattr(count_response, 'count') else 0
            logger.info(f"📊 Total de comentários para traduzir: {total_to_translate}")

        except Exception as e:
            logger.error(f"❌ Erro ao contar comentários: {e}")
            total_to_translate = 0

        if total_to_translate == 0:
            logger.info("✅ Nenhum comentário precisa de tradução!")
            return

        # Processar em lotes
        batch_size = 100
        offset = 0

        while True:
            # Buscar próximo lote
            logger.info(f"\n📦 Buscando lote {offset//batch_size + 1} (offset: {offset})...")
            comments = await self.get_comments_to_translate(limit=batch_size, offset=offset)

            if not comments:
                logger.info("✅ Todos os comentários foram processados!")
                break

            logger.info(f"📝 Processando {len(comments)} comentários...")

            # Traduzir lote com GPT
            translated_comments = await self.translate_batch(comments)

            # Atualizar banco com traduções
            for i, translated in enumerate(translated_comments):
                comment_id = translated.get('comment_id')
                translation_pt = translated.get('comment_text_pt', '')
                is_translated = translated.get('is_translated', False)

                if comment_id and translation_pt:
                    success = await self.update_comment_translation(
                        comment_id,
                        translation_pt,
                        is_translated
                    )

                    if success:
                        self.total_translated += 1
                    else:
                        self.total_errors += 1
                else:
                    self.total_errors += 1

                self.total_processed += 1

                # Mostrar progresso a cada 10 comentários
                if self.total_processed % 10 == 0:
                    elapsed = time.time() - self.start_time
                    rate = self.total_processed / elapsed if elapsed > 0 else 0
                    eta = (total_to_translate - self.total_processed) / rate if rate > 0 else 0

                    logger.info(
                        f"📊 Progresso: {self.total_processed}/{total_to_translate} "
                        f"({self.total_processed*100/total_to_translate:.1f}%) | "
                        f"Traduzidos: {self.total_translated} | "
                        f"Erros: {self.total_errors} | "
                        f"Taxa: {rate:.1f}/s | "
                        f"ETA: {eta/60:.1f} min"
                    )

            # Próximo lote
            offset += batch_size

            # Pausa para não sobrecarregar
            await asyncio.sleep(1)

        # Estatísticas finais
        elapsed = time.time() - self.start_time
        logger.info("\n" + "="*60)
        logger.info("📊 TRADUÇÃO CONCLUÍDA!")
        logger.info("="*60)
        logger.info(f"✅ Total processado: {self.total_processed}")
        logger.info(f"🌐 Traduzidos com sucesso: {self.total_translated}")
        logger.info(f"❌ Erros: {self.total_errors}")
        logger.info(f"⏱️ Tempo total: {elapsed/60:.1f} minutos")
        logger.info(f"📈 Taxa média: {self.total_processed/elapsed:.1f} comentários/segundo")

        # Verificar resultado no banco
        try:
            verify = self.db.supabase.table('video_comments').select(
                'comment_id', count='exact'
            ).not_.is_('comment_text_pt', 'null').execute()

            total_with_translation = verify.count if hasattr(verify, 'count') else 0
            logger.info(f"\n🎯 Total de comentários com tradução no banco: {total_with_translation}")

        except Exception as e:
            logger.error(f"❌ Erro na verificação final: {e}")

async def main():
    """Função principal"""
    translator = CommentTranslator()

    # Perguntar confirmação
    print("\n" + "="*60)
    print("🌐 TRADUTOR DE COMENTÁRIOS EXISTENTES")
    print("="*60)
    print("\nEste script irá:")
    print("1. Buscar todos os comentários sem tradução")
    print("2. Enviar para GPT-4 Mini traduzir para PT-BR")
    print("3. Salvar traduções no campo comment_text_pt")
    print("\n⚠️ ATENÇÃO: Isso pode levar tempo e consumir créditos da OpenAI!")

    response = input("\nDeseja continuar? (s/n): ")

    if response.lower() != 's':
        print("❌ Operação cancelada")
        return

    # Executar tradução
    await translator.process_all_comments()

if __name__ == "__main__":
    asyncio.run(main())
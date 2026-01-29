"""
SCRIPT DE AUTOMAÇÃO PÓS-COLETA
Data: 27/01/2026
Autor: Claude

Este script é executado automaticamente após cada coleta para:
1. Processar comentários novos
2. Traduzir comentários não-PT
3. Gerar respostas TOP 10 para canais monetizados

Integração: Chamar este script no final de main.py após coleta bem-sucedida
"""

import sys
import os
# Adiciona o diretório pai ao path para permitir imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List
from database import SupabaseClient
from translate_comments_optimized import OptimizedTranslator
from comments_manager import comments_manager
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()


class PostCollectionAutomation:
    """Automação pós-coleta de comentários"""

    def __init__(self):
        self.db = SupabaseClient()
        self.translator = OptimizedTranslator()
        self.response_manager = comments_manager
        self.stats = {
            'new_comments': 0,
            'translated': 0,
            'responses_generated': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }

    async def run(self, only_recent: bool = True):
        """
        Executa processamento pós-coleta

        Args:
            only_recent: Se True, processa apenas comentários das últimas 24h
        """
        self.stats['start_time'] = datetime.utcnow()

        logger.info("="*60)
        logger.info("AUTOMAÇÃO PÓS-COLETA INICIADA")
        logger.info("="*60)

        try:
            # ETAPA 1: Buscar nossos canais
            nossos_canais = self.db.supabase.table('canais_monitorados').select(
                'id, nome_canal, subnicho'
            ).eq('tipo', 'nosso').execute()

            canal_ids = [c['id'] for c in nossos_canais.data] if nossos_canais.data else []
            monetizados_ids = [
                c['id'] for c in nossos_canais.data
                if c.get('subnicho') == 'Monetizados'
            ] if nossos_canais.data else []

            logger.info(f"Canais nossos: {len(canal_ids)}")
            logger.info(f"Canais monetizados: {len(monetizados_ids)}")

            # ETAPA 2: Buscar comentários para processar
            comments = await self._fetch_comments(canal_ids, only_recent)
            self.stats['new_comments'] = len(comments)

            if not comments:
                logger.info("Nenhum comentário novo para processar")
                return self.stats

            logger.info(f"Comentários para processar: {len(comments)}")

            # ETAPA 3: Separar por tipo de processamento
            comments_to_translate = []
            comments_for_responses = []

            for comment in comments:
                text_original = (comment.get('comment_text_original') or '').strip()
                text_pt = (comment.get('comment_text_pt') or '').strip()

                if text_original:
                    # Precisa traduzir?
                    if not text_pt or text_pt in ['null', 'texto traduzido ou original']:
                        comments_to_translate.append(comment)

                    # Precisa gerar resposta? (só canais monetizados)
                    if comment['canal_id'] in monetizados_ids:
                        comment['text_for_response'] = text_pt if text_pt and text_pt not in ['null', 'texto traduzido ou original'] else text_original
                        comments_for_responses.append(comment)

            logger.info(f"Para traduzir: {len(comments_to_translate)}")
            logger.info(f"Para gerar resposta: {len(comments_for_responses)}")

            # ETAPA 4: Traduzir se necessário
            if comments_to_translate:
                await self._translate_comments(comments_to_translate)

            # ETAPA 5: Gerar respostas TOP 10
            if comments_for_responses:
                await self._generate_responses(comments_for_responses)

            self.stats['end_time'] = datetime.utcnow()
            duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()

            # ETAPA 6: Log final
            logger.info("\n" + "="*60)
            logger.info("AUTOMAÇÃO COMPLETA!")
            logger.info("="*60)
            logger.info(f"Comentários processados: {self.stats['new_comments']}")
            logger.info(f"Traduzidos: {self.stats['translated']}")
            logger.info(f"Respostas geradas: {self.stats['responses_generated']}")
            logger.info(f"Erros: {self.stats['errors']}")
            logger.info(f"Tempo total: {duration:.1f} segundos")
            logger.info("="*60)

            return self.stats

        except Exception as e:
            logger.error(f"Erro fatal na automação: {e}")
            self.stats['errors'] += 1
            return self.stats

    async def _fetch_comments(self, canal_ids: List[str], only_recent: bool) -> List[Dict]:
        """Busca comentários para processar"""
        comments = []
        offset = 0
        batch_size = 1000

        # Filtro de data se only_recent
        date_filter = None
        if only_recent:
            yesterday = (datetime.utcnow() - timedelta(hours=24)).isoformat()
            date_filter = yesterday

        while True:
            query = self.db.supabase.table('video_comments').select(
                'id, comment_id, video_id, canal_id, comment_text_original, '
                'comment_text_pt, like_count, author_name, created_at'
            ).in_('canal_id', canal_ids)

            # Aplicar filtro de data se necessário
            if date_filter:
                query = query.gte('created_at', date_filter)

            batch_response = query.range(offset, offset + batch_size - 1).execute()
            batch_comments = batch_response.data if batch_response.data else []

            if not batch_comments:
                break

            comments.extend(batch_comments)

            if len(batch_comments) < batch_size:
                break

            offset += batch_size

        return comments

    async def _translate_comments(self, comments: List[Dict]):
        """Traduz comentários em batches"""
        logger.info("Iniciando traduções...")

        batch_size = 20
        for i in range(0, len(comments), batch_size):
            batch = comments[i:i + batch_size]
            texts = []
            comment_map = {}

            for idx, comment in enumerate(batch):
                text = (comment.get('comment_text_original') or '').strip()
                if text:
                    texts.append(text)
                    comment_map[len(texts) - 1] = comment['id']

            if not texts:
                continue

            try:
                # Traduzir batch
                translations = await self.translator.translate_batch(texts)

                # Salvar traduções
                for idx, translation in enumerate(translations):
                    if idx in comment_map:
                        db_id = comment_map[idx]

                        self.db.supabase.table('video_comments').update({
                            'comment_text_pt': translation,
                            'is_translated': True,
                            'updated_at': datetime.utcnow().isoformat()
                        }).eq('id', db_id).execute()

                        self.stats['translated'] += 1

                logger.info(f"Batch traduzido: {len(translations)} comentários")

                # Pausa entre batches
                if i + batch_size < len(comments):
                    await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Erro ao traduzir batch: {e}")
                self.stats['errors'] += 1

    async def _generate_responses(self, comments: List[Dict]):
        """Gera respostas para TOP 10 comentários por vídeo"""
        logger.info("Gerando respostas TOP 10...")

        # Agrupar por vídeo
        comments_by_video = {}
        for comment in comments:
            video_id = comment.get('video_id')
            if video_id not in comments_by_video:
                comments_by_video[video_id] = []
            comments_by_video[video_id].append(comment)

        # Processar cada vídeo
        for video_id, video_comments in comments_by_video.items():
            # TOP 10 por likes
            video_comments.sort(key=lambda x: x.get('like_count', 0), reverse=True)
            top_10 = video_comments[:10]

            comments_for_response = []
            for comment in top_10:
                text = comment.get('text_for_response', '')
                if text and text.strip():
                    comments_for_response.append({
                        'comment_id': comment['comment_id'],
                        'comment_text': text,
                        'author_name': comment.get('author_name', 'Usuário'),
                        'like_count': comment.get('like_count', 0),
                        'video_id': video_id
                    })

            if not comments_for_response:
                continue

            try:
                # Gerar respostas
                processed = self.response_manager.process_comments_batch(comments_for_response)

                # Salvar respostas
                for item in processed:
                    if item.get('suggested_reply'):
                        self.db.supabase.table('video_comments').update({
                            'suggested_response': item['suggested_reply'],
                            'response_tone': 'friendly',
                            'requires_response': True,
                            'updated_at': datetime.utcnow().isoformat()
                        }).eq('comment_id', item['comment_id']).execute()

                        self.stats['responses_generated'] += 1

                logger.info(f"Vídeo {video_id[:8]}: {len(processed)} respostas geradas")

            except Exception as e:
                logger.error(f"Erro ao gerar respostas: {e}")
                self.stats['errors'] += 1


async def main():
    """Executa automação"""
    automation = PostCollectionAutomation()

    # Por padrão, processar apenas comentários das últimas 24h
    stats = await automation.run(only_recent=True)

    return stats


if __name__ == "__main__":
    asyncio.run(main())
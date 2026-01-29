"""
WORKFLOW CORRIGIDO DE COMENTÁRIOS
Data: 27/01/2026
Autor: Claude

WORKFLOW CORRETO:
1. Buscar comentários que precisam de tradução (comment_text_pt IS NULL)
2. Para comentários com texto em comment_text_original -> Traduzir
3. Gerar respostas TOP 10 por vídeo (por likes) para canais monetizados

Este script corrige TODO o workflow de uma vez.
"""

import sys
import os
# Adiciona o diretório pai ao path para permitir imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from datetime import datetime
from typing import List, Dict
import json
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


class WorkflowCommentsFixed:
    """Workflow corrigido para processar comentários"""

    def __init__(self):
        self.db = SupabaseClient()
        self.translator = OptimizedTranslator()
        self.response_manager = comments_manager
        self.stats = {
            'total_comments': 0,
            'comments_with_text': 0,
            'translated': 0,
            'responses_generated': 0,
            'errors': 0
        }

    async def run_complete_workflow(self):
        """Executa workflow completo de comentários"""

        logger.info("="*60)
        logger.info("WORKFLOW CORRIGIDO DE COMENTÁRIOS")
        logger.info("="*60)

        try:
            # ETAPA 1: Buscar NOSSOS canais
            nossos_canais = self.db.supabase.table('canais_monitorados').select(
                'id, nome_canal, subnicho'
            ).eq('tipo', 'nosso').execute()

            canal_ids = [c['id'] for c in nossos_canais.data] if nossos_canais.data else []
            monetizados_ids = [c['id'] for c in nossos_canais.data if c.get('subnicho') == 'Monetizados'] if nossos_canais.data else []

            logger.info(f"Encontrados {len(canal_ids)} canais nossos")
            logger.info(f"Destes, {len(monetizados_ids)} são monetizados")

            # ETAPA 2: Buscar TODOS os comentários dos nossos canais (COM PAGINAÇÃO!)
            comments = []
            offset = 0
            batch_size = 1000

            logger.info("Buscando comentários com paginação...")

            while True:
                # Buscar batch com range
                batch_response = self.db.supabase.table('video_comments').select(
                    'id, comment_id, video_id, canal_id, comment_text_original, comment_text_pt, like_count, author_name, gpt_analysis'
                ).in_('canal_id', canal_ids).range(offset, offset + batch_size - 1).execute()

                batch_comments = batch_response.data if batch_response.data else []

                if not batch_comments:
                    break

                comments.extend(batch_comments)
                logger.info(f"Batch {(offset//batch_size)+1}: {len(batch_comments)} comentários carregados (total: {len(comments)})")

                # Se o batch retornou menos que o batch_size, chegamos ao fim
                if len(batch_comments) < batch_size:
                    break

                offset += batch_size

            self.stats['total_comments'] = len(comments)

            logger.info(f"\nTotal de comentários: {self.stats['total_comments']}")

            # ETAPA 3: Separar comentários por status
            comments_to_translate = []
            comments_for_responses = []

            for comment in comments:
                # Verificar se tem texto original
                text_original = comment.get('comment_text_original') or ''
                text_pt = comment.get('comment_text_pt') or ''

                text_original = text_original.strip() if text_original else ''
                text_pt = text_pt.strip() if text_pt else ''

                if text_original:
                    self.stats['comments_with_text'] += 1

                    # Precisa traduzir?
                    if not text_pt or text_pt == 'null' or text_pt == 'texto traduzido ou original':
                        comments_to_translate.append(comment)

                    # Se é de canal monetizado, adicionar para gerar resposta
                    if comment['canal_id'] in monetizados_ids:
                        comment['text_for_response'] = text_pt if text_pt and text_pt not in ['null', 'texto traduzido ou original'] else text_original
                        comments_for_responses.append(comment)

            logger.info(f"Comentários com texto: {self.stats['comments_with_text']}")
            logger.info(f"Comentários para traduzir: {len(comments_to_translate)}")
            logger.info(f"Comentários para gerar resposta: {len(comments_for_responses)}")

            # ETAPA 4: Traduzir comentários
            if comments_to_translate:
                await self._translate_comments(comments_to_translate)

            # ETAPA 5: Gerar respostas TOP 10 por vídeo
            if comments_for_responses:
                await self._generate_top10_responses(comments_for_responses)

            # ETAPA 6: Estatísticas finais
            logger.info("\n" + "="*60)
            logger.info("WORKFLOW COMPLETO!")
            logger.info("="*60)
            logger.info(f"Total de comentários: {self.stats['total_comments']}")
            logger.info(f"Com texto original: {self.stats['comments_with_text']}")
            logger.info(f"Traduzidos: {self.stats['translated']}")
            logger.info(f"Respostas geradas: {self.stats['responses_generated']}")
            logger.info(f"Erros: {self.stats['errors']}")
            logger.info("="*60)

            return self.stats

        except Exception as e:
            logger.error(f"Erro fatal no workflow: {e}")
            self.stats['errors'] += 1
            return self.stats

    async def _translate_comments(self, comments: List[Dict]):
        """Traduz comentários usando GPT-4 Mini"""
        logger.info("\n--- TRADUZINDO COMENTÁRIOS ---")

        batch_size = 20
        for i in range(0, len(comments), batch_size):
            batch = comments[i:i + batch_size]

            # Preparar textos
            texts = []
            comment_map = {}

            for idx, comment in enumerate(batch):
                text = comment.get('comment_text_original') or ''
                text = text.strip() if text else ''
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

                logger.info(f"Batch {(i//batch_size)+1}: {len(translations)} traduções salvas")

                # Pausa entre batches
                if i + batch_size < len(comments):
                    await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Erro na tradução do batch: {e}")
                self.stats['errors'] += 1

    async def _generate_top10_responses(self, comments: List[Dict]):
        """Gera respostas para TOP 10 comentários por vídeo"""
        logger.info("\n--- GERANDO RESPOSTAS TOP 10 ---")

        # Agrupar por vídeo
        comments_by_video = {}
        for comment in comments:
            video_id = comment.get('video_id')
            if video_id not in comments_by_video:
                comments_by_video[video_id] = []
            comments_by_video[video_id].append(comment)

        logger.info(f"Vídeos únicos: {len(comments_by_video)}")

        # Processar cada vídeo
        for video_id, video_comments in comments_by_video.items():
            # Ordenar por likes e pegar TOP 10
            video_comments.sort(key=lambda x: x.get('like_count', 0), reverse=True)
            top_10 = video_comments[:10]

            # Preparar para geração
            comments_for_response = []
            for comment in top_10:
                text = comment.get('text_for_response', comment.get('comment_text_pt', comment.get('comment_text_original', '')))

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
                logger.error(f"Erro ao gerar respostas para vídeo {video_id}: {e}")
                self.stats['errors'] += 1


async def main():
    """Executa workflow completo"""
    processor = WorkflowCommentsFixed()
    stats = await processor.run_complete_workflow()
    return stats


if __name__ == "__main__":
    asyncio.run(main())
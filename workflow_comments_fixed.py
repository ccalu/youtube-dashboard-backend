# -*- coding: utf-8 -*-
"""
Workflow de Processamento de Comentarios - Versao Corrigida
Data: 04/02/2026
Autor: Claude

Este modulo fornece a classe WorkflowCommentsFixed que e chamada pelo main.py
apos a coleta diaria para processar (traduzir) comentarios.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List
from database import SupabaseClient
from translate_comments_optimized import OptimizedTranslator
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Carregar variaveis de ambiente
load_dotenv()


class WorkflowCommentsFixed:
    """
    Workflow completo para processamento de comentarios.

    Responsavel por:
    1. Buscar comentarios que precisam de traducao
    2. Traduzir para PT-BR usando GPT-4 Mini
    3. Atualizar o banco de dados
    """

    def __init__(self):
        self.db = SupabaseClient()
        self.translator = OptimizedTranslator()
        self.stats = {
            'total_comments': 0,
            'comments_with_text': 0,
            'translated': 0,
            'responses_generated': 0,  # Mantido para compatibilidade, mas nao usado
            'errors': 0,
            'start_time': None,
            'end_time': None
        }

    async def run_complete_workflow(self, only_recent: bool = True) -> Dict:
        """
        Executa o workflow completo de processamento de comentarios.

        Args:
            only_recent: Se True, processa apenas comentarios das ultimas 24h

        Returns:
            Dicionario com estatisticas do processamento
        """
        self.stats['start_time'] = datetime.utcnow()

        logger.info("=" * 60)
        logger.info("WORKFLOW DE COMENTARIOS INICIADO")
        logger.info("=" * 60)

        try:
            # ETAPA 1: Buscar nossos canais
            nossos_canais = self.db.supabase.table('canais_monitorados').select(
                'id, nome_canal, subnicho, is_monetized'
            ).eq('tipo', 'nosso').execute()

            canal_ids = [c['id'] for c in nossos_canais.data] if nossos_canais.data else []

            logger.info(f"Canais nossos encontrados: {len(canal_ids)}")

            # ETAPA 2: Buscar comentarios para processar
            comments = await self._fetch_comments_to_translate(canal_ids, only_recent)
            self.stats['total_comments'] = len(comments)

            # Filtrar comentarios com texto
            comments_with_text = [c for c in comments if (c.get('comment_text_original') or '').strip()]
            self.stats['comments_with_text'] = len(comments_with_text)

            if not comments_with_text:
                logger.info("Nenhum comentario novo para traduzir")
                return self.stats

            logger.info(f"Comentarios para traduzir: {len(comments_with_text)}")

            # ETAPA 3: Traduzir comentarios
            await self._translate_comments(comments_with_text)

            self.stats['end_time'] = datetime.utcnow()
            duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()

            # Log final
            logger.info("=" * 60)
            logger.info("WORKFLOW COMPLETO!")
            logger.info("=" * 60)
            logger.info(f"Total comentarios: {self.stats['total_comments']}")
            logger.info(f"Com texto: {self.stats['comments_with_text']}")
            logger.info(f"Traduzidos: {self.stats['translated']}")
            logger.info(f"Erros: {self.stats['errors']}")
            logger.info(f"Tempo total: {duration:.1f} segundos")
            logger.info("=" * 60)

            return self.stats

        except Exception as e:
            logger.error(f"Erro fatal no workflow: {e}")
            self.stats['errors'] += 1
            return self.stats

    async def _fetch_comments_to_translate(self, canal_ids: List[int], only_recent: bool) -> List[Dict]:
        """
        Busca comentarios que precisam de traducao.

        Criterios:
        - Pertencem aos nossos canais
        - Tem texto original mas sem traducao PT
        - (Opcional) Criados nas ultimas 24h
        """
        if not canal_ids:
            return []

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
                'comment_text_pt, is_translated, like_count, author_name, created_at'
            ).in_('canal_id', canal_ids).eq('is_translated', False)

            # Aplicar filtro de data se necessario
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
        """Traduz comentarios em batches usando GPT-4 Mini"""
        logger.info(f"Iniciando traducao de {len(comments)} comentarios...")

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

                # Salvar traducoes no banco
                for idx, translation in enumerate(translations):
                    if idx in comment_map:
                        db_id = comment_map[idx]

                        self.db.supabase.table('video_comments').update({
                            'comment_text_pt': translation,
                            'is_translated': True,
                            'updated_at': datetime.utcnow().isoformat()
                        }).eq('id', db_id).execute()

                        self.stats['translated'] += 1

                logger.info(f"Batch {i // batch_size + 1}: {len(translations)} comentarios traduzidos")

                # Pausa entre batches para nao sobrecarregar API
                if i + batch_size < len(comments):
                    await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Erro ao traduzir batch: {e}")
                self.stats['errors'] += 1


async def main():
    """Executa workflow (para testes manuais)"""
    workflow = WorkflowCommentsFixed()
    stats = await workflow.run_complete_workflow(only_recent=True)
    return stats


if __name__ == "__main__":
    asyncio.run(main())

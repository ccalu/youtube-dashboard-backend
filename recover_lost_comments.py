"""
SCRIPT DE RECUPERAÇÃO DE COMENTÁRIOS PERDIDOS
Data: 27/01/2026
Autor: Claude

Este script busca e recupera comentários que foram salvos sem texto devido ao bug de mapeamento.
Ele tentará re-coletar os comentários usando a API do YouTube.
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Optional
from database import SupabaseClient
from collector import YouTubeCollector
import os
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()


class CommentRecovery:
    """Recupera comentários perdidos"""

    def __init__(self):
        self.db = SupabaseClient()
        self.collector = YouTubeCollector()
        self.stats = {
            'total_empty': 0,
            'videos_to_recover': 0,
            'comments_recovered': 0,
            'comments_updated': 0,
            'errors': 0
        }

    async def find_empty_comments(self) -> List[Dict]:
        """Busca todos os comentários sem texto (com paginação)"""
        logger.info("Buscando comentários sem texto...")

        empty_comments = []
        offset = 0
        batch_size = 1000

        while True:
            # Buscar batch
            batch = self.db.supabase.table('video_comments').select(
                'id, comment_id, video_id, canal_id, author_name, comment_text_original'
            ).or_(
                'comment_text_original.is.null,comment_text_original.eq.'
            ).range(offset, offset + batch_size - 1).execute()

            batch_data = batch.data if batch.data else []

            if not batch_data:
                break

            empty_comments.extend(batch_data)
            logger.info(f"Batch {(offset//batch_size)+1}: {len(batch_data)} comentários vazios encontrados")

            if len(batch_data) < batch_size:
                break

            offset += batch_size

        self.stats['total_empty'] = len(empty_comments)
        logger.info(f"Total de comentários vazios: {self.stats['total_empty']}")

        return empty_comments

    async def group_by_video(self, comments: List[Dict]) -> Dict[str, List[Dict]]:
        """Agrupa comentários por video_id"""
        grouped = {}
        for comment in comments:
            video_id = comment.get('video_id')
            if video_id:
                if video_id not in grouped:
                    grouped[video_id] = []
                grouped[video_id].append(comment)

        self.stats['videos_to_recover'] = len(grouped)
        logger.info(f"Vídeos únicos para recuperar: {self.stats['videos_to_recover']}")
        return grouped

    async def recover_comments_for_video(self, video_id: str, existing_comments: List[Dict]):
        """Re-coleta comentários de um vídeo específico"""
        try:
            logger.info(f"Recuperando comentários do vídeo: {video_id}")

            # Buscar comentários via API
            api_comments = await self.collector.get_video_comments(
                video_id=video_id,
                max_results=1000  # Buscar até 1000 comentários por vídeo
            )

            if not api_comments:
                logger.warning(f"Não foi possível recuperar comentários do vídeo {video_id}")
                return

            # Criar mapa de comment_id -> dados da API
            api_map = {c['comment_id']: c for c in api_comments}

            # Atualizar comentários existentes
            for existing in existing_comments:
                comment_id = existing.get('comment_id')

                if comment_id in api_map:
                    api_data = api_map[comment_id]

                    # Atualizar no banco
                    update_data = {
                        'comment_text_original': api_data.get('comment_text_original', ''),
                        'author_name': api_data.get('author_name', ''),
                        'like_count': api_data.get('like_count', 0),
                        'reply_count': api_data.get('reply_count', 0),
                        'updated_at': datetime.utcnow().isoformat()
                    }

                    self.db.supabase.table('video_comments').update(
                        update_data
                    ).eq('id', existing['id']).execute()

                    self.stats['comments_updated'] += 1
                    logger.debug(f"Comentário {comment_id} atualizado com sucesso")

            # Verificar se há comentários novos que não estavam no banco
            existing_ids = {c['comment_id'] for c in existing_comments}
            new_comments = [c for c in api_comments if c['comment_id'] not in existing_ids]

            if new_comments:
                logger.info(f"Encontrados {len(new_comments)} comentários novos para o vídeo {video_id}")
                # Aqui você pode adicionar lógica para salvar novos comentários se necessário

            self.stats['comments_recovered'] += len(api_comments)
            logger.info(f"Vídeo {video_id}: {len(api_comments)} comentários recuperados, {self.stats['comments_updated']} atualizados")

        except Exception as e:
            logger.error(f"Erro ao recuperar comentários do vídeo {video_id}: {e}")
            self.stats['errors'] += 1

    async def run_recovery(self, limit_videos: Optional[int] = None):
        """Executa processo completo de recuperação"""
        logger.info("="*60)
        logger.info("RECUPERAÇÃO DE COMENTÁRIOS PERDIDOS")
        logger.info("="*60)

        # 1. Buscar comentários vazios
        empty_comments = await self.find_empty_comments()

        if not empty_comments:
            logger.info("Nenhum comentário vazio encontrado! Tudo está OK.")
            return self.stats

        # 2. Agrupar por vídeo
        grouped = await self.group_by_video(empty_comments)

        # 3. Recuperar comentários (com limite opcional)
        video_ids = list(grouped.keys())
        if limit_videos:
            video_ids = video_ids[:limit_videos]
            logger.info(f"Limitando recuperação a {limit_videos} vídeos")

        for i, video_id in enumerate(video_ids, 1):
            logger.info(f"\n[{i}/{len(video_ids)}] Processando vídeo {video_id}...")
            await self.recover_comments_for_video(video_id, grouped[video_id])

            # Pausa entre vídeos para não sobrecarregar API
            if i < len(video_ids):
                await asyncio.sleep(2)

        # 4. Estatísticas finais
        logger.info("\n" + "="*60)
        logger.info("RECUPERAÇÃO COMPLETA!")
        logger.info("="*60)
        logger.info(f"Comentários vazios encontrados: {self.stats['total_empty']}")
        logger.info(f"Vídeos processados: {min(len(video_ids), self.stats['videos_to_recover'])}")
        logger.info(f"Comentários recuperados da API: {self.stats['comments_recovered']}")
        logger.info(f"Comentários atualizados no banco: {self.stats['comments_updated']}")
        logger.info(f"Erros: {self.stats['errors']}")
        logger.info("="*60)

        return self.stats


async def main():
    """Executa recuperação de comentários"""
    recovery = CommentRecovery()

    # Perguntar ao usuário
    print("\n" + "="*60)
    print("RECUPERAÇÃO DE COMENTÁRIOS PERDIDOS")
    print("="*60)
    print("\nEste script irá:")
    print("1. Buscar comentários sem texto no banco")
    print("2. Re-coletar dados via YouTube API")
    print("3. Atualizar comentários com os dados corretos")
    print("\nAVISO: Isso consumirá quota da API do YouTube!")

    response = input("\nDeseja continuar? (s/n): ").strip().lower()
    if response != 's':
        print("Operação cancelada.")
        return

    # Perguntar sobre limite
    limit_input = input("\nQuantos vídeos processar? (Enter para todos): ").strip()
    limit_videos = int(limit_input) if limit_input.isdigit() else None

    # Executar recuperação
    stats = await recovery.run_recovery(limit_videos=limit_videos)
    return stats


if __name__ == "__main__":
    asyncio.run(main())
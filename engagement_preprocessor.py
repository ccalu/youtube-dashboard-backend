#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de pré-processamento de dados de engajamento.
Executa após a coleta diária para processar e armazenar dados em cache.

Data: 29/01/2025
"""

import logging
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from database import SupabaseClient

logger = logging.getLogger(__name__)


class EngagementPreprocessor:
    """
    Pré-processa dados de engajamento e armazena em cache.
    Executa como último step da coleta diária.
    """

    def __init__(self, db: SupabaseClient = None):
        """
        Inicializa o pré-processador.

        Args:
            db: Cliente do Supabase (opcional, cria novo se não fornecido)
        """
        self.db = db or SupabaseClient()

    async def build_engagement_cache(self) -> Dict[str, Any]:
        """
        Constrói cache completo de engajamento para todos os canais.
        Executa APÓS daily_analysis_job (último step).

        Returns:
            Dict com estatísticas do processamento
        """
        try:
            logger.info("=" * 80)
            logger.info("🔄 CONSTRUINDO CACHE DE ENGAJAMENTO")
            logger.info("=" * 80)

            start_time = datetime.now()

            # Buscar apenas canais "nossos" ativos
            canais_response = self.db.supabase.table('canais_monitorados')\
                .select('id, nome_canal')\
                .eq('tipo', 'nosso')\
                .eq('status', 'ativo')\
                .execute()

            if not canais_response.data:
                logger.warning("⚠️ Nenhum canal 'nosso' ativo encontrado")
                return {'processed': 0, 'failed': 0, 'total': 0}

            canais = canais_response.data
            total_canais = len(canais)

            logger.info(f"📊 {total_canais} canais para processar")

            processed = 0
            failed = 0

            for index, canal in enumerate(canais, 1):
                canal_id = canal['id']
                canal_nome = canal['nome_canal']

                try:
                    logger.info(f"[{index}/{total_canais}] Processando: {canal_nome} (ID: {canal_id})")

                    success = await self.process_and_cache_canal(canal_id)

                    if success:
                        processed += 1
                        logger.info(f"✅ [{index}/{total_canais}] {canal_nome} - Cache atualizado")
                    else:
                        failed += 1
                        logger.warning(f"⚠️ [{index}/{total_canais}] {canal_nome} - Sem dados para cache")

                except Exception as e:
                    failed += 1
                    logger.error(f"❌ [{index}/{total_canais}] Erro ao processar {canal_nome}: {e}")
                    import traceback
                    logger.error(traceback.format_exc())

            # Limpar cache expirado
            try:
                cleanup_result = self.db.supabase.rpc('delete_expired_engagement_cache').execute()
                if cleanup_result.data is not None:
                    logger.info(f"🧹 Cache expirado limpo: {cleanup_result.data} registros")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao limpar cache expirado: {e}")

            elapsed_time = (datetime.now() - start_time).total_seconds()

            logger.info("=" * 80)
            logger.info("✅ CACHE DE ENGAJAMENTO CONCLUÍDO")
            logger.info(f"✅ Processados: {processed}/{total_canais}")
            logger.info(f"❌ Falhas: {failed}/{total_canais}")
            logger.info(f"⏱️ Tempo total: {elapsed_time:.1f}s")
            logger.info("=" * 80)

            return {
                'processed': processed,
                'failed': failed,
                'total': total_canais,
                'elapsed_seconds': elapsed_time
            }

        except Exception as e:
            logger.error(f"❌ Erro crítico no build_engagement_cache: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {'processed': 0, 'failed': 0, 'total': 0}

    async def process_and_cache_canal(self, canal_id: int) -> bool:
        """
        Processa e armazena cache de engajamento para UM canal.

        Args:
            canal_id: ID do canal para processar

        Returns:
            True se sucesso, False se não há dados ou erro
        """
        try:
            start_time = datetime.now()

            # Usar a função existente para obter dados de engajamento
            engagement_data = await self.db.get_canal_engagement_data(canal_id)

            if not engagement_data:
                logger.info(f"   ℹ️ Canal {canal_id}: sem dados de engajamento")
                return False

            # Calcular tempo de processamento
            processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            # Contar totais - usar o summary que sempre existe
            total_comments = engagement_data.get('summary', {}).get('total_comments', 0)
            total_videos = len(engagement_data.get('videos_summary', []))

            # Preparar dados para cache
            cache_data = {
                'summary': engagement_data.get('summary', {}),
                'videos_summary': engagement_data.get('videos_summary', []),
                'actionable_comments': engagement_data.get('actionable_comments', []),
                'positive_comments': engagement_data.get('positive_comments', []),
                'negative_comments': engagement_data.get('negative_comments', []),
                'problem_comments': engagement_data.get('problem_comments', [])
            }

            # Calcular expiração (6h a partir de agora)
            expires_at = datetime.now(timezone.utc) + timedelta(hours=6)

            # Salvar no cache (upsert para atualizar se já existe)
            cache_response = self.db.supabase.table('engagement_cache').upsert({
                'canal_id': canal_id,
                'data': cache_data,
                'processed_at': datetime.now(timezone.utc).isoformat(),
                'expires_at': expires_at.isoformat(),
                'total_comments': total_comments,
                'total_videos': total_videos,
                'processing_time_ms': processing_time_ms,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }, on_conflict='canal_id').execute()

            if cache_response.data:
                logger.info(f"   💾 Cache salvo: {total_comments} comentários, "
                          f"{total_videos} vídeos, {processing_time_ms}ms")
                return True
            else:
                logger.error(f"   ❌ Falha ao salvar cache para canal {canal_id}")
                return False

        except Exception as e:
            logger.error(f"   ❌ Erro ao processar canal {canal_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    async def get_cached_engagement(self, canal_id: int) -> Optional[Dict[str, Any]]:
        """
        Busca dados de engajamento do cache.

        Args:
            canal_id: ID do canal

        Returns:
            Dados do cache se disponível e válido, None caso contrário
        """
        try:
            # Buscar cache válido (não expirado)
            cache_response = self.db.supabase.table('engagement_cache')\
                .select('*')\
                .eq('canal_id', canal_id)\
                .gt('expires_at', datetime.now(timezone.utc).isoformat())\
                .execute()

            if not cache_response.data:
                logger.info(f"⚠️ Cache miss para canal {canal_id} (vazio ou expirado)")
                return None

            cache_entry = cache_response.data[0]

            # Adicionar metadados do cache ao response
            result = cache_entry['data']
            result['_cache_metadata'] = {
                'cached': True,
                'processed_at': cache_entry['processed_at'],
                'expires_at': cache_entry['expires_at'],
                'total_comments': cache_entry.get('total_comments', 0),
                'total_videos': cache_entry.get('total_videos', 0),
                'processing_time_ms': cache_entry.get('processing_time_ms', 0)
            }

            logger.info(f"✅ Cache hit para canal {canal_id} "
                       f"({cache_entry.get('total_comments', 0)} comentários)")

            return result

        except Exception as e:
            logger.error(f"❌ Erro ao buscar cache para canal {canal_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    async def force_rebuild_cache(self, canal_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Força reconstrução do cache (útil para testes ou correções).

        Args:
            canal_id: ID específico do canal ou None para todos

        Returns:
            Estatísticas do processamento
        """
        try:
            if canal_id:
                logger.info(f"🔄 Forçando rebuild do cache para canal {canal_id}")
                success = await self.process_and_cache_canal(canal_id)
                return {
                    'processed': 1 if success else 0,
                    'failed': 0 if success else 1,
                    'total': 1
                }
            else:
                logger.info("🔄 Forçando rebuild do cache para TODOS os canais")
                return await self.build_engagement_cache()

        except Exception as e:
            logger.error(f"❌ Erro ao forçar rebuild: {e}")
            return {'processed': 0, 'failed': 1, 'total': 1}

    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do cache.

        Returns:
            Dict com estatísticas do cache
        """
        try:
            # Total de registros em cache
            total_response = self.db.supabase.table('engagement_cache')\
                .select('id', count='exact')\
                .execute()

            # Registros válidos (não expirados)
            valid_response = self.db.supabase.table('engagement_cache')\
                .select('id', count='exact')\
                .gt('expires_at', datetime.now(timezone.utc).isoformat())\
                .execute()

            # Registros expirados
            expired_response = self.db.supabase.table('engagement_cache')\
                .select('id', count='exact')\
                .lte('expires_at', datetime.now(timezone.utc).isoformat())\
                .execute()

            return {
                'total_cached': total_response.count or 0,
                'valid_cached': valid_response.count or 0,
                'expired_cached': expired_response.count or 0,
                'cache_hit_rate': 0  # Pode ser calculado com métricas adicionais
            }

        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas do cache: {e}")
            return {
                'total_cached': 0,
                'valid_cached': 0,
                'expired_cached': 0,
                'cache_hit_rate': 0
            }


# Função helper para usar no main.py
async def build_engagement_cache():
    """
    Função helper para construir cache de engajamento.
    Chamada após daily_analysis_job.
    """
    preprocessor = EngagementPreprocessor()
    return await preprocessor.build_engagement_cache()
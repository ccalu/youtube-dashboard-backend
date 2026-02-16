"""
Monetization Collector - Coleta dados específicos para canais monetizados
Roda automaticamente às 5 AM após a coleta principal
Calcula views_24h e prepara dados para estimativas
"""
import os
import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
from database import SupabaseClient

logger = logging.getLogger(__name__)

class MonetizationCollector:
    def __init__(self):
        self.db = SupabaseClient()

        # YouTube API Keys (13 ativas - suspensas: 3,4,5,6,30,31,32)
        self.api_keys = [
            os.environ.get("YOUTUBE_API_KEY_7"),
            os.environ.get("YOUTUBE_API_KEY_8"),
            os.environ.get("YOUTUBE_API_KEY_9"),
            os.environ.get("YOUTUBE_API_KEY_10"),
            os.environ.get("YOUTUBE_API_KEY_21"),
            os.environ.get("YOUTUBE_API_KEY_22"),
            os.environ.get("YOUTUBE_API_KEY_23"),
            os.environ.get("YOUTUBE_API_KEY_24"),
            os.environ.get("YOUTUBE_API_KEY_25"),
            os.environ.get("YOUTUBE_API_KEY_26"),
            os.environ.get("YOUTUBE_API_KEY_27"),
            os.environ.get("YOUTUBE_API_KEY_28"),
            os.environ.get("YOUTUBE_API_KEY_29"),
        ]

        self.api_keys = [k for k in self.api_keys if k]
        self.current_key_index = 0

        if not self.api_keys:
            logger.warning("⚠️ Nenhuma YouTube API Key configurada para monetization collector")

    def get_next_api_key(self):
        """Rotaciona entre as chaves disponíveis"""
        if not self.api_keys:
            return None

        key = self.api_keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        return key

    async def get_monetized_channels(self) -> List[Dict]:
        """Busca canais monetizados ativos"""
        try:
            response = self.db.supabase.table("yt_channels")\
                .select("channel_id, channel_name, monetization_start_date")\
                .eq("is_monetized", True)\
                .execute()

            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Erro ao buscar canais monetizados: {e}")
            return []

    async def get_channel_statistics(self, channel_id: str, session: aiohttp.ClientSession) -> Optional[Dict]:
        """Busca statistics do canal via YouTube Data API v3"""
        api_key = self.get_next_api_key()

        if not api_key:
            logger.error("Nenhuma API key disponível")
            return None

        url = "https://www.googleapis.com/youtube/v3/channels"
        params = {
            'part': 'statistics',
            'id': channel_id,
            'key': api_key
        }

        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    if 'items' in data and len(data['items']) > 0:
                        stats = data['items'][0]['statistics']
                        return {
                            'viewCount': int(stats.get('viewCount', 0)),
                            'subscriberCount': int(stats.get('subscriberCount', 0)),
                            'videoCount': int(stats.get('videoCount', 0))
                        }

                logger.warning(f"Erro API para {channel_id}: Status {response.status}")
                return None

        except Exception as e:
            logger.error(f"Exceção ao buscar statistics {channel_id}: {e}")
            return None

    def get_yesterday_snapshot(self, canal_internal_id: int, today: date) -> Optional[int]:
        """Busca snapshot de ontem para calcular views_24h"""
        try:
            yesterday = today - timedelta(days=1)

            response = self.db.supabase.table("dados_canais_historico")\
                .select("total_views")\
                .eq("canal_id", canal_internal_id)\
                .eq("data_coleta", yesterday.isoformat())\
                .execute()

            if response.data and len(response.data) > 0:
                return response.data[0]['total_views']

            return None

        except Exception as e:
            logger.error(f"Erro ao buscar snapshot de ontem: {e}")
            return None

    def save_snapshot(self, canal_internal_id: int, channel_name: str, total_views: int, today: date) -> bool:
        """Salva snapshot em dados_canais_historico"""
        try:
            payload = {
                'canal_id': canal_internal_id,
                'data_coleta': today.isoformat(),
                'total_views': total_views
            }

            # Upsert (se já existe snapshot de hoje, atualiza)
            response = self.db.supabase.table("dados_canais_historico")\
                .upsert(payload, on_conflict='canal_id,data_coleta')\
                .execute()

            return True

        except Exception as e:
            logger.error(f"Erro ao salvar snapshot {channel_name}: {e}")
            return False

    def save_views_to_yt_daily_metrics(self, channel_id: str, date: date, views_24h: int) -> bool:
        """
        Salva views de 24h em yt_daily_metrics
        Usado para criar estimativas quando não há revenue ainda
        """
        try:
            # Verificar se já existe registro para essa data
            existing = self.db.supabase.table("yt_daily_metrics")\
                .select("id, revenue, is_estimate")\
                .eq("channel_id", channel_id)\
                .eq("date", date.isoformat())\
                .execute()

            if existing.data and len(existing.data) > 0:
                # Já existe - não sobrescrever
                logger.info(f"Registro já existe para {channel_id} em {date.isoformat()}")
                return True

            # Calcular RPM médio do canal (últimos 30 dias com revenue real)
            rpm_avg = self.calculate_channel_rpm(channel_id)

            if rpm_avg is None or rpm_avg == 0:
                logger.warning(f"RPM médio não disponível para {channel_id}")
                return False

            # Estimar revenue
            revenue_estimated = rpm_avg * (views_24h / 1000)

            # Salvar estimativa
            payload = {
                'channel_id': channel_id,
                'date': date.isoformat(),
                'views': views_24h,
                'revenue': round(revenue_estimated, 2),
                'is_estimate': True,
                'rpm': rpm_avg
            }

            self.db.supabase.table("yt_daily_metrics")\
                .insert(payload)\
                .execute()

            logger.info(f"✅ Estimativa salva: {channel_id} {date.isoformat()} - ${revenue_estimated:.2f} (RPM: ${rpm_avg:.2f})")
            return True

        except Exception as e:
            logger.error(f"Erro ao salvar views em yt_daily_metrics: {e}")
            return False

    def calculate_channel_rpm(self, channel_id: str) -> Optional[float]:
        """
        Calcula RPM médio do canal baseado APENAS em dados reais
        Últimos 30 dias com revenue confirmado
        """
        try:
            thirty_days_ago = (datetime.now().date() - timedelta(days=30)).isoformat()

            response = self.db.supabase.table("yt_daily_metrics")\
                .select("revenue, views")\
                .eq("channel_id", channel_id)\
                .eq("is_estimate", False)\
                .gte("date", thirty_days_ago)\
                .execute()

            if not response.data or len(response.data) == 0:
                return None

            total_revenue = sum(r['revenue'] for r in response.data if r['revenue'])
            total_views = sum(r['views'] for r in response.data if r['views'])

            if total_views == 0:
                return None

            rpm = (total_revenue / total_views) * 1000
            return round(rpm, 2)

        except Exception as e:
            logger.error(f"Erro ao calcular RPM: {e}")
            return None

    def get_canal_internal_id(self, channel_name: str) -> Optional[int]:
        """Busca ID interno do canal em canais_monitorados"""
        try:
            response = self.db.supabase.table("canais_monitorados")\
                .select("id")\
                .ilike("nome_canal", f"%{channel_name}%")\
                .execute()

            if response.data and len(response.data) > 0:
                return response.data[0]['id']

            return None

        except Exception as e:
            logger.error(f"Erro ao buscar ID interno: {e}")
            return None

    async def collect_monetization_data(self):
        """
        Coleta dados de monetização
        - Busca total_views atual
        - Calcula views_24h (se tiver snapshot de ontem)
        - Salva snapshot
        - Cria estimativas para D-1 e D-2 (se não tiver revenue ainda)
        """
        logger.info("=" * 70)
        logger.info("🔄 INICIANDO COLETA DE MONETIZAÇÃO")
        logger.info("=" * 70)

        channels = await self.get_monetized_channels()

        if not channels:
            logger.warning("⚠️ Nenhum canal monetizado encontrado")
            return

        logger.info(f"📊 Canais monetizados: {len(channels)}")

        today = datetime.now().date()

        async with aiohttp.ClientSession() as session:
            for canal in channels:
                channel_id = canal['channel_id']
                channel_name = canal['channel_name']

                logger.info(f"\n📺 {channel_name}")

                # Buscar statistics
                stats = await self.get_channel_statistics(channel_id, session)

                if not stats:
                    logger.warning(f"  ⚠️ Erro ao buscar statistics")
                    continue

                total_views_today = stats['viewCount']
                logger.info(f"  Total Views: {total_views_today:,}")

                # Buscar ID interno
                internal_id = self.get_canal_internal_id(channel_name)

                if not internal_id:
                    logger.warning(f"  ⚠️ Canal não encontrado em canais_monitorados")
                    continue

                # Buscar snapshot de ontem
                total_views_yesterday = self.get_yesterday_snapshot(internal_id, today)

                if total_views_yesterday:
                    views_24h = total_views_today - total_views_yesterday
                    logger.info(f"  Views 24h: {views_24h:,}")

                    # Salvar views em yt_daily_metrics (para estimativas)
                    yesterday_date = today - timedelta(days=1)
                    self.save_views_to_yt_daily_metrics(channel_id, yesterday_date, views_24h)
                else:
                    logger.info(f"  Sem snapshot de ontem - primeiro dia")

                # Salvar snapshot de hoje
                if self.save_snapshot(internal_id, channel_name, total_views_today, today):
                    logger.info(f"  ✅ Snapshot salvo!")

                # Aguardar entre requests
                await asyncio.sleep(0.5)

        logger.info("\n" + "=" * 70)
        logger.info("✅ COLETA DE MONETIZAÇÃO FINALIZADA")
        logger.info("=" * 70)

async def collect_monetization():
    """Função principal chamada pelo scheduler"""
    collector = MonetizationCollector()
    await collector.collect_monetization_data()

if __name__ == "__main__":
    # Teste manual
    asyncio.run(collect_monetization())

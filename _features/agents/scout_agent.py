# ========================================
# SCOUT AGENT - Cacador de Canais Novos
# ========================================
# Funcao: Descobrir canais novos automaticamente
# Substitui: NextLev
# Custo: ZERO (usa YouTube API que voce ja tem)
# ========================================

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import asyncio
import aiohttp
import os
import re

from .base import BaseAgent, AgentResult, AgentStatus

logger = logging.getLogger(__name__)


class ScoutAgent(BaseAgent):
    """
    Agente responsavel por descobrir novos canais para monitorar.

    Metodos de descoberta:
    1. Related Channels - Canais relacionados aos que ja monitoramos
    2. YouTube Search - Busca por keywords do nicho

    Criterios de qualidade (filtros):
    - Minimo 1.000 inscritos
    - Pelo menos 1 video nos ultimos 15 dias
    - Subnicho relevante para nossos canais
    - Ignora canais inativos (>60 dias sem post)
    """

    def __init__(self, db_client, collector=None):
        """
        Args:
            db_client: Instancia do SupabaseClient
            collector: Instancia do YouTubeCollector (opcional, para usar API keys)
        """
        super().__init__(db_client)
        self.collector = collector

        # Configuracoes de filtro
        self.min_subscribers = 1000  # Minimo de inscritos
        self.max_days_inactive = 60  # Maximo de dias sem postar
        self.recent_video_days = 15  # Deve ter video recente (15 dias)

        # Limites para evitar spam de descobertas
        self.max_channels_per_run = 50  # Maximo de canais por execucao
        self.max_search_results = 20  # Maximo de resultados por busca

        # API config
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.api_keys = self._load_api_keys()
        self.current_key_index = 0

    def _load_api_keys(self) -> List[str]:
        """Carrega API keys do ambiente"""
        keys = []
        for i in range(3, 33):
            key = os.environ.get(f"YOUTUBE_API_KEY_{i}")
            if key:
                keys.append(key)
        return keys if keys else [os.environ.get("YOUTUBE_API_KEY", "")]

    def _get_api_key(self) -> str:
        """Retorna API key atual"""
        if self.collector:
            return self.collector.get_current_api_key()
        return self.api_keys[self.current_key_index % len(self.api_keys)]

    def _rotate_key(self):
        """Rotaciona para proxima API key"""
        if self.collector:
            self.collector.rotate_to_next_key()
        else:
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)

    @property
    def name(self) -> str:
        return "ScoutAgent"

    @property
    def description(self) -> str:
        return "Descobre novos canais para monitorar baseado em canais relacionados e busca por keywords"

    async def run(self) -> AgentResult:
        """Executa descoberta de canais"""
        result = self.create_result()

        try:
            # 1. Buscar canais que ja monitoramos (para encontrar relacionados)
            logger.info(f"[{self.name}] Buscando canais ja monitorados...")
            canais_monitorados = await self._get_monitored_channels()

            if not canais_monitorados:
                logger.warning(f"[{self.name}] Nenhum canal monitorado encontrado")
                return self.complete_result(result, {"discovered": [], "message": "Nenhum canal base para descoberta"})

            logger.info(f"[{self.name}] {len(canais_monitorados)} canais monitorados encontrados")

            # 2. Extrair subnichos unicos para busca
            subnichos = self._extract_unique_subnichos(canais_monitorados)
            logger.info(f"[{self.name}] Subnichos encontrados: {subnichos}")

            # 3. Descobrir canais novos
            discovered_channels = []

            # 3a. Buscar por keywords dos subnichos (mais eficiente)
            for subnicho in subnichos[:5]:  # Limitar a 5 subnichos por run
                logger.info(f"[{self.name}] Buscando canais para subnicho: {subnicho}")
                channels = await self._search_channels_by_keyword(subnicho)
                discovered_channels.extend(channels)

                if len(discovered_channels) >= self.max_channels_per_run:
                    break

                await asyncio.sleep(0.5)  # Rate limiting

            # 4. Filtrar canais ja monitorados
            existing_urls = {c.get("url_canal", "").lower() for c in canais_monitorados}
            new_channels = [
                c for c in discovered_channels
                if c.get("url_canal", "").lower() not in existing_urls
            ]

            logger.info(f"[{self.name}] {len(new_channels)} canais NOVOS descobertos (de {len(discovered_channels)} total)")

            # 5. Validar e pontuar canais
            validated_channels = await self._validate_channels(new_channels)

            # 6. Ordenar por score (melhores primeiro)
            validated_channels.sort(key=lambda x: x.get("scout_score", 0), reverse=True)

            # 7. Limitar resultado
            final_channels = validated_channels[:self.max_channels_per_run]

            # 8. Salvar descobertas na tabela de sugestoes
            saved_count = await self._save_discoveries(final_channels)

            metrics = {
                "canais_base": len(canais_monitorados),
                "subnichos_analisados": len(subnichos),
                "canais_encontrados": len(discovered_channels),
                "canais_novos": len(new_channels),
                "canais_validados": len(validated_channels),
                "canais_salvos": saved_count
            }

            return self.complete_result(result, {
                "discovered": final_channels,
                "summary": f"{saved_count} novos canais descobertos e salvos"
            }, metrics)

        except Exception as e:
            logger.error(f"[{self.name}] Erro: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return self.fail_result(result, str(e))

    async def _get_monitored_channels(self) -> List[Dict]:
        """Busca canais ja monitorados do banco"""
        try:
            response = self.db.supabase.table("canais_monitorados")\
                .select("id, nome_canal, url_canal, nicho, subnicho, lingua, tipo")\
                .eq("status", "ativo")\
                .execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Erro ao buscar canais monitorados: {e}")
            return []

    def _extract_unique_subnichos(self, canais: List[Dict]) -> List[str]:
        """Extrai subnichos unicos dos canais"""
        subnichos = set()
        for canal in canais:
            subnicho = canal.get("subnicho")
            if subnicho and subnicho.strip():
                subnichos.add(subnicho.strip())
        return list(subnichos)

    async def _search_channels_by_keyword(self, keyword: str) -> List[Dict]:
        """
        Busca canais no YouTube por keyword.
        Custo: 100 units por busca (CARO!)
        """
        channels = []

        try:
            api_key = self._get_api_key()
            if not api_key:
                logger.warning("Sem API key disponivel")
                return []

            # Termos de busca relacionados ao nicho de entretenimento
            search_terms = [
                f"{keyword} stories",
                f"{keyword} facts",
                f"dark {keyword}",
                f"{keyword} explained"
            ]

            async with aiohttp.ClientSession() as session:
                for term in search_terms[:2]:  # Limitar buscas
                    url = f"{self.base_url}/search"
                    params = {
                        "key": api_key,
                        "q": term,
                        "type": "channel",
                        "part": "snippet",
                        "maxResults": self.max_search_results,
                        "relevanceLanguage": "en"
                    }

                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()

                            for item in data.get("items", []):
                                snippet = item.get("snippet", {})
                                channel_id = item.get("id", {}).get("channelId", "")

                                if channel_id:
                                    channels.append({
                                        "channel_id": channel_id,
                                        "nome_canal": snippet.get("title", ""),
                                        "url_canal": f"https://www.youtube.com/channel/{channel_id}",
                                        "descricao": snippet.get("description", ""),
                                        "subnicho_sugerido": keyword,
                                        "thumbnail": snippet.get("thumbnails", {}).get("default", {}).get("url", "")
                                    })

                        elif response.status == 403:
                            logger.warning("Quota exceeded, rotacionando key...")
                            self._rotate_key()

                    await asyncio.sleep(0.3)  # Rate limit entre buscas

        except Exception as e:
            logger.error(f"Erro na busca por keyword '{keyword}': {e}")

        return channels

    async def _validate_channels(self, channels: List[Dict]) -> List[Dict]:
        """
        Valida canais descobertos contra criterios de qualidade.
        Adiciona metricas e score.
        """
        validated = []

        for channel in channels:
            try:
                channel_id = channel.get("channel_id")
                if not channel_id:
                    continue

                # Buscar stats do canal via API
                stats = await self._get_channel_stats(channel_id)

                if not stats:
                    continue

                subscribers = stats.get("subscriberCount", 0)
                video_count = stats.get("videoCount", 0)

                # Filtro: minimo de inscritos
                if subscribers < self.min_subscribers:
                    logger.debug(f"Canal {channel.get('nome_canal')} ignorado: {subscribers} inscritos < {self.min_subscribers}")
                    continue

                # Verificar atividade recente
                last_video_date = await self._get_last_video_date(channel_id)

                if last_video_date:
                    days_since_last = (datetime.now(timezone.utc) - last_video_date).days

                    # Filtro: deve ter video recente
                    if days_since_last > self.recent_video_days:
                        logger.debug(f"Canal {channel.get('nome_canal')} ignorado: ultimo video ha {days_since_last} dias")
                        continue

                    channel["days_since_last_video"] = days_since_last

                # Adicionar metricas
                channel["inscritos"] = subscribers
                channel["total_videos"] = video_count

                # Calcular score de potencial
                channel["scout_score"] = self._calculate_scout_score(channel)

                validated.append(channel)

            except Exception as e:
                logger.warning(f"Erro validando canal: {e}")
                continue

        return validated

    async def _get_channel_stats(self, channel_id: str) -> Optional[Dict]:
        """Busca estatisticas de um canal"""
        try:
            api_key = self._get_api_key()
            if not api_key:
                return None

            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/channels"
                params = {
                    "key": api_key,
                    "id": channel_id,
                    "part": "statistics"
                }

                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        items = data.get("items", [])
                        if items:
                            stats = items[0].get("statistics", {})
                            return {
                                "subscriberCount": int(stats.get("subscriberCount", 0)),
                                "videoCount": int(stats.get("videoCount", 0)),
                                "viewCount": int(stats.get("viewCount", 0))
                            }
            return None

        except Exception as e:
            logger.error(f"Erro buscando stats do canal {channel_id}: {e}")
            return None

    async def _get_last_video_date(self, channel_id: str) -> Optional[datetime]:
        """Busca data do ultimo video publicado"""
        try:
            api_key = self._get_api_key()
            if not api_key:
                return None

            async with aiohttp.ClientSession() as session:
                # Buscar uploads playlist
                url = f"{self.base_url}/channels"
                params = {
                    "key": api_key,
                    "id": channel_id,
                    "part": "contentDetails"
                }

                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        return None

                    data = await response.json()
                    items = data.get("items", [])
                    if not items:
                        return None

                    uploads_playlist = items[0].get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")

                    if not uploads_playlist:
                        return None

                # Buscar ultimo video
                url = f"{self.base_url}/playlistItems"
                params = {
                    "key": api_key,
                    "playlistId": uploads_playlist,
                    "part": "snippet",
                    "maxResults": 1
                }

                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        items = data.get("items", [])
                        if items:
                            published = items[0].get("snippet", {}).get("publishedAt")
                            if published:
                                return datetime.fromisoformat(published.replace("Z", "+00:00"))

            return None

        except Exception as e:
            logger.error(f"Erro buscando ultimo video do canal {channel_id}: {e}")
            return None

    def _calculate_scout_score(self, channel: Dict) -> float:
        """
        Calcula score de potencial do canal descoberto.
        Score de 0-100.
        """
        score = 0.0

        # Inscritos (ate 40 pontos)
        subscribers = channel.get("inscritos", 0)
        if subscribers >= 100000:
            score += 40
        elif subscribers >= 50000:
            score += 35
        elif subscribers >= 10000:
            score += 25
        elif subscribers >= 5000:
            score += 15
        elif subscribers >= 1000:
            score += 10

        # Atividade recente (ate 30 pontos)
        days_since = channel.get("days_since_last_video", 999)
        if days_since <= 3:
            score += 30
        elif days_since <= 7:
            score += 25
        elif days_since <= 15:
            score += 15
        elif days_since <= 30:
            score += 5

        # Quantidade de videos (ate 30 pontos)
        videos = channel.get("total_videos", 0)
        if videos >= 100:
            score += 30
        elif videos >= 50:
            score += 25
        elif videos >= 20:
            score += 15
        elif videos >= 10:
            score += 10

        return round(score, 1)

    async def _save_discoveries(self, channels: List[Dict]) -> int:
        """
        Salva canais descobertos na tabela de sugestoes.
        Nao adiciona direto em canais_monitorados (precisa aprovacao humana).
        """
        saved = 0

        try:
            for channel in channels:
                try:
                    # Verificar se ja existe na tabela de sugestoes
                    existing = self.db.supabase.table("scout_discoveries")\
                        .select("id")\
                        .eq("channel_id", channel.get("channel_id"))\
                        .execute()

                    if existing.data:
                        logger.debug(f"Canal {channel.get('nome_canal')} ja existe nas sugestoes")
                        continue

                    # Inserir nova sugestao
                    self.db.supabase.table("scout_discoveries").insert({
                        "channel_id": channel.get("channel_id"),
                        "nome_canal": channel.get("nome_canal"),
                        "url_canal": channel.get("url_canal"),
                        "descricao": channel.get("descricao", "")[:500],  # Limitar tamanho
                        "subnicho_sugerido": channel.get("subnicho_sugerido"),
                        "inscritos": channel.get("inscritos", 0),
                        "total_videos": channel.get("total_videos", 0),
                        "scout_score": channel.get("scout_score", 0),
                        "days_since_last_video": channel.get("days_since_last_video"),
                        "discovered_at": datetime.now(timezone.utc).isoformat(),
                        "status": "pending"  # pending, approved, rejected
                    }).execute()

                    saved += 1
                    logger.info(f"[Scout] Salvo: {channel.get('nome_canal')} (score: {channel.get('scout_score')})")

                except Exception as e:
                    logger.warning(f"Erro salvando canal {channel.get('nome_canal')}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Erro ao salvar descobertas: {e}")

        return saved

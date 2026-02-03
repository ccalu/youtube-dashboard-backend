# ========================================
# TREND AGENT - Detector de Tendencias
# ========================================
# Funcao: Identificar videos/temas em alta AGORA
# Custo: ZERO (analisa dados do Supabase)
# ========================================

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict
import re

from .base import BaseAgent, AgentResult, AgentStatus

logger = logging.getLogger(__name__)


class TrendAgent(BaseAgent):
    """
    Agente responsavel por detectar tendencias em tempo real.

    O que analisa:
    1. Videos com crescimento anormal de views
    2. Temas que multiplos canais estao postando
    3. Padroes de titulo que estao funcionando
    4. Micronichos emergentes

    Algoritmo de deteccao:
    - Video recente (< 7 dias)
    - Views > media do canal * 2
    - Crescimento diario > 10%
    = TENDENCIA CONFIRMADA
    """

    def __init__(self, db_client):
        super().__init__(db_client)

        # Configuracoes de deteccao
        self.viral_threshold_multiplier = 2.0  # Views > media * 2
        self.min_views_threshold = 10000  # Minimo de views para considerar
        self.recent_days = 7  # Videos dos ultimos 7 dias
        self.trend_window_hours = 72  # Janela de 72h para detectar tendencias

    @property
    def name(self) -> str:
        return "TrendAgent"

    @property
    def description(self) -> str:
        return "Detecta videos e temas em tendencia analisando dados do Supabase"

    async def run(self) -> AgentResult:
        """Executa analise de tendencias"""
        result = self.create_result()

        try:
            logger.info(f"[{self.name}] Iniciando analise de tendencias...")

            # 1. Buscar videos recentes
            videos_recentes = await self._get_recent_videos()
            logger.info(f"[{self.name}] {len(videos_recentes)} videos recentes encontrados")

            if not videos_recentes:
                return self.complete_result(result, {
                    "trending_videos": [],
                    "trending_topics": [],
                    "message": "Nenhum video recente para analisar"
                })

            # 2. Buscar medias dos canais para comparacao
            canais_stats = await self._get_canais_average_stats()
            logger.info(f"[{self.name}] Stats de {len(canais_stats)} canais carregados")

            # 3. Detectar videos virais/trending
            trending_videos = self._detect_viral_videos(videos_recentes, canais_stats)
            logger.info(f"[{self.name}] {len(trending_videos)} videos em TENDENCIA detectados")

            # 4. Extrair temas/topicos em alta
            trending_topics = self._extract_trending_topics(trending_videos)
            logger.info(f"[{self.name}] {len(trending_topics)} topicos em TENDENCIA")

            # 5. Agrupar por subnicho
            trends_by_subnicho = self._group_trends_by_subnicho(trending_videos)

            # 6. Agrupar por idioma
            trends_by_language = self._group_trends_by_language(trending_videos)

            # 7. Salvar tendencias detectadas
            await self._save_trends(trending_videos, trending_topics)

            metrics = {
                "videos_analisados": len(videos_recentes),
                "videos_trending": len(trending_videos),
                "topicos_trending": len(trending_topics),
                "subnichos_com_trends": len(trends_by_subnicho),
                "idiomas_com_trends": len(trends_by_language)
            }

            return self.complete_result(result, {
                "trending_videos": trending_videos[:50],  # Top 50
                "trending_topics": trending_topics[:20],  # Top 20 topicos
                "by_subnicho": trends_by_subnicho,
                "by_language": trends_by_language,
                "summary": f"{len(trending_videos)} videos em tendencia, {len(trending_topics)} topicos quentes"
            }, metrics)

        except Exception as e:
            logger.error(f"[{self.name}] Erro: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return self.fail_result(result, str(e))

    async def _get_recent_videos(self) -> List[Dict]:
        """Busca videos publicados nos ultimos X dias"""
        try:
            cutoff_date = (datetime.now(timezone.utc) - timedelta(days=self.recent_days)).isoformat()

            # Buscar videos com paginacao
            all_videos = []
            batch_size = 1000
            offset = 0

            while True:
                response = self.db.supabase.table("videos_historico")\
                    .select("*, canais_monitorados!inner(nome_canal, subnicho, lingua, tipo)")\
                    .gte("data_publicacao", cutoff_date)\
                    .order("views_atuais", desc=True)\
                    .range(offset, offset + batch_size - 1)\
                    .execute()

                if not response.data:
                    break

                all_videos.extend(response.data)

                if len(response.data) < batch_size:
                    break

                offset += batch_size

            # Deduplicar por video_id (pegar coleta mais recente)
            videos_dict = {}
            for video in all_videos:
                video_id = video.get("video_id")
                data_coleta = video.get("data_coleta", "")

                if video_id not in videos_dict:
                    videos_dict[video_id] = video
                elif data_coleta > videos_dict[video_id].get("data_coleta", ""):
                    videos_dict[video_id] = video

            return list(videos_dict.values())

        except Exception as e:
            logger.error(f"Erro buscando videos recentes: {e}")
            return []

    async def _get_canais_average_stats(self) -> Dict[int, Dict]:
        """
        Busca estatisticas medias de cada canal para comparacao.
        Retorna: {canal_id: {"avg_views": X, "total_videos": Y}}
        """
        try:
            # Buscar todos os videos para calcular media
            all_videos = []
            batch_size = 1000
            offset = 0

            while True:
                response = self.db.supabase.table("videos_historico")\
                    .select("canal_id, video_id, views_atuais, data_coleta")\
                    .range(offset, offset + batch_size - 1)\
                    .execute()

                if not response.data:
                    break

                all_videos.extend(response.data)

                if len(response.data) < batch_size:
                    break

                offset += batch_size

            # Deduplicar por video_id
            videos_dict = {}
            for video in all_videos:
                video_id = video.get("video_id")
                data_coleta = video.get("data_coleta", "")

                if video_id not in videos_dict:
                    videos_dict[video_id] = video
                elif data_coleta > videos_dict[video_id].get("data_coleta", ""):
                    videos_dict[video_id] = video

            # Calcular stats por canal
            canal_videos = defaultdict(list)
            for video in videos_dict.values():
                canal_id = video.get("canal_id")
                views = video.get("views_atuais", 0)
                canal_videos[canal_id].append(views)

            # Calcular medias
            canais_stats = {}
            for canal_id, views_list in canal_videos.items():
                if views_list:
                    canais_stats[canal_id] = {
                        "avg_views": sum(views_list) / len(views_list),
                        "total_videos": len(views_list),
                        "max_views": max(views_list),
                        "min_views": min(views_list)
                    }

            return canais_stats

        except Exception as e:
            logger.error(f"Erro calculando stats de canais: {e}")
            return {}

    def _detect_viral_videos(self, videos: List[Dict], canais_stats: Dict) -> List[Dict]:
        """
        Detecta videos que estao viralizando.

        Criterios:
        - Views > media do canal * 2
        - Views > 10K (minimo absoluto)
        """
        trending = []

        for video in videos:
            try:
                canal_id = video.get("canal_id")
                views = video.get("views_atuais", 0)

                # Filtro minimo de views
                if views < self.min_views_threshold:
                    continue

                # Buscar stats do canal
                canal_stats = canais_stats.get(canal_id, {})
                avg_views = canal_stats.get("avg_views", 0)

                # Calcular multiplo da media
                if avg_views > 0:
                    views_multiplier = views / avg_views
                else:
                    views_multiplier = 0

                # Detectar tendencia
                is_trending = views_multiplier >= self.viral_threshold_multiplier

                if is_trending:
                    # Extrair info do canal
                    canal_info = video.get("canais_monitorados", {})

                    trending.append({
                        "video_id": video.get("video_id"),
                        "titulo": video.get("titulo"),
                        "url_video": video.get("url_video"),
                        "views": views,
                        "likes": video.get("likes", 0),
                        "data_publicacao": video.get("data_publicacao"),
                        "canal_id": canal_id,
                        "nome_canal": canal_info.get("nome_canal", "Unknown"),
                        "subnicho": canal_info.get("subnicho", "Unknown"),
                        "lingua": canal_info.get("lingua", "Unknown"),
                        "tipo_canal": canal_info.get("tipo", "minerado"),
                        "avg_views_canal": round(avg_views),
                        "views_multiplier": round(views_multiplier, 1),
                        "trend_score": self._calculate_trend_score(video, views_multiplier),
                        "detected_at": datetime.now(timezone.utc).isoformat()
                    })

            except Exception as e:
                logger.warning(f"Erro processando video: {e}")
                continue

        # Ordenar por score
        trending.sort(key=lambda x: x.get("trend_score", 0), reverse=True)

        return trending

    def _calculate_trend_score(self, video: Dict, views_multiplier: float) -> float:
        """
        Calcula score de tendencia (0-100).

        Fatores:
        - Multiplo da media (40%)
        - Views absolutas (30%)
        - Recencia (30%)
        """
        score = 0.0

        # Multiplo da media (ate 40 pontos)
        if views_multiplier >= 10:
            score += 40
        elif views_multiplier >= 5:
            score += 35
        elif views_multiplier >= 3:
            score += 25
        elif views_multiplier >= 2:
            score += 15

        # Views absolutas (ate 30 pontos)
        views = video.get("views_atuais", 0)
        if views >= 1000000:
            score += 30
        elif views >= 500000:
            score += 25
        elif views >= 100000:
            score += 20
        elif views >= 50000:
            score += 15
        elif views >= 10000:
            score += 10

        # Recencia (ate 30 pontos)
        pub_date = video.get("data_publicacao")
        if pub_date:
            try:
                pub_datetime = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                days_old = (datetime.now(timezone.utc) - pub_datetime).days

                if days_old <= 1:
                    score += 30
                elif days_old <= 3:
                    score += 25
                elif days_old <= 7:
                    score += 15
                elif days_old <= 14:
                    score += 5
            except:
                pass

        return round(score, 1)

    def _extract_trending_topics(self, trending_videos: List[Dict]) -> List[Dict]:
        """
        Extrai topicos/temas que estao em alta baseado nos titulos.
        Agrupa por palavras-chave e conta frequencia.
        """
        # Palavras comuns para ignorar
        stopwords = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
            "be", "have", "has", "had", "do", "does", "did", "will", "would",
            "could", "should", "may", "might", "must", "shall", "can", "this",
            "that", "these", "those", "i", "you", "he", "she", "it", "we", "they",
            "what", "which", "who", "whom", "whose", "when", "where", "why", "how",
            "all", "each", "every", "both", "few", "more", "most", "other", "some",
            "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too",
            "very", "just", "about", "over", "into", "through", "during", "before",
            "after", "above", "below", "up", "down", "out", "off", "again", "then",
            "once", "here", "there", "why", "how", "any", "el", "la", "los", "las",
            "de", "del", "en", "que", "por", "para", "con", "una", "uno", "es"
        }

        # Contar palavras-chave
        keyword_count = defaultdict(lambda: {"count": 0, "views": 0, "videos": []})

        for video in trending_videos:
            titulo = video.get("titulo", "")

            # Limpar titulo e extrair palavras
            titulo_clean = re.sub(r'[^\w\s]', ' ', titulo.lower())
            words = titulo_clean.split()

            # Filtrar stopwords e palavras curtas
            keywords = [w for w in words if w not in stopwords and len(w) >= 3]

            # Contar
            for kw in keywords:
                keyword_count[kw]["count"] += 1
                keyword_count[kw]["views"] += video.get("views", 0)
                if len(keyword_count[kw]["videos"]) < 5:
                    keyword_count[kw]["videos"].append(video.get("titulo", ""))

        # Filtrar keywords com pelo menos 2 ocorrencias
        trending_topics = []
        for keyword, stats in keyword_count.items():
            if stats["count"] >= 2:
                trending_topics.append({
                    "keyword": keyword,
                    "frequency": stats["count"],
                    "total_views": stats["views"],
                    "avg_views": round(stats["views"] / stats["count"]),
                    "example_titles": stats["videos"][:3],
                    "topic_score": self._calculate_topic_score(stats)
                })

        # Ordenar por score
        trending_topics.sort(key=lambda x: x.get("topic_score", 0), reverse=True)

        return trending_topics

    def _calculate_topic_score(self, stats: Dict) -> float:
        """Calcula score do topico baseado em frequencia e views"""
        score = 0.0

        # Frequencia (ate 50 pontos)
        freq = stats.get("count", 0)
        if freq >= 10:
            score += 50
        elif freq >= 5:
            score += 35
        elif freq >= 3:
            score += 20
        elif freq >= 2:
            score += 10

        # Views totais (ate 50 pontos)
        views = stats.get("views", 0)
        if views >= 1000000:
            score += 50
        elif views >= 500000:
            score += 40
        elif views >= 100000:
            score += 25
        elif views >= 50000:
            score += 15

        return round(score, 1)

    def _group_trends_by_subnicho(self, trending_videos: List[Dict]) -> Dict[str, List[Dict]]:
        """Agrupa tendencias por subnicho"""
        by_subnicho = defaultdict(list)

        for video in trending_videos:
            subnicho = video.get("subnicho", "Unknown")
            by_subnicho[subnicho].append(video)

        # Ordenar cada grupo por trend_score
        for subnicho in by_subnicho:
            by_subnicho[subnicho].sort(key=lambda x: x.get("trend_score", 0), reverse=True)

        return dict(by_subnicho)

    def _group_trends_by_language(self, trending_videos: List[Dict]) -> Dict[str, List[Dict]]:
        """Agrupa tendencias por idioma"""
        by_language = defaultdict(list)

        for video in trending_videos:
            lingua = video.get("lingua", "Unknown")
            by_language[lingua].append(video)

        # Ordenar cada grupo por trend_score
        for lingua in by_language:
            by_language[lingua].sort(key=lambda x: x.get("trend_score", 0), reverse=True)

        return dict(by_language)

    async def _save_trends(self, trending_videos: List[Dict], trending_topics: List[Dict]):
        """Salva tendencias detectadas para historico"""
        try:
            # Salvar resumo diario
            today = datetime.now(timezone.utc).date().isoformat()

            trend_summary = {
                "data": today,
                "total_trending_videos": len(trending_videos),
                "total_trending_topics": len(trending_topics),
                "top_videos": [v.get("video_id") for v in trending_videos[:10]],
                "top_topics": [t.get("keyword") for t in trending_topics[:10]],
                "created_at": datetime.now(timezone.utc).isoformat()
            }

            # Verificar se ja existe registro de hoje
            existing = self.db.supabase.table("trend_history")\
                .select("id")\
                .eq("data", today)\
                .execute()

            if existing.data:
                # Atualizar
                self.db.supabase.table("trend_history")\
                    .update(trend_summary)\
                    .eq("data", today)\
                    .execute()
            else:
                # Inserir
                self.db.supabase.table("trend_history")\
                    .insert(trend_summary)\
                    .execute()

            logger.info(f"[{self.name}] Tendencias salvas para {today}")

        except Exception as e:
            # Se tabela nao existe, ignora (sera criada depois)
            logger.warning(f"Nao foi possivel salvar tendencias: {e}")

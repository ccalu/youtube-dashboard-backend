# ========================================
# ADVISOR AGENT - Conselheiro Estrategico
# ========================================
# Funcao: Transformar dados em ACOES concretas
# Custo: ZERO (analisa dados do Supabase)
# ========================================

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from collections import defaultdict
import statistics
import re

from .base import BaseAgent, AgentResult, AgentStatus

logger = logging.getLogger(__name__)


class AdvisorAgent(BaseAgent):
    """
    Agente responsavel por gerar recomendacoes acionaveis.

    Para cada canal, responde:
    1. "Qual micronicho voce deveria explorar HOJE?"
    2. "Qual estrutura de titulo usar?"
    3. "Qual tema tem maior probabilidade de viral?"
    4. "Quais videos de concorrentes clonar inteligentemente?"

    Priorizacao por Score:
    SCORE = (probabilidade_viral * 0.4) +
            (baixa_competicao * 0.3) +
            (relevancia_audiencia * 0.3)
    """

    def __init__(self, db_client):
        super().__init__(db_client)

        # Pesos para calculo de score
        self.weight_viral_probability = 0.4
        self.weight_low_competition = 0.3
        self.weight_audience_relevance = 0.3

    @property
    def name(self) -> str:
        return "AdvisorAgent"

    @property
    def description(self) -> str:
        return "Gera recomendacoes estrategicas acionaveis para cada canal"

    async def run(self) -> AgentResult:
        """Executa geracao de recomendacoes"""
        result = self.create_result()

        try:
            logger.info(f"[{self.name}] Iniciando geracao de recomendacoes...")

            # 1. Buscar nossos canais
            nossos_canais = await self._get_our_channels()
            logger.info(f"[{self.name}] {len(nossos_canais)} canais nossos encontrados")

            # 2. Buscar videos de sucesso dos concorrentes
            videos_sucesso = await self._get_competitor_successful_videos()
            logger.info(f"[{self.name}] {len(videos_sucesso)} videos de sucesso identificados")

            # 3. Buscar tendencias recentes
            tendencias = await self._get_recent_trends()
            logger.info(f"[{self.name}] {len(tendencias)} tendencias identificadas")

            # 4. Gerar recomendacoes por canal
            recommendations_by_channel = {}
            for canal in nossos_canais:
                recs = self._generate_channel_recommendations(
                    canal, videos_sucesso, tendencias
                )
                recommendations_by_channel[canal["id"]] = {
                    "canal": canal,
                    "recommendations": recs
                }

            # 5. Gerar recomendacoes globais (top oportunidades)
            global_recommendations = self._generate_global_recommendations(
                videos_sucesso, tendencias, nossos_canais
            )

            # 6. Priorizar e limitar
            all_recommendations = []
            for canal_id, data in recommendations_by_channel.items():
                for rec in data["recommendations"]:
                    rec["canal_id"] = canal_id
                    rec["canal_nome"] = data["canal"].get("nome_canal")
                    all_recommendations.append(rec)

            # Ordenar por score
            all_recommendations.sort(key=lambda x: x.get("score", 0), reverse=True)

            # 7. Gerar resumo executivo
            executive_summary = self._generate_executive_summary(
                all_recommendations, nossos_canais, videos_sucesso
            )

            metrics = {
                "canais_analisados": len(nossos_canais),
                "videos_sucesso_analisados": len(videos_sucesso),
                "tendencias_detectadas": len(tendencias),
                "recomendacoes_geradas": len(all_recommendations),
                "recomendacoes_globais": len(global_recommendations)
            }

            return self.complete_result(result, {
                "by_channel": recommendations_by_channel,
                "global_recommendations": global_recommendations,
                "top_recommendations": all_recommendations[:30],
                "executive_summary": executive_summary,
                "summary": f"{len(all_recommendations)} recomendacoes geradas para {len(nossos_canais)} canais"
            }, metrics)

        except Exception as e:
            logger.error(f"[{self.name}] Erro: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return self.fail_result(result, str(e))

    async def _get_our_channels(self) -> List[Dict]:
        """Busca nossos canais com metricas"""
        try:
            response = self.db.supabase.table("canais_monitorados")\
                .select("*")\
                .eq("status", "ativo")\
                .eq("tipo", "nosso")\
                .execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Erro buscando nossos canais: {e}")
            return []

    async def _get_competitor_successful_videos(self) -> List[Dict]:
        """
        Busca videos de sucesso dos concorrentes (minerados).
        Sucesso = views > 50K nos ultimos 30 dias.
        """
        try:
            cutoff_date = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()

            all_videos = []
            batch_size = 1000
            offset = 0

            while True:
                response = self.db.supabase.table("videos_historico")\
                    .select("*, canais_monitorados!inner(id, nome_canal, subnicho, lingua, tipo)")\
                    .gte("data_publicacao", cutoff_date)\
                    .gte("views_atuais", 50000)\
                    .eq("canais_monitorados.tipo", "minerado")\
                    .range(offset, offset + batch_size - 1)\
                    .execute()

                if not response.data:
                    break

                all_videos.extend(response.data)

                if len(response.data) < batch_size:
                    break

                offset += batch_size

            # Deduplicar
            videos_dict = {}
            for video in all_videos:
                video_id = video.get("video_id")
                if video_id not in videos_dict:
                    videos_dict[video_id] = video

            return list(videos_dict.values())

        except Exception as e:
            logger.error(f"Erro buscando videos de sucesso: {e}")
            return []

    async def _get_recent_trends(self) -> List[Dict]:
        """Busca tendencias recentes"""
        try:
            # Buscar videos viralizando (> 100K views em < 7 dias)
            cutoff_date = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

            response = self.db.supabase.table("videos_historico")\
                .select("*, canais_monitorados!inner(subnicho, lingua)")\
                .gte("data_publicacao", cutoff_date)\
                .gte("views_atuais", 100000)\
                .order("views_atuais", desc=True)\
                .limit(100)\
                .execute()

            trends = []
            if response.data:
                for video in response.data:
                    canal_info = video.get("canais_monitorados", {})
                    trends.append({
                        "titulo": video.get("titulo"),
                        "views": video.get("views_atuais"),
                        "subnicho": canal_info.get("subnicho"),
                        "lingua": canal_info.get("lingua"),
                        "video_id": video.get("video_id"),
                        "url_video": video.get("url_video")
                    })

            return trends

        except Exception as e:
            logger.error(f"Erro buscando tendencias: {e}")
            return []

    def _generate_channel_recommendations(
        self,
        canal: Dict,
        videos_sucesso: List[Dict],
        tendencias: List[Dict]
    ) -> List[Dict]:
        """
        Gera recomendacoes especificas para um canal.
        """
        recommendations = []
        canal_subnicho = canal.get("subnicho", "").lower()
        canal_lingua = canal.get("lingua", "").lower()

        # 1. Buscar videos de sucesso no MESMO subnicho
        same_subnicho_videos = [
            v for v in videos_sucesso
            if v.get("canais_monitorados", {}).get("subnicho", "").lower() == canal_subnicho
        ]

        if same_subnicho_videos:
            # Top 5 videos para clonar
            top_videos = sorted(same_subnicho_videos, key=lambda x: x.get("views_atuais", 0), reverse=True)[:5]

            for video in top_videos:
                score = self._calculate_recommendation_score(
                    video, canal_subnicho, canal_lingua
                )
                recommendations.append({
                    "type": "clone_video",
                    "action": f"Criar video similar a: {video.get('titulo', '')[:50]}...",
                    "original_video": {
                        "titulo": video.get("titulo"),
                        "views": video.get("views_atuais"),
                        "url": video.get("url_video"),
                        "canal": video.get("canais_monitorados", {}).get("nome_canal")
                    },
                    "reason": f"Video tem {video.get('views_atuais', 0):,} views no mesmo subnicho",
                    "score": score,
                    "priority": "high" if score > 70 else "medium"
                })

        # 2. Buscar tendencias no mesmo subnicho
        subnicho_trends = [
            t for t in tendencias
            if t.get("subnicho", "").lower() == canal_subnicho
        ]

        for trend in subnicho_trends[:3]:
            score = self._calculate_recommendation_score(
                {"views_atuais": trend.get("views")},
                canal_subnicho, canal_lingua
            )
            recommendations.append({
                "type": "trend_topic",
                "action": f"Aproveitar tendencia: {trend.get('titulo', '')[:50]}...",
                "trend": trend,
                "reason": f"Tema viralizando com {trend.get('views', 0):,} views",
                "score": score,
                "priority": "high"
            })

        # 3. Buscar videos de sucesso em OUTRO idioma (cross-language)
        other_language_videos = [
            v for v in videos_sucesso
            if v.get("canais_monitorados", {}).get("subnicho", "").lower() == canal_subnicho
            and v.get("canais_monitorados", {}).get("lingua", "").lower() != canal_lingua
        ]

        for video in other_language_videos[:3]:
            source_lang = video.get("canais_monitorados", {}).get("lingua", "Unknown")
            score = self._calculate_recommendation_score(
                video, canal_subnicho, canal_lingua, is_cross_language=True
            )
            recommendations.append({
                "type": "cross_language",
                "action": f"Adaptar de {source_lang}: {video.get('titulo', '')[:40]}...",
                "original_video": {
                    "titulo": video.get("titulo"),
                    "views": video.get("views_atuais"),
                    "url": video.get("url_video"),
                    "lingua": source_lang
                },
                "reason": f"Bombou em {source_lang} ({video.get('views_atuais', 0):,} views), adaptar para {canal_lingua}",
                "score": score,
                "priority": "medium"
            })

        # 4. Analisar estruturas de titulo que funcionam
        title_patterns = self._analyze_successful_title_patterns(same_subnicho_videos)
        if title_patterns:
            recommendations.append({
                "type": "title_pattern",
                "action": f"Usar estrutura de titulo: {title_patterns[0]}",
                "patterns": title_patterns[:3],
                "reason": "Estruturas de titulo com melhor performance no subnicho",
                "score": 60,
                "priority": "medium"
            })

        # Ordenar por score
        recommendations.sort(key=lambda x: x.get("score", 0), reverse=True)

        return recommendations[:10]  # Top 10 por canal

    def _calculate_recommendation_score(
        self,
        video: Dict,
        target_subnicho: str,
        target_lingua: str,
        is_cross_language: bool = False
    ) -> float:
        """
        Calcula score de uma recomendacao.

        SCORE = (probabilidade_viral * 0.4) +
                (baixa_competicao * 0.3) +
                (relevancia_audiencia * 0.3)
        """
        score = 0.0

        # 1. Probabilidade viral (baseado em views)
        views = video.get("views_atuais", 0)
        if views >= 500000:
            viral_score = 100
        elif views >= 200000:
            viral_score = 80
        elif views >= 100000:
            viral_score = 60
        elif views >= 50000:
            viral_score = 40
        else:
            viral_score = 20

        # 2. Baixa competicao (bonus para cross-language)
        if is_cross_language:
            competition_score = 80  # Menos competicao em outro idioma
        else:
            competition_score = 50  # Competicao normal

        # 3. Relevancia (mesmo subnicho = mais relevante)
        relevance_score = 70  # Ja estamos filtrando por subnicho

        # Calcular score final
        score = (
            (viral_score * self.weight_viral_probability) +
            (competition_score * self.weight_low_competition) +
            (relevance_score * self.weight_audience_relevance)
        )

        return round(score, 1)

    def _analyze_successful_title_patterns(self, videos: List[Dict]) -> List[str]:
        """Analisa padroes de titulo mais comuns nos videos de sucesso"""
        patterns = []

        # Verificar padroes comuns
        question_videos = [v for v in videos if "?" in v.get("titulo", "")]
        exclamation_videos = [v for v in videos if "!" in v.get("titulo", "")]
        number_videos = [v for v in videos if re.search(r'\d+', v.get("titulo", ""))]

        if len(question_videos) > len(videos) * 0.3:
            patterns.append("Usar pergunta no titulo (?)")
        if len(exclamation_videos) > len(videos) * 0.3:
            patterns.append("Usar exclamacao (!)")
        if len(number_videos) > len(videos) * 0.3:
            patterns.append("Incluir numeros (Top 10, 5 segredos...)")

        return patterns

    def _generate_global_recommendations(
        self,
        videos_sucesso: List[Dict],
        tendencias: List[Dict],
        nossos_canais: List[Dict]
    ) -> List[Dict]:
        """
        Gera recomendacoes globais (oportunidades para toda operacao).
        """
        recommendations = []

        # 1. Subnichos com mais virais
        subnicho_virals = defaultdict(int)
        for video in videos_sucesso:
            subnicho = video.get("canais_monitorados", {}).get("subnicho", "Unknown")
            if video.get("views_atuais", 0) >= 100000:
                subnicho_virals[subnicho] += 1

        hot_subnichos = sorted(subnicho_virals.items(), key=lambda x: x[1], reverse=True)[:5]
        for subnicho, count in hot_subnichos:
            recommendations.append({
                "type": "hot_subnicho",
                "action": f"Aumentar producao no subnicho: {subnicho}",
                "reason": f"{count} videos virais nos ultimos 30 dias",
                "priority": "high",
                "data": {"subnicho": subnicho, "viral_count": count}
            })

        # 2. Idiomas subexplorados
        nossos_idiomas = set(c.get("lingua", "").lower() for c in nossos_canais)
        all_idiomas = set(v.get("canais_monitorados", {}).get("lingua", "").lower() for v in videos_sucesso)
        missing_idiomas = all_idiomas - nossos_idiomas

        for idioma in list(missing_idiomas)[:3]:
            recommendations.append({
                "type": "new_language",
                "action": f"Considerar expandir para idioma: {idioma}",
                "reason": "Idioma com videos de sucesso mas sem presenca nossa",
                "priority": "medium",
                "data": {"idioma": idioma}
            })

        # 3. Temas quentes globais
        tema_count = defaultdict(lambda: {"count": 0, "views": 0})
        for trend in tendencias:
            titulo = trend.get("titulo", "").lower()
            words = re.findall(r'\b[a-zA-Z]{4,}\b', titulo)
            for word in words:
                tema_count[word]["count"] += 1
                tema_count[word]["views"] += trend.get("views", 0)

        hot_temas = sorted(tema_count.items(), key=lambda x: x[1]["views"], reverse=True)[:5]
        for tema, stats in hot_temas:
            recommendations.append({
                "type": "hot_topic",
                "action": f"Explorar tema: '{tema}'",
                "reason": f"Aparece em {stats['count']} trends com {stats['views']:,} views totais",
                "priority": "high",
                "data": stats
            })

        return recommendations

    def _generate_executive_summary(
        self,
        all_recommendations: List[Dict],
        canais: List[Dict],
        videos_sucesso: List[Dict]
    ) -> Dict:
        """Gera resumo executivo para apresentacao"""

        # Contar tipos de recomendacoes
        rec_types = defaultdict(int)
        for rec in all_recommendations:
            rec_types[rec.get("type", "other")] += 1

        # Top 5 acoes
        top_actions = [rec.get("action") for rec in all_recommendations[:5]]

        # Canais que mais precisam de atencao
        canais_with_recs = defaultdict(int)
        for rec in all_recommendations:
            if rec.get("canal_nome"):
                canais_with_recs[rec["canal_nome"]] += 1

        return {
            "total_recommendations": len(all_recommendations),
            "recommendation_types": dict(rec_types),
            "top_5_actions": top_actions,
            "channels_analyzed": len(canais),
            "competitor_videos_analyzed": len(videos_sucesso),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "key_insight": f"Foco principal: {all_recommendations[0].get('action') if all_recommendations else 'N/A'}"
        }

# ========================================
# CORRELATION AGENT - Cruzamento Cross-Language
# ========================================
# Funcao: Encontrar correlacoes entre idiomas e subnichos
# Custo: ZERO (analisa dados do Supabase)
# ========================================

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict
import re
import statistics

from .base import BaseAgent, AgentResult, AgentStatus

logger = logging.getLogger(__name__)


class CorrelationAgent(BaseAgent):
    """
    Agente responsavel por encontrar correlacoes cross-language.

    Cruzamentos:
    1. Titulo X funcionou em EN -> Probabilidade em ES/PT/JP?
    2. Tema Y performa bem no subnicho A -> Testar no subnicho B?
    3. Estrutura Z tem CTR alto em Terror -> Aplicar em Reis Perversos?

    Objetivo: Identificar oportunidades de conteudo que deu certo
    em um contexto e pode ser replicado em outro.
    """

    def __init__(self, db_client):
        super().__init__(db_client)

        # Threshold para considerar video como "sucesso"
        self.success_threshold_multiplier = 1.5  # 50% acima da media

        # Idiomas suportados
        self.languages = [
            "english", "spanish", "portuguese", "japanese",
            "korean", "arabic", "italian", "french", "german"
        ]

    @property
    def name(self) -> str:
        return "CorrelationAgent"

    @property
    def description(self) -> str:
        return "Encontra correlacoes entre idiomas e subnichos para identificar oportunidades de replicacao"

    async def run(self) -> AgentResult:
        """Executa analise de correlacoes"""
        result = self.create_result()

        try:
            logger.info(f"[{self.name}] Iniciando analise de correlacoes cross-language...")

            # 1. Buscar todos os videos
            videos = await self._get_all_videos()
            logger.info(f"[{self.name}] {len(videos)} videos carregados")

            if not videos:
                return self.complete_result(result, {
                    "correlations": [],
                    "message": "Nenhum video para analisar"
                })

            # 2. Identificar videos de sucesso
            successful_videos = self._identify_successful_videos(videos)
            logger.info(f"[{self.name}] {len(successful_videos)} videos de SUCESSO identificados")

            # 3. Extrair temas/keywords dos videos de sucesso
            success_themes = self._extract_themes_from_successful(successful_videos)
            logger.info(f"[{self.name}] {len(success_themes)} temas de sucesso extraidos")

            # 4. Encontrar oportunidades cross-language
            cross_language_opportunities = self._find_cross_language_opportunities(
                successful_videos, videos
            )
            logger.info(f"[{self.name}] {len(cross_language_opportunities)} oportunidades cross-language")

            # 5. Encontrar oportunidades cross-subnicho
            cross_subnicho_opportunities = self._find_cross_subnicho_opportunities(
                successful_videos, videos
            )
            logger.info(f"[{self.name}] {len(cross_subnicho_opportunities)} oportunidades cross-subnicho")

            # 6. Gerar matriz de correlacao lingua x subnicho
            correlation_matrix = self._build_correlation_matrix(videos)

            # 7. Gerar recomendacoes
            recommendations = self._generate_recommendations(
                cross_language_opportunities,
                cross_subnicho_opportunities,
                success_themes
            )

            metrics = {
                "videos_analisados": len(videos),
                "videos_sucesso": len(successful_videos),
                "temas_sucesso": len(success_themes),
                "oportunidades_cross_language": len(cross_language_opportunities),
                "oportunidades_cross_subnicho": len(cross_subnicho_opportunities),
                "recomendacoes_geradas": len(recommendations)
            }

            return self.complete_result(result, {
                "successful_videos": successful_videos[:50],
                "success_themes": success_themes[:30],
                "cross_language_opportunities": cross_language_opportunities[:30],
                "cross_subnicho_opportunities": cross_subnicho_opportunities[:30],
                "correlation_matrix": correlation_matrix,
                "recommendations": recommendations,
                "summary": f"{len(recommendations)} oportunidades de replicacao identificadas"
            }, metrics)

        except Exception as e:
            logger.error(f"[{self.name}] Erro: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return self.fail_result(result, str(e))

    async def _get_all_videos(self) -> List[Dict]:
        """Busca todos os videos com info do canal"""
        try:
            all_videos = []
            batch_size = 1000
            offset = 0

            while True:
                response = self.db.supabase.table("videos_historico")\
                    .select("*, canais_monitorados!inner(id, nome_canal, subnicho, lingua, tipo)")\
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
                data_coleta = video.get("data_coleta", "")

                if video_id not in videos_dict:
                    videos_dict[video_id] = video
                elif data_coleta > videos_dict[video_id].get("data_coleta", ""):
                    videos_dict[video_id] = video

            return list(videos_dict.values())

        except Exception as e:
            logger.error(f"Erro buscando videos: {e}")
            return []

    def _identify_successful_videos(self, videos: List[Dict]) -> List[Dict]:
        """
        Identifica videos que tiveram sucesso acima da media.
        Sucesso = views > media do subnicho * 1.5
        """
        # Calcular media por subnicho
        subnicho_views = defaultdict(list)
        for video in videos:
            canal_info = video.get("canais_monitorados", {})
            subnicho = canal_info.get("subnicho", "Unknown")
            views = video.get("views_atuais", 0)
            subnicho_views[subnicho].append(views)

        subnicho_avg = {}
        for subnicho, views_list in subnicho_views.items():
            if views_list:
                subnicho_avg[subnicho] = statistics.mean(views_list)

        # Filtrar videos de sucesso
        successful = []
        for video in videos:
            canal_info = video.get("canais_monitorados", {})
            subnicho = canal_info.get("subnicho", "Unknown")
            views = video.get("views_atuais", 0)

            avg = subnicho_avg.get(subnicho, 0)
            threshold = avg * self.success_threshold_multiplier

            if views >= threshold and views > 10000:  # Minimo 10K views
                video_data = {
                    "video_id": video.get("video_id"),
                    "titulo": video.get("titulo"),
                    "views": views,
                    "subnicho": subnicho,
                    "lingua": canal_info.get("lingua", "Unknown"),
                    "canal": canal_info.get("nome_canal", "Unknown"),
                    "tipo_canal": canal_info.get("tipo", "minerado"),
                    "success_ratio": round(views / avg, 2) if avg > 0 else 1.0,
                    "url_video": video.get("url_video")
                }
                successful.append(video_data)

        # Ordenar por success_ratio
        successful.sort(key=lambda x: x.get("success_ratio", 0), reverse=True)
        return successful

    def _extract_themes_from_successful(self, successful_videos: List[Dict]) -> List[Dict]:
        """
        Extrai temas/keywords dos videos de sucesso.
        """
        theme_stats = defaultdict(lambda: {
            "count": 0,
            "total_views": 0,
            "languages": set(),
            "subnichos": set(),
            "examples": []
        })

        stopwords = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "is", "was", "are", "were", "this", "that",
            "de", "la", "el", "en", "que", "por", "para", "con"
        }

        for video in successful_videos:
            titulo = video.get("titulo", "").lower()
            words = re.findall(r'\b[a-zA-Z]{3,}\b', titulo)

            keywords = [w for w in words if w not in stopwords]

            for kw in keywords:
                theme_stats[kw]["count"] += 1
                theme_stats[kw]["total_views"] += video.get("views", 0)
                theme_stats[kw]["languages"].add(video.get("lingua", "Unknown"))
                theme_stats[kw]["subnichos"].add(video.get("subnicho", "Unknown"))
                if len(theme_stats[kw]["examples"]) < 3:
                    theme_stats[kw]["examples"].append(video.get("titulo", ""))

        # Converter para lista
        themes = []
        for keyword, stats in theme_stats.items():
            if stats["count"] >= 3:  # Minimo 3 ocorrencias
                themes.append({
                    "keyword": keyword,
                    "frequency": stats["count"],
                    "total_views": stats["total_views"],
                    "avg_views": round(stats["total_views"] / stats["count"]),
                    "languages": list(stats["languages"]),
                    "subnichos": list(stats["subnichos"]),
                    "cross_language_potential": len(stats["languages"]) < len(self.languages),
                    "examples": stats["examples"]
                })

        # Ordenar por potencial (views + cross-language)
        themes.sort(key=lambda x: (x.get("avg_views", 0), x.get("cross_language_potential", False)), reverse=True)
        return themes

    def _find_cross_language_opportunities(
        self,
        successful_videos: List[Dict],
        all_videos: List[Dict]
    ) -> List[Dict]:
        """
        Encontra temas que bombaram em um idioma mas nao existem em outros.
        """
        # Mapear temas por idioma
        themes_by_language = defaultdict(lambda: defaultdict(list))

        for video in successful_videos:
            titulo = video.get("titulo", "").lower()
            lingua = video.get("lingua", "Unknown").lower()
            words = re.findall(r'\b[a-zA-Z]{4,}\b', titulo)

            for word in words:
                themes_by_language[lingua][word].append(video)

        # Mapear todos os temas existentes por idioma (para saber o que JA existe)
        existing_themes = defaultdict(set)
        for video in all_videos:
            canal_info = video.get("canais_monitorados", {})
            titulo = video.get("titulo", "").lower()
            lingua = canal_info.get("lingua", "Unknown").lower()
            words = re.findall(r'\b[a-zA-Z]{4,}\b', titulo)

            for word in words:
                existing_themes[lingua].add(word)

        # Encontrar oportunidades
        opportunities = []

        for source_lang, themes in themes_by_language.items():
            for theme, videos in themes.items():
                if len(videos) < 2:  # Precisa ter pelo menos 2 videos de sucesso
                    continue

                # Verificar em quais idiomas NAO existe
                missing_languages = []
                for lang in self.languages:
                    lang_lower = lang.lower()
                    if lang_lower != source_lang and theme not in existing_themes[lang_lower]:
                        missing_languages.append(lang)

                if missing_languages:
                    avg_views = statistics.mean([v.get("views", 0) for v in videos])
                    opportunities.append({
                        "theme": theme,
                        "source_language": source_lang,
                        "success_count": len(videos),
                        "avg_views": round(avg_views),
                        "missing_in_languages": missing_languages,
                        "opportunity_score": round(avg_views * len(missing_languages) / 100000, 2),
                        "example_titles": [v.get("titulo") for v in videos[:3]],
                        "recommendation": f"Tema '{theme}' bombou em {source_lang} com {round(avg_views):,} views media. Nao existe em: {', '.join(missing_languages)}"
                    })

        # Ordenar por opportunity_score
        opportunities.sort(key=lambda x: x.get("opportunity_score", 0), reverse=True)
        return opportunities

    def _find_cross_subnicho_opportunities(
        self,
        successful_videos: List[Dict],
        all_videos: List[Dict]
    ) -> List[Dict]:
        """
        Encontra temas que funcionaram em um subnicho e podem ser testados em outro.
        """
        # Mapear temas por subnicho
        themes_by_subnicho = defaultdict(lambda: defaultdict(list))

        for video in successful_videos:
            titulo = video.get("titulo", "").lower()
            subnicho = video.get("subnicho", "Unknown")
            words = re.findall(r'\b[a-zA-Z]{4,}\b', titulo)

            for word in words:
                themes_by_subnicho[subnicho][word].append(video)

        # Listar todos os subnichos
        all_subnichos = set()
        for video in all_videos:
            canal_info = video.get("canais_monitorados", {})
            all_subnichos.add(canal_info.get("subnicho", "Unknown"))

        # Encontrar oportunidades
        opportunities = []

        for source_subnicho, themes in themes_by_subnicho.items():
            for theme, videos in themes.items():
                if len(videos) < 2:
                    continue

                # Subnichos onde o tema pode ser relevante
                potential_subnichos = []
                for subnicho in all_subnichos:
                    if subnicho != source_subnicho:
                        # Verificar se o tema NAO existe nesse subnicho
                        exists = False
                        for video in all_videos:
                            canal_info = video.get("canais_monitorados", {})
                            if canal_info.get("subnicho") == subnicho:
                                if theme in video.get("titulo", "").lower():
                                    exists = True
                                    break
                        if not exists:
                            potential_subnichos.append(subnicho)

                if potential_subnichos:
                    avg_views = statistics.mean([v.get("views", 0) for v in videos])
                    opportunities.append({
                        "theme": theme,
                        "source_subnicho": source_subnicho,
                        "success_count": len(videos),
                        "avg_views": round(avg_views),
                        "potential_subnichos": potential_subnichos[:5],
                        "opportunity_score": round(avg_views * len(potential_subnichos) / 100000, 2),
                        "example_titles": [v.get("titulo") for v in videos[:3]],
                        "recommendation": f"Tema '{theme}' funciona bem em {source_subnicho}. Testar em: {', '.join(potential_subnichos[:3])}"
                    })

        opportunities.sort(key=lambda x: x.get("opportunity_score", 0), reverse=True)
        return opportunities

    def _build_correlation_matrix(self, videos: List[Dict]) -> Dict[str, Dict[str, Dict]]:
        """
        Constroi matriz de correlacao lingua x subnicho.
        Mostra performance media em cada combinacao.
        """
        matrix = defaultdict(lambda: defaultdict(list))

        for video in videos:
            canal_info = video.get("canais_monitorados", {})
            lingua = canal_info.get("lingua", "Unknown")
            subnicho = canal_info.get("subnicho", "Unknown")
            views = video.get("views_atuais", 0)

            matrix[lingua][subnicho].append(views)

        # Calcular medias
        result = {}
        for lingua, subnichos in matrix.items():
            result[lingua] = {}
            for subnicho, views_list in subnichos.items():
                result[lingua][subnicho] = {
                    "count": len(views_list),
                    "avg_views": round(statistics.mean(views_list)) if views_list else 0,
                    "max_views": max(views_list) if views_list else 0
                }

        return result

    def _generate_recommendations(
        self,
        cross_language: List[Dict],
        cross_subnicho: List[Dict],
        themes: List[Dict]
    ) -> List[Dict]:
        """
        Gera recomendacoes priorizadas.
        """
        recommendations = []

        # Top oportunidades cross-language
        for opp in cross_language[:10]:
            recommendations.append({
                "type": "cross_language",
                "priority": "high" if opp.get("opportunity_score", 0) > 5 else "medium",
                "action": f"Criar video sobre '{opp['theme']}' em {opp['missing_in_languages'][0]}",
                "reason": f"Tema tem {opp['avg_views']:,} views media em {opp['source_language']}",
                "potential_views": opp.get("avg_views", 0),
                "data": opp
            })

        # Top oportunidades cross-subnicho
        for opp in cross_subnicho[:10]:
            recommendations.append({
                "type": "cross_subnicho",
                "priority": "medium" if opp.get("opportunity_score", 0) > 3 else "low",
                "action": f"Testar tema '{opp['theme']}' em {opp['potential_subnichos'][0]}",
                "reason": f"Funciona bem em {opp['source_subnicho']} com {opp['avg_views']:,} views",
                "potential_views": opp.get("avg_views", 0),
                "data": opp
            })

        # Ordenar por potencial
        recommendations.sort(key=lambda x: x.get("potential_views", 0), reverse=True)
        return recommendations

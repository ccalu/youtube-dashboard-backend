# ========================================
# PATTERN AGENT - Analisador de Padroes
# ========================================
# Funcao: Decodificar O QUE faz videos viralizarem
# Custo: ZERO (analisa dados do Supabase)
# ========================================

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict, Counter
import re
import statistics

from .base import BaseAgent, AgentResult, AgentStatus

logger = logging.getLogger(__name__)


class PatternAgent(BaseAgent):
    """
    Agente responsavel por analisar padroes de sucesso.

    O que analisa:
    1. Estruturas de titulo que geram mais views
    2. Palavras-gatilho por idioma
    3. Comprimento ideal de titulo por subnicho
    4. Padroes de pontuacao (? ! ...)
    5. Correlacao tema x views
    """

    def __init__(self, db_client):
        super().__init__(db_client)

        # Padroes comuns de titulos
        self.title_patterns = {
            "question": r'\?',
            "exclamation": r'!',
            "ellipsis": r'\.{3}',
            "caps_word": r'\b[A-Z]{2,}\b',
            "numbers": r'\d+',
            "emoji": r'[\U0001F300-\U0001F9FF]',
            "brackets": r'[\[\]\(\)]',
            "quotes": r'["\']',
            "colon": r':',
            "pipe": r'\|',
            "dash": r' - '
        }

        # Palavras-gatilho conhecidas (ingles)
        self.trigger_words_en = [
            "secret", "hidden", "truth", "revealed", "shocking",
            "never", "always", "worst", "best", "top",
            "dark", "creepy", "scary", "terrifying", "haunted",
            "true", "real", "story", "stories", "facts",
            "mystery", "mysterious", "unexplained", "strange",
            "why", "how", "what", "who", "when"
        ]

    @property
    def name(self) -> str:
        return "PatternAgent"

    @property
    def description(self) -> str:
        return "Analisa padroes de titulos e conteudo que geram mais views"

    async def run(self) -> AgentResult:
        """Executa analise de padroes"""
        result = self.create_result()

        try:
            logger.info(f"[{self.name}] Iniciando analise de padroes...")

            # 1. Buscar todos os videos com suas views
            videos = await self._get_all_videos_with_stats()
            logger.info(f"[{self.name}] {len(videos)} videos carregados para analise")

            if not videos:
                return self.complete_result(result, {
                    "patterns": [],
                    "message": "Nenhum video para analisar"
                })

            # 2. Analisar padroes de titulo
            title_patterns = self._analyze_title_patterns(videos)
            logger.info(f"[{self.name}] {len(title_patterns)} padroes de titulo analisados")

            # 3. Analisar palavras-gatilho
            trigger_analysis = self._analyze_trigger_words(videos)
            logger.info(f"[{self.name}] {len(trigger_analysis)} palavras-gatilho analisadas")

            # 4. Analisar comprimento de titulo
            length_analysis = self._analyze_title_length(videos)

            # 5. Analisar por subnicho
            subnicho_patterns = self._analyze_by_subnicho(videos)
            logger.info(f"[{self.name}] {len(subnicho_patterns)} subnichos analisados")

            # 6. Analisar por idioma
            language_patterns = self._analyze_by_language(videos)
            logger.info(f"[{self.name}] {len(language_patterns)} idiomas analisados")

            # 7. Gerar recomendacoes baseadas nos padroes
            recommendations = self._generate_pattern_recommendations(
                title_patterns, trigger_analysis, length_analysis
            )

            metrics = {
                "videos_analisados": len(videos),
                "padroes_identificados": len(title_patterns),
                "palavras_gatilho": len(trigger_analysis),
                "subnichos_analisados": len(subnicho_patterns),
                "idiomas_analisados": len(language_patterns)
            }

            return self.complete_result(result, {
                "title_patterns": title_patterns,
                "trigger_words": trigger_analysis[:30],  # Top 30
                "length_analysis": length_analysis,
                "by_subnicho": subnicho_patterns,
                "by_language": language_patterns,
                "recommendations": recommendations,
                "summary": f"Analisados {len(videos)} videos, {len(recommendations)} recomendacoes geradas"
            }, metrics)

        except Exception as e:
            logger.error(f"[{self.name}] Erro: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return self.fail_result(result, str(e))

    async def _get_all_videos_with_stats(self) -> List[Dict]:
        """Busca todos os videos com informacoes do canal"""
        try:
            all_videos = []
            batch_size = 1000
            offset = 0

            while True:
                response = self.db.supabase.table("videos_historico")\
                    .select("*, canais_monitorados!inner(nome_canal, subnicho, lingua, tipo)")\
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
            logger.error(f"Erro buscando videos: {e}")
            return []

    def _analyze_title_patterns(self, videos: List[Dict]) -> List[Dict]:
        """
        Analisa quais padroes de titulo correlacionam com mais views.
        """
        pattern_stats = {}

        for pattern_name, pattern_regex in self.title_patterns.items():
            videos_with = []
            videos_without = []

            for video in videos:
                titulo = video.get("titulo", "")
                views = video.get("views_atuais", 0)

                if re.search(pattern_regex, titulo):
                    videos_with.append(views)
                else:
                    videos_without.append(views)

            if videos_with and videos_without:
                avg_with = statistics.mean(videos_with)
                avg_without = statistics.mean(videos_without)

                pattern_stats[pattern_name] = {
                    "pattern": pattern_name,
                    "videos_with_pattern": len(videos_with),
                    "videos_without_pattern": len(videos_without),
                    "avg_views_with": round(avg_with),
                    "avg_views_without": round(avg_without),
                    "lift_percentage": round(((avg_with - avg_without) / avg_without) * 100, 1) if avg_without > 0 else 0,
                    "recommended": avg_with > avg_without
                }

        # Ordenar por lift
        result = sorted(pattern_stats.values(), key=lambda x: x.get("lift_percentage", 0), reverse=True)
        return result

    def _analyze_trigger_words(self, videos: List[Dict]) -> List[Dict]:
        """
        Analisa palavras-gatilho que correlacionam com mais views.
        """
        word_stats = defaultdict(lambda: {"views": [], "count": 0})

        for video in videos:
            titulo = video.get("titulo", "").lower()
            views = video.get("views_atuais", 0)

            # Extrair palavras
            words = re.findall(r'\b[a-z]{3,}\b', titulo)

            for word in words:
                word_stats[word]["views"].append(views)
                word_stats[word]["count"] += 1

        # Calcular metricas
        trigger_analysis = []
        for word, stats in word_stats.items():
            if stats["count"] >= 5:  # Minimo 5 ocorrencias
                avg_views = statistics.mean(stats["views"])
                trigger_analysis.append({
                    "word": word,
                    "frequency": stats["count"],
                    "avg_views": round(avg_views),
                    "total_views": sum(stats["views"]),
                    "is_known_trigger": word in self.trigger_words_en
                })

        # Ordenar por media de views
        trigger_analysis.sort(key=lambda x: x.get("avg_views", 0), reverse=True)
        return trigger_analysis

    def _analyze_title_length(self, videos: List[Dict]) -> Dict:
        """
        Analisa correlacao entre comprimento do titulo e views.
        """
        length_buckets = {
            "very_short": {"range": "1-30 chars", "min": 1, "max": 30, "views": []},
            "short": {"range": "31-50 chars", "min": 31, "max": 50, "views": []},
            "medium": {"range": "51-70 chars", "min": 51, "max": 70, "views": []},
            "long": {"range": "71-100 chars", "min": 71, "max": 100, "views": []},
            "very_long": {"range": "100+ chars", "min": 101, "max": 999, "views": []}
        }

        for video in videos:
            titulo = video.get("titulo", "")
            views = video.get("views_atuais", 0)
            length = len(titulo)

            for bucket_name, bucket in length_buckets.items():
                if bucket["min"] <= length <= bucket["max"]:
                    bucket["views"].append(views)
                    break

        # Calcular metricas
        result = {}
        best_bucket = None
        best_avg = 0

        for bucket_name, bucket in length_buckets.items():
            if bucket["views"]:
                avg = statistics.mean(bucket["views"])
                result[bucket_name] = {
                    "range": bucket["range"],
                    "video_count": len(bucket["views"]),
                    "avg_views": round(avg),
                    "max_views": max(bucket["views"]),
                    "min_views": min(bucket["views"])
                }

                if avg > best_avg:
                    best_avg = avg
                    best_bucket = bucket_name

        result["recommended_length"] = best_bucket
        result["recommended_range"] = length_buckets[best_bucket]["range"] if best_bucket else "50-70 chars"

        return result

    def _analyze_by_subnicho(self, videos: List[Dict]) -> Dict[str, Dict]:
        """
        Analisa padroes especificos por subnicho.
        """
        by_subnicho = defaultdict(list)

        for video in videos:
            canal_info = video.get("canais_monitorados", {})
            subnicho = canal_info.get("subnicho", "Unknown")
            by_subnicho[subnicho].append(video)

        result = {}
        for subnicho, videos_list in by_subnicho.items():
            if len(videos_list) >= 10:  # Minimo 10 videos para analise valida
                views_list = [v.get("views_atuais", 0) for v in videos_list]
                titles = [v.get("titulo", "") for v in videos_list]

                # Encontrar palavras mais comuns nos titulos de sucesso
                top_videos = sorted(videos_list, key=lambda x: x.get("views_atuais", 0), reverse=True)[:20]
                top_words = self._extract_common_words([v.get("titulo", "") for v in top_videos])

                # Comprimento medio de titulo
                avg_title_length = statistics.mean([len(t) for t in titles])

                result[subnicho] = {
                    "total_videos": len(videos_list),
                    "avg_views": round(statistics.mean(views_list)),
                    "max_views": max(views_list),
                    "avg_title_length": round(avg_title_length),
                    "top_words": top_words[:10],
                    "best_performing_patterns": self._find_best_patterns_for_videos(top_videos)
                }

        return result

    def _analyze_by_language(self, videos: List[Dict]) -> Dict[str, Dict]:
        """
        Analisa padroes especificos por idioma.
        """
        by_language = defaultdict(list)

        for video in videos:
            canal_info = video.get("canais_monitorados", {})
            lingua = canal_info.get("lingua", "Unknown")
            by_language[lingua].append(video)

        result = {}
        for lingua, videos_list in by_language.items():
            if len(videos_list) >= 10:
                views_list = [v.get("views_atuais", 0) for v in videos_list]
                titles = [v.get("titulo", "") for v in videos_list]

                # Top palavras
                top_videos = sorted(videos_list, key=lambda x: x.get("views_atuais", 0), reverse=True)[:20]
                top_words = self._extract_common_words([v.get("titulo", "") for v in top_videos])

                result[lingua] = {
                    "total_videos": len(videos_list),
                    "avg_views": round(statistics.mean(views_list)),
                    "max_views": max(views_list),
                    "avg_title_length": round(statistics.mean([len(t) for t in titles])),
                    "top_trigger_words": top_words[:15],
                    "recommended_patterns": self._find_best_patterns_for_videos(top_videos)
                }

        return result

    def _extract_common_words(self, titles: List[str]) -> List[str]:
        """Extrai palavras mais comuns de uma lista de titulos"""
        stopwords = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
            "this", "that", "these", "those", "it", "its", "de", "la", "el"
        }

        all_words = []
        for title in titles:
            words = re.findall(r'\b[a-zA-Z]{3,}\b', title.lower())
            all_words.extend([w for w in words if w not in stopwords])

        word_counts = Counter(all_words)
        return [word for word, count in word_counts.most_common(20)]

    def _find_best_patterns_for_videos(self, videos: List[Dict]) -> List[str]:
        """Encontra padroes mais comuns em videos de sucesso"""
        pattern_counts = Counter()

        for video in videos:
            titulo = video.get("titulo", "")
            for pattern_name, pattern_regex in self.title_patterns.items():
                if re.search(pattern_regex, titulo):
                    pattern_counts[pattern_name] += 1

        return [p for p, c in pattern_counts.most_common(5)]

    def _generate_pattern_recommendations(
        self,
        title_patterns: List[Dict],
        trigger_words: List[Dict],
        length_analysis: Dict
    ) -> List[Dict]:
        """
        Gera recomendacoes praticas baseadas nos padroes encontrados.
        """
        recommendations = []

        # Recomendacoes de padroes de titulo
        positive_patterns = [p for p in title_patterns if p.get("recommended") and p.get("lift_percentage", 0) > 10]
        for pattern in positive_patterns[:5]:
            recommendations.append({
                "type": "title_pattern",
                "pattern": pattern["pattern"],
                "recommendation": f"Use '{pattern['pattern']}' em titulos - aumenta views em {pattern['lift_percentage']}%",
                "impact": "high" if pattern["lift_percentage"] > 30 else "medium",
                "data": pattern
            })

        # Recomendacoes de palavras-gatilho
        top_triggers = [t for t in trigger_words if t.get("avg_views", 0) > 50000][:10]
        for trigger in top_triggers:
            recommendations.append({
                "type": "trigger_word",
                "word": trigger["word"],
                "recommendation": f"Palavra '{trigger['word']}' tem media de {trigger['avg_views']:,} views",
                "impact": "high" if trigger["avg_views"] > 100000 else "medium",
                "data": trigger
            })

        # Recomendacao de comprimento
        rec_range = length_analysis.get("recommended_range", "50-70 chars")
        recommendations.append({
            "type": "title_length",
            "recommendation": f"Comprimento ideal de titulo: {rec_range}",
            "impact": "medium",
            "data": length_analysis
        })

        return recommendations

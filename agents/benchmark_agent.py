# ========================================
# BENCHMARK AGENT - Comparador de Performance
# ========================================
# Funcao: Comparar nossos canais vs concorrentes
# Custo: ZERO (analisa dados do Supabase)
# ========================================

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from collections import defaultdict
import statistics

from .base import BaseAgent, AgentResult, AgentStatus

logger = logging.getLogger(__name__)


class BenchmarkAgent(BaseAgent):
    """
    Agente responsavel por comparar performance dos nossos canais vs mercado.

    Metricas comparativas:
    - Views medias por video (nos vs mercado)
    - Crescimento de inscritos (nos vs top 10)
    - Frequencia de virais (% videos > X views)
    - Performance por subnicho

    Analise por canal:
    - Canal X: Performance 120% do benchmark
    - Canal Y: Performance 60% do benchmark -> Investigar
    """

    def __init__(self, db_client):
        super().__init__(db_client)

        # Thresholds
        self.viral_threshold = 100000  # Video viral = > 100K views
        self.good_performance_threshold = 0.8  # 80% do benchmark = bom
        self.excellent_performance_threshold = 1.2  # 120% do benchmark = excelente

    @property
    def name(self) -> str:
        return "BenchmarkAgent"

    @property
    def description(self) -> str:
        return "Compara performance dos nossos canais vs concorrentes do mercado"

    async def run(self) -> AgentResult:
        """Executa analise de benchmark"""
        result = self.create_result()

        try:
            logger.info(f"[{self.name}] Iniciando analise de benchmark...")

            # 1. Buscar todos os canais
            canais = await self._get_all_channels()
            logger.info(f"[{self.name}] {len(canais)} canais carregados")

            # Separar nossos canais vs minerados
            nossos_canais = [c for c in canais if c.get("tipo") == "nosso"]
            canais_minerados = [c for c in canais if c.get("tipo") == "minerado"]

            logger.info(f"[{self.name}] Nossos: {len(nossos_canais)} | Minerados: {len(canais_minerados)}")

            # 2. Buscar videos de todos os canais
            videos = await self._get_all_videos()
            logger.info(f"[{self.name}] {len(videos)} videos carregados")

            # 3. Calcular benchmark do mercado (por subnicho)
            market_benchmark = self._calculate_market_benchmark(videos, canais_minerados)
            logger.info(f"[{self.name}] Benchmark calculado para {len(market_benchmark)} subnichos")

            # 4. Avaliar nossos canais vs benchmark
            our_performance = self._evaluate_our_channels(videos, nossos_canais, market_benchmark)

            # 5. Identificar canais com problemas
            underperforming = [c for c in our_performance if c.get("performance_ratio", 0) < self.good_performance_threshold]
            outperforming = [c for c in our_performance if c.get("performance_ratio", 0) >= self.excellent_performance_threshold]

            # 6. Ranking geral
            overall_ranking = self._create_overall_ranking(our_performance)

            # 7. Analise por subnicho
            subnicho_comparison = self._compare_by_subnicho(videos, nossos_canais, canais_minerados)

            # 8. Analise de frequencia de virais
            viral_analysis = self._analyze_viral_frequency(videos, nossos_canais, canais_minerados)

            metrics = {
                "nossos_canais": len(nossos_canais),
                "canais_minerados": len(canais_minerados),
                "videos_analisados": len(videos),
                "subnichos_analisados": len(market_benchmark),
                "canais_underperforming": len(underperforming),
                "canais_outperforming": len(outperforming)
            }

            return self.complete_result(result, {
                "market_benchmark": market_benchmark,
                "our_performance": our_performance,
                "underperforming_channels": underperforming,
                "outperforming_channels": outperforming,
                "overall_ranking": overall_ranking,
                "by_subnicho": subnicho_comparison,
                "viral_analysis": viral_analysis,
                "summary": f"{len(outperforming)} canais acima do benchmark, {len(underperforming)} abaixo"
            }, metrics)

        except Exception as e:
            logger.error(f"[{self.name}] Erro: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return self.fail_result(result, str(e))

    async def _get_all_channels(self) -> List[Dict]:
        """Busca todos os canais com seus dados mais recentes"""
        try:
            response = self.db.supabase.table("canais_monitorados")\
                .select("*")\
                .eq("status", "ativo")\
                .execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Erro buscando canais: {e}")
            return []

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

    def _calculate_market_benchmark(self, videos: List[Dict], canais_minerados: List[Dict]) -> Dict[str, Dict]:
        """
        Calcula benchmark do mercado por subnicho.
        Usa apenas canais minerados (concorrentes).
        """
        minerados_ids = {c["id"] for c in canais_minerados}

        # Agrupar videos por subnicho
        by_subnicho = defaultdict(list)

        for video in videos:
            canal_info = video.get("canais_monitorados", {})

            # Apenas canais minerados
            if canal_info.get("id") not in minerados_ids:
                continue

            subnicho = canal_info.get("subnicho", "Unknown")
            by_subnicho[subnicho].append(video)

        # Calcular metricas por subnicho
        benchmark = {}
        for subnicho, videos_list in by_subnicho.items():
            if len(videos_list) < 10:  # Minimo 10 videos
                continue

            views = [v.get("views_atuais", 0) for v in videos_list]

            # Contar virais
            virals = [v for v in views if v >= self.viral_threshold]

            benchmark[subnicho] = {
                "total_videos": len(videos_list),
                "avg_views": round(statistics.mean(views)),
                "median_views": round(statistics.median(views)),
                "max_views": max(views),
                "p75_views": round(statistics.quantiles(views, n=4)[2]) if len(views) >= 4 else max(views),
                "viral_count": len(virals),
                "viral_rate": round(len(virals) / len(views) * 100, 1),
                "std_dev": round(statistics.stdev(views)) if len(views) > 1 else 0
            }

        return benchmark

    def _evaluate_our_channels(
        self,
        videos: List[Dict],
        nossos_canais: List[Dict],
        market_benchmark: Dict[str, Dict]
    ) -> List[Dict]:
        """
        Avalia cada um dos nossos canais vs benchmark do mercado.
        """
        nossos_ids = {c["id"] for c in nossos_canais}
        canais_dict = {c["id"]: c for c in nossos_canais}

        # Agrupar videos por canal
        videos_by_canal = defaultdict(list)
        for video in videos:
            canal_info = video.get("canais_monitorados", {})
            canal_id = canal_info.get("id")

            if canal_id in nossos_ids:
                videos_by_canal[canal_id].append(video)

        # Avaliar cada canal
        evaluations = []
        for canal_id, videos_list in videos_by_canal.items():
            canal = canais_dict.get(canal_id, {})
            subnicho = canal.get("subnicho", "Unknown")

            if len(videos_list) < 3:  # Minimo 3 videos
                continue

            views = [v.get("views_atuais", 0) for v in videos_list]
            avg_views = statistics.mean(views)

            # Buscar benchmark do subnicho
            bench = market_benchmark.get(subnicho, {})
            bench_avg = bench.get("avg_views", 0)

            # Calcular performance ratio
            if bench_avg > 0:
                performance_ratio = avg_views / bench_avg
            else:
                performance_ratio = 1.0

            # Contar virais
            virals = [v for v in views if v >= self.viral_threshold]

            # Determinar status
            if performance_ratio >= self.excellent_performance_threshold:
                status = "excellent"
                status_emoji = "star"
            elif performance_ratio >= self.good_performance_threshold:
                status = "good"
                status_emoji = "check"
            else:
                status = "needs_attention"
                status_emoji = "warning"

            evaluations.append({
                "canal_id": canal_id,
                "nome_canal": canal.get("nome_canal", "Unknown"),
                "subnicho": subnicho,
                "lingua": canal.get("lingua", "Unknown"),
                "total_videos": len(videos_list),
                "avg_views": round(avg_views),
                "max_views": max(views),
                "benchmark_avg": bench_avg,
                "performance_ratio": round(performance_ratio, 2),
                "performance_percentage": round(performance_ratio * 100, 1),
                "viral_count": len(virals),
                "viral_rate": round(len(virals) / len(views) * 100, 1),
                "status": status,
                "status_emoji": status_emoji
            })

        # Ordenar por performance_ratio
        evaluations.sort(key=lambda x: x.get("performance_ratio", 0), reverse=True)

        return evaluations

    def _create_overall_ranking(self, evaluations: List[Dict]) -> List[Dict]:
        """
        Cria ranking geral de todos os nossos canais.
        """
        ranking = []
        for i, eval in enumerate(evaluations, 1):
            ranking.append({
                "rank": i,
                "nome_canal": eval.get("nome_canal"),
                "subnicho": eval.get("subnicho"),
                "performance": f"{eval.get('performance_percentage')}%",
                "avg_views": eval.get("avg_views"),
                "status": eval.get("status")
            })

        return ranking

    def _compare_by_subnicho(
        self,
        videos: List[Dict],
        nossos_canais: List[Dict],
        canais_minerados: List[Dict]
    ) -> Dict[str, Dict]:
        """
        Compara performance nos vs mercado por subnicho.
        """
        nossos_ids = {c["id"] for c in nossos_canais}
        minerados_ids = {c["id"] for c in canais_minerados}

        # Agrupar por subnicho e tipo
        subnicho_data = defaultdict(lambda: {"nosso": [], "minerado": []})

        for video in videos:
            canal_info = video.get("canais_monitorados", {})
            canal_id = canal_info.get("id")
            subnicho = canal_info.get("subnicho", "Unknown")
            views = video.get("views_atuais", 0)

            if canal_id in nossos_ids:
                subnicho_data[subnicho]["nosso"].append(views)
            elif canal_id in minerados_ids:
                subnicho_data[subnicho]["minerado"].append(views)

        # Calcular comparacoes
        comparisons = {}
        for subnicho, data in subnicho_data.items():
            nosso_views = data["nosso"]
            minerado_views = data["minerado"]

            if len(nosso_views) < 3 or len(minerado_views) < 3:
                continue

            nosso_avg = statistics.mean(nosso_views)
            minerado_avg = statistics.mean(minerado_views)

            comparisons[subnicho] = {
                "nosso_videos": len(nosso_views),
                "nosso_avg_views": round(nosso_avg),
                "minerado_videos": len(minerado_views),
                "minerado_avg_views": round(minerado_avg),
                "difference": round(nosso_avg - minerado_avg),
                "ratio": round(nosso_avg / minerado_avg, 2) if minerado_avg > 0 else 1.0,
                "winning": nosso_avg > minerado_avg
            }

        return comparisons

    def _analyze_viral_frequency(
        self,
        videos: List[Dict],
        nossos_canais: List[Dict],
        canais_minerados: List[Dict]
    ) -> Dict:
        """
        Analisa frequencia de videos virais (nos vs mercado).
        """
        nossos_ids = {c["id"] for c in nossos_canais}
        minerados_ids = {c["id"] for c in canais_minerados}

        nosso_total = 0
        nosso_virals = 0
        minerado_total = 0
        minerado_virals = 0

        for video in videos:
            canal_info = video.get("canais_monitorados", {})
            canal_id = canal_info.get("id")
            views = video.get("views_atuais", 0)

            if canal_id in nossos_ids:
                nosso_total += 1
                if views >= self.viral_threshold:
                    nosso_virals += 1

            elif canal_id in minerados_ids:
                minerado_total += 1
                if views >= self.viral_threshold:
                    minerado_virals += 1

        return {
            "viral_threshold": self.viral_threshold,
            "nosso": {
                "total_videos": nosso_total,
                "viral_videos": nosso_virals,
                "viral_rate": round(nosso_virals / nosso_total * 100, 2) if nosso_total > 0 else 0
            },
            "mercado": {
                "total_videos": minerado_total,
                "viral_videos": minerado_virals,
                "viral_rate": round(minerado_virals / minerado_total * 100, 2) if minerado_total > 0 else 0
            },
            "comparison": "acima" if (nosso_virals / nosso_total if nosso_total else 0) > (minerado_virals / minerado_total if minerado_total else 0) else "abaixo"
        }

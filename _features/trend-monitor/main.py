#!/usr/bin/env python3
"""
TREND MONITOR - Script Principal (Expandido)
=============================================
Orquestra a coleta de trends, filtragem e geração de dashboard.

USO:
    python main.py                    # Execução completa expandida
    python main.py --basic            # Coleta básica (menos API units)
    python main.py --collect-only     # Apenas coleta (salva JSON)
    python main.py --generate-only    # Gera dashboard do último JSON
    python main.py --mock             # Usa dados mock (para testes)

COLETA EXPANDIDA (padrão):
    - YouTube: trending + busca por subnicho + descoberta (~8.000 units)
    - Google Trends: RSS de 7 países (~175 trends) - GRÁTIS
    - Hacker News: 500 stories - GRÁTIS
    - Total esperado: ~3.000 items brutos → ~2.000 após filtros

ESTRUTURA DE SAÍDA:
    data/trends_YYYY-MM-DD.json       # Dados coletados
    output/trends-dashboard-YYYY-MM-DD.html  # Dashboard

VARIÁVEIS DE AMBIENTE:
    YOUTUBE_API_KEY       # API key do YouTube Data API v3
    SUPABASE_URL          # URL do projeto Supabase (opcional)
    SUPABASE_KEY          # Chave anon do Supabase (opcional)

AUTOR: Content Factory
DATA: Janeiro 2026
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
from typing import Dict, Optional

# Adicionar diretório ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    DATA_DIR, OUTPUT_DIR, get_today_filename,
    COUNTRIES, get_active_subnichos
)
from collectors import GoogleTrendsCollector, RedditCollector, YouTubeCollector, HackerNewsCollector
from collectors.youtube import get_mock_youtube_data
from collectors.reddit import get_mock_reddit_data
from collectors.google_trends import get_mock_google_trends_data
from collectors.hackernews import get_mock_hackernews_data
from filters import RelevanceFilter
from filters.quality import (
    filter_youtube, filter_google_trends, filter_hackernews,
    classify_all_items, get_quality_summary
)
from generators import HTMLReportGenerator

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Usar Supabase se configurado, senao SQLite local
try:
    from config import SUPABASE_CONFIG
    if SUPABASE_CONFIG.get("enabled"):
        from database.supabase_client import TrendDatabaseSupabase as TrendDatabase
        logger.info("Usando Supabase como banco de dados")
    else:
        from database import TrendDatabase
        logger.info("Supabase nao configurado. Usando SQLite local.")
except Exception:
    from database import TrendDatabase


class TrendMonitor:
    """
    Classe principal do Trend Monitor.

    Orquestra todo o fluxo:
    1. Coleta de múltiplas fontes (básica ou expandida)
    2. Filtragem e scoring de qualidade
    3. Geração de dashboard
    """

    def __init__(self, use_mock: bool = False, expanded: bool = True):
        """
        Inicializa o monitor.

        Args:
            use_mock: Se True, usa dados mock ao invés de APIs reais
            expanded: Se True, usa coleta expandida (mais API units)
        """
        self.use_mock = use_mock
        self.expanded = expanded
        self.date_str = datetime.now().strftime("%Y-%m-%d")
        self.timestamp = datetime.now().isoformat()

        # Inicializar componentes
        if not use_mock:
            self.google_collector = GoogleTrendsCollector()
            self.reddit_collector = RedditCollector()
            self.youtube_collector = YouTubeCollector()
            self.hackernews_collector = HackerNewsCollector()

        self.filter = RelevanceFilter()
        self.generator = HTMLReportGenerator()
        self.database = TrendDatabase()

        mode = "MOCK" if use_mock else ("EXPANDIDO" if expanded else "BÁSICO")

        logger.info("=" * 60)
        logger.info("TREND MONITOR - Inicializado")
        logger.info(f"Data: {self.date_str}")
        logger.info(f"Modo: {mode}")
        if expanded and not use_mock:
            logger.info("YouTube: trending + subnicho + discovery (~8.000 units)")
            logger.info("Hacker News: 500 stories (GRÁTIS)")
        logger.info("=" * 60)

    def collect_all(self) -> Dict:
        """
        Coleta trends de todas as fontes.
        Se expanded=True, usa coleta expandida com mais dados.

        Returns:
            Dict com dados coletados por fonte e país
        """
        logger.info("\n" + "=" * 60)
        logger.info("FASE 1: COLETA DE DADOS")
        logger.info("=" * 60)

        if self.use_mock:
            logger.info("Usando dados MOCK...")
            return self._get_mock_data()

        data = {
            "google_trends": {},
            "reddit": {},
            "youtube": {},
            "youtube_expanded": None,  # Dados expandidos do YouTube
            "hackernews": {},
            "hackernews_expanded": None,  # Dados expandidos do HN
            "metadata": {
                "collected_at": self.timestamp,
                "date": self.date_str,
                "countries": list(COUNTRIES.keys()),
                "sources": ["google_trends", "youtube", "hackernews"],
                "expanded": self.expanded
            }
        }

        # 1. Google Trends (RSS - GRÁTIS)
        logger.info("\n--- Google Trends (RSS) ---")
        try:
            data["google_trends"] = self.google_collector.collect_all_countries()
        except Exception as e:
            logger.error(f"Erro na coleta Google Trends: {e}")
            data["google_trends"] = {}

        # 2. YouTube
        logger.info("\n--- YouTube ---")
        try:
            if self.expanded:
                # Coleta expandida: trending + subnicho + discovery
                expanded_result = self.youtube_collector.collect_all_expanded()
                data["youtube_expanded"] = expanded_result

                # Flatten para compatibilidade
                all_yt_videos = self.youtube_collector.flatten_results(expanded_result)
                data["youtube"] = {"all": all_yt_videos}

                # Estatísticas
                stats = expanded_result.get("stats", {})
                logger.info(f"  Trending: {stats.get('trending_count', 0)} vídeos")
                logger.info(f"  Subnicho: {stats.get('subnicho_count', 0)} vídeos")
                logger.info(f"  Discovery: {stats.get('discovery_count', 0)} vídeos")
                logger.info(f"  API Units: ~{stats.get('units_used', 0)}")
            else:
                # Coleta básica
                data["youtube"] = self.youtube_collector.collect_all_countries()
        except Exception as e:
            logger.error(f"Erro na coleta YouTube: {e}")
            data["youtube"] = {}

        # 3. Hacker News (GRÁTIS)
        logger.info("\n--- Hacker News ---")
        try:
            if self.expanded:
                # Coleta expandida: 500 stories
                expanded_result = self.hackernews_collector.collect_all_expanded()
                data["hackernews_expanded"] = expanded_result
                data["hackernews"] = {"global": expanded_result.get("global", [])}

                stats = expanded_result.get("stats", {})
                logger.info(f"  Total: {stats.get('total', 0)} stories")
                logger.info(f"  Filtradas: {stats.get('filtered', 0)} (baixa qualidade)")
            else:
                data["hackernews"] = self.hackernews_collector.collect_all()
        except Exception as e:
            logger.error(f"Erro na coleta Hacker News: {e}")
            data["hackernews"] = {}

        # 4. Reddit (desabilitado por padrão - precisa API)
        # Comentado pois requer credenciais e a API tem mais restrições
        data["reddit"] = {}

        # Estatísticas finais
        total = 0
        youtube_total = 0
        google_total = 0
        hn_total = 0

        for country, trends in data.get("google_trends", {}).items():
            google_total += len(trends)

        if self.expanded and data.get("youtube_expanded"):
            youtube_total = data["youtube_expanded"].get("stats", {}).get("total_videos", 0)
        else:
            for country, videos in data.get("youtube", {}).items():
                youtube_total += len(videos)

        if self.expanded and data.get("hackernews_expanded"):
            hn_total = data["hackernews_expanded"].get("stats", {}).get("total", 0)
        else:
            for cat, stories in data.get("hackernews", {}).items():
                hn_total += len(stories)

        total = google_total + youtube_total + hn_total

        logger.info("\n" + "-" * 40)
        logger.info("RESUMO DA COLETA:")
        logger.info(f"  Google Trends: {google_total} trends")
        logger.info(f"  YouTube: {youtube_total} vídeos")
        logger.info(f"  Hacker News: {hn_total} stories")
        logger.info(f"  TOTAL BRUTO: {total} itens")
        logger.info("-" * 40)

        data["metadata"]["totals"] = {
            "google_trends": google_total,
            "youtube": youtube_total,
            "hackernews": hn_total,
            "total": total
        }

        return data

    def _get_mock_data(self) -> Dict:
        """Retorna dados mock realistas para testes"""
        youtube_mock = get_mock_youtube_data()
        reddit_mock = get_mock_reddit_data()
        google_mock = get_mock_google_trends_data()
        hackernews_mock = get_mock_hackernews_data()

        return {
            "google_trends": google_mock,
            "reddit": reddit_mock,
            "youtube": youtube_mock,
            "hackernews": hackernews_mock,
            "metadata": {
                "collected_at": self.timestamp,
                "date": self.date_str,
                "countries": list(COUNTRIES.keys()),
                "sources": ["google_trends", "reddit", "youtube", "hackernews"],
                "is_mock": True
            }
        }

    def save_raw_data(self, data: Dict) -> str:
        """
        Salva dados raw em JSON.

        Args:
            data: Dados coletados

        Returns:
            Caminho do arquivo salvo
        """
        os.makedirs(DATA_DIR, exist_ok=True)
        filepath = os.path.join(DATA_DIR, f"trends_{self.date_str}.json")

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Dados salvos: {filepath}")
        return filepath

    def load_raw_data(self, date: str = None) -> Optional[Dict]:
        """
        Carrega dados raw de um arquivo JSON.

        Args:
            date: Data no formato YYYY-MM-DD (default: hoje)

        Returns:
            Dados carregados ou None se não encontrado
        """
        if date is None:
            date = self.date_str

        filepath = os.path.join(DATA_DIR, f"trends_{date}.json")

        if not os.path.exists(filepath):
            logger.warning(f"Arquivo não encontrado: {filepath}")
            return None

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        logger.info(f"Dados carregados: {filepath}")
        return data

    def filter_and_score(self, raw_data: Dict) -> Dict:
        """
        Filtra e pontua os trends com quality_score universal.

        Args:
            raw_data: Dados raw coletados

        Returns:
            Dados filtrados, pontuados e organizados
        """
        logger.info("\n" + "=" * 60)
        logger.info("FASE 2: FILTRAGEM E SCORING DE QUALIDADE")
        logger.info("=" * 60)

        all_items = []
        stats = {
            "youtube_raw": 0,
            "youtube_filtered": 0,
            "google_raw": 0,
            "google_filtered": 0,
            "hackernews_raw": 0,
            "hackernews_filtered": 0,
            "total_raw": 0,
            "total_filtered": 0,
            "total_with_score": 0
        }

        # 1. Processar YouTube
        logger.info("\n--- Filtrando YouTube ---")
        youtube_data = raw_data.get("youtube", {})
        youtube_items = []
        for country, videos in youtube_data.items():
            if isinstance(videos, list):
                youtube_items.extend(videos)

        stats["youtube_raw"] = len(youtube_items)
        if youtube_items:
            filtered_yt, removed_yt = filter_youtube(youtube_items)
            classified_yt = classify_all_items(filtered_yt, "youtube")
            all_items.extend(classified_yt)
            stats["youtube_filtered"] = len(classified_yt)
            logger.info(f"  YouTube: {stats['youtube_raw']} → {stats['youtube_filtered']} após filtros")

        # 2. Processar Google Trends
        logger.info("\n--- Filtrando Google Trends ---")
        google_data = raw_data.get("google_trends", {})
        google_items = []
        for country, trends in google_data.items():
            if isinstance(trends, list):
                for trend in trends:
                    trend["country"] = country
                google_items.extend(trends)

        stats["google_raw"] = len(google_items)
        if google_items:
            filtered_gt, removed_gt = filter_google_trends(google_items)
            classified_gt = classify_all_items(filtered_gt, "google_trends")
            all_items.extend(classified_gt)
            stats["google_filtered"] = len(classified_gt)
            logger.info(f"  Google Trends: {stats['google_raw']} → {stats['google_filtered']} após filtros")

        # 3. Processar Hacker News
        logger.info("\n--- Filtrando Hacker News ---")
        hn_data = raw_data.get("hackernews", {})
        hn_items = []
        for cat, stories in hn_data.items():
            if isinstance(stories, list):
                hn_items.extend(stories)

        stats["hackernews_raw"] = len(hn_items)
        if hn_items:
            filtered_hn, removed_hn = filter_hackernews(hn_items)
            classified_hn = classify_all_items(filtered_hn, "hackernews")
            all_items.extend(classified_hn)
            stats["hackernews_filtered"] = len(classified_hn)
            logger.info(f"  Hacker News: {stats['hackernews_raw']} → {stats['hackernews_filtered']} após filtros")

        # Totais
        stats["total_raw"] = stats["youtube_raw"] + stats["google_raw"] + stats["hackernews_raw"]
        stats["total_filtered"] = stats["youtube_filtered"] + stats["google_filtered"] + stats["hackernews_filtered"]
        stats["total_with_score"] = len(all_items)

        # Ordenar por quality_score
        all_items.sort(key=lambda x: x.get("quality_score", 0), reverse=True)

        # Resumo de qualidade
        quality_summary = get_quality_summary(all_items)

        logger.info("\n" + "-" * 40)
        logger.info("RESUMO DE QUALIDADE:")
        logger.info(f"  Total processado: {stats['total_filtered']} itens")
        logger.info(f"  Score médio: {quality_summary.get('avg_score', 0):.1f}")
        logger.info(f"  Excelentes (>=80): {quality_summary.get('excellent_count', 0)}")
        logger.info(f"  Bons (60-79): {quality_summary.get('good_count', 0)}")
        logger.info(f"  Match subnicho: {quality_summary.get('subnicho_matches', 0)} ({quality_summary.get('subnicho_percent', 0):.1f}%)")
        logger.info("-" * 40)

        # Organizar por categoria
        filtered = {
            "all_items": all_items,
            "by_source": {
                "youtube": [i for i in all_items if i.get("source") == "youtube"],
                "google_trends": [i for i in all_items if i.get("source") == "google_trends"],
                "hackernews": [i for i in all_items if i.get("source") == "hackernews"]
            },
            "by_subnicho": {},
            "by_language": {},
            "top_quality": [i for i in all_items if i.get("quality_score", 0) >= 70][:50],
            "stats": stats,
            "quality_summary": quality_summary,
            "metadata": raw_data.get("metadata", {})
        }

        # Agrupar por subnicho
        for item in all_items:
            subnicho = item.get("matched_subnicho")
            if subnicho:
                if subnicho not in filtered["by_subnicho"]:
                    filtered["by_subnicho"][subnicho] = []
                filtered["by_subnicho"][subnicho].append(item)

        # Agrupar por língua
        for item in all_items:
            lang = item.get("language", "en")
            if lang not in filtered["by_language"]:
                filtered["by_language"][lang] = []
            filtered["by_language"][lang].append(item)

        # Salvar no banco de dados
        logger.info("\n--- Salvando no Banco de Dados ---")
        saved = self.database.save_trends(all_items)
        logger.info(f"Salvos {saved} trends no banco de dados")

        # Salvar matches de subnicho (se Supabase)
        if hasattr(self.database, 'save_subnicho_matches'):
            matches_saved = self.database.save_subnicho_matches(all_items)
            logger.info(f"Salvos {matches_saved} matches de subnicho")

        # Atualizar padrões (evergreen, etc.)
        self.database.update_patterns()

        # Adicionar dados de evergreen
        evergreen = self.database.get_evergreen_trends(min_days=7)
        filtered["evergreen_trends"] = evergreen
        filtered["stats"]["evergreen_count"] = len(evergreen)

        filtered["metadata"]["filtered_at"] = datetime.now().isoformat()

        return filtered

    def generate_dashboard(self, filtered_data: Dict) -> str:
        """
        Gera o dashboard HTML.

        Args:
            filtered_data: Dados filtrados

        Returns:
            Caminho do arquivo gerado
        """
        logger.info("\n" + "=" * 60)
        logger.info("FASE 3: GERAÇÃO DO DASHBOARD")
        logger.info("=" * 60)

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output_path = os.path.join(OUTPUT_DIR, f"trends-dashboard-{self.date_str}.html")

        result = self.generator.generate(filtered_data, output_path)

        logger.info(f"Dashboard gerado: {result}")
        return result

    def run(self, collect: bool = True, generate: bool = True) -> Dict:
        """
        Executa o fluxo completo.

        Args:
            collect: Se True, coleta novos dados
            generate: Se True, gera dashboard

        Returns:
            Dict com resultados e paths
        """
        start_time = datetime.now()
        results = {
            "success": False,
            "date": self.date_str,
            "raw_data_path": None,
            "dashboard_path": None,
            "stats": {}
        }

        try:
            # Fase 1: Coleta
            if collect:
                raw_data = self.collect_all()
                results["raw_data_path"] = self.save_raw_data(raw_data)
            else:
                raw_data = self.load_raw_data()
                if raw_data is None:
                    raise FileNotFoundError(f"Nenhum dado encontrado para {self.date_str}")

            # Fase 2: Filtragem
            filtered_data = self.filter_and_score(raw_data)
            results["stats"] = filtered_data.get("stats", {})

            # Fase 3: Dashboard
            if generate:
                results["dashboard_path"] = self.generate_dashboard(filtered_data)

            results["success"] = True

        except Exception as e:
            logger.error(f"Erro na execução: {e}")
            results["error"] = str(e)

        # Tempo de execução
        elapsed = (datetime.now() - start_time).total_seconds()
        results["elapsed_seconds"] = elapsed

        # Sumário final
        logger.info("\n" + "=" * 60)
        logger.info("EXECUÇÃO FINALIZADA")
        logger.info("=" * 60)
        logger.info(f"Status: {'SUCESSO' if results['success'] else 'ERRO'}")
        logger.info(f"Tempo: {elapsed:.1f} segundos")
        if results["success"]:
            logger.info(f"Dashboard: {results['dashboard_path']}")
            logger.info(f"Dados: {results['raw_data_path']}")
            stats = results.get("stats", {})
            logger.info(f"Trends processados: {stats.get('total_processed', 0)}")
            logger.info(f"Trends relevantes: {stats.get('total_relevant', 0)}")

        return results


def main():
    """Função principal com argumentos de linha de comando"""

    parser = argparse.ArgumentParser(
        description="Trend Monitor - Coleta e análise de trends",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python main.py                    # Execução completa EXPANDIDA (~8.000 units)
  python main.py --basic            # Coleta BÁSICA (~100 units)
  python main.py --mock             # Teste com dados mock
  python main.py --collect-only     # Apenas coleta dados
  python main.py --generate-only    # Gera dashboard do último JSON

COLETA EXPANDIDA (padrão):
  - YouTube: trending + subnicho + discovery (~8.000 units)
  - Google Trends: RSS 7 países (~175 trends) - GRÁTIS
  - Hacker News: 500 stories - GRÁTIS
  - Total: ~3.000 items brutos

COLETA BÁSICA (--basic):
  - YouTube: apenas trending (~100 units)
  - Google Trends: RSS 7 países
  - Hacker News: 70 stories
  - Total: ~500 items

Variáveis de ambiente:
  YOUTUBE_API_KEY       # Para coleta do YouTube
  SUPABASE_URL          # URL Supabase (opcional)
  SUPABASE_KEY          # Key Supabase (opcional)
        """
    )

    parser.add_argument(
        "--mock",
        action="store_true",
        help="Usar dados mock ao invés de APIs reais"
    )

    parser.add_argument(
        "--basic",
        action="store_true",
        help="Usar coleta básica (menos API units)"
    )

    parser.add_argument(
        "--collect-only",
        action="store_true",
        help="Apenas coletar dados (não gera dashboard)"
    )

    parser.add_argument(
        "--generate-only",
        action="store_true",
        help="Apenas gerar dashboard (usa último JSON)"
    )

    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Data para carregar dados (formato: YYYY-MM-DD)"
    )

    args = parser.parse_args()

    # Determinar modo de execução
    collect = not args.generate_only
    generate = not args.collect_only
    expanded = not args.basic  # Expandido é o padrão

    # Executar
    monitor = TrendMonitor(use_mock=args.mock, expanded=expanded)

    if args.date:
        monitor.date_str = args.date

    results = monitor.run(collect=collect, generate=generate)

    # Exit code baseado no sucesso
    sys.exit(0 if results["success"] else 1)


if __name__ == "__main__":
    main()

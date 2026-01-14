#!/usr/bin/env python3
"""
TREND MONITOR - Script Principal
=================================
Orquestra a coleta de trends, filtragem e geração de dashboard.

USO:
    python main.py                    # Execução completa
    python main.py --collect-only     # Apenas coleta (salva JSON)
    python main.py --generate-only    # Gera dashboard do último JSON
    python main.py --mock             # Usa dados mock (para testes)

ESTRUTURA DE SAÍDA:
    data/trends_YYYY-MM-DD.json       # Dados coletados
    output/trends-dashboard-YYYY-MM-DD.html  # Dashboard

VARIÁVEIS DE AMBIENTE:
    YOUTUBE_API_KEY       # API key do YouTube Data API v3
    REDDIT_CLIENT_ID      # Client ID do Reddit App
    REDDIT_CLIENT_SECRET  # Client Secret do Reddit App

AUTOR: Content Factory
DATA: Janeiro 2025
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
        from database.supabase import TrendDatabaseSupabase as TrendDatabase
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
    1. Coleta de múltiplas fontes
    2. Filtragem e scoring
    3. Geração de dashboard
    """

    def __init__(self, use_mock: bool = False):
        """
        Inicializa o monitor.

        Args:
            use_mock: Se True, usa dados mock ao invés de APIs reais
        """
        self.use_mock = use_mock
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

        logger.info("=" * 60)
        logger.info("TREND MONITOR - Inicializado")
        logger.info(f"Data: {self.date_str}")
        logger.info(f"Modo: {'MOCK' if use_mock else 'PRODUÇÃO'}")
        logger.info("=" * 60)

    def collect_all(self) -> Dict:
        """
        Coleta trends de todas as fontes.

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
            "hackernews": {},
            "metadata": {
                "collected_at": self.timestamp,
                "date": self.date_str,
                "countries": list(COUNTRIES.keys()),
                "sources": ["google_trends", "reddit", "youtube", "hackernews"]
            }
        }

        # 1. Google Trends
        logger.info("\n--- Google Trends ---")
        try:
            data["google_trends"] = self.google_collector.collect_all_countries()
        except Exception as e:
            logger.error(f"Erro na coleta Google Trends: {e}")
            data["google_trends"] = {}

        # 2. Reddit
        logger.info("\n--- Reddit ---")
        try:
            data["reddit"] = self.reddit_collector.collect_all()
        except Exception as e:
            logger.error(f"Erro na coleta Reddit: {e}")
            data["reddit"] = {}

        # 3. YouTube
        logger.info("\n--- YouTube ---")
        try:
            data["youtube"] = self.youtube_collector.collect_all_countries()
        except Exception as e:
            logger.error(f"Erro na coleta YouTube: {e}")
            data["youtube"] = {}

        # 4. Hacker News
        logger.info("\n--- Hacker News ---")
        try:
            data["hackernews"] = self.hackernews_collector.collect_all()
        except Exception as e:
            logger.error(f"Erro na coleta Hacker News: {e}")
            data["hackernews"] = {}

        # Estatísticas
        total = 0
        for source in ["google_trends", "reddit", "youtube", "hackernews"]:
            source_total = sum(len(v) for v in data[source].values())
            total += source_total
            logger.info(f"  {source}: {source_total} itens")

        logger.info(f"\nTOTAL COLETADO: {total} itens")

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
        Filtra e pontua os trends.

        Args:
            raw_data: Dados raw coletados

        Returns:
            Dados filtrados e organizados
        """
        logger.info("\n" + "=" * 60)
        logger.info("FASE 2: FILTRAGEM E SCORING")
        logger.info("=" * 60)

        # Preparar dados para o filtro
        filter_input = {
            "google_trends": raw_data.get("google_trends", {}),
            "reddit": raw_data.get("reddit", {}),
            "youtube": raw_data.get("youtube", {}),
            "hackernews": raw_data.get("hackernews", {})
        }

        filtered = self.filter.filter_all_trends(filter_input)

        # Adicionar metadata
        filtered["metadata"] = raw_data.get("metadata", {})
        filtered["metadata"]["filtered_at"] = datetime.now().isoformat()

        # Salvar no banco de dados
        logger.info("\n--- Salvando no Banco de Dados ---")
        all_trends = []
        for source, country_data in filter_input.items():
            for country, trends in country_data.items():
                for trend in trends:
                    trend["source"] = source
                    trend["country"] = country
                    all_trends.append(trend)

        saved = self.database.save_trends(all_trends)
        logger.info(f"Salvos {saved} trends no SQLite")

        # Atualizar padrões (evergreen, etc.)
        self.database.update_patterns()

        # Adicionar dados de evergreen ao filtered
        evergreen = self.database.get_evergreen_trends(min_days=7)
        filtered["evergreen_trends"] = evergreen
        filtered["stats"]["evergreen_count"] = len(evergreen)

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
  python main.py                    # Execução completa
  python main.py --mock             # Teste com dados mock
  python main.py --collect-only     # Apenas coleta dados
  python main.py --generate-only    # Gera dashboard do último JSON

Variáveis de ambiente necessárias:
  YOUTUBE_API_KEY       # Para coleta do YouTube
  REDDIT_CLIENT_ID      # Para coleta do Reddit
  REDDIT_CLIENT_SECRET  # Para coleta do Reddit
        """
    )

    parser.add_argument(
        "--mock",
        action="store_true",
        help="Usar dados mock ao invés de APIs reais"
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

    # Executar
    monitor = TrendMonitor(use_mock=args.mock)

    if args.date:
        monitor.date_str = args.date

    results = monitor.run(collect=collect, generate=generate)

    # Exit code baseado no sucesso
    sys.exit(0 if results["success"] else 1)


if __name__ == "__main__":
    main()

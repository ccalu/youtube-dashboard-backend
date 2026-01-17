"""
TREND MONITOR - HTML Report Generator
=======================================
Gera dashboard HTML com os trends coletados e filtrados.

ESTRUTURA DO DASHBOARD:
- ABA GERAL: Trends por país (top 30 por período)
- ABA DIRECIONADO: Trends filtrados por subnicho
- ABA HISTÓRICO: Calendário + evergreen detection
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    COUNTRIES, SUBNICHO_CONFIG, DASHBOARD_CONFIG,
    TEMPLATES_DIR, OUTPUT_DIR, COLLECTION_CONFIG, get_active_subnichos
)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HTMLReportGenerator:
    """
    Gerador de relatórios HTML para o Trend Monitor.

    Uso:
        generator = HTMLReportGenerator()
        generator.generate(filtered_data, output_path="dashboard.html")
    """

    def __init__(self, templates_dir: str = None):
        """
        Inicializa o gerador.

        Args:
            templates_dir: Diretório dos templates Jinja2
        """
        self.templates_dir = templates_dir or TEMPLATES_DIR
        self.env = self._setup_jinja()

    def _setup_jinja(self) -> Environment:
        """Configura ambiente Jinja2"""
        env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )

        # Filtros customizados
        env.filters['format_number'] = self._format_number
        env.filters['truncate_text'] = self._truncate_text
        env.filters['time_ago'] = self._time_ago

        return env

    def _format_number(self, value: int) -> str:
        """Formata número grande (1000 -> 1K, 1000000 -> 1M)"""
        if value >= 1_000_000:
            return f"{value / 1_000_000:.1f}M"
        elif value >= 1_000:
            return f"{value / 1_000:.1f}K"
        return str(value)

    def _truncate_text(self, text: str, length: int = 50) -> str:
        """Trunca texto com ellipsis"""
        if len(text) <= length:
            return text
        return text[:length-3] + "..."

    def _time_ago(self, timestamp: str) -> str:
        """Converte timestamp para 'há X tempo'"""
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            diff = datetime.now() - dt.replace(tzinfo=None)

            if diff.days > 0:
                return f"há {diff.days} dia{'s' if diff.days > 1 else ''}"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"há {hours} hora{'s' if hours > 1 else ''}"
            else:
                mins = diff.seconds // 60
                return f"há {mins} min"
        except:
            return ""

    def generate(self, data: Dict, output_path: str = None,
                 include_raw: bool = False) -> str:
        """
        Gera o dashboard HTML.

        Args:
            data: Dados filtrados do RelevanceFilter
            output_path: Caminho do arquivo de saída
            include_raw: Se True, inclui dados raw no HTML (para debug)

        Returns:
            Caminho do arquivo gerado
        """
        if output_path is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
            output_path = os.path.join(OUTPUT_DIR, f"trends-dashboard-{date_str}.html")

        # Garantir que diretório existe
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Preparar dados para o template
        context = self._prepare_context(data)

        # Verificar se template existe, se não, usar inline
        template_path = os.path.join(self.templates_dir, "dashboard.html")
        if os.path.exists(template_path):
            template = self.env.get_template("dashboard.html")
        else:
            logger.info("Template não encontrado, usando template inline")
            template = self.env.from_string(self._get_inline_template())

        # Renderizar
        html = template.render(**context)

        # Salvar
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        logger.info(f"Dashboard gerado: {output_path}")
        return output_path

    def _prepare_context(self, data: Dict) -> Dict:
        """Prepara contexto para o template"""
        now = datetime.now()

        # Detectar se dados vem do novo formato (com quality_score)
        is_new_format = "all_items" in data or "quality_summary" in data

        max_display = COLLECTION_CONFIG["max_trends_display"]

        # ==== NOVO FORMATO: Com quality_score e by_subnicho organizado ====
        if is_new_format:
            all_items = data.get("all_items", [])
            by_source = data.get("by_source", {})
            by_subnicho = data.get("by_subnicho", {})
            by_language = data.get("by_language", {})
            top_quality = data.get("top_quality", [])
            quality_summary = data.get("quality_summary", {})

            # Preparar trends raw por fonte (novo formato)
            google_trends_raw = by_source.get("google_trends", [])[:max_display]
            youtube_raw = by_source.get("youtube", [])[:max_display]
            reddit_raw = []  # Desabilitado
            hackernews_raw = by_source.get("hackernews", [])[:max_display]

            # Preparar dados por subnicho (novo formato com quality_score)
            trends_by_subnicho = {}
            subnichos = get_active_subnichos()
            for subnicho_key, subnicho_info in subnichos.items():
                subnicho_trends = by_subnicho.get(subnicho_key, [])
                # Ordenar por quality_score
                subnicho_trends.sort(key=lambda x: x.get("quality_score", 0), reverse=True)
                trends_by_subnicho[subnicho_key] = {
                    "info": subnicho_info,
                    "trends": subnicho_trends[:max_display],
                    "total": len(subnicho_trends)
                }

            # Top por lingua (novo formato)
            top_by_language = {
                "en": by_language.get("en", [])[:max_display],
                "pt": by_language.get("pt", [])[:max_display],
                "es": by_language.get("es", [])[:max_display],
                "other": []
            }
            # Adicionar outras linguas em "other"
            for lang, items in by_language.items():
                if lang not in ["en", "pt", "es"]:
                    top_by_language["other"].extend(items)
            top_by_language["other"] = top_by_language["other"][:max_display]

            # Organizar por pais
            trends_by_country = {}
            for country_code, country_info in COUNTRIES.items():
                country_trends = [i for i in all_items if i.get("country") == country_code]
                country_trends.sort(key=lambda x: x.get("quality_score", 0), reverse=True)
                trends_by_country[country_code] = {
                    "info": country_info,
                    "trends": country_trends[:max_display]
                }

            # Evergreen
            evergreen_trends = data.get("evergreen_trends", [])[:20]

            return {
                "title": DASHBOARD_CONFIG["title"],
                "subtitle": DASHBOARD_CONFIG["subtitle"],
                "theme": DASHBOARD_CONFIG["theme"],
                "font_family": DASHBOARD_CONFIG["font_family"],
                "generated_at": now.strftime("%d %b %Y, %H:%M"),
                "date_iso": now.isoformat(),
                "countries": COUNTRIES,
                "subnichos": subnichos,
                # Dados por fonte
                "google_trends_raw": google_trends_raw,
                "youtube_raw": youtube_raw,
                "reddit_raw": reddit_raw,
                "hackernews_raw": hackernews_raw,
                # Por subnicho
                "trends_by_subnicho": trends_by_subnicho,
                "trends_by_country": trends_by_country,
                # Top quality
                "top_trends": top_quality[:50],
                "top_quality": top_quality,
                # Cross platform e multi country (vazios no novo formato)
                "cross_platform_trends": [],
                "multi_country_trends": [],
                "evergreen_trends": evergreen_trends,
                # Stats
                "stats": data.get("stats", {}),
                "quality_summary": quality_summary,
                "time_periods": COLLECTION_CONFIG["time_periods"],
                "max_display": max_display,
                "top_by_language": top_by_language,
                "is_new_format": True
            }

        # ==== FORMATO ANTIGO: Compatibilidade ====
        raw_by_source = data.get("raw_by_source", {})

        # Preparar trends raw por fonte
        google_trends_raw = raw_by_source.get("google_trends", [])[:max_display]
        youtube_raw = raw_by_source.get("youtube", [])[:max_display]
        reddit_raw = raw_by_source.get("reddit", [])[:max_display]
        hackernews_raw = raw_by_source.get("hackernews", [])[:max_display]

        # ==== ABA DIRECIONADO: Trends filtrados por subnicho ====
        trends_by_subnicho = {}
        subnichos = get_active_subnichos()
        for subnicho_key, subnicho_info in subnichos.items():
            subnicho_trends = data.get("by_subnicho", {}).get(subnicho_key, [])
            trends_by_subnicho[subnicho_key] = {
                "info": subnicho_info,
                "trends": subnicho_trends[:max_display]
            }

        # Organizar trends por país (para relatório)
        trends_by_country = {}
        for country_code, country_info in COUNTRIES.items():
            country_trends = data.get("by_country", {}).get(country_code, [])
            trends_by_country[country_code] = {
                "info": country_info,
                "trends": country_trends[:max_display]
            }

        # Top trends (relevantes para subnichos - para relatório)
        all_scored = data.get("all_scored", [])
        top_trends = all_scored[:50]

        # Cross-platform trends (aparecem em múltiplas fontes)
        cross_platform = [t for t in all_scored if t.get("is_cross_platform")][:20]

        # Multi-country trends (aparecem em múltiplos países)
        multi_country = [t for t in all_scored if t.get("is_multi_country")][:20]

        # Evergreen trends (do banco de dados)
        evergreen_trends = data.get("evergreen_trends", [])[:20]

        # ==== ANALISES: Top 10 por Lingua ====
        # Combinar todos os trends raw para analise por lingua
        all_raw_trends = []
        for source_key in ["google_trends", "youtube", "reddit", "hackernews"]:
            source_trends = raw_by_source.get(source_key, [])
            for t in source_trends:
                t["source_type"] = source_key
            all_raw_trends.extend(source_trends)

        # Ordenar por volume (descrescente)
        all_raw_trends.sort(key=lambda x: x.get("volume", 0) or 0, reverse=True)

        # Separar por lingua
        top_by_language = {
            "en": [],
            "pt": [],
            "es": [],
            "other": []
        }

        language_map = {
            "US": "en",
            "BR": "pt",
            "ES": "es",
            "FR": "other",
            "KR": "other",
            "JP": "other",
            "IT": "other"
        }

        for trend in all_raw_trends:
            country = trend.get("country", "")
            lang = trend.get("language", language_map.get(country, "en"))

            if lang == "en":
                top_by_language["en"].append(trend)
            elif lang == "pt":
                top_by_language["pt"].append(trend)
            elif lang == "es":
                top_by_language["es"].append(trend)
            else:
                top_by_language["other"].append(trend)

        return {
            "title": DASHBOARD_CONFIG["title"],
            "subtitle": DASHBOARD_CONFIG["subtitle"],
            "theme": DASHBOARD_CONFIG["theme"],
            "font_family": DASHBOARD_CONFIG["font_family"],
            "generated_at": now.strftime("%d %b %Y, %H:%M"),
            "date_iso": now.isoformat(),
            "countries": COUNTRIES,
            "subnichos": subnichos,
            # ABA GERAL - Trends RAW por fonte
            "google_trends_raw": google_trends_raw,
            "youtube_raw": youtube_raw,
            "reddit_raw": reddit_raw,
            "hackernews_raw": hackernews_raw,
            # ABA DIRECIONADO - Filtrados por subnicho
            "trends_by_subnicho": trends_by_subnicho,
            "trends_by_country": trends_by_country,
            # Relatório
            "top_trends": top_trends,
            "cross_platform_trends": cross_platform,
            "multi_country_trends": multi_country,
            "evergreen_trends": evergreen_trends,
            "stats": data.get("stats", {}),
            "time_periods": COLLECTION_CONFIG["time_periods"],
            "max_display": max_display,
            # Top por lingua para aba ANALISES
            "top_by_language": top_by_language
        }

    def _get_inline_template(self) -> str:
        """Retorna template HTML inline (fallback)"""
        return '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        :root {
            --bg-primary: {{ theme.bg_primary }};
            --bg-secondary: {{ theme.bg_secondary }};
            --bg-card: {{ theme.bg_card }};
            --accent: {{ theme.accent }};
            --accent-hover: {{ theme.accent_hover }};
            --text-primary: {{ theme.text_primary }};
            --text-secondary: {{ theme.text_secondary }};
            --text-muted: {{ theme.text_muted }};
            --border: {{ theme.border }};
            --success: {{ theme.success }};
            --warning: {{ theme.warning }};
            --danger: {{ theme.danger }};
            --google: #4285f4;
            --youtube: #ff0000;
            --reddit: #ff4500;
        }

        body {
            font-family: {{ font_family }};
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            line-height: 1.6;
        }

        /* Header */
        .header {
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border);
            padding: 1.5rem 2rem;
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .header-content {
            max-width: 1800px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .logo h1 {
            font-size: 1.5rem;
            font-weight: 800;
            color: var(--accent);
        }

        .status {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: var(--text-secondary);
            font-size: 0.875rem;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            background: var(--success);
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        /* Global Filters Bar */
        .global-filters {
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border);
            padding: 1rem 2rem;
            position: sticky;
            top: 70px;
            z-index: 99;
        }

        .filters-content {
            max-width: 1800px;
            margin: 0 auto;
            display: flex;
            gap: 1.5rem;
            align-items: center;
            flex-wrap: wrap;
        }

        .filter-group {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .filter-label {
            color: var(--text-secondary);
            font-size: 0.875rem;
            font-weight: 500;
        }

        .filter-select {
            background: var(--bg-card);
            border: 1px solid var(--border);
            color: var(--text-primary);
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-family: inherit;
            cursor: pointer;
            font-size: 0.875rem;
        }

        .filter-select:focus {
            outline: none;
            border-color: var(--accent);
        }

        .filter-count {
            background: var(--accent);
            color: var(--bg-primary);
            font-size: 0.75rem;
            font-weight: 700;
            padding: 0.25rem 0.5rem;
            border-radius: 10px;
            margin-left: auto;
        }

        /* Navigation Tabs */
        .nav-tabs {
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border);
            padding: 0 2rem;
        }

        .nav-tabs ul {
            max-width: 1800px;
            margin: 0 auto;
            display: flex;
            list-style: none;
            gap: 0;
        }

        .nav-tabs a {
            display: block;
            padding: 1rem 1.5rem;
            color: var(--text-secondary);
            text-decoration: none;
            font-weight: 600;
            transition: all 0.2s;
            border-bottom: 2px solid transparent;
        }

        .nav-tabs a:hover { color: var(--text-primary); }

        .nav-tabs a.active {
            color: var(--accent);
            border-bottom-color: var(--accent);
        }

        /* Main Content */
        .main {
            max-width: 1800px;
            margin: 0 auto;
            padding: 2rem;
        }

        .tab-content { display: none; }
        .tab-content.active { display: block; }

        /* Stats Bar */
        .stats-bar {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }

        .stat-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.25rem;
            text-align: center;
        }

        .stat-value {
            font-size: 1.75rem;
            font-weight: 800;
            color: var(--accent);
        }

        .stat-label {
            color: var(--text-secondary);
            font-size: 0.8rem;
            margin-top: 0.25rem;
        }

        /* Source Section */
        .source-section {
            margin-bottom: 2.5rem;
        }

        .source-header {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1.25rem;
            padding: 1rem 1.25rem;
            border-radius: 12px;
            border: 1px solid var(--border);
        }

        .source-header.google { background: linear-gradient(135deg, rgba(66,133,244,0.15) 0%, var(--bg-card) 100%); border-left: 4px solid var(--google); }
        .source-header.youtube { background: linear-gradient(135deg, rgba(255,0,0,0.15) 0%, var(--bg-card) 100%); border-left: 4px solid var(--youtube); }
        .source-header.reddit { background: linear-gradient(135deg, rgba(255,69,0,0.15) 0%, var(--bg-card) 100%); border-left: 4px solid var(--reddit); }

        .source-icon {
            font-size: 1.75rem;
        }

        .source-info h2 {
            font-size: 1.25rem;
            font-weight: 700;
        }

        .source-info p {
            color: var(--text-secondary);
            font-size: 0.8rem;
        }

        .source-count {
            margin-left: auto;
            font-weight: 700;
            font-size: 1.25rem;
            color: var(--accent);
        }

        /* Trends Grid */
        .trends-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 1rem;
        }

        .trend-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.25rem;
            transition: all 0.2s;
        }

        .trend-card:hover {
            border-color: var(--accent);
            transform: translateY(-2px);
        }

        .trend-card.hidden { display: none; }

        .trend-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 0.75rem;
            margin-bottom: 0.75rem;
        }

        .trend-rank {
            background: var(--accent);
            color: var(--bg-primary);
            font-weight: 700;
            font-size: 0.7rem;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            flex-shrink: 0;
        }

        .trend-title {
            font-weight: 600;
            font-size: 0.95rem;
            flex-grow: 1;
            line-height: 1.4;
        }

        .trend-score {
            background: var(--bg-secondary);
            color: var(--accent);
            font-weight: 700;
            font-size: 0.8rem;
            padding: 0.2rem 0.6rem;
            border-radius: 20px;
            flex-shrink: 0;
        }

        .trend-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            font-size: 0.75rem;
            color: var(--text-secondary);
            margin-top: 0.5rem;
        }

        .trend-meta-item {
            display: flex;
            align-items: center;
            gap: 0.25rem;
            background: var(--bg-secondary);
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
        }

        .badge-cross {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-size: 0.65rem;
            padding: 0.15rem 0.4rem;
            border-radius: 4px;
            margin-left: 0.5rem;
        }

        .badge-multi {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            font-size: 0.65rem;
            padding: 0.15rem 0.4rem;
            border-radius: 4px;
            margin-left: 0.5rem;
        }

        /* Subnicho Section */
        .subnicho-section {
            margin-bottom: 2rem;
        }

        .subnicho-header {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1rem;
            padding: 1rem;
            background: var(--bg-card);
            border-radius: 12px;
            border: 1px solid var(--border);
        }

        .subnicho-icon { font-size: 2rem; }

        .subnicho-info h3 {
            font-size: 1.25rem;
            font-weight: 700;
        }

        .subnicho-info p {
            color: var(--text-secondary);
            font-size: 0.8rem;
        }

        .subnicho-count {
            margin-left: auto;
            background: var(--accent);
            color: var(--bg-primary);
            font-weight: 700;
            padding: 0.5rem 1rem;
            border-radius: 20px;
        }

        /* Volume Bar */
        .trend-volume {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin: 0.75rem 0;
            background: var(--bg-secondary);
            border-radius: 8px;
            padding: 0.5rem 0.75rem;
        }

        .volume-bar {
            height: 6px;
            background: linear-gradient(90deg, var(--accent) 0%, #00ff88 100%);
            border-radius: 3px;
            min-width: 10px;
            max-width: 60%;
            flex-shrink: 0;
        }

        .volume-text {
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--text-secondary);
            white-space: nowrap;
        }

        /* Trend Analysis */
        .trend-analysis {
            background: linear-gradient(135deg, rgba(0,212,170,0.1) 0%, rgba(0,212,170,0.05) 100%);
            border-left: 3px solid var(--accent);
            padding: 0.75rem;
            margin: 0.75rem 0;
            border-radius: 0 8px 8px 0;
            font-size: 0.8rem;
            color: var(--text-secondary);
            line-height: 1.5;
        }

        /* Trend Link */
        .trend-link {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            margin-top: 0.75rem;
            padding: 0.5rem 1rem;
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--accent);
            text-decoration: none;
            font-size: 0.8rem;
            font-weight: 600;
            transition: all 0.2s;
        }

        .trend-link:hover {
            background: var(--accent);
            color: var(--bg-primary);
            border-color: var(--accent);
        }

        .trend-link::after {
            content: "→";
        }

        /* Report Tab Styles */
        .report-section {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 2rem;
        }

        .report-section h2 {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--accent);
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .insight-card {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.25rem;
            margin-bottom: 1rem;
        }

        .insight-card h3 {
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: var(--text-primary);
        }

        .insight-card p {
            font-size: 0.875rem;
            color: var(--text-secondary);
            line-height: 1.6;
        }

        .insight-highlight {
            background: linear-gradient(135deg, rgba(0,212,170,0.15) 0%, rgba(0,212,170,0.05) 100%);
            border-left: 4px solid var(--accent);
        }

        .insight-warning {
            background: linear-gradient(135deg, rgba(255,193,7,0.15) 0%, rgba(255,193,7,0.05) 100%);
            border-left: 4px solid var(--warning);
        }

        .top-opportunities {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }

        .opportunity-card {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.25rem;
            transition: all 0.2s;
        }

        .opportunity-card:hover {
            border-color: var(--accent);
            transform: translateY(-2px);
        }

        .opportunity-rank {
            display: inline-block;
            background: var(--accent);
            color: var(--bg-primary);
            font-weight: 700;
            font-size: 0.75rem;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            margin-bottom: 0.5rem;
        }

        .opportunity-title {
            font-weight: 600;
            font-size: 1rem;
            margin-bottom: 0.5rem;
        }

        .opportunity-meta {
            font-size: 0.8rem;
            color: var(--text-secondary);
        }

        .summary-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin: 1.5rem 0;
        }

        .summary-stat {
            text-align: center;
            padding: 1rem;
            background: var(--bg-secondary);
            border-radius: 12px;
        }

        .summary-stat-value {
            font-size: 2rem;
            font-weight: 800;
            color: var(--accent);
        }

        .summary-stat-label {
            font-size: 0.8rem;
            color: var(--text-secondary);
        }

        /* Empty State */
        .empty-state {
            text-align: center;
            padding: 3rem;
            color: var(--text-muted);
        }

        .empty-state h3 {
            font-size: 1.25rem;
            margin-bottom: 0.5rem;
        }

        /* Footer */
        .footer {
            text-align: center;
            padding: 2rem;
            color: var(--text-muted);
            font-size: 0.875rem;
            border-top: 1px solid var(--border);
            margin-top: 2rem;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .header-content { flex-direction: column; gap: 1rem; text-align: center; }
            .filters-content { justify-content: center; }
            .nav-tabs ul { justify-content: center; }
            .main { padding: 1rem; }
            .stats-bar { grid-template-columns: repeat(2, 1fr); }
            .trends-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <!-- Header -->
    <header class="header">
        <div class="header-content">
            <div class="logo">
                <h1>{{ title }}</h1>
            </div>
            <div class="status">
                <span class="status-dot"></span>
                <span>Atualizado: {{ generated_at }}</span>
            </div>
        </div>
    </header>

    <!-- Global Filters -->
    <div class="global-filters">
        <div class="filters-content">
            <div class="filter-group">
                <span class="filter-label">Fonte:</span>
                <select class="filter-select" id="filter-source" onchange="applyFilters()">
                    <option value="all">Todas as Fontes</option>
                    <option value="google_trends">🔍 Google Trends</option>
                    <option value="youtube">📺 YouTube</option>
                    <option value="reddit">💬 Reddit</option>
                    <option value="hackernews">📰 Hacker News</option>
                </select>
            </div>
            <div class="filter-group">
                <span class="filter-label">Pais:</span>
                <select class="filter-select" id="filter-country" onchange="applyFilters()">
                    <option value="all">Todos os Paises</option>
                    {% for code, info in countries.items() %}
                    <option value="{{ code }}">{{ info.flag }} {{ info.name }}</option>
                    {% endfor %}
                </select>
            </div>
            <div class="filter-group">
                <span class="filter-label">Lingua:</span>
                <select class="filter-select" id="filter-language" onchange="applyFilters()">
                    <option value="all">Todas</option>
                    <option value="en">🇺🇸 Ingles</option>
                    <option value="pt">🇧🇷 Portugues</option>
                    <option value="es">🇪🇸 Espanhol</option>
                    <option value="fr">🇫🇷 Frances</option>
                    <option value="ko">🇰🇷 Coreano</option>
                    <option value="ja">🇯🇵 Japones</option>
                    <option value="it">🇮🇹 Italiano</option>
                </select>
            </div>
            <div class="filter-group">
                <span class="filter-label">Subnicho:</span>
                <select class="filter-select" id="filter-subnicho" onchange="applyFilters()">
                    <option value="all">Todos</option>
                    {% for key, info in subnichos.items() %}
                    <option value="{{ key }}">{{ info.icon }} {{ info.name }}</option>
                    {% endfor %}
                </select>
            </div>
            <span class="filter-count" id="visible-count">{{ stats.total_relevant|default(0) }} trends</span>
        </div>
    </div>

    <!-- Navigation -->
    <nav class="nav-tabs">
        <ul>
            <li><a href="#geral" class="active" onclick="showTab('geral')">GERAL</a></li>
            <li><a href="#direcionado" onclick="showTab('direcionado')">DIRECIONADO</a></li>
            <li><a href="#analises" onclick="showTab('analises')">ANALISES</a></li>
            <li><a href="#relatorio" onclick="showTab('relatorio')">RELATORIO</a></li>
            <li><a href="#historico" onclick="showTab('historico')">HISTORICO</a></li>
        </ul>
    </nav>

    <!-- Main Content -->
    <main class="main">
        <!-- Stats Bar -->
        <div class="stats-bar">
            <div class="stat-card">
                <div class="stat-value">{{ stats.total_raw|default(stats.total_processed|default(0)) }}</div>
                <div class="stat-label">Total Coletados</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ stats.total_relevant|default(0) }}</div>
                <div class="stat-label">Match Subnichos</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ stats.cross_platform_count|default(0) }}</div>
                <div class="stat-label">Cross-Platform</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ stats.multi_country_count|default(0) }}</div>
                <div class="stat-label">Multi-Pais</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">4</div>
                <div class="stat-label">Fontes</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ countries|length }}</div>
                <div class="stat-label">Paises</div>
            </div>
        </div>

        <!-- Tab: GERAL (TODOS os Trends RAW - SEM filtro de subnicho) -->
        <div id="geral" class="tab-content active">

            <div class="section-intro" style="background: linear-gradient(135deg, rgba(0,212,170,0.1) 0%, transparent 100%); border-radius: 12px; padding: 1rem 1.5rem; margin-bottom: 1.5rem; border-left: 4px solid var(--accent);">
                <h2 style="font-size: 1.25rem; margin-bottom: 0.5rem;">🌍 Todos os Trends (Sem Filtro)</h2>
                <p style="color: var(--text-secondary); font-size: 0.9rem;">Dados RAW de todas as fontes. Use para descobrir novas oportunidades fora dos seus subnichos atuais.</p>
            </div>

            <!-- Google Trends Section (RAW) -->
            <div class="source-section" data-source="google_trends">
                <div class="source-header google">
                    <span class="source-icon">🔍</span>
                    <div class="source-info">
                        <h2>Google Trends</h2>
                        <p>Buscas em alta - Dados reais do Google</p>
                    </div>
                    <span class="source-count">{{ google_trends_raw|length }}</span>
                </div>
                <div class="trends-grid">
                    {% for trend in google_trends_raw %}
                    <div class="trend-card" data-source="google_trends" data-country="{{ trend.country }}" data-language="{{ trend.language|default(countries[trend.country].language if trend.country in countries else 'en') }}">
                        <div class="trend-header">
                            <span class="trend-rank">#{{ loop.index }}</span>
                            <span class="trend-title">{{ trend.title }}</span>
                        </div>
                        <div class="trend-volume">
                            <span class="volume-bar" style="width: {{ [trend.volume / 10000, 100] | min }}%"></span>
                            <span class="volume-text">{% if trend.volume >= 1000000 %}{{ (trend.volume / 1000000) | round(1) }}M{% elif trend.volume >= 1000 %}{{ (trend.volume / 1000) | round(0) | int }}K{% else %}{{ trend.volume }}{% endif %} buscas</span>
                        </div>
                        <div class="trend-meta">
                            <span class="trend-meta-item">{{ countries[trend.country].flag if trend.country in countries else '🌍' }} {{ trend.country }}</span>
                            {% if trend.is_cross_platform %}<span class="badge-cross">CROSS</span>{% endif %}
                            {% if trend.is_multi_country %}<span class="badge-multi">MULTI</span>{% endif %}
                        </div>
                        {% if trend.url %}<a href="{{ trend.url }}" target="_blank" class="trend-link">Ver no Google</a>{% endif %}
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- YouTube Section (RAW) -->
            <div class="source-section" data-source="youtube">
                <div class="source-header youtube">
                    <span class="source-icon">📺</span>
                    <div class="source-info">
                        <h2>YouTube Trending</h2>
                        <p>Videos em alta - Dados da API oficial</p>
                    </div>
                    <span class="source-count">{{ youtube_raw|length }}</span>
                </div>
                <div class="trends-grid">
                    {% for trend in youtube_raw %}
                    <div class="trend-card" data-source="youtube" data-country="{{ trend.country }}" data-language="{{ trend.language|default(countries[trend.country].language if trend.country in countries else 'en') }}">
                        <div class="trend-header">
                            <span class="trend-rank">#{{ loop.index }}</span>
                            <span class="trend-title">{{ trend.title }}</span>
                        </div>
                        <div class="trend-volume">
                            <span class="volume-bar" style="width: {{ [trend.volume / 1000000, 100] | min }}%"></span>
                            <span class="volume-text">{% if trend.volume >= 1000000 %}{{ (trend.volume / 1000000) | round(1) }}M{% elif trend.volume >= 1000 %}{{ (trend.volume / 1000) | round(0) | int }}K{% else %}{{ trend.volume }}{% endif %} views</span>
                        </div>
                        <div class="trend-meta">
                            <span class="trend-meta-item">{{ countries[trend.country].flag if trend.country in countries else '🌍' }} {{ trend.country }}</span>
                            {% if trend.channel_title %}<span class="trend-meta-item">📺 {{ trend.channel_title }}</span>{% endif %}
                            {% if trend.is_cross_platform %}<span class="badge-cross">CROSS</span>{% endif %}
                            {% if trend.is_multi_country %}<span class="badge-multi">MULTI</span>{% endif %}
                        </div>
                        {% if trend.url %}<a href="{{ trend.url }}" target="_blank" class="trend-link">Ver video</a>{% endif %}
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- Reddit Section (RAW) -->
            <div class="source-section" data-source="reddit">
                <div class="source-header reddit">
                    <span class="source-icon">💬</span>
                    <div class="source-info">
                        <h2>Reddit Hot</h2>
                        <p>Posts populares - Dados da API oficial</p>
                    </div>
                    <span class="source-count">{{ reddit_raw|length }}</span>
                </div>
                <div class="trends-grid">
                    {% for trend in reddit_raw %}
                    <div class="trend-card" data-source="reddit" data-country="{{ trend.country }}" data-language="{{ trend.language|default(countries[trend.country].language if trend.country in countries else 'en') }}">
                        <div class="trend-header">
                            <span class="trend-rank">#{{ loop.index }}</span>
                            <span class="trend-title">{{ trend.title }}</span>
                        </div>
                        <div class="trend-volume">
                            <span class="volume-bar" style="width: {{ [trend.volume / 50000, 100] | min }}%"></span>
                            <span class="volume-text">{% if trend.volume >= 1000 %}{{ (trend.volume / 1000) | round(1) }}K{% else %}{{ trend.volume }}{% endif %} upvotes</span>
                        </div>
                        <div class="trend-meta">
                            <span class="trend-meta-item">{{ countries[trend.country].flag if trend.country in countries else '🌍' }} {{ trend.country }}</span>
                            {% if trend.subreddit %}<span class="trend-meta-item">r/{{ trend.subreddit }}</span>{% endif %}
                            {% if trend.num_comments %}<span class="trend-meta-item">💬 {{ trend.num_comments }} comments</span>{% endif %}
                            {% if trend.is_cross_platform %}<span class="badge-cross">CROSS</span>{% endif %}
                        </div>
                        {% if trend.url %}<a href="{{ trend.url }}" target="_blank" class="trend-link">Ver post</a>{% endif %}
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- Hacker News Section (RAW) -->
            <div class="source-section" data-source="hackernews">
                <div class="source-header" style="background: linear-gradient(135deg, rgba(255,102,0,0.15) 0%, var(--bg-card) 100%); border-left: 4px solid #ff6600;">
                    <span class="source-icon">📰</span>
                    <div class="source-info">
                        <h2>Hacker News</h2>
                        <p>Top stories tech/startup - API publica</p>
                    </div>
                    <span class="source-count">{{ hackernews_raw|length }}</span>
                </div>
                <div class="trends-grid">
                    {% for trend in hackernews_raw %}
                    <div class="trend-card" data-source="hackernews" data-country="global">
                        <div class="trend-header">
                            <span class="trend-rank">#{{ loop.index }}</span>
                            <span class="trend-title">{{ trend.title }}</span>
                        </div>
                        <div class="trend-volume">
                            <span class="volume-bar" style="width: {{ [trend.volume / 500, 100] | min }}%"></span>
                            <span class="volume-text">{{ trend.volume }} pontos</span>
                        </div>
                        <div class="trend-meta">
                            <span class="trend-meta-item">🌍 Global</span>
                            {% if trend.author %}<span class="trend-meta-item">👤 {{ trend.author }}</span>{% endif %}
                            {% if trend.num_comments %}<span class="trend-meta-item">💬 {{ trend.num_comments }} comments</span>{% endif %}
                        </div>
                        <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                            {% if trend.url %}<a href="{{ trend.url }}" target="_blank" class="trend-link">Ver artigo</a>{% endif %}
                            {% if trend.hn_url %}<a href="{{ trend.hn_url }}" target="_blank" class="trend-link" style="background: rgba(255,102,0,0.1); border-color: #ff6600; color: #ff6600;">Discussao HN</a>{% endif %}
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>

        </div>

        <!-- Tab: DIRECIONADO (Por Subnicho - SO trends que matcham os 7 canais) -->
        <div id="direcionado" class="tab-content">

            <div class="section-intro" style="background: linear-gradient(135deg, rgba(255,102,0,0.1) 0%, transparent 100%); border-radius: 12px; padding: 1rem 1.5rem; margin-bottom: 1.5rem; border-left: 4px solid #ff6600;">
                <h2 style="font-size: 1.25rem; margin-bottom: 0.5rem;">🎯 Trends Filtrados por Subnicho</h2>
                <p style="color: var(--text-secondary); font-size: 0.9rem;">Apenas trends que correspondem aos seus 7 canais atuais. Score indica relevancia para producao de conteudo.</p>
            </div>

            {% for key, data in trends_by_subnicho.items() %}
            <div class="subnicho-section" data-subnicho="{{ key }}">
                <div class="subnicho-header">
                    <span class="subnicho-icon">{{ data.info.icon }}</span>
                    <div class="subnicho-info">
                        <h3>{{ data.info.name }}</h3>
                        <p>{{ data.info.description }}</p>
                    </div>
                    <span class="subnicho-count">{{ data.trends|length }}</span>
                </div>
                <div class="trends-grid">
                    {% for trend in data.trends[:max_display] %}
                    <div class="trend-card" data-source="{{ trend.source }}" data-country="{{ trend.country }}" data-subnicho="{{ key }}" data-language="{{ trend.language|default(countries[trend.country].language if trend.country in countries else 'en') }}">
                        <div class="trend-header">
                            <span class="trend-rank">#{{ loop.index }}</span>
                            <span class="trend-title">{{ trend.title }}</span>
                            <span class="trend-score">{{ trend.quality_score|default(0) }}%</span>
                        </div>
                        <div class="trend-volume">
                            <span class="volume-bar" style="width: {{ [trend.volume / 50000, 100] | min }}%"></span>
                            <span class="volume-text">{% if trend.volume >= 1000000 %}{{ (trend.volume / 1000000) | round(1) }}M{% elif trend.volume >= 1000 %}{{ (trend.volume / 1000) | round(0) | int }}K{% else %}{{ trend.volume }}{% endif %}</span>
                        </div>
                        <div class="trend-meta">
                            <span class="trend-meta-item">{% for c in trend.countries_found %}{{ countries[c].flag if c in countries else c }}{% endfor %}</span>
                            <span class="trend-meta-item">{{ trend.source }}</span>
                            {% if trend.is_cross_platform %}<span class="badge-cross">CROSS</span>{% endif %}
                            {% if trend.is_multi_country %}<span class="badge-multi">MULTI</span>{% endif %}
                        </div>
                        {% if trend.analysis %}<div class="trend-analysis">{{ trend.analysis }}</div>{% endif %}
                        {% if trend.url %}<a href="{{ trend.url }}" target="_blank" class="trend-link">Ver fonte</a>{% endif %}
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endfor %}
        </div>

        <!-- Tab: ANALISES (Top 10 por Lingua e Subnicho) -->
        <div id="analises" class="tab-content">

            <div class="section-intro" style="background: linear-gradient(135deg, rgba(138,43,226,0.1) 0%, transparent 100%); border-radius: 12px; padding: 1rem 1.5rem; margin-bottom: 1.5rem; border-left: 4px solid #8a2be2;">
                <h2 style="font-size: 1.25rem; margin-bottom: 0.5rem;">📊 Analises e Recomendacoes</h2>
                <p style="color: var(--text-secondary); font-size: 0.9rem;">Top 10 trends organizados por lingua e subnicho. Use para identificar oportunidades em cada mercado.</p>
            </div>

            <!-- TOP 10 GERAL POR LINGUA -->
            <div class="report-section" style="margin-bottom: 2rem;">
                <h2>🌍 Top 10 por Lingua (Descobertas Gerais)</h2>
                <p style="color: var(--text-secondary); margin-bottom: 1.5rem;">Trends com maior volume por idioma - ideal para descobrir novos topicos fora dos seus subnichos.</p>

                <!-- English -->
                <div class="subnicho-section">
                    <div class="subnicho-header" style="background: linear-gradient(135deg, rgba(66,133,244,0.15) 0%, var(--bg-card) 100%); border-left: 4px solid #4285f4;">
                        <span class="subnicho-icon">🇺🇸</span>
                        <div class="subnicho-info">
                            <h3>Ingles (US)</h3>
                            <p>Tendencias em ingles - Maior audiencia global</p>
                        </div>
                    </div>
                    <div class="trends-grid">
                        {% for trend in top_by_language.en[:10] %}
                        <div class="trend-card">
                            <div class="trend-header">
                                <span class="trend-rank">#{{ loop.index }}</span>
                                <span class="trend-title">{{ trend.title }}</span>
                            </div>
                            <div class="trend-volume">
                                <span class="volume-bar" style="width: {{ [(trend.volume|default(0)) / 100000, 100] | min }}%"></span>
                                <span class="volume-text">{% if trend.volume|default(0) >= 1000000 %}{{ (trend.volume / 1000000) | round(1) }}M{% elif trend.volume|default(0) >= 1000 %}{{ (trend.volume / 1000) | round(0) | int }}K{% else %}{{ trend.volume|default(0) }}{% endif %}</span>
                            </div>
                            <div class="trend-meta">
                                <span class="trend-meta-item">{{ trend.source }}</span>
                                {% if trend.is_new %}<span style="background: #ff6b35; color: white; padding: 0.1rem 0.4rem; border-radius: 4px; font-size: 0.65rem; font-weight: 700;">NOVO</span>{% endif %}
                            </div>
                            {% if trend.url %}<a href="{{ trend.url }}" target="_blank" class="trend-link">Ver fonte</a>{% endif %}
                        </div>
                        {% endfor %}
                        {% if not top_by_language.en %}
                        <div class="empty-state" style="grid-column: 1/-1;"><p>Nenhum trend em ingles coletado</p></div>
                        {% endif %}
                    </div>
                </div>

                <!-- Portugues -->
                <div class="subnicho-section">
                    <div class="subnicho-header" style="background: linear-gradient(135deg, rgba(0,156,59,0.15) 0%, var(--bg-card) 100%); border-left: 4px solid #009c3b;">
                        <span class="subnicho-icon">🇧🇷</span>
                        <div class="subnicho-info">
                            <h3>Portugues (BR)</h3>
                            <p>Tendencias em portugues - Mercado brasileiro</p>
                        </div>
                    </div>
                    <div class="trends-grid">
                        {% for trend in top_by_language.pt[:10] %}
                        <div class="trend-card">
                            <div class="trend-header">
                                <span class="trend-rank">#{{ loop.index }}</span>
                                <span class="trend-title">{{ trend.title }}</span>
                            </div>
                            <div class="trend-volume">
                                <span class="volume-bar" style="width: {{ [(trend.volume|default(0)) / 100000, 100] | min }}%"></span>
                                <span class="volume-text">{% if trend.volume|default(0) >= 1000000 %}{{ (trend.volume / 1000000) | round(1) }}M{% elif trend.volume|default(0) >= 1000 %}{{ (trend.volume / 1000) | round(0) | int }}K{% else %}{{ trend.volume|default(0) }}{% endif %}</span>
                            </div>
                            <div class="trend-meta">
                                <span class="trend-meta-item">{{ trend.source }}</span>
                                {% if trend.is_new %}<span style="background: #ff6b35; color: white; padding: 0.1rem 0.4rem; border-radius: 4px; font-size: 0.65rem; font-weight: 700;">NOVO</span>{% endif %}
                            </div>
                            {% if trend.url %}<a href="{{ trend.url }}" target="_blank" class="trend-link">Ver fonte</a>{% endif %}
                        </div>
                        {% endfor %}
                        {% if not top_by_language.pt %}
                        <div class="empty-state" style="grid-column: 1/-1;"><p>Nenhum trend em portugues coletado</p></div>
                        {% endif %}
                    </div>
                </div>

                <!-- Espanhol -->
                <div class="subnicho-section">
                    <div class="subnicho-header" style="background: linear-gradient(135deg, rgba(198,11,30,0.15) 0%, var(--bg-card) 100%); border-left: 4px solid #c60b1e;">
                        <span class="subnicho-icon">🇪🇸</span>
                        <div class="subnicho-info">
                            <h3>Espanhol (ES)</h3>
                            <p>Tendencias em espanhol - Mercado hispanico</p>
                        </div>
                    </div>
                    <div class="trends-grid">
                        {% for trend in top_by_language.es[:10] %}
                        <div class="trend-card">
                            <div class="trend-header">
                                <span class="trend-rank">#{{ loop.index }}</span>
                                <span class="trend-title">{{ trend.title }}</span>
                            </div>
                            <div class="trend-volume">
                                <span class="volume-bar" style="width: {{ [(trend.volume|default(0)) / 100000, 100] | min }}%"></span>
                                <span class="volume-text">{% if trend.volume|default(0) >= 1000000 %}{{ (trend.volume / 1000000) | round(1) }}M{% elif trend.volume|default(0) >= 1000 %}{{ (trend.volume / 1000) | round(0) | int }}K{% else %}{{ trend.volume|default(0) }}{% endif %}</span>
                            </div>
                            <div class="trend-meta">
                                <span class="trend-meta-item">{{ trend.source }}</span>
                            </div>
                            {% if trend.url %}<a href="{{ trend.url }}" target="_blank" class="trend-link">Ver fonte</a>{% endif %}
                        </div>
                        {% endfor %}
                        {% if not top_by_language.es %}
                        <div class="empty-state" style="grid-column: 1/-1;"><p>Nenhum trend em espanhol coletado</p></div>
                        {% endif %}
                    </div>
                </div>

                <!-- Outros Idiomas -->
                <div class="subnicho-section">
                    <div class="subnicho-header" style="background: linear-gradient(135deg, rgba(100,100,100,0.15) 0%, var(--bg-card) 100%); border-left: 4px solid #666;">
                        <span class="subnicho-icon">🌏</span>
                        <div class="subnicho-info">
                            <h3>Outros Idiomas (FR, KR, JP, IT)</h3>
                            <p>Tendencias em frances, coreano, japones e italiano</p>
                        </div>
                    </div>
                    <div class="trends-grid">
                        {% for trend in top_by_language.other[:10] %}
                        <div class="trend-card">
                            <div class="trend-header">
                                <span class="trend-rank">#{{ loop.index }}</span>
                                <span class="trend-title">{{ trend.title }}</span>
                            </div>
                            <div class="trend-volume">
                                <span class="volume-bar" style="width: {{ [(trend.volume|default(0)) / 100000, 100] | min }}%"></span>
                                <span class="volume-text">{% if trend.volume|default(0) >= 1000000 %}{{ (trend.volume / 1000000) | round(1) }}M{% elif trend.volume|default(0) >= 1000 %}{{ (trend.volume / 1000) | round(0) | int }}K{% else %}{{ trend.volume|default(0) }}{% endif %}</span>
                            </div>
                            <div class="trend-meta">
                                <span class="trend-meta-item">{{ countries[trend.country].flag if trend.country in countries else '' }} {{ trend.language|default('') }}</span>
                                <span class="trend-meta-item">{{ trend.source }}</span>
                            </div>
                            {% if trend.url %}<a href="{{ trend.url }}" target="_blank" class="trend-link">Ver fonte</a>{% endif %}
                        </div>
                        {% endfor %}
                        {% if not top_by_language.other %}
                        <div class="empty-state" style="grid-column: 1/-1;"><p>Nenhum trend em outros idiomas coletado</p></div>
                        {% endif %}
                    </div>
                </div>
            </div>

            <!-- TOP 10 DIRECIONADO POR SUBNICHO -->
            <div class="report-section">
                <h2>🎯 Top 10 por Subnicho (Recomendacoes Direcionadas)</h2>
                <p style="color: var(--text-secondary); margin-bottom: 1.5rem;">Melhores trends para cada um dos seus 7 canais. Ordenados por score de relevancia.</p>

                {% for key, data in trends_by_subnicho.items() %}
                <div class="subnicho-section">
                    <div class="subnicho-header">
                        <span class="subnicho-icon">{{ data.info.icon }}</span>
                        <div class="subnicho-info">
                            <h3>{{ data.info.name }}</h3>
                            <p>{{ data.info.description }}</p>
                        </div>
                        <span class="subnicho-count">{{ data.trends|length }}</span>
                    </div>
                    <div class="top-opportunities">
                        {% for trend in data.trends[:10] %}
                        <div class="opportunity-card">
                            <span class="opportunity-rank">#{{ loop.index }}</span>
                            <div class="opportunity-title">{{ trend.title }}</div>
                            <div class="opportunity-meta">
                                <span>📊 Score: {{ trend.quality_score|default(0) }}%</span> |
                                <span>{% for c in trend.countries_found %}{{ countries[c].flag if c in countries else c }}{% endfor %}</span> |
                                <span>{{ trend.source }}</span>
                            </div>
                            {% if trend.suggested_title %}
                            <div style="margin-top: 0.5rem; padding: 0.5rem; background: rgba(0,212,170,0.1); border-radius: 6px; font-size: 0.8rem;">
                                <strong style="color: var(--accent);">💡 Sugestao de Titulo:</strong><br>
                                {{ trend.suggested_title }}
                            </div>
                            {% endif %}
                            {% if trend.url %}
                            <a href="{{ trend.url }}" target="_blank" class="trend-link" style="margin-top: 0.5rem;">Ver fonte</a>
                            {% endif %}
                        </div>
                        {% endfor %}
                        {% if not data.trends %}
                        <div class="empty-state" style="grid-column: 1/-1;"><p>Nenhum trend encontrado para este subnicho</p></div>
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
            </div>

        </div>

        <!-- Tab: RELATORIO (Insights Resumidos) -->
        <div id="relatorio" class="tab-content">

            <!-- Resumo Executivo -->
            <div class="report-section">
                <h2>📊 Resumo Executivo</h2>
                <div class="summary-stats">
                    <div class="summary-stat">
                        <div class="summary-stat-value">{{ stats.total_processed|default(0) }}</div>
                        <div class="summary-stat-label">Trends Analisados</div>
                    </div>
                    <div class="summary-stat">
                        <div class="summary-stat-value">{{ stats.total_relevant|default(0) }}</div>
                        <div class="summary-stat-label">Relevantes para Voce</div>
                    </div>
                    <div class="summary-stat">
                        <div class="summary-stat-value">{{ stats.cross_platform_count|default(0) }}</div>
                        <div class="summary-stat-label">Cross-Platform</div>
                    </div>
                    <div class="summary-stat">
                        <div class="summary-stat-value">{{ stats.multi_country_count|default(0) }}</div>
                        <div class="summary-stat-label">Multi-Pais</div>
                    </div>
                </div>
                <div class="insight-card insight-highlight">
                    <h3>💡 Insight Principal</h3>
                    <p>Dos {{ stats.total_processed|default(0) }} trends coletados hoje, {{ stats.total_relevant|default(0) }} ({{ ((stats.total_relevant|default(1) / stats.total_processed|default(1)) * 100)|round|int }}%) sao relevantes para seus subnichos.
                    {% if stats.cross_platform_count|default(0) > 5 %}Destaque para {{ stats.cross_platform_count }} trends que aparecem em multiplas plataformas - indicando alta viralidade.{% endif %}
                    {% if stats.multi_country_count|default(0) > 3 %}{{ stats.multi_country_count }} trends tem relevancia internacional - otimo para conteudo em multiplos idiomas.{% endif %}</p>
                </div>
            </div>

            <!-- Top Oportunidades -->
            <div class="report-section">
                <h2>🎯 Top Oportunidades de Conteudo</h2>
                <p style="color: var(--text-secondary); margin-bottom: 1rem;">Trends com maior potencial para producao de video baseado em volume + relevancia + alcance cross-platform.</p>
                <div class="top-opportunities">
                    {% for trend in top_trends[:10] %}
                    <div class="opportunity-card">
                        <span class="opportunity-rank">#{{ loop.index }}</span>
                        <div class="opportunity-title">{{ trend.title }}</div>
                        <div class="opportunity-meta">
                            <span>📊 Score: {{ trend.quality_score|default(0) }}%</span> |
                            <span>📍 {{ trend.country }}</span> |
                            <span>📺 {{ trend.source }}</span>
                            {% if trend.is_cross_platform %} | <span style="color: var(--accent)">🔥 VIRAL</span>{% endif %}
                        </div>
                        {% if trend.url %}
                        <a href="{{ trend.url }}" target="_blank" class="trend-link" style="margin-top: 0.5rem; display: inline-block;">Ver fonte</a>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- Insights por Subnicho -->
            <div class="report-section">
                <h2>🏷️ Insights por Subnicho</h2>
                {% for key, data in trends_by_subnicho.items() %}
                {% if data.trends|length > 0 %}
                <div class="insight-card">
                    <h3>{{ data.info.icon }} {{ data.info.name }} ({{ data.trends|length }} trends)</h3>
                    <p>
                        {% if data.trends|length >= 5 %}
                        <strong style="color: var(--success);">Alta demanda!</strong> Muitos trends encontrados nesta categoria.
                        {% elif data.trends|length >= 2 %}
                        <strong style="color: var(--warning);">Demanda moderada.</strong> Alguns trends relevantes.
                        {% else %}
                        <strong>Nicho especifico.</strong> Poucos trends, mas podem ser valiosos.
                        {% endif %}
                        {% if data.trends[0] %}
                        <br><br>Top trend: "<strong>{{ data.trends[0].title }}</strong>" com score de {{ data.trends[0].quality_score|default(0) }}%.
                        {% endif %}
                    </p>
                </div>
                {% endif %}
                {% endfor %}
            </div>

            <!-- Cross-Platform Highlights -->
            {% if cross_platform_trends|length > 0 %}
            <div class="report-section">
                <h2>🔥 Trends Virais (Cross-Platform)</h2>
                <div class="insight-card insight-warning">
                    <h3>⚠️ Atencao Especial</h3>
                    <p>Estes trends aparecem em multiplas plataformas simultaneamente, indicando alto potencial de viralidade. Considere priorizar a producao de conteudo sobre eles.</p>
                </div>
                <div class="trends-grid" style="margin-top: 1rem;">
                    {% for trend in cross_platform_trends[:6] %}
                    <div class="trend-card">
                        <div class="trend-header">
                            <span class="trend-rank">#{{ loop.index }}</span>
                            <span class="trend-title">{{ trend.title }}</span>
                            <span class="trend-score">{{ trend.quality_score|default(0) }}%</span>
                        </div>
                        <div class="trend-meta">
                            <span class="trend-meta-item">{{ countries[trend.country].flag if trend.country in countries else '🌍' }} {{ trend.country }}</span>
                            <span class="badge-cross">CROSS</span>
                            {% if trend.is_multi_country %}<span class="badge-multi">MULTI</span>{% endif %}
                        </div>
                        {% if trend.analysis %}<div class="trend-analysis">{{ trend.analysis }}</div>{% endif %}
                        {% if trend.url %}<a href="{{ trend.url }}" target="_blank" class="trend-link">Ver fonte</a>{% endif %}
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endif %}

            <!-- Recomendacoes -->
            <div class="report-section">
                <h2>📝 Recomendacoes de Acao</h2>
                <div class="insight-card insight-highlight">
                    <h3>1. Producao Urgente</h3>
                    <p>Foque nos trends cross-platform com score acima de 70%. Estes tem maior probabilidade de continuar em alta nos proximos dias.</p>
                </div>
                <div class="insight-card">
                    <h3>2. Conteudo Evergreen</h3>
                    <p>Trends relacionados a historia, psicologia e misterios tendem a performar bem a longo prazo. Considere criar conteudo mais elaborado para esses temas.</p>
                </div>
                <div class="insight-card">
                    <h3>3. Expansao Internacional</h3>
                    <p>{% if stats.multi_country_count|default(0) > 3 %}Aproveite os {{ stats.multi_country_count }} trends multi-pais para criar versoes em diferentes idiomas e expandir seu alcance.{% else %}Poucos trends internacionais hoje. Foque no mercado principal.{% endif %}</p>
                </div>
            </div>

        </div>

        <!-- Tab: HISTORICO -->
        <div id="historico" class="tab-content">
            <div class="report-section">
                <h2>📅 Historico de Coletas</h2>
                <div class="insight-card">
                    <h3>Dados sendo coletados...</h3>
                    <p>O historico mostrara tendencias recorrentes (3+ dias em alta), trends evergreen (7+ dias)
                    e comparativos de performance apos algumas coletas serem feitas.</p>
                    <p style="margin-top: 1rem; color: var(--text-muted);">
                        Dica: Rode a coleta diariamente para ver padroes emergirem no Supabase.
                    </p>
                </div>

                {% if evergreen_trends %}
                <div style="margin-top: 1.5rem;">
                    <h3 style="color: var(--accent); margin-bottom: 1rem;">🔥 Trends Evergreen (7+ dias)</h3>
                    <div class="trends-grid">
                        {% for trend in evergreen_trends[:10] %}
                        <div class="trend-card">
                            <div class="trend-header">
                                <span class="trend-rank">#{{ loop.index }}</span>
                                <span class="trend-title">{{ trend.title }}</span>
                            </div>
                            <div class="trend-meta">
                                <span class="trend-meta-item">{{ trend.days_active|default(7) }} dias ativo</span>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
                {% endif %}
            </div>
        </div>
    </main>

    <!-- Footer -->
    <footer class="footer">
        <p>{{ title }} - Gerado em {{ generated_at }}</p>
        <p>Content Factory // Pesquisa de Mercado Automatica</p>
    </footer>

    <script>
        // Tab switching
        function showTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            document.querySelectorAll('.nav-tabs a').forEach(link => {
                link.classList.remove('active');
                if (link.getAttribute('href') === '#' + tabId) link.classList.add('active');
            });
            applyFilters();
        }

        // Apply all filters globally
        function applyFilters() {
            const sourceFilter = document.getElementById('filter-source').value;
            const countryFilter = document.getElementById('filter-country').value;
            const languageFilter = document.getElementById('filter-language').value;
            const subnichoFilter = document.getElementById('filter-subnicho').value;

            let visibleCount = 0;
            const sourceCounts = { google_trends: 0, youtube: 0, reddit: 0, hackernews: 0 };

            // Map country to language for filtering
            const countryLangMap = { US: 'en', BR: 'pt', ES: 'es', FR: 'fr', KR: 'ko', JP: 'ja', IT: 'it' };

            // Filter all trend cards
            document.querySelectorAll('.trend-card').forEach(card => {
                const source = card.dataset.source;
                const country = card.dataset.country;
                const subnicho = card.dataset.subnicho || '';
                const cardLang = card.dataset.language || countryLangMap[country] || 'en';

                const matchSource = sourceFilter === 'all' || source === sourceFilter;
                const matchCountry = countryFilter === 'all' || country === countryFilter || country === 'global';
                const matchLanguage = languageFilter === 'all' || cardLang === languageFilter;

                // Na aba GERAL, nao filtra por subnicho
                const activeTab = document.querySelector('.tab-content.active');
                const isGeralTab = activeTab && activeTab.id === 'geral';
                const matchSubnicho = isGeralTab || subnichoFilter === 'all' || subnicho === subnichoFilter;

                if (matchSource && matchCountry && matchLanguage && matchSubnicho) {
                    card.classList.remove('hidden');
                    visibleCount++;
                    if (sourceCounts[source] !== undefined) sourceCounts[source]++;
                } else {
                    card.classList.add('hidden');
                }
            });

            // Filter source sections (hide if empty)
            document.querySelectorAll('.source-section').forEach(section => {
                const source = section.dataset.source;
                const matchSource = sourceFilter === 'all' || source === sourceFilter;
                const hasVisibleCards = section.querySelectorAll('.trend-card:not(.hidden)').length > 0;

                section.style.display = (matchSource && hasVisibleCards) ? 'block' : 'none';
            });

            // Filter subnicho sections (only in DIRECIONADO tab)
            document.querySelectorAll('.subnicho-section').forEach(section => {
                const subnicho = section.dataset.subnicho;
                const matchSubnicho = subnichoFilter === 'all' || subnicho === subnichoFilter;
                const hasVisibleCards = section.querySelectorAll('.trend-card:not(.hidden)').length > 0;

                section.style.display = (matchSubnicho && hasVisibleCards) ? 'block' : 'none';
            });

            // Update counts
            document.getElementById('visible-count').textContent = visibleCount + ' trends';

            Object.keys(sourceCounts).forEach(source => {
                const el = document.querySelector(`[data-count="${source}"]`);
                if (el) el.textContent = sourceCounts[source];
            });
        }

        // Initialize on load
        document.addEventListener('DOMContentLoaded', applyFilters);
    </script>
</body>
</html>'''


# =============================================================================
# TESTE DO MÓDULO
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TESTE - HTML Report Generator")
    print("=" * 60)

    # Dados mock para teste
    mock_data = {
        "all_scored": [
            {
                "title": "Roman Empire Documentary 2024",
                "source": "youtube",
                "country": "US",
                "language": "en",
                "score": 85,
                "best_subnicho": "guerras_civilizacoes",
                "best_subnicho_name": "Guerras e Civilizacoes",
                "best_subnicho_icon": "🏛️",
                "sources_found": ["youtube", "google_trends"],
                "countries_found": ["US", "BR"],
                "is_cross_platform": True,
                "is_multi_country": True
            },
            {
                "title": "Psychology of Manipulation",
                "source": "reddit",
                "country": "US",
                "language": "en",
                "score": 78,
                "best_subnicho": "psicologia_mindset",
                "best_subnicho_name": "Psicologia e Mindset",
                "best_subnicho_icon": "🧠",
                "sources_found": ["reddit"],
                "countries_found": ["US"],
                "is_cross_platform": False,
                "is_multi_country": False
            }
        ],
        "by_country": {
            "US": [
                {
                    "title": "Roman Empire Documentary 2024",
                    "source": "youtube",
                    "score": 85,
                    "best_subnicho_name": "Guerras e Civilizacoes",
                    "best_subnicho_icon": "🏛️",
                    "sources_found": ["youtube", "google_trends"],
                    "is_cross_platform": True,
                    "is_multi_country": True
                }
            ],
            "BR": []
        },
        "by_subnicho": {
            "guerras_civilizacoes": [
                {
                    "title": "Roman Empire Documentary 2024",
                    "source": "youtube",
                    "country": "US",
                    "score": 85,
                    "countries_found": ["US", "BR"],
                    "is_cross_platform": True,
                    "is_multi_country": True
                }
            ],
            "psicologia_mindset": [
                {
                    "title": "Psychology of Manipulation",
                    "source": "reddit",
                    "country": "US",
                    "score": 78,
                    "countries_found": ["US"],
                    "is_cross_platform": False,
                    "is_multi_country": False
                }
            ]
        },
        "stats": {
            "total_processed": 900,
            "total_relevant": 127,
            "cross_platform_count": 23,
            "multi_country_count": 15
        }
    }

    generator = HTMLReportGenerator()
    output = generator.generate(mock_data, output_path="/Users/marcelo/Downloads/trend-monitor/output/test-dashboard.html")
    print(f"\nDashboard de teste gerado: {output}")

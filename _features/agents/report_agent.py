# ========================================
# REPORT AGENT - Gerador de Relatorios HTML
# ========================================
# Funcao: Consolidar insights em relatorios bonitos
# Custo: ZERO (gera HTML estatico)
# ========================================

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import json
import os

from .base import BaseAgent, AgentResult, AgentStatus

logger = logging.getLogger(__name__)


class ReportAgent(BaseAgent):
    """
    Agente responsavel por gerar relatorios HTML.

    Relatorios:
    1. Morning Brief (Diario) - Top 5 virais, oportunidades, acoes
    2. Weekly Review (Semanal) - Tendencias, evolucao, analise completa
    3. Channel Report - Performance individual de cada canal

    Design:
    - Dark mode
    - Responsivo (mobile-first)
    - Zero poluicao visual
    - Cores para indicar prioridade
    """

    def __init__(self, db_client, output_dir: str = None):
        super().__init__(db_client)

        # Diretorio de saida para os relatorios
        self.output_dir = output_dir or os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "reports"
        )

        # Criar diretorio se nao existir
        os.makedirs(self.output_dir, exist_ok=True)

    @property
    def name(self) -> str:
        return "ReportAgent"

    @property
    def description(self) -> str:
        return "Gera relatorios HTML consolidados com insights dos outros agentes"

    async def run(self, agent_results: Dict[str, AgentResult] = None) -> AgentResult:
        """
        Gera relatorios baseados nos resultados dos outros agentes.

        Args:
            agent_results: Dicionario com resultados dos outros agentes
        """
        result = self.create_result()

        try:
            logger.info(f"[{self.name}] Iniciando geracao de relatorios...")

            # Se nao recebeu resultados, usar dados do banco
            if not agent_results:
                agent_results = await self._load_latest_agent_data()

            reports_generated = []

            # 1. Gerar Morning Brief
            morning_brief = self._generate_morning_brief(agent_results)
            morning_path = os.path.join(self.output_dir, "morning_brief.html")
            self._save_html(morning_path, morning_brief)
            reports_generated.append("morning_brief.html")
            logger.info(f"[{self.name}] Morning Brief gerado")

            # 2. Gerar Dashboard Overview
            dashboard = self._generate_dashboard(agent_results)
            dashboard_path = os.path.join(self.output_dir, "dashboard.html")
            self._save_html(dashboard_path, dashboard)
            reports_generated.append("dashboard.html")
            logger.info(f"[{self.name}] Dashboard gerado")

            # 3. Gerar Relatorio de Tendencias
            trends = self._generate_trends_report(agent_results)
            trends_path = os.path.join(self.output_dir, "trends.html")
            self._save_html(trends_path, trends)
            reports_generated.append("trends.html")
            logger.info(f"[{self.name}] Trends Report gerado")

            # 4. Gerar Relatorio de Oportunidades
            opportunities = self._generate_opportunities_report(agent_results)
            opp_path = os.path.join(self.output_dir, "opportunities.html")
            self._save_html(opp_path, opportunities)
            reports_generated.append("opportunities.html")
            logger.info(f"[{self.name}] Opportunities Report gerado")

            # 5. Salvar dados JSON para API
            json_data = self._prepare_json_data(agent_results)
            json_path = os.path.join(self.output_dir, "latest_data.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2, default=str)
            logger.info(f"[{self.name}] JSON data salvo")

            metrics = {
                "reports_generated": len(reports_generated),
                "output_directory": self.output_dir
            }

            return self.complete_result(result, {
                "reports": reports_generated,
                "output_dir": self.output_dir,
                "json_available": True,
                "summary": f"{len(reports_generated)} relatorios HTML gerados"
            }, metrics)

        except Exception as e:
            logger.error(f"[{self.name}] Erro: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return self.fail_result(result, str(e))

    async def _load_latest_agent_data(self) -> Dict:
        """Carrega dados mais recentes do banco (fallback)"""
        # Placeholder - em producao, carregar do banco
        return {}

    def _get_base_style(self) -> str:
        """Retorna CSS base para todos os relatorios"""
        return """
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }

            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #0d1117;
                color: #c9d1d9;
                line-height: 1.6;
                padding: 20px;
            }

            .container {
                max-width: 1200px;
                margin: 0 auto;
            }

            header {
                text-align: center;
                padding: 30px 0;
                border-bottom: 1px solid #30363d;
                margin-bottom: 30px;
            }

            h1 {
                color: #58a6ff;
                font-size: 2rem;
                margin-bottom: 10px;
            }

            .subtitle {
                color: #8b949e;
                font-size: 0.9rem;
            }

            .timestamp {
                color: #6e7681;
                font-size: 0.8rem;
                margin-top: 5px;
            }

            h2 {
                color: #c9d1d9;
                font-size: 1.3rem;
                margin: 25px 0 15px;
                padding-bottom: 10px;
                border-bottom: 1px solid #21262d;
            }

            .card {
                background: #161b22;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 15px;
            }

            .card-title {
                color: #58a6ff;
                font-size: 1.1rem;
                margin-bottom: 10px;
            }

            .metric {
                display: inline-block;
                background: #21262d;
                padding: 8px 15px;
                border-radius: 6px;
                margin: 5px 5px 5px 0;
            }

            .metric-value {
                color: #58a6ff;
                font-size: 1.3rem;
                font-weight: bold;
            }

            .metric-label {
                color: #8b949e;
                font-size: 0.8rem;
            }

            .priority-critical { border-left: 4px solid #f85149; }
            .priority-high { border-left: 4px solid #d29922; }
            .priority-medium { border-left: 4px solid #58a6ff; }
            .priority-low { border-left: 4px solid #3fb950; }

            .badge {
                display: inline-block;
                padding: 3px 10px;
                border-radius: 12px;
                font-size: 0.75rem;
                font-weight: 600;
            }

            .badge-critical { background: #f85149; color: #fff; }
            .badge-high { background: #d29922; color: #000; }
            .badge-medium { background: #58a6ff; color: #000; }
            .badge-low { background: #3fb950; color: #000; }

            .list-item {
                padding: 12px;
                border-bottom: 1px solid #21262d;
            }

            .list-item:last-child { border-bottom: none; }

            .list-title {
                color: #c9d1d9;
                margin-bottom: 5px;
            }

            .list-meta {
                color: #8b949e;
                font-size: 0.85rem;
            }

            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 15px;
            }

            .views { color: #3fb950; }
            .channel { color: #58a6ff; }
            .subnicho { color: #d29922; }

            a {
                color: #58a6ff;
                text-decoration: none;
            }

            a:hover { text-decoration: underline; }

            @media (max-width: 768px) {
                body { padding: 10px; }
                h1 { font-size: 1.5rem; }
                .grid { grid-template-columns: 1fr; }
            }
        </style>
        """

    def _generate_morning_brief(self, agent_results: Dict) -> str:
        """Gera Morning Brief HTML"""
        now = datetime.now(timezone.utc)

        # Extrair dados dos agentes
        trends = agent_results.get("TrendAgent", {}).get("data", {})
        alerts = agent_results.get("AlertAgent", {}).get("data", {})
        advisor = agent_results.get("AdvisorAgent", {}).get("data", {})

        trending_videos = trends.get("trending_videos", [])[:5]
        critical_alerts = alerts.get("by_priority", {}).get("critical", [])
        high_alerts = alerts.get("by_priority", {}).get("high", [])
        top_recommendations = advisor.get("top_recommendations", [])[:5]

        html = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Morning Brief - Content Factory</title>
            {self._get_base_style()}
        </head>
        <body>
            <div class="container">
                <header>
                    <h1>Morning Brief</h1>
                    <p class="subtitle">Resumo diario da operacao</p>
                    <p class="timestamp">Gerado em {now.strftime('%d/%m/%Y as %H:%M')} UTC</p>
                </header>

                <!-- Alertas Criticos -->
                <h2>Alertas Criticos</h2>
                <div class="card priority-critical">
        """

        if critical_alerts:
            for alert in critical_alerts[:3]:
                html += f"""
                    <div class="list-item">
                        <span class="badge badge-critical">CRITICO</span>
                        <div class="list-title">{alert.get('title', 'N/A')}</div>
                        <div class="list-meta">{alert.get('message', '')}</div>
                    </div>
                """
        else:
            html += '<p style="color: #3fb950;">Nenhum alerta critico!</p>'

        html += """
                </div>

                <!-- Top 5 Videos Viralizando -->
                <h2>Top 5 Videos Viralizando</h2>
        """

        for i, video in enumerate(trending_videos, 1):
            html += f"""
                <div class="card">
                    <div class="card-title">#{i} {video.get('titulo', 'N/A')[:60]}...</div>
                    <div class="list-meta">
                        <span class="views">{video.get('views', 0):,} views</span> |
                        <span class="channel">{video.get('nome_canal', 'N/A')}</span> |
                        <span class="subnicho">{video.get('subnicho', 'N/A')}</span>
                    </div>
                    <div class="list-meta" style="margin-top: 5px;">
                        {video.get('views_multiplier', 0)}x a media do canal
                    </div>
                </div>
            """

        html += """
                <!-- Acoes Recomendadas -->
                <h2>Acoes Recomendadas para Hoje</h2>
        """

        for rec in top_recommendations:
            priority = rec.get('priority', 'medium')
            html += f"""
                <div class="card priority-{priority}">
                    <span class="badge badge-{priority}">{priority.upper()}</span>
                    <div class="list-title">{rec.get('action', 'N/A')}</div>
                    <div class="list-meta">{rec.get('reason', '')}</div>
                </div>
            """

        html += """
            </div>
        </body>
        </html>
        """

        return html

    def _generate_dashboard(self, agent_results: Dict) -> str:
        """Gera Dashboard Overview HTML"""
        now = datetime.now(timezone.utc)

        # Extrair metricas
        benchmark = agent_results.get("BenchmarkAgent", {}).get("data", {})
        trends = agent_results.get("TrendAgent", {}).get("data", {})
        alerts = agent_results.get("AlertAgent", {}).get("data", {})

        our_perf = benchmark.get("our_performance", [])
        outperforming = len([c for c in our_perf if c.get("status") == "excellent"])
        underperforming = len([c for c in our_perf if c.get("status") == "needs_attention"])

        html = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Dashboard - Content Factory Intelligence</title>
            {self._get_base_style()}
        </head>
        <body>
            <div class="container">
                <header>
                    <h1>Intelligence Dashboard</h1>
                    <p class="subtitle">Visao geral da operacao</p>
                    <p class="timestamp">{now.strftime('%d/%m/%Y %H:%M')} UTC</p>
                </header>

                <!-- Metricas Principais -->
                <div class="grid">
                    <div class="card">
                        <div class="metric">
                            <div class="metric-value">{len(our_perf)}</div>
                            <div class="metric-label">Nossos Canais</div>
                        </div>
                    </div>
                    <div class="card">
                        <div class="metric">
                            <div class="metric-value" style="color: #3fb950;">{outperforming}</div>
                            <div class="metric-label">Acima do Benchmark</div>
                        </div>
                    </div>
                    <div class="card">
                        <div class="metric">
                            <div class="metric-value" style="color: #f85149;">{underperforming}</div>
                            <div class="metric-label">Precisam Atencao</div>
                        </div>
                    </div>
                    <div class="card">
                        <div class="metric">
                            <div class="metric-value">{len(trends.get('trending_videos', []))}</div>
                            <div class="metric-label">Videos Trending</div>
                        </div>
                    </div>
                </div>

                <!-- Ranking de Canais -->
                <h2>Ranking dos Nossos Canais</h2>
        """

        for canal in our_perf[:10]:
            status_color = {
                "excellent": "#3fb950",
                "good": "#58a6ff",
                "needs_attention": "#f85149"
            }.get(canal.get("status"), "#8b949e")

            html += f"""
                <div class="card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div class="card-title">{canal.get('nome_canal', 'N/A')}</div>
                            <div class="list-meta">{canal.get('subnicho', 'N/A')} | {canal.get('lingua', 'N/A')}</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="color: {status_color}; font-size: 1.5rem; font-weight: bold;">
                                {canal.get('performance_percentage', 0)}%
                            </div>
                            <div class="list-meta">do benchmark</div>
                        </div>
                    </div>
                </div>
            """

        html += """
            </div>
        </body>
        </html>
        """

        return html

    def _generate_trends_report(self, agent_results: Dict) -> str:
        """Gera Relatorio de Tendencias HTML"""
        now = datetime.now(timezone.utc)
        trends = agent_results.get("TrendAgent", {}).get("data", {})

        trending_videos = trends.get("trending_videos", [])[:20]
        trending_topics = trends.get("trending_topics", [])[:15]
        by_subnicho = trends.get("by_subnicho", {})

        html = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Tendencias - Content Factory</title>
            {self._get_base_style()}
        </head>
        <body>
            <div class="container">
                <header>
                    <h1>Tendencias em Tempo Real</h1>
                    <p class="subtitle">O que esta bombando agora</p>
                    <p class="timestamp">{now.strftime('%d/%m/%Y %H:%M')} UTC</p>
                </header>

                <!-- Topicos em Alta -->
                <h2>Topicos em Alta</h2>
                <div class="grid">
        """

        for topic in trending_topics:
            html += f"""
                    <div class="card">
                        <div class="card-title">"{topic.get('keyword', 'N/A')}"</div>
                        <div class="metric">
                            <div class="metric-value">{topic.get('frequency', 0)}</div>
                            <div class="metric-label">ocorrencias</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">{topic.get('avg_views', 0):,}</div>
                            <div class="metric-label">views media</div>
                        </div>
                    </div>
            """

        html += """
                </div>

                <!-- Videos Trending -->
                <h2>Videos Trending</h2>
        """

        for video in trending_videos:
            html += f"""
                <div class="card">
                    <div class="card-title">{video.get('titulo', 'N/A')[:70]}...</div>
                    <div class="list-meta">
                        <span class="views">{video.get('views', 0):,} views</span> |
                        <span class="channel">{video.get('nome_canal', 'N/A')}</span> |
                        <span class="subnicho">{video.get('subnicho', 'N/A')}</span> |
                        Trend Score: {video.get('trend_score', 0)}
                    </div>
                </div>
            """

        html += """
            </div>
        </body>
        </html>
        """

        return html

    def _generate_opportunities_report(self, agent_results: Dict) -> str:
        """Gera Relatorio de Oportunidades HTML"""
        now = datetime.now(timezone.utc)

        correlation = agent_results.get("CorrelationAgent", {}).get("data", {})
        recycler = agent_results.get("RecyclerAgent", {}).get("data", {})

        cross_lang = correlation.get("cross_language_opportunities", [])[:10]
        recycle_plan = recycler.get("recycle_plan", [])[:15]

        html = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Oportunidades - Content Factory</title>
            {self._get_base_style()}
        </head>
        <body>
            <div class="container">
                <header>
                    <h1>Oportunidades Identificadas</h1>
                    <p class="subtitle">Gaps de mercado e conteudo para reciclar</p>
                    <p class="timestamp">{now.strftime('%d/%m/%Y %H:%M')} UTC</p>
                </header>

                <!-- Cross-Language -->
                <h2>Oportunidades Cross-Language</h2>
        """

        for opp in cross_lang:
            html += f"""
                <div class="card priority-high">
                    <div class="card-title">Tema: "{opp.get('theme', 'N/A')}"</div>
                    <div class="list-meta">
                        Bombou em <strong>{opp.get('source_language', 'N/A')}</strong>
                        com {opp.get('avg_views', 0):,} views media
                    </div>
                    <div class="list-meta" style="margin-top: 10px;">
                        <strong>Nao existe em:</strong> {', '.join(opp.get('missing_in_languages', [])[:5])}
                    </div>
                </div>
            """

        html += """
                <!-- Plano de Reciclagem -->
                <h2>Plano de Reciclagem</h2>
        """

        for item in recycle_plan:
            priority = "high" if item.get("priority", 99) <= 2 else "medium"
            html += f"""
                <div class="card priority-{priority}">
                    <span class="badge badge-{priority}">{item.get('type', 'N/A').upper()}</span>
                    <div class="list-title">{item.get('action', 'N/A')}</div>
                    <div class="list-meta">
                        Impacto: {item.get('impact', 'N/A')} | Esforco: {item.get('effort', 'N/A')}
                    </div>
                </div>
            """

        html += """
            </div>
        </body>
        </html>
        """

        return html

    def _prepare_json_data(self, agent_results: Dict) -> Dict:
        """Prepara dados em JSON para a API"""
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "agents": {
                name: {
                    "success": result.success if hasattr(result, 'success') else True,
                    "data": result.get("data", result) if isinstance(result, dict) else result.data if hasattr(result, 'data') else {}
                }
                for name, result in agent_results.items()
            }
        }

    def _save_html(self, path: str, content: str):
        """Salva arquivo HTML"""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

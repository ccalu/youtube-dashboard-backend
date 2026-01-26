# ========================================
# SISTEMA DE AGENTES - CONTENT FACTORY INTELLIGENCE
# ========================================
# Exercito de agentes trabalhando 24/7 para:
# - Descobrir canais novos (Scout)
# - Detectar tendencias (Trend)
# - Analisar padroes (Pattern)
# - Comparar performance (Benchmark)
# - Cruzar dados cross-language (Correlation)
# - Gerar recomendacoes (Advisor)
# - Identificar conteudo para reciclar (Recycler)
# - Alertar sobre oportunidades (Alert)
# - Gerar relatorios HTML (Report)
# ========================================

from .base import BaseAgent, AgentResult
from .scout_agent import ScoutAgent
from .trend_agent import TrendAgent
from .pattern_agent import PatternAgent
from .benchmark_agent import BenchmarkAgent
from .correlation_agent import CorrelationAgent
from .advisor_agent import AdvisorAgent
from .recycler_agent import RecyclerAgent
from .alert_agent import AlertAgent
from .report_agent import ReportAgent
from .orchestrator import AgentOrchestrator

# AI-Powered Agents (GPT-4 Mini)
from .ai_advisor_agent import AIAdvisorAgent
from .ai_title_agent import AITitleAgent

__all__ = [
    'BaseAgent',
    'AgentResult',
    'ScoutAgent',
    'TrendAgent',
    'PatternAgent',
    'BenchmarkAgent',
    'CorrelationAgent',
    'AdvisorAgent',
    'RecyclerAgent',
    'AlertAgent',
    'ReportAgent',
    'AgentOrchestrator',
    # AI Agents
    'AIAdvisorAgent',
    'AITitleAgent'
]

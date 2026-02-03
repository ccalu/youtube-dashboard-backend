# ========================================
# AGENT ORCHESTRATOR - Coordenador de Agentes
# ========================================
# Funcao: Coordenar execucao de todos os agentes
# Custo: ZERO
# ========================================

import logging
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import os

from .base import BaseAgent, AgentResult, AgentStatus
from .scout_agent import ScoutAgent
from .trend_agent import TrendAgent
from .pattern_agent import PatternAgent
from .benchmark_agent import BenchmarkAgent
from .correlation_agent import CorrelationAgent
from .advisor_agent import AdvisorAgent
from .recycler_agent import RecyclerAgent
from .alert_agent import AlertAgent
from .report_agent import ReportAgent

# AI-Powered Agents (GPT-4 Mini)
from .ai_advisor_agent import AIAdvisorAgent
from .ai_title_agent import AITitleAgent

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Coordenador central de todos os agentes.

    Responsabilidades:
    - Inicializar todos os agentes
    - Executar agentes em paralelo ou sequencial
    - Coletar resultados
    - Gerar relatorios consolidados
    """

    def __init__(self, db_client, collector=None, output_dir: str = None):
        """
        Inicializa o orquestrador com todos os agentes.

        Args:
            db_client: Instancia do SupabaseClient
            collector: Instancia do YouTubeCollector (opcional)
            output_dir: Diretorio para salvar relatorios
        """
        self.db = db_client
        self.collector = collector
        self.output_dir = output_dir

        # Inicializar todos os agentes
        self.agents: Dict[str, BaseAgent] = {
            "ScoutAgent": ScoutAgent(db_client, collector),
            "TrendAgent": TrendAgent(db_client),
            "PatternAgent": PatternAgent(db_client),
            "BenchmarkAgent": BenchmarkAgent(db_client),
            "CorrelationAgent": CorrelationAgent(db_client),
            "AdvisorAgent": AdvisorAgent(db_client),
            "RecyclerAgent": RecyclerAgent(db_client),
            "AlertAgent": AlertAgent(db_client),
            "ReportAgent": ReportAgent(db_client, output_dir)
        }

        # Inicializar agentes de IA (GPT-4 Mini) se OPENAI_API_KEY disponivel
        openai_key = os.environ.get("OPENAI_API_KEY")
        if openai_key:
            self.agents["AIAdvisorAgent"] = AIAdvisorAgent(db_client, openai_key)
            self.agents["AITitleAgent"] = AITitleAgent(db_client, openai_key)
            logger.info("AI Agents inicializados (GPT-4 Mini)")
        else:
            logger.warning("OPENAI_API_KEY nao encontrada - AI Agents desabilitados")

        # Resultados da ultima execucao
        self.last_results: Dict[str, AgentResult] = {}
        self.last_run: Optional[datetime] = None

        logger.info(f"Orchestrator initialized with {len(self.agents)} agents")

    async def run_all(self, parallel: bool = True) -> Dict[str, AgentResult]:
        """
        Executa todos os agentes.

        Args:
            parallel: Se True, executa agentes em paralelo (mais rapido)

        Returns:
            Dicionario com resultados de cada agente
        """
        logger.info("=" * 80)
        logger.info("INICIANDO EXECUCAO DE TODOS OS AGENTES")
        logger.info("=" * 80)

        start_time = datetime.now(timezone.utc)
        results = {}

        # Ordem de execucao (alguns agentes dependem de outros)
        # Fase 1: Coleta e analise de dados (podem rodar em paralelo)
        phase1_agents = [
            "TrendAgent",
            "PatternAgent",
            "BenchmarkAgent",
            "CorrelationAgent",
            "RecyclerAgent"
        ]

        # Fase 2: Agentes que dependem dos dados da fase 1
        phase2_agents = [
            "AdvisorAgent",
            "AlertAgent"
        ]

        # Adicionar AI Agents se disponiveis
        if "AIAdvisorAgent" in self.agents:
            phase2_agents.append("AIAdvisorAgent")
        if "AITitleAgent" in self.agents:
            phase2_agents.append("AITitleAgent")

        # Fase 3: Geracao de relatorios (depende de todos)
        phase3_agents = [
            "ReportAgent"
        ]

        # Scout roda separado (usa API externa)
        scout_agent = ["ScoutAgent"]

        try:
            # Fase 1: Analise de dados
            logger.info("-" * 40)
            logger.info("FASE 1: Analise de dados")
            logger.info("-" * 40)

            if parallel:
                phase1_results = await self._run_parallel(phase1_agents)
            else:
                phase1_results = await self._run_sequential(phase1_agents)

            results.update(phase1_results)

            # Fase 2: Recomendacoes e alertas
            logger.info("-" * 40)
            logger.info("FASE 2: Recomendacoes e alertas")
            logger.info("-" * 40)

            if parallel:
                phase2_results = await self._run_parallel(phase2_agents)
            else:
                phase2_results = await self._run_sequential(phase2_agents)

            results.update(phase2_results)

            # Fase 3: Relatorios
            logger.info("-" * 40)
            logger.info("FASE 3: Geracao de relatorios")
            logger.info("-" * 40)

            # Passar resultados para o ReportAgent
            report_agent = self.agents["ReportAgent"]
            report_result = await report_agent.run(results)
            results["ReportAgent"] = report_result

            # Scout (opcional, pode ser executado separadamente)
            # Comentado por padrao para economizar API quota
            # logger.info("-" * 40)
            # logger.info("FASE 4: Scout (descoberta de canais)")
            # logger.info("-" * 40)
            # scout_results = await self._run_sequential(scout_agent)
            # results.update(scout_results)

        except Exception as e:
            logger.error(f"Erro durante execucao dos agentes: {e}")
            import traceback
            logger.error(traceback.format_exc())

        # Calcular duracao total
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()

        # Salvar resultados
        self.last_results = results
        self.last_run = end_time

        # Resumo
        logger.info("=" * 80)
        logger.info("EXECUCAO CONCLUIDA")
        logger.info(f"Duracao total: {duration:.1f}s")
        logger.info(f"Agentes executados: {len(results)}")

        success_count = sum(1 for r in results.values() if r.success)
        logger.info(f"Sucessos: {success_count} / {len(results)}")

        for name, result in results.items():
            status = "OK" if result.success else "ERRO"
            logger.info(f"  - {name}: {status} ({result.duration_seconds:.1f}s)")

        logger.info("=" * 80)

        return results

    async def _run_parallel(self, agent_names: List[str]) -> Dict[str, AgentResult]:
        """Executa agentes em paralelo"""
        tasks = []
        for name in agent_names:
            if name in self.agents:
                tasks.append(self._run_agent_with_name(name))

        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        results = {}
        for name, result in zip(agent_names, results_list):
            if isinstance(result, Exception):
                logger.error(f"Erro no agente {name}: {result}")
                # Criar resultado de erro
                error_result = AgentResult(
                    agent_name=name,
                    status=AgentStatus.FAILED,
                    started_at=datetime.now(timezone.utc),
                    completed_at=datetime.now(timezone.utc),
                    errors=[str(result)]
                )
                results[name] = error_result
            else:
                results[name] = result

        return results

    async def _run_sequential(self, agent_names: List[str]) -> Dict[str, AgentResult]:
        """Executa agentes sequencialmente"""
        results = {}
        for name in agent_names:
            if name in self.agents:
                result = await self._run_agent_with_name(name)
                results[name] = result
        return results

    async def _run_agent_with_name(self, name: str) -> AgentResult:
        """Executa um agente especifico"""
        agent = self.agents[name]
        return await agent.execute()

    async def run_single(self, agent_name: str) -> AgentResult:
        """
        Executa um unico agente.

        Args:
            agent_name: Nome do agente (ex: "TrendAgent")

        Returns:
            AgentResult do agente executado
        """
        if agent_name not in self.agents:
            raise ValueError(f"Agente '{agent_name}' nao encontrado. Disponiveis: {list(self.agents.keys())}")

        agent = self.agents[agent_name]
        result = await agent.execute()

        # Atualizar resultados
        self.last_results[agent_name] = result

        return result

    async def run_analysis_only(self) -> Dict[str, AgentResult]:
        """
        Executa apenas agentes de analise (sem Scout, sem relatorios).
        Util para execucoes rapidas.
        """
        analysis_agents = [
            "TrendAgent",
            "PatternAgent",
            "BenchmarkAgent",
            "AlertAgent"
        ]

        return await self._run_parallel(analysis_agents)

    async def run_scout(self) -> AgentResult:
        """
        Executa apenas o Scout Agent (descoberta de canais).
        Separado porque usa API externa.
        """
        return await self.run_single("ScoutAgent")

    def get_status(self) -> Dict[str, Any]:
        """Retorna status de todos os agentes"""
        return {
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "agents": {
                name: agent.get_status()
                for name, agent in self.agents.items()
            },
            "last_results_summary": {
                name: {
                    "success": result.success,
                    "duration": result.duration_seconds,
                    "errors": result.errors
                }
                for name, result in self.last_results.items()
            } if self.last_results else {}
        }

    def get_latest_data(self) -> Dict[str, Any]:
        """
        Retorna dados mais recentes de todos os agentes.
        Util para a API.
        """
        data = {}

        for name, result in self.last_results.items():
            if result.success:
                data[name] = result.data

        return data

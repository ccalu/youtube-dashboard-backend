# ========================================
# AGENT SCHEDULER - Agendador de Execucoes
# ========================================
# Funcao: Agendar execucao automatica dos agentes
# Custo: ZERO (usa APScheduler local)
# ========================================

import logging
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Callable
import threading

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("APScheduler nao instalado. Scheduler nao disponivel.")

logger = logging.getLogger(__name__)


class AgentScheduler:
    """
    Agendador para execucao automatica dos agentes.

    Schedules padrao:
    - Analise completa: 1x/dia as 6h UTC (antes do time acordar)
    - Scout (descoberta): 1x/dia as 3h UTC
    - Alertas: a cada 6 horas
    - Trends: a cada 4 horas
    """

    def __init__(self, orchestrator):
        """
        Inicializa o scheduler.

        Args:
            orchestrator: Instancia do AgentOrchestrator
        """
        self.orchestrator = orchestrator
        self.scheduler = None
        self.is_running = False
        self.jobs = {}

        if APSCHEDULER_AVAILABLE:
            self.scheduler = AsyncIOScheduler(timezone="UTC")
            logger.info("AgentScheduler initialized")
        else:
            logger.warning("APScheduler nao disponivel - scheduler desabilitado")

    def start(self):
        """Inicia o scheduler com jobs padrao"""
        if not self.scheduler:
            logger.warning("Scheduler nao disponivel")
            return

        if self.is_running:
            logger.warning("Scheduler ja esta rodando")
            return

        # Configurar jobs padrao

        # 1. Analise completa diaria (6h UTC)
        self.scheduler.add_job(
            self._run_full_analysis,
            CronTrigger(hour=6, minute=0),
            id="full_analysis_daily",
            name="Analise Completa Diaria",
            replace_existing=True
        )
        self.jobs["full_analysis_daily"] = "06:00 UTC"

        # 2. Scout diario (3h UTC) - desabilitado por padrao
        # self.scheduler.add_job(
        #     self._run_scout,
        #     CronTrigger(hour=3, minute=0),
        #     id="scout_daily",
        #     name="Scout Diario",
        #     replace_existing=True
        # )

        # 3. Alertas a cada 6 horas
        self.scheduler.add_job(
            self._run_alerts,
            IntervalTrigger(hours=6),
            id="alerts_periodic",
            name="Alertas Periodicos",
            replace_existing=True
        )
        self.jobs["alerts_periodic"] = "A cada 6 horas"

        # 4. Trends a cada 4 horas
        self.scheduler.add_job(
            self._run_trends,
            IntervalTrigger(hours=4),
            id="trends_periodic",
            name="Trends Periodicos",
            replace_existing=True
        )
        self.jobs["trends_periodic"] = "A cada 4 horas"

        # Iniciar scheduler
        self.scheduler.start()
        self.is_running = True

        logger.info("=" * 60)
        logger.info("AGENT SCHEDULER INICIADO")
        logger.info("Jobs configurados:")
        for job_id, schedule in self.jobs.items():
            logger.info(f"  - {job_id}: {schedule}")
        logger.info("=" * 60)

    def stop(self):
        """Para o scheduler"""
        if self.scheduler and self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Agent Scheduler parado")

    async def _run_full_analysis(self):
        """Executa analise completa"""
        logger.info("[Scheduler] Iniciando analise completa...")
        try:
            await self.orchestrator.run_all(parallel=True)
            logger.info("[Scheduler] Analise completa finalizada")
        except Exception as e:
            logger.error(f"[Scheduler] Erro na analise completa: {e}")

    async def _run_scout(self):
        """Executa Scout Agent"""
        logger.info("[Scheduler] Iniciando Scout...")
        try:
            await self.orchestrator.run_single("ScoutAgent")
            logger.info("[Scheduler] Scout finalizado")
        except Exception as e:
            logger.error(f"[Scheduler] Erro no Scout: {e}")

    async def _run_alerts(self):
        """Executa apenas o Alert Agent"""
        logger.info("[Scheduler] Gerando alertas...")
        try:
            await self.orchestrator.run_single("AlertAgent")
            logger.info("[Scheduler] Alertas gerados")
        except Exception as e:
            logger.error(f"[Scheduler] Erro nos alertas: {e}")

    async def _run_trends(self):
        """Executa apenas o Trend Agent"""
        logger.info("[Scheduler] Analisando tendencias...")
        try:
            await self.orchestrator.run_single("TrendAgent")
            logger.info("[Scheduler] Tendencias analisadas")
        except Exception as e:
            logger.error(f"[Scheduler] Erro nas tendencias: {e}")

    def add_job(
        self,
        func: Callable,
        trigger: str,
        job_id: str,
        **trigger_args
    ):
        """
        Adiciona um job customizado.

        Args:
            func: Funcao a ser executada
            trigger: "cron" ou "interval"
            job_id: ID unico do job
            **trigger_args: Argumentos do trigger (hour, minute, hours, etc)
        """
        if not self.scheduler:
            logger.warning("Scheduler nao disponivel")
            return

        if trigger == "cron":
            trigger_obj = CronTrigger(**trigger_args)
        elif trigger == "interval":
            trigger_obj = IntervalTrigger(**trigger_args)
        else:
            raise ValueError(f"Trigger invalido: {trigger}")

        self.scheduler.add_job(
            func,
            trigger_obj,
            id=job_id,
            replace_existing=True
        )

        self.jobs[job_id] = str(trigger_args)
        logger.info(f"Job adicionado: {job_id} ({trigger_args})")

    def remove_job(self, job_id: str):
        """Remove um job"""
        if self.scheduler:
            try:
                self.scheduler.remove_job(job_id)
                del self.jobs[job_id]
                logger.info(f"Job removido: {job_id}")
            except:
                pass

    def get_status(self) -> Dict[str, Any]:
        """Retorna status do scheduler"""
        return {
            "is_running": self.is_running,
            "jobs": self.jobs,
            "next_runs": self._get_next_runs() if self.is_running else {}
        }

    def _get_next_runs(self) -> Dict[str, str]:
        """Retorna proximas execucoes de cada job"""
        if not self.scheduler:
            return {}

        next_runs = {}
        for job in self.scheduler.get_jobs():
            next_run = job.next_run_time
            if next_run:
                next_runs[job.id] = next_run.isoformat()

        return next_runs

    async def run_now(self, agent_name: str = None):
        """
        Executa agentes imediatamente (manual trigger).

        Args:
            agent_name: Nome do agente especifico ou None para todos
        """
        if agent_name:
            logger.info(f"[Manual] Executando {agent_name}...")
            return await self.orchestrator.run_single(agent_name)
        else:
            logger.info("[Manual] Executando todos os agentes...")
            return await self.orchestrator.run_all(parallel=True)

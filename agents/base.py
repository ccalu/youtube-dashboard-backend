# ========================================
# BASE AGENT - Classe base para todos os agentes
# ========================================
# Custo: ZERO (usa apenas Supabase + Python)
# ========================================

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Status de execucao do agente"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentResult:
    """Resultado padronizado da execucao de um agente"""
    agent_name: str
    status: AgentStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> float:
        """Duracao da execucao em segundos"""
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0.0

    @property
    def success(self) -> bool:
        """Retorna True se executou com sucesso"""
        return self.status == AgentStatus.COMPLETED and len(self.errors) == 0

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionario (para JSON)"""
        return {
            "agent_name": self.agent_name,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "success": self.success,
            "data": self.data,
            "errors": self.errors,
            "metrics": self.metrics
        }


class BaseAgent(ABC):
    """
    Classe base para todos os agentes do sistema.

    Todos os agentes devem herdar desta classe e implementar:
    - name: Nome do agente
    - description: Descricao do que faz
    - run(): Metodo principal de execucao
    """

    def __init__(self, db_client):
        """
        Inicializa o agente com cliente de banco de dados.

        Args:
            db_client: Instancia do SupabaseClient
        """
        self.db = db_client
        self.status = AgentStatus.IDLE
        self.last_run: Optional[datetime] = None
        self.last_result: Optional[AgentResult] = None

    @property
    @abstractmethod
    def name(self) -> str:
        """Nome unico do agente"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Descricao do que o agente faz"""
        pass

    @abstractmethod
    async def run(self) -> AgentResult:
        """
        Executa a tarefa principal do agente.

        Returns:
            AgentResult com os dados coletados/processados
        """
        pass

    def create_result(self) -> AgentResult:
        """Cria um novo AgentResult para esta execucao"""
        return AgentResult(
            agent_name=self.name,
            status=AgentStatus.RUNNING,
            started_at=datetime.now(timezone.utc)
        )

    def complete_result(self, result: AgentResult, data: Dict[str, Any] = None,
                       metrics: Dict[str, Any] = None) -> AgentResult:
        """Marca resultado como completo"""
        result.status = AgentStatus.COMPLETED
        result.completed_at = datetime.now(timezone.utc)
        if data:
            result.data = data
        if metrics:
            result.metrics = metrics
        return result

    def fail_result(self, result: AgentResult, error: str) -> AgentResult:
        """Marca resultado como falha"""
        result.status = AgentStatus.FAILED
        result.completed_at = datetime.now(timezone.utc)
        result.errors.append(error)
        return result

    async def execute(self) -> AgentResult:
        """
        Wrapper para executar o agente com tratamento de erros.
        Use este metodo ao inves de chamar run() diretamente.
        """
        self.status = AgentStatus.RUNNING
        logger.info(f"{'='*60}")
        logger.info(f"[{self.name}] INICIANDO execucao...")
        logger.info(f"{'='*60}")

        try:
            result = await self.run()
            self.status = result.status
            self.last_run = datetime.now(timezone.utc)
            self.last_result = result

            if result.success:
                logger.info(f"[{self.name}] CONCLUIDO com sucesso em {result.duration_seconds:.1f}s")
            else:
                logger.warning(f"[{self.name}] CONCLUIDO com erros: {result.errors}")

            return result

        except Exception as e:
            logger.error(f"[{self.name}] ERRO FATAL: {e}")
            import traceback
            logger.error(traceback.format_exc())

            result = self.create_result()
            result = self.fail_result(result, str(e))
            self.status = AgentStatus.FAILED
            self.last_run = datetime.now(timezone.utc)
            self.last_result = result

            return result

    def get_status(self) -> Dict[str, Any]:
        """Retorna status atual do agente"""
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "last_success": self.last_result.success if self.last_result else None
        }

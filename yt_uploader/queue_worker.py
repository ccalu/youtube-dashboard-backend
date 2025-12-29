"""
Upload Queue Worker - Processador automático de fila de uploads

Sistema isolado que processa vídeos pendentes na yt_upload_queue.
Totalmente desacoplado do main.py para garantir estabilidade.

Features:
- Circuit breaker (auto-desliga após erros consecutivos)
- Resource monitoring (memória + disco)
- Startup protection (delay configurável)
- Proper task management (sem acumulação)
- Toggle via environment variable
- Logs detalhados
"""

import asyncio
import logging
import os
import sys
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class UploadQueueWorker:
    """
    Worker isolado para processar fila de uploads automaticamente.

    Responsabilidades:
    - Buscar vídeos com status='pending' periodicamente
    - Disparar uploads respeitando limites de concorrência
    - Monitorar recursos (memória, disco)
    - Auto-desligar em caso de erros consecutivos
    """

    def __init__(self):
        """Inicializa worker com configurações de ENV"""

        # Configurações
        self.interval_seconds = int(os.getenv("UPLOAD_WORKER_INTERVAL_SECONDS", "120"))
        self.batch_size = int(os.getenv("UPLOAD_WORKER_BATCH_SIZE", "5"))  # Reduzido para segurança
        self.max_consecutive_errors = int(os.getenv("UPLOAD_WORKER_MAX_ERRORS", "5"))
        self.min_free_memory_mb = int(os.getenv("UPLOAD_WORKER_MIN_FREE_MEMORY_MB", "200"))
        self.min_free_disk_mb = int(os.getenv("UPLOAD_WORKER_MIN_FREE_DISK_MB", "500"))

        # Estado interno
        self.consecutive_errors = 0
        self.is_active = True
        self.total_processed = 0
        self.total_succeeded = 0
        self.total_failed = 0

        # Lazy initialization (evita imports circulares)
        self._db_client = None
        self._process_upload_func = None

    def _lazy_init_dependencies(self):
        """
        Inicializa dependências de forma lazy.
        Evita imports circulares e problemas de timing.
        """
        if self._db_client is None:
            try:
                # Importa DENTRO da função (não no topo do arquivo)
                from yt_uploader.database import get_pending_uploads
                self._get_pending_uploads = get_pending_uploads

                # Import da função de processamento
                # IMPORTANTE: Vamos importar do main.py que já tem tudo configurado
                import sys
                if 'main' in sys.modules:
                    main_module = sys.modules['main']
                    self._process_upload_func = main_module.process_upload_task
                else:
                    logger.error("❌ Módulo 'main' não encontrado - worker não pode processar uploads")
                    self.is_active = False
                    return False

                logger.info("✅ Worker dependencies initialized")
                return True

            except Exception as e:
                logger.error(f"❌ Erro ao inicializar dependências: {e}", exc_info=True)
                self.is_active = False
                return False

        return True

    def check_resources(self) -> tuple[bool, str]:
        """
        Verifica se há recursos suficientes para processar uploads.

        Returns:
            (ok: bool, message: str)
        """
        try:
            # Verifica memória disponível
            try:
                import psutil
                memory = psutil.virtual_memory()
                available_mb = memory.available / (1024 * 1024)

                if available_mb < self.min_free_memory_mb:
                    return False, f"Memória insuficiente: {available_mb:.0f}MB disponível (mín: {self.min_free_memory_mb}MB)"
            except ImportError:
                # psutil não disponível - skip check
                logger.warning("⚠️ psutil não instalado - check de memória desabilitado")

            # Verifica espaço em disco (/tmp para vídeos)
            try:
                import shutil
                stat = shutil.disk_usage('/tmp')
                available_mb = stat.free / (1024 * 1024)

                if available_mb < self.min_free_disk_mb:
                    return False, f"Disco insuficiente: {available_mb:.0f}MB disponível (mín: {self.min_free_disk_mb}MB)"
            except Exception as e:
                logger.warning(f"⚠️ Não foi possível verificar disco: {e}")

            return True, "OK"

        except Exception as e:
            logger.error(f"❌ Erro ao verificar recursos: {e}")
            return True, "Resource check failed - continuing anyway"

    async def _process_batch(self):
        """
        Processa um batch de uploads pendentes.

        Diferente do worker anterior que criava tasks sem aguardar,
        este aguarda a conclusão de todos antes de continuar.
        """
        # Verifica recursos antes de processar
        resources_ok, resources_msg = self.check_resources()
        if not resources_ok:
            logger.warning(f"⚠️ {resources_msg} - Aguardando próximo ciclo")
            return

        # Busca vídeos pendentes
        try:
            pending_uploads = self._get_pending_uploads(limit=self.batch_size)
        except Exception as e:
            logger.error(f"❌ Erro ao buscar uploads pendentes: {e}")
            raise

        if not pending_uploads:
            # Nenhum vídeo pendente - OK, não é erro
            return

        logger.info(f"📤 Encontrados {len(pending_uploads)} vídeos pendentes")

        # Processa uploads de forma segura
        # IMPORTANTE: Usamos gather com return_exceptions=True para não crashar se um falhar
        tasks = []
        for upload in pending_uploads:
            upload_id = upload['id']
            titulo_preview = upload.get('titulo', 'Sem título')[:50]
            logger.info(f"   🎬 Disparando upload_id={upload_id}: {titulo_preview}...")

            # Cria task
            task = asyncio.create_task(self._process_upload_func(upload_id))
            tasks.append(task)

        # AGUARDA TODOS (diferente do worker anterior)
        # return_exceptions=True evita que um erro cancele os outros
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Conta sucessos/falhas
        succeeded = sum(1 for r in results if not isinstance(r, Exception))
        failed = len(results) - succeeded

        self.total_processed += len(results)
        self.total_succeeded += succeeded
        self.total_failed += failed

        logger.info(f"📊 Batch concluído: {succeeded} sucesso, {failed} falhas")

    async def run(self):
        """
        Loop principal do worker.
        Roda indefinidamente até ser desativado.
        """
        logger.info("=" * 80)
        logger.info("📤 UPLOAD QUEUE WORKER INICIADO")
        logger.info(f"⏰ Intervalo: {self.interval_seconds}s")
        logger.info(f"📦 Batch size: {self.batch_size} uploads/vez")
        logger.info(f"🔒 Max erros consecutivos: {self.max_consecutive_errors}")
        logger.info("=" * 80)

        # Lazy initialization
        if not self._lazy_init_dependencies():
            logger.error("❌ Worker não pôde inicializar - ABORTANDO")
            return

        while self.is_active:
            try:
                # Processa batch
                await self._process_batch()

                # Reset erro counter em caso de sucesso
                self.consecutive_errors = 0

            except Exception as e:
                self.consecutive_errors += 1
                logger.error(
                    f"❌ Erro no worker (tentativa {self.consecutive_errors}/{self.max_consecutive_errors}): {e}",
                    exc_info=True
                )

                # Circuit breaker
                if self.consecutive_errors >= self.max_consecutive_errors:
                    self.is_active = False
                    logger.critical("=" * 80)
                    logger.critical(f"🚨 WORKER DESATIVADO após {self.max_consecutive_errors} erros consecutivos")
                    logger.critical(f"📊 Estatísticas finais:")
                    logger.critical(f"   Total processado: {self.total_processed}")
                    logger.critical(f"   Sucessos: {self.total_succeeded}")
                    logger.critical(f"   Falhas: {self.total_failed}")
                    logger.critical("=" * 80)
                    return

            # Aguarda próximo ciclo
            if self.is_active:
                await asyncio.sleep(self.interval_seconds)

        logger.info("📤 Worker encerrado gracefully")


async def start_queue_worker():
    """
    Entry point do worker com startup protection.

    Função assíncrona que pode ser chamada via asyncio.create_task()
    no startup do main.py sem bloquear outros schedulers.
    """
    # Verifica se está habilitado
    enabled = os.getenv("UPLOAD_WORKER_ENABLED", "true").lower() == "true"
    if not enabled:
        logger.info("📤 Upload queue worker DESABILITADO (UPLOAD_WORKER_ENABLED=false)")
        return

    # Startup protection (como outros schedulers)
    startup_delay = int(os.getenv("UPLOAD_WORKER_STARTUP_DELAY", "180"))  # 3 min padrão
    logger.info(f"📤 Upload worker aguardando {startup_delay}s (startup protection)...")
    await asyncio.sleep(startup_delay)

    # Inicializa e roda worker
    try:
        worker = UploadQueueWorker()
        await worker.run()
    except Exception as e:
        logger.error(f"❌ Upload worker crashou: {e}", exc_info=True)
        # Não propaga exceção - worker isolado não deve afetar main app

"""
Claude Worker Local — processa jobs de agentes via Claude CLI.

Roda na maquina do Marcelo (sempre ligada).
Poll Supabase a cada 5s, processa jobs pending via Claude Opus 4.6.

Uso:
    python claude_worker.py
"""

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [WORKER] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Supabase config
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    # Tentar carregar do .env
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"'))
        SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
        SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

import requests
from claude_llm_client import is_claude_cli_available

POLL_INTERVAL = 5  # segundos
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}


def fetch_pending_job():
    """Busca proximo job pending (FIFO)."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/agent_jobs",
        params={
            "status": "eq.pending",
            "order": "created_at.asc",
            "limit": "1",
        },
        headers=HEADERS,
    )
    if resp.status_code == 200 and resp.json():
        return resp.json()[0]
    return None


def update_job(job_id: int, **fields):
    """Atualiza campos do job."""
    requests.patch(
        f"{SUPABASE_URL}/rest/v1/agent_jobs",
        params={"id": f"eq.{job_id}"},
        json=fields,
        headers={**HEADERS, "Prefer": "return=minimal"},
    )


def process_temas_job(job):
    """Processa job de temas via Claude CLI."""
    from theme_agent import run_analysis as theme_run_analysis

    channel_id = job["channel_id"]
    logger.info(f"Processando TEMAS para {channel_id}")

    result = theme_run_analysis(channel_id)
    return result


def process_motores_job(job):
    """Processa job de motores via Claude CLI."""
    from motor_agent import run_analysis as motor_run_analysis

    channel_id = job["channel_id"]
    logger.info(f"Processando MOTORES para {channel_id}")

    result = motor_run_analysis(channel_id)
    return result


def process_ordenador_job(job):
    """Processa job de ordenacao de producao via Claude CLI."""
    from production_order_agent import run_analysis as order_run_analysis

    channel_id = job["channel_id"]
    logger.info(f"Processando ORDENADOR para {channel_id}")

    result = order_run_analysis(channel_id)
    return result


def process_job(job):
    """Processa um job pendente."""
    job_id = job["id"]
    agent_type = job["agent_type"]
    channel_id = job["channel_id"]

    logger.info(f"=== Job #{job_id}: {agent_type} para {channel_id} ===")

    # Marcar como processing
    update_job(job_id,
               status="processing",
               started_at=datetime.now(timezone.utc).isoformat())

    try:
        if agent_type == "temas":
            result = process_temas_job(job)
        elif agent_type == "motores":
            result = process_motores_job(job)
        elif agent_type == "ordenador":
            result = process_ordenador_job(job)
        else:
            raise ValueError(f"Tipo de agente desconhecido: {agent_type}")

        success = result.get("success", False) if isinstance(result, dict) else False

        if success:
            update_job(job_id,
                       status="completed",
                       completed_at=datetime.now(timezone.utc).isoformat(),
                       result_data=json.dumps(result))
            logger.info(f"Job #{job_id} CONCLUIDO com sucesso")
        else:
            error_msg = result.get("error", "Erro desconhecido") if isinstance(result, dict) else str(result)
            update_job(job_id,
                       status="failed",
                       completed_at=datetime.now(timezone.utc).isoformat(),
                       error_message=error_msg)
            logger.error(f"Job #{job_id} FALHOU: {error_msg}")

    except Exception as e:
        logger.error(f"Job #{job_id} EXCECAO: {e}")
        update_job(job_id,
                   status="failed",
                   completed_at=datetime.now(timezone.utc).isoformat(),
                   error_message=str(e))


def main():
    """Loop principal do worker."""
    logger.info("=" * 60)
    logger.info("CLAUDE WORKER INICIADO")
    logger.info(f"Supabase: {SUPABASE_URL[:50]}...")
    logger.info(f"Claude CLI: {'DISPONIVEL' if is_claude_cli_available() else 'NAO ENCONTRADO'}")
    logger.info(f"Modelo: {os.environ.get('CLAUDE_MODEL', 'claude-opus-4-6')}")
    logger.info(f"Poll interval: {POLL_INTERVAL}s")
    logger.info("=" * 60)

    if not is_claude_cli_available():
        logger.error("Claude CLI NAO encontrado no PATH! Worker nao pode processar jobs.")
        logger.error("Instale: npm i -g @anthropic-ai/claude-code")
        sys.exit(1)

    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("SUPABASE_URL e SUPABASE_KEY nao configurados!")
        sys.exit(1)

    while True:
        try:
            job = fetch_pending_job()
            if job:
                process_job(job)
            else:
                time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            logger.info("Worker interrompido pelo usuario (Ctrl+C)")
            break
        except Exception as e:
            logger.error(f"Erro no loop principal: {e}")
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()

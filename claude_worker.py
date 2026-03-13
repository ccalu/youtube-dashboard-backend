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

# Setup logging — level WARNING para nao poluir com logs internos dos agentes
# Output visual e feito via print() direto
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("worker")
logger.setLevel(logging.INFO)

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

# Estado visual — evitar spam de "aguardando"
_last_idle_msg = None
_last_wait_msg = {}


def _now():
    return datetime.now().strftime("%H:%M:%S")


def _fmt_duration(seconds):
    if seconds < 60:
        return f"{seconds:.0f}s"
    m, s = divmod(int(seconds), 60)
    return f"{m}m{s:02d}s"


def _resolve_channel_name(channel_id: str) -> str:
    """Busca nome do canal para exibicao."""
    try:
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/yt_channels",
            params={"channel_id": f"eq.{channel_id}", "select": "channel_name", "limit": "1"},
            headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"},
            timeout=5,
        )
        if resp.status_code == 200 and resp.json():
            return resp.json()[0].get("channel_name", channel_id)
    except Exception:
        pass
    return channel_id


def fetch_pending_jobs_count() -> int:
    """Conta jobs pending."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/agent_jobs",
        params={"status": "eq.pending", "select": "id"},
        headers=HEADERS,
    )
    return len(resp.json()) if resp.status_code == 200 else 0


def fetch_pending_job():
    """Busca proximo job pending, respeitando dependencias (temas -> motores -> ordenador)."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/agent_jobs",
        params={
            "status": "eq.pending",
            "order": "created_at.asc",
            "limit": "10",
        },
        headers=HEADERS,
    )
    if resp.status_code != 200 or not resp.json():
        return None

    # Priorizar por dependencia: temas primeiro, depois motores, depois ordenador
    priority = {"temas": 0, "motores": 1, "ordenador": 2}
    jobs = sorted(resp.json(), key=lambda j: priority.get(j.get("agent_type", ""), 99))
    return jobs[0] if jobs else None


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
    result = theme_run_analysis(channel_id)
    return result


def process_motores_job(job):
    """Processa job de motores via Claude CLI."""
    from motor_agent import run_analysis as motor_run_analysis

    channel_id = job["channel_id"]
    result = motor_run_analysis(channel_id)
    return result


def process_ordenador_job(job):
    """Processa job de ordenacao de producao via Claude CLI."""
    from production_order_agent import run_analysis as order_run_analysis

    channel_id = job["channel_id"]
    result = order_run_analysis(channel_id)
    return result


def _has_pending_dependency(channel_id: str, agent_type: str) -> bool:
    """Verifica se existe job pendente/processing de um agente que precisa rodar antes."""
    deps = {"motores": "temas", "ordenador": "motores"}
    required = deps.get(agent_type)
    if not required:
        return False

    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/agent_jobs",
        params={
            "channel_id": f"eq.{channel_id}",
            "agent_type": f"eq.{required}",
            "status": "in.(pending,processing)",
            "limit": "1",
        },
        headers=HEADERS,
    )
    return resp.status_code == 200 and len(resp.json()) > 0


def process_job(job):
    """Processa um job pendente."""
    global _last_idle_msg, _last_wait_msg

    job_id = job["id"]
    agent_type = job["agent_type"]
    channel_id = job["channel_id"]
    channel_name = _resolve_channel_name(channel_id)
    agent_label = agent_type.upper()

    # Verificar dependencias — se o agente anterior ainda nao rodou, pular por agora
    if _has_pending_dependency(channel_id, agent_type):
        dep_name = {"motores": "temas", "ordenador": "motores"}[agent_type]
        wait_key = f"{job_id}:{agent_type}"
        if _last_wait_msg.get(wait_key) != True:
            print(f"[{_now()}]   Aguardando {dep_name.upper()} finalizar para {channel_name}...")
            _last_wait_msg[wait_key] = True
        return

    # Limpar estado de espera
    _last_idle_msg = None
    _last_wait_msg = {}

    # Header do job
    print(f"[{_now()}] +-- Job #{job_id}: {agent_label} -- {channel_name}")
    print(f"[{_now()}] |   Canal: {channel_id}")

    # Marcar como processing
    update_job(job_id,
               status="processing",
               started_at=datetime.now(timezone.utc).isoformat())

    start_time = time.time()

    try:
        if agent_type == "temas":
            result = process_temas_job(job)
        elif agent_type == "motores":
            result = process_motores_job(job)
        elif agent_type == "ordenador":
            result = process_ordenador_job(job)
        else:
            raise ValueError(f"Tipo de agente desconhecido: {agent_type}")

        elapsed = time.time() - start_time
        success = result.get("success", False) if isinstance(result, dict) else False

        if success:
            update_job(job_id,
                       status="completed",
                       completed_at=datetime.now(timezone.utc).isoformat(),
                       result_data=json.dumps(result))
            print(f"[{_now()}] |   Duracao: {_fmt_duration(elapsed)}")
            print(f"[{_now()}] +-- OK CONCLUIDO")
            print()
        else:
            error_msg = result.get("error", "Erro desconhecido") if isinstance(result, dict) else str(result)
            update_job(job_id,
                       status="failed",
                       completed_at=datetime.now(timezone.utc).isoformat(),
                       error_message=error_msg)
            print(f"[{_now()}] |   Duracao: {_fmt_duration(elapsed)}")
            print(f"[{_now()}] |   Erro: {error_msg[:120]}")
            print(f"[{_now()}] +-- xx FALHOU")
            print()
            logger.error(f"Job #{job_id} ({agent_label}) falhou: {error_msg}")

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Job #{job_id} ({agent_label}) excecao: {e}")
        update_job(job_id,
                   status="failed",
                   completed_at=datetime.now(timezone.utc).isoformat(),
                   error_message=str(e))
        print(f"[{_now()}] |   Duracao: {_fmt_duration(elapsed)}")
        print(f"[{_now()}] |   Erro: {str(e)[:120]}")
        print(f"[{_now()}] +-- xx FALHOU (excecao)")
        print()


def main():
    """Loop principal do worker."""
    global _last_idle_msg

    cli_ok = is_claude_cli_available()
    model = os.environ.get("CLAUDE_MODEL", "claude-opus-4-6")

    print()
    print("=" * 55)
    print("  CLAUDE WORKER v1.1")
    print(f"  Supabase: {'OK' if SUPABASE_URL else 'NAO CONFIGURADO'}")
    print(f"  Claude CLI: {'OK' if cli_ok else 'NAO ENCONTRADO'} ({model})")
    print(f"  Poll: {POLL_INTERVAL}s")
    print("=" * 55)
    print()

    if not cli_ok:
        print("[ERRO] Claude CLI NAO encontrado no PATH!")
        print("       Instale: npm i -g @anthropic-ai/claude-code")
        sys.exit(1)

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("[ERRO] SUPABASE_URL e SUPABASE_KEY nao configurados!")
        sys.exit(1)

    while True:
        try:
            job = fetch_pending_job()
            if job:
                _last_idle_msg = None
                process_job(job)
            else:
                # Mostrar "Aguardando" apenas 1x, nao a cada poll
                if _last_idle_msg is None:
                    print(f"[{_now()}] Aguardando jobs...")
                    _last_idle_msg = True
                time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            print(f"\n[{_now()}] Worker encerrado (Ctrl+C)")
            break
        except Exception as e:
            logger.error(f"Erro no loop principal: {e}")
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()

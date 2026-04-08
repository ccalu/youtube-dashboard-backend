"""
Fila de producao de Shorts — executa 1 por vez no Freepik.

In-memory queue + worker thread unico.
Quando o servidor reinicia, a fila zera (aceitavel pra uso local).
"""

import threading
import logging
from collections import deque
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

_queue: deque[dict] = deque()
_current: Optional[dict] = None
_lock = threading.Lock()
_worker_thread: Optional[threading.Thread] = None
_worker_running = False


def enqueue(producao_id: int, json_path: str, production_path: str, subnicho: str) -> dict:
    """Adiciona producao na fila. Inicia worker se nao estiver rodando."""
    global _worker_thread, _worker_running

    item = {
        "producao_id": producao_id,
        "json_path": json_path,
        "production_path": production_path,
        "subnicho": subnicho,
        "added_at": datetime.now().strftime("%H:%M:%S"),
    }

    with _lock:
        # Evitar duplicatas
        for q in _queue:
            if q["producao_id"] == producao_id:
                return {"posicao": get_position(producao_id), "duplicado": True}
        if _current and _current["producao_id"] == producao_id:
            return {"posicao": 0, "duplicado": True}

        _queue.append(item)
        posicao = len(_queue)

    # Setar status como queued
    from shorts_endpoints import _production_status, _add_log
    _production_status[producao_id] = "queued"
    _add_log(producao_id, f"Na fila (posicao {posicao})")

    # Iniciar worker se nao estiver rodando
    with _lock:
        if not _worker_running:
            _worker_running = True
            _worker_thread = threading.Thread(target=_worker_loop, daemon=True)
            _worker_thread.start()

    logger.info(f"[queue] Enfileirado: {producao_id} (posicao {posicao})")
    return {"posicao": posicao, "duplicado": False}


def get_queue_status() -> dict:
    """Retorna estado da fila."""
    with _lock:
        current_id = _current["producao_id"] if _current else None
        queue_items = [{"producao_id": q["producao_id"], "posicao": i + 1} for i, q in enumerate(_queue)]
    return {
        "current": current_id,
        "queue": queue_items,
        "total": len(queue_items) + (1 if current_id else 0),
    }


def get_position(producao_id: int) -> int | None:
    """Retorna posicao (0 = executando, 1+ = na fila, None = nao esta)."""
    with _lock:
        if _current and _current["producao_id"] == producao_id:
            return 0
        for i, q in enumerate(_queue):
            if q["producao_id"] == producao_id:
                return i + 1
    return None


def remove_from_queue(producao_id: int) -> bool:
    """Remove da fila se ainda nao comecou."""
    with _lock:
        for q in list(_queue):
            if q["producao_id"] == producao_id:
                _queue.remove(q)
                from shorts_endpoints import _production_status, _add_log
                _production_status[producao_id] = "idle"
                _add_log(producao_id, "Removido da fila")
                logger.info(f"[queue] Removido: {producao_id}")
                return True
    return False


def _worker_loop():
    """Worker que processa a fila, 1 item por vez."""
    global _current, _worker_running

    while True:
        with _lock:
            if not _queue:
                _current = None
                _worker_running = False
                logger.info("[queue] Fila vazia, worker parou")
                return
            _current = _queue.popleft()

        producao_id = _current["producao_id"]
        logger.info(f"[queue] Processando: {producao_id}")

        # Atualizar posicoes dos que ficaram na fila
        from shorts_endpoints import _add_log
        with _lock:
            for i, q in enumerate(_queue):
                _add_log(q["producao_id"], f"Na fila (posicao {i + 1})")

        try:
            from shorts_endpoints import _run_full_production_bg
            _run_full_production_bg(
                _current["producao_id"],
                _current["json_path"],
                _current["production_path"],
                _current["subnicho"],
            )
        except Exception as e:
            try:
                logger.error(f"[queue] Erro: {producao_id} -- {str(e).encode('ascii','replace').decode()}")
            except Exception:
                logger.error(f"[queue] Erro: {producao_id}")
            from shorts_endpoints import _production_status
            _production_status[producao_id] = "error"

"""
Shorts Production API Endpoints.

Endpoints para o dashboard Shorts Factory:
- Sugerir temas (GPT-4 Mini)
- Gerar produção (Roteirista + Diretor via Claude CLI)
- Executar Freepik (Playwright)
- Editar com Remotion (Whisper + legendas + Drive upload)
- Produzir tudo (1 clique: Freepik → Remotion → Drive)
- Logs em tempo real
- CRUD de produções (via Supabase)
"""

import logging
import json
import os
import time
from datetime import datetime
from collections import defaultdict
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from database import SupabaseClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/shorts", tags=["shorts"])

db = SupabaseClient()

# === Sistema de logs em tempo real (in-memory) ===
_production_logs: dict[int, list[dict]] = defaultdict(list)
_production_status: dict[int, str] = {}  # "idle" | "running" | "done" | "error"


def _add_log(producao_id: int, msg: str):
    """Adiciona log pra uma produção."""
    entry = {"time": datetime.now().strftime("%H:%M:%S"), "msg": msg}
    _production_logs[producao_id].append(entry)
    try:
        logger.info(f"[shorts][{producao_id}] {msg}")
    except UnicodeEncodeError:
        logger.info(f"[shorts][{producao_id}] {msg.encode('ascii', 'replace').decode()}")


def _log_callback(producao_id: int):
    """Retorna callback pra usar no pipeline."""
    return lambda msg: _add_log(producao_id, msg)


# === Models ===

class GerarRequest(BaseModel):
    topic: str
    canal: str
    canal_id: Optional[int] = None
    subnicho: str
    lingua: str
    avulso: bool = False


class SugerirTemasRequest(BaseModel):
    canal: str = ""
    subnicho: str = ""
    lingua: str = "Português"
    tema_livre: str = ""


# === Background tasks ===

def _run_production_bg(topic: str, canal: str, canal_id: int | None, subnicho: str, lingua: str):
    """Roda o pipeline de geração em background."""
    try:
        topic_safe = topic.encode('ascii', 'replace').decode()
        canal_safe = canal.encode('ascii', 'replace').decode()
        logger.info(f"[shorts] BG: Iniciando producao '{topic_safe}' para {canal_safe}")

        from _features.shorts_production.pipeline import run_production
        result = run_production(topic, canal, canal_id or 0, subnicho, lingua)

        insert_data = {
            "canal": result["canal"],
            "subnicho": result["subnicho"],
            "lingua": result["lingua"],
            "titulo": result["titulo"],
            "estrutura": result["estrutura"],
            "producao_json": result["producao_json"],
            "drive_link": result["drive_link"],
            "status": "producao",
        }
        if canal_id:
            insert_data["canal_id"] = canal_id
        db.supabase.table("shorts_production").insert(insert_data).execute()

        titulo_safe = result['titulo'].encode('ascii', 'replace').decode()
        logger.info(f"[shorts] BG: Producao salva: {titulo_safe}")
    except Exception as e:
        import traceback
        logger.error(f"[shorts] BG ERRO: {str(e).encode('ascii', 'replace').decode()}")
        logger.error(traceback.format_exc())


def _run_freepik_bg(producao_id: int, json_path: str):
    """Roda automação do Freepik em background com logs."""
    _production_status[producao_id] = "running"
    _production_logs[producao_id] = []
    _add_log(producao_id, "Iniciando Freepik Spaces...")

    try:
        from _features.shorts_production.freepik_automation import run_freepik_production
        success = run_freepik_production(json_path, log_callback=_log_callback(producao_id))

        if success:
            db.supabase.table("shorts_production").update({
                "status": "edicao",
                "updated_at": datetime.utcnow().isoformat(),
            }).eq("id", producao_id).execute()
            _add_log(producao_id, "Freepik concluido! Status >> edicao")
            _production_status[producao_id] = "done"
        else:
            _add_log(producao_id, "ERRO: Freepik falhou")
            _production_status[producao_id] = "error"
    except Exception as e:
        _add_log(producao_id, f"ERRO: {str(e)[:200]}")
        _production_status[producao_id] = "error"


def _run_editing_bg(producao_id: int, production_path: str, subnicho: str):
    """Roda Remotion + Drive em background com logs."""
    _production_status[producao_id] = "running"
    _production_logs[producao_id] = []
    _add_log(producao_id, "Iniciando edicao (Remotion + Drive)...")

    try:
        from _features.shorts_production.remotion_editor import edit_short
        result = edit_short(production_path, subnicho=subnicho, log_callback=_log_callback(producao_id))

        update_data = {
            "status": "pronto",
            "updated_at": datetime.utcnow().isoformat(),
        }
        if isinstance(result, dict) and result.get("drive_url"):
            update_data["drive_url"] = result["drive_url"]
        db.supabase.table("shorts_production").update(update_data).eq("id", producao_id).execute()
        _add_log(producao_id, f"Video pronto!")
        _production_status[producao_id] = "done"
    except Exception as e:
        _add_log(producao_id, f"ERRO: {str(e)[:200]}")
        _production_status[producao_id] = "error"


def _run_full_production_bg(producao_id: int, json_path: str, production_path: str, subnicho: str):
    """Roda Freepik + Remotion + Drive em sequência."""
    _production_status[producao_id] = "running"
    _production_logs[producao_id] = []
    log = _log_callback(producao_id)

    try:
        # FASE 1: Freepik
        log("=== FASE 1: Freepik Spaces ===")
        from _features.shorts_production.freepik_automation import run_freepik_production
        success = run_freepik_production(json_path, log_callback=log)

        if not success:
            log("ERRO: Freepik falhou. Abortando.")
            _production_status[producao_id] = "error"
            return

        db.supabase.table("shorts_production").update({
            "status": "edicao",
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", producao_id).execute()
        log("Freepik concluido! Status >> edicao")

        # FASE 2: Remotion + Drive
        log("=== FASE 2: Remotion + Drive ===")
        from _features.shorts_production.remotion_editor import edit_short
        result = edit_short(production_path, subnicho=subnicho, log_callback=log)

        update_data = {
            "status": "pronto",
            "updated_at": datetime.utcnow().isoformat(),
        }
        if isinstance(result, dict) and result.get("drive_url"):
            update_data["drive_url"] = result["drive_url"]
        db.supabase.table("shorts_production").update(update_data).eq("id", producao_id).execute()
        log(f"Video pronto! Status >> pronto")
        log("=== PRODUCAO COMPLETA ===")
        _production_status[producao_id] = "done"

    except Exception as e:
        log(f"ERRO: {str(e)[:200]}")
        _production_status[producao_id] = "error"


# === Endpoints ===

@router.post("/gerar")
async def gerar_producao(req: GerarRequest, background_tasks: BackgroundTasks):
    """Gera script + prompts em background."""
    background_tasks.add_task(
        _run_production_bg,
        topic=req.topic,
        canal=req.canal,
        canal_id=req.canal_id,
        subnicho=req.subnicho,
        lingua=req.lingua,
    )
    return {"status": "gerando", "message": f"Produção de '{req.topic}' iniciada em background"}


@router.post("/sugerir-temas")
async def sugerir_temas(req: SugerirTemasRequest):
    """Sugere 5 temas via GPT-4 Mini."""
    try:
        from _features.shorts_production.theme_suggester import suggest_themes
        temas = suggest_themes(
            canal=req.canal,
            subnicho=req.subnicho,
            lingua=req.lingua,
            tema_livre=req.tema_livre,
        )
        return {"temas": temas}
    except Exception as e:
        logger.error(f"[shorts] Erro ao sugerir temas: {e}")
        raise HTTPException(500, str(e))


@router.post("/executar-freepik/{producao_id}")
async def executar_freepik(producao_id: int, background_tasks: BackgroundTasks):
    """Executa produção no Freepik Spaces via Playwright."""
    result = db.supabase.table("shorts_production").select("*").eq("id", producao_id).single().execute()
    if not result.data:
        raise HTTPException(404, "Produção não encontrada")

    drive_link = result.data.get("drive_link", "")
    json_path = os.path.join(drive_link, "producao.json") if drive_link else ""

    if not json_path or not os.path.exists(json_path):
        raise HTTPException(400, f"producao.json não encontrado em {drive_link}")

    background_tasks.add_task(_run_freepik_bg, producao_id, json_path)
    return {"status": "executando", "message": f"Freepik iniciado para '{result.data['titulo']}'"}


@router.post("/editar/{producao_id}")
async def editar_producao(producao_id: int, background_tasks: BackgroundTasks):
    """Aciona Remotion + Drive upload em background."""
    result = db.supabase.table("shorts_production").select("*").eq("id", producao_id).single().execute()
    if not result.data:
        raise HTTPException(404, "Produção não encontrada")

    drive_link = result.data.get("drive_link", "")
    if not drive_link or not os.path.exists(drive_link):
        raise HTTPException(400, f"Pasta não encontrada: {drive_link}")

    subnicho = result.data.get("subnicho", "")
    background_tasks.add_task(_run_editing_bg, producao_id, drive_link, subnicho)
    return {"status": "editando", "message": f"Remotion iniciado para '{result.data['titulo']}'"}


@router.post("/produzir/{producao_id}")
async def produzir_completo(producao_id: int):
    """Adiciona na fila de producao (Freepik >> Remotion >> Drive)."""
    result = db.supabase.table("shorts_production").select("*").eq("id", producao_id).single().execute()
    if not result.data:
        raise HTTPException(404, "Produção não encontrada")

    drive_link = result.data.get("drive_link", "")
    json_path = os.path.join(drive_link, "producao.json") if drive_link else ""

    if not json_path or not os.path.exists(json_path):
        raise HTTPException(400, f"producao.json não encontrado em {drive_link}")

    subnicho = result.data.get("subnicho", "")
    from production_queue import enqueue
    queue_result = enqueue(producao_id, json_path, drive_link, subnicho)
    return {
        "status": "na_fila",
        "posicao": queue_result["posicao"],
        "message": f"Na fila (posição {queue_result['posicao']})",
    }


@router.get("/logs/{producao_id}")
async def get_logs(producao_id: int, after: int = 0):
    """Retorna logs de uma produção (polling). after = index pra pegar só novos."""
    logs = _production_logs.get(producao_id, [])
    status = _production_status.get(producao_id, "idle")
    response = {"logs": logs[after:], "total": len(logs), "status": status}
    if status == "queued":
        from production_queue import get_position
        response["queue_position"] = get_position(producao_id)
    return response


@router.get("/fila-producao")
async def fila_producao():
    """Retorna estado da fila de producao."""
    from production_queue import get_queue_status
    return get_queue_status()


@router.delete("/fila-producao/{producao_id}")
async def remover_da_fila(producao_id: int):
    """Remove producao da fila (se ainda nao comecou)."""
    from production_queue import remove_from_queue
    removed = remove_from_queue(producao_id)
    if not removed:
        raise HTTPException(400, "Producao nao encontrada na fila ou ja em execucao")
    return {"status": "removido"}


@router.post("/pausar/{producao_id}")
async def pausar_producao(producao_id: int):
    """Pausa uma produção em andamento (marca como parado, não mata o processo)."""
    if producao_id in _production_status and _production_status[producao_id] == "running":
        _production_status[producao_id] = "paused"
        _add_log(producao_id, "PAUSADO pelo usuario")
    return {"status": "pausado"}


@router.get("/producoes")
async def listar_producoes(status: Optional[str] = None):
    """Lista produções, opcionalmente filtradas por status."""
    query = db.supabase.table("shorts_production").select("*").order("created_at", desc=True)
    if status:
        query = query.eq("status", status)
    result = query.execute()
    return {"producoes": result.data}


@router.patch("/producoes/{producao_id}/status")
async def atualizar_status(producao_id: int, status: str):
    """Atualiza status de uma produção."""
    if status not in ("producao", "edicao", "pronto", "publicado"):
        raise HTTPException(400, "Status inválido. Use: producao, edicao, pronto")

    db.supabase.table("shorts_production").update({
        "status": status,
        "updated_at": datetime.utcnow().isoformat(),
    }).eq("id", producao_id).execute()

    return {"status": "ok", "novo_status": status}


@router.delete("/producoes/{producao_id}")
async def excluir_producao(producao_id: int):
    """Exclui uma produção."""
    db.supabase.table("shorts_production").delete().eq("id", producao_id).execute()
    return {"status": "excluido"}


@router.get("/producoes/{producao_id}/json")
async def get_producao_json(producao_id: int):
    """Retorna o JSON completo de uma produção."""
    result = db.supabase.table("shorts_production").select("producao_json").eq("id", producao_id).single().execute()
    if not result.data:
        raise HTTPException(404, "Produção não encontrada")
    return result.data.get("producao_json", {})


@router.get("/edicao/fila")
async def fila_edicao():
    """Lista produções prontas pra edição."""
    result = db.supabase.table("shorts_production").select(
        "id, titulo, canal, subnicho, lingua, drive_link, created_at"
    ).eq("status", "edicao").order("created_at", desc=True).execute()
    return {"fila": result.data}


@router.post("/inicializar-browser")
async def inicializar_browser():
    """Abre Chrome com debug port e navega pro Freepik Spaces."""
    import subprocess

    try:
        subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], capture_output=True, timeout=5)
        time.sleep(2)
    except Exception:
        pass

    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    profile_path = r"C:\Users\PC\chrome-debug-profile"
    freepik_url = "https://br.freepik.com/pikaso/spaces/a166a80e-8448-4c38-b231-ce4cd2cc49ce"

    subprocess.Popen([
        chrome_path,
        "--remote-debugging-port=9222",
        f"--user-data-dir={profile_path}",
        freepik_url,
    ])

    return {"status": "ok", "message": "Chrome aberto com debug port + Freepik Spaces"}


@router.get("/browser-status")
async def browser_status():
    """Verifica se o Chrome com debug port está rodando."""
    import urllib.request
    try:
        resp = urllib.request.urlopen("http://127.0.0.1:9222/json/version", timeout=2)
        data = json.loads(resp.read())
        return {"connected": True, "browser": data.get("Browser", "Chrome")}
    except Exception:
        return {"connected": False}


@router.post("/upload-youtube/{producao_id}")
async def upload_youtube(producao_id: int, background_tasks: BackgroundTasks):
    """Faz upload do short pro YouTube como privado."""
    result = db.supabase.table("shorts_production").select("*").eq("id", producao_id).single().execute()
    if not result.data:
        raise HTTPException(404, "Producao nao encontrada")

    if result.data["status"] != "pronto":
        raise HTTPException(400, "Producao nao esta pronta pra upload")

    if result.data.get("youtube_video_id"):
        raise HTTPException(400, "Ja foi enviado pro YouTube")

    drive_link = result.data.get("drive_link", "")
    video_path = os.path.join(drive_link, "video_final.mp4") if drive_link else ""
    if not video_path or not os.path.exists(video_path):
        raise HTTPException(400, f"video_final.mp4 nao encontrado em {drive_link}")

    background_tasks.add_task(_run_youtube_upload_bg, producao_id, result.data, video_path)
    return {"status": "uploading", "message": f"Upload iniciado para '{result.data['titulo']}'"}


def _run_youtube_upload_bg(producao_id: int, production_data: dict, video_path: str):
    """Faz upload do short pro YouTube em background."""
    _production_status[producao_id] = "running"
    _production_logs[producao_id] = []
    log = _log_callback(producao_id)

    try:
        from dotenv import load_dotenv
        load_dotenv()

        canal = production_data.get("canal", "")
        titulo = production_data.get("titulo", "")
        log(f"Upload YouTube: {titulo}")

        # Buscar channel_id do YouTube pelo nome do canal (yt_channels)
        # Match exato primeiro, depois normalizado (sem acentos)
        canal_result = db.supabase.table("yt_channels").select(
            "channel_id"
        ).eq("channel_name", canal).eq("is_active", True).limit(1).execute()

        if not canal_result.data:
            # Match normalizado (sem acentos)
            import unicodedata
            canal_norm = unicodedata.normalize("NFD", canal).encode("ascii", "ignore").decode().lower()
            all_channels = db.supabase.table("yt_channels").select("channel_id, channel_name").eq("is_active", True).execute()
            for ch in all_channels.data:
                ch_norm = unicodedata.normalize("NFD", ch["channel_name"]).encode("ascii", "ignore").decode().lower()
                if ch_norm == canal_norm:
                    canal_result.data = [{"channel_id": ch["channel_id"]}]
                    log(f"Match normalizado: {ch['channel_name']}")
                    break

        if not canal_result.data:
            log(f"ERRO: Canal '{canal}' nao encontrado em canais_monitorados")
            _production_status[producao_id] = "error"
            return

        youtube_channel_id = canal_result.data[0]["channel_id"]
        log(f"Canal YouTube: {youtube_channel_id}")

        # Buscar metadata do producao_json
        prod_json = production_data.get("producao_json", {})
        descricao = prod_json.get("descricao", "")

        # Upload via YouTubeUploader existente
        from _features.yt_uploader.uploader import YouTubeUploader
        uploader = YouTubeUploader()

        result = uploader.upload_to_youtube(
            channel_id=youtube_channel_id,
            video_path=video_path,
            metadata={
                "titulo": titulo,
                "descricao": descricao,
            },
            skip_playlist=True,
            privacy_status="public",
        )
        log(f"Upload configurado: publico, sem playlist")

        if result.get("success"):
            video_id = result["video_id"]
            db.supabase.table("shorts_production").update({
                "youtube_video_id": video_id,
                "status": "publicado",
                "updated_at": datetime.utcnow().isoformat(),
            }).eq("id", producao_id).execute()
            log(f"https://youtube.com/shorts/{video_id}")
            _production_status[producao_id] = "done"
        else:
            log(f"ERRO: Upload falhou - {result}")
            _production_status[producao_id] = "error"

    except Exception as e:
        log(f"ERRO: {str(e)[:300]}")
        _production_status[producao_id] = "error"


@router.get("/canais-com-oauth")
async def canais_com_oauth():
    """Lista canais nossos que tem OAuth configurado."""
    # Canais com OAuth (yt_channels tem channel_name, channel_id, subnicho, lingua)
    oauth = db.supabase.table("yt_oauth_tokens").select("channel_id").execute()
    oauth_ids = {r["channel_id"] for r in oauth.data}

    # Canais nossos ativos (de yt_channels)
    canais = db.supabase.table("yt_channels").select(
        "channel_id, channel_name, subnicho, lingua"
    ).eq("is_active", True).execute()

    com_oauth = []
    sem_oauth = []
    for c in canais.data:
        item = {
            "channel_id": c["channel_id"],
            "nome_canal": c["channel_name"],
            "subnicho": c.get("subnicho", ""),
            "lingua": c.get("lingua", ""),
        }
        if c["channel_id"] in oauth_ids:
            com_oauth.append(item)
        else:
            sem_oauth.append(item)

    return {"com_oauth": com_oauth, "sem_oauth": sem_oauth}


@router.get("/subnichos")
async def listar_subnichos():
    """Lista subnichos dos nossos canais."""
    result = db.supabase.table("canais_monitorados").select("subnicho").eq("tipo", "nosso").eq("status", "ativo").execute()
    EXCLUDED_SUBNICHOS = {"Lições de Vida", "Licoes de Vida", "Registros Malditos"}
    SUBNICHO_ORDER = [
        "Monetizados", "Reis Perversos", "Historias Sombrias", "Culturas Macabras",
        "Relatos de Guerra", "Frentes de Guerra", "Guerras e Civilizações",
        "Guerras e Civilizacoes", "Desmonetizados",
    ]
    all_subnichos = set(
        item["subnicho"] for item in result.data
        if item.get("subnicho") and item["subnicho"] not in EXCLUDED_SUBNICHOS
    )
    # Ordenar pela ordem do dashboard principal
    ordered = [s for s in SUBNICHO_ORDER if s in all_subnichos]
    remaining = sorted(all_subnichos - set(ordered))
    return {"subnichos": ordered + remaining}


@router.get("/canais")
async def listar_canais(subnicho: str):
    """Lista canais de um subnicho, marcando quem tem OAuth."""
    result = db.supabase.table("canais_monitorados").select("id,nome_canal,subnicho,lingua").eq("tipo", "nosso").eq("status", "ativo").eq("subnicho", subnicho).execute()

    # Checar quais tem OAuth (comparar com yt_channels)
    yt = db.supabase.table("yt_channels").select("channel_name").eq("is_active", True).execute()
    yt_nomes = {c["channel_name"] for c in yt.data}

    canais = []
    for c in result.data:
        c["has_oauth"] = c["nome_canal"] in yt_nomes
        canais.append(c)

    # OAuth primeiro, sem OAuth por ultimo
    canais.sort(key=lambda c: (0 if c["has_oauth"] else 1, c["nome_canal"]))

    return {"canais": canais}

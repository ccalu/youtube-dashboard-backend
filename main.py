from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
import asyncio
import logging
import uuid
import threading
import time
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

from database import SupabaseClient
from collector import YouTubeCollector
from notifier import NotificationChecker
from monetization_endpoints import router as monetization_router
from financeiro import FinanceiroService

# YouTube Uploader
from yt_uploader.uploader import YouTubeUploader
from yt_uploader.database import (
    create_upload,
    update_upload_status,
    get_upload_by_id,
    supabase
)
from yt_uploader.sheets import update_upload_status_in_sheet

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="YouTube Dashboard API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================================
# 🔒 UPLOAD CONCURRENCY CONTROL
# ========================================
# Semáforo: máximo 3 uploads simultâneos (protege Railway de overload)
upload_semaphore = asyncio.Semaphore(3)

# ========================================
# 💰 MONETIZATION ROUTER
# ========================================
app.include_router(monetization_router)

# ========================================
# 🆕 MODELOS PYDANTIC
# ========================================

class RegraNotificacaoCreate(BaseModel):
    nome_regra: str
    views_minimas: int
    periodo_dias: int
    tipo_canal: str = "ambos"
    subnichos: Optional[List[str]] = None
    ativa: bool = True

# ========================================
# INICIALIZAÇÃO
# ========================================

db = SupabaseClient()
collector = YouTubeCollector()
notifier = NotificationChecker(db.supabase)
financeiro = FinanceiroService(db)
uploader = YouTubeUploader()

collection_in_progress = False
last_collection_time = None

# ========================================
# SISTEMA DE JOBS ASSÍNCRONOS
# ========================================

transcription_jobs: Dict[str, Dict[str, Any]] = {}
jobs_lock = threading.Lock()

def cleanup_old_jobs():
    """Remove jobs com mais de 1 hora"""
    with jobs_lock:
        now = datetime.now(timezone.utc)
        old_jobs = [
            job_id for job_id, job in transcription_jobs.items()
            if (now - job['created_at']).total_seconds() > 3600
        ]
        for job_id in old_jobs:
            logger.info(f"🧹 Removendo job antigo: {job_id}")
            del transcription_jobs[job_id]

def process_transcription_job(job_id: str, video_id: str):
    """Processa transcrição usando servidor M5 local com polling"""
    try:
        logger.info(f"🎬 [JOB {job_id}] Iniciando transcrição: {video_id}")
        
        with jobs_lock:
            transcription_jobs[job_id]['status'] = 'processing'
            transcription_jobs[job_id]['message'] = 'Iniciando job no servidor M5...'
        
        import requests
        import time
        
        # PASSO 1: Criar job no M5
        logger.info(f"📡 [JOB {job_id}] Criando job no servidor M5...")
        
        response = requests.post(
            "https://transcription.2growai.com.br/transcribe",
            json={
                "video_id": video_id,
                "language": "en"
            },
            timeout=30  # Só para criar o job
        )
        
        if response.status_code != 200:
            raise Exception(f"Servidor M5 retornou erro: {response.status_code}")
        
        data = response.json()
        m5_job_id = data.get('job_id')
        
        if not m5_job_id:
            raise Exception("Servidor M5 não retornou job_id")
        
        logger.info(f"✅ [JOB {job_id}] Job criado no M5: {m5_job_id}")
        
        # PASSO 2: Fazer polling até completar
        max_attempts = 360  # 30 minutos (360 * 5s)
        attempt = 0
        
        while attempt < max_attempts:
            time.sleep(5)  # Aguardar 5 segundos entre checks
            attempt += 1
            
            try:
                status_response = requests.get(
                    f"https://transcription.2growai.com.br/status/{m5_job_id}",
                    timeout=10
                )
                
                if status_response.status_code != 200:
                    continue
                
                status_data = status_response.json()
                m5_status = status_data.get('status')
                
                # Atualizar mensagem
                with jobs_lock:
                    transcription_jobs[job_id]['message'] = status_data.get('message', 'Processando...')
                
                logger.info(f"📊 [JOB {job_id}] Status M5: {m5_status} ({status_data.get('elapsed_seconds')}s)")
                
                # Verificar se completou
                if m5_status == 'completed':
                    result = status_data.get('result', {})
                    transcription = result.get('transcription', '')
                    
                    logger.info(f"✅ [JOB {job_id}] Transcrição completa: {len(transcription)} caracteres")
                    
                    # Salvar no cache
                    asyncio.run(db.save_transcription_cache(video_id, transcription))
                    
                    with jobs_lock:
                        transcription_jobs[job_id]['status'] = 'completed'
                        transcription_jobs[job_id]['message'] = 'Transcrição concluída'
                        transcription_jobs[job_id]['result'] = {
                            'transcription': transcription,
                            'video_id': video_id
                        }
                        transcription_jobs[job_id]['completed_at'] = datetime.now(timezone.utc)
                    
                    logger.info(f"✅ [JOB {job_id}] SUCESSO")
                    return
                
                # Verificar se falhou
                if m5_status == 'failed':
                    error_msg = status_data.get('error', 'Erro desconhecido no servidor M5')
                    raise Exception(error_msg)
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"⚠️ [JOB {job_id}] Erro no polling (tentativa {attempt}): {e}")
                continue
        
        # Timeout
        raise Exception(f"Timeout após {max_attempts * 5} segundos aguardando servidor M5")
        
    except Exception as e:
        logger.error(f"❌ [JOB {job_id}] ERRO: {e}")
        
        with jobs_lock:
            transcription_jobs[job_id]['status'] = 'failed'
            transcription_jobs[job_id]['message'] = str(e)
            transcription_jobs[job_id]['error'] = str(e)
            transcription_jobs[job_id]['failed_at'] = datetime.now(timezone.utc)

# ========================================
# ENDPOINTS DE TRANSCRIÇÃO ASSÍNCRONA
# ========================================

@app.post("/api/transcribe")
async def transcribe_video_async(video_id: str):
    """Inicia transcrição assíncrona - aceita query param"""
    try:
        logger.info(f"🎬 Nova requisição de transcrição: {video_id}")
        
        cleanup_old_jobs()
        
        # Verificar cache primeiro
        cached = await db.get_cached_transcription(video_id)
        if cached:
            logger.info(f"✅ Cache hit para: {video_id}")
            return {
                "status": "completed",
                "from_cache": True,
                "result": {
                    "transcription": cached,
                    "video_id": video_id
                }
            }
        
        job_id = str(uuid.uuid4())
        
        with jobs_lock:
            transcription_jobs[job_id] = {
                'job_id': job_id,
                'video_id': video_id,
                'status': 'queued',
                'message': 'Iniciando processamento...',
                'created_at': datetime.now(timezone.utc),
                'result': None,
                'error': None
            }
        
        thread = threading.Thread(
            target=process_transcription_job,
            args=(job_id, video_id),
            daemon=True
        )
        thread.start()
        
        logger.info(f"🚀 Job criado: {job_id} para vídeo {video_id}")
        
        return {
            "status": "processing",
            "job_id": job_id,
            "video_id": video_id,
            "message": "Transcrição iniciada. Use /api/transcribe/status/{job_id} para verificar progresso."
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar job de transcrição: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/transcribe/status/{job_id}")
async def get_transcription_status(job_id: str):
    """Verifica status do job de transcrição"""
    try:
        with jobs_lock:
            if job_id not in transcription_jobs:
                raise HTTPException(
                    status_code=404, 
                    detail="Job não encontrado. Pode ter expirado (>1h) ou não existir."
                )
            
            job = transcription_jobs[job_id]
        
        elapsed = (datetime.now(timezone.utc) - job['created_at']).total_seconds()
        
        response = {
            "job_id": job['job_id'],
            "video_id": job['video_id'],
            "status": job['status'],
            "message": job['message'],
            "elapsed_seconds": int(elapsed)
        }
        
        if job['status'] == 'completed':
            response['result'] = job['result']
            response['completed_at'] = job['completed_at'].isoformat()
        
        if job['status'] == 'failed':
            response['error'] = job['error']
            response['failed_at'] = job['failed_at'].isoformat()
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao buscar status do job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/transcribe/jobs")
async def list_active_jobs():
    """Lista todos os jobs ativos"""
    try:
        with jobs_lock:
            jobs_list = []
            for job_id, job in transcription_jobs.items():
                jobs_list.append({
                    'job_id': job['job_id'],
                    'video_id': job['video_id'],
                    'status': job['status'],
                    'created_at': job['created_at'].isoformat(),
                    'elapsed_seconds': int((datetime.now(timezone.utc) - job['created_at']).total_seconds())
                })
        
        return {
            "total_jobs": len(jobs_list),
            "jobs": jobs_list
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# ENDPOINTS ORIGINAIS
# ========================================

@app.get("/")
async def root():
    return {"message": "YouTube Dashboard API is running", "status": "healthy", "version": "1.0"}

@app.get("/health")
async def health_check():
    try:
        await db.test_connection()
        
        quota_usada = await db.get_quota_diaria_usada()
        
        return {
            "status": "healthy", 
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "supabase": "connected",
            "youtube_api": "configured",
            "collection_in_progress": collection_in_progress,
            "last_collection": last_collection_time.isoformat() if last_collection_time else None,
            "quota_usada_hoje": quota_usada,
            "active_transcription_jobs": len(transcription_jobs)
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.get("/api/canais")
async def get_canais(
    nicho: Optional[str] = None,
    subnicho: Optional[str] = None,
    lingua: Optional[str] = None,
    tipo: Optional[str] = None,
    views_30d_min: Optional[int] = None,
    views_15d_min: Optional[int] = None,
    views_7d_min: Optional[int] = None,
    score_min: Optional[float] = None,
    growth_min: Optional[float] = None,
    limit: Optional[int] = 500,
    offset: Optional[int] = 0
):
    try:
        canais = await db.get_canais_with_filters(
            nicho=nicho,
            subnicho=subnicho,
            lingua=lingua,
            tipo=tipo,
            views_30d_min=views_30d_min,
            views_15d_min=views_15d_min,
            views_7d_min=views_7d_min,
            score_min=score_min,
            growth_min=growth_min,
            limit=limit,
            offset=offset
        )
        return {"canais": canais, "total": len(canais)}
    except Exception as e:
        logger.error(f"Error fetching canais: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/nossos-canais")
async def get_nossos_canais(
    nicho: Optional[str] = None,
    subnicho: Optional[str] = None,
    lingua: Optional[str] = None,
    views_30d_min: Optional[int] = None,
    views_15d_min: Optional[int] = None,
    views_7d_min: Optional[int] = None,
    score_min: Optional[float] = None,
    growth_min: Optional[float] = None,
    limit: Optional[int] = 100,
    offset: Optional[int] = 0
):
    try:
        canais = await db.get_canais_with_filters(
            nicho=nicho,
            subnicho=subnicho,
            lingua=lingua,
            tipo="nosso",
            views_30d_min=views_30d_min,
            views_15d_min=views_15d_min,
            views_7d_min=views_7d_min,
            score_min=score_min,
            growth_min=growth_min,
            limit=limit,
            offset=offset
        )
        return {"canais": canais, "total": len(canais)}
    except Exception as e:
        logger.error(f"Error fetching nossos canais: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/canais-tabela")
async def get_canais_tabela():
    """
    Retorna nossos canais agrupados por subnicho para aba Tabela.
    Canais ordenados por desempenho (maior ganho de inscritos no topo).
    Subnichos ordenados alfabeticamente.
    """
    try:
        logger.info("Buscando canais para aba Tabela...")

        # Buscar todos os nossos canais (sem limite)
        canais = await db.get_canais_with_filters(
            tipo="nosso",
            limit=1000,
            offset=0
        )

        logger.info(f"Total de canais encontrados: {len(canais)}")

        # Agrupar por subnicho
        grupos = {}
        for canal in canais:
            subnicho = canal.get('subnicho') or 'Sem Categoria'

            if subnicho not in grupos:
                grupos[subnicho] = []

            # Adicionar canal ao grupo
            grupos[subnicho].append({
                'id': canal['id'],
                'nome_canal': canal['nome_canal'],
                'url_canal': canal['url_canal'],
                'inscritos': canal.get('inscritos', 0),
                'inscritos_diff': canal.get('inscritos_diff'),
                'ultima_coleta': canal.get('ultima_coleta'),
                'subnicho': subnicho,
                'lingua': canal.get('lingua', 'N/A')
            })

        # Ordenar canais dentro de cada grupo por desempenho
        # Ordem desejada: melhor (positivos) -> menor (negativos) -> zero -> nulo
        # Ordem secundária: maior número de inscritos (tiebreaker)
        def sort_key(canal):
            diff = canal['inscritos_diff']
            inscritos = canal['inscritos']

            # Estratégia de ordenação:
            # 1. null por último (categoria 3)
            if diff is None:
                return (3, 0, -inscritos)

            # 2. zero em penúltimo (categoria 2)
            if diff == 0:
                return (2, 0, -inscritos)

            # 3. negativos antes do zero (categoria 1, ordenados por valor)
            if diff < 0:
                return (1, diff, -inscritos)  # diff negativo = menor primeiro

            # 4. positivos no topo (categoria 0, ordenados DESC)
            return (0, -diff, -inscritos)

        for subnicho in grupos:
            grupos[subnicho].sort(key=sort_key)

        # Ordenar subnichos alfabeticamente
        grupos_ordenados = dict(sorted(grupos.items()))

        logger.info(f"Canais agrupados em {len(grupos_ordenados)} subnichos")

        return {
            "grupos": grupos_ordenados,
            "total_canais": len(canais),
            "total_subnichos": len(grupos_ordenados)
        }

    except Exception as e:
        logger.error(f"Error fetching canais tabela: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/canais/{channel_id}/monetizacao")
async def toggle_monetizacao(channel_id: str, body: dict):
    """
    Ativa/desativa coleta de monetização para um canal.

    Body: {"is_monetized": true/false}

    Se ativar (true):
      - Próxima coleta diária (5 AM) já coleta revenue
      - Para histórico: rodar script coleta_historico_completo.py

    Se desativar (false):
      - Para de coletar revenue nas próximas coletas
      - Dados históricos permanecem no banco
    """
    try:
        is_monetized = body.get('is_monetized')

        if is_monetized is None:
            raise HTTPException(
                status_code=400,
                detail="Campo 'is_monetized' obrigatório (true/false)"
            )

        # Atualiza no Supabase
        result = supabase.table('yt_channels')\
            .update({'is_monetized': is_monetized})\
            .eq('channel_id', channel_id)\
            .execute()

        if not result.data:
            raise HTTPException(
                status_code=404,
                detail=f"Canal {channel_id} não encontrado"
            )

        status = "ativada" if is_monetized else "desativada"
        logger.info(f"Monetização {status} para canal {channel_id}")

        return {
            "success": True,
            "channel_id": channel_id,
            "is_monetized": is_monetized,
            "message": f"Monetização {status} com sucesso"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao toggle monetização: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/videos")
async def get_videos(
    nicho: Optional[str] = None,
    subnicho: Optional[str] = None,
    lingua: Optional[str] = None,
    canal: Optional[str] = None,
    periodo_publicacao: Optional[str] = "60d",
    views_min: Optional[int] = None,
    growth_min: Optional[float] = None,
    order_by: Optional[str] = "views_atuais",
    limit: Optional[int] = 100,
    offset: Optional[int] = None
):
    try:
        videos = await db.get_videos_with_filters(
            nicho=nicho,
            subnicho=subnicho,
            lingua=lingua,
            canal=canal,
            periodo_publicacao=periodo_publicacao,
            views_min=views_min,
            growth_min=growth_min,
            order_by=order_by,
            limit=limit,
            offset=offset
        )
        return {"videos": videos, "total": len(videos)}
    except Exception as e:
        logger.error(f"Error fetching videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/filtros")
async def get_filtros():
    try:
        filtros = await db.get_filter_options()
        return filtros
    except Exception as e:
        logger.error(f"Error fetching filtros: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/add-canal")
async def add_canal_manual(
    nome_canal: str,
    url_canal: str,
    nicho: str = "",
    subnicho: str = "",
    lingua: str = "English",
    tipo: str = "minerado",
    status: str = "ativo"
):
    try:
        canal_data = {
            'nome_canal': nome_canal,
            'url_canal': url_canal,
            'nicho': nicho,
            'subnicho': subnicho,
            'lingua': lingua,
            'tipo': tipo,
            'status': status
        }
        
        result = await db.upsert_canal(canal_data)
        return {"message": "Canal added successfully", "canal": result}
    except Exception as e:
        logger.error(f"Error adding canal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/canais/{canal_id}")
async def update_canal(
    canal_id: int,
    nome_canal: str,
    url_canal: str,
    nicho: str = "",
    subnicho: str = "",
    lingua: str = "English",
    tipo: str = "minerado",
    status: str = "ativo"
):
    try:
        canal_exists = db.supabase.table("canais_monitorados").select("id").eq("id", canal_id).execute()
        if not canal_exists.data:
            raise HTTPException(status_code=404, detail="Canal não encontrado")
        
        response = db.supabase.table("canais_monitorados").update({
            "nome_canal": nome_canal,
            "url_canal": url_canal,
            "nicho": nicho,
            "subnicho": subnicho,
            "lingua": lingua,
            "tipo": tipo,
            "status": status
        }).eq("id", canal_id).execute()
        
        logger.info(f"Canal updated: {nome_canal} (ID: {canal_id})")
        return {"message": "Canal atualizado com sucesso", "canal": response.data[0] if response.data else None}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating canal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def can_start_collection() -> tuple[bool, str]:
    global collection_in_progress, last_collection_time

    # LOCK NO BANCO: Verificar se já há coleta ativa (fonte da verdade)
    try:
        active_collections = db.supabase.table("coletas_historico")\
            .select("id, data_inicio")\
            .eq("status", "em_progresso")\
            .execute()

        if active_collections.data:
            collection_id = active_collections.data[0]["id"]
            started_at = active_collections.data[0]["data_inicio"]
            return False, f"Collection #{collection_id} already in progress (started: {started_at})"
    except Exception as e:
        logger.error(f"Error checking active collections in DB: {e}")

    # Verificar variável em memória (proteção secundária)
    if collection_in_progress:
        return False, "Collection already in progress (in-memory lock)"

    # Verificar cooldown de 1 minuto
    if last_collection_time:
        time_since_last = datetime.now(timezone.utc) - last_collection_time
        cooldown = timedelta(minutes=1)

        if time_since_last < cooldown:
            remaining = cooldown - time_since_last
            seconds = int(remaining.total_seconds())
            return False, f"Cooldown: aguarde {seconds}s"

    # Limpar coletas travadas (> 2h)
    try:
        await db.cleanup_stuck_collections()
    except Exception as e:
        logger.error(f"Error cleaning stuck collections: {e}")

    return True, "OK"

@app.post("/api/collect-data")
async def collect_data(background_tasks: BackgroundTasks):
    try:
        can_collect, message = await can_start_collection()
        
        if not can_collect:
            return {"message": message, "status": "blocked"}
        
        background_tasks.add_task(run_collection_job)
        return {"message": "Collection started", "status": "processing"}
    except Exception as e:
        logger.error(f"Error starting collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ⬇️⬇️⬇️ ADICIONE ESTE BLOCO AQUI ⬇️⬇️⬇️
@app.post("/api/force-notifier")
async def force_notifier():
    """
    Força execução do notifier manualmente.
    Útil para: testes, debug, ou recuperar notificações perdidas.
    """
    try:
        logger.info("🔔 FORÇANDO EXECUÇÃO DO NOTIFIER (manual)")
        
        # Importar e executar o notifier
        from notifier import NotificationChecker
        
        checker = NotificationChecker(db.supabase)
        await checker.check_and_create_notifications()
        
        logger.info("✅ Notifier executado com sucesso!")
        
        return {
            "status": "success",
            "message": "Notificador executado com sucesso! Verifique as notificações."
        }
    
    except Exception as e:
        logger.error(f"❌ Erro ao executar notifier: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
# ⬆️⬆️⬆️ ATÉ AQUI ⬆️⬆️⬆️

@app.get("/api/stats")
async def get_stats():
    try:
        stats = await db.get_system_stats()
        return stats
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cleanup")
async def cleanup_data():
    try:
        await db.cleanup_old_data()
        return {"message": "Cleanup concluído com sucesso", "status": "success"}
    except Exception as e:
        logger.error(f"Error in cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reset-suspended-keys")
async def reset_suspended_keys():
    """🆕 Endpoint para resetar chaves suspensas (testar novamente após contestação)"""
    try:
        count = collector.reset_suspended_keys()
        return {
            "message": f"{count} chave(s) suspensa(s) resetada(s) com sucesso",
            "keys_reset": count,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error resetting suspended keys: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/coletas/historico")
async def get_coletas_historico(limit: Optional[int] = 20):
    try:
        historico = await db.get_coletas_historico(limit=limit)
        
        quota_usada = await db.get_quota_diaria_usada()
        
        quota_total = len(collector.api_keys) * 10000  
        quota_disponivel = quota_total - quota_usada
        porcentagem_usada = (quota_usada / quota_total) * 100 if quota_total > 0 else 0
        
        now_utc = datetime.now(timezone.utc)
        next_reset = now_utc.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        brasilia_offset = timedelta(hours=-3)
        next_reset_brasilia = next_reset + brasilia_offset

        chaves_esgotadas_real = min(int(quota_usada // 10000), len(collector.api_keys))
        chaves_suspensas_real = len(collector.suspended_keys)
        chaves_ativas_real = len(collector.api_keys) - chaves_esgotadas_real - chaves_suspensas_real
        
        return {
            "historico": historico,
            "total": len(historico),
            "quota_info": {
                "total_diario": quota_total,
                "usado_hoje": quota_usada,
                "disponivel": quota_disponivel,
                "porcentagem_usada": round(porcentagem_usada, 1),
                "total_chaves": len(collector.api_keys),
                "chaves_ativas": chaves_ativas_real,
                "chaves_esgotadas": chaves_esgotadas_real,
                "chaves_esgotadas_ids": list(collector.exhausted_keys_date.keys()),
                "chaves_suspensas": len(collector.suspended_keys),
                "chaves_suspensas_ids": list(collector.suspended_keys),
                "proximo_reset_utc": next_reset.isoformat(),
                "proximo_reset_local": next_reset_brasilia.strftime("%d/%m/%Y %H:%M (Horário de Brasília)")
            }
        }
    except Exception as e:
        logger.error(f"Error fetching coletas historico: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/coletas/cleanup")
async def cleanup_stuck_collections():
    try:
        count = await db.cleanup_stuck_collections()
        return {"message": f"{count} coletas travadas marcadas como erro", "count": count}
    except Exception as e:
        logger.error(f"Error in cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/coletas/{coleta_id}")
async def delete_coleta(coleta_id: int):
    try:
        await db.delete_coleta(coleta_id)
        return {"message": "Coleta deletada com sucesso"}
    except Exception as e:
        logger.error(f"Error deleting coleta: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/favoritos/adicionar")
async def add_favorito(tipo: str, item_id: int):
    try:
        if tipo not in ["canal", "video"]:
            raise HTTPException(status_code=400, detail="Tipo deve ser 'canal' ou 'video'")
        
        if tipo == "canal":
            canal_exists = db.supabase.table("canais_monitorados").select("id").eq("id", item_id).execute()
            if not canal_exists.data:
                raise HTTPException(status_code=404, detail="Canal não encontrado")
        elif tipo == "video":
            video_exists = db.supabase.table("videos_historico").select("id").eq("id", item_id).execute()
            if not video_exists.data:
                raise HTTPException(status_code=404, detail="Vídeo não encontrado")
        
        result = await db.add_favorito(tipo, item_id)
        return {"message": "Favorito adicionado com sucesso", "favorito": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding favorito: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/favoritos/remover")
async def remove_favorito(tipo: str, item_id: int):
    try:
        if tipo not in ["canal", "video"]:
            raise HTTPException(status_code=400, detail="Tipo deve ser 'canal' ou 'video'")

        await db.remove_favorito(tipo, item_id)
        return {"message": "Favorito removido com sucesso"}
    except Exception as e:
        logger.error(f"Error removing favorito: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/favoritos/canais")
async def get_favoritos_canais():
    try:
        canais = await db.get_favoritos_canais()
        return {"canais": canais, "total": len(canais)}
    except Exception as e:
        logger.error(f"Error fetching favoritos canais: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/favoritos/videos")
async def get_favoritos_videos():
    try:
        videos = await db.get_favoritos_videos()
        return {"videos": videos, "total": len(videos)}
    except Exception as e:
        logger.error(f"Error fetching favoritos videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/canais/{canal_id}")
async def delete_canal(canal_id: int, permanent: bool = False):
    try:
        if permanent:
            try:
                notif_response = db.supabase.table("notificacoes").delete().eq("canal_id", canal_id).execute()
                deleted_count = len(notif_response.data) if notif_response.data else 0
                logger.info(f"Deleted {deleted_count} notifications for canal {canal_id}")
            except Exception as e:
                logger.warning(f"Error deleting notifications for canal {canal_id}: {e}")
            
            await db.delete_canal_permanently(canal_id)
            return {"message": "Canal deletado permanentemente"}
        else:
            response = db.supabase.table("canais_monitorados").update({
                "status": "inativo"
            }).eq("id", canal_id).execute()
            return {"message": "Canal desativado", "canal": response.data}
    except Exception as e:
        logger.error(f"Error deleting canal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/notificacoes")
async def get_notificacoes_nao_vistas():
    try:
        notificacoes = await db.get_notificacoes_nao_vistas()
        return {
            "notificacoes": notificacoes,
            "total": len(notificacoes)
        }
    except Exception as e:
        logger.error(f"Error fetching notificacoes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/notificacoes/todas")
async def get_notificacoes_todas(
    limit: Optional[int] = 500,
    offset: Optional[int] = 0,
    vista: Optional[bool] = None,
    dias: Optional[int] = 30,
    lingua: Optional[str] = None,
    tipo_canal: Optional[str] = None
):
    """
    Lista todas as notificações com filtros.

    Query params:
    - tipo_canal: Filtrar por tipo (nosso/minerado)
    - lingua: Filtrar por língua
    - vista: Filtrar por vistas (true/false)
    - dias: Período em dias (padrão: 30)
    """
    try:
        notificacoes = await db.get_notificacoes_all(
            limit=limit,
            offset=offset,
            vista_filter=vista,
            dias=dias,
            lingua=lingua,
            tipo_canal=tipo_canal
        )
        return {
            "notificacoes": notificacoes,
            "total": len(notificacoes)
        }
    except Exception as e:
        logger.error(f"Error fetching all notificacoes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/notificacoes/historico")
async def get_notificacoes_historico(limit: Optional[int] = 100):
    try:
        notificacoes = await db.get_notificacoes_all(limit=limit, offset=0)
        return {
            "historico": notificacoes,
            "total": len(notificacoes)
        }
    except Exception as e:
        logger.error(f"Error fetching historico: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/notificacoes/{notif_id}/marcar-vista")
async def marcar_notificacao_vista(notif_id: int):
    """
    Marca uma notificação como vista.
    """
    try:
        success = await db.marcar_notificacao_vista(notif_id)
        
        if success:
            return {
                "message": "Notificação marcada como vista",
                "notif_id": notif_id
            }
        else:
            raise HTTPException(status_code=404, detail="Notificação não encontrada")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notificacao as vista: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/notificacoes/{notif_id}/desmarcar-vista")
async def desmarcar_notificacao_vista(notif_id: int):
    """
    Desmarca uma notificação como vista (volta para não vista).
    Útil quando usuário marca por engano.
    """
    try:
        logger.info(f"🔄 Desmarcando notificação {notif_id} como não vista")
        
        success = await db.desmarcar_notificacao_vista(notif_id)
        
        if success:
            logger.info(f"✅ Notificação {notif_id} desmarcada com sucesso")
            return {
                "message": "Notificação desmarcada como vista",
                "notif_id": notif_id
            }
        else:
            raise HTTPException(status_code=404, detail="Notificação não encontrada")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao desmarcar notificação: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/notificacoes/marcar-todas")
async def marcar_todas_notificacoes_vistas(
    lingua: Optional[str] = None,
    subnicho: Optional[str] = None,
    tipo_canal: Optional[str] = None,
    periodo_dias: Optional[int] = None
):
    """
    Marca notificações não vistas como vistas (com filtros opcionais).

    Query params:
    - lingua: Filtrar por língua (ex: português, francês)
    - subnicho: Filtrar por subnicho
    - tipo_canal: Filtrar por tipo (nosso/minerado)
    - periodo_dias: Filtrar por período da regra (7, 15, 30)
    """
    try:
        count = await db.marcar_todas_notificacoes_vistas(
            lingua=lingua,
            subnicho=subnicho,
            tipo_canal=tipo_canal,
            periodo_dias=periodo_dias
        )
        return {
            "message": f"{count} notificações marcadas como vistas",
            "count": count
        }
    except Exception as e:
        logger.error(f"Error marking all notificacoes as vistas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/notificacoes/stats")
async def get_notificacoes_stats():
    try:
        stats = await db.get_notificacao_stats()
        return stats
    except Exception as e:
        logger.error(f"Error fetching notificacao stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/regras-notificacoes")
async def get_regras_notificacoes():
    try:
        regras = await db.get_regras_notificacoes()
        return {
            "regras": regras,
            "total": len(regras)
        }
    except Exception as e:
        logger.error(f"Error fetching regras: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/regras-notificacoes")
async def create_regra_notificacao(regra: RegraNotificacaoCreate):
    """🆕 Aceita JSON body via Pydantic model"""
    try:
        regra_data = {
            "nome_regra": regra.nome_regra,
            "views_minimas": regra.views_minimas,
            "periodo_dias": regra.periodo_dias,
            "tipo_canal": regra.tipo_canal,
            "subnichos": regra.subnichos,
            "ativa": regra.ativa
        }
        
        result = await db.create_regra_notificacao(regra_data)
        
        if result:
            return {
                "message": "Regra criada com sucesso",
                "regra": result
            }
        else:
            raise HTTPException(status_code=500, detail="Erro ao criar regra")
    except Exception as e:
        logger.error(f"Error creating regra: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/regras-notificacoes/{regra_id}")
async def update_regra_notificacao(regra_id: int, regra: RegraNotificacaoCreate):
    """🆕 Aceita JSON body via Pydantic model"""
    try:
        regra_data = {
            "nome_regra": regra.nome_regra,
            "views_minimas": regra.views_minimas,
            "periodo_dias": regra.periodo_dias,
            "tipo_canal": regra.tipo_canal,
            "subnichos": regra.subnichos,
            "ativa": regra.ativa
        }
        
        result = await db.update_regra_notificacao(regra_id, regra_data)
        
        if result:
            return {
                "message": "Regra atualizada com sucesso",
                "regra": result
            }
        else:
            raise HTTPException(status_code=404, detail="Regra não encontrada")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating regra: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/regras-notificacoes/{regra_id}")
async def delete_regra_notificacao(regra_id: int):
    try:
        success = await db.delete_regra_notificacao(regra_id)
        
        if success:
            return {"message": "Regra deletada com sucesso"}
        else:
            raise HTTPException(status_code=404, detail="Regra não encontrada")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting regra: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/regras-notificacoes/{regra_id}/toggle")
async def toggle_regra_notificacao(regra_id: int):
    try:
        result = await db.toggle_regra_notificacao(regra_id)
        
        if result:
            status = "ativada" if result["ativa"] else "desativada"
            return {
                "message": f"Regra {status} com sucesso",
                "regra": result
            }
        else:
            raise HTTPException(status_code=404, detail="Regra não encontrada")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling regra: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================================
# ANALYSIS TAB - New Endpoints
# Added by Claude Code - 2024-11-05
# =========================================================================

@app.get("/api/analysis/keywords")
async def get_keywords_analysis(subniche: str = None, days: int = 30):
    """
    Retorna top 10 keywords

    🚀 OTIMIZADO: Usa tabela pré-calculada (atualizada diariamente)
    Fallback para tempo real se tabela vazia
    """
    try:
        if days not in [7, 15, 30]:
            raise HTTPException(status_code=400, detail="days deve ser 7, 15 ou 30")

        # 1. Tentar buscar da tabela pré-calculada (RÁPIDO - ~50ms)
        keywords = await db.get_keyword_analysis(period_days=days)

        # 2. Filtrar por subniche se especificado
        if subniche and keywords:
            keywords = [k for k in keywords if k.get('subniche') == subniche]

        # 3. Fallback: Se tabela vazia, calcular em tempo real
        if not keywords:
            logger.warning(f"Tabela keyword_analysis vazia - calculando em tempo real")
            from analyzer import Analyzer
            analyzer = Analyzer(db.supabase)
            keywords = analyzer.analyze_keywords(subniche=subniche, period_days=days)

        return {
            "subniche": subniche or "todos",
            "period_days": days,
            "total": len(keywords),
            "keywords": keywords
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting keywords analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analysis/title-patterns")
async def get_title_patterns_analysis(subniche: str, days: int = 30):
    """
    Retorna top 5 padrões de título

    🚀 OTIMIZADO: Usa tabela pré-calculada (atualizada diariamente)
    Fallback para tempo real se tabela vazia
    """
    try:
        if days not in [7, 15, 30]:
            raise HTTPException(status_code=400, detail="days deve ser 7, 15 ou 30")

        # 1. Tentar buscar da tabela pré-calculada (RÁPIDO - ~50ms)
        patterns = await db.get_title_patterns(subniche=subniche, period_days=days)

        # 2. Fallback: Se tabela vazia, calcular em tempo real
        if not patterns:
            logger.warning(f"Tabela title_patterns vazia para {subniche} - calculando em tempo real")
            from analyzer import Analyzer
            analyzer = Analyzer(db.supabase)
            patterns = analyzer.analyze_title_patterns(subniche=subniche, period_days=days)

        return {
            "subniche": subniche,
            "period_days": days,
            "total": len(patterns),
            "patterns": patterns
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting title patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analysis/top-channels")
async def get_top_channels_analysis(subniche: str, days: int = 30):
    """
    Retorna top 5 canais por subniche

    🚀 OTIMIZADO: Usa tabela pré-calculada quando disponível
    Fallback para tempo real com filtro de período
    """
    try:
        if days not in [7, 15, 30]:
            raise HTTPException(status_code=400, detail="days deve ser 7, 15 ou 30")

        channels = []

        # 1. Para período de 30 dias, tentar usar snapshot (RÁPIDO - ~50ms)
        if days == 30:
            channels = await db.get_top_channels_snapshot(subniche=subniche)

        # 2. Fallback: Se snapshot vazio OU período diferente de 30 dias, calcular em tempo real
        if not channels:
            if days == 30:
                logger.warning(f"Snapshot vazio para {subniche} - calculando em tempo real")
            from analyzer import Analyzer
            analyzer = Analyzer(db.supabase)
            channels = analyzer.analyze_top_channels(subniche=subniche, period_days=days)

        return {
            "subniche": subniche,
            "period_days": days,
            "total": len(channels),
            "channels": channels
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting top channels: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analysis/subniches")
async def get_all_subniches():
    """Retorna lista de todos os subniches ativos"""
    try:
        subniches = await db.get_all_subniches()
        return {"total": len(subniches), "subniches": subniches}
    except Exception as e:
        logger.error(f"Error getting subniches: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analysis/subniche-trends")
async def get_subniche_trends():
    """
    Retorna tendências pré-calculadas de todos os subnichos (7d, 15d, 30d)

    🚀 OTIMIZADO: Retorna os 3 períodos em uma única chamada
    Dados atualizados diariamente durante coleta
    """
    try:
        # Buscar os 3 períodos de uma vez (otimização frontend)
        trends = await db.get_all_subniche_trends()

        return {
            "success": True,
            "data": trends,
            "total_7d": len(trends.get("7d", [])),
            "total_15d": len(trends.get("15d", [])),
            "total_30d": len(trends.get("30d", []))
        }
    except Exception as e:
        logger.error(f"Error getting subniche trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/weekly/latest")
async def get_latest_weekly_report():
    """Retorna o relatório semanal mais recente"""
    try:
        report = await db.get_weekly_report_latest()
        if report:
            return report
        else:
            raise HTTPException(status_code=404, detail="Nenhum relatório encontrado")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting weekly report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reports/weekly/generate")
async def generate_weekly_report_endpoint():
    """Força a geração de um novo relatório semanal"""
    try:
        from report_generator import ReportGenerator
        logger.info("🔄 Starting weekly report generation...")
        generator = ReportGenerator(db.supabase)
        report = generator.generate_weekly_report()
        logger.info("✅ Weekly report generated successfully")
        return {"message": "Relatório gerado com sucesso", "report": report}
    except Exception as e:
        logger.error(f"Error generating weekly report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analysis/run-daily")
async def run_daily_analysis():
    """Executa análises diárias manualmente"""
    try:
        await run_daily_analysis_job()
        return {"message": "Análise diária executada com sucesso"}
    except Exception as e:
        logger.error(f"Error running daily analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analysis/run-gaps")
async def run_gap_analysis():
    """Executa análise de gaps manualmente"""
    try:
        from analyzer import Analyzer, save_analysis_to_db
        logger.info("🔄 Starting gap analysis...")
        analyzer = Analyzer(db.supabase)
        subniches = await db.get_all_subniches()
        gaps_found = {}
        for subniche in subniches:
            gaps = analyzer.analyze_gaps(subniche)
            save_analysis_to_db(db.supabase, 'gaps', gaps, subniche=subniche)
            gaps_found[subniche] = len(gaps)
        return {"message": "Análise de gaps executada com sucesso", "gaps_found": gaps_found}
    except Exception as e:
        logger.error(f"Error running gap analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def run_collection_job():
    global collection_in_progress, last_collection_time
    
    coleta_id = None
    canais_sucesso = 0
    canais_erro = 0
    videos_total = 0
    
    try:
        collection_in_progress = True
        logger.info("=" * 80)
        logger.info("🚀 STARTING COLLECTION JOB")
        logger.info("=" * 80)
        
        collector.reset_for_new_collection()
        
        canais_to_collect = await db.get_canais_for_collection()
        total_canais = len(canais_to_collect)
        logger.info(f"📊 Found {total_canais} canais to collect")
        
        coleta_id = await db.create_coleta_log(total_canais)
        logger.info(f"📝 Created coleta log ID: {coleta_id}")
        
        for index, canal in enumerate(canais_to_collect, 1):
            if collector.all_keys_exhausted():
                logger.error("=" * 80)
                logger.error("❌ ALL API KEYS EXHAUSTED - STOPPING COLLECTION")
                logger.error(f"✅ Collected {canais_sucesso}/{total_canais} canais")
                logger.error(f"📊 Total requests used: {collector.total_quota_units}")
                logger.error("=" * 80)
                break
            
            try:
                logger.info(f"[{index}/{total_canais}] 🔄 Processing: {canal['nome_canal']}")
                
                canal_data = await collector.get_canal_data(canal['url_canal'], canal['nome_canal'])
                if canal_data:
                    saved = await db.save_canal_data(canal['id'], canal_data)
                    if saved:
                        canais_sucesso += 1
                        logger.info(f"✅ [{index}/{total_canais}] Success: {canal['nome_canal']}")
                    else:
                        canais_erro += 1
                        logger.warning(f"⚠️ [{index}/{total_canais}] Data not saved (all zeros): {canal['nome_canal']}")
                else:
                    canais_erro += 1
                    logger.warning(f"❌ [{index}/{total_canais}] Failed: {canal['nome_canal']}")
                
                videos_data = await collector.get_videos_data(canal['url_canal'], canal['nome_canal'])
                if videos_data:
                    await db.save_videos_data(canal['id'], videos_data)
                    videos_total += len(videos_data)
                
                await db.update_last_collection(canal['id'])

                # 🚀 OTIMIZAÇÃO: Removido sleep entre canais - RateLimiter já controla
                # await asyncio.sleep(1)

                # Atualizar progresso no banco a cada 10 canais
                if index % 10 == 0 and coleta_id:
                    try:
                        await db.update_coleta_log(
                            coleta_id=coleta_id,
                            status="em_progresso",
                            canais_sucesso=canais_sucesso,
                            canais_erro=canais_erro,
                            videos_coletados=videos_total,
                            requisicoes_usadas=collector.total_quota_units
                        )
                        logger.info(f"📊 Progress update: {canais_sucesso} success, {canais_erro} errors, {videos_total} videos")
                    except Exception as update_error:
                        logger.warning(f"⚠️ Failed to update progress: {update_error}")

                # Log de progresso a cada 25 canais
                if index % 25 == 0:
                    logger.info("=" * 80)
                    logger.info(f"🔄 PROGRESS CHECKPOINT [{index}/{total_canais}]")
                    logger.info(f"✅ Success: {canais_sucesso} | ❌ Errors: {canais_erro} | 🎬 Videos: {videos_total}")
                    logger.info(f"📡 API Requests: {collector.total_quota_units} | ⏱️  Time elapsed: ongoing")
                    logger.info("=" * 80)

            except Exception as e:
                logger.error(f"❌ Error processing {canal['nome_canal']}: {e}")
                canais_erro += 1
                continue
        
        stats = collector.get_request_stats()
        total_requests = stats['total_quota_units']
        
        logger.info("=" * 80)
        logger.info(f"📊 COLLECTION STATISTICS")
        logger.info(f"✅ Success: {canais_sucesso}/{total_canais}")
        logger.info(f"❌ Errors: {canais_erro}/{total_canais}")
        logger.info(f"🎬 Videos: {videos_total}")
        logger.info(f"📡 Total API Requests: {total_requests}")
        logger.info(f"🔑 Active keys: {stats['active_keys']}/{len(collector.api_keys)}")
        logger.info("=" * 80)
        
        if canais_sucesso > 0:
            try:
                logger.info("=" * 80)
                logger.info("🔔 CHECKING NOTIFICATIONS")
                logger.info("=" * 80)
                await notifier.check_and_create_notifications()
                logger.info("✅ Notification check completed")

                # Cleanup old notifications (>30 days)
                logger.info("=" * 80)
                logger.info("🧹 CLEANING OLD NOTIFICATIONS")
                logger.info("=" * 80)
                deleted_count = await db.cleanup_old_notifications(days=30)
                logger.info(f"✅ Cleaned up {deleted_count} old notifications (>30 days)")
            except Exception as e:
                logger.error(f"❌ Error checking notifications: {e}")

            # 💰 COLETA DE MONETIZAÇÃO (ESTIMATIVAS)
            try:
                logger.info("=" * 80)
                logger.info("💰 STARTING MONETIZATION COLLECTION (ESTIMATES)")
                logger.info("=" * 80)
                from monetization_collector import collect_monetization
                await collect_monetization()
                logger.info("✅ Monetization estimates collection completed")
            except Exception as e:
                logger.error(f"❌ Error in monetization collection: {e}")

            # 🔐 COLETA OAUTH (REVENUE REAL)
            try:
                logger.info("=" * 80)
                logger.info("🔐 STARTING OAUTH COLLECTION (REAL REVENUE)")
                logger.info("=" * 80)
                from monetization_oauth_collector import collect_oauth_metrics
                result = await collect_oauth_metrics()
                logger.info(f"✅ OAuth collection completed - Success: {result['success']}, Errors: {result['errors']}")
            except Exception as e:
                logger.error(f"❌ Error in OAuth collection: {e}")

        if canais_sucesso >= (total_canais * 0.5):
            logger.info("🧹 Cleanup threshold met (>50% success)")
            await db.cleanup_old_data()
        else:
            logger.warning(f"⏭️ Skipping cleanup - only {canais_sucesso}/{total_canais} succeeded")
        
        if canais_erro == 0:
            status = "sucesso"
        elif canais_sucesso > 0:
            status = "parcial"
        else:
            status = "erro"
        
        if coleta_id:
            await db.update_coleta_log(
                coleta_id=coleta_id,
                status=status,
                canais_sucesso=canais_sucesso,
                canais_erro=canais_erro,
                videos_coletados=videos_total,
                requisicoes_usadas=total_requests
            )
        
        logger.info("=" * 80)
        logger.info(f"✅ COLLECTION COMPLETED")
        logger.info("=" * 80)
        
        last_collection_time = datetime.now(timezone.utc)
        
        # Run daily analysis
        await run_daily_analysis_job()
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"❌ COLLECTION JOB FAILED: {e}")
        logger.error("=" * 80)
        
        if coleta_id:
            await db.update_coleta_log(
                coleta_id=coleta_id,
                status="erro",
                canais_sucesso=canais_sucesso,
                canais_erro=canais_erro,
                videos_coletados=videos_total,
                requisicoes_usadas=collector.total_quota_units if hasattr(collector, 'total_quota_units') else 0,
                mensagem_erro=str(e)
            )
        
        raise
    finally:
        collection_in_progress = False


# =========================================================================
# CRON JOBS - Daily Analysis + Weekly Report
# =========================================================================

async def run_daily_analysis_job():
    """Executa análises diárias após a coleta de dados"""
    try:
        from analyzer import Analyzer, save_analysis_to_db
        logger.info("=" * 80)
        logger.info("STARTING DAILY ANALYSIS JOB")
        logger.info("=" * 80)
        analyzer = Analyzer(db.supabase)
        subniches = await db.get_all_subniches()

        # Keywords, Patterns e Channels POR SUBNICHE
        for subniche in subniches:
            # Keywords por subniche
            for days in [30, 15, 7]:
                keywords = analyzer.analyze_keywords(subniche=subniche, period_days=days)
                save_analysis_to_db(db.supabase, 'keywords', keywords, period_days=days, subniche=subniche)

            # Patterns por subniche
            for days in [30, 15, 7]:
                patterns = analyzer.analyze_title_patterns(subniche, period_days=days)
                save_analysis_to_db(db.supabase, 'patterns', patterns, period_days=days, subniche=subniche)

            # Channels por subniche
            channels = analyzer.analyze_top_channels(subniche)
            save_analysis_to_db(db.supabase, 'channels', channels, subniche=subniche)

        # =====================================================================
        # SUBNICHE TRENDS (novo - 2025-01-07)
        # =====================================================================
        logger.info("Analisando tendencias por subniche...")
        for days in [7, 15, 30]:
            trends = analyzer.analyze_subniche_trends(period_days=days)
            save_analysis_to_db(db.supabase, 'subniche_trends', trends, period_days=days)
        logger.info(f"OK - Tendencias de {len(subniches)} subnichos calculadas (7d, 15d, 30d)")

        logger.info("OK - DAILY ANALYSIS COMPLETED")
    except Exception as e:
        logger.error(f"ERRO - DAILY ANALYSIS FAILED: {e}")

async def run_weekly_report_job():
    """Gera relatório semanal completo (segundas 5h AM)"""
    try:
        from report_generator import ReportGenerator
        from analyzer import Analyzer, save_analysis_to_db
        logger.info("📊 STARTING WEEKLY REPORT JOB")

        # Gap analysis
        analyzer = Analyzer(db.supabase)
        subniches = await db.get_all_subniches()
        for subniche in subniches:
            gaps = analyzer.analyze_gaps(subniche)
            save_analysis_to_db(db.supabase, 'gaps', gaps, subniche=subniche)

        # Gerar relatório
        generator = ReportGenerator(db.supabase)
        report = generator.generate_weekly_report()
        logger.info(f"✅ WEEKLY REPORT COMPLETED: {report['week_start']} to {report['week_end']}")
    except Exception as e:
        logger.error(f"❌ WEEKLY REPORT FAILED: {e}")

async def weekly_report_scheduler():
    """Background task para relatório semanal (segundas 5h AM)"""
    while True:
        try:
            now = datetime.now(timezone.utc)
            sao_paulo_tz = timezone(timedelta(hours=-3))
            now_sp = now.astimezone(sao_paulo_tz)

            if now_sp.weekday() == 0 and now_sp.hour >= 5:
                await run_weekly_report_job()
                await asyncio.sleep(86400)
            else:
                await asyncio.sleep(3600)
        except Exception as e:
            logger.error(f"❌ Weekly scheduler error: {e}")
            await asyncio.sleep(3600)


async def schedule_spreadsheet_scanner():
    """
    Background task para varredura de planilhas Google Sheets.

    Roda a cada X minutos (configurável via SCANNER_INTERVAL_MINUTES).
    Detecta vídeos prontos para upload e adiciona na fila automaticamente.
    """
    from yt_uploader.spreadsheet_scanner import SpreadsheetScanner

    # Configurações
    interval_minutes = int(os.getenv("SCANNER_INTERVAL_MINUTES", "10"))  # 10 min para evitar erro 429
    enabled = os.getenv("SCANNER_ENABLED", "true").lower() == "true"

    if not enabled:
        logger.info("📊 Scanner de planilhas DESABILITADO (SCANNER_ENABLED=false)")
        return

    logger.info(f"📊 Scanner de planilhas AGENDADO (a cada {interval_minutes} min)")

    scanner = SpreadsheetScanner()

    while True:
        try:
            await scanner.scan_all_spreadsheets()
        except Exception as e:
            logger.error(f"❌ Scanner error: {e}", exc_info=True)

        # Aguarda próxima execução
        await asyncio.sleep(interval_minutes * 60)


@app.on_event("startup")
async def startup_event():
    logger.info("=" * 80)
    logger.info("🚀 YOUTUBE DASHBOARD API STARTING")
    logger.info("=" * 80)

    try:
        await db.test_connection()
        logger.info("✅ Database connected")
    except Exception as e:
        logger.error(f"❌ Database failed: {e}")

    try:
        await db.cleanup_stuck_collections()
    except Exception as e:
        logger.error(f"Error cleaning stuck collections: {e}")

    # PROTEÇÃO: Só iniciar schedulers no Railway
    is_railway = os.environ.get("RAILWAY_ENVIRONMENT") is not None

    if is_railway:
        logger.info("📅 Scheduling daily collection (NO startup collection)")
        asyncio.create_task(schedule_daily_collection())
        asyncio.create_task(weekly_report_scheduler())
        asyncio.create_task(schedule_spreadsheet_scanner())
        logger.info("✅ Schedulers started (Railway environment + Scanner)")
    else:
        logger.warning("⚠️ LOCAL ENVIRONMENT - Schedulers DISABLED")
        logger.warning("⚠️ Use /api/collect-data endpoint for manual collection")

    logger.info("=" * 80)

async def schedule_daily_collection():
    logger.info("=" * 80)
    logger.info("⏰ PROTEÇÃO DE STARTUP ATIVADA")
    logger.info("⏳ Aguardando 5 minutos para evitar coletas durante deploy...")
    logger.info("=" * 80)
    await asyncio.sleep(300)
    logger.info("✅ Proteção de startup completa - scheduler ativo")
    
    while True:
        try:
            now = datetime.now(timezone.utc)
            
            next_run = now.replace(hour=8, minute=0, second=0, microsecond=0)
            
            if next_run <= now:
                next_run += timedelta(days=1)
            
            sleep_seconds = (next_run - now).total_seconds()
            
            logger.info("=" * 80)
            logger.info(f"⏰ Next collection: {next_run.isoformat()} (05:00 AM São Paulo)")
            logger.info(f"⏳ Sleeping for {sleep_seconds/3600:.1f} hours")
            logger.info("=" * 80)
            
            await asyncio.sleep(sleep_seconds)
            
            can_collect, message = await can_start_collection()
            
            if can_collect:
                logger.info("🚀 Starting scheduled collection...")
                await run_collection_job()
            else:
                logger.warning(f"⚠️ Scheduled collection blocked: {message}")
            
        except Exception as e:
            logger.error(f"❌ Scheduled collection failed: {e}")
            await asyncio.sleep(3600)

# ========================================
# 💰 ENDPOINTS FINANCEIRO
# ========================================

# ========== CATEGORIAS ==========

@app.get("/api/financeiro/categorias")
async def listar_categorias_financeiras(ativo: bool = None):
    """Lista todas as categorias financeiras"""
    try:
        categorias = await financeiro.listar_categorias(ativo)
        return {"categorias": categorias}
    except Exception as e:
        logger.error(f"Erro ao listar categorias: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/financeiro/categorias")
async def criar_categoria_financeira(
    nome: str,
    tipo: str,
    cor: str = None,
    icon: str = None
):
    """Cria nova categoria financeira"""
    try:
        categoria = await financeiro.criar_categoria(nome, tipo, cor, icon)
        return categoria
    except Exception as e:
        logger.error(f"Erro ao criar categoria: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/financeiro/categorias/{categoria_id}")
async def editar_categoria_financeira(categoria_id: int, dados: Dict[str, Any]):
    """Edita categoria existente"""
    try:
        categoria = await financeiro.editar_categoria(categoria_id, dados)
        return categoria
    except Exception as e:
        logger.error(f"Erro ao editar categoria: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/financeiro/categorias/{categoria_id}")
async def deletar_categoria_financeira(categoria_id: int):
    """Deleta categoria (soft delete)"""
    try:
        await financeiro.deletar_categoria(categoria_id)
        return {"success": True, "message": "Categoria deletada"}
    except Exception as e:
        logger.error(f"Erro ao deletar categoria: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========== LANÇAMENTOS ==========

@app.get("/api/financeiro/lancamentos")
async def listar_lancamentos_financeiros(
    periodo: str = "30d",
    tipo: str = None,
    recorrencia: str = None
):
    """Lista lançamentos com filtros"""
    try:
        lancamentos = await financeiro.listar_lancamentos(periodo, tipo, recorrencia)
        return {"lancamentos": lancamentos, "total": len(lancamentos)}
    except Exception as e:
        logger.error(f"Erro ao listar lançamentos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/financeiro/lancamentos")
async def criar_lancamento_financeiro(request: Request):
    """Cria novo lançamento"""
    try:
        data = await request.json()

        categoria_id = data.get('categoria_id')
        valor = data.get('valor')
        data_lancamento = data.get('data')
        descricao = data.get('descricao', '')
        tipo = data.get('tipo')
        recorrencia = data.get('recorrencia')
        usuario = data.get('usuario', 'Usuario')

        # Validações
        if not categoria_id:
            raise HTTPException(status_code=422, detail="categoria_id é obrigatório")
        if not valor:
            raise HTTPException(status_code=422, detail="valor é obrigatório")
        if not data_lancamento:
            raise HTTPException(status_code=422, detail="data é obrigatória")
        if not tipo:
            raise HTTPException(status_code=422, detail="tipo é obrigatório")
        if tipo not in ['receita', 'despesa']:
            raise HTTPException(status_code=422, detail="tipo deve ser 'receita' ou 'despesa'")

        lancamento = await financeiro.criar_lancamento(
            categoria_id, valor, data_lancamento, descricao, tipo, recorrencia, usuario
        )
        return lancamento
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar lançamento: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/financeiro/lancamentos/{lancamento_id}")
async def editar_lancamento_financeiro(lancamento_id: int, dados: Dict[str, Any]):
    """Edita lançamento existente"""
    try:
        lancamento = await financeiro.editar_lancamento(lancamento_id, dados)
        return lancamento
    except Exception as e:
        logger.error(f"Erro ao editar lançamento: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/financeiro/lancamentos/{lancamento_id}")
async def deletar_lancamento_financeiro(lancamento_id: int):
    """Deleta lançamento"""
    try:
        await financeiro.deletar_lancamento(lancamento_id)
        return {"success": True, "message": "Lançamento deletado"}
    except Exception as e:
        logger.error(f"Erro ao deletar lançamento: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/financeiro/lancamentos/export-csv")
async def exportar_lancamentos_csv(periodo: str = "30d"):
    """Exporta lançamentos em formato CSV"""
    try:
        lancamentos = await financeiro.listar_lancamentos(periodo)

        # Gerar CSV
        from fastapi.responses import Response
        import io

        output = io.StringIO()
        output.write("Data,Tipo,Recorrência,Categoria,Descrição,Valor\n")

        for lanc in lancamentos:
            categoria_nome = lanc.get('financeiro_categorias', {}).get('nome', 'N/A') if lanc.get('financeiro_categorias') else 'N/A'
            recorrencia = lanc.get('recorrencia', 'N/A') or 'N/A'

            output.write(f"{lanc['data']},{lanc['tipo']},{recorrencia},{categoria_nome},{lanc.get('descricao', '')},{lanc['valor']}\n")

        csv_content = output.getvalue()
        output.close()

        return Response(
            content=csv_content.encode('utf-8-sig'),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=financeiro_{periodo}.csv"}
        )
    except Exception as e:
        logger.error(f"Erro ao exportar CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========== TAXAS ==========

@app.get("/api/financeiro/taxas")
async def listar_taxas_financeiras(ativo: bool = None):
    """Lista todas as taxas"""
    try:
        taxas = await financeiro.listar_taxas(ativo)
        return {"taxas": taxas}
    except Exception as e:
        logger.error(f"Erro ao listar taxas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/financeiro/taxas")
async def criar_taxa_financeira(request: Request):
    """Cria nova taxa"""
    try:
        data = await request.json()

        nome = data.get('nome')
        percentual = data.get('percentual')
        aplica_sobre = data.get('aplica_sobre', 'receita_bruta')

        # Validações
        if not nome:
            raise HTTPException(status_code=422, detail="nome é obrigatório")
        if not percentual or percentual <= 0:
            raise HTTPException(status_code=422, detail="percentual deve ser maior que 0")
        if aplica_sobre not in ['receita_bruta', 'receita_liquida']:
            raise HTTPException(status_code=422, detail="aplica_sobre deve ser 'receita_bruta' ou 'receita_liquida'")

        taxa = await financeiro.criar_taxa(nome, percentual, aplica_sobre)
        return taxa
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar taxa: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/financeiro/taxas/{taxa_id}")
async def editar_taxa_financeira(taxa_id: int, dados: Dict[str, Any]):
    """Edita taxa existente"""
    try:
        taxa = await financeiro.editar_taxa(taxa_id, dados)
        return taxa
    except Exception as e:
        logger.error(f"Erro ao editar taxa: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/financeiro/taxas/{taxa_id}")
async def deletar_taxa_financeira(taxa_id: int):
    """Deleta taxa (soft delete)"""
    try:
        await financeiro.deletar_taxa(taxa_id)
        return {"success": True, "message": "Taxa deletada"}
    except Exception as e:
        logger.error(f"Erro ao deletar taxa: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========== METAS ==========

@app.get("/api/financeiro/metas")
async def listar_metas_financeiras(ativo: bool = None):
    """Lista todas as metas"""
    try:
        metas = await financeiro.listar_metas(ativo)
        return {"metas": metas}
    except Exception as e:
        logger.error(f"Erro ao listar metas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/financeiro/metas/progresso")
async def progresso_metas_financeiras():
    """Calcula progresso de todas as metas ativas"""
    try:
        progresso = await financeiro.calcular_progresso_metas()
        return {"metas": progresso}
    except Exception as e:
        logger.error(f"Erro ao calcular progresso metas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/financeiro/metas")
async def criar_meta_financeira(request: Request):
    """Cria nova meta"""
    try:
        data = await request.json()

        nome = data.get('nome')
        tipo = data.get('tipo')
        valor_objetivo = data.get('valor_objetivo')
        periodo_inicio = data.get('periodo_inicio')
        periodo_fim = data.get('periodo_fim')

        # Validações
        if not nome:
            raise HTTPException(status_code=422, detail="nome é obrigatório")
        if not tipo:
            raise HTTPException(status_code=422, detail="tipo é obrigatório")
        if tipo not in ['receita', 'lucro_liquido']:
            raise HTTPException(status_code=422, detail="tipo deve ser 'receita' ou 'lucro_liquido'")
        if not valor_objetivo or valor_objetivo <= 0:
            raise HTTPException(status_code=422, detail="valor_objetivo deve ser maior que 0")
        if not periodo_inicio:
            raise HTTPException(status_code=422, detail="periodo_inicio é obrigatório")
        if not periodo_fim:
            raise HTTPException(status_code=422, detail="periodo_fim é obrigatório")

        meta = await financeiro.criar_meta(nome, tipo, valor_objetivo, periodo_inicio, periodo_fim)
        return meta
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar meta: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/financeiro/metas/{meta_id}")
async def editar_meta_financeira(meta_id: int, dados: Dict[str, Any]):
    """Edita meta existente"""
    try:
        meta = await financeiro.editar_meta(meta_id, dados)
        return meta
    except Exception as e:
        logger.error(f"Erro ao editar meta: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/financeiro/metas/{meta_id}")
async def deletar_meta_financeira(meta_id: int):
    """Deleta meta (soft delete)"""
    try:
        await financeiro.deletar_meta(meta_id)
        return {"success": True, "message": "Meta deletada"}
    except Exception as e:
        logger.error(f"Erro ao deletar meta: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========== OVERVIEW / DASHBOARD ==========

@app.get("/api/financeiro/overview")
async def overview_financeiro(periodo: str = "30d"):
    """
    Retorna overview completo:
    - Receita bruta
    - Despesas (total + breakdown fixas/únicas)
    - Taxas totais
    - Lucro líquido
    - Comparação com período anterior
    """
    try:
        overview = await financeiro.get_overview(periodo)
        return overview
    except Exception as e:
        logger.error(f"Erro ao gerar overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/financeiro/taxa-cambio")
async def taxa_cambio_atual():
    """
    Retorna taxa de câmbio USD-BRL atual
    Exemplo: {"taxa": 5.52, "atualizado_em": "2025-12-17 15:35:03"}
    """
    try:
        from financeiro import get_usd_brl_rate
        taxa = await get_usd_brl_rate()
        return taxa
    except Exception as e:
        logger.error(f"Erro ao buscar taxa de câmbio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/financeiro/graficos/receita-despesas")
async def grafico_receita_despesas(periodo: str = "30d"):
    """
    Dados para gráfico de linha: receita vs despesas vs lucro
    """
    try:
        dados = await financeiro.get_grafico_receita_despesas(periodo)
        return {"dados": dados}
    except Exception as e:
        logger.error(f"Erro ao gerar gráfico receita/despesas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/financeiro/graficos/despesas-breakdown")
async def grafico_despesas_breakdown(periodo: str = "30d"):
    """
    Dados para gráfico pizza/barras: breakdown de despesas
    - Por categoria
    - Fixas vs Únicas
    """
    try:
        dados = await financeiro.get_grafico_despesas_breakdown(periodo)
        return dados
    except Exception as e:
        logger.error(f"Erro ao gerar gráfico breakdown: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========== INTEGRAÇÃO YOUTUBE ==========

@app.get("/api/financeiro/youtube-revenue")
async def youtube_revenue_financeiro(periodo: str = "30d"):
    """Consulta receita YouTube do período"""
    try:
        revenue = await financeiro.get_youtube_revenue(periodo)
        return {"receita_youtube": revenue, "periodo": periodo}
    except Exception as e:
        logger.error(f"Erro ao consultar receita YouTube: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/financeiro/projecao-mes")
async def projecao_mes_financeiro():
    """Retorna projeção de receita para o mês atual"""
    try:
        projecao = await financeiro.get_projecao_mes()
        return projecao
    except Exception as e:
        logger.error(f"Erro ao calcular projeção: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/financeiro/comparacao-mensal")
async def comparacao_mensal_financeiro(meses: int = 6):
    """Retorna comparação mês a mês dos últimos N meses"""
    try:
        comparacao = await financeiro.get_comparacao_mensal(meses)
        return {"meses": comparacao}
    except Exception as e:
        logger.error(f"Erro ao consultar receita YouTube: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/financeiro/sync-youtube")
async def sync_youtube_financeiro(periodo: str = "90d"):
    """
    Sincroniza receita YouTube:
    - Consulta yt_daily_metrics
    - Agrupa por mês
    - Cria lançamentos automáticos
    """
    try:
        resultado = await financeiro.sync_youtube_revenue(periodo)
        return resultado
    except Exception as e:
        logger.error(f"Erro ao sincronizar YouTube: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# 📤 YOUTUBE UPLOAD AUTOMATION
# ========================================

class WebhookUploadRequest(BaseModel):
    """Request do webhook da planilha Google Sheets"""
    video_url: str
    titulo: str
    descricao: str  # COM hashtags
    channel_id: str
    subnicho: str
    lingua: Optional[str] = None
    nome_canal: Optional[str] = None
    sheets_row: int
    spreadsheet_id: str

async def process_upload_task(upload_id: int, max_retries=3):
    """
    Processa upload com retry automático e controle de concorrência.

    - Máximo 3 uploads simultâneos (semaphore)
    - Até 3 tentativas em caso de falha
    - Aguarda: 15s entre tentativa 1→2, 30s entre tentativa 2→3
    """

    # Aguarda se já tiver 3 uploads rodando (controle de concorrência)
    async with upload_semaphore:

        for attempt in range(1, max_retries + 1):
            try:
                # Busca dados do upload
                upload = get_upload_by_id(upload_id)

                if not upload:
                    logger.error(f"Upload {upload_id} não encontrado no banco")
                    return

                channel_id = upload['channel_id']
                logger.info(f"[{channel_id}] 📤 Tentativa {attempt}/{max_retries} (upload_id: {upload_id})")

                # Atualiza retry_count se retry
                if attempt > 1:
                    supabase.table('yt_upload_queue')\
                        .update({
                            'retry_count': attempt,
                            'last_retry_at': datetime.now(timezone.utc).isoformat()
                        })\
                        .eq('id', upload_id)\
                        .execute()
                    logger.info(f"[{channel_id}] 🔄 Retry #{attempt} após falha anterior")

                # FASE 1: Download
                update_upload_status(upload_id, 'downloading')
                logger.info(f"[{channel_id}] 📥 Baixando vídeo do Drive...")
                video_path = uploader.download_video(upload['video_url'], channel_id=channel_id)

                # FASE 2: Upload
                update_upload_status(upload_id, 'uploading')
                logger.info(f"[{channel_id}] ⬆️  Fazendo upload para YouTube...")

                result = uploader.upload_to_youtube(
                    channel_id=upload['channel_id'],
                    video_path=video_path,
                    metadata={
                        'titulo': upload['titulo'],
                        'descricao': upload['descricao']  # COM #hashtags
                    }
                )

                # FASE 3: Sucesso
                update_upload_status(
                    upload_id,
                    'completed',
                    youtube_video_id=result['video_id']
                )

                # FASE 4: Atualiza planilha Google Sheets
                logger.info(f"[{channel_id}] 📊 Atualizando planilha (row {upload['sheets_row_number']})")
                update_upload_status_in_sheet(
                    spreadsheet_id=upload['spreadsheet_id'],
                    row=upload['sheets_row_number'],
                    status='✅ done'
                )
                logger.info(f"[{channel_id}] ✅ Planilha atualizada: ✅ done")

                # FASE 5: Cleanup
                uploader.cleanup(video_path)

                logger.info(f"[{channel_id}] ✅ Upload completo na tentativa {attempt} (video_id: {result['video_id']})")
                return  # Sucesso - sai do loop

            except Exception as e:
                logger.error(f"[{channel_id}] ❌ Erro na tentativa {attempt}/{max_retries}: {e}")

                # Se última tentativa, marca como failed
                if attempt == max_retries:
                    error_msg = f"Falhou após {max_retries} tentativas: {str(e)}"
                    logger.error(f"[{channel_id}] 💔 {error_msg}")

                    update_upload_status(
                        upload_id,
                        'failed',
                        error_message=error_msg,
                        retry_count=attempt
                    )

                    # Atualiza planilha com erro
                    try:
                        if upload and upload.get('spreadsheet_id') and upload.get('sheets_row_number'):
                            logger.info(f"[{channel_id}] 📊 Planilha atualizada: ❌ Erro")
                            update_upload_status_in_sheet(
                                spreadsheet_id=upload['spreadsheet_id'],
                                row=upload['sheets_row_number'],
                                status='❌ Erro'
                            )
                    except Exception as sheet_error:
                        logger.error(f"[{channel_id}] ⚠️ Erro ao atualizar planilha: {sheet_error}")

                    # Cleanup se arquivo existe
                    try:
                        if 'video_path' in locals():
                            uploader.cleanup(video_path)
                    except:
                        pass

                else:
                    # Não é última tentativa - aguarda antes do retry
                    wait_time = 15 if attempt == 1 else 30  # 15s entre 1→2, 30s entre 2→3
                    logger.info(f"[{channel_id}] ⏳ Aguardando {wait_time}s antes do retry #{attempt+1}...")
                    await asyncio.sleep(wait_time)

@app.post("/api/yt-upload/webhook")
async def webhook_new_video(
    request: WebhookUploadRequest,
    background_tasks: BackgroundTasks
):
    """
    Recebe webhook da planilha Google Sheets quando adiciona novo vídeo.
    Adiciona na fila e inicia processamento em background.
    """
    try:
        logger.info(f"📩 Webhook recebido: {request.titulo[:50]}...")

        # Cria upload na fila
        upload = create_upload(
            channel_id=request.channel_id,
            video_url=request.video_url,
            titulo=request.titulo,  # EXATO da planilha
            descricao=request.descricao,  # EXATO da planilha (COM #hashtags)
            subnicho=request.subnicho,
            sheets_row=request.sheets_row,
            spreadsheet_id=request.spreadsheet_id
        )

        # Agenda processamento em background
        background_tasks.add_task(process_upload_task, upload['id'])

        return {
            'success': True,
            'upload_id': upload['id'],
            'message': 'Upload adicionado na fila'
        }

    except Exception as e:
        logger.error(f"Erro webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/yt-upload/status/{upload_id}")
async def get_upload_status(upload_id: int):
    """Consulta status de um upload específico"""
    upload = get_upload_by_id(upload_id)

    if not upload:
        raise HTTPException(status_code=404, detail="Upload não encontrado")

    return upload

@app.get("/api/yt-upload/recent")
async def get_recent_uploads(limit: int = 50):
    """Lista uploads recentes (para dashboard)"""
    result = supabase.table('yt_upload_queue')\
        .select('*')\
        .order('created_at', desc=True)\
        .limit(limit)\
        .execute()

    return result.data

@app.get("/api/yt-upload/queue")
async def get_queue_status():
    """Status geral da fila de uploads"""

    # Conta por status
    pending = supabase.table('yt_upload_queue')\
        .select('*', count='exact')\
        .eq('status', 'pending')\
        .execute()

    processing = supabase.table('yt_upload_queue')\
        .select('*', count='exact')\
        .in_('status', ['downloading', 'uploading'])\
        .execute()

    completed = supabase.table('yt_upload_queue')\
        .select('*', count='exact')\
        .eq('status', 'completed')\
        .execute()

    failed = supabase.table('yt_upload_queue')\
        .select('*', count='exact')\
        .eq('status', 'failed')\
        .execute()

    return {
        'pending': pending.count or 0,
        'processing': processing.count or 0,
        'completed': completed.count or 0,
        'failed': failed.count or 0
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

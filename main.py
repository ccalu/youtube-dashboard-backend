from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
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
from comments_logs import CommentsLogsManager
from monetization_endpoints import router as monetization_router
from financeiro import FinanceiroService
from analytics import ChannelAnalytics

# Sistema de Agentes Inteligentes
from agents_endpoints import init_agents_router

# Sistema de Calendário Empresarial
from calendar_endpoints import init_calendar_router

# YouTube Uploader
from _features.yt_uploader.uploader import YouTubeUploader
from _features.yt_uploader.database import (
    create_upload,
    update_upload_status,
    get_upload_by_id,
    supabase
)
from _features.yt_uploader.sheets import update_upload_status_in_sheet

# Daily Upload Automation
from daily_uploader import schedule_daily_uploader, SPREADSHEET_CACHE

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
# 💾 SISTEMA DE CACHE 24H PARA DASHBOARD
# ========================================
import hashlib
from functools import wraps
import json

# Cache global com TTL de 6 horas
dashboard_cache = {}
CACHE_DURATION = timedelta(hours=6)  # Cache de 6 horas (atualiza 4x por dia)

# Cache específico para comentários - 5 minutos (atualiza frequentemente)
comments_cache = {}
COMMENTS_CACHE_DURATION = timedelta(minutes=5)

def get_cache_key(endpoint: str, params: dict = None) -> str:
    """
    Gera chave única para o cache baseada no endpoint e parâmetros.

    Args:
        endpoint: Nome do endpoint
        params: Parâmetros da requisição

    Returns:
        Hash MD5 único para identificar o cache
    """
    params = params or {}
    # Ordenar parâmetros para garantir consistência
    param_str = json.dumps(sorted(params.items()) if params else [], sort_keys=True)
    cache_str = f"{endpoint}:{param_str}"
    return hashlib.md5(cache_str.encode()).hexdigest()

def get_cached_response(cache_key: str) -> Optional[Any]:
    """
    Busca resposta no cache se ainda válida.

    Args:
        cache_key: Chave do cache

    Returns:
        Dados do cache ou None se expirado/inexistente
    """
    if cache_key in dashboard_cache:
        cached_data, cached_time = dashboard_cache[cache_key]
        now = datetime.now(timezone.utc)

        # Verificar se cache ainda é válido (24h)
        if now - cached_time < CACHE_DURATION:
            age_minutes = int((now - cached_time).total_seconds() / 60)
            logger.info(f"⚡ Cache hit! Servindo instantâneo (idade: {age_minutes} min)")
            return cached_data
        else:
            # Cache expirado, remover
            del dashboard_cache[cache_key]
            logger.info(f"⏰ Cache expirado (> 24h), buscando novo...")

    return None

def save_to_cache(cache_key: str, data: Any) -> None:
    """
    Salva dados no cache com timestamp.

    Args:
        cache_key: Chave do cache
        data: Dados a serem cacheados
    """
    dashboard_cache[cache_key] = (data, datetime.now(timezone.utc))
    logger.info(f"💾 Dados salvos no cache por 24h (key: {cache_key[:8]}...)")

def clear_all_cache() -> dict:
    """
    Limpa todo o cache do dashboard.
    Chamado após coleta diária às 5h.

    Returns:
        Estatísticas do cache limpo
    """
    cache_count = len(dashboard_cache)
    cache_size = sum(len(str(v[0])) for v in dashboard_cache.values())
    dashboard_cache.clear()

    logger.info(f"🧹 Cache limpo: {cache_count} entradas, ~{cache_size/1024:.1f}KB liberados")
    return {
        "entries_cleared": cache_count,
        "approx_size_kb": round(cache_size/1024, 1)
    }

def cache_endpoint(endpoint_name: str):
    """
    Decorator para adicionar cache automático a endpoints.

    Args:
        endpoint_name: Nome do endpoint para logging

    Usage:
        @cache_endpoint("canais")
        async def get_canais(...):
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Gerar chave do cache baseada nos parâmetros
            cache_params = {k: str(v) for k, v in kwargs.items() if v is not None}
            cache_key = get_cache_key(endpoint_name, cache_params)

            # Tentar buscar do cache
            cached_data = get_cached_response(cache_key)
            if cached_data is not None:
                return cached_data

            # Cache miss - buscar dados frescos
            logger.info(f"📊 Cache miss para {endpoint_name} - buscando dados...")
            start_time = time.time()

            # Executar função original
            result = await func(*args, **kwargs)

            # Salvar no cache
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.info(f"✅ Dados obtidos em {elapsed_ms}ms")
            save_to_cache(cache_key, result)

            return result
        return wrapper
    return decorator

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
# MODELOS DO SISTEMA KANBAN
# ========================================

class KanbanMoveStatusRequest(BaseModel):
    new_status: str

class KanbanNoteRequest(BaseModel):
    note_text: str
    note_color: str = "yellow"
    coluna_id: Optional[str] = None  # Campo para permitir notas em qualquer coluna

class KanbanNoteUpdateRequest(BaseModel):
    note_text: Optional[str] = None
    note_color: Optional[str] = None
    coluna_id: Optional[str] = None  # Permite mover nota entre colunas

class KanbanReorderNotesRequest(BaseModel):
    note_positions: List[Dict[str, int]]

class KanbanMoveNoteRequest(BaseModel):
    """Request para mover uma nota para outra coluna"""
    stage_id: Optional[str] = None  # Compatibilidade com Lovable
    coluna_id: Optional[str] = None  # Nome usado no backend

    @property
    def target_column(self) -> Optional[str]:
        """Retorna o ID da coluna de destino (aceita ambos os nomes)"""
        return self.stage_id or self.coluna_id

# ========================================
# INICIALIZAÇÃO
# ========================================

db = SupabaseClient()
collector = YouTubeCollector()
notifier = NotificationChecker(db.supabase)
financeiro = FinanceiroService(db)
uploader = YouTubeUploader()

# Sistema de Agentes Inteligentes
try:
    agents_router = init_agents_router(db, collector)
    app.include_router(agents_router)
    logger.info("Sistema de Agentes Inteligentes inicializado com sucesso!")
except Exception as e:
    logger.warning(f"Sistema de Agentes nao inicializado: {e}")

# Sistema de Calendário Empresarial
try:
    calendar_router = init_calendar_router(db)
    app.include_router(calendar_router)
    logger.info("✅ Sistema de Calendário Empresarial inicializado com sucesso!")
except Exception as e:
    logger.warning(f"❌ Sistema de Calendário não inicializado: {e}")

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
        # Para requests simples (só tipo/subnicho/lingua), usar cache + MV
        if (not views_30d_min and not views_15d_min and not views_7d_min and
            not score_min and not growth_min and not nicho):

            # Gerar chave do cache
            cache_key = get_cache_key("canais", {
                "tipo": tipo,
                "subnicho": subnicho,
                "lingua": lingua,
                "limit": limit,
                "offset": offset
            })

            # Tentar buscar do cache
            cached_data = get_cached_response(cache_key)
            if cached_data is not None:
                return cached_data

            # Cache miss - buscar da MV otimizada
            logger.info(f"📊 Buscando dados da MV para /api/canais...")
            start_time = time.time()

            # Usar nova função otimizada com MV
            canais = await db.get_dashboard_from_mv(
                tipo=tipo,
                subnicho=subnicho,
                lingua=lingua,
                limit=limit,
                offset=offset
            )

            result = {"canais": canais, "total": len(canais)}

            # Salvar no cache
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.info(f"✅ Dados obtidos em {elapsed_ms}ms")
            save_to_cache(cache_key, result)

            return result

        else:
            # Para filtros complexos, usar método tradicional (sem cache por enquanto)
            logger.info("🔍 Filtros complexos detectados, usando método tradicional...")
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

    🚀 OTIMIZADO: Usa cache de 24h + Materialized View
    """
    try:
        # Gerar chave do cache
        cache_key = get_cache_key("canais-tabela", {})

        # Tentar buscar do cache
        cached_data = get_cached_response(cache_key)
        if cached_data is not None:
            return cached_data

        # Cache miss - buscar dados
        logger.info("📊 Buscando canais para aba Tabela...")
        start_time = time.time()

        # Buscar todos os nossos canais usando MV otimizada
        canais = await db.get_dashboard_from_mv(
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
            inscritos = canal['inscritos'] or 0  # FIX: None → 0

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

        result = {
            "grupos": grupos_ordenados,
            "total_canais": len(canais),
            "total_subnichos": len(grupos_ordenados)
        }

        # Salvar no cache
        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.info(f"✅ Dados processados em {elapsed_ms}ms")
        save_to_cache(cache_key, result)

        return result

    except Exception as e:
        logger.error(f"Error fetching canais tabela: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# =========================================================================
# ENDPOINT DE DIAGNÓSTICO - Canais Problemáticos
# Added by Claude Code - 2026-01-17
# =========================================================================

@app.get("/api/canais/problematicos")
async def get_canais_problematicos():
    """
    🔍 Retorna canais com falhas de coleta.

    Útil para diagnóstico e identificação de canais que precisam de atenção.
    Ordenados por quantidade de falhas consecutivas (mais problemáticos primeiro).

    Returns:
        - total: número de canais com problemas
        - canais: lista com detalhes de cada canal problemático
            - id, nome_canal, url_canal, subnicho, tipo
            - coleta_falhas_consecutivas: quantas vezes consecutivas falhou
            - coleta_ultimo_erro: mensagem do último erro
            - coleta_ultimo_sucesso: última coleta bem-sucedida
            - ultima_coleta: timestamp da última tentativa
    """
    try:
        canais = await db.get_canais_problematicos()
        return {
            "total": len(canais),
            "canais": canais
        }
    except Exception as e:
        logger.error(f"Error fetching canais problemáticos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/canais/sem-coleta-recente")
async def get_canais_sem_coleta_recente(dias: int = 3):
    """
    🔍 Retorna canais que não tiveram coleta bem-sucedida nos últimos X dias.

    Args:
        dias: Número de dias para considerar "sem coleta recente" (default: 3)

    Returns:
        - total: número de canais sem coleta recente
        - canais: lista com detalhes de cada canal
    """
    try:
        canais = await db.get_canais_sem_coleta_recente(dias)
        return {
            "total": len(canais),
            "dias_limite": dias,
            "canais": canais
        }
    except Exception as e:
        logger.error(f"Error fetching canais sem coleta recente: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/canais/{canal_id}/analytics")
async def get_canal_analytics(canal_id: int):
    """
    📊 Retorna análise completa de um canal com insights inteligentes.

    Inclui:
    - Informações básicas expandidas (data criação, custom URL, etc)
    - Métricas de performance (views, engagement, score)
    - Top 10 vídeos com thumbnails
    - Padrões de sucesso identificados estatisticamente
    - Clustering de conteúdo por tema/performance
    - Detecção de anomalias (outliers, tendências)
    - Melhor dia/hora para postar

    Returns:
        JSON com análise completa do canal
    """
    try:
        # Criar instância do analisador
        analyzer = ChannelAnalytics(db)

        # Executar análise completa
        analytics_data = await analyzer.analyze_channel(canal_id)

        if not analytics_data:
            raise HTTPException(
                status_code=404,
                detail=f"Canal {canal_id} não encontrado ou sem dados para análise"
            )

        # Atualizar campos de analytics no banco se houver dados novos
        if analytics_data.get('canal_info'):
            info = analytics_data['canal_info']
            if info.get('criado_em') or info.get('custom_url'):
                await db.update_canal_analytics_fields(canal_id, {
                    'published_at': info.get('criado_em'),
                    'custom_url': info.get('custom_url'),
                    'video_count': info.get('total_videos')
                })

        # Atualizar melhor momento no banco
        if analytics_data.get('melhor_momento'):
            momento = analytics_data['melhor_momento']
            if momento.get('dia_numero') is not None and momento.get('hora') is not None:
                await db.supabase.table('canais_monitorados').update({
                    'melhor_dia_semana': momento['dia_numero'],
                    'melhor_hora': momento['hora']
                }).eq('id', canal_id).execute()

        logger.info(f"✅ Analytics gerado para canal {canal_id}")

        return analytics_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao gerar analytics para canal {canal_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def safe_days_diff(date_str: str) -> int:
    """
    Calcula diferença em dias entre agora e uma data, com tratamento seguro de timezone.

    Args:
        date_str: String de data em formato ISO (com ou sem timezone)

    Returns:
        Número de dias de diferença ou 0 se houver erro
    """
    try:
        if not date_str:
            return 0

        # Garantir que temos datetime.now com timezone UTC
        now_utc = datetime.now(timezone.utc)

        # Tentar parsear a data
        if 'T' in date_str:
            # Formato ISO com tempo
            if date_str.endswith('Z'):
                # Z significa UTC - converter para +00:00
                date_str = date_str.replace('Z', '+00:00')

            # Parse da data
            target_date = datetime.fromisoformat(date_str)

            # Se não tem timezone (naive), assumir UTC
            if target_date.tzinfo is None:
                target_date = target_date.replace(tzinfo=timezone.utc)

        else:
            # Formato sem tempo - assumir início do dia em UTC
            target_date = datetime.fromisoformat(date_str + 'T00:00:00+00:00')

        # Calcular diferença
        delta = now_utc - target_date
        return delta.days

    except Exception as e:
        logger.debug(f"Erro ao calcular diferença de dias para '{date_str}': {e}")
        return 0


@app.get("/api/canais/{canal_id}/engagement")
async def get_canal_engagement(canal_id: int, page: int = 1, limit: int = 10):
    """
    💬 Retorna análise completa de engajamento (comentários) de um canal.

    APENAS para canais tipo="nosso" (canais próprios).

    Organizado por vídeo com:
    - Comentários traduzidos para PT-BR
    - Análise de sentimento
    - Detecção de problemas (áudio, vídeo, conteúdo)
    - Insights acionáveis
    - Separação entre positivos e negativos

    Returns:
        JSON com análise de comentários organizada por vídeo
    """
    try:
        # ========== VALIDAÇÃO: APENAS CANAIS "NOSSOS" ==========
        canal_response = db.supabase.table("canais_monitorados")\
            .select("id, tipo, nome_canal")\
            .eq("id", canal_id)\
            .execute()

        if not canal_response.data:
            raise HTTPException(status_code=404, detail="Canal não encontrado")

        canal = canal_response.data[0]

        # Verificar se é tipo="nosso"
        if canal.get('tipo') != 'nosso':
            raise HTTPException(
                status_code=403,
                detail="Análise de comentários disponível apenas para canais próprios. Este é um canal minerado de referência."
            )

        logger.info(f"✅ Buscando engagement do canal próprio: {canal.get('nome_canal')} (ID: {canal_id})")

        # PRIMEIRO: Tentar buscar do cache
        from engagement_preprocessor import EngagementPreprocessor
        preprocessor = EngagementPreprocessor(db)
        engagement_data = await preprocessor.get_cached_engagement(canal_id)

        # Se não tem cache válido, buscar dados em tempo real
        if not engagement_data:
            logger.info(f"⚠️ Cache miss para canal {canal_id}, buscando dados em tempo real...")
            engagement_data = await db.get_canal_engagement_data(canal_id)
        else:
            logger.info(f"✅ Usando cache para canal {canal_id} (processado em {engagement_data.get('_cache_metadata', {}).get('processing_time_ms', 0)}ms)")

        # Se não há dados ainda, organizar resposta vazia estruturada
        if not engagement_data or engagement_data['summary']['total_comments'] == 0:

            # Buscar vídeos do canal para estruturar resposta
            videos = await db.get_videos_by_canal(canal_id, limit=20)

            videos_data = []
            for video in videos:
                videos_data.append({
                    'video_id': video.get('video_id'),
                    'video_title': video.get('titulo', ''),
                    'published_days_ago': safe_days_diff(video.get('data_publicacao', '')),
                    'views': video.get('views_atuais', 0),
                    'total_comments': 0,
                    'positive_count': 0,
                    'negative_count': 0,
                    'has_problems': False,
                    'problem_count': 0,
                    'sentiment_score': 0,
                    'positive_comments': [],
                    'negative_comments': []
                })

            return {
                'summary': {
                    'total_comments': 0,
                    'positive_count': 0,
                    'negative_count': 0,
                    'positive_pct': 0,
                    'negative_pct': 0,
                    'actionable_count': 0,
                    'problems_count': 0
                },
                'videos': videos_data[:10],  # Top 10 vídeos
                'problems_grouped': {
                    'audio': [],
                    'video': [],
                    'content': [],
                    'technical': []
                },
                'message': 'Ainda não há comentários coletados para este canal. Execute a coleta de comentários para ver análises.'
            }

        # Processar dados dos vídeos com paginação
        videos_list = engagement_data.get('videos_summary', [])

        # Buscar dados completos dos vídeos (views, título, data de publicação)
        # Isso garante que temos as informações reais mesmo quando os comentários não trazem tudo
        video_ids = [v.get('video_id') for v in videos_list if v.get('video_id')]
        videos_from_db = []
        if video_ids:
            # Buscar vídeos do canal para obter views, título e data de publicação
            # Removido limite para garantir que pegamos TODOS os vídeos
            videos_from_db = await db.get_videos_by_canal(canal_id, limit=None)

        # Criar mapa de vídeos para acesso rápido (mapear TODOS, sem filtro)
        videos_map = {}
        for video in videos_from_db:
            video_id = video.get('video_id')
            if video_id:  # Apenas verificar se tem ID
                videos_map[video_id] = video

        # Aplicar paginação
        offset = (page - 1) * limit
        videos_paginated = videos_list[offset:offset + limit]

        # Formatar dados dos vídeos para o frontend
        videos_data = []
        for video_data in videos_paginated:
            # Obter dados reais do vídeo do mapa
            video_id = video_data.get('video_id')
            video_info = videos_map.get(video_id, {})

            # Separar comentários positivos e negativos do vídeo
            video_comments = video_data.get('comments', [])

            # Garantir que cada comentário tenha os campos obrigatórios
            formatted_comments = []
            for comment in video_comments:
                # Priorizar texto traduzido, depois original
                comment_text = (
                    comment.get('comment_text_pt') or  # Primeiro: tradução
                    comment.get('comment_text_original') or  # Segundo: original
                    comment.get('comment_text', '') or  # Terceiro: fallback antigo
                    ''  # Último: string vazia
                )

                formatted_comment = {
                    'comment_id': comment.get('comment_id', ''),
                    'author_name': comment.get('author_name', ''),
                    'comment_text_pt': comment_text,  # Sempre enviar texto (traduzido ou original)
                    'comment_text_original': comment.get('comment_text_original', ''),
                    'is_translated': comment.get('is_translated', False),
                    'like_count': comment.get('like_count', 0),
                    'insight_text': comment.get('insight_text', ''),
                    'suggested_action': comment.get('suggested_action'),
                    'sentiment_category': comment.get('sentiment_category', ''),
                    'suggested_response': comment.get('suggested_response', '')  # Resposta sugerida do banco
                }
                formatted_comments.append(formatted_comment)

            # Ordenar todos os comentários por like_count (mais likes primeiro)
            formatted_comments.sort(key=lambda x: x.get('like_count', 0), reverse=True)

            # Arrays vazios para compatibilidade (Lovable pode estar esperando)
            positive_comments = []
            negative_comments = []
            neutral_comments = []

            # Log para debug
            if video_comments:
                logger.info(f"🔍 Engagement - Video {video_id}: {len(video_comments)} comentários totais")

            # Garantir que sempre tem um título válido
            # Prioridade: 1) videos_historico, 2) video_comments (se houver), 3) fallback genérico
            video_title = video_info.get('titulo', '').strip()

            if not video_title and video_comments:
                # Tentar buscar título do primeiro comentário (que tem video_title)
                first_comment_with_title = next((c for c in video_comments if c.get('video_title')), None)
                if first_comment_with_title:
                    video_title = first_comment_with_title.get('video_title', '').strip()

            if not video_title:
                video_title = video_data.get('video_title', '').strip()

            if not video_title and video_id:
                video_title = f"Vídeo {video_id[:8]}..."

            if not video_title:
                video_title = "Vídeo sem título"

            # UNIFICAÇÃO DE CONTAGENS: Buscar contagem do YouTube para comparação
            youtube_comment_count = video_info.get('comentarios', 0)  # Da tabela videos_historico
            analyzed_comment_count = len(formatted_comments)  # Comentários que analisamos
            coverage_pct = (analyzed_comment_count / youtube_comment_count * 100) if youtube_comment_count > 0 else 0

            videos_data.append({
                'video_id': video_id,
                'video_title': video_title,  # Sempre terá um título
                'published_days_ago': safe_days_diff(video_info.get('data_publicacao', '')),  # Calcula dias desde publicação
                'views': video_info.get('views_atuais', 0),  # Views reais do banco
                'total_comments': video_data.get('total_comments', 0),  # Mantido para compatibilidade
                # NOVO: Campos unificados de contagem
                'total_comments_youtube': youtube_comment_count,  # Contagem do YouTube (videos_historico)
                'total_comments_analyzed': analyzed_comment_count,  # Contagem analisada (video_comments)
                'coverage_pct': round(coverage_pct, 1),  # Porcentagem de cobertura
                'positive_count': 0,  # Removido análise de sentimentos
                'negative_count': 0,  # Removido análise de sentimentos
                'has_problems': False,  # Removido análise de sentimentos
                'problem_count': 0,  # Removido análise de sentimentos
                'sentiment_score': 0,  # Removido análise de sentimentos
                # Arrays para compatibilidade com frontend existente
                'positive_comments': positive_comments,  # Array vazio
                'negative_comments': negative_comments,  # Array vazio
                'neutral_comments': neutral_comments,  # Array vazio
                # NOVO: Array único com TODOS os comentários
                'all_comments': formatted_comments  # TODOS os comentários do vídeo (sem limite)
            })

        # Agrupar problemas por tipo (usando comentários com problema)
        problems_grouped = {
            'audio': [],
            'video': [],
            'content': [],
            'technical': []
        }

        # Contadores por tipo de problema
        actionable_breakdown = {
            'audio': 0,
            'video': 0,
            'content': 0,
            'technical': 0,
            'other': 0
        }

        # Vídeos que precisam de ação (com problemas)
        videos_needing_action = set()

        for comment in engagement_data.get('problem_comments', []):
            problem_type = comment.get('problem_type', 'other')
            video_title = comment.get('video_title', '')

            # Adicionar vídeo à lista de ação necessária
            if video_title:
                videos_needing_action.add(video_title)

            # Contar por tipo
            if problem_type in actionable_breakdown:
                actionable_breakdown[problem_type] += 1
            else:
                actionable_breakdown['other'] += 1

            # Adicionar ao grupo apropriado
            if problem_type in problems_grouped:
                problems_grouped[problem_type].append({
                    'video_title': video_title,
                    'author': comment.get('author_name', ''),
                    'text_pt': comment.get('comment_text_pt', comment.get('comment_text', '')),
                    'specific_issue': comment.get('problem_description', ''),
                    'suggested_action': comment.get('suggested_action', '')
                })

        # Calcular total de páginas
        total_videos = len(engagement_data.get('videos_summary', []))
        total_pages = (total_videos + limit - 1) // limit

        # Calcular totais de cobertura para o summary
        total_youtube_comments = sum(v['total_comments_youtube'] for v in videos_data)
        total_analyzed_comments = sum(v['total_comments_analyzed'] for v in videos_data)
        overall_coverage = (total_analyzed_comments / total_youtube_comments * 100) if total_youtube_comments > 0 else 0

        # Melhorar o summary com detalhes de actionable e cobertura
        enhanced_summary = engagement_data['summary'].copy()
        enhanced_summary['actionable_breakdown'] = actionable_breakdown
        enhanced_summary['videos_needing_action'] = list(videos_needing_action)
        enhanced_summary['videos_needing_action_count'] = len(videos_needing_action)
        # NOVO: Campos de cobertura unificados
        enhanced_summary['total_comments_youtube'] = total_youtube_comments
        enhanced_summary['total_comments_analyzed'] = total_analyzed_comments
        enhanced_summary['overall_coverage_pct'] = round(overall_coverage, 1)

        return {
            'summary': enhanced_summary,
            'videos': videos_data,  # Vídeos paginados com comentários
            'problems_grouped': problems_grouped,
            'pagination': {
                'page': page,
                'limit': limit,
                'total_videos': total_videos,
                'total_pages': total_pages
            }
        }

    except Exception as e:
        logger.error(f"❌ Erro ao buscar engagement do canal {canal_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ======== ENDPOINTS DE COMENTÁRIOS PARA FRONTEND ========

@app.get("/api/comentarios/monetizados")
async def get_monetized_channels_comments():
    """
    Lista canais monetizados com estatísticas de comentários.
    OTIMIZADO: Cache de 5 minutos + queries agregadas

    Returns:
        Lista de canais com total de comentários, vídeos e engagement
    """
    try:
        # Verificar cache
        cache_key = get_cache_key('comentarios_monetizados')
        if cache_key in comments_cache:
            cached_data, cached_time = comments_cache[cache_key]
            if datetime.now(timezone.utc) - cached_time < COMMENTS_CACHE_DURATION:
                logger.info("📦 Retornando canais monetizados do cache")
                return cached_data

        # Buscar dados (função otimizada com apenas 3 queries)
        result = db.get_monetized_channels_with_comments()

        # Salvar no cache
        comments_cache[cache_key] = (result, datetime.now(timezone.utc))
        logger.info(f"💾 Cache atualizado para canais monetizados: {len(result)} canais")

        return result
    except Exception as e:
        logger.error(f"Erro ao buscar canais monetizados: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/canais/{canal_id}/videos-com-comentarios")
async def get_canal_videos_with_comments(canal_id: int, limit: int = 50):
    """
    Lista vídeos de um canal com contagem de comentários.
    OTIMIZADO: Cache de 5 minutos + query única

    Args:
        canal_id: ID do canal
        limit: Número máximo de vídeos a retornar (padrão: 50)

    Returns:
        Lista de vídeos com estatísticas de comentários
    """
    try:
        # Verificar cache
        cache_key = get_cache_key('videos_comentarios', {'canal_id': canal_id, 'limit': limit})
        if cache_key in comments_cache:
            cached_data, cached_time = comments_cache[cache_key]
            if datetime.now(timezone.utc) - cached_time < COMMENTS_CACHE_DURATION:
                logger.info(f"📦 Retornando vídeos do canal {canal_id} do cache")
                return cached_data

        # Buscar dados (função otimizada com apenas 2 queries)
        result = db.get_videos_with_comments_count(canal_id, limit)

        # Salvar no cache
        comments_cache[cache_key] = (result, datetime.now(timezone.utc))
        logger.info(f"💾 Cache atualizado para vídeos do canal {canal_id}: {len(result)} vídeos")

        return result
    except Exception as e:
        logger.error(f"Erro ao buscar vídeos do canal {canal_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/videos/{video_id}/comentarios-paginados")
async def get_video_comments_paginated(video_id: str, page: int = 1, limit: int = 10):
    """
    Busca comentários de um vídeo com paginação.

    Args:
        video_id: ID do vídeo no YouTube
        page: Número da página (padrão: 1)
        limit: Comentários por página (padrão: 10)

    Returns:
        Comentários paginados com sugestões de resposta
    """
    try:
        result = db.get_video_comments_paginated(video_id, page, limit)
        return result
    except Exception as e:
        logger.error(f"Erro ao buscar comentários do vídeo {video_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/comentarios/{comment_id}/marcar-respondido")
async def mark_comment_responded(comment_id: int, body: dict = {}):
    """
    Marca um comentário como respondido.

    Args:
        comment_id: ID do comentário (database ID)
        body: JSON com 'actual_response' opcional

    Returns:
        Status da operação
    """
    try:
        actual_response = body.get('actual_response')
        success = db.mark_comment_as_responded(comment_id, actual_response)

        if success:
            return {"success": True, "message": "Comentário marcado como respondido"}
        else:
            raise HTTPException(status_code=404, detail="Comentário não encontrado")
    except Exception as e:
        logger.error(f"Erro ao marcar comentário {comment_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/comentarios/{comment_id}/gerar-resposta")
async def generate_comment_response(comment_id: int):
    """
    Gera resposta personalizada para um comentário específico.

    SISTEMA SIMPLIFICADO (03/02/2026):
    - Geração sob demanda
    - Resposta na mesma língua do comentário
    - Tom educado como dono do canal

    Args:
        comment_id: ID do comentário (database ID)

    Returns:
        JSON com resposta sugerida
    """
    logger.info("="*80)
    logger.info("🚨🚨🚨 ENDPOINT GERAR RESPOSTA CHAMADO! 🚨🚨🚨")
    logger.info(f"Comentário ID recebido: {comment_id}")
    logger.info(f"Tipo do ID: {type(comment_id)}")
    logger.info("="*80)

    try:
        # Buscar apenas o comentário (sem joins desnecessários)
        logger.info(f"Buscando comentário {comment_id} no banco...")
        comment = db.supabase.table('video_comments').select(
            'id, author_name, comment_text_original, comment_text_pt'
        ).eq('id', comment_id).execute()

        if not comment.data:
            logger.error(f"❌ Comentário {comment_id} não encontrado no banco")
            raise HTTPException(status_code=404, detail=f"Comentário {comment_id} não encontrado")

        comment_data = comment.data[0]
        logger.info(f"✅ Comentário encontrado! Autor: {comment_data.get('author_name', 'N/A')}")

        # Pegar o texto do comentário (preferir original para detectar idioma correto)
        comment_text = comment_data.get('comment_text_original') or comment_data.get('comment_text_pt')
        logger.info(f"📝 Texto do comentário ({len(comment_text) if comment_text else 0} chars): {comment_text[:100] if comment_text else 'VAZIO'}...")

        if not comment_text or not comment_text.strip():
            logger.error("❌ Comentário sem texto!")
            raise HTTPException(status_code=400, detail="Comentário sem texto para análise")

        # Verificar se OPENAI_API_KEY está configurada
        logger.info("🔑 Verificando OPENAI_API_KEY...")
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("❌ OPENAI_API_KEY não encontrada nas variáveis de ambiente")
            raise HTTPException(
                status_code=500,
                detail="OPENAI_API_KEY não está configurada no Railway. Adicione em Settings > Variables"
            )

        # Sanitizar API key: remover espaços, tabs, newlines, etc
        # Railway às vezes adiciona formatação às variáveis de ambiente
        api_key = api_key.strip().replace('\n', '').replace('\r', '').replace(' ', '').replace('\t', '')
        logger.info(f"✅ OPENAI_API_KEY encontrada e sanitizada: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else '***'}")

        # Prompt humanizado - resposta natural e genuína com contexto
        prompt = f"""You're responding to a YouTube comment on your channel.

BE HUMAN AND NATURAL:
- Sometimes 1 sentence is perfect (for simple thanks or acknowledgments)
- Sometimes 2-3 sentences work better (for questions or discussions)
- NEVER force long responses - be genuine
- Match the commenter's energy and tone
- Use the EXACT SAME LANGUAGE as the comment

HOW TO RESPOND:
- If it's praise/compliment: thank them genuinely
- If it's criticism: acknowledge it and be understanding
- If it's a question: answer it directly
- If it's a suggestion: consider it and thank them
- If it's just "Thanks!": a simple "You're welcome!" is perfect

Comment from {comment_data.get('author_name', 'User')}:
"{comment_text}"

Your natural response:"""

        # Chamar OpenAI API diretamente via HTTP (igual aos agents que funcionam!)
        try:
            logger.info(f"📤 Chamando OpenAI API diretamente via HTTP...")
            logger.info(f"   Modelo: gpt-4o-mini")
            logger.info(f"   Tamanho do comentário: {len(comment_text)} caracteres")

            import requests

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are a YouTube channel owner responding to comments. IMPORTANT: Always respond in the EXACT SAME LANGUAGE as the comment. Be natural and human - sometimes 1 sentence is perfect, sometimes 2-3 sentences work better. Never force long responses. Be genuine, not robotic."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }

            logger.info("🚀 Fazendo requisição HTTP para api.openai.com...")
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30  # 30 segundos como você pediu
            )

            if response.status_code == 200:
                result = response.json()
                suggested_response = result["choices"][0]["message"]["content"].strip()
                logger.info(f"✅ Resposta gerada com sucesso: {len(suggested_response)} caracteres")
            else:
                logger.error(f"❌ Erro da API OpenAI: Status {response.status_code}")
                logger.error(f"   Resposta: {response.text}")

                error_msg = f"Erro da OpenAI (Status {response.status_code})"
                if response.status_code == 401:
                    error_msg = "Chave da API inválida ou expirada"
                elif response.status_code == 429:
                    error_msg = "Limite de requisições excedido. Tente em alguns segundos"
                elif response.status_code == 500:
                    error_msg = "Erro interno da OpenAI. Tente novamente"

                raise HTTPException(status_code=500, detail=error_msg)

        except requests.exceptions.Timeout:
            logger.error("❌ Timeout na chamada para OpenAI (30 segundos)")
            raise HTTPException(
                status_code=500,
                detail="Timeout na comunicação com OpenAI. Tente novamente"
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erro de conexão com OpenAI: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Erro de conexão com OpenAI: {str(e)}"
            )
        except Exception as e:
            logger.error(f"❌ Erro inesperado: {type(e).__name__}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao gerar resposta: {str(e)}"
            )

        # Salvar resposta no banco
        db.supabase.table('video_comments').update({
            'suggested_response': suggested_response,
            'response_tone': 'friendly',
            'response_generated_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }).eq('id', comment_id).execute()

        return {
            "success": True,
            "suggested_response": suggested_response,
            "comment_text": comment_text,
            "response_generated_at": datetime.now(timezone.utc).isoformat()
        }

    except HTTPException as he:
        logger.error(f"❌ HTTPException capturada: {he.status_code} - {he.detail}")
        raise
    except Exception as e:
        logger.error("="*80)
        logger.error(f"❌❌❌ ERRO INESPERADO NO ENDPOINT! ❌❌❌")
        logger.error(f"Tipo: {type(e).__name__}")
        logger.error(f"Mensagem: {str(e)}")
        logger.error(f"Comentário ID: {comment_id}")
        logger.error("="*80)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/comentarios/resumo")
async def get_comments_summary():
    """
    Retorna resumo geral dos comentários.

    Returns:
        Estatísticas gerais dos comentários
    """
    try:
        result = db.get_comments_summary()
        return result
    except Exception as e:
        logger.error(f"Erro ao buscar resumo de comentários: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/test-openai")
async def test_openai_configuration():
    """
    Endpoint de diagnóstico para verificar configuração da OpenAI.
    Use para debugar problemas com geração de respostas.
    """
    diagnostico = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {}
    }

    # 1. Verificar se OPENAI_API_KEY existe
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        diagnostico["checks"]["api_key_exists"] = False
        diagnostico["error"] = "OPENAI_API_KEY não está configurada nas variáveis de ambiente"
        diagnostico["solution"] = "Adicione OPENAI_API_KEY no Railway em Settings > Variables"
        return diagnostico

    # Sanitizar API key: remover espaços, tabs, newlines, etc
    api_key = api_key.strip().replace('\n', '').replace('\r', '').replace(' ', '').replace('\t', '')

    diagnostico["checks"]["api_key_exists"] = True
    diagnostico["checks"]["api_key_format"] = f"{api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else '***'}"

    # 2. Verificar formato da chave
    if not api_key.startswith(("sk-", "sk-proj-")):
        diagnostico["checks"]["api_key_valid_format"] = False
        diagnostico["warning"] = "OPENAI_API_KEY não começa com 'sk-' ou 'sk-proj-'"
    else:
        diagnostico["checks"]["api_key_valid_format"] = True

    # 3. Tentar inicializar GPTAnalyzer
    try:
        from gpt_response_suggester import GPTAnalyzer
        analyzer = GPTAnalyzer()
        diagnostico["checks"]["gpt_analyzer_init"] = True
    except ImportError as e:
        diagnostico["checks"]["gpt_analyzer_init"] = False
        diagnostico["checks"]["import_error"] = str(e)
        diagnostico["error"] = "Não foi possível importar GPTAnalyzer"
        return diagnostico
    except Exception as e:
        diagnostico["checks"]["gpt_analyzer_init"] = False
        diagnostico["checks"]["init_error"] = f"{type(e).__name__}: {str(e)}"
        diagnostico["error"] = f"Erro ao inicializar GPTAnalyzer: {str(e)}"
        return diagnostico

    # 4. Fazer uma chamada de teste simples
    try:
        response = analyzer.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Responda apenas: OK"}
            ],
            max_tokens=10,
            temperature=0
        )
        test_response = response.choices[0].message.content.strip()
        diagnostico["checks"]["api_call_test"] = True
        diagnostico["checks"]["test_response"] = test_response
    except Exception as e:
        diagnostico["checks"]["api_call_test"] = False
        diagnostico["checks"]["api_error"] = f"{type(e).__name__}: {str(e)}"

        # Interpretar erro comum
        error_str = str(e).lower()
        if "api_key" in error_str or "authentication" in error_str:
            diagnostico["error"] = "Chave da API inválida ou expirada"
            diagnostico["solution"] = "Verifique se a chave está correta e ativa em https://platform.openai.com/api-keys"
        elif "rate" in error_str:
            diagnostico["error"] = "Limite de rate da API excedido"
            diagnostico["solution"] = "Aguarde alguns segundos e tente novamente"
        elif "quota" in error_str or "insufficient" in error_str:
            diagnostico["error"] = "Quota da OpenAI excedida ou créditos insuficientes"
            diagnostico["solution"] = "Verifique seu saldo em https://platform.openai.com/usage"
        else:
            diagnostico["error"] = f"Erro na API: {str(e)}"

    # 5. Resumo final
    all_checks_passed = all(
        v for k, v in diagnostico["checks"].items()
        if isinstance(v, bool) and not k.startswith("api_key_format")
    )

    if all_checks_passed:
        diagnostico["status"] = "✅ TUDO FUNCIONANDO"
        diagnostico["message"] = "OpenAI está configurada corretamente e funcionando"
    else:
        diagnostico["status"] = "❌ PROBLEMAS DETECTADOS"
        if "error" not in diagnostico:
            diagnostico["error"] = "Verifique os detalhes acima"

    return diagnostico


@app.post("/api/collect-comments/{canal_id}")
async def collect_canal_comments(canal_id: int, background_tasks: BackgroundTasks):
    """
    💬 Coleta comentários de todos os vídeos de um canal.

    APENAS para canais tipo="nosso" (canais próprios).

    Processo:
    1. Valida se canal é tipo="nosso"
    2. Busca últimos 20 vídeos do canal
    3. Coleta até 100 comentários por vídeo
    4. Analisa sentimento e detecta problemas
    5. Salva no banco de dados

    Returns:
        JSON com resumo da coleta
    """
    try:
        # ========== VALIDAÇÃO: APENAS CANAIS "NOSSOS" ==========
        canal_response = db.supabase.table("canais_monitorados")\
            .select("id, tipo, nome_canal, url_canal")\
            .eq("id", canal_id)\
            .execute()

        if not canal_response.data:
            raise HTTPException(status_code=404, detail="Canal não encontrado")

        canal = canal_response.data[0]

        # Verificar se é tipo="nosso"
        if canal.get('tipo') != 'nosso':
            logger.info(f"⏭️ Pulando coleta de comentários - Canal minerado: {canal.get('nome_canal')} (ID: {canal_id})")
            raise HTTPException(
                status_code=403,
                detail="Coleta de comentários disponível apenas para canais próprios. Este é um canal minerado de referência."
            )

        logger.info(f"🎯 Iniciando coleta de comentários do canal próprio: {canal.get('nome_canal')} (ID: {canal_id})")

        # Buscar vídeos do canal (TOP 20 mais recentes)
        videos_response = db.supabase.table("videos")\
            .select("video_id, titulo, views_atuais, data_publicacao")\
            .eq("canal_id", canal_id)\
            .order("data_publicacao", desc=True)\
            .limit(20)\
            .execute()

        logger.info(f"📹 Encontrados {len(videos_response.data) if videos_response.data else 0} vídeos para coletar comentários")

        if not videos_response.data:
            return {
                'success': True,
                'canal': canal.get('nome_canal'),
                'message': 'Canal não possui vídeos para coletar comentários',
                'total_videos': 0,
                'total_comments': 0
            }

        videos = videos_response.data
        logger.info(f"📹 {len(videos)} vídeos encontrados para coleta de comentários")

        # Extrair channel_id da URL
        url = canal.get('url_canal', '')
        channel_id = None
        if '@' in url:
            channel_id = url.split('@')[1].strip('/')
        elif '/channel/' in url:
            channel_id = url.split('/channel/')[1].split('/')[0]
        elif '/c/' in url:
            channel_id = url.split('/c/')[1].split('/')[0]

        if not channel_id:
            logger.error(f"❌ Não foi possível extrair channel_id da URL: {url}")
            raise HTTPException(status_code=400, detail="URL do canal inválida para coleta")

        # Coletar comentários
        from scripts.comentarios.comment_analyzer import CommentAnalyzer
        analyzer = CommentAnalyzer()

        comments_data = await collector.get_all_channel_comments(
            channel_id=channel_id,
            canal_name=canal.get('nome_canal'),
            videos=videos
        )

        total_comments = comments_data.get('total_comments', 0)
        comments_by_video = comments_data.get('comments_by_video', {})

        # Obter língua do canal
        canal_lingua = canal.get('lingua', '')

        # Analisar e salvar comentários por vídeo
        saved_count = 0
        for video_id, comments in comments_by_video.items():
            if comments:
                # Analisar lote de comentários
                analyzed_comments = await analyzer.analyze_comment_batch(comments)

                # Salvar no banco (passando a língua do canal)
                success = await db.save_video_comments(video_id, canal_id, analyzed_comments, canal_lingua)
                if success:
                    saved_count += len(analyzed_comments)

        logger.info(f"✅ Coleta concluída: {saved_count}/{total_comments} comentários salvos")

        # 🔄 TRADUÇÃO AUTOMÁTICA EM BACKGROUND
        if saved_count > 0:
            try:
                logger.info(f"🌐 Iniciando tradução automática de comentários em background...")
                background_tasks.add_task(traduzir_comentarios_canal, canal_id)
            except Exception as e:
                logger.warning(f"⚠️ Não foi possível iniciar tradução automática: {e}")

        return {
            'success': True,
            'canal': canal.get('nome_canal'),
            'canal_id': canal_id,
            'total_videos': len(videos),
            'total_coletados': total_comments,
            'comments_saved': saved_count,
            'message': f'Coleta concluída com sucesso! {saved_count} comentários analisados e salvos. Tradução iniciada em background.'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao coletar comentários do canal {canal_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/canais/{canal_id}/top-videos")
async def get_canal_top_videos(canal_id: int):
    """
    📺 Retorna os 5 vídeos mais vistos de um canal.

    Usado na aba "Top Videos" do modal de analytics.
    Ordenação por views_atuais (maior → menor).

    Args:
        canal_id: ID do canal

    Returns:
        {
            "canal_id": int,
            "canal_nome": str,
            "top_videos": [
                {
                    "video_id": str,
                    "titulo": str,
                    "url_video": str,
                    "url_thumbnail": str,  // calculado
                    "data_publicacao": str,
                    "views_atuais": int,
                    "likes": int,
                    "comentarios": int,
                    "duracao": int  // segundos
                }
            ]
        }
    """
    try:
        # Verificar se canal existe
        canal_response = db.supabase.table("canais_monitorados")\
            .select("id, nome_canal")\
            .eq("id", canal_id)\
            .execute()

        if not canal_response.data:
            raise HTTPException(status_code=404, detail="Canal não encontrado")

        canal = canal_response.data[0]

        logger.info(f"📺 Buscando top 5 vídeos do canal: {canal.get('nome_canal')} (ID: {canal_id})")

        # Buscar top 5 vídeos
        top_videos = await db.get_top_videos_by_canal(canal_id, limit=5)

        return {
            "canal_id": canal_id,
            "canal_nome": canal.get("nome_canal"),
            "top_videos": top_videos
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar top vídeos do canal {canal_id}: {e}")
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


@app.get("/api/comments/logs")
async def get_comments_logs(limit: int = 10):
    """
    📊 Retorna logs detalhados das coletas de comentários

    Args:
        limit: Número máximo de logs a retornar (default: 10)

    Returns:
        Lista de logs de coleta com detalhes de sucesso/erro
    """
    try:
        logs_manager = CommentsLogsManager()
        logs = logs_manager.get_latest_logs(limit=limit)

        return {
            "logs": logs,
            "total": len(logs)
        }
    except Exception as e:
        logger.error(f"Erro ao buscar logs de comentários: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/comments/logs/summary")
async def get_comments_logs_summary(days: int = 7):
    """
    📊 Retorna resumo estatístico dos logs de comentários

    Args:
        days: Número de dias para calcular o resumo (default: 7)

    Returns:
        Estatísticas agregadas das coletas de comentários
    """
    try:
        logs_manager = CommentsLogsManager()
        summary = logs_manager.get_logs_summary(days=days)

        # Adicionar canais problemáticos
        canais_problematicos = logs_manager.get_canais_com_mais_erros(limit=10)
        summary['canais_problematicos'] = canais_problematicos

        return summary
    except Exception as e:
        logger.error(f"Erro ao buscar resumo de logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/comments/logs/{collection_id}")
async def get_comment_log_by_id(collection_id: str):
    """
    📊 Retorna detalhes de um log específico de coleta

    Args:
        collection_id: ID da coleta

    Returns:
        Detalhes completos do log de coleta
    """
    try:
        logs_manager = CommentsLogsManager()
        log = logs_manager.get_log_by_id(collection_id)

        if not log:
            raise HTTPException(status_code=404, detail="Log não encontrado")

        return log
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar log por ID: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/comments/stats")
async def get_comments_stats():
    """
    📊 Retorna estatísticas completas dos comentários analisados com GPT.

    Inclui:
    - Total de comentários coletados e analisados
    - Distribuição de sentimentos
    - Comentários prioritários
    - Métricas de uso do GPT (tokens, custo, tempo)
    - Canais com mais engajamento

    Returns:
        JSON com estatísticas detalhadas
    """
    try:
        # Importar database_comments se ainda não foi importado
        from database_comments import CommentsDB
        from gpt_response_suggester import GPTAnalyzer

        comments_db = CommentsDB()
        gpt_analyzer = GPTAnalyzer()

        # Obter estatísticas gerais (últimos 7 dias)
        stats = await comments_db.get_comments_stats(days=7)

        # Obter métricas GPT do dia
        gpt_metrics = gpt_analyzer.get_daily_metrics()

        # Buscar distribuição de sentimentos (COM PAGINAÇÃO PARA >1000 COMENTÁRIOS)
        all_comments = await db.fetch_all_records(
            table='video_comments',
            select_fields='sentiment_category'
        )

        sentiment_counts = {}
        for row in all_comments:
            category = row.get('sentiment_category', 'unknown')
            sentiment_counts[category] = sentiment_counts.get(category, 0) + 1

        # Buscar comentários de alta prioridade
        priority_query = db.supabase.table('video_comments')\
            .select('comment_id, comment_text_original, priority_score, sentiment_category, author_name, video_title')\
            .gte('priority_score', 70)\
            .order('priority_score', desc=True)\
            .limit(10)\
            .execute()

        high_priority = priority_query.data if priority_query.data else []

        # Buscar canais com mais comentários
        top_canais_query = """
            SELECT
                cm.nome_canal,
                cm.tipo,
                COUNT(vc.id) as total_comments,
                AVG(vc.sentiment_score) as avg_sentiment,
                COUNT(CASE WHEN vc.priority_score >= 70 THEN 1 END) as high_priority_count
            FROM video_comments vc
            JOIN canais_monitorados cm ON vc.canal_id = cm.id
            WHERE vc.created_at >= NOW() - INTERVAL '7 days'
            GROUP BY cm.id, cm.nome_canal, cm.tipo
            ORDER BY total_comments DESC
            LIMIT 10
        """

        # Como não temos RPC, vamos fazer uma query simplificada
        canais_stats = []
        nossos_canais = db.supabase.table('canais_monitorados')\
            .select('id, nome_canal, tipo')\
            .eq('tipo', 'nosso')\
            .execute()

        if nossos_canais.data:
            for canal in nossos_canais.data[:10]:
                # Usar paginação para garantir TODOS os comentários do canal
                canal_comments = await db.fetch_all_records(
                    table='video_comments',
                    select_fields='id, sentiment_score, priority_score',
                    filters={'canal_id': canal['id']}
                )

                if canal_comments:
                    total = len(canal_comments)
                    avg_sentiment = sum(c.get('sentiment_score', 0) for c in canal_comments) / total if total > 0 else 0
                    high_priority = sum(1 for c in canal_comments if c.get('priority_score', 0) >= 70)

                    canais_stats.append({
                        'nome_canal': canal['nome_canal'],
                        'tipo': canal['tipo'],
                        'total_comments': total,
                        'avg_sentiment': round(avg_sentiment, 2),
                        'high_priority_count': high_priority
                    })

        # Montar resposta completa
        return {
            'summary': {
                'total_comments': stats.get('total_comments', 0),
                'analyzed_comments': stats.get('analyzed_comments', 0),
                'high_priority_count': stats.get('high_priority_count', 0),
                'pending_response_count': stats.get('pending_response_count', 0),
                'last_collection': stats.get('last_collection', None)
            },
            'sentiment_distribution': {
                'positive': sentiment_counts.get('positive', 0),
                'negative': sentiment_counts.get('negative', 0),
                'neutral': sentiment_counts.get('neutral', 0),
                'mixed': sentiment_counts.get('mixed', 0)
            },
            'gpt_metrics': {
                'total_analyzed': gpt_metrics.get('total_analyzed', 0),
                'total_tokens_input': gpt_metrics.get('total_tokens_input', 0),
                'total_tokens_output': gpt_metrics.get('total_tokens_output', 0),
                'estimated_cost_usd': gpt_metrics.get('estimated_cost_usd', 0),
                'avg_response_time_ms': gpt_metrics.get('avg_response_time_ms', 0),
                'success_rate': gpt_metrics.get('success_rate', 100)
            },
            'high_priority_comments': high_priority,
            'top_canais_engagement': canais_stats,
            'collection_info': {
                'comments_per_video_limit': 100,
                'batch_size': 15,  # Reduzido para evitar erros de JSON
                'model': 'gpt-4o-mini',
                'cost_per_1m_tokens': {
                    'input': 0.15,
                    'output': 0.60
                }
            }
        }

    except Exception as e:
        logger.error(f"Erro ao obter estatísticas de comentários: {e}")
        # Retornar estrutura vazia em caso de erro
        return {
            'summary': {
                'total_comments': 0,
                'analyzed_comments': 0,
                'high_priority_count': 0,
                'pending_response_count': 0,
                'last_collection': None
            },
            'sentiment_distribution': {
                'positive': 0,
                'negative': 0,
                'neutral': 0,
                'mixed': 0
            },
            'gpt_metrics': {
                'total_analyzed': 0,
                'total_tokens_input': 0,
                'total_tokens_output': 0,
                'estimated_cost_usd': 0,
                'avg_response_time_ms': 0,
                'success_rate': 0
            },
            'high_priority_comments': [],
            'top_canais_engagement': [],
            'error': str(e),
            'message': 'Sistema de comentários ainda não tem dados. Execute a coleta para ver estatísticas.'
        }


@app.get("/api/comments/management")
async def get_comments_management():
    """
    💬 ENDPOINT REMOVIDO - Sistema antigo de respostas automáticas

    Este endpoint foi removido em 03/02/2026.
    Use o novo endpoint: POST /api/comentarios/{comment_id}/gerar-resposta

    Returns:
        JSON com mensagem de depreciação
    """
    return {
        'status': 'deprecated',
        'message': 'Endpoint removido. Use POST /api/comentarios/{comment_id}/gerar-resposta para gerar respostas sob demanda.',
        'migration_date': '2026-02-03',
        'new_endpoint': '/api/comentarios/{comment_id}/gerar-resposta'
    }


@app.post("/api/comments/translate-pending")
async def translate_pending_comments(background_tasks: BackgroundTasks):
    """
    🌐 Traduz todos os comentarios pendentes de traducao.

    Executa em background para nao bloquear a API.
    Traduz apenas comentarios de canais que NAO sao em portugues.

    Returns:
        JSON com status e quantidade de comentarios pendentes
    """
    try:
        # Buscar canais nossos que NAO sao em portugues
        canais_response = db.supabase.table('canais_monitorados')\
            .select('id, nome_canal, lingua')\
            .eq('tipo', 'nosso')\
            .execute()

        if not canais_response.data:
            return {'status': 'error', 'message': 'Nenhum canal encontrado'}

        # Filtrar canais que precisam traducao (nao sao PT)
        canais_para_traduzir = []
        for canal in canais_response.data:
            lingua = (canal.get('lingua') or '').lower()
            if 'portug' not in lingua and lingua not in ['portuguese', 'português', 'pt', 'pt-br']:
                canais_para_traduzir.append(canal)

        # Contar comentarios pendentes
        total_pendentes = 0
        for canal in canais_para_traduzir:
            count_response = db.supabase.table('video_comments')\
                .select('id', count='exact')\
                .eq('canal_id', canal['id'])\
                .eq('is_translated', False)\
                .execute()
            total_pendentes += count_response.count if count_response.count else 0

        if total_pendentes == 0:
            return {
                'status': 'success',
                'message': 'Todos os comentarios ja estao traduzidos!',
                'canais_verificados': len(canais_para_traduzir),
                'pendentes': 0,
                'canais_em_traducao': list(canais_em_traducao)
            }

        # Disparar traducao em background para cada canal
        for canal in canais_para_traduzir:
            background_tasks.add_task(traduzir_comentarios_canal, canal['id'])

        return {
            'status': 'processing',
            'message': f'Traducao iniciada para {len(canais_para_traduzir)} canais',
            'canais': [c['nome_canal'] for c in canais_para_traduzir],
            'pendentes_estimados': total_pendentes
        }

    except Exception as e:
        logger.error(f"Erro ao iniciar traducao: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/comments/translation-status")
async def get_translation_status():
    """
    📊 Retorna status atual da traducao de comentarios.

    Mostra quantos comentarios estao traduzidos vs pendentes,
    e quais canais estao em processo de traducao.
    """
    try:
        # Buscar canais nossos que NAO sao em portugues
        canais_response = db.supabase.table('canais_monitorados')\
            .select('id, nome_canal, lingua')\
            .eq('tipo', 'nosso')\
            .execute()

        if not canais_response.data:
            return {'status': 'error', 'message': 'Nenhum canal encontrado'}

        # Filtrar canais que precisam traducao (nao sao PT)
        canais_nao_pt = []
        canais_pt = []
        for canal in canais_response.data:
            lingua = (canal.get('lingua') or '').lower()
            if 'portug' not in lingua and lingua not in ['portuguese', 'português', 'pt', 'pt-br']:
                canais_nao_pt.append(canal)
            else:
                canais_pt.append(canal)

        # Contar comentarios por status
        stats_por_canal = []
        total_traduzidos = 0
        total_pendentes = 0

        for canal in canais_nao_pt:
            # Traduzidos
            trad_response = db.supabase.table('video_comments')\
                .select('id', count='exact')\
                .eq('canal_id', canal['id'])\
                .eq('is_translated', True)\
                .execute()
            traduzidos = trad_response.count if trad_response.count else 0

            # Pendentes
            pend_response = db.supabase.table('video_comments')\
                .select('id', count='exact')\
                .eq('canal_id', canal['id'])\
                .eq('is_translated', False)\
                .execute()
            pendentes = pend_response.count if pend_response.count else 0

            if traduzidos > 0 or pendentes > 0:
                stats_por_canal.append({
                    'canal': canal['nome_canal'],
                    'lingua': canal.get('lingua', 'desconhecida'),
                    'traduzidos': traduzidos,
                    'pendentes': pendentes
                })

            total_traduzidos += traduzidos
            total_pendentes += pendentes

        return {
            'status': 'success',
            'resumo': {
                'total_traduzidos': total_traduzidos,
                'total_pendentes': total_pendentes,
                'percentual_completo': round(total_traduzidos / (total_traduzidos + total_pendentes) * 100, 1) if (total_traduzidos + total_pendentes) > 0 else 100
            },
            'canais_em_traducao': list(canais_em_traducao),
            'canais_nao_portugues': len(canais_nao_pt),
            'canais_portugues': len(canais_pt),
            'detalhes': stats_por_canal
        }

    except Exception as e:
        logger.error(f"Erro ao buscar status de traducao: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/comments/test-translation")
async def test_translation():
    """
    🧪 Testa se a traducao esta funcionando.

    Tenta traduzir um texto de teste e retorna o resultado ou erro.
    Util para diagnosticar problemas com a API do OpenAI.
    """
    import os
    import traceback

    # Verificar se a chave existe
    api_key = os.getenv("OPENAI_API_KEY")
    key_exists = api_key is not None
    key_prefix = api_key[:10] + "..." if api_key else None

    try:
        from translate_comments_optimized import OptimizedTranslator

        translator = OptimizedTranslator()
        test_text = "This is a test message to verify translation is working correctly."

        result = await translator.translate_batch([test_text])

        return {
            'status': 'success',
            'original': test_text,
            'translated': result[0] if result else None,
            'message': 'Traducao funcionando corretamente!',
            'key_exists': key_exists,
            'key_prefix': key_prefix
        }

    except Exception as e:
        logger.error(f"Erro no teste de traducao: {e}")
        logger.error(traceback.format_exc())
        return {
            'status': 'error',
            'error': str(e),
            'error_type': type(e).__name__,
            'key_exists': key_exists,
            'key_prefix': key_prefix,
            'message': 'Traducao NAO esta funcionando.'
        }


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

@app.post("/api/force-cache-rebuild")
async def force_cache_rebuild(canal_id: Optional[int] = None):
    """
    🔄 Força reconstrução do cache de engajamento.

    Útil para testes ou após correções manuais.

    Args:
        canal_id: ID específico do canal ou None para todos

    Returns:
        Estatísticas do processamento
    """
    try:
        logger.info(f"🔄 FORÇANDO REBUILD DO CACHE (canal_id: {canal_id or 'TODOS'})")

        from engagement_preprocessor import EngagementPreprocessor
        preprocessor = EngagementPreprocessor(db)

        result = await preprocessor.force_rebuild_cache(canal_id)

        logger.info(f"✅ Cache rebuild concluído: {result}")

        return {
            "status": "success",
            "result": result,
            "message": f"Cache reconstruído: {result['processed']}/{result['total']} canais processados"
        }

    except Exception as e:
        logger.error(f"❌ Erro ao reconstruir cache: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cache-stats")
async def get_cache_stats():
    """
    📊 Retorna estatísticas do cache de engajamento.
    """
    try:
        from engagement_preprocessor import EngagementPreprocessor
        preprocessor = EngagementPreprocessor(db)

        stats = await preprocessor.get_cache_stats()

        return stats

    except Exception as e:
        logger.error(f"❌ Erro ao obter estatísticas do cache: {e}")
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

@app.post("/api/refresh-mv")
async def refresh_materialized_view():
    """
    🔄 Força refresh da Materialized View mv_dashboard_completo.

    Use este endpoint quando:
    - inscritos_diff estiver mostrando 0 para muitos canais
    - Após coleta manual
    - Para garantir dados atualizados
    """
    try:
        logger.info("=" * 60)
        logger.info("🔄 REFRESH MANUAL DA MATERIALIZED VIEW")
        logger.info(f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)

        # Tentar método 1: Via RPC (se existir)
        try:
            response = db.supabase.rpc("refresh_all_dashboard_mvs").execute()
            if response.data:
                logger.info("✅ Refresh via RPC executado com sucesso")
                # Limpar cache após refresh
                cache_cleared = clear_all_cache()
                return {
                    "success": True,
                    "method": "rpc",
                    "message": "Materialized View atualizada via RPC",
                    "data": response.data,
                    "cache_cleared": cache_cleared['entries_cleared']
                }
        except Exception as rpc_error:
            logger.warning(f"RPC não disponível: {rpc_error}")

        # Método 2: Verificar dados disponíveis e limpar cache
        try:
            # Verificar dados de hoje e ontem
            hoje = datetime.now(timezone.utc).date()
            ontem = hoje - timedelta(days=1)

            # Contar registros disponíveis
            hoje_count = db.supabase.table('dados_canais_historico') \
                .select('id', count='exact') \
                .gte('data_coleta', hoje.isoformat() + 'T00:00:00') \
                .lte('data_coleta', hoje.isoformat() + 'T23:59:59') \
                .execute()

            ontem_count = db.supabase.table('dados_canais_historico') \
                .select('id', count='exact') \
                .gte('data_coleta', ontem.isoformat() + 'T00:00:00') \
                .lte('data_coleta', ontem.isoformat() + 'T23:59:59') \
                .execute()

            logger.info(f"📊 Dados disponíveis - Hoje: {hoje_count.count}, Ontem: {ontem_count.count}")

            # Se não há dados suficientes
            if (hoje_count.count or 0) == 0 or (ontem_count.count or 0) == 0:
                return {
                    "success": False,
                    "method": "data_check",
                    "message": "Dados insuficientes para calcular inscritos_diff. Execute uma coleta primeiro.",
                    "stats": {
                        "dados_hoje": hoje_count.count or 0,
                        "dados_ontem": ontem_count.count or 0
                    }
                }

            # Limpar cache para forçar recálculo
            cache_cleared = clear_all_cache()
            logger.info(f"🧹 Cache limpo: {cache_cleared['entries_cleared']} entradas")

            # Forçar atualização via database.py
            mv_result = await db.refresh_all_dashboard_mvs()

            return {
                "success": True,
                "method": "force_refresh",
                "message": "Cache limpo e MV atualizada. Dados serão recalculados.",
                "stats": {
                    "dados_hoje": hoje_count.count or 0,
                    "dados_ontem": ontem_count.count or 0,
                    "cache_limpo": cache_cleared['entries_cleared']
                },
                "mv_result": mv_result
            }

        except Exception as fallback_error:
            logger.error(f"Erro no refresh: {fallback_error}")
            return {
                "success": False,
                "error": str(fallback_error),
                "message": "Execute o SQL manualmente no Supabase: REFRESH MATERIALIZED VIEW CONCURRENTLY mv_dashboard_completo;"
            }

    except Exception as e:
        logger.error(f"❌ Erro crítico no refresh da MV: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Erro ao tentar atualizar Materialized View"
        }

@app.get("/api/coletas/historico")
async def get_coletas_historico(limit: Optional[int] = 20):
    try:
        historico = await db.get_coletas_historico(limit=limit)

        # Buscar canais problemáticos para o modal de logs
        canais_problematicos = await db.get_canais_problematicos()

        quota_usada = await db.get_quota_diaria_usada()

        quota_total = len(collector.api_keys) * 10000
        quota_disponivel = quota_total - quota_usada
        porcentagem_usada = (quota_usada / quota_total) * 100 if quota_total > 0 else 0

        now_utc = datetime.now(timezone.utc)
        next_reset = now_utc.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)

        brasilia_offset = timedelta(hours=-3)
        next_reset_brasilia = next_reset + brasilia_offset

        # Usar informações reais do collector - calcular baseado na quota gasta
        chaves_esgotadas_real = min(int(quota_usada // 10000), len(collector.api_keys))
        chaves_suspensas_real = len(collector.suspended_keys)
        chaves_ativas_real = len(collector.api_keys) - chaves_esgotadas_real - chaves_suspensas_real

        # Pegar dados da última coleta
        ultima_coleta = historico[0] if historico else {}
        videos_coletados = ultima_coleta.get("videos_coletados", 0)

        return {
            "historico": historico,
            "total": len(historico),
            "canais_com_erro": {
                "total": len(canais_problematicos),
                "lista": [
                    {
                        "nome": c.get("nome_canal"),
                        "subnicho": c.get("subnicho"),
                        "tipo": c.get("tipo"),
                        "erro": c.get("coleta_ultimo_erro"),
                        "falhas_consecutivas": c.get("coleta_falhas_consecutivas"),
                        "lingua": c.get("lingua"),
                        "url_canal": c.get("url_canal")
                    }
                    for c in canais_problematicos
                ]
            },
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
                "videos_coletados": videos_coletados,
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

@app.post("/api/cache/clear")
async def clear_all_cache():
    """
    Limpa todo o cache do dashboard e força atualização das Materialized Views.
    Use este endpoint após deletar canais para forçar atualização imediata.
    """
    try:
        # Limpar cache global
        global dashboard_cache, tabela_cache, cache_timestamp_dashboard, cache_timestamp_tabela, comments_cache
        dashboard_cache = {}
        tabela_cache = {}
        comments_cache = {}  # Limpar cache de comentários também
        cache_timestamp_dashboard = None
        cache_timestamp_tabela = None

        # Forçar refresh das MVs
        try:
            await db.refresh_all_dashboard_mvs()
            mv_refreshed = True
        except Exception as e:
            logger.warning(f"Could not refresh MVs: {e}")
            mv_refreshed = False

        logger.info("🧹 Cache limpo: Dashboard, Tabela e Comentários")

        return {
            "message": "Cache limpo com sucesso",
            "cache_cleared": True,
            "comments_cache_cleared": True,
            "mv_refreshed": mv_refreshed,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
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
    # DESATIVADO - Sistema de análise removido (aba excluída do dashboard)
    raise HTTPException(
        status_code=503,
        detail="Sistema de análise foi desativado. Aba removida do dashboard."
    )
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
    # DESATIVADO - Sistema de análise removido (aba excluída do dashboard)
    raise HTTPException(
        status_code=503,
        detail="Sistema de análise foi desativado. Aba removida do dashboard."
    )
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
    # DESATIVADO - Sistema de análise removido (aba excluída do dashboard)
    raise HTTPException(
        status_code=503,
        detail="Sistema de análise foi desativado. Aba removida do dashboard."
    )
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
    # DESATIVADO - Sistema de análise removido (aba excluída do dashboard)
    raise HTTPException(
        status_code=503,
        detail="Sistema de análise foi desativado. Aba removida do dashboard."
    )
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
        # PROTEÇÃO: report_generator.py pode não existir se analyzer.py estiver faltando
        try:
            from report_generator import ReportGenerator
        except ImportError as e:
            logger.warning(f"⚠️ Report generator não disponível: {e}")
            raise HTTPException(
                status_code=503,
                detail="Sistema de relatórios indisponível (módulo analyzer.py não encontrado)"
            )

        logger.info("🔄 Starting weekly report generation...")
        generator = ReportGenerator(db.supabase)
        report = generator.generate_weekly_report()
        logger.info("✅ Weekly report generated successfully")
        return {"message": "Relatório gerado com sucesso", "report": report}
    except HTTPException:
        raise  # Re-levanta a HTTPException
    except Exception as e:
        logger.error(f"Error generating weekly report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analysis/run-daily")
async def run_daily_analysis():
    """Executa análises diárias manualmente"""
    # DESATIVADO - Sistema de análise removido (aba excluída do dashboard)
    raise HTTPException(
        status_code=503,
        detail="Sistema de análise foi desativado. Aba removida do dashboard."
    )

@app.post("/api/analysis/run-gaps")
async def run_gap_analysis():
    """Executa análise de gaps manualmente"""
    # DESATIVADO - Sistema de análise removido (aba excluída do dashboard)
    raise HTTPException(
        status_code=503,
        detail="Sistema de análise foi desativado. Aba removida do dashboard."
    )


async def run_collection_job():
    global collection_in_progress, last_collection_time

    coleta_id = None
    canais_sucesso = 0
    canais_erro = 0
    videos_total = 0
    comentarios_total = 0  # Contador de comentários coletados
    comentarios_analisados_total = 0  # Contador de comentários analisados com GPT
    comentarios_com_erro_total = 0  # Contador de comentários que falharam

    # Sistema de logs para comentários
    comments_logger = CommentsLogsManager()
    collection_id = str(uuid.uuid4())
    collection_timestamp = datetime.now(timezone.utc)

    # Listas para rastrear detalhes da coleta
    detalhes_sucesso = []
    detalhes_erros = []

    # Timeout de segurança - 2 horas máximo
    collection_start_time = time.time()
    MAX_COLLECTION_TIME = 7200  # 2 horas em segundos

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

        # Criar CommentsDB uma vez só quando necessário
        comments_db = None

        for index, canal in enumerate(canais_to_collect, 1):
            # SEM TIMEOUT - processar todos os canais

            if collector.all_keys_exhausted():
                logger.error("=" * 80)
                logger.error("❌ ALL API KEYS EXHAUSTED - STOPPING COLLECTION")
                logger.error(f"✅ Collected {canais_sucesso}/{total_canais} canais")
                logger.error(f"📊 Total requests used: {collector.total_quota_units}")
                logger.error("=" * 80)
                break
            
            try:
                logger.info(f"[{index}/{total_canais}] 🔄 Processing: {canal['nome_canal']}")

                # 🚀 OTIMIZAÇÃO: get_canal_data agora retorna (stats, videos) juntos
                # Isso economiza ~50% da quota de API eliminando busca duplicada!
                canal_data, videos_data = await collector.get_canal_data(canal['url_canal'], canal['nome_canal'])

                if canal_data:
                    saved = await db.save_canal_data(canal['id'], canal_data)
                    if saved:
                        canais_sucesso += 1
                        await db.marcar_coleta_sucesso(canal['id'])  # 🆕 Tracking de sucesso
                        logger.info(f"✅ [{index}/{total_canais}] Success: {canal['nome_canal']}")
                    else:
                        canais_erro += 1
                        await db.marcar_coleta_falha(canal['id'], "Dados não salvos (all zeros)")
                        logger.warning(f"⚠️ [{index}/{total_canais}] Data not saved (all zeros): {canal['nome_canal']}")
                else:
                    canais_erro += 1
                    await db.marcar_coleta_falha(canal['id'], "Falha ao obter dados do canal")
                    logger.warning(f"❌ [{index}/{total_canais}] Failed: {canal['nome_canal']}")

                # 🚀 Usar vídeos já buscados (não buscar novamente!)
                if videos_data:
                    await db.save_videos_data(canal['id'], videos_data)
                    videos_total += len(videos_data)

                await db.update_last_collection(canal['id'])

                # 💬 COLETA DE COMENTÁRIOS (APENAS CANAIS NOSSOS)
                if canal.get('tipo') == 'nosso' and videos_data:
                    try:
                        logger.info(f"💬 [{index}/{total_canais}] Collecting comments: {canal['nome_canal']}")

                        # Buscar channel_id necessário para coleta
                        channel_id = await collector.get_channel_id(canal['url_canal'], canal['nome_canal'])

                        if channel_id:
                            # Adaptar estrutura dos vídeos para a função de coleta
                            videos_adapted = []
                            for video in videos_data:  # Processar TODOS os vídeos dos últimos 30 dias
                                videos_adapted.append({
                                    'videoId': video.get('video_id'),
                                    'title': video.get('titulo'),
                                    'viewCount': video.get('views_atuais'),
                                    'publishedAt': video.get('data_publicacao')
                                })

                            # Buscar timestamp do último comentário coletado (para coleta incremental)
                            last_comment_timestamp = canal.get('ultimo_comentario_coletado')

                            # Coletar comentários de todos os vídeos recentes
                            comments_data = await collector.get_all_channel_comments(
                                channel_id=channel_id,
                                canal_name=canal['nome_canal'],
                                videos=videos_adapted,
                                last_collected_timestamp=last_comment_timestamp
                            )

                            if comments_data and comments_data.get('total_comments', 0) > 0:
                                # Inicializar CommentsDB uma vez só (na primeira vez que precisar)
                                if comments_db is None:
                                    logger.info("💾 Inicializando CommentsDB...")
                                    from database_comments import CommentsDB
                                    comments_db = CommentsDB()
                                    logger.info("✅ CommentsDB inicializado")

                                # Processar comentários por vídeo - APENAS SALVAR (análise GPT vem depois)
                                for video_id, video_comments in comments_data.get('comments_by_video', {}).items():
                                    if video_comments and video_comments.get('comments'):
                                        # Preparar comentários SEM análise (serão analisados no reprocessamento)
                                        comments_to_save = []

                                        for comment in video_comments['comments']:
                                            comment_data = {
                                                'comment_id': comment.get('comment_id'),
                                                'video_id': video_id,
                                                'canal_id': canal['id'],
                                                'author_name': comment.get('author_name', ''),
                                                'comment_text_original': comment.get('comment_text_original', ''),
                                                'published_at': comment.get('published_at'),
                                                'like_count': comment.get('like_count', 0),
                                                'reply_count': comment.get('reply_count', 0),
                                                # Campos de análise vazios (para reprocessar depois)
                                                'sentiment_category': None,
                                                'sentiment_score': None,
                                                'priority_score': None,
                                                'emotional_tone': None,
                                                'requires_response': False,
                                                'suggested_response': None,
                                                'analyzed_at': None  # NULL = precisa análise GPT
                                            }
                                            comments_to_save.append(comment_data)

                                        # Salvar comentários no banco (SEM análise GPT)
                                        if comments_to_save:
                                            try:
                                                await comments_db.save_video_comments(
                                                    video_id=video_id,
                                                    canal_id=canal['id'],
                                                    comments=comments_to_save
                                                )
                                                logger.info(f"💾 {len(comments_to_save)} comentários salvos (sem análise) para {canal['nome_canal']}")

                                                # Canais em português: marcar como traduzido (não precisa GPT)
                                                canal_lingua = (canal.get('lingua') or '').lower()
                                                if 'portug' in canal_lingua or canal_lingua in ('pt', 'pt-br'):
                                                    try:
                                                        for c in comments_to_save:
                                                            if c.get('comment_id'):
                                                                supabase.table('video_comments').update({
                                                                    'is_translated': True,
                                                                    'comment_text_pt': c.get('comment_text_original', '')
                                                                }).eq('comment_id', c['comment_id']).execute()
                                                        logger.info(f"🇧🇷 {len(comments_to_save)} comentários PT marcados como traduzidos para {canal['nome_canal']}")
                                                    except Exception as pt_err:
                                                        logger.error(f"Erro ao marcar comentários PT: {pt_err}")

                                            except Exception as save_error:
                                                logger.error(f"❌ Erro ao salvar comentários no banco: {save_error}")
                                                # Registrar falha de salvamento
                                                await db.marcar_coleta_falha(
                                                    canal['id'],
                                                    f"Database save failed: {str(save_error)}"
                                                )

                                comentarios_total += comments_data['total_comments']

                                # Adicionar ao log de sucesso
                                detalhes_sucesso.append({
                                    'canal_nome': canal['nome_canal'],
                                    'canal_id': canal['id'],
                                    'videos_processados': len(videos_adapted),
                                    'comentarios_coletados': comments_data['total_comments'],
                                    'comentarios_analisados_gpt': 0  # Análise será feita no reprocessamento
                                })

                                # Atualizar timestamp do último comentário coletado (para coleta incremental)
                                if comments_data.get('latest_comment_timestamp'):
                                    try:
                                        await db.update_canal_ultimo_comentario(
                                            canal['id'],
                                            comments_data['latest_comment_timestamp']
                                        )
                                        logger.debug(f"📅 Timestamp atualizado para {canal['nome_canal']}: {comments_data['latest_comment_timestamp']}")
                                    except Exception as e:
                                        logger.warning(f"⚠️ Erro ao atualizar timestamp: {e}")

                                logger.info(f"✅ [{index}/{total_canais}] {comments_data['total_comments']} comments saved: {canal['nome_canal']}")
                            else:
                                logger.info(f"ℹ️ [{index}/{total_canais}] No new comments: {canal['nome_canal']}")
                        else:
                            logger.warning(f"⚠️ [{index}/{total_canais}] Channel ID not found for comments: {canal['nome_canal']}")

                    except Exception as e:
                        logger.warning(f"⚠️ [{index}/{total_canais}] Error collecting comments from {canal['nome_canal']}: {e}")
                        # Adicionar ao log de erros
                        detalhes_erros.append({
                            'canal_nome': canal['nome_canal'],
                            'canal_id': canal['id'],
                            'tipo_erro': 'api_error' if 'quota' in str(e).lower() else 'sem_comentarios',
                            'mensagem': str(e)[:200]
                        })
                        # Não interrompe o fluxo - apenas registra o erro

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
                    logger.info(f"💬 Comments: {comentarios_total} | 📡 API: {collector.total_quota_units} | ⏱️  Time: ongoing")
                    logger.info("=" * 80)

            except Exception as e:
                logger.error(f"❌ Error processing {canal['nome_canal']}: {e}")
                await db.marcar_coleta_falha(canal['id'], str(e))  # 🆕 Tracking de falha
                canais_erro += 1
                continue
        
        stats = collector.get_request_stats()
        total_requests = stats['total_quota_units']
        
        logger.info("=" * 80)
        logger.info(f"📊 COLLECTION STATISTICS")
        logger.info(f"✅ Success: {canais_sucesso}/{total_canais}")
        logger.info(f"❌ Errors: {canais_erro}/{total_canais}")
        logger.info(f"🎬 Videos: {videos_total}")
        logger.info(f"💬 Comments: {comentarios_total}")
        logger.info(f"📡 Total API Requests: {total_requests}")
        logger.info(f"🔑 Active keys: {stats['active_keys']}/{len(collector.api_keys)}")
        logger.info("=" * 80)

        # Salvar log de comentários se houve coleta
        if comentarios_total > 0 or len(detalhes_erros) > 0:
            try:
                # Calcular tokens usados pelo GPT
                # NOTA: Durante coleta, sempre será 0 (análise só no reprocessamento)
                tokens_usados = 0
                percentual_limite = 0.0
                if comentarios_analisados_total > 0:
                    # Cálculo de tokens: ~37.5 tokens input + ~20 tokens output por comentário
                    tokens_input = int((comentarios_analisados_total * 150) / 4)  # ~150 chars por comentário, 4 chars por token
                    tokens_output = comentarios_analisados_total * 20  # ~20 tokens por análise
                    tokens_usados = tokens_input + tokens_output
                    percentual_limite = (tokens_usados / 1_000_000) * 100  # % do limite de 1M tokens/dia

                log_data = {
                    'collection_id': collection_id,
                    'timestamp': collection_timestamp,
                    'tipo': 'automatic',  # ou 'manual' se foi disparado manualmente
                    'canais_processados': len([d for d in detalhes_sucesso]) + len(detalhes_erros),
                    'canais_com_sucesso': len(detalhes_sucesso),
                    'canais_com_erro': len(detalhes_erros),
                    'total_comentarios': comentarios_total,
                    'comentarios_analisados': 0,  # Durante coleta = 0 (análise no reprocessamento)
                    'comentarios_nao_analisados': comentarios_total,  # Todos pendentes de análise
                    'detalhes_erros': detalhes_erros,
                    'detalhes_sucesso': detalhes_sucesso,
                    'tempo_execucao': time.time() - collection_start_time,
                    'tokens_usados': tokens_usados,
                    'percentual_limite_diario': percentual_limite
                }

                saved = comments_logger.save_collection_log(log_data)
                if saved:
                    logger.info(f"💾 Log de comentários salvo: {collection_id}")
                else:
                    logger.warning("⚠️ Falha ao salvar log de comentários")

            except Exception as e:
                logger.error(f"❌ Erro ao salvar log de comentários: {e}")

        # Registrar métricas GPT se comentários foram analisados
        if comentarios_total > 0:
            try:
                from database_comments import CommentsDB
                comments_db = CommentsDB()

                # Obter métricas do GPT analyzer (se foi usado)
                try:
                    from gpt_response_suggester import GPTAnalyzer
                    gpt_analyzer = GPTAnalyzer()
                    gpt_metrics = gpt_analyzer.get_daily_metrics()

                    if gpt_metrics['total_analyzed'] > 0:
                        await comments_db.record_gpt_metrics(gpt_metrics)
                        logger.info(f"🤖 GPT Metrics: {gpt_metrics['total_analyzed']} analyzed, ${gpt_metrics['estimated_cost_usd']} cost")
                except:
                    pass  # GPT não foi usado ou erro ao obter métricas
            except Exception as e:
                logger.warning(f"⚠️ Erro ao registrar métricas GPT: {e}")
        
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

            # 🤖 AUTOMAÇÃO PÓS-COLETA: Tradução e geração de respostas
            if comentarios_total > 0:
                try:
                    logger.info("=" * 80)
                    logger.info("🤖 INICIANDO AUTOMAÇÃO PÓS-COLETA")
                    logger.info(f"📝 Processando {comentarios_total} novos comentários...")
                    logger.info("=" * 80)

                    # Importar e executar automação (aguardar conclusão)
                    from post_collection_automation import PostCollectionAutomation
                    automation = PostCollectionAutomation()

                    # AGUARDAR automação completar antes de continuar
                    logger.info("🔄 Aguardando automação pós-coleta...")
                    await automation.run(only_recent=True)

                    logger.info("✅ Automação pós-coleta CONCLUÍDA")
                    logger.info("   → Comentários traduzidos")
                    logger.info("   → Respostas geradas")

                except Exception as e:
                    logger.error(f"❌ Erro ao iniciar automação pós-coleta: {e}")
                    logger.error(f"   Detalhes: {str(e)}")
                    # Não interrompe o fluxo - apenas registra o erro

            # 🔄 REPROCESSAMENTO AUTOMÁTICO DE COMENTÁRIOS SEM ANÁLISE (LEGADO - DESATIVADO)
            # NOTA: Substituído pela automação pós-coleta acima
            if False:  # Desativado - mantido apenas para referência
                try:
                    logger.info("=" * 80)
                    logger.info("🔄 REPROCESSAMENTO AUTOMÁTICO DE COMENTÁRIOS")
                    logger.info("=" * 80)

                    # Buscar comentários sem análise
                    sem_analise = db.supabase.table('video_comments')\
                        .select('id')\
                        .is_('analyzed_at', 'null')\
                        .execute()

                    total_sem_analise = len(sem_analise.data) if sem_analise.data else 0

                    if total_sem_analise > 0:
                        logger.info(f"📊 {total_sem_analise} comentários sem análise encontrados")
                        logger.info("🔄 Iniciando reprocessamento automático...")

                        # Importar função de reprocessamento
                        from reprocess_comments import reprocess_unanalyzed_comments

                        # Executar reprocessamento
                        await reprocess_unanalyzed_comments()

                        # Verificar resultado
                        ainda_sem = db.supabase.table('video_comments')\
                            .select('id')\
                            .is_('analyzed_at', 'null')\
                            .execute()

                        ainda_sem_count = len(ainda_sem.data) if ainda_sem.data else 0
                        processados = total_sem_analise - ainda_sem_count

                        logger.info(f"✅ {processados} comentários reprocessados com sucesso")
                        if ainda_sem_count > 0:
                            logger.warning(f"⚠️ {ainda_sem_count} comentários ainda sem análise (próxima tentativa amanhã)")
                    else:
                        logger.info("✅ Todos os comentários já estão analisados!")

                except Exception as e:
                    logger.error(f"❌ Erro no reprocessamento automático: {str(e)}")
                    # Não falhar a coleta por erro no reprocessamento

            # 🆕 PÓS-PROCESSAMENTO: Tradução + Geração de Respostas
            # Executado APÓS análise GPT para não quebrar o processo atual
            if comentarios_total > 0:
                try:
                    logger.info("=" * 80)
                    logger.info("🔄 PÓS-PROCESSAMENTO: TRADUÇÃO E RESPOSTAS")
                    logger.info("=" * 80)

                    # Importar o workflow corrigido
                    from workflow_comments_fixed import WorkflowCommentsFixed

                    # Processar TODOS os comentários usando workflow corrigido
                    processor = WorkflowCommentsFixed()
                    post_stats = await processor.run_complete_workflow()

                    logger.info(f"✅ Pós-processamento completo:")
                    logger.info(f"  - Total comentários: {post_stats.get('total_comments', 0)}")
                    logger.info(f"  - Com texto: {post_stats.get('comments_with_text', 0)}")
                    logger.info(f"  - Traduzidos: {post_stats.get('translated', 0)}")
                    logger.info(f"  - Respostas geradas: {post_stats.get('responses_generated', 0)}")
                    logger.info(f"  - Erros: {post_stats.get('errors', 0)}")

                except Exception as e:
                    # Não quebrar a coleta se o pós-processamento falhar
                    logger.error(f"⚠️ Erro no pós-processamento (não crítico): {e}")

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

        # 🚀 REFRESH AUTOMÁTICO DAS MATERIALIZED VIEWS + CACHE
        # Atualiza TODAS as MVs e limpa cache após cada coleta
        try:
            logger.info("")  # Linha em branco para melhor visualização
            logger.info("=" * 60)
            logger.info("🔄 ATUALIZANDO MATERIALIZED VIEWS E CACHE")
            logger.info("=" * 60)

            # 1. Atualizar TODAS as Materialized Views
            mv_results = await db.refresh_all_dashboard_mvs()

            # 2. Limpar todo o cache do dashboard (será renovado no próximo acesso)
            cache_stats = clear_all_cache()
            logger.info(f"🧹 Cache limpo: {cache_stats['entries_cleared']} entradas removidas")
            logger.info(f"💾 Memória liberada: ~{cache_stats['approx_size_kb']}KB")

            logger.info("✅ Dashboard pronto com dados frescos e cache renovado!")
            logger.info("⚡ Próximo acesso será instantâneo (< 1ms)")
            logger.info("=" * 60)
            logger.info("")  # Linha em branco para melhor visualização

        except Exception as mv_error:
            # Não é crítico - apenas log de warning
            logger.warning(f"⚠️ Falha ao atualizar MVs/Cache: {mv_error}")
            logger.warning("Dashboard continuará funcionando com dados anteriores")

        # =====================================================================
        # ANÁLISE DIÁRIA DESATIVADA (aba removida do dashboard)
        # Código preservado para referência futura
        # =====================================================================
        # await run_daily_analysis_job()  # DESATIVADO - analyzer.py não existe

        # =====================================================================
        # BUILD ENGAGEMENT CACHE - Movido para cá (roda SEMPRE após coleta)
        # Não depende mais da análise diária
        # =====================================================================
        try:
            logger.info("🔄 INICIANDO BUILD DO CACHE DE ENGAJAMENTO")
            from engagement_preprocessor import build_engagement_cache
            cache_result = await build_engagement_cache()
            logger.info(f"✅ ENGAGEMENT CACHE ATUALIZADO: {cache_result.get('processed', 0)}/{cache_result.get('total', 0)} canais processados")
        except Exception as cache_error:
            logger.error(f"❌ Erro ao construir cache de engajamento: {cache_error}")
            # Não falha o job principal se o cache falhar

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

"""
=====================================================================
FUNÇÕES DE ANÁLISE DESATIVADAS
Aba "Análise" removida do dashboard - código preservado para referência
=====================================================================
"""

# DESATIVADO - analyzer.py não existe
'''
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

        # =====================================================================
        # ÚLTIMO STEP: BUILD ENGAGEMENT CACHE
        # Executa APÓS todas as análises e processamentos
        # =====================================================================
        try:
            logger.info("🔄 INICIANDO BUILD DO CACHE DE ENGAJAMENTO (ÚLTIMO STEP)")
            from engagement_preprocessor import build_engagement_cache
            cache_result = await build_engagement_cache()
            logger.info(f"✅ ENGAGEMENT CACHE ATUALIZADO: {cache_result.get('processed', 0)}/{cache_result.get('total', 0)} canais processados")
        except Exception as cache_error:
            logger.error(f"❌ Erro ao construir cache de engajamento: {cache_error}")
            # Não falha o job principal se o cache falhar

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
'''


async def schedule_spreadsheet_scanner():
    """
    Background task para varredura de planilhas Google Sheets.

    Roda a cada X minutos (configurável via SCANNER_INTERVAL_MINUTES).
    Detecta vídeos prontos para upload e adiciona na fila automaticamente.
    """
    from yt_uploader.spreadsheet_scanner import SpreadsheetScanner

    # Configurações
    interval_minutes = int(os.getenv("SCANNER_INTERVAL_MINUTES", "20"))  # 20 min - suporte garantido para 70+ canais
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
        # asyncio.create_task(weekly_report_scheduler())  # DESATIVADO - Sistema de análise removido
        asyncio.create_task(schedule_spreadsheet_scanner())

        # Upload Queue Worker (isolado - falha não afeta main app)
        try:
            from yt_uploader.queue_worker import start_queue_worker
            asyncio.create_task(start_queue_worker())
            logger.info("✅ Upload queue worker scheduled")
        except Exception as e:
            logger.warning(f"⚠️ Upload worker disabled: {e}")

        # Daily YouTube Upload System (isolado - falha não afeta main app)
        if os.environ.get("DAILY_UPLOAD_ENABLED", "").lower() == "true":
            try:
                asyncio.create_task(schedule_daily_uploader())
                logger.info("✅ Daily YouTube upload scheduler started")
                logger.info("📅 Upload scheduled for 5:30 AM daily")
            except Exception as e:
                logger.warning(f"⚠️ Daily upload scheduler disabled: {e}")
        else:
            logger.info("📌 Daily upload system disabled (set DAILY_UPLOAD_ENABLED=true to enable)")

        logger.info("✅ Schedulers started (Railway environment + Scanner + Upload Worker)")
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
# 🌐 TRADUÇÃO AUTOMÁTICA DE COMENTÁRIOS
# ========================================

# Dicionário para controle de lock (evita tradução duplicada)
canais_em_traducao = set()

async def traduzir_comentarios_canal(canal_id: int):
    """
    Traduz TODOS os comentários não traduzidos de um canal em background.
    Processa em loop até não haver mais pendentes.
    NÃO traduz comentários de canais em português.
    Sistema de lock previne duplicação.
    """
    # Verificar se já está em tradução
    if canal_id in canais_em_traducao:
        logger.info(f"⚠️ Canal {canal_id} já está sendo traduzido, pulando...")
        return

    # Marcar canal como em tradução
    canais_em_traducao.add(canal_id)

    try:
        logger.info(f"🌐 Iniciando verificação de tradução para canal {canal_id}")

        # Verificar língua do canal
        canal_response = db.supabase.table('canais_monitorados')\
            .select('nome_canal, lingua')\
            .eq('id', canal_id)\
            .execute()

        if not canal_response.data:
            logger.error(f"❌ Canal {canal_id} não encontrado")
            return

        canal = canal_response.data[0]
        lingua = canal.get('lingua', '').lower()

        # Se canal é português, pular tradução
        if 'portug' in lingua or lingua in ['portuguese', 'português', 'pt', 'pt-br']:
            logger.info(f"🇧🇷 Canal {canal['nome_canal']} é em português - tradução não necessária")
            return

        logger.info(f"🌍 Canal {canal['nome_canal']} ({lingua}) - iniciando tradução completa")

        # Importar tradutor
        from translate_comments_optimized import OptimizedTranslator
        translator = OptimizedTranslator()

        total_traduzidos = 0
        rodadas = 0

        # Loop até traduzir TODOS os comentários
        while True:
            rodadas += 1

            # Buscar próximo lote de comentários não traduzidos
            response = db.supabase.table('video_comments')\
                .select('id, comment_text_original')\
                .eq('canal_id', canal_id)\
                .eq('is_translated', False)\
                .limit(50)\
                .execute()

            if not response.data:
                logger.info(f"✅ Todos os comentários do canal {canal_id} foram traduzidos!")
                break

            comentarios = response.data
            logger.info(f"📝 Rodada {rodadas}: {len(comentarios)} comentários para traduzir")

            # Processar em lotes de 20
            batch_size = 20
            traduzidos_rodada = 0

            for i in range(0, len(comentarios), batch_size):
                batch = comentarios[i:i+batch_size]
                textos_originais = [c['comment_text_original'] for c in batch]

                # Tentar traduzir com retry (até 3 tentativas)
                for tentativa in range(3):
                    try:
                        # Traduzir batch
                        textos_traduzidos = await translator.translate_batch(textos_originais)

                        # Atualizar no banco
                        for j, comentario in enumerate(batch):
                            if j < len(textos_traduzidos):
                                texto_traduzido = textos_traduzidos[j]

                                # Só atualizar se recebeu tradução
                                if texto_traduzido:
                                    update_result = db.supabase.table('video_comments')\
                                        .update({
                                            'comment_text_pt': texto_traduzido,
                                            'is_translated': True
                                        })\
                                        .eq('id', comentario['id'])\
                                        .execute()

                                    if update_result.data:
                                        traduzidos_rodada += 1

                        logger.info(f"✅ Lote {i//batch_size + 1} traduzido: {traduzidos_rodada} comentários")
                        break  # Sucesso, sai do loop de retry

                    except Exception as e:
                        if tentativa < 2:
                            logger.warning(f"⚠️ Erro ao traduzir lote (tentativa {tentativa + 1}/3): {e}")
                            await asyncio.sleep(5 * (tentativa + 1))  # 5s, 10s
                        else:
                            logger.error(f"❌ Erro após 3 tentativas no lote: {e}")
                            break  # Pula este lote após 3 falhas

                # Rate limiting entre batches
                await asyncio.sleep(2)

            total_traduzidos += traduzidos_rodada
            logger.info(f"📊 Rodada {rodadas} concluída: {traduzidos_rodada} traduzidos (Total: {total_traduzidos})")

            # Se não traduziu nenhum nesta rodada (todos falharam), parar para evitar loop infinito
            if traduzidos_rodada == 0:
                logger.warning(f"⚠️ Nenhum comentário traduzido nesta rodada, parando...")
                break

        logger.info(f"🎉 Tradução COMPLETA do canal {canal_id}: {total_traduzidos} comentários traduzidos em {rodadas} rodadas")

    except Exception as e:
        logger.error(f"❌ Erro na tradução automática do canal {canal_id}: {e}")
    finally:
        # Remover lock do canal
        canais_em_traducao.discard(canal_id)


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

                # FASE 4.5: Registrar no histórico (NOVO)
                try:
                    from daily_uploader import DailyUploader
                    from datetime import date

                    uploader_instance = DailyUploader()
                    uploader_instance._registrar_canal_diario(
                        channel_id=channel_id,
                        channel_name=upload.get('channel_name', ''),
                        data=date.today(),
                        status='sucesso',
                        erro_mensagem=None,
                        tentativa_numero=99,  # 99 = upload manual
                        upload_id=upload_id,
                        video_titulo=upload.get('titulo', ''),
                        video_url=f"https://youtube.com/watch?v={result['video_id']}"
                    )
                    logger.info(f"[{channel_id}] 📝 Histórico registrado (upload manual)")
                except Exception as hist_error:
                    logger.warning(f"[{channel_id}] ⚠️ Não foi possível registrar histórico: {hist_error}")

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

                    # Busca retry_count atual do banco (TOTAL de tentativas incluindo scanner retries)
                    current_upload = get_upload_by_id(upload_id)
                    total_retry_count = current_upload.get('retry_count', 0) if current_upload else 0

                    update_upload_status(
                        upload_id,
                        'failed',
                        error_message=error_msg,
                        retry_count=total_retry_count + 1  # Incrementa contador total
                    )

                    # Registrar erro no histórico (NOVO)
                    try:
                        from daily_uploader import DailyUploader
                        from datetime import date

                        uploader_instance = DailyUploader()
                        uploader_instance._registrar_canal_diario(
                            channel_id=channel_id,
                            channel_name=upload.get('channel_name', ''),
                            data=date.today(),
                            status='erro',
                            erro_mensagem=error_msg,
                            tentativa_numero=99,  # 99 = upload manual
                            upload_id=upload_id,
                            video_titulo=upload.get('titulo', ''),
                            video_url=upload.get('video_url', '')
                        )
                        logger.info(f"[{channel_id}] 📝 Histórico de erro registrado (upload manual)")
                    except Exception as hist_error:
                        logger.warning(f"[{channel_id}] ⚠️ Não foi possível registrar erro no histórico: {hist_error}")

                    # Atualiza planilha com erro
                    # Se já tentou 3 vezes TOTAL (incluindo retries do scanner), marca "❌ Erro Final"
                    try:
                        if upload and upload.get('spreadsheet_id') and upload.get('sheets_row_number'):
                            # 0 = primeira falha (permite 2 retries), 1 = segunda falha (permite 1 retry), 2 = terceira falha (FINAL)
                            if total_retry_count >= 2:
                                logger.info(f"[{channel_id}] 📊 Planilha atualizada: ❌ Erro Final (3 tentativas esgotadas)")
                                update_upload_status_in_sheet(
                                    spreadsheet_id=upload['spreadsheet_id'],
                                    row=upload['sheets_row_number'],
                                    status='❌ Erro Final'
                                )
                            else:
                                logger.info(f"[{channel_id}] 📊 Planilha atualizada: ❌ Erro (retry {total_retry_count + 1}/3)")
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


@app.get("/api/yt-upload/channels")
async def get_upload_channels():
    """
    Lista canais com upload automático ativado.
    Útil para ver qual é o último canal adicionado.
    """
    result = supabase.table('yt_channels')\
        .select('channel_id, channel_name, spreadsheet_id, upload_automatico, is_monetized, created_at')\
        .eq('is_active', True)\
        .eq('upload_automatico', True)\
        .order('created_at', desc=True)\
        .execute()

    return {
        'total': len(result.data),
        'channels': result.data
    }

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


@app.post("/api/yt-upload/force/{channel_id}")
async def force_upload_for_channel(channel_id: str, background_tasks: BackgroundTasks):
    """
    Forca o upload para um canal especifico.
    Usa o mesmo fluxo do upload automatico das 05:00 AM.

    Args:
        channel_id: ID do canal do YouTube (UCxxxxxxxxx)
    """
    try:
        from daily_uploader import DailyUploader

        # Verificar se canal existe e tem upload automatico ativo
        canal = supabase.table('yt_channels')\
            .select('*')\
            .eq('channel_id', channel_id)\
            .execute()

        if not canal.data:
            raise HTTPException(status_code=404, detail=f"Canal {channel_id} nao encontrado")

        canal_data = canal.data[0]

        if not canal_data.get('upload_automatico'):
            raise HTTPException(status_code=400, detail=f"Canal {canal_data['channel_name']} nao tem upload automatico ativado")

        if not canal_data.get('spreadsheet_id'):
            raise HTTPException(status_code=400, detail=f"Canal {canal_data['channel_name']} nao tem planilha configurada")

        # NOVA VERIFICAÇÃO: Verificar se tem vídeo disponível ANTES de criar background task
        logger.info(f"Verificando se há vídeo disponível para {canal_data['channel_name']}...")
        uploader = DailyUploader()

        # Limpar cache da planilha para forçar busca atualizada
        if canal_data['spreadsheet_id'] in SPREADSHEET_CACHE:
            del SPREADSHEET_CACHE[canal_data['spreadsheet_id']]
            logger.info(f"Cache da planilha limpo para {canal_data['channel_name']}")

        # Verificar se tem vídeo pronto na planilha
        # NOTA: _find_ready_video é async, deve ser chamado com await direto (não run_in_threadpool)
        try:
            video_pronto = await uploader._find_ready_video(
                canal_data['spreadsheet_id'],
                canal_data['channel_name']
            )

            # Se não tiver vídeo, retornar imediatamente com status 'sem_video'
            if not video_pronto:
                logger.warning(f"Nenhum vídeo disponível na planilha de {canal_data['channel_name']}")
                return {
                    'status': 'sem_video',
                    'message': f'Nenhum vídeo disponível na planilha de {canal_data["channel_name"]}',
                    'channel_id': channel_id
                }

            logger.info(f"Vídeo encontrado: {video_pronto.get('titulo', 'Sem título')}")

        except Exception as e:
            logger.error(f"Erro ao verificar vídeo disponível: {e}")
            return {
                'status': 'sem_video',
                'message': f'Erro ao verificar planilha de {canal_data["channel_name"]}: {str(e)[:100]}',
                'channel_id': channel_id
            }

        # Se chegou aqui, tem vídeo disponível - executar upload em background
        async def run_upload():
            try:
                uploader = DailyUploader()
                from datetime import date

                # Usar o mesmo fluxo do daily_uploader que ja funciona
                logger.info(f"Buscando video pronto para {canal_data['channel_name']}...")

                # _process_canal_upload ja faz:
                # 1. Verifica se ja fez upload hoje (opcional para force)
                # 2. Busca video pronto na planilha via _find_ready_video()
                # 3. Adiciona na fila e processa

                # Usa data de hoje para o registro
                hoje = date.today()
                resultado = await uploader._process_canal_upload(canal_data, hoje, retry_attempt=1)

                logger.info(f"Resultado upload {canal_data['channel_name']}: {resultado}")

                if resultado.get('status') == 'sem_video':
                    logger.warning(f"Nenhum video pronto na planilha de {canal_data['channel_name']}")
                elif resultado.get('status') == 'erro':
                    logger.error(f"Erro no upload: {resultado.get('error')}")
                elif resultado.get('status') == 'sucesso':
                    logger.info(f"Upload realizado com sucesso: {resultado.get('video_title')}")

            except Exception as e:
                logger.error(f"Erro no upload forcado: {e}")

        background_tasks.add_task(run_upload)

        return {
            'status': 'processing',
            'message': f'Upload iniciado para {canal_data["channel_name"]}',
            'channel_id': channel_id,
            'spreadsheet_id': canal_data['spreadsheet_id']
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao forcar upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/yt-upload/historico-completo")
async def get_historico_completo(
    days: int = 30,
    status_filter: Optional[str] = None  # sucesso, erro, sem_video
):
    """
    Retorna histórico completo de uploads de TODOS os canais

    Query params:
        - days: Últimos X dias (padrão: 30)
        - status_filter: Filtrar por status (opcional)

    Returns:
        {
            "total_dias": 30,
            "total_registros": 150,
            "historico_por_data": [
                {
                    "data": "2026-02-11",
                    "total_uploads": 3,
                    "sucesso": 3,
                    "erro": 0,
                    "sem_video": 17,
                    "canais": [
                        {
                            "channel_name": "Canal X",
                            "video_titulo": "Video Y",
                            "status": "sucesso",
                            "hora": "05:30:15",
                            "tentativa_numero": 1
                        }
                    ]
                }
            ]
        }
    """
    try:
        from datetime import date, timedelta

        hoje = date.today()
        data_inicio = hoje - timedelta(days=days)

        # Query base
        query = supabase.table('yt_canal_upload_historico')\
            .select('*')\
            .gte('data', data_inicio.isoformat())\
            .order('data', desc=True)\
            .order('hora_processamento', desc=True)

        # Filtro opcional de status
        if status_filter:
            query = query.eq('status', status_filter)

        result = query.execute()

        # Agrupar por data
        historico_por_data = {}
        for record in result.data:
            data_str = record['data']

            if data_str not in historico_por_data:
                historico_por_data[data_str] = {
                    'data': data_str,
                    'total_uploads': 0,
                    'sucesso': 0,
                    'erro': 0,
                    'sem_video': 0,
                    'canais': []
                }

            # Contadores
            historico_por_data[data_str]['total_uploads'] += 1
            status = record.get('status', 'pendente')
            if status in ['sucesso', 'erro', 'sem_video']:
                historico_por_data[data_str][status] += 1

            # Dados do canal
            hora = record.get('hora_processamento', '')
            if hora:
                # Converter para horário de Brasília (UTC-3)
                from datetime import datetime
                import pytz

                try:
                    # Parse do timestamp UTC
                    dt_utc = datetime.fromisoformat(hora.replace('Z', '+00:00'))
                    # Converter para Brasília
                    brasil_tz = pytz.timezone('America/Sao_Paulo')
                    dt_brasil = dt_utc.astimezone(brasil_tz)
                    hora_formatada = dt_brasil.strftime('%H:%M:%S')
                except:
                    hora_formatada = hora.split('T')[1][:8] if 'T' in hora else hora[:8] if hora else '-'
            else:
                hora_formatada = '-'

            historico_por_data[data_str]['canais'].append({
                'channel_name': record.get('channel_name', '-'),
                'video_titulo': record.get('video_titulo', '-'),
                'status': status,
                'hora': hora_formatada,
                'tentativa_numero': record.get('tentativa_numero', 1),
                'youtube_video_id': record.get('youtube_video_id'),
                'erro_mensagem': record.get('erro_mensagem')
            })

        # Converter dict para lista ordenada
        historico_lista = sorted(
            historico_por_data.values(),
            key=lambda x: x['data'],
            reverse=True
        )

        return {
            'total_dias': len(historico_lista),
            'total_registros': len(result.data),
            'data_inicio': data_inicio.isoformat(),
            'data_fim': hoje.isoformat(),
            'historico_por_data': historico_lista
        }

    except Exception as e:
        logger.error(f"Erro ao buscar histórico completo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/yt-upload/failed")
async def get_failed_uploads(limit: int = 50):
    """
    Lista uploads que falharam (status='failed').
    Mostra detalhes do erro e quantas tentativas foram feitas.
    """
    result = supabase.table('yt_upload_queue')\
        .select('id, channel_id, titulo, status, error_message, retry_count, created_at, completed_at, spreadsheet_id, sheets_row_number')\
        .eq('status', 'failed')\
        .order('completed_at', desc=True)\
        .limit(limit)\
        .execute()

    # Enriquece com nome do canal
    uploads = []
    for upload in result.data:
        channel = supabase.table('yt_channels')\
            .select('channel_name')\
            .eq('channel_id', upload['channel_id'])\
            .limit(1)\
            .execute()

        upload['channel_name'] = channel.data[0]['channel_name'] if channel.data else 'Desconhecido'
        upload['can_retry'] = (upload.get('retry_count', 0) or 0) < 3
        uploads.append(upload)

    return {
        'total': len(uploads),
        'uploads': uploads
    }


@app.post("/api/yt-upload/retry/{upload_id}")
async def retry_failed_upload(upload_id: int, background_tasks: BackgroundTasks):
    """
    Reprocessa um upload específico que falhou.

    - Verifica se upload existe e está com status='failed'
    - Verifica se retry_count < 3
    - Reseta status para 'pending' e processa novamente
    """
    try:
        # Busca upload
        upload = supabase.table('yt_upload_queue')\
            .select('*')\
            .eq('id', upload_id)\
            .limit(1)\
            .execute()

        if not upload.data:
            raise HTTPException(status_code=404, detail=f"Upload {upload_id} não encontrado")

        upload_data = upload.data[0]

        # Verifica status
        if upload_data['status'] != 'failed':
            raise HTTPException(
                status_code=400,
                detail=f"Upload {upload_id} não está com status 'failed' (atual: {upload_data['status']})"
            )

        # Verifica retry_count
        retry_count = upload_data.get('retry_count', 0) or 0
        if retry_count >= 3:
            raise HTTPException(
                status_code=400,
                detail=f"Upload {upload_id} já atingiu limite de 3 tentativas"
            )

        # Reseta status para pending
        supabase.table('yt_upload_queue').update({
            'status': 'pending',
            'error_message': None,
            'started_at': None,
            'completed_at': None
        }).eq('id', upload_id).execute()

        logger.info(f"🔁 Retry manual para upload {upload_id} (tentativa {retry_count + 1}/3)")

        # Processa em background
        background_tasks.add_task(process_upload_task, upload_id)

        return {
            'status': 'processing',
            'message': f'Retry iniciado para upload {upload_id}',
            'upload_id': upload_id,
            'retry_count': retry_count + 1,
            'titulo': upload_data['titulo'],
            'channel_id': upload_data['channel_id']
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao reprocessar upload {upload_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/yt-upload/retry-all-failed")
async def retry_all_failed_uploads(background_tasks: BackgroundTasks):
    """
    Reprocessa TODOS os uploads que falharam e ainda podem ser retentados.

    - Apenas uploads com status='failed' e retry_count < 3
    - Processa um por vez em sequência
    """
    try:
        # Busca todos os uploads failed que podem ser retentados
        result = supabase.table('yt_upload_queue')\
            .select('id, channel_id, titulo, retry_count')\
            .eq('status', 'failed')\
            .lt('retry_count', 3)\
            .execute()

        if not result.data:
            return {
                'status': 'no_uploads',
                'message': 'Nenhum upload com erro elegível para retry',
                'total': 0
            }

        # Reseta status de todos para pending
        upload_ids = [u['id'] for u in result.data]

        for upload_id in upload_ids:
            supabase.table('yt_upload_queue').update({
                'status': 'pending',
                'error_message': None,
                'started_at': None,
                'completed_at': None
            }).eq('id', upload_id).execute()

        logger.info(f"🔁 Retry em massa: {len(upload_ids)} uploads reativados")

        # Processa cada um em background (com delay entre eles)
        async def process_all():
            for upload_id in upload_ids:
                await process_upload_task(upload_id)
                await asyncio.sleep(5)  # 5s entre uploads

        background_tasks.add_task(process_all)

        return {
            'status': 'processing',
            'message': f'Retry iniciado para {len(upload_ids)} uploads',
            'total': len(upload_ids),
            'upload_ids': upload_ids
        }

    except Exception as e:
        logger.error(f"Erro ao reprocessar uploads em massa: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/yt-upload/clear-old-failed")
async def clear_old_failed_uploads():
    """
    Remove uploads antigos que falharam e já atingiram o limite de retry.

    - Deleta uploads com status='failed' e retry_count >= 3
    - Usado para limpar a fila de uploads antigos que não serão mais retentados
    """
    try:
        # Busca uploads failed com retry_count >= 3
        result = supabase.table('yt_upload_queue')\
            .select('id, titulo, channel_id, created_at')\
            .eq('status', 'failed')\
            .gte('retry_count', 3)\
            .execute()

        if not result.data:
            return {
                'status': 'no_uploads',
                'message': 'Nenhum upload antigo com erro para limpar',
                'deleted': 0
            }

        # Deleta todos
        upload_ids = [u['id'] for u in result.data]

        for upload_id in upload_ids:
            supabase.table('yt_upload_queue')\
                .delete()\
                .eq('id', upload_id)\
                .execute()

        logger.info(f"🗑️ Limpeza: {len(upload_ids)} uploads antigos com erro removidos")

        return {
            'status': 'success',
            'message': f'{len(upload_ids)} uploads antigos com erro removidos',
            'deleted': len(upload_ids)
        }

    except Exception as e:
        logger.error(f"Erro ao limpar uploads antigos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# SISTEMA KANBAN - FUNÇÕES
# =====================================================

async def get_kanban_structure():
    """
    Retorna a estrutura completa do Kanban com cards, subnichos e canais.
    Apenas canais tipo='nosso'.
    """
    try:
        # Buscar todos os canais nossos
        canais = db.supabase.table("canais_monitorados")\
            .select("*")\
            .eq("tipo", "nosso")\
            .order("subnicho", desc=False)\
            .order("nome_canal", desc=False)\
            .execute()

        # Separar monetizados e não monetizados
        monetizados = []
        nao_monetizados = []

        for canal in canais.data:
            # Calcular dias no status
            if canal.get("kanban_status_since"):
                try:
                    # Tentar vários formatos de data
                    date_str = canal["kanban_status_since"]
                    if "Z" in date_str:
                        date_str = date_str.replace("Z", "+00:00")

                    # Adicionar zeros se necessário para microsegundos
                    if "." in date_str:
                        parts = date_str.split(".")
                        microsec_part = parts[1].split("+")[0]
                        # Garantir 6 dígitos nos microsegundos
                        if len(microsec_part) < 6:
                            microsec_part = microsec_part.ljust(6, '0')
                        date_str = f"{parts[0]}.{microsec_part}+00:00"

                    status_date = datetime.fromisoformat(date_str)
                    dias_no_status = (datetime.now(timezone.utc) - status_date).days
                except Exception as e:
                    logger.warning(f"Erro ao processar data: {e}")
                    dias_no_status = 0
            else:
                dias_no_status = 0

            # Mapear status para label e cor
            status_map = {
                # Não monetizados
                "em_teste_inicial": ("Em Teste Inicial", "yellow"),
                "demonstrando_tracao": ("Demonstrando Tração", "green"),
                "em_andamento": ("Em Andamento p/ Monetizar", "orange"),
                "monetizado": ("Monetizado", "blue"),
                # Monetizados
                "em_crescimento": ("Em Crescimento", "green"),
                "em_testes_novos": ("Em Testes Novos", "yellow"),
                "canal_constante": ("Canal Constante", "blue"),
            }

            status_info = status_map.get(canal.get("kanban_status"), ("Sem Status", "gray"))

            # Buscar total de notas do canal
            notas = db.supabase.table("kanban_notes")\
                .select("id")\
                .eq("canal_id", canal["id"])\
                .execute()

            canal_info = {
                "id": canal["id"],
                "nome": canal["nome_canal"],
                "subnicho": canal["subnicho"],
                "lingua": canal.get("lingua", ""),
                "url_canal": canal.get("url_canal", ""),
                "kanban_status": canal.get("kanban_status"),
                "status_label": status_info[0],
                "status_color": status_info[1],
                "status_since": canal.get("kanban_status_since"),
                "dias_no_status": dias_no_status,
                "total_notas": len(notas.data) if notas.data else 0
            }

            if canal.get("monetizado"):
                monetizados.append(canal_info)
            else:
                nao_monetizados.append(canal_info)

        # Agrupar por subnicho
        def agrupar_por_subnicho(canais_list):
            subnichos = {}
            for canal in canais_list:
                subnicho = canal["subnicho"] or "Sem Subnicho"
                if subnicho not in subnichos:
                    subnichos[subnicho] = {
                        "nome": subnicho,
                        "total": 0,
                        "canais": []
                    }
                subnichos[subnicho]["canais"].append(canal)
                subnichos[subnicho]["total"] += 1
            return subnichos

        return {
            "monetizados": {
                "total": len(monetizados),
                "subnichos": agrupar_por_subnicho(monetizados)
            },
            "nao_monetizados": {
                "total": len(nao_monetizados),
                "subnichos": agrupar_por_subnicho(nao_monetizados)
            }
        }

    except Exception as e:
        logger.error(f"Erro ao buscar estrutura Kanban: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_kanban_board(canal_id: int):
    """
    Retorna o quadro Kanban individual de um canal.
    """
    try:
        # Buscar dados do canal
        canal = db.supabase.table("canais_monitorados")\
            .select("*")\
            .eq("id", canal_id)\
            .eq("tipo", "nosso")\
            .single()\
            .execute()

        if not canal.data:
            raise HTTPException(status_code=404, detail="Canal não encontrado")

        # Calcular dias no status
        dias_no_status = 0
        if canal.data.get("kanban_status_since"):
            try:
                # Tentar vários formatos de data
                date_str = canal.data["kanban_status_since"]
                if "Z" in date_str:
                    date_str = date_str.replace("Z", "+00:00")

                # Adicionar zeros se necessário para microsegundos
                if "." in date_str:
                    parts = date_str.split(".")
                    microsec_part = parts[1].split("+")[0]
                    # Garantir 6 dígitos nos microsegundos
                    if len(microsec_part) < 6:
                        microsec_part = microsec_part.ljust(6, '0')
                    date_str = f"{parts[0]}.{microsec_part}+00:00"

                status_date = datetime.fromisoformat(date_str)
                dias_no_status = (datetime.now(timezone.utc) - status_date).days
            except Exception as e:
                logger.warning(f"Erro ao processar data: {e}")
                dias_no_status = 0

        # Definir colunas baseado se é monetizado ou não
        if canal.data.get("monetizado"):
            colunas = [
                {
                    "id": "em_crescimento",
                    "label": "Em Crescimento",
                    "emoji": "🟢",
                    "descricao": "Canal saudável e escalando",
                    "is_current": canal.data.get("kanban_status") == "em_crescimento"
                },
                {
                    "id": "em_testes_novos",
                    "label": "Em Testes Novos",
                    "emoji": "🟡",
                    "descricao": "Perdeu tração, testando novas estratégias",
                    "is_current": canal.data.get("kanban_status") == "em_testes_novos"
                },
                {
                    "id": "canal_constante",
                    "label": "Canal Constante",
                    "emoji": "🔵",
                    "descricao": "Estável, performance previsível",
                    "is_current": canal.data.get("kanban_status") == "canal_constante"
                }
            ]
        else:
            colunas = [
                {
                    "id": "em_teste_inicial",
                    "label": "Em Teste Inicial",
                    "emoji": "🟡",
                    "descricao": "Canal testando micro-nichos pela primeira vez",
                    "is_current": canal.data.get("kanban_status") == "em_teste_inicial"
                },
                {
                    "id": "demonstrando_tracao",
                    "label": "Demonstrando Tração",
                    "emoji": "🟢",
                    "descricao": "Sinais positivos, vídeos viralizando",
                    "is_current": canal.data.get("kanban_status") == "demonstrando_tracao"
                },
                {
                    "id": "em_andamento",
                    "label": "Em Andamento p/ Monetizar",
                    "emoji": "🟠",
                    "descricao": "Caminhando para 1K subs e 4K horas",
                    "is_current": canal.data.get("kanban_status") == "em_andamento"
                },
                {
                    "id": "monetizado",
                    "label": "Monetizado",
                    "emoji": "🔵",
                    "descricao": "Atingiu requisitos de monetização",
                    "is_current": canal.data.get("kanban_status") == "monetizado"
                }
            ]

        # Buscar notas do canal
        notas = db.supabase.table("kanban_notes")\
            .select("*")\
            .eq("canal_id", canal_id)\
            .order("position", desc=False)\
            .execute()

        # Buscar histórico (últimos 20 registros não deletados)
        historico = db.supabase.table("kanban_history")\
            .select("*")\
            .eq("canal_id", canal_id)\
            .eq("is_deleted", False)\
            .order("performed_at", desc=True)\
            .limit(20)\
            .execute()

        return {
            "canal": {
                "id": canal.data["id"],
                "nome": canal.data["nome_canal"],
                "subnicho": canal.data["subnicho"],
                "monetizado": canal.data.get("monetizado", False),
                "status_atual": canal.data.get("kanban_status"),
                "status_since": canal.data.get("kanban_status_since"),
                "dias_no_status": dias_no_status
            },
            "colunas": colunas,
            "notas": notas.data if notas.data else [],
            "historico": historico.data if historico.data else []
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar kanban board: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def move_kanban_status(canal_id: int, new_status: str):
    """
    Move um canal para um novo status no Kanban.
    """
    try:
        # Verificar se o canal existe e é nosso
        canal = db.supabase.table("canais_monitorados")\
            .select("id, nome_canal, kanban_status")\
            .eq("id", canal_id)\
            .eq("tipo", "nosso")\
            .single()\
            .execute()

        if not canal.data:
            raise HTTPException(status_code=404, detail="Canal não encontrado")

        old_status = canal.data.get("kanban_status")

        # Atualizar status
        result = db.supabase.table("canais_monitorados")\
            .update({
                "kanban_status": new_status,
                "kanban_status_since": datetime.now(timezone.utc).isoformat()
            })\
            .eq("id", canal_id)\
            .execute()

        # Registrar no histórico
        db.supabase.table("kanban_history").insert({
            "canal_id": canal_id,
            "action_type": "status_change",
            "description": f"Status mudou de {old_status or 'indefinido'} para {new_status}",
            "details": {
                "from_status": old_status,
                "to_status": new_status
            }
        }).execute()

        return {"success": True, "message": "Status atualizado com sucesso"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao mover status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def create_kanban_note(canal_id: int, note_text: str, note_color: str = "yellow", coluna_id: Optional[str] = None):
    """
    Cria uma nova nota para um canal.
    Agora suporta coluna_id para permitir notas em qualquer coluna.
    """
    try:
        # Verificar se o canal existe e é nosso
        canal = db.supabase.table("canais_monitorados")\
            .select("id, nome_canal")\
            .eq("id", canal_id)\
            .eq("tipo", "nosso")\
            .single()\
            .execute()

        if not canal.data:
            raise HTTPException(status_code=404, detail="Canal não encontrado")

        # Buscar última posição
        last_note = db.supabase.table("kanban_notes")\
            .select("position")\
            .eq("canal_id", canal_id)\
            .order("position", desc=True)\
            .limit(1)\
            .execute()

        next_position = 1
        if last_note.data:
            next_position = last_note.data[0]["position"] + 1

        # Criar nota com suporte a coluna_id
        nota_data = {
            "canal_id": canal_id,
            "note_text": note_text,
            "note_color": note_color,
            "position": next_position
        }

        # Adicionar coluna_id se fornecido
        if coluna_id:
            nota_data["coluna_id"] = coluna_id

        nota = db.supabase.table("kanban_notes").insert(nota_data).execute()

        # Registrar no histórico
        db.supabase.table("kanban_history").insert({
            "canal_id": canal_id,
            "action_type": "note_added",
            "description": f"Nota {note_color} adicionada",
            "details": {
                "note_id": nota.data[0]["id"],
                "color": note_color
            }
        }).execute()

        return nota.data[0]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar nota: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def update_kanban_note(note_id: int, note_text: Optional[str] = None, note_color: Optional[str] = None, coluna_id: Optional[str] = None):
    """
    Atualiza uma nota existente.
    Agora suporta mover nota entre colunas com coluna_id.
    """
    try:
        # Buscar nota atual
        nota_atual = db.supabase.table("kanban_notes")\
            .select("*")\
            .eq("id", note_id)\
            .single()\
            .execute()

        if not nota_atual.data:
            raise HTTPException(status_code=404, detail="Nota não encontrada")

        # Preparar campos para atualizar
        update_fields = {"updated_at": datetime.now(timezone.utc).isoformat()}
        if note_text is not None:
            update_fields["note_text"] = note_text
        if note_color is not None:
            update_fields["note_color"] = note_color
        if coluna_id is not None:
            update_fields["coluna_id"] = coluna_id

        # Atualizar nota
        result = db.supabase.table("kanban_notes")\
            .update(update_fields)\
            .eq("id", note_id)\
            .execute()

        # Registrar no histórico
        db.supabase.table("kanban_history").insert({
            "canal_id": nota_atual.data["canal_id"],
            "action_type": "note_edited",
            "description": f"Nota editada",
            "details": {
                "note_id": note_id,
                "old_color": nota_atual.data["note_color"],
                "new_color": note_color or nota_atual.data["note_color"]
            }
        }).execute()

        return result.data[0]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar nota: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def delete_kanban_note(note_id: int):
    """
    Deleta uma nota.
    """
    try:
        # Buscar nota antes de deletar
        nota = db.supabase.table("kanban_notes")\
            .select("canal_id, note_color")\
            .eq("id", note_id)\
            .single()\
            .execute()

        if not nota.data:
            raise HTTPException(status_code=404, detail="Nota não encontrada")

        # Deletar nota
        db.supabase.table("kanban_notes")\
            .delete()\
            .eq("id", note_id)\
            .execute()

        # Registrar no histórico
        db.supabase.table("kanban_history").insert({
            "canal_id": nota.data["canal_id"],
            "action_type": "note_deleted",
            "description": f"Nota {nota.data['note_color']} removida",
            "details": {
                "note_id": note_id,
                "color": nota.data["note_color"]
            }
        }).execute()

        return {"success": True, "message": "Nota deletada com sucesso"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao deletar nota: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def move_note_to_column(note_id: int, target_column: str):
    """
    Move uma nota para outra coluna.
    """
    try:
        # Buscar nota atual
        nota_atual = db.supabase.table("kanban_notes")\
            .select("*")\
            .eq("id", note_id)\
            .single()\
            .execute()

        if not nota_atual.data:
            raise HTTPException(status_code=404, detail="Nota não encontrada")

        old_column = nota_atual.data.get("coluna_id")

        # Atualizar coluna da nota
        result = db.supabase.table("kanban_notes")\
            .update({"coluna_id": target_column})\
            .eq("id", note_id)\
            .execute()

        if not result.data:
            raise HTTPException(status_code=400, detail="Erro ao mover nota")

        # Buscar informações do canal para o histórico
        canal = db.supabase.table("canais_monitorados")\
            .select("nome_canal")\
            .eq("id", nota_atual.data["canal_id"])\
            .single()\
            .execute()

        # Registrar no histórico
        db.supabase.table("kanban_history").insert({
            "canal_id": nota_atual.data["canal_id"],
            "action_type": "note_moved",
            "description": f"Nota movida de {old_column or 'sem coluna'} para {target_column}",
            "details": {
                "note_id": note_id,
                "from_column": old_column,
                "to_column": target_column,
                "note_color": nota_atual.data["note_color"]
            }
        }).execute()

        return {
            "success": True,
            "message": "Nota movida com sucesso",
            "data": result.data[0]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao mover nota: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def reorder_kanban_notes(canal_id: int, note_positions: List[Dict[str, int]]):
    """
    Reordena as notas de um canal.
    """
    try:
        # Verificar se o canal existe
        canal = db.supabase.table("canais_monitorados")\
            .select("id")\
            .eq("id", canal_id)\
            .eq("tipo", "nosso")\
            .single()\
            .execute()

        if not canal.data:
            raise HTTPException(status_code=404, detail="Canal não encontrado")

        # Atualizar posições
        for item in note_positions:
            db.supabase.table("kanban_notes")\
                .update({"position": item["position"]})\
                .eq("id", item["note_id"])\
                .eq("canal_id", canal_id)\
                .execute()

        # Registrar no histórico
        db.supabase.table("kanban_history").insert({
            "canal_id": canal_id,
            "action_type": "note_reordered",
            "description": "Notas reordenadas",
            "details": {"positions": note_positions}
        }).execute()

        return {"success": True, "message": "Notas reordenadas com sucesso"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao reordenar notas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_kanban_history(canal_id: int, limit: int = 50):
    """
    Retorna o histórico de ações de um canal.
    """
    try:
        historico = db.supabase.table("kanban_history")\
            .select("*")\
            .eq("canal_id", canal_id)\
            .eq("is_deleted", False)\
            .order("performed_at", desc=True)\
            .limit(limit)\
            .execute()

        return historico.data if historico.data else []

    except Exception as e:
        logger.error(f"Erro ao buscar histórico: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def delete_history_item(history_id: int):
    """
    Remove um item do histórico (soft delete).
    """
    try:
        result = db.supabase.table("kanban_history")\
            .update({"is_deleted": True})\
            .eq("id", history_id)\
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Item de histórico não encontrado")

        return {"success": True, "message": "Item removido do histórico"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao deletar item do histórico: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================
# SISTEMA KANBAN - ENDPOINTS
# =====================================================

@app.get("/api/kanban/structure")
async def kanban_structure_endpoint():
    """Retorna a estrutura completa do Kanban"""
    return await get_kanban_structure()

@app.get("/api/kanban/canal/{canal_id}/board")
async def kanban_board_endpoint(canal_id: int):
    """Retorna o quadro Kanban de um canal específico"""
    return await get_kanban_board(canal_id)

@app.patch("/api/kanban/canal/{canal_id}/move-status")
async def kanban_move_status_endpoint(canal_id: int, request: KanbanMoveStatusRequest):
    """Move um canal para outro status"""
    return await move_kanban_status(canal_id, request.new_status)

@app.post("/api/kanban/canal/{canal_id}/note")
async def kanban_create_note_endpoint(canal_id: int, request: KanbanNoteRequest):
    """Cria uma nova nota para o canal"""
    return await create_kanban_note(canal_id, request.note_text, request.note_color, request.coluna_id)

@app.patch("/api/kanban/note/{note_id}")
async def kanban_update_note_endpoint(note_id: int, request: KanbanNoteUpdateRequest):
    """Atualiza uma nota existente"""
    return await update_kanban_note(note_id, request.note_text, request.note_color, request.coluna_id)

@app.delete("/api/kanban/note/{note_id}")
async def kanban_delete_note_endpoint(note_id: int):
    """Deleta uma nota"""
    return await delete_kanban_note(note_id)

@app.patch("/api/kanban/note/{note_id}/move")
async def kanban_move_note_endpoint(note_id: int, request: KanbanMoveNoteRequest):
    """Move uma nota para outra coluna (compatível com stage_id e coluna_id)"""
    target_column = request.target_column
    if not target_column:
        raise HTTPException(status_code=400, detail="stage_id ou coluna_id é obrigatório")
    return await move_note_to_column(note_id, target_column)

@app.patch("/api/kanban/canal/{canal_id}/reorder-notes")
async def kanban_reorder_notes_endpoint(canal_id: int, request: KanbanReorderNotesRequest):
    """Reordena as notas de um canal"""
    return await reorder_kanban_notes(canal_id, request.note_positions)

@app.get("/api/kanban/canal/{canal_id}/history")
async def kanban_history_endpoint(canal_id: int, limit: int = 50):
    """Retorna o histórico de ações do canal"""
    return await get_kanban_history(canal_id, limit)

@app.delete("/api/kanban/history/{history_id}")
async def kanban_delete_history_endpoint(history_id: int):
    """Remove um item do histórico (soft delete)"""
    return await delete_history_item(history_id)

# ============================================================
# DASHBOARD DE UPLOAD v2 - Integrado no main.py
# Acesso: /dash-upload
# ============================================================

def _extrair_hora(timestamp_str):
    """Extrai HH:MM do timestamp (sem conversao de timezone)"""
    if not timestamp_str:
        return None
    try:
        ts = str(timestamp_str)
        if 'T' in ts and len(ts) >= 16:
            return ts[11:16]
        return None
    except:
        return None

_dash_cache = {'data': None, 'timestamp': 0}
_DASH_CACHE_TTL = 3

DASH_UPLOAD_HTML = '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <title>Upload Dashboard</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        :root {
            --bg-primary: #0a0a0b;
            --bg-secondary: #141415;
            --bg-tertiary: #1c1c1e;
            --bg-elevated: #1f1f22;
            --border-primary: #27272a;
            --border-secondary: #3f3f46;
            --text-primary: #fafafa;
            --text-secondary: #a1a1aa;
            --text-tertiary: #71717a;
            --success: #22c55e;
            --success-muted: rgba(34, 197, 94, 0.12);
            --warning: #eab308;
            --warning-muted: rgba(234, 179, 8, 0.12);
            --error: #ef4444;
            --error-muted: rgba(239, 68, 68, 0.12);
            --info: #3b82f6;
            --info-muted: rgba(59, 130, 246, 0.12);
            --pending: #a855f7;
            --pending-muted: rgba(168, 85, 247, 0.12);
            --accent: #f97316;
            --radius-sm: 6px;
            --radius-md: 8px;
            --radius-lg: 12px;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: var(--bg-primary);
            color: var(--text-primary);
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
            padding-bottom: 48px;
            min-height: 100vh;
        }
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: var(--bg-primary); }
        ::-webkit-scrollbar-thumb { background: var(--border-secondary); border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--text-tertiary); }
        .page-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 32px 16px;
            border-bottom: 1px solid var(--border-primary);
            margin-bottom: 24px;
        }
        .header-title { font-size: 22px; font-weight: 600; letter-spacing: -0.025em; color: var(--text-primary); }
        .header-subtitle { font-size: 13px; color: var(--text-tertiary); margin-top: 2px; }
        .live-indicator { display: flex; align-items: center; gap: 8px; font-size: 13px; color: var(--text-secondary); }
        .live-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--success); animation: pulse-live 2s ease-in-out infinite; }
        @keyframes pulse-live {
            0%, 100% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.4); }
            50% { box-shadow: 0 0 0 6px rgba(34, 197, 94, 0); }
        }
        .stats-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; padding: 0 32px; margin-bottom: 28px; }
        .stat-card { background: var(--bg-secondary); border: 1px solid var(--border-primary); border-radius: var(--radius-md); padding: 20px; cursor: pointer; transition: all 0.15s ease; position: relative; display: flex; flex-direction: column; justify-content: space-between; min-height: 90px; }
        .stat-card:hover { border-color: var(--border-secondary); background: var(--bg-tertiary); }
        .stat-card.active { border-left: 3px solid var(--card-accent, var(--info)); background: var(--bg-tertiary); }
        .stat-card--total { --card-accent: var(--info); }
        .stat-card--sucesso { --card-accent: var(--success); }
        .stat-card--sem_video { --card-accent: var(--warning); }
        .stat-card--erro { --card-accent: var(--error); }
        .stat-card--historico { --card-accent: var(--accent); border-style: dashed; }
        .stat-card--total:hover { border-color: var(--info); }
        .stat-card--sucesso:hover { border-color: var(--success); }
        .stat-card--sem_video:hover { border-color: var(--warning); }
        .stat-card--erro:hover { border-color: var(--error); }
        .stat-card--historico:hover { border-color: var(--accent); }
        .stat-value { font-size: 32px; font-weight: 700; line-height: 1; margin-bottom: 6px; }
        .stat-value--total { color: var(--info); }
        .stat-value--sucesso { color: var(--success); }
        .stat-value--sem_video { color: var(--warning); }
        .stat-value--erro { color: var(--error); }
        .stat-value--historico { color: var(--accent); font-size: 32px; }
        .stat-label { font-size: 11px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-tertiary); }
        .content { padding: 0 32px; }
        .section { background: var(--bg-secondary); border: 1px solid var(--border-primary); border-radius: var(--radius-lg); margin-bottom: 16px; overflow: hidden; border-left: 3px solid var(--section-accent, var(--border-primary)); }
        .section-header { padding: 14px 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-primary); }
        .section-title { display: flex; align-items: center; gap: 10px; font-size: 14px; font-weight: 600; }
        .section-icon { width: 28px; height: 28px; border-radius: var(--radius-sm); display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: 700; background: var(--section-accent-muted, var(--bg-tertiary)); color: var(--section-accent, var(--text-secondary)); }
        .section-count { font-size: 12px; font-weight: 400; color: var(--text-tertiary); }
        .section-pills { display: flex; gap: 8px; }
        .stat-pill { font-size: 11px; font-weight: 500; padding: 3px 10px; border-radius: 9999px; }
        .stat-pill--success { background: var(--success-muted); color: var(--success); }
        .stat-pill--warning { background: var(--warning-muted); color: var(--warning); }
        .stat-pill--error { background: var(--error-muted); color: var(--error); }
        .stat-pill--pending { background: var(--pending-muted); color: var(--pending); }
        .channel-table { width: 100%; border-collapse: collapse; }
        .channel-table th { padding: 10px 16px; text-align: left; font-size: 11px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-tertiary); border-bottom: 1px solid var(--border-primary); background: transparent; }
        .channel-table td { padding: 10px 16px; font-size: 13px; border-bottom: 1px solid var(--border-primary); vertical-align: middle; }
        .channel-table tr:last-child td { border-bottom: none; }
        .channel-table tbody tr { transition: background 0.1s ease; }
        .channel-table tbody tr:hover { background: rgba(255, 255, 255, 0.02); }
        .cell-channel { display: flex; align-items: center; gap: 6px; }
        .channel-name { font-weight: 500; color: var(--text-primary); white-space: nowrap; }
        .lang-tag { font-size: 10px; color: var(--text-tertiary); background: var(--bg-tertiary); padding: 1px 6px; border-radius: 3px; font-weight: 500; letter-spacing: 0.02em; }
        .monetized-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--success); display: inline-block; flex-shrink: 0; }
        .status-badge { display: inline-flex; align-items: center; padding: 3px 10px; border-radius: 9999px; font-size: 11px; font-weight: 600; }
        .status-badge--success { background: var(--success-muted); color: var(--success); }
        .status-badge--sem_video { background: var(--warning-muted); color: var(--warning); }
        .status-badge--error { background: var(--error-muted); color: var(--error); }
        .status-badge--pending { background: var(--pending-muted); color: var(--pending); }
        .video-title { max-width: 350px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--text-secondary); font-size: 13px; }
        .cell-time { color: var(--text-tertiary); font-size: 13px; font-variant-numeric: tabular-nums; }
        .cell-actions { display: flex; gap: 4px; }
        .btn-icon { width: 38px; height: 38px; display: inline-flex; align-items: center; justify-content: center; border: 1px solid transparent; border-radius: var(--radius-sm); background: transparent; cursor: pointer; font-size: 20px; color: var(--text-secondary); transition: all 0.15s ease; text-decoration: none; }
        .btn-icon:hover { background: var(--bg-tertiary); border-color: var(--border-secondary); color: var(--text-primary); }
        .btn-icon:active { transform: scale(0.9); }
        .btn-icon:disabled { opacity: 0.3; cursor: not-allowed; }
        .btn-icon:disabled:hover { background: transparent; border-color: transparent; }
        @keyframes upload-spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        @keyframes upload-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        @keyframes success-pop { 0% { transform: scale(0.5); opacity: 0; } 50% { transform: scale(1.2); } 100% { transform: scale(1); opacity: 1; } }
        .btn-icon--uploading { animation: upload-spin 2s linear infinite, upload-pulse 1.2s ease-in-out infinite; background: rgba(168, 85, 247, 0.15); border-color: rgba(168, 85, 247, 0.3); pointer-events: none; color: var(--text-primary); }
        .btn-icon--upload-success { animation: success-pop 0.4s ease-out; background: rgba(34, 197, 94, 0.15); border-color: rgba(34, 197, 94, 0.3); pointer-events: none; }
        .btn-icon--upload-error { background: rgba(239, 68, 68, 0.15); border-color: rgba(239, 68, 68, 0.3); pointer-events: none; }
        .status-bar { position: fixed; bottom: 0; left: 0; right: 0; background: rgba(20, 20, 21, 0.85); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border-top: 1px solid var(--border-primary); padding: 10px 32px; display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: var(--text-tertiary); z-index: 50; }
        .status-bar-left, .status-bar-right { display: flex; align-items: center; gap: 16px; }
        .status-bar-sep { width: 1px; height: 12px; background: var(--border-primary); }
        .modal-overlay { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.6); backdrop-filter: blur(4px); -webkit-backdrop-filter: blur(4px); z-index: 1000; display: flex; align-items: flex-start; justify-content: center; padding-top: 5vh; opacity: 0; visibility: hidden; pointer-events: none; transition: opacity 0.2s ease, visibility 0s 0.2s; }
        .modal-overlay.show { opacity: 1; visibility: visible; pointer-events: auto; transition: opacity 0.2s ease, visibility 0s 0s; }
        .modal-panel { background: var(--bg-elevated); border: 1px solid var(--border-primary); border-radius: var(--radius-lg); width: 90%; max-width: 960px; max-height: 80vh; overflow: hidden; display: flex; flex-direction: column; transform: translateY(-12px) scale(0.98); transition: transform 0.2s ease; }
        .modal-overlay.show .modal-panel { transform: translateY(0) scale(1); }
        .modal-header { padding: 20px 24px; border-bottom: 1px solid var(--border-primary); display: flex; justify-content: space-between; align-items: center; flex-shrink: 0; }
        .modal-title { font-size: 16px; font-weight: 600; color: var(--text-primary); }
        .btn-close { width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border-radius: var(--radius-sm); border: none; background: transparent; color: var(--text-secondary); font-size: 18px; cursor: pointer; transition: all 0.15s ease; }
        .btn-close:hover { background: var(--bg-tertiary); color: var(--text-primary); }
        .modal-body { padding: 20px 24px; overflow-y: auto; flex: 1; }
        .modal-table { width: 100%; border-collapse: collapse; }
        .modal-table th { text-align: left; padding: 8px 12px; font-size: 11px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-tertiary); border-bottom: 1px solid var(--border-primary); }
        .modal-table td { padding: 8px 12px; font-size: 13px; border-bottom: 1px solid var(--border-primary); color: var(--text-secondary); }
        .modal-table tr:last-child td { border-bottom: none; }
        .modal-table tbody tr:hover { background: rgba(255, 255, 255, 0.02); }
        .modal-summary { display: flex; gap: 16px; align-items: center; padding: 14px 16px; background: var(--bg-tertiary); border: 1px solid var(--border-primary); border-radius: var(--radius-md); margin-bottom: 20px; font-size: 13px; }
        .modal-summary-label { font-weight: 600; color: var(--text-primary); }
        .modal-summary-stat { font-weight: 500; }
        .accordion-trigger { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; background: var(--bg-tertiary); border: 1px solid var(--border-primary); border-radius: var(--radius-sm); cursor: pointer; margin-bottom: 2px; transition: background 0.15s ease; user-select: none; }
        .accordion-trigger:hover { background: var(--bg-elevated); }
        .accordion-trigger:active { transform: scale(0.995); }
        .accordion-arrow { display: inline-block; transition: transform 0.2s ease; color: var(--text-tertiary); font-size: 12px; }
        .accordion-arrow.open { transform: rotate(90deg); }
        .accordion-content { max-height: 0; overflow: hidden; background: var(--bg-secondary); border-radius: 0 0 var(--radius-sm) var(--radius-sm); margin-bottom: 12px; transition: max-height 0.3s cubic-bezier(0.4, 0, 0.2, 1), padding 0.3s ease; padding: 0 16px; }
        .accordion-content.open { max-height: 2000px; padding: 12px 16px 16px; }
        .pagination { display: flex; justify-content: center; align-items: center; gap: 10px; margin-top: 16px; }
        .btn-page { padding: 6px 14px; background: var(--bg-tertiary); color: var(--text-secondary); border: 1px solid var(--border-primary); border-radius: var(--radius-sm); cursor: pointer; font-size: 12px; transition: all 0.15s ease; }
        .btn-page:hover { background: var(--bg-elevated); border-color: var(--border-secondary); color: var(--text-primary); }
        .btn-page:disabled { opacity: 0.35; cursor: not-allowed; }
        .btn-page:disabled:hover { background: var(--bg-tertiary); border-color: var(--border-primary); color: var(--text-secondary); }
        .page-info { font-size: 12px; color: var(--text-tertiary); }
        .empty-state { text-align: center; padding: 40px 20px; color: var(--text-tertiary); font-size: 14px; }
        .loading { text-align: center; padding: 60px 20px; color: var(--text-tertiary); font-size: 14px; }
    </style>
</head>
<body>
    <header class="page-header">
        <div>
            <div class="header-title">Upload Dashboard</div>
            <div class="header-subtitle">Sistema de upload automatizado</div>
        </div>
        <div class="live-indicator"><span class="live-dot"></span><span>Ao vivo</span></div>
    </header>
    <div class="stats-grid">
        <div class="stat-card stat-card--total" id="card-total" onclick="toggleFiltro(null)">
            <div class="stat-value stat-value--total" id="total">-</div>
            <div class="stat-label">Total de Canais</div>
        </div>
        <div class="stat-card stat-card--sucesso" id="card-sucesso" onclick="toggleFiltro('sucesso')">
            <div class="stat-value stat-value--sucesso" id="sucesso">-</div>
            <div class="stat-label">Upload com Sucesso</div>
        </div>
        <div class="stat-card stat-card--sem_video" id="card-sem_video" onclick="toggleFiltro('sem_video')">
            <div class="stat-value stat-value--sem_video" id="sem_video">-</div>
            <div class="stat-label">Sem Video</div>
        </div>
        <div class="stat-card stat-card--erro" id="card-erro" onclick="toggleFiltro('erro')">
            <div class="stat-value stat-value--erro" id="erro">-</div>
            <div class="stat-label">Com Erro</div>
        </div>
        <div class="stat-card stat-card--historico" onclick="abrirHistoricoCompleto()">
            <div class="stat-value stat-value--historico">&#x1F4DC;</div>
            <div class="stat-label">Historico Completo</div>
        </div>
    </div>
    <div class="content" id="subnichos-container"><div class="loading">Carregando dados...</div></div>
    <div class="status-bar">
        <div class="status-bar-left">
            <span>Atualizado: <span id="update-time">--:--:--</span></span>
            <span class="status-bar-sep"></span>
            <span>Refresh: 5s</span>
        </div>
        <div class="status-bar-right"><span><span id="total-monetizados">-</span> canais monetizados</span></div>
    </div>
    <div id="historicoModal" class="modal-overlay">
        <div class="modal-panel">
            <div class="modal-header">
                <h2 class="modal-title" id="modalTitle">Historico de Uploads</h2>
                <button class="btn-close" onclick="fecharModal()">&times;</button>
            </div>
            <div class="modal-body" id="modalBody"><p style="color: var(--text-tertiary); text-align: center;">Carregando...</p></div>
        </div>
    </div>
    <div id="historicoCompletoModal" class="modal-overlay">
        <div class="modal-panel">
            <div class="modal-header">
                <h2 class="modal-title" id="modalTitleCompleto">Historico Completo</h2>
                <button class="btn-close" onclick="fecharModalCompleto()">&times;</button>
            </div>
            <div class="modal-body" id="modalBodyCompleto"><p style="color: var(--text-tertiary); text-align: center;">Carregando...</p></div>
        </div>
    </div>
    <script>
        var filtroStatus = null;
        function escapeHtml(text) {
            if (!text) return '';
            return String(text).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
        }
        function truncarTitulo(titulo) {
            if (!titulo || titulo === '-') return '-';
            var palavras = titulo.split(' ');
            if (palavras.length > 7) return palavras.slice(0, 7).join(' ') + '...';
            return titulo;
        }
        function getSiglaIdioma(lingua) {
            if (!lingua) return '';
            var l = lingua.toLowerCase();
            var mapa = {'pt':'PT','portugues':'PT','portuguese':'PT','en':'EN','ingles':'EN','english':'EN','es':'ES','espanhol':'ES','spanish':'ES','de':'DE','alemao':'DE','german':'DE','fr':'FR','frances':'FR','french':'FR','it':'IT','italiano':'IT','italian':'IT','pl':'PL','polones':'PL','polish':'PL','ru':'RU','russo':'RU','russian':'RU','ja':'JP','japones':'JP','japanese':'JP','ko':'KR','coreano':'KR','korean':'KR','tr':'TR','turco':'TR','turkish':'TR','ar':'AR','arabic':'AR','arabe':'AR'};
            return mapa[l] || '';
        }
        function toggleFiltro(status) {
            document.querySelectorAll('.stat-card').forEach(function(c) { c.classList.remove('active'); });
            if (!status || filtroStatus === status) { filtroStatus = null; } else { filtroStatus = status; var card = document.getElementById('card-' + status); if (card) card.classList.add('active'); }
            atualizar();
        }
        function toggleDia(id) {
            var el = document.getElementById(id);
            var seta = document.getElementById('seta-' + id);
            if (el) el.classList.toggle('open');
            if (seta) seta.classList.toggle('open');
        }
        var _uploadingChannelId = null;
        var _successChannelId = null;
        var _errorChannelId = null;
        var _statusBeforeUpload = null;

        function _getChannelStatus(data, channelId) {
            if (data && data.subnichos) {
                for (var sub in data.subnichos) {
                    for (var i = 0; i < data.subnichos[sub].length; i++) {
                        if (data.subnichos[sub][i].channel_id === channelId) return data.subnichos[sub][i].status;
                    }
                }
            }
            return null;
        }
        async function forcarUpload(channelId, channelName) {
            var msg = 'Forcar upload do canal ' + channelName + '?\\n\\nO proximo video "done" da planilha sera enviado.';
            if (!confirm(msg)) return;
            var botao = event.target.closest('.btn-icon');
            _uploadingChannelId = channelId;
            try {
                // Captura status ANTES do upload para comparar depois
                var preXhr = new XMLHttpRequest();
                preXhr.open('GET', '/api/dash-upload/status', false);
                preXhr.send();
                if (preXhr.status === 200) {
                    _statusBeforeUpload = _getChannelStatus(JSON.parse(preXhr.responseText), channelId);
                }
                botao.innerHTML = '\\u23F3';
                botao.classList.add('btn-icon--uploading');
                var response = await fetch('/api/yt-upload/force/' + channelId, { method: 'POST' });
                var result = await response.json();
                if (response.ok && result.status !== 'sem_video' && result.status !== 'no_video') {
                    var tentativas = 0;
                    var maxTentativas = 4;
                    var pollInterval = setInterval(function() {
                        tentativas++;
                        if (tentativas > maxTentativas) {
                            clearInterval(pollInterval);
                            _uploadingChannelId = null;
                            _statusBeforeUpload = null;
                            atualizar();
                            return;
                        }
                        var xhr = new XMLHttpRequest();
                        xhr.open('GET', '/api/dash-upload/status', true);
                        xhr.onreadystatechange = function() {
                            if (xhr.readyState === 4 && xhr.status === 200) {
                                try {
                                    var data = JSON.parse(xhr.responseText);
                                    var st = _getChannelStatus(data, channelId);
                                    if (st && st !== _statusBeforeUpload) {
                                        clearInterval(pollInterval);
                                        _uploadingChannelId = null;
                                        _statusBeforeUpload = null;
                                        if (st === 'sucesso') {
                                            _successChannelId = channelId;
                                            atualizar();
                                            setTimeout(function() {
                                                _successChannelId = null;
                                                atualizar();
                                            }, 15000);
                                        } else if (st === 'erro') {
                                            _errorChannelId = channelId;
                                            atualizar();
                                            setTimeout(function() {
                                                _errorChannelId = null;
                                                atualizar();
                                            }, 5000);
                                        } else {
                                            atualizar();
                                        }
                                    }
                                } catch(e) {}
                            }
                        };
                        xhr.send();
                    }, 3000);
                } else if (result.status === 'sem_video' || result.status === 'no_video') {
                    alert('Sem videos disponiveis na planilha de ' + channelName);
                    _uploadingChannelId = null;
                    _statusBeforeUpload = null;
                    atualizar();
                } else {
                    alert('Erro: ' + (result.detail || result.message || 'Falha ao iniciar upload'));
                    _uploadingChannelId = null;
                    _statusBeforeUpload = null;
                    atualizar();
                }
            } catch (error) {
                alert('Erro de conexao: ' + error.message);
                _uploadingChannelId = null;
                _statusBeforeUpload = null;
            }
        }
        var _historicoData = [];
        var _historicoPagina = 0;
        var _HIST_POR_PAGINA = 10;
        function renderHistoricoPagina() {
            var modalBody = document.getElementById('modalBody');
            var items = _historicoData;
            var totalPaginas = Math.ceil(items.length / _HIST_POR_PAGINA);
            var inicio = _historicoPagina * _HIST_POR_PAGINA;
            var fim = Math.min(inicio + _HIST_POR_PAGINA, items.length);
            var paginaItems = items.slice(inicio, fim);
            var countSucesso = 0, countSemVideo = 0, countErro = 0;
            items.forEach(function(item) { if (item.status === 'sucesso') countSucesso++; else if (item.status === 'sem_video') countSemVideo++; else if (item.status === 'erro') countErro++; });
            var totalRegistros = countSucesso + countSemVideo + countErro;
            var html = '<div class="modal-summary" style="background:var(--success-muted);border-color:rgba(34,197,94,0.25);">';
            html += '<span class="modal-summary-stat" style="color:var(--text-primary);font-weight:600;">Total de Registros: ' + totalRegistros + ' |</span>';
            html += '<span class="modal-summary-stat" style="color:var(--success);">&#x2705; ' + countSucesso + ' uploads</span>';
            html += '<span class="modal-summary-stat" style="color:var(--warning);">&#x26A0;&#xFE0F; ' + countSemVideo + ' sem video</span>';
            html += '<span class="modal-summary-stat" style="color:var(--error);">&#x274C; ' + countErro + ' erros</span>';
            html += '</div>';
            html += '<table class="modal-table"><thead><tr><th>Data</th><th>Video</th><th>Status</th><th>Horario</th></tr></thead><tbody>';
            if (paginaItems.length > 0) {
                paginaItems.forEach(function(item) {
                    html += '<tr>';
                    var df = item.data; if (df && df.includes('-')) { var p = df.split('-'); df = p[2] + '/' + p[1] + '/' + p[0]; }
                    html += '<td>' + df + '</td>';
                    html += '<td style="max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' + escapeHtml(truncarTitulo(item.video_titulo)) + '</td>';
                    var statusColor = 'var(--text-tertiary)'; var statusText = '&#x26AA; Sem Video';
                    if (item.status === 'sucesso') { statusColor = 'var(--success)'; statusText = '&#x2705; Sucesso'; }
                    else if (item.status === 'erro') { statusColor = 'var(--error)'; statusText = '&#x274C; Erro'; }
                    html += '<td style="color:' + statusColor + ';font-weight:500;">' + statusText + '</td>';
                    html += '<td style="color:var(--text-tertiary);">' + (item.hora_processamento || '-') + '</td>';
                    html += '</tr>';
                });
            } else { html += '<tr><td colspan="4" style="text-align:center;color:var(--text-tertiary);padding:20px;">Nenhum historico</td></tr>'; }
            html += '</tbody></table>';
            if (totalPaginas > 1) {
                html += '<div class="pagination">';
                html += '<button class="btn-page" onclick="_historicoPagina--;renderHistoricoPagina();" ' + (_historicoPagina === 0 ? 'disabled' : '') + '>Anterior</button>';
                html += '<span class="page-info">Pagina ' + (_historicoPagina + 1) + ' de ' + totalPaginas + '</span>';
                html += '<button class="btn-page" onclick="_historicoPagina++;renderHistoricoPagina();" ' + (_historicoPagina >= totalPaginas - 1 ? 'disabled' : '') + '>Proxima</button>';
                html += '</div>';
            }
            modalBody.innerHTML = html;
        }
        function abrirHistorico(channelId, channelName) {
            var modal = document.getElementById('historicoModal');
            document.getElementById('modalTitle').textContent = 'Historico - ' + channelName;
            modal.classList.add('show');
            document.getElementById('modalBody').innerHTML = '<p style="color:var(--text-tertiary);text-align:center;padding:40px;">Carregando...</p>';
            fetch('/api/dash-upload/canais/' + channelId + '/historico')
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    if (data.error) { document.getElementById('modalBody').innerHTML = '<p style="color:var(--error);">Erro: ' + escapeHtml(data.error) + '</p>'; return; }
                    if (data.historico && data.historico.length > 0) {
                        var vistos = new Set(); var filtrado = [];
                        data.historico.forEach(function(item) { var chave = item.data + '|' + (item.video_titulo || 'sem_video'); if (!vistos.has(chave)) { vistos.add(chave); filtrado.push(item); } });
                        data.historico = filtrado;
                    }
                    _historicoData = data.historico || []; _historicoPagina = 0; renderHistoricoPagina();
                })
                .catch(function(error) { document.getElementById('modalBody').innerHTML = '<p style="color:var(--error);">Erro: ' + error + '</p>'; });
        }
        function fecharModal() { document.getElementById('historicoModal').classList.remove('show'); }
        function fecharModalCompleto() { document.getElementById('historicoCompletoModal').classList.remove('show'); }
        async function abrirHistoricoCompleto() {
            var modal = document.getElementById('historicoCompletoModal');
            var modalBody = document.getElementById('modalBodyCompleto');
            modal.classList.add('show');
            modalBody.innerHTML = '<p style="color:var(--text-tertiary);text-align:center;padding:40px;">Carregando historico...</p>';
            try {
                var response = await fetch('/api/dash-upload/historico-completo');
                var data = await response.json();
                if (data.historico_por_data && data.historico_por_data.length > 0) {
                    data.historico_por_data.forEach(function(dia) {
                        if (dia.canais && dia.canais.length > 0) {
                            var vistos = new Set(); var filtrado = [];
                            dia.canais.forEach(function(canal) { if (!canal.nome || canal.nome.trim() === '') return; var chave = dia.data + '|' + canal.nome + '|' + (canal.video_titulo || 'sem_video'); if (!vistos.has(chave)) { vistos.add(chave); filtrado.push(canal); } });
                            dia.canais = filtrado;
                        }
                    });
                    var totalSucesso = 0, totalSemVideo = 0, totalErro = 0;
                    data.historico_por_data.forEach(function(dia) { dia.canais.forEach(function(canal) { if (canal.status === 'sucesso') totalSucesso++; else if (canal.status === 'sem_video') totalSemVideo++; else if (canal.status === 'erro') totalErro++; }); });
                    var totalRegistros = totalSucesso + totalSemVideo + totalErro;
                    var html = '<div class="modal-summary" style="background:var(--success-muted);border-color:rgba(34,197,94,0.25);">';
                    html += '<span class="modal-summary-stat" style="color:var(--text-primary);font-weight:600;">Total de Registros: ' + totalRegistros + ' |</span>';
                    html += '<span class="modal-summary-stat" style="color:var(--success);">&#x2705; ' + totalSucesso + ' uploads</span>';
                    html += '<span class="modal-summary-stat" style="color:var(--warning);">&#x26A0;&#xFE0F; ' + totalSemVideo + ' sem video</span>';
                    html += '<span class="modal-summary-stat" style="color:var(--error);">&#x274C; ' + totalErro + ' erros</span>';
                    html += '</div>';
                    html += '<div style="max-height:450px;overflow-y:auto;">';
                    data.historico_por_data.forEach(function(dia, idx) {
                        var df = dia.data; if (df && df.includes('-')) { var p = df.split('-'); if (p.length === 3) df = p[2] + '/' + p[1] + '/' + p[0]; }
                        var suc = 0, sv = 0, err = 0;
                        dia.canais.forEach(function(c) { if (c.status === 'sucesso') suc++; else if (c.status === 'sem_video') sv++; else if (c.status === 'erro') err++; });
                        var diaId = 'dia-' + idx;
                        html += '<div class="accordion-trigger" data-dia="' + diaId + '" onclick="toggleDia(this.dataset.dia)">';
                        html += '<div style="display:flex;align-items:center;gap:8px;">';
                        html += '<span id="seta-' + diaId + '" class="accordion-arrow">&#9654;</span>';
                        html += '<span style="font-weight:600;color:var(--text-primary);">' + df + '</span>';
                        html += '</div>';
                        html += '<div style="display:flex;gap:12px;font-size:12px;">';
                        html += '<span style="color:var(--success);">&#x2705; ' + suc + '</span>';
                        html += '<span style="color:var(--warning);">&#x26A0;&#xFE0F; ' + sv + '</span>';
                        html += '<span style="color:var(--error);">&#x274C; ' + err + '</span>';
                        html += '</div></div>';
                        html += '<div class="accordion-content" id="' + diaId + '">';
                        var canaisSucesso = dia.canais.filter(function(c) { return c.status === 'sucesso'; });
                        if (canaisSucesso.length > 0) {
                            html += '<table class="modal-table"><thead><tr><th>Canal</th><th>Video</th><th>Status</th><th>Horario</th></tr></thead><tbody>';
                            canaisSucesso.forEach(function(canal) {
                                var sigla = getSiglaIdioma(canal.lingua);
                                html += '<tr><td style="color:var(--text-primary);font-weight:500;">' + escapeHtml(canal.nome);
                                if (sigla) html += ' <span class="lang-tag">' + sigla + '</span>';
                                html += '</td><td style="max-width:280px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' + escapeHtml(truncarTitulo(canal.video_titulo)) + '</td>';
                                html += '<td style="color:var(--success);font-weight:500;">Sucesso</td>';
                                html += '<td style="color:var(--text-tertiary);">' + (canal.hora || '-') + '</td></tr>';
                            });
                            html += '</tbody></table>';
                        } else { html += '<p style="color:var(--text-tertiary);text-align:center;padding:12px;">Nenhum upload com sucesso</p>'; }
                        html += '</div>';
                    });
                    html += '</div>';
                    modalBody.innerHTML = html;
                } else { modalBody.innerHTML = '<p style="color:var(--text-tertiary);text-align:center;padding:40px;">Nenhum historico encontrado.</p>'; }
            } catch (error) { modalBody.innerHTML = '<p style="color:var(--error);text-align:center;">Erro: ' + error.message + '</p>'; }
        }
        window.addEventListener('click', function(e) { if (e.target.classList && e.target.classList.contains('modal-overlay')) e.target.classList.remove('show'); });
        document.addEventListener('keydown', function(e) { if (e.key === 'Escape') document.querySelectorAll('.modal-overlay.show').forEach(function(m) { m.classList.remove('show'); }); });
        function formatTime(timeStr) { if (!timeStr) return '-'; return timeStr; }
        function atualizar() {
            var xhr = new XMLHttpRequest();
            xhr.open('GET', '/api/dash-upload/status', true);
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4 && xhr.status === 200) {
                    try {
                        var data = JSON.parse(xhr.responseText);
                        var el;
                        el = document.getElementById('total'); if (el) el.textContent = data.stats.total || 0;
                        el = document.getElementById('sucesso'); if (el) el.textContent = data.stats.sucesso || 0;
                        el = document.getElementById('sem_video'); if (el) el.textContent = data.stats.sem_video || 0;
                        el = document.getElementById('erro'); if (el) el.textContent = data.stats.erro || 0;
                        var totalMonetizados = 0;
                        var html = '';
                        if (data.subnichos) {
                            for (var subnicho in data.subnichos) {
                                var canais = data.subnichos[subnicho];
                                var ss = {sucesso: 0, erro: 0, sem_video: 0, pendente: 0};
                                for (var i = 0; i < canais.length; i++) {
                                    if (canais[i].is_monetized) totalMonetizados++;
                                    if (canais[i].status === 'sucesso') ss.sucesso++;
                                    else if (canais[i].status === 'erro') ss.erro++;
                                    else if (canais[i].status === 'sem_video') ss.sem_video++;
                                    else ss.pendente++;
                                }
                                var accent = '#3f3f46'; var accentMuted = 'rgba(63,63,70,0.15)'; var icon = '?';
                                if (subnicho === 'Monetizados') { accent = '#22c55e'; accentMuted = 'rgba(34,197,94,0.12)'; icon = '$'; }
                                else if (subnicho === 'Historias Sombrias') { accent = '#8b5cf6'; accentMuted = 'rgba(139,92,246,0.12)'; icon = '\\u265B'; }
                                else if (subnicho === 'Relatos de Guerra') { accent = '#4a8c50'; accentMuted = 'rgba(74,140,80,0.18)'; icon = '\\u2694'; }
                                else if (subnicho === 'Guerras e Civilizacoes' || subnicho === 'Guerras e Civiliza\\u00e7\\u00f5es') { accent = '#f97316'; accentMuted = 'rgba(249,115,22,0.12)'; icon = '\\u26E8'; }
                                else if (subnicho === 'Terror') { accent = '#ef4444'; accentMuted = 'rgba(239,68,68,0.12)'; icon = '\\u2620'; }
                                else if (subnicho === 'Desmonetizados') { accent = '#71717a'; accentMuted = 'rgba(113,113,122,0.12)'; icon = '\\u25CB'; }
                                html += '<div class="section" style="--section-accent:' + accent + ';--section-accent-muted:' + accentMuted + ';">';
                                html += '<div class="section-header"><div class="section-title">';
                                html += '<span class="section-icon">' + icon + '</span>';
                                html += '<span>' + escapeHtml(subnicho) + '</span>';
                                html += '<span class="section-count">' + canais.length + ' canais</span></div>';
                                html += '<div class="section-pills">';
                                if (ss.sucesso > 0) html += '<span class="stat-pill stat-pill--success">' + ss.sucesso + ' sucesso</span>';
                                if (ss.sem_video > 0) html += '<span class="stat-pill stat-pill--warning">' + ss.sem_video + ' sem video</span>';
                                if (ss.erro > 0) html += '<span class="stat-pill stat-pill--error">' + ss.erro + ' erro</span>';
                                if (ss.pendente > 0) html += '<span class="stat-pill stat-pill--pending">' + ss.pendente + ' pendente</span>';
                                html += '</div></div>';
                                html += '<table class="channel-table"><thead><tr>';
                                html += '<th style="width:280px">Canal</th><th style="width:120px">Status</th><th>Video Enviado</th><th style="width:80px">Horario</th><th style="width:120px">Acoes</th>';
                                html += '</tr></thead><tbody>';
                                var temCanais = false;
                                for (var j = 0; j < canais.length; j++) {
                                    var canal = canais[j];
                                    if (filtroStatus && canal.status !== filtroStatus) continue;
                                    temCanais = true;
                                    var badgeClass = 'status-badge--pending'; var badgeText = 'Pendente';
                                    if (canal.status === 'sucesso') { badgeClass = 'status-badge--success'; badgeText = 'Enviado'; }
                                    else if (canal.status === 'sem_video') { badgeClass = 'status-badge--sem_video'; badgeText = 'Sem Video'; }
                                    else if (canal.status === 'erro') { badgeClass = 'status-badge--error'; badgeText = 'Erro'; }
                                    html += '<tr>';
                                    html += '<td><div class="cell-channel"><span class="channel-name">' + escapeHtml(canal.channel_name) + '</span>';
                                    var sigla = getSiglaIdioma(canal.lingua);
                                    if (sigla) html += '<span class="lang-tag">' + sigla + '</span>';
                                    if (canal.is_monetized) html += '<span class="monetized-dot"></span>';
                                    html += '</div></td>';
                                    html += '<td><span class="status-badge ' + badgeClass + '">' + badgeText + '</span></td>';
                                    html += '<td><span class="video-title">' + escapeHtml(truncarTitulo(canal.video_titulo)) + '</span></td>';
                                    html += '<td><span class="cell-time">' + formatTime(canal.hora_upload) + '</span></td>';
                                    html += '<td><div class="cell-actions">';
                                    var safeName = escapeHtml(canal.channel_name).replace(/"/g, '&quot;');
                                    if (_uploadingChannelId === canal.channel_id) {
                                        html += '<button class="btn-icon btn-icon--upload btn-icon--uploading" data-channel-id="' + canal.channel_id + '" data-channel-name="' + safeName + '" title="Uploading...">&#x23F3;</button>';
                                    } else if (_successChannelId === canal.channel_id) {
                                        html += '<button class="btn-icon btn-icon--upload btn-icon--upload-success" data-channel-id="' + canal.channel_id + '" data-channel-name="' + safeName + '" title="Upload concluido!">&#x2705;</button>';
                                    } else if (_errorChannelId === canal.channel_id) {
                                        html += '<button class="btn-icon btn-icon--upload btn-icon--upload-error" data-channel-id="' + canal.channel_id + '" data-channel-name="' + safeName + '" title="Erro no upload">&#x274C;</button>';
                                    } else {
                                        html += '<button class="btn-icon btn-icon--upload" data-channel-id="' + canal.channel_id + '" data-channel-name="' + safeName + '" title="Forcar upload">&#x1F4E4;</button>';
                                    }
                                    html += '<button class="btn-icon btn-icon--hist" data-channel-id="' + canal.channel_id + '" data-channel-name="' + safeName + '" title="Historico">&#x1F4DC;</button>';
                                    if (canal.spreadsheet_id && canal.spreadsheet_id !== '') {
                                        html += '<a href="https://docs.google.com/spreadsheets/d/' + canal.spreadsheet_id + '" target="_blank" class="btn-icon" title="Planilha">&#x1F4D1;</a>';
                                    } else { html += '<button class="btn-icon" disabled title="Sem planilha">&#x1F4D1;</button>'; }
                                    html += '</div></td></tr>';
                                }
                                if (!temCanais) html += '<tr><td colspan="5" style="text-align:center;color:var(--text-tertiary);padding:20px;">Nenhum canal com este filtro</td></tr>';
                                html += '</tbody></table></div>';
                            }
                        }
                        if (html === '') html = '<div class="empty-state">Nenhum canal encontrado</div>';
                        var container = document.getElementById('subnichos-container');
                        if (container.innerHTML !== html) container.innerHTML = html;
                        document.getElementById('total-monetizados').textContent = totalMonetizados;
                        var now = new Date();
                        document.getElementById('update-time').textContent = now.toLocaleTimeString('pt-BR', {timeZone: 'America/Sao_Paulo'});
                    } catch(e) { console.error('Erro:', e); document.getElementById('subnichos-container').innerHTML = '<div class="empty-state">Erro ao carregar dados</div>'; }
                }
            };
            xhr.send();
        }
        atualizar();
        setInterval(atualizar, 5000);
        document.addEventListener('click', function(e) {
            var btn = e.target.closest('.btn-icon--hist');
            if (btn) { abrirHistorico(btn.getAttribute('data-channel-id'), btn.getAttribute('data-channel-name')); return; }
            btn = e.target.closest('.btn-icon--upload');
            if (btn) { forcarUpload(btn.getAttribute('data-channel-id'), btn.getAttribute('data-channel-name')); return; }
        });
    </script>
</body>
</html>
'''

@app.get("/dash-upload", response_class=HTMLResponse)
async def dash_upload_page():
    """Dashboard de Upload v2 - Interface web"""
    return DASH_UPLOAD_HTML

@app.get("/api/dash-upload/status")
async def dash_upload_status():
    """Status dos canais de upload agrupados por subnicho"""
    import time as _time
    from collections import defaultdict

    now = _time.time()
    if _dash_cache['data'] and (now - _dash_cache['timestamp']) < _DASH_CACHE_TTL:
        return _dash_cache['data']

    try:
        canais = supabase.table('yt_channels')\
            .select('channel_id, channel_name, spreadsheet_id, lingua, is_monetized, subnicho')\
            .eq('is_active', True)\
            .eq('upload_automatico', True)\
            .order('subnicho, channel_name')\
            .execute()

        today = datetime.now(timezone.utc).date().isoformat()
        uploads = supabase.table('yt_canal_upload_diario')\
            .select('channel_id, status, upload_realizado, video_titulo, hora_processamento, erro_mensagem, created_at')\
            .eq('data', today)\
            .execute()

        # Prioridade: sucesso > erro > sem_video (quando canal tem multiplos registros no dia)
        # Quando mesmo status, pega o MAIS RECENTE (created_at maior)
        _status_priority = {'sucesso': 0, 'erro': 1, 'sem_video': 2}
        upload_map = {}
        for u in uploads.data:
            cid = u['channel_id']
            new_prio = _status_priority.get(u.get('status'), 9)
            if cid not in upload_map:
                upload_map[cid] = u
            else:
                old_prio = _status_priority.get(upload_map[cid].get('status'), 9)
                if new_prio < old_prio or (new_prio == old_prio and (u.get('created_at') or '') > (upload_map[cid].get('created_at') or '')):
                    upload_map[cid] = u

        subnichos_dict = defaultdict(list)
        stats = {'total': 0, 'sucesso': 0, 'erro': 0, 'sem_video': 0, 'pendente': 0}

        for canal in canais.data:
            upload = upload_map.get(canal['channel_id'])
            status = 'pendente'
            video_titulo = None
            hora_upload = None

            if upload:
                if upload.get('upload_realizado'):
                    status = 'sucesso'
                    video_titulo = upload.get('video_titulo')
                    hora_upload = _extrair_hora(upload.get('hora_processamento') or upload.get('updated_at'))
                elif upload.get('status') == 'sem_video':
                    status = 'sem_video'
                elif upload.get('erro_mensagem'):
                    status = 'erro'

            stats['total'] += 1
            stats[status] += 1

            subnicho = canal.get('subnicho', 'Sem Categoria')
            subnichos_dict[subnicho].append({
                'channel_id': canal['channel_id'],
                'channel_name': canal['channel_name'],
                'spreadsheet_id': canal.get('spreadsheet_id', ''),
                'lingua': canal.get('lingua', ''),
                'is_monetized': canal.get('is_monetized', False),
                'status': status,
                'video_titulo': video_titulo,
                'hora_upload': hora_upload
            })

        monetizados_forcados = ['UCzfZRuRHSp6erCwzuhjywFw', 'UCWYzVowgJ6LlxCcYlMGcLtA']
        for sub in subnichos_dict:
            for canal in subnichos_dict[sub]:
                if canal['channel_id'] in monetizados_forcados:
                    canal['is_monetized'] = True

        novo_dict = defaultdict(list)
        for sub, canais_list in subnichos_dict.items():
            for canal in canais_list:
                if canal['is_monetized']:
                    novo_dict['Monetizados'].append(canal)
                else:
                    novo_dict[sub].append(canal)
        subnichos_dict = novo_dict

        status_order = {'sucesso': 0, 'pendente': 1, 'erro': 2, 'sem_video': 3}
        for sub in subnichos_dict:
            subnichos_dict[sub].sort(key=lambda x: (status_order.get(x['status'], 4), not x['is_monetized'], x['channel_name']))

        # Ordenar subnichos: mais sucessos primeiro
        subnichos_ordenados = dict(sorted(
            subnichos_dict.items(),
            key=lambda item: sum(1 for c in item[1] if c['status'] == 'sucesso'),
            reverse=True
        ))

        result = {'stats': stats, 'subnichos': subnichos_ordenados}
        _dash_cache['data'] = result
        _dash_cache['timestamp'] = _time.time()
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dash-upload/canais/{channel_id}/historico")
async def dash_upload_historico(channel_id: str):
    """Historico de uploads de um canal"""
    try:
        try:
            response = supabase.table('yt_canal_upload_historico')\
                .select('*')\
                .eq('channel_id', channel_id)\
                .order('data', desc=True)\
                .order('hora_processamento', desc=True)\
                .execute()
        except Exception as e:
            if "relation" in str(e) and "does not exist" in str(e):
                response = supabase.table('yt_canal_upload_diario')\
                    .select('*')\
                    .eq('channel_id', channel_id)\
                    .order('data', desc=True)\
                    .execute()
            else:
                raise e

        historico_data = response.data if response.data else []

        response_diario = supabase.table('yt_canal_upload_diario')\
            .select('*')\
            .eq('channel_id', channel_id)\
            .order('data', desc=True)\
            .execute()

        if response_diario.data:
            registros_unicos = {(item.get('channel_id'), item['data'], item.get('video_titulo', '')) for item in historico_data}
            for item_diario in response_diario.data:
                chave = (item_diario.get('channel_id'), item_diario['data'], item_diario.get('video_titulo', ''))
                if chave not in registros_unicos:
                    historico_data.append(item_diario)
                    registros_unicos.add(chave)

        historico_data.sort(key=lambda x: (x.get('data', ''), x.get('hora_processamento', '')), reverse=True)

        historico = []
        for item in historico_data:
            historico.append({
                'data': item['data'],
                'status': item.get('status', 'pendente'),
                'video_titulo': item.get('video_titulo', '-'),
                'hora_processamento': _extrair_hora(item.get('hora_processamento')),
                'erro_mensagem': item.get('erro_mensagem'),
                'tentativa_numero': item.get('tentativa_numero', 1),
                'upload_realizado': item.get('upload_realizado', False),
                'youtube_video_id': item.get('youtube_video_id')
            })

        return {'channel_id': channel_id, 'total_registros': len(historico), 'historico': historico}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dash-upload/historico-completo")
async def dash_upload_historico_completo():
    """Historico completo dos ultimos 30 dias"""
    try:
        from collections import defaultdict

        hoje = datetime.now(timezone.utc).date()
        data_inicio = hoje - timedelta(days=30)

        canais_info = supabase.table('yt_channels')\
            .select('channel_name, lingua')\
            .eq('is_active', True)\
            .execute()
        mapa_lingua = {c['channel_name']: c.get('lingua', '') for c in canais_info.data} if canais_info.data else {}

        response = supabase.table('yt_canal_upload_historico')\
            .select('*')\
            .gte('data', data_inicio.isoformat())\
            .order('data', desc=True)\
            .execute()

        historico_por_data = defaultdict(lambda: {'data': '', 'total': 0, 'sucesso': 0, 'erro': 0, 'sem_video': 0, 'canais': []})

        for item in response.data:
            data_str = item['data']
            historico_por_data[data_str]['data'] = data_str
            nome_canal = item.get('channel_name', '').strip()
            if nome_canal:
                historico_por_data[data_str]['total'] += 1
                status = item.get('status', 'pendente')
                if status == 'sucesso': historico_por_data[data_str]['sucesso'] += 1
                elif status == 'erro': historico_por_data[data_str]['erro'] += 1
                elif status == 'sem_video': historico_por_data[data_str]['sem_video'] += 1
                historico_por_data[data_str]['canais'].append({
                    'nome': nome_canal, 'status': status,
                    'video_titulo': item.get('video_titulo', ''),
                    'hora': _extrair_hora(item.get('hora_processamento')) or '',
                    'lingua': mapa_lingua.get(nome_canal, '')
                })

        response_diario = supabase.table('yt_canal_upload_diario')\
            .select('*')\
            .gte('data', data_inicio.isoformat())\
            .execute()

        if response_diario.data:
            for item in response_diario.data:
                data_str = item.get('data')
                if data_str not in historico_por_data:
                    historico_por_data[data_str] = {'data': data_str, 'total': 0, 'sucesso': 0, 'erro': 0, 'sem_video': 0, 'canais': []}
                nome_canal = item.get('channel_name', '').strip()
                if not nome_canal: continue
                video_ja_existe = any(c['nome'] == nome_canal and c.get('video_titulo', '') == item.get('video_titulo', '') for c in historico_por_data[data_str]['canais'])
                if not video_ja_existe:
                    status = item.get('status', 'pendente')
                    historico_por_data[data_str]['total'] += 1
                    if status == 'sucesso': historico_por_data[data_str]['sucesso'] += 1
                    elif status == 'erro': historico_por_data[data_str]['erro'] += 1
                    elif status == 'sem_video': historico_por_data[data_str]['sem_video'] += 1
                    historico_por_data[data_str]['canais'].append({
                        'nome': nome_canal, 'status': status,
                        'video_titulo': item.get('video_titulo', ''),
                        'hora': _extrair_hora(item.get('hora_processamento')) or '',
                        'lingua': mapa_lingua.get(nome_canal, '')
                    })

        historico_lista = sorted(historico_por_data.values(), key=lambda x: x['data'], reverse=True)
        dias_mostrados = min(30, len(historico_lista))
        total_registros = sum(d['total'] for d in historico_lista[:30])

        return {'historico_por_data': historico_lista[:30], 'total_dias': dias_mostrados, 'total_registros': total_registros}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ANALISE DE ESTRUTURA DE COPY - MVP
# ============================================================================

from copy_analysis_agent import (
    run_analysis as copy_run_analysis,
    get_latest_analysis as copy_get_latest,
    get_analysis_history as copy_get_history,
    get_video_mappings as copy_get_mappings,
    get_all_channels_for_analysis as copy_get_channels
)


@app.post("/api/analise-copy/{channel_id}")
async def trigger_copy_analysis(channel_id: str, background_tasks: BackgroundTasks):
    """
    Dispara analise de estrutura de copy para um canal.
    Roda em background e retorna imediatamente.
    """
    try:
        # Rodar sincrono (analise demora ~10-30s por canal)
        result = copy_run_analysis(channel_id)
        return result
    except Exception as e:
        logger.error(f"Erro analise copy {channel_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analise-copy/{channel_id}/latest")
async def get_latest_copy_analysis(channel_id: str):
    """Retorna a analise mais recente de estrutura de copy de um canal."""
    try:
        result = copy_get_latest(channel_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Nenhuma analise encontrada para canal {channel_id}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro buscar analise copy {channel_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analise-copy/{channel_id}/historico")
async def get_copy_analysis_history(
    channel_id: str,
    limit: int = 20,
    offset: int = 0
):
    """
    Retorna historico de analises com paginacao.
    Params: limit (default 20, max 100), offset (default 0)
    """
    try:
        limit = min(limit, 100)
        offset = max(offset, 0)
        return copy_get_history(channel_id, limit=limit, offset=offset)
    except Exception as e:
        logger.error(f"Erro historico copy {channel_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analise-copy/{channel_id}/videos")
async def get_copy_analysis_videos(
    channel_id: str,
    run_id: int = 0,
    structure: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """
    Retorna mapeamento video-estrutura de uma analise com paginacao.
    Se run_id=0, usa a analise mais recente.
    Params: run_id, structure (filtro A-G), limit (max 200), offset
    """
    try:
        if run_id == 0:
            latest = copy_get_latest(channel_id)
            if not latest:
                raise HTTPException(status_code=404, detail="Nenhuma analise encontrada")
            run_id = latest["id"]

        limit = min(limit, 200)
        offset = max(offset, 0)
        return copy_get_mappings(run_id, limit=limit, offset=offset, structure_filter=structure)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro videos copy {channel_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analise-copy/run-all")
async def run_copy_analysis_all():
    """
    Roda analise de copy para TODOS os canais nosso com spreadsheet configurado.
    Retorna resumo de cada canal.
    """
    try:
        channels = copy_get_channels()
        if not channels:
            return {"success": False, "error": "Nenhum canal encontrado com spreadsheet configurado"}

        results = []
        success_count = 0
        error_count = 0

        for ch in channels:
            try:
                result = copy_run_analysis(ch["channel_id"])
                results.append({
                    "channel_id": ch["channel_id"],
                    "channel_name": ch.get("channel_name", ""),
                    "success": result.get("success", False),
                    "summary": result.get("summary"),
                    "error": result.get("error")
                })
                if result.get("success"):
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                results.append({
                    "channel_id": ch["channel_id"],
                    "channel_name": ch.get("channel_name", ""),
                    "success": False,
                    "error": str(e)
                })
                error_count += 1

        return {
            "success": True,
            "total_channels": len(channels),
            "success_count": success_count,
            "error_count": error_count,
            "results": results
        }
    except Exception as e:
        logger.error(f"Erro run-all copy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================================
# MISSION CONTROL - Escritório Virtual
# =========================================================================
try:
    from mission_control import MISSION_CONTROL_HTML, get_mission_control_data, get_sala_detail

    @app.get("/mission-control", response_class=HTMLResponse)
    async def mission_control_page():
        """Mission Control - Escritório Virtual com agentes"""
        return MISSION_CONTROL_HTML

    @app.get("/api/mission-control/status")
    async def mission_control_status():
        """Retorna dados de todos os setores, salas e agentes"""
        return await get_mission_control_data(db)

    @app.get("/api/mission-control/sala/{canal_id}")
    async def mission_control_sala(canal_id: int):
        """Retorna detalhes de uma sala específica"""
        return await get_sala_detail(db, canal_id)

    logger.info("Mission Control inicializado com sucesso!")
except Exception as e:
    logger.warning(f"Mission Control nao inicializado: {e}")


# =========================================================================
# DASHBOARD ANALISE DE COPY - Visualizacao de Relatorios
# =========================================================================

@app.get("/api/dash-analise-copy/channels")
async def dash_copy_analysis_channels():
    """Lista canais com copy_spreadsheet_id agrupados por subnicho + ultima analise."""
    try:
        # 1. Busca canais com copy_spreadsheet_id
        channels = copy_get_channels()
        if not channels:
            return {"subnichos": {}, "stats": {"total": 0, "com_relatorio": 0}}

        # 2. Busca ultima analise de cada canal
        channel_ids = [c["channel_id"] for c in channels]
        last_analyses = {}

        # Buscar em batches de 20
        for i in range(0, len(channel_ids), 20):
            batch = channel_ids[i:i+20]
            batch_str = ",".join(batch)
            resp = supabase.table("copy_analysis_runs")\
                .select("channel_id,run_date,channel_avg_retention")\
                .in_("channel_id", batch)\
                .order("run_date", desc=True)\
                .execute()

            for row in resp.data:
                cid = row["channel_id"]
                if cid not in last_analyses:
                    last_analyses[cid] = {
                        "last_date": row["run_date"],
                        "avg_retention": row.get("channel_avg_retention")
                    }

        # 3. Agrupa por subnicho
        subnichos = {}
        com_relatorio = 0
        for ch in channels:
            sub = ch.get("subnicho", "Outros") or "Outros"
            if sub not in subnichos:
                subnichos[sub] = []

            analysis = last_analyses.get(ch["channel_id"])
            last_date = None
            avg_ret = None
            if analysis:
                last_date = analysis["last_date"]
                avg_ret = analysis["avg_retention"]
                com_relatorio += 1

            subnichos[sub].append({
                "channel_id": ch["channel_id"],
                "channel_name": ch.get("channel_name", ""),
                "lingua": ch.get("lingua", ""),
                "is_monetized": ch.get("is_monetized", False),
                "last_analysis_date": last_date,
                "avg_retention": avg_ret
            })

        return {
            "subnichos": subnichos,
            "stats": {
                "total": len(channels),
                "com_relatorio": com_relatorio
            }
        }
    except Exception as e:
        logger.error(f"Erro dash-analise-copy channels: {e}")
        raise HTTPException(status_code=500, detail=str(e))


DASH_COPY_ANALYSIS_HTML = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Analise de Copy - Dashboard</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {
    --bg-primary: #0a0a0f;
    --bg-secondary: #12121a;
    --bg-tertiary: #1a1a24;
    --bg-card: #16161f;
    --text-primary: #e8e8ed;
    --text-secondary: #a0a0b0;
    --text-muted: #6b6b7b;
    --accent: #00d4aa;
    --accent-dim: rgba(0, 212, 170, 0.15);
    --warning: #ff6b6b;
    --warning-dim: rgba(255, 107, 107, 0.15);
    --highlight: #ffd93d;
    --highlight-dim: rgba(255, 217, 61, 0.1);
    --purple: #a78bfa;
    --purple-dim: rgba(167, 139, 250, 0.15);
    --orange: #ff9f43;
    --blue: #54a0ff;
    --border: rgba(255, 255, 255, 0.08);
}
* { margin:0; padding:0; box-sizing:border-box; }
body {
    font-family: 'Plus Jakarta Sans', sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.6;
}
.container { display:flex; min-height:100vh; }

/* Sidebar */
.sidebar {
    width: 280px;
    background: var(--bg-secondary);
    border-right: 1px solid var(--border);
    padding: 1.5rem 1rem;
    position: fixed;
    height: 100vh;
    overflow-y: auto;
    z-index: 10;
}
.sidebar-header {
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--border);
}
.sidebar-title {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--accent);
    font-weight: 600;
}
.sidebar-subtitle {
    font-size: 1rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-top: 0.25rem;
}
.sidebar-stats {
    font-size: 0.75rem;
    color: var(--text-muted);
    margin-top: 0.5rem;
}
.sidebar-actions {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
}
.btn {
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.8rem;
    font-weight: 600;
    font-family: inherit;
    transition: all 0.2s;
}
.btn-accent {
    background: var(--accent);
    color: #000;
    flex: 1;
}
.btn-accent:hover { opacity: 0.85; }
.btn-accent:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-secondary {
    background: var(--bg-tertiary);
    color: var(--text-secondary);
    border: 1px solid var(--border);
}
.btn-secondary:hover { border-color: var(--accent); color: var(--accent); }

.subnicho-group { margin-bottom: 1rem; }
.subnicho-label {
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.4rem;
    font-weight: 600;
    padding-left: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}
.subnicho-icon {
    font-size: 0.75rem;
}
.channel-flag {
    font-size: 0.7rem;
    margin-right: 0.2rem;
    flex-shrink: 0;
}
.channel-info {
    display: flex;
    align-items: center;
    overflow: hidden;
    min-width: 0;
}
.channel-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 0.75rem;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.15s;
    margin-bottom: 2px;
}
.channel-item:hover { background: var(--bg-tertiary); }
.channel-item.active { background: var(--accent-dim); border-left: 3px solid var(--accent); }
.channel-name {
    font-size: 0.82rem;
    color: var(--text-secondary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 170px;
}
.channel-item.active .channel-name { color: var(--accent); font-weight: 600; }
.channel-date {
    font-size: 0.68rem;
    color: var(--text-muted);
    font-family: 'JetBrains Mono', monospace;
}
.channel-date.has-data { color: var(--accent); }

/* Main area */
.main {
    margin-left: 280px;
    flex: 1;
    padding: 2rem 3rem;
    min-height: 100vh;
}
.main-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--border);
}
.main-title { font-size: 1.2rem; font-weight: 700; }
.main-actions { display: flex; gap: 0.5rem; }

/* Report area */
.report-container {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 2rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    line-height: 1.8;
    white-space: pre-wrap;
    word-break: break-word;
}
.report-header-line {
    color: var(--accent);
    font-weight: 600;
}
.report-title {
    color: var(--accent);
    font-size: 1rem;
    font-weight: 700;
}
.report-meta { color: var(--text-secondary); }
.report-meta .val { color: var(--highlight); font-weight: 600; }
.section-header {
    color: var(--accent);
    font-weight: 600;
    margin-top: 1.5rem;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
}
.section-header.obs { color: var(--purple); }
.section-header.anom { color: var(--warning); }
.section-header.insuf { color: var(--text-muted); }
.section-header.comp { color: var(--blue); }
.ranking-line { color: var(--text-primary); }
.tag-acima { color: var(--accent); font-weight: 700; }
.tag-media { color: var(--highlight); font-weight: 600; }
.tag-abaixo { color: var(--warning); font-weight: 700; }
.anomaly-line { color: var(--warning); font-weight: 600; }
.anomaly-detail { color: var(--text-secondary); padding-left: 0.5rem; }
.narrative { color: var(--purple); }
.comp-positive { color: var(--accent); }
.comp-negative { color: var(--warning); }
.insuf-line { color: var(--text-muted); }
.table-header-line { color: var(--text-muted); font-size: 0.78rem; }

/* Empty state */
.empty-state {
    text-align: center;
    padding: 4rem 2rem;
    color: var(--text-muted);
}
.empty-state h2 { color: var(--text-secondary); margin-bottom: 1rem; font-size: 1.1rem; }
.empty-state p { margin-bottom: 1.5rem; }

/* Loading */
.loading { text-align: center; padding: 3rem; color: var(--accent); }
.loading-spinner {
    display: inline-block;
    width: 24px;
    height: 24px;
    border: 3px solid var(--border);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    margin-right: 0.5rem;
    vertical-align: middle;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Modal */
.modal-overlay {
    display: none;
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.7);
    z-index: 100;
    justify-content: center;
    align-items: center;
}
.modal-overlay.active { display: flex; }
.modal {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 2rem;
    max-width: 600px;
    width: 90%;
    max-height: 80vh;
    overflow-y: auto;
}
.modal h3 { color: var(--accent); margin-bottom: 1rem; }
.modal-close {
    float: right;
    background: none;
    border: none;
    color: var(--text-muted);
    font-size: 1.5rem;
    cursor: pointer;
}
.modal-close:hover { color: var(--text-primary); }
.history-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 1rem;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.15s;
    margin-bottom: 4px;
    border: 1px solid var(--border);
}
.history-item:hover { border-color: var(--accent); background: var(--accent-dim); }
.history-date { font-family: 'JetBrains Mono', monospace; color: var(--accent); font-weight: 600; }
.history-info { color: var(--text-muted); font-size: 0.8rem; }

@media (max-width: 1024px) {
    .sidebar { display: none; }
    .main { margin-left: 0; padding: 1.5rem; }
}
</style>
</head>
<body>
<div class="container">
    <aside class="sidebar">
        <div class="sidebar-header">
            <div class="sidebar-title">Dashboard</div>
            <div class="sidebar-subtitle">Analise de Copy</div>
            <div class="sidebar-stats" id="sidebarStats">Carregando...</div>
        </div>
        <div class="sidebar-actions">
            <button class="btn btn-accent" onclick="runAll()" id="btnRunAll">Rodar Todos</button>
        </div>
        <div id="channelList">
            <div class="loading"><span class="loading-spinner"></span> Carregando canais...</div>
        </div>
    </aside>
    <main class="main">
        <div class="main-header">
            <div class="main-title" id="mainTitle">Selecione um canal</div>
            <div class="main-actions" id="mainActions" style="display:none">
                <button class="btn btn-accent" onclick="runAnalysis()" id="btnRun">Gerar Relatorio</button>
                <button class="btn btn-secondary" onclick="showHistory()" id="btnHistory">Historico</button>
            </div>
        </div>
        <div id="reportArea">
            <div class="empty-state">
                <h2>Analise de Estrutura de Copy</h2>
                <p>Selecione um canal na sidebar para visualizar o relatorio<br>ou clique em "Rodar Todos" para gerar analises.</p>
            </div>
        </div>
    </main>
</div>

<div class="modal-overlay" id="historyModal">
    <div class="modal">
        <button class="modal-close" onclick="closeHistory()">&times;</button>
        <h3>Historico de Relatorios</h3>
        <div id="historyList">
            <div class="loading"><span class="loading-spinner"></span> Carregando...</div>
        </div>
    </div>
</div>

<script>
var _selectedChannel = null;
var _channelsData = {};

function getSubnichoStyle(sub) {
    var map = {
        'Monetizados': {color:'#22c55e', icon:'$'},
        'Historias Sombrias': {color:'#8b5cf6', icon:'\u265B'},
        'Relatos de Guerra': {color:'#4a8c50', icon:'\u2694'},
        'Guerras e Civilizacoes': {color:'#f97316', icon:'\u26E8'},
        'Guerras e Civiliza\u00e7\u00f5es': {color:'#f97316', icon:'\u26E8'},
        'Terror': {color:'#ef4444', icon:'\u2620'},
        'Desmonetizados': {color:'#71717a', icon:'\u25CB'}
    };
    return map[sub] || {color:'#64748b', icon:'\u25C6'};
}

function getFlag(lingua) {
    if (!lingua) return '';
    var l = lingua.toLowerCase();
    var map = {
        'pt':'\uD83C\uDDE7\uD83C\uDDF7','portugues':'\uD83C\uDDE7\uD83C\uDDF7','portuguese':'\uD83C\uDDE7\uD83C\uDDF7',
        'en':'\uD83C\uDDFA\uD83C\uDDF8','ingles':'\uD83C\uDDFA\uD83C\uDDF8','english':'\uD83C\uDDFA\uD83C\uDDF8',
        'es':'\uD83C\uDDEA\uD83C\uDDF8','espanhol':'\uD83C\uDDEA\uD83C\uDDF8','spanish':'\uD83C\uDDEA\uD83C\uDDF8',
        'de':'\uD83C\uDDE9\uD83C\uDDEA','alemao':'\uD83C\uDDE9\uD83C\uDDEA','german':'\uD83C\uDDE9\uD83C\uDDEA',
        'fr':'\uD83C\uDDEB\uD83C\uDDF7','frances':'\uD83C\uDDEB\uD83C\uDDF7','french':'\uD83C\uDDEB\uD83C\uDDF7',
        'it':'\uD83C\uDDEE\uD83C\uDDF9','italiano':'\uD83C\uDDEE\uD83C\uDDF9','italian':'\uD83C\uDDEE\uD83C\uDDF9',
        'pl':'\uD83C\uDDF5\uD83C\uDDF1','polones':'\uD83C\uDDF5\uD83C\uDDF1','polish':'\uD83C\uDDF5\uD83C\uDDF1',
        'ru':'\uD83C\uDDF7\uD83C\uDDFA','russo':'\uD83C\uDDF7\uD83C\uDDFA','russian':'\uD83C\uDDF7\uD83C\uDDFA',
        'ja':'\uD83C\uDDEF\uD83C\uDDF5','japones':'\uD83C\uDDEF\uD83C\uDDF5','japanese':'\uD83C\uDDEF\uD83C\uDDF5',
        'ko':'\uD83C\uDDF0\uD83C\uDDF7','coreano':'\uD83C\uDDF0\uD83C\uDDF7','korean':'\uD83C\uDDF0\uD83C\uDDF7',
        'tr':'\uD83C\uDDF9\uD83C\uDDF7','turco':'\uD83C\uDDF9\uD83C\uDDF7','turkish':'\uD83C\uDDF9\uD83C\uDDF7',
        'ar':'\uD83C\uDDF8\uD83C\uDDE6','arabic':'\uD83C\uDDF8\uD83C\uDDE6','arabe':'\uD83C\uDDF8\uD83C\uDDE6'
    };
    return map[l] || '';
}

function loadChannels() {
    fetch('/api/dash-analise-copy/channels')
        .then(function(r) { return r.json(); })
        .then(function(data) {
            var el = document.getElementById('channelList');
            var stats = document.getElementById('sidebarStats');
            var s = data.stats || {};
            stats.textContent = s.total + ' canais | ' + s.com_relatorio + ' com relatorio';

            var html = '';
            var subnichos = data.subnichos || {};
            var order = ['Monetizados','Relatos de Guerra','Historias Sombrias','Terror','Guerras e Civilizacoes','Desmonetizados'];
            var keys = Object.keys(subnichos).sort(function(a,b) {
                var ia = order.indexOf(a), ib = order.indexOf(b);
                if (ia === -1) ia = 99; if (ib === -1) ib = 99;
                return ia - ib;
            });
            for (var i = 0; i < keys.length; i++) {
                var sub = keys[i];
                var channels = subnichos[sub];
                var sStyle = getSubnichoStyle(sub);
                html += '<div class="subnicho-group">';
                html += '<div class="subnicho-label" style="color:' + sStyle.color + ';">';
                html += '<span class="subnicho-icon">' + sStyle.icon + '</span>';
                html += escHtml(sub) + ' <span style="opacity:0.5;font-size:0.6rem;">(' + channels.length + ')</span></div>';
                for (var j = 0; j < channels.length; j++) {
                    var ch = channels[j];
                    _channelsData[ch.channel_id] = ch;
                    var dateStr = '--';
                    var dateClass = '';
                    if (ch.last_analysis_date) {
                        var d = new Date(ch.last_analysis_date);
                        dateStr = pad(d.getDate()) + '/' + pad(d.getMonth()+1);
                        dateClass = ' has-data';
                    }
                    var flag = getFlag(ch.lingua || '');
                    html += '<div class="channel-item" id="ch-' + ch.channel_id + '" onclick="selectChannel(\\'' + ch.channel_id + '\\')">';
                    html += '<div class="channel-info">';
                    if (flag) html += '<span class="channel-flag">' + flag + '</span>';
                    html += '<span class="channel-name" title="' + escHtml(ch.channel_name) + '">' + escHtml(ch.channel_name) + '</span>';
                    html += '</div>';
                    html += '<span class="channel-date' + dateClass + '">' + dateStr + '</span>';
                    html += '</div>';
                }
                html += '</div>';
            }
            el.innerHTML = html;
        })
        .catch(function(e) {
            document.getElementById('channelList').innerHTML = '<div class="empty-state"><p>Erro ao carregar canais</p></div>';
        });
}

function selectChannel(channelId) {
    _selectedChannel = channelId;
    var items = document.querySelectorAll('.channel-item');
    for (var i = 0; i < items.length; i++) items[i].classList.remove('active');
    var el = document.getElementById('ch-' + channelId);
    if (el) el.classList.add('active');

    var ch = _channelsData[channelId] || {};
    document.getElementById('mainTitle').textContent = ch.channel_name || channelId;
    document.getElementById('mainActions').style.display = 'flex';

    loadLatestReport(channelId);
}

function loadLatestReport(channelId) {
    var area = document.getElementById('reportArea');
    area.innerHTML = '<div class="loading"><span class="loading-spinner"></span> Carregando relatorio...</div>';

    fetch('/api/analise-copy/' + channelId + '/latest')
        .then(function(r) {
            if (r.status === 404) return null;
            return r.json();
        })
        .then(function(data) {
            if (!data) {
                area.innerHTML = '<div class="empty-state"><h2>Nenhuma analise encontrada</h2><p>Clique em "Gerar Relatorio" para criar a primeira analise deste canal.</p></div>';
                return;
            }
            renderReport(data, area);
        })
        .catch(function(e) {
            area.innerHTML = '<div class="empty-state"><p>Erro ao carregar relatorio: ' + escHtml(e.message) + '</p></div>';
        });
}

function renderReport(data, container) {
    var text = data.report_text || '';
    if (!text) {
        container.innerHTML = '<div class="empty-state"><p>Relatorio sem conteudo</p></div>';
        return;
    }

    var runDate = data.run_date ? new Date(data.run_date).toLocaleString('pt-BR') : '';
    var infoHtml = runDate ? '<div style="color:var(--text-muted);font-size:0.75rem;margin-bottom:1rem;font-family:sans-serif;">Gerado em: ' + runDate + '</div>' : '';

    var lines = text.split('\\n');
    var html = '';
    var inSection = '';

    for (var i = 0; i < lines.length; i++) {
        var line = lines[i];
        var trimmed = line.trim();

        // Header lines (====)
        if (/^={10,}/.test(trimmed)) {
            html += '<div class="report-header-line">' + escHtml(line) + '</div>';
            continue;
        }

        // Report title (RELATORIO ...)
        if (/^RELATORIO /.test(trimmed)) {
            html += '<div class="report-title">' + escHtml(line) + '</div>';
            continue;
        }

        // Section headers (--- NAME ---)
        if (/^---\\s+(.+?)\\s+---/.test(trimmed)) {
            var secName = trimmed.replace(/^---\\s+/, '').replace(/\\s+---$/, '');
            var secClass = 'section-header';
            if (/OBSERVAC/.test(secName)) { secClass += ' obs'; inSection = 'obs'; }
            else if (/ANOMAL/.test(secName)) { secClass += ' anom'; inSection = 'anom'; }
            else if (/INSUFICIENTE/.test(secName)) { secClass += ' insuf'; inSection = 'insuf'; }
            else if (/ANTERIOR/.test(secName)) { secClass += ' comp'; inSection = 'comp'; }
            else { inSection = 'ranking'; }
            html += '<div class="' + secClass + '">' + escHtml(line) + '</div>';
            continue;
        }

        // Empty line
        if (trimmed === '') {
            html += '<br>';
            continue;
        }

        // Anomaly line (! Estrutura ...)
        if (/^!\\s+Estrutura/.test(trimmed)) {
            html += '<div class="anomaly-line">' + escHtml(line) + '</div>';
            continue;
        }

        // Anomaly detail (   Retencao: ... / Views: ... / Publicado: ... / NOTA: ...)
        if (inSection === 'anom' && /^\\s{2,}/.test(line)) {
            html += '<div class="anomaly-detail">' + escHtml(line) + '</div>';
            continue;
        }

        // Meta lines (Videos analisados / Periodo / Media geral)
        if (/^Videos analisados/.test(trimmed) || /^Periodo:/.test(trimmed) || /^Media geral/.test(trimmed)) {
            var metaHtml = escHtml(line);
            metaHtml = metaHtml.replace(/(\\d+\\.?\\d*%)/g, '<span class="val">$1</span>');
            metaHtml = metaHtml.replace(/(\\d+\\.?\\d* min)/g, '<span class="val">$1</span>');
            metaHtml = metaHtml.replace(/(\\d[\\d,]+ views)/g, '<span class="val">$1</span>');
            html += '<div class="report-meta">' + metaHtml + '</div>';
            continue;
        }

        // Table header line (# / Estr. / dashes)
        if (/^\\s*#\\s+Estr/.test(trimmed) || /^\\s*Estr\\.?\\s+/.test(trimmed) || /^\\s*[─-]{3,}/.test(trimmed)) {
            html += '<div class="table-header-line">' + escHtml(line) + '</div>';
            continue;
        }

        // Ranking lines (contain Acima/Media/Abaixo)
        if (/Acima|Media|Abaixo/.test(trimmed) && inSection === 'ranking') {
            var rLine = escHtml(line);
            rLine = rLine.replace(/Acima(\\s*\\([^)]*\\))?/g, '<span class="tag-acima">Acima$1</span>');
            rLine = rLine.replace(/Media(\\s*\\([^)]*\\))?/g, '<span class="tag-media">Media$1</span>');
            rLine = rLine.replace(/Abaixo(\\s*\\([^)]*\\))?/g, '<span class="tag-abaixo">Abaixo$1</span>');
            html += '<div class="ranking-line">' + rLine + '</div>';
            continue;
        }

        // Comparison lines (with +X% or -X%)
        if (inSection === 'comp' && /[+-]\\d+\\.?\\d*%/.test(trimmed)) {
            var cLine = escHtml(line);
            cLine = cLine.replace(/(\\+\\d+\\.?\\d*%)/g, '<span class="comp-positive">$1</span>');
            cLine = cLine.replace(/(\\-\\d+\\.?\\d*%)/g, '<span class="comp-negative">$1</span>');
            cLine = cLine.replace(/(Subiu[^<]*)/g, '<span class="comp-positive">$1</span>');
            cLine = cLine.replace(/(Caiu[^<]*)/g, '<span class="comp-negative">$1</span>');
            html += '<div class="ranking-line">' + cLine + '</div>';
            continue;
        }

        // Insufficient data lines
        if (inSection === 'insuf') {
            html += '<div class="insuf-line">' + escHtml(line) + '</div>';
            continue;
        }

        // Observation/narrative text
        if (inSection === 'obs' || (inSection === 'comp' && !/^\\s*\\d/.test(trimmed) && !/^\\s*Estr/.test(trimmed) && !/^Estruturas novas/.test(trimmed))) {
            html += '<div class="narrative">' + escHtml(line) + '</div>';
            continue;
        }

        // Default
        html += '<div>' + escHtml(line) + '</div>';
    }

    container.innerHTML = infoHtml + '<div class="report-container">' + html + '</div>';
}

function runAnalysis() {
    if (!_selectedChannel) return;
    var ch = _channelsData[_selectedChannel] || {};
    if (!confirm('Gerar relatorio para ' + (ch.channel_name || _selectedChannel) + '?\\n\\nIsso pode demorar 10-30 segundos.')) return;

    var btn = document.getElementById('btnRun');
    btn.disabled = true;
    btn.textContent = 'Gerando...';
    var area = document.getElementById('reportArea');
    area.innerHTML = '<div class="loading"><span class="loading-spinner"></span> Gerando relatorio... (10-30s)</div>';

    fetch('/api/analise-copy/' + _selectedChannel, { method: 'POST' })
        .then(function(r) { return r.json(); })
        .then(function(data) {
            btn.disabled = false;
            btn.textContent = 'Gerar Relatorio';
            if (data.success && data.report) {
                renderReport({ report_text: data.report, run_date: new Date().toISOString() }, area);
                loadChannels();
            } else {
                area.innerHTML = '<div class="empty-state"><h2>Erro na analise</h2><p>' + escHtml(data.error || 'Erro desconhecido') + '</p></div>';
            }
        })
        .catch(function(e) {
            btn.disabled = false;
            btn.textContent = 'Gerar Relatorio';
            area.innerHTML = '<div class="empty-state"><p>Erro: ' + escHtml(e.message) + '</p></div>';
        });
}

function runAll() {
    if (!confirm('Rodar analise de TODOS os canais?\\n\\nIsso pode demorar varios minutos.')) return;
    var btn = document.getElementById('btnRunAll');
    btn.disabled = true;
    btn.textContent = 'Rodando...';

    fetch('/api/analise-copy/run-all', { method: 'POST' })
        .then(function(r) { return r.json(); })
        .then(function(data) {
            btn.disabled = false;
            btn.textContent = 'Rodar Todos';
            var msg = 'Concluido! ' + (data.success_count || 0) + ' sucesso, ' + (data.error_count || 0) + ' erros de ' + (data.total_channels || 0) + ' canais.';
            alert(msg);
            loadChannels();
            if (_selectedChannel) loadLatestReport(_selectedChannel);
        })
        .catch(function(e) {
            btn.disabled = false;
            btn.textContent = 'Rodar Todos';
            alert('Erro: ' + e.message);
        });
}

function showHistory() {
    if (!_selectedChannel) return;
    document.getElementById('historyModal').classList.add('active');
    var el = document.getElementById('historyList');
    el.innerHTML = '<div class="loading"><span class="loading-spinner"></span> Carregando...</div>';

    fetch('/api/analise-copy/' + _selectedChannel + '/historico?limit=30')
        .then(function(r) { return r.json(); })
        .then(function(data) {
            var items = data.items || [];
            if (items.length === 0) {
                el.innerHTML = '<div class="empty-state"><p>Nenhum historico encontrado</p></div>';
                return;
            }
            var html = '';
            for (var i = 0; i < items.length; i++) {
                var item = items[i];
                var d = new Date(item.run_date);
                var dateStr = pad(d.getDate()) + '/' + pad(d.getMonth()+1) + '/' + d.getFullYear() + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes());
                var ret = item.channel_avg_retention ? item.channel_avg_retention.toFixed(1) + '%' : '--';
                var vids = item.total_videos_analyzed || '--';
                html += '<div class="history-item" onclick="loadHistoryReport(' + item.id + ')">';
                html += '<span class="history-date">' + dateStr + '</span>';
                html += '<span class="history-info">' + vids + ' videos | ret: ' + ret + '</span>';
                html += '</div>';
            }
            el.innerHTML = html;
        })
        .catch(function(e) {
            el.innerHTML = '<div class="empty-state"><p>Erro: ' + e.message + '</p></div>';
        });
}

function loadHistoryReport(runId) {
    closeHistory();
    if (!_selectedChannel) return;
    var area = document.getElementById('reportArea');
    area.innerHTML = '<div class="loading"><span class="loading-spinner"></span> Carregando relatorio...</div>';

    fetch('/api/analise-copy/' + _selectedChannel + '/latest')
        .then(function(r) { return r.json(); })
        .then(function(latest) {
            // Se o runId for o mais recente, ja temos
            if (latest && latest.id === runId) {
                renderReport(latest, area);
                return;
            }
            // Buscar historico e encontrar o run especifico
            return fetch('/api/analise-copy/' + _selectedChannel + '/historico?limit=100')
                .then(function(r2) { return r2.json(); })
                .then(function(hist) {
                    var items = hist.items || [];
                    // Historico nao traz report_text (so sumario)
                    // Precisamos do report_text - buscar da tabela diretamente
                    // Como nao temos endpoint por run_id, mostramos o sumario
                    for (var i = 0; i < items.length; i++) {
                        if (items[i].id === runId) {
                            var info = items[i];
                            var html = '<div class="report-container">';
                            html += '<div class="report-title">Relatorio de ' + new Date(info.run_date).toLocaleDateString('pt-BR') + '</div><br>';
                            html += '<div class="report-meta">Videos analisados: <span class="val">' + (info.total_videos_analyzed || '--') + '</span></div>';
                            html += '<div class="report-meta">Retencao media: <span class="val">' + (info.channel_avg_retention ? info.channel_avg_retention.toFixed(1) + '%' : '--') + '</span></div>';
                            html += '<div class="report-meta">Watch time medio: <span class="val">' + (info.channel_avg_watch_time ? info.channel_avg_watch_time.toFixed(1) + ' min' : '--') + '</span></div>';
                            html += '<div class="report-meta">Views media: <span class="val">' + (info.channel_avg_views ? Math.round(info.channel_avg_views).toLocaleString() : '--') + '</span></div>';
                            html += '<br><div style="color:var(--text-muted)">Relatorio detalhado disponivel apenas para a analise mais recente.</div>';
                            html += '</div>';
                            area.innerHTML = html;
                            return;
                        }
                    }
                    area.innerHTML = '<div class="empty-state"><p>Relatorio nao encontrado</p></div>';
                });
        })
        .catch(function(e) {
            area.innerHTML = '<div class="empty-state"><p>Erro: ' + e.message + '</p></div>';
        });
}

function closeHistory() {
    document.getElementById('historyModal').classList.remove('active');
}

function escHtml(s) {
    if (!s) return '';
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function pad(n) { return n < 10 ? '0' + n : '' + n; }

// Init
loadChannels();
</script>
</body>
</html>'''


@app.get("/dash-analise-copy", response_class=HTMLResponse)
async def dash_copy_analysis_page():
    """Dashboard de Analise de Copy - Interface web"""
    return DASH_COPY_ANALYSIS_HTML


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

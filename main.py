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
from comments_logs import CommentsLogsManager
from monetization_endpoints import router as monetization_router
from financeiro import FinanceiroService
from analytics import ChannelAnalytics

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


@app.get("/api/canais/{canal_id}/engagement")
async def get_canal_engagement(canal_id: int):
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

        # Buscar dados de engajamento do banco
        engagement_data = await db.get_canal_engagement_data(canal_id)

        # Se não há dados ainda, organizar resposta vazia estruturada
        if not engagement_data or engagement_data['summary']['total_comments'] == 0:

            # Buscar vídeos do canal para estruturar resposta
            videos = await db.get_videos_by_canal(canal_id, limit=20)

            videos_data = []
            for video in videos:
                videos_data.append({
                    'video_id': video.get('video_id'),
                    'video_title': video.get('titulo', ''),
                    'published_days_ago': (datetime.now(timezone.utc) - datetime.fromisoformat(video['data_publicacao'].replace('Z', '+00:00'))).days if video.get('data_publicacao') else 0,
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

        # Organizar dados por vídeo
        videos_dict = {}

        # Processar comentários com problemas
        for comment in engagement_data.get('problem_comments', []):
            video_id = comment['video_id']
            if video_id not in videos_dict:
                videos_dict[video_id] = {
                    'video_id': video_id,
                    'video_title': comment.get('video_title', ''),
                    'total_comments': 0,
                    'positive_comments': [],
                    'negative_comments': [],
                    'problem_count': 0
                }

            videos_dict[video_id]['negative_comments'].append(comment)
            videos_dict[video_id]['problem_count'] += 1

        # Processar comentários positivos
        for comment in engagement_data.get('positive_comments', []):
            video_id = comment['video_id']
            if video_id not in videos_dict:
                videos_dict[video_id] = {
                    'video_id': video_id,
                    'video_title': comment.get('video_title', ''),
                    'total_comments': 0,
                    'positive_comments': [],
                    'negative_comments': [],
                    'problem_count': 0
                }

            videos_dict[video_id]['positive_comments'].append(comment)

        # Agrupar problemas por tipo
        problems_grouped = {
            'audio': [],
            'video': [],
            'content': [],
            'technical': []
        }

        for comment in engagement_data.get('problem_comments', []):
            problem_type = comment.get('problem_type', 'other')
            if problem_type in problems_grouped:
                problems_grouped[problem_type].append({
                    'video_title': comment.get('video_title', ''),
                    'author': comment.get('author_name', ''),
                    'text_pt': comment.get('comment_text_pt', comment.get('comment_text_original', '')),
                    'specific_issue': comment.get('problem_description', ''),
                    'suggested_action': comment.get('suggested_action', '')
                })

        # Converter para lista de vídeos
        videos_list = []
        for video_id, video_data in videos_dict.items():
            video_data['positive_count'] = len(video_data['positive_comments'])
            video_data['negative_count'] = len(video_data['negative_comments'])
            video_data['total_comments'] = video_data['positive_count'] + video_data['negative_count']
            video_data['has_problems'] = video_data['problem_count'] > 0

            # Calcular sentiment score
            total = video_data['total_comments']
            if total > 0:
                video_data['sentiment_score'] = round((video_data['positive_count'] - video_data['negative_count']) / total * 100, 1)
            else:
                video_data['sentiment_score'] = 0

            videos_list.append(video_data)

        # Ordenar por mais recente ou maior engajamento
        videos_list.sort(key=lambda x: x['total_comments'], reverse=True)

        return {
            'summary': engagement_data['summary'],
            'videos': videos_list[:20],  # Top 20 vídeos
            'problems_grouped': problems_grouped
        }

    except Exception as e:
        logger.error(f"❌ Erro ao buscar engagement do canal {canal_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/collect-comments/{canal_id}")
async def collect_canal_comments(canal_id: int):
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

        # Buscar vídeos do canal
        videos_response = db.supabase.table("videos")\
            .select("video_id, titulo, views_atuais, data_publicacao")\
            .eq("canal_id", canal_id)\
            .order("data_publicacao", desc=True)\
            .limit(20)\
            .execute()

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
        from comment_analyzer import CommentAnalyzer
        analyzer = CommentAnalyzer()

        comments_data = await collector.get_all_channel_comments(
            channel_id=channel_id,
            canal_name=canal.get('nome_canal'),
            videos=videos
        )

        total_comments = comments_data.get('total_comments', 0)
        comments_by_video = comments_data.get('comments_by_video', {})

        # Analisar e salvar comentários por vídeo
        saved_count = 0
        for video_id, comments in comments_by_video.items():
            if comments:
                # Analisar lote de comentários
                analyzed_comments = await analyzer.analyze_comment_batch(comments)

                # Salvar no banco
                success = await db.save_video_comments(video_id, canal_id, analyzed_comments)
                if success:
                    saved_count += len(analyzed_comments)

        logger.info(f"✅ Coleta concluída: {saved_count}/{total_comments} comentários salvos")

        return {
            'success': True,
            'canal': canal.get('nome_canal'),
            'canal_id': canal_id,
            'total_videos': len(videos),
            'total_comments': total_comments,
            'comments_saved': saved_count,
            'message': f'Coleta concluída com sucesso! {saved_count} comentários analisados e salvos.'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao coletar comentários do canal {canal_id}: {e}")
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
        from gpt_analyzer import GPTAnalyzer

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

        # Criar GPTAnalyzer e CommentsDB UMA vez só (fora do loop)
        gpt_analyzer = None
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
                            for video in videos_data[:20]:  # Limitar a 20 vídeos mais recentes
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
                                # Inicializar GPTAnalyzer e CommentsDB uma vez só (na primeira vez)
                                if gpt_analyzer is None:
                                    logger.info("🤖 Inicializando GPTAnalyzer e CommentsDB...")
                                    from gpt_analyzer import GPTAnalyzer
                                    from database_comments import CommentsDB
                                    gpt_analyzer = GPTAnalyzer()
                                    comments_db = CommentsDB()
                                    logger.info("✅ GPTAnalyzer e CommentsDB inicializados")

                                for video_id, video_comments in comments_data.get('comments_by_video', {}).items():
                                    if video_comments and video_comments.get('comments'):
                                        # Analisar batch de comentários com GPT (com retry)
                                        analyzed_comments = None
                                        max_retries = 3

                                        for attempt in range(max_retries):
                                            try:
                                                logger.debug(f"🤖 Tentativa {attempt + 1}/{max_retries} de análise GPT para {len(video_comments['comments'])} comentários")

                                                analyzed_comments = await gpt_analyzer.analyze_batch(
                                                    comments=video_comments['comments'],
                                                    video_title=video_comments.get('video_title', ''),
                                                    canal_name=canal['nome_canal'],
                                                    batch_size=15  # Reduzido para evitar erros de JSON
                                                )

                                                if analyzed_comments is not None and len(analyzed_comments) > 0:
                                                    logger.info(f"✅ GPT analisou com sucesso {len(analyzed_comments)} comentários")
                                                    break  # Sucesso, sair do loop de retry
                                                else:
                                                    logger.warning(f"⚠️ GPT retornou lista vazia na tentativa {attempt + 1}")

                                            except Exception as e:
                                                logger.warning(f"⚠️ Tentativa {attempt + 1} falhou para análise GPT de {canal['nome_canal']}: {str(e)}")
                                                if attempt < max_retries - 1:
                                                    await asyncio.sleep(2)  # Aguardar 2 segundos antes de tentar novamente
                                                else:
                                                    logger.error(f"❌ Falha definitiva na análise GPT após {max_retries} tentativas")

                                        # SEMPRE salvar comentários (com ou sem análise GPT)
                                        comments_to_save = []

                                        if analyzed_comments and len(analyzed_comments) > 0:
                                            # GPT analisou com sucesso
                                            comments_to_save = analyzed_comments
                                            logger.info(f"✅ GPT analisou {len(analyzed_comments)} comentários")
                                            comentarios_analisados_total += len(analyzed_comments)
                                        else:
                                            # GPT falhou - salvar SEM análise para não perder dados
                                            logger.warning(f"⚠️ GPT falhou após {max_retries} tentativas - salvando {len(video_comments['comments'])} comentários SEM análise")

                                            # Preparar comentários sem análise (serão reprocessados depois)
                                            for comment in video_comments['comments']:
                                                comment_data = {
                                                    'comment_id': comment.get('comment_id'),
                                                    'video_id': video_id,
                                                    'canal_id': canal['id'],
                                                    'author': comment.get('author'),
                                                    'comment_text_original': comment.get('text', ''),
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
                                                    'analyzed_at': None  # NULL indica que precisa ser analisado
                                                }
                                                comments_to_save.append(comment_data)

                                            comentarios_com_erro_total += len(comments_to_save)

                                        # Salvar comentários (com ou sem análise)
                                        if comments_to_save:
                                            try:
                                                await comments_db.save_video_comments(
                                                    video_id=video_id,
                                                    canal_id=canal['id'],
                                                    comments=comments_to_save
                                                )
                                                logger.info(f"💾 {len(comments_to_save)} comentários salvos para {canal['nome_canal']}")
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
                                    'comentarios_analisados_gpt': comentarios_analisados_total - (comentarios_analisados_total - len([c for c in comments_to_save if c.get('analyzed_at')]))
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
                    'comentarios_analisados': comentarios_analisados_total,
                    'comentarios_nao_analisados': comentarios_com_erro_total,
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
                    from gpt_analyzer import GPTAnalyzer
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

            # 🔄 REPROCESSAMENTO AUTOMÁTICO DE COMENTÁRIOS SEM ANÁLISE
            if comentarios_total > 0:  # Só reprocessar se coletou comentários
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
        asyncio.create_task(weekly_report_scheduler())
        asyncio.create_task(schedule_spreadsheet_scanner())

        # Upload Queue Worker (isolado - falha não afeta main app)
        try:
            from yt_uploader.queue_worker import start_queue_worker
            asyncio.create_task(start_queue_worker())
            logger.info("✅ Upload queue worker scheduled")
        except Exception as e:
            logger.warning(f"⚠️ Upload worker disabled: {e}")

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

                    # Busca retry_count atual do banco (TOTAL de tentativas incluindo scanner retries)
                    current_upload = get_upload_by_id(upload_id)
                    total_retry_count = current_upload.get('retry_count', 0) if current_upload else 0

                    update_upload_status(
                        upload_id,
                        'failed',
                        error_message=error_msg,
                        retry_count=total_retry_count + 1  # Incrementa contador total
                    )

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

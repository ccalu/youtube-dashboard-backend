"""
Coleta OAuth de Métricas de Monetização
Roda automaticamente no Railway às 5 AM
Coleta revenue REAL via YouTube Analytics API (OAuth)
"""
import os
import sys
import requests
import json
import logging
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Fix encoding for Windows (local testing)
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configurar logging
log_dir = os.getenv('LOG_DIR', './logs')
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(f'{log_dir}/coleta_oauth.log'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# =============================================================================
# CONFIGURAÇÕES
# =============================================================================
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://prvkmzstyedepvlbppyo.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBydmttenN0eWVkZXB2bGJwcHlvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQxNDY3MTQsImV4cCI6MjA1OTcyMjcxNH0.T0aspHrF0tz1G6iVOBIO3zgvs1g5vvQcb25jhGriQGo")

# Headers para Supabase
SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates,return=minimal"
}

# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def get_channels():
    """Busca todos os canais monetizados no Supabase"""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/yt_channels",
        params={"is_monetized": "eq.true"},
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    )
    if resp.status_code == 200:
        return resp.json()
    log.error(f"Erro ao buscar canais: {resp.text}")
    return []

def get_tokens(channel_id):
    """Busca tokens OAuth de um canal"""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/yt_oauth_tokens",
        params={"channel_id": f"eq.{channel_id}"},
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    )
    if resp.status_code == 200 and resp.json():
        return resp.json()[0]
    return None

def get_proxy_credentials(proxy_name):
    """Busca credenciais OAuth do proxy"""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/yt_proxy_credentials",
        params={"proxy_name": f"eq.{proxy_name}"},
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    )
    if resp.status_code == 200 and resp.json():
        return resp.json()[0]
    log.error(f"Credenciais nao encontradas para proxy {proxy_name}")
    return None

def refresh_access_token(refresh_token, client_id, client_secret):
    """Renova o access_token usando o refresh_token"""
    resp = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    })
    if resp.status_code == 200:
        return resp.json().get("access_token")
    log.error(f"Erro ao renovar token: {resp.text}")
    return None

def update_tokens(channel_id, access_token):
    """Atualiza access_token no Supabase"""
    requests.patch(
        f"{SUPABASE_URL}/rest/v1/yt_oauth_tokens",
        params={"channel_id": f"eq.{channel_id}"},
        headers=SUPABASE_HEADERS,
        json={"access_token": access_token}
    )

def log_collection(channel_id, status, message):
    """Salva log de coleta no Supabase"""
    requests.post(
        f"{SUPABASE_URL}/rest/v1/yt_collection_logs",
        headers=SUPABASE_HEADERS,
        json={
            "channel_id": channel_id,
            "status": status,
            "message": message
        }
    )

# =============================================================================
# COLETA DE DADOS
# =============================================================================

def collect_daily_metrics(channel_id, access_token, start_date, end_date):
    """Coleta métricas diárias do canal"""
    headers = {"Authorization": f"Bearer {access_token}"}

    resp = requests.get(
        "https://youtubeanalytics.googleapis.com/v2/reports",
        params={
            "ids": f"channel=={channel_id}",
            "startDate": start_date,
            "endDate": end_date,
            "metrics": "estimatedRevenue,views,likes,comments,shares,subscribersGained,subscribersLost,estimatedMinutesWatched,averageViewDuration,averageViewPercentage",
            "dimensions": "day",
            "sort": "day"
        },
        headers=headers
    )

    if resp.status_code != 200:
        log.error(f"Erro métricas diárias: {resp.status_code} - {resp.text[:200]}")
        return []

    return resp.json().get("rows", [])

def collect_country_metrics(channel_id, access_token, start_date, end_date):
    """Coleta métricas por país"""
    headers = {"Authorization": f"Bearer {access_token}"}

    resp = requests.get(
        "https://youtubeanalytics.googleapis.com/v2/reports",
        params={
            "ids": f"channel=={channel_id}",
            "startDate": start_date,
            "endDate": end_date,
            "metrics": "views,estimatedRevenue,estimatedMinutesWatched",
            "dimensions": "country",
            "sort": "-views",
            "maxResults": "25"
        },
        headers=headers
    )

    if resp.status_code != 200:
        log.error(f"Erro métricas país: {resp.status_code}")
        return []

    return resp.json().get("rows", [])

def collect_video_metrics(channel_id, access_token, start_date, end_date):
    """Coleta métricas por vídeo"""
    headers = {"Authorization": f"Bearer {access_token}"}

    # Buscar métricas
    resp = requests.get(
        "https://youtubeanalytics.googleapis.com/v2/reports",
        params={
            "ids": f"channel=={channel_id}",
            "startDate": start_date,
            "endDate": end_date,
            "metrics": "estimatedRevenue,views,likes,comments,subscribersGained,averageViewDuration,averageViewPercentage,cardClickRate",
            "dimensions": "video",
            "sort": "-views",
            "maxResults": "50"
        },
        headers=headers
    )

    if resp.status_code != 200:
        log.error(f"Erro métricas vídeo: {resp.status_code}")
        return []

    rows = resp.json().get("rows", [])

    # Títulos removidos - OAuth não deve usar YouTube Data API v3
    # Videos serão salvos apenas com video_id e métricas

    return rows

# =============================================================================
# NOVAS FUNÇÕES DE COLETA - ANALYTICS AVANÇADO
# =============================================================================

def collect_traffic_sources(channel_id, access_token, start_date, end_date):
    """Coleta fontes de tráfego do canal"""
    headers = {"Authorization": f"Bearer {access_token}"}

    resp = requests.get(
        "https://youtubeanalytics.googleapis.com/v2/reports",
        params={
            "ids": f"channel=={channel_id}",
            "startDate": start_date,
            "endDate": end_date,
            "metrics": "views,estimatedMinutesWatched",
            "dimensions": "insightTrafficSourceType",
            "sort": "-views"
        },
        headers=headers
    )

    if resp.status_code != 200:
        log.error(f"Erro traffic sources: {resp.status_code}")
        return []

    return resp.json().get("rows", [])

def collect_search_terms(channel_id, access_token, start_date, end_date):
    """Coleta top 10 termos de busca"""
    headers = {"Authorization": f"Bearer {access_token}"}

    resp = requests.get(
        "https://youtubeanalytics.googleapis.com/v2/reports",
        params={
            "ids": f"channel=={channel_id}",
            "startDate": start_date,
            "endDate": end_date,
            "metrics": "views",
            "dimensions": "insightTrafficSourceDetail",
            "filters": "insightTrafficSourceType==YT_SEARCH",
            "maxResults": "10",
            "sort": "-views"
        },
        headers=headers
    )

    if resp.status_code != 200:
        log.error(f"Erro search terms: {resp.status_code}")
        return []

    return resp.json().get("rows", [])

def collect_suggested_videos(channel_id, access_token, start_date, end_date):
    """Coleta top 10 vídeos que recomendam"""
    headers = {"Authorization": f"Bearer {access_token}"}

    resp = requests.get(
        "https://youtubeanalytics.googleapis.com/v2/reports",
        params={
            "ids": f"channel=={channel_id}",
            "startDate": start_date,
            "endDate": end_date,
            "metrics": "views",
            "dimensions": "insightTrafficSourceDetail",
            "filters": "insightTrafficSourceType==YT_RELATED",
            "maxResults": "10",
            "sort": "-views"
        },
        headers=headers
    )

    if resp.status_code != 200:
        log.error(f"Erro suggested videos: {resp.status_code}")
        return []

    return resp.json().get("rows", [])

def collect_demographics(channel_id, access_token, start_date, end_date):
    """Coleta demographics (idade e gênero)"""
    headers = {"Authorization": f"Bearer {access_token}"}

    resp = requests.get(
        "https://youtubeanalytics.googleapis.com/v2/reports",
        params={
            "ids": f"channel=={channel_id}",
            "startDate": start_date,
            "endDate": end_date,
            "metrics": "viewerPercentage",
            "dimensions": "ageGroup,gender",
            "sort": "-viewerPercentage"
        },
        headers=headers
    )

    if resp.status_code != 200:
        log.error(f"Erro demographics: {resp.status_code}")
        return []

    return resp.json().get("rows", [])

def collect_device_metrics(channel_id, access_token, start_date, end_date):
    """Coleta distribuição de dispositivos"""
    headers = {"Authorization": f"Bearer {access_token}"}

    resp = requests.get(
        "https://youtubeanalytics.googleapis.com/v2/reports",
        params={
            "ids": f"channel=={channel_id}",
            "startDate": start_date,
            "endDate": end_date,
            "metrics": "views,estimatedMinutesWatched",
            "dimensions": "deviceType",
            "sort": "-views"
        },
        headers=headers
    )

    if resp.status_code != 200:
        log.error(f"Erro device metrics: {resp.status_code}")
        return []

    return resp.json().get("rows", [])

# =============================================================================
# SALVAR DADOS
# =============================================================================

def save_daily_metrics(channel_id, rows):
    """Salva métricas diárias no Supabase - APENAS se revenue > 0 ou views > 0"""
    saved = 0
    for row in rows:
        date = row[0]
        revenue = float(row[1])
        views = int(row[2])

        # IMPORTANTE: YouTube tem delay de 2-3 dias para revenue
        # Se revenue = 0 mas views > 0, provavelmente é delay da API
        # Não salvar para não sobrescrever estimativas
        if revenue == 0 and views == 0:
            log.warning(f"[{date}] Sem dados (revenue=0, views=0) - ignorando")
            continue

        # Verificar se já existe dado REAL para esta data
        check_resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/yt_daily_metrics",
            params={
                "channel_id": f"eq.{channel_id}",
                "date": f"eq.{date}",
                "is_estimate": "eq.false",
                "select": "revenue"
            },
            headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        )

        if check_resp.status_code == 200 and check_resp.json():
            existing = check_resp.json()[0]
            existing_revenue = existing.get("revenue", 0)

            # Se já tem revenue real > 0, não sobrescrever com 0
            if existing_revenue > 0 and revenue == 0:
                log.info(f"[{date}] Já tem revenue real: ${existing_revenue:.2f} - mantendo")
                continue

        # Se revenue = 0 mas tem views, é provável delay da API
        # Não marcar como "real" para não confundir
        if revenue == 0 and views > 0:
            log.warning(f"[{date}] Revenue=0 mas views={views} - provável delay da API")
            # Continua e salva, mas pode ser que o frontend ignore

        # Extrair métricas de retenção se existirem
        avg_duration = float(row[9]) if len(row) > 9 else 0
        avg_percentage = float(row[10]) if len(row) > 10 else 0

        data = {
            "channel_id": channel_id,
            "date": date,
            "revenue": revenue,
            "views": views,
            "likes": int(row[3]),
            "comments": int(row[4]),
            "shares": int(row[5]),
            "subscribers_gained": int(row[6]),
            "subscribers_lost": int(row[7]),
            "watch_time_minutes": int(row[8]),
            "rpm": (revenue / views * 1000) if views > 0 else 0,
            "avg_view_duration_sec": float(avg_duration) if avg_duration else None,  # Garante float ou NULL
            "avg_retention_pct": float(avg_percentage) if avg_percentage else None,     # Garante float ou NULL
            "ctr_approx": None,  # CTR removido - não temos dados confiáveis
            "is_estimate": False  # Dados do YouTube Analytics (podem ter delay)
        }

        # Usar PATCH para atualizar registros existentes
        # Primeiro tenta atualizar, se não existir, cria novo
        update_resp = requests.patch(
            f"{SUPABASE_URL}/rest/v1/yt_daily_metrics",
            params={"channel_id": f"eq.{channel_id}", "date": f"eq.{date}"},
            headers=SUPABASE_HEADERS,
            json=data
        )

        if update_resp.status_code in [200, 204]:
            saved += 1
            if revenue > 0:
                log.info(f"[{date}] Revenue real atualizado: ${revenue:.2f}")
        elif update_resp.status_code == 404:
            # Se não existir, criar novo
            create_resp = requests.post(
                f"{SUPABASE_URL}/rest/v1/yt_daily_metrics",
                headers=SUPABASE_HEADERS,
                json=data
            )
            if create_resp.status_code in [200, 201, 204]:
                saved += 1
                if revenue > 0:
                    log.info(f"[{date}] Revenue real criado: ${revenue:.2f}")
            else:
                log.error(f"[{date}] Erro ao criar: {create_resp.status_code}")
        else:
            log.error(f"[{date}] Erro ao atualizar: {update_resp.status_code}")

    return saved

def save_country_metrics(channel_id, rows, date):
    """Salva métricas por país no Supabase"""
    saved = 0
    for row in rows:
        data = {
            "channel_id": channel_id,
            "date": date,
            "country_code": row[0],
            "views": int(row[1]),
            "revenue": float(row[2]),
            "watch_time_minutes": int(row[3])
        }

        resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/yt_country_metrics",
            headers=SUPABASE_HEADERS,
            json=data
        )
        if resp.status_code in [200, 201, 204]:
            saved += 1

    return saved

def save_video_metrics(channel_id, rows):
    """Salva métricas por vídeo no Supabase (tabela atual - valores totais)"""
    saved = 0
    for row in rows:
        data = {
            "channel_id": channel_id,
            "video_id": row[0],
            "revenue": float(row[1]),
            "views": int(row[2]),
            "likes": int(row[3]),
            "comments": int(row[4]),
            "subscribers_gained": int(row[5]),
            "title": "",  # Titulo removido - OAuth nao usa Data API v3
            "updated_at": datetime.now().isoformat()
        }

        resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/yt_video_metrics",
            headers=SUPABASE_HEADERS,
            json=data
        )
        if resp.status_code in [200, 201, 204]:
            saved += 1

    return saved

def save_video_daily(channel_id, rows, date):
    """Salva histórico diário por vídeo no Supabase"""
    saved = 0
    for row in rows:
        data = {
            "channel_id": channel_id,
            "video_id": row[0],
            "date": date,
            "revenue": float(row[1]),
            "views": int(row[2]),
            "likes": int(row[3]),
            "comments": int(row[4]),
            "subscribers_gained": int(row[5]),
            "title": ""  # Titulo removido - OAuth nao usa Data API v3
        }

        resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/yt_video_daily",
            headers=SUPABASE_HEADERS,
            json=data
        )
        if resp.status_code in [200, 201, 204]:
            saved += 1

    return saved

# =============================================================================
# SALVAR DADOS - ANALYTICS AVANÇADO
# =============================================================================

def save_traffic_sources(channel_id, date, rows):
    """Salva fontes de tráfego"""
    saved = 0
    total_views = sum(int(row[1]) for row in rows) if rows else 1  # Evitar divisão por zero

    for row in rows:
        source_type = row[0]
        views = int(row[1])
        watch_time = int(row[2]) if len(row) > 2 else 0
        percentage = round((views / total_views) * 100, 2) if total_views > 0 else 0

        data = {
            "channel_id": channel_id,
            "date": date,
            "source_type": source_type,
            "views": views,
            "watch_time_minutes": watch_time,
            "percentage": percentage
        }

        resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/yt_traffic_summary",
            headers=SUPABASE_HEADERS,
            json=data
        )

        if resp.status_code in [200, 201]:
            saved += 1

    log.info(f"[Traffic] {saved} fontes salvas")
    return saved

def save_search_terms(channel_id, date, rows):
    """Salva termos de busca"""
    saved = 0
    total_views = sum(int(row[1]) for row in rows) if rows else 1

    for row in rows:
        search_term = row[0]
        views = int(row[1])
        percentage = round((views / total_views) * 100, 2) if total_views > 0 else 0

        data = {
            "channel_id": channel_id,
            "date": date,
            "search_term": search_term,
            "views": views,
            "percentage_of_search": percentage
        }

        resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/yt_search_analytics",
            headers=SUPABASE_HEADERS,
            json=data
        )

        if resp.status_code in [200, 201]:
            saved += 1

    log.info(f"[Search] {saved} termos salvos")
    return saved

def save_suggested_videos(channel_id, date, rows):
    """Salva vídeos que recomendam"""
    saved = 0

    for row in rows:
        video_id = row[0]
        views = int(row[1])

        # O ID pode vir como URL completa ou só ID
        if "watch?v=" in video_id:
            video_id = video_id.split("watch?v=")[1].split("&")[0]

        data = {
            "channel_id": channel_id,
            "date": date,
            "source_video_id": video_id,
            "source_video_title": "",  # API não retorna título
            "source_channel_name": "",  # API não retorna canal
            "views_generated": views
        }

        resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/yt_suggested_sources",
            headers=SUPABASE_HEADERS,
            json=data
        )

        if resp.status_code in [200, 201]:
            saved += 1

    log.info(f"[Suggested] {saved} vídeos salvos")
    return saved

def save_demographics(channel_id, date, rows):
    """Salva demographics"""
    saved = 0

    for row in rows:
        age_group = row[0]
        gender = row[1]
        percentage = float(row[2])

        data = {
            "channel_id": channel_id,
            "date": date,
            "age_group": age_group,
            "gender": gender,
            "views": 0,  # API retorna só percentual
            "watch_time_minutes": 0,
            "percentage": percentage
        }

        resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/yt_demographics",
            headers=SUPABASE_HEADERS,
            json=data
        )

        if resp.status_code in [200, 201]:
            saved += 1

    log.info(f"[Demographics] {saved} registros salvos")
    return saved

def save_device_metrics(channel_id, date, rows):
    """Salva métricas de dispositivos"""
    saved = 0
    total_views = sum(int(row[1]) for row in rows) if rows else 1

    for row in rows:
        device_type = row[0]
        views = int(row[1])
        watch_time = int(row[2]) if len(row) > 2 else 0
        percentage = round((views / total_views) * 100, 2) if total_views > 0 else 0

        data = {
            "channel_id": channel_id,
            "date": date,
            "device_type": device_type,
            "views": views,
            "watch_time_minutes": watch_time,
            "percentage": percentage
        }

        resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/yt_device_metrics",
            headers=SUPABASE_HEADERS,
            json=data
        )

        if resp.status_code in [200, 201]:
            saved += 1

    log.info(f"[Devices] {saved} dispositivos salvos")
    return saved

# FUNÇÃO DESABILITADA - USA DATA API V3 (CONSOME QUOTA DE MINERAÇÃO)
# def update_channel_info(channel_id, access_token):
#     """Atualiza info do canal (inscritos, vídeos)"""
#     headers = {"Authorization": f"Bearer {access_token}"}
#
#     resp = requests.get(
#         "https://www.googleapis.com/youtube/v3/channels",
#         params={"part": "statistics", "id": channel_id},
#         headers=headers
#     )
#
#     if resp.status_code == 200:
#         items = resp.json().get("items", [])
#         if items:
#             stats = items[0]["statistics"]
#             requests.patch(
#                 f"{SUPABASE_URL}/rest/v1/yt_channels",
#                 params={"channel_id": f"eq.{channel_id}"},
#                 headers=SUPABASE_HEADERS,
#                 json={
#                     "total_subscribers": int(stats.get("subscriberCount", 0)),
#                     "total_videos": int(stats.get("videoCount", 0)),
#                     "updated_at": datetime.now().isoformat()
#                 }
#             )

# =============================================================================
# MAIN - FUNÇÃO ASSÍNCRONA PARA RAILWAY
# =============================================================================

async def collect_oauth_metrics():
    """
    Coleta métricas OAuth dos canais monetizados
    Chamado automaticamente pelo scheduler às 5 AM
    """
    log.info("=" * 60)
    log.info("INICIANDO COLETA OAUTH (REVENUE REAL)")
    log.info("=" * 60)

    # Datas - Ajustado para delay do YouTube (2-3 dias)
    # YouTube tem delay de 2-3 dias, então pedimos dados até 3 dias atrás
    end_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")

    # Buscar canais
    channels = get_channels()
    log.info(f"Canais monetizados: {len(channels)}")

    success_count = 0
    error_count = 0

    for channel in channels:
        channel_id = channel["channel_id"]
        channel_name = channel.get("channel_name", channel_id)
        proxy_name = channel.get("proxy_name", "C000.1")

        log.info(f"\n[{channel_name}] Iniciando coleta OAuth... (proxy: {proxy_name})")

        try:
            # Buscar credenciais do proxy
            credentials = get_proxy_credentials(proxy_name)
            if not credentials:
                log.error(f"[{channel_name}] Credenciais do proxy {proxy_name} não encontradas!")
                log_collection(channel_id, "error", f"Credenciais proxy {proxy_name} não encontradas")
                error_count += 1
                continue

            # Buscar tokens
            tokens = get_tokens(channel_id)
            if not tokens:
                log.error(f"[{channel_name}] Sem tokens cadastrados!")
                log_collection(channel_id, "error", "Tokens não encontrados")
                error_count += 1
                continue

            # Renovar access_token usando credenciais do proxy
            access_token = refresh_access_token(
                tokens["refresh_token"],
                credentials["client_id"],
                credentials["client_secret"]
            )
            if not access_token:
                log.error(f"[{channel_name}] Falha ao renovar token!")
                log_collection(channel_id, "error", "Falha ao renovar token")
                error_count += 1
                continue

            # Atualizar token no banco
            update_tokens(channel_id, access_token)

            # Coletar métricas diárias
            daily_rows = collect_daily_metrics(channel_id, access_token, start_date, end_date)
            saved_daily = save_daily_metrics(channel_id, daily_rows)
            log.info(f"[{channel_name}] Métricas diárias: {saved_daily} dias salvos")

            # Coletar métricas por país (apenas do dia anterior)
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            country_rows = collect_country_metrics(channel_id, access_token, yesterday, yesterday)
            saved_country = save_country_metrics(channel_id, country_rows, yesterday)
            log.info(f"[{channel_name}] Métricas por país: {saved_country} países salvos")

            # Coletar métricas por vídeo
            video_rows = collect_video_metrics(channel_id, access_token, start_date, end_date)
            saved_video = save_video_metrics(channel_id, video_rows)
            log.info(f"[{channel_name}] Métricas por vídeo: {saved_video} vídeos salvos")

            # Salvar histórico diário por vídeo (snapshot de hoje)
            today = datetime.now().strftime("%Y-%m-%d")
            saved_video_daily = save_video_daily(channel_id, video_rows, today)
            log.info(f"[{channel_name}] Histórico diário vídeos: {saved_video_daily} registros")

            # =============================================================
            # COLETA DE ANALYTICS AVANÇADO (NOVAS MÉTRICAS)
            # =============================================================
            log.info(f"[{channel_name}] Iniciando coleta de analytics avançado...")

            # Coletar fontes de tráfego
            traffic_rows = collect_traffic_sources(channel_id, access_token, yesterday, yesterday)
            saved_traffic = save_traffic_sources(channel_id, yesterday, traffic_rows)
            log.info(f"[{channel_name}] Fontes de tráfego: {saved_traffic} salvos")

            # Coletar termos de busca
            search_rows = collect_search_terms(channel_id, access_token, yesterday, yesterday)
            saved_search = save_search_terms(channel_id, yesterday, search_rows)
            log.info(f"[{channel_name}] Termos de busca: {saved_search} salvos")

            # Coletar vídeos que recomendam
            suggested_rows = collect_suggested_videos(channel_id, access_token, yesterday, yesterday)
            saved_suggested = save_suggested_videos(channel_id, yesterday, suggested_rows)
            log.info(f"[{channel_name}] Vídeos sugeridos: {saved_suggested} salvos")

            # Coletar demographics
            demo_rows = collect_demographics(channel_id, access_token, yesterday, yesterday)
            saved_demo = save_demographics(channel_id, yesterday, demo_rows)
            log.info(f"[{channel_name}] Demographics: {saved_demo} salvos")

            # Coletar dispositivos
            device_rows = collect_device_metrics(channel_id, access_token, yesterday, yesterday)
            saved_devices = save_device_metrics(channel_id, yesterday, device_rows)
            log.info(f"[{channel_name}] Dispositivos: {saved_devices} salvos")

            # Atualizar info do canal - DESABILITADO (usa Data API v3)
            # update_channel_info(channel_id, access_token)

            # Log de sucesso
            log_collection(channel_id, "success", f"Coletados {saved_daily} dias, {saved_country} países, {saved_video} vídeos")
            success_count += 1

        except Exception as e:
            log.error(f"[{channel_name}] Erro: {str(e)}")
            log_collection(channel_id, "error", str(e)[:200])
            error_count += 1

    log.info("\n" + "=" * 60)
    log.info(f"COLETA OAUTH FINALIZADA - Sucesso: {success_count} | Erros: {error_count}")
    log.info("=" * 60)

    return {"success": success_count, "errors": error_count}

# =============================================================================
# EXECUÇÃO LOCAL (TESTE)
# =============================================================================

def main():
    """Função para testes locais"""
    asyncio.run(collect_oauth_metrics())

if __name__ == "__main__":
    main()

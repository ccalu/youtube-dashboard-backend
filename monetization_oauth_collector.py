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
            "metrics": "estimatedRevenue,views,likes,comments,shares,subscribersGained,subscribersLost,estimatedMinutesWatched",
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
            "metrics": "estimatedRevenue,views,likes,comments,subscribersGained",
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
# SALVAR DADOS
# =============================================================================

def save_daily_metrics(channel_id, rows):
    """Salva métricas diárias no Supabase"""
    saved = 0
    for row in rows:
        date = row[0]
        data = {
            "channel_id": channel_id,
            "date": date,
            "revenue": float(row[1]),
            "views": int(row[2]),
            "likes": int(row[3]),
            "comments": int(row[4]),
            "shares": int(row[5]),
            "subscribers_gained": int(row[6]),
            "subscribers_lost": int(row[7]),
            "watch_time_minutes": int(row[8]),
            "rpm": (float(row[1]) / int(row[2]) * 1000) if int(row[2]) > 0 else 0,
            "is_estimate": False  # Dados REAIS do YouTube Analytics
        }

        resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/yt_daily_metrics",
            headers=SUPABASE_HEADERS,
            json=data
        )
        # 201 = created, 200/204 = updated (upsert)
        if resp.status_code in [200, 201, 204]:
            saved += 1
        else:
            log.debug(f"Daily metrics {date}: {resp.status_code}")

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

    # Datas
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

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

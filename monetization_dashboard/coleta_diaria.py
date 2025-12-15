"""
Coleta Diaria de Metricas do YouTube
Roda via Agendador de Tarefas do Windows
"""
import requests
import json
from datetime import datetime, timedelta
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('D:/ContentFactory/youtube-dashboard-backend/monetization_dashboard/logs/coleta.log'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# =============================================================================
# CONFIGURACOES
# =============================================================================
SUPABASE_URL = "https://prvkmzstyedepvlbppyo.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBydmttenN0eWVkZXB2bGJwcHlvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQxNDY3MTQsImV4cCI6MjA1OTcyMjcxNH0.T0aspHrF0tz1G6iVOBIO3zgvs1g5vvQcb25jhGriQGo"

# Headers para Supabase
SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates,return=minimal"
}

# =============================================================================
# FUNCOES AUXILIARES
# =============================================================================

def get_channels():
    """Busca todos os canais cadastrados no Supabase"""
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
    """Coleta metricas diarias do canal"""
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
        log.error(f"Erro metricas diarias: {resp.status_code} - {resp.text[:200]}")
        return []

    return resp.json().get("rows", [])

def collect_country_metrics(channel_id, access_token, start_date, end_date):
    """Coleta metricas por pais"""
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
        log.error(f"Erro metricas pais: {resp.status_code}")
        return []

    return resp.json().get("rows", [])

def collect_video_metrics(channel_id, access_token, start_date, end_date):
    """Coleta metricas por video"""
    headers = {"Authorization": f"Bearer {access_token}"}

    # Buscar metricas
    resp = requests.get(
        "https://youtubeanalytics.googleapis.com/v2/reports",
        params={
            "ids": f"channel=={channel_id}",
            "startDate": start_date,
            "endDate": end_date,
            "metrics": "estimatedRevenue,views,likes,comments,subscribersGained,averageViewDuration,averageViewPercentage",
            "dimensions": "video",
            "sort": "-views",
            "maxResults": "50"
        },
        headers=headers
    )

    if resp.status_code != 200:
        log.error(f"Erro metricas video: {resp.status_code}")
        return []

    rows = resp.json().get("rows", [])

    # Buscar titulos dos videos
    if rows:
        video_ids = [r[0] for r in rows[:25]]
        resp2 = requests.get(
            "https://www.googleapis.com/youtube/v3/videos",
            params={"part": "snippet", "id": ",".join(video_ids)},
            headers=headers
        )

        titles = {}
        if resp2.status_code == 200:
            for v in resp2.json().get("items", []):
                titles[v["id"]] = v["snippet"]["title"]

        # Adicionar titulos aos rows
        for row in rows:
            row.append(titles.get(row[0], ""))

    return rows

# =============================================================================
# SALVAR DADOS
# =============================================================================

def save_daily_metrics(channel_id, rows):
    """Salva metricas diarias no Supabase"""
    saved = 0
    for row in rows:
        date = row[0]
        # Extrair métricas com valores padrão se não existirem
        avg_duration = float(row[9]) if len(row) > 9 else 0
        avg_percentage = float(row[10]) if len(row) > 10 else 0

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
            "avg_view_duration_sec": float(avg_duration) if avg_duration else None,  # Garante float ou NULL
            "avg_retention_pct": float(avg_percentage) if avg_percentage else None,     # Garante float ou NULL
            "ctr_approx": None,  # CTR removido - não temos dados confiáveis
            "is_estimate": False  # IMPORTANTE: Marca como dados REAIS do OAuth
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
            log.info(f"[{date}] Atualizado: ${float(row[1]):.2f} | Ret: {avg_percentage:.1f}%")
        elif update_resp.status_code == 404:
            # Se não existir, criar novo
            create_resp = requests.post(
                f"{SUPABASE_URL}/rest/v1/yt_daily_metrics",
                headers=SUPABASE_HEADERS,
                json=data
            )
            if create_resp.status_code in [200, 201, 204]:
                saved += 1
                log.info(f"[{date}] Criado novo com revenue: ${float(row[1]):.2f}")
            else:
                log.error(f"[{date}] Erro ao criar: {create_resp.status_code} - {create_resp.text[:200]}")
        else:
            log.error(f"[{date}] Erro ao atualizar: {update_resp.status_code} - {update_resp.text[:500]}")

    return saved

def save_country_metrics(channel_id, rows, date):
    """Salva metricas por pais no Supabase"""
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
    """Salva metricas por video no Supabase (tabela atual - valores totais)"""
    saved = 0
    for row in rows:
        # Extrair métricas de retenção se existirem
        avg_duration = float(row[6]) if len(row) > 6 else 0
        avg_percentage = float(row[7]) if len(row) > 7 else 0
        ctr = float(row[8]) if len(row) > 8 else 0
        title = row[9] if len(row) > 9 else ""

        data = {
            "channel_id": channel_id,
            "video_id": row[0],
            "revenue": float(row[1]),
            "views": int(row[2]),
            "likes": int(row[3]),
            "comments": int(row[4]),
            "subscribers_gained": int(row[5]),
            "average_view_duration": avg_duration,
            "average_view_percentage": avg_percentage,
            "card_click_rate": ctr,
            "title": title,
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
    """Salva historico diario por video no Supabase"""
    saved = 0
    for row in rows:
        # Extrair métricas de retenção se existirem
        avg_duration = float(row[6]) if len(row) > 6 else 0
        avg_percentage = float(row[7]) if len(row) > 7 else 0
        ctr = float(row[8]) if len(row) > 8 else 0
        title = row[9] if len(row) > 9 else ""

        data = {
            "channel_id": channel_id,
            "video_id": row[0],
            "date": date,
            "revenue": float(row[1]),
            "views": int(row[2]),
            "likes": int(row[3]),
            "comments": int(row[4]),
            "subscribers_gained": int(row[5]),
            "average_view_duration": avg_duration,
            "average_view_percentage": avg_percentage,
            "card_click_rate": ctr,
            "title": title
        }

        resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/yt_video_daily",
            headers=SUPABASE_HEADERS,
            json=data
        )
        if resp.status_code in [200, 201, 204]:
            saved += 1

    return saved

def update_channel_info(channel_id, access_token):
    """Atualiza info do canal (inscritos, videos)"""
    headers = {"Authorization": f"Bearer {access_token}"}

    resp = requests.get(
        "https://www.googleapis.com/youtube/v3/channels",
        params={"part": "statistics", "id": channel_id},
        headers=headers
    )

    if resp.status_code == 200:
        items = resp.json().get("items", [])
        if items:
            stats = items[0]["statistics"]
            requests.patch(
                f"{SUPABASE_URL}/rest/v1/yt_channels",
                params={"channel_id": f"eq.{channel_id}"},
                headers=SUPABASE_HEADERS,
                json={
                    "total_subscribers": int(stats.get("subscriberCount", 0)),
                    "total_videos": int(stats.get("videoCount", 0)),
                    "updated_at": datetime.now().isoformat()
                }
            )

# =============================================================================
# MAIN
# =============================================================================

def main():
    log.info("=" * 60)
    log.info("INICIANDO COLETA DIARIA")
    log.info("=" * 60)

    # Datas - Ajustado para delay do YouTube (2-3 dias)
    # YouTube tem delay de 2-3 dias, então pedimos dados até 3 dias atrás
    end_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")

    # Buscar canais
    channels = get_channels()
    log.info(f"Canais encontrados: {len(channels)}")

    for channel in channels:
        channel_id = channel["channel_id"]
        channel_name = channel.get("channel_name", channel_id)
        proxy_name = channel.get("proxy_name", "C000.1")

        log.info(f"\n[{channel_name}] Iniciando coleta... (proxy: {proxy_name})")

        # Buscar credenciais do proxy
        credentials = get_proxy_credentials(proxy_name)
        if not credentials:
            log.error(f"[{channel_name}] Credenciais do proxy {proxy_name} nao encontradas!")
            log_collection(channel_id, "error", f"Credenciais proxy {proxy_name} nao encontradas")
            continue

        # Buscar tokens
        tokens = get_tokens(channel_id)
        if not tokens:
            log.error(f"[{channel_name}] Sem tokens cadastrados!")
            log_collection(channel_id, "error", "Tokens nao encontrados")
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
            continue

        # Atualizar token no banco
        update_tokens(channel_id, access_token)

        try:
            # Coletar metricas diarias
            daily_rows = collect_daily_metrics(channel_id, access_token, start_date, end_date)
            saved_daily = save_daily_metrics(channel_id, daily_rows)
            log.info(f"[{channel_name}] Metricas diarias: {saved_daily} dias salvos")

            # Coletar metricas por pais (apenas do dia anterior)
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            country_rows = collect_country_metrics(channel_id, access_token, yesterday, yesterday)
            saved_country = save_country_metrics(channel_id, country_rows, yesterday)
            log.info(f"[{channel_name}] Metricas por pais: {saved_country} paises salvos")

            # Coletar metricas por video
            video_rows = collect_video_metrics(channel_id, access_token, start_date, end_date)
            saved_video = save_video_metrics(channel_id, video_rows)
            log.info(f"[{channel_name}] Metricas por video: {saved_video} videos salvos")

            # Salvar historico diario por video (snapshot de hoje)
            today = datetime.now().strftime("%Y-%m-%d")
            saved_video_daily = save_video_daily(channel_id, video_rows, today)
            log.info(f"[{channel_name}] Historico diario videos: {saved_video_daily} registros")

            # Atualizar info do canal
            update_channel_info(channel_id, access_token)

            # Log de sucesso
            log_collection(channel_id, "success", f"Coletados {saved_daily} dias, {saved_country} paises, {saved_video} videos, {saved_video_daily} hist")

        except Exception as e:
            log.error(f"[{channel_name}] Erro: {str(e)}")
            log_collection(channel_id, "error", str(e)[:200])

    log.info("\n" + "=" * 60)
    log.info("COLETA FINALIZADA")
    log.info("=" * 60)

if __name__ == "__main__":
    main()

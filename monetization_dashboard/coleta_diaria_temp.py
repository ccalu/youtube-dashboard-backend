"""
Coleta Diaria de Metricas do YouTube - VERSÃO TEMPORÁRIA
Funciona SEM as colunas de retenção no banco
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
    """Coleta metricas diarias do canal - COM RETENÇÃO"""
    headers = {"Authorization": f"Bearer {access_token}"}

    resp = requests.get(
        "https://youtubeanalytics.googleapis.com/v2/reports",
        params={
            "ids": f"channel=={channel_id}",
            "startDate": start_date,
            "endDate": end_date,
            "metrics": "estimatedRevenue,views,likes,comments,shares,subscribersGained,subscribersLost,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,cardClickRate",
            "dimensions": "day",
            "sort": "day"
        },
        headers=headers
    )

    if resp.status_code != 200:
        log.error(f"Erro metricas diarias: {resp.status_code} - {resp.text[:200]}")
        return []

    return resp.json().get("rows", [])

def collect_video_metrics(channel_id, access_token, start_date, end_date):
    """Coleta metricas por video - COM RETENÇÃO"""
    headers = {"Authorization": f"Bearer {access_token}"}

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
# SALVAR DADOS - SEM CAMPOS DE RETENÇÃO POR ENQUANTO
# =============================================================================

def save_daily_metrics(channel_id, rows):
    """Salva metricas diarias no Supabase - SEM RETENÇÃO"""
    saved = 0
    retention_data = []  # Guardar para depois

    for row in rows:
        date = row[0]

        # Extrair métricas de retenção (mas não salvar ainda)
        if len(row) > 9:
            avg_duration = float(row[9]) if row[9] else 0
            avg_percentage = float(row[10]) if len(row) > 10 and row[10] else 0
            ctr = float(row[11]) if len(row) > 11 and row[11] else 0

            retention_data.append({
                "date": date,
                "avg_duration": avg_duration,
                "avg_percentage": avg_percentage,
                "ctr": ctr
            })

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
            "is_estimate": False
        }

        # Usar PATCH para atualizar registros existentes
        update_resp = requests.patch(
            f"{SUPABASE_URL}/rest/v1/yt_daily_metrics",
            params={"channel_id": f"eq.{channel_id}", "date": f"eq.{date}"},
            headers=SUPABASE_HEADERS,
            json=data
        )

        if update_resp.status_code in [200, 204]:
            saved += 1
            log.info(f"[{date}] Atualizado com revenue: ${float(row[1]):.2f}")
        elif update_resp.status_code == 404:
            # Se não existir, criar novo
            create_resp = requests.post(
                f"{SUPABASE_URL}/rest/v1/yt_daily_metrics",
                headers=SUPABASE_HEADERS,
                json=data
            )
            if create_resp.status_code in [200, 201, 204]:
                saved += 1
                log.info(f"[{date}] Criado com revenue: ${float(row[1]):.2f}")
            else:
                log.error(f"[{date}] Erro ao criar: {create_resp.status_code}")
        else:
            log.error(f"[{date}] Erro ao atualizar: {update_resp.status_code}")

    # Log das métricas de retenção coletadas (para verificação)
    if retention_data:
        sample = retention_data[-1]  # Último dia
        log.info(f"RETENÇÃO COLETADA (mas não salva ainda): {sample['avg_percentage']:.1f}% | CTR: {sample['ctr']:.2f}%")

    return saved

def save_video_metrics(channel_id, rows):
    """Salva metricas por video no Supabase - SEM RETENÇÃO"""
    saved = 0
    for row in rows:
        # Extrair título (último elemento)
        title = row[-1] if isinstance(row[-1], str) else ""

        data = {
            "channel_id": channel_id,
            "video_id": row[0],
            "revenue": float(row[1]),
            "views": int(row[2]),
            "likes": int(row[3]),
            "comments": int(row[4]),
            "subscribers_gained": int(row[5]),
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

def update_channel_info(channel_id, access_token):
    """Atualiza info do canal"""
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
    log.info("COLETA DIARIA (TEMPORARIA - SEM RETENCAO NO BANCO)")
    log.info("=" * 60)

    # Datas - Últimos 90 dias
    end_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    start_date = "2025-09-01"  # Início dos canais

    log.info(f"Periodo: {start_date} ate {end_date}")

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

        # Renovar access_token
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

            # Coletar metricas por video
            video_rows = collect_video_metrics(channel_id, access_token, start_date, end_date)
            saved_video = save_video_metrics(channel_id, video_rows)
            log.info(f"[{channel_name}] Metricas por video: {saved_video} videos salvos")

            # Atualizar info do canal
            update_channel_info(channel_id, access_token)

            # Log de sucesso
            log_collection(channel_id, "success", f"Coletados {saved_daily} dias, {saved_video} videos")

        except Exception as e:
            log.error(f"[{channel_name}] Erro: {str(e)}")
            log_collection(channel_id, "error", str(e)[:200])

    log.info("\n" + "=" * 60)
    log.info("COLETA FINALIZADA")
    log.info("NOTA: Retencao/CTR coletados mas NAO salvos (colunas pendentes)")
    log.info("=" * 60)

if __name__ == "__main__":
    main()
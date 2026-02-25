"""
CTR Collector via YouTube Reporting API
========================================
Coleta Impressions e CTR (Click-Through Rate) por video
usando a YouTube Reporting API (channel_reach_basic_a1).

Diferente do Analytics API, o Reporting API funciona assim:
1. Criar um "job" por canal (unica vez)
2. Google gera 1 CSV por dia automaticamente
3. Baixar CSVs novos e parsear
4. Agregar: soma impressoes + CTR medio ponderado por video
5. Salvar em yt_video_metrics (mesma tabela de retencao/views)

Requer:
- YouTube Reporting API ativada no Google Cloud Console
- Scope: yt-analytics.readonly (ja configurado nos canais OAuth)

Frequencia: Semanal (domingo 6AM Sao Paulo)
"""
import os
import sys
import csv
import io
import gzip
import requests
import logging
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

# Fix encoding for Windows (local testing)
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configurar logging
log_dir = os.getenv('LOG_DIR', './logs')
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(f'{log_dir}/ctr_collector.log'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# =============================================================================
# CONFIGURACOES
# =============================================================================
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://prvkmzstyedepvlbppyo.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

# Usar service_role_key para acessar tabelas OAuth protegidas com RLS
AUTH_KEY = SUPABASE_SERVICE_ROLE_KEY if SUPABASE_SERVICE_ROLE_KEY else SUPABASE_KEY

SUPABASE_HEADERS = {
    "apikey": AUTH_KEY,
    "Authorization": f"Bearer {AUTH_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates,return=minimal"
}

REPORTING_API_BASE = "https://youtubereporting.googleapis.com/v1"
REPORT_TYPE = "channel_reach_basic_a1"


# =============================================================================
# FUNCOES AUXILIARES - OAUTH (reutiliza padrao do monetization_oauth_collector)
# =============================================================================

def get_channels_with_oauth():
    """Busca canais ATIVOS com tokens OAuth."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/yt_oauth_tokens",
        params={"select": "channel_id"},
        headers={"apikey": AUTH_KEY, "Authorization": f"Bearer {AUTH_KEY}"}
    )
    if resp.status_code != 200 or not resp.json():
        log.error(f"Erro ao buscar tokens OAuth: {resp.text if resp.status_code != 200 else 'nenhum token'}")
        return []

    channel_ids = list(set(t["channel_id"] for t in resp.json() if t.get("channel_id")))
    if not channel_ids:
        return []

    ids_str = ",".join(channel_ids)
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/yt_channels",
        params={
            "channel_id": f"in.({ids_str})",
            "is_active": "eq.true",
            "select": "channel_id,channel_name,proxy_name"
        },
        headers={"apikey": AUTH_KEY, "Authorization": f"Bearer {AUTH_KEY}"}
    )
    if resp.status_code == 200:
        channels = resp.json()
        log.info(f"Canais ativos com OAuth: {len(channels)}")
        return channels
    log.error(f"Erro ao buscar canais: {resp.text}")
    return []


def get_tokens(channel_id):
    """Busca tokens OAuth de um canal."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/yt_oauth_tokens",
        params={"channel_id": f"eq.{channel_id}"},
        headers={"apikey": AUTH_KEY, "Authorization": f"Bearer {AUTH_KEY}"}
    )
    if resp.status_code == 200 and resp.json():
        return resp.json()[0]
    return None


def get_credentials(channel_id, proxy_name):
    """Busca credenciais OAuth (proxy ou isoladas)."""
    if proxy_name:
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/yt_proxy_credentials",
            params={"proxy_name": f"eq.{proxy_name}"},
            headers={"apikey": AUTH_KEY, "Authorization": f"Bearer {AUTH_KEY}"}
        )
    else:
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/yt_channel_credentials",
            params={"channel_id": f"eq.{channel_id}"},
            headers={"apikey": AUTH_KEY, "Authorization": f"Bearer {AUTH_KEY}"}
        )
    if resp.status_code == 200 and resp.json():
        return resp.json()[0]
    return None


def refresh_access_token(refresh_token, client_id, client_secret):
    """Renova o access_token usando o refresh_token."""
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
    """Atualiza access_token no Supabase."""
    requests.patch(
        f"{SUPABASE_URL}/rest/v1/yt_oauth_tokens",
        params={"channel_id": f"eq.{channel_id}"},
        headers=SUPABASE_HEADERS,
        json={"access_token": access_token}
    )


# =============================================================================
# FUNCOES - REPORTING JOBS (yt_reporting_jobs)
# =============================================================================

def get_reporting_job(channel_id):
    """Busca job existente do canal no banco."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/yt_reporting_jobs",
        params={
            "channel_id": f"eq.{channel_id}",
            "report_type": f"eq.{REPORT_TYPE}",
            "select": "*"
        },
        headers={"apikey": AUTH_KEY, "Authorization": f"Bearer {AUTH_KEY}"}
    )
    if resp.status_code == 200 and resp.json():
        return resp.json()[0]
    return None


def save_reporting_job(channel_id, job_id, status="active", error_message=None):
    """Salva ou atualiza job no banco. Tenta INSERT, se ja existe faz PATCH."""
    data = {
        "channel_id": channel_id,
        "job_id": job_id,
        "report_type": REPORT_TYPE,
        "status": status,
        "error_message": error_message,
        "updated_at": datetime.now().isoformat()
    }
    # Tentar INSERT primeiro
    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/yt_reporting_jobs",
        headers=SUPABASE_HEADERS,
        json=data
    )
    if resp.status_code in [200, 201, 204]:
        return True

    # Se conflito (ja existe), fazer PATCH
    if resp.status_code == 409:
        update_data = {
            "job_id": job_id,
            "status": status,
            "error_message": error_message,
            "updated_at": datetime.now().isoformat()
        }
        resp2 = requests.patch(
            f"{SUPABASE_URL}/rest/v1/yt_reporting_jobs",
            params={
                "channel_id": f"eq.{channel_id}",
                "report_type": f"eq.{REPORT_TYPE}"
            },
            headers=SUPABASE_HEADERS,
            json=update_data
        )
        return resp2.status_code in [200, 201, 204]

    return False


def update_reporting_job(channel_id, last_report_date=None, last_report_id=None,
                         status=None, error_message=None):
    """Atualiza campos de um job existente."""
    data = {"updated_at": datetime.now().isoformat()}
    if last_report_date:
        data["last_report_date"] = last_report_date
    if last_report_id:
        data["last_report_id"] = last_report_id
    if status:
        data["status"] = status
    if error_message is not None:
        data["error_message"] = error_message

    requests.patch(
        f"{SUPABASE_URL}/rest/v1/yt_reporting_jobs",
        params={
            "channel_id": f"eq.{channel_id}",
            "report_type": f"eq.{REPORT_TYPE}"
        },
        headers=SUPABASE_HEADERS,
        json=data
    )


# =============================================================================
# FUNCOES - YOUTUBE REPORTING API
# =============================================================================

def create_reporting_job(access_token):
    """Cria um job no YouTube Reporting API."""
    resp = requests.post(
        f"{REPORTING_API_BASE}/jobs",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        json={
            "reportTypeId": REPORT_TYPE,
            "name": f"CTR Collector - {REPORT_TYPE}"
        }
    )
    if resp.status_code in [200, 201]:
        job = resp.json()
        return job.get("id")
    else:
        error_text = resp.text[:300]
        log.error(f"Erro ao criar job: {resp.status_code} - {error_text}")
        return None


def list_existing_jobs(access_token):
    """Lista jobs existentes no YouTube Reporting API para este canal."""
    resp = requests.get(
        f"{REPORTING_API_BASE}/jobs",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    if resp.status_code == 200:
        jobs = resp.json().get("jobs", [])
        # Filtrar pelo tipo de report que queremos
        return [j for j in jobs if j.get("reportTypeId") == REPORT_TYPE]
    log.error(f"Erro ao listar jobs: {resp.status_code} - {resp.text[:200]}")
    return []


def get_or_create_job(channel_id, access_token):
    """
    Garante que o canal tem um job ativo.
    1. Verifica no banco (yt_reporting_jobs)
    2. Se nao tem, verifica na API do Google (pode ja existir)
    3. Se nao existe em lugar nenhum, cria novo
    Retorna job_id ou None.
    """
    # 1. Verificar no banco
    db_job = get_reporting_job(channel_id)
    if db_job and db_job.get("status") == "active" and db_job.get("job_id"):
        return db_job["job_id"]

    # 2. Verificar na API do Google (pode ter sido criado antes)
    existing_jobs = list_existing_jobs(access_token)
    if existing_jobs:
        job_id = existing_jobs[0]["id"]
        log.info(f"  Job encontrado no Google: {job_id}")
        save_reporting_job(channel_id, job_id, status="active")
        return job_id

    # 3. Criar novo job
    log.info(f"  Criando novo job no Google...")
    job_id = create_reporting_job(access_token)
    if job_id:
        log.info(f"  Job criado: {job_id}")
        save_reporting_job(channel_id, job_id, status="active")
        return job_id
    else:
        save_reporting_job(channel_id, None, status="error",
                          error_message="Falha ao criar job - verificar se YouTube Reporting API esta ativada")
        return None


def list_available_reports(job_id, access_token, since_date=None):
    """
    Lista relatorios disponiveis para um job.
    Retorna lista de {id, downloadUrl, startTime, endTime}.
    """
    params = {}
    if since_date:
        # createdAfter filtra reports criados depois dessa data (ISO 8601)
        params["createdAfter"] = f"{since_date}T00:00:00Z"

    resp = requests.get(
        f"{REPORTING_API_BASE}/jobs/{job_id}/reports",
        params=params,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    if resp.status_code != 200:
        log.error(f"Erro ao listar reports: {resp.status_code} - {resp.text[:200]}")
        return []

    reports = resp.json().get("reports", [])
    result = []
    for r in reports:
        result.append({
            "id": r.get("id"),
            "downloadUrl": r.get("downloadUrl"),
            "startTime": r.get("startTime", ""),
            "endTime": r.get("endTime", ""),
            "createTime": r.get("createTime", "")
        })

    # Ordenar por startTime (mais antigo primeiro)
    result.sort(key=lambda x: x["startTime"])
    return result


def download_and_parse_csv(download_url, access_token):
    """
    Baixa um CSV do Reporting API e parseia.
    Retorna lista de dicts: {video_id, impressions, ctr}
    """
    resp = requests.get(
        download_url,
        headers={"Authorization": f"Bearer {access_token}"},
        stream=True
    )
    if resp.status_code != 200:
        log.error(f"Erro ao baixar CSV: {resp.status_code}")
        return []

    # Descomprimir se gzip
    content = resp.content
    if resp.headers.get("Content-Encoding") == "gzip" or download_url.endswith(".gz"):
        try:
            content = gzip.decompress(content)
        except Exception:
            pass  # Ja esta descomprimido

    # Decodificar e parsear CSV
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for row in reader:
        video_id = row.get("video_id", "")
        if not video_id:
            continue

        try:
            impressions = int(row.get("video_thumbnail_impressions", 0))
            ctr = float(row.get("video_thumbnail_impressions_ctr", 0))
        except (ValueError, TypeError):
            continue

        rows.append({
            "video_id": video_id,
            "impressions": impressions,
            "ctr": ctr
        })

    return rows


# =============================================================================
# FUNCOES - AGREGACAO E SALVAMENTO
# =============================================================================

def aggregate_weekly_data(all_rows):
    """
    Agrega dados de multiplos CSVs diarios por video_id.
    - Soma impressoes
    - Calcula CTR medio ponderado: total_cliques / total_impressoes
    Retorna dict: {video_id: {impressions: N, ctr: F}}
    """
    video_data = defaultdict(lambda: {"total_impressions": 0, "total_clicks": 0})

    for row in all_rows:
        vid = row["video_id"]
        imp = row["impressions"]
        ctr = row["ctr"]
        # Calcular cliques a partir de impressoes * CTR
        clicks = imp * ctr

        video_data[vid]["total_impressions"] += imp
        video_data[vid]["total_clicks"] += clicks

    # Calcular CTR medio ponderado
    result = {}
    for vid, data in video_data.items():
        total_imp = data["total_impressions"]
        total_clicks = data["total_clicks"]
        weighted_ctr = (total_clicks / total_imp) if total_imp > 0 else 0

        result[vid] = {
            "impressions": total_imp,
            "ctr": round(weighted_ctr, 6)
        }

    return result


def save_ctr_data(channel_id, aggregated_data):
    """
    Atualiza impressions + ctr em yt_video_metrics (APENAS PATCH, nunca INSERT).
    So atualiza videos que JA EXISTEM na tabela (coletados pelo collector diario).
    Videos desconhecidos sao ignorados para nao poluir a tabela.
    """
    saved = 0
    skipped = 0
    read_headers = {"apikey": AUTH_KEY, "Authorization": f"Bearer {AUTH_KEY}"}

    for video_id, data in aggregated_data.items():
        # Verificar se video ja existe na tabela
        check = requests.get(
            f"{SUPABASE_URL}/rest/v1/yt_video_metrics",
            params={
                "channel_id": f"eq.{channel_id}",
                "video_id": f"eq.{video_id}",
                "select": "id"
            },
            headers=read_headers
        )

        if check.status_code == 200 and check.json():
            # Video existe → PATCH (so impressions + ctr, NUNCA sobrescreve outros campos)
            resp = requests.patch(
                f"{SUPABASE_URL}/rest/v1/yt_video_metrics",
                params={
                    "channel_id": f"eq.{channel_id}",
                    "video_id": f"eq.{video_id}"
                },
                headers=SUPABASE_HEADERS,
                json={
                    "impressions": data["impressions"],
                    "ctr": data["ctr"],
                    "updated_at": datetime.now().isoformat()
                }
            )
            if resp.status_code in [200, 204]:
                saved += 1
        else:
            skipped += 1

    if skipped > 0:
        log.info(f"  {skipped} videos do CSV ignorados (nao existem em yt_video_metrics)")

    return saved


def save_channel_avg_ctr(channel_id, aggregated_data):
    """
    Calcula e salva CTR medio ponderado do canal em yt_channels.
    CTR canal = total_cliques / total_impressoes (de todos os videos).
    """
    total_impressions = sum(d["impressions"] for d in aggregated_data.values())
    total_clicks = sum(d["impressions"] * d["ctr"] for d in aggregated_data.values())
    avg_ctr = round(total_clicks / total_impressions, 6) if total_impressions > 0 else 0

    resp = requests.patch(
        f"{SUPABASE_URL}/rest/v1/yt_channels",
        params={"channel_id": f"eq.{channel_id}"},
        headers=SUPABASE_HEADERS,
        json={
            "avg_ctr": avg_ctr,
            "total_impressions": total_impressions
        }
    )
    if resp.status_code in [200, 204]:
        log.info(f"  CTR medio do canal: {avg_ctr*100:.2f}% ({total_impressions:,} impressoes)")
    else:
        log.warning(f"  Erro ao salvar CTR medio do canal: {resp.status_code}")


# =============================================================================
# FUNCOES PRINCIPAIS
# =============================================================================

async def setup_all_jobs():
    """
    Setup inicial: cria reporting jobs para todos os canais com OAuth.
    Chamar uma vez via POST /api/ctr/setup-jobs.
    """
    log.info("=" * 60)
    log.info("CTR SETUP: Criando reporting jobs para todos os canais")
    log.info("=" * 60)

    channels = get_channels_with_oauth()
    if not channels:
        return {"error": "Nenhum canal com OAuth encontrado", "success": 0, "errors": 0}

    results = []
    success = 0
    errors = 0

    for channel in channels:
        channel_id = channel["channel_id"]
        channel_name = channel.get("channel_name", channel_id)
        proxy_name = channel.get("proxy_name")

        log.info(f"\n[{channel_name}] Configurando job...")

        # Obter token
        tokens = get_tokens(channel_id)
        if not tokens:
            log.error(f"[{channel_name}] Sem tokens OAuth")
            results.append({"channel": channel_name, "status": "error", "message": "Sem tokens"})
            errors += 1
            continue

        credentials = get_credentials(channel_id, proxy_name)
        if not credentials:
            log.error(f"[{channel_name}] Sem credenciais")
            results.append({"channel": channel_name, "status": "error", "message": "Sem credenciais"})
            errors += 1
            continue

        access_token = refresh_access_token(
            tokens["refresh_token"],
            credentials["client_id"],
            credentials["client_secret"]
        )
        if not access_token:
            log.error(f"[{channel_name}] Falha ao renovar token")
            results.append({"channel": channel_name, "status": "error", "message": "Token refresh failed"})
            errors += 1
            continue

        update_tokens(channel_id, access_token)

        # Criar/encontrar job
        job_id = get_or_create_job(channel_id, access_token)
        if job_id:
            log.info(f"[{channel_name}] Job ativo: {job_id}")
            results.append({"channel": channel_name, "status": "active", "job_id": job_id})
            success += 1
        else:
            results.append({"channel": channel_name, "status": "error",
                           "message": "Falha ao criar job - ativar YouTube Reporting API no Console"})
            errors += 1

    log.info(f"\nSETUP CONCLUIDO: {success} sucesso, {errors} erros")
    return {
        "success": success,
        "errors": errors,
        "total": len(channels),
        "details": results,
        "message": "Jobs criados. Primeiros CSVs disponiveis em ~48h. Google gera retroativo ate 60 dias."
    }


async def collect_ctr_reports():
    """
    Coleta principal: baixa CSVs novos de todos os canais e salva no Supabase.
    Roda semanalmente (domingo 6AM) ou via POST /api/ctr/collect.
    """
    log.info("=" * 60)
    log.info("CTR COLLECTION: Baixando relatorios de impressoes/CTR")
    log.info("=" * 60)

    channels = get_channels_with_oauth()
    if not channels:
        return {"error": "Nenhum canal com OAuth", "success": 0, "errors": 0, "total_records": 0}

    success_count = 0
    error_count = 0
    total_records = 0
    skipped_count = 0

    for channel in channels:
        channel_id = channel["channel_id"]
        channel_name = channel.get("channel_name", channel_id)
        proxy_name = channel.get("proxy_name")

        try:
            # Obter token
            tokens = get_tokens(channel_id)
            if not tokens:
                log.warning(f"[{channel_name}] Sem tokens - pulando")
                error_count += 1
                continue

            credentials = get_credentials(channel_id, proxy_name)
            if not credentials:
                log.warning(f"[{channel_name}] Sem credenciais - pulando")
                error_count += 1
                continue

            access_token = refresh_access_token(
                tokens["refresh_token"],
                credentials["client_id"],
                credentials["client_secret"]
            )
            if not access_token:
                log.warning(f"[{channel_name}] Token refresh falhou - pulando")
                error_count += 1
                continue

            update_tokens(channel_id, access_token)

            # Auto-provisioning: criar job se nao existe
            job_id = get_or_create_job(channel_id, access_token)
            if not job_id:
                log.warning(f"[{channel_name}] Sem job ativo - pulando")
                error_count += 1
                continue

            # Determinar desde quando buscar reports
            db_job = get_reporting_job(channel_id)
            if db_job and db_job.get("last_report_date"):
                since_date = db_job["last_report_date"]
            else:
                # Primeira coleta: buscar ultimos 60 dias
                since_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")

            # Listar CSVs disponiveis
            reports = list_available_reports(job_id, access_token, since_date)
            if not reports:
                log.info(f"[{channel_name}] Nenhum relatorio novo")
                skipped_count += 1
                continue

            log.info(f"[{channel_name}] {len(reports)} relatorios novos para baixar")

            # Baixar e parsear todos os CSVs
            all_rows = []
            last_report_id = None
            last_report_date = None

            for report in reports:
                csv_rows = download_and_parse_csv(report["downloadUrl"], access_token)
                if csv_rows:
                    all_rows.extend(csv_rows)
                    last_report_id = report["id"]
                    # Extrair data do startTime (formato ISO 8601)
                    start_time = report.get("startTime", "")
                    if start_time:
                        last_report_date = start_time[:10]  # YYYY-MM-DD

            if not all_rows:
                log.info(f"[{channel_name}] CSVs vazios (sem dados de impressoes)")
                skipped_count += 1
                continue

            # Agregar dados semanais
            aggregated = aggregate_weekly_data(all_rows)
            log.info(f"[{channel_name}] {len(aggregated)} videos com dados de CTR")

            # Salvar CTR por video no Supabase
            saved = save_ctr_data(channel_id, aggregated)
            total_records += saved
            log.info(f"[{channel_name}] {saved} videos salvos em yt_video_metrics")

            # Salvar CTR medio do canal em yt_channels
            save_channel_avg_ctr(channel_id, aggregated)

            # Atualizar job com ultimo report processado
            if last_report_date and last_report_id:
                update_reporting_job(
                    channel_id,
                    last_report_date=last_report_date,
                    last_report_id=last_report_id,
                    error_message=""
                )

            success_count += 1

        except Exception as e:
            log.error(f"[{channel_name}] Erro: {e}")
            error_count += 1
            update_reporting_job(channel_id, error_message=str(e)[:500])

    log.info("=" * 60)
    log.info(f"CTR COLLECTION CONCLUIDA:")
    log.info(f"  Sucesso: {success_count}")
    log.info(f"  Erros: {error_count}")
    log.info(f"  Pulados (sem dados novos): {skipped_count}")
    log.info(f"  Total records salvos: {total_records}")
    log.info("=" * 60)

    return {
        "success": success_count,
        "errors": error_count,
        "skipped": skipped_count,
        "total_records": total_records,
        "total_channels": len(channels)
    }


async def get_all_jobs_status():
    """Retorna status de todos os reporting jobs."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/yt_reporting_jobs",
        params={
            "report_type": f"eq.{REPORT_TYPE}",
            "select": "channel_id,job_id,status,last_report_date,error_message,updated_at",
            "order": "updated_at.desc"
        },
        headers={"apikey": AUTH_KEY, "Authorization": f"Bearer {AUTH_KEY}"}
    )
    if resp.status_code != 200:
        return {"error": resp.text, "jobs": []}

    jobs = resp.json()

    # Enriquecer com nomes dos canais
    if jobs:
        channel_ids = ",".join(set(j["channel_id"] for j in jobs))
        resp2 = requests.get(
            f"{SUPABASE_URL}/rest/v1/yt_channels",
            params={
                "channel_id": f"in.({channel_ids})",
                "select": "channel_id,channel_name"
            },
            headers={"apikey": AUTH_KEY, "Authorization": f"Bearer {AUTH_KEY}"}
        )
        if resp2.status_code == 200:
            names = {c["channel_id"]: c["channel_name"] for c in resp2.json()}
            for j in jobs:
                j["channel_name"] = names.get(j["channel_id"], j["channel_id"])

    active = sum(1 for j in jobs if j.get("status") == "active")
    errors = sum(1 for j in jobs if j.get("status") == "error")

    return {
        "total": len(jobs),
        "active": active,
        "errors": errors,
        "jobs": jobs
    }


async def get_channel_ctr(channel_id, limit=50):
    """Retorna dados de CTR para videos de um canal + CTR medio do canal."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/yt_video_metrics",
        params={
            "channel_id": f"eq.{channel_id}",
            "ctr": "not.is.null",
            "select": "video_id,views,impressions,ctr,avg_retention_pct,updated_at",
            "order": "impressions.desc",
            "limit": str(limit)
        },
        headers={"apikey": AUTH_KEY, "Authorization": f"Bearer {AUTH_KEY}"}
    )
    if resp.status_code != 200:
        return {"error": resp.text, "videos": []}

    videos = resp.json()

    # Calcular CTR medio ponderado do canal (total_cliques / total_impressoes)
    total_impressions = sum(v.get("impressions", 0) or 0 for v in videos)
    total_clicks = sum((v.get("impressions", 0) or 0) * (v.get("ctr", 0) or 0) for v in videos)
    channel_avg_ctr = round(total_clicks / total_impressions, 6) if total_impressions > 0 else 0

    return {
        "channel_id": channel_id,
        "total_videos": len(videos),
        "channel_stats": {
            "total_impressions": total_impressions,
            "avg_ctr": channel_avg_ctr,
            "avg_ctr_percent": round(channel_avg_ctr * 100, 2)
        },
        "videos": videos
    }


# =============================================================================
# EXECUCAO STANDALONE (para testes locais)
# =============================================================================

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        result = asyncio.run(setup_all_jobs())
        print(f"\nResultado: {result}")
    else:
        result = asyncio.run(collect_ctr_reports())
        print(f"\nResultado: {result}")

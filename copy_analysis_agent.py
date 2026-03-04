"""
Agente de Analise de Estrutura de Copy - MVP
=============================================
Analisa qual estrutura de copy (A-G) performa melhor em cada canal,
usando retencao % como metrica primaria.

Fluxo:
1. Le planilha (Col A = estrutura, Col B = titulo)
2. Match titulos com videos no banco
3. Busca retencao via banco ou YouTube Analytics API
4. Agrupa por estrutura, calcula metricas
5. Classifica vs media do canal
6. Detecta anomalias
7. Compara com analise anterior
8. Gera relatorio formatado
9. Salva no banco (memoria acumulativa)
"""

import os
import re
import json
import logging
import statistics
import requests
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple, Any

logger = logging.getLogger(__name__)

# Supabase config (mesmo padrao de monetization_oauth_collector.py)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY", "")
SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

VALID_STRUCTURES = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
MIN_MATURITY_DAYS = 7
MIN_SAMPLE_SIZE = 3
CLASSIFICATION_MARGIN = 2.0  # ±2% para classificar ACIMA/MEDIA/ABAIXO
ANOMALY_VIEWS_MULTIPLIER = 5.0  # views > 5x media = anomalia
ANOMALY_RETENTION_DIFF = 15.0  # retencao difere >15% da media = anomalia

# Satisfacao (Call 2)
SATISFACTION_WEIGHT_SUB = 0.53  # Sub Ratio peso (sem sentimento)
SATISFACTION_WEIGHT_APPROVAL = 0.47  # Like Approval peso (sem sentimento)
ANOMALY_SATISFACTION_MULTIPLIER = 3.0  # metrica 3x+ acima/abaixo = anomalia


# =============================================================================
# ETAPA 1: LEITURA DA PLANILHA
# =============================================================================

def read_copy_structures(spreadsheet_id: str) -> List[Dict]:
    """
    Le a planilha de producao e extrai estrutura de copy + titulo.
    Col A = letra da estrutura (A-G)
    Col B = titulo do video

    Returns:
        Lista de {structure, title, row_number}
    """
    from _features.yt_uploader.sheets import get_sheets_client

    try:
        client = get_sheets_client()
        spreadsheet = client.open_by_key(spreadsheet_id)

        # Tenta 'Pagina1' ou 'Página1' (com/sem acento)
        worksheet = None
        for name in ['Página1', 'Pagina1', 'Sheet1', 'Planilha1']:
            try:
                worksheet = spreadsheet.worksheet(name)
                break
            except Exception:
                continue

        if not worksheet:
            # Fallback: usa a primeira aba
            worksheet = spreadsheet.sheet1
            logger.warning(f"Nenhuma aba padrao encontrada, usando primeira aba: {worksheet.title}")

        all_rows = worksheet.get_all_values()
        results = []

        for i, row in enumerate(all_rows):
            if i == 0:
                continue  # Pula header

            if len(row) < 2:
                continue

            structure = row[0].strip().upper() if row[0] else ""
            title = row[1].strip() if len(row) > 1 and row[1] else ""

            # Valida: Col A deve ser uma letra A-G
            if len(structure) == 1 and structure in VALID_STRUCTURES and title:
                results.append({
                    "structure": structure,
                    "title": title,
                    "row_number": i + 1  # 1-indexed
                })

        logger.info(f"Planilha {spreadsheet_id}: {len(results)} videos com estrutura de copy")
        return results

    except Exception as e:
        logger.error(f"Erro ao ler planilha {spreadsheet_id}: {e}")
        return []


# =============================================================================
# ETAPA 2: MATCHING VIDEOS
# =============================================================================

def _normalize_title(title: str) -> str:
    """Normaliza titulo para matching: lowercase, sem espacos extras, sem pontuacao"""
    t = title.lower().strip()
    t = re.sub(r'[^\w\s]', '', t)  # Remove pontuacao
    t = re.sub(r'\s+', ' ', t)  # Normaliza espacos
    return t


def _title_similarity(title_a: str, title_b: str) -> float:
    """
    Calcula similaridade entre dois titulos normalizados.
    Compara palavra por palavra NA MESMA ORDEM.
    Retorna 0.0 a 1.0 (1.0 = identico).
    """
    words_a = title_a.split()
    words_b = title_b.split()

    if not words_a or not words_b:
        return 0.0

    # Contar palavras que batem na mesma posicao (ordem importa)
    matches = 0
    max_len = max(len(words_a), len(words_b))
    min_len = min(len(words_a), len(words_b))

    for i in range(min_len):
        if words_a[i] == words_b[i]:
            matches += 1

    return matches / max_len if max_len > 0 else 0.0


def match_videos(channel_id: str, sheet_data: List[Dict]) -> List[Dict]:
    """
    Cruza titulos da planilha com videos do banco.
    Tenta match por:
    1. Titulo exato
    2. Titulo normalizado
    3. Upload historico (youtube_video_id + video_titulo)

    Returns:
        Lista de {structure, video_id, title, published_at, duration_sec, views}
    """
    if not sheet_data:
        return []

    # Buscar videos do canal em videos_historico (com paginacao)
    db_videos = _fetch_all_videos(channel_id)
    logger.info(f"Canal {channel_id}: {len(db_videos)} videos no banco")

    # Buscar upload historico (tem youtube_video_id + video_titulo)
    upload_videos = _fetch_upload_history(channel_id)
    logger.info(f"Canal {channel_id}: {len(upload_videos)} videos no historico de upload")

    # Construir mapas de lookup
    exact_map = {}  # titulo exato -> video data
    normalized_map = {}  # titulo normalizado -> video data

    for v in db_videos:
        titulo = v.get("titulo", "")
        if titulo:
            exact_map[titulo] = v
            normalized_map[_normalize_title(titulo)] = v

    # Adicionar uploads ao mapa (prioridade menor que videos_historico)
    for u in upload_videos:
        titulo = u.get("video_titulo", "")
        vid = u.get("youtube_video_id", "")
        norm = _normalize_title(titulo) if titulo else ""
        if titulo and vid and titulo not in exact_map and norm not in normalized_map:
            upload_data = {
                "video_id": vid,
                "titulo": titulo,
                "data_publicacao": u.get("created_at", ""),
                "duracao": None,
                "views_atuais": None
            }
            exact_map[titulo] = upload_data
            normalized_map[norm] = upload_data

    matched = []
    no_match = []

    for item in sheet_data:
        sheet_title = item["title"]
        structure = item["structure"]
        video_data = None

        # 1. Match exato
        if sheet_title in exact_map:
            video_data = exact_map[sheet_title]
        else:
            # 2. Match normalizado
            norm_title = _normalize_title(sheet_title)
            if norm_title in normalized_map:
                video_data = normalized_map[norm_title]
            else:
                # 3. Match por similaridade (90% minimo, mesma ordem de palavras)
                # Safety net para diferencas minimas que normalizar nao resolveu
                # 90% garante que nao confunde estruturas com titulos parecidos
                if norm_title and len(norm_title) >= 10:
                    best_score = 0.0
                    best_data = None
                    for db_title, db_data in exact_map.items():
                        score = _title_similarity(norm_title, _normalize_title(db_title))
                        if score >= 0.90 and score > best_score:
                            best_score = score
                            best_data = db_data
                    if best_data:
                        video_data = best_data
                        logger.debug(f"Match por similaridade ({best_score:.0%}): \"{sheet_title}\"")

        if video_data:
            published_at = video_data.get("data_publicacao")
            if isinstance(published_at, str) and published_at:
                try:
                    published_at = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    published_at = None

            matched.append({
                "structure": structure,
                "video_id": video_data.get("video_id", ""),
                "title": sheet_title,
                "published_at": published_at,
                "duration_sec": video_data.get("duracao"),
                "views": video_data.get("views_atuais")
            })
        else:
            no_match.append(sheet_title)

    if no_match:
        logger.warning(f"Canal {channel_id}: {len(no_match)} videos sem match: {no_match[:5]}")

    logger.info(f"Canal {channel_id}: {len(matched)} matched, {len(no_match)} sem match")
    return matched


def _fetch_all_videos(channel_id: str) -> List[Dict]:
    """Busca todos videos do canal em videos_historico (com paginacao Supabase)"""
    all_videos = []
    page_size = 1000
    offset = 0

    # Precisamos do video mais recente por video_id (evitar duplicatas de snapshots diarios)
    # Buscar video_ids distintos com dados mais recentes
    while True:
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/videos_historico",
            params={
                "canal_id": f"eq.{channel_id}",
                "select": "video_id,titulo,data_publicacao,duracao,views_atuais",
                "order": "data_coleta.desc",
                "limit": page_size,
                "offset": offset
            },
            headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        )

        if resp.status_code != 200:
            logger.error(f"Erro ao buscar videos: {resp.status_code} - {resp.text[:200]}")
            break

        rows = resp.json()
        if not rows:
            break

        all_videos.extend(rows)
        offset += page_size

        if len(rows) < page_size:
            break

    # Deduplicar: manter apenas o registro mais recente por video_id
    seen = {}
    for v in all_videos:
        vid = v.get("video_id")
        if vid and vid not in seen:
            seen[vid] = v
    return list(seen.values())


def _fetch_upload_history(channel_id: str) -> List[Dict]:
    """Busca historico de uploads do canal (tem youtube_video_id + titulo)"""
    all_uploads = []
    page_size = 1000
    offset = 0

    while True:
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/yt_canal_upload_historico",
            params={
                "channel_id": f"eq.{channel_id}",
                "select": "youtube_video_id,video_titulo,created_at",
                "status": "eq.sucesso",
                "youtube_video_id": "not.is.null",
                "order": "created_at.desc",
                "limit": page_size,
                "offset": offset
            },
            headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        )

        if resp.status_code != 200:
            logger.error(f"Erro ao buscar upload history: {resp.status_code}")
            break

        rows = resp.json()
        if not rows:
            break

        all_uploads.extend(rows)
        offset += page_size

        if len(rows) < page_size:
            break

    return all_uploads


# =============================================================================
# ETAPA 3: COLETA DE RETENCAO
# =============================================================================

def get_retention_data(channel_id: str, video_ids: List[str]) -> Dict[str, Dict]:
    """
    Busca retencao por video. Tenta banco primeiro (batch), depois API.

    Returns:
        {video_id: {retention_pct, watch_time_min, views, duration_sec}}
    """
    if not video_ids:
        return {}

    # 1. Buscar do banco em batch (yt_video_metrics)
    result = {}
    batch_size = 50  # Supabase suporta filtro in.() com muitos IDs

    for i in range(0, len(video_ids), batch_size):
        batch = video_ids[i:i + batch_size]
        ids_str = ",".join(batch)
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/yt_video_metrics",
            params={
                "channel_id": f"eq.{channel_id}",
                "video_id": f"in.({ids_str})",
                "avg_retention_pct": "not.is.null",
                "select": "video_id,avg_retention_pct,avg_view_duration,views",
                "order": "updated_at.desc"
            },
            headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        )

        if resp.status_code == 200 and resp.json():
            for row in resp.json():
                vid = row.get("video_id")
                if vid and vid not in result:  # Primeiro = mais recente (order desc)
                    avg_dur = row.get("avg_view_duration") or 0
                    result[vid] = {
                        "retention_pct": row.get("avg_retention_pct"),
                        "watch_time_min": round(avg_dur / 60, 2) if avg_dur else None,
                        "views": row.get("views")
                    }

    # 2. Videos sem retencao no banco → tentar API
    missing_ids = [vid for vid in video_ids if vid not in result]

    if missing_ids:
        logger.info(f"Canal {channel_id}: {len(missing_ids)} videos sem retencao no banco, tentando API...")
        api_data = _fetch_retention_from_api(channel_id, missing_ids)
        result.update(api_data)

    logger.info(f"Canal {channel_id}: retencao obtida para {len(result)}/{len(video_ids)} videos")
    return result


def _fetch_retention_from_api(channel_id: str, video_ids: List[str]) -> Dict[str, Dict]:
    """
    Busca retencao diretamente da YouTube Analytics API via OAuth.
    Mesmo padrao de monetization_oauth_collector.py.
    """
    result = {}

    # Buscar tokens OAuth
    tokens = _get_oauth_tokens(channel_id)
    if not tokens:
        logger.error(f"Canal {channel_id}: sem tokens OAuth, nao pode buscar retencao da API")
        return result

    # Buscar credenciais (isoladas ou proxy)
    credentials = _get_credentials(channel_id)
    if not credentials:
        logger.error(f"Canal {channel_id}: sem credenciais OAuth")
        return result

    # Renovar access_token
    access_token = _refresh_token(
        tokens["refresh_token"],
        credentials["client_id"],
        credentials["client_secret"]
    )
    if not access_token:
        logger.error(f"Canal {channel_id}: falha ao renovar token")
        return result

    # Query YouTube Analytics API (ultimos 365 dias para pegar todos videos)
    # Pagina de 200 em 200 para pegar TODOS (mesmo padrao do collector)
    end_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

    all_rows = []
    page_size = 200
    start_index = 1
    video_id_set = set(video_ids)

    while True:
        resp = requests.get(
            "https://youtubeanalytics.googleapis.com/v2/reports",
            params={
                "ids": f"channel=={channel_id}",
                "startDate": start_date,
                "endDate": end_date,
                "metrics": "averageViewDuration,averageViewPercentage,views,estimatedMinutesWatched",
                "dimensions": "video",
                "sort": "-views",
                "maxResults": str(page_size),
                "startIndex": str(start_index)
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if resp.status_code != 200:
            logger.error(f"YouTube Analytics API erro: {resp.status_code} - {resp.text[:200]}")
            break

        rows = resp.json().get("rows", [])
        if not rows:
            break

        all_rows.extend(rows)

        # Se ja encontrou todos os videos que faltavam, para
        found_so_far = sum(1 for r in all_rows if r[0] in video_id_set)
        if found_so_far >= len(video_ids):
            break

        if len(rows) < page_size:
            break

        start_index += page_size

    for row in all_rows:
        vid = row[0]
        if vid in video_id_set:
            avg_dur = float(row[1]) if len(row) > 1 and row[1] else 0
            result[vid] = {
                "retention_pct": float(row[2]) if len(row) > 2 and row[2] else None,
                "watch_time_min": round(avg_dur / 60, 2) if avg_dur else None,
                "views": int(row[3]) if len(row) > 3 and row[3] else None
            }

    logger.info(f"YouTube Analytics API: {len(result)} videos com retencao de {len(all_rows)} total")
    return result


def _get_oauth_tokens(channel_id: str) -> Optional[Dict]:
    """Busca tokens OAuth do canal"""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/yt_oauth_tokens",
        params={"channel_id": f"eq.{channel_id}", "select": "refresh_token,access_token"},
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    )
    if resp.status_code == 200 and resp.json():
        return resp.json()[0]
    return None


def _get_credentials(channel_id: str) -> Optional[Dict]:
    """Busca credenciais OAuth (isoladas primeiro, proxy como fallback)"""
    # Tenta credenciais isoladas
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/yt_channel_credentials",
        params={"channel_id": f"eq.{channel_id}", "select": "client_id,client_secret"},
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    )
    if resp.status_code == 200 and resp.json():
        return resp.json()[0]

    # Fallback: busca proxy_name do canal e depois credenciais do proxy
    resp2 = requests.get(
        f"{SUPABASE_URL}/rest/v1/yt_channels",
        params={"channel_id": f"eq.{channel_id}", "select": "proxy_name"},
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    )
    if resp2.status_code == 200 and resp2.json():
        proxy_name = resp2.json()[0].get("proxy_name")
        if proxy_name:
            resp3 = requests.get(
                f"{SUPABASE_URL}/rest/v1/yt_proxy_credentials",
                params={"proxy_name": f"eq.{proxy_name}", "select": "client_id,client_secret"},
                headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
            )
            if resp3.status_code == 200 and resp3.json():
                return resp3.json()[0]

    return None


def _refresh_token(refresh_token: str, client_id: str, client_secret: str) -> Optional[str]:
    """Renova access_token via OAuth refresh"""
    resp = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    })
    if resp.status_code == 200:
        return resp.json().get("access_token")
    logger.error(f"Erro refresh token: {resp.text[:200]}")
    return None


# =============================================================================
# ETAPA 4: ENGINE DE ANALISE
# =============================================================================

def analyze_copy_performance(
    matched_videos: List[Dict],
    retention_data: Dict[str, Dict]
) -> Dict:
    """
    Agrupa videos por estrutura, calcula metricas, classifica vs media do canal.

    Returns:
        {
            "channel_avg": {retention, watch_time, views},
            "structures": {A: {avg_retention, avg_watch_time, avg_views, ...}, ...},
            "insufficient": {G: {count, partial_retention}, ...},
            "anomalies": [{video_id, title, structure, reason, ...}, ...],
            "all_videos": [{video_id, structure, retention, ...}, ...]
        }
    """
    now = datetime.now(timezone.utc)

    # Combinar matched_videos com retention_data + filtro maturidade
    combined = []
    excluded_immature = 0

    for v in matched_videos:
        vid = v["video_id"]
        ret = retention_data.get(vid, {})

        # Filtro maturidade: 7+ dias
        if v.get("published_at"):
            pub_date = v["published_at"]
            if isinstance(pub_date, str):
                try:
                    pub_date = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    pub_date = None

            if pub_date and (now - pub_date).days < MIN_MATURITY_DAYS:
                excluded_immature += 1
                continue

        retention_pct = ret.get("retention_pct")
        if retention_pct is None:
            continue  # Sem dados de retencao, nao pode analisar

        combined.append({
            "video_id": vid,
            "structure": v["structure"],
            "title": v["title"],
            "retention_pct": retention_pct,
            "watch_time_min": ret.get("watch_time_min"),
            "views": ret.get("views") or v.get("views"),
            "duration_sec": v.get("duration_sec"),
            "published_at": v.get("published_at")
        })

    if not combined:
        return {
            "channel_avg": {"retention": 0, "watch_time": 0, "views": 0},
            "structures": {},
            "insufficient": {},
            "anomalies": [],
            "all_videos": [],
            "excluded_immature": excluded_immature
        }

    # Media geral do canal (todos videos analisados)
    all_retentions = [v["retention_pct"] for v in combined if v["retention_pct"]]
    all_watch_times = [v["watch_time_min"] for v in combined if v.get("watch_time_min")]
    all_views = [v["views"] for v in combined if v.get("views")]

    channel_avg = {
        "retention": round(statistics.mean(all_retentions), 2) if all_retentions else 0,
        "watch_time": round(statistics.mean(all_watch_times), 2) if all_watch_times else 0,
        "views": round(statistics.mean(all_views)) if all_views else 0
    }

    # Agrupar por estrutura
    groups = {}
    for v in combined:
        s = v["structure"]
        if s not in groups:
            groups[s] = []
        groups[s].append(v)

    structures = {}
    insufficient = {}
    anomalies = []

    for structure, videos in sorted(groups.items()):
        n = len(videos)
        retentions = [v["retention_pct"] for v in videos if v["retention_pct"]]
        watch_times = [v["watch_time_min"] for v in videos if v.get("watch_time_min")]
        views_list = [v["views"] for v in videos if v.get("views")]
        durations = [v["duration_sec"] for v in videos if v.get("duration_sec")]

        if n < MIN_SAMPLE_SIZE:
            # Dados insuficientes
            insufficient[structure] = {
                "count": n,
                "partial_retention": round(statistics.mean(retentions), 2) if retentions else None,
                "videos": [{"title": v["title"], "retention": v["retention_pct"]} for v in videos]
            }
            continue

        avg_ret = round(statistics.mean(retentions), 2) if retentions else 0
        avg_wt = round(statistics.mean(watch_times), 2) if watch_times else 0
        avg_views = round(statistics.mean(views_list)) if views_list else 0
        avg_dur = round(statistics.mean(durations)) if durations else 0
        std_ret = round(statistics.stdev(retentions), 2) if len(retentions) > 1 else 0

        # Classificacao vs media do canal
        diff = avg_ret - channel_avg["retention"]
        if diff > CLASSIFICATION_MARGIN:
            status = "ACIMA"
        elif diff < -CLASSIFICATION_MARGIN:
            status = "ABAIXO"
        else:
            status = "MEDIA"

        structures[structure] = {
            "avg_retention": avg_ret,
            "avg_watch_time": avg_wt,
            "avg_views": avg_views,
            "avg_duration": avg_dur,
            "std_retention": std_ret,
            "count": n,
            "status": status,
            "diff_from_avg": round(diff, 2),
            "videos": [{"title": v["title"], "video_id": v["video_id"],
                         "retention": v["retention_pct"], "views": v.get("views")}
                        for v in videos]
        }

        # Deteccao de anomalias
        for v in videos:
            reasons = []
            v_views = v.get("views") or 0
            v_ret = v.get("retention_pct") or 0

            if avg_views > 0 and v_views > avg_views * ANOMALY_VIEWS_MULTIPLIER:
                reasons.append(f"Views {v_views:,} = {v_views/avg_views:.1f}x acima da media da estrutura ({avg_views:,})")
            if avg_views > 0 and v_views < avg_views / ANOMALY_VIEWS_MULTIPLIER:
                reasons.append(f"Views {v_views:,} = {avg_views/max(v_views,1):.1f}x abaixo da media ({avg_views:,})")
            if abs(v_ret - avg_ret) > ANOMALY_RETENTION_DIFF:
                reasons.append(f"Retencao {v_ret:.1f}% vs {avg_ret:.1f}% media (diff {v_ret-avg_ret:+.1f}%)")

            if reasons:
                anomalies.append({
                    "video_id": v["video_id"],
                    "title": v["title"],
                    "structure": structure,
                    "retention": v_ret,
                    "views": v_views,
                    "published_at": v.get("published_at"),
                    "reasons": reasons
                })

    # Ordenar structures por retencao (ranking)
    sorted_structures = dict(sorted(
        structures.items(),
        key=lambda x: x[1]["avg_retention"],
        reverse=True
    ))

    return {
        "channel_avg": channel_avg,
        "structures": sorted_structures,
        "insufficient": insufficient,
        "anomalies": anomalies,
        "all_videos": combined,
        "excluded_immature": excluded_immature
    }


# =============================================================================
# ETAPA 5: COMPARACAO TEMPORAL
# =============================================================================

def compare_with_previous(channel_id: str, current_results: Dict) -> Optional[Dict]:
    """
    Busca a ultima analise do canal e compara.
    A ultima analise ja contem a memoria acumulada de todas as anteriores
    (cadeia: 2a se baseia na 1a, 3a se baseia na 2a que ja tem contexto da 1a, etc).

    Returns:
        {
            "previous_date": "...",
            "previous_avg": float,
            "previous_report": str,  # relatorio completo anterior (memoria acumulada)
            "changes": {A: {prev_retention, curr_retention, diff, rank_change}, ...},
            "new_structures": ["G"],
        }
    """
    # Buscar analise mais recente (que ja carrega toda a inteligencia acumulada)
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/copy_analysis_runs",
        params={
            "channel_id": f"eq.{channel_id}",
            "select": "run_date,results_json,channel_avg_retention,report_text",
            "order": "run_date.desc",
            "limit": "1"
        },
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    )

    if resp.status_code != 200 or not resp.json():
        return None  # Primeira analise, sem comparacao

    prev = resp.json()[0]
    prev_results = prev.get("results_json") or {}
    if isinstance(prev_results, str):
        prev_results = json.loads(prev_results)
    prev_structures = prev_results.get("structures", {})
    prev_date = prev.get("run_date", "")
    prev_report = prev.get("report_text", "")

    if not prev_structures:
        return None

    curr_structures = current_results.get("structures", {})

    # Gerar ranking anterior e atual
    prev_ranking = sorted(prev_structures.items(), key=lambda x: x[1].get("avg_retention", 0), reverse=True)
    curr_ranking = sorted(curr_structures.items(), key=lambda x: x[1].get("avg_retention", 0), reverse=True)

    prev_rank_map = {s: i+1 for i, (s, _) in enumerate(prev_ranking)}
    curr_rank_map = {s: i+1 for i, (s, _) in enumerate(curr_ranking)}

    changes = {}
    new_structures = []

    for structure, data in curr_structures.items():
        if structure in prev_structures:
            prev_ret = prev_structures[structure].get("avg_retention", 0)
            curr_ret = data["avg_retention"]
            prev_rank = prev_rank_map.get(structure, 0)
            curr_rank = curr_rank_map.get(structure, 0)

            changes[structure] = {
                "prev_retention": prev_ret,
                "curr_retention": curr_ret,
                "diff": round(curr_ret - prev_ret, 2),
                "prev_rank": prev_rank,
                "curr_rank": curr_rank,
                "rank_change": prev_rank - curr_rank  # positivo = subiu
            }
        else:
            new_structures.append(structure)

    return {
        "previous_date": prev_date,
        "previous_avg": prev.get("channel_avg_retention"),
        "previous_report": prev_report,
        "changes": changes,
        "new_structures": new_structures
    }


# =============================================================================
# ETAPA 5B: ANALISE INTELIGENTE (LLM)
# =============================================================================

def generate_llm_insights(
    channel_name: str,
    analysis: Dict,
    comparison: Optional[Dict]
) -> Optional[Dict]:
    """
    Envia dados brutos para GPT-4o-mini analisar.
    O GPT e o analista - recebe todos os dados video a video e gera
    a analise completa: padroes, anomalias, correlacoes, tendencias.

    Memoria acumulativa: recebe o relatorio anterior completo como contexto.
    Cada relatorio ja carrega as conclusoes de todos os anteriores,
    entao a LLM sempre tem a inteligencia acumulada para comparar.

    Returns:
        Texto com analise completa da LLM ou None se falhar
    """
    try:
        from openai import OpenAI

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY nao configurada - pulando analise LLM")
            return None

        client = OpenAI(api_key=api_key)
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

        # Montar dados BRUTOS video a video para o GPT analisar
        ch_avg = analysis["channel_avg"]
        structures = analysis["structures"]
        insufficient = analysis["insufficient"]
        all_videos = analysis.get("all_videos", [])

        data_block = f"CANAL: {channel_name}\n"
        data_block += f"Total videos analisados: {len(all_videos)}\n"
        data_block += f"Media geral do canal: {ch_avg['retention']:.1f}% retencao, {ch_avg['watch_time']:.1f} min watch time, {ch_avg['views']:,.0f} views\n\n"

        # Dados brutos por estrutura com cada video
        data_block += "DADOS POR ESTRUTURA (cada video individual):\n\n"
        for s, d in structures.items():
            data_block += f"Estrutura {s} ({d['count']} videos):\n"
            for v in d.get("videos", []):
                views_str = f"{v.get('views', 0):,}" if v.get('views') else "N/A"
                data_block += f"  - \"{v['title']}\" | ret: {v.get('retention', 0):.1f}% | views: {views_str}\n"
            data_block += f"  Media: {d['avg_retention']:.1f}% ret, {d['avg_watch_time']:.1f} min wt, {d['avg_views']:,.0f} views\n"
            data_block += f"  Desvio padrao retencao: {d['std_retention']:.1f}%\n\n"

        if insufficient:
            data_block += "ESTRUTURAS COM POUCOS DADOS (<3 videos):\n"
            for s, d in insufficient.items():
                data_block += f"  Estrutura {s}: {d['count']} video(s)"
                if d.get("partial_retention"):
                    data_block += f", retencao parcial: {d['partial_retention']:.1f}%"
                data_block += "\n"
                for v in d.get("videos", []):
                    data_block += f"    - \"{v['title']}\" | ret: {v.get('retention', 0):.1f}%\n"
            data_block += "\n"

        if comparison and comparison.get("changes"):
            prev_date = comparison.get("previous_date", "")
            if isinstance(prev_date, str) and "T" in prev_date:
                try:
                    prev_date = datetime.fromisoformat(prev_date.replace("Z", "+00:00")).strftime("%d/%m/%Y")
                except (ValueError, TypeError):
                    pass
            data_block += f"COMPARACAO COM ANALISE ANTERIOR ({prev_date}):\n"
            for s, c in comparison["changes"].items():
                rank_info = ""
                if c["rank_change"] > 0:
                    rank_info = f" (subiu no ranking: {c['prev_rank']}o->{c['curr_rank']}o)"
                elif c["rank_change"] < 0:
                    rank_info = f" (caiu no ranking: {c['prev_rank']}o->{c['curr_rank']}o)"
                data_block += f"  Estrutura {s}: {c['prev_retention']:.1f}% -> {c['curr_retention']:.1f}% ({c['diff']:+.1f}%){rank_info}\n"
            if comparison.get("new_structures"):
                data_block += f"  Novas no ranking: {', '.join(comparison['new_structures'])}\n"
            data_block += "\n"

        # =====================================================================
        # PROMPT LLM PROFISSIONAL — System + User messages separados
        # =====================================================================

        system_prompt = """Voce e um analista senior de performance de copywriting para canais YouTube.
Voce analisa dados PRE-CALCULADOS por um sistema Python e produz insights narrativos
que um humano usaria para tomar decisoes sobre producao de conteudo.

=== O QUE SAO ESTRUTURAS DE COPY ===

Cada video do canal usa uma ESTRUTURA NARRATIVA identificada por uma letra.
A estrutura define COMO a historia e contada — nao O QUE e contado.
Cada canal tem seu proprio conjunto de estruturas (letras). Nao existe um padrao
fixo — o que importa e comparar as estruturas DENTRO do mesmo canal.

Exemplo concreto:
Dois videos sobre "A Queda de Roma" podem usar estruturas narrativas diferentes:
- A (cronologica): conta do inicio ao fim, linear
- B (misterio): abre com pergunta intrigante, vai revelando aos poucos
- J (conflito): comeca pelo momento mais dramatico, depois contextualiza

O MESMO tema com estruturas diferentes gera retencoes DRASTICAMENTE diferentes.
Isso e o que estamos medindo: qual FORMA de contar a historia segura o espectador.

=== METRICA PRIMARIA: RETENCAO % ===

Retencao % e a metrica primaria porque copy/roteiro afeta DIRETAMENTE quanto tempo
o espectador assiste. CTR (taxa de clique) e afetado pelo titulo + thumbnail, NAO
pela copy — por isso NAO e metrica deste agente.

Retencao = indicador MAIS PURO da qualidade do roteiro.

=== COMO INTERPRETAR AS METRICAS ===

1. RETENCAO MEDIA POR ESTRUTURA
   - E a media de retencao % de todos os videos que usaram aquela estrutura
   - Comparada com a MEDIA GERAL DO CANAL (benchmark universal)
   - Diferenca positiva = estrutura performa acima do canal
   - Diferenca negativa = estrutura performa abaixo do canal

2. DESVIO PADRAO DA RETENCAO (informacao CRITICA)
   O desvio padrao revela se a estrutura e um fator DETERMINANTE ou nao:

   - Desvio BAIXO (<5%): estrutura CONSISTENTE
     > Os videos performam parecido INDEPENDENTE do tema
     > A forma narrativa e o fator dominante
     > Conclusao: a estrutura FUNCIONA de forma confiavel

   - Desvio MEDIO (5-10%): moderadamente variavel
     > Alguma influencia do tema, mas estrutura ainda e fator relevante

   - Desvio ALTO (>10%): estrutura VOLATIL
     > Performance varia DRASTICAMENTE entre videos
     > O TEMA escolhido importa MAIS que a forma de contar
     > Conclusao: a estrutura NAO e o fator determinante
     > Exemplo: retencao variando de 22% a 48% entre videos =
       quando acerta o tema vai muito bem, quando erra cai drasticamente

   INSIGHT CHAVE: Uma estrutura volatil com media ALTA nao e necessariamente boa.
   Significa que ALGUNS temas funcionam nela, mas outros nao. A consistencia e mais
   valiosa que a media bruta para decisoes de producao.

3. WATCH TIME (minutos) — CONTEXTO ESSENCIAL
   Watch time contextualiza retencao vs duracao do video:

   > Video de 8 min com 40% retencao = 3.2 min assistidos por viewer
   > Video de 18 min com 25% retencao = 4.5 min assistidos por viewer

   O segundo PARECE pior em retencao mas entrega 40% MAIS tempo assistido.
   Sempre analise retencao E watch time juntos. Retencao sozinha engana.

   QUANDO DESTACAR: Se uma estrutura tem retencao MENOR mas watch time MAIOR
   que outra (porque seus videos sao mais longos), isso e uma nuance critica.
   O canal pode estar subestimando uma estrutura que entrega mais sessao total.

4. VIEWS — ESCALA E ANOMALIAS
   Views indica alcance/interesse do publico. Use para:
   - Detectar anomalias: 1 video com views 5x+ acima da media da estrutura
   - Anomalias sao FATOS a reportar, nao explicar. Nao tente justificar por que
     um video viralizou — pode ser tema, thumbnail, timing, algoritmo. Nao sabemos.
   - Reporte como: "Video X tem YK views (Zx acima da media da estrutura)"

=== CLASSIFICACAO POR STATUS ===

Cada estrutura recebe um status baseado na media geral do canal:
- ACIMA: retencao da estrutura ACIMA da media geral
- MEDIA: retencao PROXIMA da media geral (margem pequena)
- ABAIXO: retencao ABAIXO da media geral

=== DISTRIBUICAO DA PRODUCAO ===

Analise quantos videos cada estrutura tem e qual % do total:
- Concentracao alta (poucas estruturas dominando): risco. Se uma cair, canal sofre
- Concentracao na MELHOR estrutura: menos grave (esta apostando no que funciona)
- Concentracao numa estrutura MEDIOCRE: desperdicio de producao

=== REGRAS INVIOLAVEIS ===

1. Seja FACTUAL — cite numeros EXATOS dos dados fornecidos
2. NAO invente dados — use APENAS o que esta nos dados
3. NAO de recomendacoes de acao — decisao e HUMANA. Voce apresenta PADROES
4. NAO tente explicar POR QUE um video viralizou ou flopou — so reporte o fato
5. NAO repita tabelas de ranking ou anomalias (o sistema ja gera automaticamente)
6. Anomalias: REPORTE como fato + flag. NAO explique a causa
7. Escreva em portugues, paragrafos curtos separados por linha em branco
8. Escreva o quanto for necessario. NAO resuma, NAO corte a analise
9. Use EXATAMENTE os marcadores [OBSERVACOES] e [TENDENCIAS]

=== TIPO DE RACIOCINIO ESPERADO ===

NAO FACA ISSO (superficial):
"A estrutura lider tem 42%. A pior tem 28%."

FACA ISSO (profissional):
"A estrutura lider tem 42.3% de retencao (+6.5pp acima da media do canal de 35.8%).
Com desvio padrao de apenas 3.1%, e a estrutura mais CONSISTENTE do canal — funciona
independente do tema. Seus 7 videos variam entre 39% e 46%, sem excecoes abaixo da media.

Em contraste, a segunda colocada tem media similar (38.1%) mas desvio de 12.4% — volatil.
Varia de 24% a 51% entre videos. Isso indica que essa abordagem narrativa nao e o
fator determinante: quando o TEMA se encaixa, vai muito bem. Quando nao, cai drasticamente.
A lider e mais confiavel para decisoes de producao, apesar da diferenca de media ser pequena."
"""

        # Montar bloco de memoria acumulativa (relatorio anterior)
        previous_report_block = ""
        if comparison and comparison.get("previous_report"):
            prev_date = comparison.get("previous_date", "")
            if isinstance(prev_date, str) and "T" in prev_date:
                try:
                    prev_date = datetime.fromisoformat(prev_date.replace("Z", "+00:00")).strftime("%d/%m/%Y")
                except (ValueError, TypeError):
                    pass
            previous_report_block = f"""
VOCE TEM MEMORIA ACUMULATIVA:
O relatorio anterior contem TODAS as conclusoes e tendencias identificadas ate agora.
Sua analise atual DEVE:
- Se basear no relatorio anterior como referencia
- Confirmar ou revisar tendencias anteriores com numeros
- Notar evolucoes (ex: "Estrutura X consolida lideranca pela 3a analise consecutiva")
- Construir em cima, nunca ignorar o historico

RELATORIO ANTERIOR COMPLETO ({prev_date}):
{comparison['previous_report']}
FIM DO RELATORIO ANTERIOR.
"""

        user_prompt = f"""{previous_report_block}

Produza EXATAMENTE 2 blocos:

[OBSERVACOES]
Analise DESTA SEMANA. Cubra obrigatoriamente TODOS os pontos abaixo, com dados:

1. LIDERANCA: Qual estrutura lidera? Com que margem (em pontos percentuais)
   sobre a media do canal? E consistente (desvio baixo) ou volatil?

2. CONSISTENCIA POR ESTRUTURA: Para CADA estrutura no ranking, cite o desvio
   padrao e interprete. Quais sao confiaveis (<5%)? Quais sao volateis (>10%)?
   Se uma volatil tem media alta, destaque que nao e necessariamente confiavel.

3. TEMA vs COPY: Se alguma estrutura tem desvio alto, identifique explicitamente:
   "A performance desta estrutura depende mais do TEMA escolhido do que da
   abordagem narrativa em si." Cite a faixa de retencao (min-max).

4. PIOR DESEMPENHO: Qual estrutura e consistentemente a pior? Com que margem
   abaixo da media? E consistentemente ruim (desvio baixo = problema da estrutura)
   ou inconsistente (desvio alto = depende do tema)?

5. DISTRIBUICAO DA PRODUCAO: Quantos videos cada estrutura tem e qual % do total.
   Ha concentracao excessiva? Se sim, a estrutura concentrada e a melhor ou mediocre?

6. ANOMALIAS: Se ha videos com views 5x+ acima da media da estrutura,
   reporte como fato com o multiplicador exato. Nao explique a causa.

7. WATCH TIME vs RETENCAO: Se alguma estrutura tem retencao MENOR mas watch time
   MAIOR que outra (videos mais longos), faca a conta explicita:
   "Estrutura X: 31% retencao em videos de 22 min = 6.8 min por viewer.
   Estrutura Y: 42% retencao em videos de 12 min = 5.0 min por viewer.
   Em tempo de sessao, X entrega 36% mais."

8. OUTROS PADROES: Qualquer insight relevante nos dados que nao se encaixe acima.

[TENDENCIAS]
EVOLUCAO ao longo do tempo (SO se houver relatorio anterior):
- Para cada estrutura, compare retencao atual vs anterior com numeros exatos
- Identifique movimentos no ranking (subiu, caiu, consolidou posicao)
- Padroes confirmados: "Estrutura X consolida lideranca pela Ya analise consecutiva"
- Padroes revertidos: "Estrutura Z reverteu queda; subiu de X% para Y%"
- Se primeira analise: "Primeira analise. Sem dados anteriores para comparacao."

DADOS DA SEMANA ATUAL:
{data_block}"""

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )

        llm_text = response.choices[0].message.content.strip()
        logger.info(f"LLM analise gerada ({response.usage.total_tokens} tokens)")

        # Split em 2 blocos: observacoes e tendencias
        result = {"observacoes": "", "tendencias": ""}

        if "[TENDENCIAS]" in llm_text:
            parts = llm_text.split("[TENDENCIAS]")
            obs_part = parts[0]
            tend_part = parts[1].strip() if len(parts) > 1 else ""

            # Limpar marcador [OBSERVACOES] do inicio
            obs_part = obs_part.replace("[OBSERVACOES]", "").strip()

            result["observacoes"] = obs_part
            result["tendencias"] = tend_part
        elif "[OBSERVACOES]" in llm_text:
            result["observacoes"] = llm_text.replace("[OBSERVACOES]", "").strip()
        else:
            # Fallback: tudo vai como observacoes
            result["observacoes"] = llm_text

        return result

    except ImportError:
        logger.warning("openai nao instalado - pulando analise LLM")
        return None
    except Exception as e:
        logger.error(f"Erro ao gerar analise LLM: {e}")
        return None


# =============================================================================
# ETAPA 5C: COLETA DE DADOS DE SATISFACAO (CALL 2)
# =============================================================================

def get_satisfaction_data(channel_id: str, video_ids: List[str]) -> Dict[str, Dict]:
    """
    Busca likes, dislikes, subscribers_gained, comments por video.
    Fonte primaria: yt_video_metrics (populado pelo monetization_oauth_collector).
    Comentarios: videos_historico (campo 'comentarios', sempre populado pelo collector).
    Fallback: videos_historico (tem likes + comentarios, sem dislikes/subs).
    Fallback API: YouTube Analytics API direto.

    Returns:
        {video_id: {likes, dislikes, subscribers_gained, views, comments, source}}
    """
    if not video_ids:
        return {}

    result = {}
    batch_size = 50

    # 1. Buscar de yt_video_metrics (fonte primaria — tem likes, dislikes, subscribers_gained)
    for i in range(0, len(video_ids), batch_size):
        batch = video_ids[i:i + batch_size]
        ids_str = ",".join(batch)
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/yt_video_metrics",
            params={
                "channel_id": f"eq.{channel_id}",
                "video_id": f"in.({ids_str})",
                "select": "video_id,likes,dislikes,subscribers_gained,views",
                "order": "updated_at.desc"
            },
            headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        )

        if resp.status_code == 200 and resp.json():
            for row in resp.json():
                vid = row.get("video_id")
                likes = row.get("likes") or 0
                if vid and vid not in result and likes > 0:
                    result[vid] = {
                        "likes": likes,
                        "dislikes": row.get("dislikes") or 0,
                        "subscribers_gained": row.get("subscribers_gained") or 0,
                        "views": row.get("views") or 0,
                        "source": "yt_video_metrics"
                    }

    # 2. Buscar comments de videos_historico (para TODOS os videos, inclusive os ja encontrados)
    # yt_video_metrics nao tem comments populado, entao sempre buscar de videos_historico
    for i in range(0, len(video_ids), batch_size):
        batch = video_ids[i:i + batch_size]
        ids_str = ",".join(batch)
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/videos_historico",
            params={
                "canal_id": f"eq.{channel_id}",
                "video_id": f"in.({ids_str})",
                "select": "video_id,comentarios,likes,views_atuais",
                "order": "data_coleta.desc"
            },
            headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        )

        if resp.status_code == 200 and resp.json():
            seen_comments = set()
            for row in resp.json():
                vid = row.get("video_id")
                if vid and vid not in seen_comments:
                    seen_comments.add(vid)
                    comments = row.get("comentarios") or 0
                    if vid in result:
                        # Adicionar comments ao registro existente (de yt_video_metrics)
                        result[vid]["comments"] = comments
                    else:
                        # Video nao encontrado em yt_video_metrics — usar videos_historico como fallback
                        likes = row.get("likes") or 0
                        if likes > 0:
                            result[vid] = {
                                "likes": likes,
                                "dislikes": 0,  # nao disponivel em videos_historico
                                "subscribers_gained": 0,  # nao disponivel
                                "comments": comments,
                                "views": row.get("views_atuais") or 0,
                                "source": "videos_historico_partial"
                            }

    # Garantir que todos os registros tenham campo 'comments' (default 0)
    for vid in result:
        if "comments" not in result[vid]:
            result[vid]["comments"] = 0

    # 3. Fallback API: buscar da YouTube Analytics API
    still_missing = [vid for vid in video_ids if vid not in result]
    if still_missing:
        logger.info(f"Canal {channel_id}: {len(still_missing)} videos sem dados de satisfacao, tentando API...")
        api_data = _fetch_satisfaction_from_api(channel_id, still_missing)
        result.update(api_data)

    logger.info(f"Canal {channel_id}: satisfacao obtida para {len(result)}/{len(video_ids)} videos")
    return result


def _fetch_satisfaction_from_api(channel_id: str, video_ids: List[str]) -> Dict[str, Dict]:
    """
    Busca likes, dislikes, subscribersGained da YouTube Analytics API via OAuth.
    Reutiliza infra de OAuth do agente (mesmos tokens/credentials).
    """
    result = {}

    tokens = _get_oauth_tokens(channel_id)
    if not tokens:
        logger.warning(f"Canal {channel_id}: sem tokens OAuth para buscar satisfacao da API")
        return result

    credentials = _get_credentials(channel_id)
    if not credentials:
        return result

    access_token = _refresh_token(
        tokens["refresh_token"],
        credentials["client_id"],
        credentials["client_secret"]
    )
    if not access_token:
        return result

    end_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

    all_rows = []
    page_size = 200
    start_index = 1
    video_id_set = set(video_ids)

    while True:
        resp = requests.get(
            "https://youtubeanalytics.googleapis.com/v2/reports",
            params={
                "ids": f"channel=={channel_id}",
                "startDate": start_date,
                "endDate": end_date,
                "metrics": "views,likes,dislikes,subscribersGained",
                "dimensions": "video",
                "sort": "-views",
                "maxResults": str(page_size),
                "startIndex": str(start_index)
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if resp.status_code != 200:
            logger.error(f"YouTube Analytics API (satisfacao) erro: {resp.status_code} - {resp.text[:200]}")
            break

        rows = resp.json().get("rows", [])
        if not rows:
            break

        all_rows.extend(rows)

        found_so_far = sum(1 for r in all_rows if r[0] in video_id_set)
        if found_so_far >= len(video_ids):
            break

        if len(rows) < page_size:
            break

        start_index += page_size

    # row format: [video_id, views, likes, dislikes, subscribersGained]
    for row in all_rows:
        vid = row[0]
        if vid in video_id_set:
            result[vid] = {
                "likes": int(row[2]) if len(row) > 2 and row[2] is not None else 0,
                "dislikes": int(row[3]) if len(row) > 3 and row[3] is not None else 0,
                "subscribers_gained": int(row[4]) if len(row) > 4 and row[4] is not None else 0,
                "views": int(row[1]) if len(row) > 1 and row[1] is not None else 0,
                "comments": 0,  # API nao retorna comments por video, vem de videos_historico
                "source": "analytics_api"
            }

    logger.info(f"YouTube Analytics API (satisfacao): {len(result)} videos de {len(all_rows)} total")
    return result


# =============================================================================
# ETAPA 5D: ENGINE DE SATISFACAO (CALL 2)
# =============================================================================

def analyze_satisfaction_performance(
    matched_videos: List[Dict],
    satisfaction_data: Dict[str, Dict]
) -> Dict:
    """
    Agrupa videos por estrutura e calcula metricas de satisfacao.
    Score composto: Sub Ratio 53% + Approval 47% (sem sentimento).

    Returns:
        {
            "channel_avg": {approval, like_ratio, sub_ratio},
            "structures": {A: {score, avg_approval, avg_like_ratio, avg_sub_ratio, ...}, ...},
            "insufficient": {G: {count, videos}, ...},
            "anomalies": [...],
            "all_videos": [...],
            "excluded_immature": int,
            "has_dislikes": bool,
            "has_subs": bool
        }
    """
    now = datetime.now(timezone.utc)

    combined = []
    excluded_immature = 0
    has_dislikes_global = False
    has_subs_global = False

    for v in matched_videos:
        vid = v["video_id"]
        sat = satisfaction_data.get(vid, {})

        # Filtro maturidade: 7+ dias
        if v.get("published_at"):
            pub_date = v["published_at"]
            if isinstance(pub_date, str):
                try:
                    pub_date = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    pub_date = None
            if pub_date and (now - pub_date).days < MIN_MATURITY_DAYS:
                excluded_immature += 1
                continue

        likes = sat.get("likes", 0)
        dislikes = sat.get("dislikes", 0)
        subs_gained = sat.get("subscribers_gained", 0)
        comments = sat.get("comments", 0)
        views = sat.get("views") or v.get("views") or 0

        if likes == 0 and views == 0:
            continue  # Sem dados de satisfacao

        if dislikes > 0:
            has_dislikes_global = True
        if subs_gained > 0:
            has_subs_global = True

        # Calcular metricas por video
        approval = (likes / (likes + dislikes) * 100) if (likes + dislikes) > 0 else None
        like_ratio = (likes / views * 100) if views > 0 else 0.0
        sub_ratio = (subs_gained / views * 100) if views > 0 else 0.0
        comment_ratio = (comments / views * 100) if views > 0 else 0.0

        combined.append({
            "video_id": vid,
            "structure": v["structure"],
            "title": v["title"],
            "likes": likes,
            "dislikes": dislikes,
            "subscribers_gained": subs_gained,
            "comments": comments,
            "views": views,
            "approval": round(approval, 2) if approval is not None else None,
            "like_ratio": round(like_ratio, 4),
            "sub_ratio": round(sub_ratio, 4),
            "comment_ratio": round(comment_ratio, 4),
            "published_at": v.get("published_at"),
            "source": sat.get("source", "unknown")
        })

    if not combined:
        return {
            "channel_avg": {"approval": 0, "like_ratio": 0, "sub_ratio": 0, "comment_ratio": 0},
            "structures": {},
            "insufficient": {},
            "anomalies": [],
            "all_videos": [],
            "excluded_immature": excluded_immature,
            "has_dislikes": False,
            "has_subs": False
        }

    # Media geral do canal
    all_approvals = [v["approval"] for v in combined if v["approval"] is not None]
    all_like_ratios = [v["like_ratio"] for v in combined]
    all_sub_ratios = [v["sub_ratio"] for v in combined]
    all_comment_ratios = [v["comment_ratio"] for v in combined]

    channel_avg = {
        "approval": round(statistics.mean(all_approvals), 2) if all_approvals else 0,
        "like_ratio": round(statistics.mean(all_like_ratios), 4) if all_like_ratios else 0,
        "sub_ratio": round(statistics.mean(all_sub_ratios), 4) if all_sub_ratios else 0,
        "comment_ratio": round(statistics.mean(all_comment_ratios), 4) if all_comment_ratios else 0
    }

    # Agrupar por estrutura
    groups = {}
    for v in combined:
        s = v["structure"]
        if s not in groups:
            groups[s] = []
        groups[s].append(v)

    structures = {}
    insufficient = {}
    anomalies = []

    for structure, videos in sorted(groups.items()):
        n = len(videos)
        approvals = [v["approval"] for v in videos if v["approval"] is not None]
        like_ratios = [v["like_ratio"] for v in videos]
        sub_ratios = [v["sub_ratio"] for v in videos]
        comment_ratios = [v["comment_ratio"] for v in videos]

        if n < MIN_SAMPLE_SIZE:
            insufficient[structure] = {
                "count": n,
                "videos": [{
                    "title": v["title"],
                    "approval": v["approval"],
                    "like_ratio": v["like_ratio"],
                    "sub_ratio": v["sub_ratio"],
                    "comment_ratio": v["comment_ratio"],
                    "comments": v["comments"]
                } for v in videos]
            }
            continue

        avg_approval = round(statistics.mean(approvals), 2) if approvals else 0
        avg_like_ratio = round(statistics.mean(like_ratios), 4)
        avg_sub_ratio = round(statistics.mean(sub_ratios), 4)
        avg_comment_ratio = round(statistics.mean(comment_ratios), 4)
        avg_comments = round(statistics.mean([v["comments"] for v in videos]))

        # Normalizacao: desvio % vs media do canal
        approval_dev = ((avg_approval - channel_avg["approval"]) / channel_avg["approval"] * 100) if channel_avg["approval"] > 0 else 0
        sub_ratio_dev = ((avg_sub_ratio - channel_avg["sub_ratio"]) / channel_avg["sub_ratio"] * 100) if channel_avg["sub_ratio"] > 0 else 0
        comment_ratio_dev = ((avg_comment_ratio - channel_avg["comment_ratio"]) / channel_avg["comment_ratio"] * 100) if channel_avg["comment_ratio"] > 0 else 0

        # Score composto 0-100 (50 = media do canal)
        # Mapear desvio para escala 0-100 onde 50 = media
        # Cada 10% de desvio = ~5 pontos no score
        approval_score = 50 + (approval_dev * 0.5)
        sub_score = 50 + (sub_ratio_dev * 0.5)

        # Clamp 0-100
        approval_score = max(0, min(100, approval_score))
        sub_score = max(0, min(100, sub_score))

        if has_subs_global:
            score = round(sub_score * SATISFACTION_WEIGHT_SUB + approval_score * SATISFACTION_WEIGHT_APPROVAL)
        else:
            # Sem dados de subscribers: score baseado apenas em approval
            score = round(approval_score)

        # Status vs media
        if score > 55:
            status = "ACIMA"
        elif score < 45:
            status = "ABAIXO"
        else:
            status = "MEDIA"

        structures[structure] = {
            "score": score,
            "avg_approval": avg_approval,
            "avg_like_ratio": round(avg_like_ratio, 4),
            "avg_sub_ratio": round(avg_sub_ratio, 4),
            "avg_comment_ratio": round(avg_comment_ratio, 4),
            "avg_comments": avg_comments,
            "approval_dev": round(approval_dev, 1),
            "sub_ratio_dev": round(sub_ratio_dev, 1),
            "comment_ratio_dev": round(comment_ratio_dev, 1),
            "count": n,
            "status": status,
            "videos": [{
                "title": v["title"],
                "video_id": v["video_id"],
                "approval": v["approval"],
                "like_ratio": v["like_ratio"],
                "sub_ratio": v["sub_ratio"],
                "comment_ratio": v["comment_ratio"],
                "comments": v["comments"],
                "likes": v["likes"],
                "dislikes": v["dislikes"],
                "subscribers_gained": v["subscribers_gained"],
                "views": v["views"]
            } for v in videos]
        }

        # Anomalias: metrica 3x+ acima/abaixo media da estrutura
        for v in videos:
            reasons = []
            if avg_sub_ratio > 0:
                if v["sub_ratio"] > 0:
                    ratio = v["sub_ratio"] / avg_sub_ratio
                    if ratio >= ANOMALY_SATISFACTION_MULTIPLIER:
                        reasons.append(f"Sub Ratio {v['sub_ratio']:.4f}% = {ratio:.1f}x acima da media da estrutura ({avg_sub_ratio:.4f}%)")
                    elif (avg_sub_ratio / v["sub_ratio"]) >= ANOMALY_SATISFACTION_MULTIPLIER:
                        reasons.append(f"Sub Ratio {v['sub_ratio']:.4f}% = {avg_sub_ratio / v['sub_ratio']:.1f}x abaixo da media ({avg_sub_ratio:.4f}%)")
                elif v["sub_ratio"] == 0:
                    # sub_ratio=0 com media >0 e sempre anomalia
                    reasons.append(f"Sub Ratio 0% — nenhum inscrito ganho (media da estrutura: {avg_sub_ratio:.4f}%)")

            if avg_approval > 0 and v["approval"] is not None:
                diff = abs(v["approval"] - avg_approval)
                if diff > 15:  # >15pp de diferenca em approval
                    direction = "acima" if v["approval"] > avg_approval else "abaixo"
                    reasons.append(f"Approval {v['approval']:.1f}% vs {avg_approval:.1f}% media ({direction}, diff {diff:.1f}pp)")

            if reasons:
                anomalies.append({
                    "video_id": v["video_id"],
                    "title": v["title"],
                    "structure": structure,
                    "approval": v["approval"],
                    "sub_ratio": v["sub_ratio"],
                    "likes": v["likes"],
                    "dislikes": v["dislikes"],
                    "views": v["views"],
                    "reasons": reasons
                })

    # Ordenar por score desc
    sorted_structures = dict(sorted(
        structures.items(),
        key=lambda x: x[1]["score"],
        reverse=True
    ))

    return {
        "channel_avg": channel_avg,
        "structures": sorted_structures,
        "insufficient": insufficient,
        "anomalies": anomalies,
        "all_videos": combined,
        "excluded_immature": excluded_immature,
        "has_dislikes": has_dislikes_global,
        "has_subs": has_subs_global
    }


# =============================================================================
# ETAPA 5E: COMPARACAO TEMPORAL DE SATISFACAO
# =============================================================================

def compare_satisfaction_with_previous(channel_id: str, current_results: Dict) -> Optional[Dict]:
    """
    Busca dados de satisfacao da analise anterior para comparacao temporal.
    """
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/copy_analysis_runs",
        params={
            "channel_id": f"eq.{channel_id}",
            "select": "run_date,results_json,report_text",
            "order": "run_date.desc",
            "limit": "1"
        },
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    )

    if resp.status_code != 200 or not resp.json():
        return None

    prev = resp.json()[0]
    prev_results = prev.get("results_json") or {}
    if isinstance(prev_results, str):
        prev_results = json.loads(prev_results)

    prev_sat = prev_results.get("satisfaction_structures", {})
    if not prev_sat:
        return None  # Analise anterior nao tinha dados de satisfacao

    prev_date = prev.get("run_date", "")
    curr_structures = current_results.get("structures", {})

    # Rankings anterior e atual
    prev_ranking = sorted(prev_sat.items(), key=lambda x: x[1].get("score", 0), reverse=True)
    curr_ranking = sorted(curr_structures.items(), key=lambda x: x[1].get("score", 0), reverse=True)

    prev_rank_map = {s: i+1 for i, (s, _) in enumerate(prev_ranking)}
    curr_rank_map = {s: i+1 for i, (s, _) in enumerate(curr_ranking)}

    changes = {}
    new_structures = []

    for structure, data in curr_structures.items():
        if structure in prev_sat:
            prev_score = prev_sat[structure].get("score", 0)
            curr_score = data["score"]
            prev_rank = prev_rank_map.get(structure, 0)
            curr_rank = curr_rank_map.get(structure, 0)

            changes[structure] = {
                "prev_score": prev_score,
                "curr_score": curr_score,
                "diff": curr_score - prev_score,
                "prev_approval": prev_sat[structure].get("avg_approval", 0),
                "curr_approval": data["avg_approval"],
                "prev_sub_ratio": prev_sat[structure].get("avg_sub_ratio", 0),
                "curr_sub_ratio": data["avg_sub_ratio"],
                "prev_rank": prev_rank,
                "curr_rank": curr_rank,
                "rank_change": prev_rank - curr_rank
            }
        else:
            new_structures.append(structure)

    return {
        "previous_date": prev_date,
        "changes": changes,
        "new_structures": new_structures
    }


# =============================================================================
# ETAPA 5F: LLM INSIGHTS DE SATISFACAO (CALL 2)
# =============================================================================

def generate_satisfaction_llm_insights(
    channel_name: str,
    sat_analysis: Dict,
    sat_comparison: Optional[Dict]
) -> Optional[Dict]:
    """
    Call 2 da LLM: analise narrativa de satisfacao do publico.
    Complementar a Call 1 (retencao). Foco em: approval, sub ratio, like ratio.
    """
    try:
        from openai import OpenAI

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY nao configurada - pulando analise LLM satisfacao")
            return None

        client = OpenAI(api_key=api_key)
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

        ch_avg = sat_analysis["channel_avg"]
        structures = sat_analysis["structures"]
        insufficient = sat_analysis["insufficient"]
        all_videos = sat_analysis.get("all_videos", [])
        has_dislikes = sat_analysis.get("has_dislikes", False)
        has_subs = sat_analysis.get("has_subs", False)

        data_block = f"CANAL: {channel_name}\n"
        data_block += f"Total videos analisados (satisfacao): {len(all_videos)}\n"
        data_block += f"Media geral do canal: {ch_avg['approval']:.1f}% approval | {ch_avg['like_ratio']:.4f}% like ratio | {ch_avg['sub_ratio']:.4f}% sub ratio | {ch_avg.get('comment_ratio', 0):.4f}% comment ratio\n"
        data_block += f"Dados de dislikes disponiveis: {'Sim' if has_dislikes else 'Nao (approval calculado apenas com likes)'}\n"
        data_block += f"Dados de inscritos ganhos por video: {'Sim' if has_subs else 'Nao'}\n\n"

        data_block += "DADOS POR ESTRUTURA (cada video individual):\n\n"
        for s, d in structures.items():
            data_block += f"Estrutura {s} ({d['count']} videos) — Score: {d['score']}/100 — Status: {d['status']}\n"
            for v in d.get("videos", []):
                approval_str = f"{v.get('approval', 0):.1f}%" if v.get('approval') is not None else "N/A"
                data_block += f"  - \"{v['title']}\" | approval: {approval_str} | like_ratio: {v.get('like_ratio', 0):.4f}% | sub_ratio: {v.get('sub_ratio', 0):.4f}% | comment_ratio: {v.get('comment_ratio', 0):.4f}% | comments: {v.get('comments', 0)} | likes: {v.get('likes', 0)} | dislikes: {v.get('dislikes', 0)} | subs_gained: {v.get('subscribers_gained', 0)} | views: {v.get('views', 0):,}\n"
            data_block += f"  Media estrutura: {d['avg_approval']:.1f}% approval | {d['avg_like_ratio']:.4f}% like_ratio | {d['avg_sub_ratio']:.4f}% sub_ratio | {d.get('avg_comment_ratio', 0):.4f}% comment_ratio | {d.get('avg_comments', 0)} coment. medio\n"
            data_block += f"  Desvio vs canal: {d['approval_dev']:+.1f}% approval | {d['sub_ratio_dev']:+.1f}% sub_ratio | {d.get('comment_ratio_dev', 0):+.1f}% comment_ratio\n\n"

        if insufficient:
            data_block += "ESTRUTURAS COM POUCOS DADOS (<3 videos):\n"
            for s, d in insufficient.items():
                data_block += f"  Estrutura {s}: {d['count']} video(s)\n"
                for v in d.get("videos", []):
                    approval_str = f"{v.get('approval', 0):.1f}%" if v.get('approval') is not None else "N/A"
                    data_block += f"    - \"{v['title']}\" | approval: {approval_str} | sub_ratio: {v.get('sub_ratio', 0):.4f}% | comments: {v.get('comments', 0)}\n"
            data_block += "\n"

        if sat_comparison and sat_comparison.get("changes"):
            prev_date = sat_comparison.get("previous_date", "")
            if isinstance(prev_date, str) and "T" in prev_date:
                try:
                    prev_date = datetime.fromisoformat(prev_date.replace("Z", "+00:00")).strftime("%d/%m/%Y")
                except (ValueError, TypeError):
                    pass
            data_block += f"COMPARACAO COM ANALISE ANTERIOR ({prev_date}):\n"
            for s, c in sat_comparison["changes"].items():
                rank_info = ""
                if c["rank_change"] > 0:
                    rank_info = f" (subiu: {c['prev_rank']}o->{c['curr_rank']}o)"
                elif c["rank_change"] < 0:
                    rank_info = f" (caiu: {c['prev_rank']}o->{c['curr_rank']}o)"
                data_block += f"  Estrutura {s}: score {c['prev_score']}->{c['curr_score']} ({c['diff']:+d}) | approval {c['prev_approval']:.1f}%->{c['curr_approval']:.1f}% | sub_ratio {c['prev_sub_ratio']:.4f}%->{c['curr_sub_ratio']:.4f}%{rank_info}\n"
            if sat_comparison.get("new_structures"):
                data_block += f"  Novas no ranking: {', '.join(sat_comparison['new_structures'])}\n"
            data_block += "\n"

        # =====================================================================
        # PROMPT LLM SATISFACAO — System + User
        # =====================================================================

        system_prompt = """Voce e um analista senior de satisfacao de audiencia para canais YouTube.
Voce analisa dados PRE-CALCULADOS por um sistema Python e produz insights narrativos
sobre o quanto a audiencia GOSTOU do conteudo — complementar a analise de retencao.

=== CONTEXTO: RETENCAO vs SATISFACAO ===

O Agente 1 (Call 1) ja analisa RETENCAO: quanto tempo o espectador ficou no video.
Voce (Call 2) analisa SATISFACAO: o espectador gostou de ter ficado?

Essa distincao e critica:
- Um video pode ter retencao alta por mecanismos retoricos (ganchos, loops abertos)
  mas deixar o espectador insatisfeito. Ele ficou, mas nao gostou.
- Um video pode ter retencao moderada mas satisfacao altissima — o espectador saiu
  genuinamente satisfeito e se inscreveu.

A combinacao das duas dimensoes (retencao + satisfacao) e mais poderosa que qualquer
uma isolada. Mas voce NAO cruza com retencao — seus dados sao apenas de satisfacao.
O cruzamento e feito por leitura humana.

=== O QUE SAO ESTRUTURAS DE COPY ===

Cada video do canal usa uma ESTRUTURA NARRATIVA identificada por uma letra.
A estrutura define COMO a historia e contada — nao O QUE e contado.
Exemplo: dois videos sobre "A Queda de Roma" podem usar:
- A (cronologica): conta linear do inicio ao fim
- B (misterio): abre com pergunta, vai revelando
O MESMO tema com estruturas diferentes gera satisfacao DIFERENTE.

=== METRICAS DE SATISFACAO ===

1. LIKE APPROVAL RATE = likes / (likes + dislikes)
   - Termometro direto: de todos que reagiram, qual % aprovou?
   - Se nao ha dislikes disponiveis, esta metrica NAO esta disponivel
   - Approval alto (>95%) e a norma no YouTube — o sinal esta nas DIFERENCAS entre estruturas
   - Approval baixo (<90%) e um sinal forte de problema

2. LIKE RATIO = likes / views (INFORMATIVO)
   - Que % dos espectadores deu like?
   - Complementar — indica engajamento geral
   - NAO entra no score composto (evita redundancia com approval)
   - Use para contexto: "estrutura X tem approval similar mas like ratio 2x maior"

3. SUB RATIO = inscritos ganhos / views
   - Sinal MAIS FORTE de satisfacao (maior commitment do espectador)
   - Um espectador que se inscreve esta dizendo: "quero mais disso"
   - Pesa 53% no score composto
   - Se nao ha dados de inscritos por video, esta metrica nao esta disponivel

4. SCORE COMPOSTO (0-100)
   - 50 = media do canal. >50 = acima. <50 = abaixo
   - Pesos: Sub Ratio 53% + Approval 47% (sem sentimento de comentarios)
   - O score e relativo ao PROPRIO canal — NAO compare entre canais

=== COMO INTERPRETAR ===

A MATRIZ RETENCAO x SATISFACAO (contexto para o leitor humano):

| | Satisfacao Alta | Satisfacao Baixa |
|---|---|---|
| Retencao Alta | Excelencia real | Alerta: prende mas nao satisfaz |
| Retencao Baixa | Oportunidade: bom conteudo, execucao fraca | Problema em ambas dimensoes |

Voce NAO faz esse cruzamento — apenas reporta satisfacao. Mas pode mencionar
que o leitor deve cruzar com o relatorio de retencao para a visao completa.

=== REGRAS INVIOLAVEIS ===

1. Seja FACTUAL — cite numeros EXATOS dos dados fornecidos
2. NAO invente dados — use APENAS o que esta nos dados
3. NAO de recomendacoes de acao — decisao e HUMANA. Voce apresenta PADROES
4. NAO tente explicar POR QUE uma estrutura tem mais satisfacao — so reporte o fato
5. NAO repita tabelas de ranking (o sistema ja gera automaticamente)
6. Anomalias: REPORTE como fato + flag. NAO explique a causa
7. Escreva em portugues, paragrafos curtos separados por linha em branco
8. Escreva o quanto for necessario. NAO resuma, NAO corte a analise
9. Use EXATAMENTE os marcadores [OBSERVACOES] e [TENDENCIAS]
10. Se dados de dislikes ou inscritos nao estao disponiveis, mencione essa limitacao

=== TIPO DE RACIOCINIO ESPERADO ===

NAO FACA ISSO (superficial):
"A estrutura lider tem score 68. A pior tem 35."

FACA ISSO (profissional):
"A estrutura A lidera com score 68/100, impulsionada por um Sub Ratio de 0.42%
(+20.0% acima da media do canal de 0.35%). Dos 5 videos analisados, 4 tem sub_ratio
acima de 0.38%, indicando que essa forma narrativa gera conversao de inscritos
de forma consistente.

Em contraste, a estrutura D tem score 35/100 com Sub Ratio de 0.18% (-48.6% abaixo
da media do canal). Apesar de um Approval Rate aceitavel de 94.2%, os espectadores
nao se sentem motivados a se inscrever apos assistir — o conteudo prende mas nao
converte. Isso sugere uma experiencia 'ok' mas nao memoravel."
"""

        previous_report_block = ""
        if sat_comparison and sat_comparison.get("changes"):
            prev_date = sat_comparison.get("previous_date", "")
            if isinstance(prev_date, str) and "T" in prev_date:
                try:
                    prev_date = datetime.fromisoformat(prev_date.replace("Z", "+00:00")).strftime("%d/%m/%Y")
                except (ValueError, TypeError):
                    pass
            previous_report_block = f"""
VOCE TEM DADOS DA ANALISE ANTERIOR ({prev_date}) para comparar tendencias.
Use esses dados para identificar evolucoes, consolidacoes ou reversoes.
"""

        user_prompt = f"""{previous_report_block}

Produza EXATAMENTE 2 blocos:

[OBSERVACOES]
Analise de satisfacao DESTA SEMANA. Cubra obrigatoriamente TODOS os pontos:

1. LIDERANCA DE SATISFACAO: Qual estrutura lidera em score? Com que margem?
   Cite approval, like ratio e sub ratio da lider. E consistente entre videos?

2. APPROVAL POR ESTRUTURA: Para CADA estrutura, cite o approval e desvio vs canal.
   Se alguma esta abaixo de 90%, destaque como sinal forte de insatisfacao.
   Se todas estao acima de 95%, note que as diferencas sao sutis mas ainda informativas.

3. SUB RATIO (se disponivel): Para CADA estrutura, cite o sub ratio.
   Qual estrutura CONVERTE mais espectadores em inscritos?
   Destaque a diferenca entre a melhor e a pior em termos relativos.

4. LIKE RATIO (informativo): Padroes notaveis no like ratio entre estruturas.
   Se uma tem approval similar mas like ratio muito diferente, destaque.

5. PIOR DESEMPENHO: Qual estrutura tem a pior satisfacao? Score, approval, sub ratio.
   O que os numeros mostram (sem teorizar POR QUE)?

6. ANOMALIAS: Videos com metricas muito acima ou abaixo da media da estrutura.
   Reporte como fato.

7. LIMITACOES DOS DADOS: Se faltam dislikes ou inscritos, mencione o impacto.
   Se a fonte e parcial (videos_historico sem dislikes), note.

8. OUTROS PADROES: Qualquer insight relevante nos dados.

[TENDENCIAS]
EVOLUCAO ao longo do tempo (SO se houver analise anterior):
- Para cada estrutura, compare scores e metricas vs anterior
- Movimentos no ranking
- Padroes confirmados ou revertidos
- Se primeira analise: "Primeira analise de satisfacao. Sem dados anteriores."

DADOS DA SEMANA ATUAL:
{data_block}"""

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )

        llm_text = response.choices[0].message.content.strip()
        logger.info(f"LLM satisfacao gerada ({response.usage.total_tokens} tokens)")

        result = {"observacoes": "", "tendencias": ""}

        if "[TENDENCIAS]" in llm_text:
            parts = llm_text.split("[TENDENCIAS]")
            obs_part = parts[0].replace("[OBSERVACOES]", "").strip()
            tend_part = parts[1].strip() if len(parts) > 1 else ""
            result["observacoes"] = obs_part
            result["tendencias"] = tend_part
        elif "[OBSERVACOES]" in llm_text:
            result["observacoes"] = llm_text.replace("[OBSERVACOES]", "").strip()
        else:
            result["observacoes"] = llm_text

        return result

    except ImportError:
        logger.warning("openai nao instalado - pulando analise LLM satisfacao")
        return None
    except Exception as e:
        logger.error(f"Erro ao gerar analise LLM satisfacao: {e}")
        return None


# =============================================================================
# ETAPA 5G: GERADOR DE RELATORIO DE SATISFACAO
# =============================================================================

def generate_satisfaction_report(
    channel_name: str,
    sat_analysis: Dict,
    sat_comparison: Optional[Dict],
    llm_insights: Optional[Dict] = None
) -> str:
    """
    Gera relatorio de satisfacao (Call 2).
    Formato: Ranking por Score + Approval + Sub Ratio + Anomalias + vs Anterior
    """
    now = datetime.now().strftime("%d-%m-%Y")
    ch_avg = sat_analysis["channel_avg"]
    structures = sat_analysis["structures"]
    insufficient = sat_analysis["insufficient"]
    anomalies = sat_analysis["anomalies"]
    all_videos = sat_analysis.get("all_videos", [])
    excluded = sat_analysis.get("excluded_immature", 0)
    has_dislikes = sat_analysis.get("has_dislikes", False)
    has_subs = sat_analysis.get("has_subs", False)

    lines = []

    # === HEADER ===
    lines.append("")
    lines.append("=" * 60)
    lines.append(f"RELATORIO SATISFACAO -- {channel_name} | {now}")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Videos analisados: {len(all_videos)} ({excluded} excluidos por maturidade <7 dias)")
    lines.append(f"Media geral: {ch_avg['approval']:.1f}% approval | {ch_avg['like_ratio']:.4f}% like ratio | {ch_avg['sub_ratio']:.4f}% sub ratio | {ch_avg.get('comment_ratio', 0):.4f}% comment ratio")

    if not has_dislikes and not has_subs:
        lines.append("AVISO: Sem dados de dislikes NEM inscritos ganhos por video. Scores exibidos NAO sao confiaveis (todos serao ~50).")
    elif not has_dislikes:
        lines.append("NOTA: Dados de dislikes nao disponiveis. Approval calculado sem dislikes.")
    elif not has_subs:
        lines.append("NOTA: Dados de inscritos ganhos por video nao disponiveis. Score calculado sem Sub Ratio.")
    else:
        lines.append(f"Score calculado sem dados de sentimento. Pesos: Sub Ratio {SATISFACTION_WEIGHT_SUB*100:.0f}% + Approval {SATISFACTION_WEIGHT_APPROVAL*100:.0f}%")
    lines.append("")

    # === RANKING POR SCORE DE SATISFACAO ===
    if structures:
        lines.append("--- RANKING POR ESTRUTURA (Score de Satisfacao) ---")
        lines.append("")
        lines.append(f" {'#':<3} {'Estr.':<8} {'Score':<8} {'Approval':<11} {'Like Ratio':<13} {'Sub Ratio':<12} {'Videos':<8} {'Status'}")
        lines.append(f" {'─'*3} {'─'*7} {'─'*7} {'─'*10} {'─'*12} {'─'*11} {'─'*7} {'─'*8}")

        for i, (structure, data) in enumerate(structures.items(), 1):
            sub_str = f"{data['avg_sub_ratio']:.4f}%" if has_subs else "N/A"
            lines.append(
                f" {i:<3} {structure:<8} {data['score']:<8} {data['avg_approval']:.1f}%{'':<5} "
                f"{data['avg_like_ratio']:.4f}%{'':<5} {sub_str:<12} {data['count']:<8} {data['status']}"
            )

        lines.append("")

    # === LIKE APPROVAL RATE ===
    if structures:
        lines.append("--- LIKE APPROVAL RATE (likes / likes+dislikes) ---")
        lines.append("")
        lines.append(f" {'Estr.':<8} {'Approval':<11} {'vs Media Canal':<16} {'Tendencia'}")

        for structure, data in structures.items():
            dev_str = f"{data['approval_dev']:+.1f}%"
            lines.append(f" {structure:<8} {data['avg_approval']:.1f}%{'':<5} {dev_str:<16}")
        lines.append("")

    # === SUB RATIO ===
    if structures and has_subs:
        lines.append("--- SUB RATIO (inscritos ganhos / views) ---")
        lines.append("")
        lines.append(f" {'Estr.':<8} {'Sub Ratio':<12} {'vs Media Canal':<16} {'Tendencia'}")

        for structure, data in structures.items():
            dev_str = f"{data['sub_ratio_dev']:+.1f}%"
            lines.append(f" {structure:<8} {data['avg_sub_ratio']:.4f}%{'':<5} {dev_str:<16}")
        lines.append("")

    # === COMMENT RATIO ===
    if structures:
        lines.append("--- COMMENT RATIO (comentarios / views) ---")
        lines.append("")
        lines.append(f" {'Estr.':<8} {'Ratio':<12} {'Coment. Med':<14} {'vs Media Canal':<16}")

        for structure, data in structures.items():
            dev_str = f"{data.get('comment_ratio_dev', 0):+.1f}%"
            lines.append(f" {structure:<8} {data.get('avg_comment_ratio', 0):.4f}%{'':<5} {data.get('avg_comments', 0):<14} {dev_str}")
        lines.append("")

    # === OBSERVACOES (LLM) ===
    obs_text = ""
    tend_text = ""
    if llm_insights and isinstance(llm_insights, dict):
        obs_text = llm_insights.get("observacoes", "")
        tend_text = llm_insights.get("tendencias", "")

    if obs_text:
        lines.append("--- OBSERVACOES (Satisfacao) ---")
        lines.append("")
        for line in obs_text.split("\n"):
            lines.append(line)
        lines.append("")

    # === ANOMALIAS ===
    if anomalies:
        lines.append("--- ANOMALIAS (Satisfacao) ---")
        lines.append("")
        for anom in anomalies:
            lines.append(f"! Estrutura {anom['structure']} -- Video \"{anom['title']}\"")
            if anom.get("approval") is not None:
                lines.append(f"   Approval: {anom['approval']:.1f}% | Likes: {anom['likes']} | Dislikes: {anom['dislikes']}")
            lines.append(f"   Sub Ratio: {anom['sub_ratio']:.4f}% | Views: {anom['views']:,}")
            for reason in anom.get("reasons", []):
                lines.append(f"   NOTA: {reason}")
            lines.append("")

    # === DADOS INSUFICIENTES ===
    if insufficient:
        lines.append("--- DADOS INSUFICIENTES (<3 videos) ---")
        lines.append("")
        for structure, data_ins in insufficient.items():
            lines.append(f" Estrutura {structure}: {data_ins['count']} video(s)")
            for v in data_ins.get("videos", []):
                approval_str = f"{v['approval']:.1f}%" if v.get('approval') is not None else "N/A"
                lines.append(f"   - \"{v['title']}\" | approval: {approval_str} | sub_ratio: {v['sub_ratio']:.4f}%")
        lines.append("")

    # === vs. ANALISE ANTERIOR ===
    if sat_comparison and sat_comparison.get("changes"):
        prev_date = sat_comparison.get("previous_date", "")
        if isinstance(prev_date, str) and "T" in prev_date:
            try:
                prev_date = datetime.fromisoformat(prev_date.replace("Z", "+00:00")).strftime("%d-%m-%Y")
            except (ValueError, TypeError):
                pass

        lines.append(f"--- vs. ANALISE ANTERIOR ({prev_date}) (Satisfacao) ---")
        lines.append("")
        lines.append(f" {'Estr.':<8} {'Score Ant.':<12} {'Score Atual':<13} {'Variacao':<10} {'Ranking'}")

        for structure, change in sat_comparison.get("changes", {}).items():
            var_str = f"{change['diff']:+d}"
            rank_str = ""
            if change["rank_change"] > 0:
                rank_str = f"Subiu {change['prev_rank']}o->{change['curr_rank']}o"
            elif change["rank_change"] < 0:
                rank_str = f"Caiu {change['prev_rank']}o->{change['curr_rank']}o"
            else:
                rank_str = f"Manteve {change['curr_rank']}o"

            lines.append(f" {structure:<8} {change['prev_score']:<12} {change['curr_score']:<13} {var_str:<10} {rank_str}")

        if sat_comparison.get("new_structures"):
            lines.append("")
            lines.append(f"Estruturas novas no ranking: {', '.join(sat_comparison['new_structures'])}")

        lines.append("")

        if tend_text:
            for line in tend_text.split("\n"):
                lines.append(line)
            lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)


# =============================================================================
# ETAPA 6: GERADOR DE RELATORIO
# =============================================================================

def generate_report(
    channel_name: str,
    analysis: Dict,
    comparison: Optional[Dict],
    total_sheet_videos: int,
    total_no_match: int,
    llm_insights: Optional[Dict] = None
) -> str:
    """
    Gera relatorio formatado no estilo EXATO do HTML spec.
    Ordem das secoes:
    1. Header + meta (videos, periodo, media)
    2. RANKING POR ESTRUTURA DE COPY (tabela)
    3. OBSERVACOES (narrativa da LLM)
    4. ANOMALIAS FLAGGED (dados estruturados)
    5. DADOS INSUFICIENTES (<3 videos)
    6. vs. ANALISE ANTERIOR (tabela + narrativa de tendencias da LLM)
    """
    now = datetime.now().strftime("%d-%m-%Y")
    ch_avg = analysis["channel_avg"]
    structures = analysis["structures"]
    insufficient = analysis["insufficient"]
    anomalies = analysis["anomalies"]
    excluded = analysis.get("excluded_immature", 0)
    all_videos = analysis.get("all_videos", [])
    total_analyzed = len(all_videos)

    # Calcular periodo (min/max de published_at dos videos analisados)
    dates = []
    for v in all_videos:
        pub = v.get("published_at")
        if pub:
            if isinstance(pub, str):
                try:
                    pub = datetime.fromisoformat(pub.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    continue
            if isinstance(pub, datetime):
                dates.append(pub)

    periodo_str = ""
    if dates:
        min_date = min(dates).strftime("%d-%m")
        max_date = max(dates).strftime("%d-%m")
        periodo_str = f"{min_date} a {max_date}"

    lines = []

    # === HEADER ===
    lines.append("=" * 60)
    lines.append(f"RELATORIO {channel_name} | {now}")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Videos analisados: {total_analyzed} (de {total_sheet_videos} na planilha, "
                 f"{excluded} excluidos por maturidade <7 dias, {total_no_match} sem match)")
    if periodo_str:
        lines.append(f"Periodo: {periodo_str}")
    lines.append(f"Media geral do canal: {ch_avg['retention']:.1f}% retencao | "
                 f"{ch_avg['watch_time']:.1f} min watch time | "
                 f"{ch_avg['views']:,.0f} views")
    lines.append("")

    # === RANKING POR ESTRUTURA DE COPY ===
    lines.append("--- RANKING POR ESTRUTURA DE COPY ---")
    lines.append("")
    lines.append(f" {'#':<3} {'Estr.':<8} {'Ret%':<8} {'Watch Time':<13} {'Views Med':<12} {'Videos':<8} {'Status'}")
    lines.append(f" {'─'*3} {'─'*7} {'─'*7} {'─'*12} {'─'*11} {'─'*7} {'─'*8}")

    for i, (structure, data) in enumerate(structures.items(), 1):
        views_fmt = f"{data['avg_views']:,.0f}" if data['avg_views'] else "N/A"
        wt_fmt = f"{data['avg_watch_time']:.1f} min" if data['avg_watch_time'] else "N/A"
        diff_str = f"({data['diff_from_avg']:+.1f}%)"

        lines.append(
            f" {i:<3} {structure:<8} {data['avg_retention']:.1f}%{'':<3} "
            f"{wt_fmt:<13} {views_fmt:<12} {data['count']:<8} {data['status']} {diff_str}"
        )

    lines.append("")

    # === OBSERVACOES (narrativa da LLM) ===
    obs_text = ""
    tend_text = ""
    if llm_insights and isinstance(llm_insights, dict):
        obs_text = llm_insights.get("observacoes", "")
        tend_text = llm_insights.get("tendencias", "")
    elif llm_insights and isinstance(llm_insights, str):
        # Fallback: se receber string pura (compatibilidade)
        obs_text = llm_insights

    if obs_text:
        lines.append("--- OBSERVACOES ---")
        lines.append("")
        for line in obs_text.split("\n"):
            lines.append(line)
        lines.append("")

    # === ANOMALIAS (FLAGGED) ===
    if anomalies:
        lines.append("--- ANOMALIAS (FLAGGED) ---")
        lines.append("")

        for anom in anomalies:
            s = anom["structure"]
            title = anom["title"]
            ret = anom["retention"]
            views = anom["views"]

            # Buscar media da estrutura para comparacao
            struct_data = structures.get(s, {})
            avg_ret = struct_data.get("avg_retention", 0)
            avg_views = struct_data.get("avg_views", 0)

            lines.append(f"! Estrutura {s} -- Video \"{title}\"")

            # Retenção vs média
            if avg_ret > 0:
                lines.append(f"   Retencao: {ret:.1f}% (vs {avg_ret:.1f}% media da estrutura)")

            # Views vs média
            if avg_views > 0 and views > 0:
                if views > avg_views:
                    multiplier = views / avg_views
                    lines.append(f"   Views: {views:,.0f} (vs {avg_views:,.0f} media da estrutura -- {multiplier:.1f}x acima)")
                elif views < avg_views:
                    multiplier = avg_views / views
                    lines.append(f"   Views: {views:,.0f} (vs {avg_views:,.0f} media da estrutura -- {multiplier:.1f}x abaixo)")

            # Data de publicação
            pub = anom.get("published_at")
            if pub:
                if isinstance(pub, str):
                    try:
                        pub = datetime.fromisoformat(pub.replace("Z", "+00:00"))
                    except (ValueError, TypeError):
                        pub = None
                if isinstance(pub, datetime):
                    lines.append(f"   Publicado: {pub.strftime('%d-%m-%Y')}")

            # Reasons detalhados
            for reason in anom.get("reasons", []):
                lines.append(f"   NOTA: {reason}")

            lines.append("")

    # === DADOS INSUFICIENTES (<3 videos) ===
    if insufficient:
        lines.append("--- DADOS INSUFICIENTES (<3 videos) ---")
        lines.append("")
        lines.append(f" {'Estr.':<8} {'Videos':<8} {'Ret% (parcial)':<18} {'Nota'}")
        for structure, data_ins in insufficient.items():
            ret_str = f"{data_ins['partial_retention']:.1f}%" if data_ins['partial_retention'] else "N/A"
            lines.append(f" {structure:<8} {data_ins['count']:<8} {ret_str:<18} Aguardando mais videos")
        lines.append("")

    # === vs. ANALISE ANTERIOR + TENDENCIAS ===
    if comparison and comparison.get("changes"):
        prev_date = comparison.get("previous_date", "")
        if isinstance(prev_date, str) and "T" in prev_date:
            try:
                prev_date = datetime.fromisoformat(prev_date.replace("Z", "+00:00")).strftime("%d-%m-%Y")
            except (ValueError, TypeError):
                pass

        lines.append(f"--- vs. ANALISE ANTERIOR ({prev_date}) ---")
        lines.append("")
        lines.append(f" {'Estr.':<8} {'Anterior':<10} {'Atual':<8} {'Variacao':<10} {'Ranking'}")

        for structure, change in comparison.get("changes", {}).items():
            var_str = f"{change['diff']:+.1f}%"
            rank_str = ""
            if change["rank_change"] > 0:
                rank_str = f"Subiu {change['prev_rank']}o->{change['curr_rank']}o"
            elif change["rank_change"] < 0:
                rank_str = f"Caiu {change['prev_rank']}o->{change['curr_rank']}o"
            else:
                rank_str = f"Manteve {change['curr_rank']}o"

            lines.append(f" {structure:<8} {change['prev_retention']:.1f}%{'':<5} "
                         f"{change['curr_retention']:.1f}%{'':<3} {var_str:<10} {rank_str}")

        if comparison.get("new_structures"):
            lines.append("")
            lines.append(f"Estruturas novas no ranking: {', '.join(comparison['new_structures'])}")

        lines.append("")

        # Narrativa de tendencias da LLM (após tabela comparativa)
        if tend_text:
            for line in tend_text.split("\n"):
                lines.append(line)
            lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)


# =============================================================================
# ETAPA 7: PERSISTENCIA
# =============================================================================

def save_analysis(
    channel_id: str,
    channel_name: str,
    analysis: Dict,
    comparison: Optional[Dict],
    report_text: str,
    total_no_match: int = 0,
    sat_analysis: Optional[Dict] = None,
    sat_comparison: Optional[Dict] = None
) -> Optional[int]:
    """Salva analise no banco (memoria acumulativa). Inclui dados de satisfacao se disponiveis."""
    ch_avg = analysis["channel_avg"]

    # Serializar videos (converter datetime para string)
    all_videos_serialized = []
    for v in analysis.get("all_videos", []):
        vc = dict(v)
        if isinstance(vc.get("published_at"), datetime):
            vc["published_at"] = vc["published_at"].isoformat()
        all_videos_serialized.append(vc)

    # Serializar comparison (sem o previous_report para nao duplicar dados)
    comparison_serialized = None
    if comparison:
        comparison_serialized = {
            "previous_date": comparison.get("previous_date"),
            "previous_avg": comparison.get("previous_avg"),
            "changes": comparison.get("changes", {}),
            "new_structures": comparison.get("new_structures", [])
        }

    results = {
        "structures": analysis["structures"],
        "insufficient": analysis["insufficient"],
        "channel_avg": ch_avg,
        "anomalies": analysis.get("anomalies", []),
        "comparison": comparison_serialized,
        "videos": all_videos_serialized
    }

    # Adicionar dados de satisfacao (Call 2) se disponiveis
    if sat_analysis and sat_analysis.get("structures"):
        # Serializar videos de satisfacao (converter datetime)
        sat_videos = []
        for v in sat_analysis.get("all_videos", []):
            vc = dict(v)
            if isinstance(vc.get("published_at"), datetime):
                vc["published_at"] = vc["published_at"].isoformat()
            sat_videos.append(vc)

        results["satisfaction_structures"] = sat_analysis["structures"]
        results["satisfaction_channel_avg"] = sat_analysis["channel_avg"]
        results["satisfaction_insufficient"] = sat_analysis.get("insufficient", {})
        results["satisfaction_anomalies"] = sat_analysis.get("anomalies", [])
        results["satisfaction_has_dislikes"] = sat_analysis.get("has_dislikes", False)
        results["satisfaction_has_subs"] = sat_analysis.get("has_subs", False)
        results["satisfaction_videos"] = sat_videos

        # Salvar comparacao de satisfacao (historico de mudancas)
        if sat_comparison:
            results["satisfaction_comparison"] = {
                "previous_date": sat_comparison.get("previous_date"),
                "changes": sat_comparison.get("changes", {}),
                "new_structures": sat_comparison.get("new_structures", [])
            }

    run_data = {
        "channel_id": channel_id,
        "channel_name": channel_name,
        "total_videos_analyzed": len(all_videos_serialized),
        "total_videos_excluded": analysis.get("excluded_immature", 0),
        "total_videos_no_match": total_no_match,
        "channel_avg_retention": ch_avg.get("retention"),
        "channel_avg_watch_time": ch_avg.get("watch_time"),
        "channel_avg_views": ch_avg.get("views"),
        "results_json": json.dumps(results),
        "report_text": report_text
    }

    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/copy_analysis_runs",
        headers=SUPABASE_HEADERS,
        json=run_data
    )

    if resp.status_code not in [200, 201]:
        logger.error(f"Erro ao salvar analise: {resp.status_code} - {resp.text[:200]}")
        return None

    run_id = resp.json()[0]["id"] if resp.json() else None

    if not run_id:
        logger.error("Run salva mas sem ID retornado")
        return None

    logger.info(f"Analise salva: run_id={run_id}, {len(all_videos_serialized)} videos")
    return run_id


# =============================================================================
# ETAPA 8: FUNCAO PRINCIPAL
# =============================================================================

def run_analysis(channel_id: str) -> Dict:
    """
    Executa analise completa de estrutura de copy para um canal.

    Args:
        channel_id: ID do canal YouTube (formato UC...)

    Returns:
        {
            "success": bool,
            "channel_id": str,
            "channel_name": str,
            "run_id": int,
            "report": str,
            "summary": {structures_analyzed, total_videos, channel_avg_retention},
            "error": str (se falhou)
        }
    """
    logger.info(f"{'='*50}")
    logger.info(f"ANALISE DE COPY: Iniciando para canal {channel_id}")
    logger.info(f"{'='*50}")

    # 1. Buscar dados do canal
    channel_info = _get_channel_info(channel_id)
    if not channel_info:
        return {"success": False, "error": f"Canal {channel_id} nao encontrado em yt_channels"}

    channel_name = channel_info.get("channel_name", channel_id)
    spreadsheet_id = channel_info.get("copy_spreadsheet_id")

    if not spreadsheet_id:
        return {"success": False, "error": f"Canal {channel_name} nao tem copy_spreadsheet_id configurado"}

    logger.info(f"Canal: {channel_name} | Planilha: {spreadsheet_id}")

    # 2. Ler planilha
    sheet_data = read_copy_structures(spreadsheet_id)
    if not sheet_data:
        return {"success": False, "error": f"Nenhum video com estrutura de copy na planilha"}

    # 3. Match videos
    matched = match_videos(channel_id, sheet_data)
    total_no_match = len(sheet_data) - len(matched)

    if not matched:
        return {"success": False, "error": f"Nenhum video da planilha encontrado no banco"}

    # 4. Buscar retencao
    video_ids = [v["video_id"] for v in matched if v.get("video_id")]
    retention_data = get_retention_data(channel_id, video_ids)

    if not retention_data:
        return {"success": False, "error": f"Sem dados de retencao disponiveis para este canal"}

    # 5. Analisar
    analysis = analyze_copy_performance(matched, retention_data)

    # 6. Comparar com anterior
    comparison = compare_with_previous(channel_id, analysis)

    # 6b. Gerar insights LLM (se OPENAI_API_KEY configurada)
    llm_insights = None
    if analysis.get("structures"):
        llm_insights = generate_llm_insights(channel_name, analysis, comparison)

    # 7. Gerar relatorio Call 1 (retencao)
    report = generate_report(channel_name, analysis, comparison, len(sheet_data), total_no_match, llm_insights)

    # =====================================================================
    # CALL 2: SATISFACAO DO PUBLICO
    # =====================================================================
    sat_analysis = None
    sat_comparison = None
    sat_report = ""

    logger.info(f"CALL 2 (Satisfacao): Buscando dados para {channel_name}...")

    # 8. Buscar dados de satisfacao (reutiliza video_ids do match)
    satisfaction_data = get_satisfaction_data(channel_id, video_ids)

    if satisfaction_data:
        # 9. Analisar satisfacao
        sat_analysis = analyze_satisfaction_performance(matched, satisfaction_data)

        if sat_analysis.get("structures"):
            # 10. Comparar satisfacao com anterior
            sat_comparison = compare_satisfaction_with_previous(channel_id, sat_analysis)

            # 11. LLM insights de satisfacao
            sat_llm_insights = generate_satisfaction_llm_insights(channel_name, sat_analysis, sat_comparison)

            # 12. Gerar relatorio de satisfacao
            sat_report = generate_satisfaction_report(channel_name, sat_analysis, sat_comparison, sat_llm_insights)

            logger.info(f"CALL 2 OK: {len(sat_analysis['structures'])} estruturas, "
                        f"{len(sat_analysis.get('all_videos', []))} videos")
        else:
            logger.warning(f"CALL 2: Sem estruturas suficientes para analise de satisfacao")
    else:
        logger.warning(f"CALL 2: Sem dados de satisfacao disponiveis para {channel_name}")

    # 13. Combinar relatorios (Call 1 + Call 2)
    combined_report = report
    if sat_report:
        combined_report = report + "\n" + sat_report

    # 14. Salvar tudo junto
    run_id = save_analysis(
        channel_id, channel_name, analysis, comparison,
        combined_report, total_no_match, sat_analysis, sat_comparison
    )

    logger.info(f"ANALISE COMPLETA: {channel_name} | run_id={run_id}")
    logger.info(f"  Structures: {len(analysis['structures'])} | "
                f"Videos: {len(analysis.get('all_videos', []))} | "
                f"Media retencao: {analysis['channel_avg']['retention']:.1f}%")
    if sat_analysis and sat_analysis.get("structures"):
        logger.info(f"  Satisfacao: {len(sat_analysis['structures'])} estruturas | "
                    f"Media approval: {sat_analysis['channel_avg']['approval']:.1f}%")

    summary = {
        "structures_analyzed": len(analysis["structures"]),
        "structures_insufficient": len(analysis["insufficient"]),
        "total_videos": len(analysis.get("all_videos", [])),
        "total_excluded": analysis.get("excluded_immature", 0),
        "total_no_match": total_no_match,
        "channel_avg_retention": analysis["channel_avg"]["retention"],
        "anomalies_count": len(analysis.get("anomalies", []))
    }

    if sat_analysis and sat_analysis.get("channel_avg"):
        summary["satisfaction_avg_approval"] = sat_analysis["channel_avg"]["approval"]
        summary["satisfaction_avg_sub_ratio"] = sat_analysis["channel_avg"]["sub_ratio"]

    return {
        "success": True,
        "channel_id": channel_id,
        "channel_name": channel_name,
        "run_id": run_id,
        "report": combined_report,
        "summary": summary
    }


def _get_channel_info(channel_id: str) -> Optional[Dict]:
    """Busca informacoes do canal em yt_channels"""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/yt_channels",
        params={
            "channel_id": f"eq.{channel_id}",
            "select": "channel_id,channel_name,copy_spreadsheet_id,subnicho,lingua,is_monetized"
        },
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    )
    if resp.status_code == 200 and resp.json():
        return resp.json()[0]
    return None


# =============================================================================
# FUNCOES DE CONSULTA (usadas pelos endpoints)
# =============================================================================

def get_latest_analysis(channel_id: str) -> Optional[Dict]:
    """Retorna a analise mais recente de um canal."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/copy_analysis_runs",
        params={
            "channel_id": f"eq.{channel_id}",
            "select": "*",
            "order": "run_date.desc",
            "limit": "1"
        },
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    )
    if resp.status_code == 200 and resp.json():
        row = resp.json()[0]
        # Parse JSONB fields
        if isinstance(row.get("results_json"), str):
            row["results_json"] = json.loads(row["results_json"])
        return row
    return None


def get_analysis_history(
    channel_id: str,
    limit: int = 20,
    offset: int = 0
) -> Dict:
    """
    Retorna historico de analises com paginacao.

    Returns:
        {
            "items": [...],
            "total": int,
            "limit": int,
            "offset": int,
            "has_more": bool
        }
    """
    # Contar total
    count_resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/copy_analysis_runs",
        params={
            "channel_id": f"eq.{channel_id}",
            "select": "id"
        },
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Prefer": "count=exact"
        }
    )
    total = 0
    if count_resp.status_code == 200:
        content_range = count_resp.headers.get("content-range", "")
        if "/" in content_range:
            try:
                total = int(content_range.split("/")[1])
            except (ValueError, IndexError):
                total = len(count_resp.json())
        else:
            total = len(count_resp.json())

    # Buscar pagina
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/copy_analysis_runs",
        params={
            "channel_id": f"eq.{channel_id}",
            "select": "id,channel_name,run_date,total_videos_analyzed,"
                      "channel_avg_retention,channel_avg_watch_time,channel_avg_views",
            "order": "run_date.desc",
            "limit": str(limit),
            "offset": str(offset)
        },
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    )

    items = resp.json() if resp.status_code == 200 else []

    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": (offset + limit) < total
    }


def get_video_mappings(
    run_id: int,
    limit: int = 50,
    offset: int = 0,
    structure_filter: Optional[str] = None
) -> Dict:
    """
    Retorna videos de uma analise com paginacao.
    Dados vem do results_json da copy_analysis_runs.
    """
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/copy_analysis_runs",
        params={
            "id": f"eq.{run_id}",
            "select": "results_json",
            "limit": "1"
        },
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    )

    if resp.status_code != 200 or not resp.json():
        return {"items": [], "total": 0, "limit": limit, "offset": offset, "has_more": False}

    results = resp.json()[0].get("results_json", {})
    if isinstance(results, str):
        results = json.loads(results)

    videos = results.get("videos", [])

    # Filtrar por estrutura
    if structure_filter and structure_filter.upper() in VALID_STRUCTURES:
        videos = [v for v in videos if v.get("structure") == structure_filter.upper()]

    # Ordenar por retencao (maior primeiro)
    videos.sort(key=lambda v: v.get("retention_pct") or 0, reverse=True)

    total = len(videos)
    items = videos[offset:offset + limit]

    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": (offset + limit) < total
    }


def get_all_channels_for_analysis() -> List[Dict]:
    """Retorna todos canais nosso com spreadsheet configurado."""
    all_channels = []
    page_size = 100
    offset = 0

    while True:
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/yt_channels",
            params={
                "is_active": "eq.true",
                "copy_spreadsheet_id": "not.is.null",
                "select": "channel_id,channel_name,subnicho,is_monetized,lingua",
                "order": "is_monetized.desc,channel_name.asc",
                "limit": str(page_size),
                "offset": str(offset)
            },
            headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        )

        if resp.status_code != 200:
            break

        rows = resp.json()
        if not rows:
            break

        all_channels.extend(rows)
        offset += page_size

        if len(rows) < page_size:
            break

    return all_channels

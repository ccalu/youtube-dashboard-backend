"""
Agente de Satisfacao do Publico
================================
Analisa o quanto a audiencia GOSTOU do conteudo, por estrutura de copy.
Complementar ao Agente de Copy (retencao).

Metricas: Like Approval Rate, Sub Ratio, Like Ratio, Comment Ratio.
Score composto: Sub Ratio 60% + Approval 40%.

Depende do Agente de Copy ter rodado antes (busca videos matched do ultimo run).
"""

import os
import json
import logging
import statistics
import requests
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# =============================================================================
# CONFIG
# =============================================================================

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY", "")
SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# =============================================================================
# CONSTANTS
# =============================================================================

MIN_MATURITY_DAYS = 7
MIN_SAMPLE_SIZE = 3
SATISFACTION_WEIGHT_SUB = 0.60
SATISFACTION_WEIGHT_APPROVAL = 0.40
ANOMALY_SATISFACTION_MULTIPLIER = 3.0


# =============================================================================
# INCREMENTAL: SNAPSHOT + DETECCAO DE VIDEOS NOVOS
# =============================================================================

def _get_previous_run(channel_id: str) -> Optional[Dict]:
    """Busca ultimo run com snapshot e run_number para deteccao incremental."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/satisfaction_analysis_runs",
        params={
            "channel_id": f"eq.{channel_id}",
            "select": "id,run_date,run_number,analyzed_video_data,report_text",
            "order": "run_date.desc",
            "limit": "1"
        },
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    )
    if resp.status_code != 200 or not resp.json():
        return None

    row = resp.json()[0]

    avd = row.get("analyzed_video_data")
    if isinstance(avd, str):
        try:
            avd = json.loads(avd)
        except (json.JSONDecodeError, TypeError):
            avd = {}
    if not isinstance(avd, dict):
        avd = {}

    return {
        "id": row.get("id"),
        "run_date": row.get("run_date", ""),
        "run_number": row.get("run_number", 1) or 1,
        "analyzed_video_data": avd,
        "report_text": row.get("report_text", ""),
    }


def _build_snapshot(all_videos: List[Dict]) -> Dict:
    """Constroi snapshot JSONB dos videos analisados para deteccao incremental."""
    snapshot = {}
    for v in all_videos:
        vid = v.get("video_id")
        if vid:
            snapshot[vid] = {
                "views": v.get("views", 0),
                "likes": v.get("likes", 0),
                "approval": v.get("approval"),
                "sub_ratio": v.get("sub_ratio", 0),
                "structure": v.get("structure", ""),
            }
    return snapshot


def _get_new_video_ids(all_videos: List[Dict], previous_snapshot: Dict) -> set:
    """Retorna set de video_ids que sao novos (nao existiam no snapshot anterior)."""
    if not previous_snapshot:
        return {v["video_id"] for v in all_videos if v.get("video_id")}
    return {v["video_id"] for v in all_videos if v.get("video_id") and v["video_id"] not in previous_snapshot}


# =============================================================================
# BUSCAR VIDEOS MATCHED DO COPY
# =============================================================================

def _get_matched_videos_from_copy(channel_id: str) -> Optional[List[Dict]]:
    """
    Busca videos matched do ultimo copy analysis run.
    O agente de copy faz o match titulo→estrutura. Nos reutilizamos.

    Returns:
        Lista de videos com: video_id, structure, title, published_at, views
        None se nao existe copy run para esse canal
    """
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/copy_analysis_runs",
        params={
            "channel_id": f"eq.{channel_id}",
            "select": "results_json",
            "order": "created_at.desc",
            "limit": "1"
        },
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    )

    if resp.status_code != 200 or not resp.json():
        return None

    row = resp.json()[0]
    results = row.get("results_json") or {}
    if isinstance(results, str):
        results = json.loads(results)

    videos = results.get("videos", [])
    if not videos:
        return None

    # Garantir campos necessarios
    matched = []
    for v in videos:
        if v.get("video_id") and v.get("structure"):
            matched.append({
                "video_id": v["video_id"],
                "structure": v["structure"],
                "title": v.get("title", ""),
                "published_at": v.get("published_at"),
                "views": v.get("views") or 0,
            })

    return matched if matched else None


def _get_channel_info(channel_id: str) -> Optional[Dict]:
    """Busca info basica do canal."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/yt_channels",
        params={
            "channel_id": f"eq.{channel_id}",
            "select": "channel_id,channel_name"
        },
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    )
    if resp.status_code == 200 and resp.json():
        return resp.json()[0]
    return None


# =============================================================================
# OAUTH (para fallback API)
# =============================================================================

def _get_oauth_tokens(channel_id: str) -> Optional[Dict]:
    """Busca tokens OAuth do canal."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/yt_oauth_tokens",
        params={"channel_id": f"eq.{channel_id}", "select": "refresh_token,access_token"},
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    )
    if resp.status_code == 200 and resp.json():
        return resp.json()[0]
    return None


def _get_credentials(channel_id: str) -> Optional[Dict]:
    """Busca credenciais OAuth (isoladas primeiro, proxy como fallback)."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/yt_channel_credentials",
        params={"channel_id": f"eq.{channel_id}", "select": "client_id,client_secret"},
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    )
    if resp.status_code == 200 and resp.json():
        return resp.json()[0]

    # Fallback: proxy credentials
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
    """Renova access_token via OAuth refresh."""
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
# RESOLVER canal_id NUMERICO
# =============================================================================

def _resolve_canal_id(video_ids: List[str]) -> Optional[int]:
    """
    Resolve o canal_id numerico (FK de canais_monitorados) a partir de um video_id.
    videos_historico usa canal_id INTEGER, nao channel_id string.
    """
    if not video_ids:
        return None
    # Tentar com o primeiro video_id
    for vid in video_ids[:3]:
        try:
            resp = requests.get(
                f"{SUPABASE_URL}/rest/v1/videos_historico",
                params={
                    "video_id": f"eq.{vid}",
                    "select": "canal_id",
                    "limit": "1"
                },
                headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
            )
            if resp.status_code == 200 and resp.json():
                canal_id = resp.json()[0].get("canal_id")
                if canal_id:
                    logger.debug(f"Resolved canal_id={canal_id} from video_id={vid}")
                    return canal_id
        except Exception as e:
            logger.warning(f"Erro ao resolver canal_id via video_id={vid}: {e}")
    logger.warning(f"Nao foi possivel resolver canal_id para nenhum dos {len(video_ids)} videos")
    return None


# =============================================================================
# BUSCAR DADOS DE SATISFACAO
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

    # 1. Buscar de yt_video_metrics (fonte primaria)
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
                views = row.get("views") or 0
                if vid and vid not in result and (likes > 0 or views > 0):
                    result[vid] = {
                        "likes": likes,
                        "dislikes": row.get("dislikes") or 0,
                        "subscribers_gained": row.get("subscribers_gained") or 0,
                        "views": views,
                        "source": "yt_video_metrics"
                    }

    # 2. Buscar comments de videos_historico (para TODOS os videos)
    # videos_historico usa canal_id INTEGER (FK canais_monitorados), nao channel_id string
    canal_id_int = _resolve_canal_id(video_ids)
    if not canal_id_int:
        logger.warning(f"Canal {channel_id}: nao foi possivel resolver canal_id numerico, pulando videos_historico")

    if canal_id_int:
        for i in range(0, len(video_ids), batch_size):
            batch = video_ids[i:i + batch_size]
            ids_str = ",".join(batch)
            resp = requests.get(
                f"{SUPABASE_URL}/rest/v1/videos_historico",
                params={
                    "canal_id": f"eq.{canal_id_int}",
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
                            result[vid]["comments"] = comments
                        else:
                            likes = row.get("likes") or 0
                            views_h = row.get("views_atuais") or 0
                            if likes > 0 or views_h > 0:
                                result[vid] = {
                                    "likes": likes,
                                    "dislikes": 0,
                                    "subscribers_gained": 0,
                                    "comments": comments,
                                    "views": views_h,
                                    "source": "videos_historico_partial"
                                }

    # Garantir campo 'comments' em todos
    for vid in result:
        if "comments" not in result[vid]:
            result[vid]["comments"] = 0

    # 3. Fallback API
    still_missing = [vid for vid in video_ids if vid not in result]
    if still_missing:
        logger.info(f"Canal {channel_id}: {len(still_missing)} videos sem dados de satisfacao, tentando API...")
        api_data = _fetch_satisfaction_from_api(channel_id, still_missing)
        result.update(api_data)

    logger.info(f"Canal {channel_id}: satisfacao obtida para {len(result)}/{len(video_ids)} videos")
    return result


def _fetch_satisfaction_from_api(channel_id: str, video_ids: List[str]) -> Dict[str, Dict]:
    """Busca likes, dislikes, subscribersGained da YouTube Analytics API via OAuth."""
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
                "comments": 0,
                "source": "analytics_api"
            }

    logger.info(f"YouTube Analytics API (satisfacao): {len(result)} videos de {len(all_rows)} total")
    return result


# =============================================================================
# ENGINE DE ANALISE
# =============================================================================

def analyze_satisfaction_performance(
    matched_videos: List[Dict],
    satisfaction_data: Dict[str, Dict]
) -> Dict:
    """
    Agrupa videos por estrutura e calcula metricas de satisfacao.
    Score composto: Sub Ratio 60% + Approval 40% (sem sentimento).

    Returns:
        {
            "channel_avg": {approval, like_ratio, sub_ratio, comment_ratio},
            "structures": {A: {score, avg_approval, ...}, ...},
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
            continue

        if dislikes > 0:
            has_dislikes_global = True
        if subs_gained > 0:
            has_subs_global = True

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
                    "video_id": v["video_id"],
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

        # Desvio % vs media do canal
        approval_dev = ((avg_approval - channel_avg["approval"]) / channel_avg["approval"] * 100) if channel_avg["approval"] > 0 else 0
        sub_ratio_dev = ((avg_sub_ratio - channel_avg["sub_ratio"]) / channel_avg["sub_ratio"] * 100) if channel_avg["sub_ratio"] > 0 else 0
        comment_ratio_dev = ((avg_comment_ratio - channel_avg["comment_ratio"]) / channel_avg["comment_ratio"] * 100) if channel_avg["comment_ratio"] > 0 else 0

        # Score composto 0-100 (50 = media do canal)
        approval_score = max(0, min(100, 50 + (approval_dev * 0.5)))
        sub_score = max(0, min(100, 50 + (sub_ratio_dev * 0.5)))

        if has_subs_global:
            score = round(sub_score * SATISFACTION_WEIGHT_SUB + approval_score * SATISFACTION_WEIGHT_APPROVAL)
        else:
            score = round(approval_score)

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

        # Anomalias
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
                    reasons.append(f"Sub Ratio 0% — nenhum inscrito ganho (media da estrutura: {avg_sub_ratio:.4f}%)")

            if avg_approval > 0 and v["approval"] is not None:
                diff = abs(v["approval"] - avg_approval)
                if diff > 15:
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
# COMPARACAO TEMPORAL
# =============================================================================

def compare_with_previous(channel_id: str, current_results: Dict) -> Optional[Dict]:
    """Busca dados de satisfacao da analise anterior para comparacao temporal."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/satisfaction_analysis_runs",
        params={
            "channel_id": f"eq.{channel_id}",
            "select": "run_date,results_json",
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

    prev_structures = prev_results.get("structures", {})
    if not prev_structures:
        return None

    prev_date = prev.get("run_date", "")
    curr_structures = current_results.get("structures", {})

    # Rankings
    prev_ranking = sorted(prev_structures.items(), key=lambda x: x[1].get("score", 0), reverse=True)
    curr_ranking = sorted(curr_structures.items(), key=lambda x: x[1].get("score", 0), reverse=True)

    prev_rank_map = {s: i+1 for i, (s, _) in enumerate(prev_ranking)}
    curr_rank_map = {s: i+1 for i, (s, _) in enumerate(curr_ranking)}

    changes = {}
    new_structures = []

    for structure, data in curr_structures.items():
        if structure in prev_structures:
            prev_score = prev_structures[structure].get("score", 0)
            curr_score = data["score"]
            prev_rank = prev_rank_map.get(structure, 0)
            curr_rank = curr_rank_map.get(structure, 0)

            changes[structure] = {
                "prev_score": prev_score,
                "curr_score": curr_score,
                "diff": curr_score - prev_score,
                "prev_approval": prev_structures[structure].get("avg_approval", 0),
                "curr_approval": data["avg_approval"],
                "prev_sub_ratio": prev_structures[structure].get("avg_sub_ratio", 0),
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
# LLM INSIGHTS
# =============================================================================

def generate_llm_insights(
    channel_name: str,
    sat_analysis: Dict,
    sat_comparison: Optional[Dict],
    new_video_ids: Optional[set] = None,
    run_number: int = 1,
    is_first_run: bool = True,
    previous_report: Optional[str] = None
) -> Optional[Dict]:
    """LLM: analise narrativa de satisfacao do publico.

    Incremental: a partir do run #2, recebe apenas videos NOVOS no data_block,
    mas as medias gerais incluem TODOS os videos. O relatorio anterior e passado
    como contexto para a LLM comparar evolucao.
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

        # Incremental: filtrar apenas videos novos no data_block (run #2+)
        is_incremental = not is_first_run and new_video_ids and len(new_video_ids) > 0
        filter_new = is_incremental

        data_block = f"CANAL: {channel_name}\n"
        data_block += f"Total videos no canal (satisfacao): {len(all_videos)}\n"
        if filter_new:
            data_block += f"Videos NOVOS nesta analise: {len(new_video_ids)}\n"
        data_block += f"Media geral do canal (TODOS os videos): {ch_avg['approval']:.1f}% approval | {ch_avg['like_ratio']:.4f}% like ratio | {ch_avg['sub_ratio']:.4f}% sub ratio | {ch_avg.get('comment_ratio', 0):.4f}% comment ratio\n"
        data_block += f"Dados de dislikes disponiveis: {'Sim' if has_dislikes else 'Nao (approval calculado apenas com likes)'}\n"
        data_block += f"Dados de inscritos ganhos por video: {'Sim' if has_subs else 'Nao'}\n\n"

        if filter_new:
            data_block += "DADOS POR ESTRUTURA (apenas videos NOVOS, medias incluem TODOS):\n\n"
        else:
            data_block += "DADOS POR ESTRUTURA (cada video individual):\n\n"
        for s, d in structures.items():
            videos_in_struct = d.get("videos", [])
            if filter_new:
                videos_to_show = [v for v in videos_in_struct if v.get("video_id") in new_video_ids]
            else:
                videos_to_show = videos_in_struct
            # Pular estruturas sem videos novos no modo incremental
            if filter_new and not videos_to_show:
                data_block += f"Estrutura {s} ({d['count']} videos total) — Score: {d['score']}/100 — sem videos novos\n"
                data_block += f"  Media (TODOS): {d['avg_approval']:.1f}% approval | {d['avg_sub_ratio']:.4f}% sub_ratio\n\n"
                continue
            new_label = f", {len(videos_to_show)} novos" if filter_new else ""
            data_block += f"Estrutura {s} ({d['count']} videos total{new_label}) — Score: {d['score']}/100 — Status: {d['status']}\n"
            for v in videos_to_show:
                approval_str = f"{v.get('approval', 0):.1f}%" if v.get('approval') is not None else "N/A"
                data_block += f"  - \"{v['title']}\" | approval: {approval_str} | like_ratio: {v.get('like_ratio', 0):.4f}% | sub_ratio: {v.get('sub_ratio', 0):.4f}% | comment_ratio: {v.get('comment_ratio', 0):.4f}% | comments: {v.get('comments', 0)} | likes: {v.get('likes', 0)} | dislikes: {v.get('dislikes', 0)} | subs_gained: {v.get('subscribers_gained', 0)} | views: {v.get('views', 0):,}\n"
            data_block += f"  Media (TODOS): {d['avg_approval']:.1f}% approval | {d['avg_like_ratio']:.4f}% like_ratio | {d['avg_sub_ratio']:.4f}% sub_ratio | {d.get('avg_comment_ratio', 0):.4f}% comment_ratio | {d.get('avg_comments', 0)} coment. medio\n"
            data_block += f"  Desvio vs canal: {d['approval_dev']:+.1f}% approval | {d['sub_ratio_dev']:+.1f}% sub_ratio | {d.get('comment_ratio_dev', 0):+.1f}% comment_ratio\n\n"

        if insufficient:
            data_block += "ESTRUTURAS COM POUCOS DADOS (<3 videos):\n"
            for s, d in insufficient.items():
                data_block += f"  Estrutura {s}: {d['count']} video(s)\n"
                for v in d.get("videos", []):
                    if filter_new and v.get("video_id") not in new_video_ids:
                        continue
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
        # PROMPT LLM SATISFACAO
        # =====================================================================

        system_prompt = """Voce e um analista senior de satisfacao de audiencia para canais YouTube.
Voce analisa dados PRE-CALCULADOS por um sistema Python e produz insights narrativos
sobre o quanto a audiencia GOSTOU do conteudo — complementar a analise de retencao.

=== CONTEXTO: RETENCAO vs SATISFACAO ===

O Agente de Copy ja analisa RETENCAO: quanto tempo o espectador ficou no video.
Voce analisa SATISFACAO: o espectador gostou de ter ficado?

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
   - Approval baixo (<85%) e um sinal forte de problema

2. LIKE RATIO = likes / views (INFORMATIVO)
   - Que % dos espectadores deu like?
   - Complementar — indica engajamento geral
   - NAO entra no score composto (evita redundancia com approval)
   - Use para contexto: "estrutura X tem approval similar mas like ratio 2x maior"

3. SUB RATIO = inscritos ganhos / views
   - Sinal MAIS FORTE de satisfacao (maior commitment do espectador)
   - Um espectador que se inscreve esta dizendo: "quero mais disso"
   - Pesa 60% no score composto
   - Se nao ha dados de inscritos por video, esta metrica nao esta disponivel

4. COMMENT RATIO = comentarios / views (INFORMATIVO)
   - Engajamento ativo — espectador motivado a comentar
   - Alto + approval alto = audiencia engajada E satisfeita
   - Alto + approval baixo = audiencia engajada mas polarizada
   - NAO entra no score composto

5. SCORE COMPOSTO (0-100)
   - 50 = media do canal. >50 = acima. <50 = abaixo
   - Pesos: Sub Ratio 60% + Approval 40% (sem sentimento de comentarios)
   - O score e relativo ao PROPRIO canal — NAO compare entre canais

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

        # Montar bloco de memoria acumulativa (relatorio anterior)
        previous_report_block = ""
        prev_report_text = previous_report if previous_report else None
        if prev_report_text:
            prev_date = sat_comparison.get("previous_date", "") if sat_comparison else ""
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
{prev_report_text}
FIM DO RELATORIO ANTERIOR.
"""

        # Montar bloco de contexto incremental (run #2+)
        incremental_block = ""
        if is_incremental:
            incremental_block = f"""
=== ANALISE INCREMENTAL (Run #{run_number}) ===

Este canal ja foi analisado anteriormente. Voce esta recebendo:
- DADOS: apenas dos {len(new_video_ids)} videos NOVOS (nao analisados antes)
- MEDIAS GERAIS: de TODOS os videos do canal (novos + anteriores)
- RELATORIO ANTERIOR: sua analise completa da ultima vez

Sua analise DEVE cobrir adicionalmente:

1. IMPACTO DOS NOVOS VIDEOS NAS ESTRUTURAS
   - Para cada estrutura que recebeu videos novos: o score subiu ou caiu?
   - Approval mudou? Sub ratio mudou? Comment ratio mudou?
   - O video novo puxou a estrutura pra cima ou pra baixo em satisfacao?

2. EVOLUCAO DO RANKING DE SATISFACAO
   - Alguma estrutura mudou de posicao no ranking por causa dos novos videos?
   - Alguma estrutura mudou de status (score passou de <50 para >50 ou vice-versa)?
   - Movimentos significativos merecem destaque

3. CONFIRMACAO OU REVERSAO DE TENDENCIAS
   - Tendencias do relatorio anterior que se CONFIRMAM com os novos dados
   - Tendencias que se REVERTEM (ex: estrutura com approval caindo que voltou a subir)
   - Padroes novos que surgem pela primeira vez

4. CONSISTENCIA DE SATISFACAO ATUALIZADA
   - Alguma estrutura tinha approval consistente e agora variou?
   - Sub ratio de alguma estrutura mudou significativamente?
   - Videos novos com comment ratio muito diferente do padrao da estrutura?

5. SINAIS DE ATENCAO
   - Videos novos com approval muito abaixo da media da estrutura
   - Videos novos com sub ratio excepcional (conversao alta de inscritos)
   - Divergencias: approval alto mas sub ratio baixo (ou vice-versa) nos novos videos
   - Estruturas que receberam muitos videos novos vs poucas que ficaram estagnadas
"""

        user_prompt = f"""{previous_report_block}
{incremental_block}
Produza EXATAMENTE 2 blocos:

[OBSERVACOES]
Analise de satisfacao DESTA SEMANA. Cubra obrigatoriamente TODOS os pontos:

1. LIDERANCA DE SATISFACAO: Qual estrutura lidera em score? Com que margem?
   Cite approval, like ratio e sub ratio da lider. E consistente entre videos?

2. APPROVAL POR ESTRUTURA: Para CADA estrutura, cite o approval e desvio vs canal.
   Se alguma esta abaixo de 85%, destaque como sinal forte de insatisfacao.
   Se todas estao acima de 95%, note que as diferencas sao sutis mas ainda informativas.

3. SUB RATIO (se disponivel): Para CADA estrutura, cite o sub ratio.
   Qual estrutura CONVERTE mais espectadores em inscritos?
   Destaque a diferenca entre a melhor e a pior em termos relativos.

4. LIKE RATIO (informativo): Padroes notaveis no like ratio entre estruturas.
   Se uma tem approval similar mas like ratio muito diferente, destaque.

5. COMMENT RATIO (informativo): Padroes de engajamento via comentarios.
   Se uma estrutura gera muito mais comentarios que outra com approval similar, destaque.

6. PIOR DESEMPENHO: Qual estrutura tem a pior satisfacao? Score, approval, sub ratio.
   O que os numeros mostram (sem teorizar POR QUE)?

7. ANOMALIAS: Videos com metricas muito acima ou abaixo da media da estrutura.
   Reporte como fato.

8. LIMITACOES DOS DADOS: Se faltam dislikes ou inscritos, mencione o impacto.
   Se a fonte e parcial (videos_historico sem dislikes), note.

9. OUTROS PADROES: Qualquer insight relevante nos dados.

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
# GERADOR DE RELATORIO
# =============================================================================

def generate_report(
    channel_name: str,
    sat_analysis: Dict,
    sat_comparison: Optional[Dict],
    llm_insights: Optional[Dict] = None,
    run_number: int = 1,
    new_count: int = -1
) -> str:
    """Gera relatorio formatado de satisfacao."""
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

    # === BANNER INCREMENTAL ===
    if run_number > 1 and new_count == 0:
        lines.append(f">> Run #{run_number} -- Nenhum video novo detectado desde a ultima analise.")
        lines.append(">> Relatorio anterior reutilizado. Proxima analise com dados novos gerara atualizacao completa.")
        lines.append("")
    elif run_number > 1 and new_count > 0:
        lines.append(f">> Run #{run_number} -- {new_count} video(s) novo(s) detectado(s) (de {len(all_videos)} total). Analise focada nos novos.")
        lines.append("")

    # === HEADER ===
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
        lines.append(f"Score: Sub Ratio {SATISFACTION_WEIGHT_SUB*100:.0f}% + Approval {SATISFACTION_WEIGHT_APPROVAL*100:.0f}%")
    lines.append("")

    # === RANKING ===
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

        lines.append(f"--- vs. ANALISE ANTERIOR ({prev_date}) ---")
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
            lines.append("--- TENDENCIAS ---")
            lines.append("")
            for line in tend_text.split("\n"):
                lines.append(line)
            lines.append("")

    elif tend_text:
        # Primeira analise (sem comparison) — mostrar tendencias mesmo assim
        lines.append("--- TENDENCIAS ---")
        lines.append("")
        for line in tend_text.split("\n"):
            lines.append(line)
        lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)


# =============================================================================
# PERSISTENCIA
# =============================================================================

def save_analysis(
    channel_id: str,
    channel_name: str,
    sat_analysis: Dict,
    sat_comparison: Optional[Dict],
    report_text: str,
    run_number: int = 1,
    snapshot: Optional[Dict] = None
) -> Optional[int]:
    """Salva analise no banco."""
    ch_avg = sat_analysis["channel_avg"]

    # Serializar videos (converter datetime para string)
    all_videos_serialized = []
    for v in sat_analysis.get("all_videos", []):
        vc = dict(v)
        if isinstance(vc.get("published_at"), datetime):
            vc["published_at"] = vc["published_at"].isoformat()
        all_videos_serialized.append(vc)

    results = {
        "structures": sat_analysis["structures"],
        "insufficient": sat_analysis["insufficient"],
        "channel_avg": ch_avg,
        "anomalies": sat_analysis.get("anomalies", []),
        "videos": all_videos_serialized,
        "has_dislikes": sat_analysis.get("has_dislikes", False),
        "has_subs": sat_analysis.get("has_subs", False),
        "excluded_immature": sat_analysis.get("excluded_immature", 0)
    }

    if sat_comparison:
        results["comparison"] = {
            "previous_date": sat_comparison.get("previous_date"),
            "changes": sat_comparison.get("changes", {}),
            "new_structures": sat_comparison.get("new_structures", [])
        }

    payload = {
        "channel_id": channel_id,
        "channel_name": channel_name,
        "total_videos_analyzed": len(all_videos_serialized),
        "total_videos_excluded": sat_analysis.get("excluded_immature", 0),
        "channel_avg_approval": ch_avg.get("approval"),
        "channel_avg_sub_ratio": ch_avg.get("sub_ratio"),
        "channel_avg_comment_ratio": ch_avg.get("comment_ratio"),
        "results_json": json.dumps(results, ensure_ascii=False),
        "report_text": report_text,
        "run_number": run_number,
        "analyzed_video_data": json.dumps(snapshot, ensure_ascii=False) if snapshot else None
    }

    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/satisfaction_analysis_runs",
        json=payload,
        headers=SUPABASE_HEADERS
    )

    if resp.status_code in (200, 201):
        rows = resp.json()
        run_id = rows[0].get("id") if rows else None
        logger.info(f"Satisfacao salva: run_id={run_id}, {len(all_videos_serialized)} videos")
        return run_id
    else:
        logger.error(f"Erro ao salvar satisfacao: {resp.status_code} - {resp.text[:300]}")
        return None


def get_latest_analysis(channel_id: str) -> Optional[Dict]:
    """Retorna analise mais recente."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/satisfaction_analysis_runs",
        params={
            "channel_id": f"eq.{channel_id}",
            "select": "*",
            "order": "run_date.desc",
            "limit": 1
        },
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    )
    if resp.status_code != 200 or not resp.json():
        return None

    row = resp.json()[0]
    val = row.get("results_json")
    if isinstance(val, str):
        try:
            row["results_json"] = json.loads(val)
        except (json.JSONDecodeError, TypeError):
            pass
    return row


def get_analysis_history(channel_id: str, limit: int = 20, offset: int = 0) -> Dict:
    """Retorna historico paginado."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/satisfaction_analysis_runs",
        params={
            "channel_id": f"eq.{channel_id}",
            "select": "id,channel_id,channel_name,run_date,total_videos_analyzed,channel_avg_approval,channel_avg_sub_ratio",
            "order": "run_date.desc",
            "limit": min(limit, 100),
            "offset": offset
        },
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Prefer": "count=exact"
        }
    )

    total = 0
    if "content-range" in resp.headers:
        try:
            total = int(resp.headers["content-range"].split("/")[-1])
        except (ValueError, IndexError):
            pass

    rows = resp.json() if resp.status_code == 200 else []
    return {"runs": rows, "total": total, "limit": limit, "offset": offset}


def delete_analysis(channel_id: str, run_id: int) -> Dict:
    """Deleta um run especifico."""
    resp = requests.delete(
        f"{SUPABASE_URL}/rest/v1/satisfaction_analysis_runs",
        params={
            "id": f"eq.{run_id}",
            "channel_id": f"eq.{channel_id}"
        },
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}"
        }
    )

    if resp.status_code in (200, 204):
        logger.info(f"Satisfacao deletada: channel={channel_id}, run_id={run_id}")
        return {"success": True, "message": f"Run {run_id} deletado"}
    else:
        logger.error(f"Erro ao deletar: {resp.status_code} - {resp.text[:200]}")
        return {"success": False, "error": resp.text[:200]}


def get_all_channels_for_analysis() -> List[Dict]:
    """Retorna canais que tem copy analysis run (prerequisito)."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/yt_channels",
        params={
            "tipo": "eq.nosso",
            "copy_spreadsheet_id": "not.is.null",
            "select": "channel_id,channel_name"
        },
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    )
    if resp.status_code == 200:
        return resp.json()
    return []


# =============================================================================
# ORQUESTRACAO PRINCIPAL
# =============================================================================

def run_analysis(channel_id: str) -> Dict:
    """
    Executa analise completa de satisfacao para um canal.

    Fluxo:
    1. Busca info do canal
    2. Busca videos matched do ultimo copy run
    3. Busca dados de satisfacao (likes/dislikes/subs/comments)
    4. Analisa por estrutura
    5. Compara com analise anterior
    6. LLM insights
    7. Gera relatorio
    8. Salva no banco
    """
    logger.info(f"{'='*50}")
    logger.info(f"ANALISE SATISFACAO: Iniciando para canal {channel_id}")
    logger.info(f"{'='*50}")

    # 1. Info do canal
    channel_info = _get_channel_info(channel_id)
    if not channel_info:
        return {"success": False, "error": f"Canal {channel_id} nao encontrado em yt_channels"}

    channel_name = channel_info.get("channel_name", channel_id)

    # 2. Buscar videos matched do copy
    matched_videos = _get_matched_videos_from_copy(channel_id)
    if not matched_videos:
        return {"success": False, "error": f"Canal {channel_name} nao tem analise de copy. Execute a analise de copy primeiro."}

    logger.info(f"Canal: {channel_name} | {len(matched_videos)} videos matched do copy")

    # 3. Buscar dados de satisfacao
    video_ids = [v["video_id"] for v in matched_videos]
    satisfaction_data = get_satisfaction_data(channel_id, video_ids)

    if not satisfaction_data:
        return {"success": False, "error": f"Sem dados de satisfacao disponiveis para {channel_name}"}

    # 4. Analisar
    sat_analysis = analyze_satisfaction_performance(matched_videos, satisfaction_data)

    if not sat_analysis.get("structures"):
        return {
            "success": False,
            "error": f"Sem estruturas suficientes para analise (min {MIN_SAMPLE_SIZE} videos por estrutura)",
            "excluded_immature": sat_analysis.get("excluded_immature", 0)
        }

    # 4b. Deteccao incremental
    prev_run = _get_previous_run(channel_id)
    is_first = prev_run is None
    run_number = 1 if is_first else prev_run["run_number"] + 1
    all_videos = sat_analysis.get("all_videos", [])
    snapshot = _build_snapshot(all_videos)
    new_ids = _get_new_video_ids(all_videos, prev_run["analyzed_video_data"] if prev_run else {})
    new_count = len(new_ids)

    logger.info(f"Canal {channel_name}: run #{run_number} | {len(all_videos)} videos | {new_count} novos")

    # 5. Comparar com anterior
    sat_comparison = compare_with_previous(channel_id, sat_analysis)

    # 6. LLM insights
    llm_insights = None
    if new_count == 0 and not is_first and prev_run.get("report_text"):
        # Zero videos novos — reutilizar LLM anterior
        logger.info(f"Canal {channel_name}: zero videos novos — reutilizando LLM anterior")
        prev_report = prev_run["report_text"]
        llm_insights = {"observacoes": "", "tendencias": ""}
        if "--- OBSERVACOES (Satisfacao) ---" in prev_report:
            parts = prev_report.split("--- OBSERVACOES (Satisfacao) ---")
            if len(parts) > 1:
                obs_block = parts[1]
                if "---" in obs_block:
                    obs_block = obs_block.split("---")[0]
                llm_insights["observacoes"] = obs_block.strip()
        if "--- TENDENCIAS ---" in prev_report:
            parts = prev_report.split("--- TENDENCIAS ---")
            if len(parts) > 1:
                tend_block = parts[1]
                if "---" in tend_block:
                    tend_block = tend_block.split("---")[0]
                llm_insights["tendencias"] = tend_block.strip()
        if not llm_insights["observacoes"]:
            llm_insights = generate_llm_insights(
                channel_name, sat_analysis, sat_comparison,
                new_video_ids=new_ids, run_number=run_number,
                is_first_run=is_first, previous_report=prev_run.get("report_text") if prev_run else None
            )
    else:
        llm_insights = generate_llm_insights(
            channel_name, sat_analysis, sat_comparison,
            new_video_ids=new_ids, run_number=run_number,
            is_first_run=is_first, previous_report=prev_run.get("report_text") if prev_run else None
        )

    # 7. Gerar relatorio
    report = generate_report(channel_name, sat_analysis, sat_comparison, llm_insights,
                             run_number=run_number, new_count=new_count)

    # 8. Salvar
    run_id = save_analysis(
        channel_id, channel_name, sat_analysis, sat_comparison, report,
        run_number=run_number, snapshot=snapshot
    )

    logger.info(f"SATISFACAO COMPLETA: {channel_name} | run #{run_number} | run_id={run_id}")
    logger.info(f"  Estruturas: {len(sat_analysis['structures'])} | "
                f"Videos: {len(all_videos)} | {new_count} novos | "
                f"Media approval: {sat_analysis['channel_avg']['approval']:.1f}%")

    summary = {
        "structures_analyzed": len(sat_analysis["structures"]),
        "structures_insufficient": len(sat_analysis["insufficient"]),
        "total_videos": len(all_videos),
        "total_excluded": sat_analysis.get("excluded_immature", 0),
        "channel_avg_approval": sat_analysis["channel_avg"]["approval"],
        "channel_avg_sub_ratio": sat_analysis["channel_avg"]["sub_ratio"],
        "anomalies_count": len(sat_analysis.get("anomalies", [])),
        "new_videos": new_count
    }

    return {
        "success": True,
        "channel_id": channel_id,
        "channel_name": channel_name,
        "run_id": run_id,
        "run_number": run_number,
        "new_videos": new_count,
        "report": report,
        "summary": summary
    }

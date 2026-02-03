"""
TREND MONITOR - Quality Filters & Universal Scoring
====================================================
Sistema de filtragem de qualidade e scoring universal (0-100) para todas as fontes.

FUNCOES PRINCIPAIS:
- filter_youtube(): Filtra videos por duracao, views, engagement, categorias
- filter_google_trends(): Filtra trends por volume e keywords
- filter_hackernews(): Filtra stories por score, comentarios, dominios
- calculate_quality_score(): Score universal 0-100 para qualquer fonte
- matches_subnicho(): Verifica se item combina com um subnicho
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import QUALITY_FILTERS, SUBNICHO_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# FILTROS POR FONTE
# =============================================================================

def filter_youtube(videos: List[Dict]) -> Tuple[List[Dict], int]:
    """
    Filtra videos do YouTube por qualidade.

    Args:
        videos: Lista de videos do YouTube

    Returns:
        Tuple: (lista filtrada, quantidade removida)
    """
    filters = QUALITY_FILTERS.get("youtube", {})

    min_duration = filters.get("min_duration", 180)
    max_duration = filters.get("max_duration", 3600)
    min_views = filters.get("min_views", 10000)
    min_engagement = filters.get("min_engagement", 0.02)
    exclude_categories = filters.get("exclude_categories", [])
    exclude_keywords = [k.lower() for k in filters.get("exclude_keywords", [])]

    filtered = []
    removed = 0

    for video in videos:
        # Filtro: duracao
        duration = video.get("duration_seconds", 0)
        if duration < min_duration or duration > max_duration:
            removed += 1
            continue

        # Filtro: views minimas
        views = video.get("view_count", 0)
        if views < min_views:
            removed += 1
            continue

        # Filtro: engagement minimo
        likes = video.get("like_count", 0)
        engagement = likes / max(views, 1)
        if engagement < min_engagement:
            removed += 1
            continue

        # Filtro: categorias excluidas
        category = video.get("category_id", "")
        if category in exclude_categories:
            removed += 1
            continue

        # Filtro: keywords excluidas no titulo
        title = video.get("title", "").lower()
        if any(kw in title for kw in exclude_keywords):
            removed += 1
            continue

        filtered.append(video)

    logger.info(f"YouTube Filter: {len(filtered)} mantidos, {removed} removidos")
    return filtered, removed


def filter_google_trends(trends: List[Dict]) -> Tuple[List[Dict], int]:
    """
    Filtra trends do Google Trends por qualidade.

    Args:
        trends: Lista de trends

    Returns:
        Tuple: (lista filtrada, quantidade removida)
    """
    filters = QUALITY_FILTERS.get("google_trends", {})

    min_volume = filters.get("min_volume", 10000)
    exclude_keywords = [k.lower() for k in filters.get("exclude_keywords", [])]

    filtered = []
    removed = 0

    for trend in trends:
        # Filtro: volume minimo
        volume = trend.get("volume", 0)
        if volume < min_volume:
            removed += 1
            continue

        # Filtro: keywords excluidas
        title = trend.get("title", "").lower()
        if any(kw in title for kw in exclude_keywords):
            removed += 1
            continue

        filtered.append(trend)

    logger.info(f"Google Trends Filter: {len(filtered)} mantidos, {removed} removidos")
    return filtered, removed


def filter_hackernews(stories: List[Dict]) -> Tuple[List[Dict], int]:
    """
    Filtra stories do Hacker News por qualidade.

    Args:
        stories: Lista de stories

    Returns:
        Tuple: (lista filtrada, quantidade removida)
    """
    filters = QUALITY_FILTERS.get("hackernews", {})

    min_score = filters.get("min_score", 50)
    min_comments = filters.get("min_comments", 10)
    exclude_domains = filters.get("exclude_domains", [])

    filtered = []
    removed = 0

    for story in stories:
        # Filtro: score minimo
        score = story.get("score", 0)
        if score < min_score:
            removed += 1
            continue

        # Filtro: comentarios minimos
        comments = story.get("num_comments", 0)
        if comments < min_comments:
            removed += 1
            continue

        # Filtro: dominios excluidos
        url = story.get("url", "").lower()
        if any(domain in url for domain in exclude_domains):
            removed += 1
            continue

        filtered.append(story)

    logger.info(f"Hacker News Filter: {len(filtered)} mantidos, {removed} removidos")
    return filtered, removed


# =============================================================================
# QUALITY SCORE UNIVERSAL (0-100)
# =============================================================================

def days_since_published(item: Dict) -> int:
    """Calcula dias desde publicacao"""
    published = item.get("published_at") or item.get("timestamp", "")
    if not published:
        return 999

    try:
        if isinstance(published, str):
            # Tentar ISO format
            if "T" in published:
                pub_date = datetime.fromisoformat(published.replace("Z", "+00:00"))
            else:
                pub_date = datetime.strptime(published[:10], "%Y-%m-%d")
        else:
            pub_date = published

        return (datetime.now(pub_date.tzinfo) - pub_date).days if hasattr(pub_date, 'tzinfo') and pub_date.tzinfo else (datetime.now() - pub_date.replace(tzinfo=None)).days
    except:
        return 999


def has_preferred_keywords(item: Dict, source: str) -> bool:
    """Verifica se item tem keywords preferidas"""
    filters = QUALITY_FILTERS.get(source, {})
    prefer_keywords = [k.lower() for k in filters.get("prefer_keywords", [])]

    if not prefer_keywords:
        return False

    title = item.get("title", "").lower()
    return any(kw in title for kw in prefer_keywords)


def is_quality_domain(item: Dict) -> bool:
    """Verifica se dominio e de qualidade (Hacker News)"""
    url = item.get("url", "").lower()

    quality_domains = [
        "nytimes.com", "washingtonpost.com", "bbc.com", "theguardian.com",
        "nature.com", "sciencedirect.com", "arxiv.org", "wikipedia.org",
        "medium.com", "substack.com", "bloomberg.com", "forbes.com",
        "wired.com", "arstechnica.com", "techcrunch.com", "reuters.com"
    ]

    return any(domain in url for domain in quality_domains)


def calculate_quality_score(item: Dict, source: str) -> int:
    """
    Calcula score de qualidade universal (0-100) para qualquer fonte.

    Args:
        item: Dict com dados do item
        source: 'youtube', 'google_trends', 'hackernews'

    Returns:
        Score de 0 a 100
    """
    score = 0

    if source == "youtube":
        # Views (30 pts)
        views = item.get("view_count", 0)
        if views >= 1_000_000:
            score += 30
        elif views >= 500_000:
            score += 25
        elif views >= 100_000:
            score += 20
        elif views >= 50_000:
            score += 15
        elif views >= 10_000:
            score += 10

        # Engagement (20 pts)
        likes = item.get("like_count", 0)
        engagement = likes / max(views, 1)
        if engagement >= 0.05:
            score += 20
        elif engagement >= 0.03:
            score += 15
        elif engagement >= 0.02:
            score += 10
        elif engagement >= 0.01:
            score += 5

        # Recencia (20 pts)
        days = days_since_published(item)
        if days <= 1:
            score += 20
        elif days <= 3:
            score += 15
        elif days <= 7:
            score += 10
        elif days <= 14:
            score += 5

    elif source == "google_trends":
        # Volume (40 pts)
        volume = item.get("volume", 0)
        if volume >= 500_000:
            score += 40
        elif volume >= 200_000:
            score += 30
        elif volume >= 100_000:
            score += 25
        elif volume >= 50_000:
            score += 20
        elif volume >= 10_000:
            score += 10

        # Keywords preferidas (30 pts)
        if has_preferred_keywords(item, source):
            score += 30

    elif source == "hackernews":
        # Score HN (30 pts)
        hn_score = item.get("score", 0)
        if hn_score >= 500:
            score += 30
        elif hn_score >= 300:
            score += 25
        elif hn_score >= 200:
            score += 20
        elif hn_score >= 100:
            score += 15
        elif hn_score >= 50:
            score += 10

        # Comentarios (20 pts)
        comments = item.get("num_comments", 0)
        if comments >= 200:
            score += 20
        elif comments >= 100:
            score += 15
        elif comments >= 50:
            score += 10
        elif comments >= 20:
            score += 5

        # Dominio confiavel (20 pts)
        if is_quality_domain(item):
            score += 20

    # BONUS: Match com subnicho (30 pts) - TODAS AS FONTES
    match_result = matches_subnicho(item)
    if match_result[0]:
        score += 30

    return min(100, score)


# =============================================================================
# MATCH COM SUBNICHOS
# =============================================================================

def normalize_text(text: str) -> str:
    """Normaliza texto para comparacao"""
    if not text:
        return ""
    # Lowercase, remover acentos basicos, remover pontuacao
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    return text


def matches_subnicho(item: Dict, specific_subnicho: str = None) -> Tuple[bool, str, int, List[str]]:
    """
    Verifica se item combina com algum subnicho (ou um especifico).

    Args:
        item: Dict com dados do item (precisa ter 'title' e opcionalmente 'description')
        specific_subnicho: Se especificado, verifica apenas este subnicho

    Returns:
        Tuple: (match: bool, best_subnicho: str, score: int, matched_keywords: List[str])
    """
    title = normalize_text(item.get("title", ""))
    description = normalize_text(item.get("description", ""))
    combined = f"{title} {description}"

    # Detectar idioma do item
    language = item.get("language", "en")

    best_match = (False, "", 0, [])

    subnichos_to_check = {}
    if specific_subnicho:
        if specific_subnicho in SUBNICHO_CONFIG:
            subnichos_to_check[specific_subnicho] = SUBNICHO_CONFIG[specific_subnicho]
    else:
        # Apenas subnichos ativos
        subnichos_to_check = {k: v for k, v in SUBNICHO_CONFIG.items() if v.get("active", False)}

    for subnicho_key, subnicho_config in subnichos_to_check.items():
        keywords_config = subnicho_config.get("keywords", {})

        # Usar keywords do idioma do item, ou ingles como fallback
        keywords = keywords_config.get(language, keywords_config.get("en", []))

        matched_keywords = []
        for keyword in keywords:
            keyword_norm = normalize_text(keyword)
            if keyword_norm in combined:
                matched_keywords.append(keyword)

        # Score baseado em quantas keywords deram match
        match_score = len(matched_keywords) * 10

        # Bonus se keyword esta no titulo (mais relevante)
        for kw in matched_keywords:
            if normalize_text(kw) in title:
                match_score += 5

        if match_score > best_match[2]:
            best_match = (len(matched_keywords) > 0, subnicho_key, match_score, matched_keywords)

    return best_match


def classify_all_items(items: List[Dict], source: str) -> List[Dict]:
    """
    Classifica todos os items com quality_score e subnicho match.

    Args:
        items: Lista de items de qualquer fonte
        source: 'youtube', 'google_trends', 'hackernews'

    Returns:
        Lista de items com campos adicionais:
        - quality_score (int 0-100)
        - matched_subnicho (str ou None)
        - subnicho_score (int)
        - matched_keywords (List[str])
    """
    classified = []

    for item in items:
        # Normalizar campo 'volume' para todas as fontes
        if "volume" not in item:
            item["volume"] = (
                item.get("view_count") or
                item.get("score") or
                item.get("upvotes") or
                0
            )

        # Garantir que source esta definido
        if "source" not in item:
            item["source"] = source

        # Calcular quality score
        item["quality_score"] = calculate_quality_score(item, source)

        # Verificar match com subnicho
        match_result = matches_subnicho(item)
        item["matched_subnicho"] = match_result[1] if match_result[0] else None
        item["subnicho_score"] = match_result[2]
        item["matched_keywords"] = match_result[3]

        classified.append(item)

    # Ordenar por quality_score
    classified.sort(key=lambda x: x.get("quality_score", 0), reverse=True)

    return classified


# =============================================================================
# FUNCOES DE RESUMO
# =============================================================================

def get_quality_summary(items: List[Dict]) -> Dict:
    """
    Retorna resumo de qualidade dos items.

    Args:
        items: Lista de items com quality_score

    Returns:
        Dict com estatisticas
    """
    if not items:
        return {"total": 0}

    scores = [i.get("quality_score", 0) for i in items]
    subnicho_matches = [i for i in items if i.get("matched_subnicho")]

    # Distribuicao por faixa de score
    excellent = len([s for s in scores if s >= 80])
    good = len([s for s in scores if 60 <= s < 80])
    average = len([s for s in scores if 40 <= s < 60])
    poor = len([s for s in scores if s < 40])

    return {
        "total": len(items),
        "avg_score": sum(scores) / len(scores),
        "max_score": max(scores),
        "min_score": min(scores),
        "excellent_count": excellent,  # >= 80
        "good_count": good,            # 60-79
        "average_count": average,      # 40-59
        "poor_count": poor,            # < 40
        "subnicho_matches": len(subnicho_matches),
        "subnicho_percent": len(subnicho_matches) / len(items) * 100
    }


# =============================================================================
# TESTE DO MODULO
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TESTE - Quality Filters & Scoring")
    print("=" * 60)

    # Teste com items mockados
    test_items = [
        {
            "title": "The Dark History of the Roman Empire - Full Documentary",
            "source": "youtube",
            "view_count": 2500000,
            "like_count": 125000,
            "duration_seconds": 3600,
            "language": "en",
            "published_at": datetime.now().isoformat()
        },
        {
            "title": "How This Billionaire Built His Empire From Nothing",
            "source": "youtube",
            "view_count": 800000,
            "like_count": 32000,
            "duration_seconds": 1800,
            "language": "en",
            "published_at": (datetime.now() - timedelta(days=3)).isoformat()
        },
        {
            "title": "Scary True Story - The Haunted House Mystery",
            "source": "youtube",
            "view_count": 500000,
            "like_count": 25000,
            "duration_seconds": 900,
            "language": "en",
            "published_at": (datetime.now() - timedelta(days=7)).isoformat()
        }
    ]

    # Classificar
    classified = classify_all_items(test_items, "youtube")

    print("\nItems classificados:")
    for item in classified:
        print(f"\n  [{item['quality_score']}] {item['title'][:50]}...")
        print(f"      Subnicho: {item['matched_subnicho'] or 'N/A'}")
        print(f"      Keywords: {item['matched_keywords'][:3] if item['matched_keywords'] else 'N/A'}")

    # Resumo
    summary = get_quality_summary(classified)
    print(f"\n\nResumo:")
    print(f"  Total: {summary['total']}")
    print(f"  Score medio: {summary['avg_score']:.1f}")
    print(f"  Excelentes (>=80): {summary['excellent_count']}")
    print(f"  Bons (60-79): {summary['good_count']}")
    print(f"  Match subnicho: {summary['subnicho_matches']} ({summary['subnicho_percent']:.1f}%)")

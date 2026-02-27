"""
Agente 4: Analise de Estruturas de Titulo
==========================================
Identifica formulas sintaticas (estruturas) de titulos YouTube
e gera ranking por score ponderado (60% CTR + 40% Views).

Hierarquia: Titulo = aplicacao concreta | Estrutura = formula com [VARIAVEIS]

Diferencial:
  - Unico agente da Camada 2 com 4 inputs (titulo, CTR, views, data)
  - CTR OBRIGATORIO: videos sem CTR sao excluidos
  - Score ponderado 60% CTR + 40% views (normalizado 0-100)
  - Analise de divergencia CTR vs views (insight exclusivo)
  - 2 chamadas LLM: Call 1 (classificar) + Call 2 (narrativa)

Fluxo:
1. Busca videos com CTR (JOIN videos_historico + yt_video_metrics)
2. Filtra videos com 7+ dias de maturidade
3. LLM classifica titulos em estruturas sintaticas
4. Python calcula ranking por score ponderado
5. Python detecta padroes (concentracao, divergencias)
6. Busca relatorio anterior (memoria cumulativa)
7. LLM interpreta ranking e gera narrativa (3 blocos)
8. Gera relatorio formatado
9. Salva no banco
"""

import os
import json
import logging
import requests
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Tuple

# Reusar funcoes dos agentes existentes
from copy_analysis_agent import (
    _get_channel_info,
    SUPABASE_URL,
    SUPABASE_KEY,
    SUPABASE_HEADERS,
)
from micronicho_agent import _get_monitorado_id

logger = logging.getLogger(__name__)

# Constantes
MATURITY_DAYS = 7   # Minimo de dias desde publicacao
MIN_VIDEOS = 5      # Minimo de videos COM CTR para rodar analise


# =============================================================================
# ETAPA 1: BUSCA DE VIDEOS COM CTR
# =============================================================================

def _fetch_videos_with_ctr(channel_id: str) -> Tuple[List[Dict], bool]:
    """
    Busca videos do canal com CTR obrigatorio.

    2 etapas:
    A) Buscar titulos + views + data de videos_historico (canal_id = integer)
    B) Buscar CTR de yt_video_metrics (channel_id = UC... string)
    C) JOIN por video_id — SO manter videos que tem CTR

    Returns:
        (videos_list, has_ctr_data)
        videos_list: [{title, views, ctr, publish_date, age_days, video_id}]
        has_ctr_data: True se algum video tem CTR
    """
    # ETAPA A: Buscar titulos + views + data de videos_historico
    monitorado_id = _get_monitorado_id(channel_id)
    if monitorado_id is None:
        logger.error(f"Nao foi possivel mapear {channel_id} para canais_monitorados")
        return [], False

    all_rows = []
    page_size = 1000
    offset = 0

    while True:
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/videos_historico",
            params={
                "canal_id": f"eq.{monitorado_id}",
                "select": "video_id,titulo,data_publicacao,views_atuais,data_coleta",
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

        all_rows.extend(rows)
        offset += page_size

        if len(rows) < page_size:
            break

    # Deduplicar por video_id (manter registro mais recente)
    seen = {}
    for v in all_rows:
        vid = v.get("video_id")
        if vid and vid not in seen:
            seen[vid] = v

    # Filtrar maturidade e montar mapa
    now = datetime.now(timezone.utc)
    video_map = {}  # video_id -> {title, views, publish_date, age_days}

    for v in seen.values():
        title = v.get("titulo", "")
        views = v.get("views_atuais", 0) or 0
        pub_date_str = v.get("data_publicacao", "")

        if not title or not pub_date_str:
            continue

        try:
            if "T" in pub_date_str:
                pub_date = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))
            else:
                pub_date = datetime.fromisoformat(pub_date_str + "T00:00:00+00:00")
            # Garantir timezone-aware (videos_historico pode ter naive datetime)
            if pub_date.tzinfo is None:
                pub_date = pub_date.replace(tzinfo=timezone.utc)
            age_days = (now - pub_date).days
        except (ValueError, TypeError):
            continue

        if age_days < MATURITY_DAYS:
            continue

        video_map[v.get("video_id")] = {
            "title": title,
            "views": views,
            "publish_date": pub_date_str,
            "age_days": age_days,
            "video_id": v.get("video_id")
        }

    logger.info(f"ETAPA A: {len(all_rows)} rows, {len(seen)} unicos, {len(video_map)} com 7+ dias")

    # ETAPA B: Buscar CTR de yt_video_metrics
    ctr_map = {}  # video_id -> ctr
    offset = 0

    while True:
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/yt_video_metrics",
            params={
                "channel_id": f"eq.{channel_id}",
                "select": "video_id,ctr",
                "ctr": "not.is.null",
                "limit": page_size,
                "offset": offset
            },
            headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        )

        if resp.status_code != 200:
            logger.error(f"Erro ao buscar CTR: {resp.status_code} - {resp.text[:200]}")
            break

        rows = resp.json()
        if not rows:
            break

        for r in rows:
            vid = r.get("video_id")
            ctr = r.get("ctr")
            if vid and ctr is not None:
                ctr_map[vid] = ctr

        offset += page_size
        if len(rows) < page_size:
            break

    logger.info(f"ETAPA B: {len(ctr_map)} videos com CTR em yt_video_metrics")

    # ETAPA C: JOIN por video_id — SO manter videos que tem CTR
    videos = []
    for vid, vdata in video_map.items():
        if vid in ctr_map:
            vdata["ctr"] = ctr_map[vid]
            videos.append(vdata)

    has_ctr_data = len(videos) > 0
    logger.info(f"ETAPA C: {len(videos)} videos com titulo + views + CTR (JOIN)")

    return videos, has_ctr_data


# =============================================================================
# ETAPA 2: CLASSIFICACAO VIA LLM (Call 1)
# =============================================================================

def classify_title_structures(
    videos: List[Dict],
    subnicho: str,
    lingua: str,
    previous_structures: Optional[List[Dict]] = None
) -> Dict:
    """
    Classifica cada titulo em exatamente 1 estrutura sintatica via LLM.

    Args:
        videos: lista de dicts com 'title'
        subnicho: subnicho do canal
        lingua: lingua dos titulos
        previous_structures: estruturas de analise anterior (consistencia)

    Returns:
        {
            "classifications": [{"title": str, "structure_code": str, "structure_formula": str}, ...],
            "all_structures": [{"code": str, "formula": str, "description": str}, ...]
        }
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY nao configurada - usando fallback")
        return _fallback_classification(videos)

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
    except ImportError:
        logger.error("openai nao instalado")
        return _fallback_classification(videos)

    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    # System prompt — Classificacao de Estruturas de Titulo
    system_prompt = """Voce e um classificador especializado em estruturas sintaticas de titulos YouTube.

=== O QUE E UMA ESTRUTURA DE TITULO ===

Uma estrutura de titulo e a FORMULA SINTATICA que define como a informacao
esta organizada no titulo. E o ESQUELETO do titulo — a forma como ele esta
construido para atrair o clique, independente do assunto especifico.

ESTRUTURA = formula replicavel com [VARIAVEIS]
TITULO = aplicacao concreta da formula a um tema

A mesma estrutura pode ser aplicada a QUALQUER tema dentro do subnicho.
Se a formula nao funciona com outros temas, e um titulo, nao uma estrutura.

=== COMO IDENTIFICAR UMA ESTRUTURA ===

Passo 1: Leia o titulo completo
Passo 2: Identifique os ELEMENTOS FIXOS (palavras/conectivos que se repetem entre titulos)
Passo 3: Identifique os ELEMENTOS VARIAVEIS (slots que mudam por tema)
Passo 4: Abstraia para nivel de formula com [VARIAVEIS]
Passo 5: Verifique se outros titulos seguem a MESMA formula

Exemplo detalhado:
- "What Ottomans Did To Christian Nuns Was Worse Than Death"
- "What Romans Did To Captured Soldiers Was Beyond Cruel"
  Fixos: "What", "Did to", "Was" + intensificador emocional
  Variaveis: [SUJEITO], [OBJETO], [INTENSIFICADOR]
  Formula: "What [SUJEITO] Did to [OBJETO] Was [INTENSIFICADOR]"

=== NIVEL DE ABSTRACAO (CRITICO) ===

Este e o desafio central. O nivel CORRETO de abstracao determina a qualidade
da classificacao:

MUITO AMPLO (errado):
  "Pergunta sobre historia" -> agrupa 80% dos titulos, inutil
  "Titulo com adjetivo" -> vago demais, sem valor analitico

MUITO ESPECIFICO (errado):
  "What Ottomans Did To Christian Nuns Was Worse Than Death" -> e o titulo inteiro
  Nao abstrai nada, impossivel replicar

CORRETO:
  "What [SUJEITO] Did to [OBJETO] Was [INTENSIFICADOR]"
  -> Captura a formula, permite substituir variaveis, replicavel

REGRA DE OURO: Uma boa estrutura permite gerar 10+ titulos diferentes
simplesmente trocando as variaveis. Se nao permite, esta especifica demais.

=== AGRUPAMENTO DE VARIACOES ===

Variacoes da MESMA FAMILIA sintatica devem ser agrupadas como UMA estrutura.
O que importa e a LOGICA do titulo, nao as palavras exatas.

Exemplos de mesma familia:
- "Was Worse Than Death" / "Will Make You Sick" / "Was Beyond Cruel"
  -> Todos sao [INTENSIFICADOR EMOCIONAL]. Mesma estrutura.
- "Tried to Erase From History" / "Tried to Hide From The World"
  -> Todos sao [ACAO DE OCULTAMENTO]. Mesma estrutura.
- "The Horrific Final Days of [X]" / "The Terrifying Last Hours of [X]"
  -> Mesma formula: "The [ADJETIVO] [PERIODO FINAL] of [FIGURA]"

NAO agrupe como mesma familia:
- "What [X] Did to [Y]..." vs "The [ADJ] Story of [X]..."
  -> Logica sintatica DIFERENTE (acao vs narrativa). Estruturas separadas.

=== NOMENCLATURA ===

Cada estrutura recebe:
- CODIGO: EST-01, EST-02, etc. (sequencial, estavel entre execucoes)
- FORMULA: com [VARIAVEIS] em maiuscula entre colchetes
  Variaveis comuns: [SUJEITO], [OBJETO], [INTENSIFICADOR], [ADJETIVO],
  [FIGURA], [EVENTO], [CONTEXTO], [CONSEQUENCIA], [SUPERLATIVO],
  [CATEGORIA], [ACAO], [PERIODO], [CIVILIZACAO], [NUMERO]
- DESCRICAO: 1 frase explicando o padrao (ex: "Acao de X contra Y com intensificador")

=== EXEMPLOS POR SUBNICHO ===

Historias Sombrias / Terror:
  EST-01: "What [SUJEITO] Did to [OBJETO] Was [INTENSIFICADOR]"
  EST-02: "The [ADJETIVO] [RITUAL/PRATICA] [SUJEITO] Tried to [ESCONDER] From History"
  EST-03: "The Horrific Final Days of [FIGURA HISTORICA]"
  EST-04: "The [ADJETIVO] Punishment for [ACAO] in [CIVILIZACAO]"

Relatos de Guerra:
  EST-A: "The [ADJETIVO] Story of [FIGURA/EVENTO] That [CONSEQUENCIA]"
  EST-B: "How [SUJEITO] [ACAO IMPOSSIVEL] During [CONTEXTO]"
  EST-C: "[FIGURA] - The [SUPERLATIVO] [CATEGORIA] of [CONTEXTO]"

=== REGRAS DE CLASSIFICACAO ===

1. Cada titulo pertence a EXATAMENTE 1 estrutura (classificacao exclusiva)
2. Estruturas devem ser FORMULAS REPLICAVEIS (gerar 10+ titulos possiveis)
3. Se o titulo nao se encaixa em nenhuma estrutura clara, use "Outros"
4. CONSISTENCIA: se uma estrutura ja existe na lista anterior, USE o mesmo codigo e formula
   (nao crie EST-07 se ja existe EST-03 com formula equivalente)
5. Variacoes da mesma familia sintatica = MESMA estrutura (agrupe sob formula mais generica)
6. A formula captura ELEMENTOS FIXOS + marca VARIAVEIS com [COLCHETES]
7. Responda APENAS com JSON valido, sem texto adicional
8. Analise na LINGUA ORIGINAL dos titulos (nao traduza)
9. Nao crie estruturas redundantes — se 2 formulas sao equivalentes, unifique"""

    # Bloco de estruturas anteriores (para consistencia)
    prev_block = ""
    if previous_structures:
        prev_list = "\n".join(
            [f"- {s.get('code', '?')}: {s.get('formula', '?')} ({s.get('description', '')})"
             for s in previous_structures]
        )
        prev_block = f"""Estruturas ja identificadas em analises anteriores (mantenha consistencia de codigos e formulas):
{prev_list}

"""

    titles_list = "\n".join([f"{i+1}. {v['title']}" for i, v in enumerate(videos)])

    user_prompt = f"""{prev_block}Subnicho do canal: {subnicho}
Lingua dos titulos: {lingua}

Analise cada titulo e identifique a ESTRUTURA SINTATICA subjacente.
Agrupe titulos com a mesma formula sob o mesmo codigo.

Titulos:
{titles_list}

JSON de saida:
{{
  "videos": [
    {{"title": "...", "structure_code": "EST-XX", "structure_formula": "..."}},
    ...
  ],
  "all_structures": [
    {{"code": "EST-01", "formula": "...", "description": "breve descricao do padrao"}},
    ...
  ]
}}"""

    # Chamar LLM com retry
    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model=model,
                temperature=0.3,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )

            content = response.choices[0].message.content
            result = json.loads(content)

            # Validar estrutura
            if "videos" not in result:
                logger.warning(f"LLM retornou JSON sem 'videos' (tentativa {attempt+1})")
                continue

            classifications = result["videos"]
            all_structures = result.get("all_structures", [])

            # Se all_structures nao veio, extrair das classificacoes
            if not all_structures:
                seen_codes = {}
                for c in classifications:
                    code = c.get("structure_code", "EST-99")
                    if code not in seen_codes:
                        seen_codes[code] = {
                            "code": code,
                            "formula": c.get("structure_formula", ""),
                            "description": ""
                        }
                all_structures = list(seen_codes.values())

            logger.info(f"LLM classificou {len(classifications)} titulos em {len(all_structures)} estruturas")
            return {
                "classifications": classifications,
                "all_structures": all_structures
            }

        except json.JSONDecodeError as e:
            logger.warning(f"JSON invalido da LLM (tentativa {attempt+1}): {e}")
            continue
        except Exception as e:
            logger.error(f"Erro na LLM Call 1 (tentativa {attempt+1}): {e}")
            continue

    # Fallback: nao conseguiu classificar
    logger.error("LLM falhou apos 2 tentativas - usando fallback")
    return _fallback_classification(videos)


def _fallback_classification(videos: List[Dict]) -> Dict:
    """Classificacao fallback quando LLM falha."""
    return {
        "classifications": [
            {"title": v["title"], "structure_code": "EST-99", "structure_formula": "Outros"}
            for v in videos
        ],
        "all_structures": [{"code": "EST-99", "formula": "Outros", "description": "Nao classificado"}]
    }


# =============================================================================
# ETAPA 3: CONSTRUCAO DO RANKING COM SCORE PONDERADO
# =============================================================================

def build_ranking(videos: List[Dict], classifications: List[Dict]) -> List[Dict]:
    """
    Agrupa videos por estrutura e calcula ranking por score ponderado.
    Score = 60% * CTR_norm + 40% * Views_norm (min-max 0-100).

    Args:
        videos: lista com {title, views, ctr, age_days, ...}
        classifications: lista com {title, structure_code, structure_formula}

    Returns:
        Lista de ranking entries ordenada por score DESC
    """
    # Criar mapa titulo -> (structure_code, structure_formula)
    title_to_struct = {}
    for c in classifications:
        title_to_struct[c.get("title", "")] = (
            c.get("structure_code", "EST-99"),
            c.get("structure_formula", "Outros")
        )

    # Agrupar videos por estrutura
    groups = {}  # code -> {"formula": str, "videos": []}
    for v in videos:
        code, formula = title_to_struct.get(v["title"], ("EST-99", "Outros"))
        if code not in groups:
            groups[code] = {"formula": formula, "videos": []}
        groups[code]["videos"].append(v)

    # Calcular metricas por estrutura
    structures = []
    for code, data in groups.items():
        struct_videos = data["videos"]
        views_list = [v["views"] for v in struct_videos]
        ctr_list = [v["ctr"] for v in struct_videos]
        total_views = sum(views_list)
        avg_views = total_views / len(struct_videos) if struct_videos else 0
        avg_ctr = sum(ctr_list) / len(ctr_list) if ctr_list else 0

        best = max(struct_videos, key=lambda x: x["views"])
        worst = min(struct_videos, key=lambda x: x["views"])

        structures.append({
            "structure_code": code,
            "structure_formula": data["formula"],
            "video_count": len(struct_videos),
            "avg_views": round(avg_views, 1),
            "total_views": total_views,
            "avg_ctr": round(avg_ctr, 6),
            "best_video": {
                "title": best["title"],
                "views": best["views"],
                "ctr": best["ctr"],
                "age_days": best["age_days"]
            },
            "worst_video": {
                "title": worst["title"],
                "views": worst["views"],
                "ctr": worst["ctr"],
                "age_days": worst["age_days"]
            },
            "all_videos": [
                {"title": v["title"], "views": v["views"], "ctr": v["ctr"], "age_days": v["age_days"]}
                for v in struct_videos
            ]
        })

    # Normalizar CTR e Views (min-max 0-100)
    if len(structures) <= 1:
        for s in structures:
            s["score"] = 100.0
    else:
        all_ctr = [s["avg_ctr"] for s in structures]
        all_views = [s["avg_views"] for s in structures]
        min_ctr, max_ctr = min(all_ctr), max(all_ctr)
        min_views, max_views = min(all_views), max(all_views)

        ctr_range = max_ctr - min_ctr if max_ctr != min_ctr else 1.0
        views_range = max_views - min_views if max_views != min_views else 1.0

        for s in structures:
            ctr_norm = ((s["avg_ctr"] - min_ctr) / ctr_range) * 100
            views_norm = ((s["avg_views"] - min_views) / views_range) * 100
            s["score"] = round(0.6 * ctr_norm + 0.4 * views_norm, 1)

    # Ordenar por score DESC
    structures.sort(key=lambda x: x["score"], reverse=True)

    # Adicionar rank
    for i, entry in enumerate(structures):
        entry["rank"] = i + 1

    return structures


# =============================================================================
# ETAPA 4: DETECCAO DE PADROES
# =============================================================================

def detect_patterns(ranking: List[Dict]) -> Dict:
    """
    Detecta padroes no ranking de estruturas de titulo.

    Returns:
        {
            "has_ctr_data": bool,
            "concentration_pct": float,
            "top_performers": [...],
            "bottom_performers": [...],
            "single_video_structures": [...],
            "total_structures": int,
            "total_videos": int,
            "avg_views_geral": float,
            "avg_ctr_geral": float,
            "ctr_views_divergences": [...]
        }
    """
    if not ranking:
        return {
            "has_ctr_data": False,
            "concentration_pct": 0,
            "top_performers": [],
            "bottom_performers": [],
            "single_video_structures": [],
            "total_structures": 0,
            "total_videos": 0,
            "avg_views_geral": 0,
            "avg_ctr_geral": 0,
            "ctr_views_divergences": []
        }

    total_views_all = sum(r["total_views"] for r in ranking)
    total_videos_all = sum(r["video_count"] for r in ranking)

    # Medias gerais
    avg_views_geral = total_views_all / total_videos_all if total_videos_all > 0 else 0
    all_ctrs = [r["avg_ctr"] for r in ranking]
    avg_ctr_geral = sum(all_ctrs) / len(all_ctrs) if all_ctrs else 0

    # Concentracao: % de views nos top 3
    top_3_views = sum(r["total_views"] for r in ranking[:3])
    concentration_pct = round((top_3_views / total_views_all * 100) if total_views_all > 0 else 0, 1)

    # Top performers: score acima de 70
    top_performers = [r["structure_code"] for r in ranking if r["score"] >= 70]

    # Bottom performers: score abaixo de 30
    bottom_performers = [r["structure_code"] for r in ranking if r["score"] < 30]

    # Estruturas com 1 video
    single_video = [r["structure_code"] for r in ranking if r["video_count"] == 1]

    # Divergencias CTR vs Views
    divergences = []
    for r in ranking:
        ctr_above_avg = r["avg_ctr"] > avg_ctr_geral * 1.15  # 15% acima
        ctr_below_avg = r["avg_ctr"] < avg_ctr_geral * 0.85  # 15% abaixo
        views_above_avg = r["avg_views"] > avg_views_geral * 1.15
        views_below_avg = r["avg_views"] < avg_views_geral * 0.85

        if ctr_above_avg and views_below_avg:
            divergences.append({
                "structure": r["structure_code"],
                "formula": r["structure_formula"],
                "type": "high_ctr_low_views",
                "ctr": r["avg_ctr"],
                "views": r["avg_views"]
            })
        elif ctr_below_avg and views_above_avg:
            divergences.append({
                "structure": r["structure_code"],
                "formula": r["structure_formula"],
                "type": "low_ctr_high_views",
                "ctr": r["avg_ctr"],
                "views": r["avg_views"]
            })

    return {
        "has_ctr_data": True,
        "concentration_pct": concentration_pct,
        "top_performers": top_performers,
        "bottom_performers": bottom_performers,
        "single_video_structures": single_video,
        "total_structures": len(ranking),
        "total_videos": total_videos_all,
        "avg_views_geral": round(avg_views_geral, 1),
        "avg_ctr_geral": round(avg_ctr_geral, 6),
        "ctr_views_divergences": divergences
    }


# =============================================================================
# ETAPA 5: NARRATIVA VIA LLM (Call 2)
# =============================================================================

def _format_views(n) -> str:
    """Formata views: 1500 -> 1.5K, 150000 -> 150K"""
    n = int(n)
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def _format_ctr(ctr: float) -> str:
    """Formata CTR: 0.058 -> 5.8%"""
    return f"{ctr * 100:.1f}%"


def _format_ranking_table(ranking: List[Dict]) -> str:
    """Formata ranking como tabela texto com CTR e Score."""
    lines = []
    lines.append(
        f"  {'#':>3}  {'Codigo':<8} {'Formula':<40} {'Vids':>4}  "
        f"{'CTR Avg':>8}  {'Views Avg':>10}  {'Score':>5}"
    )
    lines.append(
        f"  {'---':>3}  {'--------':<8} {'-'*40} {'----':>4}  "
        f"{'--------':>8}  {'-'*10}  {'-----':>5}"
    )

    for r in ranking:
        formula = r["structure_formula"]
        if len(formula) > 40:
            formula = formula[:37] + "..."
        lines.append(
            f"  {r['rank']:>3}  {r['structure_code']:<8} {formula:<40} {r['video_count']:>4}  "
            f"{_format_ctr(r['avg_ctr']):>8}  {_format_views(int(r['avg_views'])):>10}  "
            f"{r['score']:>5.1f}"
        )

    return "\n".join(lines)


def _format_patterns(patterns: Dict) -> str:
    """Formata padroes como texto."""
    lines = []
    lines.append(f"- Concentracao top 3: {patterns['concentration_pct']}%")
    lines.append(f"- Media geral de views: {_format_views(int(patterns['avg_views_geral']))}")
    lines.append(f"- Media geral de CTR: {_format_ctr(patterns['avg_ctr_geral'])}")
    lines.append(f"- Total estruturas: {patterns['total_structures']}")
    lines.append(f"- Total videos: {patterns['total_videos']}")

    if patterns["top_performers"]:
        lines.append(f"- Top performers (score 70+): {', '.join(patterns['top_performers'])}")
    if patterns["bottom_performers"]:
        lines.append(f"- Bottom performers (score <30): {', '.join(patterns['bottom_performers'])}")
    if patterns["single_video_structures"]:
        lines.append(f"- Estruturas de 1 video: {', '.join(patterns['single_video_structures'])}")

    if patterns["ctr_views_divergences"]:
        lines.append("- Divergencias CTR vs Views:")
        for d in patterns["ctr_views_divergences"]:
            dtype = "Alto CTR + Baixas Views" if d["type"] == "high_ctr_low_views" else "Baixo CTR + Altas Views"
            lines.append(f"    {d['structure']}: {dtype} (CTR={_format_ctr(d['ctr'])}, Views={_format_views(int(d['views']))})")

    return "\n".join(lines)


def generate_narrative(
    channel_name: str,
    subnicho: str,
    lingua: str,
    ranking: List[Dict],
    patterns: Dict,
    total_videos: int,
    comparison: Optional[Dict] = None
) -> Optional[Dict]:
    """
    LLM Call 2: gera narrativa interpretando o ranking de estruturas.

    Returns:
        {"observacoes": str, "recomendacoes": str, "tendencias": str}
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY nao configurada - pulando narrativa LLM")
        return None

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
    except ImportError:
        logger.error("openai nao instalado")
        return None

    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    # System prompt — Narrativa Profissional de Estruturas de Titulo
    system_prompt = """Voce e um analista de performance de titulos YouTube, especializado em
identificar estruturas sintaticas (formulas de titulo) que maximizam CTR e views.

=== O QUE SAO ESTRUTURAS DE TITULO ===

Cada titulo de video segue uma ESTRUTURA SINTATICA — uma formula que define
como a informacao esta organizada para atrair o clique.

Exemplo: "What [SUJEITO] Did to [OBJETO] Was [INTENSIFICADOR]"
- Aplicacao 1: "What Ottomans Did To Christian Nuns Was Worse Than Death"
- Aplicacao 2: "What Romans Did To Captured Soldiers Was Beyond Cruel"
Mesma formula, temas diferentes, performance SEMELHANTE = estrutura funcional.

=== POR QUE ESTRUTURAS DE TITULO IMPORTAM ===

1. PERFORMANCE: Estruturas diferentes tem CTR drasticamente diferente.
   Uma formula que gera curiosidade + tensao pode ter CTR 2x maior que uma
   formula informativa/neutra. Isso e mensuravel e replicavel.

2. REPLICABILIDADE: Uma vez identificada uma formula top (ex: EST-01 com score 92),
   o canal pode aplicar essa formula a QUALQUER tema. E a ferramenta mais
   actionable da analise — "use esta formula no proximo titulo".

3. PROTECAO: Variar estruturas de titulo protege contra:
   - Fadiga da audiencia (mesma formula repetida = cliques decrescem)
   - Inauthentic content (titulos roboticos/formulaicos = risco de derrubada)
   - Saturacao de mercado (formula viral que todos usam perde efeito)

4. DIAGNOSTICO: Divergencia CTR vs Views revela problemas FORA do titulo:
   - Alto CTR + baixas views = titulo BOM, mas copy/retencao falhou
   - Baixo CTR + altas views = distribuicao/viral sem merito do titulo

=== SEU PAPEL ===

Voce recebe uma TABELA DE RANKING ja calculada pelo Python.
A matematica ja foi feita — CTR medio, views medio, score ponderado (60% CTR + 40% views).
Seu trabalho e INTERPRETAR os padroes e dar recomendacoes estrategicas.

=== METRICA: SCORE PONDERADO ===

Score = 60% CTR + 40% Views (normalizado 0-100)

- 60% CTR: metrica que o TITULO controla diretamente (atratividade do clique)
- 40% Views: validacao de volume real (CTR alto sem views = tema fraco ou distribuicao ruim)

Todos os videos na analise TEM CTR (requisito). Sem CTR, o agente nao roda.

=== DIFERENCA DOS OUTROS AGENTES ===

O Agente 3 (Micronichos) analisa SOBRE O QUE o video fala (tema/categoria).
Este agente analisa COMO o titulo e formulado (estrutura sintatica).
Sao dimensoes ORTOGONAIS — um video pode pertencer ao micronicho "Espionagem"
E usar a estrutura "What [X] Did to [Y] Was [Z]".

O Agente 1 (Copy) analisa a estrutura narrativa (A-G) do ROTEIRO.
Este agente analisa a estrutura do TITULO. Sao complementares.

O relatorio sera consumido pelo Agente 6 (boss) que cruza todos os outputs.

=== ANALISE DE DIVERGENCIA CTR vs VIEWS ===

Este e o insight UNICO que so este agente pode oferecer:

CENARIO 1: Alto CTR + Baixas Views
- O titulo FUNCIONA (gera clique por impressao)
- Algo APOS o clique falhou: copy fraca, retencao baixa, tema obscuro
- Recomendacao: manter a ESTRUTURA, mudar o TEMA ou melhorar a COPY
- Exemplo: EST-09 com CTR 11% mas views 22K = tema Wu Zetian muito obscuro

CENARIO 2: Baixo CTR + Altas Views
- O titulo NAO funciona (nao atrai cliques)
- Views vieram de distribuicao/algoritmo, nao do titulo
- Recomendacao: REFORMULAR o titulo usando estrutura top performer
- O conteudo esta la, so precisa de titulo melhor

CENARIO 3: Alto CTR + Altas Views = FORMULA MESTRE
- Tudo alinhado: titulo atrai + conteudo entrega + algoritmo distribui
- Recomendacao: ESCALAR com prioridade maxima

=== TIPO DE RACIOCINIO ESPERADO ===

NAO FACA ISSO (superficial):
"EST-01 tem bom score. Recomendo usar mais."

FACA ISSO (profissional — dados concretos, diagnostico direto):
"EST-01 'What [X] Did to [Y] Was [Z]' lidera com score 92 — CTR 14.2% com
6 videos, o pior CTR (11.8%) ainda supera a media do canal (9.1%).
Formula-mestre: combina curiosidade direta ('What did') + injustica implicita
('Did TO') + intensificador emocional ('Worse Than Death').
Consistencia CONFIRMADA — nao e outlier.

EST-09 '[FIGURA]: The [CAT] History Forgot' tem CTR 11.0% (acima da media!)
mas apenas 22K views. DIAGNOSTICO: titulo atraente, mas 'Wu Zetian' e figura
desconhecida para audiencia ocidental -> clique por curiosidade, retencao baixa,
algoritmo parou de distribuir. Recomendacao: testar esta estrutura com figuras
mais conhecidas (Cleopatra, Nero, Vlad). Se views subirem, confirma que o
problema era o TEMA, nao a FORMULA.

[ALTA] Produzir 3+ videos com EST-01. Score 92, consistencia em 6 videos,
menor CTR individual (11.8%) ainda acima da media. Variar temas:
civilizacoes diferentes, epocas diferentes, mesma formula.

[ALTA] Testar nova estrutura: 'The [ADJETIVO] Reason [FIGURA] [ACAO EXTREMA]'
— similar a EST-01 (acao + intensificador) mas focada em MOTIVACAO.
Potencial de CTR alto baseado no padrao da audiencia (curiosidade + emocao negativa)."

=== REGRAS INVIOLAVEIS ===

1. Seja FACTUAL — cite CODIGOS (EST-XX), SCORES, CTR e VIEWS exatos do ranking
2. NAO invente dados — use APENAS o que esta no ranking fornecido
3. Considere a IDADE do video ao interpretar views/CTR
4. Cada recomendacao DEVE citar dados especificos (codigo, score, CTR, videos)
5. NAO repita a tabela de ranking — ela ja esta no relatorio
6. Escreva em portugues, paragrafos curtos separados por linha em branco
7. Escreva o quanto for necessario. NAO resuma, NAO corte a analise
8. Use EXATAMENTE os marcadores [OBSERVACOES], [RECOMENDACOES] e [TENDENCIAS]
9. Priorize recomendacoes: [ALTA] = oportunidade forte, [MEDIA] = testar, [BAIXA] = monitorar
10. Novas estruturas recomendadas devem ter FORMULA com [VARIAVEIS], nao exemplos aplicados"""

    # Montar bloco de memoria
    previous_report_block = ""
    if comparison and comparison.get("previous_report"):
        prev_date = comparison.get("previous_date", "")
        if isinstance(prev_date, str) and "T" in prev_date:
            try:
                prev_date = datetime.fromisoformat(prev_date.replace("Z", "+00:00")).strftime("%d/%m/%Y")
            except (ValueError, TypeError):
                pass
        previous_report_block = f"""VOCE TEM MEMORIA ACUMULATIVA:
O relatorio anterior contem TODAS as conclusoes e tendencias identificadas ate agora.
Sua analise atual DEVE:
- Se basear no relatorio anterior como referencia
- Verificar se recomendacoes anteriores foram implementadas (detectavel nos dados)
- Confirmar ou revisar tendencias com numeros
- Construir em cima, nunca ignorar o historico

RELATORIO ANTERIOR COMPLETO ({prev_date}):
{comparison['previous_report']}
FIM DO RELATORIO ANTERIOR.

"""

    ranking_table = _format_ranking_table(ranking)
    patterns_text = _format_patterns(patterns)

    ctr_nota = "Todos os videos tem CTR (requisito obrigatorio). Score = 60% CTR + 40% Views."

    user_prompt = f"""{previous_report_block}Produza EXATAMENTE 3 blocos:

[OBSERVACOES]
Analise os padroes do ranking. Cubra obrigatoriamente:

1. TOP PERFORMERS: Os 2-3 melhores estruturas.
   Para cada: codigo, formula, score, CTR, avg views, quantidade de videos.
   CONSISTENCIA: todos os videos performam bem ou so 1 viral puxa a media?
   Se consistente = formula CONFIRMADA. Se outlier = nao confirma.

2. BOTTOM PERFORMERS: Estruturas com pior score.
   Diferencie CLARAMENTE:
   - Performance fraca com MUITOS videos (3+) = formula nao funciona, pausar
   - Performance fraca com 1 video = amostra insuficiente, NAO condenar

3. PADRAO DA AUDIENCIA: O que os top performers tem em comum?
   Identifique o PADRAO: curiosidade + emocao? Revelacao? Superlativo?
   Cite dados dos top vs bottom para sustentar o padrao.

4. CONCENTRACAO: {patterns['concentration_pct']}% dos videos nas top 3 estruturas.
   Saudavel ou arriscado? Risco de fadiga?

5. ESTRUTURAS DE 1 VIDEO: oportunidade (score alto) ou sinal fraco (score baixo)?

6. DIVERGENCIA CTR vs VIEWS:
   - Alguma estrutura com CTR acima da media mas views abaixo? (titulo bom, algo falhou)
   - Alguma estrutura com views altas mas CTR baixo? (distribuicao sem merito)
   Diagnostique a CAUSA provavel de cada divergencia.

7. FADIGA: Alguma estrutura com muitos videos (5+) onde os mais recentes
   performam PIOR que os antigos? Sinal de fadiga da audiencia.

[RECOMENDACOES]
Acoes CONCRETAS, cada uma com prioridade [ALTA], [MEDIA] ou [BAIXA]:

1. ESCALAR: Quais estruturas merecem mais videos?
   Cite: codigo, formula, score atual, consistencia, quantos videos produzir.

2. PAUSAR: Quais estruturas tem performance fraca com volume suficiente?
   SO recomende pausar se ha 3+ videos com performance consistentemente baixa.
   NUNCA recomende pausar com base em apenas 1-2 videos.

3. NOVAS ESTRUTURAS: Sugira 3-5 formulas NOVAS com [VARIAVEIS] que o canal NAO testou.
   Para cada nova estrutura sugerida:
   - Formula completa com [VARIAVEIS]
   - Por que faz sentido (conexao com top performers, padrao da audiencia)
   - Tipo de gancho: curiosidade, emocao, revelacao, superlativo, etc.
   NAO inclua exemplos aplicados — apenas a formula abstrata.

4. REFORMULACAO: Titulos com baixo CTR em videos de alto views = oportunidade
   de reformulacao. Sugira qual estrutura usar.

5. REDISTRIBUICAO: Se concentracao > 50%, como redistribuir producao
   entre estruturas sem perder performance?

[TENDENCIAS]
EVOLUCAO ao longo do tempo (SO se houver relatorio anterior):
- Estruturas que subiram ou cairam no ranking (cite codigos, scores, posicoes)
- Novas estruturas que apareceram desde a ultima analise
- Recomendacoes anteriores que foram implementadas (se detectavel nos dados)
- Sinais de fadiga confirmados ou desmentidos pelos dados
- Mudancas no padrao de preferencia da audiencia
- Se primeira analise: "Primeira analise. Sem dados anteriores para comparacao."

DADOS DO CANAL:
Canal: {channel_name}
Subnicho: {subnicho}
Lingua: {lingua}
Videos analisados: {total_videos} (com 7+ dias de maturidade, COM CTR)
{ctr_nota}

TABELA DE RANKING:
{ranking_table}

PADROES DETECTADOS:
{patterns_text}"""

    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0.4,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )

        text = response.choices[0].message.content

        # Parse dos 3 blocos
        observacoes = ""
        recomendacoes = ""
        tendencias = ""

        if "[OBSERVACOES]" in text:
            after_obs = text.split("[OBSERVACOES]", 1)[1]
            if "[RECOMENDACOES]" in after_obs:
                observacoes = after_obs.split("[RECOMENDACOES]", 1)[0].strip()
                after_rec = after_obs.split("[RECOMENDACOES]", 1)[1]
                if "[TENDENCIAS]" in after_rec:
                    recomendacoes = after_rec.split("[TENDENCIAS]", 1)[0].strip()
                    tendencias = after_rec.split("[TENDENCIAS]", 1)[1].strip()
                else:
                    recomendacoes = after_rec.strip()
            else:
                observacoes = after_obs.strip()
        else:
            observacoes = text

        return {
            "observacoes": observacoes,
            "recomendacoes": recomendacoes,
            "tendencias": tendencias
        }

    except Exception as e:
        logger.error(f"Erro na LLM Call 2: {e}")
        return None


# =============================================================================
# ETAPA 6: GERACAO DO RELATORIO
# =============================================================================

def generate_report(
    channel_name: str,
    ranking: List[Dict],
    patterns: Dict,
    llm_narrative: Optional[Dict],
    comparison: Optional[Dict],
    total_videos: int,
    all_structures: List[Dict]
) -> str:
    """Gera relatorio formatado de estruturas de titulo."""
    now = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")

    report = []
    report.append("=" * 60)
    report.append(f"ANALISE DE ESTRUTURAS DE TITULO | {channel_name} | {now}")
    report.append("=" * 60)
    report.append("")

    # Ranking table
    report.append("RANKING DE ESTRUTURAS (por score ponderado: 60% CTR + 40% views):")
    report.append("")
    report.append(_format_ranking_table(ranking))
    report.append("")

    # Sumario
    report.append(f"Estruturas identificadas: {len(all_structures)}")
    report.append(f"Videos analisados: {total_videos}")
    report.append(f"Concentracao top 3: {patterns['concentration_pct']}%")
    report.append(f"Media geral de views: {_format_views(int(patterns['avg_views_geral']))}")
    report.append(f"Media geral de CTR: {_format_ctr(patterns['avg_ctr_geral'])}")
    report.append("")

    # LLM narrative
    if llm_narrative:
        if llm_narrative.get("observacoes"):
            report.append("--- OBSERVACOES ---")
            report.append("")
            report.append(llm_narrative["observacoes"])
            report.append("")

        if llm_narrative.get("recomendacoes"):
            report.append("--- RECOMENDACOES ---")
            report.append("")
            report.append(llm_narrative["recomendacoes"])
            report.append("")

        if llm_narrative.get("tendencias"):
            report.append("--- TENDENCIAS ---")
            report.append("")
            report.append(llm_narrative["tendencias"])
            report.append("")

    # Comparacao
    if comparison:
        report.append("--- VS ANTERIOR ---")
        report.append("")
        prev_date = comparison.get("previous_date", "N/A")
        if isinstance(prev_date, str) and "T" in prev_date:
            prev_date = prev_date.split("T")[0]
        report.append(f"  Analise anterior: {prev_date}")
        prev_count = comparison.get("previous_structure_count")
        if prev_count is not None:
            report.append(f"  Estruturas anterior: {prev_count} -> atual: {len(all_structures)}")
        prev_videos = comparison.get("previous_total_videos")
        if prev_videos is not None:
            report.append(f"  Videos anterior: {prev_videos} -> atual: {total_videos}")
        report.append("")
    else:
        report.append("--- VS ANTERIOR ---")
        report.append("")
        report.append("  Primeira analise. Sem dados anteriores.")
        report.append("")

    report.append("=" * 60)

    return "\n".join(report)


# =============================================================================
# ETAPA 7: PERSISTENCIA
# =============================================================================

def save_analysis(
    channel_id: str,
    channel_name: str,
    ranking: List[Dict],
    all_structures: List[Dict],
    report_text: str,
    patterns: Dict,
    total_videos: int,
    has_ctr_data: bool
) -> Optional[int]:
    """Salva analise no banco."""
    # Remover all_videos do ranking para nao salvar dados grandes
    ranking_clean = []
    for r in ranking:
        entry = {k: v for k, v in r.items() if k != "all_videos"}
        ranking_clean.append(entry)

    run_data = {
        "channel_id": channel_id,
        "channel_name": channel_name,
        "structure_count": len(all_structures),
        "total_videos_analyzed": total_videos,
        "has_ctr_data": has_ctr_data,
        "ranking_json": json.dumps(ranking_clean),
        "structures_list": json.dumps(all_structures),
        "patterns_json": json.dumps(patterns),
        "report_text": report_text
    }

    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/title_structure_analysis_runs",
        headers=SUPABASE_HEADERS,
        json=run_data
    )

    if resp.status_code not in [200, 201]:
        logger.error(f"Erro ao salvar analise de titulo: {resp.status_code} - {resp.text[:200]}")
        return None

    result = resp.json()
    run_id = result[0]["id"] if result else None
    logger.info(f"Analise de titulo salva: run_id={run_id}")
    return run_id


# =============================================================================
# ETAPA 8: COMPARACAO COM ANTERIOR
# =============================================================================

def compare_with_previous(channel_id: str) -> Optional[Dict]:
    """
    Busca a ultima analise de titulo do canal.
    Memoria cumulativa: cada analise carrega o relatorio anterior.
    """
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/title_structure_analysis_runs",
        params={
            "channel_id": f"eq.{channel_id}",
            "select": "run_date,structure_count,total_videos_analyzed,"
                      "structures_list,report_text",
            "order": "run_date.desc",
            "limit": "1"
        },
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    )

    if resp.status_code != 200 or not resp.json():
        return None

    prev = resp.json()[0]
    prev_structures = prev.get("structures_list")
    if isinstance(prev_structures, str):
        try:
            prev_structures = json.loads(prev_structures)
        except (json.JSONDecodeError, TypeError):
            prev_structures = []

    return {
        "previous_date": prev.get("run_date", ""),
        "previous_structure_count": prev.get("structure_count"),
        "previous_total_videos": prev.get("total_videos_analyzed"),
        "previous_structures": prev_structures or [],
        "previous_report": prev.get("report_text", "")
    }


# =============================================================================
# ETAPA 9: FUNCOES DE CONSULTA (usadas pelos endpoints)
# =============================================================================

def get_latest_analysis(channel_id: str) -> Optional[Dict]:
    """Retorna a analise de titulo mais recente."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/title_structure_analysis_runs",
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
        for field in ["ranking_json", "structures_list", "patterns_json"]:
            if isinstance(row.get(field), str):
                try:
                    row[field] = json.loads(row[field])
                except (json.JSONDecodeError, TypeError):
                    pass
        return row
    return None


def get_analysis_history(channel_id: str, limit: int = 20, offset: int = 0) -> Dict:
    """Retorna historico paginado."""
    # Contar total
    count_resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/title_structure_analysis_runs",
        params={"channel_id": f"eq.{channel_id}", "select": "id"},
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

    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/title_structure_analysis_runs",
        params={
            "channel_id": f"eq.{channel_id}",
            "select": "id,channel_name,run_date,structure_count,"
                      "total_videos_analyzed,has_ctr_data",
            "order": "run_date.desc",
            "limit": str(limit),
            "offset": str(offset)
        },
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    )

    historico = resp.json() if resp.status_code == 200 else []
    return {"historico": historico, "total": total}


# =============================================================================
# ETAPA 10: FUNCAO PRINCIPAL
# =============================================================================

def run_analysis(channel_id: str) -> Dict:
    """
    Executa analise completa de estruturas de titulo para um canal.
    CTR e OBRIGATORIO — videos sem CTR sao excluidos.

    Returns:
        {
            "success": bool,
            "channel_id": str,
            "channel_name": str,
            "run_id": int,
            "report": str,
            "structure_count": int,
            "total_videos": int,
            "has_ctr_data": bool,
            "ranking": [...],
            "error": str (se falhou)
        }
    """
    logger.info(f"{'='*50}")
    logger.info(f"TITULO: Iniciando para canal {channel_id}")
    logger.info(f"{'='*50}")

    # 1. Buscar dados do canal
    channel_info = _get_channel_info(channel_id)
    if not channel_info:
        return {"success": False, "error": f"Canal {channel_id} nao encontrado em yt_channels"}

    channel_name = channel_info.get("channel_name", channel_id)
    subnicho = channel_info.get("subnicho", "N/A")
    lingua = channel_info.get("lingua", "N/A")

    logger.info(f"Canal: {channel_name} | Subnicho: {subnicho} | Lingua: {lingua}")

    # 2. Buscar videos com CTR (filtro 7+ dias ja aplicado)
    videos, has_ctr_data = _fetch_videos_with_ctr(channel_id)

    if not has_ctr_data:
        return {"success": False, "error": "CTR nao disponivel para este canal. Rode o ctr_collector primeiro."}

    if len(videos) < MIN_VIDEOS:
        return {"success": False, "error": f"Minimo {MIN_VIDEOS} videos com CTR necessarios, encontrados: {len(videos)}"}

    # 3. Buscar estruturas anteriores (para consistencia de codigos)
    comparison = compare_with_previous(channel_id)
    previous_structures = comparison.get("previous_structures", []) if comparison else []

    # 4. LLM Call 1: classificar titulos em estruturas
    classification_result = classify_title_structures(videos, subnicho, lingua, previous_structures)
    classifications = classification_result["classifications"]
    all_structures = classification_result["all_structures"]

    logger.info(f"Classificacao: {len(classifications)} titulos em {len(all_structures)} estruturas")

    # 5. Construir ranking com score ponderado
    ranking = build_ranking(videos, classifications)

    # 6. Detectar padroes
    patterns = detect_patterns(ranking)

    # 7. LLM Call 2: narrativa
    llm_narrative = generate_narrative(
        channel_name, subnicho, lingua, ranking, patterns,
        len(videos), comparison
    )

    # 8. Gerar relatorio
    report = generate_report(
        channel_name, ranking, patterns, llm_narrative,
        comparison, len(videos), all_structures
    )

    # 9. Salvar
    run_id = save_analysis(
        channel_id, channel_name, ranking, all_structures,
        report, patterns, len(videos), has_ctr_data
    )

    logger.info(f"TITULO COMPLETA: {channel_name} | {len(all_structures)} estruturas | {len(videos)} videos")

    return {
        "success": True,
        "channel_id": channel_id,
        "channel_name": channel_name,
        "run_id": run_id,
        "report": report,
        "structure_count": len(all_structures),
        "total_videos": len(videos),
        "has_ctr_data": has_ctr_data,
        "ranking": [
            {k: v for k, v in r.items() if k != "all_videos"}
            for r in ranking
        ]
    }

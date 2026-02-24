"""
Agente de Score de Autenticidade
================================
Analisa cada canal individualmente e gera um Score de Autenticidade (0-100).
Quanto MAIS ALTO o score, mais autentico e seguro o canal parece.

Fatores analisados (50/50):
1. Variedade de Estruturas de Copy (Col A) - diversidade das letras A-G
2. Diversidade de Titulos (Col B) - quao diferentes sao os titulos entre si

Fluxo:
1. Le planilha (Col A = estrutura, Col B = titulo)
2. Calcula score de variedade de estruturas
3. Calcula score de diversidade de titulos
4. Combina scores (50/50)
5. Gera alertas se necessario
6. Compara com analise anterior (memoria cumulativa)
7. LLM gera diagnostico + recomendacoes
8. Gera relatorio formatado
9. Salva no banco
"""

import os
import re
import json
import math
import logging
import statistics
import requests
from collections import Counter
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any

# Importar funcoes reutilizaveis do copy analysis agent
from copy_analysis_agent import (
    read_copy_structures,
    _normalize_title,
    _get_channel_info,
    get_all_channels_for_analysis,
    SUPABASE_URL,
    SUPABASE_KEY,
    SUPABASE_HEADERS,
    VALID_STRUCTURES,
)

logger = logging.getLogger(__name__)

# Constantes do agente
STRUCTURE_WEIGHT = 0.50
TITLE_WEIGHT = 0.50

# Thresholds de nivel
LEVEL_EXCELENTE = 80
LEVEL_BOM = 60
LEVEL_ATENCAO = 40
LEVEL_RISCO = 20

# Alertas
ALERT_SCORE_THRESHOLD = 40  # Score abaixo disso = alerta
ALERT_FACTOR_THRESHOLD = 30  # Fator individual abaixo disso = alerta
ALERT_SPIKE_THRESHOLD = 15  # Queda de mais de 15 pontos = alerta

# Stopwords para analise de titulos (PT + EN + ES + DE + FR)
STOPWORDS = {
    # Portugues
    "o", "a", "os", "as", "um", "uma", "de", "do", "da", "dos", "das",
    "em", "no", "na", "nos", "nas", "por", "para", "com", "sem", "que",
    "e", "ou", "se", "mas", "mais", "como", "foi", "era", "ser", "ter",
    "seu", "sua", "seus", "suas", "ele", "ela", "eles", "elas",
    "este", "esta", "esse", "essa", "isso", "aqui", "ali", "la",
    "nao", "sim", "ja", "ainda", "tambem", "muito", "pouco",
    # Ingles
    "the", "a", "an", "of", "in", "on", "at", "to", "for", "and",
    "or", "but", "is", "was", "are", "were", "be", "been", "being",
    "has", "have", "had", "do", "does", "did", "will", "would",
    "can", "could", "may", "might", "shall", "should", "must",
    "it", "its", "he", "she", "they", "them", "his", "her", "their",
    "this", "that", "these", "those", "who", "what", "which", "when",
    "where", "how", "why", "not", "no", "so", "if", "than", "then",
    "with", "from", "by", "about", "into", "through", "during",
    "before", "after", "above", "below", "between", "out", "off",
    "up", "down", "over", "under", "again", "further", "once",
    "most", "very", "just", "also", "now", "here", "there",
    # Espanhol
    "el", "la", "los", "las", "un", "una", "del", "al", "en",
    "por", "para", "con", "sin", "que", "y", "o", "si", "pero",
    "mas", "como", "fue", "era", "ser", "su", "sus",
    # Alemao
    "der", "die", "das", "ein", "eine", "und", "oder", "aber",
    "ist", "war", "sind", "von", "zu", "mit", "auf", "fur",
    "nicht", "auch", "noch", "nur", "schon",
    # Frances
    "le", "la", "les", "un", "une", "des", "du", "de", "et",
    "ou", "mais", "est", "sont", "dans", "sur", "pour", "avec",
    "sans", "pas", "ne", "qui", "que", "ce", "cette", "ces",
}


# =============================================================================
# ETAPA 1: CALCULO DO SCORE DE ESTRUTURAS
# =============================================================================

def compute_structure_score(structures: List[str]) -> Dict:
    """
    Calcula score de variedade de estruturas de copy (0-100).
    Score alto = boa diversidade. Score baixo = copy engessada.

    Args:
        structures: Lista de letras (A-G) de cada video

    Returns:
        {
            "score": float (0-100),
            "metrics": {
                "distribution": {A: count, B: count, ...},
                "dominant": str,
                "dominant_pct": float,
                "unique_count": int,
                "entropy": float,
                "max_entropy": float,
                "total_videos": int
            }
        }
    """
    if not structures or len(structures) < 2:
        return {
            "score": 50.0,  # Score neutro com dados insuficientes
            "metrics": {
                "distribution": {},
                "dominant": None,
                "dominant_pct": 0,
                "unique_count": 0,
                "entropy": 0,
                "max_entropy": 0,
                "total_videos": len(structures) if structures else 0
            }
        }

    total = len(structures)
    counter = Counter(structures)
    distribution = dict(counter.most_common())

    dominant = counter.most_common(1)[0][0]
    dominant_count = counter.most_common(1)[0][1]
    dominant_pct = dominant_count / total

    unique_count = len(counter)

    # Entropia Shannon
    entropy = 0.0
    for count in counter.values():
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)

    max_entropy = math.log2(len(VALID_STRUCTURES))  # log2(7) = 2.807

    # --- Sub-scores ---

    # 1. Score de dominancia (invertido: menos dominancia = melhor)
    # dominant_pct < 0.25 → 100 (excelente distribuicao)
    # dominant_pct > 0.85 → 0 (copy totalmente engessada)
    if dominant_pct <= 0.25:
        dominance_score = 100.0
    elif dominant_pct >= 0.85:
        dominance_score = 0.0
    else:
        dominance_score = max(0, 100 * (0.85 - dominant_pct) / (0.85 - 0.25))

    # 2. Score de entropia (mais entropia = melhor)
    # entropy > 2.0 → 100
    # entropy ~ 0 → 0
    entropy_score = min(100, (entropy / 2.0) * 100) if max_entropy > 0 else 0

    # 3. Score de variedade (mais estruturas usadas = melhor)
    # 5+ estruturas = 100, 1 estrutura = 0
    if unique_count >= 5:
        variety_score = 100.0
    elif unique_count == 1:
        variety_score = 0.0
    else:
        variety_score = (unique_count - 1) / 4.0 * 100

    # Penalidade extra: se < 3 estruturas com 10+ videos
    if unique_count < 3 and total >= 10:
        variety_score = max(0, variety_score - 20)

    # Score combinado
    score = dominance_score * 0.50 + entropy_score * 0.35 + variety_score * 0.15
    score = round(max(0, min(100, score)), 1)

    return {
        "score": score,
        "metrics": {
            "distribution": distribution,
            "dominant": dominant,
            "dominant_pct": round(dominant_pct * 100, 1),
            "unique_count": unique_count,
            "entropy": round(entropy, 2),
            "max_entropy": round(max_entropy, 2),
            "total_videos": total
        }
    }


# =============================================================================
# ETAPA 2: CALCULO DO SCORE DE TITULOS
# =============================================================================

def _jaccard_similarity(words_a: List[str], words_b: List[str]) -> float:
    """Calcula Jaccard similarity entre dois conjuntos de palavras."""
    set_a = set(words_a)
    set_b = set(words_b)
    if not set_a and not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def _detect_serial_pattern(title: str) -> bool:
    """Detecta se um titulo tem padrao serial (Parte X, Ep X, #X, etc)."""
    patterns = [
        r'\bpart(?:e)?\s*\d+',
        r'\bep(?:isode|isodio)?\s*\.?\s*\d+',
        r'#\d+',
        r'\bvol(?:ume)?\s*\.?\s*\d+',
        r'\bcap(?:itulo)?\s*\.?\s*\d+',
        r'\bteil\s*\d+',
        r'\bpartie\s*\d+',
    ]
    normalized = title.lower()
    return any(re.search(p, normalized) for p in patterns)


def _find_near_duplicate_groups(titles: List[str], threshold: float = 0.75) -> List[List[int]]:
    """
    Encontra grupos de titulos que diferem por 1-2 palavras.
    Retorna indices dos titulos agrupados.
    """
    normalized = [_normalize_title(t).split() for t in titles]
    groups = []
    used = set()

    for i in range(len(normalized)):
        if i in used:
            continue
        group = [i]
        for j in range(i + 1, len(normalized)):
            if j in used:
                continue
            sim = _jaccard_similarity(normalized[i], normalized[j])
            if sim >= threshold:
                group.append(j)
                used.add(j)
        if len(group) > 1:
            groups.append(group)
            used.add(i)

    return groups


def compute_title_score(titles: List[str]) -> Dict:
    """
    Calcula score de diversidade de titulos (0-100).
    Score alto = titulos variados. Score baixo = titulos repetitivos.

    Args:
        titles: Lista de titulos dos videos

    Returns:
        {
            "score": float (0-100),
            "metrics": {
                "avg_similarity": float,
                "serial_count": int,
                "serial_pct": float,
                "top_keyword": str,
                "top_keyword_pct": float,
                "length_stdev": float,
                "avg_length": float,
                "total_titles": int
            },
            "similar_pairs": [(title_a, title_b, similarity), ...],
            "serial_titles": [str, ...],
            "near_duplicate_groups": [[str, ...], ...]
        }
    """
    if not titles or len(titles) < 2:
        return {
            "score": 50.0,
            "metrics": {
                "avg_similarity": 0,
                "serial_count": 0,
                "serial_pct": 0,
                "top_keyword": None,
                "top_keyword_pct": 0,
                "length_stdev": 0,
                "avg_length": 0,
                "total_titles": len(titles) if titles else 0
            },
            "similar_pairs": [],
            "serial_titles": [],
            "near_duplicate_groups": []
        }

    total = len(titles)
    normalized_words = [_normalize_title(t).split() for t in titles]

    # --- 1. Similaridade pairwise (Jaccard) ---
    similarities = []
    similar_pairs = []
    for i in range(len(normalized_words)):
        for j in range(i + 1, len(normalized_words)):
            sim = _jaccard_similarity(normalized_words[i], normalized_words[j])
            similarities.append(sim)
            if sim >= 0.5:  # Guardar pares com alta similaridade
                similar_pairs.append((titles[i], titles[j], round(sim * 100, 1)))

    avg_similarity = statistics.mean(similarities) if similarities else 0

    # Score: dissimilaridade (invertido)
    # avg_sim < 0.10 → 100 (muito diferentes)
    # avg_sim > 0.50 → 0 (muito parecidos)
    if avg_similarity <= 0.10:
        similarity_score = 100.0
    elif avg_similarity >= 0.50:
        similarity_score = 0.0
    else:
        similarity_score = max(0, 100 * (0.50 - avg_similarity) / (0.50 - 0.10))

    # --- 2. Padrao serial ---
    serial_titles = [t for t in titles if _detect_serial_pattern(t)]
    serial_count = len(serial_titles)
    serial_pct = serial_count / total

    # Score: menos serial = melhor
    # < 5% serial → 100
    # > 50% serial → 0
    if serial_pct <= 0.05:
        serial_score = 100.0
    elif serial_pct >= 0.50:
        serial_score = 0.0
    else:
        serial_score = max(0, 100 * (0.50 - serial_pct) / (0.50 - 0.05))

    # --- 3. Near-duplicate groups ---
    near_dup_groups = _find_near_duplicate_groups(titles, threshold=0.75)
    near_dup_titles = [[titles[idx] for idx in group] for group in near_dup_groups]

    # --- 4. Keyword stuffing ---
    all_words = []
    for words in normalized_words:
        all_words.extend([w for w in words if w not in STOPWORDS and len(w) > 2])

    word_counter = Counter(all_words)
    top_keyword = None
    top_keyword_pct = 0
    if word_counter:
        top_keyword, top_count = word_counter.most_common(1)[0]
        top_keyword_pct = top_count / total

    # Score: menos keyword stuffing = melhor
    # freq < 0.25 → 100
    # freq > 0.70 → 0
    if top_keyword_pct <= 0.25:
        keyword_score = 100.0
    elif top_keyword_pct >= 0.70:
        keyword_score = 0.0
    else:
        keyword_score = max(0, 100 * (0.70 - top_keyword_pct) / (0.70 - 0.25))

    # --- 5. Variedade de comprimento ---
    lengths = [len(t) for t in titles]
    avg_length = statistics.mean(lengths)
    length_stdev = statistics.stdev(lengths) if len(lengths) > 1 else 0

    # Score: mais variacao = melhor
    # stdev > 15 → 100
    # stdev < 3 → 0
    if length_stdev >= 15:
        length_score = 100.0
    elif length_stdev <= 3:
        length_score = 0.0
    else:
        length_score = max(0, 100 * (length_stdev - 3) / (15 - 3))

    # Score combinado
    score = (similarity_score * 0.40 +
             serial_score * 0.25 +
             keyword_score * 0.20 +
             length_score * 0.15)
    score = round(max(0, min(100, score)), 1)

    # Ordenar pares por similaridade (mais similares primeiro)
    similar_pairs.sort(key=lambda x: x[2], reverse=True)

    return {
        "score": score,
        "metrics": {
            "avg_similarity": round(avg_similarity * 100, 1),
            "serial_count": serial_count,
            "serial_pct": round(serial_pct * 100, 1),
            "top_keyword": top_keyword,
            "top_keyword_pct": round(top_keyword_pct * 100, 1),
            "length_stdev": round(length_stdev, 1),
            "avg_length": round(avg_length, 1),
            "total_titles": total
        },
        "similar_pairs": similar_pairs[:10],  # Top 10
        "serial_titles": serial_titles,
        "near_duplicate_groups": near_dup_titles
    }


# =============================================================================
# ETAPA 3: SCORE COMPOSTO + ALERTAS
# =============================================================================

def compute_composite_score(structure_score: float, title_score: float) -> Dict:
    """Calcula score final e nivel."""
    score = round(structure_score * STRUCTURE_WEIGHT + title_score * TITLE_WEIGHT, 1)

    if score >= LEVEL_EXCELENTE:
        level = "excelente"
    elif score >= LEVEL_BOM:
        level = "bom"
    elif score >= LEVEL_ATENCAO:
        level = "atencao"
    elif score >= LEVEL_RISCO:
        level = "risco"
    else:
        level = "critico"

    return {"score": score, "level": level}


def generate_alerts(
    composite: Dict,
    structure_result: Dict,
    title_result: Dict,
    previous_score: Optional[float] = None
) -> List[Dict]:
    """Gera alertas baseados nos scores."""
    alerts = []
    score = composite["score"]

    # Alerta de threshold
    if score < ALERT_SCORE_THRESHOLD:
        alerts.append({
            "type": "threshold",
            "level": composite["level"],
            "message": f"Score {score}/100 - canal na zona de {composite['level'].upper()}"
        })

    # Alerta de fator individual
    if structure_result["score"] < ALERT_FACTOR_THRESHOLD:
        dominant = structure_result.get("metrics", {}).get("dominant", "?")
        dominant_pct = structure_result.get("metrics", {}).get("dominant_pct", 0)
        alerts.append({
            "type": "factor",
            "factor": "estruturas",
            "score": structure_result["score"],
            "message": f"Estruturas ({structure_result['score']}/100) - "
                       f"copy muito engessada, {dominant} "
                       f"domina com {dominant_pct}%"
        })

    if title_result["score"] < ALERT_FACTOR_THRESHOLD:
        avg_sim = title_result.get("metrics", {}).get("avg_similarity", 0)
        alerts.append({
            "type": "factor",
            "factor": "titulos",
            "score": title_result["score"],
            "message": f"Titulos ({title_result['score']}/100) - "
                       f"similaridade media de {avg_sim}%"
        })

    # Alerta de queda (spike)
    if previous_score is not None:
        diff = previous_score - score
        if diff > ALERT_SPIKE_THRESHOLD:
            alerts.append({
                "type": "spike",
                "previous": previous_score,
                "current": score,
                "message": f"Score caiu {diff:.1f} pontos (de {previous_score} para {score})"
            })

    return alerts


# =============================================================================
# ETAPA 4: COMPARACAO COM ANTERIOR (MEMORIA CUMULATIVA)
# =============================================================================

def compare_with_previous(channel_id: str, current_score: float) -> Optional[Dict]:
    """
    Busca a ultima analise do canal e compara.
    Memoria cumulativa: cada analise carrega o relatorio anterior.
    """
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/authenticity_analysis_runs",
        params={
            "channel_id": f"eq.{channel_id}",
            "select": "run_date,authenticity_score,authenticity_level,"
                      "structure_score,title_score,results_json,report_text",
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

    return {
        "previous_date": prev.get("run_date", ""),
        "previous_score": prev.get("authenticity_score"),
        "previous_level": prev.get("authenticity_level"),
        "previous_structure_score": prev.get("structure_score"),
        "previous_title_score": prev.get("title_score"),
        "previous_report": prev.get("report_text", ""),
        "previous_results": prev_results,
        "score_diff": round(current_score - (prev.get("authenticity_score") or current_score), 1)
    }


# =============================================================================
# ETAPA 5: ANALISE LLM
# =============================================================================

def generate_llm_analysis(
    channel_name: str,
    channel_info: Dict,
    composite: Dict,
    structure_result: Dict,
    title_result: Dict,
    titles: List[str],
    alerts: List[Dict],
    comparison: Optional[Dict]
) -> Optional[Dict]:
    """
    Envia dados para GPT-4o-mini e recebe diagnostico + recomendacoes.

    Returns:
        {"diagnostico": str, "recomendacoes": str, "tendencias": str}
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY nao configurada - pulando analise LLM")
        return None

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
    except ImportError:
        logger.error("openai nao instalado")
        return None

    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    subnicho = channel_info.get("subnicho", "N/A")
    lingua = channel_info.get("lingua", "N/A")

    # Montar bloco de dados
    struct_metrics = structure_result["metrics"]
    title_metrics = title_result["metrics"]

    dist_lines = []
    for letter in "ABCDEFG":
        count = struct_metrics["distribution"].get(letter, 0)
        pct = (count / struct_metrics["total_videos"] * 100) if struct_metrics["total_videos"] > 0 else 0
        if count > 0:
            dist_lines.append(f"  {letter}: {count} videos ({pct:.0f}%)")
        else:
            dist_lines.append(f"  {letter}: 0 videos (0%)")

    similar_pairs_text = ""
    if title_result.get("similar_pairs"):
        pairs = title_result["similar_pairs"][:5]
        pair_lines = [f'  "{p[0]}" vs "{p[1]}" ({p[2]}% similar)' for p in pairs]
        similar_pairs_text = "\n".join(pair_lines)
    else:
        similar_pairs_text = "  Nenhum par com similaridade acima de 50%"

    near_dup_text = ""
    if title_result.get("near_duplicate_groups"):
        for i, group in enumerate(title_result["near_duplicate_groups"][:3]):
            near_dup_text += f"\n  Grupo {i+1} ({len(group)} titulos):\n"
            for t in group[:5]:
                near_dup_text += f'    - "{t}"\n'

    serial_text = ""
    if title_result.get("serial_titles"):
        serial_text = "\n".join([f'  - "{t}"' for t in title_result["serial_titles"][:5]])

    titles_list = "\n".join([f"  {i+1}. {t}" for i, t in enumerate(titles)])

    alerts_text = ""
    if alerts:
        alerts_text = "\n".join([f"  ! {a['message']}" for a in alerts])
    else:
        alerts_text = "  Nenhum alerta"

    previous_block = ""
    if comparison and comparison.get("previous_report"):
        previous_block = f"""
RELATORIO ANTERIOR ({comparison.get('previous_date', 'N/A')}):
Score anterior: {comparison.get('previous_score')}/100 ({comparison.get('previous_level')})
  Estruturas: {comparison.get('previous_structure_score')}/100
  Titulos: {comparison.get('previous_title_score')}/100
Diferenca: {comparison.get('score_diff'):+.1f} pontos

RELATORIO ANTERIOR COMPLETO (MEMORIA ACUMULATIVA):
{comparison['previous_report']}
"""

    data_block = f"""CANAL: {channel_name}
SUBNICHO: {subnicho}
LINGUA: {lingua}

SCORE GERAL DE AUTENTICIDADE: {composite['score']}/100 ({composite['level'].upper()})

FATOR 1 - ESTRUTURAS DE COPY (score: {structure_result['score']}/100, peso: 50%):
  Estruturas usadas: {struct_metrics['unique_count']} de 7 possiveis
  Dominante: {struct_metrics['dominant']} com {struct_metrics['dominant_pct']}%
  Entropia: {struct_metrics['entropy']} / {struct_metrics['max_entropy']} ({(struct_metrics['entropy']/struct_metrics['max_entropy']*100):.0f}% do maximo)
  Distribuicao:
{chr(10).join(dist_lines)}

FATOR 2 - TITULOS (score: {title_result['score']}/100, peso: 50%):
  Similaridade media: {title_metrics['avg_similarity']}%
  Padrao serial: {title_metrics['serial_count']}/{title_metrics['total_titles']} titulos ({title_metrics['serial_pct']}%)
  Keyword dominante: "{title_metrics['top_keyword']}" em {title_metrics['top_keyword_pct']}% dos titulos
  Comprimento: media {title_metrics['avg_length']} chars, desvio {title_metrics['length_stdev']}

  Pares mais similares:
{similar_pairs_text}
{f'  Grupos de titulos quase duplicados:{near_dup_text}' if near_dup_text else ''}
{f'  Titulos com padrao serial:{chr(10)}{serial_text}' if serial_text else ''}

ALERTAS:
{alerts_text}

LISTA COMPLETA DE TITULOS ({len(titles)} videos):
{titles_list}

{previous_block}"""

    system_prompt = """Voce e um perito em identificar padroes de conteudo inautentico no YouTube.

O YouTube flagga canais que parecem "produzidos em massa, baseados em template, facilmente replicaveis em escala". Os triggers incluem:
- Template Persistence: mesma estrutura em 80%+ dos videos
- Serial Redundancy: titulos "Parte 1/2/3" ou que diferem por 1-2 palavras
- Metadata Clustering: padroes repetitivos nos titulos
- Keyword Stuffing: mesma palavra dominando todos os titulos

Voce recebe os dados de UM canal e deve produzir EXATAMENTE 3 blocos, separados pelos marcadores:

[DIAGNOSTICO]
Paragrafos sobre o estado atual de autenticidade do canal:
- Quais fatores sao os mais preocupantes (ou fortes) e por que
- Se o score justifica acao imediata ou monitoramento
- Pontos especificos de atencao baseados nos dados

[RECOMENDACOES]
Acoes CONCRETAS para melhorar o score, cada uma com prioridade [ALTA], [MEDIA] ou [BAIXA]:
- Cada recomendacao DEVE citar dados especificos (numeros, titulos reais, estruturas)
- Sugestoes praticas de como diversificar
- NAO invente dados - use APENAS o que foi fornecido

[TENDENCIAS]
(SO se houver relatorio anterior no bloco RELATORIO ANTERIOR acima)
- Evolucao do score vs anterior
- Se recomendacoes anteriores foram implementadas
- Padroes que melhoraram ou pioraram
Se NAO houver relatorio anterior, escreva: "Primeira analise. Sem dados anteriores para comparacao."

REGRAS:
- Seja FACTUAL - cite numeros dos dados fornecidos
- NAO invente informacoes
- Responda em portugues
- Seja direto e objetivo
- NAO repita tabelas ou dados que ja estao no relatorio numerico"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": data_block}
            ],
            temperature=0.3,
            max_tokens=3000
        )

        text = response.choices[0].message.content.strip()

        # Parse os 3 blocos
        diagnostico = ""
        recomendacoes = ""
        tendencias = ""

        if "[DIAGNOSTICO]" in text:
            after_diag = text.split("[DIAGNOSTICO]", 1)[1]
            if "[RECOMENDACOES]" in after_diag:
                diagnostico = after_diag.split("[RECOMENDACOES]", 1)[0].strip()
                after_rec = after_diag.split("[RECOMENDACOES]", 1)[1]
                if "[TENDENCIAS]" in after_rec:
                    recomendacoes = after_rec.split("[TENDENCIAS]", 1)[0].strip()
                    tendencias = after_rec.split("[TENDENCIAS]", 1)[1].strip()
                else:
                    recomendacoes = after_rec.strip()
            else:
                diagnostico = after_diag.strip()
        else:
            diagnostico = text

        return {
            "diagnostico": diagnostico,
            "recomendacoes": recomendacoes,
            "tendencias": tendencias
        }

    except Exception as e:
        logger.error(f"Erro na LLM: {e}")
        return None


# =============================================================================
# ETAPA 6: GERACAO DO RELATORIO
# =============================================================================

def generate_report(
    channel_name: str,
    composite: Dict,
    structure_result: Dict,
    title_result: Dict,
    total_sheet: int,
    alerts: List[Dict],
    llm_insights: Optional[Dict],
    comparison: Optional[Dict]
) -> str:
    """Gera relatorio formatado de autenticidade."""
    now = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    struct_m = structure_result["metrics"]
    title_m = title_result["metrics"]

    level_label = {
        "excelente": "EXCELENTE",
        "bom": "BOM",
        "atencao": "ATENCAO",
        "risco": "RISCO",
        "critico": "CRITICO"
    }

    report = []
    report.append("=" * 60)
    report.append(f"SCORE DE AUTENTICIDADE | {channel_name} | {now}")
    report.append("=" * 60)
    report.append("")
    report.append(f"SCORE GERAL: {composite['score']}/100 - {level_label.get(composite['level'], composite['level'])}")
    report.append(f"Videos analisados: {total_sheet}")
    report.append("")

    # Scores por fator
    struct_contrib = round(structure_result['score'] * STRUCTURE_WEIGHT, 1)
    title_contrib = round(title_result['score'] * TITLE_WEIGHT, 1)

    report.append(" Fator                  Score    Peso    Contribuicao")
    report.append(" " + "-" * 55)
    report.append(f" Estruturas de Copy     {structure_result['score']}/100   50%     {struct_contrib}")
    report.append(f" Titulos                {title_result['score']}/100   50%     {title_contrib}")
    report.append(f"                               TOTAL:   {composite['score']}/100")
    report.append("")

    # Detalhes Estruturas
    report.append("--- ESTRUTURAS ({}/100) ---".format(structure_result['score']))
    report.append("")
    report.append("  Distribuicao:")
    for letter in "ABCDEFG":
        count = struct_m["distribution"].get(letter, 0)
        pct = (count / struct_m["total_videos"] * 100) if struct_m["total_videos"] > 0 else 0
        bar_len = int(pct / 5)
        bar = "#" * bar_len + "." * (20 - bar_len)
        if count > 0:
            report.append(f"    {letter}: {count:>3} videos ({pct:>4.0f}%)  {bar}")
        else:
            report.append(f"    {letter}:   0 videos (  0%)  {bar}")

    report.append("")
    report.append(f"  Estruturas usadas: {struct_m['unique_count']} de 7")
    report.append(f"  Dominante: {struct_m['dominant']} com {struct_m['dominant_pct']}%")
    report.append(f"  Entropia: {struct_m['entropy']} / {struct_m['max_entropy']}")
    report.append("")

    # Detalhes Titulos
    report.append("--- TITULOS ({}/100) ---".format(title_result['score']))
    report.append("")
    report.append(f"  Similaridade media: {title_m['avg_similarity']}%")

    if title_result.get("near_duplicate_groups"):
        report.append("")
        report.append("  Grupos de titulos quase duplicados:")
        for i, group in enumerate(title_result["near_duplicate_groups"][:3]):
            report.append(f"    Grupo {i+1} ({len(group)} titulos):")
            for t in group[:5]:
                report.append(f'      - "{t}"')

    if title_result.get("serial_titles"):
        report.append("")
        report.append(f"  Padrao serial: {title_m['serial_count']} titulos ({title_m['serial_pct']}%)")
        for t in title_result["serial_titles"][:5]:
            report.append(f'    - "{t}"')

    if title_m.get("top_keyword"):
        report.append("")
        report.append(f'  Keyword dominante: "{title_m["top_keyword"]}" em {title_m["top_keyword_pct"]}% dos titulos')

    if title_result.get("similar_pairs"):
        report.append("")
        report.append("  Pares mais similares:")
        for pair in title_result["similar_pairs"][:5]:
            report.append(f'    "{pair[0]}"')
            report.append(f'    vs "{pair[1]}" ({pair[2]}%)')
            report.append("")

    report.append(f"  Comprimento: media {title_m['avg_length']} chars, desvio {title_m['length_stdev']}")
    report.append("")

    # Alertas
    if alerts:
        report.append("--- ALERTAS ---")
        report.append("")
        for a in alerts:
            report.append(f"  ! {a['message']}")
        report.append("")

    # LLM
    if llm_insights:
        if llm_insights.get("diagnostico"):
            report.append("--- DIAGNOSTICO ---")
            report.append("")
            report.append(llm_insights["diagnostico"])
            report.append("")

        if llm_insights.get("recomendacoes"):
            report.append("--- RECOMENDACOES ---")
            report.append("")
            report.append(llm_insights["recomendacoes"])
            report.append("")

        if llm_insights.get("tendencias"):
            report.append("--- TENDENCIAS ---")
            report.append("")
            report.append(llm_insights["tendencias"])
            report.append("")

    # Comparacao
    if comparison:
        report.append("--- VS ANTERIOR ---")
        report.append("")
        prev_date = comparison.get("previous_date", "N/A")
        if isinstance(prev_date, str) and "T" in prev_date:
            prev_date = prev_date.split("T")[0]
        report.append(f"  Analise anterior: {prev_date}")
        report.append(f"  Score anterior: {comparison.get('previous_score')}/100 ({comparison.get('previous_level')})")
        report.append(f"  Diferenca: {comparison.get('score_diff'):+.1f} pontos")

        prev_struct = comparison.get("previous_structure_score")
        prev_title = comparison.get("previous_title_score")
        if prev_struct is not None:
            struct_diff = structure_result['score'] - prev_struct
            report.append(f"  Estruturas: {prev_struct} → {structure_result['score']} ({struct_diff:+.1f})")
        if prev_title is not None:
            title_diff = title_result['score'] - prev_title
            report.append(f"  Titulos: {prev_title} → {title_result['score']} ({title_diff:+.1f})")
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
    composite: Dict,
    structure_result: Dict,
    title_result: Dict,
    alerts: List[Dict],
    report_text: str,
    total_videos: int,
    comparison: Optional[Dict] = None
) -> Optional[int]:
    """Salva analise no banco."""

    # Serializar comparison sem previous_report (evitar duplicacao)
    comparison_serialized = None
    if comparison:
        comparison_serialized = {
            "previous_date": comparison.get("previous_date"),
            "previous_score": comparison.get("previous_score"),
            "previous_level": comparison.get("previous_level"),
            "previous_structure_score": comparison.get("previous_structure_score"),
            "previous_title_score": comparison.get("previous_title_score"),
            "score_diff": comparison.get("score_diff")
        }

    run_data = {
        "channel_id": channel_id,
        "channel_name": channel_name,
        "authenticity_score": composite["score"],
        "authenticity_level": composite["level"],
        "structure_score": structure_result["score"],
        "title_score": title_result["score"],
        "total_videos_analyzed": total_videos,
        "has_alerts": len(alerts) > 0,
        "alert_count": len(alerts),
        "results_json": json.dumps({
            "structure": {
                "score": structure_result["score"],
                "metrics": structure_result["metrics"]
            },
            "titles": {
                "score": title_result["score"],
                "metrics": title_result["metrics"],
                "similar_pairs": title_result.get("similar_pairs", []),
                "serial_titles": title_result.get("serial_titles", []),
                "near_duplicate_groups": title_result.get("near_duplicate_groups", [])
            },
            "alerts": alerts,
            "comparison": comparison_serialized
        }),
        "report_text": report_text
    }

    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/authenticity_analysis_runs",
        headers=SUPABASE_HEADERS,
        json=run_data
    )

    if resp.status_code not in [200, 201]:
        logger.error(f"Erro ao salvar analise de autenticidade: {resp.status_code} - {resp.text[:200]}")
        return None

    result = resp.json()
    run_id = result[0]["id"] if result else None
    logger.info(f"Analise de autenticidade salva: run_id={run_id}")
    return run_id


# =============================================================================
# ETAPA 8: FUNCAO PRINCIPAL
# =============================================================================

def run_analysis(channel_id: str) -> Dict:
    """
    Executa analise completa de autenticidade para um canal.

    Returns:
        {
            "success": bool,
            "channel_id": str,
            "channel_name": str,
            "run_id": int,
            "report": str,
            "score": float,
            "level": str,
            "alerts": [...],
            "error": str (se falhou)
        }
    """
    logger.info(f"{'='*50}")
    logger.info(f"AUTENTICIDADE: Iniciando para canal {channel_id}")
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

    # 2. Ler planilha (TODAS as linhas com coluna A preenchida)
    sheet_data = read_copy_structures(spreadsheet_id)
    if not sheet_data:
        return {"success": False, "error": f"Nenhum video com estrutura de copy na planilha"}

    if len(sheet_data) < 3:
        return {"success": False, "error": f"Minimo 3 videos necessarios, encontrados: {len(sheet_data)}"}

    structures = [item["structure"] for item in sheet_data]
    titles = [item["title"] for item in sheet_data]

    # 3. Calcular scores
    structure_result = compute_structure_score(structures)
    title_result = compute_title_score(titles)
    composite = compute_composite_score(structure_result["score"], title_result["score"])

    # 4. Comparar com anterior
    comparison = compare_with_previous(channel_id, composite["score"])
    previous_score = comparison.get("previous_score") if comparison else None

    # 5. Gerar alertas
    alerts = generate_alerts(composite, structure_result, title_result, previous_score)

    # 6. LLM
    llm_insights = generate_llm_analysis(
        channel_name, channel_info, composite,
        structure_result, title_result, titles,
        alerts, comparison
    )

    # 7. Gerar relatorio
    report = generate_report(
        channel_name, composite, structure_result, title_result,
        len(sheet_data), alerts, llm_insights, comparison
    )

    # 8. Salvar
    run_id = save_analysis(
        channel_id, channel_name, composite,
        structure_result, title_result, alerts,
        report, len(sheet_data), comparison
    )

    logger.info(f"AUTENTICIDADE COMPLETA: {channel_name} | Score: {composite['score']}/100 ({composite['level']})")

    return {
        "success": True,
        "channel_id": channel_id,
        "channel_name": channel_name,
        "run_id": run_id,
        "report": report,
        "score": composite["score"],
        "level": composite["level"],
        "alerts": alerts,
        "summary": {
            "authenticity_score": composite["score"],
            "authenticity_level": composite["level"],
            "structure_score": structure_result["score"],
            "title_score": title_result["score"],
            "total_videos": len(sheet_data),
            "alert_count": len(alerts)
        }
    }


# =============================================================================
# FUNCOES DE CONSULTA (usadas pelos endpoints)
# =============================================================================

def get_latest_analysis(channel_id: str) -> Optional[Dict]:
    """Retorna a analise de autenticidade mais recente."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/authenticity_analysis_runs",
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
        if isinstance(row.get("results_json"), str):
            row["results_json"] = json.loads(row["results_json"])
        return row
    return None


def get_analysis_history(channel_id: str, limit: int = 20, offset: int = 0) -> Dict:
    """Retorna historico paginado."""
    # Contar total
    count_resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/authenticity_analysis_runs",
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
        f"{SUPABASE_URL}/rest/v1/authenticity_analysis_runs",
        params={
            "channel_id": f"eq.{channel_id}",
            "select": "id,channel_name,run_date,authenticity_score,authenticity_level,"
                      "structure_score,title_score,total_videos_analyzed,has_alerts,alert_count",
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


def get_risk_overview() -> Dict:
    """Retorna overview de autenticidade de todos os canais."""
    # Buscar a analise mais recente de cada canal
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/authenticity_analysis_runs",
        params={
            "select": "channel_id,channel_name,authenticity_score,authenticity_level,"
                      "structure_score,title_score,has_alerts,run_date",
            "order": "run_date.desc",
            "limit": "500"
        },
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    )

    if resp.status_code != 200:
        return {"channels": [], "summary": {}}

    all_runs = resp.json()

    # Deduplicar: manter apenas a mais recente por channel_id
    seen = {}
    for run in all_runs:
        cid = run.get("channel_id")
        if cid and cid not in seen:
            seen[cid] = run

    channels = sorted(seen.values(), key=lambda x: x.get("authenticity_score") or 0)

    # Summary
    scores = [c["authenticity_score"] for c in channels if c.get("authenticity_score") is not None]
    summary = {
        "total_channels": len(channels),
        "avg_score": round(statistics.mean(scores), 1) if scores else 0,
        "min_score": min(scores) if scores else 0,
        "max_score": max(scores) if scores else 0,
        "critico": sum(1 for s in scores if s < LEVEL_RISCO),
        "risco": sum(1 for s in scores if LEVEL_RISCO <= s < LEVEL_ATENCAO),
        "atencao": sum(1 for s in scores if LEVEL_ATENCAO <= s < LEVEL_BOM),
        "bom": sum(1 for s in scores if LEVEL_BOM <= s < LEVEL_EXCELENTE),
        "excelente": sum(1 for s in scores if s >= LEVEL_EXCELENTE),
        "with_alerts": sum(1 for c in channels if c.get("has_alerts"))
    }

    return {"channels": channels, "summary": summary}

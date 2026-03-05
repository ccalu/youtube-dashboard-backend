"""
Agente 4 — Motores Psicologicos
Camada 2 (Analise Especializada)

Gera analise narrativa dos motores psicologicos a partir do output do Agente 3 (Temas).
Depende de theme_analysis_runs existir para o canal.
"""

import os
import json
import logging
import requests
from datetime import datetime, timezone
from typing import List, Dict, Optional

from copy_analysis_agent import (
    _get_channel_info,
    SUPABASE_URL,
    SUPABASE_KEY,
)
from theme_agent import _count_motors, _format_motor_counts

logger = logging.getLogger("motor_agent")


# =============================================================================
# SYSTEM PROMPT — LLM MOTORES
# =============================================================================

SYSTEM_PROMPT_MOTORES = """Voce e um estrategista de conteudo YouTube especializado em transformar analises de motores psicologicos em ACOES CONCRETAS. Voce trabalha para uma operacao que gerencia dezenas de canais YouTube simultaneamente.

IMPORTANTE: Voce NAO precisa descrever os motores (isso ja foi feito pelo Agente de Temas). Seu trabalho e ESTRATEGICO e PRESCRITIVO -- transformar a analise em decisoes.

=== O QUE VOCE RECEBE ===

1. CATALOGO DE MOTORES -- cada motor ja descrito com vocabulario, correlacoes (score/CTR COM vs SEM), insight psicologico
2. ANTI-PATTERNS -- padroes que matam performance, ja identificados
3. INTERACOES -- combinacoes que amplificam ou neutralizam, ja mapeadas
4. CONTAGEM DE MOTORES -- frequencia + score medio de cada motor
5. TOP DO RANKING -- melhores e piores videos para contexto
6. RELATORIO ANTERIOR (se existir) -- para comparacao e evolucao

=== SEU TRABALHO ===

1. FORMULA DE PERFORMANCE -- qual e a "receita" deste canal? Qual combinacao de motores gera os melhores resultados? Qual combinacao e toxica?
2. RECOMENDACOES CONCRETAS -- temas especificos para produzir, com titulo-exemplo no idioma do canal, explicando quais motores cada um ativaria
3. HIPOTESES PARA TESTAR -- o que ainda nao sabemos e como descobrir
4. PRIORIDADES PRATICAS -- acoes ordenadas por impacto e urgencia

=== REGRAS CRITICAS ===

SOBRE NUMEROS:
- Todos os numeros (views, CTR, scores, contagens, percentuais, correlacoes) sao FATOS calculados pelo sistema
- NUNCA invente, altere, arredonde ou estime numeros -- use EXATAMENTE o que foi fornecido
- Use os numeros como EVIDENCIA para suas recomendacoes

SOBRE RECOMENDACOES:
- TODA recomendacao DEVE incluir exemplos concretos de TITULOS que o canal deveria produzir
- Os titulos-exemplo devem ser no IDIOMA DO CANAL (coreano, portugues, etc.)
- Explique QUAIS motores cada titulo ativaria e POR QUE funcionariam
- Identifique riscos: saturacao de cenario, dependencia de motor unico, fadiga da audiencia
- Sugira testes A/B quando houver hipoteses inconclusivas

SOBRE FORMULA:
- A formula deve ser ESPECIFICA para este canal (nao generica)
- Mostre a combinacao VENCEDORA (motores que juntos geram top performance) com evidencia
- Mostre a combinacao TOXICA (o que mata CTR) com evidencia dos anti-patterns
- Use os dados de correlacao fornecidos (score COM vs SEM motor)

=== EXEMPLO DE FORMULA DE PERFORMANCE ===

EXEMPLO BOM:

  FORMULA VENCEDORA (score medio 82/100):
    [MULHERES VITIMAS] + [REVELACAO/SEGREDO] + [PERPETRADOR PODEROSO]
    Evidencia: Os 4 videos com essa combinacao tem score medio 82 (vs media geral 55).
    O motor "Mulheres Vitimas" sozinho ja eleva o score (COM: 71, SEM: 38), mas
    combinado com "Revelacao" o efeito e multiplicado.

  FORMULA TOXICA (score medio 28/100):
    [BIOGRAFIA GENERICA] + [SEM VITIMA FEMININA] + [FIGURA DESCONHECIDA]
    Evidencia: Videos com esse padrao tem score medio 28. O anti-pattern "Titulo
    Biografico" aparece em 4 dos 5 piores videos do ranking.

EXEMPLO RUIM:

  FORMULA VENCEDORA: Usar motores fortes juntos
    (NUNCA faca isso -- sem numeros, sem evidencia, sem motores especificos)

=== EXEMPLO DE RECOMENDACOES COM TITULOS ===

EXEMPLO BOM (canal em coreano):

  PRODUZIR (ativa Motor #1 + #2 + #3):
    Titulo: "진시황이 후궁들에게 숨긴 가장 충격적인 비밀"
    (O segredo mais chocante que Qin Shi Huang escondeu sobre as concubinas)
    Motores: Mulheres Vitimas + Revelacao + Perpetrador Poderoso + Civilizacao Reconhecivel
    CTR estimado: 10%+ (baseado na correlacao dos 4 motores combinados)

EXEMPLO RUIM:

  PRODUZIR: Mais videos sobre reis e mulheres
    (NUNCA faca isso -- sem titulo concreto, sem motores explicitos)

=== EXEMPLO DE COMPARACAO COM RELATORIO ANTERIOR ===

EXEMPLO BOM:

  HIPOTESES ANTERIORES -- STATUS:
  - CONFIRMADA: "Voyeurismo + Violacao do sagrado = formula do canal"
    Evidencia: Novo video "Os crimes de Nero" (score 78) confirmou. Mesmo padrao de
    Caligula (score 85). Dupla funciona consistentemente. Correlacao COM ambos: score 81.
  - EM TESTE: "Civilizacoes asiaticas tem CTR extra"
    Amostra ainda de 1 video (China, score 72). Precisa de 2-3 videos sobre
    Japao/Mongolia/India para validar.
  - REFUTADA: "Videos sobre escravos masculinos funcionam"
    2 novos videos testaram (scores 31 e 28). Motor "Mulheres Vitimas" e insubstituivel.

=== FORMATO DE RESPOSTA -- PRIMEIRA ANALISE ===

Use os marcadores exatos abaixo.

[FORMULA DE PERFORMANCE]
FORMULA VENCEDORA: combinacao de motores que gera top performance + evidencia numerica
FORMULA TOXICA: combinacao que mata performance + evidencia dos anti-patterns
DNA DO CANAL: os 1-2 motores que definem a identidade deste canal (sem eles, nada funciona)

[RECOMENDACOES]
PRODUZIR MAIS (3-5 titulos concretos no idioma do canal + quais motores ativariam)
DIVERSIFICAR (como expandir sem perder motores-chave + 2-3 titulos-teste)
EVITAR (o que NAO produzir + por que, baseado nos anti-patterns)
REFORMULAR (temas fracos que podem ser salvos mudando o angulo/motor + titulo reformulado)

[HIPOTESES PARA TESTAR]
(3-5 hipoteses estruturadas, cada uma com:)
  - O que testar
  - Qual motor validaria
  - Titulo-teste sugerido (no idioma do canal)
  - Resultado esperado
  - Risco

[PRIORIDADES PRATICAS]
IMEDIATO (proximo 1-2 videos): titulo concreto + motores + por que priorizar
CURTO PRAZO (proximas 2 semanas): 2-3 testes a rodar
ESTRATEGICO (proximo mes): direcao do canal baseada nos padroes

=== FORMATO DE RESPOSTA -- ANALISES FUTURAS (Relatorio #2+) ===

[FORMULA DE PERFORMANCE -- ATUALIZADA]
(a formula mudou? novos motores entraram? algum enfraqueceu?)
(usar dados de correlacao atuais vs anteriores)

[EVOLUCAO DOS MOTORES]
(como cada motor evoluiu: cresceu, estavel, caiu, NOVO, EXTINTO)
(numeros anteriores vs atuais)

[HIPOTESES ANTERIORES -- STATUS]
(CONFIRMADA / EM TESTE / REFUTADA -- cada uma com evidencia concreta)

[RECOMENDACOES]
(mesmo formato da primeira analise, baseado nos novos dados)

[NOVAS HIPOTESES]
(hipoteses geradas pelos novos padroes observados)

[PRIORIDADES PRATICAS]
(atualizadas com base na evolucao)"""


# =============================================================================
# FORMATACAO DE DADOS PARA PROMPTS
# =============================================================================

def _format_merged_for_prompt(merged: List[Dict], avg_ctr_str: str) -> str:
    """Formata dados merged (ranking + temas) como texto para o user prompt da LLM MOTORES."""
    lines = []
    for v in merged:
        ctr_str = ""
        if v.get("ctr") is not None:
            ctr_str = f" | CTR: {v['ctr']:.1f}%"
            if v.get("ctr_diff") is not None:
                sign = "+" if v["ctr_diff"] >= 0 else ""
                ctr_str += f" (canal: {avg_ctr_str}% | {sign}{v['ctr_diff']:.1f}pp)"

        motores_str = ", ".join(v.get("motores", [])) if v.get("motores") else "N/A"

        lines.append(
            f"#{v['rank']} | Score: {v['score']:.0f}/100 | Views: {v['views']:,}{ctr_str}\n"
            f"    Titulo: \"{v['title']}\"\n"
            f"    Tema: {v['tema']}\n"
            f"    Motores: {motores_str}"
        )

    return "\n\n".join(lines)


# =============================================================================
# LOAD DATA
# =============================================================================

def _load_theme_run(channel_id: str) -> Optional[Dict]:
    """Busca o ultimo theme_analysis_runs para este canal."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/theme_analysis_runs",
        params={
            "channel_id": f"eq.{channel_id}",
            "select": "id,channel_id,channel_name,run_date,run_number,ranking_json,themes_json,analyzed_video_data,patterns_json,report_text",
            "order": "run_date.desc",
            "limit": "1",
        },
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
        }
    )
    if resp.status_code == 200 and resp.json():
        row = resp.json()[0]
        # Parse JSONB fields
        for field in ("ranking_json", "themes_json", "analyzed_video_data", "patterns_json"):
            val = row.get(field)
            if isinstance(val, str):
                try:
                    row[field] = json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    pass
        return row
    return None


def _get_previous_motor_run(channel_id: str) -> Optional[Dict]:
    """Busca o ultimo motor_analysis_runs para este canal."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/motor_analysis_runs",
        params={
            "channel_id": f"eq.{channel_id}",
            "select": "id,run_date,run_number,report_text,motor_counts_json,ranking_snapshot,total_videos,is_first_analysis",
            "order": "run_date.desc",
            "limit": "1",
        },
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
        }
    )
    if resp.status_code == 200 and resp.json():
        row = resp.json()[0]
        for field in ("motor_counts_json", "ranking_snapshot"):
            val = row.get(field)
            if isinstance(val, str):
                try:
                    row[field] = json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    pass
        return row
    return None


# =============================================================================
# LLM MOTORES
# =============================================================================

def _format_catalog_for_prompt(themes_json: Dict, motor_counts: Optional[List[Dict]] = None) -> str:
    """Formata catalogo de motores + correlacoes + anti-patterns como texto para o prompt."""
    lines = []

    # Catalogo de motores
    catalogo = themes_json.get("catalogo_motores", [])
    correlacoes = themes_json.get("correlacoes", {})
    if catalogo:
        lines.append("=== CATALOGO DE MOTORES ===")
        for i, cat in enumerate(catalogo, 1):
            motor_name = cat.get("motor", "")
            lines.append(f"\nMotor #{i}: {motor_name}")
            lines.append(f"  Descricao: {cat.get('descricao', '')}")
            # Vocabulario
            vocab = cat.get("vocabulario", [])
            if vocab:
                vocab_strs = []
                for voc in vocab:
                    orig = voc.get("original", "")
                    trad = voc.get("traducao", "")
                    if trad and trad != orig:
                        vocab_strs.append(f"{orig} ({trad})")
                    else:
                        vocab_strs.append(orig)
                lines.append(f"  Vocabulario: {', '.join(vocab_strs)}")
            # Correlacao
            corr = correlacoes.get(motor_name, {})
            if corr:
                com = corr.get("com", {})
                sem = corr.get("sem", {})
                com_str = f"COM motor ({com.get('videos', 0)} videos): score medio {com.get('score_medio', '?')}"
                sem_str = f"SEM motor ({sem.get('videos', 0)} videos): score medio {sem.get('score_medio', '?')}"
                if com.get("ctr_medio") is not None:
                    com_str += f", CTR {com['ctr_medio']}%"
                if sem.get("ctr_medio") is not None:
                    sem_str += f", CTR {sem['ctr_medio']}%"
                lines.append(f"  {com_str}")
                lines.append(f"  {sem_str}")
            # Insight
            insight = cat.get("insight_psicologico", "")
            if insight:
                lines.append(f"  Insight: {insight}")
            # Videos count
            vids = cat.get("videos_ids", [])
            if vids:
                lines.append(f"  Videos: {len(vids)} videos")

    # Motor counts (estatisticas Python)
    if motor_counts:
        lines.append("\n=== CONTAGEM DE MOTORES (dados do sistema) ===")
        counts_text = _format_motor_counts(motor_counts)
        lines.append(counts_text)

    # Anti-patterns
    anti = themes_json.get("anti_patterns", [])
    if anti:
        lines.append("\n=== ANTI-PATTERNS IDENTIFICADOS ===")
        for i, ap in enumerate(anti, 1):
            lines.append(f"\nKiller #{i}: {ap.get('pattern', '')}")
            lines.append(f"  {ap.get('descricao', '')}")
            lines.append(f"  Impacto: {ap.get('impacto', 'N/A')}")
            ex = ap.get("exemplos_video_ids", [])
            if ex:
                lines.append(f"  Exemplos: {len(ex)} videos")

    # Interacoes
    interacoes = themes_json.get("interacoes_motores", [])
    if interacoes:
        lines.append("\n=== INTERACOES ENTRE MOTORES ===")
        for inter in interacoes:
            comb = " + ".join(inter.get("combinacao", []))
            tipo = inter.get("tipo", "")
            lines.append(f"\n  {comb} [{tipo.upper()}]")
            lines.append(f"  {inter.get('explicacao', '')}")

    return "\n".join(lines)


def _call_llm(
    merged_data: List[Dict],
    channel_info: Dict,
    avg_ctr_pct: Optional[float],
    is_first_analysis: bool,
    themes_json: Optional[Dict] = None,
    changes: Optional[Dict] = None,
    motor_counts: Optional[List[Dict]] = None,
    prev_motor_counts: Optional[List[Dict]] = None,
    previous_report: Optional[str] = None,
    run_number: int = 1,
    prev_date: str = ""
) -> Optional[str]:
    """
    LLM MOTORES: gera analise estrategica (formula, recomendacoes, hipoteses, prioridades).
    Returns: texto completo do relatorio.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY nao configurada")
        return None

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
    except ImportError:
        logger.error("openai nao instalado")
        return None

    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    channel_name = channel_info.get("channel_name", "Desconhecido")
    lingua = channel_info.get("lingua", "Portugues")
    subnicho = channel_info.get("subnicho", "Geral")
    avg_ctr_str = f"{avg_ctr_pct:.1f}" if avg_ctr_pct is not None else "N/A"

    # Catalogo + correlacoes + anti-patterns formatados
    catalog_text = _format_catalog_for_prompt(themes_json or {}, motor_counts)

    # Top 5 + bottom 3 do ranking para contexto
    top5 = _format_merged_for_prompt(merged_data[:5], avg_ctr_str) if len(merged_data) >= 5 else _format_merged_for_prompt(merged_data, avg_ctr_str)
    bottom3 = _format_merged_for_prompt(merged_data[-3:], avg_ctr_str) if len(merged_data) > 5 else ""

    if is_first_analysis:
        user_prompt = f"""CANAL: {channel_name} ({lingua})
NICHO: {channel_info.get('nicho', 'Geral')} | SUBNICHO: {subnicho}
CTR MEDIO DO CANAL: {avg_ctr_str}%
TOTAL DE VIDEOS ANALISADOS: {len(merged_data)}
IDIOMA DOS TITULOS-EXEMPLO: {lingua}

{catalog_text}

=== TOP 5 VIDEOS (para contexto) ===

{top5}

=== BOTTOM 3 VIDEOS (para contexto) ===

{bottom3}

Gere o relatorio ESTRATEGICO. Esta e a PRIMEIRA analise deste canal.
Foque em: Formula de Performance, Recomendacoes com titulos no idioma {lingua}, Hipoteses, Prioridades."""

    else:
        new_videos = changes.get("new", []) if changes else []
        updated_videos = changes.get("updated", []) if changes else []

        new_text = _format_merged_for_prompt(new_videos, avg_ctr_str) if new_videos else "Nenhum video novo."

        updated_lines = []
        for v in updated_videos:
            prev_views = v.get("_prev_views", 0)
            prev_ctr = v.get("_prev_ctr")
            views_change = round((v["views"] - prev_views) / prev_views * 100, 0) if prev_views > 0 else 0
            ctr_change_str = ""
            if v.get("ctr") is not None and prev_ctr is not None:
                ctr_change = round(v["ctr"] - prev_ctr, 1)
                sign = "+" if ctr_change >= 0 else ""
                ctr_change_str = f" | CTR {prev_ctr:.1f}% -> {v['ctr']:.1f}% ({sign}{ctr_change:.1f}pp)"
            updated_lines.append(
                f"- {v['video_id']} \"{v['title']}\": Views {prev_views:,} -> {v['views']:,} "
                f"(+{views_change:.0f}%){ctr_change_str} | Score {v['score']:.0f}"
            )
        updated_text = "\n".join(updated_lines) if updated_lines else "Nenhum video com mudanca significativa."

        user_prompt = f"""CANAL: {channel_name} ({lingua})
NICHO: {channel_info.get('nicho', 'Geral')} | SUBNICHO: {subnicho}
CTR MEDIO DO CANAL: {avg_ctr_str}%
RELATORIO NUMERO: #{run_number} (anterior: #{run_number - 1}, {prev_date})
IDIOMA DOS TITULOS-EXEMPLO: {lingua}

=== BLOCO 1: RELATORIO ANTERIOR (#{run_number - 1}) ===

{previous_report or 'Nenhum relatorio anterior disponivel.'}

=== BLOCO 2: O QUE MUDOU ===

{len(new_videos)} videos NOVOS:

{new_text}

{len(updated_videos)} videos com mudanca significativa:

{updated_text}

=== BLOCO 3: DADOS GERAIS ===

{catalog_text}

TOP 5 VIDEOS ATUAIS (para contexto):

{top5}

BOTTOM 3 VIDEOS ATUAIS (para contexto):

{bottom3}

Gere o relatorio ESTRATEGICO. FOCO: Formula atualizada, Evolucao dos motores, Hipoteses anteriores (status), Recomendacoes com titulos no idioma {lingua}, Prioridades."""

    # Chamada LLM com retry
    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model=model,
                temperature=0.4,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT_MOTORES},
                    {"role": "user", "content": user_prompt}
                ]
            )

            text = response.choices[0].message.content
            logger.info(f"LLM MOTORES OK: {len(text)} chars (tentativa {attempt+1})")
            return text

        except Exception as e:
            logger.error(f"Erro LLM MOTORES tentativa {attempt+1}: {e}")

    logger.error("LLM MOTORES falhou apos 2 tentativas")
    return None


# =============================================================================
# SAVE / DELETE / QUERY
# =============================================================================

def save_analysis(
    channel_id: str,
    channel_name: str,
    report_text: str,
    motor_counts: List[Dict],
    theme_run_id: int,
    ranking_snapshot: List[Dict],
    total_videos: int,
    is_first: bool,
    run_number: int
) -> Optional[int]:
    """Salva analise de motores no banco de dados."""
    payload = {
        "channel_id": channel_id,
        "channel_name": channel_name,
        "report_text": report_text,
        "motor_counts_json": json.dumps(motor_counts, ensure_ascii=False),
        "theme_run_id": theme_run_id,
        "ranking_snapshot": json.dumps(ranking_snapshot, ensure_ascii=False),
        "total_videos": total_videos,
        "is_first_analysis": is_first,
        "run_number": run_number,
    }

    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/motor_analysis_runs",
        json=payload,
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
    )

    if resp.status_code in (200, 201):
        rows = resp.json()
        run_id = rows[0].get("id") if rows else None
        logger.info(f"Motor analysis salva: run_id={run_id}, run_number={run_number}, {total_videos} videos")
        return run_id
    else:
        logger.error(f"Erro ao salvar motor analysis: {resp.status_code} - {resp.text[:300]}")
        return None


def delete_analysis(channel_id: str, run_id: int) -> Dict:
    """Deleta um run especifico de motor_analysis_runs."""
    resp = requests.delete(
        f"{SUPABASE_URL}/rest/v1/motor_analysis_runs",
        params={
            "id": f"eq.{run_id}",
            "channel_id": f"eq.{channel_id}",
        },
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
        }
    )
    if resp.status_code in (200, 204):
        logger.info(f"Motor run {run_id} deletado para {channel_id}")
        return {"success": True, "deleted_id": run_id}
    else:
        logger.error(f"Erro ao deletar motor run {run_id}: {resp.status_code}")
        return {"success": False, "error": resp.text[:200]}


def get_latest_analysis(channel_id: str) -> Optional[Dict]:
    """Retorna a analise de motores mais recente para o canal."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/motor_analysis_runs",
        params={
            "channel_id": f"eq.{channel_id}",
            "select": "id,channel_id,channel_name,run_date,run_number,report_text,motor_counts_json,total_videos,is_first_analysis,theme_run_id",
            "order": "run_date.desc",
            "limit": "1",
        },
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
        }
    )
    if resp.status_code == 200 and resp.json():
        row = resp.json()[0]
        if isinstance(row.get("motor_counts_json"), str):
            try:
                row["motor_counts_json"] = json.loads(row["motor_counts_json"])
            except (json.JSONDecodeError, TypeError):
                pass
        return row
    return None


def get_analysis_history(channel_id: str, limit: int = 20, offset: int = 0) -> Dict:
    """Retorna historico paginado de analises de motores."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/motor_analysis_runs",
        params={
            "channel_id": f"eq.{channel_id}",
            "select": "id,channel_id,channel_name,run_date,run_number,total_videos,is_first_analysis,theme_run_id",
            "order": "run_date.desc",
            "offset": str(offset),
            "limit": str(limit),
        },
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Prefer": "count=exact",
            "Range-Unit": "items",
            "Range": f"{offset}-{offset + limit - 1}",
        }
    )
    runs = resp.json() if resp.status_code == 200 else []
    total = 0
    if "content-range" in resp.headers:
        try:
            total = int(resp.headers["content-range"].split("/")[-1])
        except (ValueError, IndexError):
            total = len(runs)
    return {"runs": runs, "total": total, "limit": limit, "offset": offset}


# =============================================================================
# DETECCAO INCREMENTAL
# =============================================================================

def _detect_changes(
    merged_data: List[Dict],
    prev_snapshot: List[Dict]
) -> Dict[str, List[Dict]]:
    """
    Compara videos atuais com snapshot do run anterior.
    Return: {new: [...], updated: [...]}
    """
    if not prev_snapshot:
        return {"new": merged_data, "updated": []}

    prev_map = {}
    for v in prev_snapshot:
        vid = v.get("video_id")
        if vid:
            prev_map[vid] = v

    new_videos = []
    updated_videos = []

    for v in merged_data:
        vid = v.get("video_id")
        prev = prev_map.get(vid)

        if prev is None:
            new_videos.append(v)
        else:
            views_changed = (
                prev.get("views") and v.get("views")
                and v["views"] > prev["views"] * 1.2
            )
            ctr_changed = (
                v.get("ctr") is not None and prev.get("ctr") is not None
                and abs(v["ctr"] - prev["ctr"]) >= 2.0
            )
            if views_changed or ctr_changed:
                v["_prev_views"] = prev.get("views", 0)
                v["_prev_ctr"] = prev.get("ctr")
                updated_videos.append(v)

    return {"new": new_videos, "updated": updated_videos}


# =============================================================================
# ORQUESTRACAO PRINCIPAL
# =============================================================================

def run_analysis(channel_id: str) -> Dict:
    """
    Agente 5 (Motores Psicologicos) — orquestrador principal.

    Fluxo:
    1. Carrega ultimo theme run (Agente 4 Temas)
    2. Reconstroi merged_data do ranking_json
    3. Conta motores
    4. Carrega motor run anterior (para comparacao)
    5. Detecta changes (novos/atualizados)
    6. Carrega themes_json (catalogo + correlacoes + anti-patterns)
    7. Chama LLM MOTORES (estrategico)
    8. Salva em motor_analysis_runs
    """
    logger.info(f"=== INICIO Agente 5 (Motores): {channel_id} ===")

    # 1. Carregar ultimo theme run
    theme_run = _load_theme_run(channel_id)
    if not theme_run:
        msg = f"Nenhuma analise de temas encontrada para {channel_id}. Rode o Agente de Temas primeiro."
        logger.error(msg)
        return {"success": False, "error": msg}

    theme_run_id = theme_run["id"]
    channel_name = theme_run.get("channel_name", "Desconhecido")

    # 2. Reconstruir merged_data do ranking_json
    merged_data = theme_run.get("ranking_json") or []
    if isinstance(merged_data, str):
        try:
            merged_data = json.loads(merged_data)
        except (json.JSONDecodeError, TypeError):
            merged_data = []

    if not merged_data:
        msg = f"Theme run {theme_run_id} nao tem ranking_json"
        logger.error(msg)
        return {"success": False, "error": msg}

    # Garantir que merged_data tem rank
    for i, v in enumerate(merged_data):
        if "rank" not in v:
            v["rank"] = i + 1

    # 3. Buscar channel_info e avg_ctr
    channel_info = _get_channel_info(channel_id)
    if not channel_info:
        channel_info = {"channel_name": channel_name, "lingua": "Portugues", "nicho": "Geral", "subnicho": "Geral"}

    # Buscar avg_ctr do canal
    avg_ctr_pct = None
    try:
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/yt_channels",
            params={
                "channel_id": f"eq.{channel_id}",
                "select": "avg_ctr",
            },
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
            }
        )
        if resp.status_code == 200 and resp.json():
            avg_ctr = resp.json()[0].get("avg_ctr")
            if avg_ctr is not None:
                avg_ctr_pct = round(avg_ctr * 100, 2)
    except Exception as e:
        logger.warning(f"Erro ao buscar avg_ctr: {e}")

    # 4. Contagem de motores
    motor_counts = _count_motors(merged_data)

    # 5. Carregar motor run anterior
    prev_motor_run = _get_previous_motor_run(channel_id)
    is_first = prev_motor_run is None
    run_number = 1 if is_first else (prev_motor_run.get("run_number", 0) + 1)

    prev_motor_counts = None
    prev_report = None
    prev_date_str = ""

    if prev_motor_run:
        prev_motor_counts = prev_motor_run.get("motor_counts_json")
        if isinstance(prev_motor_counts, str):
            try:
                prev_motor_counts = json.loads(prev_motor_counts)
            except (json.JSONDecodeError, TypeError):
                prev_motor_counts = None

        prev_report = prev_motor_run.get("report_text")

        if prev_motor_run.get("run_date"):
            try:
                pd = prev_motor_run["run_date"]
                if isinstance(pd, str) and "T" in pd:
                    prev_date_str = datetime.fromisoformat(pd.replace("Z", "+00:00")).strftime("%d/%m/%Y")
                else:
                    prev_date_str = str(pd)
            except (ValueError, TypeError):
                prev_date_str = str(prev_motor_run.get("run_date", ""))

    # Detectar changes para prompt #2+
    changes = None
    if not is_first and prev_motor_run:
        prev_snapshot = prev_motor_run.get("ranking_snapshot") or []
        if isinstance(prev_snapshot, str):
            try:
                prev_snapshot = json.loads(prev_snapshot)
            except (json.JSONDecodeError, TypeError):
                prev_snapshot = []
        changes = _detect_changes(merged_data, prev_snapshot)

    # 6. Carregar themes_json (catalogo + anti-patterns + correlacoes)
    themes_json = theme_run.get("themes_json") or {}
    if isinstance(themes_json, str):
        try:
            themes_json = json.loads(themes_json)
        except (json.JSONDecodeError, TypeError):
            themes_json = {}

    # 7. Chamar LLM MOTORES (ou skip se zero novos)
    logger.info(f"Agente 5: {channel_name} | run #{run_number} | {len(merged_data)} videos | first={is_first}")

    skip_llm = False
    if not is_first and changes is not None:
        new_count = len(changes.get("new", []))
        updated_count = len(changes.get("updated", []))
        if new_count == 0 and updated_count == 0:
            logger.info("Zero videos novos/atualizados — reutilizando relatorio anterior (skip LLM)")
            skip_llm = True

    if skip_llm:
        llm_output = prev_report
    else:
        llm_output = _call_llm(
            merged_data=merged_data,
            channel_info=channel_info,
            avg_ctr_pct=avg_ctr_pct,
            is_first_analysis=is_first,
            themes_json=themes_json,
            changes=changes,
            motor_counts=motor_counts,
            prev_motor_counts=prev_motor_counts,
            previous_report=prev_report,
            run_number=run_number,
            prev_date=prev_date_str,
        )

    if not llm_output:
        msg = "LLM MOTORES nao retornou output"
        logger.error(msg)
        return {"success": False, "error": msg}

    # 8. Salvar
    run_id = save_analysis(
        channel_id=channel_id,
        channel_name=channel_name,
        report_text=llm_output,
        motor_counts=motor_counts,
        theme_run_id=theme_run_id,
        ranking_snapshot=merged_data,
        total_videos=len(merged_data),
        is_first=is_first,
        run_number=run_number,
    )

    if run_id is None:
        logger.warning(f"Agente 5: {channel_name} — analise ok mas save falhou!")

    logger.info(
        f"=== FIM Agente 5: {channel_name} | run #{run_number} | "
        f"{len(merged_data)} videos | {len(motor_counts)} motores | "
        f"run_id={run_id} ==="
    )

    return {
        "success": run_id is not None,
        "channel_name": channel_name,
        "run_id": run_id,
        "run_number": run_number,
        "total_videos": len(merged_data),
        "motor_count": len(motor_counts),
        "is_first_analysis": is_first,
        "theme_run_id": theme_run_id,
        "report_text": llm_output,
        "report": llm_output,
    }

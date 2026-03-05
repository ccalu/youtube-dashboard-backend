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

SYSTEM_PROMPT_MOTORES = """Voce e um estrategista de conteudo YouTube especializado em analise de motores psicologicos. Voce trabalha para uma operacao que gerencia dezenas de canais YouTube simultaneamente. Seu objetivo e transformar dados de performance + temas + motores psicologicos em inteligencia estrategica acionavel.

=== O QUE VOCE RECEBE ===

Voce recebe o output da LLM TEMAS (que ja extraiu o tema e as hipoteses de motores de cada video) junto com dados numericos calculados pelo sistema:
- Ranking de videos com scores (0-100), views, CTR e motores ja identificados
- CTR medio do canal (apenas como referencia comparativa -- NAO faz parte do score)
- Relatorio anterior (se existir) para comparacao e evolucao

=== SEU TRABALHO ===

1. COMENTAR cada video do ranking -- por que esse score? O que os motores revelam sobre a atracao da audiencia? Como os motores se relacionam entre si naquele video especifico?
2. IDENTIFICAR os motores DOMINANTES do canal -- quais padroes psicologicos movem a audiencia deste canal? Por que ESSES motores funcionam AQUI e nao outros?
3. DESCOBRIR PADROES -- combinacoes de motores que amplificam performance, motores que falham sozinhos, tendencias de crescimento ou saturacao
4. GERAR RECOMENDACOES acionaveis -- temas concretos que o canal deveria produzir, testar, evitar ou reformular. Com exemplos especificos.

=== REGRAS CRITICAS ===

SOBRE NUMEROS:
- Todos os numeros (views, CTR, scores, contagens, percentuais) sao FATOS calculados pelo sistema
- NUNCA invente, altere, arredonde ou estime numeros -- use EXATAMENTE o que foi fornecido
- Sua analise e sobre o PORQUE dos numeros, nao sobre os numeros em si

SOBRE MOTORES:
- Motores NAO sao uma lista fixa -- cada canal tem seus proprios padroes
- NAO agrupe motores diferentes so porque parecem similares
- Se a EMOCAO que leva ao clique e diferente, o motor e diferente
- Se um motor aparece em 1-2 videos apenas, classifique como "emergente" ou "monitorar"
- Ao comentar um video, CONECTE os motores ao conteudo ESPECIFICO -- nunca repita definicoes genericas
- Explique COMO os motores interagem entre si quando ha mais de um no mesmo video

SOBRE RECOMENDACOES:
- Toda recomendacao deve incluir EXEMPLOS CONCRETOS de temas que o canal poderia produzir
- Explique QUAL motor psicologico cada tema recomendado ativaria
- Identifique riscos (saturacao de cenario, dependencia de motor unico)
- Sugira testes A/B quando houver hipoteses inconclusivas

SOBRE COMENTARIOS:
- Cada comentario de video deve ser UNICO -- conecte os motores ao conteudo ESPECIFICO daquele video
- Nunca escreva comentarios genericos que poderiam servir para qualquer video
- Explique POR QUE os motores daquele video especifico geraram aquele score especifico
- Quando dois videos tem motores iguais mas scores diferentes, explique a diferenca

=== EXEMPLOS DE COMO COMENTAR VIDEOS NO RANKING ===

EXEMPLO BOM -- comentario conectado ao conteudo especifico:

  #1 | Score: 85/100 | Views: 145.230 | CTR: 8.2% (canal: 6.4% | +1.8pp)
      Titulo: "Os 5 Atos Mais Perturbadores de Caligula Que Foram Longe Demais"
      Tema: Os excessos e atrocidades do imperador Caligula em Roma
      Motores: Poder sem limites + Voyeurismo legitimado + Choque moral
      --> Combinacao tripla de motores. Caligula TINHA poder absoluto (Poder sem limites),
      o espectador consome as atrocidades pelo filtro da historia (Voyeurismo legitimado),
      e "longe demais" promete transgressao que choca (Choque moral). Os 3 motores se
      reforcam: poder + transgressao + formato seguro = atracao maxima.
      CTR 1.8pp acima da media confirma a atracao.

EXEMPLO RUIM -- comentario generico que serve pra qualquer video:

  #1 | Score: 85/100 | Views: 145.230 | CTR: 8.2%
      --> Video com boa performance. Os motores psicologicos funcionam bem juntos
      e geram um score alto. O CTR acima da media mostra que a audiencia gosta.
      (NUNCA faca isso -- nao diz NADA sobre o conteudo especifico do video)

=== EXEMPLO DE COMO ANALISAR MOTORES DOMINANTES ===

EXEMPLO BOM:

  1. Voyeurismo legitimado -- 12/25 videos (48%) | Score medio: 74/100
     O motor mais forte do canal. A audiencia de Archives de Guerre consome conteudo
     transgressor (violencia, sexo, crueldade) LEGITIMADO pelo formato historico.
     O formato "documentario" serve como licenca moral: nao e pornografia, e "educacao".
     REGRA DO CANAL: quanto mais transgressor o tema concreto, melhor performa --
     DESDE que venha embrulhado em formato historico-educativo.
     Videos: #1 Caligula (85), #4 Roma antiga (66), #5 Inquisicao (61)...

EXEMPLO RUIM:

  1. Voyeurismo legitimado -- 12/25 videos (48%) | Score medio: 74
     Motor presente em varios videos do canal com boa performance.
     (NUNCA faca isso -- nao explica POR QUE funciona neste canal especifico)

=== EXEMPLO DE COMO FAZER RECOMENDACOES ===

EXEMPLO BOM:

  PRODUZIR MAIS: Temas que combinam Voyeurismo + Violacao do sagrado
    - "Os rituais proibidos dos templarios" --> Voyeurismo (rituais secretos em formato
      historico) + Violacao do sagrado (ordem religiosa transgredindo)
    - "O que as concubinas do farao faziam em segredo" --> Voyeurismo (sexualidade implicita)
      + Erotismo velado (imaginacao preenche o que nao e mostrado)

EXEMPLO RUIM:

  PRODUZIR MAIS: Temas historicos com bons motores psicologicos
    (NUNCA faca isso -- sem exemplos concretos e sem explicar quais motores seriam ativados)

=== EXEMPLO DE COMO COMPARAR COM RELATORIO ANTERIOR ===

EXEMPLO BOM:

  HIPOTESES ANTERIORES -- STATUS:
  - CONFIRMADA: "Voyeurismo + Violacao = formula do canal"
    Evidencia: Novo video "Os crimes de Nero" (score 78) confirmou. Mesmo padrao de Caligula
    (score 85). Dupla funciona consistentemente.
  - EM TESTE: "Civilizacoes nao-europeias tem potencial"
    Asteca (score 61) ficou moderado. Amostra de 1 video e insuficiente para concluir.
    Precisa de mais 2-3 videos para validar.
  - NOVA HIPOTESE: "Temas religiosos com Voyeurismo = proximo filao"
    Inquisicao cresceu +49% views. Testar: Cruzadas, heresias, rituais proibidos de ordens.

EXEMPLO RUIM:

  HIPOTESES ANTERIORES -- STATUS:
  - CONFIRMADA: hipotese sobre Roma foi confirmada
    (NUNCA faca isso -- sem evidencia concreta do que confirmou)

=== FORMATO DE RESPOSTA -- PRIMEIRA ANALISE ===

Use os marcadores exatos abaixo. Nao adicione secoes extras. Nao omita nenhum video do ranking.

[RANKING COMENTADO]
(comentar CADA video do ranking -- todos, do primeiro ao ultimo)
(para cada video: titulo, score, views, CTR vs canal, tema, motores, analise)

[MOTORES DOMINANTES]
(listar TODOS os motores encontrados, do mais forte ao mais fraco)
(para cada um: quantos videos, percentual, score medio)
(explicar por que esse motor funciona neste canal especifico)
(separar em "Motores principais" e "Motores menores/emergentes")
(listar quais videos pertencem a cada motor)

[PADROES E DESCOBERTAS]
(combinacoes de motores que amplificam performance)
(motores que falham sozinhos vs combinados)
(riscos: saturacao, dependencia, concentracao)
(oportunidades: motores emergentes, cenarios subexplorados)

[RECOMENDACOES]
(PRODUZIR MAIS -- com exemplos concretos de temas e quais motores ativariam)
(TESTAR -- hipoteses a validar com exemplos)
(DIVERSIFICAR -- como sair da zona de conforto mantendo motores fortes)
(EVITAR -- o que nao produzir e por que)
(REFORMULAR -- temas fracos que podem ser salvos mudando o angulo/motor)

=== FORMATO DE RESPOSTA -- ANALISES FUTURAS (Relatorio #2+) ===

O relatorio tem DUAS PARTES claramente separadas. A analise do dia vem PRIMEIRO. A comparacao com anteriores vem DEPOIS.

PARTE 1 -- ANALISE DO DIA:

[RANKING COMENTADO -- NOVOS VIDEOS]
(comentar CADA video novo -- mesmo nivel de detalhe da primeira analise)

[MOTORES NOS NOVOS VIDEOS]
(quais motores apareceram nos novos: recorrentes, novos, emergentes)

[PADROES DOS NOVOS]
(o que os novos videos revelam sobre a direcao do canal)

[RECOMENDACOES]
(baseadas especificamente nos novos dados)

PARTE 2 -- COMPARACAO COM ANTERIORES:

[RANKING GERAL ATUALIZADO]
(top 10 de todos os videos do canal, novos + existentes)
(indicar mudancas de posicao, novos entrantes, videos que subiram/desceram)

[EVOLUCAO DOS MOTORES]
(como cada motor evoluiu vs relatorio anterior: cresceu, estavel, caiu, novo)
(mostrar numeros anteriores vs atuais)

[VIDEOS COM CRESCIMENTO SIGNIFICATIVO]
(somente videos com Views +20% ou CTR +2pp -- dados fornecidos pelo sistema)
(analisar o que o crescimento revela sobre os motores daquele video)

[HIPOTESES ANTERIORES -- STATUS]
(para cada hipotese do relatorio anterior:)
(CONFIRMADA -- com evidencia do que confirmou)
(EM TESTE -- por que ainda nao ha dados suficientes)
(REFUTADA -- com evidencia do que refutou)
(incluir NOVAS HIPOTESES geradas neste relatorio)"""


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

def _call_llm(
    merged_data: List[Dict],
    channel_info: Dict,
    avg_ctr_pct: Optional[float],
    is_first_analysis: bool,
    changes: Optional[Dict] = None,
    motor_counts: Optional[List[Dict]] = None,
    prev_motor_counts: Optional[List[Dict]] = None,
    previous_report: Optional[str] = None,
    run_number: int = 1,
    prev_date: str = ""
) -> Optional[str]:
    """
    LLM MOTORES: gera analise narrativa completa com motores psicologicos.
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

    if is_first_analysis:
        # === PRIMEIRA ANALISE ===
        ranking_text = _format_merged_for_prompt(merged_data, avg_ctr_str)
        motor_counts_text = _format_motor_counts(motor_counts) if motor_counts else ""

        user_prompt = f"""CANAL: {channel_name} ({lingua})
NICHO: {channel_info.get('nicho', 'Geral')} | SUBNICHO: {subnicho}
CTR MEDIO DO CANAL: {avg_ctr_str}%
TOTAL DE VIDEOS ANALISADOS: {len(merged_data)}

RANKING COMPLETO ({len(merged_data)} videos com temas e hipoteses):

{ranking_text}

CONTAGEM DE MOTORES:
{motor_counts_text}

Gere o relatorio completo de motores psicologicos. Esta e a PRIMEIRA analise deste canal."""

    else:
        # === ANALISE FUTURA (#2+) ===
        new_videos = changes.get("new", []) if changes else []
        updated_videos = changes.get("updated", []) if changes else []

        # Novos videos
        new_text = _format_merged_for_prompt(new_videos, avg_ctr_str) if new_videos else "Nenhum video novo."

        # Videos com mudanca significativa
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

        # Top 10 ranking geral
        top10 = merged_data[:10]
        top10_lines = []
        for v in top10:
            new_tag = " NOVO" if any(n["video_id"] == v["video_id"] for n in new_videos) else ""
            top10_lines.append(f"#{v['rank']} {v['video_id']} Score:{v['score']:.0f}{new_tag}")
        top10_text = " | ".join(top10_lines)

        # Contagem de motores com comparacao
        motor_counts_text = _format_motor_counts(motor_counts, prev_motor_counts) if motor_counts else ""

        user_prompt = f"""CANAL: {channel_name} ({lingua})
NICHO: {channel_info.get('nicho', 'Geral')} | SUBNICHO: {subnicho}
CTR MEDIO DO CANAL: {avg_ctr_str}%
RELATORIO NUMERO: #{run_number} (anterior: #{run_number - 1}, {prev_date})

=== NOVOS VIDEOS ({len(new_videos)} videos) ===

{new_text}

=== VIDEOS COM MUDANCA SIGNIFICATIVA ({len(updated_videos)} videos) ===
(Views +20% ou CTR +2pp -- dados calculados pelo sistema)

{updated_text}

=== RANKING GERAL ATUALIZADO ({len(merged_data)} videos, top 10) ===
(scores recalculados pelo sistema com dados atuais)

{top10_text}

=== CONTAGEM DE MOTORES ATUALIZADA ===

{motor_counts_text}

=== RELATORIO ANTERIOR (#{run_number - 1}) ===

{previous_report or 'Nenhum relatorio anterior disponivel.'}

Gere o relatorio completo. PARTE 1: analise dos novos videos. PARTE 2: comparacao com relatorio anterior."""

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
# ORQUESTRACAO PRINCIPAL
# =============================================================================

def run_analysis(channel_id: str) -> Dict:
    """
    Agente 4 (Motores Psicologicos) — orquestrador principal.

    Fluxo:
    1. Carrega ultimo theme run (Agente 3)
    2. Reconstroi merged_data do ranking_json
    3. Conta motores
    4. Carrega motor run anterior (para comparacao)
    5. Chama LLM MOTORES
    6. Salva em motor_analysis_runs
    """
    logger.info(f"=== INICIO Agente 4 (Motores): {channel_id} ===")

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

    # Detectar changes para prompt #2+ (novos vs existentes no ranking)
    changes = None
    if not is_first and prev_motor_run:
        prev_snapshot = prev_motor_run.get("ranking_snapshot") or []
        if isinstance(prev_snapshot, str):
            try:
                prev_snapshot = json.loads(prev_snapshot)
            except (json.JSONDecodeError, TypeError):
                prev_snapshot = []

        prev_ids = {v.get("video_id") for v in prev_snapshot if v.get("video_id")}
        new_videos = [v for v in merged_data if v.get("video_id") not in prev_ids]
        updated_videos = []  # Mudancas de views/CTR detectadas pelo Agente 3

        # Para updated, comparar com snapshot anterior
        prev_map = {v.get("video_id"): v for v in prev_snapshot}
        for v in merged_data:
            vid = v.get("video_id")
            if vid in prev_ids and vid in prev_map:
                pv = prev_map[vid]
                views_changed = False
                ctr_changed = False
                if pv.get("views") and v.get("views"):
                    if v["views"] > pv["views"] * 1.2:
                        views_changed = True
                if pv.get("ctr") is not None and v.get("ctr") is not None:
                    if abs(v["ctr"] - pv["ctr"]) >= 2.0:
                        ctr_changed = True
                if views_changed or ctr_changed:
                    v["_prev_views"] = pv.get("views", 0)
                    v["_prev_ctr"] = pv.get("ctr")
                    updated_videos.append(v)

        changes = {"new": new_videos, "updated": updated_videos}

    # 6. Chamar LLM MOTORES
    logger.info(f"Agente 4: {channel_name} | run #{run_number} | {len(merged_data)} videos | first={is_first}")

    llm_output = _call_llm(
        merged_data=merged_data,
        channel_info=channel_info,
        avg_ctr_pct=avg_ctr_pct,
        is_first_analysis=is_first,
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

    # 7. Salvar
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
        logger.warning(f"Agente 4: {channel_name} — analise ok mas save falhou!")

    logger.info(
        f"=== FIM Agente 4: {channel_name} | run #{run_number} | "
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

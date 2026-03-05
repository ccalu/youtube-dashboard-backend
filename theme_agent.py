"""
Agente 3 — Temas
Camada 2 (Analise Especializada)

Identifica o TEMA concreto de cada video e as HIPOTESES DE MOTORES PSICOLOGICOS
que explicam por que a audiencia clica.
Score: 50% CTR + 50% Views (normalizado 0-100).
1 LLM Call: LLM TEMAS (JSON com temas + hipoteses por video).
Deteccao incremental: analyzed_video_data snapshot evita reprocessamento.
Analise narrativa de motores movida para motor_agent.py (Agente 4).
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

logger = logging.getLogger("theme_agent")

# =============================================================================
# CONSTANTES
# =============================================================================

MIN_VIDEOS = 5
MIN_VIEWS = 500
MATURITY_DAYS = 7
CTR_WEIGHT = 0.5
VIEWS_WEIGHT = 0.5
TOP_N = 15

# Thresholds para deteccao de mudanca
VIEWS_CHANGE_PCT = 0.20   # +20%
CTR_CHANGE_PP = 0.02      # +2pp


# =============================================================================
# FUNCOES DE DADOS (Python)
# =============================================================================

def _get_monitorado_id(channel_id: str) -> Optional[int]:
    """Mapeia yt_channels.channel_id (UC...) -> canais_monitorados.id (integer)."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/yt_channels",
        params={"channel_id": f"eq.{channel_id}", "select": "channel_name"},
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    )
    if resp.status_code != 200 or not resp.json():
        logger.error(f"Canal {channel_id} nao encontrado em yt_channels")
        return None

    channel_name = resp.json()[0].get("channel_name", "")
    if not channel_name:
        return None

    resp2 = requests.get(
        f"{SUPABASE_URL}/rest/v1/canais_monitorados",
        params={"nome_canal": f"eq.{channel_name}", "select": "id"},
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    )
    if resp2.status_code != 200 or not resp2.json():
        logger.error(f"Canal '{channel_name}' nao encontrado em canais_monitorados")
        return None

    monitorado_id = resp2.json()[0].get("id")
    logger.info(f"Mapeamento: {channel_id} -> canais_monitorados.id={monitorado_id} ({channel_name})")
    return monitorado_id


def _fetch_channel_videos(channel_id: str) -> List[Dict]:
    """Busca videos do canal em videos_historico. Filtros: 7+ dias, 500+ views."""
    monitorado_id = _get_monitorado_id(channel_id)
    if monitorado_id is None:
        return []

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

    now = datetime.now(timezone.utc)
    videos = []
    for v in seen.values():
        title = v.get("titulo", "")
        views = v.get("views_atuais", 0) or 0
        pub_date_str = v.get("data_publicacao", "")
        if not title or not pub_date_str:
            continue
        # Filtro: minimo 500 views
        if views < MIN_VIEWS:
            continue
        try:
            if "T" in pub_date_str:
                pub_date = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))
            else:
                pub_date = datetime.fromisoformat(pub_date_str + "T00:00:00+00:00")
            if pub_date.tzinfo is None:
                pub_date = pub_date.replace(tzinfo=timezone.utc)
            age_days = (now - pub_date).days
        except (ValueError, TypeError):
            continue
        if age_days < MATURITY_DAYS:
            continue
        videos.append({
            "title": title,
            "views": views,
            "publish_date": pub_date_str,
            "age_days": age_days,
            "video_id": v.get("video_id")
        })

    logger.info(f"Videos encontrados: {len(all_rows)} total, {len(seen)} unicos, {len(videos)} com 7+ dias e 500+ views")
    return videos


def _fetch_video_ctr(channel_id: str, video_ids: List[str]) -> Dict[str, Dict]:
    """Busca CTR e impressions de cada video em yt_video_metrics."""
    if not video_ids:
        return {}

    ctr_data = {}
    # Buscar em batches de 50
    batch_size = 50
    for i in range(0, len(video_ids), batch_size):
        batch = video_ids[i:i + batch_size]
        # Supabase IN filter
        ids_filter = ",".join(batch)
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/yt_video_metrics",
            params={
                "channel_id": f"eq.{channel_id}",
                "video_id": f"in.({ids_filter})",
                "select": "video_id,ctr,impressions",
                "ctr": "not.is.null"
            },
            headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        )
        if resp.status_code == 200:
            for row in resp.json():
                vid = row.get("video_id")
                if vid:
                    ctr_data[vid] = {
                        "ctr": row.get("ctr", 0) or 0,
                        "impressions": row.get("impressions", 0) or 0
                    }

    logger.info(f"CTR data: {len(ctr_data)}/{len(video_ids)} videos com CTR")
    return ctr_data


def _fetch_channel_avg_ctr(channel_id: str) -> Optional[float]:
    """Busca CTR medio do canal em yt_channels."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/yt_channels",
        params={
            "channel_id": f"eq.{channel_id}",
            "select": "avg_ctr"
        },
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    )
    if resp.status_code == 200 and resp.json():
        avg_ctr = resp.json()[0].get("avg_ctr")
        if avg_ctr is not None:
            return float(avg_ctr)
    return None


def get_channels_for_themes() -> List[Dict]:
    """Retorna todos canais ativos (NAO precisa de spreadsheet)."""
    all_channels = []
    page_size = 100
    offset = 0

    while True:
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/yt_channels",
            params={
                "is_active": "eq.true",
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


# =============================================================================
# RANKING (Score: 50% CTR + 50% Views)
# =============================================================================

def build_ranking(videos: List[Dict], ctr_data: Dict[str, Dict], avg_ctr: Optional[float]) -> List[Dict]:
    """
    Constroi ranking por Score = 50% CTR + 50% Views (normalizado 0-100 min-max).
    Videos sem CTR: usam score baseado so em views (metade CTR = 50).
    """
    entries = []
    for v in videos:
        vid = v.get("video_id", "")
        ctr_info = ctr_data.get(vid, {})
        ctr_val = ctr_info.get("ctr", None)
        # CTR em yt_video_metrics e 0-1 (decimal), converter para percentual
        ctr_pct = round(ctr_val * 100, 2) if ctr_val is not None else None
        avg_ctr_pct = round(avg_ctr * 100, 2) if avg_ctr is not None else None

        ctr_diff = None
        if ctr_pct is not None and avg_ctr_pct is not None:
            ctr_diff = round(ctr_pct - avg_ctr_pct, 1)

        entries.append({
            "title": v["title"],
            "views": v["views"],
            "video_id": vid,
            "age_days": v.get("age_days", 0),
            "publish_date": v.get("publish_date", ""),
            "ctr": ctr_pct,             # None se nao disponivel
            "ctr_diff": ctr_diff,       # None se nao disponivel
            "score": 0.0,
        })

    if not entries:
        return []

    # Normalizar min-max (0-100)
    views_list = [e["views"] for e in entries]
    min_views, max_views = min(views_list), max(views_list)

    ctrs_available = [e["ctr"] for e in entries if e["ctr"] is not None]
    if ctrs_available:
        min_ctr, max_ctr = min(ctrs_available), max(ctrs_available)
    else:
        min_ctr, max_ctr = 0, 0

    for e in entries:
        # Views normalizado
        if max_views > min_views:
            views_norm = (e["views"] - min_views) / (max_views - min_views) * 100
        else:
            views_norm = 50.0

        # CTR normalizado
        if e["ctr"] is not None and max_ctr > min_ctr:
            ctr_norm = (e["ctr"] - min_ctr) / (max_ctr - min_ctr) * 100
        elif e["ctr"] is not None:
            ctr_norm = 50.0
        else:
            ctr_norm = 50.0  # sem CTR = neutro

        e["score"] = round(CTR_WEIGHT * ctr_norm + VIEWS_WEIGHT * views_norm, 1)

    # Ordenar por score DESC
    entries.sort(key=lambda x: x["score"], reverse=True)

    # Adicionar rank
    for i, e in enumerate(entries):
        e["rank"] = i + 1

    return entries


# =============================================================================
# DETECCAO INCREMENTAL
# =============================================================================

def _detect_changes(
    current_ranking: List[Dict],
    previous_snapshot: Optional[Dict]
) -> Dict[str, List[Dict]]:
    """
    Compara videos atuais com snapshot do ultimo relatorio.
    Return: {new: [...], updated: [...], unchanged: [...]}
    """
    if not previous_snapshot:
        return {"new": current_ranking, "updated": [], "unchanged": []}

    new_videos = []
    updated_videos = []
    unchanged_videos = []

    for v in current_ranking:
        vid = v["video_id"]
        prev = previous_snapshot.get(vid)

        if prev is None:
            new_videos.append(v)
        else:
            prev_views = prev.get("views", 0)
            prev_ctr = prev.get("ctr")

            views_changed = (
                prev_views > 0
                and v["views"] > 0
                and (v["views"] - prev_views) / prev_views >= VIEWS_CHANGE_PCT
            )
            ctr_changed = (
                v["ctr"] is not None
                and prev_ctr is not None
                and abs(v["ctr"] - prev_ctr) >= CTR_CHANGE_PP * 100  # ambos em %
            )

            if views_changed or ctr_changed:
                v["_prev_views"] = prev_views
                v["_prev_ctr"] = prev_ctr
                v["_prev_tema"] = prev.get("tema", "")
                v["_prev_hipoteses"] = prev.get("hipoteses", [])
                updated_videos.append(v)
            else:
                # Manter tema/hipoteses do snapshot anterior
                v["_prev_tema"] = prev.get("tema", "")
                v["_prev_hipoteses"] = prev.get("hipoteses", [])
                unchanged_videos.append(v)

    return {"new": new_videos, "updated": updated_videos, "unchanged": unchanged_videos}


def _get_previous_run(channel_id: str) -> Optional[Dict]:
    """Busca ultimo run com todos os dados necessarios."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/theme_analysis_runs",
        params={
            "channel_id": f"eq.{channel_id}",
            "select": "id,run_date,run_number,analyzed_video_data,themes_json,report_text,themes_list",
            "order": "run_date.desc",
            "limit": 1
        },
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    )
    if resp.status_code != 200 or not resp.json():
        return None

    row = resp.json()[0]

    # Parse JSONB fields
    avd = row.get("analyzed_video_data")
    if isinstance(avd, str):
        try:
            avd = json.loads(avd)
        except (json.JSONDecodeError, TypeError):
            avd = None

    tj = row.get("themes_json")
    if isinstance(tj, str):
        try:
            tj = json.loads(tj)
        except (json.JSONDecodeError, TypeError):
            tj = None

    tl = row.get("themes_list")
    if isinstance(tl, str):
        try:
            tl = json.loads(tl)
        except (json.JSONDecodeError, TypeError):
            tl = []
    elif not isinstance(tl, list):
        tl = []

    return {
        "id": row.get("id"),
        "run_date": row.get("run_date", ""),
        "run_number": row.get("run_number", 1) or 1,
        "analyzed_video_data": avd or {},
        "themes_json": tj,
        "report_text": row.get("report_text", ""),
        "themes_list": tl,
    }


# =============================================================================
# LLM TEMAS (Call 1) — Extrai tema + hipoteses de motores de cada video
# =============================================================================

SYSTEM_PROMPT_TEMAS = """Voce e um analista especializado em psicologia de audiencia no YouTube. Voce trabalha para uma operacao que gerencia dezenas de canais YouTube simultaneamente. Seu objetivo e identificar QUAIS temas concretos geram performance e POR QUE -- revelando os motores psicologicos invisiveis por tras de cada clique.

Para cada video voce deve identificar duas coisas:
1. O TEMA -- o assunto factual concreto e especifico do video
2. As HIPOTESES DE MOTORES PSICOLOGICOS -- os padroes invisiveis que explicam por que a audiencia clica

O TEMA e a DECISAO (o que produzir). O MOTOR e a ANALISE (por que funciona).

=== REGRAS PARA TEMA ===

O tema e o ASSUNTO CONCRETO do video. Nao e uma categoria. Nao e o titulo reescrito. E o fato especifico que o video aborda.

ERRADO - generico demais:
  "Historia de Roma" -- isso e um nicho, nao um tema
  "Crimes historicos" -- isso e uma categoria, nao um tema
  "Atos perturbadores" -- isso e um topico, nao um tema

ERRADO - repetindo o titulo:
  "Os 5 Atos Mais Perturbadores de Caligula Que Foram Longe Demais" -- isso e o titulo copiado

CERTO - assunto concreto e especifico:
  Titulo: "Os 5 Atos Mais Perturbadores de Caligula Que Foram Longe Demais"
    --> Tema: "Os excessos e atrocidades do imperador Caligula em Roma"
  Titulo: "O que os Vikings faziam com as freiras"
    --> Tema: "O destino das freiras nos saques vikings"
  Titulo: "A noite mais sangrenta dos Vikings em Paris"
    --> Tema: "O cerco e saque viking a Paris no ano 845 d.C."

Teste de qualidade: se dois videos DIFERENTES podem ter o mesmo tema, voce esta sendo generico demais. Cada tema deve ser unico e identificavel.

REGRA CRITICA: Voce so tem acesso ao TITULO do video. NUNCA deduza informacao que o titulo nao diz. Extraia o tema do que o titulo REALMENTE diz, sem adicionar informacao que nao esta la.

=== REGRAS PARA HIPOTESES DE MOTORES PSICOLOGICOS ===

Motores psicologicos sao os padroes INVISIVEIS que explicam o clique. Nao e o que o video e SOBRE -- e a EMOCAO que MOVE a audiencia a clicar e assistir.

Regras fundamentais:
- Cada video deve ter entre 2 e 4 hipoteses de motores
- Motores NAO sao uma lista fixa -- voce deve identificar o padrao REAL de cada video
- Se o padrao e genuinamente o mesmo em varios videos, USE O MESMO NOME (agrupe)
- Se o padrao e diferente mesmo que pareca similar, CRIE UM NOVO MOTOR (separe)
- Cada motor precisa de uma explicacao que CONECTE o padrao ao conteudo ESPECIFICO daquele video
- NUNCA escreva explicacoes genericas que poderiam servir para qualquer video

Como decidir se agrupa ou separa:
  Pergunte-se: "A EMOCAO que leva ao clique e a mesma?"
  Se SIM --> mesmo motor, mesmo nome
  Se NAO --> motor diferente, nome novo

=== EXEMPLOS DE MOTORES BEM IDENTIFICADOS ===

Estes sao EXEMPLOS DE REFERENCIA (figurados) para voce entender o nivel de profundidade esperado. NAO sao uma lista fechada. Voce DEVE criar motores novos quando o padrao e genuinamente diferente.

"Poder sem limites"
  Fascinacao por figuras com poder absoluto e zero consequencias. O espectador se pergunta "o que EU faria com esse poder?"
  Exemplo: "Os 5 Atos Mais Perturbadores de Caligula Que Foram Longe Demais" -- nao e so sobre atos perturbadores, e sobre um homem que TINHA poder absoluto e usou sem limites. O poder e o motor, nao a crueldade.
  So funciona com personagens centrais que TIVERAM poder real. NAO funciona com eventos ou grupos.

"Voyeurismo legitimado"
  O formato historico/educativo permite consumir conteudo transgressor (violencia, crueldade, tabus) sem culpa. A historia serve como LICENCA MORAL para ver o proibido. O espectador se sente "autorizado" a ver algo proibido porque e "historia".
  Exemplo: "O que os Vikings faziam com as freiras" -- o espectador consome conteudo violento e transgressor legitimado pelo formato historico. "Nao sou morbido, estou aprendendo historia."
  Diferente de curiosidade generica -- e especificamente sobre consumir o PROIBIDO em formato SEGURO.

"Choque moral"
  Brutalidade ou violencia extrema que gera indignacao imediata. Motor de ENTRADA -- atrai o clique mas nao sustenta a atencao sozinho.
  Exemplo: "O que os Vikings faziam com as freiras" -- a brutalidade viking contra freiras (maximo de vulnerabilidade) gera indignacao visceral.
  Diferente de "Violacao do sagrado": choque moral e sobre a INTENSIDADE da violencia, violacao do sagrado e sobre a NATUREZA do que esta sendo violado.

"Violacao do sagrado"
  Algo que a sociedade considera sagrado (religiao, inocencia, moral, instituicoes) sendo destruido ou corrompido. A TRANSGRESSAO do que deveria ser protegido gera indignacao + curiosidade.
  Exemplo: "O que os Vikings faziam com as freiras" -- freiras = simbolo maximo de pureza e castidade. Vikings violando esse simbolo sagrado e uma transgressao que vai alem da violencia fisica.
  NAO e o mesmo que "Choque moral" -- Choque moral e sobre brutalidade generica. Violacao do sagrado e sobre QUEM ou O QUE esta sendo violado.

"Monstruosidade feminina"
  Fascinacao por mulheres que cometeram atrocidades -- quebra o estereotipo de mulher = cuidado e protecao. A subversao do esperado gera curiosidade intensa.
  Exemplo: "Elizabeth Bathory se banhava em sangue" -- uma MULHER cometendo monstruosidades e mais chocante porque viola a expectativa social do feminino.
  Motor especifico -- nao e Choque moral generico. A emocao e de SURPRESA pela inversao do estereotipo.

"Luto civilizacional"
  Tristeza pela perda irreversivel de uma cultura inteira. O lamento pelo que se perdeu para sempre.
  Exemplo: "A queda do Imperio Asteca" -- nao e indignacao pela violencia espanhola, e TRISTEZA por uma civilizacao que nunca mais vai existir.
  NAO e Choque moral (indignacao) -- e LAMENTO.

"Conhecimento proibido"
  Gatilho de que existe verdade oculta que "eles" esconderam de voce. O sistema, a escola, a igreja, NAO queria que voce soubesse.
  Exemplo: "5 verdades que a escola nunca te ensinou" -- motor de GANCHO, funciona no clique mas nao sustenta retencao sozinho.

=== COMO MOTORES SE REPETEM ENTRE TEMAS DIFERENTES ===

Observe como os MESMOS motores aparecem em videos com TEMAS completamente diferentes. Isso e o poder da analise -- descobrir os padroes invisiveis que se repetem:

Titulo: "Os 5 Atos Mais Perturbadores de Caligula Que Foram Longe Demais"
  Tema: Os excessos e atrocidades do imperador Caligula em Roma
  Motores:
    H1: Poder sem limites -- poder absoluto sem consequencias
    H2: Voyeurismo legitimado -- conteudo transgressor em formato historico
    H3: Choque moral -- "ele fez ISSO?"

Titulo: "O que os Vikings faziam com as freiras"
  Tema: O destino das freiras nos saques vikings
  Motores:
    H1: Voyeurismo legitimado        <-- REPETE (mesmo de Caligula)
    H2: Choque moral                 <-- REPETE (mesmo de Caligula)
    H3: Violacao do sagrado          <-- NOVO (freiras = pureza sendo violada)

Titulo: "Elizabeth Bathory se banhava em sangue"
  Tema: As atrocidades de Elizabeth Bathory
  Motores:
    H1: Choque moral                 <-- REPETE
    H2: Poder sem limites            <-- REPETE (mesma emocao de Caligula)
    H3: Monstruosidade feminina      <-- NOVO (mulher cometendo atrocidades)

INSIGHT: "Voyeurismo legitimado" e "Choque moral" aparecem nos tops repetidamente.
Isso revela o que MOVE a audiencia do canal -- independente do tema concreto.

=== COMO DISTINGUIR MOTORES SIMILARES ===

Pergunte-se: "A EMOCAO que leva ao clique e a mesma?"
Se SIM --> mesmo motor, mesmo nome
Se NAO --> motor diferente, nome novo

Exemplo com o mesmo video "O que os Vikings faziam com as freiras":
  - Choque moral: emocao = INDIGNACAO pela brutalidade dos vikings
  - Violacao do sagrado: emocao = TRANSGRESSAO -- freiras (puras) sendo violadas
  - Voyeurismo legitimado: emocao = ver o PROIBIDO legitimado pela historia
  Tres emocoes diferentes = tres motores diferentes no MESMO video.

=== CATALOGO DE MOTORES ===

Apos analisar TODOS os videos, compile um CATALOGO de cada motor distinto que voce identificou. Este catalogo e crucial -- e o mapa completo dos padroes psicologicos do canal.

Para cada motor do catalogo:
1. DESCRICAO: Explique o que e este motor e POR QUE funciona NESTE canal especifico (nao generico)
2. VOCABULARIO: Extraia palavras-chave dos titulos que contem este motor. As keywords devem estar no IDIOMA ORIGINAL do canal + traducao em portugues. Sao as palavras nos titulos que ATIVAM este motor.
3. INSIGHT PSICOLOGICO: Analise profunda de por que esse motor move ESTA audiencia especifica. Conecte ao nicho, cultura e perfil do publico.
4. VIDEOS: Liste os video_ids que contem este motor

Regras:
- O vocabulario deve ser extraido dos TITULOS REAIS fornecidos (nao inventado)
- Se o canal e em coreano, as keywords sao em coreano + traducao
- Se o canal e em portugues, as keywords sao em portugues (sem traducao necessaria)
- Ordene os motores do mais frequente ao menos frequente

=== ANTI-PATTERNS (KILLERS) ===

Alem dos motores que FUNCIONAM, identifique os padroes que MATAM a performance. Olhe o FUNDO do ranking (videos com scores mais baixos) e identifique o que eles tem em comum.

Para cada anti-pattern:
1. NOME: Nome descritivo do padrao killer (ex: "Titulo Biografico Generico")
2. DESCRICAO: Por que esse padrao mata a performance neste canal
3. EXEMPLOS: Quais videos (video_ids) demonstram este killer
4. IMPACTO: Estimativa do impacto negativo (ex: "CTR cai ~50% quando presente")

Regras:
- Minimo 2 exemplos concretos para cada anti-pattern (nao reporte com 1 so exemplo)
- Use os scores/CTR REAIS dos videos como evidencia
- Anti-patterns comuns: titulo generico sem gancho, ausencia do motor dominante, repetir a mesma figura/tema, referencias culturais desconhecidas pelo publico

=== INTERACOES ENTRE MOTORES ===

Identifique como os motores interagem entre si quando aparecem no MESMO video:
- AMPLIFICAM: Combinacoes que geram scores acima da media (os motores se potencializam)
- NEUTRALIZAM: Combinacoes que nao agregam valor (um motor anula o outro)

Para cada interacao:
1. COMBINACAO: Quais motores interagem
2. TIPO: "amplifica" ou "neutraliza"
3. EXPLICACAO: Por que essa interacao acontece

Regras:
- So reporte interacoes com 2+ exemplos de videos
- Use os scores dos videos como evidencia

=== FORMATO DE RESPOSTA ===

Responda APENAS com JSON valido no formato abaixo. Sem markdown, sem comentarios, sem explicacoes fora do JSON.

{
  "videos": [
    {
      "video_id": "...",
      "titulo": "titulo original do video",
      "tema": "assunto concreto e especifico",
      "hipoteses": [
        {"motor": "Nome do Motor", "explicacao": "Por que esse motor funciona NESTE video especifico"}
      ]
    }
  ],
  "catalogo_motores": [
    {
      "motor": "Nome do Motor",
      "descricao": "O que e este motor e por que funciona neste canal",
      "vocabulario": [
        {"original": "palavra no idioma do canal", "traducao": "traducao em portugues"}
      ],
      "insight_psicologico": "Analise profunda de por que move esta audiencia",
      "videos_ids": ["id1", "id2"]
    }
  ],
  "anti_patterns": [
    {
      "pattern": "Nome do Anti-Pattern",
      "descricao": "Por que mata a performance",
      "exemplos_video_ids": ["id1", "id2"],
      "impacto": "Descricao do impacto negativo com dados"
    }
  ],
  "interacoes_motores": [
    {
      "combinacao": ["Motor A", "Motor B"],
      "tipo": "amplifica",
      "explicacao": "Por que esses motores se potencializam juntos"
    }
  ]
}"""


def _format_videos_for_prompt(ranking: List[Dict], avg_ctr_str: str) -> str:
    """Formata lista de videos para inclusao no prompt."""
    lines = []
    for v in ranking:
        ctr_str = ""
        if v.get("ctr") is not None:
            ctr_str = f" | CTR: {v['ctr']:.1f}%"
            if v.get("ctr_diff") is not None:
                sign = "+" if v["ctr_diff"] >= 0 else ""
                ctr_str += f" (canal: {avg_ctr_str}% | {sign}{v['ctr_diff']:.1f}pp)"
        lines.append(
            f"#{v['rank']} | video_id: {v['video_id']} | \"{v['title']}\" | "
            f"Views: {v['views']:,}{ctr_str} | Score: {v['score']:.0f}/100"
        )
    return "\n".join(lines)


def _format_updated_videos(updated: List[Dict]) -> str:
    """Formata videos com mudanca significativa (delta views/CTR)."""
    lines = []
    for v in updated:
        prev_views = v.get("_prev_views", 0)
        prev_ctr = v.get("_prev_ctr")
        views_pct = round((v["views"] - prev_views) / prev_views * 100, 0) if prev_views > 0 else 0
        ctr_str = ""
        if v.get("ctr") is not None and prev_ctr is not None:
            delta = round(v["ctr"] - prev_ctr, 1)
            sign = "+" if delta >= 0 else ""
            ctr_str = f" | CTR: {prev_ctr:.1f}% -> {v['ctr']:.1f}% ({sign}{delta:.1f}pp)"
        lines.append(
            f"- video_id: {v['video_id']} | \"{v['title']}\" | "
            f"Views: {prev_views:,} -> {v['views']:,} (+{views_pct:.0f}%){ctr_str} | Score: {v['score']:.0f}/100"
        )
    return "\n".join(lines) if lines else "Nenhum video com mudanca significativa."


def call_llm_temas(
    ranking: List[Dict],
    channel_info: Dict,
    avg_ctr_pct: Optional[float],
    is_first: bool = True,
    previous_report: Optional[str] = None,
    changes: Optional[Dict] = None
) -> Optional[Dict]:
    """
    LLM TEMAS: extrai tema concreto + hipoteses de motores de cada video.

    Run #1: Analisa todos os videos.
    Run #2+: Prompt 3-block (relatorio anterior + mudancas + dados gerais).

    Returns: {"videos": [...], "catalogo_motores": [...], "anti_patterns": [...], "interacoes_motores": [...]}
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

    # Ranking completo formatado (data_block — TODOS os videos)
    videos_text = _format_videos_for_prompt(ranking, avg_ctr_str)

    if is_first:
        # === RUN #1: prompt simples, todos os videos ===
        user_prompt = f"""CANAL: {channel_name} ({lingua})
NICHO: {channel_info.get('nicho', 'Geral')}
SUBNICHO: {subnicho}
CTR MEDIO DO CANAL: {avg_ctr_str}%

{len(ranking)} VIDEOS PARA ANALISAR (ordenados por score, filtrados: 7+ dias, 500+ views):

{videos_text}

Analise TODOS os videos e retorne:
1. Para cada video: tema concreto + hipoteses de motores psicologicos
2. Catalogo completo dos motores identificados (com descricao, vocabulario no idioma {lingua}, insight)
3. Anti-patterns (padroes que matam performance, minimo 2 exemplos cada)
4. Interacoes entre motores (combinacoes que amplificam ou neutralizam)

Responda com JSON no formato especificado no system prompt (videos + catalogo_motores + anti_patterns + interacoes_motores)."""

    else:
        # === RUN #2+: prompt 3-block incremental ===
        new_videos = changes.get("new", []) if changes else []
        updated_videos = changes.get("updated", []) if changes else []

        # Bloco 1: Relatorio anterior
        prev_block = previous_report or "Nenhum relatorio anterior disponivel."

        # Bloco 2: O que mudou
        new_text = _format_videos_for_prompt(new_videos, avg_ctr_str) if new_videos else "Nenhum video novo."
        updated_text = _format_updated_videos(updated_videos)

        user_prompt = f"""CANAL: {channel_name} ({lingua})
NICHO: {channel_info.get('nicho', 'Geral')}
SUBNICHO: {subnicho}
CTR MEDIO DO CANAL: {avg_ctr_str}%

=== BLOCO 1: RELATORIO ANTERIOR ===

{prev_block}

=== BLOCO 2: O QUE MUDOU ===

{len(new_videos)} videos NOVOS no ranking (nao existiam na analise anterior):

{new_text}

{len(updated_videos)} videos com mudanca significativa (views +20% ou CTR +2pp):

{updated_text}

=== BLOCO 3: DADOS GERAIS (TODOS OS {len(ranking)} VIDEOS) ===

{videos_text}

INSTRUCOES:
- Analise os {len(new_videos)} videos NOVOS individualmente (tema + hipoteses de motores)
- Para videos existentes, MANTENHA as analises do relatorio anterior (mesmo video_id = mesmo tema + hipoteses)
- Se algum video teve mudanca significativa, REVISE a analise dele
- Atualize catalogo de motores, anti-patterns e interacoes considerando o panorama COMPLETO
- Vocabulario no idioma {lingua} + traducao em portugues

Responda com JSON no formato especificado no system prompt (videos + catalogo_motores + anti_patterns + interacoes_motores)."""

    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model=model,
                temperature=0.3,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT_TEMAS},
                    {"role": "user", "content": user_prompt}
                ]
            )

            text = response.choices[0].message.content
            result = json.loads(text)
            llm_videos = result.get("videos", [])

            # Garantir campos enriquecidos com defaults
            if "catalogo_motores" not in result:
                result["catalogo_motores"] = []
            if "anti_patterns" not in result:
                result["anti_patterns"] = []
            if "interacoes_motores" not in result:
                result["interacoes_motores"] = []

            n_cat = len(result["catalogo_motores"])
            n_anti = len(result["anti_patterns"])
            n_inter = len(result["interacoes_motores"])
            logger.info(f"LLM TEMAS OK: {len(llm_videos)} videos, {n_cat} motores catalogados, {n_anti} anti-patterns, {n_inter} interacoes (tentativa {attempt+1})")
            return result

        except json.JSONDecodeError as e:
            logger.warning(f"JSON invalido LLM TEMAS tentativa {attempt+1}: {e}")
        except Exception as e:
            logger.error(f"Erro LLM TEMAS tentativa {attempt+1}: {e}")

    logger.error("LLM TEMAS falhou apos 2 tentativas")
    return None


def _fallback_temas(ranking: List[Dict]) -> Dict:
    """Fallback quando LLM TEMAS falha — usa titulo como tema, sem hipoteses."""
    videos = []
    for v in ranking:
        videos.append({
            "video_id": v["video_id"],
            "titulo": v["title"],
            "tema": v["title"][:80],
            "hipoteses": []
        })
    return {"videos": videos, "catalogo_motores": [], "anti_patterns": [], "interacoes_motores": []}


# =============================================================================
# MERGE: Python junta dados numericos + output LLM TEMAS
# =============================================================================

def _merge_ranking_with_themes(ranking: List[Dict], llm_temas: Dict, avg_ctr_pct: Optional[float]) -> List[Dict]:
    """
    Merge ranking (dados numericos) + output LLM TEMAS (tema + hipoteses).
    Produz formato que a LLM MOTORES recebe como input.
    """
    # Indexar LLM output por video_id
    llm_by_id = {}
    for v in llm_temas.get("videos", []):
        llm_by_id[v.get("video_id", "")] = v

    merged = []
    for r in ranking:
        vid = r["video_id"]
        llm = llm_by_id.get(vid, {})

        merged.append({
            "rank": r["rank"],
            "score": r["score"],
            "views": r["views"],
            "ctr": r.get("ctr"),
            "ctr_diff": r.get("ctr_diff"),
            "title": r["title"],
            "video_id": vid,
            "age_days": r.get("age_days", 0),
            "tema": llm.get("tema", r["title"][:80]),
            "hipoteses": llm.get("hipoteses", []),
            "motores": [h.get("motor", "") for h in llm.get("hipoteses", [])],
        })

    return merged


def _count_motors(merged_data: List[Dict]) -> List[Dict]:
    """Conta ocorrencias de cada motor + score medio."""
    motor_stats = {}  # motor_name -> {count, total_score, videos}
    total_videos = len(merged_data)

    for v in merged_data:
        for motor in v.get("motores", []):
            if not motor:
                continue
            if motor not in motor_stats:
                motor_stats[motor] = {"count": 0, "total_score": 0, "videos": []}
            motor_stats[motor]["count"] += 1
            motor_stats[motor]["total_score"] += v.get("score", 0)
            motor_stats[motor]["videos"].append(v.get("video_id", ""))

    result = []
    for name, stats in motor_stats.items():
        avg_score = round(stats["total_score"] / stats["count"], 0) if stats["count"] > 0 else 0
        pct = round(stats["count"] / total_videos * 100, 0) if total_videos > 0 else 0
        result.append({
            "motor": name,
            "count": stats["count"],
            "total_videos": total_videos,
            "pct": pct,
            "avg_score": avg_score,
        })

    result.sort(key=lambda x: x["count"], reverse=True)
    return result


def compute_motor_correlations(merged_data: List[Dict], catalogo_motores: List[Dict]) -> Dict:
    """
    Calcula correlacoes COM vs SEM para cada motor (Python, nao LLM).
    Para cada motor: score medio e CTR medio dos videos COM vs SEM esse motor.
    """
    correlations = {}

    for cat_motor in catalogo_motores:
        motor_name = cat_motor.get("motor", "")
        if not motor_name:
            continue

        # Separar videos COM e SEM este motor
        com = []
        sem = []
        for v in merged_data:
            video_motors = v.get("motores", [])
            if motor_name in video_motors:
                com.append(v)
            else:
                sem.append(v)

        def avg(lst, key):
            vals = [v.get(key) for v in lst if v.get(key) is not None]
            return round(sum(vals) / len(vals), 1) if vals else None

        correlations[motor_name] = {
            "com": {
                "videos": len(com),
                "score_medio": avg(com, "score"),
                "ctr_medio": avg(com, "ctr"),
            },
            "sem": {
                "videos": len(sem),
                "score_medio": avg(sem, "score"),
                "ctr_medio": avg(sem, "ctr"),
            }
        }

    return correlations


def _format_motor_counts(motor_counts: List[Dict], prev_motor_counts: Optional[List[Dict]] = None) -> str:
    """Formata contagem de motores para o user prompt da LLM MOTORES.
    Mantida aqui para ser importada por motor_agent.py."""
    prev_map = {}
    if prev_motor_counts:
        for m in prev_motor_counts:
            prev_map[m["motor"]] = m

    lines = []
    for m in motor_counts:
        line = f"- {m['motor']}: {m['count']}/{m['total_videos']} videos ({m['pct']:.0f}%) | Score medio: {m['avg_score']:.0f}"
        prev = prev_map.get(m["motor"])
        if prev:
            line += f" | era {prev['count']}/{prev['total_videos']} ({prev['pct']:.0f}%), score {prev['avg_score']:.0f}"
        lines.append(line)

    return "\n".join(lines)



# =============================================================================
# RELATORIO UNIFICADO
# =============================================================================

def _format_views(n: int) -> str:
    """Formata views: 1500 -> 1.5K, 150000 -> 150K."""
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    elif n >= 1_000:
        v = n / 1_000
        return f"{v:.1f}K" if v < 100 else f"{int(v)}K"
    return str(n)


def generate_report(
    channel_name: str,
    merged_data: List[Dict],
    avg_ctr_pct: Optional[float],
    run_number: int,
    themes_json: Optional[Dict] = None,
    new_count: int = -1,
    updated_count: int = -1
) -> str:
    """Gera relatorio do Agente 4 (Temas): ranking + temas + catalogo + anti-padroes."""
    now = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    avg_ctr_str = f"{avg_ctr_pct:.1f}" if avg_ctr_pct is not None else "N/A"

    report = []

    # === BANNER INCREMENTAL ===
    if run_number > 1 and new_count == 0 and updated_count == 0:
        report.append(f">> Run #{run_number} -- Nenhum video novo/atualizado detectado desde a ultima analise.")
        report.append(">> Relatorio anterior reutilizado. Proxima analise com dados novos gerara atualizacao completa.")
        report.append("")
    elif run_number > 1 and (new_count > 0 or updated_count > 0):
        parts = []
        if new_count > 0:
            parts.append(f"{new_count} novo(s)")
        if updated_count > 0:
            parts.append(f"{updated_count} atualizado(s)")
        report.append(f">> Run #{run_number} -- {' + '.join(parts)} (de {len(merged_data)} total). Analise focada nas mudancas.")
        report.append("")

    report.append("=" * 70)
    report.append(f"AGENTE 4 — TEMAS | {channel_name}")
    report.append(f"Relatorio #{run_number} | {now}")
    report.append(f"Score: 50% CTR + 50% Views (normalizado 0-100)")
    report.append(f"CTR medio do canal: {avg_ctr_str}%")
    report.append("=" * 70)
    report.append("")

    # Ranking com temas e hipoteses de motores
    report.append("RANKING COM TEMAS E HIPOTESES DE MOTORES:")
    report.append("")
    for v in merged_data:
        ctr_str = ""
        if v.get("ctr") is not None:
            ctr_str = f" | CTR: {v['ctr']:.1f}%"
            if v.get("ctr_diff") is not None:
                sign = "+" if v["ctr_diff"] >= 0 else ""
                ctr_str += f" (canal: {avg_ctr_str}% | {sign}{v['ctr_diff']:.1f}pp)"

        motores_str = ", ".join(v.get("motores", [])) if v.get("motores") else "N/A"

        report.append(f"#{v['rank']} | Score: {v['score']:.0f}/100 | Views: {v['views']:,}{ctr_str}")
        report.append(f"    Titulo: \"{v['title']}\"")
        report.append(f"    Tema: {v['tema']}")
        report.append(f"    Motores: {motores_str}")
        if v.get("hipoteses"):
            for h in v["hipoteses"]:
                report.append(f"      - {h.get('motor', '')}: {h.get('explicacao', '')}")
        report.append("")

    if not themes_json:
        return "\n".join(report)

    # Catalogo de motores
    catalogo = themes_json.get("catalogo_motores", [])
    correlacoes = themes_json.get("correlacoes", {})
    if catalogo:
        report.append("-" * 70)
        report.append("CATALOGO DE MOTORES PSICOLOGICOS:")
        report.append("")
        for i, cat in enumerate(catalogo, 1):
            motor_name = cat.get("motor", "")
            report.append(f"  Motor #{i}: {motor_name}")
            report.append(f"    {cat.get('descricao', '')}")
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
                report.append(f"    Vocabulario: {', '.join(vocab_strs)}")
            # Correlacao (Python-computed)
            corr = correlacoes.get(motor_name, {})
            if corr:
                com = corr.get("com", {})
                sem = corr.get("sem", {})
                com_score = f"score {com.get('score_medio', '?')}" if com.get("score_medio") is not None else ""
                sem_score = f"score {sem.get('score_medio', '?')}" if sem.get("score_medio") is not None else ""
                com_ctr = f", CTR {com.get('ctr_medio', '?')}%" if com.get("ctr_medio") is not None else ""
                sem_ctr = f", CTR {sem.get('ctr_medio', '?')}%" if sem.get("ctr_medio") is not None else ""
                report.append(f"    COM motor ({com.get('videos', 0)} videos): {com_score}{com_ctr}")
                report.append(f"    SEM motor ({sem.get('videos', 0)} videos): {sem_score}{sem_ctr}")
            # Insight
            insight = cat.get("insight_psicologico", "")
            if insight:
                report.append(f"    Insight: {insight}")
            report.append("")

    # Anti-patterns
    anti = themes_json.get("anti_patterns", [])
    if anti:
        report.append("-" * 70)
        report.append("ANTI-PADROES (KILLERS):")
        report.append("")
        for i, ap in enumerate(anti, 1):
            report.append(f"  Killer #{i}: {ap.get('pattern', '')}")
            report.append(f"    {ap.get('descricao', '')}")
            report.append(f"    Impacto: {ap.get('impacto', 'N/A')}")
            report.append("")

    # Interacoes
    interacoes = themes_json.get("interacoes_motores", [])
    if interacoes:
        report.append("-" * 70)
        report.append("INTERACOES ENTRE MOTORES:")
        report.append("")
        for inter in interacoes:
            comb = " + ".join(inter.get("combinacao", []))
            tipo = inter.get("tipo", "")
            report.append(f"  {comb} [{tipo.upper()}]")
            report.append(f"    {inter.get('explicacao', '')}")
            report.append("")

    return "\n".join(report)


# =============================================================================
# SAVE / DELETE / QUERY
# =============================================================================

def _build_snapshot(merged_data: List[Dict]) -> Dict:
    """Constroi analyzed_video_data snapshot para deteccao incremental."""
    snapshot = {}
    for v in merged_data:
        snapshot[v["video_id"]] = {
            "views": v["views"],
            "ctr": v.get("ctr"),
            "score": v["score"],
            "tema": v.get("tema", ""),
            "hipoteses": v.get("hipoteses", []),
        }
    return snapshot


def save_analysis(
    channel_id: str,
    channel_name: str,
    merged_data: List[Dict],
    report_text: str,
    themes_json: Dict,
    run_number: int
) -> Optional[int]:
    """Salva analise no banco de dados."""
    snapshot = _build_snapshot(merged_data)
    all_themes = [v.get("tema", "") for v in merged_data]
    motor_counts = _count_motors(merged_data)

    # Concentration top 5
    total_views = sum(v["views"] for v in merged_data) if merged_data else 1
    top5_views = sum(v["views"] for v in merged_data[:5])
    concentration_pct = round(top5_views / total_views * 100, 1) if total_views > 0 else 0

    payload = {
        "channel_id": channel_id,
        "channel_name": channel_name,
        "theme_count": len(all_themes),
        "total_videos_analyzed": len(merged_data),
        "concentration_pct": concentration_pct,
        "ranking_json": json.dumps(merged_data[:TOP_N], ensure_ascii=False),
        "themes_list": json.dumps(all_themes, ensure_ascii=False),
        "patterns_json": json.dumps({"motor_counts": motor_counts}, ensure_ascii=False),
        "report_text": report_text,
        "analyzed_video_data": json.dumps(snapshot, ensure_ascii=False),
        "run_number": run_number,
        "themes_json": json.dumps(themes_json, ensure_ascii=False),
    }

    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/theme_analysis_runs",
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
        logger.info(f"Analise salva: run_id={run_id}, run_number={run_number}, {len(merged_data)} videos")
        return run_id
    else:
        logger.error(f"Erro ao salvar analise: {resp.status_code} - {resp.text[:300]}")
        return None


def delete_analysis(channel_id: str, run_id: int) -> Dict:
    """Deleta um run especifico de theme_analysis_runs."""
    resp = requests.delete(
        f"{SUPABASE_URL}/rest/v1/theme_analysis_runs",
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
        logger.info(f"Analise deletada: channel={channel_id}, run_id={run_id}")
        return {"success": True, "message": f"Run {run_id} deletado"}
    else:
        logger.error(f"Erro ao deletar: {resp.status_code} - {resp.text[:200]}")
        return {"success": False, "error": resp.text[:200]}


def get_latest_analysis(channel_id: str) -> Optional[Dict]:
    """Retorna analise mais recente."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/theme_analysis_runs",
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
    # Parse JSONB fields
    for field in ("ranking_json", "themes_list", "patterns_json", "analyzed_video_data", "themes_json"):
        val = row.get(field)
        if isinstance(val, str):
            try:
                row[field] = json.loads(val)
            except (json.JSONDecodeError, TypeError):
                pass
    return row


def get_analysis_history(channel_id: str, limit: int = 20, offset: int = 0) -> Dict:
    """Retorna historico paginado de analises."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/theme_analysis_runs",
        params={
            "channel_id": f"eq.{channel_id}",
            "select": "id,channel_id,channel_name,run_date,run_number,theme_count,total_videos_analyzed,concentration_pct",
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


# =============================================================================
# ORQUESTRACAO PRINCIPAL
# =============================================================================

def run_analysis(channel_id: str) -> Dict:
    """
    Executa analise completa: Temas + Motores Psicologicos.

    Fluxo:
    1. Busca videos + aplica filtros (7 dias, 500 views)
    2. Busca CTR por video + CTR medio canal
    3. Calcula scores e monta ranking
    4. Carrega run anterior (se existe)
    5. Detecta novos/atualizados vs snapshot anterior
    6. LLM TEMAS: extrai tema + hipoteses (so novos, ou todos se primeira analise)
    7. Merge ranking + temas + dados anteriores
    8. LLM MOTORES: gera analise narrativa
    9. Gera relatorio unificado
    10. Salva tudo no banco
    """
    logger.info(f"=== INICIO Agente 3 (Temas + Motores) para {channel_id} ===")

    # 1. Info do canal
    channel_info = _get_channel_info(channel_id)
    if not channel_info:
        return {"success": False, "error": "Canal nao encontrado"}

    channel_name = channel_info.get("channel_name", "Desconhecido")

    # 2. Busca videos
    videos = _fetch_channel_videos(channel_id)
    if len(videos) < MIN_VIDEOS:
        return {
            "success": False,
            "error": f"Insuficiente: {len(videos)} videos (minimo {MIN_VIDEOS})",
            "channel_name": channel_name
        }

    # 3. Busca CTR
    video_ids = [v["video_id"] for v in videos]
    ctr_data = _fetch_video_ctr(channel_id, video_ids)
    avg_ctr = _fetch_channel_avg_ctr(channel_id)
    avg_ctr_pct = round(avg_ctr * 100, 2) if avg_ctr is not None else None

    # 4. Ranking
    ranking = build_ranking(videos, ctr_data, avg_ctr)
    if not ranking:
        return {"success": False, "error": "Ranking vazio", "channel_name": channel_name}

    logger.info(f"Ranking: {len(ranking)} videos (top score: {ranking[0]['score']:.0f})")

    # 5. Run anterior
    prev_run = _get_previous_run(channel_id)
    is_first = prev_run is None
    run_number = 1 if is_first else (prev_run.get("run_number", 1) + 1)

    # 6. Deteccao incremental
    if is_first:
        changes = {"new": ranking, "updated": [], "unchanged": []}
    else:
        changes = _detect_changes(ranking, prev_run.get("analyzed_video_data", {}))

    new_count = len(changes["new"])
    updated_count = len(changes["updated"])
    skip_llm = False

    if not is_first and new_count == 0 and updated_count == 0:
        logger.info("Zero videos novos/atualizados — reutilizando relatorio anterior (skip LLM)")
        skip_llm = True

    # 7. LLM TEMAS
    if skip_llm:
        # Reutilizar themes_json do run anterior
        llm_temas = prev_run.get("themes_json") or {"videos": [], "catalogo_motores": [], "anti_patterns": [], "interacoes_motores": []}
        if isinstance(llm_temas, str):
            try:
                llm_temas = json.loads(llm_temas)
            except (json.JSONDecodeError, TypeError):
                llm_temas = {"videos": [], "catalogo_motores": [], "anti_patterns": [], "interacoes_motores": []}
    else:
        previous_report = prev_run.get("report_text") if prev_run else None
        llm_temas = call_llm_temas(
            ranking=ranking,
            channel_info=channel_info,
            avg_ctr_pct=avg_ctr_pct,
            is_first=is_first,
            previous_report=previous_report,
            changes=changes,
        )
        if llm_temas is None:
            llm_temas = _fallback_temas(ranking if is_first else changes["new"])

    # 8. Merge: novos (com temas da LLM) + existentes (com temas do snapshot)
    new_videos = changes["new"]
    if is_first:
        merged = _merge_ranking_with_themes(ranking, llm_temas, avg_ctr_pct)
    else:
        # Merge novos com temas da LLM
        new_merged = _merge_ranking_with_themes(new_videos, llm_temas, avg_ctr_pct) if new_videos else []

        # Unchanged e updated manteem temas do snapshot
        existing_merged = []
        for v in changes["unchanged"] + changes["updated"]:
            v["tema"] = v.get("_prev_tema", v["title"][:80])
            v["hipoteses"] = v.get("_prev_hipoteses", [])
            v["motores"] = [h.get("motor", "") for h in v.get("hipoteses", [])]
            existing_merged.append(v)

        # Juntar e re-ranquear
        all_merged = new_merged + existing_merged
        all_merged.sort(key=lambda x: x.get("score", 0), reverse=True)
        for i, v in enumerate(all_merged):
            v["rank"] = i + 1

        merged = all_merged

    # 9. Compute correlacoes COM vs SEM (Python — SEMPRE recalcular)
    catalogo = llm_temas.get("catalogo_motores", [])
    correlations = compute_motor_correlations(merged, catalogo) if catalogo else {}
    if correlations:
        llm_temas["correlacoes"] = correlations
        logger.info(f"Correlacoes calculadas para {len(correlations)} motores")

    # 10. Gera relatorio
    motor_counts = _count_motors(merged)
    if skip_llm:
        # Reutilizar report anterior com banner
        report = generate_report(channel_name, merged, avg_ctr_pct, run_number, llm_temas,
                                 new_count=0, updated_count=0)
        logger.info("Reutilizando report com banner de zero novos")
    else:
        report = generate_report(channel_name, merged, avg_ctr_pct, run_number, llm_temas,
                                 new_count=new_count, updated_count=updated_count)

    # 11. Salva
    run_id = save_analysis(
        channel_id=channel_id,
        channel_name=channel_name,
        merged_data=merged,
        report_text=report,
        themes_json=llm_temas,
        run_number=run_number,
    )

    if run_id is None:
        logger.warning(f"Agente 3: {channel_name} — analise ok mas save falhou!")

    logger.info(
        f"=== FIM Agente 3: {channel_name} | run #{run_number} | "
        f"{len(merged)} videos | {new_count} novos | {updated_count} atualizados | "
        f"run_id={run_id} ==="
    )

    # Ranking resumido para resposta da API
    ranking_summary = [
        {"rank": v.get("rank"), "title": v.get("title", ""), "score": v.get("score"),
         "views": v.get("views"), "tema": v.get("tema", ""), "video_id": v.get("video_id")}
        for v in merged[:20]
    ]

    return {
        "success": run_id is not None,
        "channel_name": channel_name,
        "run_id": run_id,
        "run_number": run_number,
        "total_videos": len(merged),
        "new_videos": new_count,
        "updated_videos": updated_count,
        "theme_count": len(set(v.get("tema", "") for v in merged)),
        "motor_count": len(motor_counts),
        "ranking": ranking_summary,
        "report_text": report,
        "report": report,  # compatibilidade com _build_unified_report
    }

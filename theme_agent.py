"""
Agente 5 — Analisador de Temas
Camada 2 (Analise Especializada) — roda em paralelo com Agentes 3 e 4.

Identifica o TEMA ESPECIFICO de cada video (ultima ramificacao da hierarquia).
Score ponderado: 50% Velocity (views/dia) + 50% Views (normalizado 0-100).
Skill exclusiva: decomposicao em elementos constitutivos + hipoteses de adjacencia.
Output alimenta o Agente 6 (Recomendador) com materia-prima analitica.

Hierarquia: Nicho > Subnicho > Micronicho (Ag.3) > TEMA (Ag.5)
"""

import os
import json
import logging
import requests
from datetime import datetime, timezone
from typing import List, Dict, Optional

# Imports do ecossistema (reutilizar, nao duplicar)
from copy_analysis_agent import (
    _get_channel_info,
    SUPABASE_URL,
    SUPABASE_KEY,
    SUPABASE_HEADERS,
)
from micronicho_agent import (
    _get_monitorado_id,
    _fetch_channel_videos,
    get_channels_for_micronicho as get_channels_for_themes,
)

logger = logging.getLogger("theme_agent")

# =============================================================================
# CONSTANTES
# =============================================================================

MIN_VIDEOS = 5
MATURITY_DAYS = 7
VELOCITY_WEIGHT = 0.5
VIEWS_WEIGHT = 0.5
TOP_N = 15          # top 15 no ranking
DECOMP_TOP_N = 5    # decomposicao dos top 5


# =============================================================================
# ETAPA 1: EXTRACAO DE TEMAS (LLM Call 1)
# =============================================================================

def extract_themes(
    videos: List[Dict],
    subnicho: str,
    lingua: str,
    previous_themes: Optional[List[str]] = None
) -> Dict:
    """
    LLM Call 1: extrai o tema especifico de cada video.

    Returns:
        {
            "classifications": [{"title": str, "theme": str, "video_id": str}, ...],
            "all_themes": [str, ...]
        }
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY nao configurada — fallback")
        return _fallback_extraction(videos)

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
    except ImportError:
        logger.error("openai nao instalado")
        return _fallback_extraction(videos)

    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    # ── System Prompt ──────────────────────────────────────────────
    system_prompt = """Voce e um extrator especializado de temas especificos de videos YouTube.
Seu trabalho e identificar o ASSUNTO CONCRETO de cada video a partir do titulo.

=== O QUE E UM TEMA ===

O tema e o ASSUNTO ESPECIFICO e CONCRETO de um video individual.
E a ultima ramificacao na hierarquia de categorizacao de conteudo — nao existe
subdivisao possivel abaixo do tema.

Um tema bem identificado responde a pergunta: "Sobre o que EXATAMENTE este video fala?"

Hierarquia completa:
  Nicho > Subnicho (canal) > Micronicho (subcategoria) > TEMA (assunto especifico)

TEMA = o caso, evento, pessoa ou situacao especifica sendo retratada no video.
MICRONICHO = a CATEGORIA que agrupa multiplos temas sob um guarda-chuva tematico.

=== TEMA ≠ MICRONICHO — DISTINCAO CRITICA ===

Esta distincao e a mais importante do seu trabalho. Errar aqui invalida toda a analise.

ERRADO (amplo demais = micronicho, NAO tema):
  "Imperio Otomano" → micronicho (contem centenas de temas possiveis)
  "Nazistas" → micronicho
  "Campos de concentracao" → micronicho (ainda amplo)
  "Serial Killers" → micronicho
  "Espionagem Militar" → micronicho

CORRETO (especifico = tema):
  "O tratamento brutal dos otomanos com freiras cristas" → TEMA
  "A fuga de Siegfried Lederer de Auschwitz" → TEMA
  "Experimentos medicos de Mengele em criancas gemeas" → TEMA
  "Os crimes de Jeffrey Dahmer em Milwaukee" → TEMA
  "A infiltracao de Oleg Penkovsky na inteligencia sovietica" → TEMA

REGRA DE ESPECIFICIDADE:
  Se voce consegue imaginar 10+ videos DIFERENTES dentro do assunto,
  e amplo demais (micronicho). Se o assunto descreve UM caso/evento/situacao
  concreta que gera 1 video, e um TEMA.

=== COMO EXTRAIR O TEMA ===

Passo 1: Leia o titulo completo do video
Passo 2: Identifique O QUE o video retrata (nao COMO retrata)
         - "O que" = o assunto concreto (tema)
         - "Como" = a estrutura narrativa (agente 1) ou o titulo (agente 4)
Passo 3: Formule como frase descritiva curta (5-15 palavras)
         - Deve ser uma descricao FACTUAL do assunto
         - Na lingua do canal (nao traduza)
Passo 4: Verifique especificidade
         - Se cabe 10+ videos dentro → muito amplo, refine
         - Se descreve 1 caso concreto → correto

Exemplos de extracao:

  Titulo: "What Ottomans Did To Christian Nuns Was Worse Than Death"
  ERRADO: "Imperio Otomano" (micronicho)
  CORRETO: "Tratamento brutal dos otomanos com freiras cristas"

  Titulo: "The Nazi Doctor Who Used Twins As Lab Rats"
  ERRADO: "Nazistas" (micronicho)
  CORRETO: "Experimentos medicos nazistas em criancas gemeas"

  Titulo: "What Haitian Slaves Did To French Masters Will Shock You"
  ERRADO: "Escravidao" (micronicho)
  CORRETO: "Vinganca dos escravos haitianos contra colonizadores franceses"

  Titulo: "The Spanish Inquisition's Most Disturbing Punishment Methods"
  ERRADO: "Inquisicao" (micronicho)
  CORRETO: "Rituais de punicao da Inquisicao Espanhola com hereges"

=== 7 REGRAS DE EXTRACAO ===

1. Cada video tem EXATAMENTE 1 tema (classificacao exclusiva)
2. O tema e uma FRASE DESCRITIVA (5-15 palavras), nao uma palavra-chave
3. Escreva o tema na LINGUA dos titulos do canal (nao traduza)
4. CONSISTENCIA: se um tema ja apareceu na lista anterior, use a MESMA formulacao exata
   (nao reformule "Fuga de Lederer de Auschwitz" como "Escapada de Lederer do campo nazista")
5. Responda APENAS com JSON valido, sem texto adicional
6. NAO agrupe — cada video e um tema UNICO. Diferente do micronicho que agrupa multiplos
   videos, aqui cada titulo gera 1 tema distinto
7. Se dois videos tem titulos MUITO parecidos sobre o MESMO assunto concreto,
   podem receber o mesmo tema (ex: "Part 1" e "Part 2" do mesmo assunto)"""

    # ── User Prompt ────────────────────────────────────────────────
    prev_block = ""
    if previous_themes:
        prev_list = "\n".join([f"- {t}" for t in previous_themes[:50]])
        prev_block = f"""Temas ja identificados em analises anteriores (mantenha consistencia de formulacao):
{prev_list}

"""

    titles_list = "\n".join([f"{i+1}. {v['title']}" for i, v in enumerate(videos)])

    user_prompt = f"""{prev_block}Subnicho do canal: {subnicho}
Lingua dos titulos: {lingua}

Extraia o TEMA ESPECIFICO de cada video.
Lembre: tema = assunto concreto (5-15 palavras), NAO categoria ampla.

Titulos:
{titles_list}

JSON de saida:
{{
  "videos": [
    {{"title": "...", "theme": "descricao do tema especifico"}},
    ...
  ],
  "all_themes": ["tema1", "tema2", ...]
}}"""

    # ── Chamada LLM com retry ──────────────────────────────────────
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

            text = response.choices[0].message.content
            result = json.loads(text)

            llm_videos = result.get("videos", [])
            all_themes = result.get("all_themes", [])

            # Mapear de volta aos videos originais
            title_to_theme = {}
            for item in llm_videos:
                t = item.get("title", "").strip()
                th = item.get("theme", "Nao Identificado")
                title_to_theme[t] = th

            classifications = []
            for v in videos:
                theme = title_to_theme.get(v["title"], "Nao Identificado")
                classifications.append({
                    "title": v["title"],
                    "theme": theme,
                    "video_id": v.get("video_id", ""),
                    "views": v.get("views", 0),
                    "age_days": v.get("age_days", 1),
                })

            # Garantir all_themes inclui tudo
            theme_set = set(all_themes)
            for c in classifications:
                if c["theme"] not in theme_set:
                    all_themes.append(c["theme"])
                    theme_set.add(c["theme"])

            logger.info(f"LLM Call 1 OK: {len(classifications)} videos → {len(all_themes)} temas")
            return {"classifications": classifications, "all_themes": all_themes}

        except json.JSONDecodeError as e:
            logger.warning(f"JSON invalido na tentativa {attempt+1}: {e}")
            if attempt == 0:
                continue
        except Exception as e:
            logger.error(f"Erro LLM Call 1 tentativa {attempt+1}: {e}")
            if attempt == 0:
                continue

    logger.error("LLM Call 1 falhou apos 2 tentativas — usando fallback")
    return _fallback_extraction(videos)


def _fallback_extraction(videos: List[Dict]) -> Dict:
    """Fallback quando LLM falha — usa titulo como tema."""
    classifications = []
    all_themes = []
    for v in videos:
        title = v.get("title", "Sem Titulo")
        # Usar titulo truncado como tema
        theme = title[:80] if len(title) > 80 else title
        classifications.append({
            "title": title,
            "theme": theme,
            "video_id": v.get("video_id", ""),
            "views": v.get("views", 0),
            "age_days": v.get("age_days", 1),
        })
        if theme not in all_themes:
            all_themes.append(theme)

    return {"classifications": classifications, "all_themes": all_themes}


# =============================================================================
# ETAPA 2: RANKING (Score ponderado 50/50)
# =============================================================================

def build_ranking(videos: List[Dict], classifications: List[Dict]) -> List[Dict]:
    """
    Constroi ranking de temas por Score = 50% velocity + 50% views (normalizado 0-100).

    Como temas sao terminais (1 video = 1 tema normalmente), agrupamos por tema
    e pegamos a media (para cobrir o caso raro de 2 videos com mesmo tema).
    """
    # Agrupar por tema
    theme_data = {}
    for c in classifications:
        theme = c["theme"]
        if theme not in theme_data:
            theme_data[theme] = []
        theme_data[theme].append(c)

    # Calcular metricas por tema
    entries = []
    for theme, vids in theme_data.items():
        total_views = sum(v.get("views", 0) for v in vids)
        avg_views = total_views / len(vids)
        # Velocity = views/dia (media ponderada se multiplos videos)
        total_age = sum(max(v.get("age_days", 1), 1) for v in vids)
        velocity = total_views / max(total_age / len(vids), 1)  # avg velocity

        best = max(vids, key=lambda x: x.get("views", 0))

        entries.append({
            "theme": theme,
            "video_count": len(vids),
            "views": int(avg_views),
            "velocity": round(velocity, 1),
            "age_days": best.get("age_days", 0),
            "title": best.get("title", ""),
            "video_id": best.get("video_id", ""),
            "score": 0.0,  # calculado abaixo
        })

    if not entries:
        return []

    # Normalizar min-max (0-100)
    velocities = [e["velocity"] for e in entries]
    views_list = [e["views"] for e in entries]

    min_vel, max_vel = min(velocities), max(velocities)
    min_views, max_views = min(views_list), max(views_list)

    for e in entries:
        if max_vel > min_vel:
            vel_norm = (e["velocity"] - min_vel) / (max_vel - min_vel) * 100
        else:
            vel_norm = 50.0

        if max_views > min_views:
            views_norm = (e["views"] - min_views) / (max_views - min_views) * 100
        else:
            views_norm = 50.0

        e["score"] = round(VELOCITY_WEIGHT * vel_norm + VIEWS_WEIGHT * views_norm, 1)

    # Ordenar por score DESC
    entries.sort(key=lambda x: x["score"], reverse=True)

    # Adicionar rank
    for i, e in enumerate(entries):
        e["rank"] = i + 1

    return entries


# =============================================================================
# ETAPA 3: DETECCAO DE PADROES
# =============================================================================

def detect_patterns(ranking: List[Dict]) -> Dict:
    """Detecta padroes no ranking de temas."""
    if not ranking:
        return {
            "concentration_pct": 0,
            "top_performers": [],
            "bottom_performers": [],
            "total_themes": 0,
            "total_videos": 0,
            "avg_views_geral": 0,
            "avg_velocity_geral": 0,
            "avg_score_geral": 0,
            "high_velocity_themes": [],
            "high_views_low_velocity": [],
        }

    total_views = sum(e["views"] * e["video_count"] for e in ranking)
    total_videos = sum(e["video_count"] for e in ranking)

    # Concentracao top 5
    top5_views = sum(e["views"] * e["video_count"] for e in ranking[:5])
    concentration_pct = round((top5_views / total_views * 100) if total_views > 0 else 0, 1)

    # Medias
    avg_views = total_views / total_videos if total_videos > 0 else 0
    avg_velocity = sum(e["velocity"] for e in ranking) / len(ranking) if ranking else 0
    avg_score = sum(e["score"] for e in ranking) / len(ranking) if ranking else 0

    # Top e bottom performers
    top_performers = [e["theme"] for e in ranking if e["score"] > avg_score]
    bottom_performers = [e["theme"] for e in ranking if e["score"] < avg_score * 0.5]

    # Velocity patterns
    high_velocity = [e["theme"] for e in ranking if e["velocity"] > avg_velocity * 2]
    high_views_low_vel = [
        e["theme"] for e in ranking
        if e["views"] > avg_views and e["velocity"] < avg_velocity * 0.5
    ]

    return {
        "concentration_pct": concentration_pct,
        "top_performers": top_performers,
        "bottom_performers": bottom_performers,
        "total_themes": len(ranking),
        "total_videos": total_videos,
        "avg_views_geral": round(avg_views, 1),
        "avg_velocity_geral": round(avg_velocity, 1),
        "avg_score_geral": round(avg_score, 1),
        "high_velocity_themes": high_velocity,
        "high_views_low_velocity": high_views_low_vel,
    }


# =============================================================================
# ETAPA 4: FORMATACAO AUXILIAR
# =============================================================================

def _format_views(n: int) -> str:
    """Formata views: 1500 → 1.5K, 150000 → 150K."""
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    elif n >= 1_000:
        v = n / 1_000
        return f"{v:.1f}K" if v < 100 else f"{int(v)}K"
    return str(n)


def _format_velocity(v: float) -> str:
    """Formata velocity: 1267.3 → 1.267/d."""
    if v >= 1000:
        return f"{v/1000:.3f}K/d"
    return f"{v:.0f}/d"


def _format_ranking_table(ranking: List[Dict], limit: int = TOP_N) -> str:
    """Formata ranking como tabela ASCII."""
    lines = []
    header = f"{'#':>3}  {'Tema':<45}  {'Views':>8}  {'Velocity':>10}  {'Score':>5}  {'Titulo Original'}"
    lines.append(header)
    lines.append(f"{'---':>3}  {'-----':<45}  {'-----':>8}  {'--------':>10}  {'-----':>5}  {'---------------'}")

    for e in ranking[:limit]:
        theme_short = e["theme"][:42] + "..." if len(e["theme"]) > 45 else e["theme"]
        title_short = e["title"][:50] + "..." if len(e["title"]) > 50 else e["title"]
        lines.append(
            f"{e['rank']:>3}  {theme_short:<45}  "
            f"{_format_views(e['views']):>8}  "
            f"{_format_velocity(e['velocity']):>10}  "
            f"{e['score']:>5.0f}  "
            f"{title_short}"
        )

    return "\n".join(lines)


def _format_patterns(patterns: Dict) -> str:
    """Formata padroes detectados como texto."""
    lines = []
    lines.append(f"- Concentracao top 5: {patterns['concentration_pct']}%")
    lines.append(f"- Total temas: {patterns['total_themes']}")
    lines.append(f"- Total videos: {patterns['total_videos']}")
    lines.append(f"- Media views geral: {_format_views(int(patterns['avg_views_geral']))}")
    lines.append(f"- Velocity media geral: {_format_velocity(patterns['avg_velocity_geral'])}")
    lines.append(f"- Score medio: {patterns['avg_score_geral']:.1f}")

    if patterns["top_performers"]:
        lines.append(f"- Top performers (score > media): {len(patterns['top_performers'])} temas")
    if patterns["bottom_performers"]:
        lines.append(f"- Bottom performers (score < 50% media): {len(patterns['bottom_performers'])} temas")
    if patterns["high_velocity_themes"]:
        lines.append(f"- Temas com velocity excepcional (>2x media): {', '.join(patterns['high_velocity_themes'][:5])}")
    if patterns["high_views_low_velocity"]:
        lines.append(f"- Views altas + velocity baixa (acumulados): {', '.join(patterns['high_views_low_velocity'][:5])}")

    return "\n".join(lines)


# =============================================================================
# ETAPA 5: DECOMPOSICAO + HIPOTESES (LLM Call 2)
# =============================================================================

def generate_decomposition(
    channel_name: str,
    subnicho: str,
    lingua: str,
    ranking: List[Dict],
    patterns: Dict,
    total_videos: int,
    comparison: Optional[Dict] = None
) -> Optional[Dict]:
    """
    LLM Call 2: gera decomposicao em elementos + hipoteses de adjacencia.

    Returns:
        {"ranking": str, "decomposicao": str, "padroes": str}
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY nao configurada — pulando LLM Call 2")
        return None

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
    except ImportError:
        logger.error("openai nao instalado")
        return None

    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    # ── System Prompt ──────────────────────────────────────────────
    system_prompt = """Voce e um analista de performance tematica de canais YouTube, especializado em
decompor temas virais em seus elementos constitutivos e levantar hipoteses
de adjacencia tematica.

=== CONTEXTO: O QUE E UM TEMA ===

O tema e o ASSUNTO ESPECIFICO e CONCRETO de um video.
E a ultima ramificacao na hierarquia: Nicho > Subnicho > Micronicho > TEMA.

Diferente do micronicho (que agrupa videos), o tema e TERMINAL — cada video
tem seu tema unico. Isso cria um problema especial:

Se um tema viralizou, NAO da para "fazer outro video com o mesmo tema" — o tema
ja foi usado. Diferente de um micronicho (que contem dezenas de temas) ou uma
estrutura de titulo (que pode ser reutilizada infinitamente).

=== SEU PAPEL — O PRINCIPIO DAS HIPOTESES MULTIPLAS ===

Voce recebe um RANKING DE TEMAS ja calculado pelo Python (toda a matematica
foi feita — views, velocity, score normalizado 0-100).

Como o tema e terminal (nao-repetivel), a pergunta NAO e "repita o que deu certo".
A pergunta e: "QUAL ELEMENTO do tema que deu certo pode ser replicado em OUTRO tema?"

Seu trabalho e:
1. Apresentar o ranking formatado
2. DECOMPOR cada tema top em elementos constitutivos
3. Levantar 2-3 HIPOTESES de adjacencia por tema
4. Identificar PADROES TRANSVERSAIS entre os temas top

=== METRICA: SCORE PONDERADO (50% VELOCITY + 50% VIEWS) ===

O Score de Performance Tematica equilibra:
- VELOCITY (views/dia): compara videos de idades diferentes de forma justa
  50K views em 7 dias (7.143/dia) > 50K views em 90 dias (556/dia)
- VIEWS ABSOLUTAS: volume real de audiencia alcancada

Ambos normalizados 0-100 via min-max scaling. Score final = media ponderada 50/50.

Ao interpretar o ranking:
- Score alto + velocity alta = tema VIRAL ATIVO (ainda crescendo rapido)
- Score alto + views altas mas velocity media = tema de ALTA DEMANDA (acumulou volume)
- Velocity muito alta + views baixas = tema RECENTE com potencial (monitorar)
- Views altas + velocity baixa = tema ANTIGO que acumulou por tempo (nao necessariamente forte)

SEMPRE mencione views, velocity E idade ao interpretar um tema.

=== DECOMPOSICAO EM ELEMENTOS CONSTITUTIVOS ===

A decomposicao identifica os INGREDIENTES de um tema viral para permitir
RECOMBINACAO em novos temas. As categorias sao FLEXIVEIS e devem ser
adaptadas ao subnicho do canal:

Categorias COMUNS (use as que fizerem sentido):
- Figura de Poder: opressor, imperio, instituicao, ditador
- Vitima: grupo vulneravel, inocentes, minoria
- Dinamica: tipo de conflito, relacao entre partes
- Contexto: historico, geografico, temporal
- Emocao: choque, catarse, indignacao, fascinio, medo
- Periodo: era temporal especifica
- Instituicao: sistema envolvido (igreja, exercito, governo)
- Figura Especifica: individuo nomeavel (Mengele, Leopoldo II)
- Mecanismo Narrativo: revelacao, inversao de poder, segredo oculto
- Elemento Tabu: proibicao social, assunto incomodo

Para canais de Terror: Tipo de Ameaca, Contexto Fisico, Vitima Tipo, etc.
Para canais de Licoes de Vida: Desafio, Superacao, Transformacao, etc.
Adapte livremente — estas sao guias, nao regras rigidas.

=== HIPOTESES DE ADJACENCIA TEMATICA ===

Para cada tema do top 5, levante 2-3 hipoteses sobre QUAL ELEMENTO foi o
motor principal do sucesso. Cada hipotese deve conter:

1. NOME claro da hipotese (ex: "Otomanos como opressor recorrente")
2. PADRAO ABSTRATO que descreve o mecanismo:
   "Temas onde [elemento X] esta presente tendem a performar porque [razao]"
3. EVIDENCIA PARCIAL: outros temas no ranking que reforcam ou contradizem
   Cite tema, posicao e score especificos
4. NIVEL DE CONFIANCA: forte (3+ evidencias), moderado (1-2), ou fraco (apenas este tema)

REGRAS PARA HIPOTESES:
- Sao INDICIOS, nao conclusoes. Use linguagem cautelosa ("sugere", "indica", "possivel")
- NAO sugira titulos concretos de novos videos — apenas padroes abstratos
- As hipoteses servem como materia-prima para o Agente 6, que cruza com
  micronicho (Ag.3) e estrutura de titulo (Ag.4) para validar

Exemplo de hipotese bem formulada:
  "Hipotese A — Vitimas cristas/religiosas como motor
   Padrao: temas onde figuras religiosas sao vitimadas por imperios geram
   engajamento acima da media.
   Evidencia: tema #1 (otomanos + freiras, Score 92), tema #8 (otomanos +
   armenios cristaos, Score 75), tema #12 (Roma + cristaos, Score 61).
   Confianca: FORTE (3 evidencias distintas, imperios diferentes, mesma vitima)"

=== PADROES TRANSVERSAIS ===

Apos decompor os temas top individualmente, olhe TRANSVERSALMENTE:

1. ELEMENTOS RECORRENTES NOS TOPS: Presente em 3+ dos top 5?
   Se sim, e um candidato forte a "motor de performance" do canal.
   Cite exatamente em quantos dos top 5 aparece.

2. ELEMENTOS AUSENTES NOS PIORES: Nao aparecem nos bottom performers?
   Se um elemento esta nos tops MAS nao nos piores, reforco de que importa.

3. INDICIOS DE SATURACAO: Elemento presente em MUITOS videos com score
   progressivamente decrescente? Pode indicar que a audiencia esta saturando.

4. ANOMALIAS: Tema no top que QUEBRA o padrao dos outros tops?
   Se sim, pode revelar um SEGUNDO padrao forte paralelo ao principal.

5. INDICIO DE VELOCITY: Quais elementos tem velocity mais alta?
   Velocity alta = audiencia respondendo ATIVAMENTE (nao apenas acumulando).

OBSERVACAO FINAL OBRIGATORIA:
Encerre com uma observacao para o Agente 6 indicando o que PRECISA ser cruzado
com dados de micronicho (Ag.3) e estrutura de titulo (Ag.4) para validar as hipoteses.

=== FORMATO DE OUTPUT — EXATAMENTE 3 BLOCOS ===

[RANKING]
Tabela dos top 10-15 temas por Score, com colunas:
#  |  Tema  |  Views  |  Velocity  |  Score  |  Titulo Original

[DECOMPOSICAO]
Para CADA um dos top 5 temas:
- Tema completo + Score + Views + Velocity/dia + Idade
- Elementos constitutivos (lista adaptada ao subnicho)
- Hipotese A: nome + padrao abstrato + evidencia parcial + confianca
- Hipotese B: nome + padrao abstrato + evidencia parcial + confianca
- Hipotese C (se aplicavel): idem

[PADROES]
- Elementos recorrentes nos tops (com contagem: presente em X/5)
- Elementos ausentes nos piores
- Indicios de saturacao (se houver)
- Anomalias interessantes
- Indicio de velocity (quais elementos associados a velocity mais alta)
- Observacao para o Agente 6

=== REGRAS INVIOLAVEIS ===

1. Seja FACTUAL — cite SCORES, VIEWS, VELOCITY exatos do ranking fornecido
2. NAO invente dados — use APENAS o ranking e padroes fornecidos
3. SEMPRE mencione views, velocity E idade ao interpretar um tema
4. Hipoteses sao INDICIOS — use linguagem cautelosa, nunca afirmativa
5. NAO sugira titulos concretos de novos videos — apenas padroes abstratos
6. Escreva em portugues, paragrafos curtos separados por linha em branco
7. Escreva o quanto for necessario. NAO resuma, NAO corte a analise
8. Use EXATAMENTE os marcadores [RANKING], [DECOMPOSICAO] e [PADROES]
9. Decomposicao: top 5 temas OBRIGATORIAMENTE, todos com hipoteses
10. Padroes transversais: cite contagens especificas (presente em X/5 tops)
11. Observacao para o Agente 6 e OBRIGATORIA ao final dos [PADROES]

=== TIPO DE RACIOCINIO ESPERADO ===

NAO FACA ISSO (superficial):
"O tema 1 tem score alto. O tema 2 tambem. Ambos envolvem violencia."

FACA ISSO (profissional — decomposicao + hipoteses com evidencia):
"#1 'Tratamento brutal dos otomanos com freiras cristas' (Score 92, 152K views,
1.267/dia, 120 dias). Elementos: Poder=Imperio Otomano, Vitima=freiras cristas
(genero + fe), Dinamica=opressao imperial religiosa, Emocao=brutalidade vs pureza.

Hipotese A — Otomanos como opressor recorrente:
Temas com os otomanos exercendo dominio sobre qualquer grupo vulneravel
tendem a performar acima da media.
Evidencia: tema #8 (otomanos + armenios cristaos, Score 75) reforca.
Confianca: MODERADA (2 evidencias, mesmo opressor com vitimas diferentes).

Hipotese B — Vitimas cristas/religiosas como motor:
Temas onde figuras religiosas cristas sao vitimadas geram engajamento
independente do imperio agressor.
Evidencia: tema #4 (Inquisicao + hereges, Score 81) e tema #12 (Roma + cristaos,
Score 61) tangenciam — religiao como vitima em contextos distintos.
Confianca: FORTE (3 evidencias cruzando diferentes imperios/periodos)." """

    # ── Bloco de memoria cumulativa ────────────────────────────────
    previous_report_block = ""
    if comparison and comparison.get("previous_report"):
        prev_date = comparison.get("previous_date", "")
        if isinstance(prev_date, str) and "T" in prev_date:
            try:
                prev_date = datetime.fromisoformat(prev_date.replace("Z", "+00:00")).strftime("%d/%m/%Y")
            except (ValueError, TypeError):
                pass
        previous_report_block = f"""VOCE TEM MEMORIA ACUMULATIVA:
O relatorio anterior contem TODAS as conclusoes e hipoteses identificadas ate agora.
Sua analise atual DEVE:
- Se basear no relatorio anterior como referencia
- Verificar se hipoteses anteriores foram reforcadas ou enfraquecidas pelos novos dados
- Construir em cima, nunca ignorar o historico

RELATORIO ANTERIOR COMPLETO ({prev_date}):
{comparison['previous_report']}
FIM DO RELATORIO ANTERIOR.

"""

    ranking_table = _format_ranking_table(ranking)
    patterns_text = _format_patterns(patterns)

    # ── User Prompt ────────────────────────────────────────────────
    user_prompt = f"""{previous_report_block}Produza EXATAMENTE 3 blocos:

[RANKING]
Tabela com top 10-15 temas por Score.
Colunas: #, Tema, Views, Velocity (/dia), Score, Titulo Original

[DECOMPOSICAO]
Para CADA um dos top 5 temas:
- Elementos constitutivos (adaptados ao subnicho)
- 2-3 hipoteses de adjacencia tematica
  (padrao abstrato + evidencia parcial do ranking + nivel de confianca)

[PADROES]
Padroes transversais que cruzam multiplos temas do ranking.
Elementos recorrentes nos tops com contagens (X/5).
Anomalias e indicios de velocity.
Observacao OBRIGATORIA para o Agente 6 sobre o que precisa ser cruzado
com dados de micronicho e estrutura de titulo para validacao.

DADOS DO CANAL:
Canal: {channel_name}
Subnicho: {subnicho}
Lingua: {lingua}
Videos analisados: {total_videos} (com 7+ dias de maturidade)

TABELA DE RANKING (por Score = 50% velocity + 50% views, normalizado 0-100):
{ranking_table}

PADROES DETECTADOS:
{patterns_text}"""

    # ── Chamada LLM ────────────────────────────────────────────────
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
        ranking_text = ""
        decomposicao = ""
        padroes = ""

        if "[RANKING]" in text:
            after_rank = text.split("[RANKING]", 1)[1]
            if "[DECOMPOSICAO]" in after_rank:
                ranking_text = after_rank.split("[DECOMPOSICAO]", 1)[0].strip()
                after_decomp = after_rank.split("[DECOMPOSICAO]", 1)[1]
                if "[PADROES]" in after_decomp:
                    decomposicao = after_decomp.split("[PADROES]", 1)[0].strip()
                    padroes = after_decomp.split("[PADROES]", 1)[1].strip()
                else:
                    decomposicao = after_decomp.strip()
            else:
                ranking_text = after_rank.strip()
        else:
            ranking_text = text

        logger.info(f"LLM Call 2 OK: ranking={len(ranking_text)}ch, decomp={len(decomposicao)}ch, padroes={len(padroes)}ch")

        return {
            "ranking": ranking_text,
            "decomposicao": decomposicao,
            "padroes": padroes
        }

    except Exception as e:
        logger.error(f"Erro LLM Call 2: {e}")
        return None


# =============================================================================
# ETAPA 6: GERACAO DO RELATORIO
# =============================================================================

def generate_report(
    channel_name: str,
    ranking: List[Dict],
    patterns: Dict,
    llm_output: Optional[Dict],
    comparison: Optional[Dict],
    total_videos: int,
    all_themes: List[str]
) -> str:
    """Gera relatorio formatado de temas."""
    now = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")

    report = []
    report.append("=" * 60)
    report.append(f"ANALISE DE TEMAS | {channel_name} | {now}")
    report.append("=" * 60)
    report.append("")

    # Ranking table
    report.append("RANKING DE TEMAS (por Score: 50% velocity + 50% views, normalizado 0-100):")
    report.append("")
    report.append(_format_ranking_table(ranking))
    report.append("")

    # Sumario
    report.append(f"Temas identificados: {len(all_themes)}")
    report.append(f"Videos analisados: {total_videos}")
    report.append(f"Concentracao top 5: {patterns['concentration_pct']}%")
    report.append(f"Media geral de views: {_format_views(int(patterns['avg_views_geral']))}")
    report.append(f"Velocity media: {_format_velocity(patterns['avg_velocity_geral'])}")
    report.append(f"Score medio: {patterns['avg_score_geral']:.1f}")
    report.append("")

    # LLM output (3 blocos)
    if llm_output:
        if llm_output.get("ranking"):
            report.append("--- RANKING ---")
            report.append("")
            report.append(llm_output["ranking"])
            report.append("")

        if llm_output.get("decomposicao"):
            report.append("--- DECOMPOSICAO ---")
            report.append("")
            report.append(llm_output["decomposicao"])
            report.append("")

        if llm_output.get("padroes"):
            report.append("--- PADROES ---")
            report.append("")
            report.append(llm_output["padroes"])
            report.append("")

    # Comparacao
    if comparison:
        report.append("--- VS ANTERIOR ---")
        report.append("")
        prev_date = comparison.get("previous_date", "N/A")
        if isinstance(prev_date, str) and "T" in prev_date:
            prev_date = prev_date.split("T")[0]
        report.append(f"  Analise anterior: {prev_date}")
        prev_count = comparison.get("previous_theme_count")
        if prev_count is not None:
            report.append(f"  Temas anterior: {prev_count} -> atual: {len(all_themes)}")
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
    all_themes: List[str],
    report_text: str,
    patterns: Dict,
    total_videos: int
) -> Optional[int]:
    """Salva analise no banco."""

    run_data = {
        "channel_id": channel_id,
        "channel_name": channel_name,
        "theme_count": len(all_themes),
        "total_videos_analyzed": total_videos,
        "concentration_pct": patterns.get("concentration_pct"),
        "ranking_json": json.dumps(ranking),
        "themes_list": json.dumps(all_themes),
        "patterns_json": json.dumps(patterns),
        "report_text": report_text
    }

    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/theme_analysis_runs",
        headers=SUPABASE_HEADERS,
        json=run_data
    )

    if resp.status_code not in [200, 201]:
        logger.error(f"Erro ao salvar analise de temas: {resp.status_code} - {resp.text[:200]}")
        return None

    result = resp.json()
    run_id = result[0]["id"] if result else None
    logger.info(f"Analise de temas salva: run_id={run_id}")
    return run_id


# =============================================================================
# ETAPA 8: COMPARACAO COM ANTERIOR
# =============================================================================

def compare_with_previous(channel_id: str) -> Optional[Dict]:
    """
    Busca a ultima analise do canal.
    Memoria cumulativa: cada analise carrega o relatorio anterior.
    """
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/theme_analysis_runs",
        params={
            "channel_id": f"eq.{channel_id}",
            "select": "run_date,theme_count,total_videos_analyzed,"
                      "concentration_pct,themes_list,report_text",
            "order": "run_date.desc",
            "limit": "1"
        },
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    )

    if resp.status_code != 200 or not resp.json():
        return None

    prev = resp.json()[0]
    prev_themes = prev.get("themes_list")
    if isinstance(prev_themes, str):
        try:
            prev_themes = json.loads(prev_themes)
        except (json.JSONDecodeError, TypeError):
            prev_themes = []

    return {
        "previous_date": prev.get("run_date", ""),
        "previous_theme_count": prev.get("theme_count"),
        "previous_total_videos": prev.get("total_videos_analyzed"),
        "previous_concentration": prev.get("concentration_pct"),
        "previous_themes": prev_themes or [],
        "previous_report": prev.get("report_text", "")
    }


# =============================================================================
# ETAPA 9: FUNCOES DE CONSULTA
# =============================================================================

def get_latest_analysis(channel_id: str) -> Optional[Dict]:
    """Retorna a analise de temas mais recente."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/theme_analysis_runs",
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
        for field in ["ranking_json", "themes_list", "patterns_json"]:
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
        f"{SUPABASE_URL}/rest/v1/theme_analysis_runs",
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
        f"{SUPABASE_URL}/rest/v1/theme_analysis_runs",
        params={
            "channel_id": f"eq.{channel_id}",
            "select": "id,channel_name,run_date,theme_count,"
                      "total_videos_analyzed,concentration_pct",
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
    Executa analise completa de temas para um canal.

    Returns:
        {
            "success": bool,
            "channel_id": str,
            "channel_name": str,
            "run_id": int,
            "report": str,
            "theme_count": int,
            "total_videos": int,
            "ranking": [...],
            "error": str (se falhou)
        }
    """
    logger.info(f"{'='*50}")
    logger.info(f"TEMAS: Iniciando para canal {channel_id}")
    logger.info(f"{'='*50}")

    # 1. Buscar dados do canal
    channel_info = _get_channel_info(channel_id)
    if not channel_info:
        return {"success": False, "error": f"Canal {channel_id} nao encontrado em yt_channels"}

    channel_name = channel_info.get("channel_name", channel_id)
    subnicho = channel_info.get("subnicho", "N/A")
    lingua = channel_info.get("lingua", "")

    logger.info(f"Canal: {channel_name} | Subnicho: {subnicho} | Lingua: {lingua}")

    # 2. Buscar videos (reutiliza _fetch_channel_videos do micronicho_agent)
    videos = _fetch_channel_videos(channel_id)
    if not videos:
        return {"success": False, "error": "Nenhum video encontrado para o canal"}

    if len(videos) < MIN_VIDEOS:
        return {"success": False, "error": f"Minimo {MIN_VIDEOS} videos necessarios, encontrados: {len(videos)}"}

    # 3. Buscar temas anteriores (para consistencia de formulacao)
    comparison = compare_with_previous(channel_id)
    previous_themes = comparison.get("previous_themes", []) if comparison else []

    # 4. LLM Call 1: extrair temas
    extraction_result = extract_themes(videos, subnicho, lingua, previous_themes)
    classifications = extraction_result["classifications"]
    all_themes = extraction_result["all_themes"]

    logger.info(f"Extracao: {len(classifications)} videos -> {len(all_themes)} temas")

    # 5. Construir ranking (Score ponderado 50/50)
    ranking = build_ranking(videos, classifications)

    # 6. Detectar padroes
    patterns = detect_patterns(ranking)

    # 7. LLM Call 2: decomposicao + hipoteses
    llm_output = generate_decomposition(
        channel_name, subnicho, lingua, ranking, patterns,
        len(videos), comparison
    )

    # 8. Gerar relatorio
    report = generate_report(
        channel_name, ranking, patterns, llm_output,
        comparison, len(videos), all_themes
    )

    # 9. Salvar
    run_id = save_analysis(
        channel_id, channel_name, ranking, all_themes,
        report, patterns, len(videos)
    )

    logger.info(f"TEMAS COMPLETA: {channel_name} | {len(all_themes)} temas | {len(videos)} videos")

    return {
        "success": True,
        "channel_id": channel_id,
        "channel_name": channel_name,
        "run_id": run_id,
        "report": report,
        "theme_count": len(all_themes),
        "total_videos": len(videos),
        "ranking": ranking
    }

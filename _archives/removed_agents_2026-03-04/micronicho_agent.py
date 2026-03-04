"""
Agente 3: Analise de Micronichos
=================================
Identifica subcategorias tematicas (micronichos) dentro de cada canal
e gera um ranking por performance (views brutas).

Hierarquia: Nicho > Subnicho (foco do canal) > MICRONICHO (subcategoria) > Tema (video)

Diferencial: 2 chamadas LLM
  - Call 1: classificar cada video em 1 micronicho (JSON)
  - Call 2: interpretar ranking + gerar narrativa com recomendacoes

Fluxo:
1. Busca videos do canal em videos_historico (Supabase)
2. Filtra videos com 7+ dias de maturidade
3. LLM classifica cada titulo em 1 micronicho
4. Python agrupa e calcula ranking (avg views, total, best/worst)
5. Python detecta padroes (concentracao, top/bottom performers)
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
from typing import List, Dict, Optional

# Reusar funcoes do copy analysis agent
from copy_analysis_agent import (
    _get_channel_info,
    SUPABASE_URL,
    SUPABASE_KEY,
    SUPABASE_HEADERS,
)

logger = logging.getLogger(__name__)

# Constantes
MATURITY_DAYS = 7  # Minimo de dias desde publicacao
MIN_VIDEOS = 5     # Minimo de videos para rodar analise


# =============================================================================
# ETAPA 1: BUSCA DE VIDEOS
# =============================================================================

def _get_monitorado_id(channel_id: str) -> Optional[int]:
    """
    Mapeia yt_channels.channel_id (UC...) -> canais_monitorados.id (integer).
    videos_historico usa canais_monitorados.id como canal_id.

    Busca pelo nome do canal (yt_channels.channel_name == canais_monitorados.nome_canal).
    """
    # 1. Buscar nome do canal em yt_channels
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/yt_channels",
        params={
            "channel_id": f"eq.{channel_id}",
            "select": "channel_name"
        },
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    )
    if resp.status_code != 200 or not resp.json():
        logger.error(f"Canal {channel_id} nao encontrado em yt_channels")
        return None

    channel_name = resp.json()[0].get("channel_name", "")
    if not channel_name:
        return None

    # 2. Buscar ID em canais_monitorados pelo nome
    resp2 = requests.get(
        f"{SUPABASE_URL}/rest/v1/canais_monitorados",
        params={
            "nome_canal": f"eq.{channel_name}",
            "select": "id"
        },
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    )
    if resp2.status_code != 200 or not resp2.json():
        logger.error(f"Canal '{channel_name}' nao encontrado em canais_monitorados")
        return None

    monitorado_id = resp2.json()[0].get("id")
    logger.info(f"Mapeamento: {channel_id} -> canais_monitorados.id={monitorado_id} ({channel_name})")
    return monitorado_id


def _fetch_channel_videos(channel_id: str) -> List[Dict]:
    """
    Busca todos videos do canal em videos_historico.
    Deduplicar por video_id (manter registro mais recente por data_coleta).
    Filtra apenas videos com 7+ dias de maturidade.

    IMPORTANTE: videos_historico.canal_id = canais_monitorados.id (integer),
    NAO yt_channels.channel_id (UC...). Fazemos o mapeamento automaticamente.

    Returns:
        Lista de dicts: {title, views, publish_date, age_days, video_id}
    """
    # Mapear UC... -> integer ID
    monitorado_id = _get_monitorado_id(channel_id)
    if monitorado_id is None:
        logger.error(f"Nao foi possivel mapear {channel_id} para canais_monitorados")
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

    # Filtrar maturidade e montar resultado
    now = datetime.now(timezone.utc)
    videos = []
    for v in seen.values():
        title = v.get("titulo", "")
        views = v.get("views_atuais", 0) or 0
        pub_date_str = v.get("data_publicacao", "")

        if not title or not pub_date_str:
            continue

        # Calcular idade em dias
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

        videos.append({
            "title": title,
            "views": views,
            "publish_date": pub_date_str,
            "age_days": age_days,
            "video_id": v.get("video_id")
        })

    logger.info(f"Videos encontrados: {len(all_rows)} total, {len(seen)} unicos, {len(videos)} com 7+ dias")
    return videos


# =============================================================================
# ETAPA 2: CLASSIFICACAO VIA LLM (Call 1)
# =============================================================================

def classify_videos(
    videos: List[Dict],
    subnicho: str,
    previous_micronichos: Optional[List[str]] = None
) -> Dict:
    """
    Classifica cada video em exatamente 1 micronicho via LLM.

    Args:
        videos: lista de dicts com 'title'
        subnicho: subnicho do canal
        previous_micronichos: lista de micronichos de analise anterior (consistencia)

    Returns:
        {
            "classifications": [{"title": str, "micronicho": str}, ...],
            "all_micronichos": [str, ...]
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

    # System prompt — Classificacao de Micronichos
    system_prompt = """Voce e um classificador especializado em subcategorias tematicas (micronichos)
dentro de canais YouTube.

=== O QUE E UM MICRONICHO ===

Um micronicho e uma SUBCATEGORIA TEMATICA contida dentro do subnicho (foco) do canal.
E o nivel intermediario entre o subnicho (amplo) e o tema individual (1 video).

Hierarquia: Nicho > Subnicho (canal) > MICRONICHO (subcategoria) > Tema (video)

MICRONICHO = CATEGORIA que agrupa multiplos videos sob um mesmo guarda-chuva tematico.
TEMA = assunto especifico de 1 video individual.

=== 6 CARACTERISTICAS DE UM MICRONICHO ===

1. E uma CATEGORIA, nao um assunto individual.
   "Espionagem Militar" = micronicho (abriga dezenas de videos possiveis)
   "A historia do espiao Klaus Fuchs" = tema (1 video especifico)

2. E CONTIDO dentro do subnicho do canal.
   Canal de "Relatos de Guerra" → "Espionagem Militar" faz sentido
   Canal de "Relatos de Guerra" → "Receitas de Bolo" NAO faz sentido
   Mas "Alimentacao nas Trincheiras" SIM faz sentido

3. Um subnicho tem MUITOS micronichos possiveis.
   A riqueza de micronichos determina a capacidade de variacao do canal.

4. Mantenha granularidade MEDIA.
   Muito amplo: "Pessoas" (vago demais, agrupa tudo)
   Muito especifico: "Espiao Russo na Alemanha em 1943" (e um tema, nao categoria)
   Correto: "Espionagem e Inteligencia Militar" (agrupa espioes de qualquer lado/epoca)

5. Micronichos tem "tamanhos" diferentes.
   Alguns sao vastos (dezenas de temas possiveis), outros limitados (5-10).
   Ambos sao validos — o ranking mostra qual performa.

6. A audiencia tem preferencias DIFERENTES por micronicho.
   Dentro do mesmo canal, performance varia drasticamente entre micronichos.
   Detectar isso e o objetivo central desta classificacao.

=== EXEMPLOS POR SUBNICHO ===

Relatos de Guerra:
  Prisioneiros, Espionagem, Herois Nao Declarados, Batalhas Decisivas,
  Armamentos, Vida Civil, Estrategia de Comando, Crimes de Guerra

Historias Sombrias:
  Serial Killers, Misterios Nao Resolvidos, Cultos e Seitas,
  Desaparecimentos, Crimes Historicos, Lugares Assombrados

Terror/Horror:
  Lendas Urbanas, Casos Reais, Sobrenatural, Psicologia do Medo,
  Historias de Sobrevivencia, Fenomenos Inexplicaveis

=== REGRAS DE CLASSIFICACAO ===

1. Cada video pertence a EXATAMENTE 1 micronicho (classificacao exclusiva, sem dupla contagem)
2. Micronichos devem ser CATEGORIAS replicaveis (multiplos videos possiveis na categoria)
3. Use nomes descritivos e curtos (2-5 palavras)
4. Se o video nao se encaixa em nenhum micronicho claro, use "Outros"
5. CONSISTENCIA: se uma categoria ja existe na lista anterior, USE EXATAMENTE o mesmo nome
   (nao crie "Espioes de Guerra" se ja existe "Espionagem Militar")
6. Responda APENAS com JSON valido, sem explicacao ou texto adicional
7. Nao crie micronichos redundantes — se 2 categorias sao muito parecidas, unifique"""

    # User prompt
    prev_block = ""
    if previous_micronichos:
        prev_list = "\n".join([f"- {m}" for m in previous_micronichos])
        prev_block = f"""Micronichos ja identificados em analises anteriores (mantenha consistencia):
{prev_list}

"""

    titles_list = "\n".join([f"{i+1}. {v['title']}" for i, v in enumerate(videos)])

    user_prompt = f"""{prev_block}Subnicho do canal: {subnicho}

Classifique CADA titulo em exatamente 1 micronicho.

Titulos:
{titles_list}

JSON de saida:
{{
  "videos": [
    {{"title": "...", "micronicho": "..."}},
    ...
  ],
  "all_micronichos": ["...", "..."]
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
            all_micronichos = result.get("all_micronichos", [])

            # Se all_micronichos nao veio, extrair das classificacoes
            if not all_micronichos:
                all_micronichos = list(set(c.get("micronicho", "Outros") for c in classifications))

            logger.info(f"LLM classificou {len(classifications)} videos em {len(all_micronichos)} micronichos")
            return {
                "classifications": classifications,
                "all_micronichos": all_micronichos
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
        "classifications": [{"title": v["title"], "micronicho": "Nao Classificado"} for v in videos],
        "all_micronichos": ["Nao Classificado"]
    }


# =============================================================================
# ETAPA 3: CONSTRUCAO DO RANKING
# =============================================================================

def build_ranking(videos: List[Dict], classifications: List[Dict]) -> List[Dict]:
    """
    Agrupa videos por micronicho e calcula ranking por avg views.

    Args:
        videos: lista com {title, views, age_days, ...}
        classifications: lista com {title, micronicho}

    Returns:
        Lista de ranking entries ordenada por avg_views DESC
    """
    # Criar mapa titulo -> micronicho
    title_to_micro = {}
    for c in classifications:
        title_to_micro[c.get("title", "")] = c.get("micronicho", "Outros")

    # Agrupar videos por micronicho
    groups = {}
    for v in videos:
        micro = title_to_micro.get(v["title"], "Outros")
        if micro not in groups:
            groups[micro] = []
        groups[micro].append(v)

    # Calcular metricas por micronicho
    ranking = []
    for micro_name, micro_videos in groups.items():
        views_list = [v["views"] for v in micro_videos]
        total_views = sum(views_list)
        avg_views = total_views / len(micro_videos) if micro_videos else 0

        best = max(micro_videos, key=lambda x: x["views"])
        worst = min(micro_videos, key=lambda x: x["views"])

        ranking.append({
            "micronicho": micro_name,
            "video_count": len(micro_videos),
            "avg_views": round(avg_views, 1),
            "total_views": total_views,
            "best_video": {
                "title": best["title"],
                "views": best["views"],
                "age_days": best["age_days"]
            },
            "worst_video": {
                "title": worst["title"],
                "views": worst["views"],
                "age_days": worst["age_days"]
            }
        })

    # Ordenar por avg_views DESC
    ranking.sort(key=lambda x: x["avg_views"], reverse=True)

    # Adicionar rank
    for i, entry in enumerate(ranking):
        entry["rank"] = i + 1

    return ranking


# =============================================================================
# ETAPA 4: DETECCAO DE PADROES
# =============================================================================

def detect_patterns(ranking: List[Dict]) -> Dict:
    """
    Detecta padroes no ranking de micronichos.

    Returns:
        {
            "concentration_pct": float,
            "top_performers": [...],
            "bottom_performers": [...],
            "single_video_micronichos": [...],
            "total_micronichos": int,
            "total_videos": int,
            "avg_views_geral": float
        }
    """
    if not ranking:
        return {
            "concentration_pct": 0,
            "top_performers": [],
            "bottom_performers": [],
            "single_video_micronichos": [],
            "total_micronichos": 0,
            "total_videos": 0,
            "avg_views_geral": 0
        }

    total_views_all = sum(r["total_views"] for r in ranking)
    total_videos_all = sum(r["video_count"] for r in ranking)

    # Media geral de views por video
    avg_views_geral = total_views_all / total_videos_all if total_videos_all > 0 else 0

    # Concentracao: % de views nos top 3
    top_3_views = sum(r["total_views"] for r in ranking[:3])
    concentration_pct = round((top_3_views / total_views_all * 100) if total_views_all > 0 else 0, 1)

    # Top performers: avg_views acima da media geral
    top_performers = [r["micronicho"] for r in ranking if r["avg_views"] > avg_views_geral]

    # Bottom performers: avg_views abaixo de 50% da media
    half_avg = avg_views_geral * 0.5
    bottom_performers = [r["micronicho"] for r in ranking if r["avg_views"] < half_avg]

    # Micronichos com 1 video
    single_video = [r["micronicho"] for r in ranking if r["video_count"] == 1]

    return {
        "concentration_pct": concentration_pct,
        "top_performers": top_performers,
        "bottom_performers": bottom_performers,
        "single_video_micronichos": single_video,
        "total_micronichos": len(ranking),
        "total_videos": total_videos_all,
        "avg_views_geral": round(avg_views_geral, 1)
    }


# =============================================================================
# ETAPA 5: NARRATIVA VIA LLM (Call 2)
# =============================================================================

def _format_views(n: int) -> str:
    """Formata views: 1500 -> 1.5K, 150000 -> 150K"""
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def _format_ranking_table(ranking: List[Dict]) -> str:
    """Formata ranking como tabela texto."""
    lines = []
    lines.append(f"  {'#':>3}  {'Micronicho':<30} {'Videos':>6}  {'Avg Views':>10}  {'Total Views':>12}  {'Melhor (idade)':>20}  {'Pior (idade)':>20}")
    lines.append(f"  {'---':>3}  {'-'*30} {'------':>6}  {'-'*10}  {'-'*12}  {'-'*20}  {'-'*20}")

    for r in ranking:
        best = f"{_format_views(r['best_video']['views'])} ({r['best_video']['age_days']}d)"
        worst = f"{_format_views(r['worst_video']['views'])} ({r['worst_video']['age_days']}d)"
        lines.append(
            f"  {r['rank']:>3}  {r['micronicho']:<30} {r['video_count']:>6}  "
            f"{_format_views(int(r['avg_views'])):>10}  {_format_views(r['total_views']):>12}  "
            f"{best:>20}  {worst:>20}"
        )

    return "\n".join(lines)


def _format_patterns(patterns: Dict) -> str:
    """Formata padroes como texto."""
    lines = []
    lines.append(f"- Concentracao top 3: {patterns['concentration_pct']}%")
    lines.append(f"- Media geral de views: {_format_views(int(patterns['avg_views_geral']))}")
    lines.append(f"- Total micronichos: {patterns['total_micronichos']}")
    lines.append(f"- Total videos: {patterns['total_videos']}")

    if patterns["top_performers"]:
        lines.append(f"- Top performers (acima da media): {', '.join(patterns['top_performers'])}")
    if patterns["bottom_performers"]:
        lines.append(f"- Bottom performers (<50% da media): {', '.join(patterns['bottom_performers'])}")
    if patterns["single_video_micronichos"]:
        lines.append(f"- Micronichos de 1 video: {', '.join(patterns['single_video_micronichos'])}")

    return "\n".join(lines)


def generate_narrative(
    channel_name: str,
    subnicho: str,
    ranking: List[Dict],
    patterns: Dict,
    total_videos: int,
    comparison: Optional[Dict] = None
) -> Optional[Dict]:
    """
    LLM Call 2: gera narrativa interpretando o ranking.

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

    # System prompt — Narrativa Profissional de Micronichos
    system_prompt = """Voce e um analista de performance de conteudo YouTube, especializado em
identificar subcategorias tematicas (micronichos) que viralizam dentro de canais.

=== O QUE SAO MICRONICHOS ===

Cada canal tem um SUBNICHO (foco geral). Dentro desse subnicho, existem
MICRONICHOS — subcategorias tematicas que agrupam videos por tema.

Exemplo: Canal de "Historias Sombrias" pode ter micronichos como
"Serial Killers", "Misterios Nao Resolvidos", "Cultos e Seitas", etc.

Os micronichos sao a UNIDADE FUNDAMENTAL de diversificacao. Importam por 3 razoes:
1. PERFORMANCE: micronichos diferentes tem views drasticamente diferentes.
   Saber qual funciona muda completamente a estrategia de producao.
2. PROTECAO: 80% dos videos no mesmo micronicho = risco de inauthentic content.
   Variar micronichos protege contra derrubada do YouTube.
3. OPORTUNIDADE: micronichos pouco explorados com alta performance = ouro.
   O canal pode estar sentado numa mina sem saber.

=== SEU PAPEL ===

Voce recebe uma TABELA DE RANKING ja calculada pelo Python (toda a matematica
foi feita — views medias, totais, melhor/pior video, concentracao).
Seu trabalho e INTERPRETAR os padroes e dar recomendacoes estrategicas.

=== METRICA: VIEWS BRUTAS + IDADE COMO CONTEXTO ===

Usamos views brutas como metrica de performance.
A IDADE do video e o contexto interpretativo — NAO normalizamos por idade.
A idade aparece como informacao complementar que VOCE interpreta no texto:

- 50K views em 7 dias = video VIRAL (velocidade excepcional)
- 50K views em 90 dias = video NORMAL (acumulacao lenta)
- 100K em 12 dias > 100K em 60 dias (mesmo numero, significados diferentes)

SEMPRE mencione a idade ao interpretar um numero de views.

=== O QUE VOCE DEVE ANALISAR ===

1. TOP PERFORMERS: Quais micronichos tem mais views? Por que se destacam?
   Analise CONSISTENCIA: todos os videos do micronicho performam bem,
   ou e um outlier unico puxando a media? Isso muda TUDO na recomendacao.
   - Se consistente (todos acima da media) = demanda REAL, pode escalar
   - Se 1 viral + varios fracos = outlier, nao confirma demanda

2. BOTTOM PERFORMERS: Quais micronichos estao fracos?
   Diferencie: falta de interesse da audiencia VS poucas tentativas.
   - 5 videos com avg baixo = audiencia NAO quer esse tema
   - 1 video com views baixas = amostra insuficiente, nao condenar

3. CONCENTRACAO: A audiencia esta concentrada em poucos micronichos?
   - Alta concentracao (>60% views nos top 3) = risco de dependencia
   - Baixa concentracao = boa diversificacao tematica
   - Concentracao alta + performance alta = FUNCIONA mas e arriscado

4. MICRONICHOS DE 1 VIDEO: Oportunidades ou sinais fracos?
   - 1 video com views ALTAS = oportunidade a explorar urgentemente
   - 1 video com views BAIXAS = amostra insuficiente, nao condenar ainda
   - Nunca recomende abandonar com base em apenas 1 video

5. CANIBALIZACAO: 2+ micronichos muito parecidos competindo entre si?
   Se existem, sugira unificar ou diferenciar claramente.

6. RECOMENDACOES DE NOVOS MICRONICHOS: Baseado no padrao de preferencia
   da audiencia (ex: prefere narrativas humanas vs analises tecnicas),
   sugira micronichos que o canal AINDA NAO TESTOU mas que fazem sentido
   dentro do subnicho. Esta e a capacidade mais "inteligente" da analise.

=== DIFERENCA DOS OUTROS AGENTES ===

O Agente de Copy (Agente 1) analisa COMO o video e escrito (estrutura narrativa A-Z).
O Agente de Autenticidade (Agente 2) analisa se o canal parece automatizado.
Este agente analisa SOBRE O QUE o video fala (tema/micronicho).
Sao dimensoes complementares. NAO mencione estrutura de copy ou autenticidade aqui.

O relatorio sera consumido por um agente-chefe (Agente 6) que cruza outputs
de todos os agentes para tomar decisoes de conteudo.

=== REGRAS INVIOLAVEIS ===

1. Seja FACTUAL — cite numeros EXATOS do ranking fornecido
2. NAO invente dados — use APENAS o que esta no ranking
3. Considere a IDADE do video ao interpretar views (SEMPRE mencione)
4. Cada recomendacao DEVE citar dados especificos (micronicho, views, titulo do video)
5. NAO repita a tabela de ranking — ela ja esta no relatorio
6. Escreva em portugues, paragrafos curtos separados por linha em branco
7. Escreva o quanto for necessario. NAO resuma, NAO corte a analise
8. Use EXATAMENTE os marcadores [OBSERVACOES], [RECOMENDACOES] e [TENDENCIAS]
9. Priorize recomendacoes: [ALTA] = oportunidade forte, [MEDIA] = testar, [BAIXA] = monitorar

=== TIPO DE RACIOCINIO ESPERADO ===

NAO FACA ISSO (superficial):
"O micronicho X tem boas views. Recomendo fazer mais videos."

FACA ISSO (profissional — diagnostico direto, dados concretos, sem enrolacao):
"'Herois Nao Declarados' lidera com avg 87.5K views (4 videos). Destaque para
'O Soldado que Salvou 200 Vidas' com 180K em 12 dias — potencial viral ATIVO.
Os outros 3 videos mantem media de 55K, indicando demanda CONSISTENTE (nao outlier).

'Espionagem e Inteligencia' em 2o com avg 72.3K (3 videos). Performance estavel —
o pior video (52K em 22 dias) ainda esta acima da media geral do canal (53K).
Consistencia alta = demanda confirmada.

Padrao: audiencia responde FORTEMENTE a narrativas humanas pessoais (herois,
espioes, prisioneiros) e FRACAMENTE a conteudo analitico/tecnico (estrategia
de comando: 12K em 52 dias, armamentos: avg 28K).

[ALTA] Produzir 3+ videos de 'Herois Nao Declarados' nos proximos 15 videos.
Consistencia de 55K+ indica demanda real. Variar angulos: herois anonimos
de diferentes nacionalidades, sacrificios esquecidos, ultimas cartas.

[ALTA] Testar micronicho NOVO 'Fugas e Evasoes' — tema adjacente a
'Tratamento de Prisioneiros' (avg 58.2K, 5 vids) que combina elemento
humano + suspense narrativo. Potencial baseado no padrao de preferencia.

[MEDIA] Expandir 'Espionagem e Inteligencia' para 5+ videos.
Consistencia confirmada, mas volume ainda baixo (3 vids).

[BAIXA] Monitorar 'Estrategia de Alto Comando' — com 1 video e 12K em 52 dias
nao e possivel concluir. Se o proximo video tambem ficar abaixo de 20K, pausar." """

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

    user_prompt = f"""{previous_report_block}Produza EXATAMENTE 3 blocos:

[OBSERVACOES]
Analise os padroes do ranking. Cubra obrigatoriamente:

1. TOP PERFORMERS: Os 2-3 melhores micronichos.
   Para cada um: avg views, quantidade de videos, melhor video (com idade).
   CONSISTENCIA: todos os videos performam ou so 1 viral puxa a media?
   Se consistente = demanda REAL. Se outlier = nao confirma.

2. BOTTOM PERFORMERS: Os micronichos mais fracos.
   Diferencie CLARAMENTE:
   - Baixa performance com MUITOS videos = audiencia NAO quer
   - Baixa performance com 1 video = amostra insuficiente, NAO condenar

3. PADRAO DE PREFERENCIA: O que a audiencia prefere?
   Identifique o PADRAO: narrativas humanas vs analiticas? Drama vs informativo?
   Cite dados concretos dos top vs bottom para sustentar.

4. CONCENTRACAO: {patterns['concentration_pct']}% das views nos top 3.
   Isso e saudavel ou arriscado? A producao esta alinhada com a demanda?

5. MICRONICHOS DE 1 VIDEO: Para cada um, e oportunidade (views altas)
   ou sinal fraco (views baixas)?

6. CANIBALIZACAO: Existe sobreposicao entre micronichos que poderiam ser unificados?

[RECOMENDACOES]
Acoes CONCRETAS, cada uma com prioridade [ALTA], [MEDIA] ou [BAIXA]:

1. ESCALAR: Quais micronichos merecem mais videos?
   Cite: nome, avg views atual, consistencia, quantos videos produzir.

2. PAUSAR: Quais micronichos tem performance fraca com volume suficiente?
   SO recomende pausar se ha 3+ videos com performance consistentemente baixa.
   NUNCA recomende pausar com base em apenas 1-2 videos.

3. NOVOS MICRONICHOS: Sugira 2-4 micronichos que o canal AINDA NAO TESTOU
   mas que fazem sentido com base no padrao de preferencia da audiencia.
   Para cada novo micronicho sugerido:
   - Nome curto e descritivo
   - Por que faz sentido (conexao com os top performers)
   - Exemplos de possiveis temas/videos

4. REDISTRIBUICAO: Se concentracao > 50%, como redistribuir producao?
   Cite: de qual micronicho reduzir, para qual aumentar, com numeros.

[TENDENCIAS]
EVOLUCAO ao longo do tempo (SO se houver relatorio anterior):
- Micronichos que subiram ou cairam no ranking (cite posicoes e views)
- Novos micronichos que apareceram desde a ultima analise
- Recomendacoes anteriores que foram implementadas (se detectavel nos dados)
- Mudancas no padrao de preferencia da audiencia
- Se primeira analise: "Primeira analise. Sem dados anteriores para comparacao."

DADOS DO CANAL:
Canal: {channel_name}
Subnicho: {subnicho}
Videos analisados: {total_videos} (com 7+ dias de maturidade)

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
    all_micronichos: List[str]
) -> str:
    """Gera relatorio formatado de micronichos."""
    now = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")

    report = []
    report.append("=" * 60)
    report.append(f"ANALISE DE MICRONICHOS | {channel_name} | {now}")
    report.append("=" * 60)
    report.append("")

    # Ranking table
    report.append("RANKING DE MICRONICHOS (por media de views):")
    report.append("")
    report.append(_format_ranking_table(ranking))
    report.append("")

    # Sumario
    report.append(f"Micronichos identificados: {len(all_micronichos)}")
    report.append(f"Videos analisados: {total_videos}")
    report.append(f"Concentracao top 3: {patterns['concentration_pct']}%")
    report.append(f"Media geral de views: {_format_views(int(patterns['avg_views_geral']))}")
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
        prev_count = comparison.get("previous_micronicho_count")
        if prev_count is not None:
            report.append(f"  Micronichos anterior: {prev_count} → atual: {len(all_micronichos)}")
        prev_videos = comparison.get("previous_total_videos")
        if prev_videos is not None:
            report.append(f"  Videos anterior: {prev_videos} → atual: {total_videos}")
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
    all_micronichos: List[str],
    report_text: str,
    patterns: Dict,
    total_videos: int
) -> Optional[int]:
    """Salva analise no banco."""

    run_data = {
        "channel_id": channel_id,
        "channel_name": channel_name,
        "micronicho_count": len(all_micronichos),
        "total_videos_analyzed": total_videos,
        "concentration_pct": patterns.get("concentration_pct"),
        "ranking_json": json.dumps(ranking),
        "micronichos_list": json.dumps(all_micronichos),
        "patterns_json": json.dumps(patterns),
        "report_text": report_text
    }

    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/micronicho_analysis_runs",
        headers=SUPABASE_HEADERS,
        json=run_data
    )

    if resp.status_code not in [200, 201]:
        logger.error(f"Erro ao salvar analise de micronichos: {resp.status_code} - {resp.text[:200]}")
        return None

    result = resp.json()
    run_id = result[0]["id"] if result else None
    logger.info(f"Analise de micronichos salva: run_id={run_id}")
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
        f"{SUPABASE_URL}/rest/v1/micronicho_analysis_runs",
        params={
            "channel_id": f"eq.{channel_id}",
            "select": "run_date,micronicho_count,total_videos_analyzed,"
                      "concentration_pct,micronichos_list,report_text",
            "order": "run_date.desc",
            "limit": "1"
        },
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    )

    if resp.status_code != 200 or not resp.json():
        return None

    prev = resp.json()[0]
    prev_micronichos = prev.get("micronichos_list")
    if isinstance(prev_micronichos, str):
        try:
            prev_micronichos = json.loads(prev_micronichos)
        except (json.JSONDecodeError, TypeError):
            prev_micronichos = []

    return {
        "previous_date": prev.get("run_date", ""),
        "previous_micronicho_count": prev.get("micronicho_count"),
        "previous_total_videos": prev.get("total_videos_analyzed"),
        "previous_concentration": prev.get("concentration_pct"),
        "previous_micronichos": prev_micronichos or [],
        "previous_report": prev.get("report_text", "")
    }


# =============================================================================
# ETAPA 9: FUNCOES DE CONSULTA (usadas pelos endpoints)
# =============================================================================

def get_latest_analysis(channel_id: str) -> Optional[Dict]:
    """Retorna a analise de micronichos mais recente."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/micronicho_analysis_runs",
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
        for field in ["ranking_json", "micronichos_list", "patterns_json"]:
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
        f"{SUPABASE_URL}/rest/v1/micronicho_analysis_runs",
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
        f"{SUPABASE_URL}/rest/v1/micronicho_analysis_runs",
        params={
            "channel_id": f"eq.{channel_id}",
            "select": "id,channel_name,run_date,micronicho_count,"
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
# ETAPA 10: CANAIS DISPONIVEIS PARA MICRONICHOS
# =============================================================================

def get_channels_for_micronicho() -> List[Dict]:
    """
    Retorna todos canais ativos (NAO precisa de spreadsheet).
    Diferente de get_all_channels_for_analysis que exige copy_spreadsheet_id.
    """
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
# ETAPA 11: FUNCAO PRINCIPAL
# =============================================================================

def run_analysis(channel_id: str) -> Dict:
    """
    Executa analise completa de micronichos para um canal.

    Returns:
        {
            "success": bool,
            "channel_id": str,
            "channel_name": str,
            "run_id": int,
            "report": str,
            "micronicho_count": int,
            "total_videos": int,
            "ranking": [...],
            "error": str (se falhou)
        }
    """
    logger.info(f"{'='*50}")
    logger.info(f"MICRONICHOS: Iniciando para canal {channel_id}")
    logger.info(f"{'='*50}")

    # 1. Buscar dados do canal
    channel_info = _get_channel_info(channel_id)
    if not channel_info:
        return {"success": False, "error": f"Canal {channel_id} nao encontrado em yt_channels"}

    channel_name = channel_info.get("channel_name", channel_id)
    subnicho = channel_info.get("subnicho", "N/A")

    logger.info(f"Canal: {channel_name} | Subnicho: {subnicho}")

    # 2. Buscar videos (filtro 7+ dias ja aplicado)
    videos = _fetch_channel_videos(channel_id)
    if not videos:
        return {"success": False, "error": f"Nenhum video encontrado para o canal"}

    if len(videos) < MIN_VIDEOS:
        return {"success": False, "error": f"Minimo {MIN_VIDEOS} videos necessarios, encontrados: {len(videos)}"}

    # 3. Buscar micronichos anteriores (para consistencia de nomes)
    comparison = compare_with_previous(channel_id)
    previous_micronichos = comparison.get("previous_micronichos", []) if comparison else []

    # 4. LLM Call 1: classificar videos em micronichos
    classification_result = classify_videos(videos, subnicho, previous_micronichos)
    classifications = classification_result["classifications"]
    all_micronichos = classification_result["all_micronichos"]

    logger.info(f"Classificacao: {len(classifications)} videos em {len(all_micronichos)} micronichos")

    # 5. Construir ranking
    ranking = build_ranking(videos, classifications)

    # 6. Detectar padroes
    patterns = detect_patterns(ranking)

    # 7. LLM Call 2: narrativa
    llm_narrative = generate_narrative(
        channel_name, subnicho, ranking, patterns,
        len(videos), comparison
    )

    # 8. Gerar relatorio
    report = generate_report(
        channel_name, ranking, patterns, llm_narrative,
        comparison, len(videos), all_micronichos
    )

    # 9. Salvar
    run_id = save_analysis(
        channel_id, channel_name, ranking, all_micronichos,
        report, patterns, len(videos)
    )

    logger.info(f"MICRONICHOS COMPLETA: {channel_name} | {len(all_micronichos)} micronichos | {len(videos)} videos")

    return {
        "success": True,
        "channel_id": channel_id,
        "channel_name": channel_name,
        "run_id": run_id,
        "report": report,
        "micronicho_count": len(all_micronichos),
        "total_videos": len(videos),
        "ranking": ranking
    }

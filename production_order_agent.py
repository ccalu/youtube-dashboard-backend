"""
Agente 7 — Ordenador de Producao
Camada 3 (Decisao)

Analisa scripts pendentes na planilha de producao e recomenda a ordem ideal
de producao/postagem, maximizando viralizacao (motores psicologicos) e
protegendo a saude do canal (inauthentic content).

Dependencias obrigatorias:
- Agente 5 (Motores) — hierarquia de motores psicologicos
- Agente 3 (Autenticidade) — diagnostico de saude do canal
"""

import os
import json
import hashlib
import logging
import re
import requests
from datetime import datetime, timezone
from typing import List, Dict, Optional

from copy_analysis_agent import (
    _get_channel_info,
    SUPABASE_URL,
    SUPABASE_KEY,
    VALID_STRUCTURES,
)
from motor_agent import _strip_markdown, _create_agent_job

logger = logging.getLogger("production_order_agent")


# =============================================================================
# SYSTEM PROMPT — LLM ORDENADOR
# =============================================================================

SYSTEM_PROMPT_ORDENADOR = """Voce e um estrategista de producao YouTube especializado em otimizar a SEQUENCIA DE PRODUCAO de canais. Voce trabalha para uma operacao que gerencia dezenas de canais YouTube simultaneamente.

Seu trabalho e decidir QUAL VIDEO PRODUZIR PRIMEIRO para maximizar crescimento e faturamento, ao mesmo tempo protegendo o canal contra a politica de Inauthentic Content do YouTube.

=== CONTEXTO: POR QUE ISSO IMPORTA ===

Scripts pendentes na planilha ficam em ORDEM ARBITRARIA (ordem de upload). A equipe de producao simplesmente produz de cima para baixo, sem estrategia. Isso significa:
- Scripts com alto potencial de viralizacao ficam esperando enquanto scripts medianos sao produzidos primeiro
- Sem controle da sequencia, o canal pode publicar varios videos seguidos com a mesma estrutura de copy, ativando a politica de Inauthentic Content e arriscando desmonetizacao

Voce resolve esses dois problemas simultaneamente.

=== O QUE VOCE RECEBE ===

1. HIERARQUIA DE MOTORES PSICOLOGICOS — ranking dos motores que estao performando melhor na audiencia do canal naquele momento (baseado em CTR + Views dos videos recentes). Gerado pelo Agente de Motores (Agente 5)
2. DIAGNOSTICO DE AUTENTICIDADE — saude do canal baseada na VARIEDADE DE ESTRUTURAS DE COPY usadas nos videos recentes. Se o canal repete a mesma estrutura de copy em muitos videos consecutivos, o YouTube pode classificar como "Inauthentic Content" (conteudo produzido em massa, baseado em template). Inclui: score 0-100, nivel (excelente/bom/atencao/risco/critico), distribuicao de estruturas de copy, alertas. A frequencia de postagem ja vem embutida neste diagnostico. Gerado pelo Agente de Autenticidade (Agente 3)
3. LISTA DE SCRIPTS PENDENTES — cada script com: estrutura de copy (uma letra que identifica o tipo de estrutura narrativa — cada canal tem seu proprio conjunto de letras), titulo, e numero da linha na planilha. Apenas scripts com status "to do"

=== SEU TRABALHO (2 PILARES) ===

PILAR 1 — POTENCIAL DE VIRALIZACAO (motores psicologicos):
- Ler cada titulo pendente e IDENTIFICAR quais motores psicologicos ele carrega
- Comparar com a hierarquia de motores do canal (quais motores dominam no CTR + Views)
- Titulos alinhados com os motores #1 e #2 do canal SOBEM na fila
- Titulos sem alinhamento com nenhum motor que performa bem CAEM naturalmente para o final

PILAR 2 — SAUDE DO CANAL (inauthentic content):
- Funciona como MODULADOR da priorizacao do Pilar 1
- Se canal SAUDAVEL (bom/excelente): Pilar 1 domina. Estruturas consecutivas permitidas
- Se canal EM RISCO (atencao/risco/critico): intercalar estruturas. NUNCA mesma estrutura consecutiva. Proteger monetizacao mesmo sacrificando potencial viral imediato

=== REGRAS CRITICAS DE ORDENACAO ===

SOBRE POSICIONAMENTO:
- Posicao #1 = PROXIMO video a ser produzido e publicado. E a decisao mais importante
- Titulos que ativam motores #1 + #2 da hierarquia = tier ALTA (produzir primeiro)
- Titulos que ativam motores presentes mas nao dominantes = tier NORMAL
- Titulos sem alinhamento com nenhum motor atual = tier BAIXA (final da fila)
- Se 2 titulos ativam os mesmos motores, desempate por diversidade de estrutura

SOBRE IDENTIFICACAO DE MOTORES:
- Use a hierarquia fornecida pelo Agente de Motores como REFERENCIA PRINCIPAL
- Analise cada titulo e identifique quais motores psicologicos ele ativa
- Um titulo pode ativar MULTIPLOS motores (combinacoes sao comuns e valiosas)
- A FORCA do alinhamento depende de quantos motores top o titulo ativa e quao dominantes eles sao
- Se um titulo ativa um anti-pattern identificado pelo Agente de Motores, classifique como BAIXA e alerte

SOBRE INTERCALACAO (APENAS quando canal em ATENCAO, RISCO ou CRITICO):
- Estruturas DEVEM alternar: se posicao #1 e estrutura B, posicao #2 NAO pode ser B
- Se impossivel intercalar perfeitamente, MAXIMIZE a distancia entre mesma estrutura
- SEMPRE registre nos warnings quando intercalacao forcar reordenacao (ex: "Script X rebaixado de #2 para #4 por intercalacao de estrutura")
- Um script rebaixado por intercalacao NAO muda de tier — apenas de posicao dentro do tier ou entre tiers adjacentes

SOBRE INTERCALACAO (quando canal SAUDAVEL — nivel BOM ou EXCELENTE):
- Foco EXCLUSIVO nos motores psicologicos
- Estruturas consecutivas sao permitidas
- NAO aplique intercalacao — seria desperdicio de potencial viral

=== REGRAS INVIOLAVEIS ===

1. TODOS os scripts pendentes devem aparecer na ordenacao — nenhum pode ser omitido
2. NUNCA invente motores que nao existam na hierarquia fornecida
3. Cada justificativa DEVE citar dados especificos (motor #X, score, correlacao)
4. Idade do script e IRRELEVANTE — scripts antigos e novos sao tratados igual
5. O relatorio e RECOMENDACAO — o operador decide se segue. NAO escreva como ordem
6. Escreva o quanto for necessario. NAO resuma, NAO corte. Cada script merece justificativa

=== TIPO DE RACIOCINIO ESPERADO ===

NAO FACA ISSO (superficial):
  Posicao #1: "Titulo X" — Motor forte
  Posicao #2: "Titulo Y" — Motor presente

FACA ISSO (profissional — com dados e raciocinio):
  Posicao #1: "To, Chto Konkistadory Delali s Zhenshchinami..." (Estrutura E, Linha 39)
    Motores: Curiosidade Proibida + Revelacao (Motor #1 + #3 da hierarquia)
    Justificativa: Ativa os 2 motores mais fortes do canal. "Curiosidade Proibida" aparece
    em 8/20 videos (40%) com score medio 78/100. Combinado com "Revelacao", o efeito e
    amplificado (correlacao COM ambos: score 82 vs media geral 55). Estrutura E quebra a
    sequencia de Estruturas A que domina o canal (40%).

  Posicao #4: "Noga Genrikha VIII Gnila Zazhivo..." (Estrutura A, Linha 41)
    Motores: Grotesco Corporal + Ironia Historica (Motor #2 + #5)
    Justificativa: Motor #2 dominante, combinacao forte. POREM: rebaixado de #2 para #4
    por intercalacao — canal em nivel ATENCAO com 40% de Estrutura A nos ultimos 15 videos.
    Ja ha 1 script Estrutura A na posicao #4, proximo Estrutura A so apos posicao #7.

=== FORMATO DE RESPOSTA ===

PRIMEIRO emita o bloco JSON entre [JSON_START] e [JSON_END].
DEPOIS emita as 4 secoes de texto do relatorio.
O JSON DEVE ser valido e parseable. TODOS os scripts pendentes devem estar no JSON.

[JSON_START]
{
  "ordered_scripts": [
    {
      "position": 1,
      "row_number": 39,
      "title": "titulo completo do script",
      "structure": "E",
      "tier": "alta",
      "motors_identified": ["Curiosidade Proibida", "Revelacao"],
      "justification": "Ativa Motor #1 + #3. Correlacao combinada: score 82 vs media 55"
    },
    {
      "position": 2,
      "row_number": 42,
      "title": "titulo completo",
      "structure": "B",
      "tier": "alta",
      "motors_identified": ["Maldicao"],
      "justification": "Motor #1 dominante. Score medio COM motor: 71"
    }
  ],
  "tier_summary": {
    "alta": {"count": 4, "description": "Ativam motores #1 e/ou #2 da hierarquia"},
    "normal": {"count": 6, "description": "Motores presentes mas nao dominantes"},
    "baixa": {"count": 4, "description": "Sem alinhamento com motores atuais do canal"}
  },
  "structure_intercalation_applied": true,
  "warnings": [
    "Script 'Noga Genrikha VIII...' (Estrutura A) rebaixado de #2 para #4 — canal com 40% Estrutura A",
    "Script 'To, Chto Genrikh VIII...' (Estrutura A) rebaixado de #5 para #9 — ja ha 1 Estrutura A nos tiers superiores"
  ]
}
[JSON_END]

[JUSTIFICATIVA DA ORDENACAO]
Paragrafo(s) explicando:
- Qual logica geral foi usada (quais motores dominam e como os titulos se alinham)
- Estado de saude do canal e se intercalacao foi necessaria
- Quantos scripts em cada tier e por que
- Se algum script foi rebaixado, mencione aqui brevemente (detalhe na Secao 4)

Exemplo:
  Ordenacao baseada na hierarquia de motores psicologicos do canal (CTR + Views dos
  ultimos 20 videos). Os motores dominantes sao "Curiosidade Proibida" (Motor #1, 40%
  dos videos, score medio 78) e "Grotesco Corporal" (Motor #2, 35%, score 72).

  SAUDE DO CANAL: nivel ATENCAO (score 48/100). Estrutura A domina com 40% dos ultimos
  15 videos. Intercalacao de estruturas ATIVADA — nenhuma estrutura se repete em
  sequencia direta.

  Distribuicao: 4 scripts ALTA prioridade (ativam motores top), 6 NORMAL, 4 BAIXA.
  2 scripts rebaixados por intercalacao de estrutura (detalhes na Secao 4).

[TABELA DE PRODUCAO]
Tabela texto puro com TODOS os scripts ordenados. Formato:

Pos | Tier   | Estr | Linha | Titulo                                          | Motores Detectados              | Justificativa
1   | ALTA   | E    | 39    | To, Chto Konkistadory Delali s Zhenshchinami...  | Curiosidade Proibida, Revelacao  | Alinhado com Motor #1 e #3
2   | ALTA   | B    | 42    | Proklyatie Tutankhamona: 22 Cheloveka Pogibli... | Maldicao, Misterio Historico     | Motor #1 dominante
3   | ALTA   | C    | 40    | To, Chto Kommod Delal s Zhenshchinami na Are...  | Poder Absoluto, Sadismo          | Motor #2 + combinacao forte
4   | ALTA   | A    | 41    | Noga Genrikha VIII Gnila Zazhivo...               | Grotesco Corporal, Ironia        | Motor #2. Rebaixado de #2
5   | NORMAL | D    | 46    | 7 Samykh Chudovishchnykh Kazney...               | Lista Morbida, Poder             | Motor presente mas nao dominante
...
13  | BAIXA  | E    | 48    | Chto Stalo s Zhenshchinami Konstantinopolya...   | —                                | Sem alinhamento com motores atuais
14  | BAIXA  | A    | 50    | Kak Zhili Prostye Lyudi v Srednevekovye...       | —                                | Sem alinhamento com motores atuais

(TODOS os scripts devem aparecer. Truncar titulos longos com ... mas manter legivel)

[INSTRUCOES DE MOVIMENTACAO]
Instrucoes praticas para o operador reorganizar a planilha. Formato:

MOVER linha 39 para posicao 1 (subir — ativa Motor #1 + #3)
MOVER linha 42 para posicao 2 (subir — Motor #1 dominante)
MOVER linha 40 para posicao 3 (subir — Motor #2 + combinacao forte)
MOVER linha 41 para posicao 4 (subir — rebaixado de #2 por intercalacao)
MOVER linha 46 para posicao 5 (subir)
MANTER linha 45 na posicao atual
MOVER linha 48 para posicao 13 (descer — sem motores atuais)

(Incluir TODOS os scripts que mudam de posicao. Scripts que ficam no lugar = MANTER)

[ALERTAS DE INAUTENTICIDADE]
Se canal SAUDAVEL:
  "Canal com saude BOA/EXCELENTE (score X/100) — nenhum alerta de inautenticidade.
  Ordenacao baseada exclusivamente em potencial de viralizacao."

Se canal EM RISCO, para CADA script rebaixado:
  ALERTA: Script "Noga Genrikha VIII Gnila Zazhivo..." (Estrutura A) rebaixado de #2 para #4
  Motivo: Canal em nivel ATENCAO com 40% de Estrutura A nos ultimos 15 videos.
  Diversificacao necessaria — posicao #2 ocupada por Estrutura B para quebrar sequencia.

  ALERTA: Script "To, Chto Genrikh VIII Delal..." (Estrutura A) rebaixado de #5 para #9
  Motivo: Ja ha 1 script de Estrutura A nos tiers superiores (posicao #4).
  Maximo de 1 Estrutura A a cada 4 posicoes para diluir concentracao.

(Cada alerta com: titulo entre aspas, estrutura, posicao original vs nova, motivo especifico)

=== FORMATACAO ===

NUNCA use markdown. O relatorio e exibido em texto puro (pre-formatted).
- NAO use ** (negrito markdown)
- NAO use ### (headers markdown)
- NAO use --- (linhas horizontais markdown)
- NAO use ` (code blocks)
- Use MAIUSCULAS para enfase em vez de negrito
- Use os marcadores [ENTRE COLCHETES] conforme especificado acima
- Use indentacao com espacos para hierarquia
- Responda APENAS com o JSON + as 4 secoes. Nada antes do [JSON_START], nada apos a ultima secao"""


# =============================================================================
# LEITURA DA PLANILHA — SCRIPTS PENDENTES
# =============================================================================

def _read_pending_scripts(copy_spreadsheet_id: str) -> List[Dict]:
    """
    Le a planilha de copy e retorna scripts com status 'to do'.
    Col A = estrutura de copy (letra), Col B = titulo, Col E = status.

    Returns:
        Lista de {structure, title, row_number, status}
    """
    from _features.yt_uploader.sheets import get_sheets_client

    try:
        client = get_sheets_client()
        spreadsheet = client.open_by_key(copy_spreadsheet_id)

        worksheet = None
        for name in ['Página1', 'Pagina1', 'Sheet1', 'Planilha1']:
            try:
                worksheet = spreadsheet.worksheet(name)
                break
            except Exception:
                continue

        if not worksheet:
            worksheet = spreadsheet.sheet1
            logger.warning(f"Nenhuma aba padrao encontrada, usando primeira aba: {worksheet.title}")

        all_rows = worksheet.get_all_values()
        results = []

        for i, row in enumerate(all_rows):
            if i == 0:
                continue  # Pula header

            if len(row) < 5:
                continue

            structure = row[0].strip().upper() if row[0] else ""
            title = row[1].strip() if len(row) > 1 and row[1] else ""
            status = row[4].strip().lower() if len(row) > 4 and row[4] else ""

            # Filtrar: Col A = estrutura valida, Col B = titulo nao vazio, Col E = "to do"
            if (len(structure) == 1 and structure in VALID_STRUCTURES
                    and title
                    and status in ("to do", "todo", "a fazer", "pendente")):
                results.append({
                    "structure": structure,
                    "title": title,
                    "row_number": i + 1,  # 1-indexed (row na planilha)
                })

        logger.info(f"Planilha {copy_spreadsheet_id}: {len(results)} scripts pendentes (to do)")
        return results

    except Exception as e:
        logger.error(f"Erro ao ler planilha {copy_spreadsheet_id}: {e}")
        return []


# =============================================================================
# LOAD DATA — DEPENDENCIAS
# =============================================================================

def _load_latest_motor_run(channel_id: str) -> Optional[Dict]:
    """Carrega ultimo motor_analysis_runs para este canal."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/motor_analysis_runs",
        params={
            "channel_id": f"eq.{channel_id}",
            "select": "id,channel_id,channel_name,run_date,run_number,report_text,motor_counts_json",
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
        val = row.get("motor_counts_json")
        if isinstance(val, str):
            try:
                row["motor_counts_json"] = json.loads(val)
            except (json.JSONDecodeError, TypeError):
                pass
        return row
    return None


def _load_latest_auth_run(channel_id: str) -> Optional[Dict]:
    """Carrega ultimo authenticity_analysis_runs para este canal."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/authenticity_analysis_runs",
        params={
            "channel_id": f"eq.{channel_id}",
            "select": "id,channel_id,channel_name,run_date,authenticity_score,authenticity_level,results_json,report_text",
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
        val = row.get("results_json")
        if isinstance(val, str):
            try:
                row["results_json"] = json.loads(val)
            except (json.JSONDecodeError, TypeError):
                pass
        return row
    return None


# =============================================================================
# SAUDE DO CANAL
# =============================================================================

def _determine_channel_health(auth_run: Dict) -> Dict:
    """
    Determina saude do canal a partir do diagnostico de autenticidade.

    Returns:
        {health_level, score, is_at_risk, dominant_structure, dominant_pct, distribution}
    """
    level = auth_run.get("authenticity_level", "bom")
    score = auth_run.get("authenticity_score", 70)

    results_json = auth_run.get("results_json") or {}
    structure_metrics = results_json.get("structure", {}).get("metrics", {})

    distribution = structure_metrics.get("distribution", {})
    dominant = structure_metrics.get("dominant", "")
    dominant_pct = structure_metrics.get("dominant_pct", 0)

    is_at_risk = level in ("atencao", "risco", "critico")

    return {
        "health_level": level,
        "score": score,
        "is_at_risk": is_at_risk,
        "dominant_structure": dominant,
        "dominant_pct": dominant_pct,
        "distribution": distribution,
    }


# =============================================================================
# DETECCAO INCREMENTAL
# =============================================================================

def _build_scripts_snapshot(scripts: List[Dict]) -> Dict:
    """
    Constroi snapshot dos scripts pendentes para deteccao incremental.
    Returns: {hash: str, scripts: list}
    """
    # Sorted list de (structure, title) para hash deterministico
    sorted_scripts = sorted(
        [(s["structure"], s["title"]) for s in scripts]
    )
    hash_input = json.dumps(sorted_scripts, ensure_ascii=False, sort_keys=True)
    snapshot_hash = hashlib.md5(hash_input.encode("utf-8")).hexdigest()

    return {
        "hash": snapshot_hash,
        "scripts": [{"structure": s["structure"], "title": s["title"], "row_number": s["row_number"]} for s in scripts],
    }


def _get_previous_run(channel_id: str) -> Optional[Dict]:
    """Carrega ultimo production_order_runs para comparacao incremental."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/production_order_runs",
        params={
            "channel_id": f"eq.{channel_id}",
            "select": "id,run_number,report_text,order_json,pending_scripts_snapshot",
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
        for field in ("order_json", "pending_scripts_snapshot"):
            val = row.get(field)
            if isinstance(val, str):
                try:
                    row[field] = json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    pass
        return row
    return None


# =============================================================================
# FORMATACAO DE DADOS PARA PROMPTS
# =============================================================================

def _format_motor_hierarchy(motor_run: Dict) -> str:
    """Formata hierarquia de motores para o prompt."""
    lines = []

    # motor_counts_json: [{motor, count, total_videos, pct, avg_score}]
    motor_counts = motor_run.get("motor_counts_json") or []
    if motor_counts:
        lines.append("HIERARQUIA DE MOTORES (ordenados por frequencia + score):")
        for i, mc in enumerate(motor_counts, 1):
            motor = mc.get("motor", "?")
            count = mc.get("count", 0)
            total = mc.get("total_videos", 0)
            pct = mc.get("pct", 0)
            avg_score = mc.get("avg_score", 0)
            lines.append(
                f"  Motor #{i}: {motor} "
                f"({count}/{total} videos = {pct:.0f}%, score medio {avg_score:.0f}/100)"
            )

    # Trecho relevante do report_text (formula de performance)
    report = motor_run.get("report_text", "")
    if report:
        # Extrair secao de formula/recomendacoes (ate 1500 chars)
        excerpt = report[:1500]
        lines.append("")
        lines.append("TRECHO DO RELATORIO DE MOTORES:")
        lines.append(excerpt)

    return "\n".join(lines) if lines else "Nenhuma hierarquia de motores disponivel."


def _format_auth_diagnosis(auth_run: Dict, health: Dict) -> str:
    """Formata diagnostico de autenticidade para o prompt."""
    lines = []

    score = health.get("score", 0)
    level = health.get("health_level", "?")
    is_at_risk = health.get("is_at_risk", False)
    dominant = health.get("dominant_structure", "?")
    dominant_pct = health.get("dominant_pct", 0)
    distribution = health.get("distribution", {})

    lines.append(f"Score de Autenticidade: {score}/100")
    lines.append(f"Nivel: {level.upper()}")
    lines.append(f"Canal em risco: {'SIM' if is_at_risk else 'NAO'}")
    lines.append(f"Estrutura dominante: {dominant} ({dominant_pct:.0f}%)")

    if distribution:
        dist_parts = [f"{k}={v}" for k, v in sorted(distribution.items())]
        lines.append(f"Distribuicao de estruturas: {', '.join(dist_parts)}")

    # Alertas do auth
    results_json = auth_run.get("results_json") or {}
    alerts = results_json.get("alerts", [])
    if alerts:
        lines.append("")
        lines.append("ALERTAS:")
        for alert in alerts:
            lines.append(f"  - [{alert.get('type', '?')}] {alert.get('message', '')}")

    return "\n".join(lines)


def _format_pending_scripts(scripts: List[Dict]) -> str:
    """Formata lista de scripts pendentes para o prompt."""
    lines = []
    for i, s in enumerate(scripts, 1):
        lines.append(
            f"#{i} | Linha {s['row_number']} | Estrutura: {s['structure']} | "
            f"Titulo: \"{s['title']}\""
        )
    return "\n".join(lines)


# =============================================================================
# CHAMADA LLM
# =============================================================================

def _parse_llm_response(text: str) -> Dict:
    """
    Parseia resposta do LLM: extrai JSON entre [JSON_START]...[JSON_END] + texto report.
    Returns: {order_json: dict|None, report_text: str}
    """
    order_json = None
    report_text = text

    # Extrair bloco JSON
    json_match = re.search(r'\[JSON_START\]\s*(.*?)\s*\[JSON_END\]', text, re.DOTALL)
    if json_match:
        json_str = json_match.group(1).strip()
        try:
            order_json = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"Falha ao parsear JSON do LLM: {e}")

        # Report e tudo que vem depois do JSON
        after_json = text[json_match.end():].strip()
        if after_json:
            report_text = after_json

    return {"order_json": order_json, "report_text": report_text}


def _call_llm(
    scripts: List[Dict],
    motor_run: Dict,
    auth_run: Dict,
    health: Dict,
    channel_info: Dict,
    is_first: bool,
    run_number: int,
    previous_report: Optional[str] = None,
) -> Optional[Dict]:
    """
    Chama LLM para gerar ordenacao de producao.
    Returns: {order_json: dict|None, report_text: str} ou None se falhar.
    """
    from claude_llm_client import is_claude_cli_available, call_claude_cli

    use_claude = is_claude_cli_available()
    claude_model = os.environ.get("CLAUDE_MODEL", "claude-opus-4-6")

    if not use_claude:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY nao configurada e Claude CLI nao disponivel")
            return None
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
        except ImportError:
            logger.error("openai nao instalado e Claude CLI nao disponivel")
            return None
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    else:
        client = None
        model = claude_model
        logger.info(f"[ORDENADOR] Usando Claude CLI modelo={claude_model}")

    channel_name = channel_info.get("channel_name", "Desconhecido")
    lingua = channel_info.get("lingua", "Portugues")
    subnicho = channel_info.get("subnicho", "Geral")

    # Formatar dados
    motor_text = _format_motor_hierarchy(motor_run)
    auth_text = _format_auth_diagnosis(auth_run, health)
    scripts_text = _format_pending_scripts(scripts)

    # Instrucao de risco
    if health["is_at_risk"]:
        risk_instruction = (
            f"ATENCAO: Canal em nivel {health['health_level'].upper()}. "
            f"Estrutura dominante: {health['dominant_structure']} ({health['dominant_pct']:.0f}%). "
            f"INTERCALE estruturas — nunca mesma estrutura consecutiva. Priorize diversidade."
        )
    else:
        risk_instruction = (
            f"Canal com saude {health['health_level'].upper()} (score {health['score']}/100). "
            f"Ordene puramente por alinhamento com motores. Estruturas consecutivas permitidas."
        )

    # Montar user prompt
    if is_first or not previous_report:
        user_prompt = f"""CANAL: {channel_name} ({lingua})
NICHO: {channel_info.get('nicho', 'Geral')} | SUBNICHO: {subnicho}
ANALISE NUMERO: #1 (primeira execucao)

=== HIERARQUIA DE MOTORES (Agente 5 — Motores Psicologicos) ===

{motor_text}

=== DIAGNOSTICO DE AUTENTICIDADE (Agente 3) ===

{auth_text}

=== SCRIPTS PENDENTES ({len(scripts)} scripts com status "to do") ===

{scripts_text}

{risk_instruction}

Ordene os {len(scripts)} scripts acima por prioridade de producao."""
    else:
        user_prompt = f"""CANAL: {channel_name} ({lingua})
NICHO: {channel_info.get('nicho', 'Geral')} | SUBNICHO: {subnicho}
ANALISE NUMERO: #{run_number}

=== RELATORIO ANTERIOR (#{run_number - 1}) ===

{previous_report[:2000]}

=== HIERARQUIA DE MOTORES (Agente 5 — Motores Psicologicos) ===

{motor_text}

=== DIAGNOSTICO DE AUTENTICIDADE (Agente 3) ===

{auth_text}

=== SCRIPTS PENDENTES ({len(scripts)} scripts com status "to do") ===

{scripts_text}

{risk_instruction}

Ordene os {len(scripts)} scripts acima por prioridade de producao.
Compare com o relatorio anterior e explique mudancas na ordenacao."""

    # Chamada LLM com retry
    for attempt in range(2):
        try:
            if use_claude:
                text = call_claude_cli(
                    system_prompt=SYSTEM_PROMPT_ORDENADOR,
                    user_prompt=user_prompt,
                    model=claude_model,
                )
            else:
                response = client.chat.completions.create(
                    model=model,
                    temperature=0.3,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT_ORDENADOR},
                        {"role": "user", "content": user_prompt},
                    ]
                )
                text = response.choices[0].message.content

            # Limpar markdown residual
            text = _strip_markdown(text)

            provider = "Claude" if use_claude else "OpenAI"
            logger.info(f"LLM ORDENADOR OK [{provider}]: {len(text)} chars (tentativa {attempt + 1})")

            return _parse_llm_response(text)

        except Exception as e:
            logger.error(f"Erro LLM ORDENADOR tentativa {attempt + 1}: {e}")

    logger.error("LLM ORDENADOR falhou apos 2 tentativas")
    return None


# =============================================================================
# SAVE / DELETE / QUERY
# =============================================================================

def save_analysis(
    channel_id: str,
    channel_name: str,
    report_text: str,
    order_json: Optional[Dict],
    motor_run_id: int,
    auth_run_id: int,
    pending_scripts_snapshot: Dict,
    total_scripts: int,
    channel_health: str,
    is_first: bool,
    run_number: int,
) -> Optional[int]:
    """Salva analise de ordenacao no banco de dados."""
    payload = {
        "channel_id": channel_id,
        "channel_name": channel_name,
        "report_text": report_text,
        "order_json": json.dumps(order_json, ensure_ascii=False) if order_json else None,
        "motor_run_id": motor_run_id,
        "auth_run_id": auth_run_id,
        "pending_scripts_snapshot": json.dumps(pending_scripts_snapshot, ensure_ascii=False),
        "total_scripts": total_scripts,
        "channel_health": channel_health,
        "is_first_analysis": is_first,
        "run_number": run_number,
    }

    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/production_order_runs",
        json=payload,
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }
    )

    if resp.status_code in (200, 201):
        rows = resp.json()
        run_id = rows[0].get("id") if rows else None
        logger.info(f"Ordenacao salva: run_id={run_id}, run_number={run_number}, {total_scripts} scripts")
        return run_id
    else:
        logger.error(f"Erro ao salvar ordenacao: {resp.status_code} - {resp.text[:300]}")
        return None


def delete_analysis(channel_id: str, run_id: int) -> Dict:
    """Deleta um run especifico de production_order_runs."""
    resp = requests.delete(
        f"{SUPABASE_URL}/rest/v1/production_order_runs",
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
        logger.info(f"Ordenacao run {run_id} deletado para {channel_id}")
        return {"success": True, "deleted_id": run_id}
    else:
        logger.error(f"Erro ao deletar ordenacao run {run_id}: {resp.status_code}")
        return {"success": False, "error": resp.text[:200]}


def get_latest_analysis(channel_id: str) -> Optional[Dict]:
    """Retorna a analise de ordenacao mais recente para o canal."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/production_order_runs",
        params={
            "channel_id": f"eq.{channel_id}",
            "select": "id,channel_id,channel_name,run_date,run_number,report_text,order_json,total_scripts,channel_health,is_first_analysis,motor_run_id,auth_run_id",
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
        if isinstance(row.get("order_json"), str):
            try:
                row["order_json"] = json.loads(row["order_json"])
            except (json.JSONDecodeError, TypeError):
                pass
        return row
    return None


def get_analysis_history(channel_id: str, limit: int = 20, offset: int = 0) -> Dict:
    """Retorna historico paginado de analises de ordenacao."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/production_order_runs",
        params={
            "channel_id": f"eq.{channel_id}",
            "select": "id,channel_id,channel_name,run_date,run_number,total_scripts,channel_health,is_first_analysis",
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
    Agente 7 (Ordenador de Producao) — orquestrador principal.

    Fluxo:
    1. Verifica Claude CLI (se nao disponivel, enfileira job)
    2. Carrega channel info (precisa copy_spreadsheet_id)
    3. Le scripts pendentes da planilha (status 'to do')
    4. Carrega Motor run (Agente 5) — OBRIGATORIO
    5. Carrega Auth run (Agente 3) — OBRIGATORIO
    6. Determina saude do canal
    7. Verifica incremental (hash dos scripts pendentes)
    8. Chama LLM ORDENADOR
    9. Salva em production_order_runs
    """
    logger.info(f"=== INICIO Agente 7 (Ordenador): {channel_id} ===")

    # 1. Verificar Claude CLI
    from claude_llm_client import is_claude_cli_available
    if not is_claude_cli_available():
        logger.info(f"Claude CLI nao disponivel — criando job na fila para {channel_id}")
        try:
            _create_agent_job(channel_id, "ordenador")
            return {
                "success": True,
                "queued": True,
                "message": "Analise de ordenacao enfileirada para processamento via Claude Opus 4.6",
            }
        except Exception as e:
            logger.error(f"Erro ao criar job: {e}")
            return {"success": False, "error": f"Falha ao enfileirar job: {e}"}

    # 2. Channel info
    channel_info = _get_channel_info(channel_id)
    if not channel_info:
        msg = f"Canal {channel_id} nao encontrado em yt_channels"
        logger.error(msg)
        return {"success": False, "error": msg}

    channel_name = channel_info.get("channel_name", "Desconhecido")
    copy_spreadsheet_id = channel_info.get("copy_spreadsheet_id")

    if not copy_spreadsheet_id:
        msg = f"Canal {channel_name} nao tem copy_spreadsheet_id configurado"
        logger.error(msg)
        return {"success": False, "error": msg}

    # 3. Ler scripts pendentes
    scripts = _read_pending_scripts(copy_spreadsheet_id)
    if not scripts:
        msg = f"Nenhum script pendente (status 'to do') encontrado na planilha de {channel_name}"
        logger.warning(msg)
        return {"success": False, "error": msg}

    logger.info(f"Agente 7: {channel_name} — {len(scripts)} scripts pendentes")

    # 4. Carregar Motor run (OBRIGATORIO)
    motor_run = _load_latest_motor_run(channel_id)
    if not motor_run:
        msg = (
            f"Nenhuma analise de motores encontrada para {channel_name}. "
            f"Rode o Agente de Motores (Agente 5) primeiro."
        )
        logger.error(msg)
        return {"success": False, "error": msg}

    # 5. Carregar Auth run (OBRIGATORIO)
    auth_run = _load_latest_auth_run(channel_id)
    if not auth_run:
        msg = (
            f"Nenhuma analise de autenticidade encontrada para {channel_name}. "
            f"Rode o Agente de Autenticidade (Agente 3) primeiro."
        )
        logger.error(msg)
        return {"success": False, "error": msg}

    # 6. Saude do canal
    health = _determine_channel_health(auth_run)
    logger.info(
        f"Agente 7: {channel_name} — saude={health['health_level']} "
        f"score={health['score']} risco={health['is_at_risk']}"
    )

    # 7. Incremental: verificar se scripts mudaram
    snapshot = _build_scripts_snapshot(scripts)
    prev_run = _get_previous_run(channel_id)

    is_first = prev_run is None
    run_number = 1 if is_first else (prev_run.get("run_number", 0) + 1)

    skip_llm = False
    if not is_first and prev_run:
        prev_snapshot = prev_run.get("pending_scripts_snapshot") or {}
        prev_hash = prev_snapshot.get("hash", "")
        if prev_hash == snapshot["hash"]:
            logger.info("Scripts pendentes identicos ao run anterior — skip LLM")
            skip_llm = True

    if skip_llm:
        prev_report = prev_run.get("report_text", "")
        prev_order = prev_run.get("order_json")
        if not prev_report:
            msg = f"Skip LLM ativo mas relatorio anterior vazio para {channel_id}"
            logger.error(msg)
            return {"success": False, "error": msg}

        banner = (
            f">> Run #{run_number} -- Scripts pendentes identicos ao run anterior. "
            f"Relatorio reutilizado. Proxima analise com scripts novos gerara atualizacao.\n\n"
        )
        report_text = banner + prev_report
        order_json = prev_order
    else:
        # 8. Chamar LLM
        previous_report = prev_run.get("report_text") if prev_run else None
        llm_result = _call_llm(
            scripts=scripts,
            motor_run=motor_run,
            auth_run=auth_run,
            health=health,
            channel_info=channel_info,
            is_first=is_first,
            run_number=run_number,
            previous_report=previous_report,
        )

        if not llm_result:
            msg = "LLM ORDENADOR nao retornou output"
            logger.error(msg)
            return {"success": False, "error": msg}

        order_json = llm_result.get("order_json")
        report_text = llm_result.get("report_text", "")

        if not order_json:
            logger.warning("LLM retornou report mas JSON nao foi parseado corretamente")

    # Injetar modelo usado no cabecalho (evitar duplicar se skip_llm reutilizou report anterior)
    _used_model = os.environ.get("CLAUDE_MODEL", "claude-opus-4-6") if is_claude_cli_available() else os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    model_header = f"Modelo LLM: {_used_model}\n"
    if not report_text.startswith("Modelo LLM:"):
        report_text = model_header + report_text

    # 9. Salvar
    run_id = save_analysis(
        channel_id=channel_id,
        channel_name=channel_name,
        report_text=report_text,
        order_json=order_json,
        motor_run_id=motor_run["id"],
        auth_run_id=auth_run["id"],
        pending_scripts_snapshot=snapshot,
        total_scripts=len(scripts),
        channel_health=health["health_level"],
        is_first=is_first,
        run_number=run_number,
    )

    if run_id is None:
        logger.warning(f"Agente 7: {channel_name} — analise ok mas save falhou!")

    logger.info(
        f"=== FIM Agente 7: {channel_name} | run #{run_number} | "
        f"{len(scripts)} scripts | saude={health['health_level']} | "
        f"run_id={run_id} ==="
    )

    return {
        "success": run_id is not None,
        "channel_name": channel_name,
        "run_id": run_id,
        "run_number": run_number,
        "total_scripts": len(scripts),
        "channel_health": health["health_level"],
        "is_first_analysis": is_first,
        "motor_run_id": motor_run["id"],
        "auth_run_id": auth_run["id"],
        "order_json": order_json,
        "report_text": report_text,
    }

"""
Agente Analista de Pre-Geracao — analisa historico do canal antes de gerar script.

Decide: tom, formato (livre/modelado), temas bloqueados, video de referencia.
Cada canal e 100% isolado — nunca cruza dados entre canais.
"""

import os
import json
import time
import random
import logging
from collections import Counter
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# Planilhas por subnicho (criadas em 2026-04-09)
SPREADSHEET_IDS = {
    "Culturas Macabras": "1xCVr2YDzXeWbCNaulDhhA5KLeQZO10ZTh_dmUXjPabk",
    "Frentes de Guerra": "184pcEIp8Ic2ue2yEvVkEbYmo2tcRNoBCf2bfvuXCvpk",
    "Guerras e Civilizações": "1DUAcTXPm1CWs4Rhb1lrUzAMMFPn4aNekiHssAf8Ketk",
    "Guerras e Civilizacoes": "1DUAcTXPm1CWs4Rhb1lrUzAMMFPn4aNekiHssAf8Ketk",
    "Historias Sombrias": "1-atfSoNBNzpeTMEv2FUft4Kj_siiw_3wGJgzVS792ZI",
    "Monetizados": "1qJwzWeC7vqO7N7on0zoNP3b8kPNcjs4PZwhtJxKxKso",
    "Reis Perversos": "13HyelxV1jyOw_vdb9L-wrOePRcC3p3BTd5_gHF15Qdk",
    "Relatos de Guerra": "11KBTZp3Z9kG0Id32qul5uOZc_zpFGNt_qtM8HFZfs5I",
}

# Service account pra Sheets API
SHORTS_SA_CREDS_PATH = r"C:\Users\PC\Downloads\service-account-492821-217e559c4710.json"

# 5 tons disponiveis
TONS = ["narrativo", "provocativo", "educativo", "suspense", "epico"]

# Colunas da planilha (0-indexed)
COL_DATA = 0       # A
COL_TOM = 1        # B
COL_TITULO = 2     # C
COL_DESCRICAO = 3  # D
COL_SCRIPT = 4     # E
COL_PROMPTS_IMG = 5 # F
COL_PROMPTS_ANIM = 6 # G
COL_FORMATO = 7    # H
COL_VIDEO_REF = 8  # I
COL_DRIVE_LINK = 9 # J
COL_UPLOAD = 10    # K

_sheets_service = None


def _sheets_execute(request, max_retries=2):
    """Executa request da Sheets API com retry em caso de rate limit (429)."""
    for attempt in range(max_retries):
        try:
            return request.execute()
        except HttpError as e:
            if e.resp.status == 429 and attempt < max_retries - 1:
                logger.warning(f"[analyst] Rate limit 429, aguardando 60s...")
                time.sleep(60)
            else:
                raise


def _get_sheets_service():
    """Retorna servico autenticado do Google Sheets.

    Ordem de tentativa:
      1. Env var SHORTS_SA_JSON (JSON inline — especifico pras planilhas de Shorts)
      2. Env var GOOGLE_SHEETS_CREDENTIALS_2 (JSON inline — mesmo SA usado pelo uploader)
      3. Arquivo em SHORTS_SA_CREDS_PATH (fallback legado)

    Se a SA nao tiver acesso a planilha, erro 403 vai aparecer no read/write — nesse
    caso compartilhar a planilha com o email da SA. Email vem impresso no log.
    """
    global _sheets_service
    if _sheets_service is not None:
        return _sheets_service

    creds_dict = None
    source = None

    # 1. SHORTS_SA_JSON (especifico)
    env_shorts = os.getenv("SHORTS_SA_JSON")
    if env_shorts:
        try:
            creds_dict = json.loads(env_shorts)
            source = "SHORTS_SA_JSON env"
        except Exception as e:
            logger.warning(f"[analyst] SHORTS_SA_JSON invalido: {e}")

    # 2. GOOGLE_SHEETS_CREDENTIALS_2 (compartilhado com uploader)
    if creds_dict is None:
        env_shared = os.getenv("GOOGLE_SHEETS_CREDENTIALS_2")
        if env_shared:
            try:
                creds_dict = json.loads(env_shared)
                source = "GOOGLE_SHEETS_CREDENTIALS_2 env"
            except Exception as e:
                logger.warning(f"[analyst] GOOGLE_SHEETS_CREDENTIALS_2 invalido: {e}")

    # 3. Arquivo legado
    if creds_dict is None:
        try:
            with open(SHORTS_SA_CREDS_PATH) as f:
                creds_dict = json.load(f)
            source = f"file {SHORTS_SA_CREDS_PATH}"
        except FileNotFoundError:
            raise RuntimeError(
                "Credenciais do Google Sheets nao encontradas. Configure uma destas: "
                "SHORTS_SA_JSON ou GOOGLE_SHEETS_CREDENTIALS_2 no .env, "
                f"ou coloque o arquivo em {SHORTS_SA_CREDS_PATH}"
            )

    logger.info(f"[analyst] Sheets auth via {source} (email={creds_dict.get('client_email','?')})")
    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    _sheets_service = build("sheets", "v4", credentials=creds)
    return _sheets_service


def _find_tab_name(subnicho: str, channel_name: str) -> str:
    """Monta o nome da aba no formato '(XX) channel_name'."""
    # Ler todas as abas e encontrar a que contem o channel_name
    sid = SPREADSHEET_IDS.get(subnicho)
    if not sid:
        raise ValueError(f"Subnicho '{subnicho}' nao tem planilha configurada")

    sheets = _get_sheets_service()
    ss = _sheets_execute(sheets.spreadsheets().get(spreadsheetId=sid))

    for s in ss["sheets"]:
        tab_title = s["properties"]["title"]
        # Tab format: "(XX) channel_name"
        if channel_name in tab_title:
            return tab_title

    # Fallback: match sem acentos
    import unicodedata
    channel_norm = unicodedata.normalize("NFD", channel_name).encode("ascii", "ignore").decode().lower()
    for s in ss["sheets"]:
        tab_title = s["properties"]["title"]
        tab_norm = unicodedata.normalize("NFD", tab_title).encode("ascii", "ignore").decode().lower()
        if channel_norm in tab_norm:
            return tab_title

    raise ValueError(f"Aba para '{channel_name}' nao encontrada na planilha de '{subnicho}'")


def _read_channel_tab(subnicho: str, channel_name: str) -> list[list]:
    """Le todas as linhas de dados (sem header) da aba do canal."""
    sid = SPREADSHEET_IDS.get(subnicho)
    tab_name = _find_tab_name(subnicho, channel_name)

    sheets = _get_sheets_service()
    result = _sheets_execute(sheets.spreadsheets().values().get(
        spreadsheetId=sid,
        range=f"'{tab_name}'!A2:K",  # Pula header
    ))

    return result.get("values", [])


def _get_next_tom(rows: list[list]) -> str:
    """Seleciona proximo tom com variacao maxima.

    Logica:
    - Conta frequencia de cada tom nos ultimos 10
    - Exclui o ultimo usado (nunca 2 iguais seguidos)
    - Dos restantes, pega o MENOS usado
    - Se empate, escolhe aleatorio
    """
    if not rows:
        return random.choice(TONS)

    # Extrair tons das ultimas 10 linhas
    recent_toms = []
    for row in rows[-10:]:
        if len(row) > COL_TOM and row[COL_TOM].strip():
            recent_toms.append(row[COL_TOM].strip().lower())

    if not recent_toms:
        return random.choice(TONS)

    # Ultimo tom (excluir)
    ultimo_tom = recent_toms[-1]

    # Contar frequencia
    freq = Counter(recent_toms)

    # Candidatos: todos exceto o ultimo
    candidatos = [t for t in TONS if t != ultimo_tom]

    # Pegar os menos usados
    min_count = min(freq.get(t, 0) for t in candidatos)
    menos_usados = [t for t in candidatos if freq.get(t, 0) == min_count]

    return random.choice(menos_usados)


def _extract_blocked_themes(rows: list[list], last_n: int = 10) -> str:
    """Extrai keywords dos ultimos N titulos via GPT-4 Mini.

    Uma unica call com todos os titulos juntos.
    Retorna string compacta: "Esparta, Nero, Vikings"
    """
    # Pegar ultimos N titulos
    titulos = []
    for row in rows[-last_n:]:
        if len(row) > COL_TITULO and row[COL_TITULO].strip():
            titulos.append(row[COL_TITULO].strip())

    if not titulos:
        return ""

    # Uma call no GPT-4 Mini pra extrair keywords de todos os titulos
    from openai import OpenAI
    from dotenv import load_dotenv
    load_dotenv()

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    titulos_text = "\n".join(f"- {t}" for t in titulos)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "Extraia 2-3 palavras-chave historicas de cada titulo (figuras, locais, civilizacoes, eventos, periodos). NAO inclua verbos, artigos, adjetivos genericos ou palavras como 'historia', 'verdade', 'segredo'. Retorne SOMENTE um JSON array de strings unicas, sem duplicatas. Ex: [\"Esparta\", \"Caligula\", \"Vikings\"]",
            },
            {
                "role": "user",
                "content": f"Titulos:\n{titulos_text}",
            },
        ],
        temperature=0.3,
        max_tokens=200,
    )

    raw = response.choices[0].message.content.strip()

    # Parse JSON
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    try:
        keywords = json.loads(raw)
        if isinstance(keywords, list):
            unique = list(dict.fromkeys(keywords))  # Preserva ordem, remove duplicatas
            result = ", ".join(unique)
            logger.info(f"[analyst] Keywords bloqueadas ({len(unique)}): {result[:100]}")
            return result
    except json.JSONDecodeError:
        logger.warning(f"[analyst] Falha ao parsear keywords: {raw[:100]}")

    return ""


def _should_be_modelado(rows: list[list]) -> bool:
    """Verifica se proximo short deve ser modelado.

    Logica: a cada 3 livres seguidos, o proximo e modelado.
    Ciclo: livre -> livre -> livre -> modelado -> livre -> livre -> livre -> modelado
    """
    if not rows:
        return False  # Primeiro short e sempre livre

    # Contar livres seguidos desde o ultimo modelado
    livres_seguidos = 0
    for row in reversed(rows):
        if len(row) > COL_FORMATO and row[COL_FORMATO].strip().lower() == "modelado":
            break
        livres_seguidos += 1

    return livres_seguidos >= 3


def _get_modelado_video(channel_name: str, used_refs: list[str]) -> dict | None:
    """Busca video com 3k+ views no Supabase pra usar como referencia.

    Prioriza SEMPRE os videos com mais views.
    Exclui videos ja usados como referencia (lidos da planilha).
    Retorna dict com titulo e views, ou None se nao tem disponivel.
    """
    from dotenv import load_dotenv
    load_dotenv()
    from supabase import create_client

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    sb = create_client(url, key)

    # Buscar canal_id em canais_monitorados
    canal_result = sb.table("canais_monitorados").select("id").eq(
        "nome_canal", channel_name
    ).execute()

    if not canal_result.data:
        # Tentar com TRIM
        canal_result = sb.table("canais_monitorados").select("id, nome_canal").eq(
            "tipo", "nosso"
        ).eq("status", "ativo").execute()

        canal_id = None
        for c in (canal_result.data or []):
            if c["nome_canal"].strip() == channel_name.strip():
                canal_id = c["id"]
                break

        if not canal_id:
            logger.warning(f"[analyst] Canal '{channel_name}' nao encontrado em canais_monitorados")
            return None
    else:
        canal_id = canal_result.data[0]["id"]

    # Buscar videos com 3k+ views, ordenados por views DESC
    videos = sb.table("videos_historico").select(
        "video_id, titulo, views_atuais, data_coleta"
    ).eq("canal_id", canal_id).gte(
        "views_atuais", 3000
    ).order("views_atuais", desc=True).limit(50).execute()

    if not videos.data:
        return None

    # Deduplificar por video_id (pegar coleta mais recente)
    seen = {}
    for v in videos.data:
        vid = v["video_id"]
        if vid not in seen or v.get("data_coleta", "") > seen[vid].get("data_coleta", ""):
            seen[vid] = v

    # Extrair titulos ja usados como referencia (da planilha)
    used_titles = set()
    for ref in used_refs:
        # Formato na planilha: "titulo (Xk views)" — extrair titulo
        if "(" in ref:
            used_titles.add(ref.rsplit("(", 1)[0].strip().lower())
        else:
            used_titles.add(ref.strip().lower())

    # Encontrar primeiro video nao usado (mais views primeiro)
    sorted_videos = sorted(seen.values(), key=lambda v: v.get("views_atuais", 0), reverse=True)

    for v in sorted_videos:
        titulo = v.get("titulo", "").strip()
        if titulo.lower() not in used_titles:
            views = v.get("views_atuais", 0)
            # Formatar views (93000 -> 93k, 5200 -> 5.2k)
            if views >= 1000:
                views_str = f"{views / 1000:.0f}k" if views >= 10000 else f"{views / 1000:.1f}k"
            else:
                views_str = str(views)

            return {
                "video_ref": f"{titulo} ({views_str} views)",
                "video_ref_titulo": titulo,
                "views": views,
            }

    return None  # Todos ja foram usados


def analyze_channel(channel_name: str, subnicho: str) -> dict:
    """Analisa historico do canal e retorna decisoes pra geracao.

    Args:
        channel_name: Nome exato do canal (ex: "Forja Imperial")
        subnicho: Subnicho do canal (ex: "Guerras e Civilizacoes")

    Returns:
        Dict com tom, formato, temas_bloqueados, video_ref, video_ref_titulo, total_shorts
    """
    logger.info(f"[analyst] Analisando: {channel_name} ({subnicho})")

    # 1. Ler planilha do canal
    try:
        rows = _read_channel_tab(subnicho, channel_name)
    except Exception as e:
        logger.error(f"[analyst] Erro ao ler planilha: {e}")
        rows = []

    total = len(rows)
    logger.info(f"[analyst] {channel_name}: {total} shorts na planilha")

    # 2. Proximo tom (variacao maxima)
    tom = _get_next_tom(rows)
    logger.info(f"[analyst] Tom selecionado: {tom}")

    # 3. Temas bloqueados (ultimos 10)
    temas_bloqueados = _extract_blocked_themes(rows, last_n=10)

    # 4. Formato (livre ou modelado)
    formato = "livre"
    video_ref = None
    video_ref_titulo = None

    if _should_be_modelado(rows):
        # Buscar videos usados como referencia na planilha
        used_refs = []
        for row in rows:
            if len(row) > COL_VIDEO_REF and row[COL_VIDEO_REF].strip():
                used_refs.append(row[COL_VIDEO_REF].strip())

        video = _get_modelado_video(channel_name, used_refs)
        if video:
            formato = "modelado"
            video_ref = video["video_ref"]
            video_ref_titulo = video["video_ref_titulo"]
            logger.info(f"[analyst] Modelado: {video_ref}")
        else:
            logger.info(f"[analyst] Sem videos 3k+ disponiveis, mantendo livre")

    logger.info(f"[analyst] Resultado: tom={tom}, formato={formato}")

    return {
        "tom": tom,
        "formato": formato,
        "temas_bloqueados": temas_bloqueados,
        "video_ref": video_ref,
        "video_ref_titulo": video_ref_titulo,
        "total_shorts_produzidos": total,
    }

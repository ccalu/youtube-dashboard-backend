"""
Perfis Endpoints — Centro de Controle dos Canais
Lê planilha Google Sheets e retorna dados processados com health score e alertas.
Planilha: 1XL6VhOTVVMmfGNqPyJra2T8KjfFbtJ1o16OZkytvCPc
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime, date
import logging
import time
import re

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/perfis", tags=["perfis"])

# ── Cache ──────────────────────────────────────────────────────────────
CACHE_TTL_SECONDS = 300  # 5 min fallback
_cache = {}  # {"pub": {"data": ..., "ts": ...}, "proxys": {...}, ...}

SPREADSHEET_ID = "1XL6VhOTVVMmfGNqPyJra2T8KjfFbtJ1o16OZkytvCPc"

# Subnichos nomenclatura
SUBNICHOS = {
    "C001": "Histórias Sombrias",
    "C002": "Guerras e Civilizações",
    "C003": "Relatos de Guerra",
    "C004": "Culturas Macabras",
    "C005": "Reis Perversos",
    "C006": "Terror",
    "C007": "Biografias",
    "C008": "Frentes de Batalha",
    "C009": "Mistérios",
    "C010": "Conspiração",
    "C011": "Lições de Vida",
    "C012": "(Indefinido)",
    "C013": "Registros Malditos",
    "C014": "(Indefinido)",
    "C015": "(Indefinido)",
}


def _get_subnicho(canal_name: str) -> tuple:
    """Extract subnicho code and name from canal name like 'C005 FRA (22)'."""
    match = re.match(r'(C\d{3})', canal_name)
    if match:
        code = match.group(1)
        return code, SUBNICHOS.get(code, "(Indefinido)")
    return "", ""


def _get_sheets_client():
    """Lazy gspread client — reuses existing pattern from sheets.py."""
    from _features.yt_uploader.sheets import get_sheets_client
    return get_sheets_client()


def _get_cached(key: str):
    """Return cached data if fresh, else None."""
    entry = _cache.get(key)
    if entry and (time.time() - entry["ts"]) < CACHE_TTL_SECONDS:
        return entry["data"]
    return None


def _set_cache(key: str, data):
    _cache[key] = {"data": data, "ts": time.time()}


def _parse_date(date_str: str) -> date | None:
    """Parse DD/MM/YYYY date string."""
    if not date_str or not date_str.strip():
        return None
    try:
        return datetime.strptime(date_str.strip(), "%d/%m/%Y").date()
    except ValueError:
        return None


def _parse_float(val: str) -> float:
    """Parse float from string, handling comma decimals."""
    if not val or not val.strip():
        return 0.0
    try:
        return float(val.strip().replace(",", "."))
    except ValueError:
        return 0.0


def _parse_int(val: str) -> int:
    if not val or not val.strip():
        return 0
    try:
        return int(val.strip())
    except ValueError:
        return 0


def _parse_scripts(scripts_str: str) -> tuple:
    """Parse 'done/total' format like '8/15'. Returns (done, total)."""
    if not scripts_str or "/" not in scripts_str:
        return 0, 0
    try:
        parts = scripts_str.strip().split("/")
        return int(parts[0]), int(parts[1])
    except (ValueError, IndexError):
        return 0, 0


def _calculate_health(programar: int, scripts_done: int, scripts_total: int,
                      last_pub_date: date | None, monetized: str,
                      config: str, prod: str, today: date) -> dict:
    """Calculate health score. Only meaningful for CONFIG=SIM and PROD=SIM."""
    if config.upper() != "SIM" or prod.upper() != "SIM":
        return {"overall": "gray", "scripts": "gray", "programar": "gray", "pub_status": "gray"}

    # Scripts health
    scripts_remaining = scripts_total - scripts_done
    if scripts_total > 0:
        if scripts_remaining < 3:
            scripts_health = "red"
        elif scripts_remaining < 5:
            scripts_health = "yellow"
        else:
            scripts_health = "green"
    else:
        scripts_health = "gray"

    # Programar health — different rules for desmonetizado
    is_desmon = "desmon" in monetized.lower()
    if programar <= 0:
        programar_health = "yellow" if is_desmon else "red"
    elif programar <= 2:
        programar_health = "yellow"
    else:
        programar_health = "green"

    # Pub status — based on ULT PUB vs today
    if last_pub_date is None:
        pub_health = "red"
    elif last_pub_date <= today:
        pub_health = "red" if not is_desmon else "yellow"
    elif (last_pub_date - today).days <= 1:
        pub_health = "yellow"
    else:
        pub_health = "green"

    # Overall = worst
    levels = {"red": 0, "yellow": 1, "green": 2, "gray": 3}
    worst = min([scripts_health, programar_health, pub_health], key=lambda x: levels.get(x, 3))

    return {
        "overall": worst,
        "scripts": scripts_health,
        "programar": programar_health,
        "pub_status": pub_health,
    }


def _generate_alerts(channels: list, today: date) -> list:
    """Generate alerts only for channels with CONFIG=SIM and PROD=SIM."""
    alerts = []
    for ch in channels:
        if ch.get("config", "").upper() != "SIM" or ch.get("prod", "").upper() != "SIM":
            continue
        if ch.get("inactive"):
            continue

        subnicho_code, subnicho_name = _get_subnicho(ch["name"])
        scripts_remaining = ch.get("scripts_total", 0) - ch.get("scripts_done", 0)
        last_pub = _parse_date(ch.get("last_pub", ""))

        # URGENTE: ULT PUB <= hoje
        if last_pub and last_pub <= today:
            alerts.append({
                "channel": ch["name"],
                "subnicho": subnicho_name,
                "type": "sem_programar",
                "severity": "red",
                "message": f"Última pub {ch['last_pub']} — {ch['programar']} disponíveis",
                "monetized": ch.get("monetized", ""),
            })
        elif last_pub is None and ch.get("config", "").upper() == "SIM":
            alerts.append({
                "channel": ch["name"],
                "subnicho": subnicho_name,
                "type": "nunca_publicou",
                "severity": "red",
                "message": "Config pronto",
                "monetized": ch.get("monetized", ""),
            })

        # URGENTE: scripts < 3
        if ch.get("scripts_total", 0) > 0 and scripts_remaining < 3:
            alerts.append({
                "channel": ch["name"],
                "subnicho": subnicho_name,
                "type": "scripts_critico",
                "severity": "red",
                "message": f"{scripts_remaining} restantes ({ch['scripts_done']}/{ch['scripts_total']})",
                "monetized": ch.get("monetized", ""),
            })
        # ATENÇÃO: scripts < 5
        elif ch.get("scripts_total", 0) > 0 and scripts_remaining < 5:
            alerts.append({
                "channel": ch["name"],
                "subnicho": subnicho_name,
                "type": "scripts_baixo",
                "severity": "yellow",
                "message": f"{scripts_remaining} restantes ({ch['scripts_done']}/{ch['scripts_total']})",
                "monetized": ch.get("monetized", ""),
            })

        # ATENÇÃO: ULT PUB = amanhã
        if last_pub and (last_pub - today).days == 1:
            alerts.append({
                "channel": ch["name"],
                "subnicho": subnicho_name,
                "type": "programar_amanha",
                "severity": "yellow",
                "message": f"Amanhã ({ch['last_pub']}) — {ch['programar']} disponíveis",
                "monetized": ch.get("monetized", ""),
            })

    # Sort: red first, then yellow
    alerts.sort(key=lambda a: 0 if a["severity"] == "red" else 1)
    return alerts


# ── PUB Endpoint ───────────────────────────────────────────────────────

@router.get("/pub")
async def get_perfis_pub():
    """Dados da aba PUB: summary + alerts + channels."""
    cached = _get_cached("pub")
    if cached:
        return cached

    try:
        gc = _get_sheets_client()
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        ws = spreadsheet.get_worksheet_by_id(1449741920)
        all_rows = ws.get_all_values()
    except Exception as e:
        logger.error(f"Erro ao ler planilha PUB: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao ler planilha: {str(e)}")

    # Header is row 5 (index 4), data starts at row 6 (index 5)
    # Columns: A=CANAL, B=ULT PUB, C=PERIODO, D=PUB, E=DONE, F=PROGRAMAR,
    #          G=THUMBS, H=COMEÇOU, I=FREQ, J=PROD, K=CONFIG, L=TRACKING,
    #          M=GENERATED, N=MONETIZADO, O=SCRIPTS, P=LINKS SCRIPTS,
    #          Q=LINKS THUMBS, R=PRIORIDADE, S=URL CANAL
    today = date.today()
    channels = []
    active_channels = []
    inactive_section = False

    # Parse summary from rows 1-2
    summary_row = all_rows[1] if len(all_rows) > 1 else []
    total_channels = _parse_int(summary_row[0]) if len(summary_row) > 0 else 0
    total_pub = _parse_int(summary_row[3]) if len(summary_row) > 3 else 0
    total_done = _parse_int(summary_row[4]) if len(summary_row) > 4 else 0

    for i, row in enumerate(all_rows[5:], start=6):
        # Skip empty rows / detect inactive section
        canal = row[0].strip() if len(row) > 0 else ""
        if not canal:
            if channels:  # We had data before, now empty = start of inactive section
                inactive_section = True
            continue

        last_pub_str = row[1].strip() if len(row) > 1 else ""
        pub_count = _parse_int(row[3]) if len(row) > 3 else 0
        done = _parse_int(row[4]) if len(row) > 4 else 0
        programar = _parse_int(row[5]) if len(row) > 5 else 0
        thumbs = _parse_int(row[6]) if len(row) > 6 else 0
        started = row[7].strip() if len(row) > 7 else ""
        freq = _parse_float(row[8]) if len(row) > 8 else 0.0
        prod = row[9].strip() if len(row) > 9 else ""
        config = row[10].strip() if len(row) > 10 else ""
        monetized = row[13].strip() if len(row) > 13 else ""
        scripts_str = row[14].strip() if len(row) > 14 else ""
        priority = row[17].strip() if len(row) > 17 else ""
        url = row[18].strip() if len(row) > 18 else ""

        scripts_done, scripts_total = _parse_scripts(scripts_str)
        last_pub_date = _parse_date(last_pub_str)
        started_date = _parse_date(started)
        days_active = (today - started_date).days if started_date else 0

        subnicho_code, subnicho_name = _get_subnicho(canal)

        health = _calculate_health(
            programar, scripts_done, scripts_total,
            last_pub_date, monetized, config, prod, today
        )

        ch = {
            "name": canal,
            "subnicho": subnicho_name,
            "last_pub": last_pub_str,
            "pub_count": pub_count,
            "done": done,
            "programar": programar,
            "thumbs": thumbs,
            "started": started,
            "days_active": days_active,
            "frequency": freq,
            "prod": prod,
            "config": config,
            "monetized": monetized,
            "scripts_done": scripts_done,
            "scripts_total": scripts_total,
            "scripts_remaining": scripts_total - scripts_done,
            "priority": priority,
            "url": url,
            "health": health["overall"],
            "health_factors": health,
            "inactive": inactive_section,
        }
        channels.append(ch)

        if not inactive_section:
            active_channels.append(ch)

    # Count stats (only active, CONFIG=SIM, PROD=SIM for alerts)
    eligible = [c for c in active_channels if c["config"].upper() == "SIM" and c["prod"].upper() == "SIM"]
    scripts_low = sum(1 for c in eligible if c["scripts_total"] > 0 and c["scripts_remaining"] < 5)
    zero_programar = sum(1 for c in eligible
                         if _parse_date(c["last_pub"]) is not None and _parse_date(c["last_pub"]) <= today
                         or (not c["last_pub"] and c["config"].upper() == "SIM"))

    alerts = _generate_alerts(active_channels, today)

    result = {
        "summary": {
            "total_channels": total_channels,
            "active_channels": len([c for c in active_channels if c["prod"].upper() == "SIM"]),
            "monetized": sum(1 for c in active_channels if c["monetized"].upper() in ("SIM", "ATIVA")),
            "desmonetized": sum(1 for c in active_channels if "desmon" in c["monetized"].lower()),
            "total_pub": total_pub,
            "total_done": total_done,
            "scripts_low_count": scripts_low,
            "zero_programar_count": zero_programar,
        },
        "alerts": alerts,
        "channels": channels,
        "cached_at": datetime.now().isoformat(),
    }

    _set_cache("pub", result)
    return result


# ── Proxys Endpoint ────────────────────────────────────────────────────

@router.get("/proxys")
async def get_perfis_proxys():
    """Dados da aba Gestão de Proxy."""
    cached = _get_cached("proxys")
    if cached:
        return cached

    try:
        gc = _get_sheets_client()
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        ws = spreadsheet.worksheet("GESTÃO DE PROXY")
        all_rows = ws.get_all_values()
    except Exception as e:
        logger.error(f"Erro ao ler planilha Proxys: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao ler planilha: {str(e)}")

    # Header: CONTA, @Usuário, E-mail, Senha, Idioma/Local, 2FA, Status,
    #         MONETIZAÇÃO, Criação, Links, authenticatorurl, Adsense,
    #         recoveryemail, Senha recovery, Códigos alternativos, Fornecedor
    channels = []
    for row in all_rows[1:]:  # Skip header
        conta = row[0].strip() if len(row) > 0 else ""
        if not conta:
            continue

        # Extract subnicho from conta code (e.g. "C001" → "Histórias Sombrias")
        code_match = re.match(r'(C\d{3})', conta)
        subnicho = SUBNICHOS.get(code_match.group(1), "") if code_match else ""

        channels.append({
            "conta": conta,
            "subnicho": subnicho,
            "subnicho_code": code_match.group(1) if code_match else "",
            "username": row[1].strip() if len(row) > 1 else "",
            "email": row[2].strip() if len(row) > 2 else "",
            "password": row[3].strip() if len(row) > 3 else "",
            "location": row[4].strip() if len(row) > 4 else "",
            "two_fa": row[5].strip() if len(row) > 5 else "",
            "status": row[6].strip() if len(row) > 6 else "",
            "monetization": row[7].strip() if len(row) > 7 else "",
            "created": row[8].strip() if len(row) > 8 else "",
            "link": row[9].strip() if len(row) > 9 else "",
            "adsense": row[11].strip() if len(row) > 11 else "",
            "recovery_email": row[12].strip() if len(row) > 12 else "",
            "supplier": row[15].strip() if len(row) > 15 else "",
        })

    # Sort by conta name (natural order: C001, C002, ...)
    channels.sort(key=lambda c: c["conta"])

    stats = {
        "total": len(channels),
        "active": sum(1 for c in channels if c["status"].upper() == "ATIVO"),
        "off": sum(1 for c in channels if c["status"].upper() == "OFF"),
    }

    result = {
        "channels": channels,
        "stats": stats,
        "cached_at": datetime.now().isoformat(),
    }

    _set_cache("proxys", result)
    return result


# ── Desmonetizados Endpoint ───────────────────────────────────────────

@router.get("/desmonetizados")
async def get_perfis_desmonetizados():
    """Dados da aba Desmonetizados."""
    cached = _get_cached("desmonetizados")
    if cached:
        return cached

    try:
        gc = _get_sheets_client()
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        ws = spreadsheet.worksheet("DESMONETIZADOS")
        all_rows = ws.get_all_values()
    except Exception as e:
        logger.error(f"Erro ao ler planilha Desmonetizados: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao ler planilha: {str(e)}")

    # Left side (cols A-F): CONTAS, NOME DO CANAL, DATA DESMONETZADO, DATA PEDIR, MOTIVO, STATUS
    # Right side (cols I-P): CONTAS, NOME DO CANAL, GMAIL NOVO, SENHA, DATA OWNER NOVO, DATA DA TROCA, STATUS, VIROU
    demonetizations = []
    transfers = []

    for row in all_rows[1:]:  # Skip header
        # Left side — demonetization history
        conta_left = row[0].strip() if len(row) > 0 else ""
        if conta_left:
            demonetizations.append({
                "conta": conta_left,
                "channel_name": row[1].strip() if len(row) > 1 else "",
                "date_demonetized": row[2].strip() if len(row) > 2 else "",
                "date_reapply": row[3].strip() if len(row) > 3 else "",
                "reason": row[4].strip() if len(row) > 4 else "",
                "status": row[5].strip() if len(row) > 5 else "",
            })

        # Right side — owner transfers (cols 8-15)
        conta_right = row[8].strip() if len(row) > 8 else ""
        if conta_right:
            transfers.append({
                "conta": conta_right,
                "channel_name": row[9].strip() if len(row) > 9 else "",
                "new_email": row[10].strip() if len(row) > 10 else "",
                "new_password": row[11].strip() if len(row) > 11 else "",
                "date_new_owner": row[12].strip() if len(row) > 12 else "",
                "date_transfer": row[13].strip() if len(row) > 13 else "",
                "status": row[14].strip() if len(row) > 14 else "",
                "became": row[15].strip() if len(row) > 15 else "",
            })

    # Stats
    reasons = {}
    for d in demonetizations:
        r = d["reason"]
        if r:
            reasons[r] = reasons.get(r, 0) + 1

    stats = {
        "total_demonetized": len(demonetizations),
        "reasons": reasons,
        "transfers_done": sum(1 for t in transfers if t["status"].lower() == "done"),
        "transfers_waiting": sum(1 for t in transfers if t["status"].lower() == "waiting"),
        "transfers_todo": sum(1 for t in transfers if t["status"].lower() == "to do"),
    }

    result = {
        "demonetizations": demonetizations,
        "transfers": transfers,
        "stats": stats,
        "cached_at": datetime.now().isoformat(),
    }

    _set_cache("desmonetizados", result)
    return result


# ── Adsense Endpoint ──────────────────────────────────────────────────

@router.get("/adsense")
async def get_perfis_adsense():
    """Dados da aba Adsense — SEM senha do Gmail."""
    cached = _get_cached("adsense")
    if cached:
        return cached

    try:
        gc = _get_sheets_client()
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        ws = spreadsheet.worksheet("ADSENSE")
        all_rows = ws.get_all_values()
    except Exception as e:
        logger.error(f"Erro ao ler planilha Adsense: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao ler planilha: {str(e)}")

    # Structure: blocks separated by empty rows
    # Each block: row with "ADSENSE", name — next rows: GMAIL, SENHA, CNPJ
    # Then linked channels: col C=conta, col D=nome, col E=data vinculo, col F=monetização
    accounts = []
    current_account = None

    for row in all_rows:
        col_b = row[1].strip() if len(row) > 1 else ""
        col_c = row[2].strip() if len(row) > 2 else ""

        # Detect new account block
        if col_b == "ADSENSE":
            if current_account:
                accounts.append(current_account)
            # Extract owner from parentheses: "CRIAS AI (LUCCA)" → "LUCCA"
            owner_match = re.search(r'\(([^)]+)\)', col_c)
            owner = owner_match.group(1).strip() if owner_match else ""
            current_account = {
                "name": col_c,
                "owner": owner,
                "email": "",
                "cnpj": "",
                "channels": [],
            }
            continue

        if current_account is None:
            continue

        # Parse account details
        if col_b == "GMAIL":
            current_account["email"] = col_c
        elif col_b == "CNPJ":
            current_account["cnpj"] = col_c
        elif col_b == "SENHA":
            pass  # Skip password intentionally

        # Parse linked channels (col C=conta, D=nome, E=data, F=monetização)
        conta = row[3].strip() if len(row) > 3 else ""
        if conta and conta != current_account.get("email", "") and not conta.startswith("CONTAS"):
            channel_name = row[4].strip() if len(row) > 4 else ""
            if channel_name and channel_name != "NOME DOS CANAIS":
                date_link = row[5].strip() if len(row) > 5 else ""
                monetization = row[6].strip() if len(row) > 6 else ""
                current_account["channels"].append({
                    "conta": conta,
                    "name": channel_name,
                    "date_linked": date_link,
                    "monetization": monetization,
                })

    if current_account:
        accounts.append(current_account)

    stats = {
        "total_accounts": len(accounts),
        "total_channels_linked": sum(len(a["channels"]) for a in accounts),
        "active_monetized": sum(
            1 for a in accounts for c in a["channels"]
            if c["monetization"].upper() in ("ATIVO", "ATIVA")
        ),
    }

    result = {
        "accounts": accounts,
        "stats": stats,
        "cached_at": datetime.now().isoformat(),
    }

    _set_cache("adsense", result)
    return result


# ── Alerts Count (lightweight for sidebar badge) ──────────────────────

@router.get("/alerts-count")
async def get_alerts_count():
    """Retorna apenas a contagem de alertas para o badge da sidebar."""
    # Try to use cached PUB data
    cached = _get_cached("pub")
    if cached:
        count = len([a for a in cached.get("alerts", []) if a["severity"] == "red"])
        return {"count": count}

    # If no cache, fetch PUB data (will cache it)
    try:
        pub_data = await get_perfis_pub()
        count = len([a for a in pub_data.get("alerts", []) if a["severity"] == "red"])
        return {"count": count}
    except Exception:
        return {"count": 0}


# ── Webhook (Google Apps Script) ──────────────────────────────────────

@router.post("/webhook")
async def perfis_webhook():
    """Webhook chamado pelo Google Apps Script onEdit. Limpa todo o cache."""
    _cache.clear()
    logger.info("Perfis cache cleared via webhook")
    return {"status": "ok", "message": "Cache cleared"}

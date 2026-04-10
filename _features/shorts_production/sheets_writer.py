"""
Sheets Writer — escreve producoes nas planilhas de shorts.

Usa SA nova (shorts-service) pra Sheets API.
Cada canal tem sua aba na planilha do respectivo subnicho.
"""

import logging
from datetime import datetime
from .analyst import _get_sheets_service, _find_tab_name, _sheets_execute, SPREADSHEET_IDS

logger = logging.getLogger(__name__)


def write_production_to_sheet(channel_name: str, subnicho: str, data: dict) -> int:
    """Escreve uma nova linha na aba do canal com os dados da producao.

    Args:
        channel_name: Nome do canal
        subnicho: Subnicho do canal
        data: Dict com campos da producao (tom, titulo, descricao, script,
              prompts_imagem, prompts_animacao, formato, video_ref)

    Returns:
        Numero da linha adicionada (1-indexed, incluindo header)
    """
    sid = SPREADSHEET_IDS.get(subnicho)
    if not sid:
        raise ValueError(f"Subnicho '{subnicho}' nao tem planilha configurada")

    tab_name = _find_tab_name(subnicho, channel_name)
    sheets = _get_sheets_service()

    # Montar linha: Data | Tom | Titulo | Descricao | Script | Prompts Imagem | Prompts Animacao | Formato | Video Ref | Link Drive | Upload
    row = [
        data.get("data", datetime.now().strftime("%Y-%m-%d")),
        data.get("tom", ""),
        data.get("titulo", ""),
        data.get("descricao", ""),
        data.get("script", ""),
        data.get("prompts_imagem", ""),   # 14 prompts separados por \n
        data.get("prompts_animacao", ""),  # 14 prompts separados por \n
        data.get("formato", "livre"),
        data.get("video_ref", ""),         # "titulo (Xk views)" ou vazio
        "",  # Link Drive (preenchido depois)
        "",  # Upload (preenchido depois)
    ]

    # Append row
    result = _sheets_execute(sheets.spreadsheets().values().append(
        spreadsheetId=sid,
        range=f"'{tab_name}'!A:K",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": [row]},
    ))

    # Extrair numero da linha adicionada
    updated_range = result.get("updates", {}).get("updatedRange", "")
    # Format: "'(PT) Forja Imperial'!A5:K5" -> row 5
    row_num = 0
    if updated_range:
        try:
            row_num = int(updated_range.rsplit(":", 1)[-1].lstrip("ABCDEFGHIJK"))
        except (ValueError, IndexError):
            pass

    try:
        logger.info(f"[sheets_writer] {channel_name}: linha {row_num} adicionada ({data.get('titulo', '')[:40]})")
    except UnicodeEncodeError:
        logger.info(f"[sheets_writer] {channel_name}: linha {row_num} adicionada")

    return row_num


def update_drive_link(channel_name: str, subnicho: str, row_num: int, link: str):
    """Preenche a coluna Link Drive (J) na linha especificada."""
    sid = SPREADSHEET_IDS.get(subnicho)
    if not sid:
        return

    tab_name = _find_tab_name(subnicho, channel_name)
    sheets = _get_sheets_service()

    _sheets_execute(sheets.spreadsheets().values().update(
        spreadsheetId=sid,
        range=f"'{tab_name}'!J{row_num}",
        valueInputOption="RAW",
        body={"values": [[link]]},
    ))

    logger.info(f"[sheets_writer] {channel_name}: Drive link na linha {row_num}")


def update_upload_status(channel_name: str, subnicho: str, row_num: int, status: str):
    """Preenche a coluna Upload (K) na linha especificada."""
    sid = SPREADSHEET_IDS.get(subnicho)
    if not sid:
        return

    tab_name = _find_tab_name(subnicho, channel_name)
    sheets = _get_sheets_service()

    _sheets_execute(sheets.spreadsheets().values().update(
        spreadsheetId=sid,
        range=f"'{tab_name}'!K{row_num}",
        valueInputOption="RAW",
        body={"values": [[status]]},
    ))

    logger.info(f"[sheets_writer] {channel_name}: Upload status '{status}' na linha {row_num}")

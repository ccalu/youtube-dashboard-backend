"""
Sheets Writer — escreve producoes nas planilhas de shorts.

Usa SA nova (shorts-service) pra Sheets API.
Cada canal tem sua aba na planilha do respectivo subnicho.
"""

import logging
from datetime import datetime
from .analyst import _get_sheets_service, _find_tab_name, _sheets_execute, SPREADSHEET_IDS

logger = logging.getLogger(__name__)


def _format_prompts(prompts_text: str) -> str:
    """Formata prompts com numeracao e linha em branco entre cada.

    Input:  "prompt1\nprompt2\nprompt3"
    Output: "1 - prompt1\n\n2 - prompt2\n\n3 - prompt3"
    """
    if not prompts_text or not prompts_text.strip():
        return prompts_text
    lines = [l.strip() for l in prompts_text.split("\n") if l.strip()]
    result = []
    for i, prompt in enumerate(lines):
        result.append(f"{i + 1} - {prompt}")
        result.append("")
    if result and result[-1] == "":
        result.pop()
    return "\n".join(result)


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
        data.get("data", datetime.now().strftime("%d/%m/%Y")),
        data.get("tom", ""),
        data.get("titulo", ""),
        data.get("descricao", ""),
        data.get("script", ""),
        _format_prompts(data.get("prompts_imagem", "")),
        _format_prompts(data.get("prompts_animacao", "")),
        data.get("formato", "Livre").capitalize(),
        data.get("video_ref", "") or "-",
        "",  # Link Drive (preenchido depois)
        "",  # Upload (preenchido depois)
    ]

    formato = data.get("formato", "livre").strip().lower()

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

    # Aplicar cor de fundo na coluna Formato (H = index 7)
    if row_num > 0:
        try:
            ss = _sheets_execute(sheets.spreadsheets().get(spreadsheetId=sid))
            target_sheet_id = None
            for s in ss["sheets"]:
                if s["properties"]["title"] == tab_name:
                    target_sheet_id = s["properties"]["sheetId"]
                    break

            if target_sheet_id is not None:
                if formato == "livre":
                    bg = {"red": 0.85, "green": 0.95, "blue": 0.85}  # Verde claro
                elif formato == "modelado":
                    bg = {"red": 0.85, "green": 0.9, "blue": 1.0}  # Azul claro
                else:
                    bg = None

                if bg:
                    _sheets_execute(sheets.spreadsheets().batchUpdate(
                        spreadsheetId=sid,
                        body={"requests": [{
                            "repeatCell": {
                                "range": {
                                    "sheetId": target_sheet_id,
                                    "startRowIndex": row_num - 1,
                                    "endRowIndex": row_num,
                                    "startColumnIndex": 7,
                                    "endColumnIndex": 8,
                                },
                                "cell": {"userEnteredFormat": {"backgroundColor": bg}},
                                "fields": "userEnteredFormat.backgroundColor",
                            }
                        }]},
                    ))
        except Exception as color_err:
            logger.warning(f"[sheets_writer] Erro ao colorir formato: {str(color_err)[:80]}")

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
        valueInputOption="USER_ENTERED",
        body={"values": [[f'=HIPERLINK("{link}", "LINK")' if link.startswith("http") else link]]},
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

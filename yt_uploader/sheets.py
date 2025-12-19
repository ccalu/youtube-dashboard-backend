"""
Integração com Google Sheets API
Atualiza coluna O (Upload) quando upload completa
"""

import gspread
from google.oauth2.service_account import Credentials
import os
import json
import logging

logger = logging.getLogger(__name__)

def get_sheets_client():
    """
    Cria cliente gspread autenticado via Service Account.
    Credenciais vêm da variável de ambiente GOOGLE_SHEETS_CREDENTIALS_2 (JSON).
    """
    # Tenta GOOGLE_SHEETS_CREDENTIALS_2 primeiro (upload YouTube)
    # Se não tiver, usa GOOGLE_SHEETS_CREDENTIALS (dashboard mineração - fallback)
    credentials_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS_2') or os.getenv('GOOGLE_SHEETS_CREDENTIALS')

    if not credentials_json:
        raise ValueError("Variável GOOGLE_SHEETS_CREDENTIALS_2 não configurada no Railway")

    # Parse JSON das credenciais
    credentials_dict = json.loads(credentials_json)

    # Escopos necessários
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    # Cria credentials do Service Account
    credentials = Credentials.from_service_account_info(
        credentials_dict,
        scopes=scopes
    )

    # Retorna client autenticado
    return gspread.authorize(credentials)


def update_upload_status_in_sheet(spreadsheet_id: str, row: int, status: str):
    """
    Atualiza coluna O (Upload) na planilha Google Sheets.

    Args:
        spreadsheet_id: ID da planilha (da URL)
        row: Número da linha (começa em 1, header é linha 1)
        status: Status a escrever (ex: "done", "❌ Erro")
    """
    try:
        logger.info(f"📝 Atualizando planilha - Row {row}: {status}")

        # Conecta ao Google Sheets
        client = get_sheets_client()

        # Abre a planilha
        spreadsheet = client.open_by_key(spreadsheet_id)

        # Abre a aba "Página 1"
        worksheet = spreadsheet.worksheet('Página 1')

        # Atualiza célula O{row} (coluna 15)
        worksheet.update_cell(row, 15, status)

        # Formata célula com fonte PRETA (para ficar visível)
        worksheet.format(f'O{row}', {
            "textFormat": {
                "foregroundColor": {
                    "red": 0.0,
                    "green": 0.0,
                    "blue": 0.0
                },
                "bold": False
            }
        })

        logger.info(f"✅ Planilha atualizada - Row {row}: {status}")

    except Exception as e:
        logger.error(f"❌ Erro ao atualizar planilha: {str(e)}")
        # Não levanta exceção - não queremos que erro de planilha falhe o upload
        # O upload já foi bem-sucedido, isso é só notificação

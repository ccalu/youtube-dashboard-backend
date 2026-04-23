"""
Google Drive Uploader — sobe pasta de produção pro Drive.

Usa Service Account com acesso ao Drive compartilhado.
Estrutura: SHORTS/ → {subnicho}/ → ({LANG}) {canal}/ → {titulo}/
"""

import os
import glob
import logging
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger(__name__)

PARENT_FOLDER_ID = "1_TiJ5NO_I-8E2_ocEiwWiJTXkl8NPWyb"


def _get_creds_json():
    """Carrega credenciais do .env (GOOGLE_SERVICE_ACCOUNT_JSON)."""
    import os
    from dotenv import load_dotenv
    load_dotenv()
    creds_str = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    if not creds_str:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON não encontrado no .env")
    import json
    return json.loads(creds_str)


def _get_service():
    """Retorna serviço autenticado do Google Drive."""
    creds = Credentials.from_service_account_info(
        _get_creds_json(), scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=creds)


def _escape_drive_query_value(s: str) -> str:
    """Escapa aspas simples e backslashes em valores da Drive API query string.

    Sem isso, nomes com ' (ex: This Soldier's Last, Iskender'in) quebram a query com 400.
    Ver: https://developers.google.com/drive/api/guides/ref-search-terms#string
    """
    return s.replace("\\", "\\\\").replace("'", "\\'")


def _find_folder(service, parent_id: str, name: str) -> str | None:
    """Encontra pasta pelo nome dentro de um parent. Retorna ID ou None."""
    safe_name = _escape_drive_query_value(name)
    results = service.files().list(
        q=f"'{parent_id}' in parents and name='{safe_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
        fields="files(id, name)",
    ).execute()
    files = results.get("files", [])
    return files[0]["id"] if files else None


def _create_folder(service, parent_id: str, name: str) -> str:
    """Cria pasta no Drive e retorna ID."""
    meta = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    folder = service.files().create(body=meta, fields="id", supportsAllDrives=True).execute()
    return folder["id"]


def _find_file(service, parent_id: str, name: str) -> str | None:
    """Encontra arquivo pelo nome dentro de um parent. Retorna ID ou None."""
    safe_name = _escape_drive_query_value(name)
    results = service.files().list(
        q=f"'{parent_id}' in parents and name='{safe_name}' and trashed=false",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
        fields="files(id, name)",
    ).execute()
    files = results.get("files", [])
    return files[0]["id"] if files else None


def _upload_file(service, parent_id: str, file_path: str):
    """Faz upload de um arquivo pro Drive. Se já existe, substitui."""
    name = os.path.basename(file_path)
    mime_types = {
        ".mp4": "video/mp4",
        ".mp3": "audio/mpeg",
        ".png": "image/png",
        ".json": "application/json",
        ".txt": "text/plain",
    }
    ext = os.path.splitext(name)[1].lower()
    mime = mime_types.get(ext, "application/octet-stream")
    media = MediaFileUpload(file_path, mimetype=mime, resumable=True)

    # Se já existe, atualiza (substitui)
    existing_id = _find_file(service, parent_id, name)
    if existing_id:
        service.files().update(
            fileId=existing_id, media_body=media, supportsAllDrives=True
        ).execute()
    else:
        meta = {"name": name, "parents": [parent_id]}
        service.files().create(
            body=meta, media_body=media, fields="id", supportsAllDrives=True
        ).execute()


def upload_to_drive(production_path: str, subnicho: str, canal: str, titulo: str, log_callback=None) -> str:
    """
    Faz upload da pasta de produção pro Google Drive.

    Estrutura no Drive: SHORTS/ → {subnicho}/ → {canal}/ → {titulo}/
    Sobe: video_final.mp4, producao.json, copy.txt, narracao.mp3

    Returns:
        URL da pasta no Drive
    """
    def log(msg):
        logger.info(msg)
        if log_callback:
            log_callback(msg)

    log(f"Drive: Iniciando upload para {subnicho}/{canal}/{titulo}")
    service = _get_service()

    # Encontrar pasta do subnicho
    subnicho_id = _find_folder(service, PARENT_FOLDER_ID, subnicho)
    if not subnicho_id:
        # Tentar sem acentos
        import unicodedata
        subnicho_clean = unicodedata.normalize("NFKD", subnicho).encode("ascii", "ignore").decode()
        subnicho_id = _find_folder(service, PARENT_FOLDER_ID, subnicho_clean)
    if not subnicho_id:
        subnicho_id = _create_folder(service, PARENT_FOLDER_ID, subnicho)
        log(f"Drive: Criada pasta {subnicho}")

    # Encontrar pasta do canal
    canal_id = _find_folder(service, subnicho_id, canal)
    if not canal_id:
        canal_id = _create_folder(service, subnicho_id, canal)
        log(f"Drive: Criada pasta {canal}")

    # Criar pasta do vídeo
    video_folder_id = _find_folder(service, canal_id, titulo)
    if not video_folder_id:
        video_folder_id = _create_folder(service, canal_id, titulo)
    log(f"Drive: Pasta do video criada")

    # Upload dos arquivos principais
    files_to_upload = []

    # video_final.mp4
    vf = os.path.join(production_path, "video_final.mp4")
    if os.path.exists(vf):
        files_to_upload.append(vf)

    # producao.json
    pj = os.path.join(production_path, "producao.json")
    if os.path.exists(pj):
        files_to_upload.append(pj)

    # copy.txt
    ct = os.path.join(production_path, "copy.txt")
    if os.path.exists(ct):
        files_to_upload.append(ct)

    # narracao.mp3
    nm = os.path.join(production_path, "narracao.mp3")
    if os.path.exists(nm):
        files_to_upload.append(nm)

    for f in files_to_upload:
        _upload_file(service, video_folder_id, f)
        log(f"Drive: {os.path.basename(f)} uploaded")

    drive_url = f"https://drive.google.com/drive/folders/{video_folder_id}"
    log(f"Drive: Upload completo! {drive_url}")
    return drive_url

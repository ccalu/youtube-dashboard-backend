import json
import os
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

load_dotenv()
CREDS_JSON = json.loads(os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "{}"))

PARENT_FOLDER_ID = "1_TiJ5NO_I-8E2_ocEiwWiJTXkl8NPWyb"

STRUCTURE = {
    "Culturas Macabras": [
        "(KO) 그림자의 왕국",
        "(FR) Chroniques Anciennes",
        "(JP) 古代の物語",
        "(PT) Sombras da Historia",
    ],
    "Frentes de Guerra": [
        "(ES) Batallas Silenciadas",
        "(EN) Forgotten Frontlines",
        "(IT) Fronti Dimenticati",
        "(PT) Cronicas da Guerra",
    ],
    "Guerras e Civilizacoes": [
        "(KO) 제국의 역사",
        "(ES) Base del Imperio",
        "(EN) Empire Odyssey",
        "(JP) 征服の歴史",
        "(PT) Forja Imperial",
    ],
    "Historias Sombrias": [
        "(DE) Verborgene Geschichten",
        "(FR) Contes Sinistres",
        "(PT) Reis Perversos",
    ],
    "Monetizados": [
        "(DE) WWII Erzahlungen",
        "(FR) Archives de Guerre",
        "(PT) Grandes Mansoes",
        "(RU) Шёпот Королей",
    ],
    "Reis Perversos": [
        "(DE) Dunkle Herrschaften",
        "(KO) 어둠의 왕국들",
        "(ES) Ecos de la Soberania",
        "(FR) Vestiges Royaux",
        "(EN) Whispers of Kings",
        "(IT) Segreti del Trono",
        "(JP) 王座の秘密",
        "(PL) Mroczne Krolestwa",
        "(PT) Cronicas da Coroa",
        "(TR) Tahtin Sirlari",
    ],
    "Relatos de Guerra": [
        "(KO) 전쟁의 목소리",
        "(ES) Ecos de la Guerra",
        "(EN) War Archive Files",
        "(IT) Voci di Guerra",
        "(JP) 戦争の記録庫",
        "(PT) Arquivos da WW2",
    ],
}

def main():
    creds = Credentials.from_service_account_info(CREDS_JSON, scopes=['https://www.googleapis.com/auth/drive'])
    service = build('drive', 'v3', credentials=creds)

    # First check access
    print("Verificando acesso a pasta mae...")
    try:
        results = service.files().list(
            q=f"'{PARENT_FOLDER_ID}' in parents and trashed=false",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            fields='files(id, name)'
        ).execute()
        existing = {f['name']: f['id'] for f in results.get('files', [])}
        print(f"  Acesso OK! {len(existing)} pastas existentes.")
    except Exception as e:
        print(f"  ERRO de acesso: {e}")
        return

    created_count = 0

    for subnicho, canais in STRUCTURE.items():
        # Create subnicho folder
        if subnicho in existing:
            subnicho_id = existing[subnicho]
            print(f"\n[JA EXISTE] {subnicho}")
        else:
            folder_meta = {
                'name': subnicho,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [PARENT_FOLDER_ID]
            }
            folder = service.files().create(body=folder_meta, fields='id', supportsAllDrives=True).execute()
            subnicho_id = folder['id']
            created_count += 1
            print(f"\n[CRIADO] {subnicho}")

        # List existing canal folders
        canal_results = service.files().list(
            q=f"'{subnicho_id}' in parents and trashed=false",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            fields='files(id, name)'
        ).execute()
        existing_canais = {f['name'] for f in canal_results.get('files', [])}

        # Create canal folders
        for canal in canais:
            if canal in existing_canais:
                print(f"  [JA EXISTE] {canal}")
            else:
                canal_meta = {
                    'name': canal,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [subnicho_id]
                }
                service.files().create(body=canal_meta, fields='id', supportsAllDrives=True).execute()
                created_count += 1
                print(f"  [CRIADO] {canal}")

    print(f"\nPronto! {created_count} pastas criadas.")

if __name__ == '__main__':
    main()

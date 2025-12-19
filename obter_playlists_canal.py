"""
Script Helper: Lista playlists de um canal para obter IDs
Útil para preencher default_playlist_id no cadastro de canal
"""

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os

# IMPORTANTE: Permite OAuth em localhost (desenvolvimento)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# ESCOPOS necessários
SCOPES = [
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/youtube.force-ssl'
]

print("\n" + "="*70)
print("🔍 OBTER PLAYLISTS DE UM CANAL")
print("="*70)
print("\n⚠️  Este script lista todas as playlists de um canal")
print("   para você copiar o ID e usar no cadastro.\n")

# PASSO 1: Credenciais OAuth
print("=" * 70)
print("CREDENCIAIS OAUTH:")
print("=" * 70 + "\n")

client_id = input("Client ID (do .env ou manual): ").strip()
client_secret = input("Client Secret (do .env ou manual): ").strip()

if not client_id or not client_secret:
    print("\n❌ ERRO: Client ID/Secret são obrigatórios!")
    exit(1)

# PASSO 2: Autorização
print("\n" + "="*70)
print("PASSO 1: AUTORIZAÇÃO OAUTH")
print("="*70 + "\n")

CLIENT_CONFIG = {
    "installed": {
        "client_id": client_id,
        "client_secret": client_secret,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost"]
    }
}

flow = InstalledAppFlow.from_client_config(
    CLIENT_CONFIG,
    scopes=SCOPES,
    redirect_uri='http://localhost'
)

auth_url, _ = flow.authorization_url(
    access_type='offline',
    prompt='consent'
)

print("📋 Copie esta URL e cole no navegador (AdsPower ou normal):\n")
print(auth_url)
print("\n" + "="*70)

callback_url = input("\nCole a URL de redirecionamento aqui: ").strip()

if not callback_url or 'code=' not in callback_url:
    print("\n❌ ERRO: URL inválida!")
    exit(1)

# PASSO 3: Obter Tokens
try:
    print("\n⏳ Autenticando...")
    flow.fetch_token(authorization_response=callback_url)
    credentials = flow.credentials

    # PASSO 4: Listar Playlists
    print("\n" + "="*70)
    print("PASSO 2: LISTAR PLAYLISTS")
    print("="*70 + "\n")

    youtube = build('youtube', 'v3', credentials=credentials)

    # Lista todas as playlists do canal autenticado
    playlists_response = youtube.playlists().list(
        part='id,snippet',
        mine=True,
        maxResults=50
    ).execute()

    if not playlists_response.get('items'):
        print("⚠️  Nenhuma playlist encontrada neste canal!\n")
        print("💡 Crie playlists no YouTube Studio primeiro:")
        print("   https://studio.youtube.com/playlists\n")
        exit(0)

    print(f"✅ Encontradas {len(playlists_response['items'])} playlists:\n")
    print("="*70)

    for idx, playlist in enumerate(playlists_response['items'], 1):
        playlist_id = playlist['id']
        title = playlist['snippet']['title']

        print(f"\n{idx}. {title}")
        print(f"   📋 ID: {playlist_id}")
        print(f"   🔗 URL: https://www.youtube.com/playlist?list={playlist_id}")

    print("\n" + "="*70)
    print("💡 COMO USAR:")
    print("="*70)
    print("\n1. Copie o ID da playlist desejada (PLxxxxxxx)")
    print("2. Execute: python cadastrar_canal_simples.py")
    print("3. Cole o ID quando pedir 'Playlist ID padrão'\n")
    print("✅ Vídeos serão automaticamente adicionados a essa playlist!\n")

except Exception as e:
    print(f"\n❌ ERRO: {str(e)}\n")
    import traceback
    traceback.print_exc()

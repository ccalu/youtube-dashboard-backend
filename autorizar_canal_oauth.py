"""
Script GENÉRICO de autorização OAuth para canais YouTube
Usa client_id/client_secret únicos (do .env ou input manual)
"""

from google_auth_oauthlib.flow import InstalledAppFlow
from supabase import create_client
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv

# IMPORTANTE: Permite OAuth em localhost (desenvolvimento)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Carrega variáveis de ambiente
load_dotenv()

# Configuração Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ESCOPOS CORRETOS para upload YouTube
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.force-ssl'
]

print("\n" + "="*70)
print("🔐 AUTORIZAÇÃO OAUTH - YouTube Upload System")
print("="*70)

# PASSO 0: Busca Client ID/Secret
print("\n📋 CLIENT CREDENTIALS:")
print("="*70)

client_id = os.getenv('YOUTUBE_OAUTH_CLIENT_ID')
client_secret = os.getenv('YOUTUBE_OAUTH_CLIENT_SECRET')

if client_id and client_secret:
    print(f"✅ Usando credentials do .env")
    print(f"   Client ID: {client_id[:40]}...")
else:
    print("⚠️  Credentials não encontradas no .env")
    print("   Digite manualmente:\n")
    client_id = input("Client ID: ").strip()
    client_secret = input("Client Secret: ").strip()

if not client_id or not client_secret:
    print("\n❌ ERRO: Client ID/Secret são obrigatórios!")
    exit(1)

# PASSO 1: Channel ID
print("\n" + "="*70)
print("📌 DADOS DO CANAL:")
print("="*70)
channel_id = input("\nChannel ID (UCxxxxxxxxx): ").strip()

if not channel_id or not channel_id.startswith('UC'):
    print("\n❌ ERRO: Channel ID inválido!")
    exit(1)

# PASSO 2: Gera URL
print("\n" + "="*70)
print("PASSO 1: GERAR URL DE AUTORIZAÇÃO")
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
    prompt='consent'  # Força re-consentimento
)

print("📋 Copie esta URL e cole no navegador (AdsPower ou normal):\n")
print(auth_url)
print("\n" + "="*70)

# PASSO 3: Aguarda callback
print("PASSO 2: AUTORIZAR NO NAVEGADOR")
print("="*70)
print("\n⚠️  IMPORTANTE: Verifique se aparecem AMBAS as permissões:")
print("   ✅ Upload videos to YouTube")
print("   ✅ Manage your YouTube account")
print("\n1. Cole a URL acima no navegador")
print("2. Autorize com a conta YouTube do canal")
print("3. Copie a URL de redirecionamento completa\n")

callback_url = input("Cole a URL de redirecionamento aqui: ").strip()

if not callback_url or 'code=' not in callback_url:
    print("\n❌ ERRO: URL inválida!")
    exit(1)

# PASSO 4: Processa tokens
print("\n" + "="*70)
print("PASSO 3: PROCESSAR TOKENS")
print("="*70 + "\n")

try:
    print("⏳ Trocando código OAuth por tokens...")
    flow.fetch_token(authorization_response=callback_url)
    credentials = flow.credentials

    # Calcula data de expiração (UTC)
    if credentials.expiry:
        token_expiry = credentials.expiry.isoformat()
    else:
        token_expiry = (datetime.now(timezone.utc) + timedelta(seconds=3600)).isoformat()

    print("✅ Tokens obtidos com sucesso!")
    print(f"   Access Token: {credentials.token[:40]}...")
    print(f"   Refresh Token: {credentials.refresh_token[:40]}...")
    print(f"   Expiry: {token_expiry}\n")

    # Verifica se canal já existe
    existing = supabase.table('yt_oauth_tokens')\
        .select('*')\
        .eq('channel_id', channel_id)\
        .execute()

    # Salva no Supabase
    print("⏳ Salvando tokens no Supabase...")

    data = {
        'channel_id': channel_id,
        'access_token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_expiry': token_expiry
    }

    if existing.data:
        # Update
        result = supabase.table('yt_oauth_tokens')\
            .update(data)\
            .eq('channel_id', channel_id)\
            .execute()
        print("✅ Tokens ATUALIZADOS no banco!")
    else:
        # Insert
        result = supabase.table('yt_oauth_tokens')\
            .insert(data)\
            .execute()
        print("✅ Tokens SALVOS no banco!")

    print("\n" + "="*70)
    print("🎉 AUTORIZAÇÃO CONCLUÍDA COM SUCESSO!")
    print("="*70)
    print(f"\n✅ Canal: {channel_id}")
    print(f"✅ Tokens: PERMANENTES (production mode)")
    print(f"✅ Status: PRONTO PARA UPLOAD!\n")
    print("📌 Próximo passo: Cadastrar canal (cadastrar_canal_simples.py)")
    print("   ou testar upload diretamente!\n")

except Exception as e:
    print(f"\n❌ ERRO AO PROCESSAR: {str(e)}\n")
    import traceback
    traceback.print_exc()

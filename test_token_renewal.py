"""
Testa renovação de token OAuth para identificar o problema
"""
import os
from dotenv import load_dotenv
from supabase import create_client
from monetization_oauth_collector import (
    get_tokens,
    get_proxy_credentials,
    refresh_access_token
)

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

print("=" * 80)
print("TESTE DE RENOVACAO DE TOKEN")
print("=" * 80)

# Pegar primeiro canal para testar
result = supabase.table("yt_channels")\
    .select("channel_id, channel_name, proxy_name")\
    .eq("is_monetized", True)\
    .limit(1)\
    .execute()

if not result.data:
    print("Nenhum canal encontrado!")
    exit(1)

channel = result.data[0]
channel_id = channel['channel_id']
channel_name = channel['channel_name']
proxy_name = channel.get('proxy_name', 'C000.1')

print(f"\nCanal: {channel_name}")
print(f"Channel ID: {channel_id}")
print(f"Proxy: {proxy_name}")

# Buscar token
print("\n[1] Buscando token OAuth...")
token_data = get_tokens(channel_id)
if not token_data:
    print("  [ERRO] Nenhum token encontrado!")
    exit(1)

refresh_token = token_data.get('refresh_token')
print(f"  Refresh token: {refresh_token[:40]}...")

# Buscar credenciais do proxy
print("\n[2] Buscando credenciais do proxy...")
proxy_creds = get_proxy_credentials(proxy_name)
if not proxy_creds:
    print(f"  [ERRO] Credenciais do proxy {proxy_name} nao encontradas!")
    exit(1)

client_id = proxy_creds['client_id']
client_secret = proxy_creds['client_secret']

print(f"  Client ID: {client_id[:40]}...")
print(f"  Client Secret: {client_secret[:20]}...")

# Tentar renovar token
print("\n[3] Tentando renovar token...")
try:
    new_token_data = refresh_access_token(refresh_token, client_id, client_secret)

    if not new_token_data:
        print("  [ERRO] refresh_access_token retornou None")
    elif 'error' in new_token_data:
        print(f"  [ERRO] OAuth error: {new_token_data.get('error')}")
        print(f"  Description: {new_token_data.get('error_description', 'N/A')}")
    elif 'access_token' not in new_token_data:
        print(f"  [ERRO] Resposta sem access_token: {new_token_data}")
    else:
        print("  [OK] Token renovado com sucesso!")
        print(f"  Access token: {new_token_data['access_token'][:40]}...")

except Exception as e:
    print(f"  [ERRO] Excecao: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)

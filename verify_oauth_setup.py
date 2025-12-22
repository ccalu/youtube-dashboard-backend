"""
Verifica setup completo de OAuth tokens no Supabase
"""
import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

print("=" * 80)
print("VERIFICAÇÃO DE OAUTH TOKENS - PRODUCTION")
print("=" * 80)

# 1. Verificar yt_proxy_credentials
print("\n[1] PROXY CREDENTIALS (Production)")
print("-" * 80)
result = supabase.table("yt_proxy_credentials").select("*").execute()
proxies = result.data

print(f"Total de proxies configurados: {len(proxies)}\n")
for proxy in proxies:
    print(f"Proxy: {proxy['proxy_name']}")
    print(f"  Client ID: {proxy['client_id'][:20]}...")
    print(f"  Client Secret: {proxy['client_secret'][:20]}...")
    print()

# 2. Verificar yt_oauth_tokens
print("\n[2] OAUTH TOKENS")
print("-" * 80)
result = supabase.table("yt_oauth_tokens").select("*").execute()
tokens = result.data

print(f"Total de canais com tokens: {len(tokens)}\n")
for token in tokens:
    # Buscar nome do canal
    channel_result = supabase.table("yt_channels")\
        .select("channel_name, proxy_name")\
        .eq("channel_id", token['channel_id'])\
        .execute()

    channel_name = "???"
    proxy_name = "???"
    if channel_result.data:
        channel_name = channel_result.data[0].get('channel_name', '???')
        proxy_name = channel_result.data[0].get('proxy_name', '???')

    print(f"Canal: {channel_name}")
    print(f"  Channel ID: {token['channel_id']}")
    print(f"  Proxy: {proxy_name}")
    print(f"  Access Token: {token.get('access_token', 'N/A')[:30]}...")
    print(f"  Refresh Token: {token.get('refresh_token', 'N/A')[:30]}...")

    # Verificar data de atualização
    updated_at = token.get('updated_at', 'N/A')
    if updated_at != 'N/A':
        try:
            updated_dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            print(f"  Última atualização: {updated_dt.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        except:
            print(f"  Última atualização: {updated_at}")

    print()

# 3. Verificar canais monetizados
print("\n[3] CANAIS MONETIZADOS")
print("-" * 80)
result = supabase.table("yt_channels")\
    .select("channel_id, channel_name, proxy_name")\
    .eq("is_monetized", True)\
    .execute()

monetized = result.data
print(f"Total de canais monetizados: {len(monetized)}\n")

# Verificar se todos têm tokens
for channel in monetized:
    has_token = any(t['channel_id'] == channel['channel_id'] for t in tokens)
    status = "[OK]" if has_token else "[FALTA]"
    print(f"{status} {channel['channel_name']} (Proxy: {channel.get('proxy_name', 'N/A')})")

# 4. Verificar match entre proxies e canais
print("\n[4] VALIDACAO DE ASSOCIACOES")
print("-" * 80)

proxy_names = {p['proxy_name'] for p in proxies}
print(f"Proxies disponíveis: {', '.join(sorted(proxy_names))}\n")

for channel in monetized:
    proxy = channel.get('proxy_name', 'N/A')
    if proxy in proxy_names:
        print(f"[OK] {channel['channel_name']} -> Proxy {proxy}")
    else:
        print(f"[ERRO] {channel['channel_name']} -> Proxy {proxy} (PROXY NAO ENCONTRADO!)")

print("\n" + "=" * 80)
print("VERIFICAÇÃO COMPLETA")
print("=" * 80)

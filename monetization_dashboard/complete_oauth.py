"""
Completa o processo OAuth com o codigo fornecido
"""
import requests
import json
from config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    SUPABASE_URL,
    SUPABASE_KEY
)

# Codigo de autorizacao obtido do redirect
AUTH_CODE = "4/0ATX87lOcp4tMenP8G98wOIRjdkiFfEwJmtXuM-PGNyJFow9P6JMadxf2WutIEo6p6OAeeg"
PROXY_NAME = "C000.1 - PT - 03 - 04 - 05 - 06"  # Nome do proxy/perfil

def exchange_code_for_tokens(auth_code):
    """Troca o codigo de autorizacao por tokens."""
    print("[1] Trocando codigo por tokens...")

    token_url = "https://oauth2.googleapis.com/token"

    data = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "code": auth_code,
        "grant_type": "authorization_code",
        "redirect_uri": "http://localhost"
    }

    response = requests.post(token_url, data=data)

    if response.status_code != 200:
        print(f"    ERRO: {response.status_code}")
        print(f"    {response.text}")
        return None

    tokens = response.json()
    print(f"    OK Access Token: {tokens.get('access_token', 'N/A')[:40]}...")
    print(f"    OK Refresh Token: {tokens.get('refresh_token', 'N/A')[:40]}...")

    return tokens

def get_channel_info(access_token):
    """Obtem informacoes do canal."""
    print("\n[2] Obtendo info do canal...")

    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {"part": "snippet,statistics", "mine": "true"}
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(url, params=params, headers=headers)

    if response.status_code != 200:
        print(f"    ERRO: {response.status_code}")
        print(f"    {response.text}")
        return None

    data = response.json()

    if data.get("items"):
        channel = data["items"][0]
        info = {
            "channel_id": channel["id"],
            "channel_name": channel["snippet"]["title"],
            "subscribers": channel["statistics"].get("subscriberCount", 0)
        }
        print(f"    OK Canal: {info['channel_name']}")
        print(f"    OK ID: {info['channel_id']}")
        print(f"    OK Inscritos: {info['subscribers']}")
        return info

    return None

def save_to_supabase(channel_info, tokens, proxy_name):
    """Salva no Supabase."""
    print("\n[3] Salvando no Supabase...")

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    # 1. Salvar/atualizar canal
    channel_data = {
        "channel_id": channel_info["channel_id"],
        "channel_name": channel_info["channel_name"],
        "proxy_name": proxy_name,
        "is_monetized": True
    }

    # Usar upsert via POST com header especial
    headers_upsert = headers.copy()
    headers_upsert["Prefer"] = "resolution=merge-duplicates"

    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/yt_channels",
        headers=headers_upsert,
        json=channel_data
    )

    print(f"    Canal: {response.status_code} - {'OK' if response.status_code in [200, 201] else response.text[:100]}")

    # 2. Salvar/atualizar tokens
    token_data = {
        "channel_id": channel_info["channel_id"],
        "access_token": tokens.get("access_token"),
        "refresh_token": tokens.get("refresh_token")
    }

    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/yt_oauth_tokens",
        headers=headers_upsert,
        json=token_data
    )

    print(f"    Tokens: {response.status_code} - {'OK' if response.status_code in [200, 201] else response.text[:100]}")

    return True

def test_analytics_api(access_token, channel_id):
    """Testa se conseguimos acessar a API de Analytics."""
    print("\n[4] Testando YouTube Analytics API...")

    url = "https://youtubeanalytics.googleapis.com/v2/reports"

    params = {
        "ids": f"channel=={channel_id}",
        "startDate": "2025-01-01",
        "endDate": "2025-12-07",
        "metrics": "estimatedRevenue,views,estimatedMinutesWatched",
        "dimensions": "month"
    }

    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(url, params=params, headers=headers)

    if response.status_code == 200:
        data = response.json()
        print(f"    OK API funcionando!")
        if data.get("rows"):
            print(f"    Dados encontrados: {len(data['rows'])} registros")
            for row in data["rows"][:3]:
                print(f"      {row}")
        return True
    else:
        print(f"    ERRO: {response.status_code}")
        print(f"    {response.text[:200]}")
        return False

def main():
    print("=" * 60)
    print("COMPLETANDO OAUTH")
    print("=" * 60)

    # 1. Trocar codigo por tokens
    tokens = exchange_code_for_tokens(AUTH_CODE)
    if not tokens:
        return

    # 2. Obter info do canal
    channel_info = get_channel_info(tokens["access_token"])
    if not channel_info:
        return

    # 3. Salvar no Supabase
    save_to_supabase(channel_info, tokens, PROXY_NAME)

    # 4. Testar API de Analytics
    test_analytics_api(tokens["access_token"], channel_info["channel_id"])

    print("\n" + "=" * 60)
    print("CONCLUIDO!")
    print("=" * 60)

if __name__ == "__main__":
    main()

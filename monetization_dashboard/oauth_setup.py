"""
Script para fazer OAuth e obter refresh_token
Executar uma vez por canal, dentro do AdsPower (proxy)
"""
import requests
import json
from urllib.parse import urlencode, parse_qs, urlparse
from config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    YOUTUBE_SCOPES,
    SUPABASE_URL,
    SUPABASE_KEY
)

def generate_auth_url():
    """Gera a URL de autorizacao OAuth."""
    base_url = "https://accounts.google.com/o/oauth2/auth"

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": "http://localhost",
        "response_type": "code",
        "scope": " ".join(YOUTUBE_SCOPES),
        "access_type": "offline",  # Importante para obter refresh_token
        "prompt": "consent"  # Forca mostrar tela de consentimento
    }

    return f"{base_url}?{urlencode(params)}"

def exchange_code_for_tokens(auth_code):
    """Troca o codigo de autorizacao por tokens."""
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
        print(f"ERRO: {response.status_code}")
        print(response.text)
        return None

    return response.json()

def get_channel_info(access_token):
    """Obtem informacoes do canal usando o access_token."""
    url = "https://www.googleapis.com/youtube/v3/channels"

    params = {
        "part": "snippet,statistics",
        "mine": "true"
    }

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, params=params, headers=headers)

    if response.status_code != 200:
        print(f"ERRO ao obter canal: {response.status_code}")
        print(response.text)
        return None

    data = response.json()

    if data.get("items"):
        channel = data["items"][0]
        return {
            "channel_id": channel["id"],
            "channel_name": channel["snippet"]["title"],
            "subscribers": channel["statistics"].get("subscriberCount", 0)
        }

    return None

def save_to_supabase(channel_info, tokens, proxy_name=""):
    """Salva o canal e tokens no Supabase."""
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

    # 1. Salvar canal
    channel_data = {
        "channel_id": channel_info["channel_id"],
        "channel_name": channel_info["channel_name"],
        "proxy_name": proxy_name,
        "is_monetized": True
    }

    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/yt_channels",
        headers=headers,
        json=channel_data
    )

    if response.status_code not in [200, 201, 204]:
        # Pode ser que o canal ja existe, tentar update
        if "duplicate" in response.text.lower():
            print(f"    Canal ja existe, atualizando...")
            response = requests.patch(
                f"{SUPABASE_URL}/rest/v1/yt_channels?channel_id=eq.{channel_info['channel_id']}",
                headers=headers,
                json=channel_data
            )

    print(f"    Canal salvo: {channel_info['channel_name']}")

    # 2. Salvar tokens
    token_data = {
        "channel_id": channel_info["channel_id"],
        "access_token": tokens.get("access_token"),
        "refresh_token": tokens.get("refresh_token"),
    }

    # Tentar insert, se falhar fazer update
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/yt_oauth_tokens",
        headers=headers,
        json=token_data
    )

    if response.status_code not in [200, 201, 204]:
        if "duplicate" in response.text.lower():
            print(f"    Token ja existe, atualizando...")
            response = requests.patch(
                f"{SUPABASE_URL}/rest/v1/yt_oauth_tokens?channel_id=eq.{channel_info['channel_id']}",
                headers=headers,
                json=token_data
            )

    print(f"    Tokens salvos!")

    return True

def main():
    print("=" * 60)
    print("SETUP OAUTH - YouTube Analytics")
    print("=" * 60)

    # 1. Gerar URL
    print("\n[PASSO 1] URL de Autorizacao gerada:")
    print("-" * 60)
    auth_url = generate_auth_url()
    print(auth_url)
    print("-" * 60)

    print("\n[PASSO 2] Instrucoes:")
    print("  1. Copie a URL acima")
    print("  2. Abra no navegador DENTRO DO ADSPOWER (proxy)")
    print("  3. Faca login com a conta do Google do canal")
    print("  4. Autorize o aplicativo")
    print("  5. Voce sera redirecionado para localhost (vai dar erro, normal)")
    print("  6. Copie a URL completa da barra de endereco")
    print("     (Ex: http://localhost/?code=4/0ATx3L...)")

    print("\n[PASSO 3] Cole a URL completa aqui:")
    redirect_url = input("> ").strip()

    # Extrair o codigo da URL
    try:
        parsed = urlparse(redirect_url)
        code = parse_qs(parsed.query).get("code", [None])[0]

        if not code:
            print("ERRO: Codigo nao encontrado na URL!")
            return

        print(f"\n    Codigo extraido: {code[:20]}...")
    except Exception as e:
        print(f"ERRO ao extrair codigo: {e}")
        return

    # 4. Trocar codigo por tokens
    print("\n[PASSO 4] Trocando codigo por tokens...")
    tokens = exchange_code_for_tokens(code)

    if not tokens:
        print("ERRO: Falha ao obter tokens!")
        return

    print(f"    Access Token: {tokens.get('access_token', 'N/A')[:30]}...")
    print(f"    Refresh Token: {tokens.get('refresh_token', 'N/A')[:30]}...")

    if not tokens.get("refresh_token"):
        print("\n    AVISO: refresh_token nao retornado!")
        print("    Isso pode acontecer se voce ja autorizou antes.")
        print("    Tente revogar o acesso em: https://myaccount.google.com/permissions")
        return

    # 5. Obter info do canal
    print("\n[PASSO 5] Obtendo informacoes do canal...")
    channel_info = get_channel_info(tokens["access_token"])

    if not channel_info:
        print("ERRO: Falha ao obter info do canal!")
        return

    print(f"    Canal: {channel_info['channel_name']}")
    print(f"    ID: {channel_info['channel_id']}")
    print(f"    Inscritos: {channel_info['subscribers']}")

    # 6. Perguntar nome do proxy
    print("\n[PASSO 6] Qual o nome/ID do proxy deste canal?")
    print("    (Ex: C000.1 - PT ou proxy_1)")
    proxy_name = input("> ").strip()

    # 7. Salvar no Supabase
    print("\n[PASSO 7] Salvando no Supabase...")
    save_to_supabase(channel_info, tokens, proxy_name)

    print("\n" + "=" * 60)
    print("SETUP CONCLUIDO COM SUCESSO!")
    print("=" * 60)
    print(f"\nCanal '{channel_info['channel_name']}' configurado.")
    print("Agora voce pode executar o script de coleta.")

if __name__ == "__main__":
    main()

"""
OAuth rapido - troca codigo e salva tokens
"""
import requests
import sys
from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, SUPABASE_URL, SUPABASE_KEY

def main():
    if len(sys.argv) < 2:
        print("Uso: python quick_oauth.py <URL_COMPLETA_DO_REDIRECT>")
        print("Ex: python quick_oauth.py 'http://localhost/?code=4/0ATX87...'")
        return

    # Extrair codigo da URL
    url = sys.argv[1]
    if "code=" not in url:
        print("ERRO: URL nao contem codigo")
        return

    code = url.split("code=")[1].split("&")[0]
    print(f"[1] Codigo: {code[:30]}...")

    # Trocar por tokens
    print("[2] Trocando por tokens...")
    resp = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": "http://localhost"
    })

    if resp.status_code != 200:
        print(f"ERRO: {resp.status_code} - {resp.text}")
        return

    tokens = resp.json()
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")

    print(f"    Access: {access_token[:40]}...")
    print(f"    Refresh: {refresh_token[:40] if refresh_token else 'NAO RETORNADO'}...")

    if not refresh_token:
        print("\nAVISO: Refresh token nao retornado!")
        print("Va em https://myaccount.google.com/permissions")
        print("Remova o acesso do app 'dash' e tente novamente.")
        return

    # Obter info do canal
    print("[3] Obtendo info do canal...")
    resp = requests.get(
        "https://www.googleapis.com/youtube/v3/channels",
        params={"part": "snippet", "mine": "true"},
        headers={"Authorization": f"Bearer {access_token}"}
    )

    if resp.status_code != 200:
        print(f"ERRO ao obter canal: {resp.text}")
        return

    data = resp.json()
    if not data.get("items"):
        print("ERRO: Nenhum canal encontrado")
        return

    channel = data["items"][0]
    channel_id = channel["id"]
    channel_name = channel["snippet"]["title"]
    print(f"    Canal: {channel_name} ({channel_id})")

    # Salvar no Supabase
    print("[4] Salvando no Supabase...")
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }

    # Salvar canal
    requests.post(f"{SUPABASE_URL}/rest/v1/yt_channels", headers=headers, json={
        "channel_id": channel_id,
        "channel_name": channel_name,
        "proxy_name": "C000.1",
        "is_monetized": True
    })
    print("    Canal salvo!")

    # Salvar tokens
    requests.post(f"{SUPABASE_URL}/rest/v1/yt_oauth_tokens", headers=headers, json={
        "channel_id": channel_id,
        "refresh_token": refresh_token,
        "access_token": access_token
    })
    print("    Tokens salvos!")

    # Testar API Analytics
    print("[5] Testando API de Analytics...")
    resp = requests.get(
        "https://youtubeanalytics.googleapis.com/v2/reports",
        params={
            "ids": f"channel=={channel_id}",
            "startDate": "2025-11-01",
            "endDate": "2025-12-07",
            "metrics": "estimatedRevenue,views"
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )

    if resp.status_code == 200:
        data = resp.json()
        print(f"    OK! Colunas: {data.get('columnHeaders', [])}")
        if data.get("rows"):
            print(f"    Dados: {data['rows']}")
    else:
        print(f"    Erro: {resp.status_code} - {resp.text[:100]}")

    print("\n" + "=" * 50)
    print("CONCLUIDO!")
    print("=" * 50)

if __name__ == "__main__":
    main()

"""
OAuth v3 - salva tokens completos em arquivo
"""
import requests
import sys
import json
from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, SUPABASE_URL, SUPABASE_KEY

def main():
    if len(sys.argv) < 2:
        print("Uso: python oauth_v3.py <URL_COMPLETA>")
        return

    url = sys.argv[1]
    code = url.split("code=")[1].split("&")[0]
    print(f"Codigo: {code[:40]}...")

    # Trocar por tokens
    print("\nTrocando por tokens...")
    resp = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": "http://localhost"
    })

    if resp.status_code != 200:
        print(f"ERRO: {resp.text}")
        return

    tokens = resp.json()

    # Salvar tokens completos em arquivo
    with open("tokens_temp.json", "w") as f:
        json.dump(tokens, f, indent=2)
    print("Tokens salvos em tokens_temp.json")

    access_token = tokens["access_token"]
    refresh_token = tokens.get("refresh_token", "")

    print(f"\nAccess Token completo salvo!")
    print(f"Refresh Token: {'SIM' if refresh_token else 'NAO'}")

    # Listar canais (incluindo brand accounts)
    print("\nListando canais...")

    # Primeiro tentar mine=true
    resp = requests.get(
        "https://www.googleapis.com/youtube/v3/channels",
        params={"part": "snippet,statistics", "mine": "true"},
        headers={"Authorization": f"Bearer {access_token}"}
    )

    data = resp.json()
    items = data.get("items", [])

    if not items:
        # Tentar managedByMe
        print("Nenhum canal com mine=true, tentando managedByMe...")
        resp = requests.get(
            "https://www.googleapis.com/youtube/v3/channels",
            params={"part": "snippet,statistics", "managedByMe": "true"},
            headers={"Authorization": f"Bearer {access_token}"}
        )
        data = resp.json()
        items = data.get("items", [])

    if items:
        print(f"\nCanais encontrados: {len(items)}")
        for i, ch in enumerate(items):
            print(f"  [{i}] {ch['snippet']['title']}")
            print(f"      ID: {ch['id']}")
            print(f"      Inscritos: {ch['statistics'].get('subscriberCount', 'N/A')}")

        # Usar o primeiro canal
        channel = items[0]
        channel_id = channel["id"]
        channel_name = channel["snippet"]["title"]

        # Salvar no Supabase
        print(f"\nSalvando '{channel_name}' no Supabase...")
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"
        }

        # Canal
        resp = requests.post(f"{SUPABASE_URL}/rest/v1/yt_channels", headers=headers, json={
            "channel_id": channel_id,
            "channel_name": channel_name,
            "proxy_name": "C000.1",
            "is_monetized": True
        })
        print(f"  Canal: {resp.status_code}")

        # Tokens
        resp = requests.post(f"{SUPABASE_URL}/rest/v1/yt_oauth_tokens", headers=headers, json={
            "channel_id": channel_id,
            "refresh_token": refresh_token,
            "access_token": access_token
        })
        print(f"  Tokens: {resp.status_code}")

        # Testar Analytics
        print("\nTestando YouTube Analytics API...")
        resp = requests.get(
            "https://youtubeanalytics.googleapis.com/v2/reports",
            params={
                "ids": f"channel=={channel_id}",
                "startDate": "2025-11-01",
                "endDate": "2025-12-08",
                "metrics": "estimatedRevenue,views",
                "dimensions": "day"
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if resp.status_code == 200:
            analytics = resp.json()
            rows = analytics.get("rows", [])
            print(f"  OK! {len(rows)} dias de dados")
            if rows:
                total_revenue = sum(r[1] for r in rows if len(r) > 1)
                total_views = sum(r[2] for r in rows if len(r) > 2)
                print(f"  Receita total: ${total_revenue:.2f}")
                print(f"  Views total: {total_views:,}")
        else:
            print(f"  Erro Analytics: {resp.status_code} - {resp.text[:100]}")

        print("\n" + "=" * 50)
        print("SUCESSO!")
        print("=" * 50)
    else:
        print("\nNenhum canal encontrado!")
        print("Resposta da API:")
        print(json.dumps(data, indent=2)[:500])

if __name__ == "__main__":
    main()

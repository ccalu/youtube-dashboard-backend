"""
Lista todos os canais acessiveis (incluindo Brand Accounts)
"""
import requests

ACCESS_TOKEN = "ya29.a0Aa7pCA91HuOuTBExZEmlIYWPEIub_OsZ-"

# Tentar obter o token completo do arquivo de log ou da execucao anterior
# Por enquanto vamos tentar trocar de novo

from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET

# Codigo mais recente
CODE = "4/0ATX87lOOsxMZoAkd6rHOcH-QX1qI2dvVT2IdXhneO7H1jRg54bE-KF9YIntscZNc_63R1A"

print("[1] Obtendo tokens frescos...")
resp = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id": GOOGLE_CLIENT_ID,
    "client_secret": GOOGLE_CLIENT_SECRET,
    "code": CODE,
    "grant_type": "authorization_code",
    "redirect_uri": "http://localhost"
})

if resp.status_code != 200:
    print(f"Codigo expirado ou ja usado. Erro: {resp.text}")
    print("\nUsando metodo alternativo - listando com managedByMe...")

    # Se o codigo expirou, precisamos de um novo
    # Mas vamos tentar com o access token que ja temos

# Listar canais com diferentes parametros
print("\n[2] Listando canais disponiveis...")

# Tentar diferentes abordagens
endpoints = [
    ("mine=true", {"part": "snippet,contentDetails", "mine": "true"}),
    ("managedByMe=true", {"part": "snippet,contentDetails", "managedByMe": "true"}),
]

# Precisamos de um access token valido
# Vamos usar o refresh token para obter um novo

REFRESH_TOKEN = "1//0hQXhMj-0aia8CgYIARAAGBESNwF-L9Irec7z"

print("[3] Usando refresh token para obter novo access token...")
resp = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id": GOOGLE_CLIENT_ID,
    "client_secret": GOOGLE_CLIENT_SECRET,
    "refresh_token": REFRESH_TOKEN,
    "grant_type": "refresh_token"
})

if resp.status_code == 200:
    access_token = resp.json().get("access_token")
    print(f"    Novo access token: {access_token[:40]}...")
else:
    print(f"    Erro: {resp.text}")
    access_token = None

if access_token:
    headers = {"Authorization": f"Bearer {access_token}"}

    for name, params in endpoints:
        print(f"\n[4] Tentando {name}...")
        resp = requests.get(
            "https://www.googleapis.com/youtube/v3/channels",
            params=params,
            headers=headers
        )
        print(f"    Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("items", [])
            print(f"    Canais encontrados: {len(items)}")
            for ch in items:
                print(f"      - {ch['snippet']['title']} (ID: {ch['id']})")
        else:
            print(f"    Erro: {resp.text[:100]}")

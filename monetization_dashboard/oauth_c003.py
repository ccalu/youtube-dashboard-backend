"""
OAuth para proxy C003.1 - Batallas Silenciadas
"""
import urllib.parse

# Credenciais do projeto C003.1
CLIENT_ID = "25176202444-fd0qtr7ilojlj68u9vi66pksbln3a8bf.apps.googleusercontent.com"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/yt-analytics-monetary.readonly"
]

params = {
    "client_id": CLIENT_ID,
    "redirect_uri": "http://localhost",
    "response_type": "code",
    "scope": " ".join(SCOPES),
    "access_type": "offline",
    "prompt": "select_account consent"
}

url = "https://accounts.google.com/o/oauth2/auth?" + urllib.parse.urlencode(params)

print("=" * 70)
print("PROXY C003.1 - OAuth URL")
print("=" * 70)
print()
print("1. Abre essa URL no AdsPower (proxy C003.1)")
print("2. Seleciona a Brand Account (Batallas Silenciadas)")
print("3. Autoriza")
print("4. Copia a URL de retorno")
print()
print("=" * 70)
print("URL:")
print("=" * 70)
print()
print(url)
print()

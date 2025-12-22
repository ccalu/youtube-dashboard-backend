"""
OAuth para proxy C005.1
"""
import urllib.parse

CLIENT_ID = "789163340864-nrslnssccpfr07ogcgt9pao3e254r8nn.apps.googleusercontent.com"

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
print("PROXY C005.1 - OAuth URL")
print("=" * 70)
print()
print("Canais: ContesSinistres, RelatosOscurosYTV")
print()
print("1. Abre essa URL no AdsPower (proxy C005.1)")
print("2. Seleciona a Brand Account do canal")
print("3. Autoriza")
print("4. Copia a URL de retorno")
print()
print("URL:")
print()
print(url)
print()

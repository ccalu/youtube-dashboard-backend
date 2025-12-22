"""
OAuth para Brand Account - forca a escolha de conta
"""
import urllib.parse

CLIENT_ID = "624181268142-srjb1vjbcd0ticg2fm42sdic9lm3g7cq.apps.googleusercontent.com"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/yt-analytics-monetary.readonly"
]

# URL com prompt=select_account para forcar escolha de conta
params = {
    "client_id": CLIENT_ID,
    "redirect_uri": "http://localhost",
    "response_type": "code",
    "scope": " ".join(SCOPES),
    "access_type": "offline",
    "prompt": "select_account consent"  # FORCA escolha de conta + consent
}

url = "https://accounts.google.com/o/oauth2/auth?" + urllib.parse.urlencode(params)

print("=" * 70)
print("INSTRUCOES:")
print("=" * 70)
print()
print("1. Copie a URL abaixo")
print("2. Abra no navegador DENTRO DO ADSPOWER (proxy)")
print("3. IMPORTANTE: Quando aparecer a lista de contas,")
print("   ESCOLHA A BRAND ACCOUNT (ex: 'Reis Perversos'), NAO o Gmail!")
print("4. Autorize o app")
print("5. Copie a URL de retorno (vai dar erro, mas copie a URL)")
print("6. Cole a URL completa aqui")
print()
print("=" * 70)
print("URL DE AUTORIZACAO:")
print("=" * 70)
print()
print(url)
print()
print("=" * 70)

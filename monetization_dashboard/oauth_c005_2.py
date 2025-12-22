"""
OAuth para proxy C005.2
"""
import urllib.parse

CLIENT_ID = "386900656782-rtt61lt7g03ull7djpfsr9p8c5s6cml3.apps.googleusercontent.com"

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
print("PROXY C005.2 - OAuth URL")
print("=" * 70)
print()
print("Canal: Verborgene Geschichten")
print()
print("URL:")
print()
print(url)
print()

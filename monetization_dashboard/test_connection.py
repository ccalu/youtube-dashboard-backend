"""
Teste de conexao: Playwright -> AdsPower -> YouTube Studio
"""
from playwright.sync_api import sync_playwright
import requests
import json

ADSPOWER_API = "http://local.adspower.net:50325"
PROFILE_ID = "k12njsue"  # C000.1 - PT - 03 - 04 - 05 - 06

def get_websocket_url(profile_id: str) -> str:
    """Obtem a URL do WebSocket do perfil ativo."""
    response = requests.get(f"{ADSPOWER_API}/api/v1/browser/active?user_id={profile_id}")
    data = response.json()

    if data["code"] != 0:
        raise Exception(f"Perfil nao esta ativo: {data['msg']}")

    return data["data"]["ws"]["puppeteer"]

def test_connection():
    """Testa conexao com o browser do AdsPower."""
    print("=" * 60)
    print("TESTE DE CONEXAO: Playwright -> AdsPower -> YouTube Studio")
    print("=" * 60)

    # 1. Obter WebSocket URL
    print("\n[1] Obtendo WebSocket URL...")
    ws_url = get_websocket_url(PROFILE_ID)
    print(f"    OK WebSocket: {ws_url[:50]}...")

    # 2. Conectar via Playwright
    print("\n[2] Conectando via Playwright...")
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(ws_url)
        print(f"    OK Conectado! Browser version: {browser.version}")

        # 3. Listar contextos e paginas
        contexts = browser.contexts
        print(f"\n[3] Contextos encontrados: {len(contexts)}")

        for i, ctx in enumerate(contexts):
            pages = ctx.pages
            print(f"    Contexto {i}: {len(pages)} pagina(s)")

            for j, page in enumerate(pages):
                print(f"      Pagina {j}: {page.url[:60]}...")

        # 4. Pegar a primeira pagina ativa
        if contexts and contexts[0].pages:
            page = contexts[0].pages[0]
            title = page.title()
            print(f"\n[4] Pagina ativa:")
            print(f"    Titulo: {title}")
            print(f"    URL: {page.url}")

            # 5. Testar execucao de JavaScript
            print("\n[5] Testando execucao de JavaScript...")
            result = page.evaluate("() => { return { url: window.location.href, logged: !!window.ytcfg } }")
            print(f"    OK JavaScript executado!")
            print(f"    URL (via JS): {result['url'][:50]}...")
            print(f"    ytcfg presente: {result['logged']}")

        # Desconectar (nao fecha o browser)
        browser.disconnect()
        print("\n[6] Desconectado do browser (browser continua aberto)")

    print("\n" + "=" * 60)
    print("TESTE CONCLUIDO COM SUCESSO!")
    print("=" * 60)

if __name__ == "__main__":
    test_connection()

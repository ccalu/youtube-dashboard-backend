"""
Teste de extracao de dados de monetizacao do YouTube Studio
"""
from playwright.sync_api import sync_playwright
import requests
import json
import time

ADSPOWER_API = "http://local.adspower.net:50325"
PROFILE_ID = "k12njsue"  # C000.1 - PT - 03 - 04 - 05 - 06

def get_websocket_url(profile_id: str) -> str:
    """Obtem a URL do WebSocket do perfil ativo."""
    response = requests.get(f"{ADSPOWER_API}/api/v1/browser/active?user_id={profile_id}")
    data = response.json()
    if data["code"] != 0:
        raise Exception(f"Perfil nao esta ativo: {data['msg']}")
    return data["data"]["ws"]["puppeteer"]

def find_youtube_studio_page(contexts):
    """Encontra a pagina do YouTube Studio entre as abas abertas."""
    for ctx in contexts:
        for page in ctx.pages:
            if "studio.youtube.com" in page.url:
                return page
    return None

def test_extract_revenue():
    """Testa extracao de dados de monetizacao."""
    print("=" * 60)
    print("TESTE DE EXTRACAO: Dados de Monetizacao do YouTube Studio")
    print("=" * 60)

    # 1. Conectar ao browser
    print("\n[1] Conectando ao AdsPower...")
    ws_url = get_websocket_url(PROFILE_ID)

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(ws_url)
        print(f"    OK Conectado!")

        # 2. Encontrar pagina do YouTube Studio
        print("\n[2] Procurando pagina do YouTube Studio...")
        page = find_youtube_studio_page(browser.contexts)

        if not page:
            print("    ERRO: YouTube Studio nao esta aberto!")
            print("    Abra o YouTube Studio no browser do AdsPower primeiro.")
            return

        print(f"    OK Encontrado: {page.url[:60]}...")

        # 3. Navegar para Analytics Revenue
        print("\n[3] Navegando para Analytics > Revenue...")

        # Extrair channel_id da URL atual
        current_url = page.url
        if "/channel/" in current_url:
            channel_id = current_url.split("/channel/")[1].split("/")[0]
            print(f"    Channel ID: {channel_id}")
        else:
            channel_id = "UCmKCNZU8XSWg-bfVrg3JZCg"  # Fallback

        revenue_url = f"https://studio.youtube.com/channel/{channel_id}/analytics/tab-earn_revenue/period-default"
        page.goto(revenue_url, wait_until="domcontentloaded", timeout=60000)
        print(f"    OK Pagina de Revenue carregada!")

        # Esperar um pouco para os dados carregarem via JS
        print("    Aguardando dados async...")
        time.sleep(5)

        # 4. Aguardar carregamento
        print("\n[4] Aguardando dados carregarem...")
        time.sleep(3)

        # 5. Verificar se ytcfg existe (indica que esta logado)
        print("\n[5] Verificando sessao...")
        has_session = page.evaluate("() => !!window.ytcfg")
        print(f"    Sessao ativa (ytcfg): {has_session}")

        if not has_session:
            print("    ERRO: Nao esta logado no YouTube Studio!")
            return

        # 6. Tentar extrair dados visiveis da pagina
        print("\n[6] Extraindo dados visiveis da pagina...")

        visible_data = page.evaluate("""() => {
            const result = {
                title: document.title,
                url: window.location.href,
                metrics: []
            };

            // Tentar pegar elementos com valores de receita
            // YouTube Studio usa varios seletores diferentes
            const selectors = [
                '[class*="revenue"]',
                '[class*="metric"]',
                '[class*="analytics"]',
                'ytcp-analytics-metric-card',
                '.metric-value',
                '.data-value'
            ];

            // Pegar todo texto que parece valor monetario ($)
            const allText = document.body.innerText;
            const moneyMatches = allText.match(/\\$[\\d,]+\\.?\\d*/g) || [];
            result.moneyValues = [...new Set(moneyMatches)].slice(0, 10);

            // Pegar o contexto do YouTube
            if (window.ytcfg) {
                result.channelId = window.ytcfg.get('CHANNEL_ID') || 'N/A';
                result.clientVersion = window.ytcfg.get('INNERTUBE_CLIENT_VERSION') || 'N/A';
            }

            return result;
        }""")

        print(f"    Titulo: {visible_data.get('title', 'N/A')}")
        print(f"    Channel ID: {visible_data.get('channelId', 'N/A')}")
        print(f"    Client Version: {visible_data.get('clientVersion', 'N/A')}")
        print(f"    Valores monetarios encontrados: {visible_data.get('moneyValues', [])}")

        # 7. Tentar API interna youtubei
        print("\n[7] Testando API interna youtubei...")

        api_result = page.evaluate("""async () => {
            try {
                // Pegar contexto de autenticacao da pagina
                const ctx = window.ytcfg ? window.ytcfg.get("INNERTUBE_CONTEXT") : null;

                if (!ctx) {
                    return { error: "INNERTUBE_CONTEXT nao encontrado" };
                }

                // Tentar endpoint de analytics
                const response = await fetch("/youtubei/v1/analytics_data/join?prettyPrint=false", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        "context": ctx,
                        "browseId": "FEanalytics_revenue"
                    })
                });

                if (!response.ok) {
                    return {
                        error: `HTTP ${response.status}`,
                        statusText: response.statusText
                    };
                }

                const data = await response.json();
                return {
                    success: true,
                    hasData: !!data,
                    keys: Object.keys(data || {}).slice(0, 10)
                };
            } catch (e) {
                return { error: e.toString() };
            }
        }""")

        print(f"    Resultado API: {json.dumps(api_result, indent=2)}")

        # 8. Screenshot para debug
        print("\n[8] Salvando screenshot para debug...")
        screenshot_path = "C:/Users/User-OEM/Desktop/content-factory/monetization_dashboard/debug_revenue.png"
        page.screenshot(path=screenshot_path)
        print(f"    OK Salvo em: {screenshot_path}")

    print("\n" + "=" * 60)
    print("TESTE CONCLUIDO!")
    print("=" * 60)

if __name__ == "__main__":
    test_extract_revenue()

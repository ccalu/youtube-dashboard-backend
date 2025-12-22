"""
Teste de extracao de dados - v2
Usa a pagina que ja esta aberta, sem navegacao
"""
from playwright.sync_api import sync_playwright
import requests
import json
import time

ADSPOWER_API = "http://local.adspower.net:50325"
PROFILE_ID = "k12njsue"

def get_websocket_url(profile_id: str) -> str:
    response = requests.get(f"{ADSPOWER_API}/api/v1/browser/active?user_id={profile_id}")
    data = response.json()
    if data["code"] != 0:
        raise Exception(f"Perfil nao esta ativo: {data['msg']}")
    return data["data"]["ws"]["puppeteer"]

def find_youtube_studio_page(contexts):
    for ctx in contexts:
        for page in ctx.pages:
            if "studio.youtube.com" in page.url:
                return page
    return None

def test_extract():
    print("=" * 60)
    print("TESTE v2: Extrair dados da pagina atual")
    print("=" * 60)

    ws_url = get_websocket_url(PROFILE_ID)

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(ws_url)
        print("[1] Conectado ao browser!")

        # Encontrar pagina do YouTube Studio
        page = find_youtube_studio_page(browser.contexts)

        if not page:
            print("ERRO: Abra o YouTube Studio no AdsPower primeiro!")
            return

        print(f"[2] Pagina encontrada: {page.url[:50]}...")

        # Extrair dados da pagina atual (sem navegar)
        print("[3] Extraindo dados da pagina atual...")

        data = page.evaluate("""() => {
            const result = {
                url: window.location.href,
                title: document.title,
                channelId: null,
                revenue: null,
                ytcfgPresent: false,
                innertubeContext: null
            };

            // Verificar ytcfg
            if (window.ytcfg) {
                result.ytcfgPresent = true;
                result.channelId = window.ytcfg.get('CHANNEL_ID');

                // Pegar INNERTUBE_CONTEXT para usar em requisicoes
                const ctx = window.ytcfg.get('INNERTUBE_CONTEXT');
                if (ctx) {
                    result.innertubeContext = {
                        clientName: ctx.client?.clientName,
                        clientVersion: ctx.client?.clientVersion
                    };
                }
            }

            // Buscar valores de dinheiro na pagina
            const bodyText = document.body.innerText || '';
            const moneyRegex = /\\$[\\d,]+\\.?\\d*/g;
            const matches = bodyText.match(moneyRegex) || [];
            result.moneyValuesFound = [...new Set(matches)];

            // Tentar encontrar elemento especifico de receita
            const revenueElements = document.querySelectorAll('[class*="revenue"], [class*="metric"]');
            result.revenueElementsCount = revenueElements.length;

            return result;
        }""")

        print(f"\n[4] Resultados:")
        print(f"    URL: {data['url']}")
        print(f"    Titulo: {data['title']}")
        print(f"    Channel ID: {data['channelId']}")
        print(f"    ytcfg presente: {data['ytcfgPresent']}")
        print(f"    INNERTUBE_CONTEXT: {data['innertubeContext']}")
        print(f"    Valores monetarios na pagina: {data['moneyValuesFound']}")

        # Se estamos na pagina de analytics, tentar pegar mais dados
        if "analytics" in page.url or "revenue" in page.url:
            print("\n[5] Estamos na pagina de Analytics! Tentando API youtubei...")

            api_data = page.evaluate("""async () => {
                try {
                    const ctx = window.ytcfg?.get('INNERTUBE_CONTEXT');
                    if (!ctx) return { error: 'Sem contexto' };

                    // Endpoint de analytics
                    const resp = await fetch('/youtubei/v1/analytics_data/join?prettyPrint=false', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            context: ctx,
                            browseId: 'FEanalytics_revenue'
                        })
                    });

                    const json = await resp.json();
                    return {
                        status: resp.status,
                        keys: Object.keys(json || {}),
                        sample: JSON.stringify(json).substring(0, 500)
                    };
                } catch (e) {
                    return { error: e.toString() };
                }
            }""")

            print(f"    API Response: {json.dumps(api_data, indent=2)}")
        else:
            print("\n[5] Nao estamos na pagina de Analytics.")
            print("    Por favor, navegue manualmente para:")
            print("    YouTube Studio > Analytics > Revenue")
            print("    E execute o script novamente.")

        # Screenshot
        print("\n[6] Salvando screenshot...")
        page.screenshot(path="C:/Users/User-OEM/Desktop/content-factory/monetization_dashboard/debug_v2.png")
        print("    Salvo: debug_v2.png")

    print("\n" + "=" * 60)
    print("TESTE CONCLUIDO!")
    print("=" * 60)

if __name__ == "__main__":
    test_extract()

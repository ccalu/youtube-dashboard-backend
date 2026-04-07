# Guia Completo — Playwright + Freepik Spaces

> Como usamos Playwright (Python) para automatizar o Freepik Spaces.
> Documento para replicar em outro PC ou montar novos fluxos.

---

## O Que E

Usamos **Playwright** (biblioteca Python) para controlar o Chrome remotamente e automatizar o Freepik Spaces. O Chrome roda com uma porta de debug aberta e o Playwright se conecta nele — assim aproveita a sessao logada (cookies, login do Freepik).

**NAO abrimos um browser novo.** Conectamos no Chrome que ja esta aberto e logado.

---

## Como Funciona

```
[Chrome aberto]                    [Python + Playwright]
     |                                      |
     | porta 9222 (CDP)                     |
     |<------------------------------------>|
     |                                      |
     | Playwright envia comandos:           |
     |   - clicar em elementos              |
     |   - digitar texto                    |
     |   - ler conteudo da pagina           |
     |   - baixar arquivos                  |
     |   - esperar elementos aparecerem     |
```

**CDP** = Chrome DevTools Protocol. E o protocolo que o Chrome expoe na porta 9222 para controle remoto.

---

## Setup (1 vez)

### 1. Instalar Playwright
```bash
pip install playwright
```

NAO precisa rodar `playwright install` (nao vamos abrir browser novo, vamos conectar no existente).

### 2. Abrir Chrome com porta de debug
```bash
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir=C:\Users\SEU_USUARIO\chrome-debug-profile
```

- `--remote-debugging-port=9222` = abre a porta pra Playwright conectar
- `--user-data-dir=...` = usa perfil separado (nao mistura com seu Chrome normal)

### 3. Fazer login no Freepik (1 vez)
- Acessar https://br.freepik.com no Chrome que abriu
- Fazer login na conta
- Pronto! O login fica salvo no perfil

---

## Codigo Basico — Conectar e Interagir

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    # Conectar no Chrome ja aberto
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    
    # Pegar a primeira aba
    context = browser.contexts[0]
    page = context.pages[0]
    
    # Ver a URL atual
    print(page.url)
    
    # Navegar pra outra pagina
    page.goto("https://br.freepik.com/pikaso/spaces/SEU_WORKSPACE")
    
    # Esperar carregar
    page.wait_for_timeout(3000)
    
    # Fechar conexao (nao fecha o Chrome!)
    browser.close()
```

---

## Encontrando Elementos na Pagina

### Por data-id (como usamos no Freepik Spaces)
```python
# Os blocos do Freepik tem atributos data-id unicos
bloco = page.locator('[data-id="c4861991-3c27-4026-ad32-8fe46c43e360"]')

# Verificar se existe
if bloco.count() > 0:
    print("Bloco encontrado!")
```

### Por texto
```python
botao = page.locator("text=Adicionar texto")
botao_baixar = page.locator("text=Baixar")
```

### Por aria-label
```python
# Botoes de toolbar do Freepik usam aria-label
page.evaluate("""() => {
    const btns = document.querySelectorAll('button');
    for (const b of btns) {
        if (b.getAttribute('aria-label') === 'Iniciar a partir daqui') {
            b.click();
            return;
        }
    }
}""")
```

---

## Problema dos Overlays do Freepik

**IMPORTANTE:** O Freepik Spaces tem overlays (camadas transparentes) em cima dos elementos. O `.click()` normal do Playwright TRAVA porque detecta o overlay interceptando o click.

### Solucao: usar `page.evaluate()` pra tudo

Em vez de:
```python
# ERRADO — trava nos overlays
page.locator("text=Adicionar texto").click()
```

Fazer:
```python
# CORRETO — bypass dos overlays
page.evaluate("""() => {
    const bloco = document.querySelector('[data-id="ID_DO_BLOCO"]');
    const buttons = bloco.querySelectorAll('button');
    for (const b of buttons) {
        if (b.textContent.trim().includes('Adicionar texto')) {
            b.click();
            return;
        }
    }
}""")
```

### Quando usar cada abordagem

| Situacao | Metodo |
|----------|--------|
| Clicar em botao interno do Freepik | `page.evaluate()` com element.click() |
| Right-click (menu contexto) | `page.evaluate()` com dispatchEvent contextmenu |
| Menu popup (Limpar lista, Baixar) | `page.locator("text=...").click(force=True)` |
| Digitar texto | `page.keyboard.insert_text()` |
| Focar campo de texto | `page.evaluate()` com element.focus() |
| Baixar arquivo | `page.expect_download()` |

---

## Right-Click (Menu de Contexto)

O Freepik mostra opcoes como "Limpar lista" e "Baixar" via right-click.

```python
def right_click_bloco(page, data_id):
    """Right-click num bloco via dispatchEvent."""
    page.evaluate(f"""() => {{
        const el = document.querySelector('[data-id="{data_id}"]');
        if (el) {{
            const rect = el.getBoundingClientRect();
            el.dispatchEvent(new MouseEvent('contextmenu', {{
                bubbles: true,
                clientX: rect.x + rect.width / 2,
                clientY: rect.y + rect.height / 2,
            }}));
        }}
    }}""")
    page.wait_for_timeout(1500)

# Usar:
right_click_bloco(page, "ID_DO_BLOCO")

# Clicar na opcao do menu
page.locator("text=Limpar lista").click(force=True)
```

---

## Selecionar um Bloco (Ativar Toolbar)

Para ativar a toolbar de um bloco, precisa simular mousedown + mouseup + click:

```python
def selecionar_bloco(page, data_id):
    """Seleciona bloco via dispatchEvent (ativa toolbar)."""
    page.evaluate(f"""() => {{
        const el = document.querySelector('[data-id="{data_id}"]');
        if (el) {{
            const rect = el.getBoundingClientRect();
            const opts = {{
                bubbles: true,
                clientX: rect.x + rect.width / 2,
                clientY: rect.y + 10
            }};
            el.dispatchEvent(new MouseEvent('mousedown', opts));
            el.dispatchEvent(new MouseEvent('mouseup', opts));
            el.dispatchEvent(new MouseEvent('click', opts));
        }}
    }}""")
    page.wait_for_timeout(2000)
```

---

## Digitar Texto num Campo

Os campos de texto do Freepik usam TipTap/ProseMirror (editores rich text).

```python
def focar_e_digitar(page, data_id, texto):
    """Foca no campo tiptap de um bloco e digita texto."""
    # 1. Focar via evaluate (bypass overlay)
    page.evaluate(f"""() => {{
        const bloco = document.querySelector('[data-id="{data_id}"]');
        if (!bloco) return;
        const tiptap = bloco.querySelector('.tiptap, .ProseMirror, [contenteditable="true"]');
        if (tiptap) tiptap.focus();
    }}""")
    page.wait_for_timeout(300)
    
    # 2. Digitar
    page.keyboard.insert_text(texto)
```

### Colar multiplos itens (com Enter entre cada)
```python
prompts = ["prompt 1", "prompt 2", "prompt 3"]

for prompt in prompts:
    page.keyboard.insert_text(prompt)
    page.wait_for_timeout(400)
    page.keyboard.press("Enter")
    page.wait_for_timeout(400)
```

---

## Baixar Arquivos

Com CDP, downloads NAO vao pra `playwright-artifacts`. Precisa usar `expect_download`:

```python
def baixar(page, data_id, nome, pasta_destino):
    """Baixa via right-click > Baixar."""
    # Right-click no bloco
    right_click_bloco(page, data_id)
    
    # Clicar em Baixar e capturar download
    with page.expect_download(timeout=30000) as download_info:
        page.locator("text=Baixar").click(force=True)
    
    # Salvar na pasta destino
    download = download_info.value
    save_path = os.path.join(pasta_destino, f"{nome}.zip")
    download.save_as(save_path)
    print(f"Baixado: {save_path}")
```

---

## Ler Conteudo da Pagina

```python
# Ler texto de um bloco
texto = page.evaluate("""() => {
    const el = document.querySelector('[data-id="ID"]');
    return el ? el.textContent.trim() : '';
}""")

# Contar itens (ex: "14 textos")
count = page.evaluate("""() => {
    const el = document.querySelector('[data-id="ID"]');
    const m = el ? el.textContent.match(/(\\d+)\\s*textos?/) : null;
    return m ? parseInt(m[1]) : 0;
}""")
```

---

## Esperar Elementos

```python
# Esperar um elemento aparecer
page.wait_for_selector('[data-id="ID"]', timeout=10000)

# Esperar tempo fixo
page.wait_for_timeout(2000)  # 2 segundos

# Esperar condicao customizada (polling)
import time
for i in range(30):
    count = page.evaluate("() => { ... }")
    if count >= 14:
        break
    time.sleep(30)
```

---

## Regras de Ouro (aprendidas com erros)

1. **ZERO coordenadas x,y** — tudo via data-id + dispatchEvent + evaluate. Se o usuario der zoom, coordenadas quebram.

2. **Sempre `page.evaluate()` pra clicks internos** — Playwright's `.click()` trava nos overlays do Freepik.

3. **`force=True` nos menus popup** — "Limpar lista", "Baixar" precisam de `force=True`.

4. **Enter APOS cada prompt** — incluindo o ultimo. Se nao, o ultimo prompt nao e registrado.

5. **`expect_download` + `save_as`** — CDP nao salva em artifacts. Sempre capturar o download explicitamente.

6. **Esperar antes de baixar** — Freepik pode mostrar "pronto" mas ainda estar renderizando internamente. Esperar 4 min apos detectar todos prontos.

7. **Retry em `evaluate`** — pagina pode recarregar e destruir o contexto. Usar try/except com retry.

8. **`browser.close()` nao fecha o Chrome** — apenas desconecta o Playwright. O Chrome continua aberto com o login.

---

## Estrutura do Nosso Codigo

```
_features/shorts_production/
  freepik_automation.py     ← automacao completa do Freepik
```

Funcoes principais:
- `run_freepik_production(json_path)` — pipeline completo (limpar > colar > executar > esperar > baixar)
- `limpar_bloco(page, data_id)` — right-click > limpar lista
- `colar_prompts(page, block_id, prompts)` — adicionar texto > colar cada prompt
- `selecionar_voz(page, lingua)` — selecionar voz no ElevenLabs
- `executar_workflow(page)` — "Iniciar a partir daqui"
- `verificar_status(page)` — contar imagens/videos prontos
- `baixar_bloco(page, data_id, nome, dest)` — baixar ZIP

---

## Exemplo Completo — Fluxo Basico

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    # 1. Conectar
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    page = browser.contexts[0].pages[0]
    
    # 2. Navegar pro workspace
    if "spaces" not in page.url:
        page.goto("https://br.freepik.com/pikaso/spaces/SEU_ID")
        page.wait_for_timeout(3000)
    
    # 3. Esperar carregar
    page.wait_for_selector('[data-id]', timeout=10000)
    
    # 4. Interagir (exemplo: ler status)
    status = page.evaluate("""() => {
        const imgs = document.querySelector('[data-id="ID_LISTA_IMGS"]');
        const m = imgs ? imgs.textContent.match(/(\\d+)\\s*imagens?/) : null;
        return m ? parseInt(m[1]) : 0;
    }""")
    print(f"Imagens: {status}")
    
    # 5. Desconectar
    browser.close()
```

---

## Como Descobrir IDs de Blocos

1. Abrir Chrome DevTools (F12) no Freepik Spaces
2. Usar o seletor de elementos (icone de cursor no DevTools)
3. Clicar no bloco que quer automatizar
4. Procurar o atributo `data-id` no HTML
5. Copiar o UUID (ex: `c4861991-3c27-4026-ad32-8fe46c43e360`)

Cada bloco no Freepik Spaces tem um `data-id` unico e fixo.

---

## Dicas Finais

- **Testar no terminal primeiro** — antes de automatizar, testar cada passo no Python interativo
- **Logs em cada passo** — quando automatizar, logar o que esta fazendo pra debugar
- **Nao mexer no Chrome enquanto roda** — zoom, scroll, clicks podem interferir (menos com evaluate)
- **Um Chrome, um Playwright** — nao rodar 2 scripts Playwright no mesmo Chrome

# SETUP DEV-BROWSER — Passo a Passo

## Instalação (fazer uma vez)

```bash
npm install -g dev-browser
dev-browser install
```

## Uso (fazer toda vez que for usar)

### 1. Fechar TODO o Chrome
Fechar completamente, inclusive na bandeja do sistema (tray). Não pode ter nenhuma instância rodando.

### 2. Abrir Chrome com Remote Debugging
```bash
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
```

**No Mac:**
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
```

**No Linux:**
```bash
google-chrome --remote-debugging-port=9222
```

### 3. Navegar pro site que quer automatizar
Abrir o site normalmente no Chrome (ex: Freepik Spaces). Logar se necessário.

### 4. Usar o dev-browser via Claude Code
O dev-browser se conecta ao Chrome aberto com `--connect`:

```bash
dev-browser --connect "await (async () => {
  const page = await browser.getPage('freepik');
  // ... comandos aqui
})()"
```

## Comandos Principais

```javascript
// Navegar
await page.goto('https://url.com');

// Clicar
await page.click('selector');

// Preencher campo de texto
await page.fill('selector', 'texto');

// Screenshot
await page.screenshot({ path: 'screenshot.png' });

// Snapshot AI-friendly do DOM
const snapshot = await page.snapshotForAI();

// Esperar elemento aparecer
await page.waitForSelector('selector');

// Avaliar JavaScript na página
const result = await page.evaluate(() => document.title);

// Listar abas abertas
const pages = await browser.listPages();
```

## Notas
- `--connect` usa o Chrome que tu abriu (com login, cookies, etc.)
- `--headless` abre um Chrome novo limpo (sem login)
- Para Freepik Spaces: SEMPRE usar `--connect` (precisa da sessão logada)

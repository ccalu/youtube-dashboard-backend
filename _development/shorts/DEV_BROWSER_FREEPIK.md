# DEV-BROWSER + FREEPIK SPACES — Guia Operacional Definitivo

## URL do Workflow
```
https://br.freepik.com/pikaso/spaces/a166a80e-8448-4c38-b231-ce4cd2cc49ce
```

## Conexão
```bash
# 1. Fechar TODO o Chrome
# 2. Abrir com remote debugging:
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\Users\PC\chrome-debug-profile"
# 3. Logar no Freepik e abrir o workflow
# 4. Conectar dev-browser:
dev-browser --connect http://localhost:9222 <<'EOF'
const tabs = await browser.listPages();
const page = await browser.getPage(tabs[0].id);
EOF
```

---

## MAPA DE IDs (DEFINITIVO)

### Blocos onde COLAR conteúdo (3 blocos permitidos):

| Bloco | data-id INTERNO (onde está o botão e campo) | Ação |
|-------|---------------------------------------------|------|
| Prompts de imagem | `c4861991-3c27-4026-ad32-8fe46c43e360` | Adicionar texto → colar 14 prompts |
| Prompts de animação | `1ce52b31-1c46-4460-b4c2-a01778b76c6d` | Adicionar texto → colar 14 prompts |
| Script narração | `1d28d411-54eb-4d66-83eb-f414971cb89a` | Colar script completo |

### Blocos wrapper (não têm os campos, mas usados pra selecionar/toolbar):

| Bloco | data-id |
|-------|---------|
| LISTA PROMPT IMAGEM | `c2fe2a3f-3fd8-44a0-8a2f-c752a63a01e0` |
| LISTA PROMPT ANIMAÇÃO | `0ff343d9-9491-4970-a097-4c2a26fac991` |
| NARRAÇÃO (wrapper) | `68ea5e5a-f898-4f35-83b6-cd69a760dd76` |

### Blocos de OUTPUT (limpar e baixar):

| Bloco | data-id |
|-------|---------|
| LISTA GERAÇÃO DE IMAGENS | `8072ef08-819b-495a-8411-68e921856e9c` |
| LISTA VIDEOS | `f9217fab-bdfe-4a96-965a-2665e0dda2e2` |

### Blocos que NUNCA TOCAR:

| Bloco | data-id | PROIBIDO |
|-------|---------|----------|
| GERADOR DE IMAGEM (wrapper) | `e0ca3949-3d38-4f83-ac75-27cb69e553bc` | NÃO colar, NÃO deletar |
| GERADOR DE IMAGEM (conteúdo) | `f00a8e5a-2dec-487e-9eda-71803a6ea292` | NÃO colar, NÃO deletar |
| GERADOR DE VIDEO (wrapper) | `a394ce71-2d01-4b18-9f5e-725514c0ee9a` | NÃO colar, NÃO deletar |
| VIDEO GERADO (conteúdo) | `3f7f659d-e8b7-413a-885b-ebbeb558fecd` | NÃO colar, NÃO deletar |

### Aria-labels importantes:

| aria-label | O que faz |
|------------|-----------|
| `Iniciar a partir daqui` | PLAY — executa a partir do bloco selecionado (USAR ESTE SEMPRE) |
| `Iniciar a partir daqui options` | Dropdown — NÃO USAR (causa duplicatas) |
| `Esse nó somente` | PLAY da NARRAÇÃO (gera só narração) |
| `Decrease value to *` / `Increase value to *` | Botões +/- quantidade do gerador |

---

## REGRAS ABSOLUTAS

1. **Antes de colar**: verificar data-id. Se não for `c4861991`, `1ce52b31` ou `1d28d411` → ABORTAR
2. **NUNCA usar Ctrl+A ou Backspace** em NENHUM bloco (risco de deletar o workflow)
3. **NUNCA clicar na sidebar esquerda** (x < 240) — navega pra fora
4. **NUNCA clicar em GERADOR DE IMAGEM ou GERADOR DE VIDEO** (exceto pra verificar quantidade)
5. **Sempre buscar por data-id**, nunca por posição/coordenadas
6. **Antes de cada ação**: verificar URL (deve ser o workflow)

---

## PROCESSO COMPLETO

### Como Limpar uma Lista (TESTADO E FUNCIONANDO)

Funciona pra: PROMPTS IMAGEM, PROMPTS ANIMAÇÃO, LISTA IMAGENS, LISTA VIDEOS.

**Método:** RIGHT-CLICK (botão direito) no bloco → menu de contexto aparece com "Limpar lista" → clicar

**ALTERNATIVA (fallback):** Clicar no bloco WRAPPER → toolbar aparece ACIMA → último botão à direita = 3 pontinhos → "Limpar lista"

**IDs dos WRAPPERS pra limpar:**

| Lista | data-id do WRAPPER (clicar neste) |
|-------|-----------------------------------|
| Prompts imagem | `c2fe2a3f-3fd8-44a0-8a2f-c752a63a01e0` |
| Prompts animação | `0ff343d9-9491-4970-a097-4c2a26fac991` |
| Lista imagens geradas | `8072ef08-819b-495a-8411-68e921856e9c` |
| Lista vídeos | `f9217fab-bdfe-4a96-965a-2665e0dda2e2` |

**IMPORTANTE:** Para LISTA IMAGENS e LISTA VIDEOS, os botões da toolbar NÃO têm aria-label. Encontrar pela posição relativa ao bloco (acima do bloco, último botão à direita).

```javascript
async function limparBloco(page, wrapperId, nome) {
  // 1. Clicar no WRAPPER pra selecionar
  const block = await page.evaluate((id) => {
    const el = document.querySelector('[data-id="' + id + '"]');
    if (!el) return null;
    const rect = el.getBoundingClientRect();
    return { x: Math.round(rect.x + 20), y: Math.round(rect.y + 5), top: Math.round(rect.y), right: Math.round(rect.right) };
  }, wrapperId);
  if (!block) { console.log(nome + ": bloco nao encontrado"); return false; }

  await page.mouse.click(block.x, block.y);
  await new Promise(r => setTimeout(r, 2000));

  // 2. Toolbar aparece ACIMA do bloco — pegar botões nessa faixa
  const dotsInfo = JSON.stringify({ top: block.top, right: block.right });
  const dots = await page.evaluate((info) => {
    const d = JSON.parse(info);
    const btns = document.querySelectorAll('button');
    let rightmost = null;
    for (const b of btns) {
      const rect = b.getBoundingClientRect();
      if (rect.y > d.top - 60 && rect.y < d.top && rect.x < d.right + 10 && b.offsetParent !== null && rect.width > 10 && rect.width < 40) {
        if (!rightmost || rect.x > rightmost.x) {
          rightmost = { x: rect.x + rect.width/2, y: rect.y + rect.height/2 };
        }
      }
    }
    return rightmost;
  }, dotsInfo);
  if (!dots) { console.log(nome + ": toolbar nao apareceu"); return false; }

  // 3. Clicar 3 pontinhos (ultimo botao à direita)
  await page.mouse.click(dots.x, dots.y);
  await new Promise(r => setTimeout(r, 1500));

  // 4. Clicar "Limpar lista"
  const limpar = await page.evaluate(() => {
    for (const el of document.querySelectorAll('*')) {
      if (el.textContent.trim() === 'Limpar lista' && el.offsetParent !== null) {
        const rect = el.getBoundingClientRect();
        if (rect.width > 30) return { x: rect.x + rect.width/2, y: rect.y + rect.height/2 };
      }
    }
    return null;
  });
  if (!limpar) { console.log(nome + ": Limpar lista nao encontrado"); return false; }

  await page.mouse.click(limpar.x, limpar.y);
  await new Promise(r => setTimeout(r, 1000));
  console.log(nome + ": LIMPOU!");
  return true;
}

// Limpar os 4 blocos de lista:
await limparBloco(page, 'c2fe2a3f-3fd8-44a0-8a2f-c752a63a01e0', 'PROMPTS IMAGEM');
await limparBloco(page, '0ff343d9-9491-4970-a097-4c2a26fac991', 'PROMPTS ANIMACAO');
await limparBloco(page, '8072ef08-819b-495a-8411-68e921856e9c', 'LISTA IMAGENS');
await limparBloco(page, 'f9217fab-bdfe-4a96-965a-2665e0dda2e2', 'LISTA VIDEOS');
```

### Como Limpar Narração (DIFERENTE das listas)

A narração NÃO tem "Limpar lista". É limpa manualmente: clicar no campo, selecionar todo texto, apagar.

```javascript
// 1. Encontrar campo tiptap DENTRO do bloco 1d28d411
const narField = await page.evaluate(() => {
  const bloco = document.querySelector('[data-id="1d28d411-54eb-4d66-83eb-f414971cb89a"]');
  if (!bloco) return null;
  const tipTap = bloco.querySelector('.tiptap.ProseMirror');
  if (!tipTap) return null;
  const rect = tipTap.getBoundingClientRect();
  return { x: Math.round(rect.x + 10), y: Math.round(rect.y + 10) };
});

// 2. Clicar no campo
await page.mouse.click(narField.x, narField.y);
await new Promise(r => setTimeout(r, 500));

// 3. Selecionar TODO o texto (Ctrl+Home, Shift+Ctrl+End)
await page.keyboard.down('Control');
await page.keyboard.press('Home');
await page.keyboard.up('Control');
await new Promise(r => setTimeout(r, 200));

await page.keyboard.down('Shift');
await page.keyboard.down('Control');
await page.keyboard.press('End');
await page.keyboard.up('Control');
await page.keyboard.up('Shift');
await new Promise(r => setTimeout(r, 200));

// 4. Apagar texto selecionado
await page.keyboard.press('Backspace');
await new Promise(r => setTimeout(r, 500));

// 5. VERIFICAR que o bloco ainda existe
const blocoOk = await page.evaluate(() => {
  return !!document.querySelector('[data-id="1d28d411-54eb-4d66-83eb-f414971cb89a"]');
});
if (!blocoOk) console.log("ERRO: bloco narração sumiu!");
else console.log("NARRACAO: LIMPA!");
```

### PASSO 2: COLAR PROMPTS DE IMAGEM

```javascript
// Encontrar "Adicionar texto" DENTRO do bloco c4861991
const btn = await page.evaluate(() => {
  const bloco = document.querySelector('[data-id="c4861991-3c27-4026-ad32-8fe46c43e360"]');
  if (!bloco) return null;
  const buttons = bloco.querySelectorAll('button');
  for (const b of buttons) {
    if (b.textContent.trim().includes('Adicionar texto')) {
      const rect = b.getBoundingClientRect();
      return { x: Math.round(rect.x + rect.width/2), y: Math.round(rect.y + rect.height/2) };
    }
  }
  return null;
});
await page.mouse.click(btn.x, btn.y);
await new Promise(r => setTimeout(r, 1500));

// Encontrar campo tiptap DENTRO do mesmo bloco c4861991
const field = await page.evaluate(() => {
  const bloco = document.querySelector('[data-id="c4861991-3c27-4026-ad32-8fe46c43e360"]');
  if (!bloco) return null;
  const tipTap = bloco.querySelector('.tiptap.ProseMirror');
  if (!tipTap) return null;
  const rect = tipTap.getBoundingClientRect();
  return { x: Math.round(rect.x + 10), y: Math.round(rect.y + 5) };
});
await page.mouse.click(field.x, field.y);
await new Promise(r => setTimeout(r, 300));

// Colar prompt 1, Enter, prompt 2, Enter... até 14
await page.keyboard.insertText(prompts[0]);
for (let i = 1; i < prompts.length; i++) {
  await page.keyboard.press('Enter');
  await new Promise(r => setTimeout(r, 300));
  await page.keyboard.insertText(prompts[i]);
  await new Promise(r => setTimeout(r, 500));
}
```

### PASSO 3: COLAR PROMPTS DE ANIMAÇÃO

Mesmo processo, bloco `1ce52b31`:

```javascript
const btn = await page.evaluate(() => {
  const bloco = document.querySelector('[data-id="1ce52b31-1c46-4460-b4c2-a01778b76c6d"]');
  if (!bloco) return null;
  const buttons = bloco.querySelectorAll('button');
  for (const b of buttons) {
    if (b.textContent.trim().includes('Adicionar texto')) {
      const rect = b.getBoundingClientRect();
      return { x: Math.round(rect.x + rect.width/2), y: Math.round(rect.y + rect.height/2) };
    }
  }
  return null;
});
await page.mouse.click(btn.x, btn.y);
await new Promise(r => setTimeout(r, 1500));

const field = await page.evaluate(() => {
  const bloco = document.querySelector('[data-id="1ce52b31-1c46-4460-b4c2-a01778b76c6d"]');
  if (!bloco) return null;
  const tipTap = bloco.querySelector('.tiptap.ProseMirror');
  if (!tipTap) return null;
  const rect = tipTap.getBoundingClientRect();
  return { x: Math.round(rect.x + 10), y: Math.round(rect.y + 5) };
});
await page.mouse.click(field.x, field.y);
await new Promise(r => setTimeout(r, 300));

await page.keyboard.insertText(animPrompts[0]);
for (let i = 1; i < animPrompts.length; i++) {
  await page.keyboard.press('Enter');
  await new Promise(r => setTimeout(r, 300));
  await page.keyboard.insertText(animPrompts[i]);
  await new Promise(r => setTimeout(r, 500));
}
```

### PASSO 4: COLAR SCRIPT NA NARRAÇÃO

```javascript
const field = await page.evaluate(() => {
  const bloco = document.querySelector('[data-id="1d28d411-54eb-4d66-83eb-f414971cb89a"]');
  if (!bloco) return null;
  const tipTap = bloco.querySelector('.tiptap.ProseMirror');
  if (!tipTap) return null;
  const rect = tipTap.getBoundingClientRect();
  return { x: Math.round(rect.x + 10), y: Math.round(rect.y + 5) };
});
await page.mouse.click(field.x, field.y);
await new Promise(r => setTimeout(r, 300));
await page.keyboard.insertText(script);
```

### PASSO 5: SELECIONAR VOZ DA NARRAÇÃO (TESTADO E FUNCIONANDO)

**ANTES de gerar a narração**, verificar e trocar a voz para a língua do canal.

| Língua | Voz | Filtro no seletor |
|--------|-----|-------------------|
| Português (PT-BR) | Lucas Moreira | Português |
| Inglês (EN) | Caleb Morgan | Inglês |
| Espanhol (ES) | Diego Marín | Espanhol |
| Francês (FR) | Diego Marín | Francês |
| Italiano (IT) | Giulio Ferrante | Italiano |
| Russo (RU) | Léo Gamier | Russo |
| Japonês (JP) | Giulio Ferrante | Japonês |
| Coreano (KO) | Ji-Hoon | Coreano |
| Turco (TR) | Can Özkan | Turco |
| Polonês (PL) | Diego Marín | Polonês |
| Alemão (DE) | Lukas Schneider | Alemão |

Modelo é SEMPRE **ElevenLabs v2**.

**Processo para trocar a voz (TESTADO — usar data-id + locator):**

```javascript
// 1. Clicar no bloco NARRACAO (1d28d411) pra ativar o rodapé
const narBlock = await page.evaluate(() => {
  const el = document.querySelector('[data-id="1d28d411-54eb-4d66-83eb-f414971cb89a"]');
  const rect = el.getBoundingClientRect();
  return { x: Math.round(rect.x + rect.width/2), y: Math.round(rect.y + rect.height/2) };
});
await page.mouse.click(narBlock.x, narBlock.y);
await new Promise(r => setTimeout(r, 2000));

// 2. Encontrar botão da voz DENTRO do bloco 1d28d411
const voiceBtn = await page.evaluate(() => {
  const bloco = document.querySelector('[data-id="1d28d411-54eb-4d66-83eb-f414971cb89a"]');
  const btns = bloco.querySelectorAll('button');
  for (const b of btns) {
    const text = b.textContent.trim();
    // Botão da voz: tem texto, NÃO é ElevenLabs, NÃO é número, NÃO tem aria-label
    if (text && !text.includes('ElevenLabs') && !text.match(/^[\d:\/]+$/) && !b.getAttribute('aria-label') && text.length > 2) {
      const rect = b.getBoundingClientRect();
      return { x: rect.x + rect.width/2, y: rect.y + rect.height/2, text: text };
    }
  }
  return null;
});

// 3. Clicar no nome da voz → abre seletor de vozes
await page.mouse.click(voiceBtn.x, voiceBtn.y);
await new Promise(r => setTimeout(r, 2000));

// 4. Usar page.locator pra trocar língua (busca o filtro atual e clica)
const langFilter = page.locator('text=Inglês'); // nome da língua atual no filtro
await langFilter.first().click();
await new Promise(r => setTimeout(r, 1500));

// 5. Selecionar a língua desejada
const targetLang = page.locator('text=Italiano'); // língua alvo
await targetLang.first().click();
await new Promise(r => setTimeout(r, 2000));

// 6. Selecionar a voz desejada
const targetVoice = page.locator('text=Giulio Ferrante'); // voz alvo
await targetVoice.first().click();
await new Promise(r => setTimeout(r, 1500));
// Voz trocada!
```

**ATENÇÃO sobre limpar narração:**
- Limpar texto: Ctrl+Home → Shift+Ctrl+End → Backspace (DENTRO do campo tiptap do bloco `1d28d411`)
- SEMPRE verificar que o bloco ainda existe depois de limpar
- NUNCA usar Ctrl+A (seleciona a página inteira e pode excluir blocos)
- Limpar o texto ANTES de colar o script novo (pra não duplicar)

### PASSO 6: VERIFICAR GERADOR DE IMAGEM (quantidade = 1)

Clicar na engrenagem do GERADOR DE IMAGEM, depois nos botões +/- pra resetar:

```javascript
// Encontrar botões +/- por aria-label
const plus = await page.evaluate(() => {
  const btns = document.querySelectorAll('button');
  for (const b of btns) {
    if ((b.getAttribute('aria-label') || '').includes('Increase') && b.offsetParent !== null) {
      const rect = b.getBoundingClientRect();
      return { x: Math.round(rect.x + rect.width/2), y: Math.round(rect.y + rect.height/2) };
    }
  }
  return null;
});
const minus = await page.evaluate(() => {
  const btns = document.querySelectorAll('button');
  for (const b of btns) {
    if ((b.getAttribute('aria-label') || '').includes('Decrease') && b.offsetParent !== null) {
      const rect = b.getBoundingClientRect();
      return { x: Math.round(rect.x + rect.width/2), y: Math.round(rect.y + rect.height/2) };
    }
  }
  return null;
});
// Click + then - to reset to 1
await page.mouse.click(plus.x, plus.y);
await new Promise(r => setTimeout(r, 500));
await page.mouse.click(minus.x, minus.y);
```

### PASSO 7: EXECUTAR WORKFLOW (imagens + vídeos)

1. Selecionar o bloco interno de prompts de imagem (`c4861991`) via dispatchEvent click
2. Toolbar aparece com botão `aria-label="Iniciar a partir daqui"`
3. Clicar no botão PLAY direto (NÃO abrir dropdown, NÃO usar "Todo o fluxo")
4. Dialog "Deseja continuar?" → clicar "Aceitar"

**NUNCA usar "Todo o fluxo de trabalho" — causa duplicatas de imagens!**

```javascript
// Selecionar bloco via dispatchEvent (sem coordenadas)
await page.evaluate(() => {
  const el = document.querySelector('[data-id="c4861991-3c27-4026-ad32-8fe46c43e360"]');
  const rect = el.getBoundingClientRect();
  el.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, clientX: rect.x + rect.width/2, clientY: rect.y + 10 }));
  el.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, clientX: rect.x + rect.width/2, clientY: rect.y + 10 }));
  el.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: rect.x + rect.width/2, clientY: rect.y + 10 }));
});
await new Promise(r => setTimeout(r, 2000));

// Clicar play DIRETO (Iniciar a partir daqui)
await page.evaluate(() => {
  const btns = document.querySelectorAll('button');
  for (const b of btns) {
    if (b.getAttribute('aria-label') === 'Iniciar a partir daqui') { b.click(); return; }
  }
});
await new Promise(r => setTimeout(r, 2000));

// Aceitar dialog
const aceitar = page.locator('text=Aceitar');
if (await aceitar.count() > 0) await aceitar.first().click();
```

### PASSO 8: GERAR NARRAÇÃO (separado)

1. Clicar no bloco NARRAÇÃO pra selecionar
2. Toolbar aparece com botão `aria-label="Esse nó somente"`
3. Clicar pra gerar a narração

```javascript
const narPlay = await page.evaluate(() => {
  const btns = document.querySelectorAll('button');
  for (const b of btns) {
    if (b.getAttribute('aria-label') === 'Esse nó somente' && b.offsetParent !== null) {
      const rect = b.getBoundingClientRect();
      if (rect.width > 20) return { x: Math.round(rect.x + rect.width/2), y: Math.round(rect.y + rect.height/2) };
    }
  }
  return null;
});
await page.mouse.click(narPlay.x, narPlay.y);
```

### PASSO 9: CORRIGIR BUG DAS IMAGENS DUPLICADAS (se necessário)

**Como detectar:** Verificar LISTA GERAÇÃO DE IMAGENS (`8072ef08`). Se mostra "24 imagens" em vez de "14 imagens", o bug aconteceu.

**O que acontece:** O gerador criou 2 cópias de cada imagem (28 total). O GERADOR DE VIDEO trava porque recebe 28 imagens em vez de 14.

**Processo de correção:**

1. **PAUSAR o GERADOR DE VIDEO** — clicar no botão de pausa no bloco VIDEO GERADO (`3f7f659d`)
   ```javascript
   // Encontrar botão de pausa no GERADOR DE VIDEO
   const pauseBtn = await page.evaluate(() => {
     const bloco = document.querySelector('[data-id="3f7f659d-e8b7-413a-885b-ebbeb558fecd"]');
     if (!bloco) return null;
     const btns = bloco.querySelectorAll('button');
     for (const b of btns) {
       const rect = b.getBoundingClientRect();
       if (b.offsetParent !== null && rect.width > 15 && rect.width < 40) {
         return { x: Math.round(rect.x + rect.width/2), y: Math.round(rect.y + rect.height/2) };
       }
     }
     return null;
   });
   if (pauseBtn) {
     await page.mouse.click(pauseBtn.x, pauseBtn.y);
     await new Promise(r => setTimeout(r, 1000));
     console.log("VIDEO PAUSADO!");
   }
   ```

2. **Ir na LISTA GERAÇÃO DE IMAGENS** (`8072ef08`) — clicar em "24 imagens" no rodapé do bloco

3. **Desselecionar imagens duplicadas** — as 28 imagens são 14 pares (cada imagem aparece 2x seguidas). Selecionar UMA de cada par:
   - Imagem 1 ✅ (manter)
   - Imagem 2 ❌ (desselecionar — é cópia da 1)
   - Imagem 3 ✅ (manter)
   - Imagem 4 ❌ (desselecionar — é cópia da 3)
   - ... e assim por diante até ficar 14 selecionadas

4. **Dar PLAY no GERADOR DE VIDEO** — agora ele vai gerar vídeos só pras 14 imagens selecionadas

**NOTA:** Este bug acontece quando a quantidade no GERADOR DE IMAGEM está em 2 em vez de 1. Por isso o PASSO 6 (verificar quantidade = 1) é importante. Mas mesmo fazendo +1 -1, às vezes o bug acontece.

### PASSO 9.5: MONITORAMENTO DO FLUXO (TEMPOS E VERIFICAÇÕES)

**Nos primeiros 2 minutos após iniciar o fluxo:**
- Verificar LISTA GERAÇÃO DE IMAGENS (`8072ef08`)
- Se mostrar mais de 14 imagens → BUG! Ir pro PASSO 9
- Se mostrar 14 ou menos → tudo certo, continuar aguardando

**Após 5 minutos:**
- Todas as 14 imagens devem estar geradas
- Vídeos devem estar começando a aparecer na LISTA VIDEOS
- Se imagens prontas mas ZERO vídeos aparecendo → pausar gerador de vídeo e dar play de novo

**Após 10-15 minutos (sem erros):**
- Tudo deve estar pronto: 14 imagens + 14 vídeos + narração
- SÓ BAIXAR quando NADA estiver processando
- Verificar que não tem "na fila..." ou "gerando..." em nenhum bloco

**REGRA: SÓ BAIXAR QUANDO TUDO ESTIVER 100% PRONTO. NADA PROCESSANDO.**

### PASSO 10: VERIFICAR SE FINALIZOU

Verificar que TUDO está pronto antes de baixar:

```javascript
// Verificar quantidade de imagens geradas
const imgCount = await page.evaluate(() => {
  const bloco = document.querySelector('[data-id="8072ef08-819b-495a-8411-68e921856e9c"]');
  if (!bloco) return null;
  const text = bloco.textContent.trim();
  const match = text.match(/(\d+)\s*imagens?/);
  return match ? parseInt(match[1]) : 0;
});

// Verificar quantidade de vídeos gerados
// Procurar bloco LISTA VIDEOS pelo texto
const vidCount = await page.evaluate(() => {
  const all = document.querySelectorAll('[data-id]');
  for (const el of all) {
    const text = el.textContent.trim();
    if (text.includes('LISTA VIDEOS') || text.includes('vídeos')) {
      const match = text.match(/(\d+)\s*vídeos?/);
      if (match) return parseInt(match[1]);
    }
  }
  return 0;
});

// Verificar se narração tem duração (não está mais "na fila")
const narReady = await page.evaluate(() => {
  const bloco = document.querySelector('[data-id="1d28d411-54eb-4d66-83eb-f414971cb89a"]');
  if (!bloco) return false;
  const text = bloco.textContent.trim();
  return text.includes('00:') && !text.includes('fila');
});

console.log("Imagens: " + imgCount + "/14");
console.log("Videos: " + vidCount + "/14");
console.log("Narracao pronta: " + narReady);
// Tudo pronto quando: imgCount >= 14, vidCount >= 14, narReady === true
```

**Sinais de que finalizou:**
- LISTA GERAÇÃO DE IMAGENS mostra "14 imagens" (ou "24 imagens" se bugou)
- LISTA VIDEOS mostra "14 vídeos" com duração "00:06" em cada
- NARRAÇÃO mostra duração (ex: "00:45") e não "na fila..."
- Nenhum bloco mostra "Imagem na fila..." ou "Vídeo na fila..."

### PASSO 11: BAIXAR TUDO (TESTADO E FUNCIONANDO)

Para baixar de qualquer bloco: selecionar → toolbar aparece → clicar no **penúltimo** botão (download/setinha pra baixo).

```javascript
async function baixarBloco(page, wrapperId, nome) {
  // 1. Clicar no bloco wrapper pra selecionar
  const block = await page.evaluate((id) => {
    const el = document.querySelector('[data-id="' + id + '"]');
    if (!el) return null;
    const rect = el.getBoundingClientRect();
    return { x: Math.round(rect.x + 20), y: Math.round(rect.y + 5), top: Math.round(rect.y), right: Math.round(rect.right) };
  }, wrapperId);
  if (!block) { console.log(nome + ": nao encontrado"); return; }

  await page.mouse.click(block.x, block.y);
  await new Promise(r => setTimeout(r, 2000));

  // 2. Encontrar toolbar acima do bloco
  const dotsInfo = JSON.stringify({ top: block.top, right: block.right });
  const toolBtns = await page.evaluate((info) => {
    const d = JSON.parse(info);
    const btns = document.querySelectorAll('button');
    const found = [];
    for (const b of btns) {
      const rect = b.getBoundingClientRect();
      if (rect.y > d.top - 60 && rect.y < d.top && rect.x < d.right + 10 && b.offsetParent !== null && rect.width > 10 && rect.width < 40) {
        found.push({ x: Math.round(rect.x + rect.width/2), y: Math.round(rect.y + rect.height/2) });
      }
    }
    return found.sort((a, b) => a.x - b.x);
  }, dotsInfo);

  // 3. Penúltimo botão = download
  if (toolBtns.length >= 2) {
    const dlBtn = toolBtns[toolBtns.length - 2];
    await page.mouse.click(dlBtn.x, dlBtn.y);
    await new Promise(r => setTimeout(r, 3000));
    console.log(nome + ": DOWNLOAD!");
  }
}

// Baixar vídeos
await baixarBloco(page, 'f9217fab-bdfe-4a96-965a-2665e0dda2e2', 'LISTA VIDEOS');

// Baixar imagens
await baixarBloco(page, '8072ef08-819b-495a-8411-68e921856e9c', 'LISTA IMAGENS');

// Baixar narração
await baixarBloco(page, '68ea5e5a-f898-4f35-83b6-cd69a760dd76', 'NARRACAO');
```

**IMPORTANTE sobre downloads:**

O Freepik baixa arquivos como ZIP pra uma pasta temporária do Playwright:
```
C:\Users\PC\AppData\Local\Temp\playwright-artifacts-*\
```

Os arquivos ficam com nomes aleatórios (UUID) sem extensão, mas são ZIPs.

**Processo pós-download:**
1. Encontrar o arquivo mais recente na pasta playwright-artifacts
2. Renomear pra .zip
3. Descompactar na pasta correta em `C:\Users\PC\Downloads\SHORTS\{canal}\{video}\`
4. Organizar: imagens em `img\`, vídeos em `clips\`, narração na raiz

**Formato dos downloads:**
- Cada download é um ZIP com 1 arquivo dentro
- Imagens: ZIP contém `.png` (nome baseado no prompt)
- Vídeos: ZIP contém `.mp4` (nome baseado no prompt + minimax_768p_9-16)
- Narração: ZIP com MP3 dentro

**Pasta de artifacts do Playwright:**
```
C:\Users\PC\AppData\Local\Temp\playwright-artifacts-*\
```

**Processo completo pós-download (Python/Bash):**

```python
import os, glob, zipfile, shutil

ARTIFACTS_DIR = glob.glob("C:/Users/PC/AppData/Local/Temp/playwright-artifacts-*")[0]
DEST = "C:/Users/PC/Downloads/SHORTS/{subnicho}/{canal}/{3_primeiras_palavras}"

# Criar pastas
os.makedirs(f"{DEST}/img", exist_ok=True)
os.makedirs(f"{DEST}/clips", exist_ok=True)

# Pegar todos os ZIPs baixados (ordenados por data)
zips = sorted(glob.glob(f"{ARTIFACTS_DIR}/*"), key=os.path.getmtime)

for z in zips:
    with zipfile.ZipFile(z, 'r') as zf:
        for name in zf.namelist():
            if name.endswith('.png'):
                zf.extract(name, f"{DEST}/img/")
            elif name.endswith('.mp4'):
                zf.extract(name, f"{DEST}/clips/")
            elif name.endswith('.mp3') or name.endswith('.wav'):
                zf.extract(name, DEST)

# Renomear pra cena_01, cena_02... (na ordem)
imgs = sorted(glob.glob(f"{DEST}/img/*.png"))
for i, img in enumerate(imgs):
    os.rename(img, f"{DEST}/img/cena_{i+1:02d}.png")

clips = sorted(glob.glob(f"{DEST}/clips/*.mp4"))
for i, clip in enumerate(clips):
    os.rename(clip, f"{DEST}/clips/cena_{i+1:02d}.mp4")
```

### PASSO 12: SALVAR NA PASTA LOCAL

Pasta base: `C:\Users\PC\Downloads\SHORTS`

Estrutura (mesma do Google Drive):
```
C:\Users\PC\Downloads\SHORTS\
└── {Subnicho}\
    └── {(LINGUA) Nome do Canal}\
        └── {3 Primeiras Palavras do Título}\
            ├── producao.json      ← criado ANTES da geração (passo 0)
            ├── copy.txt           ← criado ANTES da geração (passo 0)
            ├── narracao.mp3       ← baixado do Spaces
            ├── img\
            │   ├── cena_01.png ... cena_14.png
            └── clips\
                ├── cena_01.mp4 ... cena_14.mp4
```

**IMPORTANTE:** A pasta e os arquivos .json e .txt são criados ANTES de executar o Spaces (quando os agentes geram os prompts). Depois da geração, só precisa baixar imagens, clips e narração pra dentro dessa pasta que já existe.

### PASSO 0 (ANTES DE TUDO): CRIAR PASTA E SALVAR PROMPTS

Quando os agentes (Roteirista + Diretor) geram os prompts:
1. Identificar o canal e subnicho
2. Criar pasta: `C:\Users\PC\Downloads\SHORTS\{Subnicho}\{(LINGUA) Canal}\{3 Primeiras Palavras}\`
3. Criar subpastas: `img\` e `clips\`
4. Salvar `producao.json` (JSON completo com prompts)
5. Salvar `copy.txt` (título + descrição + script)

Depois disso → seguir passos 1-11 no Spaces.

---

## SELEÇÃO DE VOZ (PROCESSO TESTADO COM IDs)

**O botão da voz está DENTRO do bloco `1d28d411` (NARRAÇÃO).**

Botões dentro do `1d28d411`:
- `[01:31]` — duração do áudio
- `[202/02]` — contagem
- `[ElevenLabs v2]` — BUTTON — modelo (não mexer)
- `[Nome da Voz]` — BUTTON — voz atual (CLICAR AQUI pra trocar)
- `aria-label: Decrease/Increase` — velocidade

**Processo:**
```javascript
// 1. Encontrar botão da voz DENTRO do bloco 1d28d411
const voiceBtn = await page.evaluate(() => {
  const bloco = document.querySelector('[data-id="1d28d411-54eb-4d66-83eb-f414971cb89a"]');
  const btns = bloco.querySelectorAll('button');
  for (const b of btns) {
    const text = b.textContent.trim();
    if (text && !text.includes('ElevenLabs') && !text.match(/^[\d:\/]+$/) && !b.getAttribute('aria-label') && text.length > 2) {
      const rect = b.getBoundingClientRect();
      return { x: rect.x + rect.width/2, y: rect.y + rect.height/2, text: text };
    }
  }
  return null;
});

// 2. Clicar pra abrir seletor
await page.mouse.click(voiceBtn.x, voiceBtn.y);

// 3. Usar page.locator pra trocar lingua e voz
const langFilter = page.locator('text=Inglês');  // ou lingua atual
await langFilter.first().click();

const targetLang = page.locator('text=Italiano');  // lingua desejada
await targetLang.first().click();

const targetVoice = page.locator('text=Giulio Ferrante');  // voz desejada
await targetVoice.first().click();
```

## DOWNLOAD — VIA RIGHT-CLICK + LOCATOR

**Método:** contextmenu via dispatchEvent no bloco → `page.locator('text=Baixar')` → clicar

Funciona igual pra TODOS os blocos:
- LISTA IMAGENS (`8072ef08`) → ZIP com 14 PNGs
- LISTA VIDEOS (`f9217fab`) → ZIP com 14 MP4s
- NARRAÇÃO (`68ea5e5a`) → ZIP com MP3 dentro

**TODOS os downloads vêm como ZIP** (incluindo narração).

```javascript
// contextmenu via dispatchEvent (sem coordenadas do viewport)
await page.evaluate(() => {
  const el = document.querySelector('[data-id="ID_DO_BLOCO"]');
  const rect = el.getBoundingClientRect();
  el.dispatchEvent(new MouseEvent('contextmenu', {
    bubbles: true,
    clientX: rect.x + rect.width/2,
    clientY: rect.y + rect.height/2,
  }));
});
await new Promise(r => setTimeout(r, 1500));

const baixar = page.locator('text=Baixar');
await baixar.first().click();
```

## ERROS QUE NUNCA MAIS COMETER

1. **Colar no GERADOR em vez do PROMPT** — sempre verificar data-id antes
2. **Usar Ctrl+A / Backspace** — risco de apagar o workflow inteiro
3. **Clicar na sidebar esquerda** — navega pra fora do workflow
4. **Confiar em coordenadas fixas** — sempre buscar por data-id
5. **Esquecer de verificar voz antes de gerar narração** — cada língua tem sua voz
6. **Não resetar quantidade do gerador** — gera 28 imagens em vez de 14

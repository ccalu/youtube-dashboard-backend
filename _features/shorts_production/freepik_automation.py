"""
Freepik Spaces Automation — executa produção de Shorts via Playwright Python.

Recebe producao.json e executa todo o workflow no Freepik Spaces:
limpar → colar prompts → verificar gerador → executar → esperar → baixar → organizar.

Requer: playwright instalado + Chrome aberto com --remote-debugging-port=9222
"""

import json
import os
import glob
import time
import shutil
import zipfile
import hashlib
import logging
from typing import Optional, Callable

from playwright.sync_api import sync_playwright, Page, Browser

logger = logging.getLogger(__name__)

WORKFLOW_URL = "https://br.freepik.com/pikaso/spaces/a166a80e-8448-4c38-b231-ce4cd2cc49ce"
CDP_URL = "http://localhost:9222"

# === IDs DEFINITIVOS DOS BLOCOS ===
IDS = {
    "PROMPTS_IMAGEM": "c4861991-3c27-4026-ad32-8fe46c43e360",
    "PROMPTS_ANIMACAO": "1ce52b31-1c46-4460-b4c2-a01778b76c6d",
    "NARRACAO_TEXTO": "1d28d411-54eb-4d66-83eb-f414971cb89a",
    "WRAPPER_NARRACAO": "68ea5e5a-f898-4f35-83b6-cd69a760dd76",
    "LISTA_IMAGENS": "8072ef08-819b-495a-8411-68e921856e9c",
    "LISTA_VIDEOS": "f9217fab-bdfe-4a96-965a-2665e0dda2e2",
}

VOZES = {
    "Português": "Lucas Moreira",
    "Portugues": "Lucas Moreira",
    "Inglês": "Caleb Morgan",
    "Ingles": "Caleb Morgan",
    "Espanhol": "Diego Marín",
    "Francês": "Diego Marín",
    "Frances": "Diego Marín",
    "Italiano": "Giulio Ferrante",
    "Russo": "Léo Garnier",
    "Japonês": "Giulio Ferrante",
    "Japones": "Giulio Ferrante",
    "Coreano": "Ji-Hoon",
    "Turco": "Can Özkan",
    "Polonês": "Diego Marín",
    "Polones": "Diego Marín",
    "Alemão": "Lukas Schneider",
    "Alemao": "Lukas Schneider",
}


def _get_page(browser: Browser) -> Page:
    """Retorna a primeira página do browser, navegando pro Freepik se necessário."""
    context = browser.contexts[0]
    page = context.pages[0]
    if "spaces" not in page.url:
        page.goto(WORKFLOW_URL)
        page.wait_for_timeout(5000)
    else:
        # Esperar página estabilizar (evita "Execution context was destroyed")
        page.wait_for_timeout(2000)
    # Confirmar que a página carregou
    page.wait_for_selector('[data-id]', timeout=10000)
    return page


def _bloco(page: Page, data_id: str):
    """Retorna locator de um bloco pelo data-id."""
    return page.locator(f'[data-id="{data_id}"]')


def _right_click_bloco(page: Page, data_id: str):
    """Right-click num bloco via dispatchEvent (funciona independente de zoom)."""
    for attempt in range(3):
        try:
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
            return
        except Exception as e:
            if attempt < 2:
                logger.warning(f"Right-click retry {attempt+1}: {e}")
                page.wait_for_timeout(2000)
            else:
                raise


def _select_bloco(page: Page, data_id: str):
    """Seleciona um bloco via dispatchEvent (mousedown + mouseup + click)."""
    page.evaluate(f"""() => {{
        const el = document.querySelector('[data-id="{data_id}"]');
        if (el) {{
            const rect = el.getBoundingClientRect();
            const opts = {{ bubbles: true, clientX: rect.x + rect.width / 2, clientY: rect.y + 10 }};
            el.dispatchEvent(new MouseEvent('mousedown', opts));
            el.dispatchEvent(new MouseEvent('mouseup', opts));
            el.dispatchEvent(new MouseEvent('click', opts));
        }}
    }}""")
    page.wait_for_timeout(2000)


# === PASSO 1: LIMPAR ===

def limpar_bloco(page: Page, data_id: str, nome: str):
    """Limpa lista via right-click → 'Limpar lista'. Usa ID INTERNO, não wrapper."""
    _right_click_bloco(page, data_id)
    limpar = page.locator("text=Limpar lista")
    if limpar.count() > 0:
        limpar.first.click(force=True)
        page.wait_for_timeout(1000)
        logger.info(f"{nome}: LIMPOU")
    else:
        logger.info(f"{nome}: lista já vazia")


def limpar_narracao(page: Page):
    """Limpa texto da narração via evaluate (bypass overlays)."""
    found = page.evaluate(f"""() => {{
        const bloco = document.querySelector('[data-id="{IDS["NARRACAO_TEXTO"]}"]');
        if (!bloco) return false;
        const tiptap = bloco.querySelector('.tiptap, .ProseMirror, [contenteditable="true"]');
        if (!tiptap) return false;
        tiptap.focus();
        return true;
    }}""")
    if found:
        page.wait_for_timeout(500)
        page.keyboard.press("Control+KeyA")
        page.wait_for_timeout(200)
        page.keyboard.press("Backspace")
        page.wait_for_timeout(500)
        logger.info("NARRACAO: texto limpo")
    else:
        logger.warning("NARRACAO: campo tiptap não encontrado")


# === PASSO 2-3: COLAR PROMPTS ===

def _click_adicionar_texto(page: Page, block_id: str) -> bool:
    """Clica em 'Adicionar texto' e foca no tiptap. Espera ate o botao aparecer."""
    # Esperar ate o botao "Adicionar texto" existir (max 10s)
    for wait in range(10):
        result = page.evaluate(f"""() => {{
            const bloco = document.querySelector('[data-id="{block_id}"]');
            if (!bloco) return 'no_block';
            const buttons = bloco.querySelectorAll('button');
            for (const b of buttons) {{
                if (b.textContent.trim().includes('Adicionar texto')) return 'found';
            }}
            return 'no_button';
        }}""")
        if result == 'found':
            break
        if result == 'no_block':
            logger.error(f"Adicionar texto: bloco nao encontrado")
            return False
        page.wait_for_timeout(1000)
    else:
        logger.error(f"Adicionar texto: botao nao apareceu em 10s")
        return False

    # Clicar no botao
    page.evaluate(f"""() => {{
        const bloco = document.querySelector('[data-id="{block_id}"]');
        const buttons = bloco.querySelectorAll('button');
        for (const b of buttons) {{
            if (b.textContent.trim().includes('Adicionar texto')) {{
                const rect = b.getBoundingClientRect();
                b.dispatchEvent(new MouseEvent('click', {{
                    bubbles: true, clientX: rect.x + rect.width/2, clientY: rect.y + rect.height/2
                }}));
                return;
            }}
        }}
    }}""")
    page.wait_for_timeout(2000)

    # Esperar tiptap aparecer (max 5s)
    for wait in range(5):
        found = page.evaluate(f"""() => {{
            const bloco = document.querySelector('[data-id="{block_id}"]');
            if (!bloco) return false;
            const tiptap = bloco.querySelector('.tiptap, .ProseMirror, [contenteditable="true"]');
            if (!tiptap) return false;
            tiptap.focus();
            return true;
        }}""")
        if found:
            page.wait_for_timeout(300)
            return True
        page.wait_for_timeout(1000)

    logger.error("Tiptap nao apareceu em 5s")
    return False


def _get_prompt_count(page: Page, block_id: str) -> int:
    """Retorna quantos prompts estao colados no bloco."""
    return page.evaluate(f"""() => {{
        const el = document.querySelector('[data-id="{block_id}"]');
        const m = el ? el.textContent.match(/(\\d+)\\s*textos?/) : null;
        return m ? parseInt(m[1]) : 0;
    }}""")


def _colar_todos(page: Page, block_id: str, prompts: list, wait_ms: int = 800):
    """Cola todos os prompts com insert_text + Enter. Re-foca tiptap antes de cada prompt."""
    if not _click_adicionar_texto(page, block_id):
        return False

    for i, prompt in enumerate(prompts):
        # Re-focar tiptap ANTES DE CADA prompt (Freepik tira o foco aleatoriamente)
        page.evaluate(f"""() => {{
            const bloco = document.querySelector('[data-id="{block_id}"]');
            if (bloco) {{
                const tiptap = bloco.querySelector('.tiptap, .ProseMirror, [contenteditable="true"]');
                if (tiptap) tiptap.focus();
            }}
        }}""")
        page.wait_for_timeout(200)

        page.keyboard.insert_text(prompt)
        page.wait_for_timeout(wait_ms)
        page.keyboard.press("Enter")
        page.wait_for_timeout(wait_ms)

    return True


def colar_prompts(page: Page, block_id: str, prompts: list, nome: str):
    """Cola prompts com retry 3x. Verifica count apos cada tentativa."""
    max_retries = 3

    for attempt in range(1, max_retries + 1):
        # Limpar se nao for a primeira tentativa
        if attempt > 1:
            logger.warning(f"{nome}: tentativa {attempt}/{max_retries}...")
            limpar_bloco(page, block_id, f"{nome} (retry {attempt})")
            page.wait_for_timeout(3000)  # Esperar mais pro botao "Adicionar texto" reaparecer

        # Colar
        success = _colar_todos(page, block_id, prompts, wait_ms=800 if attempt == 1 else 1000)
        if not success:
            logger.error(f"{nome}: tentativa {attempt} - botao/tiptap nao encontrado")
            page.wait_for_timeout(2000)
            continue

        # Verificar count
        page.wait_for_timeout(1000)
        count = _get_prompt_count(page, block_id)

        if count >= len(prompts):
            logger.info(f"{nome}: {count}/{len(prompts)} prompts colados (tentativa {attempt})")
            return

        logger.warning(f"{nome}: tentativa {attempt} colou {count}/{len(prompts)}")
        page.wait_for_timeout(2000)

    # Todas tentativas falharam
    final_count = _get_prompt_count(page, block_id)
    logger.error(f"{nome}: FALHOU apos {max_retries} tentativas ({final_count}/{len(prompts)})")


# === PASSO 4: NARRAÇÃO ===

def colar_narracao(page: Page, script_text: str):
    """Cola script no campo de narração via evaluate (bypass overlays)."""
    found = page.evaluate(f"""() => {{
        const bloco = document.querySelector('[data-id="{IDS["NARRACAO_TEXTO"]}"]');
        if (!bloco) return false;
        const tiptap = bloco.querySelector('.tiptap, .ProseMirror, [contenteditable="true"]');
        if (!tiptap) return false;
        tiptap.focus();
        return true;
    }}""")
    if found:
        page.wait_for_timeout(300)
        page.keyboard.insert_text(script_text)
        page.wait_for_timeout(500)
        logger.info(f"NARRACAO: script colado ({len(script_text)} chars)")
    else:
        logger.error("NARRACAO: campo tiptap não encontrado")


LINGUA_FILTRO = {
    "Português": "Português", "Portugues": "Português",
    "Inglês": "Inglês", "Ingles": "Inglês",
    "Espanhol": "Espanhol", "Francês": "Francês", "Frances": "Francês",
    "Italiano": "Italiano", "Russo": "Russo",
    "Japonês": "Japonês", "Japones": "Japonês",
    "Coreano": "Coreano", "Turco": "Turco",
    "Polonês": "Polonês", "Polones": "Polonês",
    "Alemão": "Alemão", "Alemao": "Alemão",
}


def selecionar_voz(page: Page, lingua: str, log_callback=None):
    """Seleciona voz correta: clica narracao -> clica voz -> filtro lingua -> seleciona voz."""
    voz_alvo = VOZES.get(lingua, "Lucas Moreira")
    filtro_lingua = LINGUA_FILTRO.get(lingua, "Português")

    def log(msg):
        logger.info(msg)
        if log_callback:
            log_callback(msg)

    # 1. Clicar no bloco de narracao pra ativar toolbar
    _select_bloco(page, IDS["NARRACAO_TEXTO"])
    page.wait_for_timeout(1000)

    # 2. Verificar voz atual (botao dentro do bloco narracao, sem ElevenLabs/numeros)
    voz_atual = page.evaluate(f"""() => {{
        const narracao = document.querySelector('[data-id="{IDS["NARRACAO_TEXTO"]}"]');
        if (!narracao) return null;
        const btns = narracao.querySelectorAll('button');
        for (const b of btns) {{
            const text = b.textContent.trim();
            if (b.offsetParent !== null && text.length > 3 && !text.includes('ElevenLabs') && !/^[\\d:x]/.test(text)) {{
                return text;
            }}
        }}
        return null;
    }}""")

    log(f"VOZ atual: {voz_atual}")
    if voz_atual == voz_alvo:
        log(f"VOZ: ja e {voz_alvo}, pulando")
        return

    # 3. Clicar no botao da voz atual pra abrir seletor de vozes
    page.evaluate(f"""() => {{
        const narracao = document.querySelector('[data-id="{IDS["NARRACAO_TEXTO"]}"]');
        if (!narracao) return;
        const btns = narracao.querySelectorAll('button');
        for (const b of btns) {{
            const text = b.textContent.trim();
            if (b.offsetParent !== null && text.length > 3 && !text.includes('ElevenLabs') && !/^[\\d:x]/.test(text)) {{
                b.dispatchEvent(new MouseEvent('click', {{bubbles: true}}));
                return;
            }}
        }}
    }}""")
    page.wait_for_timeout(2000)

    # 4. Clicar no filtro de lingua (botao com bandeira, texto curto, no topo do popup)
    langs_list = ['Português', 'Inglês', 'Espanhol', 'Francês', 'Italiano', 'Alemão', 'Russo', 'Japonês', 'Coreano', 'Turco', 'Polonês']
    page.evaluate(f"""() => {{
        const langs = {langs_list};
        const btns = document.querySelectorAll('button');
        for (const b of btns) {{
            const text = b.textContent.trim();
            if (b.offsetParent !== null && text.length < 20 && langs.some(l => text.includes(l))) {{
                b.dispatchEvent(new MouseEvent('click', {{bubbles: true}}));
                return;
            }}
        }}
    }}""")
    page.wait_for_timeout(1500)

    # 5. Selecionar a lingua alvo no dropdown (texto exato ou com bandeira)
    page.evaluate(f"""() => {{
        const all = document.querySelectorAll('*');
        for (const el of all) {{
            if (el.offsetParent !== null) {{
                const text = el.textContent.trim();
                if ((text === '{filtro_lingua}' || text.endsWith('{filtro_lingua}')) && text.length < 25) {{
                    const rect = el.getBoundingClientRect();
                    if (rect.height > 15 && rect.height < 50) {{
                        el.click();
                        return;
                    }}
                }}
            }}
        }}
    }}""")
    page.wait_for_timeout(2000)
    log(f"VOZ: filtro trocado pra {filtro_lingua}")

    # 6. Selecionar a voz alvo (texto exato via h2 ou locator)
    loc = page.locator(f'h2:has-text("{voz_alvo}")')
    if loc.count() > 0:
        loc.first.click()
        page.wait_for_timeout(1500)
        log(f"VOZ: selecionada {voz_alvo}")
    else:
        # Fallback: locator texto exato
        loc2 = page.locator(f'text="{voz_alvo}"')
        if loc2.count() > 0:
            loc2.first.click()
            page.wait_for_timeout(1500)
            log(f"VOZ: selecionada {voz_alvo} (fallback)")
        else:
            log(f"VOZ: ERRO - {voz_alvo} nao encontrada na lista")

    page.keyboard.press("Escape")
    page.wait_for_timeout(500)


# === PASSO 5: VERIFICAR GERADOR ===

def verificar_gerador(page: Page):
    """Reseta quantidade do gerador de imagem pra 1 (+1 -1).
    Botões são minúsculos (0x0px), precisa force=True ou JS click."""
    clicked = page.evaluate("""() => {
        const btns = document.querySelectorAll('button');
        let plus = null, minus = null;
        for (const b of btns) {
            const aria = b.getAttribute('aria-label') || '';
            if (aria.includes('Increase')) plus = b;
            if (aria.includes('Decrease')) minus = b;
        }
        if (plus && minus) { plus.click(); minus.click(); return true; }
        return false;
    }""")
    if clicked:
        page.wait_for_timeout(300)
        logger.info("GERADOR: resetado pra 1")
    else:
        logger.info("GERADOR: botões +/- não encontrados")


# === PASSO 6: EXECUTAR WORKFLOW ===

def executar_workflow(page: Page):
    """Executa via 'Iniciar a partir daqui' (NUNCA 'Todo o fluxo')."""
    # Selecionar bloco de prompts de imagem
    _select_bloco(page, IDS["PROMPTS_IMAGEM"])

    # Clicar "Iniciar a partir daqui"
    page.evaluate("""() => {
        const btns = document.querySelectorAll('button');
        for (const b of btns) {
            if (b.getAttribute('aria-label') === 'Iniciar a partir daqui') { b.click(); return; }
        }
    }""")
    page.wait_for_timeout(3000)

    # Aceitar dialog se aparecer
    aceitar = page.locator("text=Aceitar")
    if aceitar.count() > 0:
        aceitar.first.click(force=True)
        page.wait_for_timeout(2000)
        logger.info("WORKFLOW: ACEITO E EXECUTANDO")
    else:
        logger.info("WORKFLOW: executou direto")


# === PASSO 7: GERAR NARRAÇÃO ===

def gerar_narracao(page: Page):
    """Gera narração via 'Esse nó somente'."""
    _select_bloco(page, IDS["NARRACAO_TEXTO"])
    page.wait_for_timeout(1000)

    clicked = page.evaluate("""() => {
        const btns = document.querySelectorAll('button');
        for (const b of btns) {
            const aria = b.getAttribute('aria-label') || '';
            if (aria.includes('somente') && b.offsetParent !== null) { b.click(); return true; }
        }
        return false;
    }""")

    if clicked:
        logger.info("NARRACAO: GERANDO")
    else:
        logger.warning("NARRACAO: botão 'Esse nó somente' não encontrado")


# === PASSO 8: VERIFICAR STATUS ===

def verificar_status(page: Page) -> dict:
    """Verifica quantos assets foram gerados."""
    result = page.evaluate(f"""() => {{
        const getCount = (id, regex) => {{
            const el = document.querySelector('[data-id="' + id + '"]');
            if (!el) return 0;
            const m = el.textContent.trim().match(regex);
            return m ? parseInt(m[1]) : 0;
        }};

        const imgCount = getCount("{IDS['LISTA_IMAGENS']}", /(\\d+)\\s*imagens?/);
        const vidCount = getCount("{IDS['LISTA_VIDEOS']}", /(\\d+)\\s*v[ií]deos?/);

        const narEl = document.querySelector('[data-id="{IDS["NARRACAO_TEXTO"]}"]');
        const narText = narEl ? narEl.textContent.trim() : '';
        const narReady = narText.includes('00:') && !narText.includes('fila');

        return {{ imagens: imgCount, videos: vidCount, narracao: narReady }};
    }}""")
    return result


# === PASSO 9: BAIXAR ===

def baixar_bloco(page: Page, data_id: str, nome: str, dest_dir: str):
    """Baixa assets via right-click → 'Baixar'. Salva ZIP na pasta destino."""
    _right_click_bloco(page, data_id)

    baixar = page.locator("text=Baixar")
    if baixar.count() > 0:
        with page.expect_download(timeout=30000) as download_info:
            baixar.first.click(force=True)
        download = download_info.value
        save_path = os.path.join(dest_dir, f"{nome.lower()}.zip")
        download.save_as(save_path)
        logger.info(f"{nome}: DOWNLOAD OK → {save_path}")
    else:
        logger.warning(f"{nome}: 'Baixar' não encontrado no menu")


# === PASSO 10: ORGANIZAR DOWNLOADS ===

def _limpar_artifacts():
    """Remove diretórios inteiros de artifacts do Playwright."""
    artifacts_dirs = glob.glob(os.path.expanduser("~/AppData/Local/Temp/playwright-artifacts-*"))
    for d in artifacts_dirs:
        shutil.rmtree(d, ignore_errors=True)
    if artifacts_dirs:
        logger.info(f"Artifacts removidos: {len(artifacts_dirs)} dirs")


def organizar_downloads(dest_path: str):
    """Descompacta ZIPs baixados e organiza na pasta."""
    os.makedirs(os.path.join(dest_path, "img"), exist_ok=True)
    os.makedirs(os.path.join(dest_path, "clips"), exist_ok=True)

    # Ler ZIPs salvos pelo expect_download na pasta destino
    all_files = sorted(glob.glob(os.path.join(dest_path, "*.zip")), key=os.path.getmtime)
    if not all_files:
        logger.warning("Nenhum ZIP encontrado na pasta destino")
        return

    for z in all_files:
        try:
            with zipfile.ZipFile(z, "r") as zf:
                for name in zf.namelist():
                    if name.endswith(".png"):
                        zf.extract(name, os.path.join(dest_path, "img"))
                    elif name.endswith(".mp4"):
                        zf.extract(name, os.path.join(dest_path, "clips"))
                    elif name.endswith(".mp3") or name.endswith(".wav"):
                        zf.extract(name, dest_path)
        except zipfile.BadZipFile:
            continue

    # Dedup por MD5
    def _dedup(folder, ext):
        files = sorted(glob.glob(os.path.join(folder, f"*{ext}")))
        seen = {}
        for f in files:
            h = hashlib.md5(open(f, "rb").read()).hexdigest()
            if h in seen:
                os.remove(f)
            else:
                seen[h] = f

    _dedup(os.path.join(dest_path, "img"), ".png")
    _dedup(os.path.join(dest_path, "clips"), ".mp4")

    # Dedup audio — manter o maior
    audios = glob.glob(os.path.join(dest_path, "*.mp3")) + glob.glob(os.path.join(dest_path, "*.wav"))
    if len(audios) > 1:
        audios.sort(key=os.path.getsize, reverse=True)
        for a in audios[1:]:
            os.remove(a)

    # Renomear baseado em matching de filename contra prompts do producao.json
    producao_json = os.path.join(dest_path, "producao.json")
    prompts_img = []
    prompts_anim = []
    if os.path.exists(producao_json):
        with open(producao_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        prompts_img = [c["prompt_imagem"] for c in data.get("cenas", [])]
        prompts_anim = [c["prompt_animacao"] for c in data.get("cenas", [])]

    # Clips: ordenar por ID numerico do Freepik (100% seguro)
    # IDs sao sequenciais pq colamos prompts na ordem 1-14
    # Menor ID = cena 1, maior ID = cena 14
    import re as _re

    def _extract_freepik_id(filepath):
        name = os.path.basename(filepath)
        m = _re.search(r'_(\d{4,})\.', name)
        return int(m.group(1)) if m else 0

    clip_files = glob.glob(os.path.join(dest_path, "clips", "*.mp4"))
    if clip_files:
        clip_files.sort(key=_extract_freepik_id)
        for i, f in enumerate(clip_files):
            os.rename(f, os.path.join(dest_path, "clips", f"tmp_{i + 1:02d}.mp4"))
        for i in range(1, len(clip_files) + 1):
            os.rename(
                os.path.join(dest_path, "clips", f"tmp_{i:02d}.mp4"),
                os.path.join(dest_path, "clips", f"cena_{i:02d}.mp4"),
            )
        logger.info(f"clips: {len(clip_files)} arquivos ordenados por ID Freepik")

    # Imagens: apenas renomear sequencial (backup, ordem nao importa)
    img_files = sorted(glob.glob(os.path.join(dest_path, "img", "*.png")))
    for i, f in enumerate(img_files):
        os.rename(f, os.path.join(dest_path, "img", f"tmp_{i + 1:02d}.png"))
    for i in range(1, len(img_files) + 1):
        os.rename(
            os.path.join(dest_path, "img", f"tmp_{i:02d}.png"),
            os.path.join(dest_path, "img", f"cena_{i:02d}.png"),
        )

    # Renomear narração
    narr = glob.glob(os.path.join(dest_path, "*.mp3")) + glob.glob(os.path.join(dest_path, "*.wav"))
    target = os.path.join(dest_path, "narracao.mp3")
    if narr and narr[0] != target:
        if os.path.exists(target):
            os.remove(target)
        os.rename(narr[0], target)

    n_imgs = len(glob.glob(os.path.join(dest_path, "img", "cena_*.png")))
    n_clips = len(glob.glob(os.path.join(dest_path, "clips", "cena_*.mp4")))
    logger.info(f"Organizado: {n_imgs} imagens, {n_clips} clips")

    if n_imgs < 14 or n_clips < 14:
        logger.warning(f"ATENÇÃO: faltam assets! ({n_imgs} imgs, {n_clips} clips)")


# === PIPELINE COMPLETO ===

def run_freepik_production(producao_json_path: str, log_callback: Optional[Callable] = None) -> bool:
    """
    Executa produção completa no Freepik Spaces via Playwright.

    Args:
        producao_json_path: Caminho pro producao.json gerado pelo pipeline.
        log_callback: Função opcional (msg: str) chamada a cada passo pra logs em tempo real.
    """
    def log(msg: str):
        logger.info(msg)
        if log_callback:
            log_callback(msg)

    with open(producao_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    dest_path = os.path.dirname(producao_json_path)
    lingua = data.get("lingua", "Português")
    prompts_img = [c["prompt_imagem"] for c in data["cenas"]]
    prompts_anim = [c["prompt_animacao"] for c in data["cenas"]]
    script_text = data["script"]

    log(f"=== INICIANDO PRODUÇÃO: {data['titulo']} ===")
    log(f"Canal: {data['canal']} | Língua: {lingua} | {len(prompts_img)} cenas")

    _limpar_artifacts()

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        page = _get_page(browser)

        # 1. LIMPAR
        log("PASSO 1: Limpando listas...")
        limpar_bloco(page, IDS["PROMPTS_IMAGEM"], "PROMPTS IMAGEM")
        limpar_bloco(page, IDS["PROMPTS_ANIMACAO"], "PROMPTS ANIMACAO")
        limpar_bloco(page, IDS["LISTA_IMAGENS"], "LISTA IMAGENS")
        limpar_bloco(page, IDS["LISTA_VIDEOS"], "LISTA VIDEOS")
        limpar_narracao(page)

        # 2. COLAR PROMPTS IMAGEM
        log("PASSO 2: Colando prompts de imagem...")
        colar_prompts(page, IDS["PROMPTS_IMAGEM"], prompts_img, "PROMPTS IMAGEM")

        # 3. COLAR PROMPTS ANIMAÇÃO
        log("PASSO 3: Colando prompts de animação...")
        colar_prompts(page, IDS["PROMPTS_ANIMACAO"], prompts_anim, "PROMPTS ANIMACAO")

        # 4. NARRAÇÃO + VOZ
        log("PASSO 4: Colando script na narração...")
        colar_narracao(page, script_text)

        log("PASSO 4b: Selecionando voz...")
        selecionar_voz(page, lingua, log_callback=log)

        # 5. Verificar se prompts foram colados corretamente
        img_count = page.evaluate(f"""() => {{
            const el = document.querySelector('[data-id="{IDS["PROMPTS_IMAGEM"]}"]');
            const m = el ? el.textContent.match(/(\\d+)\\s*textos?/) : null;
            return m ? parseInt(m[1]) : 0;
        }}""")
        anim_count = page.evaluate(f"""() => {{
            const el = document.querySelector('[data-id="{IDS["PROMPTS_ANIMACAO"]}"]');
            const m = el ? el.textContent.match(/(\\d+)\\s*textos?/) : null;
            return m ? parseInt(m[1]) : 0;
        }}""")
        log(f"Verificação: {img_count} prompts img, {anim_count} prompts anim")

        if img_count < 14 or anim_count < 14:
            log(f"ERRO: prompts incompletos ({img_count} img, {anim_count} anim). Abortando.")
            browser.close()
            return False

        # 6. EXECUTAR WORKFLOW
        log("PASSO 6: Executando workflow (Iniciar a partir daqui)...")
        executar_workflow(page)

        # 7. GERAR NARRAÇÃO
        log("PASSO 7: Gerando narração (Esse nó somente)...")
        gerar_narracao(page)

        # 8. AGUARDAR
        log("PASSO 8: Aguardando geração (~15 min)...")
        start = time.time()
        timeout = 25 * 60

        # Check inicial 2 min
        time.sleep(120)
        status = verificar_status(page)
        log(f"Check 2min: {status['imagens']} imgs, {status['videos']} vids, nar={status['narracao']}")

        if status["imagens"] > 16:
            log(f"BUG: {status['imagens']} imagens (duplicadas). Precisa correção manual.")
            browser.close()
            return False

        # Polling a cada 30s
        while time.time() - start < timeout:
            status = verificar_status(page)
            log(f"Status: {status['imagens']} imgs, {status['videos']} vids, nar={status['narracao']}")

            if status["imagens"] >= 14 and status["videos"] >= 14 and status["narracao"]:
                log("16+16+nar OK. Esperando 4 min pra confirmar renderizacao...")
                time.sleep(240)
                status2 = verificar_status(page)
                if status2["imagens"] >= 14 and status2["videos"] >= 14 and status2["narracao"]:
                    log("TUDO PRONTO!")
                    break
                log("Ainda processando...")

            time.sleep(30)
        else:
            log("TIMEOUT: produção não finalizou em 25 min")
            browser.close()
            return False

        # 9. BAIXAR
        log("PASSO 9: Baixando assets...")
        _limpar_artifacts()  # Limpar antes de baixar

        log("Baixando imagens...")
        baixar_bloco(page, IDS["LISTA_IMAGENS"], "IMAGENS", dest_path)

        log("Baixando vídeos...")
        baixar_bloco(page, IDS["LISTA_VIDEOS"], "VIDEOS", dest_path)

        log("Baixando narração...")
        baixar_bloco(page, IDS["WRAPPER_NARRACAO"], "NARRACAO", dest_path)

        browser.close()

    # 10. ORGANIZAR
    log("PASSO 10: Organizando downloads...")
    organizar_downloads(dest_path)

    n_imgs = len(glob.glob(os.path.join(dest_path, "img", "cena_*.png")))
    n_clips = len(glob.glob(os.path.join(dest_path, "clips", "cena_*.mp4")))
    has_audio = os.path.exists(os.path.join(dest_path, "narracao.mp3"))

    log(f"Resultado: {n_imgs} imgs, {n_clips} clips, audio={'OK' if has_audio else 'FALTANDO'}")
    log(f"=== PRODUÇÃO COMPLETA: {data['titulo']} ===")

    return n_imgs >= 13 and n_clips >= 13 and has_audio


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    if len(sys.argv) < 2:
        print("Uso: python freepik_automation.py <caminho/producao.json>")
        sys.exit(1)

    success = run_freepik_production(sys.argv[1])
    sys.exit(0 if success else 1)

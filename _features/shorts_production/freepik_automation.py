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
    "Inglês": "Caleb Morgan",
    "Espanhol": "Diego Marín",
    "Francês": "Diego Marín",
    "Italiano": "Giulio Ferrante",
    "Russo": "Léo Gamier",
    "Japonês": "Giulio Ferrante",
    "Coreano": "Ji-Hoon",
    "Turco": "Can Özkan",
    "Polonês": "Diego Marín",
    "Alemão": "Lukas Schneider",
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
    """Clica em 'Adicionar texto' e foca no tiptap. Usa dispatchEvent (imune a zoom)."""
    result = page.evaluate(f"""() => {{
        const bloco = document.querySelector('[data-id="{block_id}"]');
        if (!bloco) return 'no_block';
        const buttons = bloco.querySelectorAll('button');
        let btn = null;
        for (const b of buttons) {{
            if (b.textContent.trim().includes('Adicionar texto')) {{ btn = b; break; }}
        }}
        if (!btn) return 'no_button';
        // Click via dispatchEvent (imune a zoom/scroll)
        const rect = btn.getBoundingClientRect();
        btn.dispatchEvent(new MouseEvent('click', {{
            bubbles: true, clientX: rect.x + rect.width/2, clientY: rect.y + rect.height/2
        }}));
        return 'ok';
    }}""")

    if result != 'ok':
        logger.error(f"Adicionar texto: {result}")
        return False

    page.wait_for_timeout(2000)

    # Focar no tiptap via focus() (sem coordenadas)
    found = page.evaluate(f"""() => {{
        const bloco = document.querySelector('[data-id="{block_id}"]');
        if (!bloco) return false;
        const tiptap = bloco.querySelector('.tiptap, .ProseMirror, [contenteditable="true"]');
        if (!tiptap) return false;
        tiptap.focus();
        return true;
    }}""")
    if not found:
        logger.error("Tiptap nao encontrado")
        return False

    page.wait_for_timeout(300)
    return True


def colar_prompts(page: Page, block_id: str, prompts: list, nome: str):
    """Cola prompts num bloco. Usa mouse.click pra 'Adicionar texto' (mais confiável)."""
    if not _click_adicionar_texto(page, block_id):
        logger.error(f"{nome}: botao 'Adicionar texto' ou tiptap nao encontrado")
        return

    # Colar cada prompt + Enter (incluindo após o último)
    for i, prompt in enumerate(prompts):
        page.keyboard.insert_text(prompt)
        page.wait_for_timeout(400)
        page.keyboard.press("Enter")
        page.wait_for_timeout(400)

    # Verificar se colou todos
    count = page.evaluate(f"""() => {{
        const el = document.querySelector('[data-id="{block_id}"]');
        const m = el ? el.textContent.match(/(\\d+)\\s*textos?/) : null;
        return m ? parseInt(m[1]) : 0;
    }}""")

    if count < len(prompts):
        logger.warning(f"{nome}: colou {count}/{len(prompts)}, re-tentando...")
        # Limpar e recolar tudo
        limpar_bloco(page, block_id, f"{nome} (retry)")
        page.wait_for_timeout(1000)

        if not _click_adicionar_texto(page, block_id):
            logger.error(f"{nome}: retry falhou - botao/tiptap nao encontrado")
            return

        # Re-colar todos com wait maior
        for prompt in prompts:
            page.keyboard.insert_text(prompt)
            page.wait_for_timeout(600)
            page.keyboard.press("Enter")
            page.wait_for_timeout(600)

        count = page.evaluate(f"""() => {{
            const el = document.querySelector('[data-id="{block_id}"]');
            const m = el ? el.textContent.match(/(\\d+)\\s*textos?/) : null;
            return m ? parseInt(m[1]) : 0;
        }}""")

    logger.info(f"{nome}: {count}/{len(prompts)} prompts colados")


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


def selecionar_voz(page: Page, lingua: str):
    """Seleciona voz correta para a língua."""
    voz_alvo = VOZES.get(lingua, "Lucas Moreira")

    # Selecionar bloco da narração pra ativar toolbar
    _select_bloco(page, IDS["NARRACAO_TEXTO"])
    page.wait_for_timeout(1000)

    # Encontrar botão com nome de pessoa (voz atual)
    voice_btn = page.evaluate("""() => {
        const btns = document.querySelectorAll('button');
        for (const b of btns) {
            const text = b.textContent.trim();
            if (b.offsetParent !== null && /^[A-Z][a-záéíóú]+ [A-Z]/.test(text) && text.length < 30) {
                if (!text.includes('ElevenLabs') && !text.includes('Adicionar') && !text.includes('Manter')) {
                    const rect = b.getBoundingClientRect();
                    return { x: rect.x + rect.width / 2, y: rect.y + rect.height / 2, text };
                }
            }
        }
        return null;
    }""")

    if not voice_btn:
        logger.warning("VOZ: botão de voz não encontrado")
        return

    logger.info(f"VOZ atual: {voice_btn['text']}")
    if voice_btn["text"] == voz_alvo:
        logger.info(f"VOZ: já é {voz_alvo}, pulando")
        return

    # Abrir seletor de vozes via dispatchEvent (imune a zoom)
    page.evaluate(f"""() => {{
        const btns = document.querySelectorAll('button');
        for (const b of btns) {{
            const text = b.textContent.trim();
            if (b.offsetParent !== null && /^[A-Z][a-záéíóú]+ [A-Z]/.test(text) && text.length < 30) {{
                if (!text.includes('ElevenLabs') && !text.includes('Adicionar') && !text.includes('Manter')) {{
                    b.click();
                    return;
                }}
            }}
        }}
    }}""")
    page.wait_for_timeout(3000)

    # Clicar na voz alvo
    target = page.locator(f"text={voz_alvo}")
    if target.count() > 0:
        target.first.click()
        page.wait_for_timeout(2000)
        logger.info(f"VOZ: selecionada {voz_alvo}")
    else:
        logger.warning(f"VOZ: {voz_alvo} não encontrada na lista")

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
        selecionar_voz(page, lingua)

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

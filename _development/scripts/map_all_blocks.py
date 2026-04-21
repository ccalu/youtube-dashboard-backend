"""Mapeia TODOS os blocos top-level do Freepik Space atual."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

sys.path.insert(0, r"C:\Users\PC\Desktop\ContentFactory\youtube-dashboard-backend")
from _features.shorts_production.freepik_automation import _get_page

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    page = _get_page(browser)

    # TODOS os blocos top-level do vue-flow + seus pais/filhos
    all_blocks = page.evaluate("""() => {
        const blocks = document.querySelectorAll('[data-id]');
        const result = [];
        blocks.forEach(b => {
            if (!b.classList.contains('vue-flow__node')) return;
            const rect = b.getBoundingClientRect();
            result.push({
                dataId: b.getAttribute('data-id'),
                text: b.innerText.slice(0, 120).replace(/\\n/g, ' | '),
                hasTiptap: b.querySelectorAll('.tiptap, .ProseMirror, [contenteditable="true"]').length > 0,
                hasAudio: !!b.querySelector('audio, [class*="audio"], [class*="waveform"]'),
                x: Math.round(rect.x),
                y: Math.round(rect.y),
            });
        });
        return result;
    }""")

    print(f"Total de blocos top-level vue-flow: {len(all_blocks)}\n")
    print(f"{'data-id':<40} {'tiptap':<7} {'audio':<6} {'x/y':<12} {'preview'}")
    print("-" * 120)
    for b in sorted(all_blocks, key=lambda x: (x['y'], x['x'])):
        did = b['dataId']
        pos = f"{b['x']}/{b['y']}"
        preview = b['text'][:70]
        print(f"{did:<40} {str(b['hasTiptap']):<7} {str(b['hasAudio']):<6} {pos:<12} {preview}")

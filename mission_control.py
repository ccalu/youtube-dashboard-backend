"""
Mission Control - Escritorio Virtual estilo Gather.town
Canvas 2D com sprites pixelados, tiles, mobilia e agentes animados.

Cada subnicho = 1 aba/setor com tema visual unico
Cada canal = 1 sala com 6 agentes bonequinhos
Agentes se comunicam apenas dentro da propria sala
"""

import random
import time
import unicodedata
from datetime import datetime, timezone

# ===========================================================
# MAPEAMENTOS
# ===========================================================

BANDEIRAS_MAP = {
    'portugues': 'BR', 'português': 'BR', 'portuguese': 'BR', 'pt': 'BR',
    'ingles': 'GB', 'inglês': 'GB', 'english': 'GB', 'en': 'GB',
    'espanhol': 'ES', 'spanish': 'ES', 'es': 'ES',
    'frances': 'FR', 'francês': 'FR', 'french': 'FR', 'fr': 'FR',
    'alemao': 'DE', 'alemão': 'DE', 'german': 'DE', 'de': 'DE',
    'italiano': 'IT', 'italian': 'IT', 'it': 'IT',
    'japones': 'JP', 'japonês': 'JP', 'japanese': 'JP', 'ja': 'JP',
    'coreano': 'KR', 'korean': 'KR', 'ko': 'KR',
    'russo': 'RU', 'russian': 'RU', 'ru': 'RU',
    'turco': 'TR', 'turkish': 'TR', 'tr': 'TR',
    'arabe': 'SA', 'árabe': 'SA', 'arabic': 'SA', 'ar': 'SA',
    'polones': 'PL', 'polonês': 'PL', 'polish': 'PL', 'pl': 'PL',
    'hindi': 'IN',
}

SETORES_CONFIG = {
    'Monetizados': {'cor': '#22c55e', 'icone': '$', 'tema': 'executive',
                    'floor': '#2d4a2d', 'wall': '#1a3a1a', 'accent': '#4ade80'},
    'Historias Sombrias': {'cor': '#8b5cf6', 'icone': 'H', 'tema': 'gothic',
                           'floor': '#2d2a4a', 'wall': '#1a1a3a', 'accent': '#a78bfa'},
    'Relatos de Guerra': {'cor': '#4a8c50', 'icone': 'G', 'tema': 'warroom',
                          'floor': '#2d3a2d', 'wall': '#1a2a1a', 'accent': '#6ee77a'},
    'Terror': {'cor': '#ef4444', 'icone': 'T', 'tema': 'darklab',
               'floor': '#4a2d2d', 'wall': '#3a1a1a', 'accent': '#f87171'},
    'Guerras e Civilizacoes': {'cor': '#f97316', 'icone': 'C', 'tema': 'command',
                               'floor': '#4a3a2d', 'wall': '#3a2a1a', 'accent': '#fb923c'},
    'Guerras e Civilizações': {'cor': '#f97316', 'icone': 'C', 'tema': 'command',
                                'floor': '#4a3a2d', 'wall': '#3a2a1a', 'accent': '#fb923c'},
    'Desmonetizados': {'cor': '#ef4444', 'icone': 'D', 'tema': 'demonetized',
                       'floor': '#3a1818', 'wall': '#2a1010', 'accent': '#f87171'},
    'Lições de Vida': {'cor': '#eab308', 'icone': 'L', 'tema': 'wisdom',
                       'floor': '#3a3418', 'wall': '#2a2410', 'accent': '#fbbf24'},
}

AGENTES_TEMPLATE = [
    {'tipo': 'copy_analyst', 'nome': 'Copy Bot', 'cor': '#3b82f6',
     'skin': '#ffcc99', 'shirt': '#3b82f6', 'hair': '#4a3728'},
    {'tipo': 'title_architect', 'nome': 'Title Bot', 'cor': '#22c55e',
     'skin': '#e8b88a', 'shirt': '#22c55e', 'hair': '#1a1a1a'},
    {'tipo': 'trend_scanner', 'nome': 'Trend Bot', 'cor': '#f59e0b',
     'skin': '#ffcc99', 'shirt': '#f59e0b', 'hair': '#8b4513'},
    {'tipo': 'content_strategist', 'nome': 'Strategy Bot', 'cor': '#8b5cf6',
     'skin': '#d4a574', 'shirt': '#8b5cf6', 'hair': '#2c1810'},
    {'tipo': 'thumbnail_designer', 'nome': 'Thumb Bot', 'cor': '#ec4899',
     'skin': '#ffcc99', 'shirt': '#ec4899', 'hair': '#c0392b'},
    {'tipo': 'performance_analyst', 'nome': 'Perf Bot', 'cor': '#06b6d4',
     'skin': '#e8b88a', 'shirt': '#06b6d4', 'hair': '#34495e'},
]

STATUS_OPTIONS = ['working', 'idle', 'done', 'waiting', 'talking', 'error']
STATUS_WEIGHTS = [30, 20, 25, 10, 10, 5]

MENSAGENS_TEMPLATES = [
    ('Copy Bot', 'Title Bot', 'Analisei {n} titulos concorrentes'),
    ('Title Bot', 'Strategy Bot', 'Estrutura A+ em {n} titulos do nicho'),
    ('Trend Bot', 'Copy Bot', 'Trend detectado: {n} videos virais hoje'),
    ('Trend Bot', 'Strategy Bot', 'Oportunidade com baixa competicao'),
    ('Strategy Bot', 'Copy Bot', 'Preciso analise de copy urgente'),
    ('Perf Bot', 'Strategy Bot', 'Ultimo video: {n}K views, retencao {n2}%'),
    ('Thumb Bot', 'Perf Bot', 'Nova thumb: CTR estimado {n2}%'),
    ('Perf Bot', 'Trend Bot', 'Buscar trends do tema top'),
    ('Copy Bot', 'Thumb Bot', 'Hook visual identificado nos tops'),
    ('Strategy Bot', 'Trend Bot', 'Validar tendencia ainda ativa'),
]

TAREFAS_TEMPLATES = [
    ('Copy Bot', 'Analise de copy concorrentes', 'done', '45s'),
    ('Copy Bot', 'Mapeamento de hooks efetivos', 'done', '1m12s'),
    ('Title Bot', 'Geracao de 5 variacoes de titulo', 'working', None),
    ('Title Bot', 'Analise de padroes CTR', 'done', '38s'),
    ('Trend Bot', 'Scan tendencias 24h', 'done', '2m05s'),
    ('Trend Bot', 'Monitoramento concorrentes', 'working', None),
    ('Strategy Bot', 'Definicao pauta semanal', 'done', '1m30s'),
    ('Strategy Bot', 'Revisao estrategia conteudo', 'pending', None),
    ('Thumb Bot', 'Analise visual top 10 thumbs', 'done', '55s'),
    ('Thumb Bot', 'Geracao referencias visuais', 'working', None),
    ('Perf Bot', 'Relatorio performance semanal', 'done', '1m45s'),
    ('Perf Bot', 'Benchmark vs concorrentes', 'pending', None),
]


# ===========================================================
# HELPERS
# ===========================================================

def sanitize_id(text):
    nfkd = unicodedata.normalize('NFKD', text)
    ascii_only = nfkd.encode('ASCII', 'ignore').decode('ASCII')
    return ascii_only.lower().replace(' ', '_').replace('__', '_')


def get_lingua_code(lingua):
    if not lingua:
        return '??'
    l = lingua.lower().strip()
    return BANDEIRAS_MAP.get(l, lingua[:2].upper() if lingua else '??')


def gerar_agentes_mock(canal_id):
    random.seed(canal_id + int(time.time() // 120))
    agentes = []
    for i, t in enumerate(AGENTES_TEMPLATE):
        status = random.choices(STATUS_OPTIONS, weights=STATUS_WEIGHTS, k=1)[0]
        agentes.append({
            'id': i + 1,
            'tipo': t['tipo'],
            'nome': t['nome'],
            'cor': t['cor'],
            'skin': t['skin'],
            'shirt': t['shirt'],
            'hair': t['hair'],
            'status': status,
            'tarefas_hoje': random.randint(3, 18),
            'ultimo_trabalho': '{:02d}:{:02d}'.format(random.randint(8, 23), random.randint(0, 59)),
        })
    return agentes


def gerar_mensagens_mock(canal_id):
    random.seed(canal_id + int(time.time() // 60))
    msgs = []
    h = random.randint(8, 14)
    m = random.randint(0, 30)
    sel = random.sample(MENSAGENS_TEMPLATES, k=min(random.randint(5, 8), len(MENSAGENS_TEMPLATES)))
    for de, para, txt in sel:
        t = txt.replace('{n}', str(random.randint(3, 25))).replace('{n2}', str(random.randint(2, 15)))
        m += random.randint(1, 5)
        if m >= 60:
            h += 1
            m -= 60
        de_a = next((a for a in AGENTES_TEMPLATE if a['nome'] == de), AGENTES_TEMPLATE[0])
        msgs.append({'de': de, 'de_cor': de_a['cor'], 'para': para, 'texto': t,
                      'hora': '{:02d}:{:02d}'.format(h, m)})
    return sorted(msgs, key=lambda x: x['hora'])


def gerar_tarefas_mock(canal_id):
    random.seed(canal_id + int(time.time() // 45))
    tarefas = []
    h = random.randint(8, 12)
    m = random.randint(0, 20)
    sel = random.sample(TAREFAS_TEMPLATES, k=min(8, len(TAREFAS_TEMPLATES)))
    for agente, desc, status, dur in sel:
        m += random.randint(3, 12)
        if m >= 60:
            h += 1
            m -= 60
        a = next((x for x in AGENTES_TEMPLATE if x['nome'] == agente), AGENTES_TEMPLATE[0])
        tarefas.append({'desc': desc, 'agente': agente, 'agente_cor': a['cor'],
                        'status': status, 'duracao': dur,
                        'hora': '{:02d}:{:02d}'.format(h, m)})
    return tarefas


# ===========================================================
# API DATA FUNCTIONS
# ===========================================================

_mc_cache = {'data': None, 'timestamp': 0}
_MC_CACHE_TTL = 5

_mc_sala_cache = {}
_MC_SALA_CACHE_TTL = 3


async def get_mission_control_data(db):
    now = time.time()
    if _mc_cache['data'] and (now - _mc_cache['timestamp']) < _MC_CACHE_TTL:
        return _mc_cache['data']

    canais = await db.get_dashboard_from_mv(tipo="nosso", limit=1000, offset=0)
    grupos = {}
    for canal in canais:
        sub = canal.get('subnicho') or 'Sem Categoria'
        if sub not in grupos:
            grupos[sub] = []
        grupos[sub].append(canal)

    setores = []
    total_ag = 0
    total_wk = 0
    total_tf = 0

    for sub, clist in sorted(grupos.items()):
        cfg = SETORES_CONFIG.get(sub, {'cor': '#666', 'icone': '?', 'tema': 'startup',
                                        'floor': '#2d2d30', 'wall': '#1a1a1e', 'accent': '#888'})
        salas = []
        for c in clist:
            cid = c['id']
            ags = gerar_agentes_mock(cid)
            wk = sum(1 for a in ags if a['status'] == 'working')
            tf = sum(a['tarefas_hoje'] for a in ags)
            total_ag += len(ags)
            total_wk += wk
            total_tf += tf
            salas.append({
                'canal_id': cid,
                'nome': c.get('nome_canal', 'Canal'),
                'lingua': get_lingua_code(c.get('lingua')),
                'inscritos': c.get('inscritos', 0),
                'inscritos_diff': c.get('inscritos_diff'),
                'agentes': [{'nome': a['nome'], 'status': a['status'], 'cor': a['cor'],
                              'skin': a['skin'], 'shirt': a['shirt'], 'hair': a['hair']}
                             for a in ags],
                'tem_atividade': wk > 0,
            })
        setores.append({
            'id': sanitize_id(sub), 'nome': sub,
            'cor': cfg['cor'], 'icone': cfg['icone'], 'tema': cfg['tema'],
            'floor': cfg.get('floor', '#2d2d30'),
            'wall': cfg.get('wall', '#1a1a1e'),
            'accent': cfg.get('accent', '#888'),
            'salas': salas,
        })

    result = {
        'stats': {'total_salas': sum(len(s['salas']) for s in setores),
                  'total_agentes': total_ag, 'agentes_working': total_wk,
                  'tarefas_hoje': total_tf},
        'setores': setores,
    }
    _mc_cache['data'] = result
    _mc_cache['timestamp'] = now
    return result


async def get_sala_detail(db, canal_id):
    ck = 'sala_{}'.format(canal_id)
    now = time.time()
    if ck in _mc_sala_cache:
        cc = _mc_sala_cache[ck]
        if (now - cc['timestamp']) < _MC_SALA_CACHE_TTL:
            return cc['data']

    canais = await db.get_dashboard_from_mv(tipo="nosso", limit=1000, offset=0)
    canal = next((c for c in canais if c['id'] == canal_id), None)
    if not canal:
        return {'error': 'Canal nao encontrado'}

    result = {
        'canal': {
            'id': canal_id,
            'nome': canal.get('nome_canal', 'Canal'),
            'lingua': get_lingua_code(canal.get('lingua')),
            'inscritos': canal.get('inscritos', 0),
            'inscritos_diff': canal.get('inscritos_diff'),
            'total_videos': canal.get('total_videos', 0),
            'ultima_coleta': canal.get('ultima_coleta'),
            'subnicho': canal.get('subnicho', ''),
        },
        'agentes': gerar_agentes_mock(canal_id),
        'mensagens': gerar_mensagens_mock(canal_id),
        'tarefas': gerar_tarefas_mock(canal_id),
    }
    _mc_sala_cache[ck] = {'data': result, 'timestamp': now}
    return result



# ===========================================================
# HTML - Mission Control (Gather.town Professional v4)
# ===========================================================

MISSION_CONTROL_HTML = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect rx='20' width='100' height='100' fill='%23111'/><circle cx='50' cy='50' r='28' stroke='%2300ff88' stroke-width='5' fill='none'/><circle cx='50' cy='50' r='5' fill='%2300ff88'/><line x1='50' y1='50' x2='50' y2='28' stroke='%2300ff88' stroke-width='4' stroke-linecap='round'/><line x1='50' y1='50' x2='68' y2='50' stroke='%2300ff88' stroke-width='3' stroke-linecap='round'/></svg>">
<title>Mission Control</title>
<link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#08081a;color:#e0e0e0;font-family:'Segoe UI',system-ui,sans-serif;overflow:hidden;height:100vh;display:flex;flex-direction:column}
.hdr{background:linear-gradient(180deg,#14142e 0%,#0c0c1e 100%);padding:10px 24px;display:flex;align-items:center;justify-content:space-between;flex-shrink:0;border-bottom:2px solid #1a1a3a;position:relative}
.hdr::after{content:"";position:absolute;bottom:-1px;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,#d4a853 30%,#d4a853 70%,transparent)}
.hdr h1{font-family:'Press Start 2P',monospace;font-size:11px;color:#d4a853;letter-spacing:3px;text-shadow:0 0 20px rgba(212,168,83,.3),0 2px 4px rgba(0,0,0,.5)}
.hdr-stats{display:flex;gap:24px}
.hdr-stats .hs{text-align:center}
.hdr-stats .hs b{display:block;font-size:16px;color:#d4a853;font-weight:800}
.hdr-stats .hs small{font-size:9px;color:#666;text-transform:uppercase;letter-spacing:1px}
.tabs{display:flex;background:#06061a;border-bottom:2px solid #1a1a3a;overflow-x:auto;flex-shrink:0;gap:0;padding:0 8px}
.tabs::-webkit-scrollbar{height:0}
.tab{padding:12px 22px;font-size:13px;color:#556;cursor:pointer;border:0;background:0;border-bottom:3px solid transparent;font-weight:700;white-space:nowrap;transition:all .3s ease;font-family:inherit;display:flex;align-items:center;gap:8px}
.tab:hover{color:#aab;background:rgba(255,255,255,.02)}
.tab.act{color:#fff;border-bottom-color:var(--c);background:linear-gradient(180deg,rgba(255,255,255,.04),transparent);text-shadow:0 0 12px var(--c)}
.tab .badge{font-size:11px;background:rgba(255,255,255,.06);padding:3px 10px;border-radius:10px;font-weight:800}
.tab.act .badge{background:var(--c);color:#000}
.wrap{flex:1;display:flex;overflow:hidden;position:relative}
.map-wrap{flex:1;overflow:auto;background:#08081a;position:relative}
.map-wrap canvas{display:block;image-rendering:pixelated;image-rendering:crisp-edges;min-width:100%;min-height:100%}
.sb{width:420px;background:#0a0a22;border-left:2px solid #1a1a3a;display:none;flex-direction:column;flex-shrink:0;box-shadow:-8px 0 40px rgba(0,0,0,.4)}
.sb.open{display:flex}
.sb-top{padding:14px 18px;background:linear-gradient(180deg,#12122e,#0e0e24);border-bottom:2px solid #1a1a3a;display:flex;justify-content:space-between;align-items:center}
.sb-top h3{font-family:'Press Start 2P',monospace;font-size:8px;color:#d4a853;text-shadow:0 0 8px rgba(212,168,83,.2)}
.sb-x{background:rgba(255,255,255,.05);border:1px solid #2a2a50;color:#888;padding:6px 16px;cursor:pointer;border-radius:4px;font-size:11px;transition:.2s}
.sb-x:hover{background:rgba(255,255,255,.12);color:#fff;border-color:#444}
.sb-scroll{flex:1;overflow-y:auto}
.sb-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;padding:14px}
.sb-card{background:rgba(255,255,255,.025);border:1px solid rgba(255,255,255,.05);border-radius:8px;padding:10px;text-align:center;position:relative;transition:.2s}
.sb-card:hover{background:rgba(255,255,255,.05);border-color:rgba(255,255,255,.1)}
.sb-card .cn{font-size:12px;font-weight:700;color:var(--ac)}
.sb-card .cs{font-size:10px;color:#667;margin-top:3px}
.sb-card .ct{font-size:9px;color:#445;margin-top:2px}
.sb-card .cd{width:12px;height:12px;border-radius:50%;position:absolute;top:6px;right:6px;box-shadow:0 0 8px currentColor,0 0 16px currentColor}
.sb-sec{padding:14px;border-top:1px solid #1a1a35}
.sb-sec h4{font-family:'Press Start 2P',monospace;font-size:7px;color:#556;margin-bottom:12px;letter-spacing:1px}
.msg{margin-bottom:8px;padding:9px 12px;background:rgba(255,255,255,.02);border-radius:6px;border-left:3px solid var(--mc);transition:.15s}
.msg:hover{background:rgba(255,255,255,.04)}
.msg .mh{font-size:11px;color:#667;margin-bottom:4px}
.msg .mh b{color:var(--mc)}
.msg .mh .arr{color:#334;margin:0 4px;font-size:10px}
.msg .mt{font-size:12px;color:#99a;line-height:1.5;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.tsk{display:flex;gap:10px;padding:8px 0;border-bottom:1px solid rgba(255,255,255,.03);font-size:12px}
.tsk .ti{width:18px;text-align:center;font-size:14px}
.tsk .td{color:#aab;font-size:12px}
.tsk .tm{font-size:10px;color:#556;margin-top:2px}
.info-bar{padding:12px 18px;background:#06061a;border-top:2px solid #1a1a35;display:flex;gap:24px;flex-shrink:0}
.info-bar .ib{display:flex;flex-direction:column;gap:2px}
.info-bar .ib label{font-size:9px;color:#445;text-transform:uppercase;letter-spacing:1px}
.info-bar .ib span{font-size:14px;font-weight:700}
.info-bar .pos{color:#4ade80}
.info-bar .neg{color:#f87171}
.tip{position:absolute;background:rgba(6,6,20,.96);border:1px solid #2a2a50;border-radius:8px;padding:12px 16px;z-index:50;pointer-events:none;display:none;min-width:220px;box-shadow:0 12px 40px rgba(0,0,0,.6);backdrop-filter:blur(12px)}
.tip .tn{font-weight:800;font-size:14px;color:#fff;margin-bottom:8px;display:flex;align-items:center;gap:8px}
.tip .tf{font-size:16px}
.tip .tr{display:flex;justify-content:space-between;padding:3px 0;font-size:11px;color:#667}
.tip .tr b{color:#bbc}
.leg{position:absolute;bottom:12px;left:12px;background:rgba(6,6,20,.92);border:1px solid #2a2a50;border-radius:8px;padding:10px 16px;font-size:10px;color:#556;z-index:10;display:flex;gap:14px;backdrop-filter:blur(8px)}
.leg .li{display:flex;align-items:center;gap:5px}
.leg .dt{width:10px;height:10px;border-radius:50%;box-shadow:0 0 8px var(--dc)}
::-webkit-scrollbar{width:6px}::-webkit-scrollbar-track{background:transparent}::-webkit-scrollbar-thumb{background:#1a1a35;border-radius:3px}::-webkit-scrollbar-thumb:hover{background:#2a2a55}
</style>
</head>
<body>
<div class="hdr">
<h1>MISSION CONTROL</h1>
<div class="hdr-stats">
<div class="hs"><b id="s0">-</b><small>Salas</small></div>
<div class="hs"><b id="s1">-</b><small>Agentes</small></div>
<div class="hs"><b id="s2">-</b><small>Ativos</small></div>
<div class="hs"><b id="s3">-</b><small>Tarefas</small></div>
</div>
</div>
<div class="tabs" id="tabs"></div>
<div class="wrap">
<div class="map-wrap" id="mapWrap"><canvas id="cv"></canvas><div class="tip" id="tip"></div></div>
<div class="sb" id="sb">
<div class="sb-top"><h3 id="sbT">Sala</h3><button class="sb-x" id="sbX">FECHAR</button></div>
<div class="sb-scroll">
<div class="sb-grid" id="sbA"></div>
<div class="sb-sec" id="sbC"><h4>CHAT</h4></div>
<div class="sb-sec" id="sbK"><h4>TAREFAS</h4></div>
</div>
<div class="info-bar" id="sbI"></div>
</div>
<div class="leg">
<div class="li"><div class="dt" style="--dc:#4ade80;background:#4ade80"></div>Working</div>
<div class="li"><div class="dt" style="--dc:#60a5fa;background:#60a5fa"></div>Done</div>
<div class="li"><div class="dt" style="--dc:#fbbf24;background:#fbbf24"></div>Wait</div>
<div class="li"><div class="dt" style="--dc:#c084fc;background:#c084fc"></div>Talk</div>
<div class="li"><div class="dt" style="--dc:#888;background:#888"></div>Idle</div>
<div class="li"><div class="dt" style="--dc:#f87171;background:#f87171"></div>Error</div>
</div>
</div>

<script>
var T=32,D=null,curT=null,hR=null,fr=0,t0=performance.now(),agSt={};
var cv=document.getElementById("cv"),cx=cv.getContext("2d");
var tip=document.getElementById("tip");

// Flag emoji map
var FLAGS={BR:"\uD83C\uDDE7\uD83C\uDDF7",GB:"\uD83C\uDDEC\uD83C\uDDE7",ES:"\uD83C\uDDEA\uD83C\uDDF8",FR:"\uD83C\uDDEB\uD83C\uDDF7",DE:"\uD83C\uDDE9\uD83C\uDDEA",IT:"\uD83C\uDDEE\uD83C\uDDF9",JP:"\uD83C\uDDEF\uD83C\uDDF5",KR:"\uD83C\uDDF0\uD83C\uDDF7",RU:"\uD83C\uDDF7\uD83C\uDDFA",TR:"\uD83C\uDDF9\uD83C\uDDF7",SA:"\uD83C\uDDF8\uD83C\uDDE6",PL:"\uD83C\uDDF5\uD83C\uDDF1",IN:"\uD83C\uDDEE\uD83C\uDDF3"};
function getFlag(c){return FLAGS[c]||"\uD83C\uDFF3\uFE0F"}

// Color math
function h2r(h){var v=parseInt(h.slice(1),16);return[(v>>16)&255,(v>>8)&255,v&255]}
function r2h(r,g,b){return"#"+((1<<24)+(r<<16)+(g<<8)+b).toString(16).slice(1)}
function dk(h,a){var c=h2r(h);return r2h(Math.max(0,c[0]-a),Math.max(0,c[1]-a),Math.max(0,c[2]-a))}
function lt(h,a){var c=h2r(h);return r2h(Math.min(255,c[0]+a),Math.min(255,c[1]+a),Math.min(255,c[2]+a))}
function al(h,a){var c=h2r(h);return"rgba("+c[0]+","+c[1]+","+c[2]+","+a+")"}
function mkC(w,h){var c=document.createElement("canvas");c.width=w;c.height=h;return c}

// Smooth time-based value
function now(){return(performance.now()-t0)/1000}

// ============ THEME DEFINITIONS - Each sector is UNIQUE ============
var THEMES={
executive:{
  floorBase:"#283828",floorLight:"#2e4030",
  roomBase:"#344a34",roomLight:"#3a5638",
  wallFront:"#4a6848",wallTop:"#5a7a58",wallSide:"#3a5438",
  accent:"#4ade80",accentDark:"#22c55e",gold:"#d4a853",
  deskColor:"#7a5a3a",deskLight:"#8a6a4a",deskDark:"#5a4028",
  screenBg:"#0a2a0a",screenGlow:"#22c55e",screenLines:"#4ade80",
  chairColor:"#2a5a2a",
  pattern:"marble",particle:"#4ade80",
  // UNIQUE furniture set
  furniture:["desk_exec","desk_exec","desk_exec","bookshelf_wood","plant_palm","coffee_premium","globe","trophy_case"],
  wallArt:["gold_frame","stock_ticker","gold_clock","certificate"]
},
gothic:{
  floorBase:"#221e38",floorLight:"#282240",
  roomBase:"#2e2848",roomLight:"#342e52",
  wallFront:"#443668",wallTop:"#504070",wallSide:"#3a2e58",
  accent:"#a78bfa",accentDark:"#8b5cf6",gold:"#9a7ad4",
  deskColor:"#3a2848",deskLight:"#4a3858",deskDark:"#2a1838",
  screenBg:"#1a0a2a",screenGlow:"#8b5cf6",screenLines:"#a78bfa",
  chairColor:"#3a2050",
  pattern:"cobblestone",particle:"#c084fc",
  furniture:["desk_antique","desk_antique","desk_antique","bookshelf_dark","candelabra","skull_shelf","potion_shelf","cobweb_corner"],
  wallArt:["gothic_mirror","torch","painting_dark","bat_window"]
},
warroom:{
  floorBase:"#262e22",floorLight:"#2c3428",
  roomBase:"#323e2e",roomLight:"#384434",
  wallFront:"#4a5840",wallTop:"#566248",wallSide:"#3e4c36",
  accent:"#6ee77a",accentDark:"#4a8c50",gold:"#8aaa60",
  deskColor:"#5a6a40",deskLight:"#6a7a50",deskDark:"#4a5a30",
  screenBg:"#0a1a08",screenGlow:"#4ade80",screenLines:"#6ee77a",
  chairColor:"#3a4a30",
  pattern:"metal_plate",particle:"#4ade80",
  furniture:["desk_tactical","desk_tactical","desk_tactical","radar_console","ammo_crate","sandbag_wall","radio_station","weapon_rack"],
  wallArt:["war_map","dog_tags","compass_rose","binoculars"]
},
darklab:{
  floorBase:"#301820",floorLight:"#381e28",
  roomBase:"#402228",roomLight:"#48282e",
  wallFront:"#5a2830",wallTop:"#683038",wallSide:"#4a2028",
  accent:"#f87171",accentDark:"#ef4444",gold:"#d44a4a",
  deskColor:"#4a2828",deskLight:"#5a3838",deskDark:"#3a1818",
  screenBg:"#2a0808",screenGlow:"#ef4444",screenLines:"#f87171",
  chairColor:"#4a1a1a",
  pattern:"cracked_tile",particle:"#f87171",
  furniture:["desk_lab","desk_lab","desk_lab","specimen_jar","blood_tank","tesla_coil","warning_sign","chain_fence"],
  wallArt:["biohazard","heartbeat","xray","claw_marks"]
},
command:{
  floorBase:"#302818",floorLight:"#382e20",
  roomBase:"#3e3422",roomLight:"#443a28",
  wallFront:"#5a4830",wallTop:"#665238",wallSide:"#4a3a28",
  accent:"#fb923c",accentDark:"#f97316",gold:"#d4a040",
  deskColor:"#6a4a20",deskLight:"#7a5a30",deskDark:"#5a3a18",
  screenBg:"#1a1408",screenGlow:"#f97316",screenLines:"#fb923c",
  chairColor:"#5a3a18",
  pattern:"sandstone",particle:"#fb923c",
  furniture:["desk_commander","desk_commander","desk_commander","strategy_table","flag_stand","periscope","supply_crate","medal_display"],
  wallArt:["battle_map","ancient_scroll","sun_emblem","shield_crest"]
},
startup:{
  floorBase:"#222228",floorLight:"#28282e",
  roomBase:"#2e2e34",roomLight:"#34343a",
  wallFront:"#444450",wallTop:"#505058",wallSide:"#3a3a44",
  accent:"#a1a1aa",accentDark:"#71717a",gold:"#8888aa",
  deskColor:"#505060",deskLight:"#606070",deskDark:"#404050",
  screenBg:"#0a0a1a",screenGlow:"#60a5fa",screenLines:"#818cf8",
  chairColor:"#3a3a50",
  pattern:"carpet_weave",particle:"#60a5fa",
  furniture:["desk_modern","desk_modern","desk_modern","whiteboard","bean_bag","water_cooler","ping_pong","neon_sign"],
  wallArt:["motivational","kanban_board","wifi_symbol","startup_logo"]
},
demonetized:{
  floorBase:"#2a1414",floorLight:"#321a1a",
  roomBase:"#381e1e",roomLight:"#402424",
  wallFront:"#5a2828",wallTop:"#683030",wallSide:"#4a2020",
  accent:"#f87171",accentDark:"#ef4444",gold:"#d44a4a",
  deskColor:"#4a2020",deskLight:"#5a3030",deskDark:"#3a1414",
  screenBg:"#1a0808",screenGlow:"#ef4444",screenLines:"#f87171",
  chairColor:"#4a1a1a",
  pattern:"cracked_tile",particle:"#f87171",
  furniture:["desk_lab","desk_lab","desk_lab","blood_tank","specimen_jar","tesla_coil","bookshelf_dark","coffee"],
  wallArt:["biohazard","claw_marks","heartbeat","xray"]
},
wisdom:{
  floorBase:"#2e2a16",floorLight:"#36301c",
  roomBase:"#3e3820",roomLight:"#464026",
  wallFront:"#5a5028",wallTop:"#686030",wallSide:"#4a4220",
  accent:"#fbbf24",accentDark:"#eab308",gold:"#d4a853",
  deskColor:"#6a5a28",deskLight:"#7a6a38",deskDark:"#5a4a18",
  screenBg:"#1a1808",screenGlow:"#eab308",screenLines:"#fbbf24",
  chairColor:"#5a4a18",
  pattern:"parchment",particle:"#fbbf24",
  furniture:["desk_commander","desk_commander","desk_commander","bookshelf_wood","globe","trophy_case","plant_palm","candelabra"],
  wallArt:["ancient_scroll","gold_clock","certificate","sun_emblem"]
}
};

// ============ FLOOR TEXTURE GENERATOR (unique per theme) ============
var tileCache={};
function getTiles(theme){
  if(tileCache[theme])return tileCache[theme];
  var TH=THEMES[theme]||THEMES.startup;
  var tiles=[];
  // 4 corridor + 4 room tiles
  for(var i=0;i<8;i++){
    var c=mkC(T,T),g=c.getContext("2d");
    var isRoom=i>=4;
    var base=isRoom?TH.roomBase:TH.floorBase;
    var light=isRoom?TH.roomLight:TH.floorLight;
    g.fillStyle=base;g.fillRect(0,0,T,T);
    var s=i*31+7; // seed

    if(TH.pattern==="marble"){
      // Rich marble: veins + polish + depth
      g.fillStyle=al(light,.3);g.fillRect(0,0,T,T);
      g.strokeStyle=al("#d4a853",.08);g.lineWidth=1;
      g.beginPath();g.moveTo(s%20,0);g.bezierCurveTo(T*.3,T*.3+s%6,T*.7,T*.5-s%8,T,T-(s%16));g.stroke();
      g.strokeStyle="rgba(255,255,255,.04)";
      g.beginPath();g.moveTo(0,s%24+4);g.bezierCurveTo(T*.4,T*.6,T*.6,T*.3,T,s%20+8);g.stroke();
      if(isRoom){
        g.fillStyle="rgba(212,168,83,.02)";g.fillRect(0,0,T,T);
        g.fillStyle="rgba(255,255,255,.015)";g.fillRect(0,0,T,1); // polish shine
      }
    }else if(TH.pattern==="cobblestone"){
      // Gothic cobblestone: irregular stones + moss + dark grout
      g.fillStyle="rgba(0,0,0,.12)";g.fillRect(0,0,T,2);g.fillRect(0,0,2,T);
      var sx=3+(s%4),sy=3+(s%5);
      g.fillStyle=al(light,.4);g.fillRect(sx,sy,T-sx*2+2,T-sy*2+2);
      // Stone texture - random highlight spots
      g.fillStyle="rgba(255,255,255,.03)";
      g.fillRect(sx+2,sy+2,T/3,T/4);
      // Moss in grout
      g.fillStyle="rgba(60,120,60,.06)";
      g.fillRect(0,0,T,2);g.fillRect(0,0,2,T);
      if(s%3===0){g.fillStyle="rgba(80,160,80,.04)";g.fillRect(1,1,4,3)}
      if(isRoom){g.fillStyle="rgba(139,92,246,.02)";g.fillRect(0,0,T,T)}
    }else if(TH.pattern==="metal_plate"){
      // Industrial: riveted steel panels + scratches
      g.fillStyle=al(light,.2);g.fillRect(0,0,T,T);
      // Panel borders
      g.fillStyle="rgba(255,255,255,.03)";g.fillRect(0,0,T,1);g.fillRect(0,0,1,T);
      g.fillStyle="rgba(0,0,0,.08)";g.fillRect(0,T-1,T,1);g.fillRect(T-1,0,1,T);
      // 4 corner rivets
      g.fillStyle="rgba(200,200,200,.1)";
      g.beginPath();g.arc(4,4,2,0,6.28);g.fill();
      g.beginPath();g.arc(T-4,4,2,0,6.28);g.fill();
      g.beginPath();g.arc(4,T-4,2,0,6.28);g.fill();
      g.beginPath();g.arc(T-4,T-4,2,0,6.28);g.fill();
      // Rivet highlight
      g.fillStyle="rgba(255,255,255,.06)";
      g.fillRect(3,3,1,1);g.fillRect(T-5,3,1,1);
      // Random scratch
      if(s%2===0){
        g.strokeStyle="rgba(255,255,255,.03)";g.lineWidth=1;
        g.beginPath();g.moveTo(s%16+4,6);g.lineTo(s%12+12,T-6);g.stroke();
      }
      if(isRoom){g.fillStyle="rgba(74,140,80,.015)";g.fillRect(0,0,T,T)}
    }else if(TH.pattern==="cracked_tile"){
      // Horror: cracked ceramic + blood red grout + stains
      // Grout lines (blood red)
      g.fillStyle="rgba(160,30,30,.1)";
      g.fillRect(0,0,T,2);g.fillRect(0,0,2,T);g.fillRect(T-2,0,2,T);g.fillRect(0,T-2,T,2);
      // Tile surface with slight color variation
      g.fillStyle=al(light,.25);g.fillRect(3,3,T-6,T-6);
      // Cracks
      if(s%3===0){
        g.strokeStyle="rgba(0,0,0,.2)";g.lineWidth=1;
        g.beginPath();g.moveTo(T/2,T/4);g.lineTo(T/2+3,T/2);g.lineTo(T/2-4,T*3/4);g.stroke();
      }
      if(s%4===0){g.strokeStyle="rgba(0,0,0,.15)";g.beginPath();g.moveTo(T/3,0);g.lineTo(T/2,T);g.stroke()}
      // Blood stain
      if(s%5===0){
        g.fillStyle="rgba(120,15,15,.06)";
        g.beginPath();g.arc(T/2+3,T/2-2,6,0,6.28);g.fill();
      }
      if(isRoom){g.fillStyle="rgba(200,40,40,.015)";g.fillRect(0,0,T,T)}
    }else if(TH.pattern==="sandstone"){
      // Ancient: weathered sandstone blocks
      g.fillStyle=al(light,.3);g.fillRect(0,0,T,T);
      // Block edges
      g.fillStyle="rgba(0,0,0,.06)";g.fillRect(0,T-1,T,1);g.fillRect(T-1,0,1,T);
      g.fillStyle="rgba(255,255,255,.03)";g.fillRect(0,0,T,1);g.fillRect(0,0,1,T);
      // Sand grain dots
      g.fillStyle="rgba(200,170,100,.04)";
      for(var d=0;d<5;d++){g.fillRect((s*3+d*7)%28+2,(s*5+d*11)%24+4,1,1)}
      // Weathering
      if(s%3===0){g.fillStyle="rgba(0,0,0,.03)";g.fillRect(4,T/2,T-8,2)}
      if(isRoom){g.fillStyle="rgba(249,115,22,.015)";g.fillRect(0,0,T,T)}
    }else if(TH.pattern==="parchment"){
      // Wisdom: warm parchment/old paper texture with golden hue
      g.fillStyle=al(light,.35);g.fillRect(0,0,T,T);
      // Warm golden wash
      g.fillStyle="rgba(212,168,83,.04)";g.fillRect(0,0,T,T);
      // Parchment fiber lines (horizontal, organic)
      g.strokeStyle="rgba(180,150,80,.04)";g.lineWidth=1;
      g.beginPath();g.moveTo(0,s%12+4);g.bezierCurveTo(T*.3,s%8+6,T*.7,s%10+2,T,s%14+3);g.stroke();
      g.beginPath();g.moveTo(0,s%16+16);g.bezierCurveTo(T*.4,s%6+18,T*.6,s%12+14,T,s%10+18);g.stroke();
      // Age spots / stains
      if(s%3===0){g.fillStyle="rgba(140,110,50,.03)";g.beginPath();g.arc(s%20+6,s%18+8,4,0,6.28);g.fill()}
      // Edge darkening
      g.fillStyle="rgba(0,0,0,.02)";g.fillRect(0,0,2,T);g.fillRect(T-2,0,2,T);
      // Gold dust specks
      g.fillStyle="rgba(212,168,83,.05)";
      g.fillRect((s*5)%26+3,(s*7)%22+5,1,1);g.fillRect((s*3)%24+8,(s*9)%20+10,1,1);
      if(isRoom){g.fillStyle="rgba(234,179,8,.02)";g.fillRect(0,0,T,T)}
    }else{
      // Startup carpet: woven fiber texture
      g.fillStyle=al(light,.15);g.fillRect(0,0,T,T);
      // Weave pattern (subtle cross-hatch)
      g.fillStyle="rgba(255,255,255,.008)";
      for(var fy=0;fy<T;fy+=2){g.fillRect(0,fy,T,1)}
      g.fillStyle="rgba(255,255,255,.005)";
      for(var fx=0;fx<T;fx+=3){g.fillRect(fx,0,1,T)}
      // Fiber texture dots
      g.fillStyle="rgba(255,255,255,.012)";
      for(var fd=0;fd<4;fd++){g.fillRect((s+fd*8)%28+2,(s+fd*13)%26+3,1,1)}
      if(isRoom){g.fillStyle="rgba(96,165,250,.01)";g.fillRect(0,0,T,T)}
    }
    tiles.push(c);
  }
  tileCache[theme]=tiles;
  return tiles;
}

// ============ WALLS with 3D isometric depth ============
function drawWall(x,y,w,th){
  var wH=24;
  // Shadow below wall
  cx.fillStyle="rgba(0,0,0,.25)";cx.fillRect(x,y+wH,w,3);
  // Front face
  var grd=cx.createLinearGradient(x,y,x,y+wH);
  grd.addColorStop(0,th.wallTop);grd.addColorStop(1,th.wallFront);
  cx.fillStyle=grd;cx.fillRect(x,y,w,wH);
  // Top ledge
  cx.fillStyle=lt(th.wallTop,15);cx.fillRect(x,y-4,w,6);
  // Accent stripe along top
  cx.fillStyle=al(th.accent,.5);cx.fillRect(x,y-4,w,2);
  // Bottom molding
  cx.fillStyle=dk(th.wallFront,15);cx.fillRect(x,y+wH-3,w,3);
  // Top highlight
  cx.fillStyle="rgba(255,255,255,.06)";cx.fillRect(x,y-4,w,1);
}

function drawSideWall(x,y,h,th,left){
  var wW=10;
  var grd=cx.createLinearGradient(left?x:x-wW,0,left?x+wW:x,0);
  grd.addColorStop(0,left?dk(th.wallSide,10):th.wallSide);
  grd.addColorStop(1,left?th.wallSide:dk(th.wallSide,10));
  cx.fillStyle=grd;cx.fillRect(left?x:x-wW,y,wW,h);
  // Edge highlights
  if(left){
    cx.fillStyle="rgba(0,0,0,.2)";cx.fillRect(x,y,1,h);
    cx.fillStyle="rgba(255,255,255,.04)";cx.fillRect(x+wW-1,y,1,h);
  }else{
    cx.fillStyle="rgba(0,0,0,.25)";cx.fillRect(x-1,y,1,h);
  }
}

// ============ UNIQUE FURNITURE PER SECTOR ============

// --- EXECUTIVE ---
function drawDeskExec(x,y,th){
  // Premium mahogany desk with gold accents
  cx.fillStyle=th.deskColor;cx.fillRect(x,y+14,56,5);
  cx.fillStyle=th.deskLight;cx.fillRect(x,y+14,56,2); // polish
  cx.fillStyle=al(th.gold,.3);cx.fillRect(x,y+14,56,1); // gold edge
  // Front panel with drawers
  cx.fillStyle=th.deskDark;cx.fillRect(x+2,y+19,52,14);
  cx.fillStyle=th.deskColor;
  cx.fillRect(x+4,y+20,22,5);cx.fillRect(x+4,y+27,22,5);
  cx.fillRect(x+30,y+20,22,5);cx.fillRect(x+30,y+27,22,5);
  cx.fillStyle=th.gold;
  cx.fillRect(x+14,y+22,2,1);cx.fillRect(x+14,y+29,2,1);
  cx.fillRect(x+40,y+22,2,1);cx.fillRect(x+40,y+29,2,1);
  // Legs
  cx.fillStyle=th.deskDark;cx.fillRect(x+1,y+33,4,4);cx.fillRect(x+51,y+33,4,4);
  // Monitor - large LCD
  cx.fillStyle="#0a0a0a";cx.fillRect(x+10,y-6,36,20);
  cx.fillStyle="#161616";cx.fillRect(x+11,y-5,34,18);
  cx.fillStyle=th.screenBg;cx.fillRect(x+12,y-4,32,16);
  // Screen content - spreadsheet
  cx.fillStyle=al(th.screenGlow,.4);
  for(var l=0;l<5;l++){cx.fillRect(x+14,y-2+l*3,8+((l*3)%12),1)}
  cx.fillStyle=al(th.screenGlow,.25);
  cx.fillRect(x+30,y-2,10,1);cx.fillRect(x+30,y+4,8,1);
  // Screen glow
  cx.fillStyle=al(th.screenGlow,.03);cx.fillRect(x+4,y-10,48,28);
  // Stand
  cx.fillStyle="#1a1a1a";cx.fillRect(x+24,y+14,8,2);cx.fillRect(x+21,y+15,14,2);
  // Keyboard + mouse
  cx.fillStyle="#151515";cx.fillRect(x+14,y+16,22,4);
  cx.fillStyle="#1e1e1e";for(var k=0;k<8;k++)cx.fillRect(x+15+k*3,y+17,2,1);
  cx.fillStyle="#151515";cx.fillRect(x+40,y+17,5,3);
  // Coffee mug
  cx.fillStyle="#fff";cx.fillRect(x+4,y+16,4,4);cx.fillRect(x+8,y+17,2,2);
  cx.fillStyle="#8b5a2a";cx.fillRect(x+5,y+16,2,2);
}

function drawGlobe(x,y){
  // World globe on stand
  cx.fillStyle="#d4a853";cx.fillRect(x+12,y+24,8,4);cx.fillRect(x+14,y+20,4,6);
  cx.fillStyle="#1a4a6a";cx.beginPath();cx.arc(x+16,y+12,10,0,6.28);cx.fill();
  cx.fillStyle="#2a6a8a";
  cx.fillRect(x+8,y+8,6,4);cx.fillRect(x+18,y+10,6,6);cx.fillRect(x+12,y+16,8,3);
  cx.fillStyle="#1a5a7a";cx.beginPath();cx.arc(x+16,y+12,10,0,6.28);cx.stroke;
  cx.strokeStyle="#d4a853";cx.lineWidth=1;cx.beginPath();cx.arc(x+16,y+12,10,0,6.28);cx.stroke();
  cx.beginPath();cx.ellipse(x+16,y+12,10,4,0,0,6.28);cx.stroke();
}

function drawTrophyCase(x,y,th){
  cx.fillStyle=th.deskDark;cx.fillRect(x,y,30,44);
  cx.fillStyle=th.deskColor;cx.fillRect(x,y,30,2);cx.fillRect(x,y,2,44);cx.fillRect(x+28,y,2,44);
  // Glass front
  cx.fillStyle="rgba(255,255,255,.03)";cx.fillRect(x+3,y+3,24,38);
  // Shelves
  cx.fillStyle=th.deskDark;cx.fillRect(x+2,y+16,26,2);cx.fillRect(x+2,y+30,26,2);
  // Trophies
  cx.fillStyle="#d4a853";
  cx.fillRect(x+8,y+8,4,7);cx.fillRect(x+6,y+6,8,3); // cup 1
  cx.fillRect(x+18,y+22,4,6);cx.fillRect(x+16,y+20,8,3); // cup 2
  cx.fillStyle="#c0c0c0";
  cx.fillRect(x+18,y+10,4,5);cx.fillRect(x+16,y+8,8,3); // silver
  cx.fillStyle="#cd7f32";
  cx.fillRect(x+8,y+34,4,6);cx.fillRect(x+6,y+32,8,3); // bronze
}

// --- GOTHIC ---
function drawDeskAntique(x,y,th){
  // Dark ornate desk with carved details
  cx.fillStyle=th.deskColor;cx.fillRect(x,y+14,52,5);
  cx.fillStyle=th.deskLight;cx.fillRect(x+1,y+14,50,1);
  // Carved front
  cx.fillStyle=th.deskDark;cx.fillRect(x+2,y+19,48,14);
  // Ornate carving pattern
  cx.fillStyle=al(th.accent,.15);
  cx.fillRect(x+6,y+22,10,1);cx.fillRect(x+6,y+26,10,1);
  cx.fillRect(x+36,y+22,10,1);cx.fillRect(x+36,y+26,10,1);
  cx.fillRect(x+22,y+21,8,8); // center motif
  cx.fillStyle=al(th.accent,.08);cx.fillRect(x+23,y+22,6,6);
  // Legs (ornate turned legs)
  cx.fillStyle=th.deskDark;
  cx.fillRect(x+1,y+33,5,5);cx.fillRect(x+46,y+33,5,5);
  cx.fillStyle=th.deskColor;cx.fillRect(x+2,y+35,3,1);cx.fillRect(x+47,y+35,3,1);
  // Monitor - old CRT style
  cx.fillStyle="#2a2a2a";cx.fillRect(x+8,y-4,36,20);
  cx.fillStyle="#1a1a1a";cx.fillRect(x+10,y-2,32,16);
  cx.fillStyle=th.screenBg;cx.fillRect(x+11,y-1,30,14);
  cx.fillStyle=al(th.screenGlow,.35);
  cx.fillRect(x+13,y+1,12,1);cx.fillRect(x+13,y+4,18,1);cx.fillRect(x+13,y+7,8,1);cx.fillRect(x+13,y+10,14,1);
  cx.fillStyle=al(th.screenGlow,.03);cx.fillRect(x+4,y-8,44,26);
  // Candle on desk
  cx.fillStyle="#eee";cx.fillRect(x+2,y+8,3,7);
  var fl=Math.sin(now()*3)>.2;
  cx.fillStyle="#f59e0b";cx.fillRect(x+2,y+5+(fl?1:0),3,3);
  cx.fillStyle="#fde68a";cx.fillRect(x+3,y+6+(fl?1:0),1,1);
  // Stand
  cx.fillStyle="#222";cx.fillRect(x+22,y+14,8,2);
  // Quill pen
  cx.fillStyle="#eee";cx.fillRect(x+44,y+10,2,8);cx.fillStyle="#333";cx.fillRect(x+44,y+17,2,3);
}

function drawCandelabra(x,y,th){
  cx.fillStyle=th.gold||"#d4a853";
  cx.fillRect(x+10,y+30,12,4);cx.fillRect(x+14,y+18,4,14);
  cx.fillRect(x+6,y+16,20,3);
  cx.fillStyle="#eee";cx.fillRect(x+7,y+10,4,7);cx.fillRect(x+14,y+8,4,9);cx.fillRect(x+21,y+10,4,7);
  var t=now();
  var f1=Math.sin(t*4)>.2,f2=Math.sin(t*4+1.2)>.2,f3=Math.sin(t*4+2.4)>.2;
  cx.fillStyle="#f59e0b";
  cx.fillRect(x+8,y+6+(f1?1:0),2,4);cx.fillRect(x+15,y+4+(f2?1:0),2,4);cx.fillRect(x+22,y+6+(f3?1:0),2,4);
  cx.fillStyle="#fde68a";
  cx.fillRect(x+8,y+7+(f1?1:0),2,2);cx.fillRect(x+15,y+5+(f2?1:0),2,2);cx.fillRect(x+22,y+7+(f3?1:0),2,2);
  // warm glow
  cx.fillStyle=al("#f59e0b",.05);cx.beginPath();cx.arc(x+16,y+12,20,0,6.28);cx.fill();
}

function drawSkullShelf(x,y,th){
  cx.fillStyle=th.deskDark||"#2a1838";cx.fillRect(x+2,y+10,28,24);
  cx.fillStyle=th.deskColor||"#3a2848";cx.fillRect(x+2,y+10,28,2);cx.fillRect(x+2,y+22,28,2);
  // Skulls
  cx.fillStyle="#d4c8a0";
  cx.beginPath();cx.arc(x+10,y+17,4,0,6.28);cx.fill();
  cx.beginPath();cx.arc(x+22,y+17,4,0,6.28);cx.fill();
  cx.fillStyle="#1a1a1a";
  cx.fillRect(x+8,y+16,2,1);cx.fillRect(x+11,y+16,2,1); // eyes
  cx.fillRect(x+20,y+16,2,1);cx.fillRect(x+23,y+16,2,1);
  // Books below
  cx.fillStyle="#8b0000";cx.fillRect(x+5,y+26,4,6);
  cx.fillStyle="#2c1810";cx.fillRect(x+10,y+25,3,7);
  cx.fillStyle="#4a1040";cx.fillRect(x+14,y+26,5,6);
}

function drawPotionShelf(x,y,th){
  cx.fillStyle=th.deskDark||"#2a1838";cx.fillRect(x+2,y+14,28,20);
  cx.fillStyle=th.deskColor||"#3a2848";cx.fillRect(x+2,y+14,28,2);
  // Potion bottles
  cx.fillStyle="rgba(80,200,80,.4)";cx.fillRect(x+6,y+18,4,8);cx.fillRect(x+7,y+16,2,3);
  cx.fillStyle="rgba(200,80,200,.4)";cx.fillRect(x+14,y+20,4,6);cx.fillRect(x+15,y+18,2,3);
  cx.fillStyle="rgba(80,80,200,.4)";cx.fillRect(x+22,y+19,4,7);cx.fillRect(x+23,y+17,2,3);
  // Bubbles
  var t=now();
  if(Math.sin(t*2)>.5){cx.fillStyle="rgba(100,255,100,.3)";cx.fillRect(x+7,y+19,1,1)}
  if(Math.sin(t*2.5)>.5){cx.fillStyle="rgba(255,100,255,.3)";cx.fillRect(x+16,y+21,1,1)}
}

// --- WAR ROOM ---
function drawDeskTactical(x,y,th){
  // Military tactical desk - metal + camo
  cx.fillStyle="#4a5040";cx.fillRect(x,y+14,56,5);
  cx.fillStyle="#565e4e";cx.fillRect(x,y+14,56,2);
  // Metal legs (not wood)
  cx.fillStyle="#3a3a3a";
  cx.fillRect(x+2,y+19,3,18);cx.fillRect(x+51,y+19,3,18);
  cx.fillRect(x+2,y+34,52,3); // support bar
  // Metal drawers
  cx.fillStyle="#444";cx.fillRect(x+8,y+20,18,12);
  cx.fillStyle="#4a4a4a";cx.fillRect(x+9,y+21,16,5);cx.fillRect(x+9,y+27,16,4);
  cx.fillStyle="#666";cx.fillRect(x+16,y+23,2,1);cx.fillRect(x+16,y+28,2,1);
  // Monitor - military green screen
  cx.fillStyle="#1a1a1a";cx.fillRect(x+10,y-6,36,20);
  cx.fillStyle="#0a0a0a";cx.fillRect(x+12,y-4,32,16);
  cx.fillStyle=th.screenBg;cx.fillRect(x+13,y-3,30,14);
  cx.fillStyle=al(th.screenGlow,.5);
  cx.fillRect(x+15,y-1,6,1);cx.fillRect(x+23,y-1,12,1);
  cx.fillRect(x+15,y+2,20,1);cx.fillRect(x+15,y+5,10,1);cx.fillRect(x+28,y+5,8,1);
  cx.fillRect(x+15,y+8,16,1);
  cx.fillStyle=al(th.screenGlow,.03);cx.fillRect(x+4,y-10,48,28);
  // Stand
  cx.fillStyle="#222";cx.fillRect(x+24,y+14,8,2);cx.fillRect(x+22,y+15,12,2);
  // Keyboard
  cx.fillStyle="#1a1a1a";cx.fillRect(x+16,y+16,20,4);
  cx.fillStyle="#252525";for(var k=0;k<7;k++)cx.fillRect(x+17+k*3,y+17,2,1);
  // Dog tag on desk
  cx.fillStyle="#999";cx.fillRect(x+42,y+16,6,4);cx.fillStyle="#777";cx.fillRect(x+43,y+17,4,2);
}

function drawRadarConsole(x,y,th){
  // Large radar station
  cx.fillStyle="#2a2a2a";cx.fillRect(x+2,y+8,28,26);
  cx.fillStyle="#1a1a1a";cx.fillRect(x+4,y+10,24,20);
  cx.fillStyle="#0a1a0a";cx.fillRect(x+5,y+11,22,18);
  // Radar circles
  cx.strokeStyle="#1a4a1a";cx.lineWidth=1;
  cx.beginPath();cx.arc(x+16,y+20,8,0,6.28);cx.stroke();
  cx.beginPath();cx.arc(x+16,y+20,4,0,6.28);cx.stroke();
  // Sweep line - smooth rotation
  var ang=now()*.8;
  cx.strokeStyle=al("#4ade80",.8);cx.lineWidth=1;
  cx.beginPath();cx.moveTo(x+16,y+20);cx.lineTo(x+16+Math.cos(ang)*9,y+20+Math.sin(ang)*9);cx.stroke();
  // Fade trail
  cx.strokeStyle=al("#4ade80",.3);
  cx.beginPath();cx.moveTo(x+16,y+20);cx.lineTo(x+16+Math.cos(ang-.3)*9,y+20+Math.sin(ang-.3)*9);cx.stroke();
  // Blips
  cx.fillStyle="#4ade80";
  cx.fillRect(x+12+(Math.sin(now()*.5)*3|0),y+17,2,2);
  cx.fillRect(x+20,y+23+(Math.cos(now()*.7)*2|0),2,2);
  // Base
  cx.fillStyle="#333";cx.fillRect(x+6,y+30,20,4);
  // Buttons
  cx.fillStyle="#4ade80";cx.fillRect(x+8,y+31,3,2);
  cx.fillStyle="#ef4444";cx.fillRect(x+14,y+31,3,2);
  cx.fillStyle="#fbbf24";cx.fillRect(x+20,y+31,3,2);
}

function drawAmmoCrate(x,y){
  cx.fillStyle="#4a5a30";cx.fillRect(x+2,y+16,28,18);
  cx.fillStyle="#566a38";cx.fillRect(x+2,y+16,28,3);
  cx.fillStyle="#3a4a20";cx.fillRect(x+4,y+20,24,2); // strap
  cx.fillStyle="#fbbf24";cx.fillRect(x+12,y+24,8,4);
  cx.fillStyle="#3a4a20";cx.fillRect(x+14,y+25,4,2); // star
}

function drawSandbagWall(x,y){
  cx.fillStyle="#8a7a50";
  for(var r=0;r<3;r++){
    for(var b=0;b<3;b++){
      var bx=x+2+b*10-(r%2)*5,by=y+20+r*6;
      cx.fillRect(bx,by,9,5);
      cx.fillStyle="#7a6a40";cx.fillRect(bx,by,9,1);cx.fillStyle="#8a7a50";
    }
  }
}

function drawRadioStation(x,y,th){
  cx.fillStyle="#2a2a2a";cx.fillRect(x+4,y+12,24,22);
  cx.fillStyle="#333";cx.fillRect(x+4,y+12,24,2);
  // Dials
  cx.fillStyle="#0a1a0a";cx.fillRect(x+8,y+16,16,8);
  cx.fillStyle=al("#4ade80",.5);
  var w=8+Math.sin(now()*1.5)*4;
  cx.fillRect(x+12,y+19,w|0,2);
  // Antenna
  cx.fillStyle="#666";cx.fillRect(x+28,y+4,2,10);cx.fillRect(x+26,y+4,6,2);
  // Mic
  cx.fillStyle="#444";cx.fillRect(x+6,y+34,4,4);cx.fillRect(x+7,y+30,2,5);
}

function drawWeaponRack(x,y){
  cx.fillStyle="#5a4a30";cx.fillRect(x+4,y+4,24,32);
  cx.fillStyle="#6a5a40";cx.fillRect(x+4,y+4,24,2);
  // Weapons (silhouettes)
  cx.fillStyle="#333";
  cx.fillRect(x+8,y+8,2,24);cx.fillRect(x+6,y+10,6,2);
  cx.fillRect(x+16,y+10,2,22);cx.fillRect(x+14,y+12,6,2);
  cx.fillRect(x+24,y+8,2,24);cx.fillRect(x+22,y+10,6,2);
}

// --- TERROR / DARK LAB ---
function drawDeskLab(x,y,th){
  // Lab workstation - stainless steel
  cx.fillStyle="#555";cx.fillRect(x,y+14,56,4);
  cx.fillStyle="#666";cx.fillRect(x,y+14,56,1);
  // Metal frame legs
  cx.fillStyle="#444";
  cx.fillRect(x+2,y+18,3,20);cx.fillRect(x+51,y+18,3,20);
  cx.fillRect(x+2,y+28,52,2); // crossbar
  // Monitor
  cx.fillStyle="#111";cx.fillRect(x+12,y-6,32,20);
  cx.fillStyle="#0a0a0a";cx.fillRect(x+13,y-5,30,18);
  cx.fillStyle=th.screenBg;cx.fillRect(x+14,y-4,28,16);
  // Screen - heartbeat line
  cx.strokeStyle=al(th.screenGlow,.6);cx.lineWidth=1;
  cx.beginPath();cx.moveTo(x+16,y+4);
  var t=now();
  for(var p=0;p<24;p++){
    var yv=y+4;
    if(p===8)yv-=4;if(p===9)yv+=6;if(p===10)yv-=8;if(p===11)yv+=3;
    cx.lineTo(x+16+p,yv);
  }
  cx.stroke();
  cx.fillStyle=al(th.screenGlow,.03);cx.fillRect(x+6,y-10,44,28);
  // Stand
  cx.fillStyle="#333";cx.fillRect(x+24,y+14,8,2);
  // Keyboard
  cx.fillStyle="#1a1a1a";cx.fillRect(x+16,y+16,20,3);
  // Test tubes
  cx.fillStyle="rgba(200,50,50,.3)";cx.fillRect(x+4,y+10,3,6);
  cx.fillStyle="rgba(50,200,50,.3)";cx.fillRect(x+8,y+11,3,5);
  cx.fillStyle="rgba(50,50,200,.3)";cx.fillRect(x+46,y+10,3,6);
}

function drawSpecimenJar(x,y){
  cx.fillStyle="rgba(100,200,100,.15)";cx.fillRect(x+6,y+8,20,22);
  cx.fillStyle="#555";cx.fillRect(x+6,y+6,20,4);
  // Specimen inside
  cx.fillStyle="rgba(200,150,150,.2)";
  cx.beginPath();cx.arc(x+16,y+20,6,0,6.28);cx.fill();
  // Bubbles
  var t=now();
  cx.fillStyle="rgba(150,255,150,.2)";
  cx.fillRect(x+12,y+12-(t%3|0),2,2);
  cx.fillRect(x+20,y+14-((t+1)%4|0),1,1);
}

function drawBloodTank(x,y){
  cx.fillStyle="#444";cx.fillRect(x+4,y+6,24,28);
  cx.fillStyle="#555";cx.fillRect(x+4,y+6,24,3);
  // Blood inside
  var lvl=18+Math.sin(now()*.5)*2;
  cx.fillStyle="rgba(180,20,20,.4)";cx.fillRect(x+6,y+6+(28-lvl),20,lvl);
  // Label
  cx.fillStyle="#ef4444";cx.fillRect(x+10,y+14,12,3);
  cx.fillStyle="#fff";cx.fillRect(x+12,y+15,8,1);
  // Tubes
  cx.fillStyle="#666";cx.fillRect(x+8,y+34,2,4);cx.fillRect(x+22,y+34,2,4);
}

function drawTeslaCoil(x,y,th){
  cx.fillStyle="#555";cx.fillRect(x+10,y+28,12,6);
  cx.fillStyle="#444";cx.fillRect(x+12,y+14,8,16);
  cx.fillStyle="#666";cx.fillRect(x+14,y+6,4,10);
  cx.fillStyle="#888";
  cx.beginPath();cx.arc(x+16,y+6,4,0,6.28);cx.fill();
  // Lightning
  var t=now();
  if(Math.sin(t*8)>.6){
    cx.strokeStyle=al(th.accent,.6);cx.lineWidth=1;
    cx.beginPath();cx.moveTo(x+16,y+6);
    cx.lineTo(x+20+(Math.random()*6|0),y-2);cx.stroke();
    cx.fillStyle=al(th.accent,.04);cx.beginPath();cx.arc(x+16,y+6,14,0,6.28);cx.fill();
  }
}

function drawWarningSign(x,y){
  cx.fillStyle="#fbbf24";
  cx.beginPath();cx.moveTo(x+16,y+8);cx.lineTo(x+28,y+28);cx.lineTo(x+4,y+28);cx.closePath();cx.fill();
  cx.fillStyle="#111";
  cx.beginPath();cx.moveTo(x+16,y+12);cx.lineTo(x+25,y+26);cx.lineTo(x+7,y+26);cx.closePath();cx.fill();
  cx.fillStyle="#fbbf24";cx.fillRect(x+15,y+15,2,6);cx.fillRect(x+15,y+23,2,2);
}

// --- COMMAND CENTER ---
function drawDeskCommander(x,y,th){
  // Heavy wood commander desk
  cx.fillStyle=th.deskColor;cx.fillRect(x,y+14,56,6);
  cx.fillStyle=th.deskLight;cx.fillRect(x,y+14,56,2);
  cx.fillStyle=al(th.gold,.2);cx.fillRect(x,y+14,56,1);
  // Thick front panel
  cx.fillStyle=th.deskDark;cx.fillRect(x+2,y+20,52,16);
  cx.fillStyle=th.deskColor;cx.fillRect(x+4,y+22,20,12);cx.fillRect(x+28,y+22,22,12);
  cx.fillStyle=th.gold;cx.fillRect(x+13,y+27,2,2);cx.fillRect(x+38,y+27,2,2);
  // Sturdy legs
  cx.fillStyle=th.deskDark;cx.fillRect(x,y+36,6,4);cx.fillRect(x+50,y+36,6,4);
  // Monitor
  cx.fillStyle="#111";cx.fillRect(x+10,y-6,36,20);cx.fillStyle="#0a0a0a";cx.fillRect(x+12,y-4,32,16);
  cx.fillStyle=th.screenBg;cx.fillRect(x+13,y-3,30,14);
  cx.fillStyle=al(th.screenGlow,.45);
  cx.fillRect(x+15,y-1,10,1);cx.fillRect(x+15,y+2,20,1);cx.fillRect(x+15,y+5,14,1);cx.fillRect(x+15,y+8,8,1);
  cx.fillStyle=al(th.screenGlow,.03);cx.fillRect(x+4,y-10,48,28);
  cx.fillStyle="#1a1a1a";cx.fillRect(x+24,y+14,8,2);
  cx.fillStyle="#151515";cx.fillRect(x+14,y+16,22,4);
  // Medal on desk
  cx.fillStyle="#d4a853";cx.beginPath();cx.arc(x+46,y+17,3,0,6.28);cx.fill();
  cx.fillStyle="#ef4444";cx.fillRect(x+44,y+12,4,3);
}

function drawStrategyTable(x,y,th){
  cx.fillStyle=th.deskColor;cx.fillRect(x+2,y+16,28,4);cx.fillRect(x+4,y+20,3,12);cx.fillRect(x+25,y+20,3,12);
  cx.fillStyle="#d4c4a0";cx.fillRect(x+4,y+10,24,8); // map on table
  cx.fillStyle="#b8a878";cx.fillRect(x+8,y+12,8,4);cx.fillRect(x+18,y+11,6,5);
  cx.fillStyle="#ef4444";cx.fillRect(x+10,y+13,2,1);cx.fillRect(x+20,y+12,2,1);
  cx.fillStyle="#3b82f6";cx.fillRect(x+14,y+14,2,1);
}

function drawFlagStand(x,y,th){
  cx.fillStyle="#666";cx.fillRect(x+14,y+6,3,28);cx.fillRect(x+8,y+32,16,3);
  cx.fillStyle=th.accent;cx.fillRect(x+16,y+7,16,10);
  cx.fillStyle=lt(th.accent,30);cx.fillRect(x+16,y+7,16,2);
  cx.fillStyle=dk(th.accent,20);cx.fillRect(x+16,y+15,16,2);
  // Wind animation
  var wave=Math.sin(now()*2)*2;
  cx.fillStyle=th.accent;cx.fillRect(x+30,y+9+(wave|0),2,6);
}

function drawPeriscope(x,y){
  cx.fillStyle="#555";cx.fillRect(x+14,y+10,4,26);
  cx.fillStyle="#666";cx.fillRect(x+12,y+6,8,6);cx.fillRect(x+10,y+36,12,3);
  cx.fillStyle="#3b82f6";cx.fillRect(x+14,y+8,4,2); // lens
  cx.fillStyle=al("#3b82f6",.1);cx.beginPath();cx.arc(x+16,y+8,8,0,6.28);cx.fill();
}

// --- STARTUP ---
function drawDeskModern(x,y,th){
  // Clean modern desk - white/light
  cx.fillStyle=th.deskColor;cx.fillRect(x,y+14,56,4);
  cx.fillStyle=th.deskLight;cx.fillRect(x,y+14,56,1);
  // Minimal legs
  cx.fillStyle=th.deskDark;cx.fillRect(x+4,y+18,2,20);cx.fillRect(x+50,y+18,2,20);
  // Monitor - ultra thin
  cx.fillStyle="#111";cx.fillRect(x+8,y-8,40,22);
  cx.fillStyle="#0a0a0a";cx.fillRect(x+9,y-7,38,20);
  cx.fillStyle=th.screenBg;cx.fillRect(x+10,y-6,36,18);
  // Screen content - modern code editor
  cx.fillStyle=al("#818cf8",.4);cx.fillRect(x+12,y-4,8,1);
  cx.fillStyle=al("#4ade80",.3);cx.fillRect(x+22,y-4,12,1);
  cx.fillStyle=al("#60a5fa",.35);cx.fillRect(x+12,y-1,16,1);
  cx.fillStyle=al("#f59e0b",.3);cx.fillRect(x+30,y-1,10,1);
  cx.fillStyle=al("#818cf8",.3);cx.fillRect(x+12,y+2,20,1);
  cx.fillStyle=al("#4ade80",.25);cx.fillRect(x+12,y+5,14,1);cx.fillRect(x+28,y+5,8,1);
  cx.fillStyle=al(th.screenGlow,.03);cx.fillRect(x+2,y-12,52,30);
  cx.fillStyle="#222";cx.fillRect(x+26,y+14,4,2);
  // Laptop-style keyboard
  cx.fillStyle="#191919";cx.fillRect(x+12,y+16,28,4);
  // Wireless mouse
  cx.fillStyle="#222";cx.fillRect(x+44,y+16,6,4);cx.fillStyle="#333";cx.fillRect(x+46,y+17,2,1);
  // Stickers on laptop
  cx.fillStyle="#ef4444";cx.fillRect(x+4,y+16,3,3);
  cx.fillStyle="#3b82f6";cx.fillRect(x+4,y+12,3,3);
}

function drawWhiteboard(x,y){
  cx.fillStyle="#888";cx.fillRect(x,y,44,32);
  cx.fillStyle="#f5f5f5";cx.fillRect(x+2,y+2,40,26);
  cx.fillStyle="#333";cx.fillRect(x+5,y+5,18,1);cx.fillRect(x+5,y+8,28,1);cx.fillRect(x+5,y+11,14,1);
  cx.fillStyle="#ef4444";cx.fillRect(x+5,y+15,12,1);
  cx.fillStyle="#3b82f6";cx.fillRect(x+20,y+15,16,1);
  cx.fillStyle="#22c55e";cx.fillRect(x+5,y+19,10,1);cx.fillRect(x+5,y+22,20,1);
  cx.fillStyle="#aaa";cx.fillRect(x+2,y+28,40,4);
  cx.fillStyle="#ef4444";cx.fillRect(x+6,y+29,6,2);cx.fillStyle="#3b82f6";cx.fillRect(x+14,y+29,6,2);
}

function drawBeanBag(x,y,th){
  cx.fillStyle=dk(th.accent,40);
  cx.beginPath();cx.ellipse(x+16,y+24,12,8,0,0,6.28);cx.fill();
  cx.fillStyle=dk(th.accent,30);
  cx.beginPath();cx.ellipse(x+16,y+18,10,10,0,0,3.14);cx.fill();
  cx.fillStyle=dk(th.accent,20);
  cx.beginPath();cx.ellipse(x+16,y+16,6,4,0,0,6.28);cx.fill();
}

function drawWaterCooler(x,y){
  cx.fillStyle="#ddd";cx.fillRect(x+10,y+18,12,16);
  cx.fillStyle="#eee";cx.fillRect(x+10,y+18,12,2);
  cx.fillStyle="rgba(100,180,255,.3)";cx.fillRect(x+12,y+6,8,14);
  cx.fillStyle="rgba(130,200,255,.2)";cx.fillRect(x+12,y+6,8,4);
  cx.fillStyle="#bbb";cx.fillRect(x+12,y+20,4,2); // tap
  cx.fillStyle="#ddd";cx.fillRect(x+14,y+22,2,8); // cup
}

function drawNeonSign(x,y,th){
  var t=now(),blink=Math.sin(t*3)>.1;
  var glow=blink?.6:.1;
  cx.fillStyle=al(th.accent,glow);
  cx.font='bold 10px "Press Start 2P",monospace';cx.textAlign="center";
  cx.fillText("HACK",x+16,y+22);cx.textAlign="start";
  if(blink){cx.fillStyle=al(th.accent,.04);cx.beginPath();cx.arc(x+16,y+18,18,0,6.28);cx.fill()}
}

// --- SHARED ---
function drawBookshelfWood(x,y,th){
  cx.fillStyle=th.deskColor;cx.fillRect(x,y,28,48);
  cx.fillStyle=th.deskLight;cx.fillRect(x,y,28,2);cx.fillRect(x,y,2,48);
  cx.fillStyle=th.deskDark;cx.fillRect(x+26,y,2,48);cx.fillRect(x,y+46,28,2);
  var colors=["#c0392b","#2980b9","#27ae60","#8e44ad","#d35400","#2c3e50","#16a085","#f39c12"];
  for(var s=0;s<3;s++){
    var sy=y+14+s*14;
    cx.fillStyle=th.deskDark;cx.fillRect(x+1,sy,26,2);
    var bx=x+3;
    for(var b=0;b<5;b++){
      var bw=3+((b+s)%3);
      cx.fillStyle=colors[(b+s*3)%colors.length];
      cx.fillRect(bx,sy-11,bw,11);
      cx.fillStyle=lt(colors[(b+s*3)%colors.length],25);cx.fillRect(bx,sy-11,bw,1);
      bx+=bw+1;
    }
  }
}

function drawBookshelfDark(x,y,th){
  cx.fillStyle="#1a1028";cx.fillRect(x,y,28,48);
  cx.fillStyle="#2a1838";cx.fillRect(x,y,28,2);cx.fillRect(x,y,2,48);cx.fillRect(x+26,y,2,48);
  var colors=["#4a1030","#1a2050","#2a1040","#3a0a1a","#1a3030","#2a0a30"];
  for(var s=0;s<3;s++){
    var sy=y+14+s*14;
    cx.fillStyle="#1a0a18";cx.fillRect(x+1,sy,26,2);
    var bx=x+3;
    for(var b=0;b<5;b++){
      var bw=3+((b+s)%2);
      cx.fillStyle=colors[(b+s*3)%colors.length];cx.fillRect(bx,sy-11,bw,11);
      bx+=bw+1;
    }
  }
}

function drawPlant(x,y,big){
  cx.fillStyle="#6b4226";
  if(big){
    cx.fillRect(x+6,y+24,20,12);cx.fillStyle="#8a5a3a";cx.fillRect(x+6,y+24,20,2);
    cx.fillStyle="#3a2a1a";cx.fillRect(x+8,y+22,16,4);
    cx.fillStyle="#5a3a1a";cx.fillRect(x+14,y+14,4,10);
    cx.fillStyle="#1a6a1a";cx.beginPath();cx.arc(x+16,y+10,10,0,6.28);cx.fill();
    cx.fillStyle="#228a22";cx.beginPath();cx.arc(x+12,y+6,7,0,6.28);cx.fill();
    cx.beginPath();cx.arc(x+20,y+8,6,0,6.28);cx.fill();
    cx.fillStyle="#2aaa2a";cx.beginPath();cx.arc(x+16,y+4,5,0,6.28);cx.fill();
  }else{
    cx.fillRect(x+8,y+26,16,8);cx.fillStyle="#8a5a3a";cx.fillRect(x+8,y+26,16,2);
    cx.fillStyle="#228a22";cx.beginPath();cx.arc(x+16,y+22,7,0,6.28);cx.fill();
    cx.fillStyle="#2aaa2a";cx.beginPath();cx.arc(x+14,y+18,4,0,6.28);cx.fill();
    cx.beginPath();cx.arc(x+19,y+20,4,0,6.28);cx.fill();
  }
}

function drawCoffee(x,y){
  cx.fillStyle="#3a3a3a";cx.fillRect(x+6,y+10,20,22);
  cx.fillStyle="#444";cx.fillRect(x+6,y+10,20,2);
  cx.fillStyle="#2a2a2a";cx.fillRect(x+10,y+22,12,8);
  cx.fillStyle="#eee";cx.fillRect(x+12,y+24,8,5);cx.fillStyle="#fff";cx.fillRect(x+12,y+24,8,1);
  var so=Math.sin(now()*1.5)*2;
  cx.fillStyle="rgba(255,255,255,.1)";cx.fillRect(x+14,y+20+so,2,3);cx.fillRect(x+18,y+18+so,2,4);
  cx.fillStyle="#4ade80";cx.fillRect(x+8,y+14,4,3);cx.fillStyle="#ef4444";cx.fillRect(x+14,y+14,4,3);
}

// ============ WALL DECORATIONS (unique per sector) ============
function drawWallArt(x,y,type,th){
  if(type==="gold_frame"){
    cx.fillStyle="#d4a853";cx.fillRect(x,y,22,16);
    cx.fillStyle=dk(th.accent,50);cx.fillRect(x+2,y+2,18,12);
    cx.fillStyle=al(th.accent,.15);cx.fillRect(x+4,y+4,14,8);
    cx.fillStyle="rgba(255,255,255,.03)";cx.fillRect(x+2,y+2,18,4);
  }else if(type==="stock_ticker"){
    cx.fillStyle="#111";cx.fillRect(x,y+2,30,10);
    cx.fillStyle="#0a0a0a";cx.fillRect(x+1,y+3,28,8);
    var t=now();var off=(t*20)%40;
    cx.fillStyle="#4ade80";cx.font="7px monospace";cx.fillText("+2.3%",x+3-(off%20),y+9);
    cx.fillStyle="#ef4444";cx.fillText("-0.8%",x+18-(off%20),y+9);
  }else if(type==="gold_clock"){
    cx.fillStyle="#d4a853";cx.beginPath();cx.arc(x+10,y+8,8,0,6.28);cx.fill();
    cx.fillStyle="#0e0e1e";cx.beginPath();cx.arc(x+10,y+8,6,0,6.28);cx.fill();
    cx.strokeStyle="#d4a853";cx.lineWidth=1;
    var t=now();
    cx.beginPath();cx.moveTo(x+10,y+8);cx.lineTo(x+10,y+3);cx.stroke();
    cx.beginPath();cx.moveTo(x+10,y+8);cx.lineTo(x+10+Math.cos(t)*4,y+8+Math.sin(t)*4);cx.stroke();
  }else if(type==="certificate"){
    cx.fillStyle="#d4a853";cx.fillRect(x,y,20,14);
    cx.fillStyle="#f5f0e0";cx.fillRect(x+1,y+1,18,12);
    cx.fillStyle="#333";cx.fillRect(x+4,y+4,12,1);cx.fillRect(x+3,y+7,14,1);
    cx.fillStyle="#d4a853";cx.beginPath();cx.arc(x+10,y+11,2,0,6.28);cx.fill();
  }else if(type==="gothic_mirror"){
    cx.fillStyle="#4a3060";cx.fillRect(x,y,18,22);
    cx.fillStyle="rgba(100,80,140,.3)";cx.fillRect(x+2,y+2,14,18);
    cx.fillStyle="rgba(255,255,255,.05)";cx.fillRect(x+3,y+3,6,8);
  }else if(type==="torch"){
    cx.fillStyle="#5a4020";cx.fillRect(x+8,y+10,4,14);
    cx.fillStyle="#777";cx.fillRect(x+6,y+10,8,3);
    var f=Math.sin(now()*4)>.2;
    cx.fillStyle="#f59e0b";cx.fillRect(x+7,y+4+(f?1:0),6,6);
    cx.fillStyle="#fde68a";cx.fillRect(x+8,y+5+(f?1:0),4,3);
    cx.fillStyle=al("#f59e0b",.04);cx.beginPath();cx.arc(x+10,y+8,12,0,6.28);cx.fill();
  }else if(type==="painting_dark"){
    cx.fillStyle="#2a1838";cx.fillRect(x,y,24,18);
    cx.fillStyle="#1a0a28";cx.fillRect(x+2,y+2,20,14);
    cx.fillStyle="rgba(139,92,246,.08)";cx.beginPath();cx.arc(x+12,y+10,5,0,6.28);cx.fill();
    cx.fillStyle="rgba(200,200,200,.04)";cx.fillRect(x+4,y+12,16,2);
  }else if(type==="bat_window"){
    cx.fillStyle="#1a1030";cx.fillRect(x,y,20,16);
    cx.fillStyle="rgba(60,40,100,.3)";cx.fillRect(x+2,y+2,16,12);
    // Moon
    cx.fillStyle="rgba(200,200,220,.15)";cx.beginPath();cx.arc(x+14,y+6,3,0,6.28);cx.fill();
    // Bat
    var f=Math.sin(now()*5)>.3;
    cx.fillStyle="#111";cx.fillRect(x+6,y+8,2,1);cx.fillRect(x+4+(f?0:1),y+7,2,1);cx.fillRect(x+8-(f?0:1),y+7,2,1);
  }else if(type==="war_map"){
    cx.fillStyle="#4a3a20";cx.fillRect(x,y,34,22);
    cx.fillStyle="#d4c4a0";cx.fillRect(x+2,y+2,30,18);
    cx.fillStyle="#b8a878";cx.fillRect(x+5,y+5,10,7);cx.fillRect(x+18,y+7,10,6);
    cx.fillStyle="#ef4444";cx.fillRect(x+9,y+7,2,2);cx.fillRect(x+22,y+9,2,2);cx.fillRect(x+14,y+12,2,2);
    cx.fillStyle="#3b82f6";cx.fillRect(x+7,y+10,2,2);cx.fillRect(x+26,y+8,2,2);
    // Movement arrows
    cx.strokeStyle="rgba(239,68,68,.3)";cx.lineWidth=1;
    cx.beginPath();cx.moveTo(x+10,y+8);cx.lineTo(x+14,y+12);cx.stroke();
  }else if(type==="dog_tags"){
    cx.fillStyle="#999";cx.fillRect(x+6,y+4,4,6);cx.fillRect(x+12,y+6,4,6);
    cx.fillStyle="#777";cx.fillRect(x+7,y+5,2,4);cx.fillRect(x+13,y+7,2,4);
    cx.strokeStyle="#666";cx.lineWidth=1;
    cx.beginPath();cx.moveTo(x+8,y+4);cx.quadraticCurveTo(x+10,y,x+14,y+6);cx.stroke();
  }else if(type==="compass_rose"){
    cx.fillStyle="#d4a853";cx.beginPath();cx.arc(x+10,y+10,8,0,6.28);cx.fill();
    cx.fillStyle="#1a1a1a";cx.beginPath();cx.arc(x+10,y+10,6,0,6.28);cx.fill();
    cx.fillStyle="#d4a853";
    cx.fillRect(x+9,y+3,2,4);cx.fillRect(x+9,y+14,2,4);cx.fillRect(x+3,y+9,4,2);cx.fillRect(x+14,y+9,4,2);
    cx.fillStyle="#ef4444";cx.fillRect(x+9,y+4,2,2); // N
  }else if(type==="binoculars"){
    cx.fillStyle="#333";cx.fillRect(x+4,y+6,6,10);cx.fillRect(x+12,y+6,6,10);
    cx.fillRect(x+10,y+8,2,6);
    cx.fillStyle="#1a3a5a";cx.beginPath();cx.arc(x+7,y+6,3,0,6.28);cx.fill();
    cx.beginPath();cx.arc(x+15,y+6,3,0,6.28);cx.fill();
  }else if(type==="biohazard"){
    cx.fillStyle=al("#ef4444",.6);cx.beginPath();cx.arc(x+10,y+10,8,0,6.28);cx.fill();
    cx.fillStyle="#111";cx.beginPath();cx.arc(x+10,y+10,6,0,6.28);cx.fill();
    cx.fillStyle=al("#ef4444",.5);cx.fillRect(x+9,y+3,2,5);cx.fillRect(x+4,y+12,4,2);cx.fillRect(x+14,y+12,4,2);
  }else if(type==="heartbeat"){
    cx.fillStyle="#1a0a0a";cx.fillRect(x,y+2,28,12);
    cx.strokeStyle=al("#ef4444",.6);cx.lineWidth=1;
    cx.beginPath();cx.moveTo(x+2,y+8);
    cx.lineTo(x+8,y+8);cx.lineTo(x+10,y+4);cx.lineTo(x+12,y+12);cx.lineTo(x+14,y+6);cx.lineTo(x+16,y+8);cx.lineTo(x+26,y+8);
    cx.stroke();
  }else if(type==="xray"){
    cx.fillStyle="#111";cx.fillRect(x,y,20,16);
    cx.fillStyle="rgba(100,200,255,.08)";cx.fillRect(x+2,y+2,16,12);
    cx.fillStyle="rgba(200,200,200,.15)";
    cx.fillRect(x+8,y+3,4,10); // spine
    cx.fillRect(x+5,y+5,10,2); // ribs
    cx.fillRect(x+6,y+8,8,2);
  }else if(type==="claw_marks"){
    cx.strokeStyle="rgba(200,50,50,.3)";cx.lineWidth=2;
    cx.beginPath();cx.moveTo(x+2,y+2);cx.lineTo(x+18,y+16);cx.stroke();
    cx.beginPath();cx.moveTo(x+6,y+2);cx.lineTo(x+22,y+16);cx.stroke();
    cx.beginPath();cx.moveTo(x+10,y+2);cx.lineTo(x+26,y+16);cx.stroke();
  }else if(type==="battle_map"){
    cx.fillStyle="#5a4020";cx.fillRect(x,y,30,20);
    cx.fillStyle="#c8b888";cx.fillRect(x+2,y+2,26,16);
    cx.fillStyle="#a09060";cx.fillRect(x+4,y+4,12,8);cx.fillRect(x+18,y+6,8,6);
    cx.fillStyle="#f97316";cx.fillRect(x+8,y+6,3,3);cx.fillRect(x+20,y+8,3,3);
    // Dotted route
    cx.fillStyle="rgba(249,115,22,.4)";
    for(var d=0;d<4;d++)cx.fillRect(x+10+d*3,y+10,1,1);
  }else if(type==="ancient_scroll"){
    cx.fillStyle="#c8b070";cx.fillRect(x+2,y+4,18,14);
    cx.fillStyle="#d4c080";cx.fillRect(x,y+3,4,3);cx.fillRect(x+18,y+3,4,3);
    cx.fillRect(x,y+15,4,3);cx.fillRect(x+18,y+15,4,3);
    cx.fillStyle="#6a5a30";cx.fillRect(x+5,y+7,12,1);cx.fillRect(x+5,y+10,10,1);cx.fillRect(x+5,y+13,8,1);
  }else if(type==="sun_emblem"){
    cx.fillStyle=al("#f97316",.5);cx.beginPath();cx.arc(x+10,y+10,7,0,6.28);cx.fill();
    cx.fillStyle=al("#fbbf24",.4);cx.beginPath();cx.arc(x+10,y+10,4,0,6.28);cx.fill();
    // Rays
    cx.strokeStyle=al("#f97316",.3);cx.lineWidth=1;
    for(var r=0;r<8;r++){
      var a=r*Math.PI/4;
      cx.beginPath();cx.moveTo(x+10+Math.cos(a)*7,y+10+Math.sin(a)*7);cx.lineTo(x+10+Math.cos(a)*10,y+10+Math.sin(a)*10);cx.stroke();
    }
  }else if(type==="shield_crest"){
    cx.fillStyle=th.accent;
    cx.beginPath();cx.moveTo(x+10,y+2);cx.lineTo(x+20,y+6);cx.lineTo(x+18,y+18);cx.lineTo(x+10,y+22);cx.lineTo(x+2,y+18);cx.lineTo(x,y+6);cx.closePath();cx.fill();
    cx.fillStyle=dk(th.accent,30);
    cx.beginPath();cx.moveTo(x+10,y+6);cx.lineTo(x+16,y+8);cx.lineTo(x+15,y+16);cx.lineTo(x+10,y+18);cx.lineTo(x+5,y+16);cx.lineTo(x+4,y+8);cx.closePath();cx.fill();
  }else if(type==="motivational"){
    cx.fillStyle="#222";cx.fillRect(x,y,26,16);
    cx.fillStyle="#1a1a1a";cx.fillRect(x+1,y+1,24,14);
    cx.fillStyle="#60a5fa";cx.font="bold 6px sans-serif";cx.textAlign="center";cx.fillText("SHIP IT",x+13,y+10);cx.textAlign="start";
  }else if(type==="kanban_board"){
    cx.fillStyle="#222";cx.fillRect(x,y,30,20);
    cx.fillStyle="#1a1a1a";cx.fillRect(x+1,y+1,28,18);
    // Columns
    cx.fillStyle="rgba(255,255,255,.04)";cx.fillRect(x+10,y+1,1,18);cx.fillRect(x+20,y+1,1,18);
    // Cards
    cx.fillStyle="#ef4444";cx.fillRect(x+3,y+4,5,3);
    cx.fillStyle="#fbbf24";cx.fillRect(x+13,y+4,5,3);cx.fillRect(x+13,y+9,5,3);
    cx.fillStyle="#4ade80";cx.fillRect(x+23,y+4,5,3);cx.fillRect(x+23,y+9,5,3);cx.fillRect(x+23,y+14,5,3);
  }else if(type==="wifi_symbol"){
    cx.strokeStyle="rgba(96,165,250,.4)";cx.lineWidth=1;
    cx.beginPath();cx.arc(x+10,y+14,10,Math.PI*1.2,Math.PI*1.8);cx.stroke();
    cx.beginPath();cx.arc(x+10,y+14,7,Math.PI*1.2,Math.PI*1.8);cx.stroke();
    cx.beginPath();cx.arc(x+10,y+14,4,Math.PI*1.2,Math.PI*1.8);cx.stroke();
    cx.fillStyle="rgba(96,165,250,.5)";cx.beginPath();cx.arc(x+10,y+14,2,0,6.28);cx.fill();
  }else if(type==="startup_logo"){
    cx.fillStyle="#333";cx.fillRect(x,y+2,20,16);
    cx.fillStyle="#60a5fa";cx.fillRect(x+4,y+6,5,8);
    cx.fillStyle="#818cf8";cx.fillRect(x+10,y+8,5,6);
    cx.fillStyle="#4ade80";cx.fillRect(x+4,y+6,2,2);
  }
}

// ============ CHARACTER SPRITE (improved with smooth animation) ============
function drawChar(x,y,skin,shirt,hair,hIdx,walkPhase,seated){
  cx.save();
  if(!seated){
    cx.fillStyle="rgba(0,0,0,.2)";
    cx.beginPath();cx.ellipse(x+16,y+32,8,3,0,0,6.28);cx.fill();
  }
  // Walk bob
  var bob=0;
  if(!seated&&walkPhase>0){bob=Math.sin(walkPhase*Math.PI)*1.5}
  var by=y-bob;
  if(seated){
    // Seated pose
    cx.fillStyle=shirt;cx.fillRect(x+10,by+16,12,7);
    // Arms forward (typing)
    cx.fillStyle=shirt;cx.fillRect(x+6,by+18,5,3);cx.fillRect(x+21,by+18,5,3);
    cx.fillStyle=skin;cx.fillRect(x+5,by+20,4,2);cx.fillRect(x+23,by+20,4,2);
  }else{
    // Walking legs
    var lo=walkPhase>0?Math.sin(walkPhase*Math.PI*2)*3:0;
    cx.fillStyle=dk(shirt,50);
    cx.fillRect(x+11,by+24+lo,4,5);cx.fillRect(x+17,by+24-lo,4,5);
    // Shoes
    cx.fillStyle="#1a1a1a";
    cx.fillRect(x+10,by+28+lo,5,3);cx.fillRect(x+17,by+28-lo,5,3);
    // Body
    cx.fillStyle=shirt;cx.fillRect(x+9,by+15,14,10);
    cx.fillStyle=lt(shirt,12);cx.fillRect(x+13,by+15,6,2); // collar
    // Arms
    cx.fillStyle=shirt;cx.fillRect(x+5,by+16,5,6);cx.fillRect(x+22,by+16,5,6);
    cx.fillStyle=skin;cx.fillRect(x+5,by+21,4,2);cx.fillRect(x+23,by+21,4,2);
  }
  // Head
  cx.fillStyle=skin;cx.fillRect(x+10,by+5,12,10);cx.fillRect(x+13,by+14,6,2);
  // Hair styles
  cx.fillStyle=hair;
  var hi=hIdx%6;
  if(hi===0){cx.fillRect(x+9,by+3,14,5);cx.fillRect(x+9,by+5,2,3);cx.fillRect(x+21,by+5,2,3);cx.fillRect(x+11,by+2,4,2);cx.fillRect(x+17,by+2,4,2)}
  else if(hi===1){cx.fillRect(x+9,by+3,14,5);cx.fillRect(x+9,by+5,3,4);cx.fillRect(x+20,by+5,3,3)}
  else if(hi===2){cx.fillRect(x+10,by+4,12,3);cx.fillRect(x+9,by+5,2,2);cx.fillRect(x+21,by+5,2,2)}
  else if(hi===3){cx.fillRect(x+8,by+3,16,5);cx.fillRect(x+8,by+5,3,6);cx.fillRect(x+21,by+5,3,6);cx.fillRect(x+8,by+10,3,3);cx.fillRect(x+21,by+10,3,3)}
  else if(hi===4){cx.fillRect(x+13,by+1,6,3);cx.fillRect(x+10,by+4,12,3);cx.fillRect(x+9,by+5,2,2);cx.fillRect(x+21,by+5,2,2)}
  else{cx.fillRect(x+9,by+2,14,5);cx.fillRect(x+8,by+4,3,5);cx.fillRect(x+21,by+4,3,5)}
  // Eyes
  cx.fillStyle="#fff";cx.fillRect(x+12,by+9,3,3);cx.fillRect(x+17,by+9,3,3);
  cx.fillStyle="#111";cx.fillRect(x+13,by+10,2,2);cx.fillRect(x+18,by+10,2,2);
  // Mouth
  cx.fillStyle=dk(skin,25);cx.fillRect(x+14,by+13,4,1);
  cx.restore();
}

// ============ STATUS EFFECTS ============
function drawStatus(x,y,status,j){
  var sc={working:"#4ade80",idle:"#888",done:"#60a5fa",waiting:"#fbbf24",talking:"#c084fc",error:"#f87171"};
  var c=sc[status]||"#888";
  var t=now();

  if(status==="working"){
    for(var p=0;p<4;p++){
      var a=t*1.5+p*1.57+j;
      var px=x+16+Math.cos(a)*12,py=y+10+Math.sin(a)*8;
      var op=.3+.4*Math.sin(t*2+p);
      cx.fillStyle=al("#4ade80",op);
      cx.fillRect(Math.floor(px),Math.floor(py),2,2);
    }
  }else if(status==="talking"){
    var by=y-10+Math.sin(t*1.5)*1.5;
    cx.fillStyle="#fff";cx.fillRect(x+18,by-10,22,12);cx.fillRect(x+20,by+2,4,4);
    var dp=Math.floor(t*2)%4;
    for(var d=0;d<3;d++){cx.fillStyle=d<=dp?"#444":"#ccc";cx.fillRect(x+21+d*6,by-5,3,3)}
  }else if(status==="done"){
    var by2=y-4+Math.sin(t*.8)*2;
    cx.fillStyle=al("#60a5fa",.7);cx.fillRect(x+12,by2,8,8);
    cx.fillStyle="#fff";cx.fillRect(x+14,by2+4,2,3);cx.fillRect(x+16,by2+2,3,2);
  }else if(status==="error"){
    if(Math.sin(t*3)>.0){
      cx.fillStyle="#f87171";cx.fillRect(x+12,y-4,8,8);
      cx.fillStyle="#fff";cx.fillRect(x+14,y-2,1,4);cx.fillRect(x+17,y-2,1,4);cx.fillRect(x+15,y-1,1,2);cx.fillRect(x+16,y,1,2);
    }
  }else if(status==="waiting"){
    var by3=y-4+Math.sin(t*.6)*2;
    cx.fillStyle=al("#fbbf24",.6);cx.fillRect(x+13,by3,6,8);
    cx.fillStyle="#fff";cx.fillRect(x+14,by3+1,4,3);cx.fillStyle="#fbbf24";cx.fillRect(x+15,by3+2,2,1);
  }

  // Status dot with glow
  cx.fillStyle=al(c,.2);cx.beginPath();cx.arc(x+24,y-2,5,0,6.28);cx.fill();
  cx.fillStyle=c;cx.beginPath();cx.arc(x+24,y-2,3,0,6.28);cx.fill();
}

// --- MISSING FURNITURE (was placeholder) ---
function drawCobweb(x,y){
  cx.strokeStyle="rgba(255,255,255,.08)";cx.lineWidth=1;
  // Main web strands from corner
  cx.beginPath();cx.moveTo(x,y);cx.lineTo(x+28,y+10);cx.stroke();
  cx.beginPath();cx.moveTo(x,y);cx.lineTo(x+20,y+24);cx.stroke();
  cx.beginPath();cx.moveTo(x,y);cx.lineTo(x+10,y+28);cx.stroke();
  cx.beginPath();cx.moveTo(x,y);cx.lineTo(x+28,y+20);cx.stroke();
  // Cross threads (curved)
  cx.strokeStyle="rgba(255,255,255,.05)";
  cx.beginPath();cx.moveTo(x+8,y+2);cx.quadraticCurveTo(x+6,y+6,x+2,y+8);cx.stroke();
  cx.beginPath();cx.moveTo(x+18,y+4);cx.quadraticCurveTo(x+12,y+12,x+4,y+16);cx.stroke();
  cx.beginPath();cx.moveTo(x+26,y+8);cx.quadraticCurveTo(x+16,y+16,x+6,y+24);cx.stroke();
  // Tiny spider
  cx.fillStyle="rgba(40,30,30,.6)";cx.fillRect(x+14,y+12,3,3);
  cx.fillStyle="rgba(40,30,30,.4)";cx.fillRect(x+12,y+13,2,1);cx.fillRect(x+17,y+13,2,1);
}

function drawChainFence(x,y){
  // Chain-link fence section
  cx.fillStyle="#555";cx.fillRect(x+4,y+6,2,28);cx.fillRect(x+26,y+6,2,28);
  cx.fillStyle="#666";cx.fillRect(x+2,y+4,28,3);cx.fillRect(x+2,y+32,28,3);
  // Chain links pattern
  cx.strokeStyle="rgba(150,150,150,.25)";cx.lineWidth=1;
  for(var r=0;r<4;r++){
    for(var c2=0;c2<3;c2++){
      var lx=x+8+c2*7,ly=y+9+r*6;
      cx.beginPath();cx.ellipse(lx,ly,3,2.5,0.3,0,6.28);cx.stroke();
    }
  }
  // Rust spots
  cx.fillStyle="rgba(160,80,40,.1)";cx.fillRect(x+10,y+14,3,2);cx.fillRect(x+20,y+24,2,3);
}

function drawPingPong(x,y,th){
  // Table
  cx.fillStyle="#1a6030";cx.fillRect(x+2,y+14,28,18);
  cx.fillStyle="#1a7038";cx.fillRect(x+2,y+14,28,2);
  // Table legs
  cx.fillStyle="#555";cx.fillRect(x+4,y+32,3,6);cx.fillRect(x+25,y+32,3,6);
  // Net
  cx.fillStyle="#ddd";cx.fillRect(x+15,y+12,2,8);
  cx.fillStyle="rgba(255,255,255,.15)";cx.fillRect(x+8,y+14,16,1);
  // Center line
  cx.fillStyle="rgba(255,255,255,.12)";cx.fillRect(x+2,y+22,28,1);
  // Ball (animated bounce)
  var t=now();var bx=x+10+Math.sin(t*2)*6,by2=y+16+Math.abs(Math.sin(t*3))*4;
  cx.fillStyle="#f5f5f5";cx.beginPath();cx.arc(bx,by2,2,0,6.28);cx.fill();
  // Paddles
  cx.fillStyle="#ef4444";cx.fillRect(x+6,y+16,3,5);
  cx.fillStyle="#3b82f6";cx.fillRect(x+23,y+18,3,5);
}

// ============ FURNITURE DISPATCHER ============
function drawFurniture(x,y,name,th){
  switch(name){
    case"desk_exec":drawDeskExec(x,y,th);break;
    case"desk_antique":drawDeskAntique(x,y,th);break;
    case"desk_tactical":drawDeskTactical(x,y,th);break;
    case"desk_lab":drawDeskLab(x,y,th);break;
    case"desk_commander":drawDeskCommander(x,y,th);break;
    case"desk_modern":drawDeskModern(x,y,th);break;
    case"bookshelf_wood":drawBookshelfWood(x,y,th);break;
    case"bookshelf_dark":drawBookshelfDark(x,y,th);break;
    case"plant_palm":drawPlant(x,y,true);break;
    case"plant_sm":drawPlant(x,y,false);break;
    case"coffee_premium":case"coffee":drawCoffee(x,y);break;
    case"globe":drawGlobe(x,y);break;
    case"trophy_case":drawTrophyCase(x,y,th);break;
    case"candelabra":drawCandelabra(x,y,th);break;
    case"skull_shelf":drawSkullShelf(x,y,th);break;
    case"potion_shelf":drawPotionShelf(x,y,th);break;
    case"cobweb_corner":drawCobweb(x,y);break;
    case"radar_console":drawRadarConsole(x,y,th);break;
    case"ammo_crate":drawAmmoCrate(x,y);break;
    case"sandbag_wall":drawSandbagWall(x,y);break;
    case"radio_station":drawRadioStation(x,y,th);break;
    case"weapon_rack":drawWeaponRack(x,y);break;
    case"specimen_jar":drawSpecimenJar(x,y);break;
    case"blood_tank":drawBloodTank(x,y);break;
    case"tesla_coil":drawTeslaCoil(x,y,th);break;
    case"warning_sign":drawWarningSign(x,y);break;
    case"chain_fence":drawChainFence(x,y);break;
    case"strategy_table":drawStrategyTable(x,y,th);break;
    case"flag_stand":drawFlagStand(x,y,th);break;
    case"periscope":drawPeriscope(x,y);break;
    case"supply_crate":drawAmmoCrate(x,y);break;
    case"medal_display":drawTrophyCase(x,y,th);break;
    case"whiteboard":drawWhiteboard(x,y);break;
    case"bean_bag":drawBeanBag(x,y,th);break;
    case"water_cooler":drawWaterCooler(x,y);break;
    case"ping_pong":drawPingPong(x,y,th);break;
    case"neon_sign":drawNeonSign(x,y,th);break;
    default:drawPlant(x,y,false);
  }
}

// ============ CHAIR ============
function drawChair(x,y,th){
  cx.fillStyle="#222";cx.fillRect(x+4,y+20,16,2);
  cx.fillRect(x+6,y+22,2,2);cx.fillRect(x+16,y+22,2,2);cx.fillRect(x+11,y+22,2,2);
  cx.fillStyle="#333";cx.fillRect(x+11,y+14,2,8);
  cx.fillStyle=dk(th.accent||"#666",60);
  cx.fillRect(x+4,y+10,16,6);cx.fillStyle=dk(th.accent||"#666",40);cx.fillRect(x+4,y+10,16,1);
  cx.fillRect(x+6,y+2,12,10);cx.fillStyle=dk(th.accent||"#666",30);cx.fillRect(x+6,y+2,12,1);
  cx.fillStyle="#333";cx.fillRect(x+3,y+8,3,2);cx.fillRect(x+18,y+8,3,2);
}

// ============ RUG ============
function drawRug(x,y,w,h,color){
  cx.fillStyle=al(color,.1);cx.fillRect(x,y,w,h);
  cx.fillStyle=al(color,.18);
  cx.fillRect(x+3,y+3,w-6,1);cx.fillRect(x+3,y+h-4,w-6,1);
  cx.fillRect(x+3,y+3,1,h-6);cx.fillRect(x+w-4,y+3,1,h-6);
  cx.fillStyle=al(color,.06);cx.fillRect(x+6,y+6,w-12,h-12);
  // Corner decorations
  cx.fillStyle=al(color,.12);
  cx.fillRect(x+4,y+4,3,3);cx.fillRect(x+w-7,y+4,3,3);
  cx.fillRect(x+4,y+h-7,3,3);cx.fillRect(x+w-7,y+h-7,3,3);
}

// ============ ROOM DRAWING (each room unique via sector theme) ============
function drawRoom(rx,ry,rw,rh,sala,setor,idx){
  var th=THEMES[setor.tema]||THEMES.startup;
  var tiles=getTiles(setor.tema);
  var act=sala.tem_atividade;
  var furn=th.furniture||[];
  var wart=th.wallArt||[];

  // Room floor tiles
  var tw=Math.floor(rw/T),tlh=Math.floor(rh/T);
  for(var ty=0;ty<tlh;ty++)for(var tx=0;tx<tw;tx++){
    var ti=4+((tx*3+ty*5+idx*2)%4);
    cx.drawImage(tiles[ti%tiles.length],rx+tx*T,ry+ty*T);
  }

  // Decorative rug
  drawRug(rx+T*2,ry+rh-T*3,rw-T*4,T*2,th.accent);

  // WALLS
  drawWall(rx-4,ry-22,rw+8,th);
  drawSideWall(rx-4,ry-14,rh+18,th,true);
  drawSideWall(rx+rw+4,ry-14,rh+18,th,false);

  // Bottom wall with door
  var doorW=30;var doorX=rx+rw/2-doorW/2;
  cx.fillStyle=th.wallFront;
  cx.fillRect(rx-4,ry+rh,doorX-rx+4,8);cx.fillRect(doorX+doorW,ry+rh,(rx+rw+4)-(doorX+doorW),8);
  // Door
  cx.fillStyle="#5a4a3a";cx.fillRect(doorX,ry+rh-2,doorW,10);
  cx.fillStyle="#7a6a50";cx.fillRect(doorX+2,ry+rh,doorW-4,7);
  cx.fillStyle="#d4a853";cx.fillRect(doorX+doorW-7,ry+rh+2,2,2);
  // Welcome mat
  cx.fillStyle=al(th.accent,.06);cx.fillRect(doorX-4,ry+rh+8,doorW+8,6);

  // Wall decorations (UNIQUE per sector - from wallArt array)
  drawWallArt(rx+18,ry-18,wart[idx%wart.length],th);
  if(rw>T*7)drawWallArt(rx+rw-62,ry-18,wart[(idx+2)%wart.length],th);

  // FURNITURE LAYOUT - 3 workstations + unique extras
  // Workstations (first 3 items in furniture array are desk types)
  drawFurniture(rx+10,ry+10,furn[0]||"desk_modern",th);
  drawChair(rx+18,ry+38,th);
  drawFurniture(rx+rw-66,ry+10,furn[1]||"desk_modern",th);
  drawChair(rx+rw-58,ry+38,th);
  if(rw>=T*8){
    drawFurniture(rx+rw/2-28,ry+rh-58,furn[2]||"desk_modern",th);
    drawChair(rx+rw/2-20,ry+rh-32,th);
  }

  // Unique sector decorations (items 3-7 from furniture array)
  var ex=furn.slice(3);
  if(ex.length>0)drawFurniture(rx+rw-T-6,ry+rh-T-16,ex[idx%ex.length],th);
  if(ex.length>1)drawFurniture(rx+4,ry+rh-T-16,ex[(idx+1)%ex.length],th);
  if(ex.length>2&&rw>=T*9)drawFurniture(rx+rw/2-16,ry+4,ex[(idx+2)%ex.length],th);

  // Active room glow (smooth pulsing)
  if(act){
    cx.save();
    var gi=.3+.2*Math.sin(now()*1.2);
    cx.shadowColor=th.accent;cx.shadowBlur=20*gi;
    cx.strokeStyle=al(th.accent,gi*.4);cx.lineWidth=2;
    cx.strokeRect(rx-3,ry-20,rw+6,rh+28);
    cx.restore();
  }

  // Hover highlight
  if(hR===sala.canal_id){
    cx.fillStyle="rgba(255,255,255,.03)";cx.fillRect(rx,ry,rw,rh);
    cx.strokeStyle="rgba(255,255,255,.12)";cx.lineWidth=1;
    cx.strokeRect(rx-4,ry-20,rw+8,rh+28);
  }

  // AGENTS (6 per room) with smooth interpolation
  var ags=sala.agentes;
  var deskPos=[
    {x:rx+26,y:ry+30},{x:rx+rw-52,y:ry+30},
    {x:rx+rw/2-28,y:ry+rh-58}
  ];
  var freePos=[
    {x:rx+T*2+8,y:ry+rh-T*2+2},{x:rx+rw/2+T,y:ry+rh-T*2+6},
    {x:rx+rw/2-T-8,y:ry+T*2+6},{x:rx+rw-T*2,y:ry+rh-T*2-2},
    {x:rx+T*2,y:ry+T*2},{x:rx+rw-T*3,y:ry+T*2+4}
  ];
  var t=now();
  var key=sala.canal_id;
  if(!agSt[key])agSt[key]={};
  for(var j=0;j<ags.length&&j<6;j++){
    var a=ags[j];
    var isDesk=j<3;
    var seated=isDesk&&(a.status==="working"||a.status==="done");
    // Target position
    var tgt;
    if(seated){tgt=deskPos[j]}
    else{tgt=freePos[j%freePos.length]}
    // Get or create agent state
    var ak=key+"_"+j;
    if(!agSt[key][j]){agSt[key][j]={x:tgt.x,y:tgt.y,st:a.status,tStart:t}}
    var st=agSt[key][j];
    // If status changed, start smooth transition
    if(st.st!==a.status){st.fromX=st.x;st.fromY=st.y;st.toX=tgt.x;st.toY=tgt.y;st.tStart=t;st.st=a.status}
    // Interpolate position (2 second transition)
    var elapsed=t-st.tStart;var prog=Math.min(1,elapsed/2);
    prog=prog*prog*(3-2*prog); // smoothstep easing
    if(st.fromX!==undefined&&prog<1){
      st.x=st.fromX+(st.toX-st.fromX)*prog;
      st.y=st.fromY+(st.toY-st.fromY)*prog;
    }else{
      st.x=tgt.x;st.y=tgt.y;st.fromX=undefined;
    }
    var px=st.x,py=st.y;
    var wf=0;
    if(a.status==="idle"){
      px+=Math.sin(t*.3+j*2.3)*18;
      py+=Math.cos(t*.25+j*1.9)*12;
      wf=(t*.8+j)%1;
    }else if(a.status==="talking"){
      px+=Math.sin(t*.5+j)*4;
    }
    // Walking animation during transition
    if(st.fromX!==undefined&&prog<1)wf=(t*1.2+j)%1;
    drawChar(px,py,a.skin,a.shirt,a.hair,j,wf,seated);
    drawStatus(px,py,a.status,j);
    cx.font='bold 8px "Segoe UI",sans-serif';
    var nw=cx.measureText(a.nome).width+8;
    cx.fillStyle="rgba(0,0,0,.75)";
    cx.fillRect(px+16-nw/2,py+T+2,nw,12);
    cx.fillStyle=a.cor;cx.textAlign="center";
    cx.fillText(a.nome,px+16,py+T+11);cx.textAlign="start";
  }

  // ============ ROOM NAMEPLATE (large, visible, with flag emoji) ============
  var npH=26;
  // Background - more opaque for contrast
  cx.fillStyle="rgba(0,0,0,.92)";
  cx.fillRect(rx-4,ry-46,rw+8,npH);
  cx.fillStyle=al(th.accent,.06);cx.fillRect(rx-4,ry-46,rw+8,npH);
  // Accent borders (top thick, bottom thin)
  cx.fillStyle=al(th.gold||"#d4a853",.5);cx.fillRect(rx-4,ry-46,rw+8,2);
  cx.fillStyle=al(th.accent,.35);cx.fillRect(rx-4,ry-46+npH-1,rw+8,1);
  // Left accent bar
  cx.fillStyle=al(th.accent,.5);cx.fillRect(rx-4,ry-44,3,npH-4);
  // Flag emoji
  var flag=getFlag(sala.lingua);
  cx.font='16px "Segoe UI Emoji","Apple Color Emoji",sans-serif';
  cx.fillText(flag,rx+6,ry-28);
  // Channel name - bigger and bolder
  cx.fillStyle="#fff";cx.font='bold 14px "Segoe UI",system-ui,sans-serif';
  var lb=sala.nome;if(lb.length>20)lb=lb.substring(0,18)+"..";
  cx.fillText(lb,rx+28,ry-29);
  // Language badge - more visible
  cx.fillStyle=al(th.accent,.3);
  cx.font="bold 11px monospace";
  var langW=cx.measureText(sala.lingua).width+14;
  cx.fillRect(rx+rw-langW-2,ry-42,langW,16);
  cx.fillStyle=th.accent;cx.fillText(sala.lingua,rx+rw-langW+5,ry-30);

  sala._rx=rx-6;sala._ry=ry-46;sala._rw=rw+12;sala._rh=rh+56;
}

// ============ FULL MAP RENDER ============
function render(setor){
  var salas=setor.salas,tema=setor.tema;
  var th=THEMES[tema]||THEMES.startup;
  var tiles=getTiles(tema);
  var cols=Math.min(4,Math.max(2,Math.ceil(Math.sqrt(salas.length))));
  var rows=Math.ceil(salas.length/cols);
  var roomW=T*10,roomH=T*8;
  var gapX=T*3,gapY=T*5;
  var padX=T*3,padTop=T*4;
  var mapW=padX*2+cols*roomW+(cols-1)*gapX;
  var mapH=padTop+rows*roomH+(rows-1)*gapY+T*3;
  var wrap=document.getElementById("mapWrap");
  var vw=wrap.clientWidth,vh=wrap.clientHeight;
  cv.width=Math.max(mapW,vw);cv.height=Math.max(mapH,vh);
  cx.imageSmoothingEnabled=false;

  // CORRIDOR FLOOR
  var tw2=Math.ceil(cv.width/T),tlh2=Math.ceil(cv.height/T);
  for(var ty=0;ty<tlh2;ty++)for(var tx=0;tx<tw2;tx++){
    var ti=(tx*7+ty*11)%4;cx.drawImage(tiles[ti],tx*T,ty*T);
  }

  // Corridor plants between rooms
  for(var ci=0;ci<cols-1;ci++){
    var ppx=padX+roomW*(ci+1)+gapX*ci+gapX/2-16;
    for(var ri=0;ri<rows;ri++){drawPlant(ppx,padTop+ri*(roomH+gapY)+roomH/2,false)}
  }

  // Ambient floating particles (themed)
  var t=now();
  cx.fillStyle=al(th.particle,.06);
  for(var p=0;p<20;p++){
    var px2=(t*15+p*137)%cv.width;
    var py2=(t*10+p*97)%cv.height;
    cx.fillRect(Math.floor(px2),Math.floor(py2),1,1);
  }

  // SECTOR BANNER
  cx.fillStyle="rgba(0,0,0,.55)";cx.fillRect(0,0,cv.width,T*2.8);
  cx.fillStyle=al(th.accent,.06);cx.fillRect(0,0,cv.width,T*2.8);
  cx.fillStyle=al(th.gold||"#d4a853",.2);cx.fillRect(0,T*2.8-1,cv.width,1);
  cx.fillStyle=th.accent;cx.font='16px "Press Start 2P",monospace';
  cx.fillText(setor.nome.toUpperCase(),T*2,T*1.4);
  cx.fillStyle="#667";cx.font='13px "Segoe UI",sans-serif';
  var activeN=salas.filter(function(s){return s.tem_atividade}).length;
  cx.fillText(salas.length+" canais  |  "+activeN+" ativos  |  "+(salas.length*6)+" agentes",T*2,T*2.2);

  // DRAW ROOMS centered
  var contentW=cols*roomW+(cols-1)*gapX;
  var offsetX=Math.max(padX,Math.floor((cv.width-contentW)/2));
  for(var i=0;i<salas.length;i++){
    var col=i%cols,row=Math.floor(i/cols);
    var rx=offsetX+col*(roomW+gapX),ry=padTop+row*(roomH+gapY);
    drawRoom(rx,ry,roomW,roomH,salas[i],setor,i);
  }
}

// ============ ANIMATION LOOP (smooth 60fps) ============
var anim=null;
function loop(){
  if(!D||!curT)return;
  var s=D.setores.find(function(s){return s.id===curT});
  if(!s)return;
  fr++;render(s);
  anim=requestAnimationFrame(loop);
}

// ============ TABS ============
function mkTabs(ss){
  var h="",icons={"$":"\uD83D\uDCB0","H":"\u265B","G":"\u2694","T":"\u2620","C":"\u26E8","D":"\u25CB","L":"\u2728"};
  for(var i=0;i<ss.length;i++){var s=ss[i];var ac=(curT===null&&i===0)||curT===s.id;
  h+='<button class="tab'+(ac?" act":"")+'" style="--c:'+s.cor+'" data-tab="'+s.id+'">'+(icons[s.icone]||s.icone)+" "+s.nome+'<span class="badge">'+s.salas.length+"</span></button>"}
  document.getElementById("tabs").innerHTML=h;
  if(curT===null&&ss.length>0)curT=ss[0].id;
}
document.getElementById("tabs").addEventListener("click",function(e){
  var t=e.target.closest(".tab");if(!t||!t.dataset.tab)return;
  curT=t.dataset.tab;hR=null;agSt={};document.getElementById("sb").classList.remove("open");
  mkTabs(D.setores);if(anim)cancelAnimationFrame(anim);loop();
});

// ============ HOVER (tooltip) ============
function fmt(n){if(!n&&n!==0)return"--";if(n>=1e6)return(n/1e6).toFixed(1)+"M";if(n>=1e3)return(n/1e3).toFixed(1)+"K";return""+n}
cv.addEventListener("mousemove",function(e){
  if(!D||!curT)return;var s=D.setores.find(function(s){return s.id===curT});if(!s)return;
  var r=cv.getBoundingClientRect(),mx=(e.clientX-r.left)*(cv.width/r.width),my=(e.clientY-r.top)*(cv.height/r.height);
  var f=null;
  for(var i=0;i<s.salas.length;i++){var sl=s.salas[i];if(sl._rx!==undefined&&mx>=sl._rx&&mx<=sl._rx+sl._rw&&my>=sl._ry&&my<=sl._ry+sl._rh){f=sl;break}}
  if(f){hR=f.canal_id;cv.style.cursor="pointer";
    var wk=f.agentes.filter(function(a){return a.status==="working"}).length;
    var dn=f.agentes.filter(function(a){return a.status==="done"}).length;
    tip.style.display="block";
    var tipX=e.clientX-r.left+16,tipY=e.clientY-r.top-10;
    if(tipX+230>r.width)tipX=e.clientX-r.left-240;
    if(tipY+160>r.height)tipY=r.height-170;
    if(tipY<0)tipY=10;
    tip.style.left=tipX+"px";tip.style.top=tipY+"px";
    var flag=getFlag(f.lingua);
    tip.innerHTML='<div class="tn"><span class="tf">'+flag+'</span>'+f.nome+'</div><div class="tr"><span>Idioma</span><b>'+f.lingua+'</b></div><div class="tr"><span>Inscritos</span><b>'+fmt(f.inscritos)+'</b></div><div class="tr"><span>Working</span><b style="color:#4ade80">'+wk+"/"+f.agentes.length+'</b></div><div class="tr"><span>Done</span><b style="color:#60a5fa">'+dn+'</b></div><div style="margin-top:8px;font-size:9px;color:#445;text-align:center">Click para abrir</div>';
  }else{hR=null;cv.style.cursor="default";tip.style.display="none"}
});
cv.addEventListener("mouseleave",function(){hR=null;tip.style.display="none"});

// ============ CLICK ============
cv.addEventListener("click",function(e){
  if(!D||!curT)return;var s=D.setores.find(function(s){return s.id===curT});if(!s)return;
  var r=cv.getBoundingClientRect(),mx=(e.clientX-r.left)*(cv.width/r.width),my=(e.clientY-r.top)*(cv.height/r.height);
  for(var i=0;i<s.salas.length;i++){var sl=s.salas[i];if(sl._rx!==undefined&&mx>=sl._rx&&mx<=sl._rx+sl._rw&&my>=sl._ry&&my<=sl._ry+sl._rh){openRoom(sl.canal_id);return}}
});

// ============ SIDEBAR ============
function openRoom(id){
  document.getElementById("sb").classList.add("open");
  var x=new XMLHttpRequest();x.open("GET","/api/mission-control/sala/"+id);
  x.onload=function(){if(x.status===200)renderSB(JSON.parse(x.responseText))};x.send();
}
document.getElementById("sbX").addEventListener("click",function(){document.getElementById("sb").classList.remove("open")});
function renderSB(d){
  var c=d.canal;
  var flag=getFlag(c.lingua);
  document.getElementById("sbT").textContent=flag+" "+c.nome+" ["+c.lingua+"]";
  var sl={working:"Trabalhando",idle:"Livre",done:"Concluido",waiting:"Aguardando",talking:"Conversando",error:"Erro"};
  var sc={working:"#4ade80",idle:"#888",done:"#60a5fa",waiting:"#fbbf24",talking:"#c084fc",error:"#f87171"};
  var ag="";for(var i=0;i<d.agentes.length;i++){var a=d.agentes[i];
    ag+='<div class="sb-card" style="--ac:'+a.cor+'"><div class="cd" style="background:'+sc[a.status]+';color:'+sc[a.status]+'"></div><div class="cn">'+a.nome+'</div><div class="cs">'+sl[a.status]+'</div><div class="ct">'+a.tarefas_hoje+" tarefas</div></div>"}
  document.getElementById("sbA").innerHTML=ag;
  var ch="<h4>CHAT</h4>";for(var i=0;i<d.mensagens.length;i++){var m=d.mensagens[i];
    ch+='<div class="msg" style="--mc:'+m.de_cor+'"><div class="mh"><span style="color:#445;font-size:9px">'+m.hora+'</span> <b>'+m.de+'</b><span class="arr">\u279C</span><span style="color:#667">'+m.para+"</span></div><div class=\"mt\">"+m.texto+"</div></div>"}
  document.getElementById("sbC").innerHTML=ch;
  var tk="<h4>TAREFAS</h4>";var ti2={done:"\u2705",working:"\u26A1",pending:"\u23F3"};
  for(var i=0;i<d.tarefas.length;i++){var t=d.tarefas[i];
    tk+='<div class="tsk"><span class="ti">'+(ti2[t.status]||"\u25CF")+'</span><div><div class="td">'+t.desc+'</div><div class="tm"><span style="color:'+t.agente_cor+'">'+t.agente+"</span> \u00B7 "+t.hora+(t.duracao?" \u00B7 "+t.duracao:"")+"</div></div></div>"}
  document.getElementById("sbK").innerHTML=tk;
  var df=c.inscritos_diff,dc2=df>0?"pos":(df<0?"neg":""),dp=df>0?"+":"";
  document.getElementById("sbI").innerHTML='<div class="ib"><label>Inscritos</label><span>'+fmt(c.inscritos)+'</span></div><div class="ib"><label>Crescimento</label><span class="'+dc2+'">'+(df!==null?dp+df+"/dia":"--")+'</span></div><div class="ib"><label>Videos</label><span>'+(c.total_videos||"--")+'</span></div><div class="ib"><label>Subnicho</label><span>'+(c.subnicho||"--")+"</span></div>";
}

// ============ DATA LOADING ============
// Agent positions interpolate smoothly via agSt when status changes.
var firstLoad=true;
function load(){
  var x=new XMLHttpRequest();x.open("GET","/api/mission-control/status");
  x.onload=function(){if(x.status!==200)return;
    var nd=JSON.parse(x.responseText);
    document.getElementById("s0").textContent=nd.stats.total_salas;
    document.getElementById("s1").textContent=nd.stats.total_agentes;
    document.getElementById("s2").textContent=nd.stats.agentes_working;
    document.getElementById("s3").textContent=nd.stats.tarefas_hoje;
    D=nd;
    if(firstLoad){mkTabs(D.setores);loop();firstLoad=false}
    else{mkTabs(D.setores)}
  };x.send()}
load();setInterval(load,8000);

// Resize handler - adapt canvas to window size
window.addEventListener("resize",function(){tileCache={};if(D&&curT){if(anim)cancelAnimationFrame(anim);loop()}});
</script>
</body>
</html>"""


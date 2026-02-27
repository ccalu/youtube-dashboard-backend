"""
Mission Control v2 - Pixel Art Office com 7 Agentes do Ecossistema
Canvas 2D com sprites pixel art, tiles, mobilia e agentes animados.

Cada subnicho = 1 aba/setor com tema visual unico
Cada canal = 1 sala com 7 agentes (Ecossistema completo)
Agentes implementados mostram dados reais, placeholders mostram "EM BREVE"
Click no agente abre painel interativo com acoes
"""

import re
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
    'Licoes de Vida': {'cor': '#eab308', 'icone': 'L', 'tema': 'wisdom',
                       'floor': '#3a3418', 'wall': '#2a2410', 'accent': '#fbbf24'},
}

# ===========================================================
# 7 AGENTES DO ECOSSISTEMA
# ===========================================================

AGENTES_V2_TEMPLATE = [
    {
        'id': 1, 'tipo': 'estrutura_copy', 'nome': 'Estrutura de Copy',
        'camada': 1, 'cor': '#22c55e',
        'skin': '#ffcc99', 'shirt': '#22c55e', 'hair': '#4a3728',
        'descricao': 'Estrutura de Copy - Analisa performance por estrutura A-G',
        'implementado': True,
        'api_run': '/api/analise-completa/{channel_id}',
        'api_latest': '/api/analise-copy/{channel_id}/latest',
        'api_historico': '/api/analise-copy/{channel_id}/historico',
        'analysis_table': 'copy_analysis_runs',
    },
    {
        'id': 2, 'tipo': 'autenticidade', 'nome': 'Autenticidade',
        'camada': 1, 'cor': '#ef4444',
        'skin': '#e8b88a', 'shirt': '#ef4444', 'hair': '#1a1a1a',
        'descricao': 'Autenticidade - Score 0-100 contra politica de Inauthentic Content',
        'implementado': True,
        'api_run': '/api/analise-completa/{channel_id}',
        'api_latest': '/api/analise-autenticidade/{channel_id}/latest',
        'api_historico': '/api/analise-autenticidade/{channel_id}/historico',
        'analysis_table': 'authenticity_analysis_runs',
    },
    {
        'id': 3, 'tipo': 'micronichos', 'nome': 'Micronichos',
        'camada': 2, 'cor': '#8b5cf6',
        'skin': '#ffcc99', 'shirt': '#8b5cf6', 'hair': '#8b4513',
        'descricao': 'Micronichos - Identifica subcategorias tematicas que viralizam',
        'implementado': False,
        'api_run': None, 'api_latest': None, 'api_historico': None,
        'analysis_table': None,
    },
    {
        'id': 4, 'tipo': 'titulo_estrutura', 'nome': 'Estrutura de Titulo',
        'camada': 2, 'cor': '#3b82f6',
        'skin': '#d4a574', 'shirt': '#3b82f6', 'hair': '#2c1810',
        'descricao': 'Estrutura de Titulo - Analisa padroes de titulo e CTR',
        'implementado': False,
        'api_run': None, 'api_latest': None, 'api_historico': None,
        'analysis_table': None,
    },
    {
        'id': 5, 'tipo': 'temas', 'nome': 'Temas',
        'camada': 2, 'cor': '#f97316',
        'skin': '#ffcc99', 'shirt': '#f97316', 'hair': '#c0392b',
        'descricao': 'Temas - Descobre assuntos especificos com potencial viral',
        'implementado': False,
        'api_run': None, 'api_latest': None, 'api_historico': None,
        'analysis_table': None,
    },
    {
        'id': 6, 'tipo': 'recomendador', 'nome': 'Recomendador',
        'camada': 3, 'cor': '#eab308',
        'skin': '#e8b88a', 'shirt': '#eab308', 'hair': '#34495e',
        'descricao': 'Recomendador - Cerebro estrategico que cruza tudo e sugere proximos videos',
        'implementado': False,
        'api_run': None, 'api_latest': None, 'api_historico': None,
        'analysis_table': None,
    },
    {
        'id': 7, 'tipo': 'concorrentes', 'nome': 'Concorrentes',
        'camada': 4, 'cor': '#06b6d4',
        'skin': '#ffcc99', 'shirt': '#06b6d4', 'hair': '#1a1a1a',
        'descricao': 'Concorrentes - Intel competitiva via audiencia do YouTube',
        'implementado': False,
        'api_run': None, 'api_latest': None, 'api_historico': None,
        'analysis_table': None,
    },
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


def build_agent_list(canal_id, agent_statuses=None):
    """Build 7 agents for a room with real or default statuses."""
    if agent_statuses is None:
        agent_statuses = {}

    agentes = []
    for t in AGENTES_V2_TEMPLATE:
        real = agent_statuses.get(t['tipo'], {})
        if t['implementado']:
            status = real.get('status', 'idle')
        else:
            status = 'waiting'

        agentes.append({
            'id': t['id'],
            'tipo': t['tipo'],
            'nome': t['nome'],
            'camada': t['camada'],
            'cor': t['cor'],
            'skin': t['skin'],
            'shirt': t['shirt'],
            'hair': t['hair'],
            'descricao': t['descricao'],
            'implementado': t['implementado'],
            'status': status,
            'last_run': real.get('last_run'),
            'extra_data': real,
            'api_run': t.get('api_run'),
            'api_latest': t.get('api_latest'),
            'api_historico': t.get('api_historico'),
        })
    return agentes


# ===========================================================
# API DATA FUNCTIONS
# ===========================================================

_mc_cache = {'data': None, 'timestamp': 0}
_MC_CACHE_TTL = 5

_mc_sala_cache = {}
_MC_SALA_CACHE_TTL = 3


async def get_agent_real_status(supabase_client, channel_id):
    """Query real agent status from analysis tables for a given yt channel_id (UC...)."""
    status = {}

    # Agent 1: Copy Analysis
    try:
        copy_resp = supabase_client.table('copy_analysis_runs') \
            .select('id,run_date,channel_avg_retention,total_videos_analyzed') \
            .eq('channel_id', channel_id) \
            .order('run_date', desc=True) \
            .limit(1) \
            .execute()
        if copy_resp.data:
            run = copy_resp.data[0]
            status['estrutura_copy'] = {
                'status': 'done',
                'last_run': run.get('run_date'),
                'videos_analyzed': run.get('total_videos_analyzed', 0),
                'avg_retention': run.get('channel_avg_retention'),
            }
        else:
            status['estrutura_copy'] = {'status': 'idle', 'last_run': None}
    except Exception:
        status['estrutura_copy'] = {'status': 'idle', 'last_run': None}

    # Agent 2: Authenticity
    try:
        auth_resp = supabase_client.table('authenticity_analysis_runs') \
            .select('id,run_date,authenticity_score,authenticity_level,has_alerts') \
            .eq('channel_id', channel_id) \
            .order('run_date', desc=True) \
            .limit(1) \
            .execute()
        if auth_resp.data:
            run = auth_resp.data[0]
            status['autenticidade'] = {
                'status': 'done' if not run.get('has_alerts') else 'error',
                'last_run': run.get('run_date'),
                'score': run.get('authenticity_score'),
                'level': run.get('authenticity_level'),
                'has_alerts': run.get('has_alerts', False),
            }
        else:
            status['autenticidade'] = {'status': 'idle', 'last_run': None}
    except Exception:
        status['autenticidade'] = {'status': 'idle', 'last_run': None}

    # Agents 3-7: Not yet implemented
    for ag in AGENTES_V2_TEMPLATE[2:]:
        status[ag['tipo']] = {'status': 'waiting', 'last_run': None}

    return status


async def get_agent_overview_batch(supabase_client):
    """Batch query agent status for ALL channels. Returns dict keyed by channel_id."""
    overview = {}

    # Latest copy analysis per channel
    try:
        copy_resp = supabase_client.table('copy_analysis_runs') \
            .select('channel_id,run_date,total_videos_analyzed') \
            .order('run_date', desc=True) \
            .execute()
        seen = set()
        for row in (copy_resp.data or []):
            cid = row.get('channel_id')
            if cid and cid not in seen:
                seen.add(cid)
                if cid not in overview:
                    overview[cid] = {}
                overview[cid]['copy'] = {
                    'status': 'done',
                    'last_run': row.get('run_date'),
                }
    except Exception:
        pass

    # Latest auth analysis per channel
    try:
        auth_resp = supabase_client.table('authenticity_analysis_runs') \
            .select('channel_id,run_date,authenticity_score,authenticity_level,has_alerts') \
            .order('run_date', desc=True) \
            .execute()
        seen = set()
        for row in (auth_resp.data or []):
            cid = row.get('channel_id')
            if cid and cid not in seen:
                seen.add(cid)
                if cid not in overview:
                    overview[cid] = {}
                overview[cid]['auth'] = {
                    'status': 'done' if not row.get('has_alerts') else 'error',
                    'last_run': row.get('run_date'),
                    'score': row.get('authenticity_score'),
                    'level': row.get('authenticity_level'),
                    'has_alerts': row.get('has_alerts', False),
                }
    except Exception:
        pass

    return overview


async def get_mission_control_data(db):
    """Build complete mission control data with real agent statuses."""
    now = time.time()
    if _mc_cache['data'] and (now - _mc_cache['timestamp']) < _MC_CACHE_TTL:
        return _mc_cache['data']

    canais = await db.get_dashboard_from_mv(tipo="nosso", limit=1000, offset=0)

    # Get OAuth channel_ids (only show channels with OAuth configured)
    # MUST use service_role client - yt_oauth_tokens has RLS enabled
    oauth_channel_ids = set()
    sr_client = getattr(db, 'supabase_service', None) or db.supabase
    try:
        oauth_resp = sr_client.table('yt_oauth_tokens').select('channel_id').execute()
        oauth_channel_ids = set(r['channel_id'] for r in (oauth_resp.data or []))
    except Exception:
        pass

    # Get yt_channels mapping (channel_name -> channel_id + copy_spreadsheet_id + avg_ctr)
    # Filter to only OAuth channels
    yt_name_map = {}  # lowercase channel_name -> channel_id
    copy_sheet_map = {}
    ctr_map = {}  # lowercase channel_name -> avg_ctr
    oauth_names = set()  # lowercase names of channels with OAuth
    try:
        yt_resp = db.supabase.table('yt_channels') \
            .select('channel_id,channel_name,copy_spreadsheet_id,avg_ctr') \
            .eq('is_active', True) \
            .execute()
        for row in (yt_resp.data or []):
            chid = row.get('channel_id')
            chname = (row.get('channel_name') or '').strip().lower()
            if chid and chname and chid in oauth_channel_ids:
                yt_name_map[chname] = chid
                oauth_names.add(chname)
                csid = row.get('copy_spreadsheet_id')
                if csid:
                    copy_sheet_map[chname] = csid
                actr = row.get('avg_ctr')
                if actr is not None:
                    ctr_map[chname] = actr
    except Exception:
        pass

    # Get latest avg_retention per channel from copy_analysis_runs
    retention_map = {}  # channel_id -> avg_retention
    try:
        ret_resp = db.supabase.table('copy_analysis_runs') \
            .select('channel_id,channel_avg_retention') \
            .order('run_date', desc=True) \
            .execute()
        for row in (ret_resp.data or []):
            chid = row.get('channel_id')
            if chid and chid not in retention_map:
                ret_val = row.get('channel_avg_retention')
                if ret_val is not None:
                    retention_map[chid] = ret_val
    except Exception:
        pass

    # Batch get agent overview
    agent_overview = await get_agent_overview_batch(db.supabase)

    grupos = {}
    for canal in canais:
        # Only include channels with OAuth configured
        # Match by exact name first, then by base name (without " (new)" suffix)
        nome_lower = (canal.get('nome_canal') or '').strip().lower()
        if nome_lower not in oauth_names:
            # Try without "(new)" or other suffixes
            base_name = re.sub(r'\s*\(.*?\)\s*$', '', nome_lower).strip()
            if base_name not in oauth_names:
                continue
            else:
                nome_lower = base_name

        sub = canal.get('subnicho') or 'Sem Categoria'
        if sub not in grupos:
            grupos[sub] = []
        grupos[sub].append(canal)

    setores = []
    total_ag = 0
    total_active = 0

    for sub, clist in sorted(grupos.items()):
        cfg = SETORES_CONFIG.get(sub, {'cor': '#666', 'icone': '?', 'tema': 'startup',
                                        'floor': '#2d2d30', 'wall': '#1a1a1e', 'accent': '#888'})
        salas = []
        for c in clist:
            cid = c['id']
            nome_lower = (c.get('nome_canal') or '').strip().lower()
            yt_channel_id = yt_name_map.get(nome_lower)
            if not yt_channel_id:
                base_name = re.sub(r'\s*\(.*?\)\s*$', '', nome_lower).strip()
                yt_channel_id = yt_name_map.get(base_name)
                if yt_channel_id:
                    nome_lower = base_name

            # Build agent statuses from overview
            ag_statuses = {}
            if yt_channel_id and yt_channel_id in agent_overview:
                ov = agent_overview[yt_channel_id]
                if 'copy' in ov:
                    ag_statuses['estrutura_copy'] = ov['copy']
                if 'auth' in ov:
                    ag_statuses['autenticidade'] = ov['auth']

            agentes = build_agent_list(cid, ag_statuses)
            active = sum(1 for a in agentes if a['status'] in ('done', 'working'))
            total_ag += len(agentes)
            total_active += active

            salas.append({
                'canal_id': cid,
                'nome': c.get('nome_canal', 'Canal'),
                'lingua': get_lingua_code(c.get('lingua')),
                'inscritos': c.get('inscritos', 0),
                'inscritos_diff': c.get('inscritos_diff', 0),
                'views_7d': c.get('views_7d', 0),
                'views_30d': c.get('views_30d', 0),
                'videos_30d': c.get('videos_30d', 0),
                'avg_ctr': ctr_map.get(nome_lower),
                'avg_retention': retention_map.get(yt_channel_id),
                'yt_channel_id': yt_channel_id,
                'agentes': [{'id': a['id'], 'nome': a['nome'], 'status': a['status'],
                              'cor': a['cor'], 'skin': a['skin'], 'shirt': a['shirt'],
                              'hair': a['hair'], 'implementado': a['implementado'],
                              'camada': a['camada']}
                             for a in agentes],
                'tem_atividade': active > 0,
            })

        # Sort salas by inscritos (most subscribers first)
        salas.sort(key=lambda x: x.get('inscritos', 0), reverse=True)

        setores.append({
            'id': sanitize_id(sub), 'nome': sub,
            'cor': cfg['cor'], 'icone': cfg['icone'], 'tema': cfg['tema'],
            'floor': cfg.get('floor', '#2d2d30'),
            'wall': cfg.get('wall', '#1a1a1e'),
            'accent': cfg.get('accent', '#888'),
            'salas': salas,
        })

    result = {
        'stats': {
            'total_salas': sum(len(s['salas']) for s in setores),
            'total_agentes': total_ag,
            'agentes_active': total_active,
        },
        'setores': setores,
    }
    _mc_cache['data'] = result
    _mc_cache['timestamp'] = now
    return result


async def get_sala_detail(db, canal_id):
    """Return detailed room data with real agent statuses and yt_channel_id."""
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

    # Resolve yt_channel_id
    yt_channel_id = None
    copy_spreadsheet_id = None
    try:
        yt_resp = db.supabase.table('yt_channels') \
            .select('channel_id,copy_spreadsheet_id') \
            .eq('canal_monitorado_id', canal_id) \
            .limit(1) \
            .execute()
        if yt_resp.data:
            yt_channel_id = yt_resp.data[0].get('channel_id')
            copy_spreadsheet_id = yt_resp.data[0].get('copy_spreadsheet_id')
    except Exception:
        pass

    # Get real agent statuses
    agent_statuses = {}
    if yt_channel_id:
        agent_statuses = await get_agent_real_status(db.supabase, yt_channel_id)

    agentes = build_agent_list(canal_id, agent_statuses)

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
        'yt_channel_id': yt_channel_id,
        'copy_spreadsheet_id': copy_spreadsheet_id,
        'agentes': agentes,
    }
    _mc_sala_cache[ck] = {'data': result, 'timestamp': now}
    return result


async def get_agent_report(supabase_client, channel_id, agent_type):
    """Return the latest report for a specific agent on a specific channel."""
    if agent_type == 'estrutura_copy':
        try:
            resp = supabase_client.table('copy_analysis_runs') \
                .select('*') \
                .eq('channel_id', channel_id) \
                .order('run_date', desc=True) \
                .limit(1) \
                .execute()
            if resp.data:
                return {'implemented': True, 'data': resp.data[0]}
            return {'implemented': True, 'data': None, 'message': 'Nenhum relatorio encontrado'}
        except Exception as e:
            return {'implemented': True, 'error': str(e)}

    elif agent_type == 'autenticidade':
        try:
            resp = supabase_client.table('authenticity_analysis_runs') \
                .select('*') \
                .eq('channel_id', channel_id) \
                .order('run_date', desc=True) \
                .limit(1) \
                .execute()
            if resp.data:
                return {'implemented': True, 'data': resp.data[0]}
            return {'implemented': True, 'data': None, 'message': 'Nenhum relatorio encontrado'}
        except Exception as e:
            return {'implemented': True, 'error': str(e)}

    else:
        return {'implemented': False, 'message': 'Este agente ainda nao foi implementado'}



# ===========================================================
# HTML - Mission Control v2 (Pixel Art Office)
# ===========================================================

MISSION_CONTROL_HTML = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Mission Control</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#08081a;color:#e0e0e0;font-family:'Segoe UI',system-ui,sans-serif;margin:0;min-height:100vh;display:flex;flex-direction:column;overflow-x:hidden}
#header{background:#0d0d24;border-bottom:1px solid #1a1a3a;padding:8px 16px;display:flex;align-items:center;justify-content:space-between;flex-shrink:0}
#header h1{font-size:18px;color:#00d4aa;font-family:monospace;letter-spacing:2px}
#stats{font-size:12px;color:#888;font-family:monospace}
#stats span{color:#00d4aa;margin:0 4px}
#tabs{background:#0a0a1e;border-bottom:1px solid #1a1a3a;padding:4px 12px;display:flex;gap:4px;flex-shrink:0;overflow-x:auto}
.tab{padding:6px 14px;border-radius:4px;cursor:pointer;font-size:12px;font-family:monospace;border:1px solid transparent;transition:all 0.2s;white-space:nowrap;background:transparent;color:#ccc;display:inline-flex;align-items:center;gap:6px}
.tab:hover{border-color:#555 !important;background:rgba(255,255,255,0.06);color:#ddd !important}
.tab-active{border-color:currentColor !important;background:rgba(255,255,255,0.1) !important;font-weight:600}
#main{flex:1;display:flex;position:relative;overflow-x:hidden}
#mapWrap{flex:1;position:relative}
canvas{display:block;cursor:pointer;width:100%}
#sb{width:360px;background:#0d0d24;border-left:1px solid #1a1a3a;display:none;overflow-y:auto;padding:16px;position:fixed;right:0;top:0;bottom:0;z-index:10;box-shadow:-4px 0 20px rgba(0,0,0,0.5)}
.sb-close{position:absolute;top:8px;right:12px;cursor:pointer;font-size:20px;color:#666;z-index:10}
.sb-close:hover{color:#fff}
.sb-header{border-left:3px solid #888;padding:8px 12px;margin-bottom:16px}
.sb-name{font-size:16px;font-weight:600;margin-top:8px}
.sb-role{font-size:11px;color:#888;text-transform:uppercase;letter-spacing:1px}
.sb-status{display:inline-block;padding:2px 10px;border-radius:10px;font-size:10px;font-weight:600;margin-top:6px;letter-spacing:1px}
.st-done{background:#22c55e33;color:#4ade80}
.st-idle{background:#88888833;color:#aaa}
.st-error{background:#ef444433;color:#f87171}
.st-waiting{background:#eab30833;color:#fbbf24}
.st-working,.st-running{background:#3b82f633;color:#60a5fa}
.st-unknown{background:#33333333;color:#666}
.sb-section{margin:12px 0;padding:8px 0;border-top:1px solid #1a1a3a}
.sb-label{font-size:10px;color:#666;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px}
.sb-value{font-size:14px}
.sb-desc{font-size:12px;color:#999;line-height:1.5}
.sb-actions{margin-top:16px;display:flex;flex-direction:column;gap:8px}
.sb-btn{display:block;padding:8px 16px;border-radius:6px;text-align:center;font-size:12px;font-family:monospace;cursor:pointer;border:1px solid #333;background:#111;color:#ccc;text-decoration:none;transition:all 0.2s}
.sb-btn:hover{border-color:#555;background:#1a1a2e}
.sb-btn-primary{background:#1a3a1a;border-color:#22c55e44;color:#4ade80}
.sb-btn-primary:hover{background:#224422}
.sb-report{margin-top:16px;max-height:400px;overflow-y:auto}
.rpt-header{font-weight:600;color:#00d4aa;padding:4px 0;margin-top:8px;font-size:12px}
.rpt-alert{color:#f87171;font-size:11px;padding:2px 0}
.rpt-line{font-size:11px;color:#999;padding:1px 0;line-height:1.4}
#legend{width:180px;background:transparent;padding:8px;overflow-y:auto;flex-shrink:0}
.legend-title{font-size:10px;color:#666;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;padding-bottom:4px;border-bottom:1px solid #1a1a3a20}
.legend-item{display:flex;align-items:center;gap:6px;padding:4px 2px;font-size:11px;color:#ccc}
.legend-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.legend-sprite{flex-shrink:0;image-rendering:pixelated}
.legend-name{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
@media(max-width:1024px){#legend{display:none}#sb{width:300px!important}}
@media(max-width:768px){#legend{display:none}#header h1{font-size:14px}#stats{font-size:10px}.tab{padding:4px 10px;font-size:10px}#sb{width:100%!important}}
</style>
</head>
<body>
<div id="header">
  <h1>MISSION CONTROL</h1>
  <div id="stats">
    Salas <span id="s0">-</span> |
    Agentes <span id="s1">-</span> |
    Ativos <span id="s2">-</span>
  </div>
</div>
<div id="tabs"></div>
<div id="main">
  <div id="legend"></div>
  <div id="mapWrap"><canvas id="cv"></canvas></div>
  <div id="sb"></div>
</div>
<script>
// ============================================================
// Mission Control v2 - Part 1: Sprite Data & Cache System
// Source: pixel-agents-v2/webview-ui/src/office/sprites/
// ============================================================

// -- Constants -----------------------------------------------
const TILE_SIZE = 16;
const WALK_SPEED = 48;
const WALK_FRAME_DUR = 0.15;
const TYPE_FRAME_DUR = 0.3;
const READ_FRAME_DUR = 0.5;
const SIT_OFFSET = 6;
const _ = '';

// Office Life Engine timing
const WORK_CYCLE_MIN = 15.0;
const WORK_CYCLE_MAX = 40.0;
const BREAK_CYCLE_MIN = 5.0;
const BREAK_CYCLE_MAX = 15.0;
const COFFEE_WAIT_TIME = 4.0;  // seconds standing at cooler
const SLEEP_TIME_MIN = 8.0;
const SLEEP_TIME_MAX = 15.0;
const PHONE_TIME_MIN = 5.0;
const PHONE_TIME_MAX = 8.0;
const CHAT_TIME_MIN = 5.0;
const CHAT_TIME_MAX = 8.0;

// -- Direction enum ------------------------------------------
const Direction = { DOWN: 0, LEFT: 1, RIGHT: 2, UP: 3 };

// -- Furniture Sprites ---------------------------------------

/** Square desk: 32x32 pixels (2x2 tiles) -- top-down wood surface */
const DESK_SQUARE_SPRITE = (function() {
  var W = '#8B6914'; // wood edge
  var L = '#A07828'; // lighter wood
  var S = '#B8922E'; // surface
  var D = '#6B4E0A'; // dark edge
  var rows = [];
  // Row 0: empty
  rows.push(new Array(32).fill(_));
  // Row 1: top edge
  rows.push([_].concat(new Array(30).fill(W), [_]));
  // Rows 2-5: top surface
  for (var r = 0; r < 4; r++) {
    rows.push([_, W].concat(new Array(28).fill(r < 1 ? L : S), [W, _]));
  }
  // Row 6: horizontal divider
  rows.push([_, D].concat(new Array(28).fill(W), [D, _]));
  // Rows 7-12: middle surface area
  for (var r = 0; r < 6; r++) {
    rows.push([_, W].concat(new Array(28).fill(S), [W, _]));
  }
  // Row 13: center line
  rows.push([_, W].concat(new Array(28).fill(L), [W, _]));
  // Rows 14-19: lower surface
  for (var r = 0; r < 6; r++) {
    rows.push([_, W].concat(new Array(28).fill(S), [W, _]));
  }
  // Row 20: horizontal divider
  rows.push([_, D].concat(new Array(28).fill(W), [D, _]));
  // Rows 21-24: bottom surface
  for (var r = 0; r < 4; r++) {
    rows.push([_, W].concat(new Array(28).fill(r > 2 ? L : S), [W, _]));
  }
  // Row 25: bottom edge
  rows.push([_].concat(new Array(30).fill(W), [_]));
  // Rows 26-29: legs/shadow
  for (var r = 0; r < 4; r++) {
    var row = new Array(32).fill(_);
    row[1] = D; row[2] = D; row[29] = D; row[30] = D;
    rows.push(row);
  }
  rows.push(new Array(32).fill(_));
  rows.push(new Array(32).fill(_));
  return rows;
})();

/** Dark mahogany desk: 32x32 (2x2 tiles) — Executive/Monetizados */
const DESK_DARK_SPRITE = (function() {
  var W = '#5C3A1E'; // mahogany edge
  var L = '#8C6038'; // lighter mahogany
  var S = '#7A4E2A'; // surface
  var D = '#3E2610'; // dark edge
  var rows = [];
  rows.push(new Array(32).fill(_));
  rows.push([_].concat(new Array(30).fill(W), [_]));
  for (var r = 0; r < 4; r++) {
    rows.push([_, W].concat(new Array(28).fill(r < 1 ? L : S), [W, _]));
  }
  rows.push([_, D].concat(new Array(28).fill(W), [D, _]));
  for (var r = 0; r < 6; r++) {
    rows.push([_, W].concat(new Array(28).fill(S), [W, _]));
  }
  rows.push([_, W].concat(new Array(28).fill(L), [W, _]));
  for (var r = 0; r < 6; r++) {
    rows.push([_, W].concat(new Array(28).fill(S), [W, _]));
  }
  rows.push([_, D].concat(new Array(28).fill(W), [D, _]));
  for (var r = 0; r < 4; r++) {
    rows.push([_, W].concat(new Array(28).fill(r > 2 ? L : S), [W, _]));
  }
  rows.push([_].concat(new Array(30).fill(W), [_]));
  for (var r = 0; r < 4; r++) {
    var row = new Array(32).fill(_);
    row[1] = D; row[2] = D; row[29] = D; row[30] = D;
    rows.push(row);
  }
  rows.push(new Array(32).fill(_));
  rows.push(new Array(32).fill(_));
  return rows;
})();

/** Stone/iron desk: 32x32 (2x2 tiles) — Gothic/Sombrias */
const DESK_STONE_SPRITE = (function() {
  var W = '#4A4A5A'; // iron edge
  var L = '#707080'; // lighter stone
  var S = '#606070'; // surface
  var D = '#3A3A4A'; // dark shadow
  var rows = [];
  rows.push(new Array(32).fill(_));
  rows.push([_].concat(new Array(30).fill(W), [_]));
  for (var r = 0; r < 4; r++) {
    rows.push([_, W].concat(new Array(28).fill(r < 1 ? L : S), [W, _]));
  }
  rows.push([_, D].concat(new Array(28).fill(W), [D, _]));
  for (var r = 0; r < 6; r++) {
    rows.push([_, W].concat(new Array(28).fill(S), [W, _]));
  }
  rows.push([_, W].concat(new Array(28).fill(L), [W, _]));
  for (var r = 0; r < 6; r++) {
    rows.push([_, W].concat(new Array(28).fill(S), [W, _]));
  }
  rows.push([_, D].concat(new Array(28).fill(W), [D, _]));
  for (var r = 0; r < 4; r++) {
    rows.push([_, W].concat(new Array(28).fill(r > 2 ? L : S), [W, _]));
  }
  rows.push([_].concat(new Array(30).fill(W), [_]));
  for (var r = 0; r < 4; r++) {
    var row = new Array(32).fill(_);
    row[1] = D; row[2] = D; row[29] = D; row[30] = D;
    rows.push(row);
  }
  rows.push(new Array(32).fill(_));
  rows.push(new Array(32).fill(_));
  return rows;
})();

/** Military metal desk: 32x32 (2x2 tiles) — Warroom/Guerra */
const DESK_METAL_SPRITE = (function() {
  var W = '#3B4A2A'; // olive metal edge
  var L = '#5E6E4A'; // lighter metal
  var S = '#4E5E3A'; // surface
  var D = '#2A3A1A'; // dark shadow
  var rows = [];
  rows.push(new Array(32).fill(_));
  rows.push([_].concat(new Array(30).fill(W), [_]));
  for (var r = 0; r < 4; r++) {
    rows.push([_, W].concat(new Array(28).fill(r < 1 ? L : S), [W, _]));
  }
  rows.push([_, D].concat(new Array(28).fill(W), [D, _]));
  for (var r = 0; r < 6; r++) {
    rows.push([_, W].concat(new Array(28).fill(S), [W, _]));
  }
  rows.push([_, W].concat(new Array(28).fill(L), [W, _]));
  for (var r = 0; r < 6; r++) {
    rows.push([_, W].concat(new Array(28).fill(S), [W, _]));
  }
  rows.push([_, D].concat(new Array(28).fill(W), [D, _]));
  for (var r = 0; r < 4; r++) {
    rows.push([_, W].concat(new Array(28).fill(r > 2 ? L : S), [W, _]));
  }
  rows.push([_].concat(new Array(30).fill(W), [_]));
  for (var r = 0; r < 4; r++) {
    var row = new Array(32).fill(_);
    row[1] = D; row[2] = D; row[29] = D; row[30] = D;
    rows.push(row);
  }
  rows.push(new Array(32).fill(_));
  rows.push(new Array(32).fill(_));
  return rows;
})();

/** Plant in pot: 16x24 */
var PLANT_SPRITE = (function() {
  var G = '#3D8B37';
  var D = '#2D6B27';
  var T = '#6B4E0A';
  var P = '#B85C3A';
  var R = '#8B4422';
  return [
    [_, _, _, _, _, _, G, G, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, G, G, G, G, _, _, _, _, _, _, _],
    [_, _, _, _, G, G, D, G, G, G, _, _, _, _, _, _],
    [_, _, _, G, G, D, G, G, D, G, G, _, _, _, _, _],
    [_, _, G, G, G, G, G, G, G, G, G, G, _, _, _, _],
    [_, G, G, D, G, G, G, G, G, G, D, G, G, _, _, _],
    [_, G, G, G, G, D, G, G, D, G, G, G, G, _, _, _],
    [_, _, G, G, G, G, G, G, G, G, G, G, _, _, _, _],
    [_, _, _, G, G, G, D, G, G, G, G, _, _, _, _, _],
    [_, _, _, _, G, G, G, G, G, G, _, _, _, _, _, _],
    [_, _, _, _, _, G, G, G, G, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, T, T, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, T, T, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, T, T, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, R, R, R, R, R, _, _, _, _, _, _],
    [_, _, _, _, R, P, P, P, P, P, R, _, _, _, _, _],
    [_, _, _, _, R, P, P, P, P, P, R, _, _, _, _, _],
    [_, _, _, _, R, P, P, P, P, P, R, _, _, _, _, _],
    [_, _, _, _, R, P, P, P, P, P, R, _, _, _, _, _],
    [_, _, _, _, R, P, P, P, P, P, R, _, _, _, _, _],
    [_, _, _, _, R, P, P, P, P, P, R, _, _, _, _, _],
    [_, _, _, _, _, R, P, P, P, R, _, _, _, _, _, _],
    [_, _, _, _, _, _, R, R, R, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  ];
})();

/** Bookshelf: 16x32 (1 tile wide, 2 tiles tall) */
var BOOKSHELF_SPRITE = (function() {
  var W = '#8B6914';
  var D = '#6B4E0A';
  var R = '#CC4444';
  var B = '#4477AA';
  var G = '#44AA66';
  var Y = '#CCAA33';
  var P = '#9955AA';
  return [
    [_, W, W, W, W, W, W, W, W, W, W, W, W, W, W, _],
    [W, D, D, D, D, D, D, D, D, D, D, D, D, D, D, W],
    [W, D, R, R, B, B, G, G, Y, Y, R, R, B, B, D, W],
    [W, D, R, R, B, B, G, G, Y, Y, R, R, B, B, D, W],
    [W, D, R, R, B, B, G, G, Y, Y, R, R, B, B, D, W],
    [W, D, R, R, B, B, G, G, Y, Y, R, R, B, B, D, W],
    [W, D, R, R, B, B, G, G, Y, Y, R, R, B, B, D, W],
    [W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W],
    [W, D, D, D, D, D, D, D, D, D, D, D, D, D, D, W],
    [W, D, P, P, Y, Y, B, B, G, G, P, P, R, R, D, W],
    [W, D, P, P, Y, Y, B, B, G, G, P, P, R, R, D, W],
    [W, D, P, P, Y, Y, B, B, G, G, P, P, R, R, D, W],
    [W, D, P, P, Y, Y, B, B, G, G, P, P, R, R, D, W],
    [W, D, P, P, Y, Y, B, B, G, G, P, P, R, R, D, W],
    [W, D, P, P, Y, Y, B, B, G, G, P, P, R, R, D, W],
    [W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W],
    [W, D, D, D, D, D, D, D, D, D, D, D, D, D, D, W],
    [W, D, G, G, R, R, P, P, B, B, Y, Y, G, G, D, W],
    [W, D, G, G, R, R, P, P, B, B, Y, Y, G, G, D, W],
    [W, D, G, G, R, R, P, P, B, B, Y, Y, G, G, D, W],
    [W, D, G, G, R, R, P, P, B, B, Y, Y, G, G, D, W],
    [W, D, G, G, R, R, P, P, B, B, Y, Y, G, G, D, W],
    [W, D, G, G, R, R, P, P, B, B, Y, Y, G, G, D, W],
    [W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W],
    [W, D, D, D, D, D, D, D, D, D, D, D, D, D, D, W],
    [W, D, D, D, D, D, D, D, D, D, D, D, D, D, D, W],
    [W, D, D, D, D, D, D, D, D, D, D, D, D, D, D, W],
    [W, D, D, D, D, D, D, D, D, D, D, D, D, D, D, W],
    [W, D, D, D, D, D, D, D, D, D, D, D, D, D, D, W],
    [W, D, D, D, D, D, D, D, D, D, D, D, D, D, D, W],
    [W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W],
    [_, W, W, W, W, W, W, W, W, W, W, W, W, W, W, _],
  ];
})();

/** Water cooler: 16x24 */
var COOLER_SPRITE = (function() {
  var W = '#CCDDEE';
  var L = '#88BBDD';
  var D = '#999999';
  var B = '#666666';
  return [
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, D, D, D, D, D, D, _, _, _, _, _],
    [_, _, _, _, D, L, L, L, L, L, L, D, _, _, _, _],
    [_, _, _, _, D, L, L, L, L, L, L, D, _, _, _, _],
    [_, _, _, _, D, L, L, L, L, L, L, D, _, _, _, _],
    [_, _, _, _, D, L, L, L, L, L, L, D, _, _, _, _],
    [_, _, _, _, D, L, L, L, L, L, L, D, _, _, _, _],
    [_, _, _, _, _, D, D, D, D, D, D, _, _, _, _, _],
    [_, _, _, _, _, D, W, W, W, W, D, _, _, _, _, _],
    [_, _, _, _, _, D, W, W, W, W, D, _, _, _, _, _],
    [_, _, _, _, _, D, W, W, W, W, D, _, _, _, _, _],
    [_, _, _, _, _, D, W, W, W, W, D, _, _, _, _, _],
    [_, _, _, _, _, D, W, W, W, W, D, _, _, _, _, _],
    [_, _, _, _, D, D, W, W, W, W, D, D, _, _, _, _],
    [_, _, _, _, D, W, W, W, W, W, W, D, _, _, _, _],
    [_, _, _, _, D, W, W, W, W, W, W, D, _, _, _, _],
    [_, _, _, _, D, D, D, D, D, D, D, D, _, _, _, _],
    [_, _, _, _, _, D, B, B, B, B, D, _, _, _, _, _],
    [_, _, _, _, _, D, B, B, B, B, D, _, _, _, _, _],
    [_, _, _, _, _, D, B, B, B, B, D, _, _, _, _, _],
    [_, _, _, _, D, D, B, B, B, B, D, D, _, _, _, _],
    [_, _, _, _, D, B, B, B, B, B, B, D, _, _, _, _],
    [_, _, _, _, D, D, D, D, D, D, D, D, _, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  ];
})();

/** Chair: 16x16 -- top-down desk chair */
var CHAIR_SPRITE = (function() {
  var W = '#8B6914';
  var D = '#6B4E0A';
  var B = '#5C3D0A';
  var S = '#A07828';
  return [
    [_, _, _, _, _, D, D, D, D, D, D, _, _, _, _, _],
    [_, _, _, _, D, B, B, B, B, B, B, D, _, _, _, _],
    [_, _, _, _, D, B, S, S, S, S, B, D, _, _, _, _],
    [_, _, _, _, D, B, S, S, S, S, B, D, _, _, _, _],
    [_, _, _, _, D, B, S, S, S, S, B, D, _, _, _, _],
    [_, _, _, _, D, B, S, S, S, S, B, D, _, _, _, _],
    [_, _, _, _, D, B, S, S, S, S, B, D, _, _, _, _],
    [_, _, _, _, D, B, S, S, S, S, B, D, _, _, _, _],
    [_, _, _, _, D, B, S, S, S, S, B, D, _, _, _, _],
    [_, _, _, _, D, B, B, B, B, B, B, D, _, _, _, _],
    [_, _, _, _, _, D, D, D, D, D, D, _, _, _, _, _],
    [_, _, _, _, _, _, D, W, W, D, _, _, _, _, _, _],
    [_, _, _, _, _, _, D, W, W, D, _, _, _, _, _, _],
    [_, _, _, _, _, D, D, D, D, D, D, _, _, _, _, _],
    [_, _, _, _, _, D, _, _, _, _, D, _, _, _, _, _],
    [_, _, _, _, _, D, _, _, _, _, D, _, _, _, _, _],
  ];
})();

/** Chair Executive: 16x16 -- premium leather chair with armrests */
var CHAIR_EXEC_SPRITE = (function() {
  var L = '#6B3A20';  // leather brown
  var D = '#3E2610';  // dark frame
  var G = '#C8A24E';  // gold accent
  var S = '#8B5A30';  // seat leather
  return [
    [_, _, _, _, G, D, D, D, D, D, D, G, _, _, _, _],
    [_, _, _, D, D, L, L, L, L, L, L, D, D, _, _, _],
    [_, _, _, D, L, S, S, S, S, S, S, L, D, _, _, _],
    [_, _, _, D, L, S, S, S, S, S, S, L, D, _, _, _],
    [_, _, G, D, L, S, S, S, S, S, S, L, D, G, _, _],
    [_, _, G, D, L, S, S, S, S, S, S, L, D, G, _, _],
    [_, _, _, D, L, S, S, S, S, S, S, L, D, _, _, _],
    [_, _, _, D, L, S, S, S, S, S, S, L, D, _, _, _],
    [_, _, _, D, L, S, S, S, S, S, S, L, D, _, _, _],
    [_, _, _, D, D, L, L, L, L, L, L, D, D, _, _, _],
    [_, _, _, _, D, D, D, D, D, D, D, D, _, _, _, _],
    [_, _, _, _, _, _, D, G, G, D, _, _, _, _, _, _],
    [_, _, _, _, _, _, D, G, G, D, _, _, _, _, _, _],
    [_, _, _, _, _, D, D, D, D, D, D, _, _, _, _, _],
    [_, _, _, _, _, D, _, _, _, _, D, _, _, _, _, _],
    [_, _, _, _, _, D, _, _, _, _, D, _, _, _, _, _],
  ];
})();

/** Chair Stone: 16x16 -- medieval stone bench */
var CHAIR_STONE_SPRITE = (function() {
  var S = '#4A4A5A';  // stone
  var D = '#3A3A4A';  // dark stone
  var L = '#5A5A6A';  // light stone
  var M = '#3A4A3A';  // moss
  return [
    [_, _, _, _, S, S, S, S, S, S, S, S, _, _, _, _],
    [_, _, _, S, D, D, D, D, D, D, D, D, S, _, _, _],
    [_, _, _, S, D, L, L, L, L, L, L, D, S, _, _, _],
    [_, _, _, S, D, L, L, L, L, L, L, D, S, _, _, _],
    [_, _, _, S, D, L, L, L, L, L, L, D, S, _, _, _],
    [_, _, _, S, D, L, L, L, L, L, L, D, S, _, _, _],
    [_, _, _, S, D, L, L, L, L, L, L, D, S, _, _, _],
    [_, _, _, S, D, L, L, L, L, L, L, D, S, _, _, _],
    [_, _, _, S, D, L, L, L, L, L, L, D, S, _, _, _],
    [_, _, _, S, D, D, D, D, D, D, D, D, S, _, _, _],
    [_, _, _, S, S, S, S, S, S, S, S, S, S, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, S, D, _, _, _, _, D, S, _, _, _, _],
    [_, _, _, _, S, D, _, _, _, _, D, S, _, _, _, _],
    [_, _, _, _, S, M, _, _, _, _, M, S, _, _, _, _],
    [_, _, _, _, S, M, _, _, _, _, M, S, _, _, _, _],
  ];
})();

/** Chair Military: 16x16 -- folding metal stool */
var CHAIR_MILITARY_SPRITE = (function() {
  var M = '#3B4A2A';  // metal green
  var D = '#2A3A1A';  // dark green
  var C = '#5E5E3A';  // canvas seat
  var K = '#222222';  // black
  return [
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, M, M, M, M, M, M, _, _, _, _, _],
    [_, _, _, _, M, D, D, D, D, D, D, M, _, _, _, _],
    [_, _, _, _, M, D, C, C, C, C, D, M, _, _, _, _],
    [_, _, _, _, M, D, C, C, C, C, D, M, _, _, _, _],
    [_, _, _, _, M, D, C, C, C, C, D, M, _, _, _, _],
    [_, _, _, _, M, D, C, C, C, C, D, M, _, _, _, _],
    [_, _, _, _, M, D, C, C, C, C, D, M, _, _, _, _],
    [_, _, _, _, M, D, D, D, D, D, D, M, _, _, _, _],
    [_, _, _, _, _, M, M, M, M, M, M, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, M, _, _, _, _, M, _, _, _, _, _],
    [_, _, _, _, M, D, _, _, _, _, D, M, _, _, _, _],
    [_, _, _, M, K, _, _, _, _, _, _, K, M, _, _, _],
    [_, _, M, K, _, _, _, _, _, _, _, _, K, M, _, _],
    [_, _, K, _, _, _, _, _, _, _, _, _, _, K, _, _],
  ];
})();

/** PC monitor: 16x16 -- top-down monitor on stand */
var PC_SPRITE = (function() {
  var F = '#555555';
  var S = '#3A3A5C';
  var B = '#6688CC';
  var D = '#444444';
  return [
    [_, _, _, F, F, F, F, F, F, F, F, F, F, _, _, _],
    [_, _, _, F, S, S, S, S, S, S, S, S, F, _, _, _],
    [_, _, _, F, S, B, B, B, B, B, B, S, F, _, _, _],
    [_, _, _, F, S, B, B, B, B, B, B, S, F, _, _, _],
    [_, _, _, F, S, B, B, B, B, B, B, S, F, _, _, _],
    [_, _, _, F, S, B, B, B, B, B, B, S, F, _, _, _],
    [_, _, _, F, S, B, B, B, B, B, B, S, F, _, _, _],
    [_, _, _, F, S, B, B, B, B, B, B, S, F, _, _, _],
    [_, _, _, F, S, S, S, S, S, S, S, S, F, _, _, _],
    [_, _, _, F, F, F, F, F, F, F, F, F, F, _, _, _],
    [_, _, _, _, _, _, _, D, D, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, D, D, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, D, D, D, D, _, _, _, _, _, _],
    [_, _, _, _, _, D, D, D, D, D, D, _, _, _, _, _],
    [_, _, _, _, _, D, D, D, D, D, D, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  ];
})();

/** Notebook: 16x16 -- top-down laptop open (executive) */
var NOTEBOOK_SPRITE = (function() {
  var A = '#C0C0C0'; // aluminum frame
  var S = '#A8A8A8'; // aluminum shadow
  var B = '#6688CC'; // screen blue
  var D = '#3A3A5C'; // screen border
  var K = '#333333'; // keyboard base
  var T = '#555555'; // key dots
  return [
    [_, _, A, A, A, A, A, A, A, A, A, A, A, A, _, _],
    [_, _, A, D, D, D, D, D, D, D, D, D, D, A, _, _],
    [_, _, A, D, B, B, B, B, B, B, B, B, D, A, _, _],
    [_, _, A, D, B, B, B, B, B, B, B, B, D, A, _, _],
    [_, _, A, D, B, B, B, B, B, B, B, B, D, A, _, _],
    [_, _, A, D, B, B, B, B, B, B, B, B, D, A, _, _],
    [_, _, A, D, D, D, D, D, D, D, D, D, D, A, _, _],
    [_, _, S, S, S, S, S, S, S, S, S, S, S, S, _, _],
    [_, _, A, K, K, K, K, K, K, K, K, K, K, A, _, _],
    [_, _, A, K, T, K, T, K, T, K, T, K, K, A, _, _],
    [_, _, A, K, K, T, K, T, K, T, K, T, K, A, _, _],
    [_, _, A, K, T, K, T, K, T, K, T, K, K, A, _, _],
    [_, _, A, K, K, K, K, K, K, K, K, K, K, A, _, _],
    [_, _, A, K, K, T, T, T, T, T, T, K, K, A, _, _],
    [_, _, A, A, A, A, A, A, A, A, A, A, A, A, _, _],
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  ];
})();

/** Military terminal: 16x16 -- CRT with green phosphor screen (warroom) */
var TERMINAL_SPRITE = (function() {
  var F = '#556B2F'; // olive frame
  var D = '#3B4A1E'; // dark frame
  var G = '#00CC00'; // green phosphor
  var S = '#003300'; // dark screen
  var B = '#444A3A'; // base
  return [
    [_, _, _, F, F, F, F, F, F, F, F, F, F, _, _, _],
    [_, _, _, F, D, D, D, D, D, D, D, D, F, _, _, _],
    [_, _, _, F, D, S, S, S, S, S, S, D, F, _, _, _],
    [_, _, _, F, D, S, G, S, G, G, S, D, F, _, _, _],
    [_, _, _, F, D, S, G, G, S, G, S, D, F, _, _, _],
    [_, _, _, F, D, S, S, G, G, S, G, D, F, _, _, _],
    [_, _, _, F, D, S, G, S, G, G, S, D, F, _, _, _],
    [_, _, _, F, D, S, S, S, S, S, S, D, F, _, _, _],
    [_, _, _, F, D, D, D, D, D, D, D, D, F, _, _, _],
    [_, _, _, F, F, F, F, F, F, F, F, F, F, _, _, _],
    [_, _, _, _, _, _, _, B, B, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, B, B, B, B, _, _, _, _, _, _],
    [_, _, _, _, _, B, B, B, B, B, B, _, _, _, _, _],
    [_, _, _, _, B, B, B, B, B, B, B, B, _, _, _, _],
    [_, _, _, _, B, B, B, B, B, B, B, B, _, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  ];
})();

/** Desk lamp: 16x16 -- top-down lamp with light cone */
var LAMP_SPRITE = (function() {
  var Y = '#FFDD55';
  var L = '#FFEE88';
  var D = '#888888';
  var B = '#555555';
  var G = '#FFFFCC';
  return [
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, G, G, G, G, _, _, _, _, _, _],
    [_, _, _, _, _, G, Y, Y, Y, Y, G, _, _, _, _, _],
    [_, _, _, _, G, Y, Y, L, L, Y, Y, G, _, _, _, _],
    [_, _, _, _, Y, Y, L, L, L, L, Y, Y, _, _, _, _],
    [_, _, _, _, Y, Y, L, L, L, L, Y, Y, _, _, _, _],
    [_, _, _, _, _, Y, Y, Y, Y, Y, Y, _, _, _, _, _],
    [_, _, _, _, _, _, D, D, D, D, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, D, D, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, D, D, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, D, D, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, D, D, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, D, D, D, D, _, _, _, _, _, _],
    [_, _, _, _, _, B, B, B, B, B, B, _, _, _, _, _],
    [_, _, _, _, _, B, B, B, B, B, B, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  ];
})();

// -- Character Sprite Templates ------------------------------
// 16x24 characters with palette substitution
// Template keys
var H = 'hair';
var K = 'skin';
var S = 'shirt';
var P = 'pants';
var O = 'shoes';
var E = '#FFFFFF'; // eyes

// ----------------------------------------------------------------
// DOWN-FACING SPRITES
// ----------------------------------------------------------------

// Walk down: 4 frames (1, 2=standing, 3=mirror legs, 2 again)
var CHAR_WALK_DOWN_1 = [
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, H, H, H, H, _, _, _, _, _, _],
  [_, _, _, _, _, H, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, H, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, K, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, K, E, K, K, E, K, _, _, _, _, _],
  [_, _, _, _, _, K, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, K, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, _, S, S, S, S, _, _, _, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, S, S, S, S, S, S, S, S, _, _, _, _],
  [_, _, _, _, S, S, S, S, S, S, S, S, _, _, _, _],
  [_, _, _, _, K, S, S, S, S, S, S, K, _, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, _, _, P, P, P, P, _, _, _, _, _, _],
  [_, _, _, _, _, P, P, P, P, P, P, _, _, _, _, _],
  [_, _, _, _, _, P, P, P, P, P, P, _, _, _, _, _],
  [_, _, _, _, P, P, _, _, _, _, P, P, _, _, _, _],
  [_, _, _, _, P, P, _, _, _, _, P, P, _, _, _, _],
  [_, _, _, _, O, O, _, _, _, _, _, O, O, _, _, _],
  [_, _, _, _, O, O, _, _, _, _, _, O, O, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
];

var CHAR_WALK_DOWN_2 = [
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, H, H, H, H, _, _, _, _, _, _],
  [_, _, _, _, _, H, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, H, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, K, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, K, E, K, K, E, K, _, _, _, _, _],
  [_, _, _, _, _, K, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, K, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, _, S, S, S, S, _, _, _, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, S, S, S, S, S, S, S, S, _, _, _, _],
  [_, _, _, _, S, S, S, S, S, S, S, S, _, _, _, _],
  [_, _, _, _, K, S, S, S, S, S, S, K, _, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, _, _, P, P, P, P, _, _, _, _, _, _],
  [_, _, _, _, _, P, P, P, P, P, P, _, _, _, _, _],
  [_, _, _, _, _, P, P, _, _, P, P, _, _, _, _, _],
  [_, _, _, _, _, P, P, _, _, P, P, _, _, _, _, _],
  [_, _, _, _, _, P, P, _, _, P, P, _, _, _, _, _],
  [_, _, _, _, _, O, O, _, _, O, O, _, _, _, _, _],
  [_, _, _, _, _, O, O, _, _, O, O, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
];

var CHAR_WALK_DOWN_3 = [
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, H, H, H, H, _, _, _, _, _, _],
  [_, _, _, _, _, H, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, H, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, K, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, K, E, K, K, E, K, _, _, _, _, _],
  [_, _, _, _, _, K, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, K, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, _, S, S, S, S, _, _, _, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, S, S, S, S, S, S, S, S, _, _, _, _],
  [_, _, _, _, S, S, S, S, S, S, S, S, _, _, _, _],
  [_, _, _, _, K, S, S, S, S, S, S, K, _, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, _, _, P, P, P, P, _, _, _, _, _, _],
  [_, _, _, _, _, P, P, P, P, P, P, _, _, _, _, _],
  [_, _, _, _, _, P, P, P, P, P, P, _, _, _, _, _],
  [_, _, _, O, O, _, _, _, _, _, _, P, P, _, _, _],
  [_, _, _, O, O, _, _, _, _, _, _, P, P, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, O, O, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, O, O, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
];

// Down typing: front-facing sitting, arms on keyboard
var CHAR_DOWN_TYPE_1 = [
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, H, H, H, H, _, _, _, _, _, _],
  [_, _, _, _, _, H, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, H, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, K, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, K, E, K, K, E, K, _, _, _, _, _],
  [_, _, _, _, _, K, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, K, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, _, S, S, S, S, _, _, _, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, S, S, S, S, S, S, S, S, _, _, _, _],
  [_, _, _, K, K, S, S, S, S, S, S, K, K, _, _, _],
  [_, _, _, _, K, S, S, S, S, S, S, K, _, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, _, _, P, P, P, P, _, _, _, _, _, _],
  [_, _, _, _, _, P, P, P, P, P, P, _, _, _, _, _],
  [_, _, _, _, _, P, P, P, P, P, P, _, _, _, _, _],
  [_, _, _, _, _, P, P, _, _, P, P, _, _, _, _, _],
  [_, _, _, _, _, O, O, _, _, O, O, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
];

var CHAR_DOWN_TYPE_2 = [
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, H, H, H, H, _, _, _, _, _, _],
  [_, _, _, _, _, H, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, H, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, K, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, K, E, K, K, E, K, _, _, _, _, _],
  [_, _, _, _, _, K, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, K, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, _, S, S, S, S, _, _, _, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, S, S, S, S, S, S, S, S, _, _, _, _],
  [_, _, _, _, K, S, S, S, S, S, S, K, K, _, _, _],
  [_, _, _, _, K, S, S, S, S, S, S, _, K, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, _, _, P, P, P, P, _, _, _, _, _, _],
  [_, _, _, _, _, P, P, P, P, P, P, _, _, _, _, _],
  [_, _, _, _, _, P, P, P, P, P, P, _, _, _, _, _],
  [_, _, _, _, _, P, P, _, _, P, P, _, _, _, _, _],
  [_, _, _, _, _, O, O, _, _, O, O, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
];

// Down reading: front-facing sitting, arms at sides, looking at screen
var CHAR_DOWN_READ_1 = [
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, H, H, H, H, _, _, _, _, _, _],
  [_, _, _, _, _, H, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, H, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, K, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, K, E, K, K, E, K, _, _, _, _, _],
  [_, _, _, _, _, K, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, K, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, _, S, S, S, S, _, _, _, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, S, S, S, S, S, S, S, S, _, _, _, _],
  [_, _, _, _, S, S, S, S, S, S, S, S, _, _, _, _],
  [_, _, _, _, K, S, S, S, S, S, S, K, _, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, _, _, P, P, P, P, _, _, _, _, _, _],
  [_, _, _, _, _, P, P, P, P, P, P, _, _, _, _, _],
  [_, _, _, _, _, P, P, P, P, P, P, _, _, _, _, _],
  [_, _, _, _, _, P, P, _, _, P, P, _, _, _, _, _],
  [_, _, _, _, _, O, O, _, _, O, O, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
];

var CHAR_DOWN_READ_2 = [
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, H, H, H, H, _, _, _, _, _, _],
  [_, _, _, _, _, H, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, H, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, K, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, K, E, K, K, E, K, _, _, _, _, _],
  [_, _, _, _, _, K, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, K, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, _, S, S, S, S, _, _, _, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, S, S, S, S, S, S, S, S, _, _, _, _],
  [_, _, _, _, S, S, S, S, S, S, S, S, _, _, _, _],
  [_, _, _, _, K, S, S, S, S, S, S, K, _, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, _, _, P, P, P, P, _, _, _, _, _, _],
  [_, _, _, _, _, P, P, P, P, P, P, _, _, _, _, _],
  [_, _, _, _, _, P, P, _, _, P, P, _, _, _, _, _],
  [_, _, _, _, _, O, O, _, _, O, O, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
];

// ----------------------------------------------------------------
// UP-FACING SPRITES (back of head, no face)
// ----------------------------------------------------------------

// Walk up: back view, legs alternate
var CHAR_WALK_UP_1 = [
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, H, H, H, H, _, _, _, _, _, _],
  [_, _, _, _, _, H, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, H, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, H, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, K, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, K, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, K, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, _, S, S, S, S, _, _, _, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, S, S, S, S, S, S, S, S, _, _, _, _],
  [_, _, _, _, S, S, S, S, S, S, S, S, _, _, _, _],
  [_, _, _, _, K, S, S, S, S, S, S, K, _, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, _, _, P, P, P, P, _, _, _, _, _, _],
  [_, _, _, _, _, P, P, P, P, P, P, _, _, _, _, _],
  [_, _, _, _, _, P, P, P, P, P, P, _, _, _, _, _],
  [_, _, _, _, P, P, _, _, _, _, P, P, _, _, _, _],
  [_, _, _, _, P, P, _, _, _, _, P, P, _, _, _, _],
  [_, _, _, O, O, _, _, _, _, _, _, O, O, _, _, _],
  [_, _, _, O, O, _, _, _, _, _, _, O, O, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
];

var CHAR_WALK_UP_2 = [
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, H, H, H, H, _, _, _, _, _, _],
  [_, _, _, _, _, H, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, H, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, H, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, K, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, K, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, K, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, _, S, S, S, S, _, _, _, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, S, S, S, S, S, S, S, S, _, _, _, _],
  [_, _, _, _, S, S, S, S, S, S, S, S, _, _, _, _],
  [_, _, _, _, K, S, S, S, S, S, S, K, _, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, _, _, P, P, P, P, _, _, _, _, _, _],
  [_, _, _, _, _, P, P, P, P, P, P, _, _, _, _, _],
  [_, _, _, _, _, P, P, _, _, P, P, _, _, _, _, _],
  [_, _, _, _, _, P, P, _, _, P, P, _, _, _, _, _],
  [_, _, _, _, _, P, P, _, _, P, P, _, _, _, _, _],
  [_, _, _, _, _, O, O, _, _, O, O, _, _, _, _, _],
  [_, _, _, _, _, O, O, _, _, O, O, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
];

var CHAR_WALK_UP_3 = [
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, H, H, H, H, _, _, _, _, _, _],
  [_, _, _, _, _, H, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, H, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, H, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, K, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, K, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, K, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, _, S, S, S, S, _, _, _, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, S, S, S, S, S, S, S, S, _, _, _, _],
  [_, _, _, _, S, S, S, S, S, S, S, S, _, _, _, _],
  [_, _, _, _, K, S, S, S, S, S, S, K, _, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, _, _, P, P, P, P, _, _, _, _, _, _],
  [_, _, _, _, _, P, P, P, P, P, P, _, _, _, _, _],
  [_, _, _, _, _, P, P, P, P, P, P, _, _, _, _, _],
  [_, _, _, O, O, _, _, _, _, _, _, P, P, _, _, _],
  [_, _, _, O, O, _, _, _, _, _, _, P, P, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, O, O, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, O, O, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
];

// Up typing: back view, arms out to keyboard
var CHAR_UP_TYPE_1 = [
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, H, H, H, H, _, _, _, _, _, _],
  [_, _, _, _, _, H, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, H, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, H, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, K, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, K, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, _, S, S, S, S, _, _, _, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, S, S, S, S, S, S, S, S, _, _, _, _],
  [_, _, _, K, K, S, S, S, S, S, S, K, K, _, _, _],
  [_, _, _, _, K, S, S, S, S, S, S, K, _, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, _, _, P, P, P, P, _, _, _, _, _, _],
  [_, _, _, _, _, P, P, P, P, P, P, _, _, _, _, _],
  [_, _, _, _, _, P, P, P, P, P, P, _, _, _, _, _],
  [_, _, _, _, _, P, P, _, _, P, P, _, _, _, _, _],
  [_, _, _, _, _, O, O, _, _, O, O, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
];

var CHAR_UP_TYPE_2 = [
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, H, H, H, H, _, _, _, _, _, _],
  [_, _, _, _, _, H, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, H, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, H, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, K, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, K, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, _, S, S, S, S, _, _, _, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, S, S, S, S, S, S, S, S, _, _, _, _],
  [_, _, _, _, K, S, S, S, S, S, S, K, K, _, _, _],
  [_, _, _, _, K, S, S, S, S, S, S, _, K, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, _, _, P, P, P, P, _, _, _, _, _, _],
  [_, _, _, _, _, P, P, P, P, P, P, _, _, _, _, _],
  [_, _, _, _, _, P, P, P, P, P, P, _, _, _, _, _],
  [_, _, _, _, _, P, P, _, _, P, P, _, _, _, _, _],
  [_, _, _, _, _, O, O, _, _, O, O, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
];

// Up reading: back view, arms at sides
var CHAR_UP_READ_1 = [
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, H, H, H, H, _, _, _, _, _, _],
  [_, _, _, _, _, H, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, H, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, H, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, K, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, K, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, _, S, S, S, S, _, _, _, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, S, S, S, S, S, S, S, S, _, _, _, _],
  [_, _, _, _, S, S, S, S, S, S, S, S, _, _, _, _],
  [_, _, _, _, K, S, S, S, S, S, S, K, _, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, _, _, P, P, P, P, _, _, _, _, _, _],
  [_, _, _, _, _, P, P, P, P, P, P, _, _, _, _, _],
  [_, _, _, _, _, P, P, P, P, P, P, _, _, _, _, _],
  [_, _, _, _, _, P, P, _, _, P, P, _, _, _, _, _],
  [_, _, _, _, _, O, O, _, _, O, O, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
];

var CHAR_UP_READ_2 = [
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, H, H, H, H, _, _, _, _, _, _],
  [_, _, _, _, _, H, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, H, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, H, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, K, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, K, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, _, S, S, S, S, _, _, _, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, S, S, S, S, S, S, S, S, _, _, _, _],
  [_, _, _, _, S, S, S, S, S, S, S, S, _, _, _, _],
  [_, _, _, _, K, S, S, S, S, S, S, K, _, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, _, _, P, P, P, P, _, _, _, _, _, _],
  [_, _, _, _, _, P, P, P, P, P, P, _, _, _, _, _],
  [_, _, _, _, _, P, P, _, _, P, P, _, _, _, _, _],
  [_, _, _, _, _, O, O, _, _, O, O, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
];

// ----------------------------------------------------------------
// RIGHT-FACING SPRITES (side profile, one eye visible)
// Left sprites are generated by flipHorizontal()
// ----------------------------------------------------------------

// Right walk: side view, legs step
var CHAR_WALK_RIGHT_1 = [
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, _, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, _, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, _, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, _, K, K, K, E, K, _, _, _, _, _],
  [_, _, _, _, _, _, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, _, K, K, K, K, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, S, S, S, _, _, _, _, _, _],
  [_, _, _, _, _, _, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, _, K, S, S, S, S, K, _, _, _, _, _],
  [_, _, _, _, _, _, S, S, S, S, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, P, P, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, P, P, P, P, _, _, _, _, _, _],
  [_, _, _, _, _, _, P, P, P, P, _, _, _, _, _, _],
  [_, _, _, _, _, P, P, _, _, _, P, P, _, _, _, _],
  [_, _, _, _, _, P, P, _, _, _, P, P, _, _, _, _],
  [_, _, _, _, _, O, O, _, _, _, _, O, O, _, _, _],
  [_, _, _, _, _, O, O, _, _, _, _, O, O, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
];

var CHAR_WALK_RIGHT_2 = [
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, _, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, _, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, _, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, _, K, K, K, E, K, _, _, _, _, _],
  [_, _, _, _, _, _, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, _, K, K, K, K, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, S, S, S, _, _, _, _, _, _],
  [_, _, _, _, _, _, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, _, K, S, S, S, S, K, _, _, _, _, _],
  [_, _, _, _, _, _, S, S, S, S, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, P, P, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, P, P, P, P, _, _, _, _, _, _],
  [_, _, _, _, _, _, P, P, _, P, P, _, _, _, _, _],
  [_, _, _, _, _, _, P, P, _, P, P, _, _, _, _, _],
  [_, _, _, _, _, _, P, P, _, P, P, _, _, _, _, _],
  [_, _, _, _, _, _, O, O, _, O, O, _, _, _, _, _],
  [_, _, _, _, _, _, O, O, _, O, O, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
];

var CHAR_WALK_RIGHT_3 = [
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, _, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, _, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, _, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, _, K, K, K, E, K, _, _, _, _, _],
  [_, _, _, _, _, _, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, _, K, K, K, K, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, S, S, S, _, _, _, _, _, _],
  [_, _, _, _, _, _, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, _, K, S, S, S, S, K, _, _, _, _, _],
  [_, _, _, _, _, _, S, S, S, S, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, P, P, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, P, P, P, P, _, _, _, _, _, _],
  [_, _, _, _, _, _, P, P, P, P, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, P, P, P, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, P, P, P, _, _, _, _, _],
  [_, _, _, _, _, O, O, _, _, O, O, _, _, _, _, _],
  [_, _, _, _, _, O, O, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
];

// Right typing: side profile sitting, one arm on keyboard
var CHAR_RIGHT_TYPE_1 = [
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, _, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, _, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, _, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, _, K, K, K, E, K, _, _, _, _, _],
  [_, _, _, _, _, _, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, _, K, K, K, K, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, S, S, S, _, _, _, _, _, _],
  [_, _, _, _, _, _, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, S, K, _, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, K, _, _, _, _, _],
  [_, _, _, _, _, _, S, S, S, S, _, _, _, _, _, _],
  [_, _, _, _, _, _, S, S, S, S, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, P, P, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, P, P, P, P, _, _, _, _, _, _],
  [_, _, _, _, _, _, P, P, P, P, _, _, _, _, _, _],
  [_, _, _, _, _, _, P, P, _, P, P, _, _, _, _, _],
  [_, _, _, _, _, _, O, O, _, O, O, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
];

var CHAR_RIGHT_TYPE_2 = [
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, _, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, _, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, _, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, _, K, K, K, E, K, _, _, _, _, _],
  [_, _, _, _, _, _, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, _, K, K, K, K, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, S, S, S, _, _, _, _, _, _],
  [_, _, _, _, _, _, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, S, _, K, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, _, _, K, _, _, _],
  [_, _, _, _, _, _, S, S, S, S, _, _, _, _, _, _],
  [_, _, _, _, _, _, S, S, S, S, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, P, P, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, P, P, P, P, _, _, _, _, _, _],
  [_, _, _, _, _, _, P, P, P, P, _, _, _, _, _, _],
  [_, _, _, _, _, _, P, P, _, P, P, _, _, _, _, _],
  [_, _, _, _, _, _, O, O, _, O, O, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
];

// Right reading: side sitting, arms at side
var CHAR_RIGHT_READ_1 = [
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, _, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, _, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, _, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, _, K, K, K, E, K, _, _, _, _, _],
  [_, _, _, _, _, _, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, _, K, K, K, K, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, S, S, S, _, _, _, _, _, _],
  [_, _, _, _, _, _, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, _, K, S, S, S, S, K, _, _, _, _, _],
  [_, _, _, _, _, _, S, S, S, S, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, P, P, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, P, P, P, P, _, _, _, _, _, _],
  [_, _, _, _, _, _, P, P, P, P, _, _, _, _, _, _],
  [_, _, _, _, _, _, P, P, _, P, P, _, _, _, _, _],
  [_, _, _, _, _, _, O, O, _, O, O, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
];

var CHAR_RIGHT_READ_2 = [
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, _, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, _, H, H, H, H, H, _, _, _, _, _],
  [_, _, _, _, _, _, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, _, K, K, K, E, K, _, _, _, _, _],
  [_, _, _, _, _, _, K, K, K, K, K, _, _, _, _, _],
  [_, _, _, _, _, _, K, K, K, K, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, S, S, S, _, _, _, _, _, _],
  [_, _, _, _, _, _, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, _, S, S, S, S, S, S, _, _, _, _, _],
  [_, _, _, _, _, K, S, S, S, S, K, _, _, _, _, _],
  [_, _, _, _, _, _, S, S, S, S, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, P, P, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, P, P, P, P, _, _, _, _, _, _],
  [_, _, _, _, _, _, P, P, _, P, P, _, _, _, _, _],
  [_, _, _, _, _, _, O, O, _, O, O, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
];

// -- Template Resolution Functions ---------------------------

/** Resolve a template to SpriteData using a palette */
function resolveTemplate(template, palette) {
  return template.map(function(row) {
    return row.map(function(cell) {
      if (cell === _) return '';
      if (cell === E) return E;
      if (cell === H) return palette.hair;
      if (cell === K) return palette.skin;
      if (cell === S) return palette.shirt;
      if (cell === P) return palette.pants;
      if (cell === O) return palette.shoes;
      return cell;
    });
  });
}

/** Flip a template horizontally (for generating left sprites from right) */
function flipHorizontal(template) {
  return template.map(function(row) {
    return row.slice().reverse();
  });
}

// -- Agent Palettes (Custom for Mission Control) -------------

var AGENT_PALETTES = [
  {skin:'#FFCC99', shirt:'#22c55e', pants:'#334466', hair:'#4a3728', shoes:'#222222'},
  {skin:'#e8b88a', shirt:'#ef4444', pants:'#333333', hair:'#1a1a1a', shoes:'#222222'},
  {skin:'#FFCC99', shirt:'#8b5cf6', pants:'#334444', hair:'#8b4513', shoes:'#333333'},
  {skin:'#d4a574', shirt:'#3b82f6', pants:'#443355', hair:'#2c1810', shoes:'#222222'},
  {skin:'#FFCC99', shirt:'#f97316', pants:'#444433', hair:'#c0392b', shoes:'#333333'},
  {skin:'#e8b88a', shirt:'#eab308', pants:'#443322', hair:'#34495e', shoes:'#333333'},
  {skin:'#FFCC99', shirt:'#06b6d4', pants:'#334466', hair:'#1a1a1a', shoes:'#222222'},
];

// -- Character Sprite Generator ------------------------------

/** Get all character sprites for a given palette index
 *  Returns { walk, typing, reading } with all 4 directions */
function getCharacterSprites(paletteIndex) {
  var pal = AGENT_PALETTES[paletteIndex % AGENT_PALETTES.length];
  var r = function(t) { return resolveTemplate(t, pal); };
  var rf = function(t) { return resolveTemplate(flipHorizontal(t), pal); };

  return {
    walk: {
      [Direction.DOWN]:  [r(CHAR_WALK_DOWN_1), r(CHAR_WALK_DOWN_2), r(CHAR_WALK_DOWN_3), r(CHAR_WALK_DOWN_2)],
      [Direction.UP]:    [r(CHAR_WALK_UP_1), r(CHAR_WALK_UP_2), r(CHAR_WALK_UP_3), r(CHAR_WALK_UP_2)],
      [Direction.RIGHT]: [r(CHAR_WALK_RIGHT_1), r(CHAR_WALK_RIGHT_2), r(CHAR_WALK_RIGHT_3), r(CHAR_WALK_RIGHT_2)],
      [Direction.LEFT]:  [rf(CHAR_WALK_RIGHT_1), rf(CHAR_WALK_RIGHT_2), rf(CHAR_WALK_RIGHT_3), rf(CHAR_WALK_RIGHT_2)],
    },
    typing: {
      [Direction.DOWN]:  [r(CHAR_DOWN_TYPE_1), r(CHAR_DOWN_TYPE_2)],
      [Direction.UP]:    [r(CHAR_UP_TYPE_1), r(CHAR_UP_TYPE_2)],
      [Direction.RIGHT]: [r(CHAR_RIGHT_TYPE_1), r(CHAR_RIGHT_TYPE_2)],
      [Direction.LEFT]:  [rf(CHAR_RIGHT_TYPE_1), rf(CHAR_RIGHT_TYPE_2)],
    },
    reading: {
      [Direction.DOWN]:  [r(CHAR_DOWN_READ_1), r(CHAR_DOWN_READ_2)],
      [Direction.UP]:    [r(CHAR_UP_READ_1), r(CHAR_UP_READ_2)],
      [Direction.RIGHT]: [r(CHAR_RIGHT_READ_1), r(CHAR_RIGHT_READ_2)],
      [Direction.LEFT]:  [rf(CHAR_RIGHT_READ_1), rf(CHAR_RIGHT_READ_2)],
    },
  };
}

// -- Sprite Cache System -------------------------------------
// Pre-renders sprites to off-screen canvases for fast drawing

var zoomCaches = new Map();

/** Get a cached canvas for a sprite at a given zoom level.
 *  Creates and caches the canvas on first call. */
function getCachedSprite(sprite, zoom) {
  // Round zoom to nearest 0.5 for cache key to limit cache entries
  var cacheZoom = Math.round(zoom * 2) / 2;
  var cache = zoomCaches.get(cacheZoom);
  if (!cache) {
    cache = new WeakMap();
    zoomCaches.set(cacheZoom, cache);
  }

  var cached = cache.get(sprite);
  if (cached) return cached;

  var rows = sprite.length;
  var cols = sprite[0].length;
  var canvas = document.createElement('canvas');
  var pxSize = Math.max(1, Math.round(cacheZoom));
  canvas.width = Math.ceil(cols * cacheZoom);
  canvas.height = Math.ceil(rows * cacheZoom);
  var ctx = canvas.getContext('2d');
  ctx.imageSmoothingEnabled = false;

  for (var r = 0; r < rows; r++) {
    for (var c = 0; c < cols; c++) {
      var color = sprite[r][c];
      if (color === '') continue;
      ctx.fillStyle = color;
      ctx.fillRect(Math.round(c * cacheZoom), Math.round(r * cacheZoom), Math.ceil(cacheZoom), Math.ceil(cacheZoom));
    }
  }

  cache.set(sprite, canvas);
  return canvas;
}

// -- Whiteboard Sprite (32x16) -- quadro branco com anotacoes -----
var WHITEBOARD_SPRITE = (function() {
  var F = '#AAAAAA';
  var W = '#EEEEFF';
  var M = '#CC4444';
  var B = '#4477AA';
  return [
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, _],
    [_, F, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, F, _],
    [_, F, W, W, M, M, M, W, W, W, W, W, B, B, B, B, W, W, W, W, W, W, W, M, W, W, W, W, W, W, F, _],
    [_, F, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, B, B, W, W, M, W, W, W, W, W, W, F, _],
    [_, F, W, W, W, W, M, M, M, M, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, B, B, W, W, F, _],
    [_, F, W, W, W, W, W, W, W, W, W, W, W, B, B, B, W, W, W, W, W, W, W, W, W, W, W, W, W, W, F, _],
    [_, F, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, M, M, M, W, W, W, W, W, W, W, F, _],
    [_, F, W, M, M, W, W, W, W, W, W, W, W, W, W, W, B, B, W, W, W, W, W, W, W, W, W, W, W, W, F, _],
    [_, F, W, W, W, W, W, W, B, B, B, W, W, W, W, W, W, W, W, W, W, W, W, W, M, M, M, M, W, W, F, _],
    [_, F, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, F, _],
    [_, F, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, F, _],
    [_, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, _],
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  ];
})();

// ====== THEME-EXCLUSIVE DECORATION SPRITES ======

/** Trophy: 16x16 -- golden trophy on pedestal (executive) */
var TROPHY_SPRITE = (function() {
  var G = '#DAA520'; // gold
  var L = '#F0D060'; // gold highlight
  var D = '#B8860B'; // gold dark
  var P = '#8B7355'; // pedestal
  var K = '#6B5735'; // pedestal dark
  return [
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, G, G, G, G, G, G, _, _, _, _, _],
    [_, _, _, _, G, L, L, L, L, L, L, G, _, _, _, _],
    [_, _, _, _, G, L, L, L, L, L, L, G, _, _, _, _],
    [_, _, _, _, G, G, L, L, L, L, G, G, _, _, _, _],
    [_, _, _, _, _, G, G, L, L, G, G, _, _, _, _, _],
    [_, _, _, _, _, _, G, G, G, G, _, _, _, _, _, _],
    [_, _, _, _, _, _, G, D, D, G, _, _, _, _, _, _],
    [_, _, _, _, _, _, G, D, D, G, _, _, _, _, _, _],
    [_, _, _, _, _, _, G, D, D, G, _, _, _, _, _, _],
    [_, _, _, _, _, G, G, G, G, G, G, _, _, _, _, _],
    [_, _, _, _, P, P, P, P, P, P, P, P, _, _, _, _],
    [_, _, _, _, P, K, K, K, K, K, K, P, _, _, _, _],
    [_, _, _, _, P, K, K, K, K, K, K, P, _, _, _, _],
    [_, _, _, P, P, P, P, P, P, P, P, P, P, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  ];
})();

/** Safe: 16x16 -- metal vault/safe (executive) */
var SAFE_SPRITE = (function() {
  var M = '#708090'; // metal body
  var D = '#4A5568'; // dark metal
  var L = '#A0AEC0'; // light metal
  var H = '#CBD5E0'; // handle highlight
  var K = '#2D3748'; // keyhole
  return [
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, D, D, D, D, D, D, D, D, D, D, _, _, _],
    [_, _, _, D, M, M, M, M, M, M, M, M, D, _, _, _],
    [_, _, _, D, M, M, M, M, M, M, M, M, D, _, _, _],
    [_, _, _, D, M, M, M, K, K, M, M, M, D, _, _, _],
    [_, _, _, D, M, M, M, K, K, M, L, H, D, _, _, _],
    [_, _, _, D, M, M, M, M, M, M, L, H, D, _, _, _],
    [_, _, _, D, M, M, M, M, M, M, L, H, D, _, _, _],
    [_, _, _, D, M, M, M, M, M, M, M, M, D, _, _, _],
    [_, _, _, D, M, M, M, M, M, M, M, M, D, _, _, _],
    [_, _, _, D, M, M, M, M, M, M, M, M, D, _, _, _],
    [_, _, _, D, D, D, D, D, D, D, D, D, D, _, _, _],
    [_, _, _, D, D, _, _, _, _, _, _, D, D, _, _, _],
    [_, _, _, D, D, _, _, _, _, _, _, D, D, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  ];
})();

/** Globe: 16x16 -- globe on stand (executive) */
var GLOBE_SPRITE = (function() {
  var B = '#4488BB'; // ocean blue
  var G = '#55AA66'; // land green
  var D = '#336699'; // deep ocean
  var L = '#66BBDD'; // light water
  var S = '#888888'; // stand
  var K = '#666666'; // stand dark
  return [
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, B, B, B, B, _, _, _, _, _, _],
    [_, _, _, _, _, B, B, G, G, B, B, _, _, _, _, _],
    [_, _, _, _, B, B, G, G, G, D, B, B, _, _, _, _],
    [_, _, _, _, B, G, G, B, G, G, D, B, _, _, _, _],
    [_, _, _, _, B, B, G, G, B, B, B, B, _, _, _, _],
    [_, _, _, _, B, D, B, B, G, G, B, B, _, _, _, _],
    [_, _, _, _, B, D, D, B, B, G, B, B, _, _, _, _],
    [_, _, _, _, _, B, B, B, B, B, B, _, _, _, _, _],
    [_, _, _, _, _, _, B, B, B, B, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, S, S, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, S, S, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, S, S, S, S, _, _, _, _, _, _],
    [_, _, _, _, _, S, K, K, K, K, S, _, _, _, _, _],
    [_, _, _, _, _, S, S, S, S, S, S, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  ];
})();

/** Candelabra: 16x24 -- candle holder with flames (gothic) */
var CANDELABRA_SPRITE = (function() {
  var G = '#DAA520'; // gold body
  var D = '#B8860B'; // gold dark
  var F = '#FF8C00'; // flame orange
  var Y = '#FFD700'; // flame yellow
  var W = '#FFFACD'; // flame tip white
  var K = '#6B4E0A'; // base dark
  return [
    [_, _, _, _, _, W, _, _, _, _, W, _, _, _, _, _],
    [_, _, _, _, _, F, _, _, _, _, F, _, _, _, _, _],
    [_, _, _, W, _, Y, _, _, _, _, Y, _, W, _, _, _],
    [_, _, _, F, _, F, _, _, _, _, F, _, F, _, _, _],
    [_, _, _, Y, _, G, _, _, _, _, G, _, Y, _, _, _],
    [_, _, _, G, _, G, _, _, _, _, G, _, G, _, _, _],
    [_, _, _, G, G, G, _, _, _, _, G, G, G, _, _, _],
    [_, _, _, _, G, _, _, _, _, _, _, G, _, _, _, _],
    [_, _, _, _, G, _, _, G, G, _, _, G, _, _, _, _],
    [_, _, _, _, _, G, _, G, G, _, G, _, _, _, _, _],
    [_, _, _, _, _, _, G, G, G, G, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, G, G, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, G, G, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, G, G, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, G, G, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, G, G, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, G, G, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, G, G, G, G, _, _, _, _, _, _],
    [_, _, _, _, _, G, D, D, D, D, G, _, _, _, _, _],
    [_, _, _, _, G, D, K, K, K, K, D, G, _, _, _, _],
    [_, _, _, _, G, D, K, K, K, K, D, G, _, _, _, _],
    [_, _, _, G, G, D, D, D, D, D, D, G, G, _, _, _],
    [_, _, _, G, G, G, G, G, G, G, G, G, G, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  ];
})();

/** Skull: 16x16 -- decorative skull on pedestal (gothic) */
var SKULL_SPRITE = (function() {
  var B = '#E8E0D0'; // bone
  var D = '#C8C0B0'; // bone shadow
  var K = '#333333'; // dark (eyes/nose)
  var T = '#AAAAAA'; // teeth
  var P = '#666666'; // pedestal
  var S = '#555555'; // pedestal dark
  return [
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, B, B, B, B, B, B, _, _, _, _, _],
    [_, _, _, _, B, B, B, B, B, B, B, B, _, _, _, _],
    [_, _, _, B, B, B, B, B, B, B, B, B, B, _, _, _],
    [_, _, _, B, K, K, B, B, B, K, K, B, B, _, _, _],
    [_, _, _, B, K, K, B, B, B, K, K, B, B, _, _, _],
    [_, _, _, B, B, B, B, K, K, B, B, B, B, _, _, _],
    [_, _, _, _, D, B, B, K, K, B, B, D, _, _, _, _],
    [_, _, _, _, D, T, T, T, T, T, T, D, _, _, _, _],
    [_, _, _, _, _, D, T, D, T, D, T, _, _, _, _, _],
    [_, _, _, _, _, _, D, D, D, D, _, _, _, _, _, _],
    [_, _, _, _, _, P, P, P, P, P, P, _, _, _, _, _],
    [_, _, _, _, P, S, S, S, S, S, S, P, _, _, _, _],
    [_, _, _, _, P, S, S, S, S, S, S, P, _, _, _, _],
    [_, _, _, P, P, P, P, P, P, P, P, P, P, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  ];
})();

/** Potion: 16x16 -- alchemy flask with liquid (gothic) */
var POTION_SPRITE = (function() {
  var G = '#888888'; // glass
  var L = '#AABBCC'; // glass light
  var P = '#9933CC'; // purple liquid
  var D = '#6622AA'; // dark liquid
  var K = '#774411'; // cork
  var C = '#996633'; // cork light
  return [
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, K, C, C, K, _, _, _, _, _, _],
    [_, _, _, _, _, _, K, C, C, K, _, _, _, _, _, _],
    [_, _, _, _, _, _, G, L, L, G, _, _, _, _, _, _],
    [_, _, _, _, _, _, G, L, L, G, _, _, _, _, _, _],
    [_, _, _, _, _, G, G, L, L, G, G, _, _, _, _, _],
    [_, _, _, _, G, G, P, P, P, P, G, G, _, _, _, _],
    [_, _, _, G, G, P, P, P, P, P, P, G, G, _, _, _],
    [_, _, _, G, P, P, D, P, P, D, P, P, G, _, _, _],
    [_, _, _, G, P, D, D, P, P, D, D, P, G, _, _, _],
    [_, _, _, G, P, P, P, D, D, P, P, P, G, _, _, _],
    [_, _, _, G, G, P, P, P, P, P, P, G, G, _, _, _],
    [_, _, _, _, G, G, G, G, G, G, G, G, _, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  ];
})();

/** Radio: 16x16 -- military field radio (warroom) */
var RADIO_SPRITE = (function() {
  var M = '#556B2F'; // olive metal body
  var D = '#3B4F1A'; // dark olive
  var K = '#2F4F2F'; // knobs
  var G = '#4A6B3A'; // grill
  var A = '#8B8B00'; // antenna
  var L = '#7CFC00'; // LED light
  return [
    [_, _, _, _, _, _, _, _, A, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, A, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, A, _, _, _, _, _, _, _],
    [_, _, _, D, D, D, D, D, D, D, D, D, D, _, _, _],
    [_, _, _, D, M, M, M, M, M, M, M, M, D, _, _, _],
    [_, _, _, D, M, G, G, G, G, G, G, M, D, _, _, _],
    [_, _, _, D, M, G, G, G, G, G, G, M, D, _, _, _],
    [_, _, _, D, M, G, G, G, G, G, G, M, D, _, _, _],
    [_, _, _, D, M, G, G, G, G, G, G, M, D, _, _, _],
    [_, _, _, D, M, M, M, M, M, M, M, M, D, _, _, _],
    [_, _, _, D, K, K, M, L, M, M, K, K, D, _, _, _],
    [_, _, _, D, K, K, M, M, M, M, K, K, D, _, _, _],
    [_, _, _, D, D, D, D, D, D, D, D, D, D, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  ];
})();

/** Sandbag: 16x16 -- stacked sandbags barricade (warroom) */
var SANDBAG_SPRITE = (function() {
  var S = '#C2B280'; // sand/burlap
  var D = '#A09060'; // sand dark
  var L = '#D4C494'; // sand light
  var K = '#8B7D5B'; // shadow/seam
  return [
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
    [_, _, _, _, _, S, S, S, S, S, S, _, _, _, _, _],
    [_, _, _, _, S, L, S, S, S, S, L, S, _, _, _, _],
    [_, _, _, _, S, S, S, D, D, S, S, S, _, _, _, _],
    [_, _, _, _, K, K, K, K, K, K, K, K, _, _, _, _],
    [_, _, _, S, S, S, S, S, S, S, S, S, S, _, _, _],
    [_, _, _, S, L, S, S, S, S, S, S, L, S, _, _, _],
    [_, _, _, S, S, S, D, D, S, D, D, S, S, _, _, _],
    [_, _, _, K, K, K, K, K, K, K, K, K, K, _, _, _],
    [_, _, S, S, S, S, S, S, S, S, S, S, S, S, _, _],
    [_, _, S, L, S, S, S, S, S, S, S, S, L, S, _, _],
    [_, _, S, S, S, D, D, S, S, D, D, S, S, S, _, _],
    [_, _, K, K, K, K, K, K, K, K, K, K, K, K, _, _],
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  ];
})();

/** Flag: 16x24 -- military flag on pole (warroom) */
var FLAG_SPRITE = (function() {
  var P = '#8B7355'; // pole
  var D = '#6B5335'; // pole dark
  var R = '#8B0000'; // flag red
  var L = '#AA2222'; // flag light
  var K = '#660000'; // flag dark
  var G = '#DAA520'; // gold finial
  return [
    [_, _, _, _, _, _, _, G, G, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, G, G, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, P, R, R, R, R, R, _, _, _],
    [_, _, _, _, _, _, _, P, R, L, L, R, R, R, _, _],
    [_, _, _, _, _, _, _, P, R, L, L, R, R, R, _, _],
    [_, _, _, _, _, _, _, P, R, R, R, K, R, R, _, _],
    [_, _, _, _, _, _, _, P, R, R, K, K, R, R, _, _],
    [_, _, _, _, _, _, _, P, R, R, R, R, R, _, _, _],
    [_, _, _, _, _, _, _, P, R, R, R, R, _, _, _, _],
    [_, _, _, _, _, _, _, P, R, R, R, _, _, _, _, _],
    [_, _, _, _, _, _, _, P, P, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, P, P, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, P, P, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, P, P, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, P, P, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, P, P, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, P, P, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, P, P, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, P, P, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, _, P, P, _, _, _, _, _, _, _],
    [_, _, _, _, _, _, D, D, D, D, _, _, _, _, _, _],
    [_, _, _, _, _, D, D, D, D, D, D, _, _, _, _, _],
    [_, _, _, _, _, D, D, D, D, D, D, _, _, _, _, _],
    [_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _],
  ];
})();

// -- Outline Sprite Generator (from spriteCache.ts) ---------------

var outlineCache = new WeakMap();

function getOutlineSprite(sprite) {
  var cached = outlineCache.get(sprite);
  if (cached) return cached;
  var rows = sprite.length;
  var cols = sprite[0].length;
  var outline = [];
  for (var r = 0; r < rows + 2; r++) {
    var row = [];
    for (var c = 0; c < cols + 2; c++) row.push('');
    outline.push(row);
  }
  for (var r = 0; r < rows; r++) {
    for (var c = 0; c < cols; c++) {
      if (sprite[r][c] === '') continue;
      var er = r + 1, ec = c + 1;
      if (outline[er - 1][ec] === '') outline[er - 1][ec] = '#FFFFFF';
      if (outline[er + 1][ec] === '') outline[er + 1][ec] = '#FFFFFF';
      if (outline[er][ec - 1] === '') outline[er][ec - 1] = '#FFFFFF';
      if (outline[er][ec + 1] === '') outline[er][ec + 1] = '#FFFFFF';
    }
  }
  for (var r = 0; r < rows; r++) {
    for (var c = 0; c < cols; c++) {
      if (sprite[r][c] !== '') outline[r + 1][c + 1] = '';
    }
  }
  outlineCache.set(sprite, outline);
  return outline;
}
var CHAR_PNG_0 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAHAAAABgCAYAAADFNvbQAAAACXBIWXMAAAsTAAALEwEAmpwYAAAGbmlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgNS42LWMxNDUgNzkuMTYzNDk5LCAyMDE4LzA4LzEzLTE2OjQwOjIyICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOmRjPSJodHRwOi8vcHVybC5vcmcvZGMvZWxlbWVudHMvMS4xLyIgeG1sbnM6cGhvdG9zaG9wPSJodHRwOi8vbnMuYWRvYmUuY29tL3Bob3Rvc2hvcC8xLjAvIiB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIgeG1sbnM6c3RFdnQ9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZUV2ZW50IyIgeG1wOkNyZWF0b3JUb29sPSJBZG9iZSBQaG90b3Nob3AgQ0MgMjAxOSAoV2luZG93cykiIHhtcDpDcmVhdGVEYXRlPSIyMDI2LTAyLTE2VDExOjM0OjQxWiIgeG1wOk1vZGlmeURhdGU9IjIwMjYtMDItMTZUMTM6MTg6MzVaIiB4bXA6TWV0YWRhdGFEYXRlPSIyMDI2LTAyLTE2VDEzOjE4OjM1WiIgZGM6Zm9ybWF0PSJpbWFnZS9wbmciIHBob3Rvc2hvcDpDb2xvck1vZGU9IjMiIHBob3Rvc2hvcDpJQ0NQcm9maWxlPSJzUkdCIElFQzYxOTY2LTIuMSIgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDowZjE1NzQ1Ny1jZWZlLWJkNDMtOGRjNC0wODM5NmM0MjI5MTQiIHhtcE1NOkRvY3VtZW50SUQ9InhtcC5kaWQ6MGYxNTc0NTctY2VmZS1iZDQzLThkYzQtMDgzOTZjNDIyOTE0IiB4bXBNTTpPcmlnaW5hbERvY3VtZW50SUQ9InhtcC5kaWQ6MGYxNTc0NTctY2VmZS1iZDQzLThkYzQtMDgzOTZjNDIyOTE0Ij4gPHBob3Rvc2hvcDpEb2N1bWVudEFuY2VzdG9ycz4gPHJkZjpCYWc+IDxyZGY6bGk+YWRvYmU6ZG9jaWQ6cGhvdG9zaG9wOjI5YWFmNzNjLTViOGMtOWE0MC1hYjk2LWNhZWQ3YjU4MmZmYTwvcmRmOmxpPiA8cmRmOmxpPmFkb2JlOmRvY2lkOnBob3Rvc2hvcDo1ZTRlNTM3Ni0yMjg0LWM3NDEtOTNmMC05ODQ0ZDZiY2U2OGI8L3JkZjpsaT4gPHJkZjpsaT54bXAuZGlkOjIwYjUxYTRhLWIwYjktNDc0Mi1iZTQ2LTQyN2Y4NGFkYmQ0MjwvcmRmOmxpPiA8cmRmOmxpPnhtcC5kaWQ6ZDUyN2YxZjUtOWE1MC0wMTQ3LTkxNzAtN2VjOGY3N2I5YzJmPC9yZGY6bGk+IDwvcmRmOkJhZz4gPC9waG90b3Nob3A6RG9jdW1lbnRBbmNlc3RvcnM+IDx4bXBNTTpIaXN0b3J5PiA8cmRmOlNlcT4gPHJkZjpsaSBzdEV2dDphY3Rpb249ImNyZWF0ZWQiIHN0RXZ0Omluc3RhbmNlSUQ9InhtcC5paWQ6MGYxNTc0NTctY2VmZS1iZDQzLThkYzQtMDgzOTZjNDIyOTE0IiBzdEV2dDp3aGVuPSIyMDI2LTAyLTE2VDExOjM0OjQxWiIgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWRvYmUgUGhvdG9zaG9wIENDIDIwMTkgKFdpbmRvd3MpIi8+IDwvcmRmOlNlcT4gPC94bXBNTTpIaXN0b3J5PiA8L3JkZjpEZXNjcmlwdGlvbj4gPC9yZGY6UkRGPiA8L3g6eG1wbWV0YT4gPD94cGFja2V0IGVuZD0iciI/Pu5QeR4AAAisSURBVHja7V3LbuVEELVgBhSkkLloeCRDeGl4CAGLERkxSIxGbFDYRELKIvtZIQHb+YAREiuWsIsEK9gg+AFW/ANbYDXfwOKSMi6r3K6ufpXdbqct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";

var CHAR_PNG_1 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAHAAAABgCAYAAADFNvbQAAAACXBIWXMAAAsTAAALEwEAmpwYAAALDWlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgNS42LWMxNDUgNzkuMTYzNDk5LCAyMDE4LzA4LzEzLTE2OjQwOjIyICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOmRjPSJodHRwOi8vcHVybC5vcmcvZGMvZWxlbWVudHMvMS4xLyIgeG1sbnM6cGhvdG9zaG9wPSJodHRwOi8vbnMuYWRvYmUuY29tL3Bob3Rvc2hvcC8xLjAvIiB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIgeG1sbnM6c3RFdnQ9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZUV2ZW50IyIgeG1sbnM6c3RSZWY9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZVJlZiMiIHhtcDpDcmVhdG9yVG9vbD0iQWRvYmUgUGhvdG9zaG9wIENDIDIwMTkgKFdpbmRvd3MpIiB4bXA6Q3JlYXRlRGF0ZT0iMjAyNi0wMi0xNlQxMTozNDo0MVoiIHhtcDpNb2RpZnlEYXRlPSIyMDI2LTAyLTE2VDIwOjA0OjA0WiIgeG1wOk1ldGFkYXRhRGF0ZT0iMjAyNi0wMi0xNlQyMDowNDowNFoiIGRjOmZvcm1hdD0iaW1hZ2UvcG5nIiBwaG90b3Nob3A6Q29sb3JNb2RlPSIzIiBwaG90b3Nob3A6SUNDUHJvZmlsZT0ic1JHQiBJRUM2MTk2Ni0yLjEiIHhtcE1NOkluc3RhbmNlSUQ9InhtcC5paWQ6MzYxODRhNjktNmYzOC1hYTQyLThkMTUtMDRmMDhlNDllYjZiIiB4bXBNTTpEb2N1bWVudElEPSJhZG9iZTpkb2NpZDpwaG90b3Nob3A6OGZkYTg1NzktZDZjOC0xZTQ3LWE2YjAtYzFmYzExNWIzZDUzIiB4bXBNTTpPcmlnaW5hbERvY3VtZW50SUQ9InhtcC5kaWQ6N2EzMGIwYWEtZmE1NS1hYzRlLWFkODItNjEwNTRiMzllMWUzIj4gPHBob3Rvc2hvcDpEb2N1bWVudEFuY2VzdG9ycz4gPHJkZjpCYWc+IDxyZGY6bGk+YWRvYmU6ZG9jaWQ6cGhvdG9zaG9wOjI5YWFmNzNjLTViOGMtOWE0MC1hYjk2LWNhZWQ3YjU4MmZmYTwvcmRmOmxpPiA8cmRmOmxpPmFkb2JlOmRvY2lkOnBob3Rvc2hvcDo1ZTRlNTM3Ni0yMjg0LWM3NDEtOTNmMC05ODQ0ZDZiY2U2OGI8L3JkZjpsaT4gPHJkZjpsaT54bXAuZGlkOjIwYjUxYTRhLWIwYjktNDc0Mi1iZTQ2LTQyN2Y4NGFkYmQ0MjwvcmRmOmxpPiA8cmRmOmxpPnhtcC5kaWQ6N2EzMGIwYWEtZmE1NS1hYzRlLWFkODItNjEwNTRiMzllMWUzPC9yZGY6bGk+IDxyZGY6bGk+eG1wLmRpZDpkNTI3ZjFmNS05YTUwLTAxNDctOTE3MC03ZWM4Zjc3YjljMmY8L3JkZjpsaT4gPC9yZGY6QmFnPiA8L3Bob3Rvc2hvcDpEb2N1bWVudEFuY2VzdG9ycz4gPHhtcE1NOkhpc3Rvcnk+IDxyZGY6U2VxPiA8cmRmOmxpIHN0RXZ0OmFjdGlvbj0iY3JlYXRlZCIgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDo3YTMwYjBhYS1mYTU1LWFjNGUtYWQ4Mi02MTA1NGIzOWUxZTMiIHN0RXZ0OndoZW49IjIwMjYtMDItMTZUMTE6MzQ6NDFaIiBzdEV2dDpzb2Z0d2FyZUFnZW50PSJBZG9iZSBQaG90b3Nob3AgQ0MgMjAxOSAoV2luZG93cykiLz4gPHJkZjpsaSBzdEV2dDphY3Rpb249InNhdmVkIiBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOmVkOWJmNTQ3LTYwZGItNTg0Ny05MTVhLTVmYzU3NmJhMDgyMSIgc3RFdnQ6d2hlbj0iMjAyNi0wMi0xNlQxMzo1NzoyN1oiIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIFBob3Rvc2hvcCBDQyAyMDE5IChXaW5kb3dzKSIgc3RFdnQ6Y2hhbmdlZD0iLyIvPiA8cmRmOmxpIHN0RXZ0OmFjdGlvbj0ic2F2ZWQiIHN0RXZ0Omluc3RhbmNlSUQ9InhtcC5paWQ6YWNiOWJjNWEtMmQ2Ni01ZDRhLTlhZjMtYmM4YjRjMDE2NWE4IiBzdEV2dDp3aGVuPSIyMDI2LTAyLTE2VDIwOjA0OjA0WiIgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWRvYmUgUGhvdG9zaG9wIENDIDIwMTkgKFdpbmRvd3MpIiBzdEV2dDpjaGFuZ2VkPSIvIi8+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJjb252ZXJ0ZWQiIHN0RXZ0OnBhcmFtZXRlcnM9ImZyb20gYXBwbGljYXRpb24vdm5kLmFkb2JlLnBob3Rvc2hvcCB0byBpbWFnZS9wbmciLz4gPHJkZjpsaSBzdEV2dDphY3Rpb249ImRlcml2ZWQiIHN0RXZ0OnBhcmFtZXRlcnM9ImNvbnZlcnRlZCBmcm9tIGFwcGxpY2F0aW9uL3ZuZC5hZG9iZS5waG90b3Nob3AgdG8gaW1hZ2UvcG5nIi8+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJzYXZlZCIgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDozNjE4NGE2OS02ZjM4LWFhNDItOGQxNS0wNGYwOGU0OWViNmIiIHN0RXZ0OndoZW49IjIwMjYtMDItMTZUMjA6MDQ6MDRaIiBzdEV2dDpzb2Z0d2FyZUFnZW50PSJBZG9iZSBQaG90b3Nob3AgQ0MgMjAxOSAoV2luZG93cykiIHN0RXZ0OmNoYW5nZWQ9Ii8iLz4gPC9yZGY6U2VxPiA8L3htcE1NOkhpc3Rvcnk+IDx4bXBNTTpEZXJpdmVkRnJvbSBzdFJlZjppbnN0YW5jZUlEPSJ4bXAuaWlkOmFjYjliYzVhLTJkNjYtNWQ0YS05YWYzLWJjOGI0YzAxNjVhOCIgc3RSZWY6ZG9j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";

var CHAR_PNG_2 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAHAAAABgCAYAAADFNvbQAAAACXBIWXMAAAsTAAALEwEAmpwYAAALDWlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgNS42LWMxNDUgNzkuMTYzNDk5LCAyMDE4LzA4LzEzLTE2OjQwOjIyICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOmRjPSJodHRwOi8vcHVybC5vcmcvZGMvZWxlbWVudHMvMS4xLyIgeG1sbnM6cGhvdG9zaG9wPSJodHRwOi8vbnMuYWRvYmUuY29tL3Bob3Rvc2hvcC8xLjAvIiB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIgeG1sbnM6c3RFdnQ9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZUV2ZW50IyIgeG1sbnM6c3RSZWY9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZVJlZiMiIHhtcDpDcmVhdG9yVG9vbD0iQWRvYmUgUGhvdG9zaG9wIENDIDIwMTkgKFdpbmRvd3MpIiB4bXA6Q3JlYXRlRGF0ZT0iMjAyNi0wMi0xNlQxMTozNDo0MVoiIHhtcDpNb2RpZnlEYXRlPSIyMDI2LTAyLTE2VDE0OjU5OjAzWiIgeG1wOk1ldGFkYXRhRGF0ZT0iMjAyNi0wMi0xNlQxNDo1OTowM1oiIGRjOmZvcm1hdD0iaW1hZ2UvcG5nIiBwaG90b3Nob3A6Q29sb3JNb2RlPSIzIiBwaG90b3Nob3A6SUNDUHJvZmlsZT0ic1JHQiBJRUM2MTk2Ni0yLjEiIHhtcE1NOkluc3RhbmNlSUQ9InhtcC5paWQ6MmY1ZjlhYjAtN2QzNC02NTQ5LWI2OTgtYWE4N2JkOTk5NTY5IiB4bXBNTTpEb2N1bWVudElEPSJhZG9iZTpkb2NpZDpwaG90b3Nob3A6ZjlmMmJhYzUtODBiYy1lODQ2LTljYTItY2YxMDRmYzIzYTQ0IiB4bXBNTTpPcmlnaW5hbERvY3VtZW50SUQ9InhtcC5kaWQ6N2EzMGIwYWEtZmE1NS1hYzRlLWFkODItNjEwNTRiMzllMWUzIj4gPHBob3Rvc2hvcDpEb2N1bWVudEFuY2VzdG9ycz4gPHJkZjpCYWc+IDxyZGY6bGk+YWRvYmU6ZG9jaWQ6cGhvdG9zaG9wOjI5YWFmNzNjLTViOGMtOWE0MC1hYjk2LWNhZWQ3YjU4MmZmYTwvcmRmOmxpPiA8cmRmOmxpPmFkb2JlOmRvY2lkOnBob3Rvc2hvcDo1ZTRlNTM3Ni0yMjg0LWM3NDEtOTNmMC05ODQ0ZDZiY2U2OGI8L3JkZjpsaT4gPHJkZjpsaT54bXAuZGlkOjIwYjUxYTRhLWIwYjktNDc0Mi1iZTQ2LTQyN2Y4NGFkYmQ0MjwvcmRmOmxpPiA8cmRmOmxpPnhtcC5kaWQ6N2EzMGIwYWEtZmE1NS1hYzRlLWFkODItNjEwNTRiMzllMWUzPC9yZGY6bGk+IDxyZGY6bGk+eG1wLmRpZDpkNTI3ZjFmNS05YTUwLTAxNDctOTE3MC03ZWM4Zjc3YjljMmY8L3JkZjpsaT4gPC9yZGY6QmFnPiA8L3Bob3Rvc2hvcDpEb2N1bWVudEFuY2VzdG9ycz4gPHhtcE1NOkhpc3Rvcnk+IDxyZGY6U2VxPiA8cmRmOmxpIHN0RXZ0OmFjdGlvbj0iY3JlYXRlZCIgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDo3YTMwYjBhYS1mYTU1LWFjNGUtYWQ4Mi02MTA1NGIzOWUxZTMiIHN0RXZ0OndoZW49IjIwMjYtMDItMTZUMTE6MzQ6NDFaIiBzdEV2dDpzb2Z0d2FyZUFnZW50PSJBZG9iZSBQaG90b3Nob3AgQ0MgMjAxOSAoV2luZG93cykiLz4gPHJkZjpsaSBzdEV2dDphY3Rpb249InNhdmVkIiBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOmVkOWJmNTQ3LTYwZGItNTg0Ny05MTVhLTVmYzU3NmJhMDgyMSIgc3RFdnQ6d2hlbj0iMjAyNi0wMi0xNlQxMzo1NzoyN1oiIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIFBob3Rvc2hvcCBDQyAyMDE5IChXaW5kb3dzKSIgc3RFdnQ6Y2hhbmdlZD0iLyIvPiA8cmRmOmxpIHN0RXZ0OmFjdGlvbj0ic2F2ZWQiIHN0RXZ0Omluc3RhbmNlSUQ9InhtcC5paWQ6ZjM3MjFmNDYtODJlMy1jNzQ4LTlmYjYtOWUyMTg5ODM2Y2VlIiBzdEV2dDp3aGVuPSIyMDI2LTAyLTE2VDE0OjU5OjAzWiIgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWRvYmUgUGhvdG9zaG9wIENDIDIwMTkgKFdpbmRvd3MpIiBzdEV2dDpjaGFuZ2VkPSIvIi8+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJjb252ZXJ0ZWQiIHN0RXZ0OnBhcmFtZXRlcnM9ImZyb20gYXBwbGljYXRpb24vdm5kLmFkb2JlLnBob3Rvc2hvcCB0byBpbWFnZS9wbmciLz4gPHJkZjpsaSBzdEV2dDphY3Rpb249ImRlcml2ZWQiIHN0RXZ0OnBhcmFtZXRlcnM9ImNvbnZlcnRlZCBmcm9tIGFwcGxpY2F0aW9uL3ZuZC5hZG9iZS5waG90b3Nob3AgdG8gaW1hZ2UvcG5nIi8+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJzYXZlZCIgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDoyZjVmOWFiMC03ZDM0LTY1NDktYjY5OC1hYTg3YmQ5OTk1NjkiIHN0RXZ0OndoZW49IjIwMjYtMDItMTZUMTQ6NTk6MDNaIiBzdEV2dDpzb2Z0d2FyZUFnZW50PSJBZG9iZSBQaG90b3Nob3AgQ0MgMjAxOSAoV2luZG93cykiIHN0RXZ0OmNoYW5nZWQ9Ii8iLz4gPC9yZGY6U2VxPiA8L3htcE1NOkhpc3Rvcnk+IDx4bXBNTTpEZXJpdmVkRnJvbSBzdFJlZjppbnN0YW5jZUlEPSJ4bXAuaWlkOmYzNzIxZjQ2LTgyZTMtYzc0OC05ZmI2LTllMjE4OTgzNmNlZSIgc3RSZWY6ZG9j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";

var CHAR_PNG_3 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAHAAAABgCAYAAADFNvbQAAAACXBIWXMAAAsTAAALEwEAmpwYAAALDWlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgNS42LWMxNDUgNzkuMTYzNDk5LCAyMDE4LzA4LzEzLTE2OjQwOjIyICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOmRjPSJodHRwOi8vcHVybC5vcmcvZGMvZWxlbWVudHMvMS4xLyIgeG1sbnM6cGhvdG9zaG9wPSJodHRwOi8vbnMuYWRvYmUuY29tL3Bob3Rvc2hvcC8xLjAvIiB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIgeG1sbnM6c3RFdnQ9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZUV2ZW50IyIgeG1sbnM6c3RSZWY9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZVJlZiMiIHhtcDpDcmVhdG9yVG9vbD0iQWRvYmUgUGhvdG9zaG9wIENDIDIwMTkgKFdpbmRvd3MpIiB4bXA6Q3JlYXRlRGF0ZT0iMjAyNi0wMi0xNlQxMTozNDo0MVoiIHhtcDpNb2RpZnlEYXRlPSIyMDI2LTAyLTE2VDE0OjU4OjQ4WiIgeG1wOk1ldGFkYXRhRGF0ZT0iMjAyNi0wMi0xNlQxNDo1ODo0OFoiIGRjOmZvcm1hdD0iaW1hZ2UvcG5nIiBwaG90b3Nob3A6Q29sb3JNb2RlPSIzIiBwaG90b3Nob3A6SUNDUHJvZmlsZT0ic1JHQiBJRUM2MTk2Ni0yLjEiIHhtcE1NOkluc3RhbmNlSUQ9InhtcC5paWQ6YWVmMjk3YTItMTk5OS0xZTQ5LWJjMjMtZGZiMGI5NGNkOGQ4IiB4bXBNTTpEb2N1bWVudElEPSJhZG9iZTpkb2NpZDpwaG90b3Nob3A6ZmRhMjdhYWQtNzc0NC1iZDRjLWI1OTktN2QyNGFhZDI5MmQwIiB4bXBNTTpPcmlnaW5hbERvY3VtZW50SUQ9InhtcC5kaWQ6N2EzMGIwYWEtZmE1NS1hYzRlLWFkODItNjEwNTRiMzllMWUzIj4gPHBob3Rvc2hvcDpEb2N1bWVudEFuY2VzdG9ycz4gPHJkZjpCYWc+IDxyZGY6bGk+YWRvYmU6ZG9jaWQ6cGhvdG9zaG9wOjI5YWFmNzNjLTViOGMtOWE0MC1hYjk2LWNhZWQ3YjU4MmZmYTwvcmRmOmxpPiA8cmRmOmxpPmFkb2JlOmRvY2lkOnBob3Rvc2hvcDo1ZTRlNTM3Ni0yMjg0LWM3NDEtOTNmMC05ODQ0ZDZiY2U2OGI8L3JkZjpsaT4gPHJkZjpsaT54bXAuZGlkOjIwYjUxYTRhLWIwYjktNDc0Mi1iZTQ2LTQyN2Y4NGFkYmQ0MjwvcmRmOmxpPiA8cmRmOmxpPnhtcC5kaWQ6N2EzMGIwYWEtZmE1NS1hYzRlLWFkODItNjEwNTRiMzllMWUzPC9yZGY6bGk+IDxyZGY6bGk+eG1wLmRpZDpkNTI3ZjFmNS05YTUwLTAxNDctOTE3MC03ZWM4Zjc3YjljMmY8L3JkZjpsaT4gPC9yZGY6QmFnPiA8L3Bob3Rvc2hvcDpEb2N1bWVudEFuY2VzdG9ycz4gPHhtcE1NOkhpc3Rvcnk+IDxyZGY6U2VxPiA8cmRmOmxpIHN0RXZ0OmFjdGlvbj0iY3JlYXRlZCIgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDo3YTMwYjBhYS1mYTU1LWFjNGUtYWQ4Mi02MTA1NGIzOWUxZTMiIHN0RXZ0OndoZW49IjIwMjYtMDItMTZUMTE6MzQ6NDFaIiBzdEV2dDpzb2Z0d2FyZUFnZW50PSJBZG9iZSBQaG90b3Nob3AgQ0MgMjAxOSAoV2luZG93cykiLz4gPHJkZjpsaSBzdEV2dDphY3Rpb249InNhdmVkIiBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOmVkOWJmNTQ3LTYwZGItNTg0Ny05MTVhLTVmYzU3NmJhMDgyMSIgc3RFdnQ6d2hlbj0iMjAyNi0wMi0xNlQxMzo1NzoyN1oiIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIFBob3Rvc2hvcCBDQyAyMDE5IChXaW5kb3dzKSIgc3RFdnQ6Y2hhbmdlZD0iLyIvPiA8cmRmOmxpIHN0RXZ0OmFjdGlvbj0ic2F2ZWQiIHN0RXZ0Omluc3RhbmNlSUQ9InhtcC5paWQ6Y2YyNGIwNTctZjBiMi02NTRmLWEyNmQtYTc1YjFiZTZkOWUwIiBzdEV2dDp3aGVuPSIyMDI2LTAyLTE2VDE0OjU4OjQ4WiIgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWRvYmUgUGhvdG9zaG9wIENDIDIwMTkgKFdpbmRvd3MpIiBzdEV2dDpjaGFuZ2VkPSIvIi8+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJjb252ZXJ0ZWQiIHN0RXZ0OnBhcmFtZXRlcnM9ImZyb20gYXBwbGljYXRpb24vdm5kLmFkb2JlLnBob3Rvc2hvcCB0byBpbWFnZS9wbmciLz4gPHJkZjpsaSBzdEV2dDphY3Rpb249ImRlcml2ZWQiIHN0RXZ0OnBhcmFtZXRlcnM9ImNvbnZlcnRlZCBmcm9tIGFwcGxpY2F0aW9uL3ZuZC5hZG9iZS5waG90b3Nob3AgdG8gaW1hZ2UvcG5nIi8+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJzYXZlZCIgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDphZWYyOTdhMi0xOTk5LTFlNDktYmMyMy1kZmIwYjk0Y2Q4ZDgiIHN0RXZ0OndoZW49IjIwMjYtMDItMTZUMTQ6NTg6NDhaIiBzdEV2dDpzb2Z0d2FyZUFnZW50PSJBZG9iZSBQaG90b3Nob3AgQ0MgMjAxOSAoV2luZG93cykiIHN0RXZ0OmNoYW5nZWQ9Ii8iLz4gPC9yZGY6U2VxPiA8L3htcE1NOkhpc3Rvcnk+IDx4bXBNTTpEZXJpdmVkRnJvbSBzdFJlZjppbnN0YW5jZUlEPSJ4bXAuaWlkOmNmMjRiMDU3LWYwYjItNjU0Zi1hMjZkLWE3NWIxYmU2ZDllMCIgc3RSZWY6ZG9j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";

var CHAR_PNG_4 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAHAAAABgCAYAAADFNvbQAAAACXBIWXMAAAsTAAALEwEAmpwYAAALDWlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgNS42LWMxNDUgNzkuMTYzNDk5LCAyMDE4LzA4LzEzLTE2OjQwOjIyICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOmRjPSJodHRwOi8vcHVybC5vcmcvZGMvZWxlbWVudHMvMS4xLyIgeG1sbnM6cGhvdG9zaG9wPSJodHRwOi8vbnMuYWRvYmUuY29tL3Bob3Rvc2hvcC8xLjAvIiB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIgeG1sbnM6c3RFdnQ9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZUV2ZW50IyIgeG1sbnM6c3RSZWY9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZVJlZiMiIHhtcDpDcmVhdG9yVG9vbD0iQWRvYmUgUGhvdG9zaG9wIENDIDIwMTkgKFdpbmRvd3MpIiB4bXA6Q3JlYXRlRGF0ZT0iMjAyNi0wMi0xNlQxMTozNDo0MVoiIHhtcDpNb2RpZnlEYXRlPSIyMDI2LTAyLTE2VDE0OjU5OjIzWiIgeG1wOk1ldGFkYXRhRGF0ZT0iMjAyNi0wMi0xNlQxNDo1OToyM1oiIGRjOmZvcm1hdD0iaW1hZ2UvcG5nIiBwaG90b3Nob3A6Q29sb3JNb2RlPSIzIiBwaG90b3Nob3A6SUNDUHJvZmlsZT0ic1JHQiBJRUM2MTk2Ni0yLjEiIHhtcE1NOkluc3RhbmNlSUQ9InhtcC5paWQ6MGVmMTI3OTgtOWY4Mi1hOTQ4LThmZDgtNTVhNWZkYTFjNjJiIiB4bXBNTTpEb2N1bWVudElEPSJhZG9iZTpkb2NpZDpwaG90b3Nob3A6MTBkNGNlNmYtZDM3Ni0yYTQwLWE2M2YtMDM0YmRiOTMxYTM2IiB4bXBNTTpPcmlnaW5hbERvY3VtZW50SUQ9InhtcC5kaWQ6N2EzMGIwYWEtZmE1NS1hYzRlLWFkODItNjEwNTRiMzllMWUzIj4gPHBob3Rvc2hvcDpEb2N1bWVudEFuY2VzdG9ycz4gPHJkZjpCYWc+IDxyZGY6bGk+YWRvYmU6ZG9jaWQ6cGhvdG9zaG9wOjI5YWFmNzNjLTViOGMtOWE0MC1hYjk2LWNhZWQ3YjU4MmZmYTwvcmRmOmxpPiA8cmRmOmxpPmFkb2JlOmRvY2lkOnBob3Rvc2hvcDo1ZTRlNTM3Ni0yMjg0LWM3NDEtOTNmMC05ODQ0ZDZiY2U2OGI8L3JkZjpsaT4gPHJkZjpsaT54bXAuZGlkOjIwYjUxYTRhLWIwYjktNDc0Mi1iZTQ2LTQyN2Y4NGFkYmQ0MjwvcmRmOmxpPiA8cmRmOmxpPnhtcC5kaWQ6N2EzMGIwYWEtZmE1NS1hYzRlLWFkODItNjEwNTRiMzllMWUzPC9yZGY6bGk+IDxyZGY6bGk+eG1wLmRpZDpkNTI3ZjFmNS05YTUwLTAxNDctOTE3MC03ZWM4Zjc3YjljMmY8L3JkZjpsaT4gPC9yZGY6QmFnPiA8L3Bob3Rvc2hvcDpEb2N1bWVudEFuY2VzdG9ycz4gPHhtcE1NOkhpc3Rvcnk+IDxyZGY6U2VxPiA8cmRmOmxpIHN0RXZ0OmFjdGlvbj0iY3JlYXRlZCIgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDo3YTMwYjBhYS1mYTU1LWFjNGUtYWQ4Mi02MTA1NGIzOWUxZTMiIHN0RXZ0OndoZW49IjIwMjYtMDItMTZUMTE6MzQ6NDFaIiBzdEV2dDpzb2Z0d2FyZUFnZW50PSJBZG9iZSBQaG90b3Nob3AgQ0MgMjAxOSAoV2luZG93cykiLz4gPHJkZjpsaSBzdEV2dDphY3Rpb249InNhdmVkIiBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOmVkOWJmNTQ3LTYwZGItNTg0Ny05MTVhLTVmYzU3NmJhMDgyMSIgc3RFdnQ6d2hlbj0iMjAyNi0wMi0xNlQxMzo1NzoyN1oiIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIFBob3Rvc2hvcCBDQyAyMDE5IChXaW5kb3dzKSIgc3RFdnQ6Y2hhbmdlZD0iLyIvPiA8cmRmOmxpIHN0RXZ0OmFjdGlvbj0ic2F2ZWQiIHN0RXZ0Omluc3RhbmNlSUQ9InhtcC5paWQ6YjU5M2U3OWEtYjVjZS1kNTQ2LWI0YjQtMTIxMWQ2ZTU3MGY0IiBzdEV2dDp3aGVuPSIyMDI2LTAyLTE2VDE0OjU5OjIzWiIgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWRvYmUgUGhvdG9zaG9wIENDIDIwMTkgKFdpbmRvd3MpIiBzdEV2dDpjaGFuZ2VkPSIvIi8+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJjb252ZXJ0ZWQiIHN0RXZ0OnBhcmFtZXRlcnM9ImZyb20gYXBwbGljYXRpb24vdm5kLmFkb2JlLnBob3Rvc2hvcCB0byBpbWFnZS9wbmciLz4gPHJkZjpsaSBzdEV2dDphY3Rpb249ImRlcml2ZWQiIHN0RXZ0OnBhcmFtZXRlcnM9ImNvbnZlcnRlZCBmcm9tIGFwcGxpY2F0aW9uL3ZuZC5hZG9iZS5waG90b3Nob3AgdG8gaW1hZ2UvcG5nIi8+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJzYXZlZCIgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDowZWYxMjc5OC05ZjgyLWE5NDgtOGZkOC01NWE1ZmRhMWM2MmIiIHN0RXZ0OndoZW49IjIwMjYtMDItMTZUMTQ6NTk6MjNaIiBzdEV2dDpzb2Z0d2FyZUFnZW50PSJBZG9iZSBQaG90b3Nob3AgQ0MgMjAxOSAoV2luZG93cykiIHN0RXZ0OmNoYW5nZWQ9Ii8iLz4gPC9yZGY6U2VxPiA8L3htcE1NOkhpc3Rvcnk+IDx4bXBNTTpEZXJpdmVkRnJvbSBzdFJlZjppbnN0YW5jZUlEPSJ4bXAuaWlkOmI1OTNlNzlhLWI1Y2UtZDU0Ni1iNGI0LTEyMTFkNmU1NzBmNCIgc3RSZWY6ZG9j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";

var CHAR_PNG_5 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAHAAAABgCAYAAADFNvbQAAAACXBIWXMAAAsTAAALEwEAmpwYAAALDWlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgNS42LWMxNDUgNzkuMTYzNDk5LCAyMDE4LzA4LzEzLTE2OjQwOjIyICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOmRjPSJodHRwOi8vcHVybC5vcmcvZGMvZWxlbWVudHMvMS4xLyIgeG1sbnM6cGhvdG9zaG9wPSJodHRwOi8vbnMuYWRvYmUuY29tL3Bob3Rvc2hvcC8xLjAvIiB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIgeG1sbnM6c3RFdnQ9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZUV2ZW50IyIgeG1sbnM6c3RSZWY9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZVJlZiMiIHhtcDpDcmVhdG9yVG9vbD0iQWRvYmUgUGhvdG9zaG9wIENDIDIwMTkgKFdpbmRvd3MpIiB4bXA6Q3JlYXRlRGF0ZT0iMjAyNi0wMi0xNlQxMTozNDo0MVoiIHhtcDpNb2RpZnlEYXRlPSIyMDI2LTAyLTE2VDE0OjU5OjM5WiIgeG1wOk1ldGFkYXRhRGF0ZT0iMjAyNi0wMi0xNlQxNDo1OTozOVoiIGRjOmZvcm1hdD0iaW1hZ2UvcG5nIiBwaG90b3Nob3A6Q29sb3JNb2RlPSIzIiBwaG90b3Nob3A6SUNDUHJvZmlsZT0ic1JHQiBJRUM2MTk2Ni0yLjEiIHhtcE1NOkluc3RhbmNlSUQ9InhtcC5paWQ6ZDI1NDFlNGYtNmMyYi00MzQ5LTg2ZTAtN2Y1ZDFlZjI1Yzk3IiB4bXBNTTpEb2N1bWVudElEPSJhZG9iZTpkb2NpZDpwaG90b3Nob3A6NmQ2NzBiZjYtOTVlNy0zOTRkLTg3ZmMtNWEyOGYyMWE0Mjc1IiB4bXBNTTpPcmlnaW5hbERvY3VtZW50SUQ9InhtcC5kaWQ6N2EzMGIwYWEtZmE1NS1hYzRlLWFkODItNjEwNTRiMzllMWUzIj4gPHBob3Rvc2hvcDpEb2N1bWVudEFuY2VzdG9ycz4gPHJkZjpCYWc+IDxyZGY6bGk+YWRvYmU6ZG9jaWQ6cGhvdG9zaG9wOjI5YWFmNzNjLTViOGMtOWE0MC1hYjk2LWNhZWQ3YjU4MmZmYTwvcmRmOmxpPiA8cmRmOmxpPmFkb2JlOmRvY2lkOnBob3Rvc2hvcDo1ZTRlNTM3Ni0yMjg0LWM3NDEtOTNmMC05ODQ0ZDZiY2U2OGI8L3JkZjpsaT4gPHJkZjpsaT54bXAuZGlkOjIwYjUxYTRhLWIwYjktNDc0Mi1iZTQ2LTQyN2Y4NGFkYmQ0MjwvcmRmOmxpPiA8cmRmOmxpPnhtcC5kaWQ6N2EzMGIwYWEtZmE1NS1hYzRlLWFkODItNjEwNTRiMzllMWUzPC9yZGY6bGk+IDxyZGY6bGk+eG1wLmRpZDpkNTI3ZjFmNS05YTUwLTAxNDctOTE3MC03ZWM4Zjc3YjljMmY8L3JkZjpsaT4gPC9yZGY6QmFnPiA8L3Bob3Rvc2hvcDpEb2N1bWVudEFuY2VzdG9ycz4gPHhtcE1NOkhpc3Rvcnk+IDxyZGY6U2VxPiA8cmRmOmxpIHN0RXZ0OmFjdGlvbj0iY3JlYXRlZCIgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDo3YTMwYjBhYS1mYTU1LWFjNGUtYWQ4Mi02MTA1NGIzOWUxZTMiIHN0RXZ0OndoZW49IjIwMjYtMDItMTZUMTE6MzQ6NDFaIiBzdEV2dDpzb2Z0d2FyZUFnZW50PSJBZG9iZSBQaG90b3Nob3AgQ0MgMjAxOSAoV2luZG93cykiLz4gPHJkZjpsaSBzdEV2dDphY3Rpb249InNhdmVkIiBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOmVkOWJmNTQ3LTYwZGItNTg0Ny05MTVhLTVmYzU3NmJhMDgyMSIgc3RFdnQ6d2hlbj0iMjAyNi0wMi0xNlQxMzo1NzoyN1oiIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIFBob3Rvc2hvcCBDQyAyMDE5IChXaW5kb3dzKSIgc3RFdnQ6Y2hhbmdlZD0iLyIvPiA8cmRmOmxpIHN0RXZ0OmFjdGlvbj0ic2F2ZWQiIHN0RXZ0Omluc3RhbmNlSUQ9InhtcC5paWQ6Zjk4NTUzNDItOWVhYi0yODRlLWI5ZWQtNjAxMWUwMjY5OTRkIiBzdEV2dDp3aGVuPSIyMDI2LTAyLTE2VDE0OjU5OjM5WiIgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWRvYmUgUGhvdG9zaG9wIENDIDIwMTkgKFdpbmRvd3MpIiBzdEV2dDpjaGFuZ2VkPSIvIi8+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJjb252ZXJ0ZWQiIHN0RXZ0OnBhcmFtZXRlcnM9ImZyb20gYXBwbGljYXRpb24vdm5kLmFkb2JlLnBob3Rvc2hvcCB0byBpbWFnZS9wbmciLz4gPHJkZjpsaSBzdEV2dDphY3Rpb249ImRlcml2ZWQiIHN0RXZ0OnBhcmFtZXRlcnM9ImNvbnZlcnRlZCBmcm9tIGFwcGxpY2F0aW9uL3ZuZC5hZG9iZS5waG90b3Nob3AgdG8gaW1hZ2UvcG5nIi8+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJzYXZlZCIgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDpkMjU0MWU0Zi02YzJiLTQzNDktODZlMC03ZjVkMWVmMjVjOTciIHN0RXZ0OndoZW49IjIwMjYtMDItMTZUMTQ6NTk6MzlaIiBzdEV2dDpzb2Z0d2FyZUFnZW50PSJBZG9iZSBQaG90b3Nob3AgQ0MgMjAxOSAoV2luZG93cykiIHN0RXZ0OmNoYW5nZWQ9Ii8iLz4gPC9yZGY6U2VxPiA8L3htcE1NOkhpc3Rvcnk+IDx4bXBNTTpEZXJpdmVkRnJvbSBzdFJlZjppbnN0YW5jZUlEPSJ4bXAuaWlkOmY5ODU1MzQyLTllYWItMjg0ZS1iOWVkLTYwMTFlMDI2OTk0ZCIgc3RSZWY6ZG9j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";

var WALLS_PNG = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEAAAACACAIAAAA04/g9AAAACXBIWXMAAAsTAAALEwEAmpwYAAAFoGlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgNS42LWMxNDUgNzkuMTYzNDk5LCAyMDE4LzA4LzEzLTE2OjQwOjIyICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOmRjPSJodHRwOi8vcHVybC5vcmcvZGMvZWxlbWVudHMvMS4xLyIgeG1sbnM6cGhvdG9zaG9wPSJodHRwOi8vbnMuYWRvYmUuY29tL3Bob3Rvc2hvcC8xLjAvIiB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIgeG1sbnM6c3RFdnQ9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZUV2ZW50IyIgeG1wOkNyZWF0b3JUb29sPSJBZG9iZSBQaG90b3Nob3AgQ0MgMjAxOSAoV2luZG93cykiIHhtcDpDcmVhdGVEYXRlPSIyMDI2LTAyLTE0VDE4OjI0WiIgeG1wOk1vZGlmeURhdGU9IjIwMjYtMDItMTRUMjM6MzU6NTVaIiB4bXA6TWV0YWRhdGFEYXRlPSIyMDI2LTAyLTE0VDIzOjM1OjU1WiIgZGM6Zm9ybWF0PSJpbWFnZS9wbmciIHBob3Rvc2hvcDpDb2xvck1vZGU9IjMiIHBob3Rvc2hvcDpJQ0NQcm9maWxlPSJzUkdCIElFQzYxOTY2LTIuMSIgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDpiNDI1ZjlhZS0wNjlkLTUwNDYtYmQyOC1hZGEyZmZmNzZkZDUiIHhtcE1NOkRvY3VtZW50SUQ9InhtcC5kaWQ6YjQyNWY5YWUtMDY5ZC01MDQ2LWJkMjgtYWRhMmZmZjc2ZGQ1IiB4bXBNTTpPcmlnaW5hbERvY3VtZW50SUQ9InhtcC5kaWQ6YjQyNWY5YWUtMDY5ZC01MDQ2LWJkMjgtYWRhMmZmZjc2ZGQ1Ij4gPHBob3Rvc2hvcDpEb2N1bWVudEFuY2VzdG9ycz4gPHJkZjpCYWc+IDxyZGY6bGk+YWRvYmU6ZG9jaWQ6cGhvdG9zaG9wOjllYzhmMjIyLTk3OTYtNmY0Ni05MzgxLWIyOWRiNDY5OTkyZjwvcmRmOmxpPiA8L3JkZjpCYWc+IDwvcGhvdG9zaG9wOkRvY3VtZW50QW5jZXN0b3JzPiA8eG1wTU06SGlzdG9yeT4gPHJkZjpTZXE+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJjcmVhdGVkIiBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOmI0MjVmOWFlLTA2OWQtNTA0Ni1iZDI4LWFkYTJmZmY3NmRkNSIgc3RFdnQ6d2hlbj0iMjAyNi0wMi0xNFQxODoyNFoiIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIFBob3Rvc2hvcCBDQyAyMDE5IChXaW5kb3dzKSIvPiA8L3JkZjpTZXE+IDwveG1wTU06SGlzdG9yeT4gPC9yZGY6RGVzY3JpcHRpb24+IDwvcmRmOlJERj4gPC94OnhtcG1ldGE+IDw/eHBhY2tldCBlbmQ9InIiPz5Cg3wsAAAA0ElEQVR42u3bMQ6AIAwAQJ5jnPy+H3DwUzrwAUtssPFIx4K9CW1j29YlGuexP4yBw6Pnt4GC8vL7llA+AAAAwHzA9Xj1gvLy+5ZQPgAAAAAAAAAAAAAAAAAAAMA8QOlo5gNaiwAAAACfAZS/BwAAAAAAAAAAAAAAAAAAAABKAWrPB1LbZtH8gQAAAACYDEgdo0fzBxYAAAAAAAAAAAAAAAAAAADAJID/B8wH9EYBAABKA0zqAQAAAAAyHxD9wgIAAAAAAAAAAAB49fU4VP3vADfcDP/jUvcigAAAAABJRU5ErkJggg==";

// -- PNG Sprite Loader (port of assetLoader.ts) -------------------
// Loads character PNGs and walls.png, extracts SpriteData arrays
// Character PNGs: 112x96 = 7 frames x 3 directions, each frame 16x32
// Walls PNG: 64x128 = 4 cols x 4 rows of 16x32 sprites (16 bitmask variants)

var loadedCharacters = null;
var wallSprites = null;
var charSpriteCache = {};

function setLoadedCharacters(data) {
  loadedCharacters = data;
  charSpriteCache = {};
}

function setWallSprites(sprites) {
  wallSprites = sprites;
}

function extractSpritesFromImage(img, frameW, frameH, framesPerRow, numRows) {
  var cv = document.createElement('canvas');
  cv.width = img.width;
  cv.height = img.height;
  var cx = cv.getContext('2d');
  cx.drawImage(img, 0, 0);
  var imgData = cx.getImageData(0, 0, img.width, img.height);
  var px = imgData.data;
  var results = [];
  for (var row = 0; row < numRows; row++) {
    var rowFrames = [];
    for (var f = 0; f < framesPerRow; f++) {
      var sprite = [];
      for (var y = 0; y < frameH; y++) {
        var line = [];
        for (var x = 0; x < frameW; x++) {
          var idx = ((row * frameH + y) * img.width + (f * frameW + x)) * 4;
          var r = px[idx], g = px[idx+1], b = px[idx+2], a = px[idx+3];
          if (a < 128) {
            line.push('');
          } else {
            line.push('#' + ((1<<24)|(r<<16)|(g<<8)|b).toString(16).slice(1).toUpperCase());
          }
        }
        sprite.push(line);
      }
      rowFrames.push(sprite);
    }
    results.push(rowFrames);
  }
  return results;
}

function loadPNGSprites(callback) {
  var CHAR_PNGS = [CHAR_PNG_0, CHAR_PNG_1, CHAR_PNG_2, CHAR_PNG_3, CHAR_PNG_4, CHAR_PNG_5];
  var totalToLoad = CHAR_PNGS.length + 1;
  var loaded = 0;
  var charData = [];
  var wallData = null;

  function checkDone() {
    loaded++;
    if (loaded >= totalToLoad) {
      if (charData.length === CHAR_PNGS.length) {
        setLoadedCharacters(charData);
      }
      if (wallData) {
        setWallSprites(wallData);
      }
      if (callback) callback();
    }
  }

  // Load character PNGs
  for (var ci = 0; ci < CHAR_PNGS.length; ci++) {
    (function(index) {
      var img = new Image();
      img.onload = function() {
        // 3 direction rows (down=0, up=1, right=2), 7 frames each, 16x32
        var rows = extractSpritesFromImage(img, 16, 32, 7, 3);
        charData[index] = {
          down: rows[0],
          up: rows[1],
          right: rows[2]
        };
        checkDone();
      };
      img.onerror = function() {
        console.error('Failed to load char_' + index + '.png');
        checkDone();
      };
      img.src = CHAR_PNGS[index];
    })(ci);
  }

  // Load walls PNG
  var wallImg = new Image();
  wallImg.onload = function() {
    // 4 cols x 4 rows of 16x32 sprites = 16 bitmask variants
    var rows = extractSpritesFromImage(wallImg, 16, 32, 4, 4);
    wallData = [];
    for (var r = 0; r < 4; r++) {
      for (var c = 0; c < 4; c++) {
        wallData.push(rows[r][c]);
      }
    }
    setWallSprites(wallData);
    checkDone();
  };
  wallImg.onerror = function() {
    console.error('Failed to load walls.png');
    checkDone();
  };
  wallImg.src = WALLS_PNG;
}

// -- Updated getCharacterSprites with PNG mode --------------------

// Override getCharacterSprites to support loaded PNG characters
var _originalGetCharacterSprites = getCharacterSprites;

getCharacterSprites = function(paletteIndex) {
  if (loadedCharacters) {
    var cacheKey = 'png_' + paletteIndex;
    if (charSpriteCache[cacheKey]) return charSpriteCache[cacheKey];

    var ch = loadedCharacters[paletteIndex % loadedCharacters.length];
    var d = ch.down, u = ch.up, rt = ch.right;
    var flip = flipHorizontal;

    var sprites = {
      walk: {},
      typing: {},
      reading: {}
    };
    sprites.walk[Direction.DOWN]  = [d[0], d[1], d[2], d[1]];
    sprites.walk[Direction.UP]    = [u[0], u[1], u[2], u[1]];
    sprites.walk[Direction.RIGHT] = [rt[0], rt[1], rt[2], rt[1]];
    sprites.walk[Direction.LEFT]  = [flip(rt[0]), flip(rt[1]), flip(rt[2]), flip(rt[1])];

    sprites.typing[Direction.DOWN]  = [d[3], d[4]];
    sprites.typing[Direction.UP]    = [u[3], u[4]];
    sprites.typing[Direction.RIGHT] = [rt[3], rt[4]];
    sprites.typing[Direction.LEFT]  = [flip(rt[3]), flip(rt[4])];

    sprites.reading[Direction.DOWN]  = [d[5], d[6]];
    sprites.reading[Direction.UP]    = [u[5], u[6]];
    sprites.reading[Direction.RIGHT] = [rt[5], rt[6]];
    sprites.reading[Direction.LEFT]  = [flip(rt[5]), flip(rt[6])];

    charSpriteCache[cacheKey] = sprites;
    return sprites;
  }
  return _originalGetCharacterSprites(paletteIndex);
};

// ============================================================
// Mission Control v2 - Part 2: Engine
// Ported from pixel-agents (github.com/pablodelucca/pixel-agents)
// colorize.ts, floorTiles.ts, wallTiles.ts, tileMap.ts,
// characters.ts, renderer.ts, gameLoop.ts
// ============================================================

// -- Constants (from constants.ts) ------------------------------
// WALK_SPEED, WALK_FRAME_DUR, TYPE_FRAME_DUR, SIT_OFFSET, TILE_SIZE, Direction
// are already declared in Part 1 (sprites.js)
var Z_SORT_OFFSET = 0.5;
var MAX_DT = 0.1;               // cap delta time
var WANDER_PAUSE_MIN = 2.0;     // s
var WANDER_PAUSE_MAX = 20.0;    // s
var WANDER_MOVES_MIN = 3;
var WANDER_MOVES_MAX = 6;
var SEAT_REST_MIN = 30.0;       // s (shorter than original for demo)
var SEAT_REST_MAX = 60.0;
var FALLBACK_FLOOR_COLOR = '#808080';
var WALL_COLOR_DEFAULT = '#3A3A5C';
var CHAR_HIT_HALF_W = 8;
var CHAR_HIT_H = 24;

// Tile types
var TILE_WALL = 0;
var TILE_FLOOR = 1;

// Character states
var CharState = { IDLE: 'idle', WALK: 'walk', TYPE: 'type', READ: 'read', SLEEP: 'sleep', COFFEE: 'coffee', PHONE: 'phone', CHAT: 'chat' };

// Particle system
var particles = [];
var MAX_PARTICLES = 200;
var gameTime = 0;  // global time accumulator for visual effects

// Room grid
var ROOM_COLS = 14;
var ROOM_ROWS = 11;
var ROOM_GAP = 28;   // px horizontal gap between rooms (native coords)
var ROOM_GAP_V = 20; // px vertical gap between room rows
var ROOMS_PER_ROW = 3;

// ============================================================
// 1. COLORIZE SYSTEM (port of colorize.ts)
// ============================================================

var colorizeCache = {};

function hslToHex(h, s, l) {
  var c = (1 - Math.abs(2 * l - 1)) * s;
  var hp = h / 60;
  var x = c * (1 - Math.abs(hp % 2 - 1));
  var r1 = 0, g1 = 0, b1 = 0;
  if (hp < 1)      { r1 = c; g1 = x; b1 = 0; }
  else if (hp < 2) { r1 = x; g1 = c; b1 = 0; }
  else if (hp < 3) { r1 = 0; g1 = c; b1 = x; }
  else if (hp < 4) { r1 = 0; g1 = x; b1 = c; }
  else if (hp < 5) { r1 = x; g1 = 0; b1 = c; }
  else             { r1 = c; g1 = 0; b1 = x; }
  var m = l - c / 2;
  var clamp = function(v) { return Math.max(0, Math.min(255, Math.round((v + m) * 255))); };
  return '#' + clamp(r1).toString(16).padStart(2,'0')
             + clamp(g1).toString(16).padStart(2,'0')
             + clamp(b1).toString(16).padStart(2,'0');
}

function rgbToHsl(r, g, b) {
  var rf = r / 255, gf = g / 255, bf = b / 255;
  var max = Math.max(rf, gf, bf), min = Math.min(rf, gf, bf);
  var l = (max + min) / 2;
  if (max === min) return [0, 0, l];
  var d = max - min;
  var s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
  var h = 0;
  if (max === rf) h = ((gf - bf) / d + (gf < bf ? 6 : 0)) * 60;
  else if (max === gf) h = ((bf - rf) / d + 2) * 60;
  else h = ((rf - gf) / d + 4) * 60;
  return [h, s, l];
}

/** Photoshop Colorize: grayscale -> fixed HSL */
function colorizeSprite(sprite, color) {
  var h = color.h, s = color.s, b = color.b, c = color.c;
  var result = [];
  for (var ri = 0; ri < sprite.length; ri++) {
    var row = sprite[ri];
    var newRow = [];
    for (var ci = 0; ci < row.length; ci++) {
      var pixel = row[ci];
      if (pixel === '') { newRow.push(''); continue; }
      var pr = parseInt(pixel.slice(1,3), 16);
      var pg = parseInt(pixel.slice(3,5), 16);
      var pb = parseInt(pixel.slice(5,7), 16);
      // Perceived luminance
      var lightness = (0.299 * pr + 0.587 * pg + 0.114 * pb) / 255;
      // Apply contrast
      if (c !== 0) {
        var factor = (100 + c) / 100;
        lightness = 0.5 + (lightness - 0.5) * factor;
      }
      // Apply brightness
      if (b !== 0) { lightness = lightness + b / 200; }
      lightness = Math.max(0, Math.min(1, lightness));
      newRow.push(hslToHex(h, s / 100, lightness));
    }
    result.push(newRow);
  }
  return result;
}

function getColorizedSprite(cacheKey, sprite, color) {
  if (colorizeCache[cacheKey]) return colorizeCache[cacheKey];
  var result = colorizeSprite(sprite, color);
  colorizeCache[cacheKey] = result;
  return result;
}

// ============================================================
// 2. FLOOR TILE SYSTEM (port of floorTiles.ts)
// ============================================================

// Default 16x16 floor tile with subtle diagonal pattern (not solid gray)
var DEFAULT_FLOOR_SPRITE = (function() {
  var tile = [];
  var a = '#808080'; // base gray
  var b = '#878787'; // slightly lighter
  var c = '#797979'; // slightly darker
  for (var r = 0; r < TILE_SIZE; r++) {
    var row = [];
    for (var ci = 0; ci < TILE_SIZE; ci++) {
      // Diagonal checkerboard pattern (2px stride)
      var diag = ((r + ci) >> 1) & 1;
      if (diag) {
        row.push(b);
      } else {
        row.push(((r ^ ci) & 1) ? c : a);
      }
    }
    tile.push(row);
  }
  return tile;
})();

// Wood plank floor: horizontal boards with grain lines (executive/monetizados)
var WOOD_FLOOR_SPRITE = (function() {
  var tile = [];
  // 4 planks of ~4px height each, alternating tones
  var planks = [
    { base: '#8a8a8a', light: '#919191', dark: '#7e7e7e', grain: '#757575' },
    { base: '#7d7d7d', light: '#858585', dark: '#737373', grain: '#6c6c6c' },
    { base: '#878787', light: '#8e8e8e', dark: '#7b7b7b', grain: '#727272' },
    { base: '#808080', light: '#888888', dark: '#767676', grain: '#6f6f6f' }
  ];
  for (var r = 0; r < 16; r++) {
    var row = [];
    var pi = Math.floor(r / 4);
    var p = planks[pi];
    var isEdge = (r % 4 === 0); // dark line between planks
    for (var c = 0; c < 16; c++) {
      if (isEdge) {
        row.push(p.dark);
      } else if ((r + c * 3) % 7 === 0) {
        row.push(p.grain); // wood grain
      } else if ((r * 2 + c) % 11 < 2) {
        row.push(p.light); // lighter highlights
      } else {
        row.push(p.base);
      }
    }
    tile.push(row);
  }
  return tile;
})();
WOOD_FLOOR_SPRITE._id = 'wood';

// Stone slab floor: irregular blocks with mortar gaps (gothic/sombrias)
var STONE_FLOOR_SPRITE = (function() {
  var tile = [];
  var a = '#7a7a7a'; // stone base
  var b = '#848484'; // stone light
  var c = '#717171'; // stone dark
  var g = '#606060'; // grout/mortar between stones
  // Pattern: 4x4 and 4x8 stone blocks with 1px grout lines
  for (var r = 0; r < 16; r++) {
    var row = [];
    var isHGrout = (r === 0 || r === 5 || r === 10 || r === 15);
    for (var ci = 0; ci < 16; ci++) {
      if (isHGrout) {
        row.push(g);
      } else {
        // Vertical grout — offset pattern for brick-like layout
        var vGrout;
        if (r < 5) {
          vGrout = (ci === 0 || ci === 6 || ci === 11);
        } else if (r < 10) {
          vGrout = (ci === 0 || ci === 4 || ci === 9 || ci === 14);
        } else {
          vGrout = (ci === 0 || ci === 7 || ci === 12);
        }
        if (vGrout) {
          row.push(g);
        } else {
          // Stone surface variation
          var v = ((r * 7 + ci * 13) % 5);
          row.push(v === 0 ? c : v === 1 ? b : a);
        }
      }
    }
    tile.push(row);
  }
  return tile;
})();
STONE_FLOOR_SPRITE._id = 'stone';

// Metal diamond plate floor: industrial cross-hatch (warroom/guerra)
var METAL_FLOOR_SPRITE = (function() {
  var tile = [];
  var a = '#838383'; // metal base
  var b = '#8d8d8d'; // highlight/ridge
  var c = '#767676'; // shadow/valley
  var d = '#6e6e6e'; // dark edge
  for (var r = 0; r < 16; r++) {
    var row = [];
    for (var ci = 0; ci < 16; ci++) {
      // Diamond plate: diagonal ridges every 4px, crossing
      var d1 = (r + ci) % 4 === 0;
      var d2 = (r - ci + 16) % 4 === 0;
      if (d1 && d2) {
        row.push(b); // intersection — brightest
      } else if (d1 || d2) {
        row.push(b); // ridge line
      } else if ((r + ci + 1) % 4 === 0 || (r - ci + 17) % 4 === 0) {
        row.push(c); // shadow next to ridge
      } else {
        row.push(((r * 3 + ci * 5) % 3 === 0) ? c : a); // base with subtle noise
      }
    }
    tile.push(row);
  }
  return tile;
})();
METAL_FLOOR_SPRITE._id = 'metal';

function getColorizedFloorSprite(color, floorSprite) {
  var fs = floorSprite || DEFAULT_FLOOR_SPRITE;
  var fid = fs._id || 'default';
  var key = 'floor-' + fid + '-' + color.h + '-' + color.s + '-' + color.b + '-' + color.c;
  return getColorizedSprite(key, fs, {
    h: color.h, s: color.s, b: color.b, c: color.c
  });
}

// ============================================================
// 3. WALL COLOR (port of wallTiles.ts wallColorToHex)
// ============================================================

function wallColorToHex(color) {
  var h = color.h, s = color.s, b = color.b, c = color.c;
  var lightness = 0.5;
  // Apply contrast
  if (c !== 0) {
    var factor = (100 + c) / 100;
    lightness = 0.5 + (lightness - 0.5) * factor;
  }
  // Apply brightness
  if (b !== 0) { lightness = lightness + b / 200; }
  lightness = Math.max(0, Math.min(1, lightness));
  return hslToHex(h, s / 100, lightness);
}

// ============================================================
// 3b. WALL AUTO-TILING (port of wallTiles.ts)
// ============================================================

// wallSprites is set by Part 1 loader (setWallSprites)
// 16 sprites indexed by 4-bit bitmask: N=1, E=2, S=4, W=8

function getWallBitmask(col, row, tileMap) {
  var tmRows = tileMap.length;
  var tmCols = tmRows > 0 ? tileMap[0].length : 0;
  var mask = 0;
  if (row > 0 && tileMap[row - 1][col] === TILE_WALL) mask |= 1;            // N
  if (col < tmCols - 1 && tileMap[row][col + 1] === TILE_WALL) mask |= 2;   // E
  if (row < tmRows - 1 && tileMap[row + 1][col] === TILE_WALL) mask |= 4;   // S
  if (col > 0 && tileMap[row][col - 1] === TILE_WALL) mask |= 8;            // W
  return mask;
}

function getColorizedWallSprite(col, row, tileMap, color) {
  if (!wallSprites) return null;
  var mask = getWallBitmask(col, row, tileMap);
  var sprite = wallSprites[mask];
  if (!sprite) return null;
  var cacheKey = 'wall-' + mask + '-' + color.h + '-' + color.s + '-' + color.b + '-' + color.c;
  var colorized = getColorizedSprite(cacheKey, sprite, {
    h: color.h, s: color.s, b: color.b, c: color.c
  });
  return { sprite: colorized, offsetY: TILE_SIZE - sprite.length };
}

function getWallInstances(tileMap, wallColor) {
  if (!wallSprites) return [];
  var tmRows = tileMap.length;
  var tmCols = tmRows > 0 ? tileMap[0].length : 0;
  var instances = [];
  for (var r = 0; r < tmRows; r++) {
    for (var c = 0; c < tmCols; c++) {
      if (tileMap[r][c] !== TILE_WALL) continue;
      var wallInfo = getColorizedWallSprite(c, r, tileMap, wallColor);
      if (!wallInfo) continue;
      instances.push({
        sprite: wallInfo.sprite,
        x: c * TILE_SIZE,
        y: r * TILE_SIZE + wallInfo.offsetY,
        zY: (r + 1) * TILE_SIZE
      });
    }
  }
  return instances;
}

// ============================================================
// 4. PATHFINDING (port of tileMap.ts)
// ============================================================

function isWalkable(col, row, tileMap, blockedTiles) {
  var rows = tileMap.length;
  var cols = rows > 0 ? tileMap[0].length : 0;
  if (row < 0 || row >= rows || col < 0 || col >= cols) return false;
  if (tileMap[row][col] === TILE_WALL) return false;
  if (blockedTiles.has(col + ',' + row)) return false;
  return true;
}

function getWalkableTiles(tileMap, blockedTiles) {
  var rows = tileMap.length;
  var cols = rows > 0 ? tileMap[0].length : 0;
  var tiles = [];
  for (var r = 0; r < rows; r++) {
    for (var c = 0; c < cols; c++) {
      if (isWalkable(c, r, tileMap, blockedTiles)) {
        tiles.push({ col: c, row: r });
      }
    }
  }
  return tiles;
}

function findPath(startCol, startRow, endCol, endRow, tileMap, blockedTiles) {
  if (startCol === endCol && startRow === endRow) return [];
  var key = function(c, r) { return c + ',' + r; };
  var startKey = key(startCol, startRow);
  var endKey = key(endCol, endRow);
  if (!isWalkable(endCol, endRow, tileMap, blockedTiles)) return [];
  var visited = new Set();
  visited.add(startKey);
  var parent = new Map();
  var queue = [{ col: startCol, row: startRow }];
  var dirs = [
    { dc: 0, dr: -1 },
    { dc: 0, dr: 1 },
    { dc: -1, dr: 0 },
    { dc: 1, dr: 0 },
  ];
  while (queue.length > 0) {
    var curr = queue.shift();
    var currKey = key(curr.col, curr.row);
    if (currKey === endKey) {
      var path = [];
      var k = endKey;
      while (k !== startKey) {
        var parts = k.split(',');
        path.unshift({ col: parseInt(parts[0]), row: parseInt(parts[1]) });
        k = parent.get(k);
      }
      return path;
    }
    for (var i = 0; i < dirs.length; i++) {
      var nc = curr.col + dirs[i].dc;
      var nr = curr.row + dirs[i].dr;
      var nk = key(nc, nr);
      if (visited.has(nk)) continue;
      if (!isWalkable(nc, nr, tileMap, blockedTiles)) continue;
      visited.add(nk);
      parent.set(nk, currKey);
      queue.push({ col: nc, row: nr });
    }
  }
  return [];
}

// ============================================================
// 5. SECTOR THEMES (FloorColor per subnicho)
// ============================================================

var SECTOR_THEMES = {
  executive: {
    floorColor: { h: 140, s: 25, b: 10, c: 0 },
    wallColor:  { h: 140, s: 15, b: -38, c: 0 },
    accent: '#4ade80',
    label: 'Monetizados',
    floorSprite: WOOD_FLOOR_SPRITE
  },
  warroom: {
    floorColor: { h: 120, s: 20, b: 5, c: 0 },
    wallColor:  { h: 120, s: 15, b: -38, c: 0 },
    accent: '#6ee77a',
    label: 'Relatos de Guerra',
    floorSprite: METAL_FLOOR_SPRITE
  },
  gothic: {
    floorColor: { h: 270, s: 20, b: 5, c: 0 },
    wallColor:  { h: 270, s: 15, b: -38, c: 0 },
    accent: '#a78bfa',
    label: 'Historias Sombrias',
    floorSprite: STONE_FLOOR_SPRITE
  },
  darklab: {
    floorColor: { h: 0, s: 25, b: 5, c: 0 },
    wallColor:  { h: 0, s: 15, b: -38, c: 0 },
    accent: '#f87171',
    label: 'Terror'
  },
  demonetized: {
    floorColor: { h: 0, s: 15, b: 0, c: 0 },
    wallColor:  { h: 0, s: 10, b: -38, c: 0 },
    accent: '#f87171',
    label: 'Desmonetizados'
  },
  command: {
    floorColor: { h: 30, s: 25, b: 10, c: 0 },
    wallColor:  { h: 30, s: 15, b: -38, c: 0 },
    accent: '#fb923c',
    label: 'Comando'
  },
  wisdom: {
    floorColor: { h: 45, s: 25, b: 10, c: 0 },
    wallColor:  { h: 45, s: 15, b: -38, c: 0 },
    accent: '#fbbf24',
    label: 'Sabedoria'
  },
  startup: {
    floorColor: { h: 210, s: 15, b: 0, c: 0 },
    wallColor:  { h: 210, s: 10, b: -38, c: 0 },
    accent: '#a1a1aa',
    label: 'Startup'
  },
};

// Map backend tema -> theme key
function getThemeKey(tema) {
  if (!tema) return 'startup';
  var t = tema.toLowerCase();
  if (t.indexOf('executive') >= 0 || t.indexOf('monetiz') >= 0) return 'executive';
  if (t.indexOf('war') >= 0 || t.indexOf('guerra') >= 0) return 'warroom';
  if (t.indexOf('gothic') >= 0 || t.indexOf('sombr') >= 0) return 'gothic';
  if (t.indexOf('dark') >= 0 || t.indexOf('terror') >= 0) return 'darklab';
  if (t.indexOf('demon') >= 0 || t.indexOf('desmon') >= 0) return 'demonetized';
  if (t.indexOf('command') >= 0 || t.indexOf('comando') >= 0) return 'command';
  if (t.indexOf('wisdom') >= 0 || t.indexOf('sabed') >= 0) return 'wisdom';
  return 'startup';
}

// ============================================================
// 6. ROOM BUILDER
// ============================================================

// Workstation positions: desk top-left (2x2), chair, agent seat, facing
var WORKSTATIONS = [
  // Row 1: 3 desks (top area)
  { deskCol: 1, deskRow: 2, chairCol: 2, chairRow: 4, facingDir: Direction.UP, pcCol: 1, pcRow: 2 },
  { deskCol: 4, deskRow: 2, chairCol: 5, chairRow: 4, facingDir: Direction.UP, pcCol: 4, pcRow: 2 },
  { deskCol: 7, deskRow: 2, chairCol: 8, chairRow: 4, facingDir: Direction.UP, pcCol: 7, pcRow: 2 },
  // Row 2: 3 desks (bottom area, more spread)
  { deskCol: 1, deskRow: 6, chairCol: 2, chairRow: 8, facingDir: Direction.UP, pcCol: 1, pcRow: 6 },
  { deskCol: 5, deskRow: 6, chairCol: 6, chairRow: 8, facingDir: Direction.UP, pcCol: 5, pcRow: 6 },
  // Extra: side desk
  { deskCol: 9, deskRow: 5, chairCol: 10, chairRow: 7, facingDir: Direction.UP, pcCol: 9, pcRow: 5 },
];

// Decorative furniture (adjusted for 14x11 room)
var DECORATIONS = [
  { type: 'bookshelf',  col: 11, row: 1 },  // top-right bookshelf (1x2)
  { type: 'bookshelf',  col: 12, row: 1 },  // second bookshelf
  { type: 'whiteboard', col: 4,  row: 1 },  // whiteboard on top wall
  { type: 'plant',      col: 11, row: 4 },  // plant right side
  { type: 'plant',      col: 1,  row: 8 },  // plant bottom-left
  { type: 'cooler',     col: 11, row: 7 },  // cooler bottom-right
  { type: 'lamp',       col: 1,  row: 5 },  // lamp left side
];

// Theme-specific layouts: each theme has multiple variations so rooms look unique
// Room grid: 14 cols x 11 rows. Walls blocked at row 0, row 10. Usable: cols 1-12, rows 1-9.
// Desk = 2x2 tiles. Chair at chairCol,chairRow. PC on desk.
var THEME_LAYOUTS = {
  // === MONETIZADOS: Escritorio CEO ===
  // Mesas mogno escuro + notebooks + cadeira executiva + trofeus/cofre/globo
  executive: { variations: [
    { deskSprite: 'dark', pcSprite: 'notebook', chairSprite: 'exec',
      workstations: [
        {deskCol:1,deskRow:1,chairCol:2,chairRow:3,facingDir:Direction.DOWN,pcCol:1,pcRow:1},
        {deskCol:5,deskRow:1,chairCol:6,chairRow:3,facingDir:Direction.DOWN,pcCol:5,pcRow:1},
        {deskCol:1,deskRow:5,chairCol:3,chairRow:6,facingDir:Direction.LEFT,pcCol:1,pcRow:5},
        {deskCol:1,deskRow:7,chairCol:3,chairRow:8,facingDir:Direction.LEFT,pcCol:1,pcRow:7},
        {deskCol:11,deskRow:5,chairCol:10,chairRow:6,facingDir:Direction.RIGHT,pcCol:11,pcRow:5},
        {deskCol:11,deskRow:7,chairCol:10,chairRow:8,facingDir:Direction.RIGHT,pcCol:11,pcRow:7}
      ],
      decorations: [
        {type:'bookshelf',col:9,row:1},{type:'trophy',col:12,row:1},
        {type:'whiteboard',col:5,row:5},
        {type:'globe',col:12,row:8},{type:'safe',col:8,row:1},
        {type:'plant',col:8,row:8}
      ]
    }
  ]},
  // === HISTORIAS SOMBRIAS: Biblioteca medieval / scriptorium ===
  // Mesas de pedra + PCs + banco de pedra + candelabros/cranios
  gothic: { variations: [
    { deskSprite: 'stone', pcSprite: 'pc', chairSprite: 'stone',
      workstations: [
        {deskCol:3,deskRow:1,chairCol:4,chairRow:3,facingDir:Direction.DOWN,pcCol:3,pcRow:1},
        {deskCol:7,deskRow:1,chairCol:8,chairRow:3,facingDir:Direction.DOWN,pcCol:7,pcRow:1},
        {deskCol:11,deskRow:1,chairCol:12,chairRow:3,facingDir:Direction.DOWN,pcCol:11,pcRow:1},
        {deskCol:3,deskRow:7,chairCol:4,chairRow:6,facingDir:Direction.UP,pcCol:3,pcRow:7},
        {deskCol:7,deskRow:7,chairCol:8,chairRow:6,facingDir:Direction.UP,pcCol:7,pcRow:7},
        {deskCol:11,deskRow:7,chairCol:12,chairRow:6,facingDir:Direction.UP,pcCol:11,pcRow:7}
      ],
      decorations: [
        {type:'bookshelf',col:1,row:1},{type:'bookshelf',col:1,row:3},
        {type:'bookshelf',col:1,row:5},
        {type:'candelabra',col:6,row:4},{type:'candelabra',col:10,row:4},
        {type:'skull',col:1,row:8}
      ]
    }
  ]},
  // === RELATOS DE GUERRA: Bunker militar / sala de comando ===
  // Mesas metal + terminais CRT + banco dobravel + radio/sandbag/flag
  warroom: { variations: [
    { deskSprite: 'metal', pcSprite: 'terminal', chairSprite: 'military',
      workstations: [
        {deskCol:1,deskRow:1,chairCol:2,chairRow:3,facingDir:Direction.UP,pcCol:1,pcRow:1},
        {deskCol:4,deskRow:1,chairCol:5,chairRow:3,facingDir:Direction.UP,pcCol:4,pcRow:1},
        {deskCol:7,deskRow:1,chairCol:8,chairRow:3,facingDir:Direction.UP,pcCol:7,pcRow:1},
        {deskCol:1,deskRow:6,chairCol:2,chairRow:8,facingDir:Direction.UP,pcCol:1,pcRow:6},
        {deskCol:4,deskRow:6,chairCol:5,chairRow:8,facingDir:Direction.UP,pcCol:4,pcRow:6},
        {deskCol:7,deskRow:6,chairCol:8,chairRow:8,facingDir:Direction.UP,pcCol:7,pcRow:6}
      ],
      decorations: [
        {type:'whiteboard',col:10,row:1},{type:'whiteboard',col:10,row:4},
        {type:'radio',col:12,row:1},{type:'sandbag',col:12,row:5},
        {type:'flag',col:10,row:7},{type:'cooler',col:12,row:8}
      ]
    }
  ]}
};

function buildRoom(canal, themeKey, roomIndex) {
  var theme = SECTOR_THEMES[themeKey] || SECTOR_THEMES.startup;

  // Build tile map - ALL floor, no walls
  var tileMap = [];
  for (var r = 0; r < ROOM_ROWS; r++) {
    var row = [];
    for (var c = 0; c < ROOM_COLS; c++) {
      row.push(TILE_FLOOR);
    }
    tileMap.push(row);
  }

  // Build furniture instances
  var furniture = [];
  var blockedTiles = new Set();
  var seats = {};

  // Choose theme-specific layout (1 layout per subnicho) or fallback to global
  var layoutDef = THEME_LAYOUTS[themeKey];
  var wsLayout, decLayout, variation;
  if (layoutDef && layoutDef.variations && layoutDef.variations.length > 0) {
    variation = layoutDef.variations[0]; // layout unico por subnicho
    wsLayout = variation.workstations;
    decLayout = variation.decorations;
  } else {
    variation = null;
    wsLayout = WORKSTATIONS;
    decLayout = DECORATIONS;
  }

  // Resolve theme-specific desk, PC and chair sprites
  var deskSpriteMap = { dark: DESK_DARK_SPRITE, stone: DESK_STONE_SPRITE, metal: DESK_METAL_SPRITE };
  var pcSpriteMap = { notebook: NOTEBOOK_SPRITE, terminal: TERMINAL_SPRITE };
  var chairSpriteMap = { exec: CHAIR_EXEC_SPRITE, stone: CHAIR_STONE_SPRITE, military: CHAIR_MILITARY_SPRITE };
  var themeDeskSprite = (variation && variation.deskSprite) ? deskSpriteMap[variation.deskSprite] || DESK_SQUARE_SPRITE : DESK_SQUARE_SPRITE;
  var themePcSprite = (variation && variation.pcSprite) ? pcSpriteMap[variation.pcSprite] || PC_SPRITE : PC_SPRITE;
  var themeChairSprite = (variation && variation.chairSprite) ? chairSpriteMap[variation.chairSprite] || CHAIR_SPRITE : CHAIR_SPRITE;

  // Place workstations
  var agentes = canal.agentes || [];
  for (var wi = 0; wi < wsLayout.length; wi++) {
    var ws = wsLayout[wi];

    // Desk (2x2 tiles) — themed sprite
    furniture.push({
      sprite: themeDeskSprite,
      x: ws.deskCol * TILE_SIZE,
      y: ws.deskRow * TILE_SIZE,
      zY: (ws.deskRow + 2) * TILE_SIZE
    });
    // Block desk tiles
    for (var dr = 0; dr < 2; dr++) {
      for (var dc = 0; dc < 2; dc++) {
        blockedTiles.add((ws.deskCol + dc) + ',' + (ws.deskRow + dr));
      }
    }

    // PC on desk — themed sprite (zY = desk bottom so PC renders ON TOP of desk)
    furniture.push({
      sprite: themePcSprite,
      x: ws.pcCol * TILE_SIZE,
      y: ws.pcRow * TILE_SIZE,
      zY: (ws.deskRow + 2) * TILE_SIZE + 1
    });

    // Chair — themed sprite
    furniture.push({
      sprite: themeChairSprite,
      x: ws.chairCol * TILE_SIZE,
      y: ws.chairRow * TILE_SIZE,
      zY: (ws.chairRow + 1) * TILE_SIZE
    });

    // Seat
    var seatId = 'seat-' + wi;
    seats[seatId] = {
      uid: seatId,
      seatCol: ws.chairCol,
      seatRow: ws.chairRow,
      facingDir: ws.facingDir,
      assigned: wi < agentes.length
    };
  }

  // Place decorations
  for (var di = 0; di < decLayout.length; di++) {
    var dec = decLayout[di];
    var sprite = null;
    var h = 1;
    if (dec.type === 'bookshelf') { sprite = BOOKSHELF_SPRITE; h = 2; }
    else if (dec.type === 'whiteboard') { sprite = WHITEBOARD_SPRITE; h = 1; }
    else if (dec.type === 'plant') { sprite = PLANT_SPRITE; h = 1; }
    else if (dec.type === 'cooler') { sprite = COOLER_SPRITE; h = 1; }
    else if (dec.type === 'lamp') { sprite = LAMP_SPRITE; h = 1; }
    // Theme-exclusive sprites
    else if (dec.type === 'trophy') { sprite = TROPHY_SPRITE; h = 1; }
    else if (dec.type === 'safe') { sprite = SAFE_SPRITE; h = 1; }
    else if (dec.type === 'globe') { sprite = GLOBE_SPRITE; h = 1; }
    else if (dec.type === 'candelabra') { sprite = CANDELABRA_SPRITE; h = 1; }
    else if (dec.type === 'skull') { sprite = SKULL_SPRITE; h = 1; }
    else if (dec.type === 'potion') { sprite = POTION_SPRITE; h = 1; }
    else if (dec.type === 'radio') { sprite = RADIO_SPRITE; h = 1; }
    else if (dec.type === 'sandbag') { sprite = SANDBAG_SPRITE; h = 1; }
    else if (dec.type === 'flag') { sprite = FLAG_SPRITE; h = 1; }
    if (!sprite) continue;

    furniture.push({
      sprite: sprite,
      x: dec.col * TILE_SIZE,
      y: dec.row * TILE_SIZE,
      zY: (dec.row + h) * TILE_SIZE
    });
    blockedTiles.add(dec.col + ',' + dec.row);
    if (h > 1) blockedTiles.add(dec.col + ',' + (dec.row + 1));
  }

  // Create characters for agents
  var characters = [];
  for (var ai = 0; ai < agentes.length && ai < wsLayout.length; ai++) {
    var ag = agentes[ai];
    var sId = 'seat-' + ai;
    var seat = seats[sId];
    var globalId = (roomIndex || 0) * 100 + ai;
    var ch = createCharacter(globalId, ai % AGENT_PALETTES.length, sId, seat);

    // Set initial state — all agents start in cycle (mix realista)
    var isImpl = ag.implementado !== false;
    if (!isImpl) {
      ch.isPlaceholder = true;
    }
    // Stagger: some start working, some start on break
    var startRoll = Math.random();
    if (startRoll < 0.65) {
      // Start working (60% TYPE, 40% READ)
      ch.cyclePhase = 'work';
      ch.cycleTimer = randomRange(5, WORK_CYCLE_MAX);
      ch.state = Math.random() < 0.6 ? CharState.TYPE : CharState.READ;
      ch.isActive = true;
    } else {
      // Start on a break
      ch.cyclePhase = 'break';
      ch.cycleTimer = randomRange(3, BREAK_CYCLE_MAX);
      var breakRoll = Math.random();
      if (breakRoll < 0.3) {
        ch.breakType = 'phone';
        ch.state = CharState.PHONE;
        ch.dir = Direction.DOWN;
      } else if (breakRoll < 0.5) {
        ch.breakType = 'sleep';
        ch.state = CharState.SLEEP;
      } else {
        ch.breakType = 'walk';
        ch.state = CharState.IDLE;
        ch.isActive = false;
        ch.wanderTimer = randomRange(1, 4);
        ch.wanderCount = 0;
        ch.wanderLimit = randomInt(2, 4);
      }
    }

    // Attach full agent data + canal info
    ag.agente_nome = ag.nome || ag.tipo || ('Agente ' + (ai + 1));
    ag.canal_id = canal.yt_channel_id || canal.canal_id || '';
    ag.planilha_url = canal.planilha_url || '';
    ch.agentData = ag;
    characters.push(ch);
  }

  // Block top and bottom rows from walking
  for (var bc = 0; bc < ROOM_COLS; bc++) {
    blockedTiles.add(bc + ',0');
    blockedTiles.add(bc + ',' + (ROOM_ROWS - 1));
  }

  var walkableTiles = getWalkableTiles(tileMap, blockedTiles);

  // Store decoration positions for coffee run pathfinding
  var decorationTiles = [];
  for (var dti = 0; dti < decLayout.length; dti++) {
    decorationTiles.push({ type: decLayout[dti].type, col: decLayout[dti].col, row: decLayout[dti].row });
  }

  // Set roomIdx on characters
  for (var chi = 0; chi < characters.length; chi++) {
    characters[chi]._roomIdx = roomIndex;
  }

  var roomObj = {
    canal: canal,
    tileMap: tileMap,
    furniture: furniture,
    seats: seats,
    characters: characters,
    blockedTiles: blockedTiles,
    walkableTiles: walkableTiles,
    decorationTiles: decorationTiles,
    floorColor: theme.floorColor,
    wallColor: theme.wallColor,
    floorSprite: theme.floorSprite || null,
    themeKey: themeKey,
    theme: theme,
    roomIndex: roomIndex
  };
  return roomObj;
}

// ============================================================
// 7. CHARACTER SYSTEM (port of characters.ts)
// ============================================================

function tileCenter(col, row) {
  return { x: col * TILE_SIZE + TILE_SIZE / 2, y: row * TILE_SIZE + TILE_SIZE / 2 };
}

function directionBetween(fromCol, fromRow, toCol, toRow) {
  var dc = toCol - fromCol;
  var dr = toRow - fromRow;
  if (dc > 0) return Direction.RIGHT;
  if (dc < 0) return Direction.LEFT;
  if (dr > 0) return Direction.DOWN;
  return Direction.UP;
}

function randomRange(min, max) {
  return min + Math.random() * (max - min);
}

function randomInt(min, max) {
  return min + Math.floor(Math.random() * (max - min + 1));
}

function createCharacter(id, palette, seatId, seat) {
  var col = seat ? seat.seatCol : 1;
  var row = seat ? seat.seatRow : 1;
  var center = tileCenter(col, row);
  // Stagger initial cycle timers so agents don't sync
  var initialWork = randomRange(3, WORK_CYCLE_MAX);
  return {
    id: id,
    state: CharState.TYPE,
    dir: seat ? seat.facingDir : Direction.DOWN,
    x: center.x,
    y: center.y,
    tileCol: col,
    tileRow: row,
    path: [],
    moveProgress: 0,
    palette: palette,
    frame: 0,
    frameTimer: 0,
    wanderTimer: 0,
    wanderCount: 0,
    wanderLimit: randomInt(WANDER_MOVES_MIN, WANDER_MOVES_MAX),
    isActive: true,
    seatId: seatId,
    seatTimer: 0,
    isPlaceholder: false,
    agentData: null,
    // Office Life Engine
    cyclePhase: 'work',
    cycleTimer: initialWork,
    breakType: null,
    _nextState: null,
    _coffeeTarget: null,
    _chatPartner: null,
    _sparkTimer: 0,
    _trailTimer: 0,
    _steamTimer: 0,
    _roomIdx: 0
  };
}

function pickBreakType(room, ch) {
  // Check if room has bookshelves or coolers/plants
  var hasBookshelf = false, hasCooler = false;
  var decs = room.decorationTiles || [];
  for (var i = 0; i < decs.length; i++) {
    if (decs[i].type === 'bookshelf') hasBookshelf = true;
    if (decs[i].type === 'cooler' || decs[i].type === 'plant') hasCooler = true;
  }
  // 20% bookshelf, 20% coffee, 20% phone, 15% sleep, 15% walk, 10% chat
  var r = Math.random();
  if (r < 0.20 && hasBookshelf) return 'bookshelf';
  if (r < 0.40 && hasCooler) return 'coffee';
  if (r < 0.60) return 'phone';
  if (r < 0.75) return 'sleep';
  if (r < 0.90) return 'walk';
  return 'chat';
}

function startWork(ch, seats, tileMap, blockedTiles) {
  ch.cyclePhase = 'work';
  ch.cycleTimer = randomRange(WORK_CYCLE_MIN, WORK_CYCLE_MAX);
  var workType = Math.random() < 0.6 ? CharState.TYPE : CharState.READ;
  // Walk to seat if not there
  if (ch.seatId) {
    var seat = seats[ch.seatId];
    if (seat && (ch.tileCol !== seat.seatCol || ch.tileRow !== seat.seatRow)) {
      var path = findPath(ch.tileCol, ch.tileRow, seat.seatCol, seat.seatRow, tileMap, blockedTiles);
      if (path.length > 0) {
        ch.path = path;
        ch.moveProgress = 0;
        ch.state = CharState.WALK;
        ch._nextState = workType;
        ch.frame = 0;
        ch.frameTimer = 0;
        return;
      }
    }
    ch.state = workType;
    ch.dir = seat ? seat.facingDir : ch.dir;
  } else {
    ch.state = workType;
  }
  ch.frame = 0;
  ch.frameTimer = 0;
}

function startBreak(ch, room, seats, tileMap, blockedTiles) {
  ch.cyclePhase = 'break';
  ch.breakType = pickBreakType(room, ch);
  ch.cycleTimer = randomRange(BREAK_CYCLE_MIN, BREAK_CYCLE_MAX);
  ch.frame = 0;
  ch.frameTimer = 0;

  switch (ch.breakType) {
    case 'bookshelf':
      // Find nearest bookshelf, walk there and read
      var bDecTiles = room.decorationTiles || [];
      var bBest = null, bBestDist = 9999;
      for (var bd = 0; bd < bDecTiles.length; bd++) {
        if (bDecTiles[bd].type === 'bookshelf') {
          var bDist = Math.abs(bDecTiles[bd].col - ch.tileCol) + Math.abs(bDecTiles[bd].row - ch.tileRow);
          if (bDist < bBestDist) { bBestDist = bDist; bBest = bDecTiles[bd]; }
        }
      }
      if (bBest) {
        var bAdjRow = Math.min(bBest.row + 2, ROOM_ROWS - 2);
        var bpath = findPath(ch.tileCol, ch.tileRow, bBest.col, bAdjRow, tileMap, blockedTiles);
        if (bpath.length > 0) {
          ch.path = bpath;
          ch.moveProgress = 0;
          ch.state = CharState.WALK;
          ch._nextState = CharState.READ;
          ch._coffeeTarget = bBest;
          ch.cycleTimer = randomRange(6, 12);
          return;
        }
      }
      // Fallback to walk
      ch.breakType = 'walk';
      ch.state = CharState.IDLE;
      ch.wanderTimer = randomRange(1, 3);
      ch.wanderCount = 0;
      ch.wanderLimit = randomInt(2, 4);
      break;

    case 'coffee':
      // Find nearest cooler or plant decoration
      var decTiles = room.decorationTiles || [];
      var best = null, bestDist = 9999;
      for (var d = 0; d < decTiles.length; d++) {
        var dt2 = decTiles[d];
        if (dt2.type === 'cooler' || dt2.type === 'plant') {
          var dist = Math.abs(dt2.col - ch.tileCol) + Math.abs(dt2.row - ch.tileRow);
          if (dist < bestDist) { bestDist = dist; best = dt2; }
        }
      }
      if (best) {
        // Walk to tile adjacent to decoration
        var adjCol = best.col;
        var adjRow = Math.min(best.row + 1, ROOM_ROWS - 2);
        var cpath = findPath(ch.tileCol, ch.tileRow, adjCol, adjRow, tileMap, blockedTiles);
        if (cpath.length > 0) {
          ch.path = cpath;
          ch.moveProgress = 0;
          ch.state = CharState.WALK;
          ch._nextState = CharState.COFFEE;
          ch._coffeeTarget = best;
          ch.cycleTimer = COFFEE_WAIT_TIME + cpath.length * 0.3;
          return;
        }
      }
      // Fallback to walk
      ch.breakType = 'walk';
      ch.state = CharState.IDLE;
      ch.wanderTimer = randomRange(1, 3);
      ch.wanderCount = 0;
      ch.wanderLimit = randomInt(2, 4);
      break;

    case 'sleep':
      // Go to seat if not there, then sleep
      if (ch.seatId) {
        var sSeat = seats[ch.seatId];
        if (sSeat && (ch.tileCol !== sSeat.seatCol || ch.tileRow !== sSeat.seatRow)) {
          var spath = findPath(ch.tileCol, ch.tileRow, sSeat.seatCol, sSeat.seatRow, tileMap, blockedTiles);
          if (spath.length > 0) {
            ch.path = spath;
            ch.moveProgress = 0;
            ch.state = CharState.WALK;
            ch._nextState = CharState.SLEEP;
            return;
          }
        }
        ch.dir = sSeat ? sSeat.facingDir : ch.dir;
      }
      ch.state = CharState.SLEEP;
      ch.cycleTimer = randomRange(SLEEP_TIME_MIN, SLEEP_TIME_MAX);
      break;

    case 'phone':
      ch.state = CharState.PHONE;
      ch.dir = Direction.DOWN;
      ch.cycleTimer = randomRange(PHONE_TIME_MIN, PHONE_TIME_MAX);
      break;

    case 'walk':
      ch.state = CharState.IDLE;
      ch.wanderTimer = randomRange(1, 3);
      ch.wanderCount = 0;
      ch.wanderLimit = randomInt(2, 4);
      break;

    case 'chat':
      // Find another agent in break or idle in same room
      var partner = null;
      if (room && room.characters) {
        for (var ci = 0; ci < room.characters.length; ci++) {
          var other = room.characters[ci];
          if (other.id !== ch.id && other.state !== CharState.WALK && other.cyclePhase === 'break' && other.state !== CharState.CHAT) {
            partner = other;
            break;
          }
        }
      }
      if (partner) {
        // Both walk to midpoint
        var midCol = Math.round((ch.tileCol + partner.tileCol) / 2);
        var midRow = Math.round((ch.tileRow + partner.tileRow) / 2);
        midCol = Math.max(1, Math.min(midCol, ROOM_COLS - 2));
        midRow = Math.max(1, Math.min(midRow, ROOM_ROWS - 2));
        var chatPath1 = findPath(ch.tileCol, ch.tileRow, midCol, midRow, tileMap, blockedTiles);
        var chatPath2 = findPath(partner.tileCol, partner.tileRow, midCol, Math.min(midRow + 1, ROOM_ROWS - 2), tileMap, blockedTiles);
        if (chatPath1.length > 0) {
          ch.path = chatPath1;
          ch.moveProgress = 0;
          ch.state = CharState.WALK;
          ch._nextState = CharState.CHAT;
          ch._chatPartner = partner.id;
          ch.cycleTimer = randomRange(CHAT_TIME_MIN, CHAT_TIME_MAX);
        }
        if (chatPath2.length > 0) {
          partner.path = chatPath2;
          partner.moveProgress = 0;
          partner.state = CharState.WALK;
          partner._nextState = CharState.CHAT;
          partner._chatPartner = ch.id;
          partner.cycleTimer = randomRange(CHAT_TIME_MIN, CHAT_TIME_MAX);
          partner.cyclePhase = 'break';
          partner.breakType = 'chat';
        } else {
          // Fallback
          ch.breakType = 'walk';
          ch.state = CharState.IDLE;
          ch.wanderTimer = 2;
          ch.wanderCount = 0;
          ch.wanderLimit = 2;
        }
      } else {
        // No partner, fallback to phone
        ch.breakType = 'phone';
        ch.state = CharState.PHONE;
        ch.dir = Direction.DOWN;
        ch.cycleTimer = randomRange(PHONE_TIME_MIN, PHONE_TIME_MAX);
      }
      break;
  }
}

function updateCharacter(ch, dt, walkableTiles, seats, tileMap, blockedTiles, room) {
  ch.frameTimer += dt;

  // ---- Office Life Cycle Engine ----
  ch.cycleTimer -= dt;
  if (ch.cycleTimer <= 0 && ch.state !== CharState.WALK) {
    if (ch.cyclePhase === 'work') {
      // Work done -> take a break
      emitBurst(ch.x, ch.y, ch._roomIdx, false);
      startBreak(ch, room, seats, tileMap, blockedTiles);
      return;
    } else {
      // Break done -> back to work
      startWork(ch, seats, tileMap, blockedTiles);
      return;
    }
  }

  // ---- State-specific logic ----
  if (ch.state === CharState.TYPE) {
    if (ch.frameTimer >= TYPE_FRAME_DUR) {
      ch.frameTimer -= TYPE_FRAME_DUR;
      ch.frame = (ch.frame + 1) % 2;
    }
    // Typing sparks effect
    ch._sparkTimer -= dt;
    if (ch._sparkTimer <= 0) {
      ch._sparkTimer = 0.3 + Math.random() * 0.2;
      // Emit spark from PC position (approximate)
      if (ch.seatId && seats[ch.seatId]) {
        var sparkSeat = seats[ch.seatId];
        emitTypingSpark(ch.x, ch.y - 8, ch._roomIdx);
      }
    }
  }
  else if (ch.state === CharState.READ) {
    if (ch.frameTimer >= READ_FRAME_DUR) {
      ch.frameTimer -= READ_FRAME_DUR;
      ch.frame = (ch.frame + 1) % 2;
    }
    // Face bookshelf if reading near one
    if (ch._coffeeTarget && ch._coffeeTarget.type === 'bookshelf') {
      ch.dir = directionBetween(ch.tileCol, ch.tileRow, ch._coffeeTarget.col, ch._coffeeTarget.row);
    }
  }
  else if (ch.state === CharState.SLEEP) {
    // Static, no animation frame changes
    ch.frame = 0;
  }
  else if (ch.state === CharState.COFFEE) {
    ch.frame = 0;
    // Look toward decoration
    if (ch._coffeeTarget) {
      ch.dir = directionBetween(ch.tileCol, ch.tileRow, ch._coffeeTarget.col, ch._coffeeTarget.row);
    }
    // Emit steam
    ch._steamTimer -= dt;
    if (ch._steamTimer <= 0) {
      ch._steamTimer = 0.4;
      emitSteam(ch.x, ch.y - 4, ch._roomIdx);
    }
  }
  else if (ch.state === CharState.PHONE) {
    ch.frame = 0;
  }
  else if (ch.state === CharState.CHAT) {
    ch.frame = 0;
    // Face partner if nearby
    if (ch._chatPartner && room && room.characters) {
      for (var pi = 0; pi < room.characters.length; pi++) {
        if (room.characters[pi].id === ch._chatPartner) {
          var p = room.characters[pi];
          ch.dir = directionBetween(ch.tileCol, ch.tileRow, p.tileCol, p.tileRow);
          break;
        }
      }
    }
  }
  else if (ch.state === CharState.IDLE) {
    ch.frame = 0;
    // Wander logic (used during break:walk)
    ch.wanderTimer -= dt;
    if (ch.wanderTimer <= 0) {
      if (ch.wanderCount >= ch.wanderLimit) {
        // Done wandering, cycle engine will handle transition
        ch.cycleTimer = 0;
        return;
      }
      if (walkableTiles.length > 0) {
        var target = walkableTiles[Math.floor(Math.random() * walkableTiles.length)];
        var wpath = findPath(ch.tileCol, ch.tileRow, target.col, target.row, tileMap, blockedTiles);
        if (wpath.length > 0) {
          ch.path = wpath;
          ch.moveProgress = 0;
          ch.state = CharState.WALK;
          ch._nextState = CharState.IDLE;
          ch.frame = 0;
          ch.frameTimer = 0;
          ch.wanderCount++;
        }
      }
      ch.wanderTimer = randomRange(WANDER_PAUSE_MIN, WANDER_PAUSE_MAX);
    }
  }
  else if (ch.state === CharState.WALK) {
    // Walk animation
    if (ch.frameTimer >= WALK_FRAME_DUR) {
      ch.frameTimer -= WALK_FRAME_DUR;
      ch.frame = (ch.frame + 1) % 4;
    }
    if (ch.path.length === 0) {
      // Path complete
      var center = tileCenter(ch.tileCol, ch.tileRow);
      ch.x = center.x;
      ch.y = center.y;

      // Transition to _nextState if set
      if (ch._nextState) {
        var ns = ch._nextState;
        ch._nextState = null;
        if (ns === CharState.TYPE || ns === CharState.READ) {
          ch.state = ns;
          if (ch.seatId && seats[ch.seatId]) ch.dir = seats[ch.seatId].facingDir;
        } else if (ns === CharState.COFFEE) {
          ch.state = CharState.COFFEE;
        } else if (ns === CharState.SLEEP) {
          ch.state = CharState.SLEEP;
          if (ch.seatId && seats[ch.seatId]) ch.dir = seats[ch.seatId].facingDir;
        } else if (ns === CharState.CHAT) {
          ch.state = CharState.CHAT;
        } else {
          ch.state = ns;
        }
        ch.frame = 0;
        ch.frameTimer = 0;
        return;
      }

      // Default: go idle
      ch.state = CharState.IDLE;
      ch.wanderTimer = randomRange(WANDER_PAUSE_MIN, WANDER_PAUSE_MAX);
      ch.frame = 0;
      ch.frameTimer = 0;
      return;
    }

    // Move toward next tile
    var nextTile = ch.path[0];
    ch.dir = directionBetween(ch.tileCol, ch.tileRow, nextTile.col, nextTile.row);
    ch.moveProgress += (WALK_SPEED / TILE_SIZE) * dt;

    var fromCenter = tileCenter(ch.tileCol, ch.tileRow);
    var toCenter = tileCenter(nextTile.col, nextTile.row);
    var t = Math.min(ch.moveProgress, 1);
    ch.x = fromCenter.x + (toCenter.x - fromCenter.x) * t;
    ch.y = fromCenter.y + (toCenter.y - fromCenter.y) * t;

    if (ch.moveProgress >= 1) {
      ch.tileCol = nextTile.col;
      ch.tileRow = nextTile.row;
      ch.x = toCenter.x;
      ch.y = toCenter.y;
      ch.path.shift();
      ch.moveProgress = 0;
    }
  }
}

/** Get the correct sprite frame for current state/direction/frame */
function getCharacterSprite(ch, sprites) {
  if (ch.state === CharState.TYPE) {
    return sprites.typing[ch.dir][ch.frame % 2];
  }
  if (ch.state === CharState.READ) {
    return sprites.reading[ch.dir][ch.frame % 2];
  }
  if (ch.state === CharState.WALK) {
    return sprites.walk[ch.dir][ch.frame % 4];
  }
  if (ch.state === CharState.SLEEP) {
    // Use typing frame 0 (static sitting pose)
    return sprites.typing[ch.dir][0];
  }
  // IDLE, COFFEE, PHONE, CHAT — standing frame
  return sprites.walk[ch.dir][1];
}

// ============================================================
// 7B. PARTICLE SYSTEM + VISUAL EFFECTS
// ============================================================

function addParticle(x, y, vx, vy, color, life, size, roomIdx, gravity) {
  if (particles.length >= MAX_PARTICLES) return;
  particles.push({ x: x, y: y, vx: vx, vy: vy, color: color, life: life, maxLife: life, size: size || 2, roomIdx: roomIdx, gravity: gravity !== undefined ? gravity : 30 });
}

function updateParticles(dt) {
  for (var i = particles.length - 1; i >= 0; i--) {
    var p = particles[i];
    p.x += p.vx * dt;
    p.y += p.vy * dt;
    p.vy += p.gravity * dt;
    p.life -= dt;
    if (p.life <= 0) particles.splice(i, 1);
  }
}

function renderParticlesForRoom(ctx, roomX, roomY, zoom, roomIdx) {
  for (var i = 0; i < particles.length; i++) {
    var p = particles[i];
    if (p.roomIdx !== roomIdx) continue;
    var alpha = Math.max(0, p.life / p.maxLife);
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.fillStyle = p.color;
    var px = Math.round(roomX + p.x * zoom);
    var py = Math.round(roomY + p.y * zoom);
    var ps = Math.max(1, Math.round(p.size * zoom));
    ctx.fillRect(px, py, ps, ps);
    ctx.restore();
  }
}

// Aura glow around character
function drawAura(ctx, screenX, screenY, color, time, zoom, pulse) {
  var radius = 18 * zoom;
  var alpha;
  if (pulse) {
    alpha = 0.10 + 0.15 * Math.sin(time * 3);
  } else {
    alpha = 0.12;
  }
  if (alpha <= 0) return;
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.arc(screenX, screenY, radius, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}

// Zzz floating above sleeping character
function drawZzz(ctx, x, y, time, zoom) {
  ctx.save();
  ctx.font = 'bold ' + Math.round(8 * zoom) + 'px monospace';
  var zees = ['z', 'Z', 'Z'];
  var sizes = [7, 9, 11];
  for (var i = 0; i < 3; i++) {
    var phase = i * 2.1;
    var yOff = -8 - i * 8 + Math.sin(time * 1.5 + phase) * 3;
    var xOff = 4 + i * 5 + Math.sin(time * 0.8 + phase) * 2;
    var alpha = 0.4 + 0.4 * Math.sin(time * 2 + phase);
    ctx.globalAlpha = alpha;
    ctx.font = 'bold ' + Math.round(sizes[i] * zoom) + 'px monospace';
    ctx.fillStyle = '#fff';
    ctx.textAlign = 'center';
    ctx.fillText(zees[i], Math.round(x + xOff * zoom), Math.round(y + yOff * zoom));
  }
  ctx.restore();
}

// Phone glow in front of character
function drawPhoneGlow(ctx, x, y, time, zoom) {
  ctx.save();
  var alpha = 0.5 + 0.5 * Math.sin(time * 2.5);
  ctx.globalAlpha = alpha;
  ctx.fillStyle = '#a5d8ff';
  var pw = Math.round(3 * zoom);
  var ph = Math.round(5 * zoom);
  ctx.fillRect(Math.round(x - pw / 2), Math.round(y + 2 * zoom), pw, ph);
  // Small white highlight
  ctx.fillStyle = '#fff';
  ctx.globalAlpha = alpha * 0.6;
  ctx.fillRect(Math.round(x - pw / 2 + zoom), Math.round(y + 3 * zoom), Math.max(1, Math.round(zoom)), Math.max(1, Math.round(2 * zoom)));
  ctx.restore();
}

// Speech bubble with text
function drawSpeechBubble(ctx, x, y, text, time, zoom, show) {
  if (!show) return;
  ctx.save();
  var alpha = 0.85;
  ctx.globalAlpha = alpha;
  var fontSize = Math.round(8 * zoom);
  ctx.font = 'bold ' + fontSize + 'px monospace';
  var tw = ctx.measureText(text).width;
  var bw = tw + 6 * zoom;
  var bh = fontSize + 4 * zoom;
  var bx = Math.round(x - bw / 2);
  var by = Math.round(y - 12 * zoom);
  // Bubble background
  ctx.fillStyle = '#fff';
  ctx.fillRect(bx, by, Math.round(bw), Math.round(bh));
  // Triangle
  ctx.beginPath();
  ctx.moveTo(x - 2 * zoom, by + bh);
  ctx.lineTo(x + 2 * zoom, by + bh);
  ctx.lineTo(x, by + bh + 3 * zoom);
  ctx.closePath();
  ctx.fill();
  // Text
  ctx.fillStyle = '#333';
  ctx.textAlign = 'center';
  ctx.fillText(text, Math.round(x), Math.round(by + fontSize));
  ctx.restore();
}

// Think bubble with "?" for placeholders
function drawThinkBubble(ctx, x, y, time, zoom) {
  var alpha = 0.5 + 0.3 * Math.sin(time * 2);
  ctx.save();
  ctx.globalAlpha = alpha;
  var fontSize = Math.round(10 * zoom);
  ctx.font = 'bold ' + fontSize + 'px monospace';
  ctx.fillStyle = '#fbbf24';
  ctx.textAlign = 'center';
  var yOff = Math.sin(time * 1.5) * 2;
  ctx.fillText('?', Math.round(x), Math.round(y - 6 * zoom + yOff * zoom));
  ctx.restore();
}

// Steam particles for coffee
function emitSteam(x, y, roomIdx) {
  for (var i = 0; i < 2; i++) {
    var sx = x + (Math.random() - 0.5) * 4;
    addParticle(sx, y - 4, (Math.random() - 0.5) * 6, -12 - Math.random() * 8, '#ffffff', 0.8 + Math.random() * 0.4, 1.5, roomIdx, -2);
  }
}

// Typing sparks
function emitTypingSpark(x, y, roomIdx) {
  addParticle(x + (Math.random() - 0.5) * 8, y, (Math.random() - 0.5) * 15, -25 - Math.random() * 15, '#FFD700', 0.25 + Math.random() * 0.15, 1, roomIdx, 10);
}

// Walk trail
function emitTrail(x, y, color, roomIdx) {
  addParticle(x, y + 14, (Math.random() - 0.5) * 3, -4 - Math.random() * 3, color, 0.35, 1.5, roomIdx, 0);
}

// Completion burst
function emitBurst(x, y, roomIdx, big) {
  var count = big ? 15 : 8;
  var colors = ['#FFD700', '#FFA500', '#FFEC8B', '#fff'];
  for (var i = 0; i < count; i++) {
    var angle = (i / count) * Math.PI * 2;
    var speed = 30 + Math.random() * 25;
    var c = colors[Math.floor(Math.random() * colors.length)];
    addParticle(x, y + 8, Math.cos(angle) * speed, Math.sin(angle) * speed - 20, c, 0.8 + Math.random() * 0.4, big ? 3 : 2, roomIdx, 40);
  }
}

// ============================================================
// 8. RENDERER (port of renderer.ts)
// ============================================================

function renderTileGrid(ctx, tileMap, offsetX, offsetY, zoom, floorColor, wallColor, themeFloorSprite) {
  var s = TILE_SIZE * zoom;
  var tmRows = tileMap.length;
  var tmCols = tmRows > 0 ? tileMap[0].length : 0;
  var useWallSprites = wallSprites !== null;

  // Pre-compute wall hex (fallback if no wall sprites)
  var wallHex = wallColorToHex(wallColor);

  // Pre-compute colorized floor sprite (theme-specific or default)
  var floorSprite = getColorizedFloorSprite(floorColor, themeFloorSprite);
  var floorCached = getCachedSprite(floorSprite, zoom);

  for (var r = 0; r < tmRows; r++) {
    for (var c = 0; c < tmCols; c++) {
      var tile = tileMap[r][c];
      if (tile === TILE_WALL) {
        if (!useWallSprites) {
          // Fallback: solid fill
          ctx.fillStyle = wallHex;
          ctx.fillRect(offsetX + c * s, offsetY + r * s, s, s);
        }
        // When wallSprites loaded, walls are rendered via z-sort in renderScene
      } else {
        // Floor tile with colorization
        ctx.drawImage(floorCached, offsetX + c * s, offsetY + r * s);
      }
    }
  }
}

function renderScene(ctx, furniture, characters, offsetX, offsetY, zoom, spriteCache, tileMap, wallColor, selectedCharId) {
  var drawables = [];

  // Wall instances (z-sorted with furniture when wallSprites loaded)
  if (wallSprites && tileMap && wallColor) {
    var wallInstances = getWallInstances(tileMap, wallColor);
    for (var wi = 0; wi < wallInstances.length; wi++) {
      var w = wallInstances[wi];
      var wCached = getCachedSprite(w.sprite, zoom);
      var wx = offsetX + w.x * zoom;
      var wy = offsetY + w.y * zoom;
      (function(cachedRef, wxRef, wyRef) {
        drawables.push({
          zY: w.zY,
          draw: function(c) { c.drawImage(cachedRef, wxRef, wyRef); }
        });
      })(wCached, wx, wy);
    }
  }

  // Furniture
  for (var fi = 0; fi < furniture.length; fi++) {
    var f = furniture[fi];
    var cached = getCachedSprite(f.sprite, zoom);
    var fx = offsetX + f.x * zoom;
    var fy = offsetY + f.y * zoom;
    (function(cachedRef, fxRef, fyRef) {
      drawables.push({
        zY: f.zY,
        draw: function(c) { c.drawImage(cachedRef, fxRef, fyRef); }
      });
    })(cached, fx, fy);
  }

  // Characters (with visual effects)
  for (var ci = 0; ci < characters.length; ci++) {
    var ch = characters[ci];
    var sprites = spriteCache[ch.palette];
    if (!sprites) sprites = spriteCache[0];
    var spriteData = getCharacterSprite(ch, sprites);
    var charCached = getCachedSprite(spriteData, zoom);
    // Sitting offset for TYPE, READ, SLEEP
    var isSitting = ch.state === CharState.TYPE || ch.state === CharState.READ || ch.state === CharState.SLEEP;
    var sittingOffset = isSitting ? SIT_OFFSET : 0;
    var drawX = Math.round(offsetX + ch.x * zoom - charCached.width / 2);
    var drawY = Math.round(offsetX + (ch.y + sittingOffset) * zoom - charCached.height);
    // Fix: use offsetY not offsetX for Y calculation
    drawY = Math.round(offsetY + (ch.y + sittingOffset) * zoom - charCached.height);
    var charZY = ch.y + TILE_SIZE / 2 + Z_SORT_OFFSET;

    // Screen center of character (for effects)
    var charCenterX = offsetX + ch.x * zoom;
    var charTopY = drawY;

    // Selected agent outline
    var isSelected = selectedCharId !== null && selectedCharId !== undefined && ch.id === selectedCharId;
    if (isSelected) {
      var outlineData = getOutlineSprite(spriteData);
      var outlineCached = getCachedSprite(outlineData, zoom);
      var olDrawX = drawX - zoom;
      var olDrawY = drawY - zoom;
      (function(oCached, oDx, oDy) {
        drawables.push({
          zY: charZY - 0.001,
          draw: function(c) {
            c.save();
            c.globalAlpha = 0.8;
            c.drawImage(oCached, oDx, oDy);
            c.restore();
          }
        });
      })(outlineCached, olDrawX, olDrawY);
    }

    // --- CHARACTER SPRITE ---
    (function(cachedRef, dxRef, dyRef) {
      drawables.push({
        zY: charZY,
        draw: function(c) {
          c.drawImage(cachedRef, dxRef, dyRef);
        }
      });
    })(charCached, drawX, drawY);

    // --- EFFECTS ABOVE CHARACTER ---
    (function(chRef, cx, topY) {
      drawables.push({
        zY: charZY + 0.001,
        draw: function(c) {
          // Zzz for sleeping
          if (chRef.state === CharState.SLEEP) {
            drawZzz(c, cx, topY, gameTime + chRef.id * 0.5, zoom);
          }
          // Phone glow
          if (chRef.state === CharState.PHONE) {
            drawPhoneGlow(c, cx, topY + 16 * zoom, gameTime, zoom);
          }
          // Chat speech bubble
          if (chRef.state === CharState.CHAT) {
            var showBubble = Math.sin(gameTime * 1.5 + chRef.id) > 0;
            drawSpeechBubble(c, cx, topY, '...', gameTime, zoom, showBubble);
          }
          // (placeholder effects removed)
        }
      });
    })(ch, charCenterX, charTopY);
  }

  // Z-sort
  drawables.sort(function(a, b) { return a.zY - b.zY; });

  for (var di = 0; di < drawables.length; di++) {
    drawables[di].draw(ctx);
  }
}

// ============================================================
// 9. GAME LOOP (port of gameLoop.ts)
// ============================================================

function startGameLoop(canvas, callbacks) {
  var ctx = canvas.getContext('2d');
  ctx.imageSmoothingEnabled = false;
  var lastTime = 0;
  var rafId = 0;

  function frame(time) {
    var dt = lastTime === 0 ? 0 : Math.min((time - lastTime) / 1000, MAX_DT);
    lastTime = time;
    callbacks.update(dt);
    ctx.imageSmoothingEnabled = false;
    callbacks.render(ctx);
    rafId = requestAnimationFrame(frame);
  }
  rafId = requestAnimationFrame(frame);

  return function() { cancelAnimationFrame(rafId); };
}

// ============================================================
// 10. MAIN CONTROLLER
// ============================================================

var mcData = null;       // API response
var allRooms = [];       // built rooms
var visibleRooms = [];   // filtered by tab
var activeTab = 'all';
var zoom = 2;  // auto-calculated in resizeCanvas()
var panX = 0, panY = 0;  // kept for handleClick compatibility but always 0
var spritesByPalette = {}; // palette index -> CharacterSprites
var selectedAgent = null;
var stopLoop = null;

// Pre-generate sprite sets for all palettes
function initSpriteCache() {
  for (var p = 0; p < AGENT_PALETTES.length; p++) {
    spritesByPalette[p] = getCharacterSprites(p);
  }
}

function loadMCData(isRefresh) {
  return fetch('/api/mission-control/status')
    .then(function(r) { return r.json(); })
    .then(function(data) {
      mcData = data;
      if (isRefresh && allRooms.length > 0) {
        // Only update stats, do NOT rebuild rooms (preserves character positions)
        refreshRoomStats(data);
      } else {
        buildAllRooms();
        filterRooms(activeTab);
      }
      updateStats();
    })
    .catch(function(err) {
      console.error('[MC] Error loading data:', err);
    });
}

function refreshRoomStats(data) {
  // Update canal stats in existing rooms without resetting characters
  if (!data || !data.setores) return;
  var statsMap = {};
  for (var si = 0; si < data.setores.length; si++) {
    var salas = data.setores[si].salas || [];
    for (var i = 0; i < salas.length; i++) {
      var s = salas[i];
      if (s.canal_id) statsMap[s.canal_id] = s;
    }
  }
  for (var ri = 0; ri < allRooms.length; ri++) {
    var room = allRooms[ri];
    var cid = room.canal && room.canal.canal_id;
    if (cid && statsMap[cid]) {
      var fresh = statsMap[cid];
      room.canal.inscritos = fresh.inscritos || 0;
      room.canal.inscritos_diff = fresh.inscritos_diff || 0;
      room.canal.views_7d = fresh.views_7d || 0;
      room.canal.videos_30d = fresh.videos_30d || 0;
      room.canal.views_30d = fresh.views_30d || 0;
      room.canal.avg_ctr = fresh.avg_ctr || null;
      room.canal.avg_retention = fresh.avg_retention || null;
    }
  }
}

function buildAllRooms() {
  allRooms = [];
  if (!mcData || !mcData.setores) return;

  // API returns: { setores: [ { tema, salas: [...] }, ... ] }
  var setores = mcData.setores;
  var roomIdx = 0;
  for (var si = 0; si < setores.length; si++) {
    var setor = setores[si];
    var salas = setor.salas || [];
    for (var i = 0; i < salas.length; i++) {
      var sala = salas[i];
      sala.setor_tema = setor.tema;
      sala.setor_nome = setor.nome;
      sala.setor_accent = setor.accent;
      var themeKey = getThemeKey(setor.tema);
      var room = buildRoom(sala, themeKey, roomIdx);
      roomIdx++;
      allRooms.push(room);
    }
  }
}

function filterRooms(tab) {
  activeTab = tab;
  if (tab === 'all') {
    visibleRooms = allRooms.slice();
  } else {
    visibleRooms = allRooms.filter(function(room) {
      return room.themeKey === tab;
    });
  }
  // Sort by inscritos (most subscribers first)
  visibleRooms.sort(function(a, b) {
    return (b.canal.inscritos || 0) - (a.canal.inscritos || 0);
  });
  resizeCanvas();  // adjust canvas height for number of rooms
}

function updateStats() {
  var s0 = document.getElementById('s0');
  var s1 = document.getElementById('s1');
  var s2 = document.getElementById('s2');
  if (mcData && mcData.stats) {
    if (s0) s0.textContent = mcData.stats.total_salas || allRooms.length;
    if (s1) s1.textContent = mcData.stats.total_agentes || 0;
    if (s2) s2.textContent = mcData.stats.agentes_active || 0;
  } else {
    if (s0) s0.textContent = allRooms.length;
    if (s1) s1.textContent = '0';
    if (s2) s2.textContent = '0';
  }
}

// ============================================================
// 11. RENDER FRAME (multi-room layout)
// ============================================================

function getRoomLayout(rooms, zoom) {
  var roomW = ROOM_COLS * TILE_SIZE;
  var roomH = ROOM_ROWS * TILE_SIZE;
  var gap = ROOM_GAP;
  var gapV = ROOM_GAP_V;
  var cols = Math.min(rooms.length, ROOMS_PER_ROW);
  var rows = Math.ceil(rooms.length / ROOMS_PER_ROW);
  var totalW = cols * roomW + (cols - 1) * gap;
  var totalH = rows * roomH + (rows - 1) * gapV;
  return { roomW: roomW, roomH: roomH, gap: gap, gapV: gapV, cols: cols, rows: rows, totalW: totalW, totalH: totalH };
}

function formatNumber(n) {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
  return '' + n;
}

function renderAllRooms(ctx, canvasW, canvasH) {
  var dpr = window.devicePixelRatio || 1;
  ctx.clearRect(0, 0, canvasW, canvasH);
  ctx.save();
  ctx.scale(dpr, dpr);

  // Use CSS pixel dimensions for all layout
  var cssW = canvasW / dpr;
  var cssH = canvasH / dpr;

  if (visibleRooms.length === 0) {
    ctx.fillStyle = '#888';
    ctx.font = '14px monospace';
    ctx.textAlign = 'center';
    ctx.fillText('Nenhuma sala encontrada', cssW / 2, cssH / 2);
    ctx.restore();
    return;
  }

  var layout = getRoomLayout(visibleRooms, zoom);
  var startX = Math.floor((cssW - layout.totalW * zoom) / 2);
  var startY = 24;

  // Font sizes scale with zoom but clamped (larger minimums for readability)
  var nameFont = Math.max(13, Math.min(18, Math.round(9 * zoom)));
  var statsFont = Math.max(11, Math.min(15, Math.round(7 * zoom)));
  var langFont = Math.max(10, Math.min(13, Math.round(6 * zoom)));
  var barH = Math.max(22, Math.min(32, Math.round(14 * zoom)));

  for (var i = 0; i < visibleRooms.length; i++) {
    var room = visibleRooms[i];
    var gridCol = i % ROOMS_PER_ROW;
    var gridRow = Math.floor(i / ROOMS_PER_ROW);

    var roomX = startX + gridCol * (layout.roomW + layout.gap) * zoom;
    var rowStep = layout.roomH * zoom + layout.gapV * zoom + barH * 2;
    var roomY = startY + gridRow * rowStep;
    var roomW = layout.roomW * zoom;
    var roomH = layout.roomH * zoom;

    var accentColor = room.theme.accent || '#888';

    // -- NAMEPLATE: ABOVE the room, separated --
    // Enable smoothing for crisp text rendering
    ctx.imageSmoothingEnabled = true;
    var npY = roomY - barH;
    // Accent line on top
    ctx.fillStyle = accentColor;
    ctx.fillRect(Math.round(roomX), Math.round(npY), Math.round(roomW), 2);
    // Name background
    ctx.fillStyle = 'rgba(13,13,36,0.9)';
    ctx.fillRect(Math.round(roomX), Math.round(npY + 2), Math.round(roomW), barH - 2);

    // Channel name
    var canalName = room.canal.nome || room.canal.canal_nome || 'Canal';
    ctx.font = 'bold ' + nameFont + 'px "Segoe UI", system-ui, sans-serif';
    while (canalName.length > 5 && ctx.measureText(canalName).width > roomW - 50) {
      canalName = canalName.substring(0, canalName.length - 3) + '..';
    }
    ctx.fillStyle = '#e0e0e0';
    ctx.textAlign = 'left';
    ctx.fillText(canalName, Math.round(roomX + 6), Math.round(npY + barH / 2 + nameFont * 0.35 + 1));

    // Language badge
    var lang = room.canal.lingua || '??';
    ctx.font = 'bold ' + langFont + 'px "Segoe UI", system-ui, sans-serif';
    var langW = ctx.measureText(lang).width + 8;
    ctx.fillStyle = accentColor;
    ctx.fillRect(Math.round(roomX + roomW - langW - 4), Math.round(npY + 4), Math.round(langW), Math.round(barH - 6));
    ctx.fillStyle = '#fff';
    ctx.textAlign = 'center';
    ctx.fillText(lang, Math.round(roomX + roomW - langW / 2 - 4), Math.round(npY + barH / 2 + langFont * 0.35 + 1));

    // -- Render room tiles (disable smoothing for pixel art) --
    ctx.imageSmoothingEnabled = false;
    renderTileGrid(ctx, room.tileMap, roomX, roomY, zoom, room.floorColor, room.wallColor, room.floorSprite);

    // -- Render furniture + characters (z-sorted) --
    var selCharId = (selectedAgent && selectedAgent.character) ? selectedAgent.character.id : null;
    renderScene(ctx, room.furniture, room.characters, roomX, roomY, zoom, spritesByPalette, room.tileMap, room.wallColor, selCharId);

    // -- Render particles for this room --
    renderParticlesForRoom(ctx, roomX, roomY, zoom, room.roomIndex);

    // -- STATS BAR: BELOW the room, separated --
    ctx.imageSmoothingEnabled = true;
    var sbY = roomY + roomH;
    ctx.fillStyle = 'rgba(13,13,36,0.9)';
    ctx.fillRect(Math.round(roomX), Math.round(sbY), Math.round(roomW), barH);

    // Prepare stats data
    var subs = formatNumber(room.canal.inscritos || 0);
    var diff = room.canal.inscritos_diff || 0;
    var v7d = formatNumber(room.canal.views_7d || 0);
    var v30d = formatNumber(room.canal.views_30d || 0);
    var vid30 = room.canal.videos_30d || 0;
    var retPct = room.canal.avg_retention;
    var ctrPct = room.canal.avg_ctr;

    // Build 5 stat blocks: [emoji, text, color, diffText, diffColor]
    var diffText = '';
    var diffColor = null;
    if (diff > 0) { diffText = ' (+' + diff + ')'; diffColor = '#4ade80'; }
    else if (diff < 0) { diffText = ' (' + diff + ')'; diffColor = '#ef4444'; }

    var viewsText = v7d + '/' + v30d;
    var vidText = '' + vid30;
    var retText = (retPct != null && retPct > 0) ? retPct.toFixed(0) + '%' : '--';
    var ctrText = (ctrPct != null && ctrPct > 0) ? (ctrPct * 100).toFixed(1) + '%' : '--';

    var blocks = [
      { emoji: '\uD83D\uDC65', text: subs, color: '#ccc', diffText: diffText, diffColor: diffColor },
      { emoji: '\uD83D\uDC41', text: viewsText, color: '#60a5fa' },
      { emoji: '\uD83C\uDFAC', text: vidText, color: '#aaa' },
      { emoji: '\u23F1', text: retText, color: '#fbbf24' },
      { emoji: '\uD83C\uDFAF', text: ctrText, color: '#fb923c' }
    ];

    ctx.font = statsFont + 'px "Segoe UI", system-ui, sans-serif';
    var stTextY = Math.round(sbY + barH / 2 + statsFont * 0.35);
    var emojiFont = Math.round(statsFont * 0.9) + 'px "Segoe UI Emoji", "Apple Color Emoji", sans-serif';
    var textFont = statsFont + 'px "Segoe UI", system-ui, sans-serif';

    // Measure total width of all blocks to distribute evenly
    var blockWidths = [];
    var totalContentW = 0;
    for (var mi = 0; mi < blocks.length; mi++) {
      ctx.font = emojiFont;
      var eW = ctx.measureText(blocks[mi].emoji).width + 3;
      ctx.font = textFont;
      var tW = ctx.measureText(blocks[mi].text).width;
      var dW = blocks[mi].diffText ? ctx.measureText(blocks[mi].diffText).width : 0;
      var bw = eW + tW + dW;
      blockWidths.push({ emojiW: eW, textW: tW, diffW: dW, totalW: bw });
      totalContentW += bw;
    }

    // Calculate equal gap between blocks
    var padding = 6;
    var availW = roomW - padding * 2;
    var totalGap = availW - totalContentW;
    var gap = blocks.length > 1 ? totalGap / (blocks.length - 1) : 0;
    if (gap < 4) gap = 4; // minimum gap

    // Draw each block with equal spacing
    var curX = Math.round(roomX + padding);
    for (var bi = 0; bi < blocks.length; bi++) {
      var blk = blocks[bi];
      var bw = blockWidths[bi];

      // Emoji
      ctx.textAlign = 'left';
      ctx.font = emojiFont;
      ctx.fillStyle = '#888';
      ctx.fillText(blk.emoji, Math.round(curX), stTextY);

      // Value text
      ctx.font = textFont;
      ctx.fillStyle = blk.color;
      ctx.fillText(blk.text, Math.round(curX + bw.emojiW), stTextY);

      // Diff text (colored green/red)
      if (blk.diffText && blk.diffColor) {
        ctx.fillStyle = blk.diffColor;
        ctx.fillText(blk.diffText, Math.round(curX + bw.emojiW + bw.textW), stTextY);
      }

      curX += Math.round(bw.totalW + gap);
    }
  }
  // Restore pixel-perfect rendering for sprites
  ctx.imageSmoothingEnabled = false;
  ctx.restore(); // restore DPR scale
}

// ============================================================
// 12. INPUT HANDLING
// ============================================================

function setupInput(canvas) {
  // Click to select agent (no zoom, no pan - page scrolls naturally)
  canvas.addEventListener('click', function(e) {
    var rect = canvas.getBoundingClientRect();
    var mx = e.clientX - rect.left;
    var my = e.clientY - rect.top;
    handleClick(mx, my);
  });
}

function handleClick(mx, my) {
  if (visibleRooms.length === 0) return;

  var layout = getRoomLayout(visibleRooms, zoom);
  var canvas = document.getElementById('cv');
  var dpr = window.devicePixelRatio || 1;
  var cssW = canvas.width / dpr;
  var startX = Math.floor((cssW - layout.totalW * zoom) / 2);
  var startY = 24;

  for (var i = 0; i < visibleRooms.length; i++) {
    var room = visibleRooms[i];
    var gridCol = i % ROOMS_PER_ROW;
    var gridRow = Math.floor(i / ROOMS_PER_ROW);
    var barH = Math.max(22, Math.min(32, Math.round(14 * zoom)));
    var roomX = startX + gridCol * (layout.roomW + layout.gap) * zoom;
    var rowStep = layout.roomH * zoom + layout.gapV * zoom + barH * 2;
    var roomY = startY + gridRow * rowStep;

    // Check each character
    for (var ci = 0; ci < room.characters.length; ci++) {
      var ch = room.characters[ci];
      var isSit = ch.state === CharState.TYPE || ch.state === CharState.READ || ch.state === CharState.SLEEP;
      var sOff = isSit ? SIT_OFFSET : 0;
      var charScreenX = roomX + ch.x * zoom;
      var charScreenY = roomY + (ch.y + sOff) * zoom;

      // Hitbox: CHAR_HIT_HALF_W on each side, CHAR_HIT_H tall
      var hitLeft = charScreenX - CHAR_HIT_HALF_W * zoom;
      var hitRight = charScreenX + CHAR_HIT_HALF_W * zoom;
      var hitTop = charScreenY - CHAR_HIT_H * zoom;
      var hitBottom = charScreenY;

      if (mx >= hitLeft && mx <= hitRight && my >= hitTop && my <= hitBottom) {
        openSidebar(room, ch);
        return;
      }
    }
  }

  // Click outside agent -> close sidebar
  closeSidebar();
}

// ============================================================
// 13. SIDEBAR
// ============================================================

function openSidebar(room, ch) {
  selectedAgent = { room: room, character: ch };
  var sb = document.getElementById('sb');
  if (!sb) return;
  sb.style.display = 'block';

  var ag = ch.agentData || {};
  var tema = room.theme;

  // Build sidebar content
  var html = '';
  html += '<div class="sb-close" onclick="closeSidebar()">&times;</div>';
  html += '<div class="sb-header" style="border-color:' + (tema.accent || '#888') + '">';

  // Draw agent sprite (smaller: 48x72)
  html += '<canvas id="sb-sprite" width="48" height="72" style="image-rendering:pixelated;margin:0 auto;display:block;"></canvas>';

  // Agent name: "Agente X - Nome"
  var agIndex = ag.id || ((ch.palette || 0) + 1);
  var agName = ag.agente_nome || ag.tipo || 'Agente';
  html += '<div class="sb-name">Agente ' + agIndex + ' - ' + escapeHtml(agName) + '</div>';
  html += '</div>';

  // Canal info
  html += '<div class="sb-section">';
  html += '<div class="sb-label">Canal</div>';
  html += '<div class="sb-value">' + escapeHtml(room.canal.nome || room.canal.canal_nome || '') + '</div>';
  html += '</div>';

  // Subnicho
  html += '<div class="sb-section">';
  html += '<div class="sb-label">Subnicho</div>';
  html += '<div class="sb-value" style="color:' + (tema.accent || '#888') + '">' + escapeHtml(tema.label || room.themeKey) + '</div>';
  html += '</div>';

  // Description
  if (ag.descricao) {
    html += '<div class="sb-section">';
    html += '<div class="sb-label">Descricao</div>';
    html += '<div class="sb-desc">' + escapeHtml(ag.descricao) + '</div>';
    html += '</div>';
  }

  // Action buttons
  html += '<div class="sb-actions">';

  if (ag.canal_id) {
    html += '<button class="sb-btn sb-btn-primary" onclick="runAgentAnalysis(\'' + ag.canal_id + '\')">Rodar Analise</button>';
    html += '<button class="sb-btn" onclick="loadAgentReport(\'' + ag.canal_id + '\', \'' + (ag.tipo || 'copy_performance') + '\')">Ver Relatorio</button>';
  }

  if (ag.planilha_url) {
    html += '<a class="sb-btn" href="' + escapeHtml(ag.planilha_url) + '" target="_blank">Abrir Planilha</a>';
  }

  html += '</div>';

  // Report container
  html += '<div id="sb-report" class="sb-report"></div>';

  sb.innerHTML = html;

  // Render front-facing sprite in sidebar
  setTimeout(function() {
    var spriteCanvas = document.getElementById('sb-sprite');
    if (!spriteCanvas) return;
    var sctx = spriteCanvas.getContext('2d');
    sctx.imageSmoothingEnabled = false;
    // Always show front-facing (DOWN) standing pose
    var sprites = spritesByPalette[ch.palette] || spritesByPalette[0];
    var spriteData = sprites.walk[Direction.DOWN][0];
    var bigZoom = 3;
    var bigCached = getCachedSprite(spriteData, bigZoom);
    sctx.clearRect(0, 0, 48, 72);
    sctx.drawImage(bigCached, 0, 0);
  }, 50);
}

function closeSidebar() {
  selectedAgent = null;
  var sb = document.getElementById('sb');
  if (sb) sb.style.display = 'none';
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function runAgentAnalysis(channelId) {
  var btn = event.target;
  btn.disabled = true;
  btn.textContent = 'Rodando...';
  fetch('/api/analise-completa/' + channelId, { method: 'POST' })
    .then(function(r) { return r.json(); })
    .then(function(data) {
      btn.textContent = 'Concluido!';
      btn.style.background = '#22c55e';
      setTimeout(function() {
        btn.disabled = false;
        btn.textContent = 'Rodar Analise';
        btn.style.background = '';
      }, 3000);
      if (data.report) {
        showReport(data.report);
      }
    })
    .catch(function(err) {
      btn.textContent = 'Erro!';
      btn.style.background = '#ef4444';
      setTimeout(function() {
        btn.disabled = false;
        btn.textContent = 'Rodar Analise';
        btn.style.background = '';
      }, 3000);
    });
}

function loadAgentReport(channelId, agentType) {
  var reportDiv = document.getElementById('sb-report');
  if (!reportDiv) return;
  reportDiv.innerHTML = '<div style="color:#888;padding:8px">Carregando...</div>';

  fetch('/api/analise-copy/' + channelId + '/latest')
    .then(function(r) { return r.json(); })
    .then(function(data) {
      if (data.report_text) {
        showReport(data.report_text);
      } else {
        reportDiv.innerHTML = '<div style="color:#666;padding:8px">Nenhum relatorio encontrado</div>';
      }
    })
    .catch(function() {
      reportDiv.innerHTML = '<div style="color:#f87171;padding:8px">Erro ao carregar</div>';
    });
}

function showReport(text) {
  var reportDiv = document.getElementById('sb-report');
  if (!reportDiv) return;
  var lines = String(text).split('\n');
  var html = '';
  for (var i = 0; i < lines.length; i++) {
    var line = escapeHtml(lines[i]);
    if (line.indexOf('[') === 0 && line.indexOf(']') > 0) {
      html += '<div class="rpt-header">' + line + '</div>';
    } else if (line.indexOf('ALERTA') >= 0 || line.indexOf('RISCO') >= 0) {
      html += '<div class="rpt-alert">' + line + '</div>';
    } else {
      html += '<div class="rpt-line">' + line + '</div>';
    }
  }
  reportDiv.innerHTML = html;
}

// ============================================================
// 14. TAB SYSTEM
// ============================================================

function setupTabs() {
  var tabsDiv = document.getElementById('tabs');
  if (!tabsDiv) return;

  // Build tabs dynamically from actual data (only subnichos with OAuth channels)
  var themeLabels = {
    'executive': '\u{1F4B0} Monetizados', 'warroom': '\u2694\uFE0F Relatos de Guerra', 'gothic': '\u{1F451} Historias Sombrias',
    'darklab': '\u{1F480} Terror', 'demonetized': '\u26A0\uFE0F Desmonetizados', 'command': '\u{1F3DB}\uFE0F Civilizacoes',
    'wisdom': '\u{1F4DA} Licoes', 'startup': '\u{1F4E6} Outros'
  };
  // Count rooms per theme
  var themeCounts = {};
  for (var ri = 0; ri < allRooms.length; ri++) {
    var tk = allRooms[ri].themeKey;
    if (tk) themeCounts[tk] = (themeCounts[tk] || 0) + 1;
  }
  var presentThemes = {};
  for (var ri2 = 0; ri2 < allRooms.length; ri2++) {
    var tk2 = allRooms[ri2].themeKey;
    if (tk2 && !presentThemes[tk2]) {
      var theme = SECTOR_THEMES[tk2] || {};
      presentThemes[tk2] = { key: tk2, label: themeLabels[tk2] || tk2, count: themeCounts[tk2] || 0, color: theme.accent || '#888' };
    }
  }
  var tabList = [{ key: 'all', label: '\u{1F3E2} Todos', count: allRooms.length, color: '#3b82f6' }];
  var themeOrder = ['executive', 'warroom', 'gothic', 'darklab', 'command', 'demonetized', 'wisdom'];
  for (var oi = 0; oi < themeOrder.length; oi++) {
    if (presentThemes[themeOrder[oi]]) tabList.push(presentThemes[themeOrder[oi]]);
  }

  var html = '';
  for (var i = 0; i < tabList.length; i++) {
    var t = tabList[i];
    var isActive = t.key === activeTab;
    var active = isActive ? ' tab-active' : '';
    var style = isActive
      ? 'border-color:' + t.color + ';background:' + t.color + '22;color:' + t.color
      : 'border-color:transparent;color:#999';
    html += '<button class="tab' + active + '" data-tab="' + t.key + '" style="' + style + '">';
    html += t.label + ' (' + t.count + ')';
    html += '</button>';
  }
  tabsDiv.innerHTML = html;

  // Tab click handlers
  var buttons = tabsDiv.querySelectorAll('.tab');
  for (var b = 0; b < buttons.length; b++) {
    buttons[b].addEventListener('click', function() {
      var key = this.getAttribute('data-tab');
      filterRooms(key);
      setupTabs(); // re-render active state
    });
  }
}

// ============================================================
// 14b. AGENT LEGEND (left panel)
// ============================================================

var AGENT_LEGEND_INFO = [
  { name: 'Estrutura de Copy', desc: 'Analisa performance por estrutura A-G' },
  { name: 'Autenticidade', desc: 'Score 0-100 contra Inauthentic Content' },
  { name: 'Micronichos', desc: 'Subcategorias tematicas que viralizam' },
  { name: 'Estrutura Titulo', desc: 'Padroes de titulo e CTR' },
  { name: 'Temas', desc: 'Assuntos com potencial viral' },
  { name: 'Recomendador', desc: 'Cerebro estrategico - sugere proximos videos' },
  { name: 'Concorrentes', desc: 'Intel competitiva via audiencia YouTube' }
];

function buildLegend() {
  var legendDiv = document.getElementById('legend');
  if (!legendDiv) return;
  legendDiv.innerHTML = '';

  var title = document.createElement('div');
  title.className = 'legend-title';
  title.textContent = 'Agentes';
  legendDiv.appendChild(title);

  for (var i = 0; i < AGENT_PALETTES.length && i < AGENT_LEGEND_INFO.length; i++) {
    var pal = AGENT_PALETTES[i];
    var info = AGENT_LEGEND_INFO[i];

    var item = document.createElement('div');
    item.className = 'legend-item';

    // Color dot
    var dot = document.createElement('div');
    dot.className = 'legend-dot';
    dot.style.background = pal.shirt;
    item.appendChild(dot);

    // Sprite canvas at 2x zoom (32x48 display)
    var sprZoom = 2;
    var miniCanvas = document.createElement('canvas');
    miniCanvas.width = 16 * sprZoom;
    miniCanvas.height = 24 * sprZoom;
    miniCanvas.className = 'legend-sprite';
    miniCanvas.style.width = (16 * sprZoom) + 'px';
    miniCanvas.style.height = (24 * sprZoom) + 'px';
    var mctx = miniCanvas.getContext('2d');
    mctx.imageSmoothingEnabled = false;

    // Render the DOWN standing frame at 2x
    var sprites = getCharacterSprites(i);
    var frame = sprites.walk[Direction.DOWN][0];
    var cached = getCachedSprite(frame, sprZoom);
    if (cached) {
      mctx.drawImage(cached, 0, 0);
    }
    item.appendChild(miniCanvas);

    // Name + description
    var nameSpan = document.createElement('span');
    nameSpan.className = 'legend-name';
    nameSpan.textContent = info.name;
    nameSpan.title = info.desc;
    item.appendChild(nameSpan);

    legendDiv.appendChild(item);
  }
}

// ============================================================
// 15. CANVAS RESIZE
// ============================================================

function resizeCanvas() {
  var canvas = document.getElementById('cv');
  var wrap = document.getElementById('mapWrap');
  if (!canvas || !wrap) return;

  var w = wrap.clientWidth;

  // Dynamic ROOMS_PER_ROW based on available width
  var roomNativeW = ROOM_COLS * TILE_SIZE;  // 224
  if (w < 500) {
    ROOMS_PER_ROW = 1;
  } else if (w < 900) {
    ROOMS_PER_ROW = 2;
  } else {
    ROOMS_PER_ROW = 3;
  }

  // Auto-calculate zoom — always based on ROOMS_PER_ROW for consistency
  var totalNativeW = ROOMS_PER_ROW * roomNativeW + (ROOMS_PER_ROW - 1) * ROOM_GAP;
  zoom = Math.floor((w * 0.80) / totalNativeW * 10) / 10;
  zoom = Math.max(0.6, Math.min(zoom, 1.5));

  // Calculate content height
  var roomCount = visibleRooms.length > 0 ? visibleRooms.length : 1;
  var layout = getRoomLayout(visibleRooms.length > 0 ? visibleRooms : [{dummy:true}], zoom);
  var rowCount = Math.ceil(roomCount / ROOMS_PER_ROW);
  var barH = Math.max(22, Math.min(32, Math.round(14 * zoom)));
  var rowStep = layout.roomH * zoom + layout.gapV * zoom + barH * 2;
  var contentH = 24 + rowCount * rowStep + barH + 60;
  var h = Math.max(contentH, 400);

  var dpr = window.devicePixelRatio || 1;
  canvas.width = w * dpr;
  canvas.height = h * dpr;
  canvas.style.width = w + 'px';
  canvas.style.height = h + 'px';
}

// ============================================================
// 16. INIT
// ============================================================

function startMCGameLoop(canvas) {
  setupTabs();
  buildLegend();

  // Re-init sprite cache after PNG loading
  initSpriteCache();

  // Start game loop
  stopLoop = startGameLoop(canvas, {
    update: function(dt) {
      gameTime += dt;
      // Update all characters in visible rooms
      for (var i = 0; i < visibleRooms.length; i++) {
        var room = visibleRooms[i];
        for (var j = 0; j < room.characters.length; j++) {
          updateCharacter(
            room.characters[j], dt,
            room.walkableTiles, room.seats,
            room.tileMap, room.blockedTiles,
            room
          );
        }
      }
      // Update particles
      updateParticles(dt);
    },
    render: function(ctx) {
      renderAllRooms(ctx, canvas.width, canvas.height);
    }
  });

  // Refresh stats every 60s (without resetting character positions)
  setInterval(function() {
    loadMCData(true);
  }, 60000);
}

function initMissionControl() {
  var canvas = document.getElementById('cv');
  if (!canvas) {
    console.error('[MC] Canvas #cv not found');
    return;
  }

  initSpriteCache();
  resizeCanvas();
  window.addEventListener('resize', resizeCanvas);
  setupInput(canvas);

  // Load API data and PNG sprites in parallel
  var dataReady = false;
  var pngReady = false;

  loadMCData().then(function() {
    dataReady = true;
    if (pngReady) startMCGameLoop(canvas);
  });

  // Load PNG character sprites + wall sprites
  if (typeof loadPNGSprites === 'function') {
    loadPNGSprites(function() {
      console.log('[MC] PNG sprites loaded: ' +
        (loadedCharacters ? loadedCharacters.length + ' characters' : 'no characters') + ', ' +
        (wallSprites ? wallSprites.length + ' wall tiles' : 'no walls'));
      pngReady = true;
      if (dataReady) startMCGameLoop(canvas);
    });
  } else {
    // No PNG loader (fallback to template mode)
    pngReady = true;
  }
}

// Auto-init when DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initMissionControl);
} else {
  initMissionControl();
}

</script>
</body>
</html>"""

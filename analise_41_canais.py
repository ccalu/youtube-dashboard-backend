"""
Análise Completa dos 41 Canais YouTube
Foco em métricas de crescimento e engajamento
"""
import requests
from datetime import datetime, timedelta
import json

# Configuração
SUPABASE_URL = 'https://prvkmzstyedepvlbppyo.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBydmttenN0eWVkZXB2bGJwcHlvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQxNDY3MTQsImV4cCI6MjA1OTcyMjcxNH0.T0aspHrF0tz1G6iVOBIO3zgvs1g5vvQcb25jhGriQGo'
headers = {'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}'}

print('='*100)
print(' '*30 + 'ANÁLISE COMPLETA DOS SEUS 41 CANAIS YOUTUBE')
print('='*100)
print(f'Data da análise: {datetime.now().strftime("%d/%m/%Y às %H:%M")}')
print('')

# Buscar os 41 canais "nossos"
print('Buscando canais...')
resp = requests.get(
    f'{SUPABASE_URL}/rest/v1/canais_monitorados',
    params={
        'tipo': 'eq.nosso',
        'status': 'eq.ativo',
        'select': '*',
        'order': 'nome_canal'
    },
    headers=headers
)

if resp.status_code != 200:
    print(f'Erro ao buscar canais: {resp.status_code}')
    exit()

canais = resp.json()
print(f'Total: {len(canais)} canais encontrados\n')

# Coletar dados históricos para cada canal
print('Coletando métricas de cada canal...')
print('-'*100)

all_data = []
errors = []

for idx, canal in enumerate(canais, 1):
    canal_id = canal['id']
    nome_canal = canal['nome_canal']
    subnicho = canal.get('subnicho', 'Não definido')
    lingua = canal.get('lingua', 'N/A')

    print(f'\n[{idx}/{len(canais)}] {nome_canal}')
    print(f'   Subnicho: {subnicho} | Língua: {lingua}')

    # Buscar dados históricos recentes (últimos 30 dias)
    end_date = datetime.now()
    start_30d = (end_date - timedelta(days=30)).strftime('%Y-%m-%d')
    start_7d = (end_date - timedelta(days=7)).strftime('%Y-%m-%d')

    # Dados dos últimos 30 dias
    hist_resp = requests.get(
        f'{SUPABASE_URL}/rest/v1/dados_canais_historico',
        params={
            'id_canal': f'eq.{canal_id}',
            'data_coleta': f'gte.{start_30d}',
            'select': 'views,inscritos,total_videos,data_coleta',
            'order': 'data_coleta.desc'
        },
        headers=headers
    )

    historico = hist_resp.json() if hist_resp.status_code == 200 else []

    if not historico:
        print(f'   Sem dados históricos')
        errors.append(nome_canal)
        continue

    # Dados mais recentes
    latest = historico[0]
    views_atual = latest.get('views', 0)
    inscritos_atual = latest.get('inscritos', 0)
    videos_atual = latest.get('total_videos', 0)

    # Dados de 7 dias atrás
    data_7d = [h for h in historico if h['data_coleta'] <= start_7d]
    if data_7d:
        views_7d_ago = data_7d[-1].get('views', 0)
        inscritos_7d_ago = data_7d[-1].get('inscritos', 0)
        videos_7d_ago = data_7d[-1].get('total_videos', 0)
    else:
        views_7d_ago = views_atual
        inscritos_7d_ago = inscritos_atual
        videos_7d_ago = videos_atual

    # Dados de 30 dias atrás
    oldest = historico[-1]
    views_30d_ago = oldest.get('views', 0)
    inscritos_30d_ago = oldest.get('inscritos', 0)
    videos_30d_ago = oldest.get('total_videos', 0)

    # Calcular crescimento
    views_crescimento_7d = views_atual - views_7d_ago
    views_crescimento_30d = views_atual - views_30d_ago
    inscritos_crescimento_7d = inscritos_atual - inscritos_7d_ago
    inscritos_crescimento_30d = inscritos_atual - inscritos_30d_ago
    videos_novos_7d = videos_atual - videos_7d_ago
    videos_novos_30d = videos_atual - videos_30d_ago

    # Calcular idade do canal
    primeira_coleta = canal.get('primeira_coleta')
    if primeira_coleta:
        try:
            primeira_data = datetime.fromisoformat(primeira_coleta.replace('T', ' ').split('.')[0])
            idade_dias = (datetime.now() - primeira_data).days
        except:
            idade_dias = len(historico)
    else:
        idade_dias = len(historico)

    # Calcular métricas de eficiência
    views_por_video = views_crescimento_30d / max(videos_novos_30d, 1) if videos_novos_30d > 0 else 0
    views_por_dia = views_crescimento_30d / 30
    taxa_conversao = (inscritos_crescimento_30d / max(views_crescimento_30d, 1) * 100) if views_crescimento_30d > 0 else 0

    # Calcular score (0-100)
    score = 0

    # Views últimos 7 dias (40 pontos)
    if views_crescimento_7d > 100000: score += 40
    elif views_crescimento_7d > 50000: score += 35
    elif views_crescimento_7d > 20000: score += 25
    elif views_crescimento_7d > 10000: score += 20
    elif views_crescimento_7d > 5000: score += 15
    elif views_crescimento_7d > 1000: score += 10
    elif views_crescimento_7d > 500: score += 5
    elif views_crescimento_7d > 100: score += 2

    # Eficiência views/vídeo (25 pontos)
    if views_por_video > 50000: score += 25
    elif views_por_video > 20000: score += 20
    elif views_por_video > 10000: score += 15
    elif views_por_video > 5000: score += 10
    elif views_por_video > 1000: score += 7
    elif views_por_video > 500: score += 4
    elif views_por_video > 100: score += 2

    # Crescimento de inscritos (20 pontos)
    if inscritos_crescimento_30d > 5000: score += 20
    elif inscritos_crescimento_30d > 2000: score += 16
    elif inscritos_crescimento_30d > 1000: score += 12
    elif inscritos_crescimento_30d > 500: score += 9
    elif inscritos_crescimento_30d > 200: score += 6
    elif inscritos_crescimento_30d > 100: score += 4
    elif inscritos_crescimento_30d > 50: score += 2
    elif inscritos_crescimento_30d > 0: score += 1

    # Consistência de publicação (15 pontos)
    if videos_novos_30d >= 30: score += 15  # 1+ vídeo por dia
    elif videos_novos_30d >= 15: score += 12  # 1 vídeo a cada 2 dias
    elif videos_novos_30d >= 8: score += 9   # 2+ vídeos por semana
    elif videos_novos_30d >= 4: score += 6   # 1 vídeo por semana
    elif videos_novos_30d >= 2: score += 3   # 2 vídeos por mês
    elif videos_novos_30d >= 1: score += 1   # Pelo menos 1 vídeo

    # Salvar dados
    canal_data = {
        'nome': nome_canal,
        'subnicho': subnicho,
        'lingua': lingua,
        'idade_dias': idade_dias,
        'inscritos': inscritos_atual,
        'videos': videos_atual,
        'views_total': views_atual,
        'views_7d': views_crescimento_7d,
        'views_30d': views_crescimento_30d,
        'inscritos_7d': inscritos_crescimento_7d,
        'inscritos_30d': inscritos_crescimento_30d,
        'videos_novos_7d': videos_novos_7d,
        'videos_novos_30d': videos_novos_30d,
        'views_por_video': views_por_video,
        'views_por_dia': views_por_dia,
        'taxa_conversao': taxa_conversao,
        'score': score
    }

    all_data.append(canal_data)

    # Mostrar preview
    print(f'   Views 7d: {views_crescimento_7d:,} | Views 30d: {views_crescimento_30d:,}')
    print(f'   Inscritos: {inscritos_atual:,} (+{inscritos_crescimento_30d:,} em 30d)')
    print(f'   Vídeos: {videos_atual} (+{videos_novos_30d} em 30d)')
    print(f'   Score: {score}/100')

# Ordenar por score (pior para melhor)
all_data.sort(key=lambda x: x['score'])

print('\n' + '='*100)
print(' '*35 + 'RANKING COMPLETO - DO PIOR PARA O MELHOR')
print('='*100)

# Estatísticas gerais
total_views_7d = sum(d['views_7d'] for d in all_data)
total_views_30d = sum(d['views_30d'] for d in all_data)
total_inscritos = sum(d['inscritos'] for d in all_data)
total_videos = sum(d['videos'] for d in all_data)
total_novos_videos_30d = sum(d['videos_novos_30d'] for d in all_data)
total_novos_inscritos_30d = sum(d['inscritos_30d'] for d in all_data)

print('\nESTATÍSTICAS GERAIS:')
print(f'   Total de canais analisados: {len(all_data)}')
print(f'   Total de inscritos: {total_inscritos:,}')
print(f'   Total de vídeos: {total_videos:,}')
print(f'   Views (últimos 7 dias): {total_views_7d:,}')
print(f'   Views (últimos 30 dias): {total_views_30d:,}')
print(f'   Novos inscritos (30 dias): +{total_novos_inscritos_30d:,}')
print(f'   Novos vídeos (30 dias): {total_novos_videos_30d}')
print(f'   Média de vídeos por canal: {total_videos/len(all_data):.1f}')
print(f'   Média de views por canal (30d): {total_views_30d/len(all_data):,.0f}')

# Tabela de ranking
print('\n' + '-'*120)
print(f'{"#":<3} {"Canal":<30} {"Score":<6} {"Views 7d":<12} {"Views 30d":<12} {"Inscritos":<10} {"Videos":<7} {"Novos/30d":<9} {"Status"}')
print('-'*120)

for i, d in enumerate(all_data, 1):
    # Determinar status
    if d['score'] < 20:
        status = 'CRÍTICO'
    elif d['score'] < 40:
        status = 'ATENÇÃO'
    elif d['score'] < 60:
        status = 'REGULAR'
    else:
        status = 'BOM'

    nome_curto = d['nome'][:29] if len(d['nome']) > 29 else d['nome']

    print(f'{i:<3} {nome_curto:<30} {d["score"]:<6} {d["views_7d"]:<12,} {d["views_30d"]:<12,} {d["inscritos"]:<10,} {d["videos"]:<7} {d["videos_novos_30d"]:<9} [{status}]')

# Insights e análises
print('\n' + '='*100)
print(' '*40 + 'INSIGHTS E RECOMENDAÇÕES')
print('='*100)

# Canais críticos
criticos = [d for d in all_data if d['score'] < 20]
if criticos:
    print(f'\nCANAIS CRÍTICOS ({len(criticos)} canais com score < 20):')
    print('-'*60)
    for c in criticos[:10]:  # Mostrar até 10
        problema = []
        if c['views_7d'] < 100: problema.append('sem views')
        if c['videos_novos_30d'] < 2: problema.append('sem novos vídeos')
        if c['inscritos_30d'] <= 0: problema.append('perdendo inscritos')
        if not problema: problema.append('baixa performance geral')

        print(f'   {c["nome"]}:')
        print(f'      Problema: {", ".join(problema)}')
        print(f'      Views 7d: {c["views_7d"]:,} | Inscritos: {c["inscritos"]:,} | Score: {c["score"]}')
        print(f'      AÇÃO: Revisar estratégia ou considerar desativação\n')

# Canais em atenção
atencao = [d for d in all_data if 20 <= d['score'] < 40]
if atencao:
    print(f'\nCANAIS QUE PRECISAM ATENÇÃO ({len(atencao)} canais):')
    print('-'*60)
    for a in atencao[:5]:  # Mostrar até 5
        print(f'   {a["nome"]}: Score {a["score"]}')
        if a['videos_novos_30d'] < 4:
            print(f'      Sugestão: Aumentar frequência (apenas {a["videos_novos_30d"]} vídeos em 30d)')
        elif a['views_por_video'] < 1000:
            print(f'      Sugestão: Melhorar qualidade/SEO (média de {a["views_por_video"]:.0f} views/vídeo)')
        else:
            print(f'      Sugestão: Analisar concorrência e otimizar estratégia')

# Top performers
top_5 = all_data[-5:] if len(all_data) >= 5 else all_data
print(f'\nTOP {len(top_5)} MELHORES CANAIS:')
print('-'*60)
for i, t in enumerate(reversed(top_5), 1):
    print(f'   {i}. {t["nome"]}')
    print(f'      Score: {t["score"]}/100')
    print(f'      Views 30d: {t["views_30d"]:,} | Views/vídeo: {t["views_por_video"]:,.0f}')
    print(f'      Inscritos: {t["inscritos"]:,} (+{t["inscritos_30d"]:,} em 30d)')
    print(f'      Publicação: {t["videos_novos_30d"]} vídeos em 30d')
    print()

# Análise por subnicho
print('\nANÁLISE POR SUBNICHO:')
print('-'*60)

subnichos = {}
for d in all_data:
    s = d['subnicho']
    if s not in subnichos:
        subnichos[s] = {
            'canais': [],
            'total_views_30d': 0,
            'total_inscritos': 0,
            'scores': []
        }
    subnichos[s]['canais'].append(d['nome'])
    subnichos[s]['total_views_30d'] += d['views_30d']
    subnichos[s]['total_inscritos'] += d['inscritos']
    subnichos[s]['scores'].append(d['score'])

# Ordenar por média de score
subnichos_ordenados = sorted(subnichos.items(),
                             key=lambda x: sum(x[1]['scores'])/len(x[1]['scores']),
                             reverse=True)

for subnicho, info in subnichos_ordenados:
    media_score = sum(info['scores']) / len(info['scores'])
    print(f'\n   {subnicho}:')
    print(f'      Canais: {len(info["canais"])}')
    print(f'      Score médio: {media_score:.1f}')
    print(f'      Views 30d total: {info["total_views_30d"]:,}')
    print(f'      Inscritos total: {info["total_inscritos"]:,}')
    if media_score < 30:
        print(f'      Subnicho com performance baixa - revisar estratégia')

# Canais mais eficientes
print('\nCANAIS MAIS EFICIENTES (views por vídeo):')
print('-'*60)
eficientes = sorted(all_data, key=lambda x: x['views_por_video'], reverse=True)[:5]
for e in eficientes:
    print(f'   {e["nome"]}: {e["views_por_video"]:,.0f} views/vídeo')
    print(f'     ({e["views_30d"]:,} views com {e["videos_novos_30d"]} vídeos)')

# Canais com maior crescimento
print('\nMAIOR CRESCIMENTO DE INSCRITOS (30 dias):')
print('-'*60)
crescimento = sorted(all_data, key=lambda x: x['inscritos_30d'], reverse=True)[:5]
for c in crescimento:
    base_inscritos = c['inscritos'] - c['inscritos_30d']
    percentual = (c['inscritos_30d'] / max(base_inscritos, 1)) * 100
    print(f'   {c["nome"]}: +{c["inscritos_30d"]:,} ({percentual:.1f}% de crescimento)')

# Recomendações finais
print('\n' + '='*100)
print(' '*35 + 'PLANO DE AÇÃO RECOMENDADO')
print('='*100)

print('\n1. AÇÃO IMEDIATA (Próximos 7 dias):')
print(f'   Revisar {len(criticos)} canais críticos - decidir quais desativar')
print(f'   Replicar estratégia dos top 5 nos canais médios')
print(f'   Aumentar frequência de publicação em canais com < 4 vídeos/mês')

print('\n2. AÇÃO DE MÉDIO PRAZO (Próximos 30 dias):')
print(f'   Estabelecer meta mínima: Score 40+ para todos os canais')
print(f'   Focar em subnichos com melhor performance média')
print(f'   Implementar análise semanal de performance')

print('\n3. MÉTRICAS PARA ACOMPANHAR:')
print(f'   Meta de views/mês: {(total_views_30d * 1.2):,.0f} (+20%)')
print(f'   Meta de novos inscritos/mês: {(total_novos_inscritos_30d * 1.5):,.0f} (+50%)')
print(f'   Meta de vídeos/mês: {max(total_novos_videos_30d * 1.2, len(all_data) * 4):.0f}')

if errors:
    print(f'\nCANAIS SEM DADOS: {len(errors)}')
    for e in errors[:5]:
        print(f'   {e}')

print('\n' + '='*100)
print(' '*40 + 'ANÁLISE COMPLETA!')
print(f' '*30 + f'Processados {len(all_data)} de {len(canais)} canais com sucesso')
print('='*100)

# Salvar dados em JSON para análise posterior
output_data = {
    'data_analise': datetime.now().isoformat(),
    'total_canais': len(all_data),
    'estatisticas': {
        'total_views_7d': total_views_7d,
        'total_views_30d': total_views_30d,
        'total_inscritos': total_inscritos,
        'total_videos': total_videos,
        'novos_videos_30d': total_novos_videos_30d,
        'novos_inscritos_30d': total_novos_inscritos_30d
    },
    'canais': all_data
}

with open('analise_canais_completa.json', 'w', encoding='utf-8') as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)

print('\nDados salvos em: analise_canais_completa.json')
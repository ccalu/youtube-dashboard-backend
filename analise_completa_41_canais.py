"""
Análise Completa dos 41 Canais
Inclui: data de criação, total de vídeos, inscritos, views
"""
import os
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client
import pandas as pd
from tabulate import tabulate

# Carregar variáveis de ambiente
load_dotenv()

# Configurar cliente Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

def get_channel_age(data_adicionado):
    """Calcula a idade do canal em dias/meses"""
    if not data_adicionado:
        return "N/A"

    try:
        # Parse da data
        if 'T' in data_adicionado:
            created = datetime.fromisoformat(data_adicionado.replace('Z', '+00:00'))
        else:
            created = datetime.fromisoformat(data_adicionado)

        now = datetime.now(created.tzinfo or datetime.now().tzinfo)
        diff = now - created

        days = diff.days
        if days < 30:
            return f"{days} dias"
        elif days < 365:
            months = days // 30
            return f"{months} {'mês' if months == 1 else 'meses'}"
        else:
            years = days // 365
            months = (days % 365) // 30
            if months > 0:
                return f"{years} {'ano' if years == 1 else 'anos'} e {months} {'mês' if months == 1 else 'meses'}"
            return f"{years} {'ano' if years == 1 else 'anos'}"
    except:
        return "N/A"

async def get_complete_channel_data():
    """Busca dados completos dos 41 canais"""

    print("📊 Buscando dados completos dos 41 canais...")
    print("=" * 80)

    # 1. Buscar canais com informações básicas incluindo data_adicionado
    canais_response = supabase.table("canais_monitorados")\
        .select("id, nome_canal, subnicho, lingua, data_adicionado, url_canal")\
        .eq("tipo", "nosso")\
        .execute()

    print(f"✅ {len(canais_response.data)} canais encontrados")

    # 2. Buscar métricas mais recentes de cada canal
    canal_ids = [c['id'] for c in canais_response.data]

    # Buscar dados históricos mais recentes
    historico_response = supabase.table("dados_canais_historico")\
        .select("*")\
        .in_("canal_id", canal_ids)\
        .execute()

    # Organizar por canal_id pegando o mais recente
    historico_por_canal = {}
    for h in historico_response.data:
        canal_id = h['canal_id']
        data_coleta = h.get('data_coleta', '')

        if canal_id not in historico_por_canal or data_coleta > historico_por_canal[canal_id].get('data_coleta', ''):
            historico_por_canal[canal_id] = h

    # 3. Buscar total de vídeos de cada canal
    print("\n📹 Buscando total de vídeos por canal...")

    videos_response = supabase.table("videos_historico")\
        .select("canal_id, video_id")\
        .in_("canal_id", canal_ids)\
        .execute()

    # Contar vídeos únicos por canal
    videos_por_canal = {}
    for v in videos_response.data:
        canal_id = v['canal_id']
        if canal_id not in videos_por_canal:
            videos_por_canal[canal_id] = set()
        videos_por_canal[canal_id].add(v['video_id'])

    # Converter sets para contagem
    videos_count = {k: len(v) for k, v in videos_por_canal.items()}

    # 4. Compilar dados completos
    canais_completos = []
    for canal in canais_response.data:
        canal_id = canal['id']
        historico = historico_por_canal.get(canal_id, {})

        canal_data = {
            'nome': canal['nome_canal'],
            'subnicho': canal['subnicho'],
            'lingua': canal['lingua'],
            'data_criacao': canal.get('data_adicionado', 'N/A'),
            'idade': get_channel_age(canal.get('data_adicionado')),
            'total_videos': videos_count.get(canal_id, 0),
            'videos_7d': historico.get('videos_publicados_7d', 0),
            'inscritos': historico.get('inscritos', 0),
            'views_30d': historico.get('views_30d', 0),
            'views_7d': historico.get('views_7d', 0),
            'engagement': historico.get('engagement_rate', 0),
            'url': canal['url_canal']
        }

        # Calcular métricas derivadas
        if canal_data['inscritos'] > 0:
            canal_data['views_por_inscrito'] = round(canal_data['views_30d'] / canal_data['inscritos'], 2)
        else:
            canal_data['views_por_inscrito'] = 0

        if canal_data['total_videos'] > 0:
            canal_data['views_por_video'] = round(canal_data['views_30d'] / canal_data['total_videos'], 0)
        else:
            canal_data['views_por_video'] = 0

        canais_completos.append(canal_data)

    return canais_completos

def analyze_channels(canais):
    """Análise completa na sequência: criação → videos → inscritos → views"""

    print("\n" + "=" * 100)
    print("📊 ANÁLISE COMPLETA DOS 41 CANAIS")
    print("=" * 100)

    # Converter para DataFrame para facilitar análise
    df = pd.DataFrame(canais)

    # 1. ANÁLISE POR IDADE DO CANAL
    print("\n🗓️ ANÁLISE POR IDADE DO CANAL")
    print("-" * 50)

    # Ordenar por idade (mais antigos primeiro)
    df_sorted = df.sort_values('data_criacao')

    # Agrupar por faixas de idade
    age_groups = {
        '< 1 mês': [],
        '1-3 meses': [],
        '3-6 meses': [],
        '6-12 meses': [],
        '> 1 ano': []
    }

    for _, canal in df_sorted.iterrows():
        idade = canal['idade']
        if 'dias' in str(idade) or '1 mês' in str(idade):
            age_groups['< 1 mês'].append(canal)
        elif any(x in str(idade) for x in ['2 meses', '3 meses']):
            age_groups['1-3 meses'].append(canal)
        elif any(x in str(idade) for x in ['4 meses', '5 meses', '6 meses']):
            age_groups['3-6 meses'].append(canal)
        elif 'meses' in str(idade) and not 'ano' in str(idade):
            age_groups['6-12 meses'].append(canal)
        else:
            age_groups['> 1 ano'].append(canal)

    for grupo, canais_grupo in age_groups.items():
        if canais_grupo:
            print(f"\n{grupo}: {len(canais_grupo)} canais")
            df_grupo = pd.DataFrame(canais_grupo)
            print(f"  - Média de vídeos: {df_grupo['total_videos'].mean():.1f}")
            print(f"  - Média de inscritos: {df_grupo['inscritos'].mean():.0f}")
            print(f"  - Média de views/30d: {df_grupo['views_30d'].mean():.0f}")

    # 2. TOP 10 CANAIS POR TOTAL DE VÍDEOS
    print("\n\n📹 TOP 10 CANAIS POR TOTAL DE VÍDEOS")
    print("-" * 50)

    top_videos = df.nlargest(10, 'total_videos')[['nome', 'total_videos', 'idade', 'views_30d', 'inscritos']]
    print(tabulate(top_videos, headers=['Canal', 'Total Vídeos', 'Idade', 'Views 30d', 'Inscritos'],
                   tablefmt='grid', showindex=False))

    # 3. ANÁLISE DE PRODUTIVIDADE (vídeos por mês de vida)
    print("\n\n⚡ ANÁLISE DE PRODUTIVIDADE")
    print("-" * 50)

    productivity = []
    for _, canal in df.iterrows():
        idade_str = str(canal['idade'])
        # Estimar dias de vida
        if 'dias' in idade_str:
            dias = int(idade_str.split()[0])
        elif 'mês' in idade_str or 'meses' in idade_str:
            meses = int(idade_str.split()[0])
            dias = meses * 30
        elif 'ano' in idade_str:
            anos = int(idade_str.split()[0])
            dias = anos * 365
        else:
            dias = 30  # default

        if dias > 0:
            videos_por_mes = (canal['total_videos'] / dias) * 30
            productivity.append({
                'nome': canal['nome'],
                'total_videos': canal['total_videos'],
                'idade': canal['idade'],
                'videos_por_mes': round(videos_por_mes, 1),
                'views_30d': canal['views_30d']
            })

    df_prod = pd.DataFrame(productivity)
    top_prod = df_prod.nlargest(10, 'videos_por_mes')
    print("\nCanais Mais Produtivos (vídeos/mês):")
    print(tabulate(top_prod[['nome', 'videos_por_mes', 'total_videos', 'idade', 'views_30d']],
                   headers=['Canal', 'Vídeos/Mês', 'Total', 'Idade', 'Views 30d'],
                   tablefmt='grid', showindex=False))

    # 4. ANÁLISE POR SUBNICHO
    print("\n\n🎯 ANÁLISE POR SUBNICHO")
    print("-" * 50)

    subnicho_stats = df.groupby('subnicho').agg({
        'nome': 'count',
        'total_videos': 'sum',
        'inscritos': 'sum',
        'views_30d': 'sum',
        'views_7d': 'sum'
    }).rename(columns={'nome': 'canais'})

    subnicho_stats['videos_por_canal'] = (subnicho_stats['total_videos'] / subnicho_stats['canais']).round(1)
    subnicho_stats['inscritos_por_canal'] = (subnicho_stats['inscritos'] / subnicho_stats['canais']).round(0)
    subnicho_stats['views_por_canal'] = (subnicho_stats['views_30d'] / subnicho_stats['canais']).round(0)

    print(tabulate(subnicho_stats[['canais', 'videos_por_canal', 'inscritos_por_canal', 'views_por_canal']],
                   headers=['Subnicho', 'Canais', 'Vídeos/Canal', 'Inscritos/Canal', 'Views/Canal'],
                   tablefmt='grid'))

    # 5. CANAIS CRÍTICOS (baixo desempenho considerando idade e vídeos)
    print("\n\n⚠️ CANAIS CRÍTICOS")
    print("-" * 50)

    # Calcular score considerando idade e vídeos
    for i, canal in df.iterrows():
        # Penalizar canais antigos com poucas views
        idade_factor = 1
        if 'meses' in str(canal['idade']) or 'ano' in str(canal['idade']):
            idade_factor = 2  # Canais mais antigos deveriam ter mais views

        # Score: views por vídeo, ajustado pela idade
        if canal['total_videos'] > 0:
            df.at[i, 'score_critico'] = (canal['views_30d'] / canal['total_videos']) / idade_factor
        else:
            df.at[i, 'score_critico'] = 0

    canais_criticos = df.nsmallest(15, 'score_critico')
    print("\nCanais com pior desempenho (considerando idade e total de vídeos):")

    critical_table = []
    for _, canal in canais_criticos.iterrows():
        critical_table.append({
            'Canal': canal['nome'][:30],
            'Idade': canal['idade'],
            'Vídeos': canal['total_videos'],
            'Views/30d': f"{canal['views_30d']:,}",
            'Views/Vídeo': int(canal['views_por_video']),
            'Inscritos': f"{canal['inscritos']:,}",
            'Subnicho': canal['subnicho'][:20]
        })

    print(tabulate(critical_table, headers='keys', tablefmt='grid'))

    # 6. RECOMENDAÇÕES
    print("\n\n💡 RECOMENDAÇÕES BASEADAS NA ANÁLISE")
    print("-" * 50)

    # Canais para cortar
    cortar = df[(df['views_30d'] < 1000) & (df['total_videos'] > 10)]
    if not cortar.empty:
        print(f"\n🔴 CORTAR IMEDIATAMENTE ({len(cortar)} canais):")
        print("Canais com mais de 10 vídeos e menos de 1.000 views/mês:")
        for _, c in cortar.iterrows():
            print(f"  - {c['nome']}: {c['total_videos']} vídeos, {c['views_30d']} views/30d, idade: {c['idade']}")

    # Canais para observar
    observar = df[(df['views_30d'] >= 1000) & (df['views_30d'] < 5000) & (df['total_videos'] > 20)]
    if not observar.empty:
        print(f"\n🟡 OBSERVAR ({len(observar)} canais):")
        print("Canais com desempenho mediano que precisam melhorar:")
        for _, c in observar.iterrows():
            print(f"  - {c['nome']}: {c['views_30d']:,} views/30d, {c['total_videos']} vídeos")

    # Canais promissores
    promissores = df[(df['views_30d'] > 10000) | ((df['views_por_video'] > 500) & (df['total_videos'] < 20))]
    if not promissores.empty:
        print(f"\n🟢 MANTER E INVESTIR ({len(promissores)} canais):")
        print("Canais com bom desempenho ou alto potencial:")
        for _, c in promissores.nlargest(10, 'views_30d').iterrows():
            print(f"  - {c['nome']}: {c['views_30d']:,} views/30d, {c['views_por_video']:.0f} views/vídeo")

    # Estatísticas gerais
    print("\n\n📈 ESTATÍSTICAS GERAIS")
    print("-" * 50)
    print(f"Total de canais: {len(df)}")
    print(f"Total de vídeos publicados: {df['total_videos'].sum():,}")
    print(f"Total de inscritos: {df['inscritos'].sum():,}")
    print(f"Total de views (30d): {df['views_30d'].sum():,}")
    print(f"Média de vídeos por canal: {df['total_videos'].mean():.1f}")
    print(f"Média de inscritos por canal: {df['inscritos'].mean():.0f}")
    print(f"Média de views/30d por canal: {df['views_30d'].mean():.0f}")

async def main():
    try:
        # Buscar dados
        canais = await get_complete_channel_data()

        # Fazer análise
        analyze_channels(canais)

        # Salvar em CSV para análise posterior
        df = pd.DataFrame(canais)
        df.to_csv('analise_41_canais_completa.csv', index=False, encoding='utf-8')
        print("\n✅ Análise salva em 'analise_41_canais_completa.csv'")

    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
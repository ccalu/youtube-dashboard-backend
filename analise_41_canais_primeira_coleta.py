"""
Análise Completa dos 41 Canais - Baseada na Primeira Coleta
Data de criação = primeira coleta no sistema
"""
import os
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client
import pandas as pd
import csv

# Carregar variáveis de ambiente
load_dotenv()

# Configurar cliente Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

def calcular_idade(primeira_coleta):
    """Calcula a idade baseada na primeira coleta"""
    if not primeira_coleta:
        return "N/A", 0

    try:
        if isinstance(primeira_coleta, str):
            primeira = datetime.fromisoformat(primeira_coleta.replace('Z', '+00:00').split('T')[0])
        else:
            primeira = primeira_coleta

        hoje = datetime.now()
        diff = hoje - primeira
        dias = diff.days

        if dias < 30:
            return f"{dias} dias", dias
        elif dias < 365:
            meses = dias // 30
            return f"{meses} {'mês' if meses == 1 else 'meses'}", dias
        else:
            anos = dias // 365
            meses_resto = (dias % 365) // 30
            if meses_resto > 0:
                return f"{anos} {'ano' if anos == 1 else 'anos'} e {meses_resto} {'mês' if meses_resto == 1 else 'meses'}", dias
            return f"{anos} {'ano' if anos == 1 else 'anos'}", dias
    except:
        return "N/A", 0

async def get_complete_data():
    """Busca dados completos com primeira coleta"""

    print("ANALISE COMPLETA DOS 41 CANAIS DO YOUTUBE")
    print("=" * 80)
    print("Buscando dados...")

    # 1. Buscar canais básicos
    canais_response = supabase.table("canais_monitorados")\
        .select("id, nome_canal, subnicho, lingua, url_canal")\
        .eq("tipo", "nosso")\
        .execute()

    print(f"[OK] {len(canais_response.data)} canais encontrados")
    canal_ids = [c['id'] for c in canais_response.data]

    # 2. Buscar PRIMEIRA coleta de cada canal
    print("\nBuscando data da primeira coleta...")
    historico_response = supabase.table("dados_canais_historico")\
        .select("canal_id, data_coleta, inscritos, views_30d, views_7d, engagement_rate, videos_publicados_7d")\
        .in_("canal_id", canal_ids)\
        .execute()

    # Processar para pegar primeira e última coleta
    primeira_coleta = {}
    ultima_coleta = {}

    for h in historico_response.data:
        canal_id = h['canal_id']
        data_coleta = h.get('data_coleta', '')

        # Primeira coleta (mais antiga)
        if canal_id not in primeira_coleta or data_coleta < primeira_coleta[canal_id]:
            primeira_coleta[canal_id] = data_coleta

        # Última coleta (mais recente) com métricas
        if canal_id not in ultima_coleta or data_coleta > ultima_coleta[canal_id]['data_coleta']:
            ultima_coleta[canal_id] = h

    # 3. Buscar total de vídeos
    print("Contando total de videos por canal...")
    videos_response = supabase.table("videos_historico")\
        .select("canal_id, video_id")\
        .in_("canal_id", canal_ids)\
        .execute()

    # Contar vídeos únicos
    videos_por_canal = {}
    for v in videos_response.data:
        canal_id = v['canal_id']
        if canal_id not in videos_por_canal:
            videos_por_canal[canal_id] = set()
        videos_por_canal[canal_id].add(v['video_id'])

    videos_count = {k: len(v) for k, v in videos_por_canal.items()}

    # 4. Compilar dados completos
    canais_completos = []
    for canal in canais_response.data:
        canal_id = canal['id']
        metricas = ultima_coleta.get(canal_id, {})

        idade_str, dias = calcular_idade(primeira_coleta.get(canal_id))

        canal_data = {
            'id': canal_id,
            'nome': canal['nome_canal'],
            'subnicho': canal['subnicho'],
            'lingua': canal['lingua'],
            'primeira_coleta': primeira_coleta.get(canal_id, 'N/A'),
            'idade': idade_str,
            'dias': dias,
            'total_videos': videos_count.get(canal_id, 0),
            'videos_7d': metricas.get('videos_publicados_7d', 0),
            'inscritos': metricas.get('inscritos', 0),
            'views_30d': metricas.get('views_30d', 0),
            'views_7d': metricas.get('views_7d', 0),
            'engagement': metricas.get('engagement_rate', 0),
            'url': canal['url_canal']
        }

        # Métricas derivadas
        if canal_data['inscritos'] > 0:
            canal_data['views_por_inscrito'] = round(canal_data['views_30d'] / canal_data['inscritos'], 2)
        else:
            canal_data['views_por_inscrito'] = 0

        if canal_data['total_videos'] > 0:
            canal_data['views_por_video'] = round(canal_data['views_30d'] / canal_data['total_videos'], 0)
        else:
            canal_data['views_por_video'] = 0

        if dias > 0:
            canal_data['videos_por_mes'] = round((canal_data['total_videos'] / dias) * 30, 1)
        else:
            canal_data['videos_por_mes'] = 0

        canais_completos.append(canal_data)

    return canais_completos

def print_table(data, headers, max_width=None):
    """Imprime tabela formatada simples"""
    if not data:
        return

    # Calcular larguras
    col_widths = []
    for i, header in enumerate(headers):
        width = len(str(header))
        for row in data:
            if i < len(row):
                width = max(width, len(str(row[i])))
        if max_width and i == 0:  # Limitar primeira coluna (nome)
            width = min(width, max_width)
        col_widths.append(width)

    # Header
    header_line = " | ".join(str(h).ljust(w) for h, w in zip(headers, col_widths))
    print(header_line)
    print("-" * len(header_line))

    # Dados
    for row in data:
        row_line = " | ".join(str(r)[:w].ljust(w) if i == 0 and max_width else str(r).ljust(w)
                              for i, (r, w) in enumerate(zip(row, col_widths)))
        print(row_line)

def analyze_channels(canais):
    """Análise na sequência: criação → videos → inscritos → views"""

    print("\n" + "=" * 80)
    print("ANALISE DETALHADA")
    print("=" * 80)

    # Converter para DataFrame
    df = pd.DataFrame(canais)

    # 1. ANÁLISE POR DATA DE PRIMEIRA COLETA
    print("\n[1] DATA DA PRIMEIRA COLETA (quando foi adicionado ao sistema)")
    print("-" * 60)

    df_sorted = df.sort_values('primeira_coleta')
    print("\n5 Canais mais antigos no sistema:")
    for i, canal in df_sorted.head(5).iterrows():
        print(f"  - {canal['nome'][:30]}: {canal['primeira_coleta']} ({canal['idade']})")

    print("\n5 Canais mais recentes no sistema:")
    for i, canal in df_sorted.tail(5).iterrows():
        print(f"  - {canal['nome'][:30]}: {canal['primeira_coleta']} ({canal['idade']})")

    # Estatísticas por idade
    print("\nDistribuicao por idade:")
    age_ranges = {
        '< 1 mês': df[df['dias'] < 30],
        '1-2 meses': df[(df['dias'] >= 30) & (df['dias'] < 60)],
        '2-3 meses': df[(df['dias'] >= 60) & (df['dias'] < 90)],
        '> 3 meses': df[df['dias'] >= 90]
    }

    for range_name, range_df in age_ranges.items():
        if not range_df.empty:
            print(f"\n  {range_name}: {len(range_df)} canais")
            print(f"    - Média de vídeos: {range_df['total_videos'].mean():.1f}")
            print(f"    - Média de inscritos: {range_df['inscritos'].mean():.0f}")
            print(f"    - Média de views/30d: {range_df['views_30d'].mean():.0f}")

    # 2. ANÁLISE POR TOTAL DE VÍDEOS
    print("\n\n[2] TOTAL DE VIDEOS PUBLICADOS")
    print("-" * 60)

    print("\nTop 10 canais com mais vídeos:")
    top_videos = df.nlargest(10, 'total_videos')
    data_videos = []
    for i, c in top_videos.iterrows():
        data_videos.append([
            c['nome'][:30],
            c['total_videos'],
            c['idade'],
            f"{c['views_30d']:,}",
            f"{c['inscritos']:,}"
        ])
    print_table(data_videos, ['Canal', 'Vídeos', 'Idade', 'Views/30d', 'Inscritos'], 30)

    # 3. ANÁLISE POR INSCRITOS
    print("\n\n[3] INSCRITOS ATUAIS")
    print("-" * 60)

    print("\nTop 10 canais com mais inscritos:")
    top_inscritos = df.nlargest(10, 'inscritos')
    data_inscritos = []
    for i, c in top_inscritos.iterrows():
        data_inscritos.append([
            c['nome'][:30],
            f"{c['inscritos']:,}",
            c['total_videos'],
            f"{c['views_30d']:,}",
            c['subnicho'][:20]
        ])
    print_table(data_inscritos, ['Canal', 'Inscritos', 'Vídeos', 'Views/30d', 'Subnicho'], 30)

    # 4. ANÁLISE POR VIEWS
    print("\n\n[4] VIEWS DOS ULTIMOS 30 DIAS")
    print("-" * 60)

    print("\nTop 10 canais com mais views:")
    top_views = df.nlargest(10, 'views_30d')
    data_views = []
    for i, c in top_views.iterrows():
        data_views.append([
            c['nome'][:30],
            f"{c['views_30d']:,}",
            f"{c['views_por_video']:.0f}",
            c['total_videos'],
            c['idade']
        ])
    print_table(data_views, ['Canal', 'Views/30d', 'Views/Vídeo', 'Vídeos', 'Idade'], 30)

    # 5. PRODUTIVIDADE
    print("\n\n[5] ANALISE DE PRODUTIVIDADE")
    print("-" * 60)

    print("\nCanais mais produtivos (vídeos/mês desde primeira coleta):")
    top_prod = df.nlargest(10, 'videos_por_mes')
    data_prod = []
    for i, c in top_prod.iterrows():
        data_prod.append([
            c['nome'][:30],
            f"{c['videos_por_mes']:.1f}",
            c['total_videos'],
            c['idade'],
            f"{c['views_30d']:,}"
        ])
    print_table(data_prod, ['Canal', 'Vídeos/Mês', 'Total', 'Idade', 'Views/30d'], 30)

    # 6. ANÁLISE POR SUBNICHO
    print("\n\n[6] ANALISE POR SUBNICHO")
    print("-" * 60)

    subnicho_stats = df.groupby('subnicho').agg({
        'nome': 'count',
        'total_videos': ['sum', 'mean'],
        'inscritos': ['sum', 'mean'],
        'views_30d': ['sum', 'mean']
    })

    print("\nEstatísticas por subnicho:")
    data_subnicho = []
    for subnicho in subnicho_stats.index:
        data_subnicho.append([
            subnicho[:25],
            int(subnicho_stats.loc[subnicho, ('nome', 'count')]),
            int(subnicho_stats.loc[subnicho, ('total_videos', 'sum')]),
            f"{int(subnicho_stats.loc[subnicho, ('views_30d', 'mean')]):,}",
            f"{int(subnicho_stats.loc[subnicho, ('inscritos', 'mean')]):,}"
        ])
    print_table(data_subnicho, ['Subnicho', 'Canais', 'Total Vídeos', 'Views/Canal', 'Insc/Canal'], 25)

    # 7. CANAIS CRÍTICOS
    print("\n\n[7] CANAIS CRITICOS (baixo desempenho)")
    print("-" * 60)

    # Score: views por vídeo, penalizado pela idade
    for i, canal in df.iterrows():
        idade_factor = 1
        if canal['dias'] > 60:  # Mais de 2 meses
            idade_factor = 2
        elif canal['dias'] > 90:  # Mais de 3 meses
            idade_factor = 3

        if canal['total_videos'] > 0:
            df.at[i, 'score_critico'] = (canal['views_30d'] / canal['total_videos']) / idade_factor
        else:
            df.at[i, 'score_critico'] = 0

    canais_criticos = df.nsmallest(15, 'score_critico')
    print("\n15 canais com pior desempenho (considerando idade e vídeos):")
    data_criticos = []
    for i, c in canais_criticos.iterrows():
        data_criticos.append([
            c['nome'][:30],
            c['idade'],
            c['total_videos'],
            f"{c['views_30d']:,}",
            f"{c['views_por_video']:.0f}",
            c['subnicho'][:15]
        ])
    print_table(data_criticos, ['Canal', 'Idade', 'Vídeos', 'Views/30d', 'V/Video', 'Subnicho'], 30)

    # 8. RECOMENDAÇÕES
    print("\n\n[8] RECOMENDACOES")
    print("-" * 60)

    # Cortar
    cortar = df[(df['views_30d'] < 1000) & (df['total_videos'] > 10) & (df['dias'] > 30)]
    if not cortar.empty:
        print(f"\n[VERMELHO] CORTAR IMEDIATAMENTE ({len(cortar)} canais):")
        print("Canais antigos com muitos videos e poucas views:")
        for i, c in cortar.iterrows():
            print(f"  - {c['nome'][:40]}: {c['total_videos']} videos, {c['views_30d']} views, idade: {c['idade']}")

    # Observar
    observar = df[(df['views_30d'] >= 1000) & (df['views_30d'] < 5000) & (df['total_videos'] > 20)]
    if not observar.empty:
        print(f"\n[AMARELO] OBSERVAR ({len(observar)} canais):")
        print("Desempenho mediano, precisam melhorar:")
        for i, c in observar.head(5).iterrows():
            print(f"  - {c['nome'][:40]}: {c['views_30d']:,} views, {c['total_videos']} videos")

    # Investir
    promissores = df[(df['views_30d'] > 10000) | ((df['views_por_video'] > 500) & (df['total_videos'] < 20))]
    if not promissores.empty:
        print(f"\n[VERDE] MANTER E INVESTIR ({len(promissores)} canais):")
        print("Alto desempenho ou potencial:")
        for i, c in promissores.nlargest(10, 'views_30d').iterrows():
            print(f"  - {c['nome'][:40]}: {c['views_30d']:,} views, {c['views_por_video']:.0f} views/video")

    # Estatísticas gerais
    print("\n\n📈 ESTATÍSTICAS GERAIS")
    print("-" * 60)
    print(f"Total de canais: {len(df)}")
    print(f"Total de vídeos publicados: {df['total_videos'].sum():,}")
    print(f"Total de inscritos: {df['inscritos'].sum():,}")
    print(f"Total de views (30d): {df['views_30d'].sum():,}")
    print(f"\nMédias por canal:")
    print(f"  • Vídeos: {df['total_videos'].mean():.1f}")
    print(f"  • Inscritos: {df['inscritos'].mean():.0f}")
    print(f"  • Views/30d: {df['views_30d'].mean():.0f}")
    print(f"  • Idade média: {df['dias'].mean():.0f} dias")

async def main():
    try:
        # Buscar dados
        canais = await get_complete_data()

        # Fazer análise
        analyze_channels(canais)

        # Salvar CSV
        print("\n" + "=" * 80)
        print("💾 Salvando dados em CSV...")

        with open('analise_41_canais_primeira_coleta.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=canais[0].keys())
            writer.writeheader()
            writer.writerows(canais)

        print("✅ Análise salva em 'analise_41_canais_primeira_coleta.csv'")

    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
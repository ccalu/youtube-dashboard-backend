"""
Investiga o que os 9 canais problemáticos têm em comum
"""

import os
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from database import SupabaseClient

load_dotenv()

# Os 9 canais problemáticos (8 na verdade, 1 estava faltando)
CANAIS_PROBLEMA = [837, 376, 167, 416, 222, 16, 711, 715]

async def investigate_common_pattern():
    """Investiga padrões comuns"""
    db = SupabaseClient()

    output = []
    output.append("=" * 100)
    output.append("INVESTIGACAO DE PADROES COMUNS - 9 CANAIS PROBLEMATICOS")
    output.append("=" * 100)
    output.append("")

    # Buscar dados completos dos canais
    output.append("[1] DADOS DOS CANAIS:")
    output.append("=" * 100)
    output.append("")

    canais_data = []

    for canal_id in CANAIS_PROBLEMA:
        canal_info = db.supabase.table("canais_monitorados")\
            .select("*")\
            .eq("id", canal_id)\
            .execute()

        if canal_info.data:
            canal = canal_info.data[0]

            # Buscar última coleta BEM-SUCEDIDA
            ultima_coleta_sucesso = db.supabase.table("dados_canais_historico")\
                .select("*")\
                .eq("canal_id", canal_id)\
                .order("data_coleta", desc=True)\
                .limit(1)\
                .execute()

            ultima_data = None
            views_30d = 0
            views_15d = 0
            views_7d = 0
            inscritos = 0

            if ultima_coleta_sucesso.data:
                ultima = ultima_coleta_sucesso.data[0]
                ultima_data = ultima.get('data_coleta')
                views_30d = ultima.get('views_30d', 0)
                views_15d = ultima.get('views_15d', 0)
                views_7d = ultima.get('views_7d', 0)
                inscritos = ultima.get('inscritos', 0)

            canal_data = {
                'id': canal_id,
                'nome': canal.get('nome_canal', 'N/A'),
                'url': canal.get('url_canal', 'N/A'),
                'tipo': canal.get('tipo', 'N/A'),
                'subnicho': canal.get('subnicho', 'N/A'),
                'monetizado': canal.get('monetizado', False),
                'ultima_data': ultima_data,
                'views_30d': views_30d,
                'views_15d': views_15d,
                'views_7d': views_7d,
                'inscritos': inscritos
            }

            canais_data.append(canal_data)

            output.append(f"Canal ID {canal_id} - {canal_data['nome']}")
            output.append(f"  URL: {canal_data['url']}")
            output.append(f"  Tipo: {canal_data['tipo']}")
            output.append(f"  Subnicho: {canal_data['subnicho']}")
            output.append(f"  Monetizado: {canal_data['monetizado']}")
            output.append(f"  Ultima coleta sucesso: {ultima_data}")
            output.append(f"  Views 30d: {views_30d:,}")
            output.append(f"  Views 15d: {views_15d:,}")
            output.append(f"  Views 7d: {views_7d:,}")
            output.append(f"  Inscritos: {inscritos:,}")
            output.append("")

    # Análise de padrões
    output.append("=" * 100)
    output.append("[2] ANALISE DE PADROES:")
    output.append("=" * 100)
    output.append("")

    # Padrão 1: Formato de URL
    url_patterns = {}
    for canal in canais_data:
        url = canal['url']
        if '@' in url:
            pattern = 'handle (@)'
        elif '/channel/' in url:
            pattern = 'channel ID'
        elif '/c/' in url:
            pattern = 'custom URL (/c/)'
        else:
            pattern = 'outro'

        if pattern not in url_patterns:
            url_patterns[pattern] = 0
        url_patterns[pattern] += 1

    output.append("PADRAO 1 - Formato de URL:")
    for pattern, count in url_patterns.items():
        output.append(f"  {pattern}: {count}/9 ({(count/9)*100:.1f}%)")
    output.append("")

    # Padrão 2: Tipo de canal
    tipo_patterns = {}
    for canal in canais_data:
        tipo = canal['tipo']
        if tipo not in tipo_patterns:
            tipo_patterns[tipo] = 0
        tipo_patterns[tipo] += 1

    output.append("PADRAO 2 - Tipo de Canal:")
    for tipo, count in tipo_patterns.items():
        output.append(f"  {tipo}: {count}/9 ({(count/9)*100:.1f}%)")
    output.append("")

    # Padrão 3: Subnicho
    subnicho_patterns = {}
    for canal in canais_data:
        subnicho = canal['subnicho']
        if subnicho not in subnicho_patterns:
            subnicho_patterns[subnicho] = 0
        subnicho_patterns[subnicho] += 1

    output.append("PADRAO 3 - Subnicho:")
    for subnicho, count in sorted(subnicho_patterns.items(), key=lambda x: x[1], reverse=True):
        output.append(f"  {subnicho}: {count}/9 ({(count/9)*100:.1f}%)")
    output.append("")

    # Padrão 4: Monetização
    monetizados = sum(1 for c in canais_data if c['monetizado'])
    nao_monetizados = len(canais_data) - monetizados

    output.append("PADRAO 4 - Monetizacao:")
    output.append(f"  Monetizados: {monetizados}/9 ({(monetizados/9)*100:.1f}%)")
    output.append(f"  Nao monetizados: {nao_monetizados}/9 ({(nao_monetizados/9)*100:.1f}%)")
    output.append("")

    # Padrão 5: Views nas últimas coletas
    output.append("PADRAO 5 - Views nas Ultimas Coletas:")
    output.append("")

    # Canais com views_15d = 0 na última coleta
    views_15d_zero = sum(1 for c in canais_data if c['views_15d'] == 0)
    views_7d_zero = sum(1 for c in canais_data if c['views_7d'] == 0)
    todas_views_zero = sum(1 for c in canais_data if c['views_30d'] == 0 and c['views_15d'] == 0 and c['views_7d'] == 0)

    output.append(f"  Views 15d = 0: {views_15d_zero}/9 ({(views_15d_zero/9)*100:.1f}%)")
    output.append(f"  Views 7d = 0: {views_7d_zero}/9 ({(views_7d_zero/9)*100:.1f}%)")
    output.append(f"  TODAS as views = 0: {todas_views_zero}/9 ({(todas_views_zero/9)*100:.1f}%)")
    output.append("")

    if views_15d_zero == 9 or views_7d_zero == 9:
        output.append("[PADRAO CRITICO ENCONTRADO!]")
        output.append("TODOS os 9 canais tem views curtas (7d/15d) = 0 na ultima coleta!")
        output.append("Isso sugere que o collector NAO esta conseguindo buscar videos recentes!")
        output.append("")

    # Padrão 6: Tamanho do canal
    output.append("PADRAO 6 - Tamanho do Canal:")
    output.append("")

    pequenos = sum(1 for c in canais_data if c['inscritos'] < 10000)
    medios = sum(1 for c in canais_data if 10000 <= c['inscritos'] < 100000)
    grandes = sum(1 for c in canais_data if c['inscritos'] >= 100000)

    output.append(f"  Pequenos (<10k inscritos): {pequenos}/9 ({(pequenos/9)*100:.1f}%)")
    output.append(f"  Medios (10k-100k): {medios}/9 ({(medios/9)*100:.1f}%)")
    output.append(f"  Grandes (>100k): {grandes}/9 ({(grandes/9)*100:.1f}%)")
    output.append("")

    # Hipótese NOVA: Todos têm views_15d = 0?
    output.append("=" * 100)
    output.append("[3] HIPOTESE NOVA - PROBLEMA COM BUSCA DE VIDEOS:")
    output.append("=" * 100)
    output.append("")

    if views_15d_zero >= 7:  # >77%
        output.append("[HIPOTESE CONFIRMADA]")
        output.append("")
        output.append("PROBLEMA: API do YouTube retorna NENHUM video nos ultimos 15-30 dias")
        output.append("")
        output.append("POSSIVEIS CAUSAS:")
        output.append("1. Collector busca videos com publishedAfter incorreto")
        output.append("2. API throttling especifico para search.list (custa 100 units!)")
        output.append("3. Canal tem poucos videos e publishedAfter ta filtrando demais")
        output.append("4. Timezone issue - publishedAfter usando UTC incorreto")
        output.append("5. Esses canais tem videos mas nao sao publicos/listados")
        output.append("")
        output.append("PROXIMA INVESTIGACAO:")
        output.append("- Testar manualmente busca de videos de The Sharpline")
        output.append("- Ver quantos videos YouTube API retorna")
        output.append("- Comparar com quantos videos existem no canal real")
    else:
        output.append("[HIPOTESE REFUTADA]")
        output.append("Views 15d = 0 nao e padrao comum")

    output.append("")
    output.append("=" * 100)

    return "\n".join(output)


async def main():
    resultado = await investigate_common_pattern()

    # Salvar em arquivo
    with open('RELATORIO_PADROES_COMUNS.txt', 'w', encoding='utf-8') as f:
        f.write(resultado)

    # Exibir no console
    print(resultado.encode('ascii', 'replace').decode('ascii'))
    print("\n\n>>> Relatorio salvo em: RELATORIO_PADROES_COMUNS.txt")


if __name__ == "__main__":
    asyncio.run(main())

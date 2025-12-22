"""
Investigação DETALHADA dos 9 canais que pararam de coletar
"""

import os
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from database import SupabaseClient

load_dotenv()

# Os 9 canais que tinham dados mas zeraram hoje
CANAIS_PROBLEMA = [837, 376, 167, 416, 222, 16, 711, 715]


async def investigar_canais():
    """Investiga cada canal em detalhes"""
    db = SupabaseClient()

    output = []
    output.append("=" * 100)
    output.append("INVESTIGACAO DETALHADA - 9 CANAIS QUE PARARAM DE COLETAR")
    output.append("=" * 100)
    output.append("")

    for i, canal_id in enumerate(CANAIS_PROBLEMA, 1):
        output.append("=" * 100)
        output.append(f"CANAL #{i} - ID: {canal_id}")
        output.append("=" * 100)

        # 1. Buscar dados do canal
        canal_info = db.supabase.table("canais_monitorados")\
            .select("*")\
            .eq("id", canal_id)\
            .execute()

        if not canal_info.data:
            output.append(f"[ERRO] Canal {canal_id} nao encontrado no banco!")
            output.append("")
            continue

        canal = canal_info.data[0]
        nome = canal.get('nome_canal', 'N/A')
        url = canal.get('url_canal', 'N/A')
        status = canal.get('status', 'N/A')
        tipo = canal.get('tipo', 'N/A')
        ultima_coleta = canal.get('ultima_coleta', 'N/A')

        output.append(f"Nome: {nome}")
        output.append(f"URL: {url}")
        output.append(f"Status: {status}")
        output.append(f"Tipo: {tipo}")
        output.append(f"Ultima tentativa de coleta: {ultima_coleta}")
        output.append("")

        # 2. Buscar histórico de coletas (últimos 30 dias)
        trinta_dias_atras = (datetime.now().date() - timedelta(days=30)).isoformat()

        historico = db.supabase.table("dados_canais_historico")\
            .select("*")\
            .eq("canal_id", canal_id)\
            .gte("data_coleta", trinta_dias_atras)\
            .order("data_coleta", desc=True)\
            .execute()

        output.append("HISTORICO DE COLETAS (ultimos 30 dias):")
        if not historico.data:
            output.append("  [!] NENHUMA coleta bem-sucedida nos ultimos 30 dias!")
        else:
            output.append(f"  Total de coletas bem-sucedidas: {len(historico.data)}")
            output.append("")
            output.append("  Ultimas 5 coletas:")
            for j, coleta in enumerate(historico.data[:5], 1):
                data = coleta.get('data_coleta', 'N/A')
                views_30d = coleta.get('views_30d', 0)
                views_15d = coleta.get('views_15d', 0)
                views_7d = coleta.get('views_7d', 0)
                inscritos = coleta.get('inscritos', 0)

                output.append(f"  [{j}] {data}")
                output.append(f"      Views 30d: {views_30d:,}")
                output.append(f"      Views 15d: {views_15d:,}")
                output.append(f"      Views 7d: {views_7d:,}")
                output.append(f"      Inscritos: {inscritos:,}")

        output.append("")

        # 3. Verificar vídeos salvos
        videos = db.supabase.table("videos_historico")\
            .select("video_id, data_coleta")\
            .eq("canal_id", canal_id)\
            .gte("data_coleta", trinta_dias_atras)\
            .execute()

        output.append(f"VIDEOS COLETADOS (ultimos 30 dias): {len(videos.data or [])}")
        output.append("")

        # 4. Analisar padrão de falha
        if historico.data:
            ultima_coleta_sucesso = historico.data[0]
            dias_desde_sucesso = (datetime.now().date() - datetime.fromisoformat(ultima_coleta_sucesso['data_coleta']).date()).days

            output.append("ANALISE:")
            output.append(f"  - Ultima coleta BEM-SUCEDIDA: {ultima_coleta_sucesso['data_coleta']} ({dias_desde_sucesso} dias atras)")
            output.append(f"  - Views na ultima coleta: 30d={ultima_coleta_sucesso.get('views_30d', 0):,}")

            if dias_desde_sucesso == 0:
                output.append("  [!] FALHOU HOJE mas coletava normalmente ate ONTEM!")
                output.append("  [?] Possivel problema TEMPORARIO:")
                output.append("      - Throttling da API do YouTube")
                output.append("      - Canal ficou privado temporariamente")
                output.append("      - Erro de rede pontual")
            elif dias_desde_sucesso <= 3:
                output.append(f"  [!] Parou de coletar ha {dias_desde_sucesso} dias")
                output.append("  [?] Possivel problema:")
                output.append("      - Canal mudou de URL")
                output.append("      - Canal foi suspenso")
                output.append("      - Problema persistente com este canal especifico")
            else:
                output.append(f"  [!!] NAO coleta ha {dias_desde_sucesso} dias!")
                output.append("  [?] Problema CRONICO - verificar:")
                output.append("      - URL pode estar incorreta")
                output.append("      - Canal pode ter sido deletado")
                output.append("      - Canal pode estar privado permanentemente")

        output.append("")

        # 5. Verificar formato da URL
        output.append("ANALISE DA URL:")
        if not url or url == 'N/A':
            output.append("  [ERRO] URL nao cadastrada!")
        elif '@' in url:
            output.append(f"  [OK] URL com handle: {url}")
        elif '/channel/' in url:
            output.append(f"  [OK] URL com channel ID: {url}")
        elif '/c/' in url:
            output.append(f"  [!] URL com custom URL antiga (/c/): {url}")
            output.append("  [?] Pode estar desatualizada - YouTube migrou para @handles")
        else:
            output.append(f"  [?] Formato de URL desconhecido: {url}")

        output.append("")
        output.append("")

    # 6. Análise geral
    output.append("=" * 100)
    output.append("ANALISE GERAL DOS 9 CANAIS:")
    output.append("=" * 100)
    output.append("")

    # Contar quantos têm cada problema
    total_investigados = len(CANAIS_PROBLEMA)
    output.append(f"Total de canais investigados: {total_investigados}")
    output.append("")

    output.append("PROXIMOS PASSOS:")
    output.append("1. Verificar manualmente cada URL no YouTube")
    output.append("2. Atualizar URLs que estiverem incorretas")
    output.append("3. Marcar como 'inativo' canais deletados/privados")
    output.append("4. Retentar coleta manual dos canais ativos")
    output.append("5. Implementar retry automatico para erros temporarios")
    output.append("")

    output.append("=" * 100)

    return "\n".join(output)


async def main():
    resultado = await investigar_canais()

    # Salvar em arquivo
    with open('INVESTIGACAO_9_CANAIS.txt', 'w', encoding='utf-8') as f:
        f.write(resultado)

    # Exibir no console
    print(resultado.encode('ascii', 'replace').decode('ascii'))
    print("\n\n>>> Relatorio salvo em: INVESTIGACAO_9_CANAIS.txt")


if __name__ == "__main__":
    asyncio.run(main())

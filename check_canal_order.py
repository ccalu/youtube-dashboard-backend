"""
Verifica ordem de coleta dos canais e identifica posição dos 9 problemáticos
"""

import os
import asyncio
from dotenv import load_dotenv
from database import SupabaseClient

load_dotenv()

# Os 9 canais problemáticos
CANAIS_PROBLEMA = [837, 376, 167, 416, 222, 16, 711, 715]

async def check_canal_order():
    """Verifica ordem de coleta"""
    db = SupabaseClient()

    output = []
    output.append("=" * 100)
    output.append("ANALISE DA ORDEM DE COLETA")
    output.append("=" * 100)
    output.append("")

    # Buscar TODOS os canais ativos na ORDEM que são coletados
    canais = db.supabase.table("canais_monitorados")\
        .select("id, nome_canal, tipo, status")\
        .eq("status", "ativo")\
        .order("id", desc=False)\
        .execute()

    total = len(canais.data)
    output.append(f"[1] TOTAL DE CANAIS ATIVOS: {total}")
    output.append("")

    # Encontrar posição de cada canal problemático
    output.append("[2] POSICAO DOS 9 CANAIS PROBLEMATICOS NA FILA:")
    output.append("")

    problematicos_info = []

    for idx, canal in enumerate(canais.data, 1):
        canal_id = canal.get('id')

        if canal_id in CANAIS_PROBLEMA:
            nome = canal.get('nome_canal', 'N/A')
            tipo = canal.get('tipo', 'N/A')

            problematicos_info.append({
                'id': canal_id,
                'nome': nome,
                'posicao': idx,
                'tipo': tipo,
                'percentual': (idx / total) * 100
            })

    # Ordenar por posição
    problematicos_info.sort(key=lambda x: x['posicao'])

    for info in problematicos_info:
        output.append(f"Canal ID {info['id']:3d} - Posicao {info['posicao']:3d}/{total} ({info['percentual']:5.1f}%) - {info['nome']}")

    output.append("")

    # Análise estatística
    output.append("=" * 100)
    output.append("[3] ANALISE ESTATISTICA:")
    output.append("=" * 100)
    output.append("")

    posicoes = [p['posicao'] for p in problematicos_info]

    output.append(f"Posicao minima: {min(posicoes)}/{total} ({(min(posicoes)/total)*100:.1f}%)")
    output.append(f"Posicao maxima: {max(posicoes)}/{total} ({(max(posicoes)/total)*100:.1f}%)")
    output.append(f"Posicao media: {sum(posicoes)/len(posicoes):.1f}/{total} ({(sum(posicoes)/len(posicoes)/total)*100:.1f}%)")
    output.append("")

    # Verificar hipótese: canais problemáticos estão depois de 300?
    depois_300 = sum(1 for p in posicoes if p > 300)
    antes_300 = len(posicoes) - depois_300

    output.append(f"Canais ANTES da posicao 300: {antes_300}/9 ({(antes_300/9)*100:.1f}%)")
    output.append(f"Canais DEPOIS da posicao 300: {depois_300}/9 ({(depois_300/9)*100:.1f}%)")
    output.append("")

    if depois_300 > 6:  # >66%
        output.append("[CONFIRMADO] Maioria (>66%) dos canais problematicos esta DEPOIS de 300!")
        output.append("            Hipotese do rate limiting CONFIRMADA!")
    elif depois_300 > 4:  # >50%
        output.append("[PROVAVEL] Maioria dos canais problematicos esta DEPOIS de 300")
        output.append("           Hipotese do rate limiting PROVAVEL")
    else:
        output.append("[REFUTADA] Canais problematicos NAO estao concentrados depois de 300")
        output.append("           Causa raiz pode ser OUTRA!")

    output.append("")

    # Listar primeiros 20 e últimos 20 canais
    output.append("=" * 100)
    output.append("[4] PRIMEIROS 20 CANAIS NA FILA:")
    output.append("=" * 100)
    output.append("")

    for idx, canal in enumerate(canais.data[:20], 1):
        canal_id = canal.get('id')
        nome = canal.get('nome_canal', 'N/A')
        status_str = " [PROBLEMA]" if canal_id in CANAIS_PROBLEMA else ""
        output.append(f"  {idx:3d}. Canal ID {canal_id:3d} - {nome}{status_str}")

    output.append("")
    output.append("=" * 100)
    output.append("[5] ULTIMOS 20 CANAIS NA FILA:")
    output.append("=" * 100)
    output.append("")

    for idx, canal in enumerate(canais.data[-20:], total - 19):
        canal_id = canal.get('id')
        nome = canal.get('nome_canal', 'N/A')
        status_str = " [PROBLEMA]" if canal_id in CANAIS_PROBLEMA else ""
        output.append(f"  {idx:3d}. Canal ID {canal_id:3d} - {nome}{status_str}")

    output.append("")
    output.append("=" * 100)

    return "\n".join(output)


async def main():
    resultado = await check_canal_order()

    # Salvar em arquivo
    with open('RELATORIO_ORDEM_COLETA.txt', 'w', encoding='utf-8') as f:
        f.write(resultado)

    # Exibir no console (sem Unicode)
    print(resultado.encode('ascii', 'replace').decode('ascii'))
    print("\n\n>>> Relatorio salvo em: RELATORIO_ORDEM_COLETA.txt")


if __name__ == "__main__":
    asyncio.run(main())

"""
Lista SIMPLES dos canais sem comentários
"""
import asyncio
import os
from dotenv import load_dotenv
from database import SupabaseClient

# Carregar variáveis
load_dotenv()

async def main():
    print("\n" + "="*80)
    print("CANAIS SEM COMENTÁRIOS - LISTA COMPLETA")
    print("="*80)

    db = SupabaseClient()

    # Buscar TODOS os canais tipo="nosso" ativos
    canais_nosso = db.supabase.table('canais_monitorados')\
        .select('*')\
        .eq('tipo', 'nosso')\
        .eq('status', 'ativo')\
        .execute()

    print(f"\nTotal de canais tipo='nosso' ativos: {len(canais_nosso.data)}")

    # Buscar TODOS os comentários usando paginação
    all_comments = await db.fetch_all_records(
        table='video_comments',
        select_fields='canal_id'
    )

    print(f"Total de comentários no banco: {len(all_comments)}")

    # Identificar canais únicos com comentários
    canais_com_comentarios = set()
    for c in all_comments:
        if c.get('canal_id'):
            canais_com_comentarios.add(c['canal_id'])

    print(f"Canais com pelo menos 1 comentário: {len(canais_com_comentarios)}")

    # Filtrar canais SEM comentários
    canais_sem_comentarios = []
    for canal in canais_nosso.data:
        if canal['id'] not in canais_com_comentarios:
            # Buscar dados do histórico
            historico = db.supabase.table('dados_canais_historico')\
                .select('inscritos')\
                .eq('canal_id', canal['id'])\
                .order('data_coleta', desc=True)\
                .limit(1)\
                .execute()

            if historico.data:
                canal['inscritos'] = historico.data[0].get('inscritos', 0)
            else:
                canal['inscritos'] = 0

            canais_sem_comentarios.append(canal)

    print(f"\n" + "="*80)
    print(f"18 CANAIS SEM NENHUM COMENTÁRIO:")
    print("="*80)

    if not canais_sem_comentarios:
        print("\n✓ TODOS os canais têm pelo menos 1 comentário!")
        return

    # Ordenar por inscritos (maior primeiro)
    canais_sem_comentarios.sort(key=lambda x: x.get('inscritos', 0), reverse=True)

    # Listar todos com detalhes
    for i, canal in enumerate(canais_sem_comentarios, 1):
        nome = canal['nome_canal']
        url = canal.get('url_canal', 'N/A')
        inscritos = canal.get('inscritos', 0)
        videos_coletados = canal.get('videos_coletados', 0)
        subnicho = canal.get('subnicho', 'N/A')
        lingua = canal.get('lingua', 'N/A')

        print(f"\n{i:2}. {nome}")
        print(f"    URL: {url}")
        print(f"    Inscritos: {inscritos:,}")
        print(f"    Vídeos coletados: {videos_coletados}")
        print(f"    Subnicho: {subnicho}")
        print(f"    Língua: {lingua}")

    # Análise por faixa de inscritos
    print("\n" + "="*80)
    print("ANÁLISE POR FAIXA DE INSCRITOS:")
    print("="*80)

    faixas = {
        "0 inscritos": [],
        "1-100 inscritos": [],
        "101-1000 inscritos": [],
        "1000+ inscritos": []
    }

    for canal in canais_sem_comentarios:
        inscritos = canal.get('inscritos', 0)
        if inscritos == 0:
            faixas["0 inscritos"].append(canal)
        elif inscritos <= 100:
            faixas["1-100 inscritos"].append(canal)
        elif inscritos <= 1000:
            faixas["101-1000 inscritos"].append(canal)
        else:
            faixas["1000+ inscritos"].append(canal)

    for faixa, canais in faixas.items():
        if canais:
            print(f"\n{faixa}: {len(canais)} canais")
            for canal in canais[:3]:  # Mostrar até 3 exemplos
                print(f"  • {canal['nome_canal']} ({canal.get('inscritos', 0)} inscritos)")

    # Destacar canais problemáticos (muitos inscritos mas sem comentários)
    problematicos = [c for c in canais_sem_comentarios if c.get('inscritos', 0) > 1000]
    if problematicos:
        print("\n" + "="*80)
        print(f"⚠️ ATENÇÃO: {len(problematicos)} CANAIS COM 1000+ INSCRITOS SEM COMENTÁRIOS:")
        print("="*80)
        for canal in problematicos:
            print(f"\n  • {canal['nome_canal']}")
            print(f"    Inscritos: {canal.get('inscritos', 0):,}")
            print(f"    Vídeos coletados: {canal.get('videos_coletados', 0)}")
            print(f"    URL: {canal.get('url_canal', 'N/A')}")

    print("\n" + "="*80)
    print("CONCLUSÃO:")
    print("="*80)
    print(f"\nDos {len(canais_sem_comentarios)} canais sem comentários:")

    # Contar por categoria
    novos = len([c for c in canais_sem_comentarios if c.get('inscritos', 0) <= 100])
    pequenos = len([c for c in canais_sem_comentarios if 100 < c.get('inscritos', 0) <= 1000])
    grandes = len([c for c in canais_sem_comentarios if c.get('inscritos', 0) > 1000])

    if novos > 0:
        print(f"  • {novos} são canais muito novos (≤100 inscritos)")
    if pequenos > 0:
        print(f"  • {pequenos} são canais pequenos (101-1000 inscritos)")
    if grandes > 0:
        print(f"  • {grandes} são canais maiores (>1000 inscritos) - VERIFICAR!")

    # Salvar relatório
    with open('canais_sem_comentarios.txt', 'w', encoding='utf-8') as f:
        f.write(f"CANAIS SEM COMENTÁRIOS - LISTA COMPLETA\n")
        f.write(f"{'='*80}\n\n")
        f.write(f"Total de canais tipo='nosso': {len(canais_nosso.data)}\n")
        f.write(f"Canais COM comentários: {len(canais_com_comentarios)}\n")
        f.write(f"Canais SEM comentários: {len(canais_sem_comentarios)}\n\n")

        for i, canal in enumerate(canais_sem_comentarios, 1):
            f.write(f"{i}. {canal['nome_canal']}\n")
            f.write(f"   URL: {canal.get('url_canal', 'N/A')}\n")
            f.write(f"   Inscritos: {canal.get('inscritos', 0):,}\n")
            f.write(f"   Vídeos coletados: {canal.get('videos_coletados', 0)}\n\n")

    print(f"\n✓ Relatório salvo em: canais_sem_comentarios.txt")

if __name__ == "__main__":
    asyncio.run(main())
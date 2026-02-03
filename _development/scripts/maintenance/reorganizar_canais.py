"""
Script para reorganizar canais nossos
Data: 30/01/2026
Autor: Claude Code

Este script:
1. Move 2 canais para Desmonetizados
2. Mantém apenas os canais especificados
3. Exclui todos os outros canais nossos
"""

import asyncio
import json
import sys
import io
from datetime import datetime
from dotenv import load_dotenv
from database import SupabaseClient
import os

# Configurar encoding UTF-8 para Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

load_dotenv()

# Canais para MANTER (não deletar) - usando nomes exatos do banco
CANAIS_MANTER = {
    'Monetizados': [
        'Reinos Sombrios',
        'Archives de Guerre',
        'Mistérios da Realeza (new)',  # Nome correto
        '王の影 (new)',  # Nome correto
        '古代の物語',
        'Tales of Antiquity',
        'Archived Mysteries',
        'Mistérios Arquivados'
    ],
    'Relatos de Guerra': [
        'Memorie di Guerra',
        'WWII Erzählungen'
    ],
    'Historias Sombrias': [
        'Sombras del Trono (new)'  # Nome correto
    ],
    'Terror': [
        'Grandes Mansões'
    ]
}

# Canais para MOVER para Desmonetizados
CANAIS_MOVER_DESMONETIZADO = [
    '그림자의 왕국',  # Era Monetizado
    'Sombras da História'  # Era Monetizado
]

async def main():
    print("=" * 70)
    print("REORGANIZAÇÃO DOS CANAIS NOSSOS")
    print("=" * 70)
    print("\n⚠️  AVISO: Esta operação é IRREVERSÍVEL!")
    print("Canais não listados serão PERMANENTEMENTE deletados.\n")

    db = SupabaseClient()

    # 1. Buscar todos os canais nossos
    print("1. Buscando todos os canais nossos...")
    print("-" * 40)

    nossos = db.supabase.table("canais_monitorados")\
        .select("id, nome_canal, subnicho")\
        .eq("tipo", "nosso")\
        .execute()

    if not nossos.data:
        print("❌ Nenhum canal nosso encontrado!")
        return

    todos_canais = nossos.data
    print(f"✅ Encontrados {len(todos_canais)} canais nossos\n")

    # 2. Mover canais para Desmonetizados
    print("2. Movendo canais para Desmonetizados...")
    print("-" * 40)

    for nome_canal in CANAIS_MOVER_DESMONETIZADO:
        # Buscar o canal
        canal = next((c for c in todos_canais if c['nome_canal'] == nome_canal), None)

        if canal:
            try:
                # Atualizar subnicho (sem updated_at que não existe)
                db.supabase.table("canais_monitorados").update({
                    "subnicho": "Desmonetizados"
                }).eq("id", canal['id']).execute()

                print(f"✅ {nome_canal} movido para Desmonetizados")

                # Atualizar na lista local
                canal['subnicho'] = 'Desmonetizados'
            except Exception as e:
                print(f"❌ Erro ao mover {nome_canal}: {e}")
        else:
            print(f"⚠️  Canal '{nome_canal}' não encontrado")

    # 3. Identificar canais Desmonetizados existentes
    print("\n3. Identificando canais Desmonetizados existentes...")
    print("-" * 40)

    desmonetizados = [c for c in todos_canais if c['subnicho'] == 'Desmonetizados']
    print(f"✅ {len(desmonetizados)} canais em Desmonetizados (incluindo os movidos)\n")

    # 4. Preparar lista de canais para manter
    print("4. Preparando lista de canais para MANTER...")
    print("-" * 40)

    canais_manter_ids = []
    canais_manter_nomes = []

    # Adicionar canais especificados para manter
    for subnicho, nomes in CANAIS_MANTER.items():
        for nome in nomes:
            canal = next((c for c in todos_canais if c['nome_canal'] == nome), None)
            if canal:
                canais_manter_ids.append(canal['id'])
                canais_manter_nomes.append(canal['nome_canal'])
                print(f"✅ Mantendo: {canal['nome_canal']} ({subnicho})")
            else:
                print(f"⚠️  Canal '{nome}' não encontrado")

    # Adicionar TODOS os Desmonetizados (incluindo os recém-movidos)
    for canal in desmonetizados:
        if canal['id'] not in canais_manter_ids:
            canais_manter_ids.append(canal['id'])
            canais_manter_nomes.append(canal['nome_canal'])
            print(f"✅ Mantendo: {canal['nome_canal']} (Desmonetizados)")

    print(f"\n📊 Total de canais para MANTER: {len(canais_manter_ids)}")

    # 5. Identificar canais para EXCLUIR
    print("\n5. Identificando canais para EXCLUIR...")
    print("-" * 40)

    canais_excluir = [c for c in todos_canais if c['id'] not in canais_manter_ids]

    if not canais_excluir:
        print("✅ Nenhum canal para excluir!")
        return

    print(f"⚠️  {len(canais_excluir)} canais serão EXCLUÍDOS:")
    for canal in canais_excluir:
        print(f"   ❌ [{canal['id']:4}] {canal['nome_canal']:30} - {canal['subnicho']}")

    # 6. Criar backup
    print("\n6. Criando backup...")
    print("-" * 40)

    backup_file = f"backup_reorganizacao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    backup_data = {
        "data_reorganizacao": datetime.now().isoformat(),
        "total_antes": len(todos_canais),
        "total_mantidos": len(canais_manter_ids),
        "total_excluidos": len(canais_excluir),
        "canais_mantidos": canais_manter_nomes,
        "canais_excluidos": canais_excluir,
        "canais_movidos": CANAIS_MOVER_DESMONETIZADO,
        "todos_canais_antes": todos_canais
    }

    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Backup salvo em: {backup_file}")

    # 7. Confirmar exclusão
    print("\n" + "=" * 70)
    print("RESUMO DA OPERAÇÃO:")
    print("=" * 70)
    print(f"✅ Canais para MANTER: {len(canais_manter_ids)}")
    print(f"❌ Canais para EXCLUIR: {len(canais_excluir)}")
    print("=" * 70)

    # Verificar se foi passado --confirm
    if '--confirm' in sys.argv:
        print("\n✅ Confirmação automática via --confirm")
        resposta = "SIM"
    else:
        resposta = input("\n🔴 Tem certeza que deseja EXCLUIR PERMANENTEMENTE os canais? (digite 'SIM' para confirmar): ")

    if resposta != "SIM":
        print("\n❌ Operação cancelada.")
        return

    # 8. Executar exclusões
    print("\n8. Executando exclusões...")
    print("-" * 40)

    sucesso = 0
    erros = []

    for i, canal in enumerate(canais_excluir, 1):
        try:
            print(f"\n[{i}/{len(canais_excluir)}] Excluindo {canal['nome_canal']}...")

            # Contar dados antes
            videos = db.supabase.table("videos_historico")\
                .select("video_id", count="exact")\
                .eq("canal_id", canal['id'])\
                .execute()

            total_videos = videos.count if hasattr(videos, 'count') else 0
            print(f"   - Deletando {total_videos} vídeos e dados relacionados...")

            # Deletar permanentemente
            await db.delete_canal_permanently(canal['id'])

            print(f"   ✅ Canal {canal['id']} excluído com sucesso!")
            sucesso += 1

        except Exception as e:
            print(f"   ❌ Erro ao excluir: {e}")
            erros.append({
                "canal": canal['nome_canal'],
                "erro": str(e)
            })

    # 9. Relatório final
    print("\n" + "=" * 70)
    print("RELATÓRIO FINAL")
    print("=" * 70)
    print(f"✅ Canais excluídos com sucesso: {sucesso}/{len(canais_excluir)}")

    if erros:
        print(f"\n❌ Erros ({len(erros)}):")
        for erro in erros:
            print(f"   - {erro['canal']}: {erro['erro']}")

    # 10. Verificar estado final
    print("\n10. Verificando estado final...")
    print("-" * 40)

    # Recontar canais nossos
    nossos_final = db.supabase.table("canais_monitorados")\
        .select("id, nome_canal, subnicho", count="exact")\
        .eq("tipo", "nosso")\
        .execute()

    print(f"📊 Total de canais nossos agora: {nossos_final.count if hasattr(nossos_final, 'count') else 0}")

    # Contar por subnicho
    if nossos_final.data:
        subnichos_count = {}
        for canal in nossos_final.data:
            sub = canal.get('subnicho', 'Sem subnicho')
            subnichos_count[sub] = subnichos_count.get(sub, 0) + 1

        print("\nDistribuição por subnicho:")
        for sub, count in sorted(subnichos_count.items()):
            print(f"   - {sub}: {count} canais")

    print("\n✅ REORGANIZAÇÃO CONCLUÍDA!")
    print(f"📁 Backup salvo em: {backup_file}")
    print("\n⚠️  LEMBRETE: O cache/MV pode mostrar dados antigos por até 6h")

if __name__ == "__main__":
    asyncio.run(main())
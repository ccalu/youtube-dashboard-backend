"""
Script para marcar 4 canais como desmonetizados
Canais: 그림자의 왕국, Reinos Sombrios, Sombras da História, 古代の物語
"""

import sys
import io
from database import SupabaseClient
from dotenv import load_dotenv

# Fix encoding Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Carregar variáveis de ambiente
load_dotenv()

def marcar_desmonetizados():
    """Marca os 4 canais como desmonetizados"""

    print("=" * 80)
    print("MARCANDO CANAIS COMO DESMONETIZADOS")
    print("=" * 80)

    # Canais a atualizar
    canais_desmonetizar = [
        "그림자의 왕국",
        "Reinos Sombrios",
        "Sombras da História",
        "古代の物語"
    ]

    print("\n📋 Canais a marcar como desmonetizados:")
    for canal in canais_desmonetizar:
        print(f"   - {canal}")

    # Inicializar banco
    db = SupabaseClient()

    atualizados = []
    nao_encontrados = []

    print("\n🔍 Buscando e atualizando canais...")

    for nome_canal in canais_desmonetizar:
        print(f"\n[{nome_canal}]")

        # Buscar canal no banco
        result = db.supabase.table("canais_monitorados")\
            .select("*")\
            .eq("nome_canal", nome_canal)\
            .execute()

        if not result.data:
            # Tentar busca parcial se não encontrar exato
            result = db.supabase.table("canais_monitorados")\
                .select("*")\
                .ilike("nome_canal", f"%{nome_canal}%")\
                .execute()

        if result.data:
            canal = result.data[0]
            canal_id = canal['id']
            print(f"   ✅ Encontrado: ID {canal_id}")
            print(f"      Tipo: {canal.get('tipo')}")
            print(f"      Subnicho atual: {canal.get('subnicho')}")
            print(f"      Monetizado atual: {canal.get('monetizado')}")

            # Atualizar para desmonetizado
            print(f"   🔄 Atualizando para desmonetizado...")
            try:
                update_result = db.supabase.table("canais_monitorados")\
                    .update({
                        "subnicho": "Desmonetizados",
                        "monetizado": False
                    })\
                    .eq("id", canal_id)\
                    .execute()

                if update_result.data:
                    print(f"   ✅ Canal atualizado com sucesso!")
                    atualizados.append({
                        'nome': canal['nome_canal'],
                        'id': canal_id,
                        'subnicho_antigo': canal.get('subnicho')
                    })
            except Exception as e:
                print(f"   ❌ Erro ao atualizar: {e}")
        else:
            print(f"   ❌ Canal não encontrado no banco")
            nao_encontrados.append(nome_canal)

    # Resumo final
    print("\n" + "=" * 80)
    print("RESUMO DA ATUALIZAÇÃO")
    print("=" * 80)

    if atualizados:
        print(f"\n✅ ATUALIZADOS COM SUCESSO ({len(atualizados)}):")
        for a in atualizados:
            print(f"   - {a['nome']} (ID: {a['id']})")
            print(f"     Subnicho anterior: {a['subnicho_antigo']} → Desmonetizados")

    if nao_encontrados:
        print(f"\n❌ NÃO ENCONTRADOS ({len(nao_encontrados)}):")
        for n in nao_encontrados:
            print(f"   - {n}")

    # Verificar atualização
    print("\n🔍 Verificando atualizações...")
    for nome_canal in canais_desmonetizar:
        check = db.supabase.table("canais_monitorados")\
            .select("nome_canal, subnicho, monetizado")\
            .eq("nome_canal", nome_canal)\
            .execute()

        if not check.data:
            check = db.supabase.table("canais_monitorados")\
                .select("nome_canal, subnicho, monetizado")\
                .ilike("nome_canal", f"%{nome_canal}%")\
                .execute()

        if check.data:
            c = check.data[0]
            if c['subnicho'] == 'Desmonetizados' and not c.get('monetizado', True):
                print(f"   ✅ {c['nome_canal']}: Desmonetizado com sucesso")
            else:
                print(f"   ⚠️ {c['nome_canal']}: Subnicho={c['subnicho']}, Monetizado={c.get('monetizado')}")
        else:
            print(f"   ❌ {nome_canal}: Não encontrado")

    # Contar canais desmonetizados
    print("\n📊 ESTATÍSTICAS:")
    desmonetizados = db.supabase.table('canais_monitorados')\
        .select('id', count='exact')\
        .eq('status', 'ativo')\
        .eq('subnicho', 'Desmonetizados')\
        .execute()

    nossos = db.supabase.table('canais_monitorados')\
        .select('id', count='exact')\
        .eq('status', 'ativo')\
        .eq('tipo', 'nosso')\
        .execute()

    print(f"   Total de canais desmonetizados: {desmonetizados.count}")
    print(f"   Total de canais nossos: {nossos.count}")

    print("\n" + "=" * 80)
    print("✅ PROCESSO CONCLUÍDO!")
    print("=" * 80)

if __name__ == "__main__":
    marcar_desmonetizados()
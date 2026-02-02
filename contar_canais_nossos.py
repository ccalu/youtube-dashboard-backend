"""
Script para contar exatamente quantos canais "nossos" existem
"""

import sys
import io
from database import SupabaseClient
from dotenv import load_dotenv

# Fix encoding Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Carregar variáveis de ambiente
load_dotenv()

def contar_canais():
    """Conta canais nossos ativos"""

    # Inicializar banco
    db = SupabaseClient()

    print("=" * 60)
    print("CONTAGEM DE CANAIS NOSSOS")
    print("=" * 60)

    # Contar canais nossos ativos
    nossos_ativos = db.supabase.table('canais_monitorados')\
        .select('id, nome_canal, lingua', count='exact')\
        .eq('tipo', 'nosso')\
        .eq('status', 'ativo')\
        .execute()

    print(f"\n✅ Canais NOSSOS ATIVOS: {nossos_ativos.count}")

    # Contar todos os canais nossos (incluindo inativos)
    nossos_total = db.supabase.table('canais_monitorados')\
        .select('id', count='exact')\
        .eq('tipo', 'nosso')\
        .execute()

    print(f"📊 Canais NOSSOS TOTAL (incluindo inativos): {nossos_total.count}")

    # Listar por língua
    print("\n🌍 DISTRIBUIÇÃO POR LÍNGUA:")
    linguas = {}
    for canal in nossos_ativos.data:
        lingua = canal.get('lingua', 'não definida')
        linguas[lingua] = linguas.get(lingua, 0) + 1

    for lingua, count in sorted(linguas.items(), key=lambda x: x[1], reverse=True):
        print(f"   {lingua}: {count} canais")

    # Contar comentários pendentes desses canais
    print("\n💬 COMENTÁRIOS PENDENTES DE TRADUÇÃO:")
    total_pendentes = 0
    canais_com_pendentes = 0

    for canal in nossos_ativos.data:
        pendentes = db.supabase.table('video_comments')\
            .select('id', count='exact')\
            .eq('canal_id', canal['id'])\
            .eq('is_translated', False)\
            .execute()

        if pendentes.count > 0:
            canais_com_pendentes += 1
            total_pendentes += pendentes.count

    print(f"   Canais com comentários pendentes: {canais_com_pendentes}")
    print(f"   Total de comentários pendentes: {total_pendentes}")

    print("\n" + "=" * 60)
    print(f"RESUMO: {nossos_ativos.count} canais nossos ativos")
    print("=" * 60)

if __name__ == "__main__":
    contar_canais()
"""
Script para traduzir comentários de um canal específico
Foca no canal WWII Erzählungen (ID: 895) para teste
"""

import asyncio
import sys
import os
import io
from database import SupabaseClient
from translate_comments_optimized import OptimizedTranslator
from dotenv import load_dotenv

# Fix encoding Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Carregar variáveis de ambiente
load_dotenv()

async def traduzir_canal_especifico(canal_id=895):
    """Traduz comentários de um canal específico"""

    print("=" * 80)
    print(f"TRADUÇÃO DE COMENTÁRIOS - CANAL ID {canal_id}")
    print("=" * 80)

    # Inicializar
    db = SupabaseClient()
    translator = OptimizedTranslator()

    # Buscar informações do canal
    canal_info = db.supabase.table('canais_monitorados')\
        .select('nome_canal, lingua')\
        .eq('id', canal_id)\
        .execute()

    if not canal_info.data:
        print(f"❌ Canal {canal_id} não encontrado!")
        return

    info = canal_info.data[0]
    print(f"\n📂 Canal: {info['nome_canal']}")
    print(f"🌍 Língua: {info.get('lingua', 'unknown')}")

    # Buscar comentários não traduzidos deste canal
    print(f"\n📊 Buscando comentários não traduzidos...")

    response = db.supabase.table('video_comments')\
        .select('id, comment_text_original, comment_text_pt')\
        .eq('canal_id', canal_id)\
        .eq('is_translated', False)\
        .limit(10)\
        .execute()

    if not response.data:
        print("✅ Nenhum comentário pendente de tradução!")
        return

    comentarios = response.data
    print(f"📝 {len(comentarios)} comentários encontrados para tradução")

    # Mostrar exemplos antes de traduzir
    print("\n📖 EXEMPLOS DE COMENTÁRIOS ORIGINAIS:")
    for i, c in enumerate(comentarios[:3], 1):
        print(f"\n   {i}. {c['comment_text_original'][:150]}...")

    # Traduzir em batch
    print("\n⏳ Iniciando tradução com GPT-4 Mini...")

    textos_originais = [c['comment_text_original'] for c in comentarios]

    try:
        # Traduzir batch
        print(f"   Traduzindo {len(textos_originais)} comentários...")
        textos_traduzidos = await translator.translate_batch(textos_originais)

        print(f"   ✅ Tradução concluída! Recebidos {len(textos_traduzidos)} textos traduzidos")

        # Atualizar no banco
        atualizados = 0
        for i, comentario in enumerate(comentarios):
            if i < len(textos_traduzidos):
                texto_traduzido = textos_traduzidos[i]

                # Atualizar no banco
                update_response = db.supabase.table('video_comments')\
                    .update({
                        'comment_text_pt': texto_traduzido,
                        'is_translated': True
                    })\
                    .eq('id', comentario['id'])\
                    .execute()

                if update_response.data:
                    atualizados += 1

                    # Mostrar primeiro exemplo traduzido
                    if atualizados <= 3:
                        print(f"\n   ✅ Tradução {atualizados}:")
                        print(f"      DE: {comentario['comment_text_original'][:100]}...")
                        print(f"      PT: {texto_traduzido[:100]}...")

        print(f"\n✅ {atualizados} comentários atualizados no banco!")

    except Exception as e:
        print(f"\n❌ Erro ao traduzir: {e}")
        import traceback
        traceback.print_exc()
        return

    # Verificar resultado
    print("\n🔍 VERIFICANDO TRADUÇÃO NO BANCO...")

    check = db.supabase.table('video_comments')\
        .select('comment_text_original, comment_text_pt, is_translated')\
        .eq('canal_id', canal_id)\
        .eq('is_translated', True)\
        .limit(3)\
        .execute()

    if check.data:
        print("\n📝 Comentários traduzidos no banco:")
        for i, c in enumerate(check.data, 1):
            print(f"\n   {i}. Original: {c['comment_text_original'][:80]}...")
            print(f"      PT-BR: {c['comment_text_pt'][:80]}...")
            print(f"      Status: {'✅ Traduzido' if c['is_translated'] else '❌'}")

    print("\n" + "=" * 80)
    print("✅ PROCESSO CONCLUÍDO!")
    print("=" * 80)
    print("\n💡 Verifique no dashboard se os comentários do canal aparecem em PT-BR agora!")

if __name__ == "__main__":
    print("\n🎯 Canal: WWII Erzählungen (ID: 895)")
    print("⚠️ Este script usa OpenAI API (GPT-4 Mini)")
    print("\nIniciando em 3 segundos...\n")

    import time
    time.sleep(3)

    asyncio.run(traduzir_canal_especifico(895))  # WWII Erzählungen
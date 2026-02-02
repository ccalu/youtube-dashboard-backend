"""
Script para traduzir comentários pendentes usando GPT-4 Mini
Traduz comentários que estão em língua original para PT-BR
"""

import asyncio
import sys
import os
import io
from datetime import datetime
from database import SupabaseClient
from translate_comments_optimized import OptimizedTranslator
from dotenv import load_dotenv
import json

# Fix encoding Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Carregar variáveis de ambiente
load_dotenv()

async def traduzir_comentarios_pendentes():
    """Traduz comentários que ainda não foram traduzidos"""

    print("=" * 80)
    print("TRADUÇÃO DE COMENTÁRIOS PENDENTES")
    print("=" * 80)

    # Inicializar
    db = SupabaseClient()
    translator = OptimizedTranslator()

    # Buscar comentários não traduzidos
    print("\n📊 Buscando comentários não traduzidos...")

    # Buscar comentários onde is_translated = False ou comment_text_pt = comment_text_original
    response = db.supabase.table('video_comments')\
        .select('id, comment_id, comment_text_original, comment_text_pt, is_translated, canal_id, video_id')\
        .eq('is_translated', False)\
        .limit(100)\
        .execute()

    if not response.data:
        print("✅ Nenhum comentário pendente de tradução!")
        return

    comentarios = response.data
    total = len(comentarios)

    print(f"📝 {total} comentários encontrados para tradução")

    # Agrupar por canal para melhor visualização
    canais_ids = list(set([c['canal_id'] for c in comentarios]))

    print(f"\n📂 Canais com comentários pendentes: {len(canais_ids)}")

    # Buscar nomes dos canais
    canais_info = {}
    for canal_id in canais_ids[:5]:  # Limitar a 5 canais para teste
        canal_response = db.supabase.table('canais_monitorados')\
            .select('nome_canal, lingua')\
            .eq('id', canal_id)\
            .execute()

        if canal_response.data:
            canais_info[canal_id] = canal_response.data[0]

    # Processar comentários por canal
    traduzidos = 0
    erros = 0

    for canal_id, info in canais_info.items():
        canal_comentarios = [c for c in comentarios if c['canal_id'] == canal_id]

        print(f"\n🎯 Canal: {info['nome_canal']} ({info.get('lingua', 'unknown')})")
        print(f"   Comentários a traduzir: {len(canal_comentarios)}")

        # Processar em lotes de 20
        batch_size = 20
        for i in range(0, len(canal_comentarios), batch_size):
            batch = canal_comentarios[i:i+batch_size]

            print(f"\n   📦 Processando lote {i//batch_size + 1} ({len(batch)} comentários)...")

            # Extrair textos
            textos_originais = [c['comment_text_original'] for c in batch]

            # Mostrar exemplos
            if i == 0 and textos_originais:
                print(f"   📝 Exemplo original: {textos_originais[0][:100]}...")

            try:
                # Traduzir batch
                print("   ⏳ Traduzindo com GPT-4 Mini...")
                textos_traduzidos = await translator.translate_batch(textos_originais)

                # Atualizar no banco
                for j, comentario in enumerate(batch):
                    if j < len(textos_traduzidos):
                        texto_traduzido = textos_traduzidos[j]

                        # Só atualizar se a tradução for diferente do original
                        if texto_traduzido and texto_traduzido != comentario['comment_text_original']:
                            update_response = db.supabase.table('video_comments')\
                                .update({
                                    'comment_text_pt': texto_traduzido,
                                    'is_translated': True
                                })\
                                .eq('id', comentario['id'])\
                                .execute()

                            if update_response.data:
                                traduzidos += 1

                                # Mostrar primeiro exemplo traduzido
                                if traduzidos == 1:
                                    print(f"   ✅ Exemplo traduzido: {texto_traduzido[:100]}...")
                        else:
                            # Texto já em português ou tradução falhou
                            print(f"   ⚠️ Comentário {j+1}: Já em PT ou tradução idêntica")

                print(f"   ✅ Lote processado: {traduzidos} traduzidos até agora")

            except Exception as e:
                print(f"   ❌ Erro ao traduzir lote: {e}")
                erros += len(batch)
                continue

    # Resumo final
    print("\n" + "=" * 80)
    print("RESUMO DA TRADUÇÃO")
    print("=" * 80)

    print(f"\n📊 ESTATÍSTICAS:")
    print(f"   Total processado: {traduzidos + erros}")
    print(f"   ✅ Traduzidos com sucesso: {traduzidos}")
    print(f"   ❌ Erros: {erros}")

    if traduzidos > 0:
        print(f"\n💰 CUSTO ESTIMADO:")
        # GPT-4 Mini: $0.15/1M input, $0.60/1M output
        # Estimativa: ~100 tokens por comentário (input) + 100 tokens (output)
        tokens_total = traduzidos * 200
        custo_estimado = (tokens_total / 1_000_000) * 0.30  # Média entre input e output
        print(f"   Tokens usados: ~{tokens_total:,}")
        print(f"   Custo: ~${custo_estimado:.4f}")

    # Verificar um exemplo específico
    if traduzidos > 0:
        print("\n🔍 VERIFICANDO TRADUÇÃO NO BANCO...")

        # Buscar um comentário traduzido
        check = db.supabase.table('video_comments')\
            .select('comment_text_original, comment_text_pt, is_translated')\
            .eq('is_translated', True)\
            .limit(1)\
            .execute()

        if check.data:
            exemplo = check.data[0]
            print(f"   Original: {exemplo['comment_text_original'][:100]}...")
            print(f"   Traduzido: {exemplo['comment_text_pt'][:100]}...")
            print(f"   Status: {'✅ Traduzido' if exemplo['is_translated'] else '❌ Não traduzido'}")

    print("\n✅ PROCESSO CONCLUÍDO!")
    print("\n💡 PRÓXIMOS PASSOS:")
    print("1. Verificar no dashboard se comentários aparecem em PT-BR")
    print("2. Configurar tradução automática após cada coleta")
    print("3. Traduzir os comentários restantes (se houver mais)")

if __name__ == "__main__":
    print("\n⚠️ Este script usa OpenAI API (GPT-4 Mini)")
    print("Custo estimado: ~$0.0003 por comentário")
    print("\nIniciando em 3 segundos...\n")

    import time
    time.sleep(3)

    asyncio.run(traduzir_comentarios_pendentes())
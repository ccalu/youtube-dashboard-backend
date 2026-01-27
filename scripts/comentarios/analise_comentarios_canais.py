"""
Script para analisar de quais canais são os comentários salvos
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime
from collections import Counter

load_dotenv()

# Conectar ao Supabase
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

print("=" * 80)
print("ANÁLISE DOS 5.785 COMENTÁRIOS ENCONTRADOS")
print("=" * 80)

# 1. Buscar todos os canal_id únicos dos comentários
print("\n1. BUSCANDO CANAIS ÚNICOS DOS COMENTÁRIOS...")
try:
    # Buscar IDs únicos de canais
    result = supabase.table('video_comments').select('canal_id').execute()

    if result.data:
        canal_ids = [r['canal_id'] for r in result.data if r.get('canal_id')]
        canal_ids_unicos = list(set(canal_ids))

        print(f"   - Total de comentários: {len(result.data)}")
        print(f"   - Canais únicos com comentários: {len(canal_ids_unicos)}")

        # Contar comentários por canal
        contador = Counter(canal_ids)
        top_10 = contador.most_common(10)

        print("\n   TOP 10 CANAIS COM MAIS COMENTÁRIOS:")
        for canal_id, count in top_10:
            if canal_id:
                # Buscar nome do canal
                canal_info = supabase.table('canais_monitorados').select('nome_canal, subnicho, tipo').eq('id', canal_id).limit(1).execute()
                if canal_info.data:
                    nome = canal_info.data[0]['nome_canal']
                    subnicho = canal_info.data[0]['subnicho']
                    tipo = canal_info.data[0]['tipo']
                    print(f"     - Canal ID {canal_id}: {nome} ({tipo}) - {subnicho}: {count} comentários")
                else:
                    print(f"     - Canal ID {canal_id}: [canal não encontrado]: {count} comentários")

        # Verificar se há comentários de canais monetizados
        print("\n2. VERIFICANDO COMENTÁRIOS DE CANAIS MONETIZADOS...")

        # Buscar IDs dos canais monetizados
        monetizados = supabase.table('canais_monitorados').select('id, nome_canal').eq('subnicho', 'Monetizados').execute()

        if monetizados.data:
            ids_monetizados = [c['id'] for c in monetizados.data]
            print(f"   - Canais monetizados cadastrados: {len(ids_monetizados)}")

            # Verificar quantos comentários são de canais monetizados
            comentarios_monetizados = [cid for cid in canal_ids if cid in ids_monetizados]
            print(f"   - Comentários de canais monetizados: {len(comentarios_monetizados)}")

            if comentarios_monetizados:
                print("\n   CANAIS MONETIZADOS COM COMENTÁRIOS:")
                for canal in monetizados.data:
                    count = contador.get(canal['id'], 0)
                    if count > 0:
                        print(f"     - {canal['nome_canal']}: {count} comentários")
            else:
                print("\n   ⚠️ NENHUM COMENTÁRIO É DE CANAL MONETIZADO!")
                print("   Os comentários salvos são de outros canais (mineração)")

        # Verificar comentários sem canal_id
        sem_canal = [r for r in result.data if not r.get('canal_id')]
        if sem_canal:
            print(f"\n   ⚠️ Comentários sem canal_id: {len(sem_canal)}")

            # Pegar amostra desses comentários
            sample = supabase.table('video_comments').select('video_title, author_name, comment_text_original').is_('canal_id', 'null').limit(3).execute()
            if sample.data:
                print("\n   EXEMPLOS DE COMENTÁRIOS SEM CANAL:")
                for i, comment in enumerate(sample.data, 1):
                    print(f"     {i}. Vídeo: {comment.get('video_title', 'N/A')[:50]}...")
                    print(f"        Autor: {comment.get('author_name', 'N/A')}")
                    print(f"        Texto: {comment.get('comment_text_original', '')[:100]}...")

        # Verificar datas dos comentários
        print("\n3. ANÁLISE TEMPORAL DOS COMENTÁRIOS:")

        # Buscar comentários mais recentes
        recentes = supabase.table('video_comments').select('published_at, canal_id').order('published_at', desc=True).limit(10).execute()

        if recentes.data:
            data_mais_recente = recentes.data[0].get('published_at', 'N/A')
            print(f"   - Comentário mais recente: {data_mais_recente}")

            # Buscar mais antigo
            antigos = supabase.table('video_comments').select('published_at').order('published_at').limit(1).execute()
            if antigos.data:
                data_mais_antiga = antigos.data[0].get('published_at', 'N/A')
                print(f"   - Comentário mais antigo: {data_mais_antiga}")

        # Verificar campos preenchidos
        print("\n4. ANÁLISE DOS CAMPOS PREENCHIDOS:")

        # Verificar quantos têm sugestão de resposta
        com_sugestao = supabase.table('video_comments').select('id').not_.is_('suggested_response', 'null').execute()
        print(f"   - Com sugestão de resposta: {len(com_sugestao.data) if com_sugestao.data else 0}")

        # Verificar quantos foram respondidos
        respondidos = supabase.table('video_comments').select('id').eq('is_responded', True).execute()
        print(f"   - Marcados como respondidos: {len(respondidos.data) if respondidos.data else 0}")

        # Verificar quantos foram traduzidos
        traduzidos = supabase.table('video_comments').select('id').eq('is_translated', True).execute()
        print(f"   - Traduzidos: {len(traduzidos.data) if traduzidos.data else 0}")

        # Verificar quantos foram analisados
        analisados = supabase.table('video_comments').select('id').not_.is_('gpt_analysis', 'null').execute()
        print(f"   - Com análise GPT: {len(analisados.data) if analisados.data else 0}")

    else:
        print("   ❌ Nenhum comentário encontrado!")

except Exception as e:
    print(f"   ❌ Erro ao analisar: {e}")

print("\n" + "=" * 80)
print("CONCLUSÃO DA ANÁLISE")
print("=" * 80)
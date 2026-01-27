"""
Script para vasculhar TODO o Supabase procurando por comentários
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime

load_dotenv()

# Conectar ao Supabase
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

print("=" * 80)
print("VASCULHANDO TODO O SUPABASE PROCURANDO POR COMENTÁRIOS")
print("=" * 80)

# 1. Verificar tabela video_comments
print("\n1. TABELA video_comments:")
try:
    result = supabase.table('video_comments').select('*').limit(5).execute()
    total_count = supabase.table('video_comments').select('id', count='exact').execute()
    print(f"   - Total de registros: {total_count.count}")
    if result.data:
        print(f"   - Primeiros registros encontrados: {len(result.data)}")
        for comment in result.data[:2]:
            print(f"     -> ID: {comment.get('id')}, Autor: {comment.get('author_name')}")
except Exception as e:
    print(f"   - ERRO ao acessar: {e}")

# 2. Verificar se existe tabela comments (sem video_)
print("\n2. TABELA comments:")
try:
    result = supabase.table('comments').select('*').limit(5).execute()
    total_count = supabase.table('comments').select('id', count='exact').execute()
    print(f"   - Total de registros: {total_count.count}")
    if result.data:
        print(f"   - Primeiros registros encontrados: {len(result.data)}")
except Exception as e:
    print(f"   - Tabela não existe ou erro: {e}")

# 3. Verificar tabela videos_historicos (pode ter comentários embedded)
print("\n3. TABELA videos_historicos (procurando campo de comentários):")
try:
    result = supabase.table('videos_historicos').select('*').limit(1).execute()
    if result.data:
        campos = list(result.data[0].keys())
        campos_comentarios = [c for c in campos if 'comment' in c.lower()]
        if campos_comentarios:
            print(f"   - Campos relacionados a comentários: {campos_comentarios}")
            # Verificar se há dados nesses campos
            for campo in campos_comentarios:
                check = supabase.table('videos_historicos').select(campo).not_.is_('null', campo).limit(5).execute()
                if check.data:
                    print(f"     -> Campo '{campo}' tem dados em {len(check.data)} registros")
        else:
            print(f"   - Nenhum campo de comentário encontrado")
            print(f"   - Campos disponíveis: {', '.join(campos[:10])}...")
except Exception as e:
    print(f"   - Erro: {e}")

# 4. Verificar tabela videos_monitoreados
print("\n4. TABELA videos_monitorados (procurando campo de comentários):")
try:
    result = supabase.table('videos_monitorados').select('*').limit(1).execute()
    if result.data:
        campos = list(result.data[0].keys())
        campos_comentarios = [c for c in campos if 'comment' in c.lower()]
        if campos_comentarios:
            print(f"   - Campos relacionados a comentários: {campos_comentarios}")
            # Verificar se há dados nesses campos
            for campo in campos_comentarios:
                check = supabase.table('videos_monitorados').select(campo).not_.is_('null', campo).limit(5).execute()
                if check.data:
                    print(f"     -> Campo '{campo}' tem dados em {len(check.data)} registros")
        else:
            print(f"   - Nenhum campo de comentário encontrado")
except Exception as e:
    print(f"   - Erro: {e}")

# 5. Verificar tabela youtube_comments
print("\n5. TABELA youtube_comments:")
try:
    result = supabase.table('youtube_comments').select('*').limit(5).execute()
    total_count = supabase.table('youtube_comments').select('id', count='exact').execute()
    print(f"   - Total de registros: {total_count.count}")
    if result.data:
        print(f"   - Primeiros registros encontrados: {len(result.data)}")
except Exception as e:
    print(f"   - Tabela não existe ou erro: {e}")

# 6. Verificar tabela channel_comments
print("\n6. TABELA channel_comments:")
try:
    result = supabase.table('channel_comments').select('*').limit(5).execute()
    total_count = supabase.table('channel_comments').select('id', count='exact').execute()
    print(f"   - Total de registros: {total_count.count}")
    if result.data:
        print(f"   - Primeiros registros encontrados: {len(result.data)}")
except Exception as e:
    print(f"   - Tabela não existe ou erro: {e}")

# 7. Listar TODAS as tabelas disponíveis (usando query no information_schema)
print("\n7. PROCURANDO EM TODAS AS TABELAS DO SCHEMA:")
print("   (Vou tentar listar todas as tabelas e procurar por 'comment' no nome)")

# Tabelas conhecidas do sistema
tabelas_conhecidas = [
    'canais_monitorados',
    'canais_historicos',
    'videos_monitorados',
    'videos_historicos',
    'notificacoes',
    'video_comments',
    'coletas'
]

for tabela in tabelas_conhecidas:
    try:
        # Pegar primeiro registro para ver estrutura
        result = supabase.table(tabela).select('*').limit(1).execute()
        if result.data:
            campos = list(result.data[0].keys())
            campos_com_comment = [c for c in campos if 'comment' in c.lower()]
            if campos_com_comment:
                print(f"\n   TABELA '{tabela}' TEM CAMPOS DE COMENTÁRIO:")
                print(f"   - Campos: {campos_com_comment}")

                # Verificar se há dados
                for campo in campos_com_comment:
                    try:
                        check = supabase.table(tabela).select(campo).not_.is_('null', campo).limit(10).execute()
                        if check.data:
                            print(f"   - Campo '{campo}' tem {len(check.data)} registros com dados!")
                            # Mostrar amostra
                            for i, item in enumerate(check.data[:2]):
                                valor = str(item.get(campo))[:100]
                                print(f"     Exemplo {i+1}: {valor}...")
                    except:
                        pass
    except:
        pass

# 8. Verificar especificamente a estrutura da tabela video_comments
print("\n" + "=" * 80)
print("ANÁLISE DETALHADA DA TABELA video_comments:")
print("=" * 80)
try:
    # Pegar um registro de exemplo para ver todos os campos
    result = supabase.table('video_comments').select('*').limit(1).execute()

    if result.data:
        print("ESTRUTURA DA TABELA:")
        for campo in result.data[0].keys():
            print(f"  - {campo}")

        # Contar total
        total = supabase.table('video_comments').select('id', count='exact').execute()
        print(f"\nTOTAL DE COMENTÁRIOS: {total.count}")

        # Verificar últimos registros
        ultimos = supabase.table('video_comments').select('*').order('updated_at', desc=True).limit(5).execute()
        if ultimos.data:
            print("\nÚLTIMOS COMENTÁRIOS ADICIONADOS:")
            for comment in ultimos.data:
                print(f"  - {comment.get('updated_at')}: {comment.get('author_name')} - {comment.get('comment_text_original')[:50]}...")
    else:
        print("TABELA ESTÁ VAZIA!")

        # Verificar se a tabela existe mesmo
        try:
            # Tentar inserir um registro de teste para ver se a tabela existe
            test_data = {
                'video_id': 'test123',
                'comment_id': 'test_comment_123',
                'author_name': 'Teste',
                'comment_text_original': 'Teste para verificar se tabela existe',
                'published_at': datetime.now().isoformat(),
                'is_responded': False
            }

            # Tentar inserir
            print("\nTestando se a tabela aceita inserção...")
            insert_result = supabase.table('video_comments').insert(test_data).execute()

            if insert_result.data:
                print("  - Tabela existe e aceita dados!")
                # Deletar o teste
                supabase.table('video_comments').delete().eq('comment_id', 'test_comment_123').execute()
                print("  - Teste removido")

        except Exception as e:
            print(f"  - Erro ao testar inserção: {e}")

except Exception as e:
    print(f"ERRO ao acessar video_comments: {e}")

print("\n" + "=" * 80)
print("FIM DA BUSCA")
print("=" * 80)
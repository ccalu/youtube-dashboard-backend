# -*- coding: utf-8 -*-
"""
VERIFICAÇÃO COMPLETA - COMENTÁRIOS DOS NOSSOS CANAIS
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime, timedelta
from collections import Counter
import json

# Force UTF-8 output
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

load_dotenv()

# Conectar ao Supabase
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

print("=" * 100)
print("VERIFICAÇÃO COMPLETA DOS COMENTÁRIOS - NOSSOS CANAIS")
print("=" * 100)

# 1. PRIMEIRO: IDENTIFICAR NOSSOS CANAIS
print("\n1. IDENTIFICANDO NOSSOS CANAIS (tipo='nosso'):")
print("-" * 80)

nossos_canais = supabase.table('canais_monitorados').select('*').eq('tipo', 'nosso').execute()

if nossos_canais.data:
    print(f"[OK] Total de NOSSOS canais: {len(nossos_canais.data)}")

    nossos_ids = [c['id'] for c in nossos_canais.data]

    print("\nNOSSOS CANAIS:")
    for canal in nossos_canais.data:
        print(f"  • ID {canal['id']}: {canal['nome_canal']} - Subnicho: {canal.get('subnicho', 'N/A')}")

    # 2. BUSCAR COMENTÁRIOS DOS NOSSOS CANAIS
    print("\n2. BUSCANDO COMENTÁRIOS DOS NOSSOS CANAIS:")
    print("-" * 80)

    total_nossos_comentarios = 0
    comentarios_por_canal = {}

    for canal_id in nossos_ids:
        # Buscar comentários deste canal
        comentarios = supabase.table('video_comments').select('id').eq('canal_id', canal_id).execute()

        if comentarios.data:
            count = len(comentarios.data)
            total_nossos_comentarios += count
            comentarios_por_canal[canal_id] = count

            # Buscar nome do canal
            canal_info = next((c for c in nossos_canais.data if c['id'] == canal_id), None)
            nome_canal = canal_info['nome_canal'] if canal_info else f"ID {canal_id}"

            print(f"  [OK] {nome_canal}: {count} comentários")
        else:
            canal_info = next((c for c in nossos_canais.data if c['id'] == canal_id), None)
            nome_canal = canal_info['nome_canal'] if canal_info else f"ID {canal_id}"
            print(f"  [!] {nome_canal}: 0 comentários")

    print(f"\n[TOTAL] COMENTARIOS DOS NOSSOS CANAIS: {total_nossos_comentarios}")

    # 3. ANÁLISE DETALHADA DOS COMENTÁRIOS
    if total_nossos_comentarios > 0:
        print("\n3. ANÁLISE DETALHADA DOS COMENTÁRIOS:")
        print("-" * 80)

        # Buscar todos os comentários dos nossos canais
        all_comments = []
        for canal_id in nossos_ids:
            result = supabase.table('video_comments').select('*').eq('canal_id', canal_id).execute()
            if result.data:
                all_comments.extend(result.data)

        # Análise de traduções
        print("\n[TRADUCOES]:")
        traduzidos = [c for c in all_comments if c.get('is_translated') == True]
        com_texto_pt = [c for c in all_comments if c.get('comment_text_pt')]
        print(f"  - Marcados como traduzidos: {len(traduzidos)}")
        print(f"  - Com texto em portugues: {len(com_texto_pt)}")

        # Análise de respostas
        print("\n[RESPOSTAS]:")
        com_sugestao = [c for c in all_comments if c.get('suggested_response')]
        respondidos = [c for c in all_comments if c.get('is_responded') == True]
        print(f"  - Com sugestao de resposta: {len(com_sugestao)}")
        print(f"  - Marcados como respondidos: {len(respondidos)}")

        # Análise temporal
        print("\n[ANALISE TEMPORAL]:")
        if all_comments:
            datas = [c['published_at'] for c in all_comments if c.get('published_at')]
            if datas:
                datas.sort()
                print(f"  • Comentário mais antigo: {datas[0]}")
                print(f"  • Comentário mais recente: {datas[-1]}")

        # Mostrar exemplos
        print("\n4. EXEMPLOS DE COMENTÁRIOS DOS NOSSOS CANAIS:")
        print("-" * 80)

        for i, comment in enumerate(all_comments[:3], 1):
            print(f"\nEXEMPLO {i}:")
            canal_info = next((c for c in nossos_canais.data if c['id'] == comment.get('canal_id')), None)
            nome_canal = canal_info['nome_canal'] if canal_info else "Desconhecido"

            print(f"  Canal: {nome_canal}")
            print(f"  Vídeo: {comment.get('video_title', 'N/A')[:50]}...")
            print(f"  Autor: {comment.get('author_name', 'N/A')}")
            print(f"  Texto Original: {comment.get('comment_text_original', '')[:100]}...")

            if comment.get('comment_text_pt'):
                print(f"  Tradução PT: {comment.get('comment_text_pt', '')[:100]}...")

            if comment.get('suggested_response'):
                print(f"  Resposta Sugerida: {comment.get('suggested_response', '')[:100]}...")

            print(f"  Respondido: {'[Sim]' if comment.get('is_responded') else '[Nao]'}")
            print(f"  Traduzido: {'[Sim]' if comment.get('is_translated') else '[Nao]'}")

else:
    print("[X] Nenhum canal com tipo='nosso' encontrado!")

# 4. VERIFICAR CANAIS MONETIZADOS
print("\n" + "=" * 100)
print("5. VERIFICANDO CANAIS MONETIZADOS (subnicho='Monetizados'):")
print("-" * 80)

monetizados = supabase.table('canais_monitorados').select('*').eq('subnicho', 'Monetizados').execute()

if monetizados.data:
    print(f"[OK] Total de canais monetizados: {len(monetizados.data)}")

    monetizados_ids = [c['id'] for c in monetizados.data]

    print("\nCANAIS MONETIZADOS:")
    total_comentarios_monetizados = 0

    for canal in monetizados.data:
        # Buscar comentários
        comentarios = supabase.table('video_comments').select('id').eq('canal_id', canal['id']).execute()
        count = len(comentarios.data) if comentarios.data else 0
        total_comentarios_monetizados += count

        tipo = canal.get('tipo', 'N/A')
        print(f"  • ID {canal['id']}: {canal['nome_canal']} (tipo: {tipo}) - {count} comentários")

    print(f"\n[INFO] TOTAL DE COMENTÁRIOS DE CANAIS MONETIZADOS: {total_comentarios_monetizados}")

# 5. TESTE DOS ENDPOINTS
print("\n" + "=" * 100)
print("6. TESTANDO ENDPOINTS DA API:")
print("-" * 80)

# Testar endpoint de resumo
print("\n[INFO] Testando /api/comentarios/resumo...")
try:
    # Simular a lógica do endpoint
    canais_monetizados = supabase.table('canais_monitorados').select('id').eq('subnicho', 'Monetizados').execute()
    canais_monetizados_count = len(canais_monetizados.data) if canais_monetizados.data else 0

    # Total de comentários
    total_result = supabase.table('video_comments').select('id', count='exact').execute()
    total_comentarios = total_result.count if total_result else 0

    # Novos hoje
    hoje = datetime.now().date()
    novos_result = supabase.table('video_comments').select('id').gte('updated_at', hoje.isoformat()).execute()
    novos_hoje = len(novos_result.data) if novos_result.data else 0

    # Aguardando resposta
    aguardando = supabase.table('video_comments').select('id').eq('is_responded', False).execute()
    aguardando_resposta = len(aguardando.data) if aguardando.data else 0

    print(f"  [OK] Resumo:")
    print(f"     • Canais Monetizados: {canais_monetizados_count}")
    print(f"     • Total Comentários: {total_comentarios}")
    print(f"     • Novos Hoje: {novos_hoje}")
    print(f"     • Aguardando Resposta: {aguardando_resposta}")

except Exception as e:
    print(f"  [X] Erro no endpoint de resumo: {e}")

# Testar endpoint de canais monetizados
print("\n[INFO] Testando /api/comentarios/monetizados...")
try:
    canais_result = supabase.table('canais_monitorados').select('*').eq('subnicho', 'Monetizados').execute()

    if canais_result.data:
        print(f"  [OK] {len(canais_result.data)} canais monetizados encontrados")

        for canal in canais_result.data[:3]:  # Primeiros 3 como exemplo
            # Contar comentários
            comments_result = supabase.table('video_comments').select('id').eq('canal_id', canal['id']).execute()
            total_comments = len(comments_result.data) if comments_result.data else 0

            # Sem resposta
            sem_resposta_result = supabase.table('video_comments').select('id').eq('canal_id', canal['id']).eq('is_responded', False).execute()
            sem_resposta = len(sem_resposta_result.data) if sem_resposta_result.data else 0

            print(f"     • {canal['nome_canal']}: {total_comments} comentários, {sem_resposta} sem resposta")
    else:
        print(f"  [!] Nenhum canal monetizado encontrado")

except Exception as e:
    print(f"  [X] Erro: {e}")

print("\n" + "=" * 100)
print("CONCLUSÃO DA VERIFICAÇÃO")
print("=" * 100)

# Resumo final
print("\n[RESUMO] RESUMO FINAL:")
print(f"  • Total de comentários no banco: {total_result.count if total_result else 0}")
print(f"  • Comentários dos NOSSOS canais: {total_nossos_comentarios}")
print(f"  • Comentários de canais monetizados: {total_comentarios_monetizados}")
print(f"  • Canais tipo='nosso': {len(nossos_canais.data) if nossos_canais.data else 0}")
print(f"  • Canais subnicho='Monetizados': {len(monetizados.data) if monetizados.data else 0}")

print("\n[OK] VERIFICAÇÃO COMPLETA FINALIZADA!")
print("=" * 100)
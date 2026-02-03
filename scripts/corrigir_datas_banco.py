"""
Script para Corrigir Datas no Banco de Dados
Data: 03/02/2026
Objetivo: Adicionar timezone em todas as datas sem timezone
"""

import sys
import os
import io
from datetime import datetime, timezone

# Fix encoding Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
from database import SupabaseClient

# Carregar variáveis de ambiente
load_dotenv()

def formatar_data_com_timezone(date_str):
    """Adiciona timezone UTC se não houver"""
    if not date_str:
        return None

    # Se já tem timezone, retornar como está
    if date_str.endswith('Z') or '+' in date_str.split('T')[-1]:
        return date_str

    # Tratar microsegundos com muitos dígitos
    if '.' in date_str:
        parts = date_str.split('.')
        base = parts[0]
        # Pegar apenas 6 dígitos dos microsegundos
        microseconds = parts[1][:6].ljust(6, '0')
        date_str = f"{base}.{microseconds}"

    # Adicionar timezone UTC
    return date_str + '+00:00'

def main():
    print("=" * 90)
    print("CORREÇÃO DE DATAS NO BANCO DE DADOS")
    print(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("=" * 90)

    db = SupabaseClient()

    # 1. Buscar comentários com datas problemáticas
    print("\n1. BUSCANDO COMENTÁRIOS COM DATAS PROBLEMÁTICAS")
    print("-" * 50)

    # Buscar em lotes de 1000
    offset = 0
    batch_size = 1000
    total_corrigidos = 0
    total_falhas = 0

    while True:
        # Buscar próximo lote
        comments = db.supabase.table('video_comments').select(
            'id, published_at, collected_at'
        ).range(offset, offset + batch_size - 1).execute()

        if not comments.data:
            break

        print(f"\nProcessando lote {offset//batch_size + 1} ({len(comments.data)} comentários)...")

        # Processar cada comentário
        for comment in comments.data:
            precisa_update = False
            updates = {}

            pub = comment.get('published_at')
            col = comment.get('collected_at')

            # Verificar published_at
            if pub and not (pub.endswith('Z') or '+' in pub.split('T')[-1] if 'T' in pub else False):
                pub_corrigida = formatar_data_com_timezone(pub)
                if pub_corrigida != pub:
                    updates['published_at'] = pub_corrigida
                    precisa_update = True

            # Verificar collected_at
            if col and not (col.endswith('Z') or '+' in col.split('T')[-1] if 'T' in col else False):
                col_corrigida = formatar_data_com_timezone(col)
                if col_corrigida != col:
                    updates['collected_at'] = col_corrigida
                    precisa_update = True

            # Fazer update se necessário
            if precisa_update:
                try:
                    db.supabase.table('video_comments').update(updates).eq('id', comment['id']).execute()
                    total_corrigidos += 1

                    # Mostrar progresso a cada 50 correções
                    if total_corrigidos % 50 == 0:
                        print(f"   ✅ {total_corrigidos} comentários corrigidos...")

                except Exception as e:
                    total_falhas += 1
                    print(f"   ❌ Erro ao corrigir comentário {comment['id']}: {e}")

        offset += batch_size

        # Parar se processar mais de 10000 registros (segurança)
        if offset >= 10000:
            print("\n⚠️ Limite de segurança atingido (10000 registros)")
            break

    # 2. Resumo
    print("\n" + "=" * 90)
    print("RESUMO DA CORREÇÃO")
    print("=" * 90)

    print(f"\n✅ Total de comentários corrigidos: {total_corrigidos}")
    if total_falhas > 0:
        print(f"❌ Total de falhas: {total_falhas}")

    # 3. Verificação pós-correção
    print("\n3. VERIFICAÇÃO PÓS-CORREÇÃO")
    print("-" * 50)

    # Buscar amostra para verificar
    verification = db.supabase.table('video_comments').select(
        'id, published_at, collected_at'
    ).limit(100).execute()

    problemas_restantes = 0
    for comment in verification.data:
        pub = comment.get('published_at')
        col = comment.get('collected_at')

        # Verificar se ainda há problemas
        if pub and not (pub.endswith('Z') or '+' in pub.split('T')[-1] if 'T' in pub else False):
            problemas_restantes += 1
        if col and not (col.endswith('Z') or '+' in col.split('T')[-1] if 'T' in col else False):
            problemas_restantes += 1

    if problemas_restantes == 0:
        print("✅ Verificação concluída: TODAS as datas estão com timezone!")
    else:
        print(f"⚠️ Ainda restam {problemas_restantes} datas sem timezone na amostra")

    print("\n📋 Próximos passos:")
    print("   1. Testar endpoints novamente")
    print("   2. Verificar se RangeError foi resolvido no frontend")
    print("   3. Monitorar novas coletas para garantir datas corretas")

    print("\n" + "=" * 90)

if __name__ == "__main__":
    # Confirmar antes de executar
    print("⚠️ ATENÇÃO: Este script irá MODIFICAR datas no banco de dados!")
    print("Ele adicionará timezone UTC (+00:00) em todas as datas que não têm timezone.")

    resposta = input("\nDeseja continuar? (s/n): ")

    if resposta.lower() == 's':
        main()
    else:
        print("Operação cancelada.")
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script inteligente para traduzir comentários que NÃO estão em português
Data: 28/01/2025

Este script:
1. Busca comentários sem tradução (comment_text_pt = NULL)
2. Detecta automaticamente se o comentário está em português
3. Se estiver em PT: copia o texto original para comment_text_pt
4. Se NÃO estiver em PT: traduz usando GPT-4
5. Marca is_translated = True e atualiza translation_updated_at
"""

import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase import create_client, Client
import openai
import time

# Configurar encoding UTF-8 no Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Carregar variáveis de ambiente
load_dotenv()

# Configurações
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Configurar OpenAI
openai.api_key = OPENAI_API_KEY

def is_portuguese_text(text):
    """
    Detecta se um texto está em português
    """
    if not text:
        return False

    # Palavras muito comuns em português
    pt_keywords = [
        'que', 'não', 'para', 'com', 'mais', 'mas', 'foi', 'ser',
        'está', 'muito', 'bem', 'isso', 'você', 'quando', 'como',
        'ainda', 'fazer', 'tem', 'tinha', 'pelo', 'pela', 'dos',
        'das', 'nos', 'nas', 'esse', 'essa', 'este', 'esta',
        'aquele', 'aquela', 'mesmo', 'mesma', 'pode', 'vai',
        'são', 'era', 'já', 'até', 'depois', 'antes', 'sempre',
        'também', 'outro', 'outra', 'qualquer', 'coisa', 'assim',
        'então', 'porque', 'porquê', 'pra', 'pro', 'né', 'tá'
    ]

    text_lower = text.lower()
    pt_word_count = 0

    for word in pt_keywords:
        if f' {word} ' in f' {text_lower} ' or \
           text_lower.startswith(f'{word} ') or \
           text_lower.endswith(f' {word}'):
            pt_word_count += 1

    # Se tem 2+ palavras PT, considera português
    return pt_word_count >= 2

def translate_to_portuguese(text):
    """
    Traduz texto para português usando GPT-4
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional translator. Translate the following text to Brazilian Portuguese. Keep the same tone and style as the original. Only respond with the translation, nothing else."},
                {"role": "user", "content": text}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"      [X] Erro GPT-4: {e}")
        return None

def main():
    print("=" * 60)
    print("TRADUÇÃO INTELIGENTE DE COMENTÁRIOS")
    print("=" * 60)
    print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    # Conectar ao Supabase
    print("\n[*] Conectando ao Supabase...")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Verificar se tem API key do OpenAI
    if not OPENAI_API_KEY:
        print("[X] ERRO: OPENAI_API_KEY não configurada no .env")
        return

    # Buscar comentários sem tradução
    print("[*] Buscando comentários sem tradução...")

    offset = 0
    limit = 100
    total_pt_copiados = 0
    total_traduzidos = 0
    total_erros = 0

    while True:
        try:
            # Buscar comentários onde comment_text_pt está NULL
            result = supabase.table('video_comments').select(
                'id, comment_text_original, comment_text_pt, is_translated'
            ).is_('comment_text_pt', 'null').not_.is_(
                'comment_text_original', 'null'
            ).range(offset, offset + limit - 1).execute()

            if not result.data:
                break

            comments = result.data
            print(f"\n[*] Processando batch {offset//limit + 1}: {len(comments)} comentários")

            for i, comment in enumerate(comments, 1):
                comment_id = comment['id']
                original_text = comment['comment_text_original']

                # Detectar se está em português
                if is_portuguese_text(original_text):
                    # Copiar texto original
                    try:
                        supabase.table('video_comments').update({
                            'comment_text_pt': original_text,
                            'is_translated': True,
                            'translation_updated_at': datetime.now(timezone.utc).isoformat()
                        }).eq('id', comment_id).execute()

                        total_pt_copiados += 1

                        if total_pt_copiados % 10 == 0:
                            print(f"   [PT] {total_pt_copiados} comentários PT copiados")

                    except Exception as e:
                        print(f"   [X] Erro ao copiar PT {comment_id}: {e}")
                        total_erros += 1

                else:
                    # Traduzir com GPT-4
                    try:
                        print(f"   [{i}/{len(comments)}] Traduzindo: {original_text[:50]}...")

                        translated = translate_to_portuguese(original_text)

                        if translated:
                            supabase.table('video_comments').update({
                                'comment_text_pt': translated,
                                'is_translated': True,
                                'translation_updated_at': datetime.now(timezone.utc).isoformat()
                            }).eq('id', comment_id).execute()

                            total_traduzidos += 1
                            print(f"      [OK] Traduzido para: {translated[:50]}...")

                            # Pausa para não exceder rate limit
                            time.sleep(0.5)
                        else:
                            total_erros += 1

                    except Exception as e:
                        print(f"      [X] Erro ao traduzir {comment_id}: {e}")
                        total_erros += 1

            # Se processou menos que o limite, chegou ao fim
            if len(comments) < limit:
                break

            offset += limit

        except Exception as e:
            print(f"[X] Erro ao buscar comentários: {e}")
            break

    # Resumo final
    print("\n" + "=" * 60)
    print("RESUMO DA TRADUÇÃO")
    print("=" * 60)
    print(f"Comentários em PT (copiados): {total_pt_copiados}")
    print(f"Comentários traduzidos (GPT-4): {total_traduzidos}")
    print(f"Erros encontrados: {total_erros}")
    print(f"Total processado: {total_pt_copiados + total_traduzidos}")

    # Verificar situação atual
    print("\n[*] Verificando situação atual...")

    try:
        result = supabase.table('video_comments').select('id', count='exact').execute()
        total = result.count or 0

        result = supabase.table('video_comments').select(
            'id', count='exact'
        ).not_.is_('comment_text_pt', 'null').execute()
        com_traducao = result.count or 0

        sem_traducao = total - com_traducao

        print(f"\nESTATÍSTICAS FINAIS:")
        print(f"Total de comentários: {total}")
        print(f"Com texto em PT: {com_traducao} ({com_traducao/total*100:.1f}%)")
        print(f"Sem texto em PT: {sem_traducao} ({sem_traducao/total*100:.1f}%)")

    except Exception as e:
        print(f"[X] Erro ao verificar estatísticas: {e}")

    print("\n[OK] Tradução concluída!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        confirm = input("\nEste script vai traduzir comentários usando GPT-4 (tem custo).\nDeseja continuar? (s/n): ")
        if confirm.lower() == 's':
            main()
        else:
            print("Operação cancelada.")
    except Exception as e:
        print(f"\n[X] ERRO FATAL: {e}")
        import traceback
        traceback.print_exc()
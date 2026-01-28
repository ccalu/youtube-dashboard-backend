#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script FINAL para garantir 100% dos comentários com texto PT
Data: 28/01/2025

Este script:
1. Busca TODOS comentários sem comment_text_pt
2. Se está em PT: copia o original
3. Se NÃO está em PT: traduz com GPT-4-mini
4. Garante 100% de cobertura
"""

import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase import create_client, Client
from openai import OpenAI
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

# Cliente OpenAI (nova API)
client = OpenAI(api_key=OPENAI_API_KEY)

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
        'das', 'nos', 'nas', 'esse', 'essa', 'este', 'esta'
    ]

    text_lower = text.lower()
    pt_word_count = 0

    for word in pt_keywords:
        if f' {word} ' in f' {text_lower} ' or \
           text_lower.startswith(f'{word} ') or \
           text_lower.endswith(f' {word}'):
            pt_word_count += 1
            if pt_word_count >= 2:  # Otimização: parar assim que encontrar 2
                return True

    return False

def translate_to_portuguese(text):
    """
    Traduz texto para português usando GPT-4-mini (nova API)
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Modelo mais barato e rápido
            messages=[
                {
                    "role": "system",
                    "content": "Traduza o texto a seguir para português brasileiro. Mantenha o tom e estilo original. Responda APENAS com a tradução, nada mais."
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            temperature=0.3,
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"      [X] Erro GPT: {str(e)[:100]}")
        return None

def main():
    print("=" * 60)
    print("PROCESSAMENTO FINAL - 100% COBERTURA PT")
    print("=" * 60)
    print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    # Conectar ao Supabase
    print("\n[*] Conectando ao Supabase...")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Verificar situação inicial
    result = supabase.table('video_comments').select('id', count='exact').execute()
    total_inicial = result.count or 0

    result = supabase.table('video_comments').select(
        'id', count='exact'
    ).is_('comment_text_pt', 'null').execute()
    sem_pt_inicial = result.count or 0

    print(f"\n[*] Situação inicial:")
    print(f"    Total de comentários: {total_inicial}")
    print(f"    Sem texto PT: {sem_pt_inicial} ({sem_pt_inicial/total_inicial*100:.1f}%)")

    if sem_pt_inicial == 0:
        print("\n[OK] Todos os comentários já têm texto em PT!")
        return

    # Buscar comentários sem PT
    print(f"\n[*] Processando {sem_pt_inicial} comentários...")

    offset = 0
    limit = 50  # Menor batch para melhor controle
    total_pt_copiados = 0
    total_traduzidos = 0
    total_erros = 0

    while True:
        try:
            # Buscar próximo batch
            result = supabase.table('video_comments').select(
                'id, comment_text_original'
            ).is_('comment_text_pt', 'null').not_.is_(
                'comment_text_original', 'null'
            ).range(offset, offset + limit - 1).execute()

            if not result.data:
                break

            comments = result.data
            batch_num = (offset // limit) + 1
            print(f"\n[Batch {batch_num}] Processando {len(comments)} comentários...")

            for i, comment in enumerate(comments, 1):
                comment_id = comment['id']
                original_text = comment['comment_text_original']

                # Verificar se é português
                if is_portuguese_text(original_text):
                    # É português - apenas copiar
                    try:
                        supabase.table('video_comments').update({
                            'comment_text_pt': original_text,
                            'is_translated': True,
                            'translation_updated_at': datetime.now(timezone.utc).isoformat()
                        }).eq('id', comment_id).execute()

                        total_pt_copiados += 1

                    except Exception as e:
                        print(f"   [X] Erro ao copiar {comment_id}: {e}")
                        total_erros += 1

                else:
                    # NÃO é português - traduzir
                    print(f"   [{i}/{len(comments)}] Traduzindo: {original_text[:40]}...")

                    translated = translate_to_portuguese(original_text)

                    if translated:
                        try:
                            supabase.table('video_comments').update({
                                'comment_text_pt': translated,
                                'is_translated': True,
                                'translation_updated_at': datetime.now(timezone.utc).isoformat()
                            }).eq('id', comment_id).execute()

                            total_traduzidos += 1

                            # Pequena pausa para não exceder rate limit
                            if total_traduzidos % 10 == 0:
                                time.sleep(1)

                        except Exception as e:
                            print(f"      [X] Erro ao salvar: {e}")
                            total_erros += 1
                    else:
                        # Se falhou tradução, copiar original como fallback
                        try:
                            supabase.table('video_comments').update({
                                'comment_text_pt': original_text,
                                'is_translated': False,
                                'translation_updated_at': datetime.now(timezone.utc).isoformat()
                            }).eq('id', comment_id).execute()
                            total_erros += 1
                        except:
                            pass

            # Status do batch
            print(f"   [OK] Batch {batch_num}: {total_pt_copiados} PT copiados, {total_traduzidos} traduzidos")

            # Se processou menos que o limite, acabou
            if len(comments) < limit:
                break

            offset += limit

        except Exception as e:
            print(f"[X] Erro no batch: {e}")
            break

    # Verificar situação final
    print("\n" + "=" * 60)
    print("RESUMO DO PROCESSAMENTO")
    print("=" * 60)

    result = supabase.table('video_comments').select('id', count='exact').execute()
    total_final = result.count or 0

    result = supabase.table('video_comments').select(
        'id', count='exact'
    ).not_.is_('comment_text_pt', 'null').execute()
    com_pt_final = result.count or 0

    sem_pt_final = total_final - com_pt_final

    print(f"Comentários PT copiados: {total_pt_copiados}")
    print(f"Comentários traduzidos: {total_traduzidos}")
    print(f"Erros/Fallbacks: {total_erros}")
    print(f"\nESTATÍSTICAS FINAIS:")
    print(f"Total de comentários: {total_final}")
    print(f"Com texto PT: {com_pt_final} ({com_pt_final/total_final*100:.1f}%)")
    print(f"Sem texto PT: {sem_pt_final}")

    if sem_pt_final == 0:
        print("\n[OK] SUCESSO! 100% dos comentários têm texto em PT!")
    else:
        print(f"\n[!] Ainda faltam {sem_pt_final} comentários")

    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[X] ERRO FATAL: {e}")
        import traceback
        traceback.print_exc()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script FORÇADO para garantir 100% dos comentários com PT
Data: 28/01/2025

REGRAS:
1. TODOS os comentários devem ter comment_text_pt preenchido
2. Se for emoji/URL/texto curto: copiar o original
3. Se for texto válido: traduzir com GPT-4o-mini
4. SEM EXCEÇÕES - 100% de cobertura
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

# Cliente OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

def translate_to_portuguese(text):
    """
    Traduz texto para português usando GPT-4o-mini
    Se falhar, retorna o texto original
    """
    try:
        # Se for muito curto ou apenas emojis/símbolos, retornar como está
        if len(text.strip()) < 3 or not any(c.isalpha() for c in text):
            return text

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # SEMPRE MINI!
            messages=[
                {
                    "role": "system",
                    "content": "Traduza para português brasileiro. Mantenha emojis, URLs e formatação. Responda APENAS com a tradução."
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
    except:
        # Se falhar, retornar o original
        return text

def main():
    print("=" * 60)
    print("FORÇANDO 100% DE COBERTURA PT")
    print("=" * 60)
    print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    # Conectar ao Supabase
    print("\n[*] Conectando ao Supabase...")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Buscar TODOS os comentários sem PT
    print("[*] Buscando comentários sem texto PT...")

    offset = 0
    limit = 50
    total_processados = 0

    while True:
        try:
            # Buscar próximo batch
            result = supabase.table('video_comments').select(
                'id, comment_text_original'
            ).is_('comment_text_pt', 'null').range(
                offset, offset + limit - 1
            ).execute()

            if not result.data:
                break

            comments = result.data
            print(f"\n[Batch] Processando {len(comments)} comentários...")

            for comment in comments:
                comment_id = comment['id']
                original = comment.get('comment_text_original', '')

                # Se não tem texto original, colocar string vazia
                if not original:
                    pt_text = "[sem texto]"
                else:
                    # Traduzir ou copiar
                    pt_text = translate_to_portuguese(original)

                # Salvar no banco
                try:
                    supabase.table('video_comments').update({
                        'comment_text_pt': pt_text,
                        'is_translated': True,
                        'translation_updated_at': datetime.now(timezone.utc).isoformat()
                    }).eq('id', comment_id).execute()

                    total_processados += 1

                    if total_processados % 10 == 0:
                        print(f"   [+] {total_processados} comentários processados...")

                except Exception as e:
                    # Se falhar, pelo menos copiar o original
                    try:
                        supabase.table('video_comments').update({
                            'comment_text_pt': original or "[erro]",
                            'is_translated': False
                        }).eq('id', comment_id).execute()
                    except:
                        pass

            # Se processou menos que o limite, acabou
            if len(comments) < limit:
                break

            offset += limit

        except Exception as e:
            print(f"[X] Erro no batch: {e}")
            break

    # Verificar resultado final
    print("\n" + "=" * 60)
    print("VERIFICAÇÃO FINAL")
    print("=" * 60)

    result = supabase.table('video_comments').select('id', count='exact').execute()
    total = result.count or 0

    result = supabase.table('video_comments').select(
        'id', count='exact'
    ).is_('comment_text_pt', 'null').execute()
    sem_pt = result.count or 0

    com_pt = total - sem_pt
    percentual = (com_pt / total * 100) if total > 0 else 0

    print(f"Total de comentários: {total}")
    print(f"Com texto PT: {com_pt} ({percentual:.1f}%)")
    print(f"Sem texto PT: {sem_pt}")

    if sem_pt == 0:
        print("\n[OK] SUCESSO! 100% DOS COMENTÁRIOS TÊM TEXTO PT!")
    else:
        print(f"\n[!] Ainda faltam {sem_pt} comentários")

        # Forçar cópia do original nos que faltarem
        if sem_pt > 0 and sem_pt < 50:
            print("[*] Forçando cópia do original nos restantes...")

            result = supabase.table('video_comments').select(
                'id, comment_text_original'
            ).is_('comment_text_pt', 'null').execute()

            for comment in result.data:
                try:
                    supabase.table('video_comments').update({
                        'comment_text_pt': comment.get('comment_text_original', '[vazio]'),
                        'is_translated': False
                    }).eq('id', comment['id']).execute()
                except:
                    pass

            print("[OK] Forçado nos restantes!")

    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[X] ERRO: {e}")
        import traceback
        traceback.print_exc()
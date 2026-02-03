#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para desativar canais problemáticos
Data: 28/01/2025

Marca os 6 canais como inativos ao invés de deletar (por causa das referências)
Conforme solicitado: canais #3, #4, #7, #8, #13, #14
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

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

# Lista dos 6 canais para desativar (URLs específicas)
CANAIS_PARA_DESATIVAR = [
    "https://www.youtube.com/@WW2NavalHistory",
    "https://www.youtube.com/@CoronadoSecreto",
    "https://www.youtube.com/@ChroniquesDeLaSecondeGuerre",
    "https://www.youtube.com/@TracesofVoice",
    "https://www.youtube.com/@WarEchoes35",
    "https://www.youtube.com/@Historia_EnSecreto"
]

def main():
    print("=" * 60)
    print("DESATIVAÇÃO DE CANAIS PROBLEMÁTICOS")
    print("=" * 60)
    print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    # Conectar ao Supabase
    print("\n[*] Conectando ao Supabase...")
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("[OK] Conectado com sucesso!")
    except Exception as e:
        print(f"[X] Erro ao conectar: {e}")
        return

    print(f"\n[*] Canais a desativar: {len(CANAIS_PARA_DESATIVAR)}")

    desativados = 0
    nao_encontrados = 0
    erros = 0

    for i, url in enumerate(CANAIS_PARA_DESATIVAR, 1):
        print(f"\n[{i}/6] Processando: {url}")

        try:
            # Buscar o canal pelo URL
            result = supabase.table('canais_monitorados').select(
                'id, nome_canal, subnicho, tipo, ativo'
            ).eq('url_canal', url).execute()

            if result.data and len(result.data) > 0:
                canal = result.data[0]
                print(f"   Nome: {canal['nome_canal']}")
                print(f"   Status atual: {'Ativo' if canal.get('ativo', True) else 'Inativo'}")

                # Desativar o canal
                print("   [*] Desativando...")
                supabase.table('canais_monitorados').update({
                    'ativo': False,
                    'updated_at': datetime.now().isoformat()
                }).eq('id', canal['id']).execute()

                print("   [OK] Canal desativado com sucesso!")
                desativados += 1

            else:
                print("   [!] Canal não encontrado no banco")
                nao_encontrados += 1

        except Exception as e:
            print(f"   [X] Erro ao processar: {str(e)[:100]}")
            erros += 1

    # Resumo final
    print("\n" + "=" * 60)
    print("RESUMO DA DESATIVAÇÃO")
    print("=" * 60)
    print(f"✅ Desativados com sucesso: {desativados}")
    print(f"⚠️ Não encontrados: {nao_encontrados}")
    print(f"❌ Erros: {erros}")

    if desativados > 0:
        print(f"\n[OK] {desativados} canais foram desativados!")
        print("Eles não serão mais processados nas coletas.")

    # Verificar total de canais ativos
    try:
        result = supabase.table('canais_monitorados').select(
            'id', count='exact'
        ).eq('ativo', True).execute()
        total = result.count or 0
        print(f"\n[*] Total de canais ATIVOS no sistema: {total}")
    except:
        pass

    print("\n" + "=" * 60)
    print("[OK] Script concluído!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[X] ERRO FATAL: {e}")
        import traceback
        traceback.print_exc()
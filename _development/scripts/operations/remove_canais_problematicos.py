#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para remover canais problemáticos do banco
Data: 28/01/2025

Remove os 6 canais específicos com múltiplas falhas de coleta
Conforme solicitado pelo usuário: canais #3, #4, #7, #8, #13, #14
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

# Lista dos 6 canais para remover (URLs específicas)
CANAIS_PARA_REMOVER = [
    # #3 - WW2 Naval History (7 falhas)
    "https://www.youtube.com/@WW2NavalHistory",

    # #4 - Secretos de los Coronados (6 falhas)
    "https://www.youtube.com/@CoronadoSecreto",

    # #7 - Chroniques de la Seconde Guerre (3 falhas)
    "https://www.youtube.com/@ChroniquesDeLaSecondeGuerre",

    # #8 - Traces of Voice (3 falhas)
    "https://www.youtube.com/@TracesofVoice",

    # #13 - WAR ECHOES (4 falhas)
    "https://www.youtube.com/@WarEchoes35",

    # #14 - Historia En Secreto (3 falhas)
    "https://www.youtube.com/@Historia_EnSecreto"
]

def main():
    print("=" * 60)
    print("REMOÇÃO DE CANAIS PROBLEMÁTICOS")
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

    print(f"\n[*] Canais a remover: {len(CANAIS_PARA_REMOVER)}")

    # Buscar informações dos canais antes de remover
    print("\n[*] Buscando informações dos canais...")

    removidos = 0
    nao_encontrados = 0
    erros = 0

    for i, url in enumerate(CANAIS_PARA_REMOVER, 1):
        print(f"\n[{i}/6] Processando: {url}")

        try:
            # Buscar o canal pelo URL
            result = supabase.table('canais_monitorados').select(
                'id, nome_canal, subnicho, tipo, coleta_falhas_consecutivas'
            ).eq('url_canal', url).execute()

            if result.data and len(result.data) > 0:
                canal = result.data[0]
                print(f"   Nome: {canal['nome_canal']}")
                print(f"   Subnicho: {canal['subnicho']}")
                print(f"   Tipo: {canal['tipo']}")
                print(f"   Falhas: {canal.get('coleta_falhas_consecutivas', 0)}")

                # Remover o canal
                print("   [*] Removendo...")
                supabase.table('canais_monitorados').delete().eq(
                    'id', canal['id']
                ).execute()

                print("   [OK] Canal removido com sucesso!")
                removidos += 1

            else:
                print("   [!] Canal não encontrado no banco")
                nao_encontrados += 1

        except Exception as e:
            print(f"   [X] Erro ao processar: {str(e)[:100]}")
            erros += 1

    # Resumo final
    print("\n" + "=" * 60)
    print("RESUMO DA REMOÇÃO")
    print("=" * 60)
    print(f"✅ Removidos com sucesso: {removidos}")
    print(f"⚠️ Não encontrados: {nao_encontrados}")
    print(f"❌ Erros: {erros}")

    if removidos > 0:
        print(f"\n[OK] {removidos} canais problemáticos foram removidos do sistema!")
        print("As próximas coletas não tentarão mais processar esses canais.")

    # Verificar total de canais restantes
    try:
        result = supabase.table('canais_monitorados').select('id', count='exact').execute()
        total = result.count or 0
        print(f"\n[*] Total de canais ativos no sistema: {total}")
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
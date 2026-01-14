#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para popular spreadsheet_ids na tabela yt_channels

Uso:
1. Preencher dicion

ário SPREADSHEET_IDS abaixo
2. Rodar: python populate_spreadsheet_ids.py
3. Verificar no Supabase se foi atualizado
"""

from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# CONFIGURAÇÃO: Adicione os spreadsheet_ids aqui
# ============================================================================
# Formato: 'channel_id': 'spreadsheet_id'
SPREADSHEET_IDS = {
    # ========== MENTALIDADE MASCULINA E FINANÇAS (7 canais) ==========
    'UCbB1WtTqBWYdSk3JE6iRNRw': '1bLc31LHgNXUag-h0xxDzVqlCc76lsnynt8jzJQiQ3kE',  # Sans Limites
    'UCcVQxMf4R4m1sgoXMXNohYg': '1Q0VcdAld_KlqQYgW03xXPkeIMxtwSw5G_szoK0IgJ5k',  # El Camino
    'UCkfVIV0aTE6FIf69KInaDbg': '17ydtcTj56_59x022FIrIGbezEyUTbpni1MrJyDrQFwg',  # Traccia Interiore
    'UC1VnTiQU_r5kmyQianCxfkQ': '1WILiGHPH6dhZX16s-YR_M8I3LUnAfpOzdDD4pIg-F04',  # Stick to the Plan
    'UCh86kORh0IQmWEd0J7TRAzA': '1GRf1mEWTcSz3lkEWUnQ6Mtzh-AC4dkN9obePzJEqGKM',  # O Essencial
    'UCI20Jp7RmA-DqRWa31l9GPA': '1Nbba6IlMn7PHWdGAYuhAgdRENhVL3koJEx61ePg8ewk',  # Plan Umysłu
    'UCr-DmlEMcIQKm7Vwf0-CDyQ': '1iqLui3vYAgXmw-PDDCmgorMmSAft_RgkCtWorlamj_w',  # Kural Yok

    # ========== EMPREENDEDORISMO - DINASTIAS FINANCEIRAS (4 canais) ==========
    'UCdNsmU5wcXG1d313tXdu3Ug': '1F-3cXpdEymFj-hNn_v8faJH6-pSkC7E07hd4bTG202E',  # Dynasties Financières
    'UCXb7D1wL1cCU8OUMltP9oDA': '1u1BYcXrdZG4ZXFEDlBUo-vmZS76xuHrAH00_i6Txpsk',  # Financial Dynasties
    'UCVFjuVKCBhgM4XCYheB3nfA': '1ICsBcjm92KNufGeYfV-jA1pTuT6zzpHWGeeAFHlnQQI',  # Dinastías Financieras
    'UClvgnpdTdIx5zAvcjiurOJw': '1N6IqMiXhTuV1Jim0gubIQ37xAm3W6EF1MlDOsVLAjP8',  # Dinastie Finanziarie

    # ========== MISTÉRIOS (7 canais) ==========
    'UC05sfttG19DmHtKwJgad2vA': '1ybZ5-MAinKWKBzf_342c3Ehbk_LFPhNwycYA52lkaRk',  # Enigmas Reales
    'UCNh6Y70bZRkWuXwK82iIdvg': '18cR3pQkiTeEnbiarJgTH4TSQ42tipq2dN-Iw39E4-bQ',  # Archived Mysteries
    'UC5wU_hftDEiP8QPlqDbua0w': '1St95rID9KAs2ZEzxTCvEH4ilfcYkM8ndkh3CpdHw3AI',  # Chroniques du Mystère
    'UCnufwQb_3X2um1NQpzA1lIQ': '1MycT7UhHj_zJ8cbiYZAgSxtFTI2iQPuLM0uzJkP7mfE',  # Mistérios Arquivados
    'UCA_WmrDoBmFCKrvu0YbHiRQ': '167J3YoG0yDNbeSUMK8gmkqa96OR8YrEd5mM0fTy1nQI',  # Odkrywając Tajemnice
    'UCo0cx0JTJS0M9e1eMmvvhTg': '1xNxqeoxAPDZvKqW-1HfQOgvJaw6b8JDbxRzD5Kasd78',  # Gerçek Gizemler
    'UCivaa4bfXnoxIAKh3KLPLxA': '1PnZOHrrpzzaiz4r9oqkzG5jtN70N4ouzYFIGVpJk6nU',  # Misteri Archiviati

    # ========== TERROR (5 canais) ==========
    'UCLWB5HmHYUh6MhzccSqqpwg': '1yLf0-Z875lKCecDflxpWN3q8mFIKKAnTaCJK9jVKMiE',  # Relatos Obscuros
    'UCn50hcQls0thZKlxqIzBf8w': '1dXDLTKazKk6E51RFo-ysLWTk6O32MhPig2PR7OjkVFU',  # The Whispering Fear
    'UC5cqQuYs5rF3aTAU0AbF3Ww': '1M50J3FIxvgn5_ic9vzoZ6KsuCXkhmw5iEgJsCsN6G3Y',  # Historias Malditas
    'UCakyoZMYsQPcO2MVsZ6Bn2Q': '1w7kIyU6wGNw5-yJKjTrlAltxbB9MjshM2_Ms62JNN0g',  # Il Sussurro del Terrore
    'UCXly7vmGaGVP5XtJVAvqXbA': '1BXu-jxwsG7BTYgsw01Om-lD88Iclhlm1FExydjutxPU',  # N'ÉTEINS PAS LA LUMIÈRE

    # ========== GUERRAS E CIVILIZAÇÕES (4 canais) ==========
    'UCeaCIer3l-AYmIUc34Z019g': '1IEy39qyK1vKgYEENwxGF8WIDR4qKNBwa9EiYKi6zsU4',  # Fallen Empires
    'UCfqmFKYPD4tV3qNDhQnCLCw': '170aH9OVJvK5q04ku83vQfBNRZPMQM8LiKeEthdFA6fI',  # El Legado Eterno
    'UCQWjUcLU3CUuidv9BJ4VMNg': '1xK5Mzr81Z536iRD3Uie48OMtGRwD_YNzVNhEueTC1dg',  # Asche der Imperien
    'UCE_NL77h4u2E_SROLAP1Yvg': '1y140dk7iwjmIFKVzP5HGUdoig1rLWH_f4LYnfcS1muI',  # Empires Déchus
}

def main():
    """Popula spreadsheet_ids no banco"""

    print("=" * 80)
    print("POPULANDO SPREADSHEET_IDS")
    print("=" * 80)
    print()

    if not SPREADSHEET_IDS:
        print("[ERRO] Dicionario SPREADSHEET_IDS esta vazio!")
        print("   Por favor, preencha com os 35 channel_ids e spreadsheet_ids")
        return

    # Conecta Supabase
    sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

    print(f"Total de canais para atualizar: {len(SPREADSHEET_IDS)}")
    print()

    success_count = 0
    error_count = 0

    for channel_id, spreadsheet_id in SPREADSHEET_IDS.items():
        try:
            # Verifica se canal existe
            channel = sb.table('yt_channels').select('channel_id, channel_name').eq('channel_id', channel_id).execute()

            if not channel.data:
                print(f"[AVISO] Canal {channel_id} nao encontrado no banco - skipando")
                error_count += 1
                continue

            channel_name = channel.data[0].get('channel_name', 'Unknown')

            # Atualiza spreadsheet_id
            result = sb.table('yt_channels').update({
                'spreadsheet_id': spreadsheet_id
            }).eq('channel_id', channel_id).execute()

            if result.data:
                print(f"[OK] {channel_name} ({channel_id})")
                print(f"   Spreadsheet ID: {spreadsheet_id}")
                success_count += 1
            else:
                print(f"[ERRO] Erro ao atualizar {channel_id}")
                error_count += 1

        except Exception as e:
            print(f"[ERRO] Erro ao processar {channel_id}: {e}")
            error_count += 1

        print()

    # Resumo
    print("=" * 80)
    print("RESUMO")
    print("=" * 80)
    print(f"Sucessos: {success_count}")
    print(f"Erros: {error_count}")
    print(f"Total: {len(SPREADSHEET_IDS)}")
    print()

    # Verifica quais canais ativos ainda não têm spreadsheet_id
    print("=" * 80)
    print("CANAIS ATIVOS SEM SPREADSHEET_ID")
    print("=" * 80)

    all_channels = sb.table('yt_channels').select('channel_id, channel_name, spreadsheet_id').eq('is_active', True).execute()

    missing_count = 0
    for channel in all_channels.data:
        if not channel.get('spreadsheet_id'):
            print(f"[FALTA] {channel.get('channel_name', 'Unknown')} ({channel['channel_id']})")
            missing_count += 1

    if missing_count == 0:
        print("[OK] Todos os canais ativos tem spreadsheet_id configurado!")
    else:
        print(f"\n[AVISO] {missing_count} canais ainda precisam de spreadsheet_id")

    print("=" * 80)

if __name__ == '__main__':
    main()

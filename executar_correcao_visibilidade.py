#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORRIGIR VISIBILIDADE - Dashboard de Monetização
=================================================
Marca show_monetization_history=TRUE apenas para:
- 15 canais ativos (is_monetized=TRUE)
- 3 canais desmonetizados (Chroniques, Reis, Contes)

Total: 18 canais visíveis (não 52!)
"""

from supabase import create_client
import os
import sys
from dotenv import load_dotenv

# Fix encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

load_dotenv()

sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print("=" * 80)
print("CORRIGIR VISIBILIDADE - Dashboard de Monetização".center(80))
print("=" * 80)
print()

# IDs dos 3 canais desmonetizados (que FORAM monetizados)
CANAIS_DESMONETIZADOS = [
    'UCpWl6TezIQFXod8H2q3uw-w',  # Chroniques Anciennes
    'UCV9aMsA0swcuExud2tZSlUg',  # Reis Perversos
    'UCD9mEdIqxsDqkn0Vw2UC91A'   # Contes Sinistres
]

print("🎯 OBJETIVO:")
print("   Dashboard deve mostrar apenas 18 canais:")
print("   • 15 canais ativos (is_monetized=TRUE)")
print("   • 3 canais desmonetizados (Chroniques, Reis, Contes)")
print()
print("=" * 80)
print()

# PASSO 1: Marcar todos como FALSE
print("1️⃣  Marcando TODOS os canais como ocultos (FALSE)...")
print()

try:
    result = sb.table('yt_channels').update({
        'show_monetization_history': False
    }).neq('channel_id', '').execute()

    count = len(result.data) if result.data else 0
    print(f"   ✅ {count} canais marcados como ocultos")
except Exception as e:
    print(f"   ❌ Erro: {str(e)}")
    sys.exit(1)

print()

# PASSO 2: Marcar canais ativos como TRUE
print("2️⃣  Marcando canais ATIVOS como visíveis (TRUE)...")
print()

try:
    result = sb.table('yt_channels').update({
        'show_monetization_history': True
    }).eq('is_monetized', True).execute()

    count = len(result.data) if result.data else 0
    print(f"   ✅ {count} canais ativos marcados como visíveis")

    if result.data:
        print()
        print("   Canais marcados:")
        for canal in result.data:
            print(f"      • {canal['channel_name']}")
except Exception as e:
    print(f"   ❌ Erro: {str(e)}")
    sys.exit(1)

print()

# PASSO 3: Marcar os 3 desmonetizados como TRUE
print("3️⃣  Marcando 3 canais DESMONETIZADOS como visíveis (TRUE)...")
print()

success_count = 0
for channel_id in CANAIS_DESMONETIZADOS:
    try:
        result = sb.table('yt_channels').update({
            'show_monetization_history': True
        }).eq('channel_id', channel_id).execute()

        if result.data:
            canal = result.data[0]
            print(f"   ✅ {canal['channel_name']}")
            success_count += 1
        else:
            print(f"   ⚠️  Canal {channel_id} não encontrado")
    except Exception as e:
        print(f"   ❌ Erro em {channel_id}: {str(e)}")

print()
print(f"   Total: {success_count}/3 canais desmonetizados marcados")
print()

# PASSO 4: Validar resultado final
print("=" * 80)
print("VALIDAÇÃO FINAL".center(80))
print("=" * 80)
print()

# Contar visíveis
result_visiveis = sb.table('yt_channels').select('*', count='exact').eq('show_monetization_history', True).execute()
count_visiveis = result_visiveis.count if hasattr(result_visiveis, 'count') else len(result_visiveis.data or [])

# Contar ativos
result_ativos = sb.table('yt_channels').select('*', count='exact').eq('is_monetized', True).execute()
count_ativos = result_ativos.count if hasattr(result_ativos, 'count') else len(result_ativos.data or [])

# Contar desmonetizados visíveis
result_desmon = sb.table('yt_channels').select('*', count='exact').eq('is_monetized', False).eq('show_monetization_history', True).execute()
count_desmon = result_desmon.count if hasattr(result_desmon, 'count') else len(result_desmon.data or [])

# Contar ocultos
result_ocultos = sb.table('yt_channels').select('*', count='exact').eq('show_monetization_history', False).execute()
count_ocultos = result_ocultos.count if hasattr(result_ocultos, 'count') else len(result_ocultos.data or [])

print(f"✅ Total visível no dashboard: {count_visiveis}")
print(f"   🟢 Canais ativos (coleta diária): {count_ativos}")
print(f"   🟡 Canais desmonetizados (com histórico): {count_desmon}")
print()
print(f"⚫ Canais ocultos (nunca monetizados): {count_ocultos}")
print()

# Verificar se está correto
if count_visiveis == 18 and count_ativos == 15 and count_desmon == 3:
    print("🎉 PERFEITO! Dashboard vai mostrar exatamente 18 canais!")
    print()
    print("Breakdown:")
    print("   • 15 canais monetizados (🟢 coleta automática 5 AM)")
    print("   • 3 canais desmonetizados (🟡 apenas histórico)")
    print()
    print("Próximo passo:")
    print("   python validar_monetization_final.py")
else:
    print(f"⚠️  Números não batem com o esperado!")
    print(f"   Esperado: 18 visíveis (15 ativos + 3 desmon)")
    print(f"   Recebido: {count_visiveis} visíveis ({count_ativos} ativos + {count_desmon} desmon)")

print()
print("=" * 80)

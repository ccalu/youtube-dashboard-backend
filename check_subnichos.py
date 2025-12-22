#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para listar todos os subnichos cadastrados no dashboard
"""

from dotenv import load_dotenv
import os
from supabase import create_client

# Carrega variáveis de ambiente
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Cria cliente Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 60)
print("SUBNICHOS CADASTRADOS NO DASHBOARD")
print("=" * 60)

# Busca subnichos únicos dos canais minerados (tipo="referencia")
print("\n[MINERADOS] SUBNICHOS DE CANAIS DE REFERENCIA:")
response_ref = supabase.table('canais_monitorados').select('subnicho').eq('tipo', 'referencia').execute()
subnichos_ref = sorted(set([c['subnicho'] for c in response_ref.data if c.get('subnicho')]))

for i, sub in enumerate(subnichos_ref, 1):
    # Conta quantos canais tem nesse subnicho
    count = len([c for c in response_ref.data if c.get('subnicho') == sub])
    print(f"  {i}. {sub} ({count} canais)")

print(f"\n  Total: {len(subnichos_ref)} subnichos")

# Busca subnichos únicos dos nossos canais (tipo="nosso")
print("\n\n[NOSSOS] SUBNICHOS DOS NOSSOS CANAIS:")
response_nosso = supabase.table('canais_monitorados').select('subnicho').eq('tipo', 'nosso').execute()
subnichos_nosso = sorted(set([c['subnicho'] for c in response_nosso.data if c.get('subnicho')]))

for i, sub in enumerate(subnichos_nosso, 1):
    # Conta quantos canais nossos tem nesse subnicho
    count = len([c for c in response_nosso.data if c.get('subnicho') == sub])
    print(f"  {i}. {sub} ({count} canais)")

print(f"\n  Total: {len(subnichos_nosso)} subnichos")

# Verifica se há subnichos em comum
comum = set(subnichos_ref) & set(subnichos_nosso)
if comum:
    print(f"\n\n[COMUM] SUBNICHOS EM COMUM (Referencia + Nossos): {len(comum)}")
    for sub in sorted(comum):
        print(f"  - {sub}")

print("\n" + "=" * 60)

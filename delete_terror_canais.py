#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para deletar todos os canais minerados do subnicho Terror
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

print("=" * 70)
print("DELETAR CANAIS MINERADOS DO SUBNICHO TERROR")
print("=" * 70)

# PASSO 1: Buscar canais que serão deletados
print("\n[1/4] Buscando canais Terror (tipo=minerado)...")
response = supabase.table('canais_monitorados')\
    .select('id, nome_canal, url_canal')\
    .eq('subnicho', 'Terror')\
    .eq('tipo', 'minerado')\
    .execute()

canais_terror = response.data
total = len(canais_terror)

print(f"      Encontrados: {total} canais")

if total == 0:
    print("\n[!] Nenhum canal encontrado. Operacao cancelada.")
    exit(0)

# PASSO 2: Mostrar prévia dos canais
print(f"\n[2/4] Previa dos canais que serao deletados:")
for i, canal in enumerate(canais_terror[:5], 1):
    print(f"      {i}. {canal['nome_canal']}")
if total > 5:
    print(f"      ... e mais {total - 5} canais")

# PASSO 3: Confirmar exclusão
print(f"\n[3/4] Confirmar exclusao de {total} canais? (sim/nao)")
confirmacao = input("      > ").strip().lower()

if confirmacao not in ['sim', 's', 'yes', 'y']:
    print("\n[!] Operacao cancelada pelo usuario.")
    exit(0)

# PASSO 4: Deletar dados relacionados e canais
print(f"\n[4/5] Deletando dados relacionados dos {total} canais...")
canal_ids = [canal['id'] for canal in canais_terror]

try:
    # 4.1 - Deletar histórico de dados dos canais
    print(f"      [4.1] Deletando historico de dados...")
    for canal_id in canal_ids:
        supabase.table('dados_canais_historico').delete().eq('canal_id', canal_id).execute()
    print(f"      [OK] Historico deletado")

    # 4.2 - Deletar vídeos dos canais
    print(f"      [4.2] Deletando videos...")
    for canal_id in canal_ids:
        supabase.table('videos_historico').delete().eq('canal_id', canal_id).execute()
    print(f"      [OK] Videos deletados")

    # 4.3 - Deletar notificações dos canais
    print(f"      [4.3] Deletando notificacoes...")
    for canal_id in canal_ids:
        supabase.table('notificacoes').delete().eq('canal_id', canal_id).execute()
    print(f"      [OK] Notificacoes deletadas")

except Exception as e:
    print(f"\n[AVISO] Erro ao deletar dados relacionados (pode ser normal se nao houver): {e}")

# PASSO 5: Deletar canais
print(f"\n[5/5] Deletando os {total} canais...")
try:
    delete_response = supabase.table('canais_monitorados')\
        .delete()\
        .eq('subnicho', 'Terror')\
        .eq('tipo', 'minerado')\
        .execute()

    print(f"      [OK] {total} canais deletados com sucesso!")

    # Verificar exclusão
    print("\n[VERIFICACAO] Contando canais restantes...")
    check_response = supabase.table('canais_monitorados')\
        .select('id', count='exact')\
        .eq('tipo', 'minerado')\
        .execute()

    total_restante = check_response.count
    print(f"      Total de canais minerados restantes: {total_restante}")
    print(f"      (Esperado: 344 = 396 - 52)")

except Exception as e:
    print(f"\n[ERRO] Falha ao deletar canais: {e}")
    exit(1)

print("\n" + "=" * 70)
print("OPERACAO CONCLUIDA COM SUCESSO!")
print("=" * 70)

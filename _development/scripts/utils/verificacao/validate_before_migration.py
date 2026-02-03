# -*- coding: utf-8 -*-
"""
Script de Pre-Validacao - Migration OAuth Multi-Proxy
Valida banco atual antes de rodar unify_oauth_system_v2.sql
"""

import os
from supabase import create_client
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Carrega variaveis de ambiente
load_dotenv()

# Conecta ao Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

print("=" * 80)
print("PRE-VALIDACAO - MIGRATION OAUTH MULTI-PROXY")
print("=" * 80)
print()

# ============================================================
# 1. VALIDAR ESTRUTURA ATUAL DA TABELA yt_channels
# ============================================================
print("[1] ESTRUTURA ATUAL DA TABELA yt_channels")
print("-" * 80)

# Lista de colunas que a migration vai adicionar
colunas_migration = [
    'is_monetized',
    'is_active',
    'lingua',
    'subnicho',
    'default_playlist_id',
    'monetization_start_date',
    'total_subscribers',
    'total_videos',
    'updated_at',
    'proxy_name',
    'performance_score'
]

# Busca 1 registro pra ver quais colunas existem
try:
    sample = supabase.table('yt_channels').select('*').limit(1).execute()

    if sample.data:
        colunas_existentes = list(sample.data[0].keys())

        print("\n[OK] Colunas que JA EXISTEM (nao serao modificadas):")
        for col in colunas_migration:
            if col in colunas_existentes:
                print(f"   - {col}")

        print("\n[NOVO] Colunas que SERAO CRIADAS:")
        for col in colunas_migration:
            if col not in colunas_existentes:
                print(f"   - {col}")
    else:
        print("[AVISO] Tabela yt_channels esta vazia!")

except Exception as e:
    print(f"[ERRO] Erro ao verificar estrutura: {e}")

print()

# ============================================================
# 2. VALIDAR DADOS ATUAIS (35 CANAIS)
# ============================================================
print("[2] VALIDACAO DOS CANAIS EXISTENTES")
print("-" * 80)

try:
    canais = supabase.table('yt_channels').select('*').execute()
    total_canais = len(canais.data)

    print(f"\n[OK] Total de canais: {total_canais}")

    # Verifica Sans Limites
    sans_limites = [c for c in canais.data if c.get('channel_id') == 'UCbB1WtTqBWYdSk3JE6iRNRw']

    if sans_limites:
        canal = sans_limites[0]
        print(f"\n[OK] Canal Sans Limites encontrado:")
        print(f"   - channel_id: {canal.get('channel_id')}")
        print(f"   - channel_name: {canal.get('channel_name')}")
        print(f"   - proxy_name atual: {canal.get('proxy_name') or 'NULL (sera preenchido)'}")
        print(f"   - is_monetized: {canal.get('is_monetized', 'coluna nao existe')}")
    else:
        print("\n[AVISO] Sans Limites NAO encontrado! (UCbB1WtTqBWYdSk3JE6iRNRw)")

    # Verifica campos criticos
    print(f"\n[STATS] Estatisticas dos campos:")

    # Linguas
    linguas = {}
    for c in canais.data:
        lingua = c.get('lingua')
        if lingua:
            linguas[lingua] = linguas.get(lingua, 0) + 1

    if linguas:
        print(f"   - lingua: {sum(linguas.values())}/{total_canais} preenchidos")
        for l, count in linguas.items():
            print(f"      * {l}: {count} canais")
    else:
        print(f"   - lingua: coluna nao existe ou 0/{total_canais} preenchidos")

    # Subnichos
    subnichos = {}
    for c in canais.data:
        subnicho = c.get('subnicho')
        if subnicho:
            subnichos[subnicho] = subnichos.get(subnicho, 0) + 1

    if subnichos:
        print(f"\n   - subnicho: {sum(subnichos.values())}/{total_canais} preenchidos")
        for s, count in sorted(subnichos.items()):
            print(f"      * {s}: {count} canais")
    else:
        print(f"   - subnicho: coluna nao existe ou 0/{total_canais} preenchidos")

    # Proxy names
    proxies = {}
    for c in canais.data:
        proxy = c.get('proxy_name')
        if proxy:
            proxies[proxy] = proxies.get(proxy, 0) + 1

    if proxies:
        print(f"\n   - proxy_name: {sum(proxies.values())}/{total_canais} preenchidos")
        for p, count in proxies.items():
            print(f"      * {p}: {count} canais")
    else:
        print(f"   - proxy_name: coluna nao existe ou 0/{total_canais} preenchidos")

except Exception as e:
    print(f"[ERRO] Erro ao validar canais: {e}")

print()

# ============================================================
# 3. VALIDAR CONSTRAINT DE DATA
# ============================================================
print("[3] VALIDACAO DE DATAS DE MONETIZACAO")
print("-" * 80)

try:
    # Busca canais com monetization_start_date
    canais_monetizados = [c for c in canais.data if c.get('monetization_start_date')]

    if canais_monetizados:
        print(f"\n[OK] {len(canais_monetizados)} canais com monetization_start_date")

        # Valida datas (constraint exige >= CURRENT_DATE - 10 anos)
        data_limite = datetime.now() - timedelta(days=365*10)
        datas_invalidas = []

        for c in canais_monetizados:
            data_str = c.get('monetization_start_date')
            try:
                data = datetime.fromisoformat(data_str.replace('Z', '+00:00'))
                if data < data_limite:
                    datas_invalidas.append({
                        'channel_id': c.get('channel_id'),
                        'channel_name': c.get('channel_name'),
                        'data': data_str
                    })
            except:
                pass

        if datas_invalidas:
            print(f"\n[AVISO] {len(datas_invalidas)} canais com data ANTES de {data_limite.strftime('%Y-%m-%d')}:")
            print("   (CONSTRAINT vai FALHAR se nao ajustarmos!)")
            for d in datas_invalidas:
                print(f"   - {d['channel_name']} ({d['channel_id']}): {d['data']}")
        else:
            print(f"\n[OK] Todas as datas sao >= {data_limite.strftime('%Y-%m-%d')}")
            print("   (CONSTRAINT vai passar!)")
    else:
        print("\n[OK] Nenhum canal com monetization_start_date")
        print("   (coluna nao existe ou todos NULL - CONSTRAINT nao vai afetar)")

except Exception as e:
    print(f"[ERRO] Erro ao validar datas: {e}")

print()

# ============================================================
# 4. VALIDAR TABELA yt_proxy_credentials
# ============================================================
print("[4] VALIDACAO DE PROXIES (yt_proxy_credentials)")
print("-" * 80)

try:
    proxies_result = supabase.table('yt_proxy_credentials').select('*').execute()

    if proxies_result.data:
        print(f"\n[OK] {len(proxies_result.data)} proxies cadastrados:")
        for p in proxies_result.data:
            print(f"   - {p['proxy_name']}")

        # Verifica se proxy_c0008_1 ja existe
        proxy_sans = [p for p in proxies_result.data if p['proxy_name'] == 'proxy_c0008_1']
        if proxy_sans:
            print(f"\n[OK] Proxy proxy_c0008_1 JA EXISTE")
            print(f"   (Migration vai atualizar com ON CONFLICT)")
        else:
            print(f"\n[NOVO] Proxy proxy_c0008_1 NAO EXISTE")
            print(f"   (Migration vai inserir novo)")
    else:
        print("\n[NOVO] Tabela yt_proxy_credentials esta vazia")
        print("   (Migration vai criar primeiro proxy)")

except Exception as e:
    print(f"[ERRO] Erro ao validar proxies: {e}")

print()

# ============================================================
# 5. RELATORIO FINAL
# ============================================================
print("=" * 80)
print("RELATORIO FINAL - E SEGURO RODAR A MIGRATION?")
print("=" * 80)
print()

seguro = True
warnings = []
errors = []

# Verifica se Sans Limites existe
if not sans_limites:
    errors.append("[ERRO] Sans Limites nao encontrado (UCbB1WtTqBWYdSk3JE6iRNRw)")
    seguro = False

# Verifica constraint de data
try:
    if canais_monetizados and datas_invalidas:
        errors.append(f"[ERRO] {len(datas_invalidas)} canais com data < 2015 (constraint vai falhar)")
        seguro = False
except:
    pass

# Warnings gerais
if total_canais != 35:
    warnings.append(f"[AVISO] Esperado 35 canais, encontrado {total_canais}")

if seguro:
    print("[OK] SEGURO RODAR MIGRATION!")
    print()
    print("Proximos passos:")
    print("1. Copie o conteudo de migrations/unify_oauth_system_v2.sql")
    print("2. Cole no Supabase SQL Editor")
    print("3. Execute")
    print()
else:
    print("[ERRO] NAO E SEGURO RODAR MIGRATION!")
    print()
    print("Problemas encontrados:")
    for e in errors:
        print(f"   {e}")
    print()
    print("Acoes recomendadas:")
    print("1. Corrigir problemas acima")
    print("2. Ou remover CONSTRAINT de data da SQL")
    print()

if warnings:
    print("Avisos:")
    for w in warnings:
        print(f"   {w}")
    print()

print("=" * 80)

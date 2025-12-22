#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para adicionar 19 novos canais minerados ao dashboard
"""

from dotenv import load_dotenv
import os
from supabase import create_client
import re

# Carrega variáveis de ambiente
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Cria cliente Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 70)
print("ADICIONAR 19 NOVOS CANAIS MINERADOS")
print("=" * 70)

# Lista de canais organizados por subnicho
canais = [
    # Terror - 10 canais
    {"url": "https://www.youtube.com/@OldMoneyDynasty", "subnicho": "Terror", "lingua": "English"},
    {"url": "https://www.youtube.com/@HistoryOnWallsYT", "subnicho": "Terror", "lingua": "English"},
    {"url": "https://www.youtube.com/@oldmoneymansions", "subnicho": "Terror", "lingua": "English"},
    {"url": "https://www.youtube.com/@oldmoneyempires", "subnicho": "Terror", "lingua": "English"},
    {"url": "https://www.youtube.com/@EternalManors", "subnicho": "Terror", "lingua": "English"},
    {"url": "https://www.youtube.com/@OldLinePower", "subnicho": "Terror", "lingua": "English"},
    {"url": "https://www.youtube.com/@Mansions_Castles_DarkHistory", "subnicho": "Terror", "lingua": "English"},
    {"url": "https://www.youtube.com/channel/UCQdNVkVO03ajNH18j-CyVbw", "subnicho": "Terror", "lingua": "English"},
    {"url": "https://www.youtube.com/@MurosconHistoria", "subnicho": "Terror", "lingua": "Spanish"},
    {"url": "https://www.youtube.com/@GrandManors", "subnicho": "Terror", "lingua": "English"},

    # Empreendedorismo - 3 canais
    {"url": "https://www.youtube.com/channel/UCzgRbi9TXN6acU-KxPBI6lQ", "subnicho": "Empreendedorismo", "lingua": "English"},
    {"url": "https://www.youtube.com/@Therichprofile", "subnicho": "Empreendedorismo", "lingua": "English"},
    {"url": "https://www.youtube.com/channel/UCuLZpbu5_Yuw5sfB8vWWqYg", "subnicho": "Empreendedorismo", "lingua": "English"},

    # Guerras e Civilizações - 2 canais
    {"url": "https://www.youtube.com/channel/UCsnXfzmMBL8Od4q5vKuIaLg", "subnicho": "Guerras e Civilizações", "lingua": "Italian"},
    {"url": "https://www.youtube.com/@darkhistoryclass", "subnicho": "Guerras e Civilizações", "lingua": "English"},

    # Historias Sombrias - 1 canal
    {"url": "https://www.youtube.com/channel/UCHoH9MRrbPs6Tgp2NKIwmdQ", "subnicho": "Historias Sombrias", "lingua": "Italian"},

    # Conspiração - 3 canais
    {"url": "https://www.youtube.com/channel/UCEvyOG3ee2YT1O2Rly1X_bg", "subnicho": "Conspiração", "lingua": "English"},
    {"url": "https://www.youtube.com/channel/UC3RQo9UD36HH_dQ-bfyPbeQ", "subnicho": "Conspiração", "lingua": "English"},
    {"url": "https://www.youtube.com/@HistoryAfterDark-k8l", "subnicho": "Conspiração", "lingua": "English"},
]

def extrair_nome_temporario(url):
    """Extrai um nome temporário da URL até a coleta preencher o nome real"""
    # Tenta extrair @nome
    match = re.search(r'@([^/]+)', url)
    if match:
        return match.group(1).replace('_', ' ').title()

    # Se for channel/UCxxxx, usa o ID como placeholder
    match = re.search(r'channel/(UC[^/]+)', url)
    if match:
        return f"Canal {match.group(1)[:8]}"

    return "Canal YouTube"

def normalizar_url(url):
    """Remove /videos, /featured da URL"""
    url = url.rstrip('/')
    url = re.sub(r'/(videos|featured)$', '', url)
    return url

print("\n[1/3] Preparando dados dos canais...")
canais_preparados = []
for canal in canais:
    url_limpa = normalizar_url(canal['url'])
    nome_temp = extrair_nome_temporario(url_limpa)

    canais_preparados.append({
        'nome_canal': nome_temp,
        'url_canal': url_limpa,
        'nicho': '',
        'subnicho': canal['subnicho'],
        'lingua': canal['lingua'],
        'tipo': 'minerado',
        'status': 'ativo'
    })

print(f"      {len(canais_preparados)} canais preparados")

# Exibir resumo por subnicho
print("\n[2/3] Resumo dos canais por subnicho:")
subnichos_count = {}
for canal in canais_preparados:
    sub = canal['subnicho']
    subnichos_count[sub] = subnichos_count.get(sub, 0) + 1

for subnicho, count in sorted(subnichos_count.items()):
    print(f"      - {subnicho}: {count} canais")

# Inserir canais
print(f"\n[3/3] Inserindo {len(canais_preparados)} canais no banco...")
sucesso = 0
falhas = 0

for i, canal in enumerate(canais_preparados, 1):
    try:
        response = supabase.table('canais_monitorados').insert(canal).execute()
        sucesso += 1
        print(f"      [{i}/{len(canais_preparados)}] OK: {canal['nome_canal']} ({canal['subnicho']})")
    except Exception as e:
        falhas += 1
        print(f"      [{i}/{len(canais_preparados)}] ERRO: {canal['nome_canal']} - {e}")

print("\n" + "=" * 70)
print(f"RESULTADO: {sucesso} canais inseridos | {falhas} falhas")

# Verificar total final
print("\n[VERIFICACAO] Contando canais minerados...")
check_response = supabase.table('canais_monitorados')\
    .select('id', count='exact')\
    .eq('tipo', 'minerado')\
    .execute()

total_minerados = check_response.count
print(f"      Total de canais minerados: {total_minerados}")
print(f"      (Esperado: 363 = 344 + 19)")

print("=" * 70)

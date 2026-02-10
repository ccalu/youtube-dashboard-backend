#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para adicionar múltiplos canais minerados ao dashboard
Data: 09/02/2026
"""

import os
import sys
import io
from datetime import datetime
from database import SupabaseClient
from dotenv import load_dotenv

# Configurar encoding UTF-8 para saída
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Carregar variáveis de ambiente
load_dotenv()

# Lista de canais para adicionar
CANAIS = [
    # Guerras e Civilizações
    {
        "nome_canal": "Vercingétorix",
        "url_canal": "https://www.youtube.com/@axiomspark",
        "subnicho": "Guerras e Civilizações",
        "lingua": "Espanhol",
        "tipo": "minerado"
    },
    {
        "nome_canal": "Warpath History",
        "url_canal": "https://www.youtube.com/@warpathbattle",
        "subnicho": "Guerras e Civilizações",
        "lingua": "Inglês",
        "tipo": "minerado"
    },
    {
        "nome_canal": "Noches del Pasado",
        "url_canal": "https://www.youtube.com/channel/UCFzaFJSsE_cF_AabYilHlmQ",
        "subnicho": "Guerras e Civilizações",
        "lingua": "Espanhol",
        "tipo": "minerado"
    },
    {
        "nome_canal": "Крик Молчания",
        "url_canal": "https://www.youtube.com/channel/UCLkxD0gdrJC-6BmE1EJTw5w",
        "subnicho": "Guerras e Civilizações",
        "lingua": "Russo",
        "tipo": "minerado"
    },
    {
        "nome_canal": "TRUE HAPPENED",
        "url_canal": "https://www.youtube.com/@truehappened",
        "subnicho": "Guerras e Civilizações",
        "lingua": "Inglês",
        "tipo": "minerado"
    },
    {
        "nome_canal": "Dynast's Saga",
        "url_canal": "https://www.youtube.com/channel/UCx3eGC6H3DE-IoqYDWGcoxA",
        "subnicho": "Guerras e Civilizações",
        "lingua": "Inglês",
        "tipo": "minerado"
    },
    {
        "nome_canal": "Korkunç Hayatlar",
        "url_canal": "https://www.youtube.com/@korkunchayatlar22",
        "subnicho": "Guerras e Civilizações",
        "lingua": "Turco",
        "tipo": "minerado"
    },

    # Historias Sombrias
    {
        "nome_canal": "Reino Oscuro",
        "url_canal": "https://www.youtube.com/@reinoscuro",
        "subnicho": "Historias Sombrias",
        "lingua": "Espanhol",
        "tipo": "minerado"
    },
    {
        "nome_canal": "Relatos del Castigo",
        "url_canal": "https://www.youtube.com/@RelatosdelCastigo",
        "subnicho": "Historias Sombrias",
        "lingua": "Espanhol",
        "tipo": "minerado"
    },
    {
        "nome_canal": "Torture of Echoes TV",
        "url_canal": "https://www.youtube.com/channel/UCT8QG7qqSgG2I5HI24GP0Qw",
        "subnicho": "Historias Sombrias",
        "lingua": "Inglês",
        "tipo": "minerado"
    },
    {
        "nome_canal": "Crimson Historians",
        "url_canal": "https://www.youtube.com/@RealCrimsonHistorians",
        "subnicho": "Historias Sombrias",
        "lingua": "Inglês",
        "tipo": "minerado"
    },
    {
        "nome_canal": "Ancestral",
        "url_canal": "https://www.youtube.com/@WatchAncestral",
        "subnicho": "Historias Sombrias",
        "lingua": "Inglês",
        "tipo": "minerado"
    },
    {
        "nome_canal": "Безмолвные Историки",
        "url_canal": "https://www.youtube.com/channel/UChhBAFyQYV7F1536Ov_bPzg",
        "subnicho": "Historias Sombrias",
        "lingua": "Russo",
        "tipo": "minerado"
    },
    {
        "nome_canal": "Geschichten der Bestrafung",
        "url_canal": "https://www.youtube.com/@GeschichtenderBestrafung",
        "subnicho": "Historias Sombrias",
        "lingua": "Alemão",
        "tipo": "minerado"
    },
    {
        "nome_canal": "Tales of Steel and Blood",
        "url_canal": "https://www.youtube.com/channel/UC2m-XCJ7-fsKZrTLKbWYE9A",
        "subnicho": "Historias Sombrias",
        "lingua": "Inglês",
        "tipo": "minerado"
    },
    {
        "nome_canal": "Script Historians",
        "url_canal": "https://www.youtube.com/@ScriptHistorians",
        "subnicho": "Historias Sombrias",
        "lingua": "Inglês",
        "tipo": "minerado"
    },
    {
        "nome_canal": "History's Dark Ledger",
        "url_canal": "https://www.youtube.com/channel/UCKODE8Y1-eIKR0VKM4AoZmw",
        "subnicho": "Historias Sombrias",
        "lingua": "Inglês",
        "tipo": "minerado"
    },
    {
        "nome_canal": "Opowieści o Karze",
        "url_canal": "https://www.youtube.com/@Opowie%C5%9BcioKarze",
        "subnicho": "Historias Sombrias",
        "lingua": "Polones",
        "tipo": "minerado"
    },
    {
        "nome_canal": "The Forgotten Historians",
        "url_canal": "https://www.youtube.com/@TheForgottenHistorians",
        "subnicho": "Historias Sombrias",
        "lingua": "Inglês",
        "tipo": "minerado"
    },
    {
        "nome_canal": "Torture Diary",
        "url_canal": "https://www.youtube.com/@TortureDiary1",
        "subnicho": "Historias Sombrias",
        "lingua": "Inglês",
        "tipo": "minerado"
    },

    # Relatos de Guerra
    {
        "nome_canal": "Tales Of Britain",
        "url_canal": "https://www.youtube.com/channel/UCTaRz7gd4QL96xHKXGMryhA",
        "subnicho": "Relatos de Guerra",
        "lingua": "Inglês",
        "tipo": "minerado"
    },
    {
        "nome_canal": "WW2 Tactical Tales",
        "url_canal": "https://www.youtube.com/channel/UCSlSs8XoPeS7LyWWsCPs1kg",
        "subnicho": "Relatos de Guerra",
        "lingua": "Inglês",
        "tipo": "minerado"
    },
    {
        "nome_canal": "British WW2 Tales",
        "url_canal": "https://www.youtube.com/channel/UCSFI_YQg6zIFl64wyQxMvKg",
        "subnicho": "Relatos de Guerra",
        "lingua": "Inglês",
        "tipo": "minerado"
    },
    {
        "nome_canal": "Echoes of 1945",
        "url_canal": "https://www.youtube.com/channel/UCCUWJh3jCftOnmlasqDAA6g",
        "subnicho": "Relatos de Guerra",
        "lingua": "Inglês",
        "tipo": "minerado"
    },
    {
        "nome_canal": "WW2 Memoirs",
        "url_canal": "https://www.youtube.com/channel/UCtMgo5Cn6WjBGhv33vRgX7A",
        "subnicho": "Relatos de Guerra",
        "lingua": "Inglês",
        "tipo": "minerado"
    },
    {
        "nome_canal": "Hidden History",
        "url_canal": "https://www.youtube.com/@HiddenHistoryYT",
        "subnicho": "Relatos de Guerra",
        "lingua": "Inglês",
        "tipo": "minerado"
    },
    {
        "nome_canal": "Secrets of World War II",
        "url_canal": "https://www.youtube.com/@SecretsofWorldWarII-e2w",
        "subnicho": "Relatos de Guerra",
        "lingua": "Inglês",
        "tipo": "minerado"
    },
    {
        "nome_canal": "WW2 Rediscovered",
        "url_canal": "https://www.youtube.com/@WW2Rediscovered",
        "subnicho": "Relatos de Guerra",
        "lingua": "Inglês",
        "tipo": "minerado"
    },
    {
        "nome_canal": "WW2 Recode",
        "url_canal": "https://www.youtube.com/@WW2Recode",
        "subnicho": "Relatos de Guerra",
        "lingua": "Inglês",
        "tipo": "minerado"
    },
    {
        "nome_canal": "WW2 Legacy",
        "url_canal": "https://www.youtube.com/channel/UCZ_demPDwqCz9BbcXLfNAeg",
        "subnicho": "Relatos de Guerra",
        "lingua": "Inglês",
        "tipo": "minerado"
    },
    {
        "nome_canal": "WW2 Cauldron",
        "url_canal": "https://www.youtube.com/@ww2.cauldron",
        "subnicho": "Relatos de Guerra",
        "lingua": "Inglês",
        "tipo": "minerado"
    },
    {
        "nome_canal": "War Time Review",
        "url_canal": "https://www.youtube.com/channel/UCj05unNuACkQu-XtwFL3thw",
        "subnicho": "Relatos de Guerra",
        "lingua": "Inglês",
        "tipo": "minerado"
    },
    {
        "nome_canal": "Cold War Chronicles- US",
        "url_canal": "https://www.youtube.com/@ColdWarChroniclesUS",
        "subnicho": "Relatos de Guerra",
        "lingua": "Inglês",
        "tipo": "minerado"
    },
    {
        "nome_canal": "WW2 Explained",
        "url_canal": "https://www.youtube.com/channel/UCMXLenT5ywg3ydl2dlesMbg",
        "subnicho": "Relatos de Guerra",
        "lingua": "Inglês",
        "tipo": "minerado"
    },

    # Mistérios
    {
        "nome_canal": "Misterios del Espacio",
        "url_canal": "https://www.youtube.com/channel/UC9FK-91m4lyuP5m8GMcecCQ",
        "subnicho": "Mistérios",
        "lingua": "Espanhol",
        "tipo": "minerado"
    },
    {
        "nome_canal": "Night Science",
        "url_canal": "https://www.youtube.com/channel/UCT-_XJEMBYPcTjG1bzgtVfg",
        "subnicho": "Mistérios",
        "lingua": "Inglês",
        "tipo": "minerado"
    },
    {
        "nome_canal": "Boring Space",
        "url_canal": "https://www.youtube.com/channel/UCem0RtgLQWokYeAaJLYfMdw",
        "subnicho": "Mistérios",
        "lingua": "Inglês",
        "tipo": "minerado"
    },
    {
        "nome_canal": "Calm Space",
        "url_canal": "https://www.youtube.com/channel/UCXyJmt3PKv0fbsU9DtcreEw",
        "subnicho": "Mistérios",
        "lingua": "Inglês",
        "tipo": "minerado"
    },
    {
        "nome_canal": "Sleep On Science",
        "url_canal": "https://www.youtube.com/@SleepOnScience",
        "subnicho": "Mistérios",
        "lingua": "Inglês",
        "tipo": "minerado"
    }
]

def limpar_url_canal(url):
    """Limpa e padroniza a URL do canal"""
    url = url.strip()
    # Remove /videos se existir
    if url.endswith('/videos'):
        url = url[:-7]
    return url

def adicionar_canais():
    """Adiciona todos os canais no banco de dados"""
    client = SupabaseClient()

    # Estatísticas
    stats = {
        "Guerras e Civilizações": {"total": 0, "sucesso": 0, "erro": 0},
        "Historias Sombrias": {"total": 0, "sucesso": 0, "erro": 0},
        "Relatos de Guerra": {"total": 0, "sucesso": 0, "erro": 0},
        "Mistérios": {"total": 0, "sucesso": 0, "erro": 0}
    }

    erros = []

    print("=" * 60)
    print("ADICIONANDO CANAIS MINERADOS AO DASHBOARD")
    print("=" * 60)
    print(f"Total de canais para adicionar: {len(CANAIS)}")
    print()

    for canal in CANAIS:
        subnicho = canal["subnicho"]
        stats[subnicho]["total"] += 1

        try:
            # Limpar URL
            canal["url_canal"] = limpar_url_canal(canal["url_canal"])

            # Adicionar campos obrigatórios
            canal["nicho"] = "Dark"
            canal["data_adicionado"] = datetime.now(tz=datetime.now().astimezone().tzinfo).isoformat()

            # Verificar se canal já existe
            existing = client.supabase.table("canais_monitorados")\
                .select("id, nome_canal")\
                .eq("url_canal", canal["url_canal"])\
                .execute()

            if existing.data:
                print(f"[!] Canal já existe: {canal['nome_canal']} ({subnicho})")
                stats[subnicho]["erro"] += 1
                erros.append(f"Já existe: {canal['nome_canal']}")
                continue

            # Inserir canal
            response = client.supabase.table("canais_monitorados").insert(canal).execute()

            if response.data:
                print(f"[OK] Adicionado: {canal['nome_canal']} ({subnicho} - {canal['lingua']})")
                stats[subnicho]["sucesso"] += 1
            else:
                print(f"[ERRO] Erro ao adicionar: {canal['nome_canal']}")
                stats[subnicho]["erro"] += 1
                erros.append(f"Erro insert: {canal['nome_canal']}")

        except Exception as e:
            print(f"[ERRO] Erro ao processar {canal['nome_canal']}: {e}")
            stats[subnicho]["erro"] += 1
            erros.append(f"Exception {canal['nome_canal']}: {str(e)}")

    # Relatório final
    print("\n" + "=" * 60)
    print("RELATÓRIO FINAL")
    print("=" * 60)

    for subnicho, dados in stats.items():
        if dados["total"] > 0:
            print(f"\n{subnicho}:")
            print(f"  Total: {dados['total']}")
            print(f"  [OK] Sucesso: {dados['sucesso']}")
            print(f"  [X] Erro: {dados['erro']}")

    # Total geral
    total_geral = sum(s["total"] for s in stats.values())
    total_sucesso = sum(s["sucesso"] for s in stats.values())
    total_erro = sum(s["erro"] for s in stats.values())

    print("\n" + "-" * 40)
    print(f"TOTAL GERAL:")
    print(f"  Tentados: {total_geral}")
    print(f"  [OK] Adicionados: {total_sucesso}")
    print(f"  [X] Erros: {total_erro}")

    if erros:
        print("\n" + "=" * 60)
        print("DETALHES DOS ERROS:")
        print("=" * 60)
        for erro in erros:
            print(f"  - {erro}")

    print("\n" + "=" * 60)
    print("PROCESSO CONCLUÍDO!")
    print("=" * 60)

if __name__ == "__main__":
    adicionar_canais()
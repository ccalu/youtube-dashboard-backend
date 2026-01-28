#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script simplificado para coleta completa de comentários
Data: 28/01/2025
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from supabase import create_client, Client
from collector import YouTubeCollector

# Configurar encoding UTF-8 no Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

async def main():
    print("=" * 60)
    print("COLETA COMPLETA DE COMENTÁRIOS")
    print("=" * 60)
    print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    # Conectar ao Supabase
    print("\n[*] Conectando ao Supabase...")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Buscar nossos canais
    print("[*] Buscando nossos canais...")
    result = supabase.table('canais_monitorados').select(
        'id, nome_canal, url_canal, custom_url'
    ).eq('tipo', 'nosso').execute()

    canais = result.data or []
    print(f"[OK] {len(canais)} canais encontrados")

    # Inicializar coletor
    print("[*] Inicializando coletor...")
    collector = YouTubeCollector()
    collector.supabase = supabase  # Passar supabase para o coletor

    # Estatísticas
    total_videos = 0
    total_comments = 0
    canais_processados = 0

    print("\n" + "=" * 60)

    for i, canal in enumerate(canais, 1):
        nome = canal['nome_canal']
        url = canal.get('url_canal', '')
        custom_url = canal.get('custom_url', '')

        # Extrair channel ID
        channel_id = None
        if custom_url and custom_url.startswith('@'):
            channel_id = custom_url
        elif '@' in url:
            channel_id = '@' + url.split('@')[1].split('/')[0].split('?')[0]
        elif '/channel/' in url:
            channel_id = url.split('/channel/')[1].split('/')[0].split('?')[0]

        if not channel_id:
            print(f"[{i}/{len(canais)}] {nome}: Sem channel ID")
            continue

        print(f"\n[{i}/{len(canais)}] Processando: {nome}")
        print(f"   Channel ID: {channel_id}")

        try:
            # Buscar dados do canal
            stats, videos = await collector.get_canal_data(channel_id, nome)

            if not videos:
                print("   [!] Sem vídeos")
                continue

            # Filtrar vídeos dos últimos 30 dias
            data_limite = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
            videos_recentes = []

            for video in videos:
                published = video.get('snippet', {}).get('publishedAt', '')
                if published and published >= data_limite:
                    videos_recentes.append(video)

            print(f"   [*] {len(videos_recentes)} vídeos dos últimos 30 dias")

            # Processar comentários
            canal_comments = 0
            for j, video in enumerate(videos_recentes, 1):
                video_id = video.get('id', {}).get('videoId') or video.get('id')
                title = video.get('snippet', {}).get('title', '')

                if not video_id:
                    continue

                # Buscar comentários (máximo 100)
                comments = await collector.get_video_comments(video_id, title, max_results=100)

                if comments:
                    canal_comments += len(comments)
                    if j % 5 == 0 or j == len(videos_recentes):
                        print(f"      Processados {j}/{len(videos_recentes)} vídeos, {canal_comments} comentários até agora")

            total_videos += len(videos_recentes)
            total_comments += canal_comments
            canais_processados += 1

            print(f"   [OK] {canal_comments} comentários coletados de {len(videos_recentes)} vídeos")

        except Exception as e:
            print(f"   [X] Erro: {str(e)[:100]}")

    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO DA COLETA:")
    print(f"  Canais processados: {canais_processados}/{len(canais)}")
    print(f"  Total de vídeos: {total_videos}")
    print(f"  Total de comentários: {total_comments}")

    # Verificar banco
    result = supabase.table('video_comments').select('id', count='exact').execute()
    total_db = result.count or 0

    result = supabase.table('video_comments').select(
        'id', count='exact'
    ).gte('collected_at', datetime.now().strftime('%Y-%m-%d')).execute()
    hoje = result.count or 0

    print(f"\nBANCO DE DADOS:")
    print(f"  Total geral: {total_db} comentários")
    print(f"  Coletados hoje: {hoje} comentários")
    print("=" * 60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n[X] ERRO: {e}")
        import traceback
        traceback.print_exc()
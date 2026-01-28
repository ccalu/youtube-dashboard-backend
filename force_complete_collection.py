#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para forçar coleta manual completa de comentários
Data: 28/01/2025

Este script vai coletar comentários de TODOS os vídeos dos últimos 30 dias
de TODOS os nossos canais, sem limites de vídeos e com 100 comentários por vídeo.
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from supabase import create_client, Client
from collector import YouTubeCollector
import json

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
    """
    Força coleta completa de comentários
    """
    print("=" * 60)
    print("COLETA MANUAL COMPLETA DE COMENTÁRIOS")
    print("=" * 60)
    print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("-" * 60)

    # Conectar ao Supabase
    print("\n[*] Conectando ao Supabase...")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Buscar todos os nossos canais
    print("[*] Buscando nossos canais...")
    result = supabase.table('canais_monitorados').select(
        'id, nome_canal, url_canal, custom_url'
    ).eq('tipo', 'nosso').execute()

    canais = result.data or []
    print(f"[OK] Encontrados {len(canais)} canais nossos")

    if not canais:
        print("[X] Nenhum canal encontrado!")
        return

    # Inicializar coletor
    print("\n[*] Inicializando coletor YouTube...")
    collector = YouTubeCollector(supabase)

    # Estatísticas
    total_videos = 0
    total_comments = 0
    canais_com_comentarios = 0
    erros = []

    print("\n[*] INICIANDO COLETA...")
    print("-" * 60)

    for i, canal in enumerate(canais, 1):
        canal_id = canal['id']
        nome_canal = canal['nome_canal']

        # Extrair channel_id da URL ou custom_url
        url_canal = canal.get('url_canal', '')
        custom_url = canal.get('custom_url', '')

        # Tentar extrair o @username ou channel ID
        channel_id = None
        if custom_url and custom_url.startswith('@'):
            channel_id = custom_url
        elif url_canal:
            if '@' in url_canal:
                channel_id = '@' + url_canal.split('@')[1].split('/')[0]
            elif '/channel/' in url_canal:
                channel_id = url_canal.split('/channel/')[1].split('/')[0]
            elif '/c/' in url_canal:
                channel_id = url_canal.split('/c/')[1].split('/')[0]

        if not channel_id:
            print(f"\n[{i}/{len(canais)}] PULANDO {nome_canal} - sem channel ID")
            continue

        print(f"\n[{i}/{len(canais)}] Processando: {nome_canal} ({channel_id})")

        try:
            # Buscar vídeos dos últimos 30 dias
            data_limite = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()

            # Buscar dados do canal e vídeos
            stats, videos_data = await collector.get_canal_data(channel_id)

            if not videos_data:
                print(f"   [!] Nenhum vídeo encontrado")
                continue

            # Filtrar vídeos dos últimos 30 dias (SEM LIMITE!)
            videos_recentes = []
            for video in videos_data:
                try:
                    published_at = video.get('snippet', {}).get('publishedAt', '')
                    if published_at and published_at >= data_limite:
                        videos_recentes.append(video)
                except:
                    continue

            print(f"   [*] {len(videos_recentes)} vídeos dos últimos 30 dias")

            if not videos_recentes:
                continue

            videos_com_comentarios = 0
            comentarios_canal = 0

            # Processar TODOS os vídeos
            for j, video in enumerate(videos_recentes, 1):
                video_id = video['id'].get('videoId') if 'id' in video else video.get('id')
                video_title = video.get('snippet', {}).get('title', 'Sem título')

                if not video_id:
                    continue

                # Buscar comentários (máximo 100 por vídeo)
                comments = await collector.get_video_comments(video_id, video_title, max_results=100)

                if comments:
                    videos_com_comentarios += 1
                    comentarios_canal += len(comments)
                    print(f"      [{j}/{len(videos_recentes)}] {len(comments)} comentários: {video_title[:50]}...")

                    # Salvar comentários no banco
                    for comment in comments:
                        try:
                            # Preparar dados do comentário
                            comment_data = {
                                'comment_id': comment.get('id'),
                                'video_id': video_id,
                                'video_title': video_title,
                                'canal_id': canal_id,
                                'author_name': comment.get('snippet', {}).get('authorDisplayName'),
                                'author_channel_id': comment.get('snippet', {}).get('authorChannelId', {}).get('value'),
                                'comment_text_original': comment.get('snippet', {}).get('textDisplay'),
                                'like_count': comment.get('snippet', {}).get('likeCount', 0),
                                'reply_count': comment.get('snippet', {}).get('totalReplyCount', 0),
                                'is_reply': False,
                                'published_at': comment.get('snippet', {}).get('publishedAt'),
                                'collected_at': datetime.now(timezone.utc).isoformat(),
                                'is_translated': False,
                                'is_responded': False
                            }

                            # Verificar se comentário já existe
                            existing = supabase.table('video_comments').select(
                                'id'
                            ).eq('comment_id', comment_data['comment_id']).execute()

                            if not existing.data:
                                # Inserir novo comentário
                                supabase.table('video_comments').insert(comment_data).execute()

                        except Exception as e:
                            print(f"      [X] Erro ao salvar comentário: {e}")

            total_videos += len(videos_recentes)
            total_comments += comentarios_canal

            if comentarios_canal > 0:
                canais_com_comentarios += 1
                print(f"   [OK] Total: {comentarios_canal} comentários de {videos_com_comentarios} vídeos")

            # Atualizar último comentário coletado
            if videos_recentes:
                latest_published = max([v.get('snippet', {}).get('publishedAt', '') for v in videos_recentes])
                supabase.table('canais_monitorados').update({
                    'ultimo_comentario_coletado': datetime.now(timezone.utc).isoformat()
                }).eq('id', canal_id).execute()

        except Exception as e:
            print(f"   [X] Erro: {e}")
            erros.append({'canal': nome_canal, 'erro': str(e)})

    # Resumo final
    print("\n" + "=" * 60)
    print("RESUMO DA COLETA")
    print("=" * 60)
    print(f"✅ Canais processados: {len(canais)}")
    print(f"✅ Canais com comentários: {canais_com_comentarios}")
    print(f"✅ Total de vídeos analisados: {total_videos}")
    print(f"✅ Total de comentários coletados: {total_comments}")

    if erros:
        print(f"\n⚠️ Erros encontrados: {len(erros)}")
        for erro in erros[:5]:
            print(f"   - {erro['canal']}: {erro['erro'][:50]}...")

    # Verificar total no banco
    print("\n[*] Verificando totais no banco de dados...")

    result = supabase.table('video_comments').select(
        'id', count='exact'
    ).execute()
    total_db = result.count or 0

    result = supabase.table('video_comments').select(
        'id', count='exact'
    ).gte('collected_at', datetime.now().strftime('%Y-%m-%d')).execute()
    hoje_db = result.count or 0

    print(f"\n📊 ESTATÍSTICAS DO BANCO:")
    print(f"   Total de comentários: {total_db}")
    print(f"   Coletados hoje: {hoje_db}")

    print("\n[OK] COLETA COMPLETA FINALIZADA!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n[X] ERRO FATAL: {e}")
        import traceback
        traceback.print_exc()
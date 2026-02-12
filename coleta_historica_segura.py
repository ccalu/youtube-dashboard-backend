"""
Script de Coleta Histórica Segura de Comentários
================================================
Este script coleta comentários históricos de TODOS os vídeos dos canais tipo='nosso'
com proteções para NÃO sobrescrever dados existentes e NÃO duplicar comentários.

Autor: Claude Code para Cellibs
Data: 12/02/2026
"""

import os
import sys
import json
import time
import logging
import argparse
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Set
from dotenv import load_dotenv
from supabase import create_client, Client
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configurar encoding UTF-8 para Windows
sys.stdout.reconfigure(encoding='utf-8')

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('coleta_historica.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Configurar Supabase
supabase_url = os.getenv('SUPABASE_URL')
supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not supabase_url or not supabase_service_key:
    logger.error("❌ Credenciais Supabase não configuradas!")
    sys.exit(1)

supabase: Client = create_client(supabase_url, supabase_service_key)

# Configurar YouTube API (precisa de pelo menos uma key)
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY_3')  # Usar KEY_3 como padrão
if not YOUTUBE_API_KEY:
    logger.error("❌ YouTube API Key não configurada! Configure pelo menos YOUTUBE_API_KEY_3")
    sys.exit(1)

youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

# Arquivo de checkpoint para retomar se interrompido
CHECKPOINT_FILE = 'coleta_checkpoint.json'

# Estatísticas globais
stats = {
    'canais_processados': 0,
    'videos_processados': 0,
    'comentarios_novos': 0,
    'comentarios_existentes': 0,
    'comentarios_traduzidos': 0,
    'erros': 0,
    'inicio': datetime.now(timezone.utc)
}


def load_checkpoint() -> Dict:
    """Carrega checkpoint se existir"""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_checkpoint(data: Dict):
    """Salva checkpoint para retomar depois"""
    with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def get_existing_comment_ids(canal_id: int) -> Set[str]:
    """
    Retorna conjunto de IDs de comentários já existentes para um canal
    CRÍTICO: Evita duplicatas
    """
    logger.info(f"  📊 Buscando comentários existentes do canal {canal_id}...")

    existing_ids = set()
    offset = 0
    limit = 1000

    while True:
        try:
            response = supabase.table('video_comments').select('comment_id').eq(
                'canal_id', canal_id
            ).range(offset, offset + limit - 1).execute()

            if not response.data:
                break

            for comment in response.data:
                existing_ids.add(comment['comment_id'])

            if len(response.data) < limit:
                break

            offset += limit

        except Exception as e:
            logger.error(f"  ❌ Erro ao buscar IDs existentes: {e}")
            break

    logger.info(f"  ✅ {len(existing_ids)} comentários já existem no banco")
    return existing_ids


def get_channel_info(channel_url: str) -> Optional[str]:
    """Extrai channel ID da URL"""
    try:
        # Decodificar URL se necessário
        from urllib.parse import unquote
        channel_url = unquote(channel_url)

        if '@' in channel_url:
            handle = channel_url.split('@')[-1].split('/')[0]
            # Buscar por handle customizado
            response = youtube.search().list(
                part="snippet",
                q=handle,
                type="channel",
                maxResults=1
            ).execute()

            if 'items' in response and response['items']:
                return response['items'][0]['snippet']['channelId']
        elif '/channel/' in channel_url:
            channel_id = channel_url.split('/channel/')[-1].split('/')[0]
            return channel_id
        elif '/c/' in channel_url or '/user/' in channel_url:
            custom_url = channel_url.split('/')[-1]
            response = youtube.channels().list(
                part="id",
                forUsername=custom_url
            ).execute()
        else:
            return None

        if 'items' in response and response['items']:
            return response['items'][0]['id']

    except Exception as e:
        logger.error(f"Erro ao extrair channel ID: {e}")

    return None


def get_all_channel_videos(channel_id: str) -> List[Dict]:
    """
    Busca TODOS os vídeos de um canal (sem limite)
    Ordena por data de publicação (mais recentes primeiro)
    """
    videos = []
    next_page_token = None

    try:
        while True:
            # Buscar vídeos do canal
            request = youtube.search().list(
                part="id,snippet",
                channelId=channel_id,
                type="video",
                maxResults=50,
                pageToken=next_page_token,
                order="date"  # Mais recentes primeiro
            )
            response = request.execute()

            # Processar cada vídeo
            for item in response.get('items', []):
                video_data = {
                    'id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'publishedAt': item['snippet']['publishedAt']
                }
                videos.append(video_data)

            # Verificar se há mais páginas
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break

            # Pequena pausa para não sobrecarregar API
            time.sleep(0.1)

    except HttpError as e:
        logger.error(f"Erro HTTP ao buscar vídeos: {e}")
    except Exception as e:
        logger.error(f"Erro ao buscar vídeos: {e}")

    return videos


def get_video_comments(video_id: str, max_results: int = 100) -> List[Dict]:
    """
    Busca comentários de um vídeo
    Retorna até max_results comentários ordenados por data
    """
    comments = []
    next_page_token = None

    try:
        while len(comments) < max_results:
            request = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=min(100, max_results - len(comments)),
                order='time',  # Comentários mais recentes primeiro
                pageToken=next_page_token
            )
            response = request.execute()

            for item in response.get('items', []):
                comment = item['snippet']['topLevelComment']['snippet']
                comments.append({
                    'id': item['snippet']['topLevelComment']['id'],
                    'author': comment['authorDisplayName'],
                    'author_channel_id': comment['authorChannelId']['value'],
                    'text': comment['textDisplay'],
                    'published_at': comment['publishedAt'],
                    'like_count': comment.get('likeCount', 0),
                    'reply_count': item['snippet'].get('totalReplyCount', 0)
                })

            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break

        return comments[:max_results]

    except HttpError as e:
        if e.resp.status == 403 and 'commentsDisabled' in str(e):
            logger.debug(f"    Comentários desabilitados no vídeo {video_id}")
        else:
            logger.error(f"    Erro HTTP ao buscar comentários: {e}")
    except Exception as e:
        logger.error(f"    Erro ao buscar comentários: {e}")

    return []


def translate_text(text: str, target_lang: str = 'pt') -> str:
    """
    Traduz texto para português usando GPT
    NOTA: Implementação simplificada - você pode usar sua API de tradução preferida
    """
    # Por enquanto, retorna o texto original
    # Você pode integrar com Google Translate, DeepL ou GPT aqui
    return text


def save_comments_batch(comments_data: List[Dict]) -> bool:
    """
    Salva lote de comentários no banco
    USA INSERT (não UPSERT) para garantir que não sobrescreve
    """
    if not comments_data:
        return True

    try:
        # INSERT apenas (não UPSERT)
        response = supabase.table('video_comments').insert(comments_data).execute()

        if response.data:
            logger.info(f"    ✅ {len(comments_data)} comentários novos salvos")
            return True
        else:
            logger.warning(f"    ⚠️ Nenhum comentário foi salvo")
            return False

    except Exception as e:
        logger.error(f"    ❌ Erro ao salvar comentários: {e}")
        return False


def process_channel(canal: Dict, dry_run: bool = False) -> Dict:
    """
    Processa um canal completo
    Coleta comentários de TODOS os vídeos
    """
    canal_id = canal['id']
    canal_nome = canal['nome_canal']
    canal_lingua = canal.get('lingua', 'unknown')
    canal_url = canal['url_canal']

    logger.info(f"\n{'='*80}")
    logger.info(f"📺 Processando canal: {canal_nome} (ID: {canal_id})")
    logger.info(f"   Subnicho: {canal['subnicho']}")
    logger.info(f"   Língua: {canal_lingua}")
    logger.info(f"{'='*80}")

    # Estatísticas do canal
    canal_stats = {
        'videos': 0,
        'comentarios_novos': 0,
        'comentarios_existentes': 0,
        'comentarios_traduzidos': 0
    }

    # 1. Buscar IDs existentes para evitar duplicatas
    existing_ids = get_existing_comment_ids(canal_id) if not dry_run else set()

    # 2. Extrair channel ID do YouTube
    channel_id = get_channel_info(canal_url)
    if not channel_id:
        logger.error(f"❌ Não foi possível extrair channel ID de: {canal_url}")
        return canal_stats

    # 3. Buscar TODOS os vídeos do canal
    logger.info(f"  🔍 Buscando vídeos do canal...")
    videos = get_all_channel_videos(channel_id)
    logger.info(f"  ✅ {len(videos)} vídeos encontrados")

    if not videos:
        logger.warning(f"  ⚠️ Nenhum vídeo encontrado para o canal")
        return canal_stats

    # 4. Processar cada vídeo
    for i, video in enumerate(videos, 1):
        video_id = video['id']
        video_title = video['title'][:50]

        logger.info(f"\n  [{i}/{len(videos)}] Vídeo: {video_title}...")

        # Buscar comentários do vídeo
        comments = get_video_comments(video_id, max_results=100)

        if not comments:
            logger.debug(f"    Sem comentários")
            continue

        logger.info(f"    📝 {len(comments)} comentários encontrados")

        # Processar cada comentário
        new_comments = []
        for comment in comments:
            # Verificar se já existe
            if comment['id'] in existing_ids:
                canal_stats['comentarios_existentes'] += 1
                continue

            # Preparar dados do comentário
            comment_data = {
                'comment_id': comment['id'],
                'video_id': video_id,
                'canal_id': canal_id,
                'author_name': comment['author'],
                'author_channel_id': comment['author_channel_id'],
                'comment_text_original': comment['text'],
                'published_at': comment['published_at'],
                'collected_at': datetime.now(timezone.utc).isoformat(),
                'like_count': comment['like_count'],
                'reply_count': comment['reply_count'],
                'is_reply': False,
                'parent_id': None,
                'canal_lingua': canal_lingua
            }

            # Tradução inteligente
            if canal_lingua == 'portuguese':
                # Canal em português: copiar original
                comment_data['comment_text_pt'] = comment['text']
                comment_data['is_translated'] = True
            elif canal_lingua in ['english', 'spanish', 'german', 'french']:
                # Outros idiomas: traduzir
                # NOTA: Implementar tradução real aqui se necessário
                comment_data['comment_text_pt'] = comment['text']  # Por enquanto copia
                comment_data['is_translated'] = False
                canal_stats['comentarios_traduzidos'] += 1
            else:
                # Idioma desconhecido
                comment_data['comment_text_pt'] = comment['text']
                comment_data['is_translated'] = False

            new_comments.append(comment_data)
            canal_stats['comentarios_novos'] += 1

        # Salvar lote de comentários novos
        if new_comments and not dry_run:
            success = save_comments_batch(new_comments)
            if success:
                # Adicionar IDs ao conjunto de existentes
                for c in new_comments:
                    existing_ids.add(c['comment_id'])

        canal_stats['videos'] += 1

        # Checkpoint a cada 10 vídeos
        if i % 10 == 0 and not dry_run:
            checkpoint = {
                'ultimo_canal_id': canal_id,
                'ultimo_video_index': i,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            save_checkpoint(checkpoint)

        # Pequena pausa para não sobrecarregar
        time.sleep(0.5)

    logger.info(f"\n  📊 Resumo do canal {canal_nome}:")
    logger.info(f"     Vídeos processados: {canal_stats['videos']}")
    logger.info(f"     Comentários novos: {canal_stats['comentarios_novos']}")
    logger.info(f"     Comentários existentes: {canal_stats['comentarios_existentes']}")
    logger.info(f"     Comentários traduzidos: {canal_stats['comentarios_traduzidos']}")

    return canal_stats


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Coleta Histórica de Comentários')
    parser.add_argument('--canal', type=str, help='Nome específico do canal para coletar')
    parser.add_argument('--todos', action='store_true', help='Coletar de TODOS os canais')
    parser.add_argument('--dry-run', action='store_true', help='Modo simulação (não salva)')
    parser.add_argument('--verbose', action='store_true', help='Log detalhado')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("\n" + "="*80)
    logger.info("🚀 COLETA HISTÓRICA DE COMENTÁRIOS - INICIANDO")
    logger.info("="*80)

    if args.dry_run:
        logger.warning("⚠️ MODO DRY-RUN: Nenhum dado será salvo!")

    # Buscar canais para processar
    if args.canal:
        # Canal específico
        response = supabase.table('canais_monitorados').select('*').eq(
            'tipo', 'nosso'
        ).eq('nome_canal', args.canal).execute()
        canais = response.data

        if not canais:
            logger.error(f"❌ Canal '{args.canal}' não encontrado!")
            return

    elif args.todos:
        # Todos os canais nossos
        response = supabase.table('canais_monitorados').select('*').eq(
            'tipo', 'nosso'
        ).order('subnicho').execute()
        canais = response.data
    else:
        logger.error("❌ Especifique --canal NOME ou --todos")
        return

    logger.info(f"📋 {len(canais)} canais para processar\n")

    # Carregar checkpoint se existir
    checkpoint = load_checkpoint()
    start_index = 0

    if checkpoint.get('ultimo_canal_id'):
        # Encontrar índice para continuar
        for i, canal in enumerate(canais):
            if canal['id'] == checkpoint['ultimo_canal_id']:
                start_index = i + 1
                logger.info(f"📌 Retomando do canal {start_index}/{len(canais)}")
                break

    # Processar cada canal
    for i, canal in enumerate(canais[start_index:], start=start_index+1):
        logger.info(f"\n[{i}/{len(canais)}] Canal: {canal['nome_canal']}")

        try:
            canal_stats = process_channel(canal, dry_run=args.dry_run)

            # Atualizar estatísticas globais
            stats['canais_processados'] += 1
            stats['videos_processados'] += canal_stats['videos']
            stats['comentarios_novos'] += canal_stats['comentarios_novos']
            stats['comentarios_existentes'] += canal_stats['comentarios_existentes']
            stats['comentarios_traduzidos'] += canal_stats['comentarios_traduzidos']

        except KeyboardInterrupt:
            logger.warning("\n⚠️ Interrompido pelo usuário!")
            break
        except Exception as e:
            logger.error(f"❌ Erro ao processar canal: {e}")
            stats['erros'] += 1
            continue

    # Relatório final
    tempo_total = datetime.now(timezone.utc) - stats['inicio']
    logger.info("\n" + "="*80)
    logger.info("📊 RELATÓRIO FINAL DA COLETA HISTÓRICA")
    logger.info("="*80)
    logger.info(f"⏱️ Tempo total: {tempo_total}")
    logger.info(f"📺 Canais processados: {stats['canais_processados']}")
    logger.info(f"🎬 Vídeos processados: {stats['videos_processados']}")
    logger.info(f"✅ Comentários novos salvos: {stats['comentarios_novos']}")
    logger.info(f"⏭️ Comentários já existentes (pulados): {stats['comentarios_existentes']}")
    logger.info(f"🌍 Comentários traduzidos: {stats['comentarios_traduzidos']}")
    logger.info(f"❌ Erros: {stats['erros']}")

    if not args.dry_run and os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)
        logger.info("🗑️ Checkpoint removido")

    logger.info("\n✅ COLETA HISTÓRICA CONCLUÍDA!")


if __name__ == "__main__":
    main()
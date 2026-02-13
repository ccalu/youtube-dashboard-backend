"""
Script de Coleta Histórica Completa com Tradução
================================================
Este script:
1. Coleta TODOS os comentários de TODOS os vídeos
2. Salva primeiro SEM traduzir
3. Depois traduz em lote usando o sistema existente

Autor: Claude Code para Cellibs
Data: 12/02/2026
"""

import os
import sys
import json
import time
import logging
import asyncio
import argparse
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Set
from dotenv import load_dotenv
from supabase import create_client, Client
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from urllib.parse import unquote

# Configurar encoding UTF-8 para Windows
sys.stdout.reconfigure(encoding='utf-8')

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('coleta_historica_completa.log', encoding='utf-8'),
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

# Configurar YouTube API com rotação de chaves
class YouTubeAPIManager:
    """Gerenciador de API Keys com rotação automática"""
    def __init__(self):
        # Lista de todas as API keys disponíveis
        self.api_keys = []

        # Keys 3 a 10
        for i in range(3, 11):
            key = os.getenv(f'YOUTUBE_API_KEY_{i}')
            if key:
                self.api_keys.append(key)

        # Keys 21 a 32
        for i in range(21, 33):
            key = os.getenv(f'YOUTUBE_API_KEY_{i}')
            if key:
                self.api_keys.append(key)

        if not self.api_keys:
            logger.error("❌ Nenhuma YouTube API Key configurada!")
            sys.exit(1)

        logger.info(f"✅ {len(self.api_keys)} API Keys configuradas para rotação")

        self.current_key_index = 0
        self.youtube = build('youtube', 'v3', developerKey=self.api_keys[0])
        self.requests_count = 0
        self.max_requests_per_key = 500  # Mudar de chave a cada 500 requests para distribuir uso

    def rotate_key(self):
        """Rotaciona para próxima API key"""
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        new_key = self.api_keys[self.current_key_index]
        self.youtube = build('youtube', 'v3', developerKey=new_key)
        logger.info(f"🔄 Rotacionando para API Key {self.current_key_index + 1}/{len(self.api_keys)}")
        self.requests_count = 0

    def execute_request(self, request):
        """Executa request com tratamento de erro e rotação de chave"""
        max_retries = len(self.api_keys)
        retry_count = 0

        while retry_count < max_retries:
            try:
                # Rotacionar preventivamente a cada N requests
                self.requests_count += 1
                if self.requests_count >= self.max_requests_per_key:
                    self.rotate_key()

                return request.execute()

            except HttpError as e:
                if e.resp.status == 403 and 'quotaExceeded' in str(e):
                    logger.warning(f"⚠️ Quota excedida na chave {self.current_key_index + 1}")
                    self.rotate_key()
                    retry_count += 1
                    if retry_count < max_retries:
                        logger.info(f"🔄 Tentando com nova chave...")
                        # Reconstruir request com nova API
                        continue
                else:
                    raise e
            except Exception as e:
                logger.error(f"❌ Erro na requisição: {e}")
                raise e

        logger.error("❌ Todas as API keys estão com quota excedida!")
        raise Exception("Todas as API keys estão com quota excedida")

# Inicializar gerenciador de API
api_manager = YouTubeAPIManager()
youtube = api_manager.youtube

# Arquivo de checkpoint
CHECKPOINT_FILE = 'coleta_checkpoint.json'

# Estatísticas globais
stats = {
    'canais_processados': 0,
    'videos_processados': 0,
    'comentarios_novos': 0,
    'comentarios_existentes': 0,
    'comentarios_para_traduzir': 0,
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
    """Salva checkpoint"""
    with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def get_existing_comment_ids(canal_id: int) -> Set[str]:
    """Retorna IDs de comentários já existentes"""
    logger.info(f"  📊 Verificando comentários existentes...")

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
            logger.error(f"  ❌ Erro ao buscar IDs: {e}")
            break

    logger.info(f"  ✅ {len(existing_ids)} comentários já existem")
    return existing_ids


def get_channel_info(channel_url: str) -> Optional[str]:
    """Extrai channel ID da URL"""
    try:
        # Decodificar URL
        channel_url = unquote(channel_url)

        if '@' in channel_url:
            handle = channel_url.split('@')[-1].split('/')[0]
            request = api_manager.youtube.search().list(
                part="snippet",
                q=handle,
                type="channel",
                maxResults=1
            )
            response = api_manager.execute_request(request)

            if 'items' in response and response['items']:
                return response['items'][0]['snippet']['channelId']

        elif '/channel/' in channel_url:
            return channel_url.split('/channel/')[-1].split('/')[0]

    except Exception as e:
        logger.error(f"Erro ao extrair channel ID: {e}")

    return None


def get_all_channel_videos(channel_id: str) -> List[Dict]:
    """Busca TODOS os vídeos do canal"""
    videos = []
    next_page_token = None

    try:
        while True:
            request = api_manager.youtube.search().list(
                part="id,snippet",
                channelId=channel_id,
                type="video",
                maxResults=50,
                pageToken=next_page_token,
                order="date"
            )
            response = api_manager.execute_request(request)

            for item in response.get('items', []):
                videos.append({
                    'id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'publishedAt': item['snippet']['publishedAt']
                })

            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break

            time.sleep(0.1)

    except Exception as e:
        logger.error(f"Erro ao buscar vídeos: {e}")

    return videos


def get_video_comments(video_id: str, max_results: int = 100) -> List[Dict]:
    """Busca até 100 comentários de um vídeo"""
    comments = []
    next_page_token = None

    try:
        while len(comments) < max_results:
            request = api_manager.youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=min(100, max_results - len(comments)),
                order='time',
                pageToken=next_page_token
            )
            response = api_manager.execute_request(request)

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
            logger.debug(f"    Comentários desabilitados")
        else:
            logger.error(f"    Erro HTTP: {e}")
    except Exception as e:
        logger.error(f"    Erro: {e}")

    return []


def save_comments_batch(comments_data: List[Dict]) -> bool:
    """Salva lote de comentários (INSERT apenas novos)"""
    if not comments_data:
        return True

    try:
        # INSERT (não UPSERT) para garantir que não sobrescreve
        response = supabase.table('video_comments').insert(comments_data).execute()

        if response.data:
            logger.info(f"    ✅ {len(comments_data)} comentários salvos")
            return True

    except Exception as e:
        # Se der erro de duplicata, tenta um por um
        if 'duplicate key' in str(e).lower():
            salvos = 0
            for comment in comments_data:
                try:
                    response = supabase.table('video_comments').insert(comment).execute()
                    if response.data:
                        salvos += 1
                except:
                    pass  # Já existe, pular
            logger.info(f"    ✅ {salvos}/{len(comments_data)} comentários salvos")
            return salvos > 0
        else:
            logger.error(f"    ❌ Erro ao salvar: {e}")

    return False


def process_channel(canal: Dict, dry_run: bool = False) -> Dict:
    """Processa um canal - FASE 1: Apenas coleta, SEM tradução"""
    canal_id = canal['id']
    canal_nome = canal['nome_canal']
    canal_lingua = canal.get('lingua', 'unknown')
    canal_url = canal['url_canal']

    logger.info(f"\n{'='*80}")
    logger.info(f"📺 CANAL: {canal_nome} (ID: {canal_id})")
    logger.info(f"   Subnicho: {canal['subnicho']}")
    logger.info(f"   Língua: {canal_lingua}")
    logger.info(f"{'='*80}")

    canal_stats = {
        'videos': 0,
        'comentarios_novos': 0,
        'comentarios_existentes': 0,
        'precisa_traducao': 0
    }

    # 1. Buscar comentários existentes
    existing_ids = get_existing_comment_ids(canal_id) if not dry_run else set()

    # 2. Extrair channel ID
    channel_id = get_channel_info(canal_url)
    if not channel_id:
        logger.error(f"❌ Não foi possível extrair channel ID")
        return canal_stats

    # 3. Buscar TODOS os vídeos
    logger.info(f"  🔍 Buscando vídeos...")
    videos = get_all_channel_videos(channel_id)
    logger.info(f"  ✅ {len(videos)} vídeos encontrados")

    if not videos:
        return canal_stats

    # 4. Processar cada vídeo
    for i, video in enumerate(videos, 1):
        video_id = video['id']
        video_title = video['title'][:50]

        # Mostrar progresso
        if i % 10 == 0 or i == 1:
            logger.info(f"\n  📹 [{i}/{len(videos)}] {video_title}...")

        # Buscar comentários
        comments = get_video_comments(video_id, max_results=100)

        if not comments:
            continue

        # Processar apenas comentários NOVOS
        new_comments = []
        for comment in comments:
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
                'parent_comment_id': None  # Campo correto é parent_comment_id
                # Removido canal_lingua - não existe na tabela!
            }

            # FASE 1: Salvar SEM tradução
            if canal_lingua == 'portuguese':
                # Português: copiar original
                comment_data['comment_text_pt'] = comment['text']
                comment_data['is_translated'] = True
            else:
                # Outros idiomas: marcar para traduzir depois
                comment_data['comment_text_pt'] = None  # Será traduzido na FASE 2
                comment_data['is_translated'] = False
                canal_stats['precisa_traducao'] += 1

            new_comments.append(comment_data)
            canal_stats['comentarios_novos'] += 1

        # Salvar em lotes de 50
        if len(new_comments) >= 50:
            if not dry_run:
                success = save_comments_batch(new_comments[:50])
                if success:
                    for c in new_comments[:50]:
                        existing_ids.add(c['comment_id'])
            new_comments = new_comments[50:]

        canal_stats['videos'] += 1

        # Checkpoint periódico
        if i % 20 == 0 and not dry_run:
            checkpoint = {
                'canal_id': canal_id,
                'video_index': i,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            save_checkpoint(checkpoint)

        # Pausa pequena
        time.sleep(0.2)

    # Salvar comentários restantes
    if new_comments and not dry_run:
        save_comments_batch(new_comments)

    logger.info(f"\n  📊 RESUMO - {canal_nome}:")
    logger.info(f"     Vídeos: {canal_stats['videos']}")
    logger.info(f"     Novos: {canal_stats['comentarios_novos']}")
    logger.info(f"     Existentes: {canal_stats['comentarios_existentes']}")
    logger.info(f"     Para traduzir: {canal_stats['precisa_traducao']}")

    return canal_stats


async def traduzir_comentarios_pendentes():
    """FASE 2: Traduz todos os comentários pendentes"""
    logger.info("\n" + "="*80)
    logger.info("🌍 FASE 2: TRADUÇÃO DOS COMENTÁRIOS")
    logger.info("="*80)

    # Importar o sistema de tradução existente
    try:
        from main import traduzir_comentarios_canal

        # Buscar canais com comentários não traduzidos
        response = supabase.table('canais_monitorados').select(
            'id, nome_canal, lingua'
        ).eq('tipo', 'nosso').neq('lingua', 'portuguese').execute()

        canais_para_traduzir = response.data

        logger.info(f"\n📋 {len(canais_para_traduzir)} canais para traduzir")

        for canal in canais_para_traduzir:
            # Contar comentários não traduzidos
            count_response = supabase.table('video_comments').select(
                'id', count='exact'
            ).eq('canal_id', canal['id']).eq('is_translated', False).execute()

            if count_response.count > 0:
                logger.info(f"\n🔄 Traduzindo {count_response.count} comentários de {canal['nome_canal']}...")

                # Usar função existente do sistema
                await traduzir_comentarios_canal(canal['id'])

                logger.info(f"✅ Tradução concluída para {canal['nome_canal']}")

        logger.info("\n✅ FASE 2 CONCLUÍDA: Todos os comentários traduzidos!")

    except ImportError:
        logger.warning("⚠️ Sistema de tradução não disponível localmente")
        logger.info("Execute no Railway: POST /api/traduzir-comentarios-todos")


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Coleta Histórica Completa')
    parser.add_argument('--canal', type=str, help='Nome do canal específico')
    parser.add_argument('--todos', action='store_true', help='Processar TODOS os canais')
    parser.add_argument('--dry-run', action='store_true', help='Modo teste (não salva)')
    parser.add_argument('--traduzir', action='store_true', help='Executar tradução após coleta')

    args = parser.parse_args()

    logger.info("\n" + "="*80)
    logger.info("🚀 COLETA HISTÓRICA COMPLETA - INICIANDO")
    logger.info("="*80)

    if args.dry_run:
        logger.warning("⚠️ MODO DRY-RUN: Nada será salvo!")

    # Buscar canais
    if args.canal:
        response = supabase.table('canais_monitorados').select('*').eq(
            'tipo', 'nosso'
        ).eq('nome_canal', args.canal).execute()
        canais = response.data
    elif args.todos:
        response = supabase.table('canais_monitorados').select('*').eq(
            'tipo', 'nosso'
        ).order('subnicho').execute()
        canais = response.data
    else:
        logger.error("❌ Use --canal NOME ou --todos")
        return

    logger.info(f"📋 {len(canais)} canais para processar\n")

    # FASE 1: COLETA
    logger.info("="*80)
    logger.info("📥 FASE 1: COLETA DE COMENTÁRIOS")
    logger.info("="*80)

    # Processar cada canal
    for i, canal in enumerate(canais, 1):
        logger.info(f"\n[{i}/{len(canais)}] Processando...")

        try:
            canal_stats = process_channel(canal, dry_run=args.dry_run)

            stats['canais_processados'] += 1
            stats['videos_processados'] += canal_stats['videos']
            stats['comentarios_novos'] += canal_stats['comentarios_novos']
            stats['comentarios_existentes'] += canal_stats['comentarios_existentes']
            stats['comentarios_para_traduzir'] += canal_stats['precisa_traducao']

        except KeyboardInterrupt:
            logger.warning("\n⚠️ Interrompido pelo usuário!")
            break
        except Exception as e:
            logger.error(f"❌ Erro: {e}")
            stats['erros'] += 1

    # FASE 2: TRADUÇÃO (se solicitado)
    if args.traduzir and not args.dry_run:
        asyncio.run(traduzir_comentarios_pendentes())

    # Relatório final
    tempo_total = datetime.now(timezone.utc) - stats['inicio']
    logger.info("\n" + "="*80)
    logger.info("📊 RELATÓRIO FINAL")
    logger.info("="*80)
    logger.info(f"⏱️ Tempo: {tempo_total}")
    logger.info(f"📺 Canais: {stats['canais_processados']}")
    logger.info(f"🎬 Vídeos: {stats['videos_processados']}")
    logger.info(f"✅ Novos: {stats['comentarios_novos']}")
    logger.info(f"⏭️ Existentes: {stats['comentarios_existentes']}")
    logger.info(f"🌍 Para traduzir: {stats['comentarios_para_traduzir']}")
    logger.info(f"❌ Erros: {stats['erros']}")

    if not args.dry_run and os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)
        logger.info("🗑️ Checkpoint removido")

    logger.info("\n✅ COLETA CONCLUÍDA!")

    if stats['comentarios_para_traduzir'] > 0 and not args.traduzir:
        logger.info("\n💡 DICA: Execute com --traduzir para traduzir os comentários")


if __name__ == "__main__":
    main()
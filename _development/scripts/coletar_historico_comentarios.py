# -*- coding: utf-8 -*-
"""
Coleta historica completa de comentarios de todos os canais 'nosso'.
Usa INSERT (nao upsert) - comentarios existentes sao ignorados.
Sistema de checkpoint para retomar se parar.
"""
import os
import sys
import json
import asyncio
import requests
import logging
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from supabase import create_client

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

CHECKPOINT_FILE = '_runtime/coleta_historica_checkpoint.json'
DAYS_BACK = 30


def get_api_key():
    for i in list(range(7, 11)) + list(range(21, 25)):
        k = os.getenv(f'YOUTUBE_API_KEY_{i}')
        if k:
            return k
    return None


def load_checkpoint():
    try:
        with open(CHECKPOINT_FILE, 'r') as f:
            return json.load(f)
    except:
        return {'completed_canais': [], 'stats': {'novos': 0, 'existentes': 0, 'erros': 0}}


def save_checkpoint(data):
    os.makedirs(os.path.dirname(CHECKPOINT_FILE), exist_ok=True)
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def get_channel_videos(channel_id, api_key):
    """Busca videos dos ultimos 30 dias via playlistItems"""
    uploads_playlist = 'UU' + channel_id[2:]
    cutoff = (datetime.now(timezone.utc) - timedelta(days=DAYS_BACK)).isoformat()

    videos = []
    page_token = None

    while True:
        url = f'https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={uploads_playlist}&maxResults=50&key={api_key}'
        if page_token:
            url += f'&pageToken={page_token}'

        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            break

        data = resp.json()
        for item in data.get('items', []):
            pub = item['snippet'].get('publishedAt', '')
            if pub < cutoff:
                return videos  # Passou dos 30 dias, parar

            vid = item['snippet']['resourceId']['videoId']
            title = item['snippet']['title']
            videos.append({'videoId': vid, 'title': title, 'publishedAt': pub})

        page_token = data.get('nextPageToken')
        if not page_token:
            break

    return videos


def get_video_comments(video_id, api_key):
    """Busca todos os comentarios de um video"""
    all_comments = []
    page_token = None

    while True:
        url = f'https://www.googleapis.com/youtube/v3/commentThreads?part=snippet,replies&videoId={video_id}&maxResults=100&order=time&textFormat=plainText&key={api_key}'
        if page_token:
            url += f'&pageToken={page_token}'

        resp = requests.get(url, timeout=15)
        if resp.status_code == 403:
            # Comentarios desabilitados
            return []
        if resp.status_code != 200:
            return all_comments

        data = resp.json()
        for item in data.get('items', []):
            snippet = item['snippet']['topLevelComment']['snippet']
            all_comments.append({
                'comment_id': item['id'],
                'video_id': video_id,
                'author_name': snippet.get('authorDisplayName', ''),
                'comment_text_original': snippet.get('textOriginal', snippet.get('textDisplay', '')),
                'published_at': snippet.get('publishedAt', ''),
                'like_count': snippet.get('likeCount', 0),
                'reply_count': item['snippet'].get('totalReplyCount', 0),
                'is_reply': False,
            })

            # Replies
            if 'replies' in item:
                for reply in item['replies'].get('comments', []):
                    rs = reply['snippet']
                    all_comments.append({
                        'comment_id': reply['id'],
                        'video_id': video_id,
                        'author_name': rs.get('authorDisplayName', ''),
                        'comment_text_original': rs.get('textOriginal', rs.get('textDisplay', '')),
                        'published_at': rs.get('publishedAt', ''),
                        'like_count': rs.get('likeCount', 0),
                        'reply_count': 0,
                        'is_reply': True,
                        'parent_comment_id': item['id'],
                    })

        page_token = data.get('nextPageToken')
        if not page_token or len(all_comments) >= 1000:
            break

    return all_comments


def save_comments(video_id, canal_id, comments, is_portuguese):
    """Salva comentarios via INSERT (ignora existentes)"""
    if not comments:
        return 0

    # Buscar IDs existentes
    existing = supabase.table('video_comments').select('comment_id').eq('video_id', video_id).execute()
    existing_ids = set(r['comment_id'] for r in existing.data) if existing.data else set()

    new_comments = [c for c in comments if c['comment_id'] not in existing_ids]
    if not new_comments:
        return 0

    # Preparar records
    now = datetime.now(timezone.utc).isoformat()
    records = []
    for c in new_comments:
        record = {
            'comment_id': c['comment_id'],
            'video_id': video_id,
            'canal_id': canal_id,
            'author_name': c.get('author_name', ''),
            'comment_text_original': c.get('comment_text_original', ''),
            'published_at': c.get('published_at'),
            'like_count': c.get('like_count', 0),
            'reply_count': c.get('reply_count', 0),
            'is_reply': c.get('is_reply', False),
            'parent_comment_id': c.get('parent_comment_id'),
            'collected_at': now,
            'is_translated': is_portuguese,
            'comment_text_pt': c.get('comment_text_original', '') if is_portuguese else None,
        }
        records.append(record)

    # Inserir em batches de 50
    inserted = 0
    for i in range(0, len(records), 50):
        batch = records[i:i+50]
        try:
            supabase.table('video_comments').insert(batch).execute()
            inserted += len(batch)
        except Exception as e:
            # Se falhar em batch, tentar um por um
            for r in batch:
                try:
                    supabase.table('video_comments').insert(r).execute()
                    inserted += 1
                except:
                    pass

    return inserted


def main():
    api_key = get_api_key()
    if not api_key:
        print('[ERRO] Nenhuma API key disponivel')
        return

    checkpoint = load_checkpoint()
    completed = set(checkpoint.get('completed_canais', []))
    stats = checkpoint.get('stats', {'novos': 0, 'existentes': 0, 'erros': 0})

    # Buscar canais nossos
    canais = supabase.table('canais_monitorados').select('id, nome_canal, url_canal, lingua').eq('tipo', 'nosso').order('nome_canal').execute()

    total_canais = len(canais.data)
    print(f'\n{"="*70}')
    print(f'  COLETA HISTORICA DE COMENTARIOS ({total_canais} canais)')
    print(f'  Ultimos {DAYS_BACK} dias | INSERT (nao sobrescreve)')
    print(f'{"="*70}\n')

    if completed:
        print(f'Retomando... {len(completed)} canais ja concluidos\n')

    for idx, canal in enumerate(canais.data):
        canal_id = canal['id']
        nome = canal['nome_canal']
        lingua = (canal.get('lingua') or '').lower()
        is_portuguese = 'portug' in lingua or lingua in ('pt', 'pt-br')

        if str(canal_id) in completed:
            continue

        print(f'[{idx+1}/{total_canais}] {nome} ({"PT" if is_portuguese else lingua[:5]})')

        # Extrair channel_id do URL
        url = canal.get('url_canal', '')
        yt_channel_id = None

        if '/channel/' in url:
            yt_channel_id = url.split('/channel/')[-1].split('/')[0].split('?')[0]
        elif '/@' in url:
            # Resolver handle via API
            handle = url.split('/@')[-1].split('/')[0].split('?')[0]
            resolve_url = f'https://www.googleapis.com/youtube/v3/channels?part=id&forHandle={handle}&key={api_key}'
            resp = requests.get(resolve_url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('items'):
                    yt_channel_id = data['items'][0]['id']

        if not yt_channel_id:
            print(f'  [SKIP] Nao consegui extrair channel_id de {url}')
            completed.add(str(canal_id))
            save_checkpoint({'completed_canais': list(completed), 'stats': stats})
            continue

        # Buscar videos
        videos = get_channel_videos(yt_channel_id, api_key)
        if not videos:
            print(f'  [OK] 0 videos nos ultimos {DAYS_BACK} dias')
            completed.add(str(canal_id))
            save_checkpoint({'completed_canais': list(completed), 'stats': stats})
            continue

        print(f'  {len(videos)} videos encontrados')
        canal_novos = 0

        for v in videos:
            vid = v['videoId']
            title = v['title'][:40]

            comments = get_video_comments(vid, api_key)
            if comments:
                novos = save_comments(vid, canal_id, comments, is_portuguese)
                canal_novos += novos
                stats['novos'] += novos
                stats['existentes'] += len(comments) - novos
                if novos > 0:
                    print(f'  + {title}: {novos} novos de {len(comments)}')

            import time
            time.sleep(0.3)

        if canal_novos > 0:
            print(f'  [OK] {canal_novos} novos comentarios inseridos')
        else:
            print(f'  [OK] Todos comentarios ja existiam')

        completed.add(str(canal_id))
        save_checkpoint({'completed_canais': list(completed), 'stats': stats})

    print(f'\n{"="*70}')
    print(f'  COLETA CONCLUIDA!')
    print(f'  Novos inseridos: {stats["novos"]}')
    print(f'  Ja existiam: {stats["existentes"]}')
    print(f'{"="*70}\n')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n\nInterrompido. Rode novamente para retomar do checkpoint.')
    except Exception as e:
        print(f'\n[ERRO] {e}')

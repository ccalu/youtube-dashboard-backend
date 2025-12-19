from supabase import create_client, Client
from typing import Optional, Dict, List
import os

supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

def get_channel(channel_id: str) -> Optional[Dict]:
    """Busca configuração completa de um canal"""
    result = supabase.table('yt_channels')\
        .select('*')\
        .eq('channel_id', channel_id)\
        .eq('is_active', True)\
        .single()\
        .execute()
    return result.data if result.data else None

def get_oauth_tokens(channel_id: str) -> Optional[Dict]:
    """Busca tokens OAuth de um canal"""
    result = supabase.table('yt_oauth_tokens')\
        .select('*')\
        .eq('channel_id', channel_id)\
        .single()\
        .execute()
    return result.data if result.data else None

def get_proxy_credentials(proxy_name: str) -> Optional[Dict]:
    """Busca credentials OAuth do proxy (Client ID/Secret)"""
    result = supabase.table('yt_proxy_credentials')\
        .select('*')\
        .eq('proxy_name', proxy_name)\
        .single()\
        .execute()
    return result.data if result.data else None

def create_upload(channel_id: str, video_url: str, titulo: str,
                  descricao: str, subnicho: str,
                  sheets_row: int) -> Dict:
    """Adiciona upload na fila"""

    channel = get_channel(channel_id)

    data = {
        'channel_id': channel_id,
        'video_url': video_url,
        'titulo': titulo,  # EXATO da planilha
        'descricao': descricao,  # EXATO da planilha (COM #hashtags)
        'subnicho': subnicho,
        'lingua': channel.get('lingua') if channel else None,
        'sheets_row_number': sheets_row,
        'status': 'pending'
    }

    result = supabase.table('yt_upload_queue')\
        .insert(data)\
        .execute()

    return result.data[0]

def update_upload_status(upload_id: int, status: str, **kwargs):
    """Atualiza status de um upload"""
    from datetime import datetime

    update_data = {'status': status}

    if status == 'downloading':
        update_data['started_at'] = datetime.now().isoformat()
    elif status in ['completed', 'failed']:
        update_data['completed_at'] = datetime.now().isoformat()

    # Adiciona campos extras (youtube_video_id, error_message, etc)
    update_data.update(kwargs)

    supabase.table('yt_upload_queue')\
        .update(update_data)\
        .eq('id', upload_id)\
        .execute()

def get_pending_uploads(limit: int = 10) -> List[Dict]:
    """Busca uploads pendentes na fila"""
    result = supabase.table('yt_upload_queue')\
        .select('*')\
        .eq('status', 'pending')\
        .order('scheduled_at', desc=False)\
        .limit(limit)\
        .execute()
    return result.data

def update_oauth_tokens(channel_id: str, access_token: str,
                        refresh_token: str, token_expiry: str):
    """Atualiza tokens OAuth após refresh"""
    supabase.table('yt_oauth_tokens')\
        .update({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_expiry': token_expiry
        })\
        .eq('channel_id', channel_id)\
        .execute()

def get_upload_by_id(upload_id: int) -> Optional[Dict]:
    """Busca um upload específico por ID"""
    result = supabase.table('yt_upload_queue')\
        .select('*')\
        .eq('id', upload_id)\
        .single()\
        .execute()
    return result.data if result.data else None

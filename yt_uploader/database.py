from supabase import create_client, Client
from typing import Optional, Dict, List
import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Carrega .env se ainda não foi carregado
load_dotenv()

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
        .limit(1)\
        .execute()
    return result.data[0] if result.data else None

def get_oauth_tokens(channel_id: str) -> Optional[Dict]:
    """Busca tokens OAuth de um canal"""
    result = supabase.table('yt_oauth_tokens')\
        .select('*')\
        .eq('channel_id', channel_id)\
        .limit(1)\
        .execute()
    return result.data[0] if result.data else None

def create_upload(channel_id: str, video_url: str, titulo: str,
                  descricao: str, subnicho: str,
                  sheets_row: int, spreadsheet_id: str) -> Dict:
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
        'spreadsheet_id': spreadsheet_id,
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
        .limit(1)\
        .execute()
    return result.data[0] if result.data else None

def get_proxy_credentials(proxy_name: str) -> Optional[Dict]:
    """
    [DEPRECATED] Busca credenciais OAuth do proxy no Supabase.

    ATENÇÃO: Esta função está deprecated. Use get_channel_credentials() para
    arquitetura com credenciais isoladas por canal.

    Args:
        proxy_name: Nome do proxy (ex: proxy_c0008_1)

    Returns:
        Dict com client_id e client_secret ou None
    """
    try:
        result = supabase.table('yt_proxy_credentials')\
            .select('client_id, client_secret')\
            .eq('proxy_name', proxy_name)\
            .limit(1)\
            .execute()

        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Erro ao buscar credenciais do proxy {proxy_name}: {e}")
        return None

def get_channel_credentials(channel_id: str) -> Optional[Dict]:
    """
    Busca credenciais OAuth específicas de um canal no Supabase.

    NOVA ARQUITETURA: 1 canal = 1 Client ID/Secret único
    Garante isolamento total e contingência máxima.

    Args:
        channel_id: ID do canal YouTube (ex: UCbB1WtTqBWYdSk3JE6iRNRw)

    Returns:
        Dict com client_id e client_secret ou None

    Exemplo:
        >>> creds = get_channel_credentials('UCbB1WtTqBWYdSk3JE6iRNRw')
        >>> print(creds['client_id'])
        '123456789-abc.apps.googleusercontent.com'
    """
    try:
        result = supabase.table('yt_channel_credentials')\
            .select('client_id, client_secret')\
            .eq('channel_id', channel_id)\
            .limit(1)\
            .execute()

        if result.data:
            logger.debug(f"Credenciais encontradas para canal {channel_id}")
            return result.data[0]
        else:
            logger.warning(f"Nenhuma credencial encontrada para canal {channel_id}")
            return None

    except Exception as e:
        logger.error(f"Erro ao buscar credenciais do canal {channel_id}: {e}")
        return None

def save_channel_credentials(channel_id: str, client_id: str, client_secret: str) -> bool:
    """
    Salva ou atualiza credenciais OAuth de um canal.

    Args:
        channel_id: ID do canal YouTube
        client_id: Client ID do projeto Google Cloud
        client_secret: Client Secret do projeto Google Cloud

    Returns:
        True se salvo com sucesso, False caso contrário

    Exemplo:
        >>> save_channel_credentials(
        ...     'UCbB1WtTqBWYdSk3JE6iRNRw',
        ...     '123-abc.apps.googleusercontent.com',
        ...     'GOCSPX-xxx'
        ... )
        True
    """
    try:
        data = {
            'channel_id': channel_id,
            'client_id': client_id,
            'client_secret': client_secret
        }

        # Upsert: insere ou atualiza se já existir
        result = supabase.table('yt_channel_credentials')\
            .upsert(data, on_conflict='channel_id')\
            .execute()

        logger.info(f"Credenciais salvas para canal {channel_id}")
        return True

    except Exception as e:
        logger.error(f"Erro ao salvar credenciais do canal {channel_id}: {e}")
        return False

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from google_auth_httplib2 import AuthorizedHttp
import httpx
import httplib2
import socks
import os
import logging
from typing import Dict
from urllib.parse import urlparse
from .oauth_manager import OAuthManager
from .database import get_channel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YouTubeUploader:
    """Serviço de upload de vídeos para YouTube"""

    def __init__(self):
        self.temp_path = os.getenv('TEMP_VIDEO_PATH', '/tmp/videos')
        os.makedirs(self.temp_path, exist_ok=True)

    def download_video(self, video_url: str) -> str:
        """
        Baixa vídeo do Google Drive.
        Aceita URLs: drive.google.com/file/d/FILE_ID ou ?id=FILE_ID
        """
        logger.info(f"📥 Baixando vídeo: {video_url[:50]}...")

        # Extrai file_id da URL
        if '/file/d/' in video_url:
            file_id = video_url.split('/file/d/')[1].split('/')[0]
        elif 'id=' in video_url:
            file_id = video_url.split('id=')[1].split('&')[0]
        else:
            raise ValueError(f"URL do Drive inválida: {video_url}")

        # URL de download direto
        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"

        # Download
        response = httpx.get(download_url, follow_redirects=True, timeout=300)
        response.raise_for_status()

        # Salva localmente
        file_path = os.path.join(self.temp_path, f"{file_id}.mp4")
        with open(file_path, 'wb') as f:
            f.write(response.content)

        file_size_mb = len(response.content) / (1024 * 1024)
        logger.info(f"✅ Vídeo baixado: {file_size_mb:.1f}MB → {file_path}")

        return file_path

    def upload_to_youtube(self, channel_id: str, video_path: str,
                          metadata: Dict) -> Dict:
        """
        Faz upload de vídeo para YouTube em modo RASCUNHO.

        IMPORTANTE:
        - Título e descrição são usados EXATAMENTE como vem (sem alteração)
        - Upload passa pelo proxy SOCKS5 do grupo
        - Vídeo fica PRIVATE (rascunho) - nunca publicado automaticamente

        Args:
            channel_id: ID do canal YouTube (UCxxxxxxxxx)
            video_path: Caminho do arquivo local
            metadata: {titulo, descricao}

        Returns:
            {success: bool, video_id: str}
        """
        logger.info(f"🎬 Iniciando upload: {metadata['titulo'][:50]}...")

        # 1. Busca configuração do canal
        channel = get_channel(channel_id)
        if not channel:
            raise ValueError(f"Canal {channel_id} não encontrado")

        # 2. Configura HTTP client com PROXY SOCKS5 (httplib2)
        if channel.get('proxy_url'):
            # Parse: socks5://user:pass@host:port
            parsed = urlparse(channel['proxy_url'])

            # Extrai credenciais do proxy
            proxy_user = parsed.username if parsed.username else None
            proxy_pass = parsed.password if parsed.password else None

            # Configura proxy para httplib2
            proxy_info = httplib2.ProxyInfo(
                proxy_type=socks.PROXY_TYPE_SOCKS5,
                proxy_host=parsed.hostname,
                proxy_port=parsed.port,
                proxy_user=proxy_user,
                proxy_pass=proxy_pass
            )
            http = httplib2.Http(proxy_info=proxy_info, timeout=300)
            logger.info(f"🔒 Usando proxy SOCKS5: {parsed.hostname}:{parsed.port}")
        else:
            http = httplib2.Http(timeout=300)
            logger.warning("⚠️  UPLOAD SEM PROXY - CUIDADO COM CONTINGÊNCIA!")

        # 3. Obtém credenciais OAuth válidas
        try:
            credentials = OAuthManager.get_valid_credentials(channel_id)
        except Exception as e:
            raise ValueError(f"Erro OAuth: {str(e)}")

        # 4. Autoriza o http com as credentials usando AuthorizedHttp
        authorized_http = AuthorizedHttp(credentials, http=http)

        # 5. Cria serviço YouTube API COM PROXY
        youtube = build('youtube', 'v3', http=authorized_http)

        # 5. Prepara metadata do upload
        body = {
            'snippet': {
                'title': metadata['titulo'],  # EXATO da planilha
                'description': metadata['descricao'],  # EXATO da planilha (COM #hashtags)
                'categoryId': '24'  # Entertainment
            },
            'status': {
                'privacyStatus': 'private',  # ← RASCUNHO!!!
                'selfDeclaredMadeForKids': False
            }
        }

        # 6. Prepara arquivo para upload
        media = MediaFileUpload(
            video_path,
            chunksize=1024*1024*5,  # 5MB chunks (resumable)
            resumable=True
        )

        try:
            # 7. Executa upload com progress tracking
            request = youtube.videos().insert(
                part='snippet,status',
                body=body,
                media_body=media
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    logger.info(f"⬆️  Upload: {progress}%")

            # 8. Upload concluído
            video_id = response['id']

            logger.info(f"✅ Upload concluído! Video ID: {video_id}")

            return {
                'success': True,
                'video_id': video_id
            }

        except HttpError as e:
            logger.error(f"❌ Erro no upload YouTube: {e}")
            raise

    def cleanup(self, file_path: str):
        """Remove arquivo temporário após upload"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"🗑️  Arquivo removido: {file_path}")
        except Exception as e:
            logger.warning(f"⚠️  Erro ao remover arquivo: {e}")

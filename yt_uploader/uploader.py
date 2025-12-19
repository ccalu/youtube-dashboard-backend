from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import httpx
import os
import logging
from typing import Dict
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
        - Vídeo fica PRIVATE (rascunho) - nunca publicado automaticamente
        - Upload direto via YouTube Data API (sem proxy)

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

        # 2. Obtém credenciais OAuth válidas
        try:
            credentials = OAuthManager.get_valid_credentials(channel_id)
        except Exception as e:
            raise ValueError(f"Erro OAuth: {str(e)}")

        # 3. Cria serviço YouTube API (direto, sem proxy)
        youtube = build('youtube', 'v3', credentials=credentials)
        logger.info(f"✅ Conectado à YouTube API - Canal: {channel.get('channel_name')}")

        # 4. Prepara metadata do upload
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

        # 5. Prepara arquivo para upload
        media = MediaFileUpload(
            video_path,
            chunksize=1024*1024*5,  # 5MB chunks (resumable)
            resumable=True
        )

        try:
            # 6. Executa upload com progress tracking
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

            # 7. Upload concluído
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

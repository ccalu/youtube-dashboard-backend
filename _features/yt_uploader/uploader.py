from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import httpx
import os
import logging
from typing import Dict
import gdown
import unicodedata
from .oauth_manager import OAuthManager
from .database import get_channel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YouTubeUploader:
    """Serviço de upload de vídeos para YouTube"""

    def __init__(self):
        self.temp_path = os.getenv('TEMP_VIDEO_PATH', '/tmp/videos')
        os.makedirs(self.temp_path, exist_ok=True)

    def download_video(self, video_url: str, channel_id: str = None) -> str:
        """
        Baixa vídeo do Google Drive usando gdown.
        Aceita URLs: drive.google.com/file/d/FILE_ID ou ?id=FILE_ID

        Bypass automático de "virus scan warning" para arquivos grandes.
        """
        prefix = f"[{channel_id}] " if channel_id else ""
        logger.info(f"{prefix}📥 Download iniciado (Google Drive)")

        # Extrai file_id da URL
        if '/file/d/' in video_url:
            file_id = video_url.split('/file/d/')[1].split('/')[0]
        elif 'id=' in video_url:
            file_id = video_url.split('id=')[1].split('&')[0]
        else:
            raise ValueError(f"URL do Drive inválida: {video_url}")

        # Caminho de destino
        file_path = os.path.join(self.temp_path, f"{file_id}.mp4")

        # Download usando gdown (lida automaticamente com virus scan warning)
        # quiet=False mostra progress bar
        download_url = f"https://drive.google.com/uc?id={file_id}"

        try:
            gdown.download(download_url, file_path, quiet=False, fuzzy=True)
        except Exception as e:
            raise ValueError(
                f"Erro ao baixar do Google Drive: {str(e)}. "
                f"Verifique se o arquivo está compartilhado publicamente (Anyone with the link)."
            )

        # Verifica se arquivo foi baixado e não está vazio
        if not os.path.exists(file_path):
            raise ValueError("Download falhou - arquivo não foi criado")

        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

        if file_size_mb < 0.1:  # < 100KB
            os.remove(file_path)
            raise ValueError(
                f"Arquivo muito pequeno ({file_size_mb:.2f} MB). "
                f"Verifique permissões de compartilhamento no Google Drive."
            )

        logger.info(f"{prefix}✅ Download concluído ({file_size_mb:.1f} MB)")

        return file_path

    def upload_to_youtube(self, channel_id: str, video_path: str,
                          metadata: Dict, skip_playlist: bool = False,
                          privacy_status: str = "private") -> Dict:
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
        # Sanitiza título UTF-8 (fix para caracteres especiais alemães, franceses, etc)
        titulo_original = metadata['titulo']
        logger.info(f"[{channel_id}] 🔧 UTF-8 SANITIZATION V2 ACTIVE")  # Log para confirmar codigo novo

        titulo_sanitized = unicodedata.normalize('NFC', titulo_original)
        titulo_sanitized = titulo_sanitized.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')

        # Remove caracteres de replacement (�) que YouTube rejeita
        titulo_sanitized = titulo_sanitized.replace('\ufffd', 'O')  # � → O
        titulo_sanitized = titulo_sanitized.replace('�', 'O')       # Fallback
        titulo_sanitized = titulo_sanitized.strip()

        # YouTube limite = 100 caracteres
        if len(titulo_sanitized) > 100:
            logger.info(f"[{channel_id}] ⚠️  Título muito longo ({len(titulo_sanitized)} chars) - truncando para 100")
            titulo_sanitized = titulo_sanitized[:97] + "..."

        titulo_sanitized = titulo_sanitized or "Video"  # Fallback se vazio

        logger.info(f"[{channel_id}] 🎬 Título: {titulo_sanitized[:60]}...")
        logger.info(f"[{channel_id}] 📏 Tamanho: {len(titulo_sanitized)} chars")
        logger.info(f"[{channel_id}] 🔤 Repr: {repr(titulo_sanitized[:80])}")
        if titulo_original != titulo_sanitized:
            logger.info(f"[{channel_id}] 🔧 UTF-8 fix aplicado (original: {len(titulo_original)} chars → sanitized: {len(titulo_sanitized)} chars)")

        # 1. Busca configuração do canal
        channel = get_channel(channel_id)
        if not channel:
            raise ValueError(f"Canal {channel_id} não encontrado")

        # 2. Obtém credenciais OAuth válidas
        logger.info(f"[{channel_id}] 🔑 Buscando credenciais OAuth...")
        try:
            credentials = OAuthManager.get_valid_credentials(channel_id)
        except Exception as e:
            raise ValueError(f"Erro OAuth: {str(e)}")

        # 3. Cria serviço YouTube API (direto, sem proxy)
        logger.info(f"[{channel_id}] 📹 Upload iniciado para YouTube")
        youtube = build('youtube', 'v3', credentials=credentials)

        # 4. Prepara metadata do upload
        body = {
            'snippet': {
                'title': titulo_sanitized,  # UTF-8 sanitizado
                'description': metadata['descricao'],  # EXATO da planilha (COM #hashtags)
                'categoryId': '24',  # Entertainment
                'defaultLanguage': channel.get('lingua', 'en'),  # Idioma do título/descrição
                'defaultAudioLanguage': channel.get('lingua', 'en')  # Idioma do áudio
            },
            'status': {
                'privacyStatus': privacy_status,  # padrao "private", shorts passam "public"
                'selfDeclaredMadeForKids': False,
                'containsSyntheticMedia': True  # ← MARCA COMO CONTEÚDO ALTERADO/IA
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

            logger.info(f"[{channel_id}] ✅ Vídeo enviado com sucesso (ID: {video_id})")

            # 8. Adiciona a playlist (se configurado e nao for skip)
            if channel.get('default_playlist_id') and not skip_playlist:
                playlist_id = channel['default_playlist_id']
                logger.info(f"[{channel_id}] 📋 Adicionando à playlist {playlist_id}")
                try:
                    youtube.playlistItems().insert(
                        part='snippet',
                        body={
                            'snippet': {
                                'playlistId': playlist_id,
                                'resourceId': {
                                    'kind': 'youtube#video',
                                    'videoId': video_id
                                }
                            }
                        }
                    ).execute()
                    logger.info(f"[{channel_id}] ✅ Vídeo adicionado à playlist")
                except Exception as e:
                    error_msg = str(e)
                    if "403" in error_msg and "Insufficient" in error_msg:
                        logger.error(f"[{channel_id}] ❌ ERRO DE PERMISSÃO: OAuth sem scope para playlists!")
                        logger.error(f"[{channel_id}] ❌ Execute: python reauth_channel_oauth.py")
                        logger.error(f"[{channel_id}] ❌ Para corrigir as permissões do canal")
                    else:
                        logger.error(f"[{channel_id}] ❌ Erro ao adicionar à playlist: {error_msg}")
                    # Não falha upload se playlist der erro, mas loga como erro para visibilidade

            return {
                'success': True,
                'video_id': video_id
            }

        except HttpError as e:
            logger.error(f"[{channel_id}] ❌ Erro no upload YouTube: {e}")
            raise

    def cleanup(self, file_path: str):
        """Remove arquivo temporário após upload"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"🗑️  Arquivo removido: {file_path}")
        except Exception as e:
            logger.warning(f"⚠️  Erro ao remover arquivo: {e}")

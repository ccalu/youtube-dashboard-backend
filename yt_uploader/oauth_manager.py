from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from datetime import datetime, timedelta, timezone
import os
from .database import (
    get_channel,
    get_oauth_tokens,
    update_oauth_tokens
)

class OAuthManager:
    """Gerencia autenticação OAuth dos canais"""

    @staticmethod
    def get_valid_credentials(channel_id: str) -> Credentials:
        """
        Retorna credenciais OAuth válidas para um canal.
        Renova automaticamente se expirado.
        """

        # 1. Busca dados do canal
        channel = get_channel(channel_id)
        if not channel:
            raise ValueError(f"Canal {channel_id} não encontrado ou inativo")

        # 2. Busca tokens OAuth do canal
        oauth = get_oauth_tokens(channel_id)
        if not oauth or not oauth.get('refresh_token'):
            raise ValueError(f"Canal {channel_id} sem OAuth configurado")

        # 3. Busca Client ID/Secret das variáveis de ambiente
        client_id = os.getenv('YOUTUBE_OAUTH_CLIENT_ID')
        client_secret = os.getenv('YOUTUBE_OAUTH_CLIENT_SECRET')

        if not client_id or not client_secret:
            raise ValueError("Variáveis YOUTUBE_OAUTH_CLIENT_ID/SECRET não configuradas")

        # 4. Cria objeto Credentials
        credentials = Credentials(
            token=oauth.get('access_token'),
            refresh_token=oauth.get('refresh_token'),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret
        )

        # 5. Renova se expirado
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())

            # Calcula expiry real do token (se disponível)
            if credentials.expiry:
                token_expiry = credentials.expiry.isoformat()
            else:
                # Fallback: +3600 segundos (1 hora) com timezone UTC
                token_expiry = (datetime.now(timezone.utc) + timedelta(seconds=3600)).isoformat()

            # Salva novo token no banco
            update_oauth_tokens(
                channel_id=channel_id,
                access_token=credentials.token,
                refresh_token=credentials.refresh_token,
                token_expiry=token_expiry
            )

        return credentials

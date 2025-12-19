from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from datetime import datetime, timedelta
from .database import (
    get_channel,
    get_oauth_tokens,
    get_proxy_credentials,
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

        # 3. Busca Client ID/Secret do proxy
        proxy_creds = get_proxy_credentials(channel.get('proxy_name'))
        if not proxy_creds:
            raise ValueError(f"Proxy {channel.get('proxy_name')} sem credentials OAuth")

        # 4. Cria objeto Credentials
        credentials = Credentials(
            token=oauth.get('access_token'),
            refresh_token=oauth.get('refresh_token'),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=proxy_creds['client_id'],
            client_secret=proxy_creds['client_secret']
        )

        # 5. Renova se expirado
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())

            # Salva novo token no banco
            update_oauth_tokens(
                channel_id=channel_id,
                access_token=credentials.token,
                refresh_token=credentials.refresh_token,
                token_expiry=(datetime.now() + timedelta(seconds=3600)).isoformat()
            )

        return credentials

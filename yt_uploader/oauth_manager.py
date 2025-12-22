from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from datetime import datetime, timedelta, timezone
import os
import logging
from .database import (
    get_channel,
    get_oauth_tokens,
    update_oauth_tokens,
    get_proxy_credentials
)

logger = logging.getLogger(__name__)

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

        # 3. Busca proxy_name do canal
        proxy_name = channel.get('proxy_name')
        if not proxy_name:
            raise ValueError(f"Canal {channel_id} sem proxy_name configurado")

        # 4. Busca credenciais OAuth do proxy
        proxy_creds = get_proxy_credentials(proxy_name)
        if not proxy_creds:
            raise ValueError(f"Credenciais do proxy {proxy_name} não encontradas em yt_proxy_credentials")

        client_id = proxy_creds['client_id']
        client_secret = proxy_creds['client_secret']
        logger.info(f"[{channel_id}] Usando credenciais do proxy: {proxy_name}")

        # 5. Cria objeto Credentials
        credentials = Credentials(
            token=oauth.get('access_token'),
            refresh_token=oauth.get('refresh_token'),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret
        )

        # 6. Renova se expirado
        if credentials.expired and credentials.refresh_token:
            logger.info(f"[{channel_id}] ⚠️ Token expirado, renovando...")

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

            logger.info(f"[{channel_id}] ✅ Token renovado com sucesso (expira: {token_expiry})")
        else:
            logger.debug(f"[{channel_id}] 🔑 Token ainda válido, sem renovação necessária")

        return credentials

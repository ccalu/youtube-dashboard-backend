from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from datetime import datetime, timedelta, timezone
import os
import logging
from .database import (
    get_channel,
    get_oauth_tokens,
    update_oauth_tokens,
    get_proxy_credentials,  # DEPRECATED - manter para compatibilidade
    get_channel_credentials  # NOVA ARQUITETURA
)

logger = logging.getLogger(__name__)

class OAuthManager:
    """Gerencia autenticação OAuth dos canais"""

    @staticmethod
    def get_valid_credentials(channel_id: str) -> Credentials:
        """
        Retorna credenciais OAuth válidas para um canal.
        Renova automaticamente se expirado.

        NOVA ARQUITETURA (v2.0):
        - Busca credenciais direto do canal (1 canal = 1 Client ID/Secret)
        - Fallback para credenciais de proxy (compatibilidade com Sans Limites)
        - Isolamento total entre canais
        """

        # 1. Busca dados do canal
        channel = get_channel(channel_id)
        if not channel:
            raise ValueError(f"Canal {channel_id} não encontrado ou inativo")

        # 2. Busca tokens OAuth do canal
        oauth = get_oauth_tokens(channel_id)
        if not oauth or not oauth.get('refresh_token'):
            raise ValueError(f"Canal {channel_id} sem OAuth configurado")

        # 3. NOVA ARQUITETURA: Busca credenciais do canal
        channel_creds = get_channel_credentials(channel_id)

        if channel_creds:
            # Arquitetura nova: credenciais isoladas por canal
            client_id = channel_creds['client_id']
            client_secret = channel_creds['client_secret']
            logger.info(f"[{channel_id}] ✅ Usando credenciais isoladas do canal")

        else:
            # FALLBACK: Arquitetura antiga (compatibilidade com Sans Limites)
            proxy_name = channel.get('proxy_name')
            if not proxy_name:
                raise ValueError(
                    f"Canal {channel_id} sem credenciais próprias e sem proxy_name configurado. "
                    "Execute migration ou adicione credenciais via wizard."
                )

            proxy_creds = get_proxy_credentials(proxy_name)
            if not proxy_creds:
                raise ValueError(
                    f"Canal {channel_id} sem credenciais em yt_channel_credentials "
                    f"e proxy {proxy_name} não encontrado em yt_proxy_credentials"
                )

            client_id = proxy_creds['client_id']
            client_secret = proxy_creds['client_secret']
            logger.warning(
                f"[{channel_id}] ⚠️ Usando credenciais do proxy: {proxy_name} (DEPRECATED). "
                "Migre para yt_channel_credentials para isolamento total."
            )

        # 4. Cria objeto Credentials com scopes completos
        credentials = Credentials(
            token=oauth.get('access_token'),
            refresh_token=oauth.get('refresh_token'),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=[
                'https://www.googleapis.com/auth/youtube.upload',
                'https://www.googleapis.com/auth/youtube',
                'https://www.googleapis.com/auth/youtube.force-ssl',
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/yt-analytics.readonly'
            ]
        )

        # 4.1. Define expiry do token para verificação correta
        expiry_str = oauth.get('token_expiry')
        if expiry_str:
            try:
                # Parse da data de expiração
                if 'Z' in expiry_str or '+' in expiry_str:
                    expiry = datetime.fromisoformat(expiry_str.replace('Z', '+00:00'))
                else:
                    expiry = datetime.fromisoformat(expiry_str).replace(tzinfo=timezone.utc)
                # Remove timezone para compatibilidade com Google Auth (espera naive datetime)
                credentials.expiry = expiry.replace(tzinfo=None)
                logger.debug(f"[{channel_id}] Token expira em: {credentials.expiry}")
            except Exception as e:
                logger.warning(f"[{channel_id}] Erro ao parsear token_expiry: {e}")
                # Se não conseguir parsear, considera expirado para forçar refresh
                credentials.expiry = datetime.now() - timedelta(hours=1)

        # 5. Renova se expirado (ou se está prestes a expirar em 5 minutos)
        if credentials.expired or (
            credentials.expiry and
            credentials.expiry < datetime.now() + timedelta(minutes=5)
        ):
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

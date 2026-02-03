# -*- coding: utf-8 -*-
"""
Script para fazer refresh dos tokens OAuth expirados
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from supabase import create_client
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Adiciona o diretório ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Carrega variáveis
load_dotenv()

def refresh_tokens():
    """Faz refresh dos tokens OAuth"""

    channel_id = "UCiMgKMWsYH8a8EFp94TClIQ"

    print("=" * 80)
    print("REFRESH DE TOKENS OAUTH")
    print("=" * 80)

    # Usa SERVICE_ROLE_KEY para bypass RLS
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    )

    # 1. Busca tokens atuais
    print("\n1. Buscando tokens atuais...")
    result = supabase.table('yt_oauth_tokens')\
        .select('*')\
        .eq('channel_id', channel_id)\
        .limit(1)\
        .execute()

    if not result.data:
        print("   [ERRO] Nenhum token encontrado!")
        return False

    oauth_data = result.data[0]
    print(f"   [OK] Tokens encontrados")
    print(f"   Token expiry: {oauth_data.get('token_expiry')}")

    # 2. Busca credenciais (client_id/secret)
    print("\n2. Buscando credenciais OAuth...")
    result = supabase.table('yt_channel_credentials')\
        .select('*')\
        .eq('channel_id', channel_id)\
        .limit(1)\
        .execute()

    if not result.data:
        print("   [ERRO] Nenhuma credencial encontrada!")
        return False

    creds_data = result.data[0]
    print(f"   [OK] Credenciais encontradas")
    print(f"   Client ID: {creds_data['client_id'][:30]}...")

    # 3. Cria objeto Credentials do Google
    print("\n3. Criando objeto Credentials...")

    # Parse da data de expiração
    expiry_str = oauth_data.get('token_expiry')
    if expiry_str:
        if 'Z' in expiry_str or '+' in expiry_str:
            expiry = datetime.fromisoformat(expiry_str.replace('Z', '+00:00'))
        else:
            expiry = datetime.fromisoformat(expiry_str).replace(tzinfo=timezone.utc)
    else:
        # Se não tem expiry, considera expirado
        expiry = datetime.now(timezone.utc) - timedelta(hours=1)

    credentials = Credentials(
        token=oauth_data['access_token'],
        refresh_token=oauth_data['refresh_token'],
        token_uri='https://oauth2.googleapis.com/token',
        client_id=creds_data['client_id'],
        client_secret=creds_data['client_secret'],
        scopes=['https://www.googleapis.com/auth/youtube.upload']
    )

    # Define a expiração manualmente
    credentials.expiry = expiry.replace(tzinfo=None)  # Google espera naive datetime

    print(f"   [OK] Credentials criado")
    print(f"   Expirado? {credentials.expired}")

    # 4. Faz refresh se necessário
    print("\n4. Fazendo refresh do token...")

    try:
        # Força o refresh
        credentials.refresh(Request())

        print(f"   [OK] Token renovado com sucesso!")
        print(f"   Novo access token: {credentials.token[:30]}...")
        print(f"   Novo expiry: {credentials.expiry}")

        # 5. Salva no banco
        print("\n5. Salvando tokens renovados...")

        # Adiciona timezone UTC ao expiry
        if credentials.expiry:
            new_expiry = credentials.expiry.replace(tzinfo=timezone.utc)
        else:
            # Se não tem expiry, define 1 hora no futuro
            new_expiry = datetime.now(timezone.utc) + timedelta(hours=1)

        update_data = {
            'access_token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_expiry': new_expiry.isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }

        result = supabase.table('yt_oauth_tokens')\
            .update(update_data)\
            .eq('channel_id', channel_id)\
            .execute()

        print(f"   [OK] Tokens salvos no banco!")

        # 6. Verifica se foi salvo
        print("\n6. Verificando se foi salvo corretamente...")

        result = supabase.table('yt_oauth_tokens')\
            .select('access_token, token_expiry')\
            .eq('channel_id', channel_id)\
            .limit(1)\
            .execute()

        if result.data:
            saved_token = result.data[0]
            if saved_token['access_token'][:30] == credentials.token[:30]:
                print(f"   [OK] Token confirmado no banco!")
                print(f"   Expira em: {saved_token['token_expiry']}")

                # Calcula tempo até expirar
                saved_expiry = datetime.fromisoformat(saved_token['token_expiry'].replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                delta = saved_expiry - now
                hours = delta.total_seconds() / 3600

                print(f"   [OK] Token válido por {hours:.1f} horas")
                return True
            else:
                print(f"   [ERRO] Token no banco diferente do renovado!")
                return False
        else:
            print(f"   [ERRO] Token não encontrado após salvar!")
            return False

    except Exception as e:
        print(f"   [ERRO] Falha no refresh: {e}")
        return False

if __name__ == "__main__":
    success = refresh_tokens()

    print("\n" + "=" * 80)
    if success:
        print("SUCESSO! Tokens renovados. Agora pode testar o upload.")
    else:
        print("FALHA! Verifique os erros acima.")
    print("=" * 80)
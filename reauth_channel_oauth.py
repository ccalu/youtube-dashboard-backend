# -*- coding: utf-8 -*-
"""
Script para Re-autorizar OAuth de um canal existente.
Uso: python reauth_channel_oauth.py [channel_id]

Se nao passar channel_id, mostra lista de canais para escolher.
Mantém todas as configs do canal (spreadsheet, playlist, etc).
Apenas substitui os tokens OAuth.
"""

import os
import sys
import requests
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse, parse_qs
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/yt-analytics.readonly"
]


def listar_canais():
    """Lista canais disponiveis para re-auth"""
    result = supabase.table('yt_channels').select('channel_id, channel_name, subnicho').eq('is_active', True).order('channel_name').execute()
    print("\nCanais disponiveis:\n")
    for i, c in enumerate(result.data):
        print(f"  [{i+1:2d}] {c['channel_name']:<35} ({c.get('subnicho', '?')})")
    print()
    while True:
        try:
            escolha = input("Escolha o numero do canal: ").strip()
            idx = int(escolha) - 1
            if 0 <= idx < len(result.data):
                return result.data[idx]['channel_id']
            print("Numero invalido!")
        except ValueError:
            print("Digite um numero!")


def extrair_codigo_da_url(url_completa):
    """Extrai codigo OAuth de URL de redirect"""
    try:
        parsed = urlparse(url_completa)
        params = parse_qs(parsed.query)
        if 'code' in params:
            return params['code'][0]
    except:
        pass
    return None


def main():
    print("=" * 70)
    print("  RE-AUTORIZACAO OAUTH DE CANAL EXISTENTE")
    print("=" * 70)

    # 1. Determina channel_id
    if len(sys.argv) > 1:
        channel_id = sys.argv[1]
    else:
        channel_id = listar_canais()

    # 2. Busca dados do canal
    canal = supabase.table('yt_channels').select('channel_name, subnicho').eq('channel_id', channel_id).execute()
    if not canal.data:
        print(f"\n[ERRO] Canal {channel_id} nao encontrado!")
        return

    channel_name = canal.data[0]['channel_name']
    subnicho = canal.data[0].get('subnicho', '?')
    print(f"\nCanal: {channel_name} ({subnicho})")
    print(f"ID:    {channel_id}")

    # 3. Verifica tokens atuais
    tokens_atuais = supabase.table('yt_oauth_tokens').select('token_expiry, created_at').eq('channel_id', channel_id).execute()
    if tokens_atuais.data:
        expiry = tokens_atuais.data[0].get('token_expiry', '?')[:16]
        created = tokens_atuais.data[0].get('created_at', '?')[:16]
        print(f"\nToken atual: criado={created}  expiry={expiry}")
        print("Sera SUBSTITUIDO por novo token.\n")

    resp = input("Continuar com re-autorizacao? (s/n): ").strip().lower()
    if resp != 's':
        print("Cancelado.")
        return

    # 4. Pede novas credenciais OAuth (client_id / client_secret)
    print("\n" + "-" * 70)
    print("  CREDENCIAIS DO PROJETO GOOGLE CLOUD")
    print("-" * 70)

    # Verifica se ja tem credenciais salvas
    creds_existentes = supabase.table('yt_channel_credentials').select('client_id').eq('channel_id', channel_id).execute()
    if creds_existentes.data:
        print(f"\nCredenciais existentes: {creds_existentes.data[0]['client_id'][:35]}...")
        usar_existente = input("Usar as credenciais existentes? (s/n): ").strip().lower()
        if usar_existente == 's':
            creds = supabase.table('yt_channel_credentials').select('client_id, client_secret').eq('channel_id', channel_id).execute()
            client_id = creds.data[0]['client_id']
            client_secret = creds.data[0]['client_secret']
            print("[OK] Usando credenciais existentes")
        else:
            print("\nDigite as NOVAS credenciais:")
            client_id = input("  Client ID: ").strip()
            client_secret = input("  Client Secret: ").strip()
            # Atualiza no banco
            supabase.table('yt_channel_credentials').update({
                'client_id': client_id,
                'client_secret': client_secret,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }).eq('channel_id', channel_id).execute()
            print("[OK] Credenciais atualizadas no banco")
    else:
        print("\nNenhuma credencial salva. Digite as novas:")
        client_id = input("  Client ID: ").strip()
        client_secret = input("  Client Secret: ").strip()
        supabase.table('yt_channel_credentials').insert({
            'channel_id': channel_id,
            'client_id': client_id,
            'client_secret': client_secret,
            'created_at': datetime.now(timezone.utc).isoformat()
        }).execute()
        print("[OK] Credenciais salvas no banco")

    if not client_id or not client_secret:
        print("[ERRO] Client ID e Client Secret sao obrigatorios!")
        return

    # 5. Gera URL de autorizacao
    print("\n" + "-" * 70)
    print("  AUTORIZACAO OAUTH")
    print("-" * 70)

    redirect_uri = "http://localhost:8080"
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': ' '.join(SCOPES),
        'response_type': 'code',
        'access_type': 'offline',
        'prompt': 'consent'
    }
    query_string = '&'.join([f"{k}={requests.utils.quote(str(v))}" for k, v in params.items()])
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{query_string}"

    print("\nAbra esta URL no NAVEGADOR DO PROXY (conta Google do canal):\n")
    print(auth_url)
    print("\nApos autorizar, o Google redireciona para localhost:8080")
    print("Copie a URL COMPLETA do redirect (http://localhost:8080/?code=...)\n")

    redirect_url = input("Cole a URL de redirect aqui: ").strip()
    code = extrair_codigo_da_url(redirect_url)
    if not code:
        # Tenta usar como codigo direto
        if redirect_url.startswith('4/'):
            code = redirect_url
        else:
            print("[ERRO] Nao consegui extrair o codigo da URL!")
            return

    print(f"[OK] Codigo extraido: {code[:25]}...")

    # 6. Troca codigo por tokens
    print("\nObtendo tokens...")
    try:
        response = requests.post("https://oauth2.googleapis.com/token", data={
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }, timeout=30)
        response.raise_for_status()
        tokens = response.json()

        access_token = tokens['access_token']
        refresh_token = tokens.get('refresh_token')
        expires_in = tokens.get('expires_in', 3600)

        if not refresh_token:
            print("[ERRO] Refresh token nao retornado! Certifique-se de aceitar todas permissoes.")
            return

        print(f"[OK] Access token obtido")
        print(f"[OK] Refresh token obtido")

    except Exception as e:
        print(f"[ERRO] Falha ao obter tokens: {e}")
        return

    # 7. Valida token com YouTube API
    print("\nValidando token...")
    try:
        resp = requests.get("https://www.googleapis.com/youtube/v3/channels",
            headers={'Authorization': f'Bearer {access_token}'},
            params={'part': 'snippet', 'mine': 'true'}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if data.get('items'):
            yt_name = data['items'][0]['snippet']['title']
            print(f"[OK] Token valido! Canal YouTube: {yt_name}")
        else:
            print("[AVISO] Token valido mas nenhum canal encontrado")
    except Exception as e:
        print(f"[AVISO] Erro ao validar: {e}")
        cont = input("Continuar mesmo assim? (s/n): ").strip().lower()
        if cont != 's':
            return

    # 8. Remove tokens antigos e salva novos
    print("\nSalvando no banco...")

    # Deleta tokens antigos
    supabase.table('yt_oauth_tokens').delete().eq('channel_id', channel_id).execute()
    print("[OK] Tokens antigos removidos")

    # Salva novos
    token_expiry = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat()
    supabase.table('yt_oauth_tokens').insert({
        'channel_id': channel_id,
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_expiry': token_expiry,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'updated_at': datetime.now(timezone.utc).isoformat()
    }).execute()
    print("[OK] Novos tokens salvos")

    # 9. Verifica
    check = supabase.table('yt_oauth_tokens').select('channel_id, refresh_token').eq('channel_id', channel_id).execute()
    if check.data and check.data[0].get('refresh_token'):
        print("[OK] Tokens confirmados no banco!")
    else:
        print("[ERRO] Tokens nao encontrados apos salvar!")
        return

    # Sucesso
    print("\n" + "=" * 70)
    print(f"  RE-AUTORIZACAO CONCLUIDA - {channel_name}")
    print("=" * 70)
    print(f"\nAgora force o upload manualmente:")
    print(f"  python forcar_upload_manual_fixed.py --canal \"{channel_name}\"")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelado.")
    except Exception as e:
        print(f"\n[ERRO] {e}")

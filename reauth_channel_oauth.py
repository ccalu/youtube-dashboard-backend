# -*- coding: utf-8 -*-
"""
Script para Re-autorizar Canal com Scopes Corretos
Corrige o problema de playlist não ser adicionada por falta de permissões
"""

import os
import sys
import webbrowser
import requests
from datetime import datetime, timedelta, timezone
from supabase import create_client
from dotenv import load_dotenv

# Carrega variáveis
load_dotenv()

# Usa SERVICE_ROLE_KEY para bypass RLS
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

def main():
    channel_id = "UCiMgKMWsYH8a8EFp94TClIQ"

    print("=" * 80)
    print(" RE-AUTORIZAÇÃO DE CANAL COM SCOPES CORRETOS")
    print("=" * 80)
    print("\nESTE SCRIPT CORRIGIRÁ O PROBLEMA DA PLAYLIST!")
    print("\nO problema: O OAuth foi feito apenas com permissão de upload,")
    print("mas não tem permissão para adicionar vídeos a playlists.")
    print("\nSolução: Refazer o OAuth com todas as permissões necessárias.")
    print("=" * 80)

    # 1. Verifica situação atual
    print(f"\n1. Verificando situação atual do canal {channel_id}...")

    # Busca tokens atuais
    result = supabase.table('yt_oauth_tokens')\
        .select('*')\
        .eq('channel_id', channel_id)\
        .limit(1)\
        .execute()

    if result.data:
        print("   [!] Tokens OAuth existentes encontrados")
        print("   Estes tokens serão SUBSTITUÍDOS por novos com permissões corretas")

        # Pergunta se quer continuar
        resp = input("\nDeseja continuar e refazer o OAuth? (s/n): ").lower()
        if resp != 's':
            print("Operação cancelada.")
            return
    else:
        print("   [!] Nenhum token encontrado (precisará fazer OAuth do zero)")

    # 2. Busca credenciais OAuth (client_id/secret)
    print("\n2. Buscando credenciais OAuth...")
    result = supabase.table('yt_channel_credentials')\
        .select('*')\
        .eq('channel_id', channel_id)\
        .limit(1)\
        .execute()

    if not result.data:
        print("   [ERRO] Credenciais não encontradas!")
        print("   Execute o wizard primeiro para configurar o canal.")
        return

    creds = result.data[0]
    client_id = creds['client_id']
    client_secret = creds['client_secret']
    print(f"   [OK] Client ID: {client_id[:30]}...")

    # 3. Deleta tokens antigos
    print("\n3. Removendo tokens antigos...")
    result = supabase.table('yt_oauth_tokens')\
        .delete()\
        .eq('channel_id', channel_id)\
        .execute()

    if result.data:
        print(f"   [OK] Tokens antigos removidos")
    else:
        print(f"   [INFO] Nenhum token para remover")

    # 4. Gera nova URL de autorização com TODOS os scopes necessários
    print("\n4. Gerando nova autorização OAuth...")

    auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
    token_url = "https://oauth2.googleapis.com/token"
    redirect_uri = "urn:ietf:wg:oauth:2.0:oob"

    # SCOPES COMPLETOS - incluindo permissão para playlists!
    scope = " ".join([
        "https://www.googleapis.com/auth/youtube.upload",     # Upload de vídeos
        "https://www.googleapis.com/auth/youtube",            # Gerenciar playlists e canal
        "https://www.googleapis.com/auth/spreadsheets"        # Ler planilhas
    ])

    # Monta URL de autorização
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scope,
        "access_type": "offline",
        "prompt": "consent"  # Força mostrar tela de consentimento
    }

    auth_url_complete = auth_url + "?" + "&".join([f"{k}={v}" for k, v in params.items()])

    print("\n" + "=" * 80)
    print(" INSTRUÇÕES PARA RE-AUTORIZAR")
    print("=" * 80)
    print("\n1. A URL de autorização será aberta no navegador")
    print("2. Faça login com a conta do YouTube do canal")
    print("3. IMPORTANTE: Aceite TODAS as permissões solicitadas:")
    print("   - Gerenciar conta do YouTube")
    print("   - Fazer upload de vídeos")
    print("   - Ver planilhas do Google")
    print("4. Copie o código de autorização que aparecer")
    print("5. Cole o código aqui quando solicitado")
    print("\n" + "=" * 80)

    input("\nPressione ENTER para abrir o navegador...")

    # Abre navegador
    print("\n🌐 Abrindo navegador...")
    webbrowser.open(auth_url_complete)

    # Solicita código
    print("\nApós autorizar, copie o código que aparece na tela.")
    auth_code = input("Cole o código aqui: ").strip()

    if not auth_code:
        print("\n[ERRO] Código não fornecido!")
        return

    # 5. Troca código por tokens
    print("\n5. Obtendo novos tokens com permissões completas...")

    token_data = {
        "code": auth_code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }

    try:
        response = requests.post(token_url, data=token_data)
        response.raise_for_status()
        tokens = response.json()

        access_token = tokens['access_token']
        refresh_token = tokens.get('refresh_token')
        expires_in = tokens.get('expires_in', 3600)

        if not refresh_token:
            print("\n[ERRO] Refresh token não retornado!")
            print("Certifique-se de usar 'prompt=consent' na autorização")
            return

        print(f"   [OK] Access token: {access_token[:30]}...")
        print(f"   [OK] Refresh token: {refresh_token[:30]}...")
        print(f"   [OK] Expira em: {expires_in} segundos")

    except requests.exceptions.RequestException as e:
        print(f"\n[ERRO] Falha ao obter tokens: {e}")
        if hasattr(e.response, 'text'):
            print(f"Detalhes: {e.response.text}")
        return

    # 6. Salva novos tokens no banco
    print("\n6. Salvando novos tokens com permissões corretas...")

    # Calcula expiração
    token_expiry = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat()

    # Prepara dados
    oauth_data = {
        'channel_id': channel_id,
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_expiry': token_expiry,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'updated_at': datetime.now(timezone.utc).isoformat()
    }

    # Salva no banco
    result = supabase.table('yt_oauth_tokens')\
        .insert(oauth_data)\
        .execute()

    if result.data:
        print(f"   [OK] Tokens salvos com sucesso!")
    else:
        print(f"   [ERRO] Falha ao salvar tokens!")
        return

    # 7. Verifica se salvou corretamente
    print("\n7. Verificando se tokens foram salvos...")

    result = supabase.table('yt_oauth_tokens')\
        .select('channel_id, access_token, refresh_token')\
        .eq('channel_id', channel_id)\
        .limit(1)\
        .execute()

    if result.data and result.data[0]['refresh_token']:
        print(f"   [OK] Tokens confirmados no banco!")
    else:
        print(f"   [ERRO] Tokens não encontrados após salvar!")
        return

    # Sucesso!
    print("\n" + "=" * 80)
    print(" ✅ RE-AUTORIZAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 80)
    print("\nO canal agora tem TODAS as permissões necessárias:")
    print("✅ Upload de vídeos")
    print("✅ Gerenciar playlists")
    print("✅ Ler planilhas")
    print("\n🎉 O PROBLEMA DA PLAYLIST FOI CORRIGIDO!")
    print("\nPróximos uploads serão adicionados automaticamente à playlist.")
    print("\nPara testar: python daily_uploader.py --test")
    print()

if __name__ == "__main__":
    main()
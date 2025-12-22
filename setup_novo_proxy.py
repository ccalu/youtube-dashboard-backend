# -*- coding: utf-8 -*-
"""
Wizard Completo: Setup Novo Proxy + 4 Canais + OAuth
Adiciona proxy completo no sistema de upload YouTube
"""

import os
import re
import requests
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime, timezone

# Carrega variaveis
load_dotenv()

# Conecta Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# ============================================================
# VALIDADORES
# ============================================================

def validar_proxy_name(proxy_name):
    """Valida formato: proxy_cXXXX_Y"""
    pattern = r'^proxy_c\d{4}_\d+$'
    if not re.match(pattern, proxy_name):
        print(f"[ERRO] Formato invalido! Use: proxy_cXXXX_Y (ex: proxy_c0009_1)")
        return False
    return True

def validar_client_id(client_id):
    """Valida formato Google OAuth Client ID"""
    pattern = r'^\d+-[a-zA-Z0-9]+\.apps\.googleusercontent\.com$'
    if not re.match(pattern, client_id):
        print(f"[ERRO] Client ID invalido! Formato esperado: XXXXX-YYYY.apps.googleusercontent.com")
        return False
    return True

def validar_client_secret(client_secret):
    """Valida formato Google OAuth Client Secret"""
    pattern = r'^GOCSPX-[a-zA-Z0-9_-]+$'
    if not re.match(pattern, client_secret):
        print(f"[ERRO] Client Secret invalido! Formato esperado: GOCSPX-XXXX")
        return False
    return True

def validar_channel_id(channel_id):
    """Valida formato YouTube Channel ID"""
    pattern = r'^UC[a-zA-Z0-9_-]{22}$'
    if not re.match(pattern, channel_id):
        print(f"[ERRO] Channel ID invalido! Formato esperado: UCxxxxxxxxxxxxxxxxxx (24 caracteres)")
        return False
    return True

def validar_playlist_id(playlist_id):
    """Valida formato YouTube Playlist ID"""
    if not playlist_id:  # Opcional
        return True
    pattern = r'^PL[a-zA-Z0-9_-]{32}$'
    if not re.match(pattern, playlist_id):
        print(f"[ERRO] Playlist ID invalido! Formato esperado: PLxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx (34 caracteres)")
        return False
    return True

def validar_oauth_code(code):
    """Valida formato OAuth authorization code"""
    pattern = r'^4/[a-zA-Z0-9_-]+$'
    if not re.match(pattern, code):
        print(f"[ERRO] Codigo OAuth invalido! Formato esperado: 4/XXXXXXX")
        return False
    return True

# ============================================================
# FUNCOES AUXILIARES
# ============================================================

def buscar_linguas_disponiveis():
    """Busca linguas distintas no banco"""
    try:
        result = supabase.table('yt_channels')\
            .select('lingua')\
            .not_.is_('lingua', 'null')\
            .execute()

        linguas = set()
        for row in result.data:
            if row.get('lingua'):
                linguas.add(row['lingua'])

        return sorted(list(linguas))
    except:
        # Fallback se banco estiver vazio
        return ['pt', 'en', 'es', 'fr', 'de', 'it']

def buscar_subnichos_disponiveis():
    """Busca subnichos distintos no banco"""
    try:
        result = supabase.table('yt_channels')\
            .select('subnicho')\
            .not_.is_('subnicho', 'null')\
            .execute()

        subnichos = set()
        for row in result.data:
            if row.get('subnicho'):
                subnichos.add(row['subnicho'])

        return sorted(list(subnichos))
    except:
        # Fallback
        return ['terror', 'suspense', 'misterio', 'true_crime']

def contar_canais_proxy(proxy_name):
    """Conta quantos canais um proxy tem"""
    try:
        result = supabase.table('yt_channels')\
            .select('id', count='exact')\
            .eq('proxy_name', proxy_name)\
            .execute()
        return result.count or 0
    except:
        return 0

def proxy_existe(proxy_name):
    """Verifica se proxy ja existe"""
    try:
        result = supabase.table('yt_proxy_credentials')\
            .select('proxy_name')\
            .eq('proxy_name', proxy_name)\
            .execute()
        return len(result.data) > 0
    except:
        return False

def canal_existe(channel_id):
    """Verifica se canal ja existe"""
    try:
        result = supabase.table('yt_channels')\
            .select('channel_id')\
            .eq('channel_id', channel_id)\
            .execute()
        return len(result.data) > 0
    except:
        return False

# ============================================================
# FUNCOES PRINCIPAIS
# ============================================================

def adicionar_proxy(proxy_name, client_id, client_secret):
    """Adiciona proxy no Supabase"""
    try:
        data = {
            'proxy_name': proxy_name,
            'client_id': client_id,
            'client_secret': client_secret
        }

        result = supabase.table('yt_proxy_credentials')\
            .insert(data)\
            .execute()

        print(f"[OK] Proxy {proxy_name} adicionado com sucesso!")
        return True
    except Exception as e:
        print(f"[ERRO] Falha ao adicionar proxy: {e}")
        return False

def adicionar_canal(channel_id, channel_name, proxy_name, lingua, subnicho, playlist_id=None):
    """Adiciona canal no Supabase"""
    try:
        data = {
            'channel_id': channel_id,
            'channel_name': channel_name,
            'proxy_name': proxy_name,
            'lingua': lingua,
            'subnicho': subnicho,
            'is_active': True,
            'is_monetized': False  # Canais de upload nao sao monetizados
        }

        if playlist_id:
            data['default_playlist_id'] = playlist_id

        result = supabase.table('yt_channels')\
            .insert(data)\
            .execute()

        print(f"[OK] Canal {channel_name} adicionado com sucesso!")
        return True
    except Exception as e:
        print(f"[ERRO] Falha ao adicionar canal: {e}")
        return False

def gerar_url_oauth(channel_id, client_id):
    """Gera URL de autorizacao OAuth"""
    scopes = [
        'https://www.googleapis.com/auth/youtube.upload',
        'https://www.googleapis.com/auth/youtube',
        'https://www.googleapis.com/auth/youtube.force-ssl'
    ]

    params = {
        'client_id': client_id,
        'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
        'scope': ' '.join(scopes),
        'response_type': 'code',
        'access_type': 'offline',
        'prompt': 'consent'
    }

    query_string = '&'.join([f"{k}={requests.utils.quote(str(v))}" for k, v in params.items()])
    return f"https://accounts.google.com/o/oauth2/v2/auth?{query_string}"

def trocar_codigo_por_tokens(code, client_id, client_secret):
    """Troca codigo OAuth por access_token + refresh_token"""
    try:
        url = "https://oauth2.googleapis.com/token"
        data = {
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
            'grant_type': 'authorization_code'
        }

        response = requests.post(url, data=data, timeout=30)
        response.raise_for_status()

        tokens = response.json()
        return {
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'expires_in': tokens.get('expires_in', 3600)
        }
    except Exception as e:
        print(f"[ERRO] Falha ao trocar codigo por tokens: {e}")
        return None

def salvar_tokens(channel_id, access_token, refresh_token, expires_in):
    """Salva tokens OAuth no Supabase"""
    try:
        # Calcula expiry
        from datetime import datetime, timedelta, timezone
        expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        data = {
            'channel_id': channel_id,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_expiry': expiry.isoformat()
        }

        result = supabase.table('yt_oauth_tokens')\
            .insert(data)\
            .execute()

        print(f"[OK] Tokens salvos com sucesso (expira: {expiry.strftime('%Y-%m-%d %H:%M')})")
        return True
    except Exception as e:
        print(f"[ERRO] Falha ao salvar tokens: {e}")
        return False

def validar_token(access_token):
    """Testa token fazendo request para YouTube API"""
    try:
        url = "https://www.googleapis.com/youtube/v3/channels"
        headers = {'Authorization': f'Bearer {access_token}'}
        params = {'part': 'snippet', 'mine': 'true'}

        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        if 'items' in data and len(data['items']) > 0:
            channel_name = data['items'][0]['snippet']['title']
            print(f"[OK] Token valido! Canal autenticado: {channel_name}")
            return True
        else:
            print(f"[ERRO] Token valido mas nenhum canal encontrado")
            return False
    except Exception as e:
        print(f"[ERRO] Token invalido: {e}")
        return False

# ============================================================
# WIZARD PRINCIPAL
# ============================================================

def main():
    print("=" * 80)
    print("WIZARD: SETUP NOVO PROXY + CANAIS + OAUTH")
    print("=" * 80)
    print()

    # ============================================================
    # PARTE 1: CREDENCIAIS DO PROXY
    # ============================================================
    print("[1/6] CREDENCIAIS DO PROXY")
    print("-" * 80)

    while True:
        proxy_name = input("\nNome do proxy (ex: proxy_c0009_1): ").strip()
        if not proxy_name:
            print("[ERRO] Nome do proxy e obrigatorio!")
            continue
        if not validar_proxy_name(proxy_name):
            continue
        if proxy_existe(proxy_name):
            print(f"[AVISO] Proxy {proxy_name} ja existe!")
            confirma = input("Deseja usar este proxy existente? (s/n): ").strip().lower()
            if confirma == 's':
                break
            else:
                continue
        break

    if not proxy_existe(proxy_name):
        while True:
            client_id = input("Client ID: ").strip()
            if not client_id:
                print("[ERRO] Client ID e obrigatorio!")
                continue
            if not validar_client_id(client_id):
                continue
            break

        while True:
            client_secret = input("Client Secret: ").strip()
            if not client_secret:
                print("[ERRO] Client Secret e obrigatorio!")
                continue
            if not validar_client_secret(client_secret):
                continue
            break

        print(f"\n[...] Adicionando proxy {proxy_name}...")
        if not adicionar_proxy(proxy_name, client_id, client_secret):
            print("[ERRO] Falha ao adicionar proxy! Abortando...")
            return
    else:
        # Busca credenciais existentes
        result = supabase.table('yt_proxy_credentials')\
            .select('client_id, client_secret')\
            .eq('proxy_name', proxy_name)\
            .single()\
            .execute()
        client_id = result.data['client_id']
        client_secret = result.data['client_secret']
        print(f"[OK] Usando credenciais existentes do proxy {proxy_name}")

    # ============================================================
    # PARTE 2: QUANTIDADE DE CANAIS
    # ============================================================
    print(f"\n[2/6] QUANTIDADE DE CANAIS")
    print("-" * 80)

    canais_atuais = contar_canais_proxy(proxy_name)
    print(f"Canais atuais neste proxy: {canais_atuais}")

    if canais_atuais >= 4:
        print(f"[AVISO] Este proxy ja tem {canais_atuais} canais (limite recomendado: 4)")
        print("Voce pode continuar, mas pode haver problemas de quota.")

    while True:
        try:
            qtd = int(input("\nQuantos canais adicionar? (1-4): ").strip())
            if qtd < 1 or qtd > 4:
                print("[ERRO] Digite um numero entre 1 e 4")
                continue
            break
        except ValueError:
            print("[ERRO] Digite um numero valido!")

    # Busca opcoes do banco
    print("\n[...] Buscando linguas e subnichos do banco...")
    linguas_disponiveis = buscar_linguas_disponiveis()
    subnichos_disponiveis = buscar_subnichos_disponiveis()

    print(f"[OK] {len(linguas_disponiveis)} linguas disponiveis")
    print(f"[OK] {len(subnichos_disponiveis)} subnichos disponiveis")

    # ============================================================
    # PARTE 3: DADOS DOS CANAIS
    # ============================================================
    print(f"\n[3/6] DADOS DOS {qtd} CANAIS")
    print("-" * 80)

    canais = []

    for i in range(qtd):
        print(f"\n--- CANAL {i+1}/{qtd} ---")

        # Channel ID
        while True:
            channel_id = input("Channel ID (UCxxxxxxxxx): ").strip()
            if not channel_id:
                print("[ERRO] Channel ID e obrigatorio!")
                continue
            if not validar_channel_id(channel_id):
                continue
            if canal_existe(channel_id):
                print(f"[ERRO] Canal {channel_id} ja existe no banco!")
                continue
            break

        # Channel Name
        while True:
            channel_name = input("Nome do canal: ").strip()
            if not channel_name:
                print("[ERRO] Nome do canal e obrigatorio!")
                continue
            break

        # Lingua
        print(f"\nLinguas disponiveis: {', '.join(linguas_disponiveis)}")
        while True:
            lingua = input("Lingua (ex: pt): ").strip().lower()
            if not lingua:
                print("[ERRO] Lingua e obrigatoria!")
                continue
            if lingua not in linguas_disponiveis:
                print(f"[AVISO] Lingua '{lingua}' nao existe no banco, sera adicionada")
                confirma = input("Confirma? (s/n): ").strip().lower()
                if confirma != 's':
                    continue
            break

        # Subnicho
        print(f"\nSubnichos disponiveis: {', '.join(subnichos_disponiveis)}")
        while True:
            subnicho = input("Subnicho (ex: terror): ").strip().lower()
            if not subnicho:
                print("[ERRO] Subnicho e obrigatorio!")
                continue
            if subnicho not in subnichos_disponiveis:
                print(f"[AVISO] Subnicho '{subnicho}' nao existe no banco, sera adicionado")
                confirma = input("Confirma? (s/n): ").strip().lower()
                if confirma != 's':
                    continue
            break

        # Playlist ID (opcional)
        while True:
            playlist_id = input("Playlist ID (opcional, Enter para pular): ").strip()
            if not playlist_id:
                break
            if not validar_playlist_id(playlist_id):
                continue
            break

        canais.append({
            'channel_id': channel_id,
            'channel_name': channel_name,
            'lingua': lingua,
            'subnicho': subnicho,
            'playlist_id': playlist_id if playlist_id else None
        })

        print(f"[OK] Canal {i+1}/{qtd} configurado")

    # ============================================================
    # PARTE 4: ADICIONAR CANAIS NO SUPABASE
    # ============================================================
    print(f"\n[4/6] ADICIONANDO {qtd} CANAIS NO SUPABASE")
    print("-" * 80)

    for i, canal in enumerate(canais):
        print(f"\n[{i+1}/{qtd}] Adicionando {canal['channel_name']}...")
        if not adicionar_canal(
            channel_id=canal['channel_id'],
            channel_name=canal['channel_name'],
            proxy_name=proxy_name,
            lingua=canal['lingua'],
            subnicho=canal['subnicho'],
            playlist_id=canal['playlist_id']
        ):
            print(f"[ERRO] Falha ao adicionar canal {i+1}! Abortando...")
            return

    print(f"\n[OK] Todos os {qtd} canais adicionados com sucesso!")

    # ============================================================
    # PARTE 5: OAUTH PARA CADA CANAL
    # ============================================================
    print(f"\n[5/6] AUTORIZACAO OAUTH ({qtd} canais)")
    print("-" * 80)
    print("\nIMPORTANTE:")
    print("- Abra cada URL no NAVEGADOR DO PROXY (conta Google do canal)")
    print("- Autorize o acesso")
    print("- Copie o CODIGO que aparece na tela")
    print("- Cole aqui quando solicitado")
    print()

    tokens_ok = []

    for i, canal in enumerate(canais):
        print(f"\n{'='*80}")
        print(f"CANAL {i+1}/{qtd}: {canal['channel_name']} ({canal['channel_id']})")
        print(f"{'='*80}")

        # Gera URL
        url = gerar_url_oauth(canal['channel_id'], client_id)
        print(f"\n[1] Abra esta URL no navegador do proxy:")
        print(f"\n{url}\n")

        input("Pressione ENTER quando tiver aberto a URL...")

        # Aguarda codigo
        while True:
            code = input("\n[2] Cole o codigo de autorizacao aqui: ").strip()
            if not code:
                print("[ERRO] Codigo e obrigatorio!")
                continue
            if not validar_oauth_code(code):
                continue
            break

        # Troca codigo por tokens
        print("\n[...] Trocando codigo por tokens...")
        tokens = trocar_codigo_por_tokens(code, client_id, client_secret)
        if not tokens:
            print(f"[ERRO] Falha ao obter tokens do canal {i+1}!")
            print("Voce pode tentar novamente depois manualmente.")
            continue

        # Salva tokens
        print("[...] Salvando tokens no Supabase...")
        if not salvar_tokens(
            canal['channel_id'],
            tokens['access_token'],
            tokens['refresh_token'],
            tokens['expires_in']
        ):
            print(f"[ERRO] Falha ao salvar tokens do canal {i+1}!")
            continue

        # Valida token
        print("[...] Validando token...")
        if validar_token(tokens['access_token']):
            tokens_ok.append(canal['channel_name'])
        else:
            print(f"[AVISO] Token salvo mas falhou na validacao!")

    # ============================================================
    # PARTE 6: RELATORIO FINAL
    # ============================================================
    print(f"\n{'='*80}")
    print(f"RELATORIO FINAL")
    print(f"{'='*80}")
    print()
    print(f"Proxy: {proxy_name}")
    print(f"Canais adicionados: {qtd}")
    print(f"Tokens OAuth OK: {len(tokens_ok)}/{qtd}")
    print()

    if len(tokens_ok) == qtd:
        print("[SUCESSO] Todos os canais estao prontos para upload!")
    else:
        print(f"[AVISO] {qtd - len(tokens_ok)} canais com problemas de OAuth")
        print("Execute novamente ou autorize manualmente.")

    print()
    print("Proximos passos:")
    print("1. Testar upload de 1 video em um dos canais")
    print("2. Verificar logs no Railway")
    print()
    print(f"{'='*80}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[CANCELADO] Wizard interrompido pelo usuario")
    except Exception as e:
        print(f"\n\n[ERRO FATAL] {e}")
        import traceback
        traceback.print_exc()

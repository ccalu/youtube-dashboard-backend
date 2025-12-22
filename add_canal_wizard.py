# -*- coding: utf-8 -*-
"""
Wizard: Adicionar 1 Canal em Proxy Existente
Adiciona canal avulso em proxy ja configurado
"""

import os
import re
import requests
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

# Carrega variaveis
load_dotenv()

# Conecta Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# ============================================================
# VALIDADORES (mesmos do setup_novo_proxy.py)
# ============================================================

def validar_channel_id(channel_id):
    """Valida formato YouTube Channel ID"""
    pattern = r'^UC[a-zA-Z0-9_-]{22}$'
    if not re.match(pattern, channel_id):
        print(f"[ERRO] Channel ID invalido! Formato esperado: UCxxxxxxxxxxxxxxxxxx (24 caracteres)")
        return False
    return True

def validar_playlist_id(playlist_id):
    """Valida formato YouTube Playlist ID"""
    if not playlist_id:
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

def validar_client_id(client_id):
    """Valida formato Google Cloud Client ID"""
    pattern = r'^\d+-[a-zA-Z0-9]+\.apps\.googleusercontent\.com$'
    if not re.match(pattern, client_id):
        print(f"[ERRO] Client ID invalido! Formato esperado: 123456789-abc.apps.googleusercontent.com")
        return False
    return True

def validar_client_secret(client_secret):
    """Valida formato Google Cloud Client Secret"""
    pattern = r'^GOCSPX-[a-zA-Z0-9_-]+$'
    if not re.match(pattern, client_secret):
        print(f"[ERRO] Client Secret invalido! Formato esperado: GOCSPX-xxxxxxxxx")
        return False
    return True

# ============================================================
# FUNCOES AUXILIARES
# ============================================================

def listar_proxies():
    """Lista todos os proxies cadastrados"""
    try:
        result = supabase.table('yt_proxy_credentials')\
            .select('proxy_name, client_id')\
            .execute()

        if not result.data:
            return []

        proxies = []
        for p in result.data:
            # Conta canais
            canais_result = supabase.table('yt_channels')\
                .select('id', count='exact')\
                .eq('proxy_name', p['proxy_name'])\
                .execute()

            qtd_canais = canais_result.count or 0

            proxies.append({
                'proxy_name': p['proxy_name'],
                'client_id': p['client_id'],
                'qtd_canais': qtd_canais
            })

        return proxies
    except Exception as e:
        print(f"[ERRO] Falha ao listar proxies: {e}")
        return []

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
        return ['terror', 'suspense', 'misterio', 'true_crime']

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

def buscar_proxy_credentials(proxy_name):
    """Busca credenciais de um proxy"""
    try:
        result = supabase.table('yt_proxy_credentials')\
            .select('client_id, client_secret')\
            .eq('proxy_name', proxy_name)\
            .single()\
            .execute()
        return result.data
    except:
        return None

# ============================================================
# FUNCOES PRINCIPAIS (mesmas do setup_novo_proxy.py)
# ============================================================

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
            'is_monetized': False
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
    print("WIZARD: ADICIONAR NOVO CANAL (ARQUITETURA V2)")
    print("=" * 80)
    print()
    print("IMPORTANTE:")
    print("- 1 canal = 1 projeto Google Cloud = 1 Client ID/Secret unico")
    print("- Isolamento total entre canais (contingencia maxima)")
    print("- Proxy identifica apenas maquina fisica (AdsPower, VPS, etc)")
    print()

    # ============================================================
    # PARTE 1: DADOS DO CANAL
    # ============================================================
    print("[1/5] DADOS DO CANAL")
    print("-" * 80)

    # Channel ID
    while True:
        channel_id = input("\nChannel ID (UCxxxxxxxxx): ").strip()
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

    # Busca opcoes do banco
    print("\n[...] Buscando linguas e subnichos do banco...")
    linguas_disponiveis = buscar_linguas_disponiveis()
    subnichos_disponiveis = buscar_subnichos_disponiveis()

    # Lingua
    print(f"\nLinguas disponiveis:")
    for i, lang in enumerate(linguas_disponiveis):
        print(f"[{i+1}] {lang}")
    print(f"[{len(linguas_disponiveis)+1}] Outro (digitar manualmente)")

    while True:
        try:
            escolha = input(f"\nEscolha a lingua (1-{len(linguas_disponiveis)+1}): ").strip()
            escolha_num = int(escolha)

            if escolha_num < 1 or escolha_num > len(linguas_disponiveis) + 1:
                print(f"[ERRO] Digite um numero entre 1 e {len(linguas_disponiveis)+1}")
                continue

            if escolha_num == len(linguas_disponiveis) + 1:
                # Opcao "Outro"
                lingua = input("Digite a lingua manualmente (ex: pt): ").strip().lower()
                if not lingua:
                    print("[ERRO] Lingua e obrigatoria!")
                    continue
                print(f"[AVISO] Lingua '{lingua}' nao existe no banco, sera adicionada")
                confirma = input("Confirma? (s/n): ").strip().lower()
                if confirma != 's':
                    continue
            else:
                lingua = linguas_disponiveis[escolha_num - 1]

            break
        except ValueError:
            print("[ERRO] Digite um numero valido!")
            continue

    # Subnicho
    print(f"\nSubnichos disponiveis:")
    for i, sub in enumerate(subnichos_disponiveis):
        print(f"[{i+1}] {sub}")
    print(f"[{len(subnichos_disponiveis)+1}] Outro (digitar manualmente)")

    while True:
        try:
            escolha = input(f"\nEscolha o subnicho (1-{len(subnichos_disponiveis)+1}): ").strip()
            escolha_num = int(escolha)

            if escolha_num < 1 or escolha_num > len(subnichos_disponiveis) + 1:
                print(f"[ERRO] Digite um numero entre 1 e {len(subnichos_disponiveis)+1}")
                continue

            if escolha_num == len(subnichos_disponiveis) + 1:
                # Opcao "Outro"
                subnicho = input("Digite o subnicho manualmente (ex: terror): ").strip().lower()
                if not subnicho:
                    print("[ERRO] Subnicho e obrigatorio!")
                    continue
                print(f"[AVISO] Subnicho '{subnicho}' nao existe no banco, sera adicionado")
                confirma = input("Confirma? (s/n): ").strip().lower()
                if confirma != 's':
                    continue
            else:
                subnicho = subnichos_disponiveis[escolha_num - 1]

            break
        except ValueError:
            print("[ERRO] Digite um numero valido!")
            continue

    # Playlist ID (opcional)
    while True:
        playlist_id = input("Playlist ID (opcional, Enter para pular): ").strip()
        if not playlist_id:
            break
        if not validar_playlist_id(playlist_id):
            continue
        break

    # ============================================================
    # PARTE 2: CREDENCIAIS GOOGLE CLOUD (OAUTH)
    # ============================================================
    print(f"\n[2/5] CREDENCIAIS DO PROJETO GOOGLE CLOUD")
    print("-" * 80)
    print()
    print("IMPORTANTE: Cada canal deve ter seu proprio projeto Google Cloud!")
    print("Criado no navegador do proxy (AdsPower, VPS, etc)")
    print()

    # Client ID
    while True:
        client_id = input("Client ID: ").strip()
        if not client_id:
            print("[ERRO] Client ID e obrigatorio!")
            continue
        if not validar_client_id(client_id):
            continue
        break

    # Client Secret
    while True:
        client_secret = input("Client Secret: ").strip()
        if not client_secret:
            print("[ERRO] Client Secret e obrigatorio!")
            continue
        if not validar_client_secret(client_secret):
            continue
        break

    print(f"\n[OK] Credenciais validadas!")

    # ============================================================
    # PARTE 3: IDENTIFICACAO DO PROXY
    # ============================================================
    print(f"\n[3/5] IDENTIFICACAO DO PROXY (MAQUINA FISICA)")
    print("-" * 80)
    print()
    print("Proxy = Maquina fisica onde canal sera autorizado")
    print("Exemplo: proxy_c0008_1 (perfil AdsPower C0008.1)")
    print()

    # Proxy Name
    while True:
        proxy_name = input("Proxy name (ex: proxy_c0008_1): ").strip().lower()
        if not proxy_name:
            print("[ERRO] Proxy name e obrigatorio!")
            continue
        # Validacao basica de formato
        if not proxy_name.startswith('proxy_'):
            print("[ERRO] Proxy name deve comecar com 'proxy_' (ex: proxy_c0008_1)")
            continue
        break

    print(f"\n[OK] Proxy identificado: {proxy_name}")

    # ============================================================
    # PARTE 4: ADICIONAR CANAL NO SUPABASE
    # ============================================================
    print(f"\n[4/5] ADICIONANDO CANAL NO SUPABASE")
    print("-" * 80)

    print(f"\n[...] Adicionando {channel_name} ao proxy {proxy_name}...")
    if not adicionar_canal(
        channel_id=channel_id,
        channel_name=channel_name,
        proxy_name=proxy_name,
        lingua=lingua,
        subnicho=subnicho,
        playlist_id=playlist_id if playlist_id else None
    ):
        print("[ERRO] Falha ao adicionar canal! Abortando...")
        return

    # Salvar credenciais OAuth do canal
    print(f"[...] Salvando credenciais OAuth do canal...")
    try:
        from yt_uploader.database import save_channel_credentials
        if not save_channel_credentials(channel_id, client_id, client_secret):
            print("[ERRO] Falha ao salvar credenciais OAuth!")
            print("Canal foi adicionado, mas sem credenciais.")
            return
        print("[OK] Credenciais OAuth salvas com sucesso!")
    except Exception as e:
        print(f"[ERRO] Falha ao salvar credenciais: {e}")
        return

    # ============================================================
    # PARTE 5: OAUTH
    # ============================================================
    print(f"\n[5/5] AUTORIZACAO OAUTH")
    print("-" * 80)
    print("\nIMPORTANTE:")
    print("- Abra a URL no NAVEGADOR DO PROXY (conta Google do canal)")
    print("- Autorize o acesso")
    print("- Copie o CODIGO que aparece na tela")
    print("- Cole aqui quando solicitado")
    print()

    # Gera URL
    url = gerar_url_oauth(channel_id, client_id)
    print(f"[1] Abra esta URL no navegador do proxy:")
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
        print("[ERRO] Falha ao obter tokens!")
        print("Canal foi adicionado, mas OAuth falhou.")
        print("Tente autorizar manualmente depois.")
        return

    # Salva tokens
    print("[...] Salvando tokens no Supabase...")
    if not salvar_tokens(
        channel_id,
        tokens['access_token'],
        tokens['refresh_token'],
        tokens['expires_in']
    ):
        print("[ERRO] Falha ao salvar tokens!")
        return

    # Valida token
    print("[...] Validando token...")
    token_ok = validar_token(tokens['access_token'])

    # ============================================================
    # RELATORIO FINAL
    # ============================================================
    print(f"\n{'='*80}")
    print(f"RELATORIO FINAL")
    print(f"{'='*80}")
    print()
    print(f"Canal: {channel_name} ({channel_id})")
    print(f"Proxy: {proxy_name}")
    print(f"OAuth: {'[OK] Autorizado' if token_ok else '[ERRO] Falhou'}")
    print()

    if token_ok:
        print("[SUCESSO] Canal pronto para upload!")
    else:
        print("[AVISO] Canal adicionado mas OAuth com problemas")
        print("Tente autorizar novamente manualmente.")

    print()
    print("Proximos passos:")
    print("1. Testar upload de 1 video")
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

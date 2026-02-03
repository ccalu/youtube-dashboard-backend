# -*- coding: utf-8 -*-
"""
Wizard V2: Adicionar Canal com Upload Automático
Versão atualizada para sistema de upload diário
"""

import os
import re
import requests
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse, parse_qs

# Carrega variaveis
load_dotenv()

# Conecta Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# ============================================================
# MAPEAMENTO DE IDIOMAS (Nome → Código ISO 639-1)
# ============================================================
IDIOMAS_MAP = {
    'Alemão': 'de',
    'Árabe': 'ar',
    'Coreano': 'ko',
    'Espanhol': 'es',
    'Francês': 'fr',
    'Hindi': 'hi',
    'Inglês': 'en',
    'Italiano': 'it',
    'Japonês': 'ja',
    'Polonês': 'pl',
    'Português': 'pt',
    'Russo': 'ru',
    'Turco': 'tr'
}

# ============================================================
# VALIDADORES
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

def validar_spreadsheet_id(spreadsheet_id):
    """Valida formato Google Sheets ID"""
    # Google Sheets IDs têm entre 40-45 caracteres alfanuméricos com _ e -
    pattern = r'^[a-zA-Z0-9_-]{40,50}$'
    if not re.match(pattern, spreadsheet_id):
        print(f"[ERRO] Spreadsheet ID invalido! Deve ter ~44 caracteres alfanuméricos")
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

def buscar_linguas_disponiveis():
    """Retorna lista completa de idiomas disponíveis"""
    # SEMPRE retorna TODOS os idiomas (ordem alfabética)
    # Não depende do banco - sempre funciona!
    return sorted(IDIOMAS_MAP.keys())

def buscar_subnichos_disponiveis():
    """Retorna lista de subnichos reais do sistema"""
    # Subnichos que REALMENTE existem nos nossos canais
    # Ordem: do mais usado para o menos usado
    subnichos = [
        'Desmonetizados',        # 17 canais
        'Historias Sombrias',    # 9 canais
        'Relatos de Guerra',     # 7 canais
        'Monetizados',           # 5 canais
        'Guerras e Civilizações', # 1 canal
        'Terror'                 # 1 canal
    ]

    return subnichos

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

def extrair_spreadsheet_id_da_url(url):
    """Extrai ID da planilha de uma URL do Google Sheets"""
    # Formatos suportados:
    # https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
    # https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit#gid=0
    pattern = r'/spreadsheets/d/([a-zA-Z0-9_-]+)'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None

# ============================================================
# FUNCOES PRINCIPAIS
# ============================================================

def verificar_acesso_planilha(spreadsheet_id):
    """Verifica se consegue acessar a planilha do Google Sheets"""
    try:
        import json
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials

        # Buscar credenciais
        creds_str = os.getenv("GOOGLE_SHEETS_CREDENTIALS_2")
        if not creds_str:
            print("[AVISO] Não foi possível verificar acesso (credenciais não configuradas localmente)")
            return True  # Permite continuar (será verificado em produção)

        # Configurar cliente
        creds_dict = json.loads(creds_str)
        scope = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(credentials)

        # Tentar abrir planilha
        sheet = client.open_by_key(spreadsheet_id)
        print(f"[OK] Planilha acessível: {sheet.title}")

        # Verificar primeira aba
        worksheet = sheet.get_worksheet(0)
        print(f"[OK] Primeira aba: {worksheet.title}")

        return True

    except gspread.SpreadsheetNotFound:
        print("[ERRO] Planilha não encontrada! Verifique o ID.")
        print("Possíveis causas:")
        print("  1. ID incorreto")
        print("  2. Planilha não existe")
        print("  3. Planilha não está compartilhada com a conta de serviço")
        return False
    except gspread.APIError as e:
        print(f"[ERRO] Erro da API Google Sheets: {e}")
        return False
    except Exception as e:
        print(f"[AVISO] Não foi possível verificar acesso: {e}")
        # Permite continuar mas avisa
        confirma = input("Deseja continuar mesmo assim? (s/n): ").strip().lower()
        return confirma == 's'

def adicionar_canal_v2(channel_id, channel_name, lingua, subnicho, spreadsheet_id,
                      is_monetized, playlist_id=None):
    """Adiciona canal no Supabase com configuração de upload automático"""
    try:
        data = {
            'channel_id': channel_id,
            'channel_name': channel_name,
            'proxy_name': None,  # V2.0: proxy_name não é necessário
            'lingua': lingua,
            'subnicho': subnicho,
            'spreadsheet_id': spreadsheet_id,  # NOVO!
            'is_active': True,
            'is_monetized': is_monetized,  # Agora pergunta ao usuário
            'upload_automatico': True  # SEMPRE TRUE para novos canais
        }

        if playlist_id:
            data['default_playlist_id'] = playlist_id

        result = supabase.table('yt_channels')\
            .insert(data)\
            .execute()

        print(f"[OK] Canal {channel_name} adicionado com sucesso!")
        print(f"    - Upload automático: ATIVADO")
        print(f"    - Monetizado: {'SIM' if is_monetized else 'NÃO'}")
        print(f"    - Planilha configurada: SIM")
        return True
    except Exception as e:
        print(f"[ERRO] Falha ao adicionar canal: {e}")
        return False

def extrair_codigo_da_url(url_completa):
    """Extrai codigo OAuth de uma URL de redirect (http://localhost:8080/?code=...)"""
    try:
        parsed = urlparse(url_completa)
        params = parse_qs(parsed.query)

        if 'code' in params:
            return params['code'][0]
        else:
            return None
    except:
        return None

def gerar_url_oauth(channel_id, client_id):
    """Gera URL de autorizacao OAuth"""
    scopes = [
        'https://www.googleapis.com/auth/youtube.upload',
        'https://www.googleapis.com/auth/youtube',
        'https://www.googleapis.com/auth/youtube.force-ssl'
    ]

    params = {
        'client_id': client_id,
        'redirect_uri': 'http://localhost:8080',
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
            'redirect_uri': 'http://localhost:8080',
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

def salvar_credenciais_canal(channel_id, client_id, client_secret):
    """Salva as credenciais OAuth do canal no banco de dados"""
    try:
        # Primeiro verifica se já existe
        result = supabase.table('yt_channel_credentials').select('id').eq('channel_id', channel_id).execute()

        if result.data:
            # Atualiza se já existir
            result = supabase.table('yt_channel_credentials').update({
                'client_id': client_id,
                'client_secret': client_secret,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }).eq('channel_id', channel_id).execute()
            print(f"[OK] Credenciais atualizadas para o canal {channel_id}")
        else:
            # Insere se não existir
            result = supabase.table('yt_channel_credentials').insert({
                'channel_id': channel_id,
                'client_id': client_id,
                'client_secret': client_secret,
                'created_at': datetime.now(timezone.utc).isoformat()
            }).execute()
            print(f"[OK] Credenciais inseridas para o canal {channel_id}")

        return True
    except Exception as e:
        print(f"[ERRO] Erro ao salvar credenciais: {e}")
        return False

# ============================================================
# WIZARD PRINCIPAL V2
# ============================================================

def main():
    print("=" * 80)
    print("WIZARD V2: ADICIONAR CANAL COM UPLOAD AUTOMÁTICO")
    print("=" * 80)
    print()
    print("IMPORTANTE:")
    print("- Todos os canais adicionados terão upload automático ATIVADO")
    print("- Sistema fará 1 upload por dia após coleta diária")
    print("- Canais monetizados têm prioridade no processamento")
    print()

    # ============================================================
    # PARTE 1: DADOS DO CANAL
    # ============================================================
    print("[1/4] DADOS DO CANAL")
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

    # Busca opcoes de linguas e subnichos
    print("\n[...] Carregando opcoes...")
    linguas_disponiveis = buscar_linguas_disponiveis()
    subnichos_disponiveis = buscar_subnichos_disponiveis()

    # Lingua (movido para logo após nome)
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
                lingua = input("Digite o codigo ISO da lingua (ex: pt, es, fr): ").strip().lower()
                if not lingua:
                    print("[ERRO] Lingua e obrigatoria!")
                    continue
                if len(lingua) != 2:
                    print("[ERRO] Codigo ISO deve ter 2 letras (ex: pt, es, fr)")
                    continue
                print(f"[AVISO] Lingua '{lingua}' nao existe na lista padrao, sera adicionada")
                confirma = input("Confirma? (s/n): ").strip().lower()
                if confirma != 's':
                    continue
            else:
                # Pega nome escolhido e converte para codigo ISO
                lingua_nome = linguas_disponiveis[escolha_num - 1]
                lingua = IDIOMAS_MAP[lingua_nome]
                print(f"[OK] Lingua selecionada: {lingua_nome} (codigo: {lingua})")

            break
        except ValueError:
            print("[ERRO] Digite um numero valido!")
            continue

    # Subnicho (logo após língua)
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
                subnicho = input("Digite o subnicho manualmente (ex: terror): ").strip()
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

    # Canal monetizado? (após categorização)
    print("\n💰 MONETIZAÇÃO")
    while True:
        monetizado = input("Este canal é monetizado? (s/n): ").strip().lower()
        if monetizado not in ['s', 'n']:
            print("[ERRO] Digite 's' para sim ou 'n' para não")
            continue
        is_monetized = (monetizado == 's')
        break

    # Playlist ID (opcional)
    while True:
        playlist_id = input("\nPlaylist ID (opcional, Enter para pular): ").strip()
        if not playlist_id:
            break
        if not validar_playlist_id(playlist_id):
            continue
        break

    # Spreadsheet ID (movido para o final das configs)
    print("\n📊 PLANILHA DO GOOGLE SHEETS (OBRIGATÓRIO)")
    print("Cole a URL completa da planilha ou apenas o ID")
    print("Exemplo: https://docs.google.com/spreadsheets/d/1234.../edit")
    while True:
        spreadsheet_input = input("\nURL ou ID da planilha: ").strip()
        if not spreadsheet_input:
            print("[ERRO] Planilha é obrigatória para upload automático!")
            continue

        # Tenta extrair ID da URL
        if spreadsheet_input.startswith('http'):
            spreadsheet_id = extrair_spreadsheet_id_da_url(spreadsheet_input)
            if not spreadsheet_id:
                print("[ERRO] Não foi possível extrair o ID da URL fornecida!")
                continue
        else:
            spreadsheet_id = spreadsheet_input

        if not validar_spreadsheet_id(spreadsheet_id):
            print("[ERRO] ID da planilha inválido!")
            continue

        print(f"[OK] Formato do ID válido: {spreadsheet_id[:20]}...")

        # Verificar acesso real à planilha
        print("\n[...] Verificando acesso à planilha...")
        if not verificar_acesso_planilha(spreadsheet_id):
            print("[ERRO] Não foi possível acessar a planilha!")
            continue

        break

    # ============================================================
    # PARTE 2: CREDENCIAIS GOOGLE CLOUD (OAUTH)
    # ============================================================
    print(f"\n[2/4] CREDENCIAIS DO PROJETO GOOGLE CLOUD")
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
    # PARTE 3: ADICIONAR CANAL NO SUPABASE
    # ============================================================
    print(f"\n[3/4] ADICIONANDO CANAL NO SUPABASE")
    print("-" * 80)

    print(f"\n[...] Adicionando canal {channel_name}...")
    print(f"      Upload automático: ATIVADO")
    print(f"      Monetizado: {'SIM' if is_monetized else 'NÃO'}")
    print(f"      Planilha: {spreadsheet_id[:20]}...")

    if not adicionar_canal_v2(
        channel_id=channel_id,
        channel_name=channel_name,
        lingua=lingua,
        subnicho=subnicho,
        spreadsheet_id=spreadsheet_id,
        is_monetized=is_monetized,
        playlist_id=playlist_id if playlist_id else None
    ):
        print("[ERRO] Falha ao adicionar canal! Abortando...")
        return

    # Salvar credenciais OAuth do canal
    print(f"[...] Salvando credenciais OAuth do canal...")
    if not salvar_credenciais_canal(channel_id, client_id, client_secret):
        print("[ERRO] Falha ao salvar credenciais OAuth!")
        print("Canal foi adicionado, mas sem credenciais.")
        return
    print("[OK] Credenciais OAuth salvas com sucesso!")

    # ============================================================
    # PARTE 4: OAUTH
    # ============================================================
    print(f"\n[4/4] AUTORIZACAO OAUTH")
    print("-" * 80)
    print("\nIMPORTANTE:")
    print("- Abra a URL no NAVEGADOR DO PROXY (conta Google do canal)")
    print("- Autorize o acesso")
    print("- Google vai redirecionar para http://localhost:8080")
    print("- Copie a URL COMPLETA do redirect")
    print()

    # Gera URL OAuth
    oauth_url = gerar_url_oauth(channel_id, client_id)
    print(f"URL de autorizacao:")
    print("-" * 80)
    print(oauth_url)
    print("-" * 80)

    # Aguarda codigo
    print("\nApos autorizar, cole aqui a URL COMPLETA do redirect")
    print("(deve comecar com http://localhost:8080/?code=...)")

    while True:
        redirect_url = input("\nURL de redirect: ").strip()
        if not redirect_url:
            print("[ERRO] URL e obrigatoria!")
            continue

        # Extrai codigo
        code = extrair_codigo_da_url(redirect_url)
        if not code:
            print("[ERRO] Codigo OAuth nao encontrado na URL!")
            print("A URL deve conter ?code=4/xxxxx")
            continue

        if not validar_oauth_code(code):
            continue

        print(f"[OK] Codigo extraido: {code[:20]}...")
        break

    # Troca codigo por tokens
    print(f"\n[...] Trocando codigo por tokens...")
    tokens = trocar_codigo_por_tokens(code, client_id, client_secret)
    if not tokens:
        print("[ERRO] Falha ao obter tokens! Abortando...")
        return

    # Salva tokens
    print(f"[...] Salvando tokens no banco...")
    if not salvar_tokens(
        channel_id,
        tokens['access_token'],
        tokens['refresh_token'],
        tokens['expires_in']
    ):
        print("[ERRO] Falha ao salvar tokens!")
        return

    # Valida token
    print(f"[...] Validando token com YouTube API...")
    if not validar_token(tokens['access_token']):
        print("[AVISO] Token pode estar invalido, mas foi salvo")

    # ============================================================
    # RESUMO FINAL
    # ============================================================
    print("\n" + "=" * 80)
    print("✅ CANAL ADICIONADO COM SUCESSO!")
    print("=" * 80)
    print(f"Canal: {channel_name}")
    print(f"ID: {channel_id}")
    print(f"Lingua: {lingua}")
    print(f"Subnicho: {subnicho}")
    print(f"Monetizado: {'SIM' if is_monetized else 'NÃO'}")
    print(f"Upload automático: ATIVADO")
    print(f"Planilha: Configurada")

    if playlist_id:
        print(f"Playlist: {playlist_id}")

    print("\n📌 PRÓXIMOS PASSOS:")
    print("1. Configure a planilha com os vídeos (coluna J = 'done')")
    print("2. O sistema fará 1 upload por dia automaticamente")
    print("3. Acompanhe pelo dashboard em localhost:5002")
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
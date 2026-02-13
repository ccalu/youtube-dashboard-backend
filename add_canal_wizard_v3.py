# -*- coding: utf-8 -*-
"""
Wizard V3: Adicionar Canal com Upload Automatico
Visual profissional com cores - Logica identica ao V2
"""

import os
import re
import requests
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse, parse_qs
from colorama import init, Fore, Style

# Inicializa colorama para Windows
init(autoreset=True)

# Carrega variaveis
load_dotenv()

# Conecta Supabase (usa SERVICE_ROLE_KEY para bypass RLS)
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
)

# ============================================================
# FUNCOES DE FORMATACAO VISUAL
# ============================================================

def print_header():
    """Imprime cabecalho principal"""
    print(f"\n{Fore.CYAN}{'=' * 70}")
    print(f"{Fore.CYAN}|{' ' * 10}{Fore.YELLOW}{Style.BRIGHT}WIZARD V3 - ADICIONAR CANAL COM UPLOAD AUTOMATICO{Style.RESET_ALL}{' ' * 8}{Fore.CYAN}|")
    print(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}\n")

def print_section(number, total, title):
    """Imprime cabecalho de secao"""
    print(f"\n{Fore.CYAN}{'─' * 70}")
    print(f"  {Fore.YELLOW}{Style.BRIGHT}[{number}/{total}] {title}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'─' * 70}{Style.RESET_ALL}")

def print_error(msg):
    print(f"  {Fore.RED}{Style.BRIGHT}[ERRO]{Style.RESET_ALL} {Fore.RED}{msg}{Style.RESET_ALL}")

def print_ok(msg):
    print(f"  {Fore.GREEN}{Style.BRIGHT}[OK]{Style.RESET_ALL} {Fore.GREEN}{msg}{Style.RESET_ALL}")

def print_warning(msg):
    print(f"  {Fore.YELLOW}{Style.BRIGHT}[AVISO]{Style.RESET_ALL} {Fore.YELLOW}{msg}{Style.RESET_ALL}")

def print_processing(msg):
    print(f"  {Fore.MAGENTA}[...] {msg}{Style.RESET_ALL}")

def prompt(msg):
    """Input formatado"""
    return input(f"  {Fore.YELLOW}> {msg}: {Style.RESET_ALL}").strip()

# ============================================================
# MAPEAMENTO DE IDIOMAS (Nome -> Codigo ISO 639-1)
# ============================================================
IDIOMAS_MAP = {
    'Alemao': 'de',
    'Arabe': 'ar',
    'Coreano': 'ko',
    'Espanhol': 'es',
    'Frances': 'fr',
    'Hindi': 'hi',
    'Ingles': 'en',
    'Italiano': 'it',
    'Japones': 'ja',
    'Polones': 'pl',
    'Portugues': 'pt',
    'Russo': 'ru',
    'Turco': 'tr'
}

# ============================================================
# VALIDADORES (identicos ao V2)
# ============================================================

def validar_channel_id(channel_id):
    """Valida formato YouTube Channel ID"""
    pattern = r'^UC[a-zA-Z0-9_-]{22}$'
    if not re.match(pattern, channel_id):
        print_error("Channel ID invalido! Formato esperado: UCxxxxxxxxxxxxxxxxxx (24 caracteres)")
        return False
    return True

def validar_playlist_id(playlist_id):
    """Valida formato YouTube Playlist ID"""
    if not playlist_id:
        return True
    pattern = r'^PL[a-zA-Z0-9_-]{32}$'
    if not re.match(pattern, playlist_id):
        print_error("Playlist ID invalido! Formato esperado: PLxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx (34 caracteres)")
        return False
    return True

def validar_spreadsheet_id(spreadsheet_id):
    """Valida formato Google Sheets ID"""
    pattern = r'^[a-zA-Z0-9_-]{40,50}$'
    if not re.match(pattern, spreadsheet_id):
        print_error("Spreadsheet ID invalido! Deve ter ~44 caracteres alfanumericos")
        return False
    return True

def validar_oauth_code(code):
    """Valida formato OAuth authorization code"""
    pattern = r'^4/[a-zA-Z0-9_-]+$'
    if not re.match(pattern, code):
        print_error("Codigo OAuth invalido! Formato esperado: 4/XXXXXXX")
        return False
    return True

def validar_client_id(client_id):
    """Valida formato Google Cloud Client ID"""
    pattern = r'^\d+-[a-zA-Z0-9]+\.apps\.googleusercontent\.com$'
    if not re.match(pattern, client_id):
        print_error("Client ID invalido! Formato esperado: 123456789-abc.apps.googleusercontent.com")
        return False
    return True

def validar_client_secret(client_secret):
    """Valida formato Google Cloud Client Secret"""
    pattern = r'^GOCSPX-[a-zA-Z0-9_-]+$'
    if not re.match(pattern, client_secret):
        print_error("Client Secret invalido! Formato esperado: GOCSPX-xxxxxxxxx")
        return False
    return True

# ============================================================
# FUNCOES AUXILIARES (identicas ao V2)
# ============================================================

def buscar_linguas_disponiveis():
    """Retorna lista completa de idiomas disponiveis"""
    return sorted(IDIOMAS_MAP.keys())

def buscar_subnichos_disponiveis():
    """Retorna lista de subnichos reais do sistema"""
    subnichos = [
        'Desmonetizados',
        'Historias Sombrias',
        'Relatos de Guerra',
        'Monetizados',
        'Guerras e Civilizacoes',
        'Terror'
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
    pattern = r'/spreadsheets/d/([a-zA-Z0-9_-]+)'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None

# ============================================================
# FUNCOES PRINCIPAIS (identicas ao V2)
# ============================================================

def verificar_acesso_planilha(spreadsheet_id):
    """Verifica se consegue acessar a planilha do Google Sheets"""
    import json
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials

    try:
        creds_str = os.getenv("GOOGLE_SHEETS_CREDENTIALS_2")
        if not creds_str:
            print_warning("Nao foi possivel verificar acesso (credenciais nao configuradas localmente)")
            return True

        creds_dict = json.loads(creds_str)
        scope = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(credentials)

        sheet = client.open_by_key(spreadsheet_id)
        print_ok(f"Planilha acessivel: {sheet.title}")

        worksheet = sheet.get_worksheet(0)
        print_ok(f"Primeira aba: {worksheet.title}")

        return True

    except gspread.SpreadsheetNotFound:
        print_error("Planilha nao encontrada! Verifique o ID.")
        print(f"  {Fore.WHITE}Possiveis causas:")
        print(f"  {Fore.WHITE}  1. ID incorreto")
        print(f"  {Fore.WHITE}  2. Planilha nao existe")
        print(f"  {Fore.WHITE}  3. Planilha nao esta compartilhada com a conta de servico")
        return False
    except gspread.APIError as e:
        print_error(f"Erro da API Google Sheets: {e}")
        return False
    except Exception as e:
        print_warning(f"Nao foi possivel verificar acesso: {e}")
        confirma = prompt("Deseja continuar mesmo assim? (s/n)").lower()
        return confirma == 's'

def adicionar_canal_v2(channel_id, channel_name, lingua, subnicho, spreadsheet_id,
                      is_monetized, playlist_id=None):
    """Adiciona canal no Supabase com configuracao de upload automatico"""
    try:
        data = {
            'channel_id': channel_id,
            'channel_name': channel_name,
            'proxy_name': None,
            'lingua': lingua,
            'subnicho': subnicho,
            'spreadsheet_id': spreadsheet_id,
            'is_active': True,
            'is_monetized': is_monetized,
            'upload_automatico': True
        }

        if playlist_id:
            data['default_playlist_id'] = playlist_id

        result = supabase.table('yt_channels')\
            .insert(data)\
            .execute()

        print_ok(f"Canal {channel_name} adicionado com sucesso!")
        print(f"    {Fore.WHITE}- Upload automatico: {Fore.GREEN}ATIVADO{Style.RESET_ALL}")
        print(f"    {Fore.WHITE}- Monetizado: {Fore.GREEN if is_monetized else Fore.RED}{'SIM' if is_monetized else 'NAO'}{Style.RESET_ALL}")
        print(f"    {Fore.WHITE}- Planilha configurada: {Fore.GREEN}SIM{Style.RESET_ALL}")
        return True
    except Exception as e:
        print_error(f"Falha ao adicionar canal: {e}")
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
        'https://www.googleapis.com/auth/youtube.force-ssl',
        'https://www.googleapis.com/auth/spreadsheets'
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
        print_error(f"Falha ao trocar codigo por tokens: {e}")
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

        print_ok(f"Tokens salvos com sucesso (expira: {expiry.strftime('%Y-%m-%d %H:%M')})")
        return True
    except Exception as e:
        print_error(f"Falha ao salvar tokens: {e}")
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
            print_ok(f"Token valido! Canal autenticado: {channel_name}")
            return True
        else:
            print_error("Token valido mas nenhum canal encontrado")
            return False
    except Exception as e:
        print_error(f"Token invalido: {e}")
        return False

def salvar_credenciais_canal(channel_id, client_id, client_secret):
    """Salva as credenciais OAuth do canal no banco de dados"""
    try:
        result = supabase.table('yt_channel_credentials').select('id').eq('channel_id', channel_id).execute()

        if result.data:
            result = supabase.table('yt_channel_credentials').update({
                'client_id': client_id,
                'client_secret': client_secret,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }).eq('channel_id', channel_id).execute()
            print_ok(f"Credenciais atualizadas para o canal {channel_id}")
        else:
            result = supabase.table('yt_channel_credentials').insert({
                'channel_id': channel_id,
                'client_id': client_id,
                'client_secret': client_secret,
                'created_at': datetime.now(timezone.utc).isoformat()
            }).execute()
            print_ok(f"Credenciais inseridas para o canal {channel_id}")

        return True
    except Exception as e:
        print_error(f"Erro ao salvar credenciais: {e}")
        return False

# ============================================================
# WIZARD PRINCIPAL V3 (fluxo identico ao V2, visual melhorado)
# ============================================================

def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    print_header()

    print(f"  {Fore.MAGENTA}{Style.BRIGHT}IMPORTANTE:{Style.RESET_ALL}")
    print(f"  {Fore.WHITE}- Todos os canais adicionados terao upload automatico ATIVADO")
    print(f"  {Fore.WHITE}- Sistema fara 1 upload por dia apos coleta diaria")
    print(f"  {Fore.WHITE}- Canais monetizados tem prioridade no processamento\n")

    # ============================================================
    # PARTE 1: DADOS DO CANAL
    # ============================================================
    print_section(1, 4, "DADOS DO CANAL")

    # Channel ID
    while True:
        channel_id = prompt("Channel ID (UCxxxxxxxxx)")
        if not channel_id:
            print_error("Channel ID e obrigatorio!")
            continue
        if not validar_channel_id(channel_id):
            continue
        print_processing("Verificando duplicatas")
        if canal_existe(channel_id):
            print_error(f"Canal {channel_id} ja existe no banco!")
            continue
        print_ok(f"Channel ID valido: {channel_id}")
        break

    # Channel Name
    while True:
        channel_name = prompt("Nome do canal")
        if not channel_name:
            print_error("Nome do canal e obrigatorio!")
            continue
        print_ok(f"Nome salvo: {channel_name}")
        break

    # Busca opcoes
    print_processing("Carregando opcoes")
    linguas_disponiveis = buscar_linguas_disponiveis()
    subnichos_disponiveis = buscar_subnichos_disponiveis()

    # Lingua
    print(f"\n  {Fore.CYAN}{Style.BRIGHT}Idiomas disponiveis:{Style.RESET_ALL}")
    for i, lang in enumerate(linguas_disponiveis):
        codigo = IDIOMAS_MAP[lang]
        print(f"    {Fore.WHITE}[{Fore.YELLOW}{i+1:2d}{Fore.WHITE}] {lang} ({codigo})")
    print(f"    {Fore.WHITE}[{Fore.YELLOW}{len(linguas_disponiveis)+1:2d}{Fore.WHITE}] Outro (digitar manualmente)")

    while True:
        try:
            escolha = prompt(f"Escolha a lingua (1-{len(linguas_disponiveis)+1})")
            escolha_num = int(escolha)

            if escolha_num < 1 or escolha_num > len(linguas_disponiveis) + 1:
                print_error(f"Digite um numero entre 1 e {len(linguas_disponiveis)+1}")
                continue

            if escolha_num == len(linguas_disponiveis) + 1:
                lingua = prompt("Digite o codigo ISO da lingua (ex: pt, es, fr)").lower()
                if not lingua:
                    print_error("Lingua e obrigatoria!")
                    continue
                if len(lingua) != 2:
                    print_error("Codigo ISO deve ter 2 letras (ex: pt, es, fr)")
                    continue
                print_warning(f"Lingua '{lingua}' nao existe na lista padrao, sera adicionada")
                confirma = prompt("Confirma? (s/n)").lower()
                if confirma != 's':
                    continue
            else:
                lingua_nome = linguas_disponiveis[escolha_num - 1]
                lingua = IDIOMAS_MAP[lingua_nome]
                print_ok(f"Lingua selecionada: {lingua_nome} (codigo: {lingua})")

            break
        except ValueError:
            print_error("Digite um numero valido!")
            continue

    # Subnicho
    print(f"\n  {Fore.CYAN}{Style.BRIGHT}Subnichos disponiveis:{Style.RESET_ALL}")
    for i, sub in enumerate(subnichos_disponiveis):
        print(f"    {Fore.WHITE}[{Fore.YELLOW}{i+1}{Fore.WHITE}] {sub}")
    print(f"    {Fore.WHITE}[{Fore.YELLOW}{len(subnichos_disponiveis)+1}{Fore.WHITE}] Outro (digitar manualmente)")

    while True:
        try:
            escolha = prompt(f"Escolha o subnicho (1-{len(subnichos_disponiveis)+1})")
            escolha_num = int(escolha)

            if escolha_num < 1 or escolha_num > len(subnichos_disponiveis) + 1:
                print_error(f"Digite um numero entre 1 e {len(subnichos_disponiveis)+1}")
                continue

            if escolha_num == len(subnichos_disponiveis) + 1:
                subnicho = prompt("Digite o subnicho manualmente (ex: terror)")
                if not subnicho:
                    print_error("Subnicho e obrigatorio!")
                    continue
                print_warning(f"Subnicho '{subnicho}' nao existe no banco, sera adicionado")
                confirma = prompt("Confirma? (s/n)").lower()
                if confirma != 's':
                    continue
            else:
                subnicho = subnichos_disponiveis[escolha_num - 1]
                print_ok(f"Subnicho selecionado: {subnicho}")

            break
        except ValueError:
            print_error("Digite um numero valido!")
            continue

    # Monetizacao
    print(f"\n  {Fore.CYAN}{Style.BRIGHT}MONETIZACAO{Style.RESET_ALL}")
    while True:
        monetizado = prompt("Este canal e monetizado? (s/n)").lower()
        if monetizado not in ['s', 'n']:
            print_error("Digite 's' para sim ou 'n' para nao")
            continue
        is_monetized = (monetizado == 's')
        status = f"{Fore.GREEN}SIM" if is_monetized else f"{Fore.RED}NAO"
        print_ok(f"Monetizado: {status}{Style.RESET_ALL}")
        break

    # Playlist ID (opcional)
    while True:
        playlist_id = prompt("Playlist ID (opcional, Enter para pular)")
        if not playlist_id:
            break
        if not validar_playlist_id(playlist_id):
            continue
        print_ok(f"Playlist ID: {playlist_id}")
        break

    # Spreadsheet ID
    print(f"\n  {Fore.CYAN}{Style.BRIGHT}PLANILHA DO GOOGLE SHEETS (OBRIGATORIO){Style.RESET_ALL}")
    print(f"  {Fore.WHITE}Cole a URL completa da planilha ou apenas o ID")
    print(f"  {Fore.WHITE}Exemplo: https://docs.google.com/spreadsheets/d/1234.../edit")
    while True:
        spreadsheet_input = prompt("URL ou ID da planilha")
        if not spreadsheet_input:
            print_error("Planilha e obrigatoria para upload automatico!")
            continue

        if spreadsheet_input.startswith('http'):
            spreadsheet_id = extrair_spreadsheet_id_da_url(spreadsheet_input)
            if not spreadsheet_id:
                print_error("Nao foi possivel extrair o ID da URL fornecida!")
                continue
        else:
            spreadsheet_id = spreadsheet_input

        if not validar_spreadsheet_id(spreadsheet_id):
            print_error("ID da planilha invalido!")
            continue

        print_ok(f"Formato do ID valido: {spreadsheet_id[:20]}...")

        print_processing("Verificando acesso a planilha")
        if not verificar_acesso_planilha(spreadsheet_id):
            print_error("Nao foi possivel acessar a planilha!")
            continue

        break

    # ============================================================
    # PARTE 2: CREDENCIAIS GOOGLE CLOUD (OAUTH)
    # ============================================================
    print_section(2, 4, "CREDENCIAIS DO PROJETO GOOGLE CLOUD")

    print(f"  {Fore.MAGENTA}{Style.BRIGHT}IMPORTANTE:{Style.RESET_ALL} Cada canal deve ter seu proprio projeto Google Cloud!")
    print(f"  {Fore.WHITE}Criado no navegador do proxy (AdsPower, VPS, etc)\n")

    # Client ID
    while True:
        client_id = prompt("Client ID")
        if not client_id:
            print_error("Client ID e obrigatorio!")
            continue
        if not validar_client_id(client_id):
            continue
        print_ok("Client ID valido!")
        break

    # Client Secret
    while True:
        client_secret = prompt("Client Secret")
        if not client_secret:
            print_error("Client Secret e obrigatorio!")
            continue
        if not validar_client_secret(client_secret):
            continue
        print_ok("Client Secret valido!")
        break

    print_ok("Credenciais validadas!")

    # ============================================================
    # PARTE 3: AUTORIZACAO OAUTH
    # ============================================================
    print_section(3, 4, "AUTORIZACAO OAUTH")

    print(f"  {Fore.MAGENTA}{Style.BRIGHT}IMPORTANTE:{Style.RESET_ALL}")
    print(f"  {Fore.WHITE}- Abra a URL no NAVEGADOR DO PROXY (conta Google do canal)")
    print(f"  {Fore.WHITE}- Autorize o acesso")
    print(f"  {Fore.WHITE}- Google vai redirecionar para http://localhost:8080")
    print(f"  {Fore.WHITE}- Copie a URL COMPLETA do redirect\n")

    # Gera URL OAuth
    oauth_url = gerar_url_oauth(channel_id, client_id)
    print(f"  {Fore.CYAN}{Style.BRIGHT}URL de autorizacao:{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}{'─' * 68}")
    print(f"  {Fore.WHITE}{oauth_url}")
    print(f"  {Fore.CYAN}{'─' * 68}")

    print(f"\n  {Fore.WHITE}Apos autorizar, cole aqui a URL COMPLETA do redirect")
    print(f"  {Fore.WHITE}(deve comecar com http://localhost:8080/?code=...)")

    while True:
        redirect_url = prompt("URL de redirect")
        if not redirect_url:
            print_error("URL e obrigatoria!")
            continue

        code = extrair_codigo_da_url(redirect_url)
        if not code:
            print_error("Codigo OAuth nao encontrado na URL!")
            print(f"  {Fore.WHITE}A URL deve conter ?code=4/xxxxx")
            continue

        if not validar_oauth_code(code):
            continue

        print_ok(f"Codigo extraido: {code[:20]}...")
        break

    # Troca codigo por tokens
    print_processing("Trocando codigo por tokens")
    tokens = trocar_codigo_por_tokens(code, client_id, client_secret)
    if not tokens:
        print_error("Falha ao obter tokens! Abortando...")
        input(f"\n  {Fore.YELLOW}Pressione ENTER para fechar...{Style.RESET_ALL}")
        return

    # Valida token
    print_processing("Validando token com YouTube API")
    if not validar_token(tokens['access_token']):
        print_warning("Token pode estar invalido!")
        confirma = prompt("Continuar mesmo assim? (s/n)").lower()
        if confirma != 's':
            print_warning("Abortado pelo usuario.")
            input(f"\n  {Fore.YELLOW}Pressione ENTER para fechar...{Style.RESET_ALL}")
            return

    # ============================================================
    # PARTE 4: SALVAR TUDO NO BANCO (ATOMICAMENTE)
    # ============================================================
    print_section(4, 4, "SALVANDO DADOS NO BANCO")

    print_processing("Salvando configuracao completa do canal")

    save_success = True
    canal_saved = False
    creds_saved = False
    tokens_saved = False

    try:
        # 1. Adicionar canal ao banco
        print(f"\n  {Fore.WHITE}[1/3] Salvando canal...")
        if adicionar_canal_v2(
            channel_id=channel_id,
            channel_name=channel_name,
            lingua=lingua,
            subnicho=subnicho,
            spreadsheet_id=spreadsheet_id,
            is_monetized=is_monetized,
            playlist_id=playlist_id if playlist_id else None
        ):
            print(f"    {Fore.GREEN}{Style.BRIGHT}v{Style.RESET_ALL} {Fore.WHITE}Canal salvo: {channel_name}")
            canal_saved = True
        else:
            print(f"    {Fore.RED}{Style.BRIGHT}x{Style.RESET_ALL} {Fore.RED}Erro ao salvar canal!")
            save_success = False

        if save_success:
            # 2. Salvar credenciais OAuth
            print(f"\n  {Fore.WHITE}[2/3] Salvando credenciais...")
            if salvar_credenciais_canal(channel_id, client_id, client_secret):
                print(f"    {Fore.GREEN}{Style.BRIGHT}v{Style.RESET_ALL} {Fore.WHITE}Credenciais salvas")
                creds_saved = True
            else:
                print(f"    {Fore.RED}{Style.BRIGHT}x{Style.RESET_ALL} {Fore.RED}Erro ao salvar credenciais!")
                save_success = False

        if save_success:
            # 3. Salvar tokens OAuth
            print(f"\n  {Fore.WHITE}[3/3] Salvando tokens de acesso...")
            if salvar_tokens(
                channel_id,
                tokens['access_token'],
                tokens['refresh_token'],
                tokens['expires_in']
            ):
                print(f"    {Fore.GREEN}{Style.BRIGHT}v{Style.RESET_ALL} {Fore.WHITE}Tokens salvos e validos")
                tokens_saved = True
            else:
                print(f"    {Fore.RED}{Style.BRIGHT}x{Style.RESET_ALL} {Fore.RED}Erro ao salvar tokens!")
                save_success = False

    except Exception as e:
        print_error(f"Falha ao salvar: {e}")
        save_success = False

    # Verificar resultado final
    if not save_success:
        print(f"\n{Fore.RED}{'=' * 70}")
        print(f"  {Fore.RED}{Style.BRIGHT}ERRO AO CONFIGURAR CANAL!{Style.RESET_ALL}")
        print(f"{Fore.RED}{'=' * 70}")
        print(f"\n  {Fore.WHITE}Alguns dados podem nao ter sido salvos corretamente.")
        print(f"  {Fore.WHITE}Verifique o erro acima e tente novamente.")
        input(f"\n  {Fore.YELLOW}Pressione ENTER para fechar...{Style.RESET_ALL}")
        return

    # ============================================================
    # RESUMO FINAL
    # ============================================================
    print(f"\n{Fore.GREEN}{'=' * 70}")
    print(f"  {Fore.GREEN}{Style.BRIGHT}CANAL CONFIGURADO COM SUCESSO!{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{'=' * 70}")

    print(f"\n  {Fore.GREEN}{Style.BRIGHT}DETALHES DO CANAL SALVO:{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}{'─' * 50}")
    print(f"  {Fore.WHITE}  Canal:            {Fore.YELLOW}{channel_name}")
    print(f"  {Fore.WHITE}  Channel ID:       {Fore.YELLOW}{channel_id}")
    print(f"  {Fore.WHITE}  Lingua:           {Fore.YELLOW}{lingua}")
    print(f"  {Fore.WHITE}  Subnicho:         {Fore.YELLOW}{subnicho}")
    print(f"  {Fore.WHITE}  Monetizado:       {Fore.YELLOW}{'SIM' if is_monetized else 'NAO'}")
    print(f"  {Fore.WHITE}  Upload automatico:{Fore.YELLOW} ATIVADO")
    print(f"  {Fore.WHITE}  Planilha:         {Fore.YELLOW}{spreadsheet_id[:20]}...")

    if playlist_id:
        print(f"  {Fore.WHITE}  Playlist:         {Fore.YELLOW}{playlist_id}")

    print(f"\n  {Fore.CYAN}{Style.BRIGHT}PROXIMOS PASSOS:{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}{'─' * 50}")
    print(f"  {Fore.WHITE}  1. Configure a planilha com os videos (coluna J = 'done')")
    print(f"  {Fore.WHITE}  2. O sistema fara 1 upload por dia automaticamente")
    print(f"  {Fore.WHITE}  3. Acompanhe pelo dashboard em localhost:5006")

    print(f"\n{Fore.GREEN}{'=' * 70}{Style.RESET_ALL}")
    input(f"\n  {Fore.GREEN}Pressione ENTER para fechar...{Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n  {Fore.YELLOW}Operacao cancelada pelo usuario.{Style.RESET_ALL}")
        input(f"\n  {Fore.YELLOW}Pressione ENTER para fechar...{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n\n  {Fore.RED}{Style.BRIGHT}ERRO INESPERADO: {e}{Style.RESET_ALL}")
        input(f"\n  {Fore.YELLOW}Pressione ENTER para fechar...{Style.RESET_ALL}")

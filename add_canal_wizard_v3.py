# -*- coding: utf-8 -*-
"""
WIZARD v3 - Adicionar Canal com Upload Automático
Visual profissional com cores e formatação aprimorada
"""

import os
import re
import json
import requests
from datetime import datetime, timedelta, timezone
from supabase import create_client
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs
from colorama import init, Fore, Back, Style

# Inicializa colorama para Windows
init(autoreset=True)

# Carrega variáveis de ambiente
load_dotenv()

# Conecta Supabase (usa SERVICE_ROLE_KEY para bypass RLS)
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
)

# ============================================================================
# FUNÇÕES DE FORMATAÇÃO VISUAL
# ============================================================================

def clear_screen():
    """Limpa a tela do terminal"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Imprime o cabeçalho principal do wizard"""
    print(f"\n{Fore.CYAN}{'=' * 70}")
    print(f"{Fore.CYAN}|{' ' * 13}{Fore.YELLOW}{Style.BRIGHT}WIZARD v3 - ADICIONAR CANAL YOUTUBE{Style.RESET_ALL}{' ' * 13}{Fore.CYAN}|")
    print(f"{Fore.CYAN}|{' ' * 13}{Fore.WHITE}Sistema de Upload Automatico Profissional{' ' * 14}{Fore.CYAN}|")
    print(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}\n")

def print_section(number, total, title, emoji=""):
    """Imprime cabeçalho de seção"""
    print(f"\n{Fore.CYAN}{'-' * 60}")
    print(f"{Fore.CYAN}{emoji} {Style.BRIGHT}ETAPA {number}/{total} - {title}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'-' * 60}{Style.RESET_ALL}\n")

def print_error(message):
    """Imprime mensagem de erro formatada"""
    print(f"{Fore.RED}{Style.BRIGHT}[X] ERRO: {Style.RESET_ALL}{Fore.RED}{message}{Style.RESET_ALL}")

def print_success(message):
    """Imprime mensagem de sucesso formatada"""
    print(f"{Fore.GREEN}{Style.BRIGHT}[OK] {message}{Style.RESET_ALL}")

def print_warning(message):
    """Imprime mensagem de aviso formatada"""
    print(f"{Fore.YELLOW}{Style.BRIGHT}[!] AVISO: {Style.RESET_ALL}{Fore.YELLOW}{message}{Style.RESET_ALL}")

def print_info(message):
    """Imprime mensagem informativa"""
    print(f"{Fore.CYAN}[i] {message}{Style.RESET_ALL}")

def print_processing(message):
    """Imprime mensagem de processamento"""
    print(f"{Fore.MAGENTA}[...] {message}...{Style.RESET_ALL}")

def print_prompt(message):
    """Retorna prompt formatado para input"""
    return f"{Fore.YELLOW}> {message}: {Style.RESET_ALL}"

def print_box(title, items):
    """Imprime uma caixa com título e items"""
    max_width = max(len(title), max(len(str(item)) for item in items if item)) + 4

    print(f"\n{Fore.CYAN}+{'-' * max_width}+")
    print(f"{Fore.CYAN}| {Fore.YELLOW}{Style.BRIGHT}{title}{Style.RESET_ALL}{' ' * (max_width - len(title) - 2)}{Fore.CYAN}|")
    print(f"{Fore.CYAN}+{'-' * max_width}+")

    for item in items:
        if item:
            item_str = str(item)
            padding = max_width - len(item_str) - 2
            print(f"{Fore.CYAN}| {Fore.WHITE}{item_str}{' ' * padding}{Fore.CYAN}|")

    print(f"{Fore.CYAN}+{'-' * max_width}+{Style.RESET_ALL}")

def print_final_summary(canal_data):
    """Imprime resumo final profissional"""
    print(f"\n{Fore.GREEN}{'=' * 70}")
    print(f"{Fore.GREEN}{' ' * 15}{Style.BRIGHT}CANAL CONFIGURADO COM SUCESSO!{Style.RESET_ALL}{' ' * 15}")
    print(f"{Fore.GREEN}{'=' * 70}")

    # Dados do canal
    print(f"\n{Fore.GREEN}{Style.BRIGHT}DETALHES DO CANAL:{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{'-' * 70}")

    items = [
        ("Canal", canal_data.get('channel_name', 'N/A')),
        ("ID", canal_data.get('channel_id', 'N/A')),
        ("Lingua", f"{canal_data.get('lingua_nome', 'N/A')} ({canal_data.get('lingua', 'N/A')})"),
        ("Subnicho", canal_data.get('subnicho', 'N/A')),
        ("Monetizado", "SIM" if canal_data.get('is_monetized') else "NAO"),
        ("Upload Auto", "ATIVADO"),
        ("Planilha", f"{canal_data.get('spreadsheet_id', 'N/A')[:20]}...")
    ]

    for label, value in items:
        print(f"{Fore.WHITE}  {label:15}: {Fore.YELLOW}{value}{Style.RESET_ALL}")

    print(f"\n{Fore.CYAN}{Style.BRIGHT}PROXIMOS PASSOS:{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'-' * 70}")
    print(f"{Fore.WHITE}  * Configure videos na planilha (coluna J = 'done')")
    print(f"{Fore.WHITE}  * Sistema fara 1 upload/dia automaticamente")
    print(f"{Fore.WHITE}  * Acompanhe pelo dashboard em localhost:5002")
    print(f"{Fore.GREEN}{'=' * 70}{Style.RESET_ALL}\n")

# ============================================================================
# FUNÇÕES AUXILIARES DO WIZARD
# ============================================================================

def verificar_canal_existe(channel_id):
    """Verifica se canal já existe no banco"""
    try:
        print_processing("Verificando duplicatas")

        result = supabase.table('yt_channels')\
            .select('channel_id, channel_name')\
            .eq('channel_id', channel_id)\
            .execute()

        if result.data:
            canal = result.data[0]
            print_error(f"Canal já existe no banco!")
            print(f"   {Fore.WHITE}Nome: {canal['channel_name']}")
            print(f"   {Fore.WHITE}ID: {canal['channel_id']}")
            return True
        else:
            print_success("Canal não existe - pode adicionar!")
            return False
    except Exception as e:
        print_error(f"Falha ao verificar: {e}")
        return None

def obter_linguas_disponiveis():
    """Retorna lista de línguas disponíveis"""
    return [
        ("de", "Alemao"),
        ("ar", "Arabe"),
        ("ko", "Coreano"),
        ("es", "Espanhol"),
        ("fr", "Frances"),
        ("hi", "Hindi"),
        ("en", "Ingles"),
        ("it", "Italiano"),
        ("ja", "Japones"),
        ("pt", "Portugues"),
        ("ru", "Russo"),
        ("tr", "Turco"),
        ("zh", "Chines")
    ]

def obter_subnichos_reais():
    """Retorna apenas os subnichos reais dos nossos canais"""
    return [
        "Terror",
        "Monetizados",
        "Desmonetizados",
        "Relatos de Guerra",
        "Historias Sombrias",
        "Mistérios"
    ]

def validar_channel_id(channel_id):
    """Valida formato do Channel ID"""
    pattern = r'^UC[a-zA-Z0-9_-]{22}$'

    if not re.match(pattern, channel_id):
        print_error("Channel ID inválido!")
        print(f"   {Fore.WHITE}Formato esperado: UCxxxxxxxxxxxxxxxxxx (24 caracteres)")
        print(f"   {Fore.WHITE}Exemplo: UCQkTVF_9ipsZx5URt1FfGLw")
        return False

    return True

def validar_client_id(client_id):
    """Valida formato do Client ID do Google"""
    pattern = r'^\d+-[a-z0-9]+\.apps\.googleusercontent\.com$'

    if not re.match(pattern, client_id):
        print_error("Client ID inválido!")
        print(f"   {Fore.WHITE}Formato esperado: XXXXX-YYYY.apps.googleusercontent.com")
        return False

    return True

def verificar_acesso_planilha(spreadsheet_id):
    """Verifica se consegue acessar a planilha (teste básico)"""
    try:
        print_processing("Verificando acesso à planilha")

        # Teste básico - verifica se é um ID válido
        if len(spreadsheet_id) < 20:
            print_error("ID da planilha muito curto!")
            return False

        print_success("ID da planilha válido!")
        return True
    except Exception as e:
        print_error(f"Erro ao verificar planilha: {e}")
        return False

def fazer_oauth(client_id, client_secret, channel_id):
    """Realiza o fluxo OAuth do Google"""
    try:
        # URLs do OAuth
        auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        token_url = "https://oauth2.googleapis.com/token"

        # Parâmetros da autorização
        redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
        scope = " ".join([
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube",  # Necessário para gerenciar playlists
            "https://www.googleapis.com/auth/spreadsheets"
        ])

        # Monta URL de autorização
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": scope,
            "access_type": "offline",
            "prompt": "consent"
        }

        auth_full_url = f"{auth_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"

        print_info("Abrindo navegador para autorizacao...")
        print(f"\n{Fore.CYAN}URL: {Fore.BLUE}{auth_full_url[:80]}...{Style.RESET_ALL}\n")

        # Abre navegador
        import webbrowser
        webbrowser.open(auth_full_url)

        print_box("INSTRUCOES", [
            "1. Faca login com a conta do canal",
            "2. Autorize o acesso solicitado",
            "3. Copie o codigo de autorizacao",
            "4. Cole abaixo e pressione ENTER"
        ])

        # Recebe código
        auth_code = input(print_prompt("Codigo de autorizacao")).strip()

        if not auth_code:
            print_error("Codigo nao pode estar vazio!")
            return None

        print_processing("Trocando codigo por tokens")

        # Troca código por tokens
        token_data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": auth_code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }

        response = requests.post(token_url, data=token_data)

        if response.status_code != 200:
            print_error(f"Falha ao obter tokens: {response.text}")
            return None

        tokens = response.json()

        # Calcula expiração
        expiry = datetime.now(timezone.utc) + timedelta(seconds=tokens.get('expires_in', 3600))

        print_success("Tokens obtidos com sucesso!")
        print(f"   {Fore.WHITE}Expira em: {expiry.strftime('%Y-%m-%d %H:%M')}")

        return {
            "access_token": tokens.get("access_token"),
            "refresh_token": tokens.get("refresh_token"),
            "token_expiry": expiry.isoformat()
        }

    except Exception as e:
        print_error(f"Erro no OAuth: {e}")
        return None

def salvar_credenciais_canal(channel_id, client_id, client_secret):
    """Salva credenciais do canal no Supabase"""
    try:
        print_processing("Salvando credenciais")

        result = supabase.table('yt_channel_credentials')\
            .insert({
                "channel_id": channel_id,
                "client_id": client_id,
                "client_secret": client_secret
            })\
            .execute()

        if result.data:
            print_success("Credenciais salvas!")
            return True
        else:
            print_error("Credenciais não foram salvas")
            return False
    except Exception as e:
        print_error(f"Erro ao salvar credenciais: {e}")
        return False

def salvar_tokens(channel_id, tokens):
    """Salva tokens OAuth no Supabase"""
    try:
        print_processing("Salvando tokens OAuth")

        result = supabase.table('yt_oauth_tokens')\
            .insert({
                "channel_id": channel_id,
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
                "token_expiry": tokens["token_expiry"]
            })\
            .execute()

        if result.data:
            print_success("Tokens salvos!")
            return True
        else:
            print_error("Tokens não foram salvos")
            return False
    except Exception as e:
        print_error(f"Erro ao salvar tokens: {e}")
        return False

# ============================================================================
# FUNÇÃO PRINCIPAL DO WIZARD
# ============================================================================

def main():
    """Função principal do wizard"""
    clear_screen()
    print_header()

    print(f"{Fore.MAGENTA}{Style.BRIGHT}IMPORTANTE:{Style.RESET_ALL}")
    print(f"  {Fore.WHITE}* Todos os canais terao upload automatico ATIVADO")
    print(f"  {Fore.WHITE}* Sistema fara 1 upload por dia apos coleta diaria")
    print(f"  {Fore.WHITE}* Canais monetizados tem prioridade no processamento\n")

    # Dados que serão coletados
    canal_data = {}

    while True:
        try:
            # ====================================================================
            # PARTE 1: DADOS DO CANAL
            # ====================================================================
            print_section(1, 4, "DADOS DO CANAL", "[DADOS]")

            # Channel ID
            while True:
                channel_id = input(print_prompt("Channel ID (UCxxxxxxxxx)")).strip()

                if not channel_id:
                    print_error("Channel ID é obrigatório!")
                    continue

                if not validar_channel_id(channel_id):
                    continue

                # Verifica duplicata
                existe = verificar_canal_existe(channel_id)
                if existe:
                    print_warning("Canal já existe! Não pode adicionar duplicado.")
                    print("\n" + "=" * 60)
                    input(f"\n{Fore.YELLOW}Pressione ENTER para sair...{Style.RESET_ALL}")
                    return

                canal_data['channel_id'] = channel_id
                print_success(f"Channel ID válido: {channel_id}")
                break

            # Nome do canal
            while True:
                channel_name = input(print_prompt("Nome do canal")).strip()
                if not channel_name:
                    print_error("Nome é obrigatório!")
                    continue
                canal_data['channel_name'] = channel_name
                print_success(f"Nome salvo: {channel_name}")
                break

            # Língua
            print_processing("Carregando opcoes de idioma")
            linguas_disponiveis = obter_linguas_disponiveis()

            print_box("IDIOMAS DISPONIVEIS", [
                f"[{i+1}] {nome}" for i, (_, nome) in enumerate(linguas_disponiveis)
            ] + [f"[{len(linguas_disponiveis)+1}] Outro (digitar manualmente)"])

            while True:
                escolha = input(print_prompt(f"Escolha o idioma (1-{len(linguas_disponiveis)+1})")).strip()

                if not escolha.isdigit():
                    print_error("Digite apenas o número da opção!")
                    continue

                escolha_num = int(escolha)

                if escolha_num < 1 or escolha_num > len(linguas_disponiveis) + 1:
                    print_error(f"Opção inválida! Escolha entre 1 e {len(linguas_disponiveis)+1}")
                    continue

                if escolha_num <= len(linguas_disponiveis):
                    lingua_codigo, lingua_nome = linguas_disponiveis[escolha_num - 1]
                    canal_data['lingua'] = lingua_codigo
                    canal_data['lingua_nome'] = lingua_nome.split()[1]  # Remove emoji
                    print_success(f"Idioma selecionado: {lingua_nome}")
                else:
                    lingua_custom = input(print_prompt("Digite o código do idioma (ex: pt, en, es)")).strip().lower()
                    if len(lingua_custom) != 2:
                        print_error("Código deve ter 2 letras!")
                        continue
                    canal_data['lingua'] = lingua_custom
                    canal_data['lingua_nome'] = lingua_custom.upper()
                    print_success(f"Idioma personalizado: {lingua_custom}")
                break

            # Subnicho
            print_processing("Carregando subnichos")
            subnichos = obter_subnichos_reais()

            print_box("SUBNICHOS DISPONIVEIS", [
                f"[{i+1}] {subnicho}" for i, subnicho in enumerate(subnichos)
            ] + [f"[{len(subnichos)+1}] Outro (digitar manualmente)"])

            while True:
                escolha = input(print_prompt(f"Escolha o subnicho (1-{len(subnichos)+1})")).strip()

                if not escolha.isdigit():
                    print_error("Digite apenas o número da opção!")
                    continue

                escolha_num = int(escolha)

                if escolha_num < 1 or escolha_num > len(subnichos) + 1:
                    print_error(f"Opção inválida! Escolha entre 1 e {len(subnichos)+1}")
                    continue

                if escolha_num <= len(subnichos):
                    canal_data['subnicho'] = subnichos[escolha_num - 1]
                    print_success(f"Subnicho selecionado: {subnichos[escolha_num - 1]}")
                else:
                    subnicho_custom = input(print_prompt("Digite o nome do subnicho")).strip()
                    if not subnicho_custom:
                        print_error("Subnicho não pode estar vazio!")
                        continue
                    canal_data['subnicho'] = subnicho_custom
                    print_success(f"Subnicho personalizado: {subnicho_custom}")
                break

            # Monetizado
            while True:
                monetizado = input(print_prompt("Canal monetizado? (s/n)")).strip().lower()
                if monetizado not in ['s', 'n']:
                    print_error("Digite 's' para sim ou 'n' para não!")
                    continue
                canal_data['is_monetized'] = (monetizado == 's')
                status_text = "Monetizado" if monetizado == 's' else "Nao monetizado"
                print_success(f"Status: {status_text}")
                break

            # Playlist ID
            while True:
                playlist_id = input(print_prompt("ID da Playlist do YouTube (PLxxxxxx ou UUxxxxxx)")).strip()
                if not playlist_id:
                    print_error("Playlist ID é obrigatório!")
                    continue
                if not playlist_id.startswith(('PL', 'UU', 'LL', 'FL')):
                    print_warning("Playlist ID geralmente começa com PL, UU, LL ou FL")
                canal_data['playlist_id'] = playlist_id
                print_success(f"Playlist ID: {playlist_id}")
                break

            # Spreadsheet ID
            while True:
                spreadsheet_id = input(print_prompt("ID da Planilha Google Sheets")).strip()
                if not spreadsheet_id:
                    print_error("Spreadsheet ID é obrigatório!")
                    continue

                if not verificar_acesso_planilha(spreadsheet_id):
                    retry = input(print_prompt("Tentar outro ID? (s/n)")).strip().lower()
                    if retry != 's':
                        break
                    continue

                canal_data['spreadsheet_id'] = spreadsheet_id
                print_success(f"Planilha configurada!")
                break

            # ====================================================================
            # PARTE 2: CONFIGURACAO OAUTH
            # ====================================================================
            print_section(2, 4, "CONFIGURACAO OAUTH", "[OAUTH]")

            print_box("INSTRUCOES GOOGLE CLOUD", [
                "1. Acesse: console.cloud.google.com",
                "2. Crie ou selecione um projeto",
                "3. Ative YouTube Data API v3",
                "4. Crie credenciais OAuth 2.0",
                "5. Tipo: Aplicativo para desktop",
                "6. Copie Client ID e Client Secret"
            ])

            # Client ID
            while True:
                client_id = input(print_prompt("Client ID")).strip()
                if not client_id:
                    print_error("Client ID é obrigatório!")
                    continue
                if not validar_client_id(client_id):
                    continue
                canal_data['client_id'] = client_id
                print_success("Client ID válido!")
                break

            # Client Secret
            while True:
                client_secret = input(print_prompt("Client Secret")).strip()
                if not client_secret:
                    print_error("Client Secret é obrigatório!")
                    continue
                if not client_secret.startswith('GOCSPX-'):
                    print_warning("Client Secret geralmente começa com GOCSPX-")
                canal_data['client_secret'] = client_secret
                print_success("Client Secret salvo!")
                break

            # ====================================================================
            # PARTE 3: AUTORIZACAO
            # ====================================================================
            print_section(3, 4, "AUTORIZACAO GOOGLE", "[AUTH]")

            tokens = fazer_oauth(
                canal_data['client_id'],
                canal_data['client_secret'],
                canal_data['channel_id']
            )

            if not tokens:
                print_error("Falha na autorização!")
                retry = input(print_prompt("Tentar novamente? (s/n)")).strip().lower()
                if retry == 's':
                    continue
                else:
                    print_warning("Saindo sem salvar...")
                    input(f"\n{Fore.YELLOW}Pressione ENTER para sair...{Style.RESET_ALL}")
                    return

            canal_data['tokens'] = tokens

            # ====================================================================
            # PARTE 4: SALVAMENTO FINAL
            # ====================================================================
            print_section(4, 4, "SALVAMENTO NO BANCO", "[SAVE]")

            print_processing("Salvando todas as informações")

            # 1. Salva canal principal
            try:
                result = supabase.table('yt_channels')\
                    .insert({
                        "channel_id": canal_data['channel_id'],
                        "channel_name": canal_data['channel_name'],
                        "lingua": canal_data['lingua'],
                        "subnicho": canal_data['subnicho'],
                        "is_monetized": canal_data['is_monetized'],
                        "upload_automatico": True,
                        "playlist_id": canal_data['playlist_id'],
                        "spreadsheet_id": canal_data['spreadsheet_id']
                    })\
                    .execute()

                if not result.data:
                    raise Exception("Canal não foi salvo")

                print_success(f"Canal salvo: {canal_data['channel_name']}")

            except Exception as e:
                print_error(f"Erro ao salvar canal: {e}")
                print_warning("Abortando processo...")
                input(f"\n{Fore.YELLOW}Pressione ENTER para sair...{Style.RESET_ALL}")
                return

            # 2. Salva credenciais
            if not salvar_credenciais_canal(
                canal_data['channel_id'],
                canal_data['client_id'],
                canal_data['client_secret']
            ):
                # Rollback - deleta canal
                print_warning("Fazendo rollback...")
                supabase.table('yt_channels').delete().eq('channel_id', canal_data['channel_id']).execute()
                print_error("Processo abortado! Canal não foi salvo.")
                input(f"\n{Fore.YELLOW}Pressione ENTER para sair...{Style.RESET_ALL}")
                return

            # 3. Salva tokens
            if not salvar_tokens(canal_data['channel_id'], canal_data['tokens']):
                # Rollback - deleta canal e credenciais
                print_warning("Fazendo rollback...")
                supabase.table('yt_channel_credentials').delete().eq('channel_id', canal_data['channel_id']).execute()
                supabase.table('yt_channels').delete().eq('channel_id', canal_data['channel_id']).execute()
                print_error("Processo abortado! Canal não foi salvo.")
                input(f"\n{Fore.YELLOW}Pressione ENTER para sair...{Style.RESET_ALL}")
                return

            # ====================================================================
            # SUCESSO TOTAL!
            # ====================================================================
            print_final_summary(canal_data)

            print_info("Para verificar: python verificar_canal_salvo.py")
            print_info("Para upload manual: python daily_uploader.py")
            print_info("Dashboard: python dashboard_daily_uploads.py")

            # Fim com sucesso
            break

        except KeyboardInterrupt:
            print(f"\n\n{Fore.YELLOW}Processo interrompido pelo usuário!{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW}Pressione ENTER para sair...{Style.RESET_ALL}")
            return
        except Exception as e:
            print_error(f"Erro inesperado: {e}")
            input(f"\n{Fore.YELLOW}Pressione ENTER para sair...{Style.RESET_ALL}")
            return

    input(f"\n{Fore.GREEN}Pressione ENTER para sair...{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
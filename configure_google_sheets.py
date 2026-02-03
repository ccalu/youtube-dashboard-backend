# -*- coding: utf-8 -*-
"""
Script para configurar credenciais do Google Sheets
Necessário para o sistema de upload automático funcionar
"""

import os
import json
from dotenv import load_dotenv, set_key
from colorama import init, Fore, Style

# Inicializa colorama
init(autoreset=True)

# Carrega variáveis existentes
load_dotenv()

def print_header():
    print(f"\n{Fore.CYAN}{'=' * 70}")
    print(f"{Fore.CYAN}     CONFIGURAR CREDENCIAIS DO GOOGLE SHEETS")
    print(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}\n")

def main():
    print_header()

    print(f"{Fore.YELLOW}IMPORTANTE:{Style.RESET_ALL}")
    print("Para o upload automatico funcionar, precisamos configurar")
    print("as credenciais do Google Sheets (conta de servico).\n")

    print(f"{Fore.CYAN}PASSOS NECESSARIOS:{Style.RESET_ALL}")
    print("1. Acesse: https://console.cloud.google.com")
    print("2. Selecione seu projeto (ou crie um novo)")
    print("3. Ative as APIs:")
    print("   - Google Sheets API")
    print("   - Google Drive API")
    print("4. Va em 'Credenciais' > 'Criar credenciais'")
    print("5. Escolha: 'Conta de servico'")
    print("6. Preencha os dados e crie")
    print("7. Na conta criada, clique em 'Chaves'")
    print("8. Adicione chave > JSON > Baixar")
    print("9. Abra o arquivo JSON baixado\n")

    print(f"{Fore.YELLOW}Agora vamos configurar:{Style.RESET_ALL}")
    print("Cole o conteudo COMPLETO do arquivo JSON aqui.")
    print("Termine com uma linha vazia e pressione CTRL+Z + ENTER:\n")

    # Lê múltiplas linhas até EOF
    lines = []
    print(f"{Fore.GREEN}Cole o JSON aqui:{Style.RESET_ALL}")
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass

    json_content = '\n'.join(lines).strip()

    if not json_content:
        print(f"\n{Fore.RED}[ERRO] Nenhum conteudo fornecido!{Style.RESET_ALL}")
        return

    # Valida JSON
    try:
        credentials = json.loads(json_content)

        # Verifica campos essenciais
        required_fields = ['client_email', 'private_key', 'project_id']
        missing = [field for field in required_fields if field not in credentials]

        if missing:
            print(f"\n{Fore.RED}[ERRO] JSON invalido! Campos faltando: {', '.join(missing)}{Style.RESET_ALL}")
            return

        print(f"\n{Fore.GREEN}[OK] JSON valido!{Style.RESET_ALL}")
        print(f"  Projeto: {credentials['project_id']}")
        print(f"  Email: {credentials['client_email']}")

    except json.JSONDecodeError as e:
        print(f"\n{Fore.RED}[ERRO] JSON invalido: {e}{Style.RESET_ALL}")
        return

    # Salva no .env
    print(f"\n{Fore.YELLOW}Salvando credenciais...{Style.RESET_ALL}")

    # Escapa o JSON para salvar no .env (uma linha)
    json_escaped = json.dumps(credentials, separators=(',', ':'))

    # Salva no .env
    env_file = '.env'
    set_key(env_file, 'GOOGLE_SHEETS_CREDENTIALS_2', json_escaped)

    print(f"{Fore.GREEN}[OK] Credenciais salvas no .env!{Style.RESET_ALL}")

    # Instruções finais
    print(f"\n{Fore.CYAN}{'=' * 70}")
    print(f"PROXIMOS PASSOS:")
    print(f"{'=' * 70}{Style.RESET_ALL}")

    print(f"\n{Fore.YELLOW}1. COMPARTILHE A PLANILHA:{Style.RESET_ALL}")
    print(f"   Abra sua planilha do Google Sheets")
    print(f"   Clique em 'Compartilhar'")
    print(f"   Adicione este email: {Fore.GREEN}{credentials['client_email']}{Style.RESET_ALL}")
    print(f"   De permissao de 'Editor'\n")

    print(f"{Fore.YELLOW}2. CONFIGURE VIDEOS NA PLANILHA:{Style.RESET_ALL}")
    print("   Coluna J: Status (marque como 'done')")
    print("   Coluna K: Titulo do video")
    print("   Coluna L: Descricao")
    print("   Coluna M: Tags (separadas por virgula)")
    print("   Coluna O: Path do video no Google Drive\n")

    print(f"{Fore.YELLOW}3. TESTE O UPLOAD:{Style.RESET_ALL}")
    print("   python test_upload_simulation.py")
    print("   ou")
    print("   python daily_uploader.py\n")

    print(f"{Fore.GREEN}Configuracao concluida com sucesso!{Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Processo cancelado!{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}[ERRO] {e}{Style.RESET_ALL}")

    input(f"\n{Fore.YELLOW}Pressione ENTER para sair...{Style.RESET_ALL}")
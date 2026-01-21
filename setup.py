#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SETUP.PY - Configuração Inicial Universal v3.0
Dashboard de Mineração YouTube
Funciona em Windows, Mac e Linux sem limitações
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

# Detectar sistema operacional
SISTEMA = platform.system()
MACHINE_NAME = platform.node()
USER_NAME = os.getenv('USERNAME') if SISTEMA == 'Windows' else os.getenv('USER')

# Cores (funciona em todos os sistemas)
class Colors:
    if SISTEMA == 'Windows':
        # Ativar cores no Windows
        os.system('color')

    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'

def run_command(cmd, capture=True):
    """Executa comando e retorna output"""
    try:
        if capture:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            return result.stdout.strip(), result.returncode
        else:
            result = subprocess.run(cmd, shell=True)
            return None, result.returncode
    except Exception as e:
        return str(e), 1

def print_header():
    """Imprime cabeçalho"""
    os.system('cls' if SISTEMA == 'Windows' else 'clear')
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}      SETUP - Dashboard de Mineração YouTube{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")

    print(f"{Colors.CYAN}Sistema:{Colors.RESET}  {SISTEMA}")
    print(f"{Colors.CYAN}Máquina:{Colors.RESET}  {MACHINE_NAME}")
    print(f"{Colors.CYAN}Usuário:{Colors.RESET}  {USER_NAME}")
    print(f"\n{'-'*40}\n")

def step1_check_git():
    """Passo 1: Verificar Git"""
    print(f"{Colors.YELLOW}[1/5]{Colors.RESET} Verificando Git...")

    # Verificar se Git está instalado
    output, code = run_command("git --version")
    if code != 0:
        print(f"   {Colors.RED}[ERRO] Git não está instalado!{Colors.RESET}")
        print(f"   Instale em: https://git-scm.com/downloads")
        sys.exit(1)
    else:
        print(f"   {Colors.GREEN}[OK]{Colors.RESET} {output}")

    # Verificar se já é repositório
    if os.path.exists('.git'):
        print(f"   {Colors.GREEN}[OK]{Colors.RESET} Já é um repositório Git")

        # Verificar remote
        output, code = run_command("git remote get-url origin")
        if code == 0:
            print(f"   {Colors.GREEN}[OK]{Colors.RESET} Remote configurado: {output}")
            return True

    return False

def step2_init_repo():
    """Passo 2: Inicializar repositório"""
    print(f"\n{Colors.YELLOW}[2/5]{Colors.RESET} Inicializando repositório...")

    if not os.path.exists('.git'):
        output, code = run_command("git init")
        if code != 0:
            print(f"   {Colors.RED}[ERRO] Falha ao inicializar Git!{Colors.RESET}")
            sys.exit(1)
        print(f"   {Colors.GREEN}[OK]{Colors.RESET} Repositório inicializado")

    # Adicionar remote
    output, code = run_command("git remote get-url origin")
    if code != 0:
        print(f"   {Colors.CYAN}[i]{Colors.RESET} Adicionando remote origin...")
        cmd = "git remote add origin https://github.com/ccalu/youtube-dashboard-backend.git"
        output, code = run_command(cmd)
        if code == 0:
            print(f"   {Colors.GREEN}[OK]{Colors.RESET} Remote adicionado")
    else:
        print(f"   {Colors.GREEN}[OK]{Colors.RESET} Remote já configurado")

def step3_config_git():
    """Passo 3: Configurar Git"""
    print(f"\n{Colors.YELLOW}[3/5]{Colors.RESET} Configurando Git...")

    # Verificar configuração atual
    name, _ = run_command("git config user.name")
    email, _ = run_command("git config user.email")

    if name and email:
        print(f"   {Colors.GREEN}[OK]{Colors.RESET} Nome: {name}")
        print(f"   {Colors.GREEN}[OK]{Colors.RESET} Email: {email}")

        print(f"\n   Manter configuração atual? (S/n): ", end='')
        try:
            resposta = input().strip().lower()
            if resposta == 'n':
                name = None
                email = None
        except:
            pass

    if not name:
        print(f"   Digite seu nome: ", end='')
        try:
            name = input().strip()
            if name:
                run_command(f'git config user.name "{name}"')
                print(f"   {Colors.GREEN}[OK]{Colors.RESET} Nome configurado: {name}")
        except:
            name = "User"
            run_command(f'git config user.name "{name}"')

    if not email:
        print(f"   Digite seu email: ", end='')
        try:
            email = input().strip()
            if email:
                run_command(f'git config user.email "{email}"')
                print(f"   {Colors.GREEN}[OK]{Colors.RESET} Email configurado: {email}")
        except:
            email = "user@example.com"
            run_command(f'git config user.email "{email}"')

def step4_create_shortcuts():
    """Passo 4: Criar atalhos"""
    print(f"\n{Colors.YELLOW}[4/5]{Colors.RESET} Criando atalhos...")

    if SISTEMA == 'Windows':
        # Criar sync.cmd
        sync_cmd = Path('sync.cmd')
        sync_cmd.write_text('@echo off\npython sync.py %*\n')
        print(f"   {Colors.GREEN}[OK]{Colors.RESET} Criado: sync.cmd → python sync.py")

        # Criar setup.cmd
        setup_cmd = Path('setup.cmd')
        setup_cmd.write_text('@echo off\npython setup.py %*\n')
        print(f"   {Colors.GREEN}[OK]{Colors.RESET} Criado: setup.cmd → python setup.py")

        print(f"\n   {Colors.CYAN}[i]{Colors.RESET} No Windows, use:")
        print(f"       {Colors.BOLD}sync{Colors.RESET}   - Para sincronizar")
        print(f"       {Colors.BOLD}setup{Colors.RESET}  - Para configurar")

    else:  # Mac/Linux
        # Detectar shell
        shell = os.environ.get('SHELL', '/bin/bash')

        # Arquivos de configuração do shell
        rc_files = []
        home = Path.home()

        if 'zsh' in shell:
            rc_files.append(home / '.zshrc')
        if 'bash' in shell:
            rc_files.append(home / '.bashrc')

        # Adicionar aliases
        for rc_file in rc_files:
            if rc_file.exists():
                content = rc_file.read_text()

                # Adicionar alias sync se não existir
                if 'alias sync=' not in content:
                    with open(rc_file, 'a') as f:
                        f.write(f'\n# Dashboard YouTube aliases\n')
                        f.write(f'alias sync="python {os.getcwd()}/sync.py"\n')
                        f.write(f'alias setup="python {os.getcwd()}/setup.py"\n')

                    print(f"   {Colors.GREEN}[OK]{Colors.RESET} Aliases adicionados em {rc_file.name}")

        # Tornar executáveis
        os.chmod('sync.py', 0o755)
        os.chmod('setup.py', 0o755)
        print(f"   {Colors.GREEN}[OK]{Colors.RESET} Arquivos tornados executáveis")

        print(f"\n   {Colors.CYAN}[i]{Colors.RESET} No {SISTEMA}, use:")
        print(f"       {Colors.BOLD}sync{Colors.RESET}   - Para sincronizar")
        print(f"       {Colors.BOLD}setup{Colors.RESET}  - Para configurar")
        print(f"\n   {Colors.YELLOW}[!]{Colors.RESET} Recarregue o terminal ou execute:")
        print(f"       source ~/.bashrc  (ou ~/.zshrc)")

def step5_test_sync():
    """Passo 5: Testar sincronização"""
    print(f"\n{Colors.YELLOW}[5/5]{Colors.RESET} Testando sincronização...")

    # Fazer um pull inicial
    print(f"   {Colors.CYAN}[i]{Colors.RESET} Baixando arquivos do GitHub...")
    output, code = run_command("git pull origin main")

    if code == 0 or "Already up to date" in str(output):
        print(f"   {Colors.GREEN}[OK]{Colors.RESET} Sincronização funcionando!")
    else:
        print(f"   {Colors.YELLOW}[!]{Colors.RESET} Primeira sincronização pode precisar de:")
        print(f"       git pull origin main --allow-unrelated-histories")

def show_summary():
    """Mostra resumo final"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.GREEN}       SETUP COMPLETO COM SUCESSO!{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")

    print(f"{Colors.CYAN}✓ Git configurado{Colors.RESET}")
    print(f"{Colors.CYAN}✓ Repositório inicializado{Colors.RESET}")
    print(f"{Colors.CYAN}✓ Remote GitHub conectado{Colors.RESET}")
    print(f"{Colors.CYAN}✓ Atalhos criados{Colors.RESET}")
    print(f"{Colors.CYAN}✓ Pronto para usar!{Colors.RESET}\n")

    print(f"{Colors.YELLOW}PRÓXIMOS PASSOS:{Colors.RESET}")
    print(f"1. Use {Colors.BOLD}sync{Colors.RESET} (ou {Colors.BOLD}python sync.py{Colors.RESET}) para sincronizar")
    print(f"2. Faça isso sempre que quiser enviar/receber mudanças")
    print(f"3. O sync funciona em qualquer PC configurado\n")

    print(f"{Colors.GREEN}Projeto configurado com sucesso!{Colors.RESET}\n")

def main():
    """Função principal"""
    try:
        print_header()

        # Verificar se já está configurado
        already_configured = step1_check_git()

        if already_configured:
            print(f"\n{Colors.GREEN}[OK] Sistema já está configurado!{Colors.RESET}")
            print(f"\nDeseja reconfigurar? (s/N): ", end='')
            try:
                resposta = input().strip().lower()
                if resposta != 's':
                    print(f"\n{Colors.CYAN}Use 'sync' ou 'python sync.py' para sincronizar{Colors.RESET}")
                    sys.exit(0)
            except:
                sys.exit(0)

        step2_init_repo()
        step3_config_git()
        step4_create_shortcuts()
        step5_test_sync()
        show_summary()

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}[!] Setup interrompido pelo usuário{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}[ERRO] {str(e)}{Colors.RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()
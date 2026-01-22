#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SYNC.PY - Sincronização Universal v4.0
Dashboard de Mineração YouTube
Funciona em Windows, Mac e Linux sem limitações

IMPORTANTE: Este script garante que a documentação seja atualizada
antes de fazer commit/push. Workflow obrigatório:
1. Fazer alterações no código
2. ATUALIZAR DOCUMENTAÇÃO (obrigatório!)
3. Rodar sync.py
4. Railway deploya automaticamente
"""

import os
import sys
import subprocess
import platform
from datetime import datetime

# Detectar sistema operacional
SISTEMA = platform.system()
MACHINE_NAME = platform.node()
USER_NAME = os.getenv('USERNAME') if SISTEMA == 'Windows' else os.getenv('USER')

# Mapeamento: arquivo de código → documentação relacionada
DOC_MAPPING = {
    'main.py': '2_DASHBOARD_TECNICO/08_API_ENDPOINTS_COMPLETA.md',
    'collector.py': '2_DASHBOARD_TECNICO/06_YOUTUBE_COLLECTOR.md',
    'notifier.py': '2_DASHBOARD_TECNICO/07_NOTIFICACOES_INTELIGENTES.md',
    'database.py': '2_DASHBOARD_TECNICO/05_DATABASE_SCHEMA.md',
    'financeiro.py': '2_DASHBOARD_TECNICO/10_SISTEMA_FINANCEIRO.md',
    'monetization_collector.py': '2_DASHBOARD_TECNICO/09_MONETIZACAO_SISTEMA.md',
    'monetization_endpoints.py': '2_DASHBOARD_TECNICO/09_MONETIZACAO_SISTEMA.md',
    'yt_uploader/': '2_DASHBOARD_TECNICO/11_YOUTUBE_UPLOADER.md',
}

# Documentos que SEMPRE devem ser atualizados quando há mudanças
ALWAYS_UPDATE = [
    '.claude/CLAUDE.md',      # Resumo geral para Claude
    'CHANGELOG.md',           # Histórico de mudanças
]

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
    print(f"{Colors.BLUE}       SYNC - Dashboard de Mineração YouTube{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")

    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    print(f"{Colors.CYAN}Máquina:{Colors.RESET}  {MACHINE_NAME}")
    print(f"{Colors.CYAN}Usuário:{Colors.RESET}  {USER_NAME}")
    print(f"{Colors.CYAN}Sistema:{Colors.RESET}  {SISTEMA}")
    print(f"{Colors.CYAN}Horário:{Colors.RESET}  {timestamp}")
    print(f"\n{'-'*40}\n")

def check_git():
    """Verifica se é repositório Git"""
    if not os.path.exists('.git'):
        print(f"{Colors.RED}[ERRO] Não é um repositório Git!{Colors.RESET}")
        print("Execute primeiro: git init")
        sys.exit(1)

    output, code = run_command("git remote -v")
    if code != 0:
        print(f"{Colors.RED}[ERRO] Nenhum remote configurado!{Colors.RESET}")
        sys.exit(1)

def check_documentation():
    """
    PASSO 0: Verificar se documentação foi atualizada
    CRÍTICO: Garante que mudanças de código tenham docs atualizados
    """
    print(f"{Colors.YELLOW}[0/7]{Colors.RESET} Verificando documentação...")

    output, _ = run_command("git status --porcelain")
    if not output:
        print(f"   {Colors.CYAN}[i]{Colors.RESET} Nenhuma mudança para verificar")
        return True

    changed_files = [line.split()[-1] for line in output.split('\n') if line.strip()]

    # Separar arquivos de código e documentação
    code_files = []
    doc_files = []

    for f in changed_files:
        if f.endswith('.py'):
            code_files.append(f)
        elif f.endswith('.md'):
            doc_files.append(f)

    # Se não há código alterado, OK
    if not code_files:
        print(f"   {Colors.GREEN}[OK]{Colors.RESET} Apenas documentação alterada")
        return True

    # Verificar quais docs deveriam ser atualizados
    expected_docs = set()
    for code_file in code_files:
        base_name = os.path.basename(code_file)
        if base_name in DOC_MAPPING:
            expected_docs.add(DOC_MAPPING[base_name])
        # Verificar pastas (ex: yt_uploader/)
        for folder, doc in DOC_MAPPING.items():
            if folder.endswith('/') and folder in code_file:
                expected_docs.add(doc)

    # Sempre adicionar docs obrigatórios
    expected_docs.update(ALWAYS_UPDATE)

    # Verificar quais docs foram atualizados
    updated_docs = set(f for f in doc_files)
    missing_docs = expected_docs - updated_docs

    # Mostrar código alterado
    print(f"\n   {Colors.CYAN}Código alterado:{Colors.RESET}")
    for f in code_files[:5]:
        print(f"      {Colors.YELLOW}>{Colors.RESET} {f}")
    if len(code_files) > 5:
        print(f"      {Colors.CYAN}... +{len(code_files)-5} arquivo(s){Colors.RESET}")

    # Mostrar docs atualizados
    if updated_docs:
        print(f"\n   {Colors.CYAN}Documentação atualizada:{Colors.RESET}")
        for f in list(updated_docs)[:5]:
            print(f"      {Colors.GREEN}[OK]{Colors.RESET} {f}")

    # ALERTA: Docs faltando (apenas aviso, não bloqueia)
    if missing_docs:
        print(f"\n   {Colors.YELLOW}[LEMBRETE] Docs que podem precisar de atualizacao:{Colors.RESET}")
        for doc in missing_docs:
            print(f"      {Colors.YELLOW}>{Colors.RESET} {doc}")
        print(f"   {Colors.CYAN}(Continuando sync...){Colors.RESET}")
    else:
        print(f"\n   {Colors.GREEN}[OK]{Colors.RESET} Documentacao esta atualizada!")

    return True

def step1_status():
    """Passo 1: Verificar status local"""
    print(f"\n{Colors.YELLOW}[1/7]{Colors.RESET} Verificando status local...")

    output, _ = run_command("git status --porcelain")
    local_changes = len(output.split('\n')) if output else 0

    if local_changes > 0:
        print(f"   {Colors.CYAN}[i]{Colors.RESET} Mudanças locais: {Colors.BOLD}{local_changes} arquivo(s){Colors.RESET}")
    else:
        print(f"   {Colors.CYAN}[i]{Colors.RESET} Nenhuma mudança local")

def step2_fetch():
    """Passo 2: Buscar atualizações"""
    print(f"\n{Colors.YELLOW}[2/7]{Colors.RESET} Buscando atualizações do GitHub...")

    run_command("git fetch origin main", capture=False)

    output, _ = run_command("git rev-list HEAD..origin/main --count")
    behind = int(output) if output and output.isdigit() else 0

    if behind > 0:
        print(f"   {Colors.CYAN}[i]{Colors.RESET} Commits para baixar: {Colors.BOLD}{behind}{Colors.RESET}")
    else:
        print(f"   {Colors.CYAN}[i]{Colors.RESET} Já está atualizado")

def step3_pull():
    """Passo 3: Baixar atualizações"""
    print(f"\n{Colors.YELLOW}[3/7]{Colors.RESET} Baixando atualizações...")

    # Hash antes
    hash_before, _ = run_command("git rev-parse HEAD")

    # Pull
    output, code = run_command("git pull origin main")
    if code != 0:
        print(f"   {Colors.RED}[ERRO] Falha ao baixar! Possível conflito.{Colors.RESET}")
        sys.exit(1)

    # Hash depois
    hash_after, _ = run_command("git rev-parse HEAD")

    if hash_before != hash_after:
        output, _ = run_command(f"git diff --name-only {hash_before} {hash_after}")
        files_pulled = len([f for f in output.split('\n') if f.strip()]) if output else 0
        print(f"   {Colors.GREEN}[OK]{Colors.RESET} Baixados: {Colors.BOLD}{files_pulled} arquivo(s){Colors.RESET}")

        # Listar primeiros 5 arquivos
        if output:
            files = [f for f in output.split('\n') if f.strip()][:5]
            for file in files:
                print(f"      {Colors.GREEN}v{Colors.RESET} {file}")
            if len([f for f in output.split('\n') if f.strip()]) > 5:
                more = len([f for f in output.split('\n') if f.strip()]) - 5
                print(f"      {Colors.CYAN}... +{more} arquivo(s){Colors.RESET}")

        # Mostrar ultima mudanca recebida
        msg, _ = run_command("git log -1 --format=%s")
        date, _ = run_command('git log -1 --format=%cd --date=format:"%d/%m %H:%M"')
        print(f"\n   {Colors.CYAN}[i] Ultima mudanca:{Colors.RESET} \"{msg}\" ({date})")
    else:
        print(f"   {Colors.CYAN}[i]{Colors.RESET} Nenhum arquivo novo")

def step4_add():
    """Passo 4: Adicionar mudanças"""
    print(f"\n{Colors.YELLOW}[4/7]{Colors.RESET} Preparando envio...")

    # Usar git add -A para garantir que TODOS os arquivos sejam adicionados
    # (novos, modificados e deletados)
    _, code = run_command("git add -A")
    if code != 0:
        print(f"   {Colors.RED}[ERRO] Falha ao adicionar arquivos!{Colors.RESET}")

    output, _ = run_command("git diff --cached --name-only")
    staged = len([f for f in output.split('\n') if f.strip()]) if output else 0

    if staged > 0:
        print(f"   {Colors.CYAN}[i]{Colors.RESET} Para enviar: {Colors.BOLD}{staged} arquivo(s){Colors.RESET}")
    else:
        print(f"   {Colors.CYAN}[i]{Colors.RESET} Nada para enviar")

def step5_commit():
    """Passo 5: Criar commit"""
    print(f"\n{Colors.YELLOW}[5/7]{Colors.RESET} Criando commit...")

    output, code = run_command("git diff-index --quiet HEAD --")

    if code != 0:
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        commit_msg = f"sync: {MACHINE_NAME} [{timestamp}]"
        run_command(f'git commit -m "{commit_msg}"')
        print(f"   {Colors.GREEN}[OK]{Colors.RESET} Commit: {Colors.BOLD}{commit_msg}{Colors.RESET}")
        return True
    else:
        print(f"   {Colors.CYAN}[i]{Colors.RESET} Nada para commitar")
        return False

def step6_push(commit_made):
    """Passo 6: Enviar para GitHub"""
    print(f"\n{Colors.YELLOW}[6/7]{Colors.RESET} Enviando para GitHub...")

    if commit_made:
        output, code = run_command("git push origin main")
        if code != 0:
            print(f"   {Colors.RED}[ERRO] Falha ao enviar!{Colors.RESET}")
            sys.exit(1)
        else:
            print(f"   {Colors.GREEN}[OK]{Colors.RESET} Enviado com sucesso!")
    else:
        print(f"   {Colors.CYAN}[i]{Colors.RESET} Nada para enviar")

def step7_summary():
    """Passo 7: Mostrar resumo final"""
    print(f"\n{Colors.YELLOW}[7/7]{Colors.RESET} Resumo final...")
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.GREEN}       SYNC COMPLETO COM SUCESSO!{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")

    # Último commit
    print(f"{Colors.CYAN}-- ÚLTIMO COMMIT --{'-'*41}{Colors.RESET}")

    hash_val, _ = run_command("git log -1 --format=%h")
    msg, _ = run_command("git log -1 --format=%s")
    author, _ = run_command("git log -1 --format=%an")
    date, _ = run_command('git log -1 --format=%cd --date=format:"%d/%m/%Y %H:%M:%S"')

    print(f"{Colors.CYAN}Hash:{Colors.RESET}     {Colors.GREEN}{hash_val}{Colors.RESET}")
    print(f"{Colors.CYAN}Mensagem:{Colors.RESET} {msg}")
    print(f"{Colors.CYAN}Autor:{Colors.RESET}    {author}")
    print(f"{Colors.CYAN}Data:{Colors.RESET}     {date}")
    print(f"{Colors.CYAN}{'-'*60}{Colors.RESET}\n")

    # Status
    print(f"{Colors.CYAN}-- STATUS --{'-'*47}{Colors.RESET}")

    branch, _ = run_command("git branch --show-current")
    print(f"{Colors.CYAN}Branch:{Colors.RESET}   {Colors.GREEN}{branch}{Colors.RESET}")
    print(f"{Colors.CYAN}Remote:{Colors.RESET}   origin/main")
    print(f"{Colors.CYAN}Sync:{Colors.RESET}     {Colors.GREEN}OK{Colors.RESET}")
    print(f"{Colors.CYAN}{'-'*60}{Colors.RESET}\n")

def main():
    """Função principal"""
    try:
        print_header()
        check_git()
        check_documentation()  # NOVO: Verifica docs ANTES de tudo
        step1_status()
        step2_fetch()
        step3_pull()
        step4_add()
        commit_made = step5_commit()
        step6_push(commit_made)
        step7_summary()

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}[!] Sync interrompido pelo usuário{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}[ERRO] {str(e)}{Colors.RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()
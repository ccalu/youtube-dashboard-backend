#!/bin/bash
# ========================================
# SYNC.SH - Sincronizacao Universal v2.0
# Dashboard de Mineracao YouTube
# ========================================
# Com logs detalhados e verificacao de erros
# ========================================

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Variavel para rastrear erros
ERRORS=0

# Funcao para mostrar erro
show_error() {
    echo ""
    echo -e "${RED}========================================"
    echo -e " [ERRO] $1"
    echo -e "========================================${NC}"
    echo ""
    ERRORS=$((ERRORS + 1))
}

# Funcao para mostrar sucesso
show_success() {
    echo -e "   ${GREEN}[OK]${NC} $1"
}

# Funcao para mostrar info
show_info() {
    echo -e "   ${CYAN}[i]${NC} $1"
}

# Funcao para mostrar warning
show_warning() {
    echo -e "   ${YELLOW}[!]${NC} $1"
}

# Header
clear
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}     ${BOLD}SYNC - Dashboard de Mineracao YouTube${NC}     ${BLUE}║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Detectar nome da maquina
MACHINE_NAME=$(hostname | cut -d'.' -f1)
TIMESTAMP=$(date "+%d/%m/%Y %H:%M:%S")
USER_NAME=$(whoami)

echo -e "${CYAN}Maquina:${NC}  $MACHINE_NAME"
echo -e "${CYAN}Usuario:${NC}  $USER_NAME"
echo -e "${CYAN}Horario:${NC}  $TIMESTAMP"
echo ""
echo -e "${YELLOW}────────────────────────────────────────${NC}"

# Verificar se eh repositorio Git
if [ ! -d ".git" ] && [ ! -d "../.git" ]; then
    show_error "Nao eh um repositorio Git! Execute ./setup.sh primeiro."
    exit 1
fi

# Verificar se tem remote configurado
if ! git remote -v > /dev/null 2>&1; then
    show_error "Nenhum remote configurado!"
    exit 1
fi

# ========================================
# PASSO 1: Status local
# ========================================
echo ""
echo -e "${YELLOW}[1/6]${NC} Verificando status local..."
LOCAL_CHANGES=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
if [ "$LOCAL_CHANGES" -gt "0" ]; then
    show_info "Mudancas locais: ${BOLD}$LOCAL_CHANGES arquivo(s)${NC}"
else
    show_info "Nenhuma mudanca local"
fi

# ========================================
# PASSO 2: Buscar atualizacoes
# ========================================
echo ""
echo -e "${YELLOW}[2/6]${NC} Buscando atualizacoes do GitHub..."
git fetch origin main 2>/dev/null

BEHIND=$(git rev-list HEAD..origin/main --count 2>/dev/null || echo "0")
if [ "$BEHIND" -gt "0" ]; then
    show_info "Commits para baixar: ${BOLD}$BEHIND${NC}"
else
    show_info "Ja esta atualizado"
fi

# ========================================
# PASSO 3: Pull (baixar atualizacoes)
# ========================================
echo ""
echo -e "${YELLOW}[3/6]${NC} Baixando atualizacoes..."

HASH_BEFORE=$(git rev-parse HEAD 2>/dev/null)
PULL_OUTPUT=$(git pull origin main 2>&1)
PULL_STATUS=$?

if [ $PULL_STATUS -ne 0 ]; then
    show_error "Falha ao baixar! Possivel conflito."
    echo "$PULL_OUTPUT"
    exit 1
fi

HASH_AFTER=$(git rev-parse HEAD 2>/dev/null)

if [ "$HASH_BEFORE" != "$HASH_AFTER" ]; then
    FILES_PULLED=$(git diff --name-only $HASH_BEFORE $HASH_AFTER 2>/dev/null | wc -l | tr -d ' ')
    show_success "Baixados: ${BOLD}$FILES_PULLED arquivo(s)${NC}"

    # Listar arquivos baixados (max 5)
    echo ""
    git diff --name-only $HASH_BEFORE $HASH_AFTER 2>/dev/null | head -5 | while read file; do
        echo -e "      ${GREEN}↓${NC} $file"
    done

    MORE=$((FILES_PULLED - 5))
    if [ "$MORE" -gt "0" ]; then
        echo -e "      ${CYAN}... +$MORE arquivo(s)${NC}"
    fi
else
    show_info "Nenhum arquivo novo"
fi

# ========================================
# PASSO 4: Adicionar mudancas locais
# ========================================
echo ""
echo -e "${YELLOW}[4/6]${NC} Preparando envio..."
git add -A 2>/dev/null

STAGED=$(git diff --cached --name-only 2>/dev/null | wc -l | tr -d ' ')
if [ "$STAGED" -gt "0" ]; then
    show_info "Para enviar: ${BOLD}$STAGED arquivo(s)${NC}"
else
    show_info "Nada para enviar"
fi

# ========================================
# PASSO 5: Commit
# ========================================
echo ""
echo -e "${YELLOW}[5/6]${NC} Criando commit..."

COMMIT_MADE="false"
if ! git diff-index --quiet HEAD -- 2>/dev/null; then
    COMMIT_MSG="sync: $MACHINE_NAME [$TIMESTAMP]"
    git commit -m "$COMMIT_MSG" > /dev/null 2>&1
    show_success "Commit: ${BOLD}$COMMIT_MSG${NC}"
    COMMIT_MADE="true"
else
    show_info "Nada para commitar"
fi

# ========================================
# PASSO 6: Push
# ========================================
echo ""
echo -e "${YELLOW}[6/6]${NC} Enviando para GitHub..."

if [ "$COMMIT_MADE" = "true" ]; then
    PUSH_OUTPUT=$(git push origin main 2>&1)
    PUSH_STATUS=$?

    if [ $PUSH_STATUS -ne 0 ]; then
        show_error "Falha ao enviar!"
        echo "$PUSH_OUTPUT"
        ERRORS=$((ERRORS + 1))
    else
        show_success "Enviado com sucesso!"
    fi
else
    show_info "Nada para enviar"
fi

# ========================================
# LOG FINAL DETALHADO
# ========================================
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"

if [ "$ERRORS" -eq "0" ]; then
    echo -e "${BLUE}║${NC}         ${GREEN}${BOLD}SYNC COMPLETO COM SUCESSO!${NC}         ${BLUE}║${NC}"
else
    echo -e "${BLUE}║${NC}         ${RED}${BOLD}SYNC COMPLETO COM $ERRORS ERRO(S)${NC}         ${BLUE}║${NC}"
fi

echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Informacoes do ultimo commit
echo -e "${CYAN}┌─ ULTIMO COMMIT ─────────────────────────────────────────────┐${NC}"
LAST_HASH=$(git log -1 --format="%h")
LAST_MSG=$(git log -1 --format="%s")
LAST_AUTHOR=$(git log -1 --format="%an")
LAST_DATE=$(git log -1 --format="%cd" --date=format:"%d/%m/%Y %H:%M:%S")
LAST_MACHINE=$(echo "$LAST_MSG" | grep -oP '(?<=sync: )[^[]+' | tr -d ' ' || echo "$LAST_AUTHOR")

echo -e "${CYAN}│${NC} Hash:     ${GREEN}$LAST_HASH${NC}"
echo -e "${CYAN}│${NC} Mensagem: $LAST_MSG"
echo -e "${CYAN}│${NC} Autor:    $LAST_AUTHOR"
echo -e "${CYAN}│${NC} Data:     $LAST_DATE"
echo -e "${CYAN}└──────────────────────────────────────────────────────────────┘${NC}"
echo ""

# Status final
echo -e "${CYAN}┌─ STATUS ─────────────────────────────────────────────────────┐${NC}"
echo -e "${CYAN}│${NC} Branch:   ${GREEN}$(git branch --show-current)${NC}"
echo -e "${CYAN}│${NC} Remote:   origin/main"

if [ "$ERRORS" -eq "0" ]; then
    echo -e "${CYAN}│${NC} Erros:    ${GREEN}Nenhum${NC}"
    echo -e "${CYAN}│${NC} Sync:     ${GREEN}OK${NC}"
else
    echo -e "${CYAN}│${NC} Erros:    ${RED}$ERRORS${NC}"
    echo -e "${CYAN}│${NC} Sync:     ${YELLOW}Parcial${NC}"
fi

echo -e "${CYAN}└──────────────────────────────────────────────────────────────┘${NC}"
echo ""

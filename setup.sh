#!/bin/bash
# ========================================
# SETUP.SH - Configuracao Inicial
# Dashboard de Mineracao YouTube - Pasta Docs
# ========================================
#
# USO: Rode este arquivo APENAS NA PRIMEIRA VEZ
#      em um novo PC que recebeu a pasta docs/
#
# ========================================

echo ""
echo "========================================"
echo " SETUP - Dashboard de Mineracao YouTube"
echo "========================================"
echo ""

# Verificar se ja tem .git na pasta pai
if [ -d "../.git" ]; then
    echo "[OK] Repositorio git JA EXISTE na pasta pai!"
    echo "     Voce pode usar ./sync.sh diretamente."
    echo ""
    read -p "Pressione ENTER para sair..."
    exit 0
fi

# Verificar se ja tem .git aqui mesmo
if [ -d ".git" ]; then
    echo "[OK] Repositorio git JA EXISTE aqui!"
    echo "     Voce pode usar ./sync.sh diretamente."
    echo ""
    read -p "Pressione ENTER para sair..."
    exit 0
fi

echo "[1/5] Inicializando repositorio Git..."
if ! git init; then
    echo "[ERRO] Falha ao inicializar git!"
    read -p "Pressione ENTER para sair..."
    exit 1
fi

echo ""
echo "[2/5] Conectando ao GitHub..."
if ! git remote add origin https://github.com/ccalu/youtube-dashboard-backend.git; then
    echo "[ERRO] Falha ao adicionar remote!"
    read -p "Pressione ENTER para sair..."
    exit 1
fi

echo ""
echo "[3/5] Configurando sparse checkout (somente docs/)..."
git config core.sparseCheckout true
mkdir -p .git/info
echo "docs/*" > .git/info/sparse-checkout
if [ $? -ne 0 ]; then
    echo "[ERRO] Falha ao configurar sparse checkout!"
    read -p "Pressione ENTER para sair..."
    exit 1
fi

echo ""
echo "[4/5] Puxando arquivos do GitHub..."
if ! git pull origin main; then
    echo "[AVISO] Erro ao puxar arquivos!"
    echo "        Isso e normal na primeira vez."
    echo "        Verifique sua conexao e tente novamente."
    echo ""
    read -p "Pressione ENTER para sair..."
    exit 1
fi

echo ""
echo "[5/5] Configurando branch padrao..."
git branch -M main
git branch --set-upstream-to=origin/main main

echo ""
echo "========================================"
echo " [SUCESSO] Setup completo!"
echo "========================================"
echo ""
echo " Agora voce pode usar:"
echo " - ./sync.sh (sincronizar)"
echo ""
echo " A pasta docs/ esta pronta para uso!"
echo ""
echo "========================================"
echo ""
read -p "Pressione ENTER para sair..."

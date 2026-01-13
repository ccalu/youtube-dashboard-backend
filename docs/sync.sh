#!/bin/bash
# ========================================
# SYNC.SH - Sincronizacao Universal
# Dashboard de Mineracao YouTube
# ========================================
#
# USO: Rode este arquivo em QUALQUER Mac/Linux
#      - Puxa atualizacoes do GitHub
#      - Salva suas mudancas locais
#      - 100% automatico!
#
# ========================================

echo ""
echo "========================================"
echo " SYNC - Dashboard de Mineracao YouTube"
echo "========================================"
echo ""

# Verificar se estamos em um repositorio Git (deixa Git detectar automaticamente)
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "[ERRO] Nenhum repositorio Git detectado!"
    echo ""
    echo "Rode primeiro: ./setup.sh"
    echo ""
    read -p "Pressione ENTER para sair..."
    exit 1
fi

# Mostrar informacao da ultima sincronizacao
echo "[INFO] Ultima sincronizacao:"
git log -1 --pretty=format:"       %s%n       📅 %ad%n       🔗 %h - %ar%n"
echo ""

echo "[1/5] Verificando status local..."
git status --short

echo ""
echo "[2/5] Puxando atualizacoes do GitHub..."
if ! git pull origin main; then
    echo ""
    echo "[AVISO] Conflito detectado ou erro ao puxar!"
    echo "         Resolva conflitos manualmente e rode novamente."
    echo ""
    read -p "Pressione ENTER para sair..."
    exit 1
fi

echo ""
echo "[3/5] Adicionando mudancas locais..."
git add .

echo ""
echo "[4/5] Criando commit com suas mudancas..."
# Verifica se tem algo para commitar
if git diff-index --quiet HEAD --; then
    echo "         Nenhuma mudanca para commitar."
else
    TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
    git commit -m "sync: deu boa - Mac Casa [$TIMESTAMP]"
fi

echo ""
echo "[5/5] Enviando para GitHub..."
if ! git push origin main; then
    echo ""
    echo "[ERRO] Falha ao enviar para GitHub!"
    echo "        Verifique sua conexao e credenciais."
    echo ""
    read -p "Pressione ENTER para sair..."
    exit 1
fi

echo ""
echo "========================================"
echo " [SUCESSO] Sincronizacao completa!"
echo "========================================"
echo ""
echo " Docs estao atualizados:"
echo " - Local: Suas mudancas salvas"
echo " - GitHub: Versao mais recente"
echo " - Outros PCs: Rodem sync para atualizar"
echo ""
echo "========================================"
echo ""
read -p "Pressione ENTER para sair..."

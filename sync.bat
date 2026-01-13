@echo off
REM ========================================
REM SYNC.BAT - Sincronizacao Universal
REM Dashboard de Mineracao YouTube
REM ========================================
REM
REM USO: Rode este arquivo em QUALQUER PC
REM      - Puxa atualizacoes do GitHub
REM      - Salva suas mudancas locais
REM      - 100% automatico!
REM
REM ========================================

echo.
echo ========================================
echo  SYNC - Dashboard de Mineracao YouTube
echo ========================================
echo.

REM Verificar se eh repositorio Git
if not exist ".git\" (
    echo [ERRO] Este nao eh um repositorio Git!
    echo.
    echo Execute primeiro: git init
    echo                   git remote add origin [URL]
    echo.
    pause
    exit /b 1
)

REM Verificar se tem remote configurado
git remote -v >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Nenhum remote configurado!
    echo.
    echo Execute: git remote add origin [URL-DO-GITHUB]
    echo.
    pause
    exit /b 1
)

echo [1/5] Verificando status local...
git status --short

echo.
echo [2/5] Puxando atualizacoes do GitHub...
git pull origin main
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [AVISO] Conflito detectado ou erro ao puxar!
    echo         Resolva conflitos manualmente e rode novamente.
    echo.
    pause
    exit /b 1
)

echo.
echo [3/5] Adicionando mudancas locais...
git add docs/
git add README.md
git add sync.bat

echo.
echo [4/5] Criando commit com suas mudancas...
REM Verifica se tem algo para commitar
git diff-index --quiet HEAD --
if %ERRORLEVEL% EQU 0 (
    echo         Nenhuma mudanca para commitar.
) else (
    git commit -m "docs: Update documentation - %date% %time%"
)

echo.
echo [5/5] Enviando para GitHub...
git push origin main
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERRO] Falha ao enviar para GitHub!
    echo        Verifique sua conexao e credenciais.
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo  [SUCESSO] Sincronizacao completa!
echo ========================================
echo.
echo  Docs estao atualizados:
echo  - Local: Suas mudancas salvas
echo  - GitHub: Versao mais recente
echo  - Outros PCs: Rodem sync.bat para atualizar
echo.
echo ========================================
pause

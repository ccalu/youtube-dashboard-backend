@echo off
REM ========================================
REM SETUP.BAT - Configuracao Inicial
REM Dashboard de Mineracao YouTube - Pasta Docs
REM ========================================
REM
REM USO: Rode este arquivo APENAS NA PRIMEIRA VEZ
REM      em um novo PC que recebeu a pasta docs/
REM
REM ========================================

echo.
echo ========================================
echo  SETUP - Dashboard de Mineracao YouTube
echo ========================================
echo.

REM Verificar se ja tem .git na pasta pai
if exist "..\.git\" (
    echo [OK] Repositorio git JA EXISTE na pasta pai!
    echo      Voce pode usar sync.bat diretamente.
    echo.
    pause
    exit /b 0
)

REM Verificar se ja tem .git aqui mesmo
if exist ".git\" (
    echo [OK] Repositorio git JA EXISTE aqui!
    echo      Voce pode usar sync.bat diretamente.
    echo.
    pause
    exit /b 0
)

echo [1/5] Inicializando repositorio Git...
git init
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Falha ao inicializar git!
    pause
    exit /b 1
)

echo.
echo [2/5] Conectando ao GitHub...
git remote add origin https://github.com/ccalu/youtube-dashboard-backend.git
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Falha ao adicionar remote!
    pause
    exit /b 1
)

echo.
echo [3/5] Configurando sparse checkout (somente docs/)...
git config core.sparseCheckout true
echo docs/* > .git\info\sparse-checkout
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Falha ao configurar sparse checkout!
    pause
    exit /b 1
)

echo.
echo [4/5] Puxando arquivos do GitHub...
git pull origin main
if %ERRORLEVEL% NEQ 0 (
    echo [AVISO] Erro ao puxar arquivos!
    echo         Isso e normal na primeira vez.
    echo         Verifique sua conexao e tente novamente.
    echo.
    pause
    exit /b 1
)

echo.
echo [5/5] Configurando branch padrao...
git branch -M main
git branch --set-upstream-to=origin/main main

echo.
echo ========================================
echo  [SUCESSO] Setup completo!
echo ========================================
echo.
echo  Agora voce pode usar:
echo  - sync.bat (sincronizar)
echo.
echo  A pasta docs/ esta pronta para uso!
echo.
echo ========================================
pause

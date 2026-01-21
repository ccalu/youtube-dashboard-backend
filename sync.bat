@echo off
REM ========================================
REM SYNC.BAT - Sincronizacao Universal v2.0
REM Dashboard de Mineracao YouTube
REM ========================================
REM Com logs detalhados igual ao sync.sh
REM ========================================

setlocal enabledelayedexpansion

REM Limpar tela
cls

REM Header
echo.
echo ============================================================
echo                SYNC - Dashboard de Mineracao YouTube
echo ============================================================
echo.

REM Detectar informacoes da maquina
set MACHINE_NAME=%COMPUTERNAME%
set USER_NAME=%USERNAME%
set TIMESTAMP=%date% %time%

echo Maquina:  %MACHINE_NAME%
echo Usuario:  %USER_NAME%
echo Horario:  %TIMESTAMP%
echo.
echo ----------------------------------------

REM Verificar se eh repositorio Git
if not exist ".git\" (
    echo.
    echo ========================================
    echo  [ERRO] Nao eh um repositorio Git!
    echo ========================================
    echo.
    pause
    exit /b 1
)

REM Verificar se tem remote configurado
git remote -v >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Nenhum remote configurado!
    pause
    exit /b 1
)

REM ========================================
REM PASSO 1: Status local
REM ========================================
echo.
echo [1/6] Verificando status local...

REM Contar mudancas locais
for /f %%i in ('git status --porcelain 2^>nul ^| find /c /v ""') do set LOCAL_CHANGES=%%i

if %LOCAL_CHANGES% GTR 0 (
    echo    [i] Mudancas locais: %LOCAL_CHANGES% arquivo(s)
) else (
    echo    [i] Nenhuma mudanca local
)

REM ========================================
REM PASSO 2: Buscar atualizacoes
REM ========================================
echo.
echo [2/6] Buscando atualizacoes do GitHub...
git fetch origin main >nul 2>&1

REM Contar commits para baixar
for /f %%i in ('git rev-list HEAD..origin/main --count 2^>nul') do set BEHIND=%%i
if not defined BEHIND set BEHIND=0

if %BEHIND% GTR 0 (
    echo    [i] Commits para baixar: %BEHIND%
) else (
    echo    [i] Ja esta atualizado
)

REM ========================================
REM PASSO 3: Pull (baixar atualizacoes)
REM ========================================
echo.
echo [3/6] Baixando atualizacoes...

REM Salvar hash antes do pull
for /f %%i in ('git rev-parse HEAD 2^>nul') do set HASH_BEFORE=%%i

git pull origin main >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo    [ERRO] Falha ao baixar! Possivel conflito.
    pause
    exit /b 1
)

REM Salvar hash depois do pull
for /f %%i in ('git rev-parse HEAD 2^>nul') do set HASH_AFTER=%%i

if not "%HASH_BEFORE%"=="%HASH_AFTER%" (
    REM Contar arquivos baixados
    for /f %%i in ('git diff --name-only %HASH_BEFORE% %HASH_AFTER% 2^>nul ^| find /c /v ""') do set FILES_PULLED=%%i
    echo    [OK] Baixados: %FILES_PULLED% arquivo(s)

    REM Listar primeiros 5 arquivos
    echo.
    for /f "tokens=*" %%i in ('git diff --name-only %HASH_BEFORE% %HASH_AFTER% 2^>nul ^| head -5') do (
        echo       v %%i
    )
) else (
    echo    [i] Nenhum arquivo novo
)

REM ========================================
REM PASSO 4: Adicionar mudancas locais
REM ========================================
echo.
echo [4/6] Preparando envio...
git add . 2>nul

REM Contar arquivos para enviar
for /f %%i in ('git diff --cached --name-only 2^>nul ^| find /c /v ""') do set STAGED=%%i
if not defined STAGED set STAGED=0

if %STAGED% GTR 0 (
    echo    [i] Para enviar: %STAGED% arquivo(s)
) else (
    echo    [i] Nada para enviar
)

REM ========================================
REM PASSO 5: Commit
REM ========================================
echo.
echo [5/6] Criando commit...

set COMMIT_MADE=false
git diff-index --quiet HEAD -- 2>nul
if %ERRORLEVEL% NEQ 0 (
    set COMMIT_MSG=sync: %MACHINE_NAME% [%date% %time%]
    git commit -m "!COMMIT_MSG!" >nul 2>&1
    echo    [OK] Commit: !COMMIT_MSG!
    set COMMIT_MADE=true
) else (
    echo    [i] Nada para commitar
)

REM ========================================
REM PASSO 6: Push
REM ========================================
echo.
echo [6/6] Enviando para GitHub...

if "%COMMIT_MADE%"=="true" (
    git push origin main >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo    [ERRO] Falha ao enviar!
        pause
        exit /b 1
    ) else (
        echo    [OK] Enviado com sucesso!
    )
) else (
    echo    [i] Nada para enviar
)

REM ========================================
REM LOG FINAL DETALHADO
REM ========================================
echo.
echo ============================================================
echo                 SYNC COMPLETO COM SUCESSO!
echo ============================================================
echo.

REM Informacoes do ultimo commit
echo -- ULTIMO COMMIT -------------------------------------------
for /f "tokens=*" %%i in ('git log -1 --format="Hash: %%h"') do echo %%i
for /f "tokens=*" %%i in ('git log -1 --format="Mensagem: %%s"') do echo %%i
for /f "tokens=*" %%i in ('git log -1 --format="Autor: %%an"') do echo %%i
for /f "tokens=*" %%i in ('git log -1 --format="Data: %%cd" --date^=format:"%%d/%%m/%%Y %%H:%%M:%%S"') do echo %%i
echo ------------------------------------------------------------
echo.

REM Status final
echo -- STATUS --------------------------------------------------
for /f "tokens=*" %%i in ('git branch --show-current') do echo Branch: %%i
echo Remote: origin/main
echo Sync: OK
echo ------------------------------------------------------------
echo.
pause

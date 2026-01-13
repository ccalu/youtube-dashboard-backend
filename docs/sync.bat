@echo off
chcp 65001 >nul 2>&1
REM ========================================
REM SYNC.BAT - Sincronizacao Universal v2.1
REM Dashboard de Mineracao YouTube
REM ========================================
REM Com logs detalhados e verificacao de erros
REM Suporta mensagem personalizada: sync.bat "minha mensagem"
REM ========================================

setlocal enabledelayedexpansion

REM Capturar mensagem personalizada (se fornecida)
set "CUSTOM_MSG=%~1"

REM Variavel para rastrear erros
set ERRORS=0

cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║     SYNC - Dashboard de Mineracao YouTube                  ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Detectar nome da maquina
for /f "tokens=*" %%a in ('hostname') do set "MACHINE_NAME=%%a"
set "TIMESTAMP=%date% %time:~0,8%"
set "USER_NAME=%USERNAME%"

echo Maquina:  %MACHINE_NAME%
echo Usuario:  %USER_NAME%
echo Horario:  %TIMESTAMP%
if not "%CUSTOM_MSG%"=="" (
    echo Mensagem: %CUSTOM_MSG%
)
echo.
echo ────────────────────────────────────────

REM Verificar se eh repositorio Git
git rev-parse --git-dir >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================
    echo  [ERRO] Nao eh um repositorio Git!
    echo         Execute setup.bat primeiro.
    echo ========================================
    echo.
    set /a ERRORS+=1
    pause
    exit /b 1
)

REM ========================================
REM PASSO 1: Status local
REM ========================================
echo.
echo [1/6] Verificando status local...
for /f %%a in ('git status --porcelain 2^>nul ^| find /c /v ""') do set LOCAL_CHANGES=%%a
if %LOCAL_CHANGES% GTR 0 (
    echo    [i] Mudancas locais: %LOCAL_CHANGES% arquivo^(s^)
) else (
    echo    [i] Nenhuma mudanca local
)

REM ========================================
REM PASSO 2: Buscar atualizacoes
REM ========================================
echo.
echo [2/6] Buscando atualizacoes do GitHub...
git fetch origin main >nul 2>&1

for /f %%a in ('git rev-list HEAD..origin/main --count 2^>nul') do set BEHIND=%%a
if "%BEHIND%"=="" set BEHIND=0
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

for /f %%a in ('git rev-parse HEAD 2^>nul') do set HASH_BEFORE=%%a
git pull origin main >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================
    echo  [ERRO] Falha ao baixar! Possivel conflito.
    echo ========================================
    echo.
    set /a ERRORS+=1
    pause
    exit /b 1
)

for /f %%a in ('git rev-parse HEAD 2^>nul') do set HASH_AFTER=%%a

if not "%HASH_BEFORE%"=="%HASH_AFTER%" (
    echo    [OK] Arquivos baixados com sucesso!
) else (
    echo    [i] Nenhum arquivo novo
)

REM ========================================
REM PASSO 4: Adicionar mudancas locais
REM ========================================
echo.
echo [4/6] Preparando envio...
git add -A >nul 2>&1

for /f %%a in ('git diff --cached --name-only 2^>nul ^| find /c /v ""') do set STAGED=%%a
if %STAGED% GTR 0 (
    echo    [i] Para enviar: %STAGED% arquivo^(s^)
) else (
    echo    [i] Nada para enviar
)

REM ========================================
REM PASSO 5: Commit
REM ========================================
echo.
echo [5/6] Criando commit...

set COMMIT_MADE=false
git diff-index --quiet HEAD -- >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    if not "%CUSTOM_MSG%"=="" (
        set "COMMIT_MSG=%CUSTOM_MSG%"
    ) else (
        set "COMMIT_MSG=sync: %MACHINE_NAME% [%TIMESTAMP%]"
    )
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
        echo.
        echo ========================================
        echo  [ERRO] Falha ao enviar!
        echo ========================================
        echo.
        set /a ERRORS+=1
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
echo ╔════════════════════════════════════════════════════════════╗
if %ERRORS% EQU 0 (
    echo ║         SYNC COMPLETO COM SUCESSO!                         ║
) else (
    echo ║         SYNC COMPLETO COM %ERRORS% ERRO^(S^)                        ║
)
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Informacoes do ultimo commit
echo ┌─ ULTIMO COMMIT ─────────────────────────────────────────────┐
for /f "tokens=*" %%a in ('git log -1 --format^="%%h"') do echo │ Hash:     %%a
for /f "tokens=*" %%a in ('git log -1 --format^="%%s"') do echo │ Mensagem: %%a
for /f "tokens=*" %%a in ('git log -1 --format^="%%an"') do echo │ Autor:    %%a
for /f "tokens=*" %%a in ('git log -1 --format^="%%cd" --date^=format^:"%%d/%%m/%%Y %%H:%%M:%%S"') do echo │ Data:     %%a
echo └──────────────────────────────────────────────────────────────┘
echo.

REM Status final
echo ┌─ STATUS ─────────────────────────────────────────────────────┐
for /f "tokens=*" %%a in ('git branch --show-current') do echo │ Branch:   %%a
echo │ Remote:   origin/main
if %ERRORS% EQU 0 (
    echo │ Erros:    Nenhum
    echo │ Sync:     OK
) else (
    echo │ Erros:    %ERRORS%
    echo │ Sync:     Parcial
)
echo └──────────────────────────────────────────────────────────────┘
echo.
pause

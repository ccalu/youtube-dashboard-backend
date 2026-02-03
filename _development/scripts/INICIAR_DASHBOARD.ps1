# ========================================
# SCRIPT DE INICIALIZAÇÃO DO DASHBOARD
# ========================================
# Autor: Claude Code
# Descrição: Inicia Backend + Frontend + Abre Dashboard no navegador
# ========================================

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "   YOUTUBE DASHBOARD - INICIANDO   " -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Configurações
$BACKEND_PATH = "D:\ContentFactory\youtube-dashboard-backend"
$FRONTEND_PATH = "D:\ContentFactory\youtube-dashboard-backend\frontend"
$DASHBOARD_URL = "http://localhost:5000"
$WAIT_SECONDS = 5

# Função para verificar se uma porta está em uso
function Test-Port {
    param($Port)
    $connection = Test-NetConnection -ComputerName localhost -Port $Port -InformationLevel Quiet -WarningAction SilentlyContinue
    return $connection
}

# Verificar se as portas já estão em uso
Write-Host "[1/5] Verificando portas..." -ForegroundColor Yellow

$backend_running = Test-Port -Port 8000
$frontend_running = Test-Port -Port 5000

if ($backend_running) {
    Write-Host "   ✓ Backend já está rodando (porta 8000)" -ForegroundColor Green
} else {
    Write-Host "   ⚠ Backend não está rodando - iniciando..." -ForegroundColor Yellow

    # Iniciar Backend em nova janela
    Write-Host "[2/5] Iniciando Backend (FastAPI)..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$BACKEND_PATH'; python main.py"
    Write-Host "   ✓ Backend iniciado!" -ForegroundColor Green
    Start-Sleep -Seconds 3
}

if ($frontend_running) {
    Write-Host "   ✓ Frontend já está rodando (porta 5000)" -ForegroundColor Green
} else {
    Write-Host "   ⚠ Frontend não está rodando - iniciando..." -ForegroundColor Yellow

    # Iniciar Frontend em nova janela
    Write-Host "[3/5] Iniciando Frontend (Flask)..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$FRONTEND_PATH'; python app.py"
    Write-Host "   ✓ Frontend iniciado!" -ForegroundColor Green
}

# Aguardar servidores iniciarem
Write-Host ""
Write-Host "[4/5] Aguardando servidores iniciarem..." -ForegroundColor Yellow
for ($i = $WAIT_SECONDS; $i -gt 0; $i--) {
    Write-Host "   Aguardando $i segundos..." -ForegroundColor Gray
    Start-Sleep -Seconds 1
}
Write-Host "   ✓ Servidores prontos!" -ForegroundColor Green

# Abrir Dashboard no navegador
Write-Host ""
Write-Host "[5/5] Abrindo Dashboard no navegador..." -ForegroundColor Yellow
Start-Process $DASHBOARD_URL
Write-Host "   ✓ Dashboard aberto em: $DASHBOARD_URL" -ForegroundColor Green

# Finalização
Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "   DASHBOARD INICIADO COM SUCESSO!  " -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:5000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Pressione qualquer tecla para fechar esta janela..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# -*- coding: utf-8 -*-
"""
Dashboard de Upload Diário
Interface visual para monitoramento do sistema de upload automático
Porta: localhost:5002
"""

from flask import Flask, render_template_string, jsonify, request
from flask_cors import CORS
import os
from datetime import datetime, timedelta, timezone
from supabase import create_client
from dotenv import load_dotenv
import asyncio
import logging
import threading

# Importa o uploader
from daily_uploader import DailyUploader

# Carrega variáveis
load_dotenv()

# Configuração Flask
app = Flask(__name__)
CORS(app)
app.config['JSON_AS_ASCII'] = False

# Cliente Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================
# TEMPLATE HTML
# ============================================================

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard de Upload Diário</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        /* Header */
        .header {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .header h1 {
            font-size: 24px;
            color: #333;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .header-info {
            font-size: 14px;
            color: #666;
        }

        .header-buttons {
            display: flex;
            gap: 10px;
        }

        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.3s;
        }

        .btn-primary {
            background: #4CAF50;
            color: white;
        }

        .btn-primary:hover {
            background: #45a049;
        }

        .btn-danger {
            background: #f44336;
            color: white;
        }

        .btn-danger:hover {
            background: #da190b;
        }

        .btn-warning {
            background: #ff9800;
            color: white;
        }

        .btn-warning:hover {
            background: #e68900;
        }

        /* Stats Cards */
        .stats-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }

        .stat-card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .stat-card .number {
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 5px;
        }

        .stat-card .label {
            font-size: 14px;
            color: #666;
        }

        .stat-card.success { border-left: 5px solid #4CAF50; }
        .stat-card.success .number { color: #4CAF50; }

        .stat-card.error { border-left: 5px solid #f44336; }
        .stat-card.error .number { color: #f44336; }

        .stat-card.warning { border-left: 5px solid #ff9800; }
        .stat-card.warning .number { color: #ff9800; }

        .stat-card.info { border-left: 5px solid #2196F3; }
        .stat-card.info .number { color: #2196F3; }

        .stat-card.pending { border-left: 5px solid #9E9E9E; }
        .stat-card.pending .number { color: #9E9E9E; }

        /* Main Table */
        .table-container {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .table-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }

        .table-header h2 {
            font-size: 20px;
            color: #333;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th {
            background: #f5f5f5;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #666;
            border-bottom: 2px solid #ddd;
        }

        td {
            padding: 12px;
            border-bottom: 1px solid #eee;
        }

        tr:hover {
            background: #f9f9f9;
        }

        /* Status badges */
        .status {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
        }

        .status.success {
            background: #d4edda;
            color: #155724;
        }

        .status.error {
            background: #f8d7da;
            color: #721c24;
        }

        .status.warning {
            background: #fff3cd;
            color: #856404;
        }

        .status.pending {
            background: #e2e3e5;
            color: #383d41;
        }

        /* Monetizado badge */
        .monetizado {
            font-size: 18px;
        }

        /* Alerts Section */
        .alerts-container {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .alert-group {
            margin-bottom: 20px;
        }

        .alert-group h3 {
            font-size: 16px;
            color: #333;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .alert-item {
            background: #f8f9fa;
            padding: 10px;
            margin-bottom: 8px;
            border-radius: 5px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-left: 3px solid #ff9800;
        }

        .alert-item.error {
            border-left-color: #f44336;
        }

        .alert-actions {
            display: flex;
            gap: 5px;
        }

        .alert-actions button {
            padding: 4px 8px;
            font-size: 12px;
            border: none;
            border-radius: 3px;
            cursor: pointer;
        }

        /* Progress Bar */
        .progress-container {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .progress-bar-wrapper {
            background: #f0f0f0;
            border-radius: 10px;
            height: 30px;
            overflow: hidden;
            margin-bottom: 10px;
        }

        .progress-bar {
            background: linear-gradient(90deg, #4CAF50, #45a049);
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            transition: width 0.5s ease;
        }

        .progress-info {
            text-align: center;
            color: #666;
            font-size: 14px;
        }

        /* Loading spinner */
        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(0,0,0,.1);
            border-radius: 50%;
            border-top-color: #667eea;
            animation: spin 1s ease-in-out infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        /* Modal */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
        }

        .modal-content {
            background: white;
            margin: 10% auto;
            padding: 30px;
            width: 80%;
            max-width: 500px;
            border-radius: 10px;
        }

        .close {
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }

        .close:hover {
            color: #000;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>
                🎬 Sistema de Upload Automático Diário
            </h1>
            <div class="header-info">
                <div>Última atualização: <span id="ultima-atualizacao">--:--:--</span></div>
                <div>Próximo retry: <span id="proximo-retry">--:--</span></div>
            </div>
            <div class="header-buttons">
                <button class="btn btn-primary" onclick="forcarAgora()">🔄 Forçar Agora</button>
                <button class="btn btn-warning" onclick="retryErros()">🔁 Retry Erros</button>
                <button class="btn btn-danger" onclick="pararTudo()">🛑 Parar Tudo</button>
            </div>
        </div>

        <!-- Stats Cards -->
        <div class="stats-container" id="stats-container">
            <div class="stat-card info">
                <div class="number" id="stat-total">0</div>
                <div class="label">📊 Total</div>
            </div>
            <div class="stat-card success">
                <div class="number" id="stat-sucesso">0</div>
                <div class="label">✅ Sucesso</div>
            </div>
            <div class="stat-card error">
                <div class="number" id="stat-erro">0</div>
                <div class="label">❌ Erros</div>
            </div>
            <div class="stat-card warning">
                <div class="number" id="stat-sem-video">0</div>
                <div class="label">⚠️ Sem Vídeo</div>
            </div>
            <div class="stat-card pending">
                <div class="number" id="stat-pendente">0</div>
                <div class="label">⏳ Pendente</div>
            </div>
        </div>

        <!-- Progress Bar -->
        <div class="progress-container">
            <h3>📈 Progresso do Dia</h3>
            <div class="progress-bar-wrapper">
                <div class="progress-bar" id="progress-bar" style="width: 0%">0%</div>
            </div>
            <div class="progress-info" id="progress-info">
                Aguardando início...
            </div>
        </div>

        <!-- Main Table -->
        <div class="table-container">
            <div class="table-header">
                <h2>📋 Canais - Upload do Dia (<span id="data-hoje">--/--/----</span>)</h2>
                <div id="table-loading" class="spinner"></div>
            </div>
            <table id="canais-table">
                <thead>
                    <tr>
                        <th>Canal</th>
                        <th style="text-align: center">💰</th>
                        <th>Subnicho</th>
                        <th>Status</th>
                        <th>Vídeo</th>
                        <th>⏰</th>
                        <th>Ações</th>
                    </tr>
                </thead>
                <tbody id="canais-tbody">
                    <tr>
                        <td colspan="7" style="text-align: center; padding: 40px;">
                            Carregando dados...
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- Alerts Section -->
        <div class="alerts-container" id="alerts-container">
            <h2>⚠️ Alertas e Ações Necessárias</h2>

            <!-- Canais com erro -->
            <div class="alert-group" id="alert-erros" style="display: none;">
                <h3>🔴 Canais com Erro (<span id="erro-count">0</span>)</h3>
                <div id="erro-list"></div>
            </div>

            <!-- Canais sem vídeo -->
            <div class="alert-group" id="alert-sem-video" style="display: none;">
                <h3>🟡 Canais sem Vídeo Disponível (<span id="sem-video-count">0</span>)</h3>
                <div id="sem-video-list"></div>
            </div>
        </div>
    </div>

    <!-- Modal -->
    <div id="modal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal()">&times;</span>
            <h2 id="modal-title">Título</h2>
            <p id="modal-body">Conteúdo</p>
            <div id="modal-buttons" style="margin-top: 20px; text-align: right;"></div>
        </div>
    </div>

    <script>
        // Estado global
        let dashboardData = null;
        let autoRefreshInterval = null;

        // Inicialização
        document.addEventListener('DOMContentLoaded', function() {
            console.log('Dashboard carregado');
            updateDashboard();

            // Auto-refresh de 1 segundo
            autoRefreshInterval = setInterval(updateDashboard, 1000);

            // Data de hoje
            const hoje = new Date().toLocaleDateString('pt-BR');
            document.getElementById('data-hoje').textContent = hoje;
        });

        // Função principal de atualização
        async function updateDashboard() {
            try {
                const response = await fetch('/api/daily-uploads/status');
                if (!response.ok) throw new Error('Erro ao buscar dados');

                const data = await response.json();
                dashboardData = data;

                // Atualiza timestamp
                const agora = new Date().toLocaleTimeString('pt-BR');
                document.getElementById('ultima-atualizacao').textContent = agora;

                // Atualiza próximo retry
                if (data.proxima_execucao) {
                    const proxima = new Date(data.proxima_execucao);
                    document.getElementById('proximo-retry').textContent =
                        proxima.toLocaleTimeString('pt-BR', {hour: '2-digit', minute: '2-digit'});
                }

                // Atualiza estatísticas
                updateStats(data.stats);

                // Atualiza progresso
                updateProgress(data.stats);

                // Atualiza tabela
                updateTable(data.canais);

                // Atualiza alertas
                updateAlerts(data.canais);

                // Remove loading
                document.getElementById('table-loading').style.display = 'none';

            } catch (error) {
                console.error('Erro ao atualizar dashboard:', error);
            }
        }

        // Atualiza cards de estatísticas
        function updateStats(stats) {
            if (!stats) return;

            document.getElementById('stat-total').textContent = stats.total_canais || 0;
            document.getElementById('stat-sucesso').textContent = stats.com_sucesso || 0;
            document.getElementById('stat-erro').textContent = stats.com_erro || 0;
            document.getElementById('stat-sem-video').textContent = stats.sem_video || 0;
            document.getElementById('stat-pendente').textContent = stats.pendentes || 0;
        }

        // Atualiza barra de progresso
        function updateProgress(stats) {
            if (!stats || !stats.total_canais) return;

            const processados = (stats.com_sucesso || 0) + (stats.com_erro || 0) +
                               (stats.sem_video || 0);
            const percentual = Math.round((processados / stats.total_canais) * 100);

            const progressBar = document.getElementById('progress-bar');
            progressBar.style.width = percentual + '%';
            progressBar.textContent = percentual + '%';

            document.getElementById('progress-info').textContent =
                `Processados: ${processados} de ${stats.total_canais} canais`;
        }

        // Atualiza tabela de canais
        function updateTable(canais) {
            if (!canais || canais.length === 0) return;

            const tbody = document.getElementById('canais-tbody');
            tbody.innerHTML = '';

            canais.forEach(canal => {
                const row = document.createElement('tr');

                // Nome do canal
                const nomeCell = document.createElement('td');
                nomeCell.textContent = canal.channel_name;
                row.appendChild(nomeCell);

                // Monetizado
                const monetizadoCell = document.createElement('td');
                monetizadoCell.style.textAlign = 'center';
                monetizadoCell.innerHTML = canal.is_monetized ?
                    '<span class="monetizado">✅</span>' :
                    '<span class="monetizado">❌</span>';
                row.appendChild(monetizadoCell);

                // Subnicho
                const subnichoCell = document.createElement('td');
                subnichoCell.textContent = canal.subnicho || '-';
                row.appendChild(subnichoCell);

                // Status
                const statusCell = document.createElement('td');
                statusCell.innerHTML = getStatusBadge(canal.status, canal.tentativa_numero);
                row.appendChild(statusCell);

                // Vídeo
                const videoCell = document.createElement('td');
                if (canal.video_title) {
                    // Trunca título longo
                    const titulo = canal.video_title.length > 30 ?
                        canal.video_title.substring(0, 30) + '...' :
                        canal.video_title;
                    videoCell.textContent = titulo;
                    videoCell.title = canal.video_title; // Tooltip com título completo
                } else {
                    videoCell.textContent = '-';
                }
                row.appendChild(videoCell);

                // Horário
                const horarioCell = document.createElement('td');
                if (canal.ultima_tentativa) {
                    const hora = new Date(canal.ultima_tentativa);
                    horarioCell.textContent = hora.toLocaleTimeString('pt-BR',
                        {hour: '2-digit', minute: '2-digit'});
                } else {
                    horarioCell.textContent = '-';
                }
                row.appendChild(horarioCell);

                // Ações
                const acoesCell = document.createElement('td');
                acoesCell.innerHTML = getAcoes(canal);
                row.appendChild(acoesCell);

                tbody.appendChild(row);
            });
        }

        // Retorna badge de status formatado
        function getStatusBadge(status, tentativa) {
            const tentativaText = tentativa > 1 ? ` (${tentativa}/3)` : '';

            switch(status) {
                case 'sucesso':
                    return '<span class="status success">✅ Enviado</span>';
                case 'erro':
                    return `<span class="status error">❌ Erro${tentativaText}</span>`;
                case 'sem_video':
                    return '<span class="status warning">⚠️ Sem Vídeo</span>';
                case 'pendente':
                    return '<span class="status pending">⏳ Aguardando</span>';
                case 'pulado':
                    return '<span class="status pending">⏭️ Pulado</span>';
                default:
                    return '<span class="status pending">❓ Desconhecido</span>';
            }
        }

        // Retorna botões de ação para o canal
        function getAcoes(canal) {
            let html = '';

            if (canal.status === 'erro') {
                html += `<button class="btn btn-primary" style="font-size: 12px; padding: 4px 8px;"
                         onclick="retryCanal('${canal.channel_id}')">🔁 Retry</button> `;
                html += `<button class="btn btn-warning" style="font-size: 12px; padding: 4px 8px;"
                         onclick="uploadNext('${canal.channel_id}')" title="Pula o vídeo com erro e envia o próximo">⏭️ Próximo</button> `;
            }

            if (canal.spreadsheet_id) {
                html += `<button class="btn" style="font-size: 12px; padding: 4px 8px; background: #9C27B0; color: white;"
                         onclick="abrirPlanilha('${canal.spreadsheet_id}')">📊</button>`;
            }

            return html || '-';
        }

        // Atualiza seção de alertas
        function updateAlerts(canais) {
            if (!canais) return;

            // Canais com erro
            const comErro = canais.filter(c => c.status === 'erro');
            const erroGroup = document.getElementById('alert-erros');
            const erroList = document.getElementById('erro-list');

            if (comErro.length > 0) {
                erroGroup.style.display = 'block';
                document.getElementById('erro-count').textContent = comErro.length;
                erroList.innerHTML = '';

                comErro.forEach(canal => {
                    const item = document.createElement('div');
                    item.className = 'alert-item error';
                    item.innerHTML = `
                        <div>
                            <strong>${canal.channel_name}</strong>:
                            ${canal.erro_mensagem || 'Erro desconhecido'}
                            ${canal.tentativa_numero > 1 ? `(Tentativa ${canal.tentativa_numero}/3)` : ''}
                        </div>
                        <div class="alert-actions">
                            <button onclick="verLogs('${canal.channel_id}')">Ver Logs</button>
                            <button onclick="retryCanal('${canal.channel_id}')">Forçar Retry</button>
                            ${canal.spreadsheet_id ? `<button onclick="abrirPlanilha('${canal.spreadsheet_id}')">Abrir Planilha</button>` : ''}
                        </div>
                    `;
                    erroList.appendChild(item);
                });
            } else {
                erroGroup.style.display = 'none';
            }

            // Canais sem vídeo
            const semVideo = canais.filter(c => c.status === 'sem_video');
            const semVideoGroup = document.getElementById('alert-sem-video');
            const semVideoList = document.getElementById('sem-video-list');

            if (semVideo.length > 0) {
                semVideoGroup.style.display = 'block';
                document.getElementById('sem-video-count').textContent = semVideo.length;
                semVideoList.innerHTML = '';

                semVideo.forEach(canal => {
                    const item = document.createElement('div');
                    item.className = 'alert-item';
                    item.innerHTML = `
                        <div>
                            <strong>${canal.channel_name}</strong> -
                            Última verificação: ${canal.ultima_tentativa ?
                                new Date(canal.ultima_tentativa).toLocaleTimeString('pt-BR',
                                {hour: '2-digit', minute: '2-digit'}) : 'N/A'}
                        </div>
                        <div class="alert-actions">
                            ${canal.spreadsheet_id ? `<button onclick="abrirPlanilha('${canal.spreadsheet_id}')">Abrir Planilha</button>` : ''}
                            <button onclick="verificarNovamente('${canal.channel_id}')">Verificar Novamente</button>
                        </div>
                    `;
                    semVideoList.appendChild(item);
                });
            } else {
                semVideoGroup.style.display = 'none';
            }
        }

        // === AÇÕES ===

        async function forcarAgora() {
            if (!confirm('Forçar execução do upload diário agora?')) return;

            showModal('Executando...', 'Processando uploads diários...');

            try {
                const response = await fetch('/api/daily-uploads/force-now', {method: 'POST'});
                const data = await response.json();

                if (data.success) {
                    alert('Upload diário iniciado! Acompanhe o progresso no dashboard.');
                } else {
                    alert('Erro ao iniciar upload: ' + (data.error || 'Erro desconhecido'));
                }
            } catch (error) {
                alert('Erro: ' + error.message);
            } finally {
                closeModal();
            }
        }

        async function retryErros() {
            if (!confirm('Reprocessar todos os canais com erro?')) return;

            showModal('Retry em andamento...', 'Reprocessando canais com erro...');

            try {
                const response = await fetch('/api/daily-uploads/force-retry-all', {method: 'POST'});
                const data = await response.json();

                if (data.success) {
                    alert(`Retry concluído!\nSucesso: ${data.resultados.sucesso.length}\nErro: ${data.resultados.erro.length}`);
                    updateDashboard();
                } else {
                    alert('Erro no retry: ' + (data.error || 'Erro desconhecido'));
                }
            } catch (error) {
                alert('Erro: ' + error.message);
            } finally {
                closeModal();
            }
        }

        async function retryCanal(channelId) {
            if (!confirm('Tentar novamente o upload para este canal?')) return;

            try {
                const response = await fetch(`/api/daily-uploads/force-retry/${channelId}`, {method: 'POST'});
                const data = await response.json();

                if (data.success) {
                    alert('Upload reprocessado com sucesso!');
                    updateDashboard();
                } else {
                    alert('Erro no retry: ' + (data.error || 'Erro desconhecido'));
                }
            } catch (error) {
                alert('Erro: ' + error.message);
            }
        }

        async function uploadNext(channelId) {
            if (!confirm('Pular o vídeo com erro e enviar o PRÓXIMO vídeo da fila?')) return;

            showModal('Enviando próximo...', 'Buscando e enviando próximo vídeo na fila...');

            try {
                const response = await fetch(`/api/daily-uploads/upload-next/${channelId}`, {method: 'POST'});
                const data = await response.json();

                if (data.success) {
                    const videoTitle = data.resultado?.video_title || 'Vídeo';
                    alert(`✅ Próximo vídeo enviado com sucesso!\n\n"${videoTitle}"`);
                    updateDashboard();
                } else if (data.resultado?.status === 'sem_video') {
                    alert('⚠️ Não há próximo vídeo disponível na fila.\n\nVerifique a planilha do canal.');
                } else {
                    alert('❌ Erro ao enviar próximo: ' + (data.resultado?.error || data.error || 'Erro desconhecido'));
                }
            } catch (error) {
                alert('Erro: ' + error.message);
            } finally {
                closeModal();
            }
        }

        function pararTudo() {
            if (!confirm('⚠️ ATENÇÃO: Deseja realmente PARAR todos os uploads em andamento?')) return;

            alert('Sistema de parada de emergência ainda não implementado.\nPor favor, pare o processo manualmente no servidor.');
        }

        function abrirPlanilha(spreadsheetId) {
            const url = `https://docs.google.com/spreadsheets/d/${spreadsheetId}/edit`;
            window.open(url, '_blank');
        }

        function verificarNovamente(channelId) {
            retryCanal(channelId);
        }

        function verLogs(channelId) {
            alert(`Logs do canal ${channelId}:\n\nFuncionalidade em desenvolvimento...`);
        }

        // === MODAL ===
        function showModal(title, body) {
            document.getElementById('modal-title').textContent = title;
            document.getElementById('modal-body').textContent = body;
            document.getElementById('modal').style.display = 'block';
        }

        function closeModal() {
            document.getElementById('modal').style.display = 'none';
        }

        // Fecha modal ao clicar fora
        window.onclick = function(event) {
            const modal = document.getElementById('modal');
            if (event.target == modal) {
                closeModal();
            }
        }
    </script>
</body>
</html>
"""

# ============================================================
# ROTAS DA API
# ============================================================

@app.route('/')
def index():
    """Página principal do dashboard"""
    return render_template_string(DASHBOARD_HTML)


@app.route('/api/daily-uploads/status')
def get_daily_status():
    """
    Retorna status completo do dia para o dashboard
    """
    try:
        hoje = datetime.now().date().isoformat()

        # Buscar canais com upload automático
        canais_result = supabase.table('yt_channels')\
            .select('*')\
            .eq('is_active', True)\
            .eq('upload_automatico', True)\
            .execute()

        canais = canais_result.data if canais_result.data else []

        # Buscar status de hoje
        status_result = supabase.table('yt_canal_upload_diario')\
            .select('*')\
            .eq('data', hoje)\
            .execute()

        status_map = {}
        if status_result.data:
            for s in status_result.data:
                status_map[s['channel_id']] = s

        # Combinar dados
        canais_com_status = []
        stats = {
            'total_canais': len(canais),
            'com_sucesso': 0,
            'com_erro': 0,
            'sem_video': 0,
            'pendentes': 0
        }

        for canal in canais:
            channel_id = canal['channel_id']
            status_hoje = status_map.get(channel_id, {})

            canal_data = {
                'channel_id': channel_id,
                'channel_name': canal['channel_name'],
                'subnicho': canal.get('subnicho'),
                'is_monetized': canal.get('is_monetized', False),
                'spreadsheet_id': canal.get('spreadsheet_id'),
                'status': status_hoje.get('status', 'pendente'),
                'video_title': status_hoje.get('video_titulo'),
                'ultima_tentativa': status_hoje.get('hora_processamento'),
                'tentativa_numero': status_hoje.get('tentativa_numero', 0),
                'erro_mensagem': status_hoje.get('erro_mensagem')
            }

            # Atualiza estatísticas
            status = canal_data['status']
            if status == 'sucesso':
                stats['com_sucesso'] += 1
            elif status == 'erro':
                stats['com_erro'] += 1
            elif status == 'sem_video':
                stats['sem_video'] += 1
            else:
                stats['pendentes'] += 1

            canais_com_status.append(canal_data)

        # Ordenar: monetizados primeiro, depois por status
        canais_com_status.sort(key=lambda x: (
            not x['is_monetized'],  # Monetizados primeiro
            x['status'] != 'erro',   # Erros no topo
            x['channel_name']
        ))

        # Calcular próxima execução
        now = datetime.now()
        if now.hour < 6:
            proxima_execucao = now.replace(hour=6, minute=0, second=0)
        elif now.hour == 6 and now.minute < 30:
            proxima_execucao = now.replace(hour=6, minute=30, second=0)
        elif now.hour < 7:
            proxima_execucao = now.replace(hour=7, minute=0, second=0)
        else:
            # Próximo dia
            amanha = now + timedelta(days=1)
            proxima_execucao = amanha.replace(hour=6, minute=0, second=0)

        return jsonify({
            'data': hoje,
            'stats': stats,
            'canais': canais_com_status,
            'proxima_execucao': proxima_execucao.isoformat()
        })

    except Exception as e:
        logger.error(f"Erro ao buscar status: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/daily-uploads/force-now', methods=['POST'])
def force_upload_now():
    """Força execução do upload diário agora"""
    try:
        # Executa em background usando Thread
        uploader = DailyUploader()

        def run_upload():
            """Executa upload em thread separada"""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(uploader.execute_daily_upload(retry_attempt=1))
            loop.close()

        # Inicia thread em background
        thread = threading.Thread(target=run_upload, daemon=True)
        thread.start()

        return jsonify({
            'success': True,
            'message': 'Upload diário iniciado em background'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/daily-uploads/force-retry-all', methods=['POST'])
def force_retry_all():
    """Força retry de todos os canais com erro"""
    try:
        uploader = DailyUploader()

        # Executa retry de forma síncrona para retornar resultado
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        resultados = loop.run_until_complete(
            uploader.retry_failed_channels(retry_attempt=99, manual=True)
        )

        return jsonify({
            'success': True,
            'resultados': {
                'sucesso': [{'channel_name': r['channel_name']} for r in resultados.get('sucesso', [])],
                'erro': [{'channel_name': r['channel_name'], 'error': r.get('error')}
                        for r in resultados.get('erro', [])]
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/daily-uploads/force-retry/<channel_id>', methods=['POST'])
def force_retry_single(channel_id):
    """Força retry de um canal específico"""
    try:
        uploader = DailyUploader()

        # Executa retry
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        resultado = loop.run_until_complete(
            uploader.retry_single_channel(channel_id, manual=True)
        )

        return jsonify({
            'success': resultado.get('status') == 'sucesso',
            'resultado': resultado
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/daily-uploads/upload-next/<channel_id>', methods=['POST'])
def upload_next_video(channel_id):
    """
    Pula o vídeo com erro atual e faz upload do próximo na fila

    Útil quando o primeiro vídeo está com problema e você quer
    continuar com o próximo sem precisar consertar o atual.
    """
    try:
        uploader = DailyUploader()

        # Executa upload do próximo
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        resultado = loop.run_until_complete(
            uploader.upload_next_video(channel_id)
        )

        return jsonify({
            'success': resultado.get('status') == 'sucesso',
            'resultado': resultado
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================
# INICIALIZAÇÃO
# ============================================================

if __name__ == '__main__':
    print("=" * 60)
    print("📊 DASHBOARD DE UPLOAD DIÁRIO")
    print("=" * 60)
    print("Acesse: http://localhost:5002")
    print("Auto-refresh: 1 segundo")
    print("=" * 60)

    app.run(debug=False, host='0.0.0.0', port=5002)
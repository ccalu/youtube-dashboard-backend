#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard Organizado por Subnichos - COM HISTÓRICO DIÁRIO E CORREÇÕES
"""

from flask import Flask, render_template_string, jsonify
from flask_cors import CORS
import os
from datetime import datetime, timezone, timedelta
from supabase import create_client
from dotenv import load_dotenv
from collections import defaultdict

# Carrega variáveis
load_dotenv()

# Configuração Flask
app = Flask(__name__)
CORS(app)
app.config['JSON_AS_ASCII'] = False  # Para mostrar caracteres árabes corretamente
app.config['JSONIFY_MIMETYPE'] = 'application/json; charset=utf-8'

# Cliente Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

# HTML com JavaScript CORRIGIDO
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard de Upload Diário</title>
    <meta charset="UTF-8">
    <style>
        body {
            background: #1a1a2e;
            color: white;
            font-family: 'Segoe UI', Arial;
            padding: 20px;
            margin: 0;
        }

        h1 {
            color: #fff;
            margin-bottom: 20px;
            font-size: 28px;
        }

        .stats {
            display: flex;
            gap: 15px;
            margin-bottom: 30px;
        }

        .card {
            background: #16213e;
            padding: 20px;
            border-radius: 8px;
            flex: 1;
            border: 1px solid #0f3460;
            transition: all 0.3s ease;
        }

        .card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }

        .card-value {
            font-size: 36px;
            font-weight: bold;
            margin-bottom: 5px;
        }

        .card-label {
            color: #888;
            font-size: 12px;
            text-transform: uppercase;
        }

        .success { color: #4CAF50; }
        .warning { color: #FFC107; }
        .error { color: #F44336; }
        .info { color: #2196F3; }
        .pending { color: #9C27B0; }

        .subnicho-section {
            margin-bottom: 30px;
            background: #16213e;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #0f3460;
        }

        .subnicho-header {
            background: #0f3460;
            padding: 12px 15px;
            font-weight: bold;
            font-size: 16px;
            color: #fff;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .subnicho-stats {
            font-size: 12px;
            font-weight: normal;
            color: #aaa;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th {
            background: rgba(15, 52, 96, 0.3);
            padding: 10px;
            text-align: left;
            font-size: 13px;
            color: #aaa;
            font-weight: 600;
        }

        td {
            padding: 10px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            font-size: 14px;
        }

        tr:hover {
            background: rgba(255, 255, 255, 0.03);
        }

        .channel-name {
            font-weight: 500;
            color: #fff;
        }

        .monetized-yes {
            color: #4CAF50;
            font-weight: bold;
        }

        .monetized-no {
            color: #888;
        }

        .status-badge {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
        }

        .status-success {
            background: rgba(76, 175, 80, 0.2);
            color: #4CAF50;
        }

        .status-sem_video {
            background: rgba(255, 193, 7, 0.2);
            color: #FFC107;
        }

        .status-error {
            background: rgba(244, 67, 54, 0.2);
            color: #F44336;
        }

        .status-pending {
            background: rgba(156, 39, 176, 0.2);
            color: #9C27B0;
        }

        .video-title {
            max-width: 400px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            color: #b0b0b0;
        }

        .footer {
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #333;
            color: #666;
            font-size: 12px;
        }

        .loading {
            text-align: center;
            padding: 50px;
            color: #666;
        }

        .empty-state {
            text-align: center;
            padding: 20px;
            color: #666;
        }

        .btn-action {
            padding: 8px 12px;
            font-size: 14px;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            margin-right: 8px;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }

        .btn-action:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }

        .btn-upload { background: #2196F3; }
        .btn-upload:hover { background: #1976D2; }

        .btn-hist { background: #9C27B0; }
        .btn-hist:hover { background: #7B1FA2; }

        .btn-sheet {
            background: #4CAF50;
            text-decoration: none;
            color: white;
            will-change: transform;
        }
        .btn-sheet:hover { background: #388E3C; }

        /* Modal de Histórico */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.7);
        }

        .modal-content {
            background-color: #2a2a3e;
            margin: 5% auto;
            padding: 20px;
            border: 1px solid #444;
            width: 90%;
            max-width: 1000px;
            border-radius: 10px;
            max-height: 80vh;
            overflow-y: auto;
        }

        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid #444;
        }

        .modal-header h2 {
            color: #fff;
            margin: 0;
        }

        .close {
            color: #aaa;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }

        .close:hover,
        .close:focus {
            color: #fff;
        }

        .historico-table {
            width: 100%;
            border-collapse: collapse;
        }

        .historico-table th,
        .historico-table td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #444;
        }

        .historico-table th {
            background-color: #1a1a2e;
            color: #fff;
            font-weight: 600;
        }

        .historico-table tr:hover {
            background-color: rgba(255, 255, 255, 0.05);
        }

        .status-success {
            color: #4CAF50;
            font-weight: bold;
        }

        .status-error {
            color: #f44336;
            font-weight: bold;
        }

        .status-sem-video {
            color: #9E9E9E;
            font-style: italic;
        }

        .erro-msg {
            color: #ff6b6b;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <h1>Dashboard de Upload Diário</h1>

    <div class="stats">
        <div class="card" onclick="mostrarResumoCanais()" style="cursor: pointer;">
            <div class="card-value info" id="total">-</div>
            <div class="card-label">📁 Canais Ativos</div>
        </div>
        <div class="card" onclick="abrirHistoricoDiario('sucesso')" style="cursor: pointer;">
            <div class="card-value success" id="sucesso">-</div>
            <div class="card-label">✅ Uploads Hoje</div>
        </div>
        <div class="card" onclick="abrirHistoricoDiario('erro')" style="cursor: pointer;">
            <div class="card-value error" id="erro">-</div>
            <div class="card-label">❌ Falhas Hoje</div>
        </div>
        <div class="card" onclick="abrirHistoricoDiario()" style="cursor: pointer;">
            <div class="card-value pending" id="historico-total">-</div>
            <div class="card-label">📜 Histórico Completo</div>
        </div>
    </div>

    <div id="subnichos-container">
        <div class="loading">Carregando dados...</div>
    </div>

    <div class="footer">
        <span>Última atualização: <span id="update-time">--:--:--</span></span> |
        <span>Auto-refresh: 1 segundo</span> |
        <span id="total-monetizados">-</span> canais monetizados
    </div>

    <!-- Modal de Histórico por Canal -->
    <div id="historicoModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 id="modalTitle">Histórico de Uploads</h2>
                <span class="close" onclick="fecharModal()">&times;</span>
            </div>
            <div id="modalBody">
                <p style="color: #aaa; text-align: center;">Carregando...</p>
            </div>
        </div>
    </div>

    <!-- Modal de Histórico Diário -->
    <div id="historicoDiarioModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 id="historicoDiarioTitulo">Histórico de Uploads - Hoje</h2>
                <span class="close" onclick="fecharHistoricoDiario()">&times;</span>
            </div>
            <div class="modal-body" id="historicoDiarioBody">
                <p>Carregando...</p>
            </div>
        </div>
    </div>

    <script>
        async function forcarUpload(channelId, channelName) {
            if (!confirm('Forçar upload do canal ' + channelName + '?\\n\\nO próximo vídeo "done" da planilha será enviado.')) {
                return;
            }

            // Encontra a célula de status da linha atual
            const botao = event.target;
            const linha = botao.closest('tr');
            const statusCell = linha.querySelector('td:nth-child(3)'); // Coluna de status (3ª coluna)
            const statusOriginal = statusCell.textContent;

            try {
                // Mostra loading no status, não no botão
                statusCell.textContent = statusOriginal + ' ⏳';
                botao.disabled = true;

                const response = await fetch('http://localhost:8000/api/yt-upload/force/' + channelId, {
                    method: 'POST'
                });

                const result = await response.json();

                if (response.ok) {
                    if (result.status === 'sem_video') {
                        // Sem vídeos disponíveis
                        alert('❌ Sem vídeos disponíveis na planilha de ' + channelName);
                        statusCell.textContent = statusOriginal;
                    } else {
                        // Mostra sucesso temporariamente
                        statusCell.textContent = 'processando ✅';

                        // Remove emoji após 5 segundos
                        setTimeout(() => {
                            statusCell.textContent = statusOriginal;
                            atualizar(); // Atualiza dashboard
                        }, 5000);
                    }
                } else {
                    // Erro real - mostra emoji de erro
                    statusCell.textContent = 'erro ❌';
                    alert('❌ Erro: ' + (result.detail || result.message || 'Falha ao iniciar upload'));

                    // Remove emoji após 5 segundos
                    setTimeout(() => {
                        statusCell.textContent = statusOriginal;
                    }, 5000);
                }

                // Restaura botão
                botao.disabled = false;
            } catch (error) {
                alert('❌ Erro de conexão: ' + error.message);
                statusCell.textContent = statusOriginal;
                botao.disabled = false;
            }
        }

        // Funções do Modal de Histórico
        function abrirHistorico(channelId, channelName) {
            var modal = document.getElementById('historicoModal');
            var modalTitle = document.getElementById('modalTitle');
            var modalBody = document.getElementById('modalBody');

            // Atualizar título
            modalTitle.innerHTML = 'Histórico de Uploads - ' + channelName;

            // Mostrar modal com loading
            modal.style.display = 'block';
            modalBody.innerHTML = '<p style="color: #aaa; text-align: center;">Carregando histórico...</p>';

            // Buscar histórico via API
            fetch('/api/canais/' + channelId + '/historico-uploads')
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        modalBody.innerHTML = '<p style="color: #f44336;">Erro ao carregar histórico: ' + data.error + '</p>';
                        return;
                    }

                    // Montar tabela de histórico
                    var html = '<table class="historico-table">';
                    html += '<thead><tr>';
                    html += '<th>Data</th>';
                    html += '<th>Status</th>';
                    html += '<th>Vídeo</th>';
                    html += '<th>Horário</th>';
                    html += '<th>Tentativa</th>';
                    html += '<th>Erro</th>';
                    html += '</tr></thead>';
                    html += '<tbody>';

                    if (data.historico && data.historico.length > 0) {
                        data.historico.forEach(function(item) {
                            html += '<tr>';

                            // Data
                            var data_formatada = new Date(item.data).toLocaleDateString('pt-BR');
                            html += '<td>' + data_formatada + '</td>';

                            // Status com cor
                            var statusClass = 'status-sem-video';
                            var statusText = item.status || 'pendente';
                            if (item.status === 'sucesso') {
                                statusClass = 'status-success';
                                statusText = '✅ Sucesso';
                            } else if (item.status === 'erro') {
                                statusClass = 'status-error';
                                statusText = '❌ Erro';
                            } else if (item.status === 'sem_video') {
                                statusClass = 'status-sem-video';
                                statusText = '⚪ Sem Vídeo';
                            }
                            html += '<td><span class="' + statusClass + '">' + statusText + '</span></td>';

                            // Vídeo
                            html += '<td style="max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">';
                            html += item.video_titulo || '-';
                            html += '</td>';

                            // Horário - CORRIGIDO: converter UTC para Brasília
                            var hora = '-';
                            if (item.hora_processamento) {
                                var dt = new Date(item.hora_processamento);
                                // Converter UTC para Brasília (UTC-3)
                                var brasiliaOffset = -3 * 60 * 60 * 1000; // -3 horas em ms
                                var brasiliaTime = new Date(dt.getTime() + brasiliaOffset);
                                hora = brasiliaTime.toLocaleTimeString('pt-BR', {hour: '2-digit', minute: '2-digit'});
                            }
                            html += '<td>' + hora + '</td>';

                            // Tentativa
                            html += '<td>' + (item.tentativa_numero || 1) + 'ª</td>';

                            // Erro
                            html += '<td>';
                            if (item.erro_mensagem) {
                                html += '<span class="erro-msg" title="' + item.erro_mensagem + '">';
                                // Truncar mensagem de erro se muito longa
                                var erro = item.erro_mensagem;
                                if (erro.length > 50) {
                                    erro = erro.substring(0, 50) + '...';
                                }
                                html += erro;
                                html += '</span>';
                            } else {
                                html += '-';
                            }
                            html += '</td>';

                            html += '</tr>';
                        });
                    } else {
                        html += '<tr><td colspan="6" style="text-align: center; color: #666;">Nenhum histórico encontrado</td></tr>';
                    }

                    html += '</tbody></table>';

                    // Adicionar resumo no topo
                    var resumo = '<div style="margin-bottom: 20px; padding: 10px; background: rgba(255,255,255,0.05); border-radius: 5px;">';
                    resumo += '<strong>Total de registros:</strong> ' + data.total_registros + ' (últimos 30 dias)';
                    resumo += '</div>';

                    modalBody.innerHTML = resumo + html;
                })
                .catch(error => {
                    modalBody.innerHTML = '<p style="color: #f44336;">Erro ao buscar histórico: ' + error + '</p>';
                });
        }

        function fecharModal() {
            var modal = document.getElementById('historicoModal');
            modal.style.display = 'none';
        }

        // Funções do Modal de Histórico Diário
        function abrirHistoricoDiario(statusFiltro) {
            var modal = document.getElementById('historicoDiarioModal');
            var modalBody = document.getElementById('historicoDiarioBody');
            var titulo = document.getElementById('historicoDiarioTitulo');

            // Definir título baseado no filtro
            if (statusFiltro === 'sucesso') {
                titulo.innerText = '✅ Uploads com Sucesso - Hoje';
            } else if (statusFiltro === 'erro') {
                titulo.innerText = '❌ Uploads com Erro - Hoje';
            } else {
                titulo.innerText = '📜 Histórico Completo - Hoje';
            }

            modal.style.display = 'block';
            modalBody.innerHTML = '<p>Carregando...</p>';

            fetch('/api/historico-diario')
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        modalBody.innerHTML = '<p style="color: #f44336;">Erro: ' + data.error + '</p>';
                        return;
                    }

                    var historico = data.historico;

                    // Filtrar se necessário
                    if (statusFiltro) {
                        historico = historico.filter(h => h.status === statusFiltro);
                    }

                    // Montar resumo
                    var html = '<div style="margin-bottom: 20px; padding: 15px; background: rgba(255,255,255,0.05); border-radius: 5px;">';
                    html += '<h3 style="margin-top: 0;">📊 Resumo do Dia ' + data.data + '</h3>';
                    html += '<div style="display: flex; gap: 20px; margin-top: 10px;">';
                    html += '<div>Total de Uploads: <strong>' + data.stats.total + '</strong></div>';
                    html += '<div>✅ Sucesso: <strong style="color: #4CAF50;">' + data.stats.sucesso + '</strong></div>';
                    html += '<div>❌ Erro: <strong style="color: #F44336;">' + data.stats.erro + '</strong></div>';
                    html += '<div>⚪ Sem Vídeo: <strong style="color: #FFC107;">' + data.stats.sem_video + '</strong></div>';
                    html += '</div>';
                    html += '</div>';

                    // Tabela de uploads
                    html += '<table class="historico-table">';
                    html += '<thead><tr>';
                    html += '<th>Horário</th>';
                    html += '<th>Canal</th>';
                    html += '<th>Vídeo</th>';
                    html += '<th>Status</th>';
                    html += '</tr></thead>';
                    html += '<tbody>';

                    if (historico.length > 0) {
                        historico.forEach(function(item) {
                            html += '<tr>';

                            // Horário - CORRIGIDO: converter UTC para Brasília
                            var hora = '-';
                            if (item.hora_processamento || item.created_at) {
                                var dt = new Date(item.hora_processamento || item.created_at);
                                // Converter UTC para Brasília (UTC-3)
                                var brasiliaOffset = -3 * 60 * 60 * 1000; // -3 horas em ms
                                var brasiliaTime = new Date(dt.getTime() + brasiliaOffset);
                                hora = brasiliaTime.toLocaleTimeString('pt-BR', {hour: '2-digit', minute: '2-digit'});
                            }
                            html += '<td>' + hora + '</td>';

                            // Canal
                            html += '<td>' + (item.channel_name || '-') + '</td>';

                            // Vídeo
                            html += '<td style="max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">';
                            html += item.video_titulo || '-';
                            html += '</td>';

                            // Status
                            var statusClass = 'status-pending';
                            var statusText = item.status || 'pendente';
                            if (item.status === 'sucesso') {
                                statusClass = 'status-success';
                                statusText = '✅ Sucesso';
                            } else if (item.status === 'erro') {
                                statusClass = 'status-error';
                                statusText = '❌ Erro';
                            } else if (item.status === 'sem_video') {
                                statusClass = 'status-sem-video';
                                statusText = '⚪ Sem Vídeo';
                            }
                            html += '<td><span class="' + statusClass + '">' + statusText + '</span></td>';

                            html += '</tr>';
                        });
                    } else {
                        html += '<tr><td colspan="4" style="text-align: center; color: #666;">Nenhum upload encontrado</td></tr>';
                    }

                    html += '</tbody></table>';
                    modalBody.innerHTML = html;
                })
                .catch(error => {
                    modalBody.innerHTML = '<p style="color: #f44336;">Erro ao carregar: ' + error + '</p>';
                });
        }

        function fecharHistoricoDiario() {
            var modal = document.getElementById('historicoDiarioModal');
            modal.style.display = 'none';
        }

        function mostrarResumoCanais() {
            // Função para mostrar resumo de canais ativos
            var total = document.getElementById('total').innerText;
            var monetizados = document.getElementById('total-monetizados').innerText;
            alert('📁 Resumo dos Canais\\n\\nTotal de canais ativos: ' + total + '\\nCanais monetizados: ' + monetizados);
        }

        // Fechar modais ao clicar fora
        window.onclick = function(event) {
            var modal = document.getElementById('historicoModal');
            var modalDiario = document.getElementById('historicoDiarioModal');
            if (event.target == modal) {
                modal.style.display = 'none';
            }
            if (event.target == modalDiario) {
                modalDiario.style.display = 'none';
            }
        }

        function verHistorico(channelId, channelName) {
            alert('Histórico do canal: ' + channelName);
            // Aqui você pode adicionar redirecionamento ou modal
        }

        function abrirPlanilha() {
            window.open('https://docs.google.com/spreadsheets/d/1vRF7eyXQpBOaZPo6JTrhXBseL6e5oVzJZZ3N3pUe6J4/edit', '_blank');
        }

        function formatTime(dateStr) {
            if (!dateStr) return '-';
            try {
                // CORRIGIDO: Converter UTC para Brasília manualmente
                var date = new Date(dateStr);
                // Converter UTC para Brasília (UTC-3)
                var brasiliaOffset = -3 * 60 * 60 * 1000; // -3 horas em ms
                var brasiliaTime = new Date(date.getTime() + brasiliaOffset);

                return brasiliaTime.toLocaleTimeString('pt-BR', {
                    hour: '2-digit',
                    minute: '2-digit'
                });
            } catch(e) {
                return '-';
            }
        }

        function atualizar() {
            var xhr = new XMLHttpRequest();
            xhr.open('GET', '/api/status', true);
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4 && xhr.status === 200) {
                    try {
                        var data = JSON.parse(xhr.responseText);

                        // Atualizar estatísticas
                        document.getElementById('total').innerText = data.stats.total || 0;
                        document.getElementById('sucesso').innerText = data.stats.sucesso || 0;
                        document.getElementById('erro').innerText = data.stats.erro || 0;

                        // Atualizar card de histórico total (soma de todos os uploads do dia)
                        var totalHistorico = (data.stats.sucesso || 0) + (data.stats.erro || 0) +
                                           (data.stats.sem_video || 0) + (data.stats.pendente || 0);
                        document.getElementById('historico-total').innerText = totalHistorico;

                        // Contar monetizados
                        var totalMonetizados = 0;

                        // Construir HTML dos subnichos
                        var html = '';

                        if (data.subnichos) {
                            for (var subnicho in data.subnichos) {
                                var canais = data.subnichos[subnicho];

                                // Estatísticas do subnicho
                                var subnichostats = {sucesso: 0, erro: 0, sem_video: 0, pendente: 0};
                                for (var i = 0; i < canais.length; i++) {
                                    var canal = canais[i];
                                    if (canal.is_monetized) totalMonetizados++;
                                    if (canal.status === 'sucesso') subnichostats.sucesso++;
                                    else if (canal.status === 'erro') subnichostats.erro++;
                                    else if (canal.status === 'sem_video') subnichostats.sem_video++;
                                    else subnichostats.pendente++;
                                }

                                // Cores e emojis personalizados por subnicho
                                var corHeader = '#0f3460';
                                var emoji = '';

                                if (subnicho === 'Historias Sombrias') {
                                    corHeader = '#372E65';
                                    emoji = '👑 ';
                                } else if (subnicho === 'Monetizados') {
                                    corHeader = '#24C35D';
                                    emoji = '💸 ';
                                } else if (subnicho === 'Relatos de Guerra') {
                                    corHeader = '#304831';
                                    emoji = '⚔️ ';
                                } else if (subnicho === 'Guerras e Civilizações') {
                                    corHeader = '#EA580C';
                                    emoji = '🛡️ ';
                                }

                                html += '<div class="subnicho-section">';
                                html += '<div class="subnicho-header" style="background: ' + corHeader + ';">';
                                html += '<span>' + emoji + subnicho + '</span>';
                                html += '<span class="subnicho-stats">';
                                html += canais.length + ' canais | ';
                                html += subnichostats.sucesso + ' sucesso | ';
                                html += subnichostats.sem_video + ' sem vídeo';
                                html += '</span>';
                                html += '</div>';

                                html += '<table>';
                                html += '<thead><tr>';
                                html += '<th style="width: 30px">#</th>';
                                html += '<th style="width: 250px">Canal</th>';
                                html += '<th style="width: 100px">Status</th>';
                                html += '<th style="width: 400px">Vídeo Enviado</th>';
                                html += '<th style="width: 80px">Horário</th>';
                                html += '<th style="width: 150px">Ações</th>';
                                html += '</tr></thead>';
                                html += '<tbody>';

                                for (var j = 0; j < canais.length; j++) {
                                    var canal = canais[j];

                                    var statusClass = 'status-pending';
                                    var statusText = 'Pendente';

                                    if (canal.status === 'sucesso') {
                                        statusClass = 'status-success';
                                        statusText = 'Enviado';
                                    } else if (canal.status === 'sem_video') {
                                        statusClass = 'status-sem_video';
                                        statusText = 'Sem Vídeo';
                                    } else if (canal.status === 'erro') {
                                        statusClass = 'status-error';
                                        statusText = 'Erro';
                                    }

                                    html += '<tr>';
                                    html += '<td style="color: #666">' + (j + 1) + '</td>';
                                    html += '<td class="channel-name">' + canal.channel_name;

                                    // Adicionar sigla do idioma
                                    var siglaIdioma = '';
                                    if (canal.lingua) {
                                        var lingua = canal.lingua.toLowerCase();
                                        // Mapear códigos de 2 letras e nomes completos
                                        if (lingua === 'pt' || lingua === 'português' || lingua === 'portugues' || lingua === 'portuguese') {
                                            siglaIdioma = 'PT';
                                        } else if (lingua === 'en' || lingua === 'inglês' || lingua === 'ingles' || lingua === 'english') {
                                            siglaIdioma = 'EN';
                                        } else if (lingua === 'es' || lingua === 'espanhol' || lingua === 'spanish') {
                                            siglaIdioma = 'ES';
                                        } else if (lingua === 'de' || lingua === 'alemão' || lingua === 'alemao' || lingua === 'german') {
                                            siglaIdioma = 'DE';
                                        } else if (lingua === 'fr' || lingua === 'francês' || lingua === 'frances' || lingua === 'french') {
                                            siglaIdioma = 'FR';
                                        } else if (lingua === 'it' || lingua === 'italiano' || lingua === 'italian') {
                                            siglaIdioma = 'IT';
                                        } else if (lingua === 'pl' || lingua === 'polonês' || lingua === 'polones' || lingua === 'polish') {
                                            siglaIdioma = 'PL';
                                        } else if (lingua === 'ru' || lingua === 'russo' || lingua === 'russian') {
                                            siglaIdioma = 'RU';
                                        } else if (lingua === 'ja' || lingua === 'japonês' || lingua === 'japones' || lingua === 'japanese') {
                                            siglaIdioma = 'JP';
                                        } else if (lingua === 'ko' || lingua === 'coreano' || lingua === 'korean') {
                                            siglaIdioma = 'KR';
                                        } else if (lingua === 'tr' || lingua === 'turco' || lingua === 'turkish') {
                                            siglaIdioma = 'TR';
                                        } else if (lingua === 'ar' || lingua === 'arabic' || lingua === 'árabe' || lingua === 'arabe') {
                                            siglaIdioma = 'AR';
                                        }

                                        if (siglaIdioma) {
                                            html += ' <span style="color: #888; font-size: 11px;">(' + siglaIdioma + ')</span>';
                                        }
                                    }

                                    if (canal.is_monetized) {
                                        html += ' <span style="color: #4CAF50; font-size: 10px;">$</span>';
                                    }
                                    html += '</td>';
                                    html += '<td><span class="status-badge ' + statusClass + '">' + statusText + '</span></td>';
                                    html += '<td class="video-title">' + (canal.video_titulo || '-') + '</td>';
                                    html += '<td>' + formatTime(canal.hora_upload) + '</td>';
                                    html += '<td>';
                                    // Botão de upload forçado com data attributes
                                    html += '<button class="btn-action btn-upload" data-channel-id="' + canal.channel_id + '" data-channel-name="' + canal.channel_name.replace(/"/g, '&quot;') + '">📤</button>';
                                    // Botão de histórico
                                    html += '<button class="btn-action btn-hist" data-channel-id="' + canal.channel_id + '" data-channel-name="' + canal.channel_name.replace(/"/g, '&quot;') + '">📊</button>';

                                    // Botão da planilha como link clicável
                                    if (canal.spreadsheet_id && canal.spreadsheet_id !== '') {
                                        var sheetUrl = 'https://docs.google.com/spreadsheets/d/' + canal.spreadsheet_id;
                                        html += '<a href="' + sheetUrl + '" target="_blank" class="btn-action btn-sheet">📑</a>';
                                    } else {
                                        html += '<button class="btn-action btn-sheet" disabled style="opacity: 0.5; cursor: not-allowed;">📑</button>';
                                    }

                                    html += '</td>';
                                    html += '</tr>';
                                }

                                html += '</tbody></table>';
                                html += '</div>';
                            }
                        }

                        if (html === '') {
                            html = '<div class="empty-state">Nenhum canal encontrado</div>';
                        }

                        document.getElementById('subnichos-container').innerHTML = html;
                        document.getElementById('total-monetizados').innerText = totalMonetizados;

                        // Atualizar hora - CORRIGIDO: converter para Brasília
                        var now = new Date();
                        // Pegar horário atual em UTC e converter para Brasília
                        var utcTime = now.getTime() + (now.getTimezoneOffset() * 60000);
                        var brasiliaOffset = -3 * 60 * 60 * 1000; // -3 horas em ms
                        var brasiliaTime = new Date(utcTime + brasiliaOffset);
                        var timeStr = brasiliaTime.toLocaleTimeString('pt-BR');
                        document.getElementById('update-time').innerText = timeStr;

                    } catch(e) {
                        console.error('Erro:', e);
                        document.getElementById('subnichos-container').innerHTML =
                            '<div class="empty-state">Erro ao carregar dados</div>';
                    }
                }
            };
            xhr.send();
        }

        // Atualizar imediatamente e depois a cada segundo
        atualizar();
        setInterval(atualizar, 1000);

        // Adicionar listener para botões de histórico
        document.addEventListener('click', function(e) {
            if (e.target && e.target.classList && e.target.classList.contains('btn-hist')) {
                var channelId = e.target.getAttribute('data-channel-id');
                var channelName = e.target.getAttribute('data-channel-name');
                if (channelId && channelName) {
                    abrirHistorico(channelId, channelName);
                }
            }
            // Listener para botões de upload forçado
            else if (e.target && e.target.classList && e.target.classList.contains('btn-upload')) {
                var channelId = e.target.getAttribute('data-channel-id');
                var channelName = e.target.getAttribute('data-channel-name');
                if (channelId && channelName) {
                    forcarUpload(channelId, channelName);
                }
            }
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/status')
def get_status():
    try:
        # Buscar canais ativos
        canais = supabase.table('yt_channels')\
            .select('*')\
            .eq('is_active', True)\
            .eq('upload_automatico', True)\
            .execute()

        # Buscar uploads de hoje
        today = datetime.now(timezone.utc).date().isoformat()
        uploads = supabase.table('yt_canal_upload_diario')\
            .select('*')\
            .eq('data', today)\
            .execute()

        # Criar mapa de uploads
        upload_map = {u['channel_id']: u for u in uploads.data}

        # Processar dados e agrupar por subnicho
        subnichos_dict = defaultdict(list)
        stats = {
            'total': 0,
            'sucesso': 0,
            'erro': 0,
            'sem_video': 0,
            'pendente': 0
        }

        for canal in canais.data:
            upload = upload_map.get(canal['channel_id'])

            status = 'pendente'
            video_titulo = None
            hora_upload = None

            if upload:
                if upload.get('upload_realizado'):
                    status = 'sucesso'
                    video_titulo = upload.get('video_titulo')
                    hora_upload = upload.get('hora_processamento') or upload.get('updated_at')
                elif upload.get('status') == 'sem_video':
                    status = 'sem_video'
                elif upload.get('erro_mensagem'):
                    status = 'erro'

            stats['total'] += 1
            stats[status] += 1

            # Agrupar por subnicho
            subnicho = canal.get('subnicho', 'Sem Categoria')
            subnichos_dict[subnicho].append({
                'channel_id': canal['channel_id'],
                'channel_name': canal['channel_name'],
                'spreadsheet_id': canal.get('spreadsheet_id', ''),
                'lingua': canal.get('lingua', ''),
                'is_monetized': canal.get('is_monetized', False),
                'status': status,
                'video_titulo': video_titulo,
                'hora_upload': hora_upload
            })

        # Corrigir monetização dos canais específicos
        monetizados_forcados = [
            'UCzfZRuRHSp6erCwzuhjywFw',  # Archives de Guerre
            'UCWYzVowgJ6LlxCcYlMGcLtA',  # WWII Erzählungen
        ]

        # Corrigir dados antes de agrupar
        for subnicho in subnichos_dict:
            for canal in subnichos_dict[subnicho]:
                # Forçar monetização
                if canal['channel_id'] in monetizados_forcados:
                    canal['is_monetized'] = True

        # Padronizar subnichos - MONETIZADOS TÊM PRIORIDADE
        novo_dict = defaultdict(list)
        for subnicho, canais in subnichos_dict.items():
            for canal in canais:
                # Se é monetizado, SEMPRE vai para Monetizados
                if canal['is_monetized']:
                    novo_dict['Monetizados'].append(canal)
                # Unificar Guerras e Civilizações com Relatos de Guerra
                elif 'Guerra' in subnicho or 'guerra' in subnicho or 'Civiliza' in subnicho:
                    novo_dict['Relatos de Guerra'].append(canal)
                else:
                    novo_dict[subnicho].append(canal)
        subnichos_dict = novo_dict

        # Ordenar canais: status primeiro (sucesso > pendente > erro > sem_video)
        status_order = {'sucesso': 0, 'pendente': 1, 'erro': 2, 'sem_video': 3}
        for subnicho in subnichos_dict:
            subnichos_dict[subnicho].sort(key=lambda x: (
                status_order.get(x['status'], 4),  # Status primeiro
                not x['is_monetized'],  # Depois monetizados
                x['channel_name']  # Por fim, nome
            ))

        return jsonify({
            'stats': stats,
            'subnichos': dict(subnichos_dict)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/historico-diario')
def get_historico_diario():
    """Retorna histórico de uploads do dia"""
    try:
        # Buscar uploads de hoje (Brasília UTC-3)
        agora_utc = datetime.now(timezone.utc)
        brasilia_offset = timedelta(hours=-3)
        agora_brasilia = agora_utc + brasilia_offset
        hoje_inicio = agora_brasilia.replace(hour=0, minute=0, second=0, microsecond=0)
        hoje_fim = agora_brasilia.replace(hour=23, minute=59, second=59, microsecond=999999)

        # Converter de volta para UTC para query
        hoje_inicio_utc = hoje_inicio - brasilia_offset
        hoje_fim_utc = hoje_fim - brasilia_offset

        # Buscar da tabela de histórico
        response = supabase.table('yt_canal_upload_historico')\
            .select('*')\
            .gte('created_at', hoje_inicio_utc.isoformat())\
            .lte('created_at', hoje_fim_utc.isoformat())\
            .order('created_at', desc=True)\
            .execute()

        historico = response.data if response.data else []

        # Se não tiver histórico, buscar da tabela diária
        if not historico:
            today = agora_brasilia.date().isoformat()
            response = supabase.table('yt_canal_upload_diario')\
                .select('*')\
                .eq('data', today)\
                .execute()
            historico = response.data if response.data else []

        # Estatísticas
        stats = {
            'total': len(historico),
            'sucesso': sum(1 for h in historico if h.get('status') == 'sucesso' or h.get('upload_realizado')),
            'erro': sum(1 for h in historico if h.get('status') == 'erro' or (h.get('erro_mensagem') and not h.get('upload_realizado'))),
            'sem_video': sum(1 for h in historico if h.get('status') == 'sem_video'),
            'pendente': sum(1 for h in historico if h.get('status') == 'pendente' or (not h.get('status') and not h.get('upload_realizado')))
        }

        # Ajustar status dos registros
        for h in historico:
            if not h.get('status'):
                if h.get('upload_realizado'):
                    h['status'] = 'sucesso'
                elif h.get('erro_mensagem'):
                    h['status'] = 'erro'
                else:
                    h['status'] = 'pendente'

        return jsonify({
            'stats': stats,
            'historico': historico,
            'data': agora_brasilia.strftime('%d/%m/%Y')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/canais/<channel_id>/historico-uploads')
def get_historico_uploads(channel_id):
    """Retorna histórico de uploads do canal (últimos 30 dias)"""
    try:
        from datetime import timedelta

        # Buscar últimos 30 dias de histórico
        hoje = datetime.now(timezone.utc).date()
        data_inicio = hoje - timedelta(days=30)

        # Primeiro tentar buscar da tabela de histórico (preserva múltiplos uploads)
        try:
            response = supabase.table('yt_canal_upload_historico')\
                .select('*')\
                .eq('channel_id', channel_id)\
                .gte('data', data_inicio.isoformat())\
                .order('data', desc=False)\
                .order('hora_processamento', desc=False)\
                .execute()
        except Exception as e:
            # Se a tabela de histórico não existe, buscar da tabela diária
            if "relation" in str(e) and "does not exist" in str(e):
                response = supabase.table('yt_canal_upload_diario')\
                    .select('*')\
                    .eq('channel_id', channel_id)\
                    .gte('data', data_inicio.isoformat())\
                    .order('data', desc=False)\
                    .execute()
            else:
                raise e

        # Formatar resposta
        historico = []
        for item in response.data:
            registro = {
                'data': item['data'],
                'status': item.get('status', 'pendente'),
                'video_titulo': item.get('video_titulo', '-'),
                'hora_processamento': item.get('hora_processamento'),
                'erro_mensagem': item.get('erro_mensagem'),
                'tentativa_numero': item.get('tentativa_numero', 1),
                'upload_realizado': item.get('upload_realizado', False),
                'youtube_video_id': item.get('youtube_video_id')
            }

            # Ajustar status baseado em outros campos se necessário
            if not registro['status'] or registro['status'] == 'pendente':
                if registro['upload_realizado']:
                    registro['status'] = 'sucesso'
                elif registro['erro_mensagem']:
                    registro['status'] = 'erro'

            historico.append(registro)

        return jsonify({
            'channel_id': channel_id,
            'total_registros': len(historico),
            'historico': historico
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("DASHBOARD COM HISTÓRICO DIÁRIO E CORREÇÕES")
    print("Acesse: http://localhost:5006")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5006, debug=False)
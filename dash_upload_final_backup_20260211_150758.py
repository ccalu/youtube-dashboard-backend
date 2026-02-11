#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard Organizado por Subnichos - CORRIGIDO COM ONCLICK
"""

from flask import Flask, render_template_string, jsonify, make_response
from flask_cors import CORS
import os
from datetime import datetime, timezone
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
        <div class="card">
            <div class="card-value info" id="total">-</div>
            <div class="card-label">Total de Canais</div>
        </div>
        <div class="card">
            <div class="card-value success" id="sucesso">-</div>
            <div class="card-label">Upload com Sucesso</div>
        </div>
        <div class="card">
            <div class="card-value warning" id="sem_video">-</div>
            <div class="card-label">Sem Vídeo</div>
        </div>
        <div class="card">
            <div class="card-value error" id="erro">-</div>
            <div class="card-label">Com Erro</div>
        </div>
        <div class="card" onclick="abrirHistoricoCompleto()" style="cursor: pointer;">
            <div class="card-value info" id="historico_completo">📜</div>
            <div class="card-label">Histórico Completo</div>
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

    <!-- Modal de Histórico -->
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

    <!-- Modal de Histórico Completo -->
    <div id="historicoCompletoModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 id="modalTitleCompleto">Histórico Completo - Todos os Canais</h2>
                <span class="close" onclick="fecharModalCompleto()">&times;</span>
            </div>
            <div id="modalBodyCompleto">
                <p style="color: #aaa; text-align: center;">Carregando histórico completo...</p>
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
                    // Mostra sucesso temporariamente
                    statusCell.textContent = 'processando ✅';

                    // Remove emoji após 5 segundos
                    setTimeout(() => {
                        statusCell.textContent = statusOriginal;
                        atualizar(); // Atualiza dashboard
                    }, 5000);

                } else if (result.status === 'sem_video' || result.status === 'no_video') {
                    // Sem vídeos disponíveis - não mostra emoji, apenas alerta
                    alert('❌ Sem vídeos disponíveis na planilha de ' + channelName);
                    statusCell.textContent = statusOriginal;
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

                            // Horário
                            var hora = '-';
                            if (item.hora_processamento) {
                                var dt = new Date(item.hora_processamento);
                                hora = dt.toLocaleTimeString('pt-BR', {hour: '2-digit', minute: '2-digit', timeZone: 'America/Sao_Paulo'});
                            }
                            html += '<td>' + hora + '</td>';

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

        function fecharModalCompleto() {
            var modal = document.getElementById('historicoCompletoModal');
            modal.style.display = 'none';
        }

        // Função para abrir o histórico completo
        async function abrirHistoricoCompleto() {
            var modal = document.getElementById('historicoCompletoModal');
            var modalBody = document.getElementById('modalBodyCompleto');

            modal.style.display = 'block';
            modalBody.innerHTML = '<p style="color: #aaa; text-align: center;">Carregando histórico completo...</p>';

            try {
                const response = await fetch('/api/historico-completo');
                const data = await response.json();

                if (data.historico_por_data && data.historico_por_data.length > 0) {
                    var html = '<div style="max-height: 500px; overflow-y: auto;">';

                    // Estatísticas gerais
                    html += '<div style="background: rgba(76, 175, 80, 0.2); padding: 15px; border-radius: 5px; margin-bottom: 20px; border: 1px solid #4CAF50;">';
                    html += '<p style="margin: 0; color: #4CAF50; font-weight: bold; font-size: 16px;">Últimos ' + data.total_dias + ' dias | Total de registros: ' + data.total_registros + '</p>';
                    html += '</div>';

                    // Histórico por data
                    data.historico_por_data.forEach(function(dia) {
                        // Formatar data para dd/mm/yyyy
                        var dataFormatada = dia.data;
                        if (dia.data && dia.data.includes('-')) {
                            var partes = dia.data.split('-');
                            if (partes.length === 3) {
                                dataFormatada = partes[2] + '/' + partes[1] + '/' + partes[0];
                            }
                        }

                        html += '<div style="background: #1a1a1a; padding: 15px; border-radius: 5px; margin-bottom: 15px;">';
                        html += '<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">';
                        html += '<h4 style="margin: 0; color: #4CAF50;">' + dataFormatada + '</h4>';
                        html += '<div>';
                        html += '<span style="color: #4CAF50;">✅ Sucesso: ' + dia.sucesso + '</span> | ';
                        html += '<span style="color: #FF9800;">⚠️ Sem vídeo: ' + dia.sem_video + '</span> | ';
                        html += '<span style="color: #f44336;">❌ Erro: ' + dia.erro + '</span>';
                        html += '</div>';
                        html += '</div>';

                        if (dia.canais && dia.canais.length > 0) {
                            // Filtrar apenas canais com sucesso
                            var canaisSucesso = dia.canais.filter(function(canal) {
                                return canal.status === 'sucesso';
                            });

                            if (canaisSucesso.length > 0) {
                                html += '<table style="width: 100%; font-size: 0.9em;">';
                                html += '<thead><tr>';
                                html += '<th style="text-align: left; padding: 5px;">Hora</th>';
                                html += '<th style="text-align: left; padding: 5px;">Canal</th>';
                                html += '<th style="text-align: left; padding: 5px;">Vídeo</th>';
                                html += '<th style="text-align: left; padding: 5px;">Status</th>';
                                html += '</tr></thead>';
                                html += '<tbody>';

                                canaisSucesso.forEach(function(canal) {
                                    // Converter hora de ISO para HH:MM
                                    var horaFormatada = '-';
                                    if (canal.hora) {
                                        try {
                                            var dt = new Date(canal.hora);
                                            horaFormatada = dt.toLocaleTimeString('pt-BR', {
                                                hour: '2-digit',
                                                minute: '2-digit',
                                                timeZone: 'America/Sao_Paulo'
                                            });
                                        } catch(e) {
                                            horaFormatada = canal.hora.substring(11, 16); // fallback
                                        }
                                    }

                                    var statusColor = '#4CAF50'; // Sempre verde pois só mostra sucessos
                                    var statusEmoji = '✅';

                                    html += '<tr>';
                                    html += '<td style="padding: 5px;">' + horaFormatada + '</td>';
                                    html += '<td style="padding: 5px;">' + canal.nome + '</td>';
                                    html += '<td style="padding: 5px; max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">' +
                                           (canal.video_titulo || '-') + '</td>';
                                    html += '<td style="padding: 5px; color: ' + statusColor + ';">' +
                                           statusEmoji + ' ' + canal.status + '</td>';
                                    html += '</tr>';
                                });

                                html += '</tbody></table>';
                            } else {
                                html += '<p style="color: #666; text-align: center; padding: 10px;">Nenhum upload bem-sucedido neste dia</p>';
                            }
                        }

                        html += '</div>';
                    });

                    html += '</div>';
                    modalBody.innerHTML = html;
                } else {
                    modalBody.innerHTML = '<p style="color: #aaa; text-align: center;">Nenhum histórico encontrado.</p>';
                }
            } catch (error) {
                modalBody.innerHTML = '<p style="color: #f44336; text-align: center;">Erro ao carregar histórico: ' + error.message + '</p>';
            }
        }

        // Fechar modal ao clicar fora
        window.onclick = function(event) {
            var modal = document.getElementById('historicoModal');
            var modalCompleto = document.getElementById('historicoCompletoModal');
            if (event.target == modal) {
                modal.style.display = 'none';
            } else if (event.target == modalCompleto) {
                modalCompleto.style.display = 'none';
            }
        }

        function verHistorico(channelId, channelName) {
            alert('Histórico do canal: ' + channelName);
            // Aqui você pode adicionar redirecionamento ou modal
        }

        function abrirPlanilha() {
            window.open('https://docs.google.com/spreadsheets/d/1vRF7eyXQpBOaZPo6JTrhXBseL6e5oVzJZZ3N3pUe6J4/edit', '_blank');
        }

        function atualizarCache() {
            // Limpar cache e recarregar página
            if (confirm('Isso irá atualizar o cache e recarregar a página. Continuar?')) {
                // Forçar reload sem cache
                location.reload(true);
            }
        }

        function formatTime(dateStr) {
            if (!dateStr) return '-';
            try {
                var date = new Date(dateStr);
                // Força timezone do Brasil
                return date.toLocaleTimeString('pt-BR', {
                    hour: '2-digit',
                    minute: '2-digit',
                    timeZone: 'America/Sao_Paulo'
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

                        // Atualizar estatísticas com verificações defensivas
                        var totalElement = document.getElementById('total');
                        if (totalElement) totalElement.innerText = data.stats.total || 0;

                        var sucessoElement = document.getElementById('sucesso');
                        if (sucessoElement) sucessoElement.innerText = data.stats.sucesso || 0;

                        var semVideoElement = document.getElementById('sem_video');
                        if (semVideoElement) semVideoElement.innerText = data.stats.sem_video || 0;

                        var erroElement = document.getElementById('erro');
                        if (erroElement) erroElement.innerText = data.stats.erro || 0;

                        // Nota: elemento 'pendente' foi removido e substituído por histórico completo

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

                        // Atualizar hora
                        var now = new Date();
                        var timeStr = now.toLocaleTimeString('pt-BR', {timeZone: 'America/Sao_Paulo'});
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
    response = make_response(render_template_string(HTML_TEMPLATE))
    # Headers anti-cache para evitar problemas com navegador
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

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

@app.route('/api/canais/<channel_id>/historico-uploads')
def get_historico_uploads(channel_id):
    """Retorna histórico de uploads do canal (últimos 30 dias)"""
    try:
        from datetime import timedelta

        # Buscar últimos 30 dias de histórico
        hoje = datetime.now(timezone.utc).date()
        data_inicio = hoje - timedelta(days=30)

        # Primeiro buscar da tabela de histórico (preserva múltiplos uploads)
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

        historico_data = response.data if response.data else []

        # IMPORTANTE: Adicionar dados da tabela diária para o dia atual (fallback)
        # Isso garante que uploads de hoje apareçam mesmo se ainda não foram movidos para histórico
        response_diario = supabase.table('yt_canal_upload_diario')\
            .select('*')\
            .eq('channel_id', channel_id)\
            .eq('data', hoje.isoformat())\
            .execute()

        if response_diario.data:
            # Verificar se já temos dados de hoje no histórico
            datas_historico = {item['data'] for item in historico_data}
            print(f"DEBUG: Tem dados diários? {len(response_diario.data)}, Hoje está no histórico? {hoje.isoformat() in datas_historico}")
            if hoje.isoformat() not in datas_historico:
                # Adicionar dados do dia atual da tabela diária
                print(f"DEBUG: Adicionando {len(response_diario.data)} registros da tabela diária")
                historico_data.extend(response_diario.data)

        # Formatar resposta
        historico = []
        for item in historico_data:
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
            historico.append(registro)

        return jsonify({
            'channel_id': channel_id,
            'total_registros': len(historico),
            'historico': historico
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/historico-completo')
def get_historico_completo():
    """Retorna histórico completo dos últimos 30 dias agrupado por data"""
    try:
        from datetime import timedelta
        from collections import defaultdict

        # Buscar últimos 30 dias
        hoje = datetime.now(timezone.utc).date()
        data_inicio = hoje - timedelta(days=30)

        # Buscar do histórico
        response = supabase.table('yt_canal_upload_historico')\
            .select('*')\
            .gte('data', data_inicio.isoformat())\
            .order('data', desc=True)\
            .execute()

        # Agrupar por data
        historico_por_data = defaultdict(lambda: {
            'data': '',
            'total': 0,
            'sucesso': 0,
            'erro': 0,
            'sem_video': 0,
            'canais': []
        })

        for item in response.data:
            data_str = item['data']
            historico_por_data[data_str]['data'] = data_str
            historico_por_data[data_str]['total'] += 1

            # Contar por status
            status = item.get('status', 'pendente')
            if status == 'sucesso':
                historico_por_data[data_str]['sucesso'] += 1
            elif status == 'erro':
                historico_por_data[data_str]['erro'] += 1
            elif status == 'sem_video':
                historico_por_data[data_str]['sem_video'] += 1

            # Adicionar detalhes do canal
            historico_por_data[data_str]['canais'].append({
                'nome': item.get('channel_name', ''),
                'status': status,
                'video_titulo': item.get('video_titulo', ''),
                'hora': item.get('hora_processamento', '')
            })

        # Adicionar dados da tabela diária para o dia atual (pode não estar no histórico ainda)
        response_diario = supabase.table('yt_canal_upload_diario')\
            .select('*')\
            .eq('data', hoje.isoformat())\
            .execute()

        if response_diario.data:
            data_str = hoje.isoformat()
            if data_str not in historico_por_data:
                historico_por_data[data_str] = {
                    'data': data_str,
                    'total': 0,
                    'sucesso': 0,
                    'erro': 0,
                    'sem_video': 0,
                    'canais': []
                }

            # Adicionar TODOS os status do dia atual da tabela diária (não apenas sem_video)
            for item in response_diario.data:
                # Verificar se este canal já não está no histórico
                canal_ja_existe = any(
                    c['nome'] == item.get('channel_name') and c['status'] == item.get('status')
                    for c in historico_por_data[data_str]['canais']
                )
                if not canal_ja_existe:
                    status = item.get('status', 'pendente')

                    # Atualizar contadores
                    historico_por_data[data_str]['total'] += 1
                    if status == 'sucesso':
                        historico_por_data[data_str]['sucesso'] += 1
                    elif status == 'erro':
                        historico_por_data[data_str]['erro'] += 1
                    elif status == 'sem_video':
                        historico_por_data[data_str]['sem_video'] += 1

                    # Adicionar canal à lista
                    historico_por_data[data_str]['canais'].append({
                        'nome': item.get('channel_name', ''),
                        'status': status,
                        'video_titulo': item.get('video_titulo', ''),
                        'hora': item.get('hora_processamento', '')
                    })

        # Converter para lista e ordenar por data
        historico_lista = sorted(
            historico_por_data.values(),
            key=lambda x: x['data'],
            reverse=True
        )

        # Calcular totais
        dias_mostrados = min(30, len(historico_lista))
        total_registros = sum(d['total'] for d in historico_lista[:30])

        return jsonify({
            'historico_por_data': historico_lista[:30],  # Limitar a 30 dias
            'total_dias': dias_mostrados,
            'total_registros': total_registros
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("DASHBOARD ORGANIZADO POR SUBNICHOS - CORRIGIDO")
    print("Acesse: http://localhost:5006")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5006, debug=False)
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
import time

# Carrega variáveis
load_dotenv()

def extrair_hora(timestamp_str):
    """Extrai HH:MM do timestamp (sem conversão de timezone)"""
    if not timestamp_str:
        return None
    try:
        ts = str(timestamp_str)
        if 'T' in ts and len(ts) >= 16:
            return ts[11:16]
        return None
    except:
        return None

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

# Cache global para otimização (10 segundos de TTL)
_status_cache = {'data': None, 'timestamp': 0}
CACHE_TTL = 10  # 10 segundos de cache para reduzir carga

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
            transition: transform 0.15s ease, border-color 0.2s ease, box-shadow 0.2s ease;
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
            color: #ddd;
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

        tr {
            transition: background 0.15s ease;
        }
        tr:hover {
            background: rgba(255, 255, 255, 0.05);
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
            transition: transform 0.1s ease, opacity 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
            text-decoration: none;
            display: inline-block;
        }

        .btn-action:hover {
            opacity: 0.9;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        }

        .btn-action:active {
            transform: scale(0.92);
            opacity: 1;
        }

        .btn-upload { background: #2196F3; }
        .btn-upload:hover { background: #1976D2; }

        .btn-hist { background: #FF9800; }
        .btn-hist:hover { background: #F57C00; }

        .btn-sheet {
            background: #4CAF50;
            text-decoration: none;
            color: white;
        }
        .btn-sheet:hover { background: #388E3C; }

        /* Modal de Histórico */
        .modal {
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.7);
            visibility: hidden;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.2s ease, visibility 0s 0.2s;
        }

        .modal.show {
            visibility: visible;
            opacity: 1;
            pointer-events: auto;
            transition: opacity 0.2s ease, visibility 0s 0s;
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
            transform: translateY(-20px);
            transition: transform 0.25s ease;
        }

        .modal.show .modal-content {
            transform: translateY(0);
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
            transition: color 0.15s ease, transform 0.15s ease;
        }

        .close:hover,
        .close:focus {
            color: #fff;
            transform: scale(1.2);
        }

        .close:active {
            transform: scale(0.9);
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

        .card-filtro, .card-historico {
            cursor: pointer;
        }
        .card-filtro:hover, .card-historico:hover {
            border-color: #fff;
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        }
        .card-filtro:active, .card-historico:active {
            transform: translateY(0) scale(0.97);
            transition: transform 0.05s ease;
        }
        .card-filtro.ativo {
            border-color: #fff;
            box-shadow: 0 0 10px rgba(255,255,255,0.2);
        }

        .dia-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 15px;
            background: #0f3460;
            border-radius: 5px;
            cursor: pointer;
            margin-bottom: 2px;
            user-select: none;
            transition: background 0.15s ease, transform 0.1s ease;
        }
        .dia-header:hover {
            background: #13407a;
        }
        .dia-header:active {
            transform: scale(0.99);
        }
        .dia-seta {
            display: inline-block;
            transition: transform 0.2s ease;
        }
        .dia-seta.aberto {
            transform: rotate(90deg);
        }
        .dia-content {
            max-height: 0;
            overflow: hidden;
            padding: 0 15px;
            background: #16213e;
            border-radius: 0 0 5px 5px;
            margin-bottom: 15px;
            transition: max-height 0.3s ease, padding 0.3s ease;
        }
        .dia-content.aberto {
            max-height: 2000px;
            padding: 10px 15px 15px;
        }

        .btn-pagina {
            padding: 6px 14px;
            background: #0f3460;
            color: #fff;
            border: 1px solid #1a5276;
            border-radius: 5px;
            cursor: pointer;
            font-size: 13px;
            transition: background 0.15s ease, transform 0.1s ease;
        }
        .btn-pagina:hover { background: #1a5276; }
        .btn-pagina:active { transform: scale(0.95); }
        .btn-pagina:disabled { opacity: 0.4; cursor: not-allowed; }

        @keyframes pulse-success {
            0%, 100% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.4); }
            50% { box-shadow: 0 0 0 4px rgba(76, 175, 80, 0); }
        }
        .status-success { animation: pulse-success 2s infinite; }
    </style>
</head>
<body>
    <h1>Dashboard de Upload Diário</h1>

    <div class="stats">
        <div class="card card-filtro" id="card-total" onclick="toggleFiltro(null)" style="cursor: pointer;">
            <div class="card-value info" id="total">-</div>
            <div class="card-label">Total de Canais</div>
        </div>
        <div class="card card-filtro" id="card-sucesso" onclick="toggleFiltro('sucesso')" style="background: rgba(76, 175, 80, 0.15);">
            <div class="card-value success" id="sucesso">-</div>
            <div class="card-label">Upload com Sucesso</div>
        </div>
        <div class="card card-filtro" id="card-sem_video" onclick="toggleFiltro('sem_video')" style="background: rgba(255, 193, 7, 0.15);">
            <div class="card-value warning" id="sem_video">-</div>
            <div class="card-label">Sem Vídeo</div>
        </div>
        <div class="card card-filtro" id="card-erro" onclick="toggleFiltro('erro')" style="background: rgba(244, 67, 54, 0.15);">
            <div class="card-value error" id="erro">-</div>
            <div class="card-label">Com Erro</div>
        </div>
        <div class="card card-historico" onclick="abrirHistoricoCompleto()" style="cursor: pointer; background: rgba(255, 152, 0, 0.15);">
            <div class="card-value info" id="historico_completo">📜</div>
            <div class="card-label">Histórico Completo</div>
        </div>
    </div>

    <div id="subnichos-container">
        <div class="loading">Carregando dados...</div>
    </div>

    <div class="footer">
        <span>Última atualização: <span id="update-time">--:--:--</span></span> |
        <span>Auto-refresh: 5 segundos</span> |
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
        // Variável global de filtro
        var filtroStatus = null;

        function truncarTitulo(titulo) {
            if (!titulo || titulo === '-') return '-';
            var palavras = titulo.split(' ');
            if (palavras.length > 7) return palavras.slice(0, 7).join(' ') + '...';
            return titulo;
        }

        function getSiglaIdioma(lingua) {
            if (!lingua) return '';
            var l = lingua.toLowerCase();
            var mapa = {
                'pt': 'PT', 'português': 'PT', 'portugues': 'PT', 'portuguese': 'PT',
                'en': 'EN', 'inglês': 'EN', 'ingles': 'EN', 'english': 'EN',
                'es': 'ES', 'espanhol': 'ES', 'spanish': 'ES',
                'de': 'DE', 'alemão': 'DE', 'alemao': 'DE', 'german': 'DE',
                'fr': 'FR', 'francês': 'FR', 'frances': 'FR', 'french': 'FR',
                'it': 'IT', 'italiano': 'IT', 'italian': 'IT',
                'pl': 'PL', 'polonês': 'PL', 'polones': 'PL', 'polish': 'PL',
                'ru': 'RU', 'russo': 'RU', 'russian': 'RU',
                'ja': 'JP', 'japonês': 'JP', 'japones': 'JP', 'japanese': 'JP',
                'ko': 'KR', 'coreano': 'KR', 'korean': 'KR',
                'tr': 'TR', 'turco': 'TR', 'turkish': 'TR',
                'ar': 'AR', 'arabic': 'AR', 'árabe': 'AR', 'arabe': 'AR'
            };
            return mapa[l] || '';
        }

        function toggleFiltro(status) {
            document.querySelectorAll('.card-filtro').forEach(function(c) { c.classList.remove('ativo'); });
            if (!status || filtroStatus === status) {
                filtroStatus = null;
            } else {
                filtroStatus = status;
                var card = document.getElementById('card-' + status);
                if (card) card.classList.add('ativo');
            }
            atualizar();
        }

        function toggleDia(id) {
            var el = document.getElementById(id);
            var seta = document.getElementById('seta-' + id);
            el.classList.toggle('aberto');
            if (seta) seta.classList.toggle('aberto');
        }

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

        // Dados do histórico individual (para paginação)
        var _historicoData = [];
        var _historicoPagina = 0;
        var _HIST_POR_PAGINA = 10;

        function renderHistoricoPagina() {
            var modalBody = document.getElementById('modalBody');
            var items = _historicoData;
            var totalPaginas = Math.ceil(items.length / _HIST_POR_PAGINA);
            var inicio = _historicoPagina * _HIST_POR_PAGINA;
            var fim = Math.min(inicio + _HIST_POR_PAGINA, items.length);
            var paginaItems = items.slice(inicio, fim);

            // Contadores gerais
            var countSucesso = 0, countSemVideo = 0, countErro = 0;
            items.forEach(function(item) {
                if (item.status === 'sucesso') countSucesso++;
                else if (item.status === 'sem_video') countSemVideo++;
                else if (item.status === 'erro') countErro++;
            });

            // Resumo (estilo unificado com histórico completo)
            var resumo = '<div style="background: rgba(76,175,80,0.2); padding: 15px; border-radius: 5px; margin-bottom: 20px; border: 1px solid #4CAF50;">';
            resumo += '<p style="margin: 0; color: #4CAF50; font-weight: bold; font-size: 16px;">';
            resumo += 'Total: ' + items.length + ' registros — ';
            resumo += '<span style="color: #4CAF50;">✅ ' + countSucesso + '</span> | ';
            resumo += '<span style="color: #FF9800;">⚠️ ' + countSemVideo + '</span> | ';
            resumo += '<span style="color: #f44336;">❌ ' + countErro + '</span>';
            resumo += '</p></div>';

            // Tabela (estilo unificado com histórico completo)
            var thStyle = 'text-align: left; padding: 8px; background: #0f3460; color: #aaa; font-weight: 600;';
            var html = '<div style="background: #16213e; padding: 10px 15px 15px; border-radius: 5px;">';
            html += '<table style="width: 100%; font-size: 0.9em; border-collapse: collapse;">';
            html += '<thead><tr>';
            html += '<th style="' + thStyle + '">Data</th>';
            html += '<th style="' + thStyle + '">Vídeo</th>';
            html += '<th style="' + thStyle + '">Status</th>';
            html += '<th style="' + thStyle + '">Horário</th>';
            html += '</tr></thead>';
            html += '<tbody>';

            var tdBorder = 'border-bottom: 1px solid rgba(255,255,255,0.05);';
            if (paginaItems.length > 0) {
                paginaItems.forEach(function(item) {
                    html += '<tr>';
                    var df = item.data;
                    if (df && df.includes('-')) { var p = df.split('-'); df = p[2] + '/' + p[1] + '/' + p[0]; }
                    html += '<td style="padding: 8px; ' + tdBorder + '">' + df + '</td>';
                    html += '<td style="padding: 8px; max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; ' + tdBorder + '">' + truncarTitulo(item.video_titulo) + '</td>';
                    var statusColor = '#9E9E9E'; var statusText = '⚪ Sem Vídeo';
                    if (item.status === 'sucesso') { statusColor = '#4CAF50'; statusText = '✅ Sucesso'; }
                    else if (item.status === 'erro') { statusColor = '#f44336'; statusText = '❌ Erro'; }
                    html += '<td style="padding: 8px; color: ' + statusColor + '; ' + tdBorder + '">' + statusText + '</td>';
                    html += '<td style="padding: 8px; ' + tdBorder + '">' + (item.hora_processamento || '-') + '</td>';
                    html += '</tr>';
                });
            } else {
                html += '<tr><td colspan="4" style="text-align: center; color: #666; padding: 15px;">Nenhum histórico encontrado</td></tr>';
            }
            html += '</tbody></table>';

            // Paginação
            if (totalPaginas > 1) {
                html += '<div style="display: flex; justify-content: center; align-items: center; gap: 10px; margin-top: 15px;">';
                html += '<button class="btn-pagina" onclick="_historicoPagina--; renderHistoricoPagina();" ' + (_historicoPagina === 0 ? 'disabled' : '') + '>← Anterior</button>';
                html += '<span style="color: #aaa;">Página ' + (_historicoPagina + 1) + ' de ' + totalPaginas + '</span>';
                html += '<button class="btn-pagina" onclick="_historicoPagina++; renderHistoricoPagina();" ' + (_historicoPagina >= totalPaginas - 1 ? 'disabled' : '') + '>Próxima →</button>';
                html += '</div>';
            }
            html += '</div>';

            modalBody.innerHTML = resumo + html;
        }

        // Funções do Modal de Histórico
        function abrirHistorico(channelId, channelName) {
            var modal = document.getElementById('historicoModal');
            var modalTitle = document.getElementById('modalTitle');
            var modalBody = document.getElementById('modalBody');

            modalTitle.innerHTML = 'Histórico de Uploads - ' + channelName;
            modal.classList.add('show');
            modalBody.innerHTML = '<p style="color: #aaa; text-align: center;">Carregando histórico...</p>';

            fetch('/api/canais/' + channelId + '/historico-uploads')
                .then(function(response) { return response.json(); })
                .then(function(data) {
                    if (data.error) {
                        modalBody.innerHTML = '<p style="color: #f44336;">Erro: ' + data.error + '</p>';
                        return;
                    }

                    // Filtrar duplicatas
                    if (data.historico && data.historico.length > 0) {
                        var vistos = new Set();
                        var filtrado = [];
                        data.historico.forEach(function(item) {
                            var chave = item.data + '|' + (item.video_titulo || 'sem_video');
                            if (!vistos.has(chave)) { vistos.add(chave); filtrado.push(item); }
                        });
                        data.historico = filtrado;
                    }

                    _historicoData = data.historico || [];
                    _historicoPagina = 0;
                    renderHistoricoPagina();
                })
                .catch(function(error) {
                    modalBody.innerHTML = '<p style="color: #f44336;">Erro ao buscar histórico: ' + error + '</p>';
                });
        }

        function fecharModal() {
            var modal = document.getElementById('historicoModal');
            modal.classList.remove('show');
        }

        function fecharModalCompleto() {
            var modal = document.getElementById('historicoCompletoModal');
            modal.classList.remove('show');
        }

        // Função para abrir o histórico completo
        async function abrirHistoricoCompleto() {
            var modal = document.getElementById('historicoCompletoModal');
            var modalBody = document.getElementById('modalBodyCompleto');

            modal.classList.add('show');
            modalBody.innerHTML = '<p style="color: #aaa; text-align: center;">Carregando histórico completo...</p>';

            try {
                const response = await fetch('/api/historico-completo');
                const data = await response.json();

                if (data.historico_por_data && data.historico_por_data.length > 0) {
                    // Primeiro passo: filtrar duplicatas e canais sem nome em cada dia
                    data.historico_por_data.forEach(function(dia) {
                        if (dia.canais && dia.canais.length > 0) {
                            var vistos = new Set();
                            var canaisFiltrados = [];
                            dia.canais.forEach(function(canal) {
                                if (!canal.nome || canal.nome.trim() === '') return;
                                var chave = dia.data + '|' + canal.nome + '|' + (canal.video_titulo || 'sem_video');
                                if (!vistos.has(chave)) {
                                    vistos.add(chave);
                                    canaisFiltrados.push(canal);
                                }
                            });
                            dia.canais = canaisFiltrados;
                        }
                    });

                    // Segundo passo: contar tudo ANTES de montar o HTML
                    var totalSucessoGeral = 0;
                    var totalSemVideoGeral = 0;
                    var totalErroGeral = 0;

                    data.historico_por_data.forEach(function(dia) {
                        dia.canais.forEach(function(canal) {
                            if (canal.status === 'sucesso') totalSucessoGeral++;
                            else if (canal.status === 'sem_video') totalSemVideoGeral++;
                            else if (canal.status === 'erro') totalErroGeral++;
                        });
                    });

                    // Terceiro passo: montar HTML
                    var html = '<div style="max-height: 500px; overflow-y: auto;">';

                    // Estatísticas gerais no topo
                    html += '<div style="background: rgba(76, 175, 80, 0.2); padding: 15px; border-radius: 5px; margin-bottom: 20px; border: 1px solid #4CAF50;">';
                    html += '<p style="margin: 0; color: #4CAF50; font-weight: bold; font-size: 16px;">Últimos ' + data.total_dias + ' dias | Total de uploads: ' + totalSucessoGeral + '</p>';
                    html += '</div>';

                    // Histórico por data (accordion)
                    data.historico_por_data.forEach(function(dia, idx) {
                        var dataFormatada = dia.data;
                        if (dia.data && dia.data.includes('-')) {
                            var partes = dia.data.split('-');
                            if (partes.length === 3) {
                                dataFormatada = partes[2] + '/' + partes[1] + '/' + partes[0];
                            }
                        }

                        var sucessoDia = 0, semVideoDia = 0, erroDia = 0;
                        dia.canais.forEach(function(canal) {
                            if (canal.status === 'sucesso') sucessoDia++;
                            else if (canal.status === 'sem_video') semVideoDia++;
                            else if (canal.status === 'erro') erroDia++;
                        });

                        var diaId = 'dia-' + idx;

                        // Header clicável (accordion)
                        var diaIdSafe = diaId.replace(/"/g, '');
                        html += '<div class="dia-header" data-dia="' + diaIdSafe + '" onclick="toggleDia(this.dataset.dia)">';
                        html += '<div>';
                        html += '<span id="seta-' + diaId + '" class="dia-seta" style="margin-right: 8px;">▶</span>';
                        html += '<span style="color: #4CAF50; font-weight: bold;">' + dataFormatada + '</span>';
                        html += '</div>';
                        html += '<div style="font-size: 0.85em;">';
                        html += '<span style="color: #4CAF50;">✅ Sucesso: ' + sucessoDia + '</span> | ';
                        html += '<span style="color: #FF9800;">⚠️ Sem vídeo: ' + semVideoDia + '</span> | ';
                        html += '<span style="color: #f44336;">❌ Erro: ' + erroDia + '</span>';
                        html += '</div>';
                        html += '</div>';

                        // Conteúdo (fechado por padrão)
                        html += '<div class="dia-content" id="' + diaId + '">';

                        var canaisSucesso = dia.canais.filter(function(c) { return c.status === 'sucesso'; });
                        if (canaisSucesso.length > 0) {
                            html += '<table style="width: 100%; font-size: 0.9em;">';
                            html += '<thead><tr>';
                            html += '<th style="text-align: left; padding: 5px;">Canal</th>';
                            html += '<th style="text-align: left; padding: 5px;">Vídeo</th>';
                            html += '<th style="text-align: left; padding: 5px;">Status</th>';
                            html += '<th style="text-align: left; padding: 5px;">Horário</th>';
                            html += '</tr></thead>';
                            html += '<tbody>';

                            canaisSucesso.forEach(function(canal) {
                                var sigla = getSiglaIdioma(canal.lingua);
                                var nomeComIdioma = canal.nome + (sigla ? ' <span style="color: #888; font-size: 0.85em;">(' + sigla + ')</span>' : '');

                                html += '<tr>';
                                html += '<td style="padding: 5px;">' + nomeComIdioma + '</td>';
                                html += '<td style="padding: 5px; max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">' +
                                       truncarTitulo(canal.video_titulo) + '</td>';
                                html += '<td style="padding: 5px; color: #4CAF50;">✅ sucesso</td>';
                                html += '<td style="padding: 5px;">' + (canal.hora || '-') + '</td>';
                                html += '</tr>';
                            });

                            html += '</tbody></table>';
                        } else {
                            html += '<p style="color: #666; text-align: center; padding: 10px;">Nenhum upload com sucesso neste dia</p>';
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
                modal.classList.remove('show');
            } else if (event.target == modalCompleto) {
                modalCompleto.classList.remove('show');
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

        function formatTime(timeStr) {
            if (!timeStr) return '-';
            return timeStr;
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

                                    // Filtro por status
                                    if (filtroStatus && canal.status !== filtroStatus) continue;

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
                                    var siglaIdioma = getSiglaIdioma(canal.lingua);
                                    if (siglaIdioma) {
                                        html += ' <span style="color: #888; font-size: 11px;">(' + siglaIdioma + ')</span>';
                                    }

                                    if (canal.is_monetized) {
                                        html += ' <span style="color: #4CAF50; font-size: 10px;">$</span>';
                                    }
                                    html += '</td>';
                                    html += '<td><span class="status-badge ' + statusClass + '">' + statusText + '</span></td>';
                                    html += '<td class="video-title">' + truncarTitulo(canal.video_titulo) + '</td>';
                                    html += '<td>' + formatTime(canal.hora_upload) + '</td>';
                                    html += '<td>';
                                    // Botão de upload forçado com data attributes
                                    html += '<button class="btn-action btn-upload" data-channel-id="' + canal.channel_id + '" data-channel-name="' + canal.channel_name.replace(/"/g, '&quot;') + '">📤</button>';
                                    // Botão de histórico
                                    html += '<button class="btn-action btn-hist" data-channel-id="' + canal.channel_id + '" data-channel-name="' + canal.channel_name.replace(/"/g, '&quot;') + '">📜</button>';

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

                        var container = document.getElementById('subnichos-container');
                        if (container.innerHTML !== html) {
                            container.innerHTML = html;
                        }
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
        setInterval(atualizar, 5000);

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
    global _status_cache

    # Verificar cache (reduz 90% das queries)
    now = time.time()
    if _status_cache['data'] and (now - _status_cache['timestamp']) < CACHE_TTL:
        return _status_cache['data']

    try:
        # Buscar canais ativos (apenas campos necessários - otimizado)
        canais = supabase.table('yt_channels')\
            .select('channel_id, channel_name, spreadsheet_id, lingua, is_monetized, subnicho')\
            .eq('is_active', True)\
            .eq('upload_automatico', True)\
            .order('subnicho, channel_name')\
            .execute()

        # Buscar uploads de hoje (apenas campos necessários - otimizado)
        today = datetime.now(timezone.utc).date().isoformat()
        uploads = supabase.table('yt_canal_upload_diario')\
            .select('channel_id, status, upload_realizado, video_titulo, hora_processamento, erro_mensagem')\
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
                    hora_upload = extrair_hora(upload.get('hora_processamento') or upload.get('updated_at'))
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

        # Salvar no cache antes de retornar
        result = jsonify({
            'stats': stats,
            'subnichos': dict(subnichos_dict)
        })
        _status_cache['data'] = result
        _status_cache['timestamp'] = time.time()
        return result

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/canais/<channel_id>/historico-uploads')
def get_historico_uploads(channel_id):
    """Retorna histórico completo de uploads do canal"""
    try:
        # Buscar TODO o histórico (sem limite de data)
        try:
            response = supabase.table('yt_canal_upload_historico')\
                .select('*')\
                .eq('channel_id', channel_id)\
                .order('data', desc=True)\
                .order('hora_processamento', desc=True)\
                .execute()
        except Exception as e:
            if "relation" in str(e) and "does not exist" in str(e):
                response = supabase.table('yt_canal_upload_diario')\
                    .select('*')\
                    .eq('channel_id', channel_id)\
                    .order('data', desc=True)\
                    .execute()
            else:
                raise e

        historico_data = response.data if response.data else []

        # Buscar TODOS os dados da tabela diária como fallback
        response_diario = supabase.table('yt_canal_upload_diario')\
            .select('*')\
            .eq('channel_id', channel_id)\
            .order('data', desc=True)\
            .execute()

        if response_diario.data:
            # Criar set com chave única usando canal + data + video_titulo
            # Isso evita duplicatas visuais do mesmo vídeo no mesmo dia
            # Mantém múltiplos uploads diferentes do mesmo canal no mesmo dia
            registros_unicos = {
                (
                    item.get('channel_id'),
                    item['data'],
                    item.get('video_titulo', '')
                )
                for item in historico_data
            }

            # Adicionar registros da tabela diária que não estão no histórico
            for item_diario in response_diario.data:
                chave_unica = (
                    item_diario.get('channel_id'),
                    item_diario['data'],
                    item_diario.get('video_titulo', '')
                )
                if chave_unica not in registros_unicos:
                    historico_data.append(item_diario)
                    registros_unicos.add(chave_unica)  # Atualizar set para evitar duplicatas

        # Ordenar por data desc + hora desc (garante ordem após merge das 2 tabelas)
        historico_data.sort(key=lambda x: (x.get('data', ''), x.get('hora_processamento', '')), reverse=True)

        # Formatar resposta
        historico = []
        for item in historico_data:
            registro = {
                'data': item['data'],
                'status': item.get('status', 'pendente'),
                'video_titulo': item.get('video_titulo', '-'),
                'hora_processamento': extrair_hora(item.get('hora_processamento')),
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

        # Buscar mapa de idiomas dos canais
        canais_info = supabase.table('yt_channels')\
            .select('channel_name, lingua')\
            .eq('is_active', True)\
            .execute()
        mapa_lingua = {c['channel_name']: c.get('lingua', '') for c in canais_info.data} if canais_info.data else {}

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

            # VERIFICAR NOME DO CANAL ANTES DE CONTAR
            nome_canal = item.get('channel_name', '').strip()
            if nome_canal:  # Só conta e adiciona se tiver nome
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
                    'nome': nome_canal,
                    'status': status,
                    'video_titulo': item.get('video_titulo', ''),
                    'hora': extrair_hora(item.get('hora_processamento')) or '',
                    'lingua': mapa_lingua.get(nome_canal, '')
                })

        # Adicionar TODOS os dados da tabela diária dos últimos 30 dias
        # Isso garante que status sem_video e erro apareçam para TODAS as datas
        response_diario = supabase.table('yt_canal_upload_diario')\
            .select('*')\
            .gte('data', data_inicio.isoformat())\
            .execute()

        if response_diario.data:
            # Processar TODAS as datas da tabela diária, não apenas hoje
            for item in response_diario.data:
                data_str = item.get('data')

                # Criar entrada para a data se não existir
                if data_str not in historico_por_data:
                    historico_por_data[data_str] = {
                        'data': data_str,
                        'total': 0,
                        'sucesso': 0,
                        'erro': 0,
                        'sem_video': 0,
                        'canais': []
                    }

                # PULAR SE NÃO TIVER NOME DE CANAL
                nome_canal = item.get('channel_name', '').strip()
                if not nome_canal:
                    continue  # Pula para o próximo item se não tiver nome

                # Verificar se este vídeo específico já não está no histórico
                # Usar chave composta: nome + video_titulo (evita duplicatas visuais)
                # Permite múltiplos uploads diferentes do mesmo canal no mesmo dia
                video_ja_existe = any(
                    c['nome'] == nome_canal and
                    c.get('video_titulo', '') == item.get('video_titulo', '')
                    for c in historico_por_data[data_str]['canais']
                )
                if not video_ja_existe:
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
                        'nome': nome_canal,
                        'status': status,
                        'video_titulo': item.get('video_titulo', ''),
                        'hora': extrair_hora(item.get('hora_processamento')) or '',
                        'lingua': mapa_lingua.get(nome_canal, '')
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
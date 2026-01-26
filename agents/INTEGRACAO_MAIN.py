# ========================================
# CODIGO DE INTEGRACAO - ADICIONAR AO main.py
# ========================================
# INSTRUCOES:
# 1. Adicione o import no inicio do main.py (linha ~25)
# 2. Adicione a inicializacao apos "db = SupabaseClient()" (linha ~205)
# 3. Adicione o router apos "app.include_router(monetization_router)" (linha ~181)
# ========================================

# ==========================================
# PASSO 1: ADICIONAR ESTE IMPORT NO INICIO DO main.py
# (junto com os outros imports, linha ~25)
# ==========================================

# Agents System
from agents_endpoints import router as agents_router, init_agents_router


# ==========================================
# PASSO 2: ADICIONAR ESTA LINHA APOS app.include_router(monetization_router)
# (linha ~181)
# ==========================================

# 🤖 AGENTS ROUTER
# app.include_router(agents_router)


# ==========================================
# PASSO 3: ADICIONAR ESTA INICIALIZACAO APOS "uploader = YouTubeUploader()"
# (linha ~203)
# ==========================================

# 🤖 Inicializar sistema de agentes
# agents_api = init_agents_router(db, collector)
# app.include_router(agents_api)


# ==========================================
# ALTERNATIVA: CODIGO COMPLETO PARA ADICIONAR
# Copie este bloco e adicione onde indicado
# ==========================================

"""
# ========================================
# 🤖 SISTEMA DE AGENTES INTELIGENTES
# ========================================
# Importar (no inicio do arquivo):
from agents_endpoints import router as agents_router, init_agents_router

# Inicializar (apos uploader = YouTubeUploader()):
try:
    agents_api = init_agents_router(db, collector)
    app.include_router(agents_api)
    logger.info("🤖 Sistema de Agentes inicializado com sucesso!")
except Exception as e:
    logger.warning(f"⚠️ Nao foi possivel inicializar sistema de agentes: {e}")
"""

# ==========================================
# ENDPOINTS DISPONIVEIS APOS INTEGRACAO:
# ==========================================
"""
STATUS:
- GET  /api/agents/status              - Status de todos os agentes
- GET  /api/agents/scheduler/status    - Status do scheduler

EXECUCAO:
- POST /api/agents/run/all             - Executa todos os agentes
- POST /api/agents/run/{agent_name}    - Executa um agente especifico
- POST /api/agents/run/analysis        - Executa apenas analise (rapido)

DADOS:
- GET  /api/agents/data                - Dados de todos os agentes
- GET  /api/agents/data/{agent_name}   - Dados de um agente especifico

RELATORIOS HTML:
- GET  /api/agents/reports             - Lista relatorios disponiveis
- GET  /api/agents/reports/{filename}  - Visualiza relatorio HTML
- GET  /api/agents/reports/json/latest - Dados JSON mais recentes

SCHEDULER:
- POST /api/agents/scheduler/start     - Inicia execucao automatica
- POST /api/agents/scheduler/stop      - Para execucao automatica

INSIGHTS RAPIDOS:
- GET  /api/agents/insights/trending       - Tendencias atuais
- GET  /api/agents/insights/recommendations - Recomendacoes
- GET  /api/agents/insights/alerts         - Alertas ativos
- GET  /api/agents/insights/opportunities  - Oportunidades
"""

# ==========================================
# EXEMPLO DE USO VIA CURL:
# ==========================================
"""
# Executar todos os agentes
curl -X POST http://localhost:8000/api/agents/run/all

# Ver status
curl http://localhost:8000/api/agents/status

# Ver tendencias
curl http://localhost:8000/api/agents/insights/trending

# Ver relatorio HTML (abrir no navegador)
http://localhost:8000/api/agents/reports/morning_brief.html
"""

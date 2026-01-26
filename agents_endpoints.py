# ========================================
# AGENTS API ENDPOINTS
# ========================================
# Endpoints para acessar o sistema de agentes
# ========================================

import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse
import os
import json

logger = logging.getLogger(__name__)

# Router para os endpoints de agentes
router = APIRouter(prefix="/api/agents", tags=["agents"])

# Variaveis globais (serao inicializadas pelo main.py)
orchestrator = None
scheduler = None


def init_agents_router(db_client, collector=None, output_dir: str = None):
    """
    Inicializa o router com as dependencias.
    Deve ser chamado pelo main.py apos inicializar db e collector.
    """
    global orchestrator, scheduler

    from agents.orchestrator import AgentOrchestrator
    from agents.scheduler import AgentScheduler

    # Definir diretorio de saida
    if not output_dir:
        output_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "reports"
        )

    # Criar diretorio se nao existir
    os.makedirs(output_dir, exist_ok=True)

    # Inicializar orchestrator e scheduler
    orchestrator = AgentOrchestrator(db_client, collector, output_dir)
    scheduler = AgentScheduler(orchestrator)

    logger.info(f"Agents router initialized. Reports dir: {output_dir}")

    return router


# ========================================
# ENDPOINTS DE STATUS
# ========================================

@router.get("/status")
async def get_agents_status():
    """
    Retorna status de todos os agentes.
    """
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator nao inicializado")

    return {
        "status": "ok",
        "orchestrator": orchestrator.get_status(),
        "scheduler": scheduler.get_status() if scheduler else None
    }


@router.get("/scheduler/status")
async def get_scheduler_status():
    """
    Retorna status do scheduler.
    """
    if not scheduler:
        raise HTTPException(status_code=500, detail="Scheduler nao inicializado")

    return scheduler.get_status()


# ========================================
# ENDPOINTS DE EXECUCAO
# ========================================

@router.post("/run/all")
async def run_all_agents(background_tasks: BackgroundTasks):
    """
    Executa todos os agentes em background.
    """
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator nao inicializado")

    # Executar em background
    background_tasks.add_task(orchestrator.run_all, parallel=True)

    return {
        "status": "started",
        "message": "Todos os agentes iniciados em background",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.post("/run/{agent_name}")
async def run_single_agent(agent_name: str, background_tasks: BackgroundTasks):
    """
    Executa um agente especifico.

    Agentes disponiveis:
    - ScoutAgent
    - TrendAgent
    - PatternAgent
    - BenchmarkAgent
    - CorrelationAgent
    - AdvisorAgent
    - RecyclerAgent
    - AlertAgent
    - ReportAgent
    """
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator nao inicializado")

    if agent_name not in orchestrator.agents:
        available = list(orchestrator.agents.keys())
        raise HTTPException(
            status_code=404,
            detail=f"Agente '{agent_name}' nao encontrado. Disponiveis: {available}"
        )

    # Executar em background
    background_tasks.add_task(orchestrator.run_single, agent_name)

    return {
        "status": "started",
        "agent": agent_name,
        "message": f"Agente {agent_name} iniciado em background",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.post("/run/analysis")
async def run_analysis_only(background_tasks: BackgroundTasks):
    """
    Executa apenas agentes de analise (rapido, sem Scout).
    """
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator nao inicializado")

    background_tasks.add_task(orchestrator.run_analysis_only)

    return {
        "status": "started",
        "message": "Analise iniciada em background (Trend, Pattern, Benchmark, Alert)",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# ========================================
# ENDPOINTS DE DADOS
# ========================================

@router.get("/data")
async def get_latest_data():
    """
    Retorna dados mais recentes de todos os agentes.
    """
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator nao inicializado")

    return orchestrator.get_latest_data()


@router.get("/data/{agent_name}")
async def get_agent_data(agent_name: str):
    """
    Retorna dados de um agente especifico.
    """
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator nao inicializado")

    if agent_name not in orchestrator.last_results:
        raise HTTPException(
            status_code=404,
            detail=f"Dados do agente '{agent_name}' nao encontrados. Execute o agente primeiro."
        )

    result = orchestrator.last_results[agent_name]

    return {
        "agent": agent_name,
        "success": result.success,
        "duration_seconds": result.duration_seconds,
        "data": result.data,
        "metrics": result.metrics,
        "errors": result.errors
    }


# ========================================
# ENDPOINTS DE RELATORIOS HTML
# ========================================

@router.get("/reports", response_class=HTMLResponse)
async def list_reports():
    """
    Lista relatorios disponiveis com links.
    """
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator nao inicializado")

    reports_dir = orchestrator.agents["ReportAgent"].output_dir

    # Listar arquivos HTML
    html_files = []
    if os.path.exists(reports_dir):
        html_files = [f for f in os.listdir(reports_dir) if f.endswith('.html')]

    # Gerar HTML de listagem
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Relatorios - Content Factory Intelligence</title>
        <style>
            body { font-family: sans-serif; background: #0d1117; color: #c9d1d9; padding: 40px; }
            h1 { color: #58a6ff; }
            a { color: #58a6ff; text-decoration: none; display: block; padding: 10px; }
            a:hover { background: #161b22; }
        </style>
    </head>
    <body>
        <h1>Relatorios Disponiveis</h1>
    """

    for f in html_files:
        html += f'<a href="/api/agents/reports/{f}">{f}</a>'

    html += """
    </body>
    </html>
    """

    return html


@router.get("/reports/{filename}", response_class=HTMLResponse)
async def get_report(filename: str):
    """
    Retorna um relatorio HTML especifico.
    """
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator nao inicializado")

    reports_dir = orchestrator.agents["ReportAgent"].output_dir
    file_path = os.path.join(reports_dir, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Relatorio '{filename}' nao encontrado")

    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


@router.get("/reports/json/latest")
async def get_latest_json():
    """
    Retorna dados JSON mais recentes dos agentes.
    """
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator nao inicializado")

    reports_dir = orchestrator.agents["ReportAgent"].output_dir
    json_path = os.path.join(reports_dir, "latest_data.json")

    if not os.path.exists(json_path):
        raise HTTPException(status_code=404, detail="Dados JSON nao encontrados. Execute os agentes primeiro.")

    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


# ========================================
# ENDPOINTS DO SCHEDULER
# ========================================

@router.post("/scheduler/start")
async def start_scheduler():
    """
    Inicia o scheduler automatico.
    """
    if not scheduler:
        raise HTTPException(status_code=500, detail="Scheduler nao inicializado")

    scheduler.start()

    return {
        "status": "started",
        "message": "Scheduler iniciado",
        "jobs": scheduler.jobs
    }


@router.post("/scheduler/stop")
async def stop_scheduler():
    """
    Para o scheduler automatico.
    """
    if not scheduler:
        raise HTTPException(status_code=500, detail="Scheduler nao inicializado")

    scheduler.stop()

    return {
        "status": "stopped",
        "message": "Scheduler parado"
    }


# ========================================
# ENDPOINTS DE INSIGHTS RAPIDOS
# ========================================

@router.get("/insights/trending")
async def get_trending_insights():
    """
    Retorna resumo rapido de tendencias.
    """
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator nao inicializado")

    if "TrendAgent" not in orchestrator.last_results:
        raise HTTPException(status_code=404, detail="Dados de tendencias nao disponiveis. Execute o TrendAgent.")

    result = orchestrator.last_results["TrendAgent"]

    return {
        "trending_videos": result.data.get("trending_videos", [])[:10],
        "trending_topics": result.data.get("trending_topics", [])[:10],
        "generated_at": result.completed_at.isoformat() if result.completed_at else None
    }


@router.get("/insights/recommendations")
async def get_recommendations_insights():
    """
    Retorna recomendacoes priorizadas.
    """
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator nao inicializado")

    if "AdvisorAgent" not in orchestrator.last_results:
        raise HTTPException(status_code=404, detail="Dados de recomendacoes nao disponiveis. Execute o AdvisorAgent.")

    result = orchestrator.last_results["AdvisorAgent"]

    return {
        "top_recommendations": result.data.get("top_recommendations", [])[:15],
        "global_recommendations": result.data.get("global_recommendations", [])[:10],
        "executive_summary": result.data.get("executive_summary", {}),
        "generated_at": result.completed_at.isoformat() if result.completed_at else None
    }


@router.get("/insights/alerts")
async def get_alerts_insights():
    """
    Retorna alertas ativos.
    """
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator nao inicializado")

    if "AlertAgent" not in orchestrator.last_results:
        raise HTTPException(status_code=404, detail="Dados de alertas nao disponiveis. Execute o AlertAgent.")

    result = orchestrator.last_results["AlertAgent"]
    by_priority = result.data.get("by_priority", {})

    return {
        "critical": by_priority.get("critical", []),
        "high": by_priority.get("high", []),
        "medium": by_priority.get("medium", [])[:10],
        "total_alerts": result.data.get("alerts", []),
        "generated_at": result.completed_at.isoformat() if result.completed_at else None
    }


@router.get("/insights/opportunities")
async def get_opportunities_insights():
    """
    Retorna oportunidades identificadas.
    """
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator nao inicializado")

    correlation = orchestrator.last_results.get("CorrelationAgent")
    recycler = orchestrator.last_results.get("RecyclerAgent")

    opportunities = {
        "cross_language": [],
        "recycle": [],
        "generated_at": None
    }

    if correlation:
        opportunities["cross_language"] = correlation.data.get("cross_language_opportunities", [])[:15]
        opportunities["generated_at"] = correlation.completed_at.isoformat() if correlation.completed_at else None

    if recycler:
        opportunities["recycle"] = recycler.data.get("recycle_plan", [])[:15]

    return opportunities


# ========================================
# ENDPOINTS DE AI AGENTS (GPT-4 Mini)
# ========================================

@router.get("/ai/briefing")
async def get_ai_briefing():
    """
    Retorna briefing diario gerado por IA (GPT-4 Mini).
    """
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator nao inicializado")

    if "AIAdvisorAgent" not in orchestrator.agents:
        raise HTTPException(status_code=404, detail="AI Advisor nao disponivel. Configure OPENAI_API_KEY.")

    if "AIAdvisorAgent" not in orchestrator.last_results:
        raise HTTPException(status_code=404, detail="Dados do AI Advisor nao disponiveis. Execute o AIAdvisorAgent.")

    result = orchestrator.last_results["AIAdvisorAgent"]

    return {
        "daily_briefing": result.data.get("daily_briefing", ""),
        "viral_analysis": result.data.get("viral_analysis", []),
        "strategic_recommendations": result.data.get("strategic_recommendations", []),
        "generated_at": result.completed_at.isoformat() if result.completed_at else None
    }


@router.get("/ai/titles")
async def get_ai_titles():
    """
    Retorna banco de titulos gerados por IA (GPT-4 Mini).
    """
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator nao inicializado")

    if "AITitleAgent" not in orchestrator.agents:
        raise HTTPException(status_code=404, detail="AI Title Agent nao disponivel. Configure OPENAI_API_KEY.")

    if "AITitleAgent" not in orchestrator.last_results:
        raise HTTPException(status_code=404, detail="Dados do AI Title Agent nao disponiveis. Execute o AITitleAgent.")

    result = orchestrator.last_results["AITitleAgent"]

    return {
        "title_bank": result.data.get("title_bank", {}),
        "patterns_by_subnicho": result.data.get("patterns_by_subnicho", {}),
        "recommended_structures": result.data.get("recommended_structures", []),
        "generated_at": result.completed_at.isoformat() if result.completed_at else None
    }


@router.post("/ai/generate-titles")
async def generate_titles_on_demand(
    topic: str,
    subnicho: str,
    lingua: str = "portuguese",
    count: int = 10
):
    """
    Gera titulos sob demanda para um topico especifico.

    Args:
        topic: Tema do video (ex: "rei que comeu a familia")
        subnicho: Subnicho do canal (ex: "Reis Perversos")
        lingua: Idioma (ex: "spanish", "english", "portuguese")
        count: Quantidade de titulos (max 20)
    """
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator nao inicializado")

    if "AITitleAgent" not in orchestrator.agents:
        raise HTTPException(status_code=404, detail="AI Title Agent nao disponivel. Configure OPENAI_API_KEY.")

    # Limitar count
    count = min(count, 20)

    # Gerar titulos
    ai_title = orchestrator.agents["AITitleAgent"]
    titles = await ai_title.generate_titles_for_topic(topic, subnicho, lingua, count)

    return {
        "topic": topic,
        "subnicho": subnicho,
        "lingua": lingua,
        "titles": titles,
        "count": len(titles),
        "generated_at": datetime.now(timezone.utc).isoformat()
    }


@router.post("/ai/adapt-title")
async def adapt_title_language(
    original_title: str,
    source_lang: str,
    target_lang: str,
    subnicho: str
):
    """
    Adapta um titulo de sucesso para outro idioma.

    Args:
        original_title: Titulo original que funcionou
        source_lang: Idioma original (ex: "english")
        target_lang: Idioma destino (ex: "spanish")
        subnicho: Subnicho do conteudo
    """
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator nao inicializado")

    if "AITitleAgent" not in orchestrator.agents:
        raise HTTPException(status_code=404, detail="AI Title Agent nao disponivel. Configure OPENAI_API_KEY.")

    # Adaptar titulo
    ai_title = orchestrator.agents["AITitleAgent"]
    adaptations = await ai_title.adapt_title_to_language(
        original_title, source_lang, target_lang, subnicho
    )

    return {
        "original_title": original_title,
        "source_lang": source_lang,
        "target_lang": target_lang,
        "subnicho": subnicho,
        "adaptations": adaptations,
        "count": len(adaptations),
        "generated_at": datetime.now(timezone.utc).isoformat()
    }

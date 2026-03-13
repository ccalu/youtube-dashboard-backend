"""Gera HTML com output EXATO dos 5 agentes - Cronicas da Coroa"""
import json
import html

with open(r"D:\ContentFactory\youtube-dashboard-backend\_runtime\agent_reports.json", "r", encoding="utf-8") as f:
    data = json.load(f)

agents = [
    {
        "key": "Agente 1 — Estrutura de Copy",
        "num": "1",
        "name": "Agente 1 — Estrutura de Copy",
        "camada": "Camada 1 (Diagnostico)",
        "desc": "Analisa qual estrutura de copy (A-G) performa melhor em retencao e watch time. Dados: planilha de copy + YouTube Analytics API (retencao, watch time).",
        "color": "#3b82f6",
        "summary_items": lambda d: [
            ("Videos", str(d.get("total_videos", "?"))),
            ("Metrica", "Retencao %"),
            ("Fonte", "Planilha Copy + Analytics API"),
        ],
    },
    {
        "key": "Agente 2 — Autenticidade",
        "num": "2",
        "name": "Agente 2 — Autenticidade",
        "camada": "Camada 1 (Diagnostico)",
        "desc": "Avalia risco de 'Inauthentic Content' do YouTube. Score 0-100, diagnostico LLM com recomendacoes. Dados: planilha de copy (estruturas) + titulos dos videos.",
        "color": "#22c55e",
        "summary_items": lambda d: [
            ("Videos", str(d.get("total_videos", "?"))),
            ("Score", f'{d.get("score", "?")}'),
            ("Nivel", d.get("level", "?").upper()),
            ("Metrica", "Diversidade"),
        ],
    },
    {
        "key": "Agente 3 — Micronichos",
        "num": "3",
        "name": "Agente 3 — Micronichos",
        "camada": "Camada 2 (Analise Especializada)",
        "desc": "Classifica videos em subcategorias tematicas (micronichos) via LLM (GPT-4o-mini, 2 calls). Ranqueia por views brutas. Dados: videos_historico (Supabase).",
        "color": "#a855f7",
        "summary_items": lambda d: [
            ("Videos", str(d.get("total_videos", "?"))),
            ("Micronichos", str(d.get("count", "?"))),
            ("Metrica", "Views Brutas"),
            ("LLM", "GPT-4o-mini (2 calls)"),
        ],
    },
    {
        "key": "Agente 4 — Estrutura de Titulo",
        "num": "4",
        "name": "Agente 4 — Estrutura de Titulo",
        "camada": "Camada 2 (Analise Especializada)",
        "desc": "Identifica padroes estruturais de titulos que geram CTR. Classifica formulas via LLM e ranqueia por score (60% CTR + 40% views). Dados: videos_historico + yt_video_metrics (CTR).",
        "color": "#eab308",
        "summary_items": lambda d: [
            ("Videos", str(d.get("total_videos", "?"))),
            ("Estruturas", str(d.get("count", "?"))),
            ("Metrica", "CTR + Views"),
            ("LLM", "GPT-4o-mini (2 calls)"),
        ],
    },
    {
        "key": "Agente 5 — Temas",
        "num": "5",
        "name": "Agente 5 — Temas",
        "camada": "Camada 2 (Analise Especializada)",
        "desc": "Identifica TEMAS especificos que viralizam (ultimo nivel da hierarquia). Score = 50% velocity + 50% views. Decompoe em elementos constitutivos + hipoteses de adjacencia. Dados: videos_historico (Supabase).",
        "color": "#f97316",
        "summary_items": lambda d: [
            ("Videos", str(d.get("total_videos", "?"))),
            ("Temas", str(d.get("count", "?"))),
            ("Metrica", "Velocity + Views"),
            ("LLM", "GPT-4o-mini (2 calls)"),
        ],
    },
]

# Build HTML
parts = []
parts.append("""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Output 5 Agentes — Cronicas da Coroa</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: #0f0f0f;
    color: #e0e0e0;
    font-family: 'Segoe UI', system-ui, sans-serif;
    padding: 40px 20px;
    line-height: 1.6;
  }
  .container { max-width: 1100px; margin: 0 auto; }
  .header {
    text-align: center;
    margin-bottom: 50px;
    padding: 30px;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border-radius: 16px;
    border: 1px solid #2a2a4a;
  }
  .header h1 { font-size: 28px; color: #fff; margin-bottom: 8px; }
  .header .subtitle { color: #8b8ba0; font-size: 14px; }
  .header .channel-name { color: #a78bfa; font-size: 20px; font-weight: 600; margin: 10px 0; }
  .header .channel-id { color: #666; font-size: 12px; font-family: monospace; }
  .hierarchy {
    background: #1a1a2e;
    border: 1px solid #2a2a4a;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 40px;
  }
  .hierarchy h3 { color: #a78bfa; margin-bottom: 12px; font-size: 16px; }
  .hierarchy-flow {
    display: flex; align-items: center; justify-content: center;
    gap: 8px; flex-wrap: wrap; font-size: 13px;
  }
  .hierarchy-item { padding: 8px 16px; border-radius: 8px; font-weight: 600; }
  .hierarchy-arrow { color: #555; font-size: 18px; }
  .h-nicho { background: #1e3a5f; color: #60a5fa; }
  .h-subnicho { background: #1e3a2e; color: #4ade80; }
  .h-micronicho { background: #3b1e5f; color: #c084fc; }
  .h-tema { background: #5f3b1e; color: #fb923c; }
  .agent-card {
    background: #1a1a1a;
    border-radius: 16px;
    margin-bottom: 30px;
    overflow: hidden;
    border: 1px solid #2a2a2a;
  }
  .agent-header {
    padding: 20px 24px;
    display: flex; align-items: center; gap: 16px;
  }
  .agent-badge {
    width: 48px; height: 48px; border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px; font-weight: 800; color: #fff; flex-shrink: 0;
  }
  .agent-info { flex: 1; }
  .agent-name { font-size: 18px; font-weight: 700; color: #fff; }
  .agent-meta { font-size: 12px; color: #888; margin-top: 2px; }
  .agent-desc { font-size: 13px; color: #aaa; margin-top: 4px; }
  .summary-row { display: flex; gap: 12px; padding: 0 24px 16px; flex-wrap: wrap; }
  .summary-card { background: #252525; border-radius: 8px; padding: 10px 16px; min-width: 120px; }
  .summary-label { font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; }
  .summary-value { font-size: 16px; font-weight: 700; color: #fff; margin-top: 2px; }
  .report-content { padding: 0 24px 24px; }
  .report-text {
    background: #111; border: 1px solid #222; border-radius: 8px;
    padding: 20px;
    font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
    font-size: 12px; line-height: 1.7;
    white-space: pre-wrap; word-wrap: break-word;
    color: #ccc;
    max-height: 800px; overflow-y: auto;
  }
  .report-text::-webkit-scrollbar { width: 6px; }
  .report-text::-webkit-scrollbar-track { background: #111; }
  .report-text::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }
  .note-section {
    background: #1a2332; border: 1px solid #2a3a5a;
    border-radius: 12px; padding: 24px; margin-top: 40px;
  }
  .note-section h3 { color: #60a5fa; margin-bottom: 10px; }
  .note-section p { color: #8ba4c4; font-size: 14px; }
  .note-section ul { margin-top: 10px; padding-left: 20px; }
  .note-section li { color: #8ba4c4; font-size: 13px; margin-bottom: 6px; }
  .footer {
    text-align: center; margin-top: 40px; padding: 20px;
    color: #555; font-size: 12px;
  }
</style>
</head>
<body>
<div class="container">

  <div class="header">
    <h1>Output dos 5 Agentes de Analise</h1>
    <div class="channel-name">Cronicas da Coroa</div>
    <div class="channel-id">UC51z3LFFGP6xaOhlWerIgSQ</div>
    <div class="subtitle">Gerado em 02/03/2026 — Teste E2E completo com LLM (GPT-4o-mini)</div>
  </div>

  <div class="hierarchy">
    <h3>Hierarquia de Classificacao</h3>
    <div class="hierarchy-flow">
      <span class="hierarchy-item h-nicho">Nicho</span>
      <span class="hierarchy-arrow">&#8594;</span>
      <span class="hierarchy-item h-subnicho">Subnicho</span>
      <span class="hierarchy-arrow">&#8594;</span>
      <span class="hierarchy-item h-micronicho">Micronicho (Ag.3)</span>
      <span class="hierarchy-arrow">&#8594;</span>
      <span class="hierarchy-item h-tema">Tema (Ag.5)</span>
    </div>
    <p style="text-align:center; color:#888; font-size:12px; margin-top:10px;">
      Nicho = "Historia Sombria" | Subnicho = "Cronicas da Coroa" | Micronicho = categoria tematica | Tema = assunto concreto de 1 video
    </p>
  </div>
""")

for agent in agents:
    agent_data = data.get(agent["key"], {})
    report_text = agent_data.get("report_text", "Sem dados")
    run_date = agent_data.get("run_date", "?")
    color = agent["color"]

    # Summary items
    summary_items = agent["summary_items"](agent_data)

    # Escape HTML in report text
    escaped_report = html.escape(report_text)

    parts.append(f"""
  <div class="agent-card" style="border-left: 4px solid {color};">
    <div class="agent-header">
      <div class="agent-badge" style="background: {color};">{agent["num"]}</div>
      <div class="agent-info">
        <div class="agent-name">{html.escape(agent["name"])}</div>
        <div class="agent-meta">{html.escape(agent["camada"])} &bull; {html.escape(str(run_date)[:19].replace("T", " "))} UTC</div>
        <div class="agent-desc">{html.escape(agent["desc"])}</div>
      </div>
    </div>
    <div class="summary-row">""")

    for label, value in summary_items:
        parts.append(f"""
      <div class="summary-card">
        <div class="summary-label">{html.escape(label)}</div>
        <div class="summary-value">{html.escape(value)}</div>
      </div>""")

    parts.append(f"""
    </div>
    <div class="report-content">
      <div class="report-text">{escaped_report}</div>
    </div>
  </div>
""")

# Note for Agent 6
parts.append("""
  <div class="note-section">
    <h3>Nota para Construcao do Agente 6 (Recomendador de Conteudo)</h3>
    <p>O Agente 6 deve cruzar os outputs de TODOS os agentes acima para gerar a lista final de proximos videos recomendados.</p>
    <ul>
      <li><strong>Ag.1 (Copy)</strong> — Qual estrutura de copy (A-G) usar no proximo video? Baseado em retencao e watch time</li>
      <li><strong>Ag.2 (Autenticidade)</strong> — Score de seguranca. Se abaixo de 70, forcar diversificacao. Se acima de 90, pode repetir padroes com seguranca</li>
      <li><strong>Ag.3 (Micronichos)</strong> — Em qual micronicho produzir? Escalar os tops, testar os com 1 video, pausar os fracos</li>
      <li><strong>Ag.4 (Estrutura de Titulo)</strong> — Qual formula de titulo usar? Escalar os top scores, pausar os bottom performers</li>
      <li><strong>Ag.5 (Temas)</strong> — Qual tema concreto? Elementos constitutivos (opressao, brutalidade, vitimizacao) + hipoteses de adjacencia para gerar NOVOS temas</li>
    </ul>
    <p style="margin-top: 15px; color: #60a5fa;">
      <strong>Output esperado do Ag.6:</strong> Lista ordenada de 5-10 videos recomendados, cada um com: titulo sugerido, estrutura de copy, micronicho, tema, score de confianca, e justificativa cruzando os 5 agentes.
    </p>
  </div>

  <div class="footer">
    Dark YouTube Channels — Sistema de Agentes v2 &bull; Gerado automaticamente via API
  </div>

</div>
</body>
</html>""")

output_path = r"D:\ContentFactory\youtube-dashboard-backend\_runtime\output_5_agentes_cronicas_da_coroa.html"
with open(output_path, "w", encoding="utf-8") as f:
    f.write("".join(parts))

print(f"HTML gerado: {output_path}")
print(f"Tamanho: {len(''.join(parts)):,} chars")

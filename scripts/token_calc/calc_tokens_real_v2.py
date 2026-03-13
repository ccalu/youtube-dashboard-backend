"""
Calcula tokens REAIS baseado nos:
- System prompts: extraidos diretamente do codigo fonte
- User prompts: reconstruidos com dados reais do Cronicas da Coroa
- Outputs LLM: extraidos do report_text salvo no banco (teste E2E de 02/03/2026)

Usa tiktoken (o200k_base) = mesmo tokenizer do GPT-4o-mini
"""
import tiktoken
import json
import re
import os

enc = tiktoken.encoding_for_model("gpt-4o-mini")

def count_tokens(text):
    if not text:
        return 0
    return len(enc.encode(text))

def extract_between(content, start_marker, end_marker, search_from=0):
    """Extract text between markers"""
    idx = content.find(start_marker, search_from)
    if idx == -1:
        return None, -1
    start = idx + len(start_marker)
    end = content.find(end_marker, start)
    if end == -1:
        return None, -1
    return content[start:end], end

# ============================================================
# Read agent source files
# ============================================================
BASE = r"D:\ContentFactory\youtube-dashboard-backend"

with open(os.path.join(BASE, "copy_analysis_agent.py"), "r", encoding="utf-8") as f:
    src_ag1 = f.read()
with open(os.path.join(BASE, "authenticity_agent.py"), "r", encoding="utf-8") as f:
    src_ag2 = f.read()
with open(os.path.join(BASE, "micronicho_agent.py"), "r", encoding="utf-8") as f:
    src_ag3 = f.read()
with open(os.path.join(BASE, "title_structure_agent.py"), "r", encoding="utf-8") as f:
    src_ag4 = f.read()
with open(os.path.join(BASE, "theme_agent.py"), "r", encoding="utf-8") as f:
    src_ag5 = f.read()

# Read real outputs
with open(os.path.join(BASE, "_runtime", "agent_reports.json"), "r", encoding="utf-8") as f:
    reports = json.load(f)

# ============================================================
# Extract SYSTEM PROMPTS (fixed text from source code)
# ============================================================
def extract_system_prompt(source, nth=1):
    """Extract the nth system_prompt triple-quoted string"""
    pattern = r'system_prompt\s*=\s*"""(.*?)"""'
    matches = list(re.finditer(pattern, source, re.DOTALL))
    if len(matches) >= nth:
        return matches[nth-1].group(1)
    return ""

# Ag.1 - 1 call
ag1_sys = extract_system_prompt(src_ag1, 1)

# Ag.2 - 1 call
ag2_sys = extract_system_prompt(src_ag2, 1)

# Ag.3 - 2 calls
ag3_sys_c1 = extract_system_prompt(src_ag3, 1)  # classification
ag3_sys_c2 = extract_system_prompt(src_ag3, 2)  # narrative

# Ag.4 - 2 calls
ag4_sys_c1 = extract_system_prompt(src_ag4, 1)  # classification
ag4_sys_c2 = extract_system_prompt(src_ag4, 2)  # narrative

# Ag.5 - 2 calls
ag5_sys_c1 = extract_system_prompt(src_ag5, 1)  # extraction
ag5_sys_c2 = extract_system_prompt(src_ag5, 2)  # decomposition

# ============================================================
# Extract USER PROMPT templates (to estimate dynamic part)
# ============================================================
def extract_user_prompt(source, nth=1):
    """Extract the nth user_prompt f-string template"""
    pattern = r'user_prompt\s*=\s*f"""(.*?)"""'
    matches = list(re.finditer(pattern, source, re.DOTALL))
    if len(matches) >= nth:
        return matches[nth-1].group(1)
    return ""

ag1_usr_template = extract_user_prompt(src_ag1, 1)
ag2_usr_template = extract_user_prompt(src_ag2, 1)
ag3_usr_c1_template = extract_user_prompt(src_ag3, 1)
ag3_usr_c2_template = extract_user_prompt(src_ag3, 2)
ag4_usr_c1_template = extract_user_prompt(src_ag4, 1)
ag4_usr_c2_template = extract_user_prompt(src_ag4, 2)
ag5_usr_c1_template = extract_user_prompt(src_ag5, 1)
ag5_usr_c2_template = extract_user_prompt(src_ag5, 2)

# ============================================================
# REAL OUTPUT (from saved reports - what LLM actually generated)
# We need to extract ONLY the LLM-generated parts from report_text.
#
# Ag.1: LLM generates [OBSERVACOES] + [TENDENCIAS] sections
# Ag.2: LLM generates [DIAGNOSTICO] + [RECOMENDACOES] + [TENDENCIAS]
# Ag.3 Call 1: JSON classification output
# Ag.3 Call 2: [OBSERVACOES] + [RECOMENDACOES] + [TENDENCIAS]
# Ag.4 Call 1: JSON classification output
# Ag.4 Call 2: [OBSERVACOES] + [RECOMENDACOES] + [TENDENCIAS]
# Ag.5 Call 1: JSON theme extraction output
# Ag.5 Call 2: [RANKING] + [DECOMPOSICAO] + [PADROES]
# ============================================================

# For outputs, we use the full report_text as a proxy since
# the LLM-generated narrative is the bulk of it
ag1_report = reports["Agente 1 \u2014 Estrutura de Copy"]["report_text"]
ag2_report = reports["Agente 2 \u2014 Autenticidade"]["report_text"]
ag3_report = reports["Agente 3 \u2014 Micronichos"]["report_text"]
ag4_report = reports["Agente 4 \u2014 Estrutura de Titulo"]["report_text"]
ag5_report = reports["Agente 5 \u2014 Temas"]["report_text"]

# For Ag.1: LLM only generates the OBSERVACOES + TENDENCIAS sections
# The ranking table is code-generated. Extract LLM part:
def extract_llm_section(report, start_marker, end_marker="============"):
    idx = report.find(start_marker)
    if idx == -1:
        return ""
    end = report.find(end_marker, idx + len(start_marker))
    if end == -1:
        return report[idx:]
    return report[idx:end]

# Ag.1 LLM output (from "--- OBSERVACOES ---" or similar to end)
# Actually Ag.1 doesn't have clear LLM sections in this case (insufficient data)
# The report_text IS the full report including code-generated parts
# Since we can't separate, we estimate LLM output conservatively
ag1_llm_out = ""  # No LLM output in this run (insufficient data, no OBSERVACOES section)

# Ag.2 LLM output
ag2_llm_out = extract_llm_section(ag2_report, "--- DIAGNOSTICO ---")

# Ag.3 LLM output (Call 2 = narrative sections)
ag3_llm_c2_out = extract_llm_section(ag3_report, "--- OBSERVACOES ---")

# Ag.4 LLM output (Call 2 = narrative sections)
ag4_llm_c2_out = extract_llm_section(ag4_report, "--- OBSERVACOES ---")

# Ag.5 LLM output (Call 2 = 3 sections)
ag5_llm_c2_out = extract_llm_section(ag5_report, "--- RANKING ---") or extract_llm_section(ag5_report, "--- DECOMPOSICAO ---")

# For Call 1 outputs (JSON) we estimate based on video count
# Cronicas da Coroa: 9 videos analyzed
# Each JSON entry ~ 50-80 tokens
n_videos = 9
ag3_llm_c1_out_est = n_videos * 65  # ~65 tokens per video classification
ag4_llm_c1_out_est = n_videos * 75  # ~75 tokens per title structure classification
ag5_llm_c1_out_est = n_videos * 55  # ~55 tokens per theme extraction

# ============================================================
# TOKEN COUNTS
# ============================================================
print("=" * 80)
print("TOKENS REAIS — 5 Agentes x Cronicas da Coroa (tiktoken o200k_base)")
print("Canal: Cronicas da Coroa | UC51z3LFFGP6xaOhlWerIgSQ")
print("Data do teste: 02/03/2026 | Videos analisados: 9 (Ag3-5), 6 (Ag1), 27 (Ag2)")
print("=" * 80)

# Build results table
results = []

# ---- AGENTE 1 (1 call) ----
ag1_sys_tok = count_tokens(ag1_sys)
ag1_usr_tok = count_tokens(ag1_usr_template)
ag1_out_tok = count_tokens(ag1_llm_out) if ag1_llm_out else 0
# Note: Ag.1 had insufficient data, so LLM may not have been called
# But it IS called — it just doesn't have OBSERVACOES sections when data is insufficient
# Let's check if there's any LLM section
has_ag1_llm = "OBSERVACOES" in ag1_report or "TENDENCIAS" in ag1_report
ag1_note = "(sem LLM neste run — dados insuf.)" if not has_ag1_llm else ""
results.append({
    "agent": "Ag.1 Copy",
    "calls": 1,
    "sys_tok": ag1_sys_tok,
    "usr_template_tok": ag1_usr_tok,
    "output_tok": ag1_out_tok,
    "note": ag1_note,
})

# ---- AGENTE 2 (1 call) ----
ag2_sys_tok = count_tokens(ag2_sys)
ag2_usr_tok = count_tokens(ag2_usr_template)
ag2_out_tok = count_tokens(ag2_llm_out)
results.append({
    "agent": "Ag.2 Autenticidade",
    "calls": 1,
    "sys_tok": ag2_sys_tok,
    "usr_template_tok": ag2_usr_tok,
    "output_tok": ag2_out_tok,
    "note": "",
})

# ---- AGENTE 3 (2 calls) ----
ag3_c1_sys_tok = count_tokens(ag3_sys_c1)
ag3_c1_usr_tok = count_tokens(ag3_usr_c1_template)
ag3_c2_sys_tok = count_tokens(ag3_sys_c2)
ag3_c2_usr_tok = count_tokens(ag3_usr_c2_template)
ag3_c2_out_tok = count_tokens(ag3_llm_c2_out)
results.append({
    "agent": "Ag.3 Micronichos C1",
    "calls": "1/2",
    "sys_tok": ag3_c1_sys_tok,
    "usr_template_tok": ag3_c1_usr_tok,
    "output_tok": ag3_llm_c1_out_est,
    "note": "(JSON, output estimado)",
})
results.append({
    "agent": "Ag.3 Micronichos C2",
    "calls": "2/2",
    "sys_tok": ag3_c2_sys_tok,
    "usr_template_tok": ag3_c2_usr_tok,
    "output_tok": ag3_c2_out_tok,
    "note": "(narrativa REAL)",
})

# ---- AGENTE 4 (2 calls) ----
ag4_c1_sys_tok = count_tokens(ag4_sys_c1)
ag4_c1_usr_tok = count_tokens(ag4_usr_c1_template)
ag4_c2_sys_tok = count_tokens(ag4_sys_c2)
ag4_c2_usr_tok = count_tokens(ag4_usr_c2_template)
ag4_c2_out_tok = count_tokens(ag4_llm_c2_out)
results.append({
    "agent": "Ag.4 Titulo C1",
    "calls": "1/2",
    "sys_tok": ag4_c1_sys_tok,
    "usr_template_tok": ag4_c1_usr_tok,
    "output_tok": ag4_llm_c1_out_est,
    "note": "(JSON, output estimado)",
})
results.append({
    "agent": "Ag.4 Titulo C2",
    "calls": "2/2",
    "sys_tok": ag4_c2_sys_tok,
    "usr_template_tok": ag4_c2_usr_tok,
    "output_tok": ag4_c2_out_tok,
    "note": "(narrativa REAL)",
})

# ---- AGENTE 5 (2 calls) ----
ag5_c1_sys_tok = count_tokens(ag5_sys_c1)
ag5_c1_usr_tok = count_tokens(ag5_usr_c1_template)
ag5_c2_sys_tok = count_tokens(ag5_sys_c2)
ag5_c2_usr_tok = count_tokens(ag5_usr_c2_template)
ag5_c2_out_tok = count_tokens(ag5_llm_c2_out)
results.append({
    "agent": "Ag.5 Temas C1",
    "calls": "1/2",
    "sys_tok": ag5_c1_sys_tok,
    "usr_template_tok": ag5_c1_usr_tok,
    "output_tok": ag5_llm_c1_out_est,
    "note": "(JSON, output estimado)",
})
results.append({
    "agent": "Ag.5 Temas C2",
    "calls": "2/2",
    "sys_tok": ag5_c2_sys_tok,
    "usr_template_tok": ag5_c2_usr_tok,
    "output_tok": ag5_c2_out_tok,
    "note": "(narrativa REAL)",
})

# ============================================================
# PRINT
# ============================================================
print()
print(f"  {'Componente':<24} {'SysPrompt':>10} {'UsrTemplate':>12} {'Output':>10} {'Nota'}")
print("  " + "-" * 85)

grand_sys = 0
grand_usr = 0
grand_out = 0

for r in results:
    s = r["sys_tok"]
    u = r["usr_template_tok"]
    o = r["output_tok"]
    grand_sys += s
    grand_usr += u
    grand_out += o
    print(f"  {r['agent']:<24} {s:>10,} {u:>12,} {o:>10,}  {r['note']}")

print("  " + "-" * 85)
grand_total = grand_sys + grand_usr + grand_out
print(f"  {'TOTAL':<24} {grand_sys:>10,} {grand_usr:>12,} {grand_out:>10,}")
print(f"  {'GRAND TOTAL':>48} = {grand_total:>10,} tokens")

# ============================================================
# IMPORTANT NOTE about user prompt templates
# ============================================================
print()
print("=" * 80)
print("NOTA IMPORTANTE: User prompts acima sao TEMPLATES (parte fixa)")
print("Os dados dinamicos (titulos, rankings, report anterior) adicionam mais tokens.")
print("Vou calcular a parte dinamica com dados reais do Cronicas da Coroa:")
print("=" * 80)
print()

# Simulate the dynamic data that gets injected into user prompts
# Using real data from the test

# 9 video titles from Cronicas da Coroa (real titles from the theme report)
real_titles = [
    "Os Espetaculos de Tortura Publica Mais Horripilantes da Historia",
    "As 16 Freiras que Cantaram a Caminho da Guilhotina",
    "O Que Imperadores Chineses Faziam Com Suas Concubinas Quando Cansavam Delas",
    "O que os Piratas da Barbaria Faziam com as Mulheres Capturadas",
    "Elizabeth Bathory: A Condessa que Se Banhava no Sangue de Jovens",
    "O que os Mongois Fizeram com a Dinastia Real de Bagda",
    "Por Que as Filhas dos Reis Derrotados Imploravam pela Morte",
    "O Dia Mais Sombrio da Historia de Zhongdu: Os Mongois",
    "Os Ultimos Dias de Cleopatra Foram Piores do que Voce Imagina",
]

# Titles block (used by Ag.3 C1, Ag.4 C1, Ag.5 C1)
titles_block = "\n".join(f"{i+1}. {t}" for i, t in enumerate(real_titles))
titles_tok = count_tokens(titles_block)
print(f"  Bloco de {len(real_titles)} titulos:           {titles_tok:>6,} tokens")

# Previous report block (used by all Call 2s)
# Using actual Ag.3 report as example of previous report size
prev_report_tok = count_tokens(ag3_report)
print(f"  Report anterior (Ag.3 ex):     {prev_report_tok:>6,} tokens")

# Ranking table (used by Ag.3 C2, Ag.4 C2, Ag.5 C2)
# Reconstruct from real data
ranking_ag3 = """    #  Micronicho                     Videos   Avg Views   Total Views        Melhor (idade)          Pior (idade)
  ---  ------------------------------ ------  ----------  ------------  --------------------  --------------------
    1  Crimes Historicos                   8         429          3.4K            2.4K (13d)              20 (12d)
    2  Serial Killers                      1          84            84               84 (9d)               84 (9d)"""
ranking_ag3_tok = count_tokens(ranking_ag3)
print(f"  Ranking table (Ag.3):           {ranking_ag3_tok:>6,} tokens")

ranking_ag4 = """    #  Codigo   Formula                                  Vids   CTR Avg   Views Avg  Score
  ---  -------- ---------------------------------------- ----  --------  ----------  -----
    1  EST-03   Os [ADJETIVO] [CATEGORIA] [SUJEITO] Q...    1      5.7%        2.4K   95.5
    2  EST-04   Por Que [SUJEITO] [ACAO] Antes Que [S...    1      5.9%          28   60.1
    3  EST-02   O [ADJETIVO] [PERIODO] da Historia de...    1      5.6%          24   52.0
    4  EST-01   O Que [SUJEITO] Faziam Com [OBJETO] F...    4      3.5%         119   11.5
    5  EST-05   [FIGURA] que [ACAO] no [OBJETO] de [N...    2      3.1%         308    4.8"""
ranking_ag4_tok = count_tokens(ranking_ag4)
print(f"  Ranking table (Ag.4):           {ranking_ag4_tok:>6,} tokens")

ranking_ag5 = """  #  Tema                                              Views    Velocity  Score  Titulo Original
---  -----                                             -----    --------  -----  ---------------
  1  Os metodos de tortura publica                      2.4K       183/d    100  Os Espetaculos de Tortura...
  2  A execucao das 16 freiras                           533        33/d     20  As 16 Freiras que Cantaram...
  3  Concubinas de imperadores chineses                  261        16/d      9  O Que Imperadores Chineses...
  4  Piratas da Barbaria contra mulheres                 124         8/d      4  O que os Piratas...
  5  Elizabeth Bathory                                     84         9/d      4  Elizabeth Bathory...
  6  Dinastia real de Bagda                               73         7/d      3  O que os Mongois...
  7  Filhas de reis derrotados                            28         2/d      0  Por Que as Filhas...
  8  Palacio real Zhongdu                                 24         2/d      0  O Dia Mais Sombrio...
  9  Ultimos dias de Cleopatra                            20         2/d      0  Os Ultimos Dias..."""
ranking_ag5_tok = count_tokens(ranking_ag5)
print(f"  Ranking table (Ag.5):           {ranking_ag5_tok:>6,} tokens")

# Patterns block
patterns_sample = """Concentracao top 3: 100.0%\nMedia geral de views: 391\nMicronichos de 1 video: Serial Killers (84 views)"""
patterns_tok = count_tokens(patterns_sample)
print(f"  Patterns block:                 {patterns_tok:>6,} tokens")

# Previous micronichos/themes/structures list
prev_list = "Micronichos anteriores: Crimes Historicos"
prev_list_tok = count_tokens(prev_list)
print(f"  Lista anterior (prev memory):   {prev_list_tok:>6,} tokens")

# Copy data block (Ag.1 specific - structure performance data)
# Ag.1 has more complex data with retention, watch time per video
copy_data = """CANAL: Cronicas da Coroa | Total videos: 6 | Media geral: 27.4% retencao | 7.6 min watch time | 43 views

Estrutura A: 1 video
  "Os Espetaculos de Tortura..." | ret: 37.9% | watch: 11.2min | views: 2,400

Estrutura B: 1 video
  "As 16 Freiras..." | ret: 12.8% | watch: 3.8min | views: 533

Estrutura C: 1 video
  "O Que Imperadores Chineses..." | ret: 29.1% | watch: 8.6min | views: 261

Estrutura D: 1 video
  "O que os Piratas..." | ret: 34.1% | watch: 10.1min | views: 124

Estrutura E: 2 videos
  "Elizabeth Bathory..." | ret: 28.5% | watch: 8.4min | views: 84
  "O que os Mongois..." | ret: 21.7% | watch: 6.4min | views: 73"""
copy_data_tok = count_tokens(copy_data)
print(f"  Copy data block (Ag.1):         {copy_data_tok:>6,} tokens")

# Auth data block (Ag.2 specific)
auth_data = """CANAL: Cronicas da Coroa | Subnicho: Monetizados | Lingua: Frances
Score: 98.1/100 | Level: excelente

FATOR 1 - Estruturas (99.2/100):
Distribuicao: A=22% B=19% C=26% D=7% E=26%
Estruturas usadas: 5 | Dominante: E (25.9%) | Entropia: 2.22/2.32

FATOR 2 - Titulos (97.0/100):
Similaridade media: 10.2% | Serial patterns: 0
Keyword dominante: "roma" 14.8% | Comprimento: 79.2 chars (desvio 12.8)
Near-duplicates: 0 pares

ALERTAS: Nenhum

TITULOS:
""" + "\n".join(f"{i+1}. {t}" for i, t in enumerate(real_titles))
auth_data_tok = count_tokens(auth_data)
print(f"  Auth data block (Ag.2):         {auth_data_tok:>6,} tokens")

# ============================================================
# FINAL CALCULATION WITH DYNAMIC DATA
# ============================================================
print()
print("=" * 80)
print("CALCULO FINAL — TOKENS REAIS POR AGENTE (Cronicas da Coroa, 9 videos)")
print("=" * 80)
print()

# Pricing
PRICE_IN = 0.15 / 1_000_000
PRICE_OUT = 0.60 / 1_000_000

agents_final = [
    {
        "name": "Ag.1 Copy",
        "calls": 1,
        "input": ag1_sys_tok + ag1_usr_tok + copy_data_tok,
        "output": ag1_out_tok if ag1_out_tok > 0 else 0,
        "note": "sem LLM (dados insuf.)",
    },
    {
        "name": "Ag.2 Autenticidade",
        "calls": 1,
        "input": ag2_sys_tok + ag2_usr_tok + auth_data_tok + prev_report_tok,
        "output": ag2_out_tok,
        "note": "output REAL",
    },
    {
        "name": "Ag.3 Micro (C1+C2)",
        "calls": 2,
        "input": (ag3_c1_sys_tok + ag3_c1_usr_tok + titles_tok + prev_list_tok) +
                 (ag3_c2_sys_tok + ag3_c2_usr_tok + ranking_ag3_tok + patterns_tok + prev_report_tok),
        "output": ag3_llm_c1_out_est + ag3_c2_out_tok,
        "note": "C1 JSON est. | C2 REAL",
    },
    {
        "name": "Ag.4 Titulo (C1+C2)",
        "calls": 2,
        "input": (ag4_c1_sys_tok + ag4_c1_usr_tok + titles_tok + prev_list_tok) +
                 (ag4_c2_sys_tok + ag4_c2_usr_tok + ranking_ag4_tok + patterns_tok + prev_report_tok),
        "output": ag4_llm_c1_out_est + ag4_c2_out_tok,
        "note": "C1 JSON est. | C2 REAL",
    },
    {
        "name": "Ag.5 Temas (C1+C2)",
        "calls": 2,
        "input": (ag5_c1_sys_tok + ag5_c1_usr_tok + titles_tok + prev_list_tok) +
                 (ag5_c2_sys_tok + ag5_c2_usr_tok + ranking_ag5_tok + patterns_tok + prev_report_tok),
        "output": ag5_llm_c1_out_est + ag5_c2_out_tok,
        "note": "C1 JSON est. | C2 REAL",
    },
]

print(f"  {'Agente':<24} {'Calls':>5} {'Input':>8} {'Output':>8} {'Total':>8} {'Custo':>10}  Nota")
print("  " + "-" * 90)

total_in = 0
total_out = 0
total_calls = 0

for a in agents_final:
    t = a["input"] + a["output"]
    c = a["input"] * PRICE_IN + a["output"] * PRICE_OUT
    total_in += a["input"]
    total_out += a["output"]
    total_calls += a["calls"]
    print(f"  {a['name']:<24} {a['calls']:>5} {a['input']:>7,} {a['output']:>7,} {t:>7,}  ${c:.5f}  {a['note']}")

total_tokens = total_in + total_out
total_cost = total_in * PRICE_IN + total_out * PRICE_OUT
print("  " + "-" * 90)
print(f"  {'TOTAL 1 CANAL':<24} {total_calls:>5} {total_in:>7,} {total_out:>7,} {total_tokens:>7,}  ${total_cost:.5f}")

# ============================================================
# PROJECTIONS
# ============================================================
print()
print("=" * 80)
print("PROJECAO")
print("=" * 80)
print()

for n in [1, 10, 40, 43, 100]:
    c = n * total_cost
    t = n * total_tokens
    print(f"  {n:>3} canais (1x):  {t:>10,} tokens  =  ${c:.4f} USD")

print()
print("  --- Mensal (40 canais) ---")
for freq, label in [(1, "1x/mes"), (4, "semanal"), (8, "2x/semana"), (30, "diario")]:
    c = 40 * total_cost * freq
    t = 40 * total_tokens * freq
    print(f"  {label:<20}  {t:>12,} tokens  =  ${c:.4f} USD/mes")

print()
print("=" * 80)
print("METODOLOGIA")
print("=" * 80)
print(f"  Tokenizer: tiktoken o200k_base (mesmo do GPT-4o-mini)")
print(f"  System prompts: extraidos DIRETO do codigo fonte (texto fixo)")
print(f"  User prompt templates: extraidos do codigo (parte fixa)")
print(f"  Dados dinamicos: reconstruidos com dados REAIS do teste")
print(f"  Outputs Call 2: tokenizados do report_text SALVO no banco")
print(f"  Outputs Call 1 (JSON): estimados (~60-75 tokens/video)")
print(f"  Preco: GPT-4o-mini input=$0.15/1M, output=$0.60/1M")
print()

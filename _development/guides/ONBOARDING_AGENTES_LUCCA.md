# Onboarding Completo — Sistema de Agentes de Análise

> Documento para Lucca. Tudo que precisa para clonar, entender e trabalhar em cima do sistema de agentes do YouTube Dashboard Backend.

---

## PARTE 1 — SETUP INICIAL

### 1.1 Clonar o Repositório

```bash
git clone https://github.com/ccalu/youtube-dashboard-backend.git
cd youtube-dashboard-backend
pip install -r requirements.txt
```

**Pré-requisitos:**
- Git instalado
- Python 3.10+
- Acesso ao repositório (Marcelo precisa te adicionar como Collaborator em https://github.com/ccalu/youtube-dashboard-backend/settings/access)

### 1.2 Arquivo `.env` (receber do Marcelo)

Criar na raiz do projeto:

```env
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJ...                        # Anon key (RLS ativo)
SUPABASE_SERVICE_ROLE_KEY=eyJ...           # Bypass RLS — OBRIGATÓRIO pra OAuth tokens
OPENAI_API_KEY=sk-...                      # Para agentes com LLM (GPT-4o-mini)
OPENAI_MODEL=gpt-4o-mini                   # Modelo padrão
```

**NÃO precisa:** YouTube API Keys (coletores rodam no Railway, não localmente).

### 1.3 Rodar o Servidor

```bash
# Terminal 1 — API + Dashboards
python main.py
# → http://localhost:8000

# Terminal 2 — Worker de Jobs (processa temas/motores/ordenador)
python claude_worker.py
# → Poll a cada 5s na tabela agent_jobs
```

### 1.4 Testar que Funciona

- `http://localhost:8000/mission-control` — Dashboard pixel art (todas as salas)
- `http://localhost:8000/dash-analise-copy` — Dashboard de análise de copy
- `GET http://localhost:8000/api/agents/status` — Status de todos os agentes
- `POST http://localhost:8000/api/analise-copy/{channel_id}` — Rodar análise de um canal

---

## PARTE 2 — VISÃO GERAL DO SISTEMA

### 2.1 O Que São os "Agentes"

São 6 agentes de análise que rodam por canal do YouTube. Cada um analisa um aspecto diferente do conteúdo e gera um relatório. Juntos, formam um pipeline de inteligência que orienta a produção de vídeos.

### 2.2 Pipeline dos 6 Agentes (por canal)

```
┌─────────────────────┐     ┌─────────────────────┐
│  AGENTE 1            │     │  AGENTE 4            │
│  Copy Analysis       │     │  Temas               │
│  (estrutura de copy) │     │  (temas + motores     │
│                      │     │   psicológicos)       │
└──────────┬───────────┘     └──────────┬───────────┘
           │                            │
     ┌─────┴─────┐                      │
     │           │                      │
     ▼           ▼                      ▼
┌─────────┐ ┌─────────┐        ┌─────────────┐
│ AGENTE 2│ │ AGENTE 3│        │  AGENTE 5   │
│ Satisf. │ │ Autent. │        │  Motores    │
└─────────┘ └────┬────┘        └──────┬──────┘
                 │                     │
                 └──────────┬──────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │    AGENTE 6     │
                   │ Ordenador de    │
                   │ Produção        │
                   └─────────────────┘
```

**Dependências obrigatórias:**
1. `copy_analysis_agent` — BASE (roda primeiro, sem dependências)
2. `theme_agent` — Pode rodar em paralelo com copy
3. `authenticity_agent` — Depende de copy (lê estruturas)
4. `satisfaction_agent` — Depende de copy (lê vídeos matched)
5. `motor_agent` — Depende de theme (lê temas extraídos)
6. `production_order_agent` — Depende de motor + authenticity

### 2.3 Dois Sistemas de Agentes (Separados!)

**Sistema A — Agentes de Análise por Canal (ROOT)**
São os 6 agentes acima. Rodam por canal individual. Usam LLM (GPT/Claude). Salvam em tabelas `*_analysis_runs`.

**Sistema B — Agentes de Market Intelligence (`_features/agents/`)**
São 9+ agentes que analisam o mercado em geral (trends, benchmarks, scout, alertas). Rodam via Orchestrator. Não usam LLM (rule-based, exceto AI Advisor/Title opcionais).

O Lucca vai focar no **Sistema A** primariamente, mas também manter o **Sistema B** (orchestrator + scheduler).

---

## PARTE 3 — CADA AGENTE EM DETALHE

---

### AGENTE 1: Copy Analysis Agent

**Arquivo:** `copy_analysis_agent.py` (raiz, ~1960 linhas)
**Tabela:** `copy_analysis_runs`
**O que faz:** Analisa qual estrutura de copy (letras A-G+) performa melhor em retenção para cada canal.

#### Conceito Central
Cada vídeo do canal tem uma "estrutura de copy" — uma letra (A, B, C, D...) que representa a FORMA narrativa do roteiro (não o tema). Exemplo:
- A = Cronológico (início ao fim linear)
- B = Mistério (pergunta → revelação)
- C = Problema-Solução

Essas letras são definidas em uma **Google Sheet** (a `copy_spreadsheet_id` de cada canal). A planilha tem:
- **Coluna A:** Letra da estrutura (A-Z)
- **Coluna B:** Título do vídeo

#### Fluxo Completo (10 etapas)

**Etapa 1 — Info do Canal:**
- Busca `yt_channels` pelo `channel_id` (UC...)
- Pega `copy_spreadsheet_id`, `channel_name`, `subnicho`, `lingua`

**Etapa 2 — Leitura da Planilha:**
- Google Sheets API via `gspread` → `get_sheets_client()`
- Tenta abas: 'Página1', 'Pagina1', 'Sheet1', 'Planilha1'
- Retorna: `[{structure: "A", title: "...", row_number: 1}, ...]`

**Etapa 3 — Matching de Vídeos:**
- Cruza títulos da planilha com vídeos no banco (`videos_historico`)
- Match em 3 níveis:
  1. Exato (case-sensitive)
  2. Normalizado (lowercase, sem pontuação)
  3. Similaridade ≥90% (word-by-word, Jaccard-like)
- Fallback: `yt_canal_upload_historico` (histórico de uploads)

**Etapa 4 — Dados de Retenção:**
- Busca `yt_video_metrics` em batches de 50
- Se faltam dados: chama YouTube Analytics API via OAuth
  - `_get_oauth_tokens()` → `_get_credentials()` → `_refresh_token()`
  - Métricas: `averageViewDuration`, `averageViewPercentage`, `views`
  - **IMPORTANTE:** Sempre usar `SUPABASE_SERVICE_ROLE_KEY` pra acessar tokens (RLS!)

**Etapa 5 — Análise:**
- Filtra vídeos < 7 dias (imaturos)
- Agrupa por estrutura
- Para cada estrutura com ≥3 vídeos:
  - `avg_retention`, `avg_watch_time`, `avg_views`, `std_retention`
  - Classificação vs média do canal:
    - **ACIMA:** > canal_avg + 2pp
    - **MEDIA:** dentro de ±2pp
    - **ABAIXO:** < canal_avg - 2pp
- Estruturas com <3 vídeos → "insuficiente"

**Etapa 6 — Detecção de Anomalias:**
- Views > 5x média da estrutura → anomalia de views
- Retenção > 15pp diferente da média → anomalia de retenção

**Etapa 7 — Detecção Incremental:**
- Busca run anterior → compara snapshot → identifica vídeos NOVOS
- `run_number` incrementa (1, 2, 3...)

**Etapa 8 — Comparação Temporal:**
- Ranking anterior vs atual
- Rastreia: mudanças de rank, retenção delta, novas estruturas

**Etapa 9 — LLM Insights (GPT-4o-mini):**
- Se incremental: mostra APENAS vídeos novos no prompt
- Pede [OBSERVACOES] + [TENDENCIAS]
- Temperature: 0.3 (factual)
- Passa relatório anterior como memória acumulativa

**Etapa 10 — Persistência:**
- Salva em `copy_analysis_runs` com: `results_json`, `report_text`, `analyzed_video_data` (snapshot)

#### Endpoints
| Método | Rota | Função |
|--------|------|--------|
| POST | `/api/analise-copy/{channel_id}` | Rodar análise |
| GET | `/api/analise-copy/{channel_id}/latest` | Última análise |
| GET | `/api/analise-copy/{channel_id}/historico` | Histórico paginado |
| GET | `/api/analise-copy/{channel_id}/videos` | Vídeos de uma run |
| POST | `/api/analise-copy/run-all` | Rodar pra todos os canais |
| DELETE | `/api/analise-copy/{channel_id}/run/{run_id}` | Deletar run |

#### Tabelas Lidas
`yt_channels`, `videos_historico`, `yt_canal_upload_historico`, `yt_video_metrics`, `yt_oauth_tokens`, `yt_channel_credentials`, `yt_proxy_credentials`

#### Tabela Escrita
`copy_analysis_runs`

---

### AGENTE 2: Satisfaction Agent

**Arquivo:** `satisfaction_agent.py` (raiz, ~1620 linhas)
**Tabela:** `satisfaction_analysis_runs`
**Depende de:** `copy_analysis_runs` (usa vídeos matched do copy agent)
**O que faz:** Mede quanto a audiência GOSTOU do conteúdo por estrutura de copy.

#### Conceito Central
Copy Analysis mede RETENÇÃO (tempo assistido). Satisfaction mede APROVAÇÃO (likes, inscrições, comentários).

#### Métricas Calculadas (por vídeo)
- **Like Approval Rate** = likes / (likes + dislikes) × 100
- **Like Ratio** = likes / views × 100
- **Sub Ratio** = subs_gained / views × 100 (sinal mais forte de satisfação)
- **Comment Ratio** = comments / views × 100

#### Fórmula do Score (0-100)
```
approval_score = max(0, min(100, 50 + (approval_dev% × 0.5)))
sub_score = max(0, min(100, 50 + (sub_ratio_dev% × 0.5)))

SCORE = sub_score × 0.60 + approval_score × 0.40
```
- Score 50 = média do canal
- \>55 = ACIMA
- <45 = ABAIXO

#### Coleta de Dados (3 fontes)
1. **`yt_video_metrics`** — likes, dislikes, subs_gained, views (primário)
2. **`videos_historico`** — comentários, views lifetime (enriquecimento)
3. **YouTube Analytics API** — fallback pra vídeos sem dados no DB

#### Detecção de Anomalias
- Sub Ratio > 3x média da estrutura
- Approval > 15pp diferente da média

#### Pipeline
1. Busca vídeos matched do último `copy_analysis_runs`
2. Coleta dados de satisfação (3 fontes)
3. Agrupa por estrutura, calcula métricas
4. Detecção incremental (snapshot)
5. LLM: [OBSERVACOES] + [TENDENCIAS]
6. Salva em `satisfaction_analysis_runs`

#### Endpoints
| Método | Rota | Função |
|--------|------|--------|
| POST | `/api/analise-satisfacao/{channel_id}` | Rodar |
| GET | `/api/analise-satisfacao/{channel_id}/latest` | Última |
| GET | `/api/analise-satisfacao/{channel_id}/historico` | Histórico |
| POST | `/api/analise-satisfacao/run-all` | Todos os canais |

---

### AGENTE 3: Authenticity Agent

**Arquivo:** `authenticity_agent.py` (raiz, ~1400 linhas)
**Tabela:** `authenticity_analysis_runs`
**Depende de:** `copy_analysis_agent` (importa funções de leitura de planilha)
**O que faz:** Score 0-100 de autenticidade para proteger canal contra políticas do YouTube.

#### Conceito Central
YouTube tem política contra "Inauthentic Content" — conteúdo produzido em massa, baseado em templates, facilmente replicável. Este agente detecta se o canal está em risco.

#### Dois Fatores (50/50)

**Fator 1 — Variedade de Estruturas (50%)**
3 sub-componentes:
- **Dominância (50%)** — % da estrutura mais usada. ≤25% = 100pts, ≥85% = 0pts
- **Entropia Shannon (35%)** — Distribuição uniforme = alta entropia = bom
- **Variedade (15%)** — Quantidade de estruturas únicas. ≥5 = 100pts

**Fator 2 — Diversidade de Títulos (50%)**
4 sub-componentes:
- **Similaridade Pairwise (40%)** — Jaccard entre todos os pares. avg ≤0.10 = 100pts, ≥0.50 = 0pts
- **Padrões Seriais (15%)** — "Parte 1", "Ep 2", "#3". ≤5% = 100pts, ≥50% = 0pts
- **Keyword Stuffing (30%)** — Palavra mais repetida. ≤25% = 100pts, ≥70% = 0pts
- **Variação de Comprimento (15%)** — stdev dos comprimentos. ≥15 = 100pts, ≤3 = 0pts

#### Score Composto
```
COMPOSITE = structure_score × 0.50 + title_score × 0.50
```

#### Níveis
| Score | Nível | Risco |
|-------|-------|-------|
| 80-100 | EXCELENTE | Seguro |
| 60-79 | BOM | Monitorar |
| 40-59 | ATENCAO | Agir |
| 20-39 | RISCO | Urgente |
| 0-19 | CRITICO | Perigo iminente |

#### Alertas (3 tipos)
- **Threshold:** Score < 40
- **Factor:** Qualquer fator < 30
- **Spike:** Queda > 15 pontos vs run anterior

#### Stopwords
Suporta 5 idiomas: PT, EN, ES, DE, FR (~100+ stopwords)

#### Filtro de Publicados
Se o canal tem `spreadsheet_id` (tracking), filtra apenas vídeos com Col K preenchida (publicados).

#### LLM Output
3 seções: [DIAGNOSTICO], [RECOMENDACOES], [TENDENCIAS]

#### Endpoints
| Método | Rota | Função |
|--------|------|--------|
| POST | `/api/analise-autenticidade/{channel_id}` | Rodar |
| GET | `/api/analise-autenticidade/{channel_id}/latest` | Última |
| GET | `/api/analise-autenticidade/{channel_id}/historico` | Histórico |
| GET | `/api/analise-autenticidade/overview` | Overview de TODOS os canais |

---

### AGENTE 4: Theme Agent

**Arquivo:** `theme_agent.py` (raiz, ~1500 linhas)
**Tabela:** `theme_analysis_runs`
**O que faz:** Identifica o TEMA concreto e as HIPÓTESES DE MOTORES PSICOLÓGICOS de cada vídeo.

#### Conceito Central
Cada vídeo tem:
- **TEMA:** Assunto concreto e específico (ex: "Os excessos do imperador Calígula em Roma")
- **MOTORES PSICOLÓGICOS:** Padrões invisíveis que explicam o clique (ex: "Voyeurismo legitimado", "Choque moral")

Os motores se REPETEM entre vídeos de temas COMPLETAMENTE diferentes. Eles revelam o que MOVE a audiência.

#### Scoring: 50% CTR + 50% Views
```
views_norm = (views - min) / (max - min) × 100   # Min-max 0-100
ctr_norm = (ctr - min) / (max - min) × 100       # Min-max 0-100
score = 0.5 × ctr_norm + 0.5 × views_norm
```
Vídeos sem CTR recebem `ctr_norm = 50.0` (neutro, não são excluídos).

#### Filtros de Entrada
- `MIN_VIDEOS = 5` (mínimo pra rodar)
- `MIN_VIEWS = 500` (ou 7+ dias de idade)

#### Detecção Incremental
- Snapshot: `{video_id: {views, ctr, score, tema, hipoteses}}`
- Mudança significativa: views +20% OU CTR ±2pp
- 3 categorias: NEW, UPDATED, UNCHANGED
- UNCHANGED reutiliza análise anterior (sem LLM call)

#### LLM — System Prompt (225 linhas!)
Define:
- Como extrair TEMA (concreto, específico, factual, NÃO genérico)
- Como identificar MOTORES (padrões invisíveis de clique)
- Catálogo de motores exemplo: "Poder sem limites", "Voyeurismo legitimado", "Choque moral", "Violação do sagrado", "Monstruosidade feminina", "Luto civilizacional", "Conhecimento proibido"
- Anti-patterns (padrões que matam performance)
- Interações entre motores (amplificam/neutralizam)

#### Output JSON do LLM
```json
{
  "videos": [{video_id, titulo, tema, hipoteses: [{motor, explicacao}]}],
  "catalogo_motores": [{motor, descricao, vocabulario, insight_psicologico, videos_ids}],
  "anti_patterns": [{pattern, descricao, exemplos_video_ids, impacto}],
  "interacoes_motores": [{combinacao, tipo: "amplifica"|"neutraliza", explicacao}]
}
```

#### Correlações (Python, não LLM)
Após LLM, calcula: score médio e CTR médio COM vs SEM cada motor.

#### Claude CLI vs OpenAI
- Primeiro tenta Claude CLI local (via `claude_llm_client`)
- Se não disponível: cria job na fila `agent_jobs` (processed by `claude_worker.py`)
- Fallback final: OpenAI API

#### Endpoints
| Método | Rota | Função |
|--------|------|--------|
| POST | `/api/analise-temas/{channel_id}` | Rodar |
| POST | `/api/analise-temas/run-all` | Todos os canais |
| GET | `/api/analise-temas/{channel_id}/latest` | Última |
| GET | `/api/analise-temas/{channel_id}/historico` | Histórico |

---

### AGENTE 5: Motor Agent

**Arquivo:** `motor_agent.py` (raiz, ~940 linhas)
**Tabela:** `motor_analysis_runs`
**Depende de:** `theme_analysis_runs` (lê temas e catálogo de motores)
**O que faz:** Transforma a análise de motores em AÇÕES CONCRETAS — fórmula de performance, recomendações com títulos, hipóteses para testar.

#### Conceito Central
O Theme Agent IDENTIFICA motores. O Motor Agent ESTRATEGIZA em cima deles:
- Qual é a "receita" deste canal? (fórmula vencedora)
- O que é tóxico? (fórmula que mata CTR)
- O que produzir? (títulos concretos no idioma do canal)
- O que testar? (hipóteses estruturadas)

#### System Prompt (150+ linhas)
Define:
- Nunca inventar números (são FATOS do sistema)
- TODA recomendação DEVE incluir títulos concretos no idioma do canal
- Explicar QUAIS motores cada título ativa
- Fórmula deve ser ESPECÍFICA (não genérica)
- Mostrar evidência numérica (correlações COM vs SEM)

#### Output do LLM (Primeira Análise)
```
[FORMULA DE PERFORMANCE]
  FORMULA VENCEDORA: combinação de motores + evidência
  FORMULA TOXICA: anti-patterns + evidência
  DNA DO CANAL: 1-2 motores essenciais

[RECOMENDACOES]
  PRODUZIR MAIS: 3-5 títulos concretos + motores
  DIVERSIFICAR: expansão + títulos-teste
  EVITAR: o que NÃO produzir
  REFORMULAR: temas fracos com ângulo novo

[HIPOTESES PARA TESTAR]
  3-5 hipóteses com: o que testar, motor, título-teste, resultado esperado, risco

[PRIORIDADES PRATICAS]
  IMEDIATO / CURTO PRAZO / ESTRATEGICO
```

#### Output do LLM (Run #2+)
Adiciona:
- `[FORMULA DE PERFORMANCE -- ATUALIZADA]`
- `[EVOLUCAO DOS MOTORES]` (cresceu, estável, caiu, NOVO, EXTINTO)
- `[HIPOTESES ANTERIORES -- STATUS]` (CONFIRMADA / EM TESTE / REFUTADA)

#### Detecção Incremental
- Compara ranking atual vs snapshot da run anterior
- Views +20% ou CTR ±2pp = UPDATED
- Se zero novos/atualizados: reutiliza relatório anterior

#### Endpoints
| Método | Rota | Função |
|--------|------|--------|
| POST | `/api/analise-motores/{channel_id}` | Rodar |
| POST | `/api/analise-motores/run-all` | Todos os canais |
| GET | `/api/analise-motores/{channel_id}/latest` | Última |
| GET | `/api/analise-motores/{channel_id}/historico` | Histórico |

---

### AGENTE 6: Production Order Agent

**Arquivo:** `production_order_agent.py` (raiz, ~700 linhas)
**Tabela:** `production_order_runs`
**Depende de:** `motor_analysis_runs` + `authenticity_analysis_runs`
**O que faz:** Recomenda a ORDEM IDEAL de produção dos roteiros pendentes para maximizar viralização e proteger saúde do canal.

#### Conceito Central
Roteiros na planilha vêm em ordem arbitrária. A equipe produz de cima pra baixo sem estratégia. Este agente REORDENA os roteiros baseado em 2 pilares:

**Pilar 1 — Potencial Viral:**
- Lê hierarquia de motores (do Motor Agent)
- Analisa cada título → identifica quais motores ativa
- Ranqueia por potencial de viralização

**Pilar 2 — Saúde do Canal (Autenticidade):**
- Se canal saudável (score ≥60): otimiza APENAS por motores
- Se canal em risco (score <60): ALTERNA estruturas de copy pra diversificar
- Nunca produz 3+ vídeos da mesma estrutura em sequência

#### System Prompt (214 linhas!)
Define regras intrincadas de ordenação:
- Canal saudável → maximizar motores, ignorar estrutura
- Canal em atenção → alternar estruturas a cada 2 vídeos
- Canal em risco → máxima diversificação, nunca repetir estrutura adjacente
- Sempre explicar o PORQUÊ de cada posição na ordem

#### Leitura da Planilha
- Lê roteiros pendentes (status "to do") da `copy_spreadsheet_id`
- Cada roteiro tem: estrutura (letra), título, row_number
- Usa hash MD5 do conteúdo para detectar mudanças incrementais

#### Output
```json
{
  "ordem_recomendada": [
    {
      "posicao": 1,
      "titulo": "...",
      "estrutura": "B",
      "row_number": 5,
      "motores_identificados": ["Motor X", "Motor Y"],
      "justificativa": "..."
    }
  ],
  "diagnostico_canal": "...",
  "regras_aplicadas": "..."
}
```

#### Endpoints
| Método | Rota | Função |
|--------|------|--------|
| POST | `/api/analise-ordenador/{channel_id}` | Rodar |
| GET | `/api/analise-ordenador/{channel_id}/latest` | Última |
| GET | `/api/analise-ordenador/{channel_id}/historico` | Histórico |

---

### Endpoint Unificado: Análise Completa

| Método | Rota | Função |
|--------|------|--------|
| POST | `/api/analise-completa/{channel_id}` | Roda os 6 agentes sequencialmente para 1 canal |
| POST | `/api/analise-completa/run-all` | Roda pra TODOS os canais |
| DELETE | `/api/analise-completa/{channel_id}/date/{YYYY-MM-DD}` | Deleta todas as runs de uma data |

---

## PARTE 4 — SISTEMA DE ORQUESTRAÇÃO

### 4.1 Orchestrator (`_features/agents/orchestrator.py`)

Coordena os agentes do **Sistema B** (Market Intelligence) em 3 fases:

**Fase 1 — Data Analysis (paralelo):**
TrendAgent, PatternAgent, BenchmarkAgent, CorrelationAgent, RecyclerAgent

**Fase 2 — Recomendações (paralelo, depende da Fase 1):**
AdvisorAgent, AlertAgent, AIAdvisorAgent*, AITitleAgent*
(*requerem OPENAI_API_KEY)

**Fase 3 — Relatórios (sequencial):**
ReportAgent (consolida tudo em HTML)

### 4.2 Scheduler (`_features/agents/scheduler.py`)

Jobs automáticos (APScheduler):
- **06:00 UTC:** Full analysis (todas as fases)
- **A cada 4h:** TrendAgent (leve)
- **A cada 6h:** AlertAgent (leve)
- ScoutAgent: desabilitado (economiza API quota)

### 4.3 Base Agent (`_features/agents/base.py`)

Classe abstrata com lifecycle:
- `AgentStatus`: IDLE, RUNNING, COMPLETED, FAILED
- `AgentResult`: dataclass com data, errors, metrics, duration
- `BaseAgent.execute()`: wrapper com try-catch, logging, caching

### 4.4 Agents Endpoints (`agents_endpoints.py`)

Prefixo: `/api/agents`

| Método | Rota | O que faz |
|--------|------|-----------|
| GET | `/api/agents/status` | Status de todos os agentes |
| GET | `/api/agents/scheduler/status` | Status do scheduler |
| POST | `/api/agents/run/all` | Roda todos (background) |
| POST | `/api/agents/run/{agent_name}` | Roda 1 agente específico |
| POST | `/api/agents/run/analysis` | Análise rápida (sem Scout) |
| GET | `/api/agents/data` | Dados de todos |
| GET | `/api/agents/data/{agent_name}` | Dados de 1 agente |
| GET | `/api/agents/reports` | Lista relatórios HTML |
| GET | `/api/agents/reports/{filename}` | Ver relatório |
| POST | `/api/agents/scheduler/start` | Iniciar scheduler |
| POST | `/api/agents/scheduler/stop` | Parar scheduler |
| GET | `/api/agents/insights/trending` | Trends atuais |
| GET | `/api/agents/insights/recommendations` | Recomendações |
| GET | `/api/agents/insights/alerts` | Alertas ativos |
| GET | `/api/agents/insights/opportunities` | Oportunidades |
| GET | `/api/agents/ai/briefing` | Briefing diário GPT |
| GET | `/api/agents/ai/titles` | Banco de títulos GPT |
| POST | `/api/agents/ai/generate-titles` | Gerar títulos por tema |
| POST | `/api/agents/ai/adapt-title` | Adaptar título entre idiomas |

---

## PARTE 5 — DASHBOARDS

### 5.1 Mission Control (`mission_control.py`)

**Rota:** `GET /mission-control`

Dashboard visual com pixel art de escritório. Cada canal é uma "sala" com 7 agentes animados.

**Funcionalidades:**
- Visualização por subnicho (abas: Monetizados, Reis Perversos, etc.)
- Status real-time de cada agente por canal (done/idle/error/waiting)
- Click em agente → abre sidebar com detalhes + relatório
- Botão "RUN ALL" → dispara análise completa pra todos os canais
- Botão "ATUALIZAR" → refresh MVs + limpa cache

**APIs consumidas pelo frontend:**
- `GET /api/mission-control/status` — Dados de todas as salas
- `GET /api/mission-control/sala/{canal_id}` — Detalhe de uma sala
- `POST /api/mission-control/refresh` — Refresh cache
- `GET /api/analise-copy/{channel_id}/latest` — Relatório de agente
- `POST /api/analise-completa/run-all` — Rodar todos

**21 temas visuais** (1 por subnicho): executive, palace, gothic, macabre, warroom, frontline, command, wisdom, cursed, demonetized, darklab, ancient, inspire, mystery, missing, mindset, conspiracy, business, alpha, news, random.

### 5.2 Dashboard Copy Analysis

**Rota:** `GET /dash-analise-copy`

Dashboard focado na análise de copy structures. Mostra canais agrupados por subnicho com resumo de performance.

**API:** `GET /api/dash-analise-copy/channels` — Lista canais com copy_spreadsheet_id

---

## PARTE 6 — CLAUDE WORKER (Job Queue)

### 6.1 O que é

**Arquivo:** `claude_worker.py`
**Roda na máquina do Marcelo** (always-on). Processa jobs de agentes que precisam de Claude CLI (que não está disponível no Railway).

### 6.2 Como Funciona

```
1. Poll `agent_jobs` a cada 5s (status = "pending")
2. Prioriza: temas (0) → motores (1) → ordenador (2)
3. Verifica dependências: motores espera temas, ordenador espera motores
4. Executa: import agent → run_analysis(channel_id)
5. Atualiza status: pending → processing → completed/failed
```

### 6.3 Tabela `agent_jobs`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | int | PK auto |
| channel_id | str | UC... do canal |
| agent_type | str | "temas", "motores", "ordenador" |
| status | str | "pending", "processing", "completed", "failed" |
| created_at | timestamp | Criação |
| started_at | timestamp | Início processamento |
| completed_at | timestamp | Fim |
| result_data | jsonb | Resultado (se completed) |
| error_message | text | Erro (se failed) |

### 6.4 Quando Jobs São Criados

Quando `theme_agent.py`, `motor_agent.py`, ou `production_order_agent.py` detectam que Claude CLI NÃO está disponível (ex: rodando no Railway), eles criam um job na fila:
```python
_create_agent_job(channel_id, "temas")  # Enfileira pra worker processar
```

---

## PARTE 7 — CLAUDE LLM CLIENT (Como os Agentes Chamam LLM)

### 7.1 Dois Caminhos de LLM

Os agentes 4, 5 e 6 (Temas, Motores, Ordenador) precisam de LLM pesado. Eles têm **dois caminhos**:

```
                  ┌─ Claude CLI disponível? ──→ SIM ──→ call_claude_cli() direto
                  │                                       (usa plano Max, Claude Opus 4.6)
run_analysis() ───┤
                  │
                  └─ NÃO (Railway/server) ──→ Cria job na fila `agent_jobs`
                                               → claude_worker.py processa localmente
                                               → Fallback: OpenAI API (gpt-4o-mini)
```

Os agentes 1, 2 e 3 (Copy, Satisfaction, Authenticity) usam **apenas OpenAI** (GPT-4o-mini) para insights opcionais — se a `OPENAI_API_KEY` não existir, rodam sem LLM normalmente.

### 7.2 Claude LLM Client (`claude_llm_client.py`)

**Arquivo:** `claude_llm_client.py` (raiz)
**Requisito:** Claude Code instalado (`npm i -g @anthropic-ai/claude-code`) + plano Max logado

**Duas funções exportadas:**

#### `is_claude_cli_available() -> bool`
- Verifica se o binário `claude` está no PATH (`shutil.which("claude")`)
- Retorna True/False
- Chamado pelos agentes antes de decidir o caminho

#### `call_claude_cli(system_prompt, user_prompt, model, timeout) -> str`
- **model:** Default `claude-opus-4-6`
- **timeout:** 600 segundos (10 min)
- **Modo:** Single-turn, sem tools, sem settings (puro texto)
- **Formato:** stream-json (input e output)

**Fluxo interno:**
1. Monta comando CLI com flags: `--print`, `--output-format stream-json`, `--max-turns 1`, `--allowedTools ""` (sem tools)
2. Se system prompt < 32K chars → passa via `--system-prompt`
3. Se system prompt > 32K chars → concatena no user prompt (workaround Windows)
4. Executa como `subprocess.run()` síncrono
5. Parseia output stream-json: extrai blocos `type: "assistant"` com `content.text`
6. Extrai usage: `input_tokens`, `output_tokens` (inclui cache tokens)
7. Detecta erros: returncode != 0, ghost response (0 tokens)
8. Retorna texto completo

**Por que Claude CLI e não API diretamente?**
- Usa tokens do **plano Max** do Marcelo (sem custo de API)
- Claude Opus 4.6 pra análise estratégica pesada (motores, produção)
- GPT-4o-mini é fallback pra quando Claude não está disponível

### 7.3 Resumo de Qual LLM Cada Agente Usa

| Agente | LLM Principal | Fallback | Obrigatório? |
|--------|--------------|----------|-------------|
| Copy Analysis | GPT-4o-mini (OpenAI) | Roda sem LLM | Não |
| Satisfaction | GPT-4o-mini (OpenAI) | Roda sem LLM | Não |
| Authenticity | GPT-4o-mini (OpenAI) | Roda sem LLM | Não |
| Temas | Claude Opus 4.6 (CLI) | GPT-4o-mini / Job queue | Sim |
| Motores | Claude Opus 4.6 (CLI) | GPT-4o-mini / Job queue | Sim |
| Ordenador | Claude Opus 4.6 (CLI) | GPT-4o-mini / Job queue | Sim |

---

## PARTE 8 — TABELAS DO SUPABASE

### Tabelas de Resultados dos Agentes

| Tabela | Agente | Campos Chave |
|--------|--------|-------------|
| `copy_analysis_runs` | Copy | channel_avg_retention, results_json, report_text, analyzed_video_data |
| `satisfaction_analysis_runs` | Satisfaction | channel_avg_approval, channel_avg_sub_ratio, results_json |
| `authenticity_analysis_runs` | Authenticity | authenticity_score, authenticity_level, structure_score, title_score |
| `theme_analysis_runs` | Temas | theme_count, ranking_json, themes_json, themes_list |
| `motor_analysis_runs` | Motores | motor_counts_json, ranking_snapshot, report_text |
| `production_order_runs` | Ordenador | results_json, report_text |
| `agent_jobs` | Worker Queue | channel_id, agent_type, status |

### Tabelas de Dados (lidas pelos agentes)

| Tabela | Quem lê | O que contém |
|--------|---------|-------------|
| `yt_channels` | Todos | Metadata do canal (nome, subnicho, lingua, spreadsheet_ids, avg_ctr) |
| `videos_historico` | Copy, Theme, Auth, Sat | Vídeos com título, views, data de publicação |
| `yt_video_metrics` | Copy, Theme, Sat | Retenção, CTR, impressões, likes, dislikes, subs |
| `yt_oauth_tokens` | Copy, Sat | Tokens OAuth (SERVICE_ROLE_KEY!) |
| `yt_channel_credentials` | Copy, Sat | Client ID/Secret por canal |
| `yt_proxy_credentials` | Copy, Sat | Credenciais proxy |
| `canais_monitorados` | Theme, Agents B | Lista de canais monitorados |
| `yt_video_daily` | CTR | Snapshots diários |

---

## PARTE 9 — LISTA COMPLETA DE ARQUIVOS

### Agentes de Análise (ROOT — nunca mover!)
```
copy_analysis_agent.py          # Agente 1 — Estrutura de Copy
satisfaction_agent.py           # Agente 2 — Satisfação da Audiência
authenticity_agent.py           # Agente 3 — Score de Autenticidade
theme_agent.py                  # Agente 4 — Temas + Motores Psicológicos
motor_agent.py                  # Agente 5 — Estratégia de Motores
production_order_agent.py       # Agente 6 — Ordenador de Produção
```

### Orquestração e Infraestrutura
```
agents_endpoints.py             # Endpoints /api/agents/* (orquestrador)
mission_control.py              # Dashboard Mission Control (/mission-control)
claude_worker.py                # Worker local de jobs (temas/motores/ordenador)
claude_llm_client.py            # Client para Claude CLI (usa plano Max)
```

### Sistema de Agentes B (`_features/agents/`)
```
_features/agents/base.py            # Classe base abstrata
_features/agents/orchestrator.py    # Coordenador de fases
_features/agents/scheduler.py       # Agendamento automático
_features/agents/__init__.py        # Exports
_features/agents/scout_agent.py     # Descoberta de canais
_features/agents/trend_agent.py     # Detecção de trends
_features/agents/pattern_agent.py   # Padrões de títulos
_features/agents/benchmark_agent.py # Comparação vs mercado
_features/agents/correlation_agent.py # Correlação cross-language
_features/agents/recycler_agent.py  # Reciclagem de conteúdo
_features/agents/advisor_agent.py   # Recomendações (rule-based)
_features/agents/ai_advisor_agent.py # Recomendações GPT
_features/agents/ai_title_agent.py  # Geração de títulos GPT
_features/agents/alert_agent.py     # Alertas inteligentes
_features/agents/report_agent.py    # Relatórios HTML
```

### Frontend (referência)
```
_features/frontend-code/AnalysisTab.tsx
_features/frontend-code/api-methods.ts
_features/frontend-code/types-analysis.ts
```

### Migrations (referência)
```
_database/  → migrations 015, 016, 020, 024, 025, 031, 032, 033
```

---

## PARTE 10 — REGRAS CRÍTICAS

### Supabase
1. **NUNCA** usar `resolution=merge-duplicates` → usar POST + PATCH on 409
2. **NUNCA** usar CURRENT_DATE em materialized views → usar ROW_NUMBER() ORDER BY date DESC
3. **SEMPRE** usar `SUPABASE_SERVICE_ROLE_KEY` pra acessar `yt_oauth_tokens` (RLS bloqueia anon key)

### Planilhas
4. **NUNCA** misturar `spreadsheet_id` (upload/tracking) com `copy_spreadsheet_id` (análise de copy)

### HTML/Railway
5. **NUNCA** usar emoji flags (surrogate pairs quebram encoding) → usar badges texto (PT, EN, ES)
6. **NUNCA** editar HTML/CSS via PowerShell (encoding UTF-8 quebra)

### API YouTube
7. **NUNCA** usar `search.list` (100 units) → usar `playlistItems.list` (1 unit)

### Imports
8. `main.py` importa de `_features.yt_uploader`
9. `agents_endpoints.py` importa de `_features.agents`
10. Agentes root importam de `copy_analysis_agent` (funções compartilhadas)

---

## PARTE 11 — PROMPT PARA CLAUDE CODE DO LUCCA

Depois de clonar e configurar o `.env`, o Lucca pode usar este prompt no Claude Code dele para entender o sistema a fundo:

```
Analise a fundo o sistema de agentes deste projeto. Leia os seguintes arquivos e
me explique como cada um funciona em detalhe:

1. copy_analysis_agent.py — Como lê planilhas, matcha vídeos, calcula retenção
2. authenticity_agent.py — Como calcula score de autenticidade (fórmulas exatas)
3. theme_agent.py — Como extrai temas e motores psicológicos via LLM
4. motor_agent.py — Como transforma motores em estratégia
5. satisfaction_agent.py — Como mede satisfação por estrutura
6. production_order_agent.py — Como ordena produção
7. claude_worker.py — Como processa jobs na fila
8. agents_endpoints.py — Todos os endpoints da API
9. mission_control.py — Como funciona o dashboard visual
10. _features/agents/orchestrator.py — Como coordena agentes de mercado

Depois, me faça um resumo de:
- Cadeia de dependências entre agentes
- Quais tabelas cada agente lê/escreve
- Como funciona a detecção incremental (snapshots)
- Como a memória acumulativa funciona (relatório anterior → LLM)

Leia também _development/guides/ONBOARDING_AGENTES_LUCCA.md para contexto completo.
```

---

## PARTE 12 — CHECKLIST DE PRIMEIRO DIA

- [ ] Clonar repo
- [ ] Configurar `.env`
- [ ] `pip install -r requirements.txt`
- [ ] `python main.py` → acessar http://localhost:8000/mission-control
- [ ] Rodar 1 análise de copy: `POST /api/analise-copy/{channel_id}`
- [ ] Ver resultado: `GET /api/analise-copy/{channel_id}/latest`
- [ ] Rodar análise completa: `POST /api/analise-completa/{channel_id}`
- [ ] Explorar Mission Control (clicar nas salas, ver agentes)
- [ ] Ler este documento por completo
- [ ] Usar o prompt da Parte 11 no Claude Code

# Sistema de Agentes Inteligentes - Content Factory

## Visao Geral

Sistema de mineracao inteligente com **11 agentes** (9 gratuitos + 2 com IA) trabalhando em paralelo para:
- Descobrir canais novos automaticamente
- Detectar tendencias em tempo real
- Analisar padroes de sucesso
- Comparar performance vs concorrentes
- Encontrar oportunidades cross-language
- Gerar recomendacoes acionaveis
- Identificar conteudo para reciclar
- Alertar sobre eventos importantes
- Gerar relatorios HTML bonitos

## Custo: ZERO (base) + ~$0.02-0.04/dia (IA opcional)

**Agentes Base (9):** ZERO custo adicional
- Supabase (seu banco existente)
- YouTube API (suas 20 keys)
- Python puro (sem IA externa)
- Roda no Railway que voce ja paga

**Agentes IA (2):** ~$0.02-0.04/dia com GPT-4 Mini
- AIAdvisorAgent: ~30-50K tokens/dia
- AITitleAgent: ~20-50K tokens/dia
- Total: ~50-100K tokens = ~$0.02-0.04/dia
- **Requer:** OPENAI_API_KEY no Railway

## Arquitetura

```
                         ORCHESTRATOR
                              |
    +-------------------------+-------------------------+
    |           |           |           |           |
  SCOUT     TREND     PATTERN   BENCHMARK   CORRELATION
    |           |           |           |           |
    +-------------------------+-------------------------+
                              |
              +---------------+---------------+
              |         |          |          |
           ADVISOR   RECYCLER    ALERT    AI AGENTS
              |         |          |     (GPT-4 Mini)
              +---------------+---------------+
                              |
                           REPORT
                              |
                         HTML/JSON

    AI AGENTS (opcional, requer OPENAI_API_KEY):
    +-------------------------------------------+
    |                                           |
    |   AI ADVISOR          AI TITLE            |
    |   (briefings)        (titulos)            |
    |                                           |
    +-------------------------------------------+
```

## Agentes

### 1. ScoutAgent - Cacador de Canais
- **Funcao:** Descobrir novos canais concorrentes
- **Substitui:** NextLev
- **Filtros:**
  - Minimo 1.000 inscritos
  - Video publicado nos ultimos 15 dias
  - Subnicho relevante
- **Output:** Lista rankeada de canais para aprovar

### 2. TrendAgent - Detector de Tendencias
- **Funcao:** Identificar videos/temas em alta
- **Algoritmo:**
  - Video recente (< 7 dias)
  - Views > media do canal * 2
  - Crescimento diario > 10%
- **Output:** Feed de tendencias por subnicho/idioma

### 3. PatternAgent - Analisador de Padroes
- **Funcao:** Decodificar o que faz videos viralizarem
- **Analisa:**
  - Estruturas de titulo
  - Palavras-gatilho por idioma
  - Comprimento ideal de titulo
  - Padroes de pontuacao
- **Output:** Recomendacoes de titulo validadas

### 4. BenchmarkAgent - Comparador de Performance
- **Funcao:** Comparar nossos canais vs mercado
- **Metricas:**
  - Views medias (nos vs benchmark)
  - Frequencia de virais
  - Performance por subnicho
- **Output:** Ranking e alertas de performance

### 5. CorrelationAgent - Cruzamento Cross-Language
- **Funcao:** Encontrar correlacoes entre idiomas
- **Busca:**
  - Temas que bombaram em EN mas nao existem em JP
  - Padroes que funcionam em um subnicho vs outro
- **Output:** Oportunidades de replicacao

### 6. AdvisorAgent - Conselheiro Estrategico
- **Funcao:** Transformar dados em ACOES
- **Responde:**
  - Qual micronicho explorar HOJE?
  - Qual estrutura de titulo usar?
  - Quais videos clonar?
- **Output:** Lista priorizada de recomendacoes por canal

### 7. RecyclerAgent - Reciclador de Conteudo
- **Funcao:** Identificar conteudo para adaptar
- **Busca:**
  - Videos nossos para adaptar em outro idioma
  - Videos antigos para atualizar
  - Temas evergreen para explorar
- **Output:** Plano de reciclagem priorizado

### 8. AlertAgent - Sistema de Alertas
- **Funcao:** Notificar apenas o que importa
- **Tipos:**
  - VIRAL: Video concorrente > 50K em 3 dias
  - TREND: Micronicho emergente
  - DROP: Nosso canal caiu
  - OPPORTUNITY: Gap de mercado
- **Anti-ruido:** Agrega alertas similares

### 9. ReportAgent - Gerador de Relatorios
- **Funcao:** Consolidar insights em HTML bonito
- **Relatorios:**
  - Morning Brief (diario)
  - Dashboard Overview
  - Trends Report
  - Opportunities Report
- **Design:** Dark mode, responsivo, mobile-first

### 10. AIAdvisorAgent - Conselheiro Inteligente (GPT-4 Mini)
- **Funcao:** Analise profunda com inteligencia artificial
- **Custo:** ~30-50K tokens/dia (~$0.01-0.02)
- **Features:**
  - Gera briefing diario em linguagem natural
  - Analisa POR QUE videos viralizaram
  - Fornece recomendacoes estrategicas contextuais
  - Identifica padroes que humanos nao percebem
- **Output:** Briefing matinal, analise de virais, estrategias

### 11. AITitleAgent - Gerador de Titulos (GPT-4 Mini)
- **Funcao:** Criar titulos otimizados baseado em padroes de sucesso
- **Custo:** ~20-50K tokens/dia (~$0.01-0.02)
- **Features:**
  - Analisa estruturas de titulos por subnicho
  - Gera banco de titulos novos e originais
  - Adapta titulos para outros idiomas
  - Identifica formulas de titulo que funcionam
- **Endpoints especiais:**
  - `POST /ai/generate-titles` - Gera titulos sob demanda
  - `POST /ai/adapt-title` - Adapta titulo para outro idioma

## Como Usar

### Via API (endpoints)

```bash
# Executar todos os agentes
curl -X POST http://localhost:8000/api/agents/run/all

# Executar um agente especifico
curl -X POST http://localhost:8000/api/agents/run/TrendAgent

# Ver tendencias
curl http://localhost:8000/api/agents/insights/trending

# Ver recomendacoes
curl http://localhost:8000/api/agents/insights/recommendations

# Ver alertas
curl http://localhost:8000/api/agents/insights/alerts

# Ver relatorio HTML (navegador)
http://localhost:8000/api/agents/reports/morning_brief.html
```

### Via Script de Teste

```bash
cd youtube-dashboard-backend
python test_agents.py
```

### Scheduler Automatico

```bash
# Iniciar scheduler (via API)
curl -X POST http://localhost:8000/api/agents/scheduler/start

# Parar scheduler
curl -X POST http://localhost:8000/api/agents/scheduler/stop
```

Schedule padrao:
- Analise completa: 6h UTC (antes de acordar)
- Alertas: a cada 6 horas
- Tendencias: a cada 4 horas

## Setup

### 1. Criar tabelas no Supabase

Execute o SQL em `agents/create_tables.sql` no SQL Editor do Supabase.

### 2. Instalar dependencias (se necessario)

```bash
pip install apscheduler
```

### 3. Rodar servidor

```bash
python main.py
```

O sistema de agentes sera inicializado automaticamente.

## Endpoints Disponiveis

| Endpoint | Metodo | Descricao |
|----------|--------|-----------|
| `/api/agents/status` | GET | Status de todos os agentes |
| `/api/agents/run/all` | POST | Executar todos |
| `/api/agents/run/{nome}` | POST | Executar um agente |
| `/api/agents/data` | GET | Dados de todos |
| `/api/agents/data/{nome}` | GET | Dados de um agente |
| `/api/agents/reports` | GET | Lista relatorios |
| `/api/agents/reports/{file}` | GET | Ver relatorio HTML |
| `/api/agents/insights/trending` | GET | Tendencias |
| `/api/agents/insights/recommendations` | GET | Recomendacoes |
| `/api/agents/insights/alerts` | GET | Alertas |
| `/api/agents/scheduler/start` | POST | Iniciar scheduler |
| `/api/agents/scheduler/stop` | POST | Parar scheduler |

### Endpoints de IA (GPT-4 Mini)
| Endpoint | Metodo | Descricao |
|----------|--------|-----------|
| `/api/agents/ai/briefing` | GET | Briefing diario gerado por IA |
| `/api/agents/ai/titles` | GET | Banco de titulos otimizados |
| `/api/agents/ai/generate-titles` | POST | Gerar titulos sob demanda |
| `/api/agents/ai/adapt-title` | POST | Adaptar titulo para outro idioma |

## Arquivos

```
agents/
├── __init__.py           # Exports
├── base.py              # Classe base
├── scout_agent.py       # Descoberta de canais
├── trend_agent.py       # Deteccao de tendencias
├── pattern_agent.py     # Analise de padroes
├── benchmark_agent.py   # Comparacao de performance
├── correlation_agent.py # Cruzamento cross-language
├── advisor_agent.py     # Recomendacoes
├── recycler_agent.py    # Reciclagem de conteudo
├── alert_agent.py       # Sistema de alertas
├── report_agent.py      # Geracao de relatorios
├── ai_advisor_agent.py  # 🤖 Conselheiro IA (GPT-4 Mini)
├── ai_title_agent.py    # 🤖 Gerador de titulos IA (GPT-4 Mini)
├── orchestrator.py      # Coordenador de agentes
├── scheduler.py         # Agendador automatico
├── create_tables.sql    # SQL para Supabase
└── README.md           # Esta documentacao

agents_endpoints.py      # Endpoints da API
test_agents.py          # Script de teste
test_imports.py         # Verificacao de imports
reports/                # Relatorios HTML gerados
```

## Proximos Passos

1. **Testar localmente:** `python test_agents.py`
2. **Criar tabelas:** Execute o SQL no Supabase
3. **Deploy:** Push para GitHub, Railway deploya automaticamente
4. **Acessar relatorios:** `https://seu-railway.app/api/agents/reports/`

## Suporte

Se tiver problemas:
1. Verificar logs no Railway
2. Testar conexao com Supabase
3. Verificar se tabelas foram criadas

# DNA dos Agentes — Arquitetura Completa

> Documento tecnico detalhado dos 5 agentes de analise do sistema YouTube Dashboard.
> Atualizado em: 05/03/2026

---

## Visao Geral

O sistema opera 5 agentes de IA que analisam canais YouTube automaticamente. Cada agente tem uma responsabilidade especifica e produz um relatorio salvo no banco de dados. Juntos, formam um pipeline de inteligencia que vai desde performance de copy ate motores psicologicos de viralidade.

### Cadeia de Dependencias

```
[Planilha de Copy]
       |
       v
  AGENTE 1: COPY ──────────────> AGENTE 2: SATISFACAO
       |                              (usa videos matched do Copy)
       |
       v
  AGENTE 3: AUTENTICIDADE
       (le planilha diretamente, importa funcoes do Copy)

[Supabase: yt_video_metrics + videos_historico]
       |
       v
  AGENTE 4: TEMAS ──────────────> AGENTE 5: MOTORES
       (ranking proprio)              (depende do run de Temas)
```

### Ordem na Analise Completa

`POST /api/analise-completa/{channel_id}` roda sequencialmente:

1. Copy → 2. Satisfacao → 3. Autenticidade → 4. Temas → 5. Motores

Cada agente e isolado em try/except — se um falha, os outros continuam.

Os resultados dos 5 agentes sao combinados pela funcao `_build_unified_report()` (main.py) em um relatorio unificado:
1. ANALISE DE PERFORMANCE (report do Copy)
2. ANALISE DE SATISFACAO (report da Satisfacao)
3. SCORE DE AUTENTICIDADE (report da Autenticidade)
4. ANALISE DE TEMAS (report dos Temas)
5. ANALISE DE MOTORES PSICOLOGICOS (report dos Motores)

O endpoint retorna tambem um JSON com `performance`, `satisfacao`, `authenticity`, `temas`, `motores` e `errors[]` separados.

---

## O Que os Agentes Tem em Comum

### Padrao Incremental (todos os 5)

Todos seguem o mesmo padrao de analise incremental:

1. **Snapshot JSONB**: Cada run salva um snapshot dos dados analisados no campo `analyzed_video_data` (ou `ranking_snapshot` no Motores)
2. **Deteccao de novos**: Proximo run compara dados atuais vs snapshot anterior
3. **Skip LLM**: Se zero dados novos, reutiliza relatorio anterior (economiza tokens OpenAI)
4. **Run number**: Contador sequencial por canal (`run_number` incrementa a cada execucao)
5. **Banner no relatorio**: Mensagem no topo indicando se houve dados novos ou reutilizacao

### Banner Incremental (aparece no topo do relatorio)

Sem dados novos:
```
>> Run #2 -- Nenhum video novo detectado desde a ultima analise.
>> Relatorio anterior reutilizado. Proxima analise com dados novos gerara atualizacao completa.
```

Com dados novos:
```
>> Run #3 -- 5 video(s) novo(s) detectado(s) (de 45 total). Analise focada nos novos.
```

### Memoria Acumulativa LLM

Todos os agentes passam o relatorio anterior completo para a LLM como "memoria acumulativa". A LLM deve:
- Se basear no relatorio anterior como referencia
- Verificar se recomendacoes anteriores foram implementadas
- Confirmar ou revisar tendencias com numeros
- Construir em cima, nunca ignorar o historico

### Configuracao LLM Compartilhada

| Config | Valor |
|--------|-------|
| Modelo | GPT-4o-mini (configuravel via `OPENAI_MODEL`) |
| max_tokens | Nao definido (evita truncacao) |
| Retry | 2 tentativas |
| Fallback | Se LLM falha, relatorio e gerado sem secao LLM |

### Funcoes Compartilhadas (importadas do Copy Agent)

O `copy_analysis_agent.py` exporta funcoes reutilizadas pelos outros:

- `_get_channel_info(channel_id)` — busca dados do canal em `yt_channels`
- `_normalize_title(title)` — normaliza titulo para comparacao
- `read_copy_structures(spreadsheet_id)` — le planilha de copy (Col A = estrutura, Col B = titulo)
- `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_HEADERS` — configuracao de banco
- `VALID_STRUCTURES` — letras validas (A-Z)

### Formato de Retorno Padrao

Todos retornam:
```python
# Sucesso
{"success": True, "channel_name": "...", "run_id": 123, "report": "...", "summary": {...}}

# Falha
{"success": False, "error": "mensagem de erro"}
```

---

## Agente 1: Copy (copy_analysis_agent.py)

### Proposito

Analisa a **performance de cada estrutura de copy** (letras A-G) com base em retencao, watch time e views. Responde: "Qual estrutura de copy performa melhor neste canal?"

### Por Que Existe

Cada video usa uma estrutura narrativa (ex: A = Cronologico, B = Problema-Solucao). Saber qual performa melhor permite otimizar a producao — usar mais as que funcionam, menos as que nao.

### Fonte de Dados

1. **Planilha de Copy** (`copy_spreadsheet_id`) — Col A = letra da estrutura, Col B = titulo
2. **Supabase** (`yt_video_metrics`) — retencao, views, watch time por video
3. **YouTube Analytics API** — fallback se video nao esta no banco

### Fluxo Detalhado

```
1. Buscar dados do canal (yt_channels)
2. Ler planilha de copy (Col A + Col B)
3. Match titulos da planilha com videos do Supabase (3 niveis):
   - Match exato
   - Match normalizado (lowercase, sem pontuacao)
   - Match por similaridade (90% threshold, palavra a palavra)
4. Buscar metricas de retencao (banco primeiro, API fallback)
5. Filtrar: >= 7 dias de maturidade, retencao nao-nula
6. Agrupar por estrutura:
   - >= 3 videos: analise completa (media, desvio, classificacao)
   - < 3 videos: vai para "dados insuficientes"
7. Calcular media geral do canal
8. Classificar cada estrutura: ACIMA (>+2%), MEDIA, ABAIXO (<-2%)
9. Detectar anomalias (views 5x acima/abaixo, retencao 15%+ diferente)
10. INCREMENTAL: detectar videos novos via snapshot
11. LLM: gerar observacoes + tendencias
12. Gerar relatorio formatado
13. Salvar no banco (copy_analysis_runs)
```

### Metricas

| Metrica | Fonte | Uso |
|---------|-------|-----|
| Retencao % | yt_video_metrics / Analytics API | Metrica primaria de ranking |
| Watch Time (min) | yt_video_metrics / Analytics API | Contexto de engajamento |
| Views | yt_video_metrics / Analytics API | Volume de audiencia |

### LLM

| Config | Valor |
|--------|-------|
| Temperature | 0.3 |
| Calls por run | 1 |
| Output | 2 blocos: `[OBSERVACOES]` + `[TENDENCIAS]` |

**`[OBSERVACOES]` cobre 8 pontos obrigatorios:**
1. Lideranca: qual estrutura lidera e por que
2. Consistencia: desvio padrao alto/baixo por estrutura
3. Tema vs Copy: relacao entre temas dos videos e a estrutura usada
4. Pior performance: qual estrutura e por que
5. Distribuicao de producao: concentracao vs diversificacao
6. Anomalias: videos flagged e explicacao
7. Watch time vs Retencao: correlacao ou divergencia
8. Outros padroes detectados

**`[TENDENCIAS]` cobre evolucao temporal:**
- Score anterior vs atual (numeros exatos)
- Estruturas que subiram ou cairam no ranking
- Recomendacoes anteriores implementadas ou nao

### Nota sobre API Fallback

Quando um video nao tem metricas no banco (`yt_video_metrics`), o agente busca via YouTube Analytics API usando credenciais OAuth do canal. Metricas buscadas: `averageViewDuration`, `averageViewPercentage`, `views`. Requer OAuth configurado.

### Incremental

- **Snapshot**: `{video_id: {views, retention_pct, watch_time_min, structure}}`
- **Deteccao**: Novo = video_id nao existe no snapshot anterior
- **Zero novos**: Extrai `[OBSERVACOES]` e `[TENDENCIAS]` do report anterior, pula LLM

### Banco de Dados

| Tabela | Campos principais |
|--------|-------------------|
| `copy_analysis_runs` | channel_id, run_number, report_text, results_json, analyzed_video_data, channel_avg_retention |

### Endpoints

| Metodo | Rota | Descricao |
|--------|------|-----------|
| POST | `/api/analise-copy/{id}` | Rodar analise |
| POST | `/api/analise-copy/run-all` | Rodar todos os canais |
| GET | `/api/analise-copy/{id}/latest` | Ultimo relatorio |
| GET | `/api/analise-copy/{id}/historico` | Historico paginado |
| GET | `/api/analise-copy/{id}/run/{run_id}` | Buscar run especifico |
| GET | `/api/analise-copy/{id}/videos` | Videos matched (filtro por estrutura) |

### Constantes

```python
MIN_MATURITY_DAYS = 7        # Dias minimos para incluir video
MIN_SAMPLE_SIZE = 3          # Videos minimos por estrutura
CLASSIFICATION_MARGIN = 2.0  # +/- 2% para ACIMA/ABAIXO
ANOMALY_VIEWS_MULTIPLIER = 5 # Views 5x acima/abaixo = anomalia
ANOMALY_RETENTION_DIFF = 15  # Retencao 15%+ diferente = anomalia
```

---

## Agente 2: Satisfacao (satisfaction_agent.py)

### Proposito

Analisa a **satisfacao do publico** por estrutura de copy, usando likes, dislikes, inscritos ganhos e comentarios. Responde: "Qual estrutura de copy deixa a audiencia mais satisfeita?"

### Por Que Existe

Performance (retencao/views) nao e tudo. Um video pode ter muitas views mas dislikes altos. A satisfacao mede o SENTIMENTO do publico — se ele aprova, se inscreve, se comenta. Complementa o Copy Agent.

### Fonte de Dados

1. **Copy Agent** — herda os videos matched (nao refaz o match)
2. **Supabase** (`yt_video_metrics`) — likes, dislikes, subscribers_gained
3. **Supabase** (`videos_historico`) — comentarios
4. **YouTube Analytics API** — fallback para metricas faltantes

### Fluxo Detalhado

```
1. Buscar dados do canal
2. Carregar videos matched do ultimo run de Copy (NAO le planilha)
3. Buscar metricas de satisfacao (3 camadas):
   a. yt_video_metrics (likes, dislikes, subs_gained, views)
   b. videos_historico (comentarios)
   c. YouTube Analytics API (fallback)
4. Calcular por video:
   - Approval Rate = likes / (likes + dislikes) * 100
   - Like Ratio = likes / views * 100
   - Sub Ratio = subs_gained / views * 100
   - Comment Ratio = comentarios / views * 100
5. Agrupar por estrutura (>= 3 videos)
6. Calcular score composto: 60% Sub Ratio + 40% Approval
7. Classificar: ACIMA (>55), MEDIA, ABAIXO (<45)
8. Detectar anomalias (sub ratio 3x, approval 15%+ diferente)
9. INCREMENTAL: detectar videos novos via snapshot
10. LLM: gerar observacoes + tendencias
11. Gerar relatorio formatado
12. Salvar no banco (satisfaction_analysis_runs)
```

### Metricas

| Metrica | Formula | Peso no Score |
|---------|---------|---------------|
| Sub Ratio | subs_gained / views * 100 | 60% |
| Approval Rate | likes / (likes + dislikes) * 100 | 40% |
| Like Ratio | likes / views * 100 | Informativo (nao entra no score) |
| Comment Ratio | comments / views * 100 | Informativo (nao entra no score) |

### LLM

| Config | Valor |
|--------|-------|
| Temperature | 0.3 |
| Calls por run | 1 |
| Output | 2 blocos: `[OBSERVACOES]` + `[TENDENCIAS]` |
| Incremental | 5 pontos especificos de satisfacao |

### Incremental

- **Snapshot**: `{video_id: {views, likes, approval, sub_ratio, structure}}`
- **Deteccao**: Novo = video_id nao existe no snapshot anterior
- **Zero novos**: Extrai do report anterior via headers

### Banco de Dados

| Tabela | Campos principais |
|--------|-------------------|
| `satisfaction_analysis_runs` | channel_id, run_number, report_text, results_json, analyzed_video_data, channel_avg_approval, channel_avg_sub_ratio |

### Endpoints

| Metodo | Rota | Descricao |
|--------|------|-----------|
| POST | `/api/analise-satisfacao/{id}` | Rodar analise |
| POST | `/api/analise-satisfacao/run-all` | Rodar todos |
| GET | `/api/analise-satisfacao/{id}/latest` | Ultimo relatorio |
| GET | `/api/analise-satisfacao/{id}/historico` | Historico paginado |
| GET | `/api/analise-satisfacao/{id}/run/{run_id}` | Buscar run especifico |
| DELETE | `/api/analise-satisfacao/{id}/run/{run_id}` | Deletar run |

### Constantes

```python
SATISFACTION_WEIGHT_SUB = 0.60              # Peso do Sub Ratio
SATISFACTION_WEIGHT_APPROVAL = 0.40         # Peso do Approval
MIN_MATURITY_DAYS = 7
MIN_SAMPLE_SIZE = 3
ANOMALY_SATISFACTION_MULTIPLIER = 3.0       # Sub ratio 3x acima/abaixo = anomalia
```

### Edge Cases de Dados

O agente detecta automaticamente se o canal tem dados de dislikes e inscritos:

| Cenario | Aviso no relatorio | Impacto no score |
|---------|-------------------|-----------------|
| Sem dislikes E sem subs | "Scores NAO sao confiaveis (todos serao ~50)" | Score perde sentido |
| Sem dislikes | "Approval calculado sem dislikes" | Approval sempre ~100% |
| Sem subs | "Score calculado sem Sub Ratio" | Score = 100% Approval |
| Ambos disponiveis | Score normal (60/40) | Confiavel |

---

## Agente 3: Autenticidade (authenticity_agent.py)

### Proposito

Calcula um **Score de Autenticidade (0-100)** que mede o risco de o canal ser flagged por "Inauthentic Content" pelo YouTube. Quanto MAIOR o score, mais seguro. Responde: "Este canal parece automatizado/template-based?"

### Por Que Existe

O YouTube derruba canais que parecem "produzidos em massa, baseados em template". Isso NAO e sobre qualidade — e sobre PADRAO DE PRODUCAO. Um canal excelente pode ser derrubado se PARECE automatizado. Este agente e um sistema de alerta precoce.

### Fonte de Dados

1. **Planilha de Copy** (`copy_spreadsheet_id`) — Col A = estrutura, Col B = titulo
2. NAO usa videos do Supabase (analisa apenas a planilha)

### Fluxo Detalhado

```
1. Buscar dados do canal
2. Ler planilha de copy (estruturas + titulos)
3. Calcular FATOR 1 — Variedade de Estruturas (score 0-100):
   - Dominancia: % da estrutura mais usada (50% do fator)
   - Entropia de Shannon: "desordem" da distribuicao (35%)
   - Quantidade de estruturas unicas (15%)
4. Calcular FATOR 2 — Diversidade de Titulos (score 0-100):
   - Similaridade media entre pares de titulos (40%)
   - Padrao serial: "Parte 1", "Ep 2", etc. (15%)
   - Keyword stuffing: mesma palavra em muitos titulos (30%)
   - Variacao de comprimento (15%)
5. Composite Score = 50% Estruturas + 50% Titulos
6. Nivel: EXCELENTE (80+), BOM (60-79), ATENCAO (40-59), RISCO (20-39), CRITICO (0-19)
7. Comparar com analise anterior
8. Gerar alertas:
   - Score < 40 (zona de risco)
   - Fator individual < 30 (fator critico)
   - Queda > 15 pontos (deterioracao rapida)
9. INCREMENTAL: detectar titulos novos via snapshot
10. LLM: gerar diagnostico + recomendacoes + tendencias
11. Gerar relatorio formatado
12. Salvar no banco (authenticity_analysis_runs)
```

### Metricas

| Sub-metrica | Peso | O que mede |
|-------------|------|------------|
| **Fator Estruturas (50%)** | | |
| Dominancia | 50% do fator | % da estrutura mais usada. >80% = CRITICO |
| Entropia Shannon | 35% do fator | Distribuicao entre estruturas. Baixa = repetitivo |
| Quantidade unicas | 15% do fator | Quantas estruturas diferentes usa |
| **Fator Titulos (50%)** | | |
| Similaridade media | 40% do fator | Pares de titulos parecidos (Jaccard) |
| Padrao serial | 15% do fator | "Parte 1", "Ep 2", etc. |
| Keyword stuffing | 30% do fator | Mesma palavra em muitos titulos |
| Variacao comprimento | 15% do fator | Desvio padrao do tamanho dos titulos |

### Stopwords (5 idiomas)

A analise de keyword stuffing e similaridade entre titulos remove stopwords em 5 idiomas: Portugues, Ingles, Espanhol, Alemao, Frances. Isso evita falsos positivos (ex: "O" e "The" nao contam como keyword repetida).

### Near-Duplicates

O sistema detecta automaticamente titulos quase identicos (similaridade >75%):
- "O Rei Mais Cruel da Idade Media" vs "O Rei Mais Sanguinario da Idade Media"
- Este e o trigger MAIS FORTE para Inauthentic Content

### LLM

| Config | Valor |
|--------|-------|
| Temperature | 0.3 |
| Calls por run | 1 |
| Output | 3 blocos: `[DIAGNOSTICO]` + `[RECOMENDACOES]` + `[TENDENCIAS]` |
| Incremental | 4 pontos especificos de autenticidade |

### Incremental

- **Snapshot**: `{titulo_normalizado: {structure, title}}`
- **Deteccao**: Novo = titulo normalizado (lowercase, strip) nao existe no snapshot anterior
- **Zero novos**: Extrai diagnostico/recomendacoes/tendencias do report anterior via headers

### Banco de Dados

| Tabela | Campos principais |
|--------|-------------------|
| `authenticity_analysis_runs` | channel_id, run_number, report_text, authenticity_score, structure_score, title_score, results_json, analyzed_video_data, has_alerts, alert_count |

### Endpoints

| Metodo | Rota | Descricao |
|--------|------|-----------|
| POST | `/api/analise-autenticidade/{id}` | Rodar analise |
| GET | `/api/analise-autenticidade/{id}/latest` | Ultimo relatorio |
| GET | `/api/analise-autenticidade/{id}/historico` | Historico paginado |
| GET | `/api/analise-autenticidade/{id}/run/{run_id}` | Buscar run especifico |
| GET | `/api/analise-autenticidade/overview` | Scores de todos os canais |

### Constantes

```python
STRUCTURE_WEIGHT = 0.50
TITLE_WEIGHT = 0.50
LEVEL_EXCELENTE = 80
LEVEL_BOM = 60
LEVEL_ATENCAO = 40
LEVEL_RISCO = 20
ALERT_SCORE_THRESHOLD = 40
ALERT_FACTOR_THRESHOLD = 30
ALERT_SPIKE_THRESHOLD = 15
```

---

## Agente 4: Temas (theme_agent.py)

### Proposito

Identifica o **tema** de cada video e gera **hipoteses de motores psicologicos** — padroes invisiveis que explicam POR QUE a audiencia clica. Responde: "Quais temas e gatilhos psicologicos fazem este canal viralizar?"

### Por Que Existe

Retencao e views dizem O QUE performou. Temas e motores dizem POR QUE performou. Um tema como "Mulheres Vitimas na Historia" pode ter um motor "Empatia + Injustica" que explica o engajamento. Saber isso permite replicar o sucesso de forma consciente.

### Fonte de Dados

1. **Supabase** (`videos_historico`) — titulos, views, data de publicacao
2. **Supabase** (`yt_video_metrics`) — CTR, impressoes
3. **Supabase** (`yt_channels`) — CTR medio do canal

### Fluxo Detalhado

```
1. Buscar dados do canal
2. Buscar videos (videos_historico) + CTR (yt_video_metrics)
3. Filtrar: >= 7 dias, >= 500 views, minimo 5 videos
4. Calcular score por video: 50% CTR + 50% Views (min-max normalizado 0-100)
5. Ranquear todos os videos por score
6. INCREMENTAL: detectar novos + atualizados via snapshot
   - Novo: video_id nao existe no snapshot
   - Atualizado: views +20% OU CTR +/-2pp
7. LLM TEMAS (JSON): para cada video novo/atualizado:
   - Tema concreto (ex: "Mulheres Vitimas na Idade Media")
   - 2-4 hipoteses de motores (ex: "Empatia + Injustica")
   - Catalogo de motores do canal
   - Anti-patterns identificados
   - Interacoes entre motores
8. MERGE: novos + atualizados recebem temas da LLM, unchanged mantem do snapshot
9. CORRELACOES (Python, sempre recalculado):
   - Para cada motor: score medio COM vs SEM
   - CTR medio COM vs SEM
10. Gerar relatorio formatado
11. Salvar no banco (theme_analysis_runs)
```

### Metricas

| Metrica | Formula | Peso no Score |
|---------|---------|---------------|
| CTR | impressoes → cliques (%) | 50% |
| Views | total de visualizacoes | 50% |
| Score | min-max normalizado 0-100 | — |

### LLM

| Config | Valor |
|--------|-------|
| Temperature | 0.3 |
| Calls por run | 1 |
| Output | JSON estruturado |
| Formato JSON | `{videos, catalogo_motores, anti_patterns, interacoes_motores}` |
| Response format | `json_object` (forcado) |
| Fallback | Se LLM falha apos 2 tentativas, usa titulo[:80] como tema e hipoteses vazias |

### Output JSON da LLM

```json
{
  "videos": [
    {
      "video_id": "abc123",
      "tema": "Mulheres Vitimas na Idade Media",
      "hipoteses": [
        {"motor": "Empatia + Injustica", "explicacao": "..."},
        {"motor": "Curiosidade Morbida", "explicacao": "..."}
      ]
    }
  ],
  "catalogo_motores": [
    {"motor": "Empatia + Injustica", "descricao": "...", "vocabulario": [...]}
  ],
  "anti_patterns": [
    {"nome": "Template Generico", "descricao": "...", "impacto": "..."}
  ],
  "interacoes_motores": [
    {"combinacao": "Empatia + Curiosidade", "tipo": "amplifica", "explicacao": "..."}
  ]
}
```

### Correlacoes (calculadas em Python)

Para cada motor do catalogo:
```
Motor "Empatia + Injustica":
  COM: 8 videos, score medio 72, CTR medio 4.2%
  SEM: 12 videos, score medio 45, CTR medio 2.8%
  → Videos COM este motor performam 60% melhor
```

### Incremental

- **Snapshot**: `{video_id: {views, ctr, score, tema, hipoteses}}`
- **Deteccao dupla**:
  - Novo: video_id nao existe no snapshot
  - Atualizado: views aumentou >20% OU CTR mudou >2pp
- **Zero novos + zero atualizados**: Reutiliza themes_json do run anterior, gera report com banner

### Banco de Dados

| Tabela | Campos principais |
|--------|-------------------|
| `theme_analysis_runs` | channel_id, run_number, report_text, ranking_json, themes_json, analyzed_video_data, themes_list, patterns_json |

### Endpoints

| Metodo | Rota | Descricao |
|--------|------|-----------|
| POST | `/api/analise-temas/{id}` | Rodar analise |
| POST | `/api/analise-temas/run-all` | Rodar todos |
| GET | `/api/analise-temas/{id}/latest` | Ultimo relatorio |
| GET | `/api/analise-temas/{id}/historico` | Historico paginado |
| GET | `/api/analise-temas/{id}/run/{run_id}` | Buscar run especifico |
| DELETE | `/api/analise-temas/{id}/run/{run_id}` | Deletar run |

### Constantes

```python
MIN_VIDEOS = 5
MIN_VIEWS = 500
MATURITY_DAYS = 7
CTR_WEIGHT = 0.5
VIEWS_WEIGHT = 0.5
TOP_N = 15
VIEWS_CHANGE_PCT = 0.20  # +20% para detectar "atualizado"
CTR_CHANGE_PP = 0.02     # +2pp para detectar "atualizado"
```

---

## Agente 5: Motores (motor_agent.py)

### Proposito

Gera uma **analise estrategica narrativa** dos motores psicologicos, com recomendacoes praticas de producao. Responde: "Quais videos produzir agora para maximizar viralidade?"

### Por Que Existe

O Agente de Temas identifica OS motores. O Agente de Motores INTERPRETA esses motores e transforma em acao. Ele e o "cerebro estrategico" que diz exatamente o que produzir, o que evitar, e o que testar.

### Fonte de Dados

1. **Agente de Temas** (run mais recente) — ranking, themes_json, catalogo, correlacoes
2. NAO acessa banco diretamente para videos (tudo vem do Temas)

### DEPENDENCIA CRITICA

O Agente de Motores **NAO funciona** sem um run do Agente de Temas. Se nao existe `theme_analysis_runs` para o canal, retorna erro: "Rode o Agente de Temas primeiro."

### Fluxo Detalhado

```
1. Carregar ultimo run de Temas (theme_analysis_runs)
2. Extrair: ranking_json (videos), themes_json (catalogo, correlacoes)
3. Buscar dados do canal (channel_info)
4. Contar motores atuais (frequencia, score medio, %)
5. Buscar run anterior de Motores (motor_analysis_runs)
6. INCREMENTAL: detectar mudancas via ranking_snapshot
   - Novo: video_id nao existe no snapshot anterior
   - Atualizado: views +20% OU CTR +/-2pp
7. Se zero mudancas: reutilizar relatorio anterior com banner
8. LLM MOTORES (narrativa estrategica):
   - Run #1: prompt completo com catalogo + top/bottom
   - Run #2+: prompt 3 blocos (anterior + mudancas + dados gerais)
9. Prepend banner no output
10. Salvar no banco (motor_analysis_runs)
```

### LLM

| Config | Valor |
|--------|-------|
| Temperature | 0.4 (mais criativo que os outros) |
| Calls por run | 1 |
| Output | Narrativa estrategica em texto |

**Prompt incremental (Run #2+) — 3 blocos:**
1. **BLOCO 1 — Relatorio anterior**: texto completo do run anterior como memoria
2. **BLOCO 2 — O que mudou**: videos novos + videos atualizados com deltas (views anterior→atual, CTR anterior→atual)
3. **BLOCO 3 — Dados gerais**: catalogo de motores + correlacoes + top 5 videos + bottom 3 videos

### Output LLM (4 secoes)

```
[FORMULA DE PERFORMANCE]
- FORMULA VENCEDORA: motores que dominam o top + evidencias
- FORMULA TOXICA: anti-patterns + evidencias
- DNA DO CANAL: 1-2 motores essenciais

[RECOMENDACOES]
- PRODUZIR MAIS: 3-5 titulos concretos na lingua do canal + analise de motores
- DIVERSIFICAR: como expandir sem perder motores-chave
- EVITAR: o que NAO produzir + motivo
- REFORMULAR: temas fracos que podem ser salvos

[HIPOTESES PARA TESTAR]
- 3-5 hipoteses testaveis com validacao por motores

[PRIORIDADES PRATICAS]
- IMEDIATO: proximos 1-2 videos + motores + justificativa
- CURTO PRAZO: testes de 2 semanas
- ESTRATEGICO: direcao mensal
```

### Incremental

- **Snapshot**: `ranking_snapshot` (copia do merged_data do Temas)
- **Deteccao**: Mesmos thresholds do Temas (views +20%, CTR +/-2pp)
- **Zero mudancas**: Prepend banner + reutiliza report anterior
- **Guard defensivo**: Se `prev_report` e None no skip, retorna erro claro

### Banco de Dados

| Tabela | Campos principais |
|--------|-------------------|
| `motor_analysis_runs` | channel_id, run_number, report_text, motor_counts_json, theme_run_id (FK), ranking_snapshot, total_videos, is_first_analysis |

### Endpoints

| Metodo | Rota | Descricao |
|--------|------|-----------|
| POST | `/api/analise-motores/{id}` | Rodar analise (requer Temas) |
| POST | `/api/analise-motores/run-all` | Rodar todos com Temas |
| GET | `/api/analise-motores/{id}/latest` | Ultimo relatorio |
| GET | `/api/analise-motores/{id}/historico` | Historico paginado |
| GET | `/api/analise-motores/{id}/run/{run_id}` | Buscar run especifico |
| DELETE | `/api/analise-motores/{id}/run/{run_id}` | Deletar run |

---

## Tabela Comparativa Final

| | Copy | Satisfacao | Autenticidade | Temas | Motores |
|---|---|---|---|---|---|
| **Arquivo** | copy_analysis_agent.py | satisfaction_agent.py | authenticity_agent.py | theme_agent.py | motor_agent.py |
| **Linhas** | ~1920 | ~1600 | ~1520 | ~1420 | ~860 |
| **Tabela** | copy_analysis_runs | satisfaction_analysis_runs | authenticity_analysis_runs | theme_analysis_runs | motor_analysis_runs |
| **Calls LLM** | 1 | 1 | 1 | 1 | 1 |
| **Temperatura** | 0.3 | 0.3 | 0.3 | 0.3 | 0.4 |
| **Output LLM** | Texto (2 blocos) | Texto (2 blocos) | Texto (3 blocos) | JSON estruturado | Texto (4 secoes) |
| **Fonte dados** | Planilha + Supabase | Copy Agent + Supabase | Planilha | Supabase direto | Agente Temas |
| **Score** | Por estrutura | 60/40 Sub/Approval | 50/50 Struct/Title | 50/50 CTR/Views | N/A (narrativo) |
| **Incremental** | video_id snapshot | video_id snapshot | titulo snapshot | video_id + views/CTR | ranking snapshot |
| **Detecta "atualizado"** | Nao | Nao | Nao | Sim (+20% views, +2pp CTR) | Sim |
| **Depende de** | Nenhum | Copy | Nenhum (imports do Copy) | Nenhum (imports do Copy) | Temas |

---

## Migrations Necessarias

| Migration | Tabela | Colunas adicionadas |
|-----------|--------|---------------------|
| 026_incremental_columns.sql | copy_analysis_runs, satisfaction_analysis_runs | analyzed_video_data JSONB, run_number INTEGER |
| 027_authenticity_incremental.sql | authenticity_analysis_runs | analyzed_video_data JSONB, run_number INTEGER |
| 023_theme_agent_v2.sql | theme_analysis_runs | analyzed_video_data JSONB, run_number INTEGER, themes_json JSONB |

---

## Fluxo de Producao Completo

```
COLETA (automatica, diaria):
  collector.py → videos novos
  ctr_collector.py → CTR/impressoes (semanal)
  monetization_oauth_collector.py → likes/dislikes/subs

ANALISE (sob demanda ou agendada):
  POST /api/analise-completa/{id}
    1. Copy Agent → "Qual estrutura performa?"
    2. Satisfacao Agent → "O publico esta satisfeito?"
    3. Autenticidade Agent → "O canal parece automatizado?"
    4. Temas Agent → "Quais temas viralizam e por que?"
    5. Motores Agent → "O que produzir agora?"

CONSUMO:
  /dash-agentes → Dashboard visual dos agentes
  /dash-analise-copy → Dashboard detalhado de copy
  /mission-control → Centro de comando geral
```

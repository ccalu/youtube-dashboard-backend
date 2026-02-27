# Mission Control - Documentacao Completa

> Documento vivo — atualizado conforme novos agentes sao implementados.
> Ultima atualizacao: 27/02/2026 (Agentes 1-5 implementados)

## O que e

Escritorio virtual 2D estilo Gather.town onde cada canal YouTube = 1 sala. Dentro de cada sala trabalham 7 agentes IA representados por bonequinhos pixelados (sprites LiMEZu 48x72px). O Mission Control e o CENTRO DE COMANDO de toda a operacao — orquestra e visualiza cada canal individualmente.

**URL:** `/mission-control` (Railway producao)
**Arquivo principal:** `mission_control.py` (~4600 linhas — backend Python + HTML/CSS/JS inline)

---

## Arquitetura

```
Browser (Canvas 2D)                          Backend (FastAPI)
========================                     ========================

 GET /mission-control ------>  HTMLResponse   mission_control.py
       (pagina completa)                     MISSION_CONTROL_HTML

 GET /api/mission-control/    JSON           get_mission_control_data()
     status  (polling 8s) -->                  - Busca canais do Supabase (MV)
                                               - Agrupa por subnicho (7 setores)
                                               - Consulta status real dos agentes
                                               - Cache 5s

 GET /api/mission-control/    JSON           get_sala_detail()
     sala/{canal_id}  ------->                 - Detalhes do canal
                                               - Agentes + chat + tarefas
                                               - Cache 3s

 POST /api/mission-control/   JSON           mission_control_refresh()
      refresh  -------------->                 - Refresh Materialized View
                                               - Limpa cache MC (nao do dash)
```

---

## Ecossistema de 7 Agentes

### Visao Geral

Cada canal recebe 7 agentes especializados organizados em 4 camadas. O objetivo e maximizar viralizacao + faturamento + protecao contra Inauthentic Content.

```
                    ┌─────────────────────────────────────┐
                    │         YOUTUBE API (dados)          │
                    └──────────┬──────────────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                    ▼
  ┌───────────────┐  ┌─────────────────┐  ┌──────────────┐
  │  CAMADA 1     │  │   CAMADA 2      │  │  CAMADA 4    │
  │  Diagnostico  │  │ Analise Espec.  │  │ Intel Compet.│
  │               │  │                 │  │              │
  │ Ag.1 Copy  ✅ │  │ Ag.3 Micro  ✅  │  │ Ag.7 Concorr.│
  │ Ag.2 Auth  ✅ │  │ Ag.4 Titulo ✅  │  │    (futuro)  │
  │               │  │ Ag.5 Temas  ✅  │  │              │
  └───────┬───────┘  └────────┬────────┘  └──────┬───────┘
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
                    ┌─────────────────┐
                    │   CAMADA 3      │
                    │   Decisao       │
                    │                 │
                    │ Ag.6 Recomend.  │
                    │   (futuro)      │
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │    OUTPUT       │
                    │ Lista de videos │
                    │  recomendados   │
                    └─────────────────┘
```

### Hierarquia de Conteudo

```
Nicho (ex: Dark History)
  └── Subnicho (ex: canal "Archives de Guerre")
        └── Micronicho (Ag.3) — subcategoria (ex: "Campos de Concentracao")
              └── Tema (Ag.5) — assunto concreto (ex: "Fuga de Lederer de Auschwitz")
```

---

## Os 7 Agentes — Detalhes

### Agente 1: Estrutura de Copy ✅

| Campo | Valor |
|-------|-------|
| **Arquivo** | `copy_analysis_agent.py` (~1670 linhas) |
| **Camada** | 1 — Diagnostico |
| **Cor** | `#22c55e` (verde) |
| **Tipo MC** | `estrutura_copy` |
| **Tabela** | `copy_analysis_runs` |
| **Status** | ✅ Implementado e ativo no Mission Control |

**O que faz:** Analisa qual estrutura de copy (A-G) performa melhor em cada canal usando retencao % como metrica primaria.

**Metrica:** Retencao % (YouTube Analytics API)

**Dados:** Google Sheets (`copy_spreadsheet_id`) + YouTube Analytics API (retencao)

**LLM:** 1 chamada — GPT-4o-mini, temp 0.3 (narrativa analitica)

**Endpoints:**
- `POST /api/analise-copy/{channel_id}` — Roda analise
- `POST /api/analise-copy/run-all` — Roda todos
- `GET /api/analise-copy/{channel_id}/latest` — Ultima analise
- `GET /api/analise-copy/{channel_id}/historico` — Historico
- `GET /api/analise-copy/{channel_id}/videos` — Mapeamento de videos

**Requisitos:** Canal com `copy_spreadsheet_id` + OAuth configurado

---

### Agente 2: Autenticidade ✅

| Campo | Valor |
|-------|-------|
| **Arquivo** | `authenticity_agent.py` (~1345 linhas) |
| **Camada** | 1 — Diagnostico |
| **Cor** | `#ef4444` (vermelho) |
| **Tipo MC** | `autenticidade` |
| **Tabela** | `authenticity_analysis_runs` |
| **Status** | ✅ Implementado e ativo no Mission Control |

**O que faz:** Gera Score de Autenticidade (0-100, maior = mais seguro). Analisa diversidade de estruturas de copy e unicidade de titulos. Detecta padroes que violam a politica de Inauthentic Content do YouTube.

**Metrica:** Score 0-100 (50% variancia de estrutura + 50% diversidade de titulo)

**Dados:** Google Sheets (`copy_spreadsheet_id`)

**LLM:** 1 chamada — GPT-4o-mini, temp 0.3 (diagnostico + recomendacoes)

**Endpoints:**
- `GET /api/analise-autenticidade/{channel_id}/latest` — Ultimo score
- `GET /api/analise-autenticidade/{channel_id}/historico` — Historico
- `GET /api/analise-autenticidade/overview` — Resumo de todos os canais

**Requisitos:** Canal com `copy_spreadsheet_id`

**Sidebar MC:** Score com cor (verde >= 70, amarelo >= 40, vermelho < 40) + nivel + alertas

---

### Agente 3: Micronichos ✅

| Campo | Valor |
|-------|-------|
| **Arquivo** | `micronicho_agent.py` (~530 linhas) |
| **Camada** | 2 — Analise Especializada |
| **Cor** | `#8b5cf6` (roxo) |
| **Tipo MC** | `micronichos` |
| **Tabela** | `micronicho_analysis_runs` |
| **Status** | ✅ Implementado e ativo no Mission Control |

**O que faz:** Classifica videos em subcategorias tematicas (micronichos) e rankeia por views medias. Identifica quais subcategorias viralizam mais dentro do canal.

**Metrica:** Views brutas (media por micronicho) — NAO usa retencao/CTR

**Dados:** Supabase `videos_historico` (NAO precisa de planilha nem OAuth)

**LLM:** 2 chamadas:
- Call 1: GPT-4o-mini, temp 0.3 (classifica videos em micronichos — JSON)
- Call 2: GPT-4o-mini, temp 0.4 (narrativa: [OBSERVACOES] + [RECOMENDACOES] + [TENDENCIAS])

**Endpoints:**
- `POST /api/analise-micronichos/{channel_id}` — Roda analise
- `POST /api/analise-micronichos/run-all` — Roda todos
- `GET /api/analise-micronichos/{channel_id}/latest` — Ultima analise
- `GET /api/analise-micronichos/{channel_id}/historico` — Historico

**Requisitos:** Canal ativo com 5+ videos com 7+ dias de maturidade

**Notas criticas:**
- `videos_historico.canal_id` = INTEGER (canais_monitorados.id), NAO UC... string
- `_get_monitorado_id()` faz o mapeamento UC... → integer
- `data_publicacao` pode ser naive datetime — usar `.replace(tzinfo=timezone.utc)`

**Sidebar MC:** Count de micronichos + Top micronicho

---

### Agente 4: Estrutura de Titulo ✅

| Campo | Valor |
|-------|-------|
| **Arquivo** | `title_structure_agent.py` (~550 linhas) |
| **Camada** | 2 — Analise Especializada |
| **Cor** | `#3b82f6` (azul) |
| **Tipo MC** | `titulo_estrutura` |
| **Tabela** | `title_structure_analysis_runs` |
| **Status** | ✅ Implementado e ativo no Mission Control |

**O que faz:** Identifica padroes estruturais de titulo (formulas com [VARIAVEIS]). Rankeia por score ponderado de CTR e views. Detecta divergencias entre CTR e views.

**Metrica:** Score = 60% CTR + 40% Views (normalizado min-max 0-100)

**Dados:** JOIN de `videos_historico` + `yt_video_metrics` (EXIGE CTR)

**LLM:** 2 chamadas:
- Call 1: GPT-4o-mini, temp 0.3 (classifica titulos em estruturas sintaticas — JSON)
- Call 2: GPT-4o-mini, temp 0.4 (narrativa analitica + divergencia CTR vs Views)

**Endpoints:**
- `POST /api/analise-titulo/{channel_id}` — Roda analise
- `POST /api/analise-titulo/run-all` — Roda todos
- `GET /api/analise-titulo/{channel_id}/latest` — Ultima analise
- `GET /api/analise-titulo/{channel_id}/historico` — Historico

**Requisitos:** Canal com 5+ videos COM CTR (YouTube Reporting API ativo)

**UNICO agente que exige CTR** — videos sem CTR sao excluidos da analise

**Sidebar MC:** Count de estruturas + Top estrutura

---

### Agente 5: Temas ✅

| Campo | Valor |
|-------|-------|
| **Arquivo** | `theme_agent.py` (~700 linhas) |
| **Camada** | 2 — Analise Especializada |
| **Cor** | `#f97316` (laranja) |
| **Tipo MC** | `temas` |
| **Tabela** | `theme_analysis_runs` |
| **Status** | ✅ Implementado e ativo no Mission Control |

**O que faz:** Identifica o ASSUNTO CONCRETO de cada video (ultimo nivel da hierarquia). Rankeia por score ponderado de velocity e views. Skill exclusiva: decomposicao em elementos constitutivos + hipoteses de adjacencia tematica.

**Metrica:** Score = 50% Velocity (views/dia) + 50% Views (normalizado min-max 0-100)

**Dados:** Supabase `videos_historico` (NAO precisa de planilha nem OAuth)

**LLM:** 2 chamadas:
- Call 1: GPT-4o-mini, temp 0.3 (extrai tema especifico de cada titulo — JSON)
- Call 2: GPT-4o-mini, temp 0.4 (decomposicao + hipoteses: [RANKING] + [DECOMPOSICAO] + [PADROES])

**Endpoints:**
- `POST /api/analise-temas/{channel_id}` — Roda analise
- `POST /api/analise-temas/run-all` — Roda todos
- `GET /api/analise-temas/{channel_id}/latest` — Ultima analise
- `GET /api/analise-temas/{channel_id}/historico` — Historico

**Requisitos:** Canal ativo com 5+ videos com 7+ dias de maturidade

**Conceitos chave:**
- Tema = terminal, nao-repetivel. 1 video = 1 tema concreto
- Diferente de micronicho (categoria que agrupa multiplos videos)
- Reutiliza `_fetch_channel_videos` do micronicho_agent (zero duplicacao)
- Decomposicao: elementos como Figura de Poder, Vitima, Dinamica, Emocao, etc.
- Hipoteses de adjacencia: "qual elemento do tema viral pode ser replicado em outro tema?"

**Sidebar MC:** Count de temas + Top tema + Score

---

### Agente 6: Recomendador (futuro)

| Campo | Valor |
|-------|-------|
| **Camada** | 3 — Decisao |
| **Cor** | `#eab308` (amarelo) |
| **Tipo MC** | `recomendador` |
| **Status** | Nao implementado |

**O que fara:** Cerebro estrategico que cruza outputs de TODOS os agentes das Camadas 1, 2 e 4. Gera lista de proximos videos recomendados combinando: micronicho (Ag.3) + estrutura de titulo (Ag.4) + tema (Ag.5) + estrutura de copy (Ag.1).

---

### Agente 7: Concorrentes (futuro)

| Campo | Valor |
|-------|-------|
| **Camada** | 4 — Intel Competitiva |
| **Cor** | `#06b6d4` (cyan) |
| **Tipo MC** | `concorrentes` |
| **Status** | Nao implementado |

**O que fara:** Intel competitiva via aba "audiencia assiste" do YouTube. Requer tracao no canal para ter dados disponiveis.

---

## Tabela Comparativa dos Agentes

| Ag. | Nome | Camada | Metrica | LLM Calls | CTR? | Data Source | Status |
|-----|------|--------|---------|-----------|------|-------------|--------|
| 1 | Copy | 1 | Retencao % | 1 (0.3) | Nao | Sheets + Analytics | ✅ |
| 2 | Auth | 1 | Score 0-100 | 1 (0.3) | Nao | Sheets | ✅ |
| 3 | Micro | 2 | Avg Views | 2 (0.3, 0.4) | Nao | videos_historico | ✅ |
| 4 | Titulo | 2 | 60% CTR + 40% Views | 2 (0.3, 0.4) | **SIM** | videos_historico + metrics | ✅ |
| 5 | Temas | 2 | 50% Velocity + 50% Views | 2 (0.3, 0.4) | Nao | videos_historico | ✅ |
| 6 | Recomend. | 3 | — | — | — | Outputs Ag.1-5 | Futuro |
| 7 | Concorr. | 4 | — | — | — | YouTube "audiencia" | Futuro |

Todos os agentes usam **GPT-4o-mini** como modelo (configuravel via env `OPENAI_MODEL`).

---

## Mission Control — Interface Visual

### Setores (Abas)

Cada subnicho de canais = 1 aba com tema visual unico.

| Setor | Cor | Tema JS | Piso | Mobilia Unica |
|-------|-----|---------|------|---------------|
| Monetizados | `#22c55e` | `executive` | Marmore dourado | Mesas mogno, globo, trofeus, ticker bolsa |
| Historias Sombrias | `#8b5cf6` | `gothic` | Pedra com musgo | Mesas antigas, candelabros, caveiras, pocoes |
| Relatos de Guerra | `#4a8c50` | `warroom` | Metal rebitado | Mesas taticas, radar, caixas municao, radio |
| Terror | `#ef4444` | `darklab` | Ceramica rachada | Mesas lab, especimes, tanque sangue, tesla |
| Guerras e Civilizacoes | `#f97316` | `command` | Arenito | Mesas comandante, mesa estrategia, bandeira |
| Desmonetizados | `#ef4444` | `demonetized` | Ceramica rachada | Mesas lab, tanque sangue, tesla, estante |
| Licoes de Vida | `#eab308` | `wisdom` | Pergaminho dourado | Mesas comandante, globo, trofeus, candelabro |

### Personagens dos Agentes

Sprites LiMEZu (48x72px, 4 direcoes, walk frames). Cada agente tem cores unicas:

| Ag. | Skin | Camisa | Cabelo |
|-----|------|--------|--------|
| 1 Copy | `#ffcc99` | `#22c55e` verde | `#4a3728` castanho |
| 2 Auth | `#e8b88a` | `#ef4444` vermelho | `#1a1a1a` preto |
| 3 Micro | `#ffcc99` | `#8b5cf6` roxo | `#8b4513` marrom |
| 4 Titulo | `#d4a574` | `#3b82f6` azul | `#2c1810` escuro |
| 5 Temas | `#ffcc99` | `#f97316` laranja | `#c0392b` ruivo |
| 6 Recomend. | `#e8b88a` | `#eab308` amarelo | `#34495e` cinza |
| 7 Concorr. | `#ffcc99` | `#06b6d4` cyan | `#1a1a1a` preto |

### Sidebar de Agente (click no personagem)

Ao clicar num personagem, abre sidebar com:
- Sprite do agente (canvas 48x72, pose frontal)
- Nome: "Agente X - {nome}"
- Canal + Subnicho
- Descricao do agente
- **Status real** (dados da API):
  - Ag.1: Videos analisados
  - Ag.2: Score + nivel + alertas (cor por faixa)
  - Ag.3: Count de micronichos + Top micronicho
  - Ag.4: Count de estruturas + Top estrutura
  - Ag.5: Count de temas + Top tema + Score
- Botoes: "Rodar Analise" + "Ver Relatorio"
- Area de relatorio (report_text renderizado)

### Botao ATUALIZAR

Endpoint dedicado `POST /api/mission-control/refresh`:
- Refresh da Materialized View (`mv_dashboard_completo`)
- Limpa cache do MC (`_mc_cache` + `_mc_sala_cache`)
- NAO afeta cache do dashboard principal

---

## Analise Completa (5 agentes)

O endpoint `/api/analise-completa/{channel_id}` roda todos os agentes implementados sequencialmente e retorna um relatorio unificado:

```
POST /api/analise-completa/{channel_id}
  → Ag.1 Estrutura de Copy
  → Ag.2 Autenticidade
  → Ag.3 Micronichos
  → Ag.4 Estrutura de Titulo
  → Ag.5 Temas
  → _build_unified_report(copy, auth, micro, title, theme)
```

A funcao `_build_unified_report()` combina os 5 resultados em um relatorio unico com secoes separadas. Aceita `None` para qualquer agente (backward compatible).

---

## Database — Migrations

| Migration | Tabela | Agente |
|-----------|--------|--------|
| (original) | `copy_analysis_runs` | Ag.1 |
| (original) | `authenticity_analysis_runs` | Ag.2 |
| `018_micronicho_tables.sql` | `micronicho_analysis_runs` | Ag.3 |
| `019_title_structure_tables.sql` | `title_structure_analysis_runs` | Ag.4 |
| `020_theme_tables.sql` | `theme_analysis_runs` | Ag.5 |

---

## Arquivos Relacionados

| Arquivo | O que faz |
|---------|-----------|
| `mission_control.py` | Backend + Frontend completo (~4600 linhas) |
| `main.py` | Endpoints + import dos agentes + analise-completa |
| `copy_analysis_agent.py` | Agente 1 — Estrutura de Copy |
| `authenticity_agent.py` | Agente 2 — Autenticidade |
| `micronicho_agent.py` | Agente 3 — Micronichos |
| `title_structure_agent.py` | Agente 4 — Estrutura de Titulo |
| `theme_agent.py` | Agente 5 — Temas |
| `_features/agents/` | Specs HTML dos agentes (Micha) |

## Endpoints do Mission Control

| Metodo | Rota | Retorno | Cache |
|--------|------|---------|-------|
| GET | `/mission-control` | HTML completo | Nenhum |
| GET | `/api/mission-control/status` | JSON overview | 5s |
| GET | `/api/mission-control/sala/{id}` | JSON detalhes | 3s |
| POST | `/api/mission-control/refresh` | JSON (refresh MV + cache) | Nenhum |

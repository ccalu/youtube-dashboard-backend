# Context Document: Facebook Monetization Guide + ClawdBot Study

> **Propósito:** Documento de contexto para continuar o trabalho em outra conversa com Claude.
> **Criado em:** 06/02/2026
> **Próximo passo:** Estudar o ClawdBot e atualizar a Seção 11 do HTML.

---

## 1. O Que Foi Feito

### Arquivo criado
**`/docs/_features/DNA/FACEBOOK-MONETIZATION-GUIDE.html`** (~2.500 linhas)

Um guia completo e profissional sobre monetização no Facebook, no design system DNA do projeto (dark theme, teal accent #00d4aa, Plus Jakarta Sans + JetBrains Mono). Contém sidebar com scroll-spy, 12 seções, responsivo e self-contained.

### As 12 Seções do HTML

| # | ID | Título | Status |
|---|---|---|---|
| 01 | `#monetizacao` | Como Monetizar uma Página no Facebook | ✅ Completo + fontes verificadas |
| 02 | `#rpm-cpm` | RPM e CPM por Língua e País | ✅ Completo |
| 03 | `#nichos` | Melhores Nichos para Trabalhar | ✅ Completo |
| 04 | `#guerras` | Análise: Guerras & Civilizações | ✅ Completo |
| 05 | `#formato` | Duração e Formato de Vídeos | ✅ Completo |
| 06 | `#postagem` | Postagem Diária Ideal | ✅ Completo |
| 07 | `#crescimento` | Acelerar Crescimento | ✅ Completo |
| 08 | `#youtube-facebook` | YouTube → Facebook | ✅ Completo |
| 09 | `#desmonetizacao` | Desmonetização e Proibições | ✅ Completo |
| 10 | `#multiplas-paginas` | Múltiplas Páginas | ✅ Completo |
| 11 | `#automacao` | Automação com ClawdBot | ⚠️ PRECISA REESCREVER — estudar ClawdBot real |
| 12 | `#resumo` | Resumo Executivo para Sócios | ✅ Completo |

---

## 2. Dados Verificados sobre Monetização Facebook (com fontes)

### Requisitos In-Stream Ads (CONFIRMADO por 5+ fontes)

Todos são **obrigatórios simultaneamente** (E, não OU):

| Requisito | Valor | Nota |
|---|---|---|
| Seguidores | **10.000** | Obrigatório |
| Watch Time | **600.000 minutos (10.000 horas)** em 60 dias | GARGALO principal |
| Vídeos ativos | **5+** (mín. 1 min cada) | Fácil |
| Conta ativa | **90 dias** | Automático |
| País elegível | Lista de países da Meta | Brasil/Portugal elegíveis |
| Sem violações | 30+ dias sem policy violations | Manter compliance |

### Watch Time: Análise Realista

- YouTube exige 4.000h em 12 meses (= ~11h/dia)
- Facebook exige 10.000h em 60 dias (= ~167h/dia) — **15x mais volume diário**
- São minutos TOTAIS somados (todos vídeos × todos viewers)
- Com 5.000 views/dia × 3 min médios = 15.000 min/dia (250h) ✓
- 1 vídeo viral (50K views × 2 min) = 100.000 min num dia ✓✓

### Alternativa "30K views de 1 minuto"

- Mencionada por 1-2 fontes, **NÃO confirmada pela maioria**
- Pode ser requisito antigo, regional ou não-oficial
- **Não contar com isso** — usar 600K minutos como base

### Requisitos Fan Subscriptions (caminho mais fácil)

| Requisito | Valor |
|---|---|
| Seguidores | 10.000 OU 250 viewers recorrentes |
| Watch Time | **180.000 min (3.000h)** OU 50.000 engajamentos |

### Timeline Realista

| Meta | Com ads agressivos | Sem ads |
|---|---|---|
| 10K seguidores | 30-60 dias | 3-6 meses |
| 600K min watch time | 30-90 dias (precisa de virais) | 3-6 meses |
| Monetização total | **1-3 meses** | 3-6 meses |

### CPM por País (dados do documento)

| País | CPM Médio | Tier |
|---|---|---|
| EUA | $15-25 (média $20.48) | S |
| Canadá | $12-20 | S |
| UK | $8-15 (média $10.85) | A |
| Austrália | $10-18 | A |
| Portugal | $6-12 (média $9.88) | B |
| Brasil | $2-5 | C |

### Fontes Verificadas

1. **PublisherInABox** — https://publisherinabox.com/how-to-get-approved-for-content-monetization-program-and-earn-up-to-35k-month/
   - Confirma 600K min OU 30K views 1-min para In-Stream Ads (única fonte com alternativa)

2. **ActionSprout** — https://actionsprout.com/blog/facebook-monetization-requirements/
   - Detalha requisitos separados por programa (In-Stream, Stars, Subscriptions)
   - Confirma 600K min + 10K seguidores

3. **Metricool** — https://metricool.com/monetize-facebook-account/
   - Confirma 10K seguidores + 180K min para Subscriptions

4. **Epidemic Sound** — https://www.epidemicsound.com/blog/how-to-monetize-facebook/
   - Visão geral do CMP unificado (atualização Ago/2025)

5. **Supliful** — https://supliful.com/blog/facebook-monetization-requirements
   - Confirma 600K min + 10K seguidores para In-Stream

6. **Famups** — https://www.famups.com/blog/facebook-in-stream-ads-eligibility/
   - Confirma 600K min, menciona 5.000 seguidores (pode ser requisito antigo)

7. **Multilogin** — https://multilogin.com/blog/how-to-get-paid-on-facebook/
   - Confirma 10K seg + 600K min + 5 vídeos para 2026

8. **TechEvangelist** — https://techevangelistseo.com/how-to-make-money-on-facebook/
   - Confirma 10K + 600K min como "still standard" em 2026

---

## 3. O Que Já Existe de Automação no Projeto

O projeto tem um sistema robusto de automação para **YouTube**. Não existe NADA para Facebook ainda.

### Ferramentas Existentes (YouTube)

| Ferramenta | Arquivo | O Que Faz |
|---|---|---|
| **Agent Scheduler** | `docs/_features/agents/scheduler.py` | Agendamento de tarefas de IA com APScheduler. Análise diária 6h UTC, alertas cada 6h, trends cada 4h |
| **Upload Queue Worker** | `docs/_features/yt_uploader/queue_worker.py` | Processamento de fila de uploads YouTube. Batches de 5, circuit breaker, monitoramento de recursos |
| **Daily Uploader** | `docs/daily_uploader.py` | 1 upload/dia/canal após coleta. 3 tentativas, prioriza monetizados, integração Google Sheets |
| **Spreadsheet Scanner** | `docs/main.py` (linhas 3966-3980) | Detecta vídeos prontos no Google Sheets a cada 20 min, adiciona à fila |
| **Post-Collection Automation** | `docs/post_collection_automation.py` | Após coleta diária: processa comentários, traduz, análise |
| **Automation UI** | `docs/_features/frontend-code/AutomacaoUploads.tsx` | Dashboard React com monitoramento real-time de fila, scanner, worker |

### Infraestrutura

- **Backend:** Python (FastAPI) no Railway
- **Database:** Supabase (PostgreSQL)
- **YouTube API:** 20 API keys com rotação
- **Google Sheets:** Integração para tracking
- **CNPJs:** 4 disponíveis para diversificação

---

## 4. ClawdBot — O Que É (pesquisa inicial)

### Definição
ClawdBot (OpenClaw / clawd.bot) é um **assistente de IA open-source e self-hosted** que funciona como um gateway local conectando modelos de IA (Claude, OpenAI) a canais de chat, ferramentas e scripts.

### NÃO é uma ferramenta de Facebook
ClawdBot NÃO é específico para Facebook. É um **agente de automação pessoal** que pode ser configurado para diversas tarefas.

### Características Principais
- **Self-hosted:** Roda localmente, dados ficam no seu dispositivo
- **Multi-canal:** WhatsApp, Telegram, Slack, Discord, Signal, iMessage
- **Memória persistente:** Mantém contexto entre sessões
- **Browser automation:** Pode controlar navegador
- **Execução de scripts:** Roda comandos no terminal
- **Mensagens proativas:** Envia alertas, lembretes, briefings sem ser solicitado
- **Integrações:** Gmail, Google Calendar, Todoist, GitHub, WordPress, e mais

### Links para Estudo
- **Site oficial:** https://clawd.bot/
- **Documentação:** https://docs.clawd.bot/
- **Tom's Hardware (análise):** https://www.tomshardware.com/tech-industry/artificial-intelligence/exploring-clawdbot-the-ai-agent-taking-the-internet-by-storm
- **MagicShot (features):** https://magicshot.ai/news/clawdbot-the-self-hosted-ai-assistant-redefining-personal-automation/
- **MarkTechPost (técnico):** https://www.marktechpost.com/2026/01/25/what-is-clawdbot-how-a-local-first-agent-stack-turns-chats-into-real-automations/
- **Medium (overview):** https://medium.com/data-science-in-your-pocket/what-is-clawdbot-the-viral-ai-assistant-b432d275de66
- **Medium (deep dive):** https://pub.towardsai.net/clawdbot-ai-the-revolutionary-open-source-personal-assistant-transforming-productivity-in-2026-6ec5fdb3084f
- **Orbilontech (workflow guide):** https://orbilontech.com/clawdbot-ai-workflow-automation-guide/

---

## 5. PRÓXIMO PASSO: Reescrever Seção 11 do HTML

### O Que Precisa Ser Feito

A **Seção 11 (`#automacao`)** do HTML precisa ser **completamente reescrita** com base num estudo real do ClawdBot. O conteúdo atual é genérico e placeholder.

### O Que Estudar sobre o ClawdBot

1. **O que é exatamente** — capacidades reais, limitações, como funciona
2. **Como instalar e configurar** — requisitos, setup, self-hosting
3. **Integrações relevantes para nós:**
   - Pode postar no Facebook automaticamente?
   - Pode agendar posts via Meta Business Suite?
   - Pode monitorar métricas do Facebook?
   - Pode responder comentários?
   - Pode integrar com nosso pipeline de conteúdo IA?
4. **Browser automation** — pode controlar o Meta Business Suite via browser?
5. **Integração com nosso stack existente:**
   - Pode se conectar ao Agent Scheduler?
   - Pode usar o Queue Worker para Facebook?
   - Pode integrar com Supabase?
6. **Fluxo de automação Facebook proposto:**
   - Criação de conteúdo (IA) → Revisão → Agendamento → Publicação → Monitoramento
   - Quais partes o ClawdBot pode fazer vs. o que precisa ser manual?
7. **Riscos e limitações:**
   - Facebook detecta automação? Risco de ban?
   - Rate limits da API do Facebook
   - O que NÃO automatizar (engajamento em comentários = risco de parecer bot)
8. **Alternativas ao ClawdBot** para comparação:
   - Meta Business Suite API direta
   - Buffer / Hootsuite APIs
   - n8n / Make (Integromat)
   - Custom Python scripts

### Como Atualizar o HTML

1. Ler o arquivo: `/docs/_features/DNA/FACEBOOK-MONETIZATION-GUIDE.html`
2. Localizar `<section id="automacao"` (Seção 11, ~linha 2180+)
3. Reescrever o conteúdo inteiro da seção com dados reais do ClawdBot
4. Manter o design system DNA (mesmos componentes CSS)
5. Usar os componentes: `.card`, `.data-table`, `.stats-grid`, `.stat-card`, `.opportunity-grid`, `.opportunity-card`, `.checklist`, `.step-list`, `.highlight-box`, `.warning-box`, `.warning-box.info`

### Estrutura Sugerida para Nova Seção 11

```
11.1 — O Que é o ClawdBot (explicação real)
11.2 — Capacidades Relevantes para Facebook
11.3 — O Que JÁ Temos no Projeto (tabela das ferramentas existentes)
11.4 — Fluxo de Automação Proposto (diagrama/steps)
11.5 — O Que Pode vs. Não Pode Ser Automatizado
11.6 — Setup e Integração com Nosso Stack
11.7 — Riscos e Limitações
11.8 — Alternativas e Comparação
11.9 — Recomendação Final
```

---

## 6. Design System do HTML (para referência)

### CSS Variables
```css
--bg-primary: #0a0a0f;
--bg-secondary: #12121a;
--bg-tertiary: #1a1a24;
--bg-card: #15151f;
--border-color: #2a2a3a;
--accent-primary: #00d4aa;    /* teal */
--accent-blue: #4dabf7;
--accent-warning: #ffd43b;
--accent-danger: #ff6b6b;
--accent-purple: #9775fa;
```

### Componentes Disponíveis
- `.card` + `.card-title` — Cards com borda e hover glow
- `.data-table` — Tabelas com headers teal
- `.stats-grid` + `.stat-card` + `.stat-value` + `.stat-label` — Grid de estatísticas
- `.stat-value.blue` / `.warning` / `.danger` / `.purple` — Cores nos valores
- `.opportunity-grid` + `.opportunity-card` (.high/.medium/.volume) — Cards de oportunidade
- `.checklist` — Lista com checkmarks verdes
- `.step-list` + `.step-item` + `.step-text` — Lista numerada com círculos
- `.highlight-box` — Box verde/teal para destaques positivos
- `.warning-box` — Box vermelho para alertas
- `.warning-box.info` — Box azul para informações
- `.tag` + `.tag-s`/`.tag-a`/`.tag-b`/`.tag-c` — Tags coloridas por tier
- `.phase-card` + `.phase-header` + `.phase-title` + `.phase-timeline` + `.phase-items` — Cards de fases

### Fontes
- **Plus Jakarta Sans** (300-700) — texto geral
- **JetBrains Mono** (400-700) — números, labels, código

---

## 7. Resumo para o Claude na Próxima Conversa

> Você está continuando um trabalho de criação de um guia HTML sobre monetização no Facebook.
> O arquivo está em `/docs/_features/DNA/FACEBOOK-MONETIZATION-GUIDE.html`.
> A Seção 11 (id="automacao") precisa ser reescrita com um estudo real do ClawdBot (https://clawd.bot/).
> Leia este documento de contexto primeiro, depois estude o ClawdBot usando os links fornecidos,
> e reescreva a Seção 11 com dados reais sobre o que o ClawdBot pode fazer para automatizar
> publicação e gestão de páginas no Facebook.
> Mantenha o design system DNA existente no HTML.
> O projeto NÃO tem ClawdBot instalado ainda — esta seção é um estudo de viabilidade.

# FRONTEND COMPLETO - YouTube Dashboard

**Atualizado:** 2026-01-13
**Fonte:** Lovable (React SPA)
**Mantido por:** Cellibs + Claude Code

---

## 1. ESTRUTURA DE ABAS/PAGINAS

O dashboard usa uma **Single Page Application (SPA)** com navegacao por abas gerenciada pelo estado interno.

| Aba | Nome | Descricao |
|-----|------|-----------|
| `tabela` | Tabela | Aba principal. Exibe nossos canais agrupados por subniche com metricas de inscritos e crescimento diario. Cards colapsaveis por subniche. |
| `our-channels` | Nossos Canais | Tabela detalhada dos canais tipo "nosso" com views 7d/30d, inscritos, filtros e acoes (editar, deletar, favoritar). |
| `channels` | Canais Minerados | Tabela de canais tipo "minerado" (concorrentes) com mesmas funcionalidades de Nossos Canais. |
| `notifications` | Notificacoes | Sistema de alertas para videos que atingiram metas de views. Gerenciamento de regras e transcricao de videos. |
| `monetization` | Monetizacao | Dashboard de receita YouTube AdSense com RPM, revenue por canal, projecoes e analytics avancados. |
| `financeiro` | Financeiro | Gestao financeira da empresa: receitas, despesas, metas, projecoes e comparacoes mensais. |

**Modais/Ferramentas (acessiveis via sidebar):**
- **Favoritos**: Lista de canais/videos favoritados
- **Analise**: Tendencias por subniche, top channels, padroes de titulos
- **Historico de Coleta**: Status das coletas de dados e uso da API YouTube

---

## 2. COMPONENTES POR ABA

### 2.1 ABA: Tabela (`TabelaCanais.tsx`)

**Componentes:**
- `SubnichoCard` - Cards colapsaveis por subniche

**Exibe:**
- Canais agrupados por subniche
- Nome do canal com bandeira do idioma
- Numero de inscritos
- Crescimento de inscritos (diff)
- Botao para abrir canal no YouTube

**Interacoes:**
- Clicar no card para expandir/colapsar
- Clicar no botao play para abrir canal no YouTube

---

### 2.2 ABA: Nossos Canais (`OurChannelsTable.tsx`)

**Componentes:**
- Tabela com colunas: Canal, Subnicho, Lingua, Inscritos, Views 7d, Views 30d, Acoes
- `AddEditCanalModal` - Modal para adicionar/editar canal
- `ConfirmDeleteDialog` - Dialogo de confirmacao de exclusao

**Exibe:**
- Dados dos canais tipo "nosso"
- Badges coloridos por subnicho/lingua
- Icones de ordenacao

**Interacoes:**
- Busca por nome do canal
- Filtros: Lingua, Subnicho, Views minimas
- Ordenacao por qualquer coluna (clicando no header)
- Adicionar novo canal
- Editar canal existente
- Deletar/Desativar canal
- Favoritar canal (estrela)
- Abrir canal no YouTube
- Paginacao (20 itens por pagina)

---

### 2.3 ABA: Canais Minerados (`ChannelsTable.tsx`)

**Estrutura identica a Nossos Canais**, porem:
- Filtra apenas canais tipo "minerado"
- Usa query key diferente

---

### 2.4 ABA: Notificacoes (`NotificationsTab.tsx`)

**Componentes:**
- Cards de notificacao agrupados por periodo (hoje, ontem, esta semana, anteriores)
- `NotificationRulesPanel` - Painel de gerenciamento de regras
- Sistema de transcricao de videos

**Exibe:**
- Alertas de videos que atingiram metas de views
- Stats: total, nao vistas, vistas, hoje, esta semana
- Badge com nome do canal, subnicho, lingua
- Views atingidas e periodo

**Interacoes:**
- Filtros: Regra, Subnichos, Linguas, Periodo, Status (novas/vistas), Tipo canal
- Busca por nome
- Marcar como vista/nao vista
- Marcar todas como vistas
- Abrir video no YouTube
- Solicitar transcricao do video
- Copiar transcricao
- Gerenciar regras de notificacao
- Toggle: Ver novas vs Ver historico
- Paginacao

---

### 2.5 ABA: Monetizacao (`MonetizationTab.tsx`)

**Componentes:**
- `MonetizationFilterBar` - Barra de filtros
- `MonetizationCards` - Cards de resumo (Revenue 24h, RPM, Daily Avg, Total)
- `MonetizationChannelsList` - Lista de canais por subniche
- `TrophyModalButton` - Modal de Top Performers + Best/Worst Day
- `TargetModalButton` - Modal de Projecoes + Metricas de Qualidade
- `AdvancedAnalyticsButton` - Modal de Analytics Avancados
- `MonetizationChannelHistoryModal` - Historico por canal

**Exibe:**
- Revenue total, RPM medio, media diaria
- Revenue 24h (real vs estimado)
- Lista de canais agrupados por subniche
- Grafico de tendencias
- Top performers por RPM e Revenue
- Projecao mensal
- Metricas de qualidade (retencao, duracao)

**Interacoes:**
- Filtros: Periodo (24h, 3d, 7d, 15d, 30d, total, custom), Mes especifico, Lingua, Subniche
- Toggle: Real+Estimate vs Real Only
- Expandir/colapsar grupos de subniche
- Ver historico detalhado por canal
- Abrir modais de analytics
- Exportar CSV

---

### 2.6 ABA: Financeiro (`FinanceiroTab.tsx`)

**Componentes:**
- `FinanceiroFiltroPeriodo` - Seletor de periodo
- `FinanceiroOverviewCards` - Cards de receita, despesas, lucro
- `FinanceiroMetas` - Progresso de metas
- `FinanceiroProjecaoCard` - Projecao do mes
- `FinanceiroComparacaoCard` - Comparacao mensal
- `FinanceiroGraficoReceitaDespesas` - Grafico de linha
- `FinanceiroDespesasCard` - Breakdown de despesas

**Exibe:**
- Receita bruta, despesas, lucro liquido
- Variacoes percentuais
- Grafico de receita vs despesas
- Breakdown por categoria
- Metas e progresso
- Projecao para fim do mes
- Comparacao ultimos 6 meses

**Interacoes:**
- Filtro de periodo (7d, 15d, 30d, all, custom)
- CRUD de lancamentos
- CRUD de categorias
- CRUD de metas
- Exportar CSV

---

## 3. ENDPOINTS CONSUMIDOS

### 3.1 API Principal (`src/services/api.ts`)

**Base URL:** `https://youtube-dashboard-backend-production.up.railway.app`

| Endpoint | Metodo | Quando Chamado | Dados Esperados |
|----------|--------|----------------|-----------------|
| `/api/canais?tipo=minerado` | GET | Ao carregar Canais Minerados | `{ canais: Channel[], total: number }` |
| `/api/nossos-canais` | GET | Ao carregar Nossos Canais | `{ canais: Channel[], total: number }` |
| `/api/canais-tabela` | GET | Ao carregar aba Tabela | `{ grupos: { [subnicho]: Canal[] }, total_canais, total_subnichos }` |
| `/api/filtros` | GET | Ao carregar tabelas (para dropdowns) | `{ nichos, subnichos, linguas, canais }` |
| `/api/add-canal?params` | POST | Ao adicionar canal | void |
| `/api/canais/{id}?params` | PUT | Ao editar canal | void |
| `/api/canais/{id}?permanent=bool` | DELETE | Ao deletar canal | void |
| `/api/favoritos/canais` | GET | Ao carregar favoritos | `{ canais: Channel[], total }` |
| `/api/favoritos/videos` | GET | Ao carregar favoritos videos | `{ videos: Video[], total }` |
| `/api/favoritos/adicionar?tipo&item_id` | POST | Ao favoritar | void |
| `/api/favoritos/remover?tipo&item_id` | DELETE | Ao desfavoritar | void |
| `/api/notificacoes` | GET | Ao carregar notificacoes novas | `{ notificacoes: Notificacao[], total }` |
| `/api/notificacoes/todas?params` | GET | Com filtros avancados | `{ notificacoes: Notificacao[], total }` |
| `/api/notificacoes/stats` | GET | Ao carregar sidebar/notificacoes | `{ total, nao_vistas, vistas, hoje, esta_semana }` |
| `/api/notificacoes/{id}/marcar-vista` | PUT | Ao marcar como vista | void |
| `/api/notificacoes/{id}/desmarcar-vista` | PUT | Ao desmarcar | void |
| `/api/notificacoes/marcar-todas?params` | POST | Marcar todas vistas | `{ message, count }` |
| `/api/regras-notificacoes` | GET | Ao abrir painel de regras | `{ regras: Regra[] }` |
| `/api/analysis/subniches` | GET | Ao abrir modal Analise | `{ total, subniches: string[] }` |
| `/api/analysis/subniche-trends` | GET | Ao carregar tendencias | `{ success, data: { '7d', '15d', '30d' }, totals }` |
| `/api/analysis/top-channels?subniche&days` | GET | No carousel de top channels | `{ subniche, total, channels: TopChannel[] }` |
| `/api/analysis/title-patterns?subniche&days` | GET | No carousel de padroes | `{ subniche, period_days, total, patterns }` |
| `/api/analysis/keywords?subniche&days` | GET | (Desabilitado atualmente) | `{ period_days, total, keywords }` |
| `/api/coletas/historico?limit` | GET | Ao abrir modal Historico | `{ historico, total, quota_info }` |
| `/api/coletas/cleanup` | POST | Ao abrir modal Historico (background) | void |
| `/api/coletas/{id}` | DELETE | Ao deletar coleta | void |
| `/api/collect-data` | POST | Ao clicar "Coletar" | `{ message }` |

---

### 3.2 API Monetizacao (`MonetizationTab.tsx`)

| Endpoint | Metodo | Quando Chamado | Dados Esperados |
|----------|--------|----------------|-----------------|
| `/api/monetization/summary?params` | GET | Ao carregar/filtrar | `{ total_monetized_channels, daily_avg, rpm_avg, total_revenue }` |
| `/api/monetization/channels?params` | GET | Ao carregar/filtrar | `{ subnichos: [{ name, color, channels }] }` |
| `/api/monetization/analytics?params` | GET | Ao carregar/filtrar | `{ projection_monthly, comparison_period, best_day, worst_day, avg_retention_pct, avg_view_duration_sec }` |
| `/api/monetization/top-performers?params` | GET | Ao carregar/filtrar | `{ top_rpm: [], top_revenue: [] }` |
| `/api/monetization/revenue-24h` | GET | Ao carregar | `{ real: {}, estimate: {} }` |
| `/api/monetization/channel-history?channel_id&month&period` | GET | Ao abrir modal historico | `{ history: [], summary: {} }` |
| `/api/monetization/config` | GET | Para carregar subnichos/linguas | `{ subnichos, linguas }` |
| `/api/monetization/quality-metrics?params` | GET | No modal de metricas | `{ subniches: [], channels: [] }` |
| `/api/monetization/overall-revenue?params` | GET | No grafico geral | `{ data: [{ date, revenue, views }], summary: {} }` |

**Parametros comuns (query string):**
- `period`: 24h, 3d, 7d, 15d, 30d, total, custom
- `type_filter`: real_estimate, real_only
- `language`: all, pt, es, en, de, fr
- `subnicho`: string ou null
- `month`: YYYY-MM (opcional, substitui period)
- `start_date`, `end_date`: YYYY-MM-DD (para custom)

---

### 3.3 API Financeiro (`src/services/financeiroApi.ts`)

| Endpoint | Metodo | Quando Chamado | Dados Esperados |
|----------|--------|----------------|-----------------|
| `/api/financeiro/overview?periodo` | GET | Ao carregar/filtrar | `{ receita_bruta, despesas_totais, lucro_liquido, variacoes... }` |
| `/api/financeiro/taxa-cambio` | GET | Ao carregar | `{ taxa, atualizado_em }` |
| `/api/financeiro/projecao-mes` | GET | Ao carregar | `{ mes, projecao_mes, media_diaria, dias_restantes... }` |
| `/api/financeiro/comparacao-mensal?meses` | GET | Ao carregar | `{ meses: [{ mes, receita, despesas, lucro, variacao }] }` |
| `/api/financeiro/graficos/receita-despesas?periodo` | GET | Ao carregar | `{ dados: [{ data, receita, despesas, taxas, lucro }] }` |
| `/api/financeiro/graficos/despesas-breakdown?periodo` | GET | Ao carregar | `{ por_categoria, por_recorrencia, total }` |
| `/api/financeiro/lancamentos?params` | GET | Ao carregar | `{ lancamentos: Lancamento[], total }` |
| `/api/financeiro/lancamentos` | POST | Ao criar | `Lancamento` |
| `/api/financeiro/lancamentos/{id}` | PATCH | Ao editar | `Lancamento` |
| `/api/financeiro/lancamentos/{id}` | DELETE | Ao deletar | void |
| `/api/financeiro/categorias` | GET | Ao carregar | `{ categorias: Categoria[], total }` |
| `/api/financeiro/categorias` | POST | Ao criar | `Categoria` |
| `/api/financeiro/categorias/{id}` | PATCH | Ao editar | `Categoria` |
| `/api/financeiro/categorias/{id}` | DELETE | Ao deletar | void |
| `/api/financeiro/metas/progresso?periodo` | GET | Ao carregar | `{ metas: Meta[], total }` |
| `/api/financeiro/metas` | POST | Ao criar | `Meta` |
| `/api/financeiro/metas/{id}` | PATCH | Ao editar | `Meta` |
| `/api/financeiro/metas/{id}` | DELETE | Ao deletar | void |
| `/api/financeiro/lancamentos/export-csv?periodo` | GET | Ao exportar | Arquivo CSV (download) |

**Periodos aceitos:** `7d`, `15d`, `30d`, `all`, ou `YYYY-MM-DD,YYYY-MM-DD` (custom range)

---

## 4. ESTADO/FILTROS POR ABA

### Tabela
- Sem filtros (exibe todos os canais tipo "nosso" agrupados)
- Estado: cards colapsados por padrao

### Nossos Canais / Canais Minerados
- Filtros: `lingua`, `subnicho`, `minViews`
- Busca: `searchTerm`
- Ordenacao: `sortConfig { key, direction }`
- Paginacao: `currentPage`, `itemsPerPage` (20)

### Notificacoes
- Filtros: `regra`, `subnichos[]`, `linguas[]`, `periodo`, `status`, `tipo_canal`
- Busca: `searchTerm`
- Toggle: `showAll` (novas vs historico)
- Paginacao: `currentPage`, `itemsPerPage` (50)
- Estados de transcricao: `transcriptionStatus`, `transcriptions`, `jobIds`

### Monetizacao
- Filtros: `period`, `language`, `subnicho`, `typeFilter`, `month`, `customStart`, `customEnd`
- Todos os filtros sao persistidos no estado React

### Financeiro
- Filtro: `periodo` (7d, 15d, 30d, all, custom)
- Estado de modais para CRUD

---

## 5. FUNCIONALIDADES ESPECIAIS

### Notificacoes/Alertas
- Badge animado com contagem de nao vistas no sidebar
- Cache local com expiracao as 6h Brasilia
- Auto-refresh a cada 30 segundos

### Graficos (Recharts)
- `MonetizationChannelHistoryModal`: LineChart com Revenue e RPM
- `FinanceiroGraficoReceitaDespesas`: LineChart com Receita, Despesas, Lucro
- `OverallMonetizationChart`: LineChart com tendencia geral

### Exportacao de Dados
- Monetizacao: Download CSV do historico por canal
- Financeiro: Export CSV de lancamentos

### Transcricao de Videos
- Sistema assincrono com polling
- Status: idle, loading, success, error
- Persistencia no localStorage

### Pull-to-Refresh (Mobile)
- Gesture para atualizar dados
- Indicador visual de progresso

---

## 6. INTEGRACOES

### Autenticacao
- Nao ha autenticacao implementada (uso interno)

### Cache/Polling
- **React Query** com staleTime configurado:
  - Global: 4h ou ate 5h Brasilia
  - Notificacoes: auto-refresh 30s
  - Historico de coletas: refetch 10s quando modal aberto
  - Filter options: 10min
  - Favoritos: 2min

### Cache Local (localStorage)
- `transcriptionStatus`, `transcriptions`, `jobIds` - Estado de transcricoes
- `sidebar_stats_last_refresh`, `sidebar_notification_stats` - Stats do sidebar
- Caches de notificacoes com expiracao as 6h Brasilia

---

## 7. DESIGN SYSTEM

### Cores Principais (HSL)
```css
--background: 222 47% 5%        /* #0f172a - Fundo escuro */
--card: 215 28% 17%             /* #1e293b - Cards */
--primary: 217 91% 60%          /* Azul primario */
--destructive: 0 84% 60%        /* Vermelho */
--growth-positive: 142 76% 36%  /* Verde para crescimento */
--growth-negative: 0 84% 60%    /* Vermelho para queda */
```

### Componentes de UI
- **Biblioteca**: shadcn/ui (Radix + Tailwind)
- **Icones**: lucide-react
- **Graficos**: Recharts
- **Tabelas**: Custom com Table do shadcn
- **Modais**: Dialog do Radix
- **Selects**: Multi-select customizado
- **Toast**: Sonner + shadcn Toast

### Responsividade
- **Mobile-first** com breakpoints Tailwind
- `lg:` para desktop (1024px+)
- Cards empilhados em mobile, tabelas em desktop
- Sidebar colapsavel
- Pull-to-refresh em mobile

---

## 8. ARQUITETURA DO FRONTEND

```
Frontend - React SPA
├── Dashboard.tsx (Main container)
│   ├── AppSidebar (Navegacao)
│   └── Abas Principais
│       ├── TabelaCanais (tabela)
│       ├── OurChannelsTable (our-channels)
│       ├── ChannelsTable (channels)
│       ├── NotificationsTab (notifications)
│       ├── MonetizationTab (monetization)
│       └── FinanceiroTab (financeiro)
│
├── Modais Globais
│   ├── FavoritesTable
│   ├── AnalysisModal
│   └── CollectionHistoryModal
│
└── Services
    ├── api.ts → API Principal
    ├── financeiroApi.ts → API Financeiro
    └── (inline) → API Monetizacao
```

---

## 9. PARA CLAUDE PROXIMA VEZ

### Abas Existentes (6 total):
1. **Tabela** - Cards por subniche (nossos canais)
2. **Nossos Canais** - Tabela detalhada tipo "nosso"
3. **Canais Minerados** - Tabela detalhada tipo "minerado"
4. **Notificacoes** - Alertas de videos virais + transcricao
5. **Monetizacao** - Revenue, RPM, analytics
6. **Financeiro** - Receitas, despesas, metas

### Modais Importantes:
- Favoritos (canais + videos)
- Analise (trends, top channels, patterns)
- Historico de Coleta (status, quota)

### Base URL Backend:
```
https://youtube-dashboard-backend-production.up.railway.app
```

### Bibliotecas Chave:
- React Query (cache/fetch)
- Recharts (graficos)
- shadcn/ui (componentes)
- lucide-react (icones)

---

**Ultima atualizacao:** 2026-01-13
**Fonte:** Analise completa do Lovable

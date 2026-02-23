# DASHBOARD DE MINERAÇÃO - Backend Python

## 📍 VOCÊ ESTÁ NO: Backend do Dashboard de Mineração
**Localização:** D:\ContentFactory\youtube-dashboard-backend
**Linguagem:** Python (FastAPI)
**Deploy:** Railway

## 🎯 O QUE ESTE BACKEND FAZ:
API REST que gerencia coleta de dados YouTube, notificações e transcrições.

## ⚠️ REGRAS DE HONESTIDADE (CRÍTICO - NUNCA VIOLAR):
1. **SEMPRE verificar dados antes de afirmar** - Nunca diga "100% funcional" sem testar
2. **NUNCA inventar informações** - Se não souber, diga "vou verificar"
3. **SEMPRE reportar problemas reais** - Não esconda bugs ou erros
4. **VERIFICAR antes de confirmar** - Execute queries, teste código, valide dados
5. **SER TRANSPARENTE sobre limitações** - Se algo pode falhar, avise antes
6. **ADMITIR erros imediatamente** - Se errou, corrija sem desculpas
7. **DADOS > SUPOSIÇÕES** - Sempre prefira verificar a assumir
8. **DOCUMENTAR APÓS FINALIZAR** - Toda feature completa DEVE ser documentada imediatamente

## 📂 ARQUIVOS PRINCIPAIS:
- `main.py` - FastAPI app + endpoints (1122 linhas)
- `collector.py` - YouTube collector + rotação de API keys (727 linhas)
- `notifier.py` - Sistema de notificações inteligente (394 linhas)
- `database.py` - Client Supabase + queries
- `daily_uploader.py` - Orquestrador de upload diário (1025 linhas)
- `dash_upload_final.py` - Dashboard de upload Flask porta 5006 (887 linhas)
- `copy_analysis_agent.py` - Agente de análise de copy (~1550 linhas)
- `monetization_oauth_collector.py` - Coleta métricas Analytics API
- `mission_control.py` - Mission Control escritório virtual
- `requirements.txt` - Dependências Python

## 🔗 INTEGRAÇÕES:
- **Supabase:** PostgreSQL (credenciais em .env)
- **YouTube API:** 20 keys (KEY_3 a 10 + KEY_21 a 32) - NÃO ESTÃO AQUI! (Railway)
- **Servidor M5:** https://transcription.2growai.com.br

## ⚠️ CREDENCIAIS LOCAIS (.env):
- `SUPABASE_URL` - Configurado ✅
- `SUPABASE_KEY` - Configurado ✅ (chave ANON com RLS)
- `SUPABASE_SERVICE_ROLE_KEY` - Configurado ✅ (bypass RLS)
- `YOUTUBE_API_KEY_X` - NÃO configuradas localmente (só Railway)

**IMPORTANTE:**
- Para testar localmente: precisa configurar pelo menos 1 YouTube API key
- Para produção: usar Railway (já tem tudo configurado)
- Arquivo .env está em .gitignore (não sobe pro GitHub)

## 🔐 CRÍTICO - VERIFICAÇÃO DE TOKENS OAUTH:
**SEMPRE use SERVICE_ROLE_KEY para verificar tokens OAuth!**
- `SUPABASE_KEY` (anon) = RLS ativo = **NÃO mostra tokens**
- `SERVICE_ROLE_KEY` = Bypass RLS = **MOSTRA todos os tokens**
- `daily_uploader.py` usa SERVICE_ROLE_KEY = Por isso funciona!

**Para verificar tokens:** `python check_oauth_definitivo.py`
**Documentação completa:** `VERIFICACAO_TOKENS_OAUTH.md`

## 🚀 RODAR LOCALMENTE:
```bash
# Instalar dependências
pip install -r requirements.txt --break-system-packages

# Rodar servidor
python main.py
```

**Porta:** 8000 (local) ou PORT env var (Railway)

## 📊 ENDPOINTS PRINCIPAIS:

### Canais & Vídeos:
- `GET /api/canais` - Lista canais minerados (com filtros)
- `GET /api/canais-tabela` - **NOVO!** Nossos canais agrupados por subnicho (para aba Tabela)
- `GET /api/videos` - Lista vídeos (com filtros)
- `POST /api/canais` - Adiciona novo canal

### Notificações:
- `GET /api/notificacoes` - Lista notificações (com filtros)
- `POST /api/force-notifier` - Força disparo manual de notificações
- `PATCH /api/notificacoes/{id}/vista` - Marca notificação como vista
- `POST /api/notificacoes/marcar-todas-vistas` - Marca todas como vistas

### Análise:
- `GET /api/subniche-trends` - Tendências por subnicho
- `GET /api/system-stats` - Estatísticas do sistema

### 💬 Sistema de Comentários (NOVO!):
- `GET /api/comentarios/resumo` - Resumo dos comentários (canais monetizados)
- `GET /api/comentarios/monetizados` - Lista canais monetizados com stats
- `GET /api/canais/{id}/videos-com-comentarios` - Vídeos com comentários
- `GET /api/videos/{id}/comentarios-paginados` - Comentários paginados
- `PATCH /api/comentarios/{id}/marcar-respondido` - Marcar como respondido
- `POST /api/collect-comments/{canal_id}` - Coletar comentários

**Documentação completa:** `.claude/3_SISTEMA_COMENTARIOS/`

Ver documentação completa em: D:\ContentFactory\.claude\DASHBOARD_MINERACAO.md

## 🔧 PARA CLAUDE CODE:
- Você pode ler/editar código Python
- Testar conexão Supabase (tem credenciais)
- NÃO pode testar coleta YouTube (faltam API keys locais)
- Pode criar novos endpoints
- Pode melhorar lógica existente
- SEMPRE fazer backup antes de mudanças grandes

## 🆕 ATUALIZAÇÕES RECENTES (23/02/2026):

### 🧠 Agente de Análise de Copy - MVP Completo ✅
**Desenvolvido:** 20-23/02/2026
**Status:** ✅ MVP completo, aguardando dados de copy nas planilhas

**O que foi implementado:**
1. **`copy_analysis_agent.py`** - Agente que analisa estruturas de copy por canal
   - Lê planilha de copy (coluna A = estrutura)
   - Match com vídeos do YouTube (similaridade 90%+ palavra-por-palavra)
   - Busca retenção/watch time via `yt_video_metrics` + fallback Analytics API
   - Gera ranking por estrutura de copy
   - LLM (GPT-4o) gera observações narrativas e tendências
   - Relatório completo alinhado com HTML spec do Micha

2. **`monetization_oauth_collector.py`** - Coleta métricas via YouTube Analytics API
   - Coleta views, averageViewDuration, averageViewPercentage por vídeo
   - Paginação completa (200 por página, sem limite)
   - Salva em `yt_video_metrics` via UPSERT

3. **Campo `copy_spreadsheet_id` em `yt_channels`:**
   - Planilhas de copy analysis separadas das planilhas de upload (`spreadsheet_id`)
   - 21 canais com planilhas de copy configuradas
   - **CRÍTICO:** `spreadsheet_id` = upload, `copy_spreadsheet_id` = análise de copy. NUNCA misturar!

4. **Analytics API habilitado em 21 canais:**
   - Scope `yt-analytics.readonly` adicionado ao OAuth
   - Reauth feito em todos os 21 canais
   - Endpoints: `/api/copy-analysis/run/{channel_id}`, `/api/copy-analysis/run-all`, etc.

### 🔧 Fix: Dashboard Upload Mostra Último Vídeo ✅
**Desenvolvido:** 23/02/2026
**Status:** ✅ Corrigido e em produção

**Problema:** Quando canal tinha múltiplos uploads com sucesso no dia, dashboard mostrava o primeiro (vídeo antigo)
**Solução:** `upload_map` agora pega o mais recente por `created_at` quando mesmo status
**Arquivo:** `main.py` (linha ~6645)

### 🏢 Mission Control - Escritório Virtual ✅
**Desenvolvido:** 23/02/2026
**Status:** ✅ Endpoints funcionais

- 3 novos endpoints: `/mission-control`, `/api/mission-control/status`, `/api/mission-control/sala/{canal_id}`
- `mission_control.py` - Módulo separado com HTML + dados

---

## 🆕 ATUALIZAÇÕES RECENTES (16/02/2026):

### ⚡ OTIMIZAÇÃO CRÍTICA: Quota API 95% mais barata ✅
**Desenvolvido:** 13/02/2026 (commit `3421567`)
**Validado:** 16/02/2026
**Status:** ✅ Em produção no Railway

**Problema identificado:**
- `collector.py` usava `search.list` (100 units/request!) para buscar vídeos de cada canal
- Com ~232 canais: ~25,520 units/dia só em busca de vídeos
- Gastava 2-3 chaves API por coleta

**Solução implementada:**
1. **`get_channel_videos()` reescrita** para usar `playlistItems.list` (1 unit/request)
   - Converte `channel_id` (UC...) → uploads playlist (UU...) trocando 2 primeiros chars
   - Filtra por data no código (últimos 30 dias) - para quando encontra vídeo mais antigo
   - Busca detalhes com `videos.list` em batch de 50 (já existia)

2. **`get_request_cost()` atualizada** com custo de playlistItems = 1 unit

3. **7 chaves API suspensas removidas** (KEY_3,4,5,6,30,31,32)
   - 13 chaves ativas: KEY_7-10, KEY_21-29

**Resultado:**
| Métrica | Antes | Depois |
|---------|-------|--------|
| Custo vídeos (232 canais) | ~25,520 units | ~464 units |
| Custo comentários (43 canais) | ~860 units | ~860 units |
| **Total diário** | **~26,380** | **~1,324** |
| **Chaves usadas** | 2-3 | 0-1 |
| **Economia** | - | **95%** |

**Histórico de coleta no dashboard:**
- Campo `requisicoes_usadas` mostra total de TODAS as chamadas API (vídeos + comentários + channels + detalhes)
- Contabilização via `collector.total_quota_units` que soma custos de cada endpoint
- A partir de 16/02 o histórico reflete os novos valores otimizados

### 🎬 Animação de Upload Forçado no Dashboard ✅
**Desenvolvido:** 16/02/2026
**Status:** ✅ 100% funcional

**O que foi implementado:**
1. **Animação visual ao forçar upload:**
   - Clicou e confirmou → botão vira ⏳ girando + pulsando (CSS spin + pulse)
   - Upload com sucesso → botão vira ✅ por 15 segundos + tabela atualiza imediatamente
   - Upload com erro → botão vira ❌ por 5 segundos
   - Sem vídeo na planilha → alert em até 12 segundos + botão volta ao normal

2. **Polling inteligente:**
   - Captura status ANTES do upload para comparar mudanças
   - Polling a cada 3s (máximo 4 tentativas = 12s timeout)
   - Estado preservado entre rebuilds da tabela (variáveis globais)

3. **Correções relacionadas:**
   - `upload_map` prioriza `sucesso > erro > sem_video` (múltiplos registros/dia)
   - Backend retorna `sem_video` imediato se verificação de planilha falha
   - Cache do dashboard reduzido de 10s para 3s (`_DASH_CACHE_TTL`)

**Arquivos alterados:** `main.py` (CSS, JS `forcarUpload()`, endpoint force, `upload_map`)

### 🔧 Correção OAuth + Script Re-auth ✅
**Desenvolvido:** 16/02/2026
**Status:** ✅ Corrigido

**Problema:** Canal "Crônicas da Coroa" com `invalid_grant` - refresh token revogado
**Solução:** Re-autorização via `reauth_channel_oauth.py` (script reescrito)
- Aceita `channel_id` como argumento CLI ou lista interativa
- Usa `localhost:8080` redirect (mesmo que wizard v3)
- Inclui 4 scopes OAuth obrigatórios
- Valida token com YouTube API antes de salvar

---

## 🆕 ATUALIZAÇÕES RECENTES (03/02/2026):

### 🔧 CORREÇÃO CRÍTICA: OAuth Scopes para Playlists ✅
**Desenvolvido:** 03/02/2026
**Status:** ✅ Bug resolvido e sistema 100% funcional

**Problema identificado:**
- Sistema fazia upload com sucesso, mas não adicionava vídeos às playlists
- Erro 403: `insufficientPermissions` ao tentar adicionar à playlist
- Causa: Falta do scope `youtube.force-ssl` na autorização OAuth

**Solução implementada:**
1. **4 scopes obrigatórios configurados:**
   - `youtube.upload` - Upload de vídeos
   - `youtube` - Leitura do canal
   - `youtube.force-ssl` - **Gerenciar playlists/canal** ⭐ NOVO
   - `spreadsheets` - Google Sheets

2. **Arquivos corrigidos:**
   - `yt_uploader/oauth_manager.py` (linha 80-85)
   - `add_canal_wizard_v2.py` (linha 242-247)
   - `add_canal_wizard_v3.py` (linha 224-229)

3. **Validação realizada (15:51):**
   - ✅ Upload funciona perfeitamente
   - ✅ Playlists são adicionadas corretamente
   - ✅ Sheets atualizado com status
   - ✅ Refresh automático de tokens

**Ação necessária:**
- Canais adicionados antes de 03/02/2026 devem refazer OAuth com wizard v3
- Aceitar TODAS as permissões durante autorização

**Documentação criada:**
- `SISTEMA_UPLOAD_COMPLETO_2026.md` - Documentação completa do sistema

---

## 🆕 ATUALIZAÇÕES RECENTES (02/02/2026):

### 💬 SISTEMA DE COMENTÁRIOS - 100% Funcional e Otimizado
**Desenvolvido:** 23-27/01/2025
**Otimizado:** 02/02/2026
**Coleta histórica completa:** 13/02/2026
**Status:** ✅ Completo, testado e em produção

**O que foi implementado:**
1. **Tabela `video_comments`:** 38 campos para gestão completa
2. **6 novos endpoints:** API completa para comentários
3. **Coleta histórica completa:** 15.074 comentários coletados (TODOS os vídeos, sem limite)
4. **Tradução automática:** 100% traduzidos para PT-BR
5. **Sugestões GPT:** 1.860 respostas prontas
6. **Frontend React:** Componente completo para Lovable

**Números atualizados (13/02/2026):**
- 43 canais monitorados (tipo="nosso")
- 6 canais monetizados (foco das respostas)
- 15.074 comentários totais coletados
- 100% traduzidos para PT-BR
- 11 canais em português (não gastam tokens GPT)
- Coleta histórica completa (TODOS os vídeos de cada canal)

**Documentação:** `.claude/3_SISTEMA_COMENTARIOS/`
- README.md - Visão geral
- ENDPOINTS.md - API completa
- BANCO_DADOS.md - Estrutura tabela
- IMPLEMENTACAO.md - Timeline
- FRONTEND.md - Componente React

**Correção importante (27/01):**
- Função `get_comments_summary()` corrigida
- Agora filtra APENAS comentários dos monetizados
- Evita confusão entre coleta (todos) e resposta (monetizados)

### 🔧 6 FIXES DO SISTEMA DE COMENTÁRIOS (13/02/2026):
**Status:** ✅ Todos corrigidos e validados

1. **Fix: campo `comment_text_original`** - Coleta agora salva no campo correto
2. **Fix: campo `response_generated_at`** - Atualizado ao gerar sugestões GPT
3. **Fix: campo `comentarios_sem_resposta`** - Endpoint retorna campo correto
4. **Fix: `videos_to_collect` sem limite** - Coleta TODOS os vídeos (não mais TOP 20)
5. **Fix: `total_coletados` no response** - Endpoint retorna total real coletado
6. **Fix: coleta histórica completa** - 15.074 comentários de 43 canais

**Resultado:** Sistema de comentários 100% funcional com coleta histórica completa

### 🔧 CORREÇÕES DE BUGS ANTERIORES (02/02/2026):
**Status:** ✅ Corrigidos e validados

**Bug #1 - collector.py:** Variável `recent_videos` → corrigido
**Bug #2 - engagement_preprocessor.py:** Campo `all_comments` → corrigido

---

## 📊 DASHBOARD DE UPLOAD DIÁRIO - 100% Funcional
**Desenvolvido:** Janeiro 2026
**Última atualização:** 13/02/2026
**Status:** ✅ 100% funcional e em produção

### Dashboard v2 (Railway - PRINCIPAL):
- **URL Produção:** `https://youtube-dashboard-backend-production.up.railway.app/dash-upload`
- **Implementado em:** `main.py` (linhas 5994-6741, ~750 linhas)
- **Cache:** 10 segundos entre requests
- **Atualização:** A cada 5 segundos (JavaScript)
- **Endpoints:** `/dash-upload`, `/api/dash-upload/status`, `/api/dash-upload/canais/{id}/historico`, `/api/dash-upload/historico-completo`

### Dashboard v1 (Local - Legado):
- `dash_upload_final.py` (887 linhas) - Dashboard Flask na porta 5006
- **URL Local:** http://localhost:5006

### Funcionalidades (ambas versões):
- Dashboard visual organizado por subnichos
- Estatísticas em tempo real (Total, Sucesso, Erros, Pendentes, Sem Vídeo)
- Tags de idioma automáticas (PT, EN, ES, DE, FR, AR, etc.)
- Modal de histórico (últimos 30 dias por canal)
- Links diretos para Google Sheets
- Cores e emojis por subnicho (Monetizados, Relatos de Guerra, etc.)
- Subnichos ordenados por quantidade de uploads com sucesso

### Sistema de Upload Automático:
- **Orquestrador:** `daily_uploader.py` (1025 linhas)
- **Horário:** 5:30 AM diário (Railway cron)
- **Capacidade:** 35 canais ativos
- **Integração:** Google Sheets + Drive + YouTube API
- **Sistema de retry:** 3 tentativas por vídeo

### Arquitetura:
- **Módulo:** `_features/yt_uploader/` (uploader.py, oauth_manager.py, sheets.py, database.py)
- **OAuth:** 4 scopes obrigatórios (incluindo youtube.force-ssl para playlists)
- **Credenciais isoladas:** Por canal (nova arquitetura)
- **Banco:** Tabelas `yt_channels`, `yt_canal_upload_diario`, `yt_oauth_tokens`, `yt_upload_queue`

### Como usar:
```bash
# Acessar dashboard v2 online (principal)
# https://youtube-dashboard-backend-production.up.railway.app/dash-upload

# Rodar dashboard local (legado)
python dash_upload_final.py
# Acesse: http://localhost:5006

# Upload manual forçado
python forcar_upload_manual_fixed.py --canal "Nome do Canal"

# Verificar tokens OAuth
python check_oauth_definitivo.py

# Adicionar novo canal
python add_canal_wizard_v3.py
```

**Documentação completa:** `_features/dash_upload/DASHBOARD_UPLOAD_SISTEMA_ATUAL.md`

---

## 🆕 ATUALIZAÇÕES RECENTES (23/01/2026):

### 🚀 OTIMIZAÇÃO CRÍTICA: Materialized Views + Cache 24h
**Performance alcançada:** Dashboard de 3000ms → 0.109ms (**27,522x mais rápido!**)

**Implementação:**
1. **Duas Materialized Views no Supabase:**
   - `mv_canal_video_stats` - Pré-calcula total_videos e total_views
   - `mv_dashboard_completo` - Consolida TODOS dados do dashboard

2. **Sistema de Cache 24 horas:**
   - Cache global no servidor (compartilhado entre TODOS usuários)
   - Primeiro acesso do dia: busca da MV (~100ms) e cria cache
   - Próximos acessos: instantâneo do cache (< 1ms)
   - Cache limpo automaticamente após coleta diária

3. **Mudanças no código:**
   - **database.py:** `get_dashboard_from_mv()`, `refresh_all_dashboard_mvs()`
   - **main.py:** Sistema completo de cache (linhas 50-170)
   - Endpoints `/api/canais` e `/api/canais-tabela` usando MV + cache

**Resultado:**
- ✅ Dashboard abre INSTANTANEAMENTE
- ✅ 99% menos queries ao Supabase (1/dia vs 100+)
- ✅ 90% menos CPU/memória no Railway
- ✅ Escalável para 1000+ canais

---

## 🆕 ATUALIZAÇÕES RECENTES (22/01/2026):

### 0. sync.py v4.3 - Sync Automático Completo
**Arquivo:** `sync.py`

- ✅ Passo [0/7]: Verifica se docs foram atualizados
- ✅ Mapeamento código → documentação (main.py → 08_API_ENDPOINTS, etc.)
- ✅ Mostra LEMBRETE se docs podem precisar de atualização (não bloqueia)
- ✅ Sync é 100% automático - apenas puxa, commita e envia
- ✅ **NOVO:** Mostra última mudança recebida após pull (mensagem + data)
- ✅ Fix: `git add -A` para garantir que todos arquivos são adicionados
- ✅ Fix: Caracteres ASCII para compatibilidade Windows

**Workflow obrigatório:**
```
1. Alterar código
2. ATUALIZAR DOCS (.claude/CLAUDE.md, CHANGELOG.md, 2_DASHBOARD_TECNICO/*.md)
3. python sync.py
4. Railway deploya
```

### 1. Bug Fix: Colisão de Variável `offset` (CRÍTICO)
**Arquivo:** `database.py` (linhas 342, 348, 359)
**Função:** `get_canais_with_filters()`

- **Problema:** Variável `offset` do loop de paginação sobrescrevia o parâmetro `offset` da função
- **Sintoma:** API `/api/canais` retornava `[]` (array vazio)
- **Solução:** Renomeada para `pagination_offset`
- **Commit:** `8bd8777`

### 2. Bug Fix: Cálculo de `inscritos_diff`
**Arquivo:** `database.py` (linhas 427-429)

- **Problema:** Assumia que `datas_disponiveis[1]` era "ontem", mas podia ser de vários dias atrás
- **Sintoma:** `inscritos_diff` mostrava diferença errada ou nula
- **Solução:** Agora busca especificamente a data de ontem: `data_ontem_str = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()`
- **Commit:** `809e596`

### 3. Bug Fix: Paginação do Histórico
**Arquivo:** `database.py`

- **Problema:** Query não buscava todos os registros do histórico
- **Solução:** Corrigida lógica de paginação para buscar todos os records
- **Commit:** `79de42f`

### 4. Campos de Views Growth/Diff
**Endpoint:** `GET /api/canais`

Novos campos disponíveis (calculados automaticamente):
- `views_growth_7d` - Crescimento % de views nos últimos 7 dias
- `views_growth_30d` - Crescimento % de views nos últimos 30 dias
- `views_diff_7d` - Diferença absoluta de views (7 dias)
- `views_diff_30d` - Diferença absoluta de views (30 dias)

**Status Atual:**
- 300 canais ativos retornando dados
- 228 canais com `views_growth_7d`
- 287 canais com `inscritos_diff`

---

## 🆕 ATUALIZAÇÕES RECENTES (30/01/2026):

### Grande Reorganização de Canais - Limpeza do Dashboard ✅
**Desenvolvido:** 30/01/2026
**Status:** ✅ Dashboard limpo e organizado

**O que foi feito:**
1. **Remoção de 4 subnichos completos (117 canais):**
   - Psicologia & Mindset: 62 canais removidos
   - Empreendedorismo: 29 canais removidos
   - Historia Reconstruida: 1 canal removido
   - Notícias e Atualidade: 12 canais removidos
   - Guerras/Civilizações/Terror: 24 canais nossos reorganizados

2. **Reorganização dos canais nossos (de 50 para 26):**
   - Mantidos apenas canais específicos de nichos dark
   - 2 canais movidos para Desmonetizados
   - 24 canais não essenciais removidos
   - Foco em: Monetizados (8), Relatos de Guerra (2), Historias Sombrias (1), Terror (1), Desmonetizados (14)

3. **Estado final do sistema:**
   - **Antes:** 304 canais totais (misturados)
   - **Depois:** 232 canais (26 nossos + 206 minerados)
   - **Redução:** 72 canais (-24%)
   - Dashboard mais limpo e focado

4. **Scripts criados para manutenção:**
   - `delete_subnichos.py` - Remove subnichos completos
   - `reorganizar_canais.py` - Reorganiza canais nossos
   - `update_materialized_views.py` - Atualiza MVs manualmente
   - Todos com backup automático antes de mudanças

### Correção Crítica: Endpoint DELETE Revertido ✅
**Desenvolvido:** 30/01/2026
**Status:** ✅ Erro 500 corrigido

**Problema identificado:**
- Endpoint DELETE modificado causava erro 500 em produção
- Erro: "argument of type 'NoneType' is not iterable"
- Dashboard não conseguia deletar canais

**Solução implementada:**
1. **Revertido DELETE para versão original:**
   - Mantém parâmetro `permanent` (false=desativa, true=deleta)
   - Removido endpoint `/desativar` desnecessário
   - Commit: `d7f3517`

2. **Script separado para MVs:**
   - `update_materialized_views.py` criado
   - Não interfere com endpoints de produção
   - Pode ser executado manualmente quando necessário

### Otimização de Materialized Views - Solução Simplificada ✅
**Desenvolvido:** 30/01/2026
**Status:** ✅ Dashboard sempre atualizado

**Solução implementada (SIMPLES E EFETIVA):**
1. **Botão "Atualizar" no dashboard agora:**
   - Chama `POST /api/cache/clear`
   - Atualiza Materialized Views
   - Limpa cache do servidor
   - Dashboard mostra dados corretos imediatamente

2. **Endpoint `/api/cache/clear` já faz tudo:**
   - ✅ Limpa cache global (Dashboard + Tabela)
   - ✅ Força refresh das MVs (`refresh_all_dashboard_mvs()`)
   - ✅ Tratamento de erro (não quebra se MV falhar)
   - ✅ Retorna status da operação

3. **Integração com Lovable configurada:**
   - Frontend atualizado para chamar endpoint correto
   - Feedback visual durante atualização
   - Toast de sucesso/erro
   - Recarrega dados automaticamente

**Resultado:** Qualquer mudança no sistema → Clique no botão Atualizar → Dashboard sincronizado!

---

## 🆕 ATUALIZAÇÕES RECENTES (29/01/2026):

### Reorganização Completa do Projeto ✅
**Desenvolvido:** 29/01/2026 (v1) | 03/02/2026 (v2)
**Status:** ✅ Projeto limpo e totalmente organizado

### 🆕 REORGANIZAÇÃO v2 (03/02/2026):
**Nova estrutura com 5 pastas organizadoras:**

```
youtube-dashboard-backend/
├── _archives/         # Backups, código antigo, documentação histórica
├── _database/         # Arquivos de banco e migrations
├── _development/      # Ferramentas de desenvolvimento
│   ├── scripts/       # Scripts organizados por categoria
│   ├── utilities/     # Utilitários do sistema
│   ├── guides/        # Guias e instruções
│   └── prompts/       # Templates de prompts
├── _features/         # Funcionalidades isoladas
│   ├── agents/        # Sistema de agentes IA
│   ├── yt_uploader/   # Sistema de upload YouTube
│   ├── frontend-code/ # Componentes React/TypeScript
│   └── kanban-system/ # Sistema Kanban completo
├── _runtime/          # Arquivos gerados em runtime
│   ├── logs/          # Logs do sistema
│   ├── reports/       # Relatórios gerados
│   └── *.json/*.db    # Arquivos de dados runtime
└── [22 arquivos .py]  # Core do backend no ROOT
```

**Mudanças de imports (apenas 2 arquivos):**
- `main.py`: yt_uploader → _features.yt_uploader
- `agents_endpoints.py`: agents → _features.agents

**Resultado:** De 32+ pastas misturadas → 6 pastas super organizadas!

**O que foi feito:**
1. **Limpeza de arquivos temporários:**
   - 11 arquivos de teste/temporários deletados
   - Scripts SQL movidos para pasta apropriada
   - Código órfão movido para /legacy/

2. **Nova estrutura de pastas (atualizada 03/02/2026):**
   - `/_development/scripts/maintenance/` - Scripts de manutenção
   - `/_development/scripts/database/` - Arquivos SQL
   - `/_development/scripts/tests/` - Scripts de teste
   - `/_features/frontend-code/` - Componentes React/TypeScript
   - `/_archives/legacy/` - Código descontinuado

3. **Documentação criada:**
   - `ESTRUTURA_PROJETO.md` - Guia completo da estrutura
   - READMEs em cada pasta nova
   - Regras claras de onde salvar novos arquivos

**IMPORTANTE - Arquivos que NUNCA devem sair do ROOT:**
- main.py, database.py, collector.py, notifier.py
- financeiro.py, analytics.py, comments_logs.py
- agents_endpoints.py, monetization_endpoints.py
- gpt_response_suggester.py

### Sistema Kanban - Endpoint de Movimentação ✅
**Desenvolvido:** 29/01/2026
**Status:** ✅ 100% funcional e testado

**O que foi implementado:**
1. **Novo endpoint `/api/kanban/note/{id}/move`:**
   - Move notas entre colunas (drag & drop)
   - Aceita `stage_id` (Lovable) ou `coluna_id` (backend)
   - Resolve erro 404 no frontend

2. **Campo `coluna_id` nas notas:**
   - Notas podem existir em qualquer coluna
   - Independente do status do canal
   - Suporte ao "Card Principal"

3. **Tipo `note_moved` no histórico:**
   - Constraint atualizada no Supabase
   - Registro detalhado de movimentações

4. **Correção Reinos Sombrios:**
   - Status corrigido para `canal_constante`
   - Consistência com monetizado=true

**Testes realizados:**
- ✅ 63 canais com Kanban configurado
- ✅ Movimentação real testada (canal 875)
- ✅ Sistema salvando tudo corretamente
- ✅ 13 canais com mudanças em 24h

### Correções Críticas - Sistema de Comentários ✅
**Desenvolvido:** 29/01/2026 (tarde)
**Status:** ✅ 100% corrigido e testado

**PROBLEMAS CORRIGIDOS:**

1. **inscritos_diff calculado para TODOS os canais (ERRO):**
   - **Problema:** Estava calculando para 287+ canais (nossos + minerados)
   - **Correção:** Agora calcula APENAS para canais tipo="nosso" (63 canais)
   - **Código:** `database.py` linha 437: `if item.get("tipo") == "nosso":`
   - **Impacto:** Economia de processamento e dados corretos

2. **"Comentários novos hoje" sempre mostrando 0:**
   - **Problema:** Filtro usava `created_at` (data de publicação no YouTube)
   - **Correção:** Criado campo `collected_at` (data de coleta no banco)
   - **Código:** `database.py` linha 2438: `.gte('collected_at', today)`
   - **SQL:** `add_collected_at_column.sql` executado no Supabase
   - **Impacto:** Dashboard mostra corretamente comentários coletados no dia

3. **Campo collected_at adicionado:**
   - **Tabela:** `video_comments` agora tem 3 campos de data:
     - `published_at` - Quando foi publicado no YouTube
     - `created_at` - Cópia do published_at (Supabase auto)
     - `collected_at` - Quando NÓS coletamos (NOVO)
   - **Status:** 5.785 comentários já com collected_at preenchido
   - **Índice:** Criado para melhor performance de filtros

**Verificação realizada:**
- Script `verify_fixes.py` criado e testado
- Confirmou todas as correções funcionando
- SQL executado com sucesso no Supabase

**Números confirmados:**
- 63 canais tipo="nosso" (inscritos_diff)
- 0 canais tipo="minerado" com inscritos_diff
- 5.785 comentários com collected_at
- Filtro "novos hoje" configurado corretamente

---

## 📜 ATUALIZAÇÕES ANTERIORES (17/01/2026):

### 1. Otimização do Sistema de Coleta (50% menos API calls)
**Arquivos:** `collector.py`, `main.py`, `database.py`

- ✅ `get_canal_data()` agora retorna tuple `(stats, videos)` - elimina duplicação
- ✅ Timeout aumentado de 30s para 60s
- ✅ Economia de ~50% da quota diária

### 2. Tracking de Falhas de Coleta
**Novos campos em `canais_monitorados`:**
- `coleta_falhas_consecutivas` (INTEGER)
- `coleta_ultimo_erro` (TEXT)
- `coleta_ultimo_sucesso` (TIMESTAMP)

**Novas funções em `database.py`:**
- `marcar_coleta_sucesso()` - reseta contador de falhas
- `marcar_coleta_falha()` - incrementa contador e salva erro
- `get_canais_problematicos()` - lista canais com falhas

### 3. Novos Endpoints de Diagnóstico
- `GET /api/canais/problematicos` - Lista canais com erros de coleta
- `GET /api/canais/sem-coleta-recente` - Canais sem coleta nos últimos X dias

### 4. Melhorias no Endpoint `/api/coletas/historico`
Agora retorna:
```json
{
  "historico": [...],
  "canais_com_erro": {
    "total": 8,
    "lista": [
      {
        "nome": "Canal X",
        "subnicho": "Terror",
        "tipo": "nosso",
        "erro": "Dados não salvos",
        "lingua": "portuguese",
        "url_canal": "https://youtube.com/@..."
      }
    ]
  },
  "quota_info": {
    "videos_coletados": 6029,
    ...
  }
}
```

### 5. Limpeza de Canais
- Deletados 24 canais problemáticos (22 minerados inativos + 2 com URL inválida)
- Total atual: **305 canais ativos**

---

## 📜 ATUALIZAÇÕES ANTERIORES (02/12/2025):

### 1. Nova Feature: Aba "Tabela" (Nossos Canais)
**Endpoint:** `GET /api/canais-tabela`
- Retorna canais `tipo="nosso"` agrupados por subnicho
- Ordenação por desempenho: **melhor → menor → zero → nulo**
- Response inclui: `inscritos`, `inscritos_diff` (ganho ontem→hoje), `ultima_coleta`
- Frontend pronto: `_features/frontend-code/TabelaCanais.tsx` (366 linhas, mobile-first)
- Documentação: `INTEGRACAO_ABA_TABELA.md`

**Lógica de Ordenação:**
- Categoria 0: Positivos (+35, +10, +2...) - Melhor no topo
- Categoria 1: Negativos (-5, -10...) - Perdas
- Categoria 2: Zero (0) - Sem mudança
- Categoria 3: Null (--) - Sem dados, sempre no final
- Tiebreaker: Maior número de inscritos

### 2. Sistema de Notificações - Bugs Corrigidos
**Arquivo:** `notifier.py`
- ✅ Query SQL otimizada (dados em uma query só)
- ✅ Filtro de subnicho case-insensitive
- ✅ Permite re-notificação para milestones maiores
- **Status:** 100% funcional (69 notificações criadas no teste)

### 3. Expansão de API Keys
**Arquivo:** `collector.py`
- ✅ Adicionadas 8 novas chaves (KEY_25 a KEY_32)
- ✅ Total: 20 chaves (antes: 12)
- ✅ Capacidade +67% (~2M requisições/dia)
- **Configuração:** Railway (variáveis de ambiente)

### 4. Arquivos de Referência Criados:
- `_features/frontend-code/TabelaCanais.tsx` - Componente React completo
- `INTEGRACAO_ABA_TABELA.md` - Guia de integração Lovable
- `FIX_ORDENACAO_TABELA.md` - Documentação técnica do sorting
- `VALIDACAO_API_KEYS.md` - Validação das 8 novas chaves

## 🎯 INTEGRAÇÃO FUTURA:
Este backend será integrado com o Sistema Musical (D:\ContentFactory\music_queue_system)

Para documentação completa do Dashboard, consulte:
`D:\ContentFactory\.claude\DASHBOARD_MINERACAO.md`

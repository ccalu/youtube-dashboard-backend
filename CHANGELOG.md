# CHANGELOG - CEREBRO CELLIBS

> Este arquivo documenta todas as alteracoes na pasta /docs.
> Atualizar sempre que fizer sync.

---

## [30/01/2026 - v6] - Grande Reorganização e Otimização de MVs

### 🧹 Reorganização Massiva do Dashboard

**Data:** 30/01/2026
**Status:** ✅ Completo
**Desenvolvedor:** Claude com Cellibs
**Propósito:** Limpar dashboard e focar em nichos essenciais

### Mudanças Implementadas

1. **Remoção de 4 subnichos completos (117 canais)**
   - **Psicologia & Mindset:** 62 canais deletados
   - **Empreendedorismo:** 29 canais deletados
   - **Historia Reconstruida:** 1 canal deletado
   - **Notícias e Atualidade:** 12 canais deletados
   - **Total removido:** 104 canais minerados + 13 nossos

2. **Reorganização dos canais nossos**
   - **Antes:** 50 canais nossos (misturados)
   - **Depois:** 26 canais nossos (focados)
   - **Movidos para Desmonetizados:** 2 canais
   - **Deletados permanentemente:** 24 canais
   - **Distribuição final:**
     - Monetizados: 8 canais
     - Desmonetizados: 14 canais
     - Relatos de Guerra: 2 canais
     - Historias Sombrias: 1 canal
     - Terror: 1 canal

3. **Estado final do sistema**
   - **Total antes:** 304 canais
   - **Total depois:** 232 canais (26 nossos + 206 minerados)
   - **Redução:** 72 canais (-24%)
   - **Performance:** Dashboard mais rápido e focado

### Correção Crítica: Endpoint DELETE

**Problema:** Endpoint modificado causava erro 500 em produção
**Solução:**
- Revertido para versão original com parâmetro `permanent`
- Removido endpoint `/desativar` desnecessário
- Criado script separado `update_materialized_views.py`
- **Commit:** d7f3517

### Otimização de Materialized Views

**Solução Simplificada Implementada:**
1. **Botão "Atualizar" no dashboard:**
   - Chama `POST /api/cache/clear`
   - Atualiza MVs automaticamente
   - Limpa cache do servidor
   - Dashboard sincronizado em ~3 segundos

2. **Endpoint `/api/cache/clear` melhorado:**
   - Limpa cache global (Dashboard + Tabela)
   - Força refresh das MVs com `refresh_all_dashboard_mvs()`
   - Tratamento de erro robusto
   - Retorna status detalhado

3. **Integração com Lovable:**
   - Frontend configurado para chamar endpoint correto
   - Feedback visual durante atualização
   - Toast de sucesso/erro
   - Reload automático dos dados

### Scripts de Manutenção Criados

- `delete_subnichos.py` - Remove subnichos completos com backup
- `reorganizar_canais.py` - Reorganiza canais nossos
- `update_materialized_views.py` - Atualiza MVs manualmente
- `force_refresh_mv.py` - Força refresh simples das MVs

### Arquivos de Backup Gerados

- `backup_canais_removidos_*.json` - Backup dos deletados
- `backup_reorganizacao_*.json` - Backup da reorganização
- `backup_minerados_removidos_*.json` - Backup dos minerados

---

## [29/01/2026 - v5] - Correções Críticas: Sistema de Comentários

### 🔧 Correções Críticas Implementadas

**Data:** 29/01/2026 (tarde)
**Status:** ✅ 100% corrigido e testado
**Desenvolvedor:** Claude com Cellibs
**Propósito:** Corrigir problemas críticos no dashboard de comentários

### Problemas Corrigidos

1. **inscritos_diff calculado para TODOS os canais**
   - **Problema:** Calculando para 287+ canais (nossos + minerados)
   - **Correção:** Agora calcula APENAS para tipo="nosso" (63 canais)
   - **Arquivo:** `database.py` linha 437
   - **Código:** `if item.get("tipo") == "nosso":`
   - **Impacto:** Economia de 78% no processamento

2. **"Comentários novos hoje" sempre mostrando 0**
   - **Problema:** Filtro usava `created_at` (data publicação YouTube)
   - **Correção:** Criado campo `collected_at` (data de coleta)
   - **Arquivo:** `database.py` linha 2438
   - **SQL:** `add_collected_at_column.sql` executado no Supabase
   - **Impacto:** Dashboard agora mostra dados reais

3. **Novo campo collected_at adicionado**
   - **Tabela:** `video_comments`
   - **Campos de data:**
     - `published_at` - Quando foi publicado no YouTube
     - `created_at` - Cópia do published_at (Supabase auto)
     - `collected_at` - Quando NÓS coletamos (NOVO)
   - **Status:** 5.785 comentários já com collected_at preenchido
   - **Índice:** Criado para melhor performance

### Testes e Verificação

- ✅ Script `verify_fixes.py` criado e executado
- ✅ 63 canais tipo="nosso" com inscritos_diff
- ✅ 0 canais tipo="minerado" com inscritos_diff
- ✅ 100% dos comentários com collected_at
- ✅ Filtro "novos hoje" funcionando corretamente

### Arquivos Criados/Modificados

- **Modificados:**
  - `database.py` - 3 correções principais
  - `.claude/CLAUDE.md` - Documentação atualizada

- **Criados:**
  - `add_collected_at_column.sql` - Script SQL para Supabase
  - `verify_fixes.py` - Script de verificação

### Impacto na Coleta Diária (30/01 às 08:00 UTC)

- Comentários novos aparecerão corretamente
- inscritos_diff apenas para canais "nossos"
- 1.7k comentários aguardando resposta serão processados

---

## [29/01/2026 - v4] - Sistema Kanban: Endpoint de Movimentação e Compatibilidade

### 🚀 Nova Feature: Drag & Drop Entre Colunas

**Data:** 29/01/2026 14:30
**Status:** ✅ Implementado e testado
**Desenvolvedor:** Claude com Cellibs
**Propósito:** Resolver erro 404 no Lovable e adicionar movimentação de notas

### Implementações Principais

1. **Novo Endpoint de Movimentação**
   - `PATCH /api/kanban/note/{id}/move` - Move notas entre colunas
   - Compatibilidade total com drag & drop do frontend
   - Histórico detalhado de movimentações

2. **Compatibilidade stage_id ↔ coluna_id**
   - Frontend usa `stage_id` (Lovable)
   - Backend usa `coluna_id` (Supabase)
   - Property `target_column` aceita ambos os nomes
   - Classe `KanbanMoveNoteRequest` com compatibilidade dupla

3. **Campo coluna_id Adicionado**
   - Notas podem existir em qualquer coluna
   - Independente do status do canal
   - Suporte ao "Card Principal" que define status

4. **Atualizações no Histórico**
   - Tipo `note_moved` adicionado ao constraint
   - Registro detalhado de movimentações
   - SQL executado: `update_kanban_history_constraint.sql`

5. **Correção Status Reinos Sombrios**
   - Canal monetizado com status inconsistente
   - Corrigido para `canal_constante`
   - ID 875 agora com status correto

### Testes Realizados

- ✅ 63 canais com status Kanban configurado
- ✅ Sistema salvando todas mudanças corretamente
- ✅ Movimentação real testada (canal 875)
- ✅ Histórico funcionando com note_moved
- ✅ 13 canais com mudanças nas últimas 24h

---

## [28/01/2025 - v3] - Sistema Kanban 100% Integrado e Testado

### 🚀 Nova Feature: Sistema Kanban Completo

**Data:** 28/01/2025 17:35
**Status:** ✅ 100% Funcional e testado
**Desenvolvedor:** Claude com Cellibs
**Propósito:** Gestão visual dos 63 canais para Micha

### Implementações Principais

1. **Backend Totalmente Integrado**
   - 479 linhas de código adicionadas ao `main.py`
   - 10 endpoints funcionais para gestão Kanban
   - Tratamento robusto de microsegundos em timestamps
   - Correção de campos: `nome_canal` (não `nome`)

2. **Tabelas do Banco de Dados**
   - Confirmado: coluna `monetizado` já existia (não duplicada)
   - `kanban_status` e `kanban_status_since` adicionados
   - `kanban_notes` - Sistema completo de notas
   - `kanban_history` - Histórico com soft delete

3. **Endpoints Implementados**
   - `GET /api/kanban/structure` - Estrutura completa
   - `GET /api/kanban/canal/{id}/board` - Kanban individual
   - `PATCH /api/kanban/canal/{id}/move-status` - Mudar status
   - `POST /api/kanban/canal/{id}/note` - Criar nota
   - `PATCH /api/kanban/note/{id}` - Editar nota
   - `DELETE /api/kanban/note/{id}` - Deletar nota
   - `PATCH /api/kanban/canal/{id}/reorder-notes` - Reordenar
   - `GET /api/kanban/canal/{id}/history` - Ver histórico
   - `DELETE /api/kanban/history/{id}` - Soft delete

### Correções Implementadas

1. **Campo nome_canal**
   - Problema: Código usava `nome` mas banco usa `nome_canal`
   - Solução: Corrigido em todas as ocorrências (linhas 4027, 4065, 4210, 4235, 4281 do main.py)
   - Arquivos atualizados: `main.py`, `kanban_endpoints.py`

2. **Tratamento de Microsegundos**
   - Problema: Supabase retorna timestamps com precisão variável
   - Solução: Tratamento robusto com padding de zeros
   - Código: Linhas 4036-4058 e 4148-4168 do main.py

### Documentação Atualizada

1. **LOVABLE_INTEGRATION.md**
   - Adicionada seção "CORREÇÕES IMPORTANTES"
   - Documentado tratamento de microsegundos
   - Alerta sobre diferenças entre arquivos

2. **kanban_endpoints.py**
   - Alinhado com código real do main.py
   - Correções de campos aplicadas
   - Tratamento de datas adicionado

### Testes Realizados

- ✅ Coluna monetizado verificada (9 monetizados, 54 não monetizados)
- ✅ Estrutura Kanban testada
- ✅ Kanban individual funcionando
- ✅ Mudança de status OK
- ✅ CRUD de notas completo
- ✅ Histórico e soft delete OK
- ✅ Reordenação funcionando

### Arquivos Modificados
- `main.py` - Código principal integrado
- `kanban-system/docs/LOVABLE_INTEGRATION.md` - Documentação atualizada
- `kanban-system/backend/kanban_endpoints.py` - Arquivo de referência corrigido
- `test_kanban.py` - Script de testes completo

---

## [28/01/2025 - v2] - Correções Adicionais do Engagement Endpoint

### 🔥 Fixes nos Endpoints de Comentários

**Data:** 28/01/2025 15:30
**Problema:** Lovable reportou 3 problemas no engagement endpoint
**Status:** ✅ Corrigido e pronto para deploy

### Problemas Resolvidos

1. **Array all_comments limitado a 20 itens**
   - Antes: `'all_comments': formatted_comments[:20]`
   - Agora: `'all_comments': formatted_comments` (sem limite)
   - Arquivo: `main.py` linha 1039

2. **Campo video_title retornando null**
   - Adicionado fallback com ID do vídeo quando título não existe
   - Arquivo: `main.py` linhas 1016-1021

3. **Contagem de comentários inconsistente entre endpoints**
   - Adicionados campos unificados:
     - `total_comments_youtube`: contagem do YouTube (videos_historico)
     - `total_comments_analyzed`: contagem analisada (video_comments)
     - `coverage_pct`: porcentagem de cobertura
     - `overall_coverage_pct`: cobertura geral no summary
   - Arquivo: `main.py` linhas 1023-1112

4. **Campo actionable_count sem detalhes**
   - Adicionado `actionable_breakdown` com contagem por tipo (audio, video, content, technical, other)
   - Adicionado `videos_needing_action` com lista de vídeos
   - Adicionado `videos_needing_action_count` com total
   - Arquivo: `main.py` linhas 1042-1108

### Scripts Criados/Atualizados
- `fix_database_schema.py` - Adiciona coluna translation_updated_at
- `force_complete_collection.py` - Coleta forçada sem limites

---

## [28/01/2025] - Correção Crítica do Sistema de Comentários

### 🔥 Fixes Críticos: Limites de Coleta Removidos

**Data:** 28/01/2025
**Problema:** Coleta de comentários estava limitada e incompleta
**Status:** ✅ Corrigido e pronto para deploy

### Problemas Resolvidos

1. **Limite de 20 vídeos REMOVIDO**
   - Antes: Processava apenas 20 vídeos mais recentes
   - Agora: Processa TODOS os vídeos dos últimos 30 dias
   - Arquivo: `main.py` linha 2676

2. **Limite reduzido de 500 para 100 comentários**
   - Antes: 500 comentários por vídeo (desnecessário)
   - Agora: 100 comentários por vídeo (otimizado)
   - Arquivo: `collector.py` linha 964

3. **Bug de tradução corrigido**
   - Problema: Comentários em PT marcados como traduzidos incorretamente
   - Solução: 588 comentários corrigidos
   - Script: `fix_translation_issue.py` criado e executado

4. **Script de coleta forçada criado**
   - Arquivo: `force_complete_collection.py`
   - Permite forçar coleta manual completa
   - Processa TODOS os canais sem limites

### Impacto das Mudanças
- De: ~3 comentários por canal (limitado)
- Para: Centenas de comentários por canal (completo)
- Quota API: Uso eficiente (100 vs 500 comentários)

### Scripts Novos
- `fix_translation_issue.py` - Corrige traduções incorretas
- `force_complete_collection.py` - Força coleta completa manual

---

## [27/01/2025] - Sistema de Comentários Completo

### 💬 Nova Feature: Gestão de Comentários YouTube

**Desenvolvimento:** 23-27/01/2025
**Status:** ✅ 100% Funcional e Documentado

### O que foi implementado

**Backend:**
- Tabela `video_comments` com 38 campos no Supabase
- 6 novos endpoints na API para gestão completa
- Funções em database.py para todas operações
- Coleta automática via YouTube API
- Sistema de tradução automática
- Geração de sugestões de resposta via GPT (não análises)

**Frontend:**
- Componente React completo (527 linhas)
- Interface de 3 níveis: Canais → Vídeos → Comentários
- Paginação e filtros inteligentes
- Ações: copiar sugestão, marcar respondido

**Scripts de Automação:**
- Scripts de coleta e processamento
- Tradução em batch
- Análise de sentimento
- Geração de sugestões de resposta personalizadas

### Números Alcançados
- **5.761** comentários coletados total
- **3.152** em canais monetizados (foco)
- **99.9%** traduzidos para português
- **1.854** com sugestões de resposta prontas
- **0** respondidos (aguardando início)

### Correções Importantes (27/01)
- Função `get_comments_summary()` corrigida - filtra APENAS monetizados
- Arquivo renomeado: `gpt_analyzer.py` → `gpt_response_suggester.py` (clareza)
- Código morto removido: `log_gpt_analysis()` nunca era usado
- Imports atualizados em `main.py` e `collector.py`
- Documentação clarificada: sistema gera "sugestões de resposta", não "análises"
- Nova regra em CLAUDE.md: "DOCUMENTAR APÓS FINALIZAR" (regra #8)

### Documentação Criada
```
.claude/3_SISTEMA_COMENTARIOS/
├── README.md           # Visão geral do sistema
├── ENDPOINTS.md        # Documentação da API
├── BANCO_DADOS.md      # Estrutura da tabela
├── IMPLEMENTACAO.md    # Timeline de desenvolvimento
└── FRONTEND.md         # Componente React
```

### Arquivos Modificados
- `database.py` - 6 novas funções (+400 linhas)
- `main.py` - 6 novos endpoints (+200 linhas)
- `.claude/CLAUDE.md` - Atualizado com novo sistema

---

## [23/01/2026] - Otimização Crítica: Materialized Views + Cache 24h

### Performance Revolucionária Alcançada

| Métrica | Antes | Depois | Melhoria |
|---------|-------|--------|----------|
| **Dashboard (SQL)** | 3000ms | 0.109ms | **27,522x mais rápido!** |
| **Primeira MV** | 95s | 100ms | **950x mais rápido** |
| **Com cache** | N/A | < 1ms | **Instantâneo** |
| **Queries/dia** | 100+ | 1 | **99% menos** |
| **CPU Railway** | Alto | Mínimo | **~90% redução** |

### Implementação Completa

**1. Duas Materialized Views criadas no Supabase:**
- `mv_canal_video_stats` - Pré-calcula total_videos e total_views
- `mv_dashboard_completo` - Consolida TODOS dados do dashboard em uma tabela

**2. Sistema de Cache 24 horas:**
- Cache global no servidor (compartilhado entre todos usuários)
- Primeiro acesso do dia: busca da MV (~100ms) e cria cache
- Próximos acessos: servido instantâneo do cache (< 1ms)
- Cache limpo automaticamente após coleta diária (5h AM)

**3. Integração com coleta:**
- Função `refresh_all_dashboard_mvs()` executada após cada coleta
- MVs atualizadas automaticamente
- Fallback seguro se MV não existir

### Arquivos Criados (e depois deletados após execução)

| Arquivo | Descrição | Status |
|---------|-----------|---------|
| create_materialized_view.sql | SQL primeira MV | ✅ Executado e deletado |
| create_dashboard_mv.sql | SQL segunda MV | ✅ Executado e deletado |
| INSTRUCOES_SUPABASE.md | Setup primeira MV | ✅ Usado e deletado |
| INSTRUCOES_DASHBOARD_MV.md | Setup segunda MV + cache | ✅ Usado e deletado |
| analise_erros.txt | Análise 60 canais | ✅ Processado e deletado |
| 60_canais_adicionados_23jan2026.txt | Lista canais | ✅ Usado e deletado |

### Mudanças no Código

**database.py:**
- `get_dashboard_from_mv()` - Busca dados da MV ao invés de paginar
- `refresh_all_dashboard_mvs()` - Atualiza ambas MVs
- `import time` adicionado (linha 3)

**main.py:**
- Sistema completo de cache implementado (linhas 50-170)
- Cache key com hash MD5 para diferentes filtros
- `/api/canais` modificado para usar MV + cache
- `/api/canais-tabela` modificado para usar MV + cache
- Integração com coleta diária para refresh automático

### Commits

- `c37b6fe` - Dashboard Instantâneo: Cache 24h + Materialized View
- `525d0a2` - Otimização CRÍTICA: Dashboard 3s → < 100ms com Materialized View
- `fe94ce5` - Refresh automático da MV após coleta diária
- `2953e73` - Fix bug: endpoint /top-videos retornando menos de 5 vídeos
- `b3f3012` - Fix timezone error no endpoint engagement

### Resultado Final

✅ **Dashboard agora abre INSTANTANEAMENTE**
✅ **Zero perda de dados** - todos 364 canais preservados
✅ **Cache compartilhado global** - todos usuários beneficiados
✅ **Refresh automático** após coleta diária
✅ **Sem mudanças no frontend** - API mantém mesma estrutura

---

## [22/01/2026] - sync.py v4.3 + Bug Fixes Críticos

### sync.py v4.3 - Sync Automático Completo

- **v4.3:** Mostra última mudança recebida após pull (mensagem + data)
- **v4.2:** Removida pergunta interativa - sync agora é 100% automático
- **v4.1:** Alterado `git add .` para `git add -A`
- **v4.1:** Corrigidos caracteres Unicode para ASCII (compatibilidade Windows)
- **v4.0:** Adicionado passo [0/7] verificação de documentação

**Arquivo:** `sync.py`

| Feature | Descrição |
|---------|-----------|
| Passo [0/7] | Verifica se documentação foi atualizada ANTES de commitar |
| Mapeamento | Código → Documentação (main.py → 08_API_ENDPOINTS, etc.) |
| Alerta visual | Mostra quais docs estão faltando |
| Confirmação | Pergunta se quer continuar sem docs atualizados |

**Docs obrigatórios em qualquer mudança:**
- `.claude/CLAUDE.md` - Resumo geral para Claude
- `CHANGELOG.md` - Histórico de mudanças

**Mapeamento código → docs:**
| Código | Documentação |
|--------|-------------|
| main.py | 08_API_ENDPOINTS_COMPLETA.md |
| collector.py | 06_YOUTUBE_COLLECTOR.md |
| notifier.py | 07_NOTIFICACOES_INTELIGENTES.md |
| database.py | 05_DATABASE_SCHEMA.md |
| financeiro.py | 10_SISTEMA_FINANCEIRO.md |
| monetization_*.py | 09_MONETIZACAO_SISTEMA.md |
| yt_uploader/ | 11_YOUTUBE_UPLOADER.md |

**Commit:** `d4873eb`

---

## [22/01/2026] - Bug Fixes Críticos em database.py

### Bugs Corrigidos

| Bug | Arquivo | Linha | Descrição |
|-----|---------|-------|-----------|
| Colisão de variável `offset` | database.py | 342, 348, 359 | Variável do loop sobrescrevia parâmetro da função, causando API retornar `[]` |
| Cálculo `inscritos_diff` | database.py | 427-429 | Assumia que `datas_disponiveis[1]` era ontem, mas podia ser de dias atrás |
| Paginação histórico | database.py | - | Query não buscava todos os registros |

### Novos Campos na API `/api/canais`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `views_growth_7d` | float/null | Crescimento % de views (7 dias) |
| `views_growth_30d` | float/null | Crescimento % de views (30 dias) |
| `views_diff_7d` | int/null | Diferença absoluta de views (7 dias) |
| `views_diff_30d` | int/null | Diferença absoluta de views (30 dias) |

### Commits

- `8bd8777` - Fix critical bugs in get_canais_with_filters function
- `79de42f` - Fix pagination bug in history query
- `809e596` - Fix bug in views_growth and views_diff calculations

### Status Pós-Fix

- 300 canais ativos retornando dados (antes: 0)
- 228 canais com `views_growth_7d`
- 287 canais com `inscritos_diff`

### Documentação Atualizada

- `.claude/CLAUDE.md` - Adicionada seção de atualizações 22/01/2026
- `2_DASHBOARD_TECNICO/08_API_ENDPOINTS_COMPLETA.md` - Documentados novos campos e changelog

---

## [14/01/2025] - Reorganizacao Completa

### Estrutura Criada

```
/docs/
├── README.md                    ← Indice geral
├── CHANGELOG.md                 ← Este arquivo
├── .claude/CLAUDE.md            ← Contexto para Claude Code
│
├── DNA/                         ← Documentos fundacionais
│   ├── DNA-CELLIBS.html        ← Papel do Cellibs (65KB)
│   └── DNA-MICHA-V2.html       ← Papel do Micha (79KB)
│
├── 1_CONTEXTO_NEGOCIO/          ← Estrategia e visao
├── 2_DASHBOARD_TECNICO/         ← Documentacao tecnica
│   └── SUPABASE_COMPLETO.md    ← Merge dos docs Supabase
├── 3_OPERACIONAL/               ← Processos e procedimentos
│
├── database/                    ← Infraestrutura DB
│   ├── migrations/             ← Scripts SQL
│   └── snapshots/              ← Backups JSON
│
├── utils/                       ← Scripts utilitarios Python
│   ├── verificacao/            ← 7 scripts de validacao
│   ├── setup/                  ← 3 scripts de configuracao
│   └── one-time/               ← 6 scripts de uso unico
│
├── scripts/                     ← Scripts JS e PowerShell
├── frontend-code/               ← Componentes React
├── referencia/                  ← Documentacao de referencia
│   ├── documentacao-completa/  ← 16 docs detalhados
│   ├── htmls/                  ← HTMLs grandes
│   └── fluxos/                 ← Diagramas de fluxo
│
└── archive/                     ← Historico/backup
    ├── changelog/
    ├── mini-steps/
    ├── org-max/
    └── docs-backup/
```

### Arquivos Criados

| Arquivo | Tamanho | Descricao |
|---------|---------|-----------|
| DNA/DNA-CELLIBS.html | 65KB | Documento fundacional - papel do Cellibs |
| 2_DASHBOARD_TECNICO/SUPABASE_COMPLETO.md | ~15KB | Consolidacao dos docs Supabase |
| CHANGELOG.md | - | Este arquivo |

### Arquivos Movidos

**Para utils/verificacao/** (7 arquivos)
- verify_historico.py
- verify_historico2.py
- verify_oauth_setup.py
- verify_canals_exist.py
- verify_all_12_canals.py
- validate_data.py
- validate_before_migration.py

**Para utils/setup/** (3 arquivos)
- setup_simples.py
- setup_financeiro.py
- setup_novo_proxy.py

**Para utils/one-time/** (6 arquivos)
- update_17_urls.py
- search_missing_canals.py
- populate_spreadsheet_ids.py
- snapshot_initial_views.py
- obter_playlists_canal.py
- monitor_coleta.py

**Para scripts/** (5 arquivos)
- google-apps-script-*.js (4 arquivos)
- INICIAR_DASHBOARD.ps1

**Para database/**
- migrations/ (pasta inteira)
- supabase_snapshot.json → database/snapshots/

**Para referencia/**
- documentacao-completa/ (16 arquivos)
- CODIGO_DETALHADO/FLOW_COMPLETO_SISTEMA.md → referencia/fluxos/
- HTMLs grandes de docs/ → referencia/htmls/

**Para archive/**
- changelog/ (historico antigo)
- mini-steps/ (apenas STEP_01 tem conteudo)
- org-max/ (imagens WhatsApp)
- docs/ duplicada → archive/docs-backup/

### Atualizacoes Supabase (mesmo dia)

14 canais atualizados na tabela `canais_monitorados`:

| ID | Mudanca |
|----|---------|
| 878 | Nome: Konige des Kapitals, Subnicho: Empreendedorismo |
| 871-877 | Subnicho: Guerras e Civilizacoes (7 canais) |
| 879-880 | Subnicho: Relatos de Guerra (2 canais) |
| 835 | Subnicho: Historias Sombrias |
| 836 | Subnicho: Historias Sombrias |
| 865 | Subnicho: Misterios |
| 866 | Subnicho: Misterios |

### Regras Estabelecidas

1. **Codigo Python fica na raiz** - Nao mover para nao quebrar imports
2. **Novos documentos** - Encaminhar direto para pasta correta
3. **Sync = Backup** - Sempre atualizar CHANGELOG antes do sync
4. **DNAs** - Documentos fundacionais ficam em DNA/

---

## Metricas Atuais (Janeiro 2025)

| Metrica | Valor |
|---------|-------|
| Canais Monitorados | 344 |
| Canais Nossos | 51 |
| Canais Minerados | 293 |
| Canais Monetizados | 16 |
| Videos Coletados | ~400.000 |
| Subnichos Ativos | 10 |
| Idiomas | 11 |

---

## Proximas Atualizacoes

Documentar aqui cada alteracao futura com:
- Data
- O que foi feito
- Arquivos criados/movidos/deletados
- Atualizacoes de banco de dados

---

**Autor:** Claude Code
**Proposito:** Manter historico para continuidade entre sessoes

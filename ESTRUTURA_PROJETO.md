# Estrutura do Projeto - YouTube Dashboard Backend

## 📁 Organização de Diretórios

```
youtube-dashboard-backend/
│
├── 📂 .claude/                      # Documentação para Claude Code
│   ├── CLAUDE.md                    # Instruções principais
│   ├── 2_DASHBOARD_TECNICO/         # Docs técnicas do dashboard
│   ├── 3_SISTEMA_COMENTARIOS/       # Docs do sistema de comentários
│   └── kanban-system/               # Docs do sistema Kanban
│
├── 📂 frontend/                     # Componentes frontend
│   └── tsx/                         # Arquivos TypeScript/React
│       ├── TabelaCanais.tsx        # Componente da tabela de canais
│       └── README.md
│
├── 📂 scripts/                      # Scripts auxiliares organizados
│   ├── 📂 maintenance/              # Scripts de manutenção e diagnóstico
│   │   ├── remove_banned_channels.py    # Remove canais banidos
│   │   ├── sync.py                      # Sincroniza com GitHub/Railway
│   │   ├── check_dashboard_health.py    # Diagnóstico do dashboard
│   │   ├── diagnostico_mv_completo.py   # Diagnóstico da Materialized View
│   │   ├── test_coleta.py               # Diagnóstico do sistema de coleta
│   │   ├── verificar_remocao.py         # Verifica operações de remoção
│   │   └── README.md
│   │
│   ├── 📂 database/                 # Scripts SQL
│   │   ├── [arquivos .sql]
│   │   └── README.md
│   │
│   ├── 📂 examples/                 # Código de exemplo/referência
│   │   ├── refresh_mv_endpoint.py       # Exemplo de endpoint para MV
│   │   └── README.md
│   │
│   ├── 📂 manual/                   # Scripts para execução manual
│   │   ├── force_complete_collection.py # Força coleta completa
│   │   ├── run_collection_now.py        # Coleta manual simplificada
│   │   ├── force_mv_refresh.py          # Refresh manual da MV
│   │   └── README.md
│   │
│   ├── 📂 operations/               # Operações pontuais
│   │   ├── remove_canais_problematicos.py  # Remove canais específicos
│   │   ├── desativar_canais_problematicos.py # Desativa canais
│   │   └── README.md
│   │
│   └── 📂 tests/                    # Scripts de teste
│       ├── test_endpoints.py            # Testa endpoints da API
│       ├── test_inscritos_diff.py       # Testa inscritos_diff
│       ├── test_canais_nossos.py        # Testa aba Tabela
│       └── README.md
│
├── 📂 legacy/                       # Código legado/descontinuado
│   ├── report_generator.py         # Sistema de relatórios (órfão)
│   └── README.md
│
├── 📂 kanban-system/                # Sistema Kanban completo
│   ├── main.py                      # Servidor principal do Kanban
│   ├── database.py                  # Conexão Supabase
│   └── docs/                        # Documentação API
│
├── 📂 yt_uploader/                  # Sistema de upload YouTube
│   ├── sheets.py                    # Integração Google Sheets (ativo)
│   └── ...
│
└── 📂 [ROOT]                        # Arquivos principais (NÃO MOVER!)
    ├── main.py                      # FastAPI app principal
    ├── database.py                  # Cliente Supabase
    ├── collector.py                 # Coletor YouTube
    ├── notifier.py                  # Sistema de notificações
    ├── financeiro.py                # Serviço financeiro
    ├── analytics.py                 # Analytics de canais
    ├── agents_endpoints.py          # Router de agents
    ├── monetization_endpoints.py    # Router de monetização
    ├── comments_logs.py             # Gerenciador de comentários
    ├── gpt_response_suggester.py    # Sugestor de respostas GPT
    ├── requirements.txt             # Dependências Python
    ├── .env                         # Variáveis de ambiente
    └── .gitignore                   # Arquivos ignorados
```

## ⚠️ REGRAS CRÍTICAS - NUNCA VIOLAR

### 🔴 ARQUIVOS QUE NUNCA DEVEM SER MOVIDOS DO ROOT:
1. **main.py** - App principal FastAPI
2. **database.py** - Cliente Supabase usado por todos
3. **collector.py** - Coletor YouTube
4. **notifier.py** - Sistema de notificações
5. **financeiro.py** - Importado diretamente no main.py
6. **analytics.py** - Analytics de canais
7. **agents_endpoints.py** - Router FastAPI
8. **monetization_endpoints.py** - Router FastAPI
9. **comments_logs.py** - Gerenciador de logs
10. **gpt_response_suggester.py** - Tem imports dinâmicos

### 📂 ONDE SALVAR NOVOS ARQUIVOS:

#### 1. **Scripts de Teste/Temporários**
   - **Local:** `/scripts/tests/`
   - **Exemplos:** test_*.py, verificar_*.py, testar_*.py
   - **Nota:** Limpar periodicamente

#### 2. **Scripts de Manutenção**
   - **Local:** `/scripts/maintenance/`
   - **Exemplos:** fix_*.py, update_*.py, cleanup_*.py
   - **Nota:** Manter apenas scripts ativos

#### 3. **Scripts SQL**
   - **Local:** `/scripts/database/`
   - **Exemplos:** *.sql
   - **Nota:** Organizar por funcionalidade

#### 4. **Componentes Frontend**
   - **Local:** `/frontend/tsx/`
   - **Exemplos:** *.tsx, *.jsx
   - **Nota:** Componentes React/TypeScript

#### 5. **Código Descontinuado**
   - **Local:** `/legacy/`
   - **Exemplos:** Sistemas órfãos, código antigo
   - **Nota:** Mantido apenas para referência

#### 6. **Sistema Kanban**
   - **Local:** `/kanban-system/`
   - **Nota:** Sistema completo isolado

#### 7. **Novos Endpoints/Routers**
   - **Local:** ROOT (se for router FastAPI)
   - **Padrão:** *_endpoints.py
   - **Motivo:** main.py espera routers no root

## 🔄 HISTÓRICO DE REORGANIZAÇÃO (29/01/2026)

### Arquivos Deletados (11):
- test_move_endpoint.py
- teste_movimentacao.py
- verificar_kanban.py
- test_kanban.py
- fix_translation_issue.py
- add_translation_field.sql
- fix_mv_100_CORRETO.sql
- update_kanban_history_constraint.sql
- fix_comments_table.sql
- create_engagement_cache_table.sql
- add_coluna_id_kanban.sql

### Arquivos Movidos:
- **report_generator.py** → `/legacy/` (órfão, dependia de analyzer.py deletado)
- **remove_banned_channels.py** → `/scripts/maintenance/`
- **sync.py** → `/scripts/maintenance/`
- **TabelaCanais.tsx** → `/frontend/tsx/`

### Arquivos Mantidos no Root (críticos):
- Todos os módulos principais importados por main.py
- Routers FastAPI (*_endpoints.py)
- Arquivos de configuração (.env, requirements.txt, etc)

## 📝 NOTAS IMPORTANTES

1. **Imports Dinâmicos:** gpt_response_suggester.py usa imports dinâmicos, mover pode quebrar
2. **Routers FastAPI:** Devem ficar no root para main.py encontrar
3. **Kanban System:** É um sistema isolado em `/kanban-system/`
4. **Legacy:** Código em `/legacy/` não é usado, mantido apenas para referência
5. **Git Recovery:** Todos arquivos deletados podem ser recuperados via git se necessário

## 🚀 PARA NOVOS DESENVOLVIMENTOS

### Antes de criar um arquivo, pergunte-se:

1. **É um teste temporário?** → `/scripts/tests/`
2. **É manutenção/fix?** → `/scripts/maintenance/`
3. **É SQL?** → `/scripts/database/`
4. **É componente frontend?** → `/frontend/tsx/`
5. **É router FastAPI?** → ROOT (obrigatório)
6. **É módulo core?** → ROOT (se importado por main.py)
7. **É código antigo?** → `/legacy/`

### Workflow de Limpeza:
```bash
# Periodicamente executar
1. Revisar /scripts/tests/ - deletar testes antigos
2. Revisar /scripts/maintenance/ - arquivar scripts não usados
3. Verificar /legacy/ - considerar deletar código muito antigo
4. Atualizar esta documentação com mudanças
```

## 📋 CHECKLIST DE SEGURANÇA

Antes de mover QUALQUER arquivo:

- [ ] Verificar se é importado em main.py
- [ ] Verificar se é router FastAPI
- [ ] Buscar imports com: `grep -r "from arquivo import" .`
- [ ] Buscar imports com: `grep -r "import arquivo" .`
- [ ] Testar localmente após mover
- [ ] Atualizar esta documentação

---

**Última atualização:** 29/01/2026
**Responsável:** Claude Code + Cellibs
**Status:** Sistema 100% funcional e organizado
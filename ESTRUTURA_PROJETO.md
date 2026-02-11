# ESTRUTURA DO PROJETO - YouTube Dashboard Backend

**Última atualização:** 03/02/2026 (Reorganização v2)

## 📂 ESTRUTURA PRINCIPAL

```
youtube-dashboard-backend/
│
├── 📌 ARQUIVOS PYTHON NO ROOT (23 arquivos essenciais)
│   ├── main.py                        # FastAPI server principal
│   ├── database.py                    # Cliente Supabase
│   ├── collector.py                   # Coletor YouTube
│   ├── notifier.py                    # Sistema de notificações
│   ├── financeiro.py                  # Endpoints financeiros
│   ├── analytics.py                   # Analytics de canais
│   ├── comments_logs.py               # Logs de comentários
│   ├── agents_endpoints.py            # Endpoints dos agentes IA
│   ├── monetization_endpoints.py      # Endpoints de monetização
│   ├── monetization_collector.py      # Coletor de monetização
│   ├── monetization_oauth_collector.py # OAuth para monetização
│   ├── gpt_response_suggester.py      # Sugestões de respostas GPT
│   ├── engagement_preprocessor.py     # Preprocessador de engajamento
│   ├── daily_uploader.py              # Sistema de upload diário
│   ├── dash_upload_final.py           # 🆕 Dashboard Flask de uploads (porta 5006)
│   ├── dashboard_daily_uploads.py     # Dashboard Flask para uploads (legado)
│   ├── sheets.py                      # Integração Google Sheets
│   ├── setup.py                       # Setup inicial
│   ├── add_canal_wizard_v2.py        # Wizard para adicionar canais (v2)
│   ├── add_canal_wizard_v3.py        # Wizard para adicionar canais (v3)
│   ├── refresh_oauth_tokens.py        # Refresh de tokens OAuth
│   ├── reauth_channel_oauth.py        # Reautenticação OAuth
│   └── integrate_daily_upload.py      # Integração upload diário
│
├── 📁 _features/                      # Funcionalidades isoladas
│   ├── agents/                        # Sistema de agentes inteligentes
│   │   ├── orchestrator.py           # Orquestrador principal
│   │   ├── scheduler.py              # Agendador de tarefas
│   │   └── [outros agentes]          # Agentes específicos
│   ├── yt_uploader/                  # Sistema de upload YouTube
│   │   ├── uploader.py               # Upload principal
│   │   ├── database.py               # DB do uploader
│   │   ├── sheets.py                 # Integração com Sheets
│   │   └── oauth_manager.py          # Gestão OAuth
│   ├── frontend-code/                # Componentes React/TypeScript
│   │   └── TabelaCanais.tsx          # Componente da tabela de canais
│   ├── kanban-system/                # Sistema Kanban completo
│   ├── monetization_dashboard/       # Dashboard de monetização
│   ├── trend-monitor/                # Monitor de tendências
│   ├── discovery/                    # Sistema de descoberta
│   ├── DNA/                          # DNA dos canais
│   └── frontend/                     # Frontend adicional
│
├── 📁 _development/                   # Ferramentas de desenvolvimento
│   ├── scripts/                      # Scripts organizados
│   │   ├── maintenance/              # Manutenção do sistema
│   │   ├── database/                 # Scripts SQL
│   │   ├── tests/                    # Scripts de teste
│   │   ├── comentarios/              # Scripts de comentários
│   │   ├── upload/                   # Scripts de upload
│   │   ├── manual/                   # Scripts manuais
│   │   └── utils/                    # Utilitários gerais
│   ├── utilities/                    # Ferramentas utilitárias
│   │   ├── validar_sistema.py        # Validação do sistema
│   │   ├── monitor_sistema.py        # Monitor do sistema
│   │   ├── sync.py                   # Sincronização
│   │   └── [outros utilitários]      # Outras ferramentas
│   ├── guides/                       # Guias e instruções
│   │   ├── INSTRUCOES_*.md          # Instruções diversas
│   │   ├── CHECKLIST_FINAL.md       # Checklist de deploy
│   │   └── COMANDOS_RAPIDOS.md      # Comandos úteis
│   ├── prompts/                      # Templates de prompts IA
│   ├── templates/                    # Templates diversos
│   ├── debug/                        # Scripts de debug
│   └── .autocoder/                   # Configurações autocoder
│
├── 📁 _database/                      # Arquivos de banco de dados
│   ├── database/                     # Scripts de banco
│   └── databasemigrations/           # Migrations do banco
│
├── 📁 _runtime/                       # Arquivos gerados em runtime
│   ├── logs/                         # Logs do sistema
│   ├── reports/                      # Relatórios gerados
│   ├── __pycache__/                  # Cache Python
│   ├── canal_status.json             # Status dos canais
│   ├── kanban_structure.json         # Estrutura Kanban
│   ├── assistant.db                  # DB do assistente
│   └── features.db*                  # DBs de features
│
├── 📁 _archives/                      # Backups e código antigo
│   ├── referencia/                   # Documentação de referência
│   │   ├── 1_CONTEXTO_NEGOCIO/       # Contexto do negócio
│   │   ├── 2_DASHBOARD_TECNICO/      # Documentação técnica
│   │   ├── 3_OPERACIONAL/            # Guias operacionais
│   │   └── documentacao-completa/    # Docs completos 00-14
│   ├── legacy/                       # Código descontinuado
│   ├── legacy-docs/                  # Documentação antiga
│   ├── correcoes/                    # Correções realizadas
│   ├── backups/                      # Backups gerais
│   ├── backup_20012025_fixes/        # Backup de correções Jan/25
│   ├── backup_limpeza_03022026/      # Backup limpeza 03/02
│   └── backup_final_cleanup_03022026/ # Backup final 03/02
│
├── 📁 Configuração e Docs ROOT
│   ├── .claude/                      # Configuração Claude Code
│   │   └── CLAUDE.md                 # Instruções para Claude
│   ├── README.md                     # README principal
│   ├── CHANGELOG.md                  # Histórico de mudanças
│   ├── ESTRUTURA_PROJETO.md          # Este arquivo
│   ├── requirements.txt              # Dependências Python
│   ├── runtime.txt                   # Versão Python (Railway)
│   ├── Procfile                      # Config deploy (Railway)
│   ├── .env                          # Variáveis de ambiente (local)
│   ├── .gitignore                    # Ignorar no git
│   └── .git/                         # Versionamento git
│
└── 📁 Sistema (não mexer)
    └── __pycache__/                   # Cache Python (ROOT)
```

## 🎯 ONDE SALVAR NOVOS ARQUIVOS

### ✅ SEMPRE NO ROOT:
- **Endpoints novos:** `*_endpoints.py`
- **Serviços core:** Arquivos que main.py importa diretamente
- **Wizards:** Scripts interativos de configuração

### ✅ EM _features/:
- **Nova funcionalidade isolada:** Criar pasta própria
- **Frontend components:** Em `frontend-code/`
- **Sistema com múltiplos arquivos:** Pasta dedicada

### ✅ EM _development/:
- **Scripts de manutenção:** `scripts/maintenance/`
- **Scripts SQL:** `scripts/database/`
- **Testes:** `scripts/tests/`
- **Utilitários:** `utilities/`
- **Documentação técnica:** `guides/`

### ✅ EM _archives/:
- **Código antigo/deprecated:** `legacy/`
- **Backups antes de mudanças grandes:** `backups/`
- **Documentação histórica:** `legacy-docs/`

### ⚠️ NUNCA MOVER DO ROOT:
```python
# Estes arquivos DEVEM ficar no ROOT:
CORE_FILES = [
    'main.py',
    'database.py',
    'collector.py',
    'notifier.py',
    'financeiro.py',
    'analytics.py',
    'comments_logs.py',
    'agents_endpoints.py',
    'monetization_endpoints.py',
    'gpt_response_suggester.py',
    'engagement_preprocessor.py',
    'daily_uploader.py',
    'sheets.py'
]
```

## 📊 ESTATÍSTICAS DA ESTRUTURA

- **Total de arquivos Python no ROOT:** 22 (apenas essenciais)
- **Pastas organizadoras:** 5 (_features, _development, _database, _runtime, _archives)
- **Redução de complexidade:** De 32+ pastas → 6 pastas principais
- **Imports atualizados:** Apenas 2 arquivos precisaram de ajustes

## 🔄 HISTÓRICO DE REORGANIZAÇÕES

### v2.0 - 03/02/2026 (ATUAL)
- Criação de 5 pastas organizadoras com prefixo "_"
- Movimentação de 32+ pastas para estrutura hierárquica
- Limpeza de 15+ arquivos temporários de verificação/tradução
- Documentação totalmente atualizada
- Sistema 100% funcional verificado

### v1.0 - 29/01/2026
- Primeira organização básica
- Criação de pastas scripts/, utilities/
- Limpeza inicial de arquivos temporários

### v0.1 - Janeiro/2026
- Estrutura inicial sem organização
- 32+ pastas no ROOT
- Mistura de código, docs e backups

## 🚀 NOVO DESENVOLVIMENTO

Ao criar novos arquivos, pergunte-se:

1. **É um endpoint ou serviço core?** → ROOT
2. **É uma feature isolada?** → _features/nova_pasta/
3. **É um script de manutenção?** → _development/scripts/
4. **É documentação?** → _development/guides/ ou ROOT (se principal)
5. **É código antigo?** → _archives/legacy/
6. **É gerado automaticamente?** → _runtime/

## 📝 NOTAS IMPORTANTES

- **Prefixo "_":** Usado para pastas organizadoras aparecerem no topo
- **ROOT limpo:** Apenas arquivos Python essenciais e configs
- **Imports:** Usar paths completos (_features.module.file)
- **Backups:** Sempre criar antes de mudanças grandes
- **Railway:** Deploy funciona sem alterações

## 🔗 DOCUMENTAÇÃO RELACIONADA

- `.claude/CLAUDE.md` - Instruções gerais do projeto
- `README.md` - Visão geral do sistema
- `CHANGELOG.md` - Histórico detalhado de mudanças
- `_development/guides/` - Guias técnicos específicos

---

**Mantido por:** Cellibs (Marcelo)
**Última revisão:** 03/02/2026
**Status:** ✅ Estrutura organizada e funcional
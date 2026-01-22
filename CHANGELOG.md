# CHANGELOG - CEREBRO CELLIBS

> Este arquivo documenta todas as alteracoes na pasta /docs.
> Atualizar sempre que fizer sync.

---

## [22/01/2026] - sync.py v4.2 + Bug Fixes Críticos

### sync.py v4.2 - Verificação de Documentação (Automático)

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

# Backend Dashboard de Mineração YouTube

Python (FastAPI) | Supabase (PostgreSQL) | Railway deploy

## Workflow Orchestration

### 1. Plan Mode Default
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately — don't keep pushing
- Use plan mode for verification steps, not just building
- Write detailed specs upfront to reduce ambiguity

### 2. Subagent Strategy
- Use subagents liberally to keep main context window clean
- Offload research, exploration, and parallel analysis to subagents
- For complex problems, throw more compute at it via subagents
- One task per subagent for focused execution

### 3. Self-Improvement Loop
- After ANY correction from the user: update memory files with the lesson
- Write rules for yourself that prevent the same mistake
- Ruthlessly iterate on these lessons until mistake rate drops
- Review lessons at session start for relevant project

### 4. Verification Before Done
- NEVER mark a task complete without proving it works
- Diff behavior between main and your changes when relevant
- Ask yourself: "Would a staff engineer approve this?"
- Run tests, check logs, demonstrate correctness

### 5. Demand Elegance (Balanced)
- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution"
- Skip this for simple, obvious fixes — don't over-engineer
- Challenge your own work before presenting it

### 6. Autonomous Bug Fixing
- When given a bug report, just fix it. Don't ask for hand-holding
- Point at logs, errors, failing tests — then resolve them
- Zero context switching required from the user
- Go fix failing CI tests without being told how

## Task Management

1. **Plan First**: Write plan to task list with checkable items
2. **Verify Plans**: Check in before starting implementation
3. **Track Progress**: Mark items complete as you go
4. **Explain Changes**: High-level summary at each step
5. **Document Results**: Add review section when done
6. **Capture Lessons**: Update memory files after corrections

## Core Principles

- **Simplicity First**: Make every change as simple as possible. Impact minimal code
- **No Laziness**: Find root causes. No temporary fixes. Senior developer standards
- **Minimal Impact**: Changes should only touch what's necessary. Avoid introducing bugs
- **Honesty**: NEVER claim "funcional" without testing. NEVER invent data. DATA > ASSUMPTIONS
- **No PowerShell HTML**: NEVER edit HTML/CSS via PowerShell (UTF-8 encoding breaks!)

## Project Structure

```
youtube-dashboard-backend/
├── _archives/         # Backups, código antigo, changelog
├── _database/         # Migrations SQL
├── _development/      # Scripts dev, utilities, guides
├── _features/         # Funcionalidades isoladas
│   ├── agents/        # Sistema de agentes IA
│   ├── yt_uploader/   # Upload YouTube (oauth_manager, sheets, uploader)
│   ├── frontend-code/ # Componentes React/TypeScript
│   └── kanban-system/ # Sistema Kanban
├── _runtime/          # Logs, reports, dados runtime
└── [core .py files]   # NUNCA mover do ROOT
```

**Arquivos ROOT (nunca mover):** main.py, database.py, collector.py, notifier.py, daily_uploader.py, copy_analysis_agent.py, authenticity_agent.py, ctr_collector.py, mission_control.py, financeiro.py, analytics.py, comments_logs.py, agents_endpoints.py, monetization_endpoints.py, gpt_response_suggester.py

## Credentials (.env)

- `SUPABASE_URL` / `SUPABASE_KEY` (anon, RLS ativo)
- `SUPABASE_SERVICE_ROLE_KEY` (bypass RLS — SEMPRE usar para tokens OAuth!)
- `YOUTUBE_API_KEY_X` — NÃO configuradas localmente (só Railway)
- 13 API keys ativas: KEY_7-10, KEY_21-29

## Critical Gotchas

- **OAuth tokens:** SEMPRE usar SERVICE_ROLE_KEY (anon key NÃO mostra tokens por RLS)
- **spreadsheet_id** = planilha de UPLOAD | **copy_spreadsheet_id** = planilha de COPY → NUNCA misturar
- **API quota:** playlistItems.list (1 unit) — NUNCA usar search.list (100 units)
- **Railway HTML:** NUNCA usar emoji flags (surrogate pairs quebram encoding) → usar badges texto (PT, EN, ES)
- **Supabase UPSERT:** `Prefer: resolution=merge-duplicates` NÃO funciona em todas tabelas → usar INSERT + fallback PATCH on 409
- **Imports:** main.py usa `_features.yt_uploader`, agents_endpoints usa `_features.agents`

## Key Endpoints

**Canais:** GET /api/canais, GET /api/canais-tabela, POST /api/canais
**Vídeos:** GET /api/videos
**Notificações:** GET /api/notificacoes, POST /api/force-notifier
**Comentários:** GET /api/comentarios/resumo, POST /api/collect-comments/{id}
**Análise:** POST /api/analise-completa/{id}, GET /api/analise-copy/{id}/latest, GET /api/analise-autenticidade/{id}/latest
**CTR:** POST /api/ctr/setup-jobs, POST /api/ctr/collect, GET /api/ctr/{id}/latest
**Upload:** GET /dash-upload, POST /api/dash-upload/force-upload/{id}
**Dashboard Copy:** GET /dash-analise-copy
**Mission Control:** GET /mission-control
**Cache:** POST /api/cache/clear (limpa cache + refresh MVs)

## Run Locally

```bash
pip install -r requirements.txt
python main.py  # porta 8000
```

## Changelog

Histórico completo de atualizações em: `_archives/CHANGELOG_CLAUDE_MD.md`

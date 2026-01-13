# YouTube Dashboard Backend - Content Factory

Backend API para o Dashboard de Mineração YouTube da Content Factory.

**Stack:** FastAPI + Supabase + Railway + Python 3.10+

**Documentação criada por:** Cellibs (Marcelo) via Claude Code
**Data:** Janeiro 2025
**Versão:** 1.0

---

## 🚀 Quick Start

```bash
# Instalar dependências
pip install -r requirements.txt --break-system-packages

# Configurar .env (ver docs/13_DEPLOY_RAILWAY.md para variáveis)
cp .env.example .env

# Rodar servidor local
python main.py
```

**API Local:** http://localhost:8000
**API Docs:** http://localhost:8000/docs

---

## 🎯 Para Que Serve Este Sistema

O Dashboard de Mineração é o **cérebro de inteligência de mercado** da Content Factory:

✅ **Minera** centenas de canais YouTube (concorrentes e referências)
✅ **Identifica** oportunidades (vídeos 10k+ views em 24h)
✅ **Notifica** Arthur/Micha em tempo real
✅ **Monitora** nossos 50 canais (desempenho, inscritos, receita)
✅ **Coleta** receita de 16 canais monetizados (YouTube Analytics)
✅ **Automatiza** upload de 100-130 vídeos/dia
✅ **Integra** produção → publicação → análise

**Sem o dashboard, operaríamos no escuro.**

---

## 🏗️ Arquitetura

```
📺 YouTube APIs
    ↓
[Collector] ← 20 API Keys (200k req/dia)
    ↓
[Supabase] PostgreSQL (27 tables)
    ↓
[FastAPI Backend] (Railway) ← Este repositório
    ↓
[Lovable Frontend] (Dashboard visual)
    ↑
Arthur/Cellibs/Micha (usuários)
```

**Ver:** `docs/04_ARQUITETURA_SISTEMA.md`

---

## 🗂️ Organização de Arquivos

O repositório está organizado de forma limpa e profissional:

### **Pastas Principais:**
```
youtube-dashboard-backend/
├── docs/                   ← Documentação completa (600+ KB, 15.5k linhas)
├── yt_uploader/            ← Sistema de upload automático
├── monetization_dashboard/ ← Dashboard de monetização
├── migrations/             ← Migrações de database
│
├── scripts-temp/           ← Scripts de teste (NÃO vão pro Git)
├── backups/                ← Backups OAuth (NÃO vão pro Git)
├── debug/                  ← Arquivos debug (NÃO vão pro Git)
│
└── (arquivos principais na raiz)
```

### **Arquivos Principais (Raiz):**
- `main.py` - FastAPI app + endpoints (1122 linhas)
- `collector.py` - Coletor YouTube (792 linhas)
- `database.py` - Conexão Supabase
- `notifier.py` - Sistema de notificações (449 linhas)
- `monetization_collector.py` - Coleta de receita (311 linhas)
- `monetization_endpoints.py` - Endpoints OAuth (2233 linhas)
- `financeiro.py` - Sistema financeiro
- `requirements.txt` - Dependências Python

### **O Que Vai/Não Vai para o Git:**

✅ **VAI (sincroniza entre PCs):**
- Código Python principal (main.py, collector.py, etc)
- Documentação completa (docs/)
- Configurações (.gitignore, requirements.txt)
- Pastas de código (yt_uploader/, monetization_dashboard/, migrations/)

❌ **NÃO VAI (ignorado pelo .gitignore):**
- Scripts de teste (scripts-temp/)
- Backups de OAuth (backups/)
- Arquivos de debug/investigação (debug/)
- Credenciais (.env, tokens*.json)
- Arquivos temporários (*.tmp, *.log)

**Resultado:** Repositório limpo, só com o essencial! 🎯

---

## 📚 DOCUMENTAÇÃO COMPLETA

**Toda a documentação está em [`docs/`](./docs/)**

### 🎯 Comece por aqui:

**Para visualização rápida e bonita:**
```bash
# Windows
start docs/DASHBOARD_DOCUMENTATION.html

# Mac/Linux
open docs/DASHBOARD_DOCUMENTATION.html
```

**Para leitura detalhada:**
1. **[00_INDICE_GERAL.md](./docs/documentacao-completa/00_INDICE_GERAL.md)** - Índice completo e navegação
2. **[01_CONTENT_FACTORY_VISAO_GERAL.md](./docs/documentacao-completa/01_CONTENT_FACTORY_VISAO_GERAL.md)** - Contexto de negócio
3. **[03_DASHBOARD_PROPOSTA_VALOR.md](./docs/documentacao-completa/03_DASHBOARD_PROPOSTA_VALOR.md)** - Por que este sistema existe
4. **[FRONTEND_COMPLETO.md](./docs/FRONTEND_COMPLETO.md)** - Frontend: 6 abas do dashboard (Lovable)

**Setup e Sincronização:**
- **[SETUP_NOVO_PC.md](./docs/SETUP_NOVO_PC.md)** - Configurar em novo PC (casa, trabalho, etc)
- **[CONVERT_TO_FULL_CLONE.md](./docs/CONVERT_TO_FULL_CLONE.md)** - Converter Mac de sparse para completo

---

## 📂 Estrutura da Documentação

### **Resumo (Ver árvore completa em docs/README.md):**

**PARTE 1: Contexto de Negócio (3 docs)**
- `01_CONTENT_FACTORY_VISAO_GERAL.md` - Empresa, estratégia, 50 canais, 8 subnichos
- `02_PIPELINE_PRODUCAO_OVERVIEW.md` - Como produzimos 100-130 vídeos/dia
- `03_DASHBOARD_PROPOSTA_VALOR.md` - Valor estratégico do dashboard

**PARTE 2: Dashboard Técnico (9 docs)**
- `04_ARQUITETURA_SISTEMA.md` - Stack completo (FastAPI, Supabase, Railway)
- `05_DATABASE_SCHEMA.md` - Todas as 27 tabelas (DDL, queries, indexes)
- `06_YOUTUBE_COLLECTOR.md` - Coleta automatizada (20 API keys, 200k req/dia)
- `07_NOTIFICACOES_INTELIGENTES.md` - Sistema de alertas (10k, 50k, 100k views)
- `08_API_ENDPOINTS_COMPLETA.md` - Referência completa de API
- `09_MONETIZACAO_SISTEMA.md` - Coleta de receita (OAuth, 16 canais)
- `10_SISTEMA_FINANCEIRO.md` - Gestão financeira multi-canal
- `11_YOUTUBE_UPLOADER.md` - Upload automatizado (100-130 vídeos/dia)
- `FRONTEND_COMPLETO.md` - Frontend completo (6 abas: Tabela, Nossos Canais, Minerados, Notificações, Monetização, Financeiro)

**PARTE 3: Operacional (3 docs)**
- `12_INTEGRACAO_GOOGLE_APIS.md` - Sheets, Drive, YouTube APIs
- `13_DEPLOY_RAILWAY.md` - Deploy em produção (CI/CD, env vars)
- `14_TROUBLESHOOTING.md` - Problemas comuns e soluções

**SISTEMAS COMPLEMENTARES:**
- **Mini-Steps:** 11 documentos (1 por função backend/frontend)
- **Changelog:** Histórico de mudanças
- **Fluxos Completos:** Frontend → Railway → Supabase

---

## 📖 Descrição Detalhada de Cada Documento

### **🌐 HTML Visual**

#### `DASHBOARD_DOCUMENTATION.html` (77 KB)
- **Visualização moderna e interativa**
- Design profissional dark theme
- Sidebar navegável
- Todas as 11 seções principais
- Responsivo (mobile-friendly)
- **Recomendado para apresentações**

---

### **PARTE 1: Contexto de Negócio (56 KB)**

#### `01_CONTENT_FACTORY_VISAO_GERAL.md` (17 KB)
- Quem somos (4 sócios, funções)
- 50 canais, 8 subnichos, 10+ idiomas
- Crise Jan 2025 e oportunidades
- Estratégia de diversificação radical
- Como Dashboard se encaixa no negócio

#### `02_PIPELINE_PRODUCAO_OVERVIEW.md` (21 KB)
- 17 passos automatizados de produção
- 8 agentes AI
- 5 máquinas (M1-M5)
- 100-130 vídeos/dia
- Sistema de rotação anti-detecção
- HeyGen avatars (novo formato)

#### `03_DASHBOARD_PROPOSTA_VALOR.md` (18 KB)
- **Por que o Dashboard existe**
- Casos de uso (Arthur, Cellibs workflows)
- Valor estratégico para Content Factory
- Métricas de impacto
- Decisões de design

---

### **PARTE 2: Dashboard Técnico (271 KB)**

#### `04_ARQUITETURA_SISTEMA.md` (33 KB)
- Stack completo (FastAPI + Supabase + Railway + Lovable)
- Fluxos de dados detalhados
- Componentes principais
- Integrações externas (20 API keys)
- Segurança (OAuth, RLS, CORS)
- Escalabilidade

#### `05_DATABASE_SCHEMA.md` (35 KB)
- **27 tabelas completas** (DDL, constraints, indexes)
- 6 módulos: Mineração, Notificações, Monetização, Upload, Financeiro
- Relacionamentos e foreign keys
- **20+ queries práticas** com exemplos
- Row Level Security (RLS)
- Backup/restore procedures

#### `06_YOUTUBE_COLLECTOR.md` (45 KB)
- `collector.py` (792 linhas) documentado
- **20 API keys** (rotação inteligente)
- Rate limiter (90 req/100s)
- Métodos de coleta completos
- Error handling e retry logic
- HTML decoding
- Troubleshooting coleta

#### `07_NOTIFICACOES_INTELIGENTES.md` (32 KB)
- `notifier.py` (449 linhas) documentado
- Sistema de marcos (10k, 50k, 100k views)
- **Anti-duplicação completo**
- Sistema de elevação (10k → 50k → 100k)
- Filtros por subnicho
- Workflow Arthur/Micha

#### `08_API_ENDPOINTS_COMPLETA.md` (24 KB)
- `main.py` (1122 linhas) documentado
- **Todos os endpoints REST**
- Request/Response examples (curl, Python)
- Modelos Pydantic
- Background tasks (transcription, upload)
- Testing e exemplos práticos

#### `09_MONETIZACAO_SISTEMA.md` (24 KB)
- OAuth 2.0 flow completo
- YouTube Analytics API
- Revenue collection (USD→BRL)
- Métricas: revenue, demographics, traffic sources
- **16 canais monetizados**
- Troubleshooting OAuth (Invalid Grant, etc)

#### `10_SISTEMA_FINANCEIRO.md` (27 KB)
- `financeiro.py` documentado
- Lançamentos receita/despesa
- Categorias e metas
- Conversão USD→BRL automática
- Projeções e comparações mensais

#### `11_YOUTUBE_UPLOADER.md` (24 KB)
- `yt_uploader/` folder completo
- Upload queue flow (Google Drive → YouTube)
- OAuth Manager (v2.0: credenciais isoladas)
- **Semáforo** (max 3 simultâneos)
- Google Sheets integration
- Status tracking e retry logic

#### `FRONTEND_COMPLETO.md` (16 KB, 420 linhas)
- **6 abas do dashboard** documentadas
- Componentes React (Lovable/SPA)
- Interações e fluxos de usuário
- Integrações com backend (API calls)
- Modais e ferramentas auxiliares

**Abas documentadas:**
1. **Tabela** - Nossos canais agrupados por subnicho (cards colapsáveis)
2. **Nossos Canais** - Tabela detalhada com views 7d/30d, inscritos, filtros
3. **Canais Minerados** - Concorrentes com mesmas funcionalidades
4. **Notificações** - Sistema de alertas e transcrição de vídeos
5. **Monetização** - Dashboard de receita YouTube AdSense (RPM, projeções)
6. **Financeiro** - Gestão financeira: receitas, despesas, metas, comparações

---

### **PARTE 3: Operacional (33 KB)**

#### `12_INTEGRACAO_GOOGLE_APIS.md` (18 KB)
- Google Sheets API (Service Account)
- Google Drive API (gdown, virus scan bypass)
- YouTube Data API v3 (20 keys, quota management)
- YouTube Analytics API v3 (OAuth, métricas avançadas)
- Setup completo de permissões

#### `13_DEPLOY_RAILWAY.md` (15 KB)
- **Environment variables** (20+ vars: Supabase, YouTube keys, Google)
- Build configuration
- CI/CD flow (GitHub → Railway → Deploy)
- Monitoring (logs, metrics, alertas)
- Rollback procedures
- Best practices

#### `14_TROUBLESHOOTING.md` (18 KB)
- Problemas de coleta (quota exceeded, API key suspensa)
- Problemas de OAuth (Invalid Grant, token expiration)
- Problemas de upload (download fail, timeout, UTF-8)
- Problemas de database (connection, RLS, constraints)
- **100+ scripts diagnósticos** no repo
- SQL queries úteis
- Checklist completo de diagnóstico

---

### **🆕 SISTEMAS COMPLEMENTARES (Janeiro 2026)**

#### **Mini-Steps Documentation** (📁 `mini-steps/`)
- **MINI_STEP_01_COLETA_YOUTUBE.md** (29 KB, 709 linhas) - Documentação ultra-detalhada completa
- **MINI_STEP_02 through MINI_STEP_11** (estrutura criada)
- **MINI_STEPS_INDEX.md** (52 KB) - Índice navegável de todas as 11 funções
- **FLOW_COMPLETO_SISTEMA.md** (32 KB) - Fluxos completos Frontend → Railway → Supabase

**Sistema de 11 mini-steps:**
- 8 funções backend (Coleta, Notificações, OAuth, Upload, Financeiro, Transcrição, Histórico, Sheets)
- 3 funções frontend (Mineração, Tabela, Analytics)
- Cada mini-step: código linha por linha + flows + troubleshooting + "Para Claude Próxima Vez"

#### **Sincronização Universal** (`sync.bat` e `sync.sh`)
- **sync.bat / sync.sh** - Comando universal para qualquer PC (Windows/Mac)
- Automatiza: git pull → git commit → git push
- Mantém documentação sincronizada via GitHub
- 100% automático, detecta conflitos
- Detecção inteligente de repositório (parent ou local)

#### **Changelog System** (📁 `changelog/`)
- **2025-01-12_CRIACAO_SISTEMA_COMPLETO.md** (12 KB) - Changelog inicial
- Todas as mudanças registradas com data, descrição e impacto
- Preserva contexto para Claude Code em sessões futuras

---

## 📊 Estatísticas da Documentação

| Métrica | Valor |
|---------|-------|
| **Total de arquivos** | 32+ arquivos (.md + .html + .bat + .sh) |
| **Total de conteúdo** | ~600 KB |
| **Linhas de markdown** | 15,500+ linhas |
| **Palavras estimadas** | ~80,000 palavras |
| **Tempo de leitura** | 5-6 horas (completo) |
| **Cobertura** | 100% do sistema (backend + frontend + infra) |

---

## 🔧 Principais Componentes

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `main.py` | 1122 | FastAPI app + endpoints |
| `collector.py` | 792 | YouTube collector (20 keys) |
| `notifier.py` | 449 | Sistema de notificações |
| `monetization_collector.py` | 311 | Coleta de receita (OAuth) |
| `monetization_endpoints.py` | 2233 | 9 endpoints de monetização |
| `financeiro.py` | ? | Sistema financeiro |
| `database.py` | ? | Supabase client |
| `yt_uploader/` | ? | Upload automatizado |

---

## 📊 Capacidade Atual

| Métrica | Valor |
|---------|-------|
| **Canais monitorados** | 50 próprios + 213 minerados = 263 total |
| **Canais monetizados** | 16 (com OAuth) |
| **API Keys YouTube** | 20 chaves (KEY_3-10, KEY_21-32) |
| **Quota disponível** | ~200,000 units/dia |
| **Uso atual** | ~50,000 units/dia (25%) |
| **Uploads/dia** | 100-130 vídeos |
| **Coleta completa** | 60-80 minutos |
| **Notificações/dia** | 10-50 oportunidades |

---

## 🚀 Deploy

**Produção:** Railway (auto-deploy via GitHub)

### **Sincronização Automática (Windows + Mac/Linux):**

```bash
# Navegue para a pasta docs primeiro
cd docs

# Windows
sync.bat

# Mac/Linux
./sync.sh
```

**O que faz:**
- ✅ Puxa atualizações do GitHub (git pull) - **TODOS os arquivos**
- ✅ Adiciona suas mudanças (git add .) - **TUDO** (código, docs, qualquer arquivo)
- ✅ Cria commit automático (git commit)
- ✅ Envia para GitHub (git push) - **Sincronização completa!**
- ✅ Auto-deploy Railway quando push em main

**💡 IMPORTANTE:** O sync agora sincroniza **TUDO** (não só docs/):
- Código Python (main.py, collector.py, etc)
- Documentação (docs/)
- Qualquer arquivo novo/editado/deletado

**Arquivos ignorados automaticamente (.gitignore):**
- scripts-temp/ (scripts de teste)
- backups/ (backups OAuth)
- debug/ (arquivos de investigação)

### **Manual:**

```bash
# Push para main → Auto-deploy Railway
git add .
git commit -m "Update"
git push origin main
```

**Ver:** `docs/13_DEPLOY_RAILWAY.md` para configuração completa

---

## 🔑 Variáveis de Ambiente (Railway)

```bash
# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJhbGc...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc... # Para OAuth tables

# YouTube Data API (20 keys)
YOUTUBE_API_KEY_3=AIzaSy...
YOUTUBE_API_KEY_4=AIzaSy...
# ... KEY_5 a KEY_10
YOUTUBE_API_KEY_21=AIzaSy...
# ... KEY_22 a KEY_32

# Google APIs
GOOGLE_CREDENTIALS_JSON={"type":"service_account"...}

# Optional
M5_TRANSCRIPTION_URL=https://transcription.2growai.com.br
```

**Ver lista completa:** `docs/13_DEPLOY_RAILWAY.md`

---

## 🧪 Testing

```bash
# Test local
python test_endpoint.py

# Test Railway
python test_railway.py

# API Docs (Swagger)
http://localhost:8000/docs
```

---

## 📝 Principais Endpoints

```bash
# Canais
GET  /api/canais              # Lista canais minerados
GET  /api/canais-tabela       # Nossos 50 canais (aba Tabela)
POST /api/canais              # Adiciona novo canal

# Vídeos
GET  /api/videos              # Lista vídeos coletados
GET  /api/videos/{id}         # Detalhes de vídeo
POST /api/videos/{id}/transcript  # Solicita transcrição

# Notificações
GET   /api/notificacoes       # Lista notificações
POST  /api/force-notifier     # Força verificação
PATCH /api/notificacoes/{id}/vista  # Marca como vista

# Análise
GET /api/subniche-trends      # Trends por subnicho
GET /api/system-stats         # Estatísticas gerais
GET /api/channel/{id}/history # Histórico diário

# Upload
POST /api/upload-video        # Upload vídeo YouTube
GET  /api/upload/{id}/status  # Status do upload

# Monetização (OAuth)
GET  /api/monetization/channels  # Canais com OAuth
POST /api/monetization/collect   # Coleta receita
```

**Ver referência completa:** `docs/08_API_ENDPOINTS_COMPLETA.md`

---

## 🆘 Troubleshooting

**Problemas comuns:**

- ❌ **Quota YouTube excedida** → Ver `docs/06_YOUTUBE_COLLECTOR.md` (rotação de keys)
- ❌ **OAuth expirado** → Ver `docs/09_MONETIZACAO_SISTEMA.md` (reautorização)
- ❌ **Coleta falhando** → Ver `docs/14_TROUBLESHOOTING.md` (diagnóstico)
- ❌ **Upload timeout** → Ver `docs/11_YOUTUBE_UPLOADER.md` (semáforo)

**Guia completo:** `docs/14_TROUBLESHOOTING.md`

---

## 🎯 Como Usar Esta Documentação

### **🚀 Setup Inicial (PRIMEIRA VEZ EM NOVO PC):**

**Quando você recebe/copia a pasta `docs/` para um novo PC:**

#### **Windows:**
1. Navegue até a pasta docs: `cd docs`
2. Execute **UMA VEZ**: `setup.bat`
3. Aguarde configuração automática
4. Pronto! Agora pode usar `sync.bat`

#### **Mac/Linux:**
1. Navegue até a pasta docs: `cd docs`
2. Execute **UMA VEZ**: `./setup.sh`
3. Aguarde configuração automática
4. Pronto! Agora pode usar `./sync.sh`

**O que o setup faz:**
- ✅ Inicializa repositório git local
- ✅ Conecta ao GitHub automaticamente
- ✅ Configura sparse checkout (somente docs/)
- ✅ Puxa arquivos mais recentes do GitHub

💡 **IMPORTANTE:** Rode `setup` APENAS na primeira vez! Se já tiver git configurado, ele detecta e não faz nada.

---

### **🔄 Sincronização (USO DIÁRIO):**

**Para manter documentação atualizada em qualquer PC:**

#### **Windows:**
1. Navegue até a pasta docs: `cd docs`
2. Execute: **`sync.bat`**

#### **Mac/Linux:**
1. Navegue até a pasta docs: `cd docs`
2. Execute: **`./sync.sh`**

**O que acontece automaticamente:**
- ✅ Puxa atualizações do GitHub (git pull)
- ✅ Salva suas mudanças locais (git add + commit)
- ✅ Envia tudo para GitHub (git push)
- ✅ **Sincronização perfeita entre Windows e Mac!**

**Arquivos:**
- `docs/setup.bat` e `docs/setup.sh` - Setup inicial (primeira vez)
- `docs/sync.bat` e `docs/sync.sh` - Sincronização (uso diário)

💡 **Pasta docs/ é 100% portátil!** Copie para qualquer PC, rode setup uma vez, e está pronta!

---

### **Para Claude Code em Nova Máquina:**

1. **Clone o repositório** do GitHub
2. **Claude lê `docs/00_INDICE_GERAL.md`** primeiro
3. **Claude lê `docs/MINI_STEPS_INDEX.md`** para funções específicas
4. **Claude lê `docs/FRONTEND_COMPLETO.md`** para entender as 6 abas
5. **Pronto!** Claude tem contexto completo de 100% do sistema (backend + frontend)

### **Para Desenvolvimento:**

1. Leia `README.md` (raiz do repo) para overview
2. Consulte documento específico (ex: `06_YOUTUBE_COLLECTOR.md`)
3. Use exemplos de código/SQL diretos
4. Referências cruzadas levam a docs relacionados

### **Para Troubleshooting:**

1. Vá direto para `14_TROUBLESHOOTING.md`
2. Encontre o problema específico
3. Siga o guia passo a passo
4. Links para docs detalhados se necessário

### **Para Apresentações:**

1. Abra `DASHBOARD_DOCUMENTATION.html` no navegador
2. Navegue pelas seções via sidebar
3. Visual moderno e profissional
4. Pode usar para onboarding de novos membros

---

## 🔗 Links Úteis

- **Repositório:** D:\ContentFactory\youtube-dashboard-backend
- **README principal:** ../README.md
- **Frontend:** Lovable (não neste repo)
- **Deploy:** Railway (auto-deploy via GitHub)
- **Database:** Supabase (PostgreSQL)
- **GitHub:** https://github.com/ccalu/youtube-dashboard-backend.git

---

## ✅ Checklist de Uso

### **Para Claude Code:**
- [ ] Ler `00_INDICE_GERAL.md`
- [ ] Ler `01_CONTENT_FACTORY_VISAO_GERAL.md` (contexto)
- [ ] Ler `03_DASHBOARD_PROPOSTA_VALOR.md` (propósito)
- [ ] Ler `FRONTEND_COMPLETO.md` (6 abas do dashboard)
- [ ] Consultar docs específicos conforme necessário

### **Para Desenvolvimento:**
- [ ] Entender arquitetura (`04_ARQUITETURA_SISTEMA.md`)
- [ ] Conhecer database schema (`05_DATABASE_SCHEMA.md`)
- [ ] Referência de API (`08_API_ENDPOINTS_COMPLETA.md`)
- [ ] Frontend (`FRONTEND_COMPLETO.md`)

### **Para Deploy:**
- [ ] Configurar env vars (`13_DEPLOY_RAILWAY.md`)
- [ ] Setup Google APIs (`12_INTEGRACAO_GOOGLE_APIS.md`)
- [ ] Verificar OAuth (`09_MONETIZACAO_SISTEMA.md`)

### **Para Troubleshooting:**
- [ ] Checklist completo (`14_TROUBLESHOOTING.md`)
- [ ] Scripts diagnósticos (100+ no repo)

---

## 🎓 Para Claude Code: Contexto Completo

Esta documentação foi criada para ser o **documento-mãe definitivo** do Dashboard de Mineração YouTube.

**Qualquer máquina + Claude Code que receber estes arquivos conseguirá:**

✅ Entender o negócio (Content Factory, estratégia, visão)
✅ Compreender por que o Dashboard existe
✅ Conhecer toda a arquitetura técnica (backend + frontend)
✅ Trabalhar em qualquer parte do código com confiança
✅ Fazer deploy e configurar em nova máquina
✅ Troubleshootar problemas comuns
✅ Propor melhorias alinhadas com o negócio

**Transferibilidade total. Contexto completo. Pronto para trabalhar.** 🚀

---

## 🔄 Manutenção

Esta documentação deve ser atualizada quando:
- Novas features forem adicionadas
- Arquitetura mudar significativamente
- Novas integrações forem criadas
- Processos operacionais mudarem

**Mantenha este documento-mãe sempre atualizado!**

---

## 📞 Contato

- **Cellibs (Marcelo):** Sistemas e inteligência
- **Projeto:** Content Factory
- **Repositório:** youtube-dashboard-backend
- **Deploy:** Railway (auto-deploy via GitHub)
- **Frontend:** Lovable (não neste repo)

---

## 📄 Licença

Propriedade da Content Factory. Uso interno.

---

**🚀 Comece lendo:**
1. [`docs/00_INDICE_GERAL.md`](./docs/documentacao-completa/00_INDICE_GERAL.md) - Índice completo
2. [`docs/FRONTEND_COMPLETO.md`](./docs/FRONTEND_COMPLETO.md) - Frontend: 6 abas do dashboard

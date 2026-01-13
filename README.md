# YouTube Dashboard Backend - Content Factory

Backend API para o Dashboard de Mineração YouTube da Content Factory.

**Stack:** FastAPI + Supabase + Railway + Python 3.10+

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

## 📚 DOCUMENTAÇÃO COMPLETA

**Toda a documentação está em [`docs/`](./docs/)**

### 🎯 Comece por aqui:

1. **[00_INDICE_GERAL.md](./docs/documentacao-completa/00_INDICE_GERAL.md)** - Índice completo e navegação
2. **[01_CONTENT_FACTORY_VISAO_GERAL.md](./docs/documentacao-completa/01_CONTENT_FACTORY_VISAO_GERAL.md)** - Contexto de negócio
3. **[03_DASHBOARD_PROPOSTA_VALOR.md](./docs/documentacao-completa/03_DASHBOARD_PROPOSTA_VALOR.md)** - Por que este sistema existe

---

## 📂 Estrutura da Documentação

### **PARTE 1: Contexto de Negócio**
- `01_CONTENT_FACTORY_VISAO_GERAL.md` - Empresa, estratégia, 50 canais, 8 subnichos
- `02_PIPELINE_PRODUCAO_OVERVIEW.md` - Como produzimos 100-130 vídeos/dia
- `03_DASHBOARD_PROPOSTA_VALOR.md` - Valor estratégico do dashboard

### **PARTE 2: Dashboard Técnico (9 docs)**
- `04_ARQUITETURA_SISTEMA.md` - Stack completo (FastAPI, Supabase, Railway)
- `05_DATABASE_SCHEMA.md` - Todas as 27 tabelas (DDL, queries, indexes)
- `06_YOUTUBE_COLLECTOR.md` - Coleta automatizada (20 API keys, 200k req/dia)
- `07_NOTIFICACOES_INTELIGENTES.md` - Sistema de alertas (10k, 50k, 100k views)
- `08_API_ENDPOINTS_COMPLETA.md` - Referência completa de API
- `09_MONETIZACAO_SISTEMA.md` - Coleta de receita (OAuth, 16 canais)
- `10_SISTEMA_FINANCEIRO.md` - Gestão financeira multi-canal
- `11_YOUTUBE_UPLOADER.md` - Upload automatizado (100-130 vídeos/dia)

### **PARTE 3: Operacional (3 docs)**
- `12_INTEGRACAO_GOOGLE_APIS.md` - Sheets, Drive, YouTube APIs
- `13_DEPLOY_RAILWAY.md` - Deploy em produção (CI/CD, env vars)
- `14_TROUBLESHOOTING.md` - Problemas comuns e soluções

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
- ✅ Puxa atualizações do GitHub (git pull)
- ✅ Adiciona suas mudanças (git add)
- ✅ Cria commit automático (git commit)
- ✅ Envia para GitHub (git push)
- ✅ Auto-deploy Railway quando push em main

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

## 🎓 Para Claude Code

**Esta documentação foi criada para ser o "documento-mãe" definitivo.**

Qualquer Claude Code que ler [`docs/00_INDICE_GERAL.md`](./docs/00_INDICE_GERAL.md) terá:

✅ Contexto completo do negócio Content Factory
✅ Arquitetura técnica detalhada (stack, integrações, fluxos)
✅ Database schema (27 tabelas, DDL, queries)
✅ Código documentado (files, functions, line numbers)
✅ Casos de uso práticos (Arthur, Cellibs, workflows)
✅ Troubleshooting (problemas comuns + soluções)
✅ Deploy e operação (Railway, CI/CD, env vars)

**Resultado:** Claude pode trabalhar no sistema com total confiança e contexto.

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

**🚀 Comece lendo:** [`docs/00_INDICE_GERAL.md`](./docs/00_INDICE_GERAL.md)

# 📚 ÍNDICE GERAL - Dashboard de Mineração YouTube

## 🎯 Bem-vindo ao DOCUMENTO-MÃE

Esta documentação contém **TODO o conhecimento necessário** para entender, operar e replicar o Dashboard de Mineração YouTube da **Content Factory**.

Qualquer máquina + Claude Code que ler estes documentos terá contexto completo para trabalhar no sistema.

---

## 📖 COMO USAR ESTA DOCUMENTAÇÃO

### Para Começar Rapidamente:
1. **Leia primeiro:** `01_CONTENT_FACTORY_VISAO_GERAL.md` - Entenda o negócio
2. **Depois:** `03_DASHBOARD_PROPOSTA_VALOR.md` - Entenda por que este sistema existe
3. **Então:** `04_ARQUITETURA_SISTEMA.md` - Visão técnica geral

### Para Desenvolvimento:
- Consulte os documentos técnicos (PARTE 2) por área específica
- Use `08_API_ENDPOINTS_COMPLETA.md` como referência de API
- Troubleshooting: vá direto para `14_TROUBLESHOOTING.md`

### Para Deploy:
- `13_DEPLOY_RAILWAY.md` tem tudo sobre produção
- `12_INTEGRACAO_GOOGLE_APIS.md` para configurar credenciais

---

## 📂 ESTRUTURA COMPLETA

### **PARTE 1: CONTEXTO DE NEGÓCIO**
Entenda quem somos, o que fazemos, e por que este sistema existe.

#### 01. [Visão Geral da Content Factory](./01_CONTENT_FACTORY_VISAO_GERAL.md)
- Quem somos (4 sócios, funções)
- Modelo de negócio (Netflix of AI content)
- Escala: 50 canais YouTube, 16 monetizados, 8 subnichos
- Crise Jan 2025 e oportunidades de mercado
- Estratégia de diversificação radical
- Filosofia: "Build a company, not an operation"

#### 02. [Pipeline de Produção - Overview](./02_PIPELINE_PRODUCAO_OVERVIEW.md)
- Como criamos vídeos (17 passos, 8 agentes AI)
- 5 máquinas de produção (M1-M5)
- Capacidade: 100-130 vídeos/dia
- Tech stack: ComfyUI, FFmpeg, AllTalk, WhisperX, Gemini
- Sistema de rotação (música, overlays, animações)
- Novos formatos: HeyGen avatars

---

### **PARTE 2: DASHBOARD TÉCNICO**
Detalhes técnicos completos do sistema de mineração e gestão.

#### 03. [Dashboard - Proposta de Valor](./03_DASHBOARD_PROPOSTA_VALOR.md)
- **Por que este sistema existe**
- Inteligência de mercado para Content Factory
- Minera canais concorrentes/referência
- Identifica oportunidades (vídeos 10k+ views)
- Monitora NOSSOS 50 canais
- Base de decisões estratégicas

#### 04. [Arquitetura do Sistema](./04_ARQUITETURA_SISTEMA.md)
- **Stack completo e fluxo de dados**
- Frontend: Lovable (online)
- Backend: Railway (FastAPI Python)
- Database: Supabase (PostgreSQL)
- APIs: YouTube Data v3, YouTube Analytics v3, M5 Transcription
- Deploy: GitHub → Railway auto-deploy
- Diagramas e relacionamentos

#### 05. [Database Schema](./05_DATABASE_SCHEMA.md)
- **Todas as tabelas com propósito de negócio**
- `canais` - Canais minerados + nossos 50 canais
- `videos` - Vídeos coletados + análise
- `notificacoes` - Alertas de oportunidade
- `regras_notificacao` - Configuração de marcos
- `historico_diario` - Evolução inscritos
- `monetization_history` - Receita dos 16 canais monetizados
- `upload_queue` - Fila de uploads
- `lancamentos_financeiro` - Gestão financeira
- Relacionamentos, indexes, queries comuns

#### 06. [YouTube Collector - Coleta Automatizada](./06_YOUTUBE_COLLECTOR.md)
- **Sistema de coleta com 20 API keys**
- Arquivo: `collector.py` (727 linhas)
- 20 chaves YouTube (KEY_3-10 + KEY_21-32)
- Capacidade: ~200k requisições/dia
- Rate limiter: 90 req/100s (anti-ban)
- Rotação inteligente de chaves
- O que coleta: canais, vídeos, estatísticas, transcrições
- Decodificação HTML, tratamento de erros

#### 07. [Sistema de Notificações Inteligentes](./07_NOTIFICACOES_INTELIGENTES.md)
- **Como identificamos oportunidades**
- Arquivo: `notifier.py` (394 linhas)
- Lógica: Marcos de performance (10k/24h, 50k/7d, 100k/30d)
- Anti-duplicação: Não notifica 2x o mesmo marco
- Sistema de elevação: 10k → 50k → 100k
- Filtros: Por subnicho, tipo de canal
- Use case: Arthur recebe alerta → analisa → cria versão nossa

#### 08. [API Endpoints - Referência Completa](./08_API_ENDPOINTS_COMPLETA.md)
- **Todos os endpoints com exemplos**
- Arquivo: `main.py` (1122 linhas)
- Canais: CRUD + filtros + aba Tabela
- Vídeos: Busca + detalhes + transcrição
- Notificações: Lista + marcar vista + forçar verificação
- Análise: Trends por subnicho + system stats
- Histórico: Evolução diária dos canais
- Coleta: Forçar manual + status
- Monetização: OAuth + coleta receita
- Upload: Enviar vídeo + status
- Financeiro: Lançamentos receita/despesa
- Exemplos de request/response

#### 09. [Sistema de Monetização](./09_MONETIZACAO_SISTEMA.md)
- **Coleta de receita dos 16 canais monetizados**
- Arquivo: `monetization_collector.py`
- OAuth 2.0: Autenticação com refresh tokens
- YouTube Analytics API: Dados de receita
- Métricas: Revenue (USD→BRL), Views, Engagement, Watch Time
- Demographics: País, idade, gênero
- Traffic sources: YouTube search, Browse, External
- Proxies: Proteção multi-proxy
- Tabelas: `monetization_credentials`, `monetization_history`

#### 10. [Sistema Financeiro](./10_SISTEMA_FINANCEIRO.md)
- **Gestão financeira multi-canal**
- Arquivo: `financeiro.py`
- Lançamentos manuais (receita/despesa)
- Conversão USD → BRL automática
- Categorias customizadas
- Filtros por canal/período
- Dashboard lucro/prejuízo
- Tabelas: `lancamentos_financeiro`, `categorias_lancamento`

#### 11. [YouTube Uploader - Upload Automatizado](./11_YOUTUBE_UPLOADER.md)
- **Integração com pipeline de produção**
- Pasta: `yt_uploader/`
- Fluxo: Produção → Fila → Upload → Sheets → DB
- Componentes: `uploader.py`, `database.py`, `sheets.py`
- Proteções: Semáforo (max 3 uploads simultâneos)
- Retry logic + Status tracking detalhado
- Fecha o loop: produção → publicação

---

### **PARTE 3: INTEGRAÇÕES E OPERAÇÕES**
Como conectamos com sistemas externos e rodamos em produção.

#### 12. [Integração com Google APIs](./12_INTEGRACAO_GOOGLE_APIS.md)
- **Google Sheets API**
  - Credenciais: `service_account.json`
  - Permissões necessárias
  - Planilhas usadas (tracking uploads, revenue, analytics)
- **Google Drive API**
  - Download de vídeos via `gdown`
  - Contorno virus scan para arquivos grandes
- **YouTube Data API v3**
  - 20 chaves configuradas
  - Quota limits e rotação
- **YouTube Analytics API v3**
  - OAuth por canal
  - Dados de monetização

#### 13. [Deploy e Produção (Railway)](./13_DEPLOY_RAILWAY.md)
- **Configuração Railway**
  - 20+ variáveis de ambiente
  - Build/start commands
  - Health checks
- **Logs e monitoramento**
  - Como acessar logs
  - Principais erros e soluções
- **CI/CD**
  - Push GitHub → Auto-deploy Railway
  - Rollback process
- **Segurança**
  - CORS configurado
  - Secrets management

#### 14. [Troubleshooting - Guia Completo](./14_TROUBLESHOOTING.md)
- **Problemas comuns e soluções**
  - Quota YouTube excedida → Rotação de keys
  - OAuth expirado → Reautorização
  - Coleta falhando → Diagnóstico passo a passo
  - Notificações duplicadas → Sistema anti-dup
  - Upload timeout → Ajustar semáforo
- **Comandos úteis**
  - Reset database
  - Forçar coleta
  - Validar setup
- **Scripts de diagnóstico** (100+ scripts .py no repo)

---

## 🔗 RELACIONAMENTOS ENTRE SISTEMAS

### Fluxo Principal de Dados

```
📺 YouTube (Canais Concorrentes)
    ↓
[YouTube Collector] ← 20 API Keys
    ↓
[Supabase Database] → canais, videos
    ↓
[Notification Checker] → regras_notificacao
    ↓
[Dashboard Frontend] ← Arthur/Cellibs veem oportunidades
    ↓
[Pipeline de Produção] → M1-M5 criam vídeo
    ↓
[YouTube Uploader] → Publica no canal
    ↓
[Monetization Collector] → Coleta receita (16 canais)
    ↓
[Sistema Financeiro] → Dashboards financeiros
```

### Integrações Externas

```
🔴 YouTube Data API v3
   - Coleta de dados públicos
   - 20 keys, 200k req/dia

🔴 YouTube Analytics API v3
   - Dados de receita (OAuth)
   - 16 canais monetizados

🟢 Supabase (PostgreSQL)
   - Database principal
   - Real-time subscriptions

🟢 Google Sheets API
   - Tracking uploads
   - Revenue dashboards

🟢 Google Drive API
   - Download vídeos
   - Virus scan workaround

🟠 M5 Transcription Server
   - https://transcription.2growai.com.br
   - Transcrições automáticas

🟣 Railway
   - Deploy backend
   - Auto-deploy GitHub

🔵 Lovable
   - Frontend online
   - Interface para Arthur/Cellibs
```

---

## 📊 MÉTRICAS E ESCALA

### Capacidade do Sistema
- **Canais monitorados:** 50+ (nossos) + centenas (minerados)
- **Vídeos coletados:** Milhares/dia
- **Notificações:** 10-50/dia (oportunidades)
- **API requests:** ~200k/dia (YouTube)
- **Uploads:** 100-130 vídeos/dia
- **Receita coletada:** Diária (16 canais)

### Performance
- **Coleta completa:** ~30-45min (todos os canais)
- **Rate limit:** 90 req/100s (YouTube)
- **Upload simultâneo:** Max 3 (Railway protection)
- **Database queries:** <500ms (médio)
- **Uptime:** 99.5% (Railway)

---

## 🎓 GLOSSÁRIO TÉCNICO

### Termos de Negócio
- **Subnicho:** Categoria de conteúdo (ex: Wars, Psychology, Mysteries)
- **Canal Nosso:** Um dos 50 canais da Content Factory
- **Canal Minerado:** Canal concorrente/referência que monitoramos
- **Monetizado:** Canal com monetização YouTube ativa (16 de 50)
- **Marco:** Milestone de views (10k, 50k, 100k)
- **Oportunidade:** Vídeo que atingiu marco e pode ser replicado

### Termos Técnicos
- **Collector:** Sistema que coleta dados do YouTube
- **Notifier:** Sistema que cria notificações de oportunidades
- **Rate Limiter:** Proteção contra ban (90 req/100s)
- **API Key Rotation:** Rotação automática entre 20 chaves
- **OAuth Flow:** Autenticação para dados de monetização
- **Semaphore:** Controle de uploads simultâneos (max 3)
- **Supabase:** PostgreSQL gerenciado (database)
- **Railway:** Plataforma de deploy (backend)
- **Lovable:** Plataforma frontend (sem código)

### Tabelas Principais
- **canais:** Todos os canais (nossos + minerados)
- **videos:** Vídeos coletados dos canais
- **notificacoes:** Alertas de oportunidades
- **historico_diario:** Evolução diária de inscritos
- **monetization_history:** Histórico de receita
- **upload_queue:** Fila de uploads pendentes

---

## 🚀 QUICK START

### Para Desenvolvimento Local

1. **Clone o repositório:**
```bash
git clone [repo-url]
cd youtube-dashboard-backend
```

2. **Instale dependências:**
```bash
pip install -r requirements.txt --break-system-packages
```

3. **Configure .env:**
```bash
SUPABASE_URL=your_url
SUPABASE_KEY=your_key
YOUTUBE_API_KEY_3=your_key
# ... (ver 13_DEPLOY_RAILWAY.md para lista completa)
```

4. **Rode o servidor:**
```bash
python main.py
```

5. **Acesse:**
- API local: http://localhost:8000
- Docs: http://localhost:8000/docs

### Para Trabalhar no Código

1. **Leia primeiro:**
   - `01_CONTENT_FACTORY_VISAO_GERAL.md` (contexto)
   - `03_DASHBOARD_PROPOSTA_VALOR.md` (propósito)
   - `04_ARQUITETURA_SISTEMA.md` (arquitetura)

2. **Consulte referências:**
   - `05_DATABASE_SCHEMA.md` (tabelas)
   - `08_API_ENDPOINTS_COMPLETA.md` (endpoints)

3. **Para features específicas:**
   - Coleta: `06_YOUTUBE_COLLECTOR.md`
   - Notificações: `07_NOTIFICACOES_INTELIGENTES.md`
   - Monetização: `09_MONETIZACAO_SISTEMA.md`
   - Upload: `11_YOUTUBE_UPLOADER.md`

4. **Problemas?**
   - `14_TROUBLESHOOTING.md` (soluções)

---

## 🎯 OBJETIVO DESTA DOCUMENTAÇÃO

Esta documentação foi criada para ser **o documento-mãe definitivo** do Dashboard de Mineração YouTube.

**Qualquer máquina + Claude Code que receber estes arquivos conseguirá:**

✅ Entender o contexto completo do negócio Content Factory
✅ Compreender por que o Dashboard existe e como serve à estratégia
✅ Conhecer toda a arquitetura técnica (stack, integrações, fluxos)
✅ Trabalhar em qualquer parte do código com confiança
✅ Fazer deploy e configurar em nova máquina
✅ Troubleshootar problemas comuns
✅ Propor melhorias alinhadas com o negócio

**Transferibilidade total. Contexto completo. Pronto para trabalhar.** 🚀

---

## 📝 SOBRE ESTA DOCUMENTAÇÃO

- **Criado por:** Cellibs (Marcelo) via Claude Code
- **Data:** Janeiro 2025
- **Versão:** 1.0
- **Propósito:** Documento-mãe para transferência de conhecimento
- **Audiência:** Claude Code em qualquer máquina
- **Status:** Completo e pronto para uso

---

## 🔄 ATUALIZAÇÃO

Esta documentação deve ser atualizada quando:
- Novas features forem adicionadas
- Arquitetura mudar significativamente
- Novas integrações forem criadas
- Processos operacionais mudarem

**Mantenha este documento-mãe sempre atualizado!**

---

**🎯 Próximos Passos:**
Comece lendo `01_CONTENT_FACTORY_VISAO_GERAL.md` para entender o contexto completo do negócio.

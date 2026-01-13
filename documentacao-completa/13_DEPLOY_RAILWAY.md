# 13 - Deploy Railway

**Configuração completa do deploy em produção no Railway**

---

## Índice

1. [Visão Geral](#visão-geral)
2. [Environment Variables](#environment-variables)
3. [Build Configuration](#build-configuration)
4. [CI/CD Flow](#cicd-flow)
5. [Monitoring](#monitoring)
6. [Rollback](#rollback)

---

## Visão Geral

**Plataforma:** Railway (https://railway.app)

**Serviço:** youtube-dashboard-backend

**GitHub:** Conectado via GitHub App (auto-deploy em push)

**Runtime:** Python 3.11

**Comandos:**
```bash
# Build
pip install -r requirements.txt --break-system-packages

# Start
python main.py
```

**Port:** Detectado automaticamente via `$PORT` env var (Railway injeta)

---

## Environment Variables

### 1. Supabase (Database)

```bash
# URL do projeto Supabase
SUPABASE_URL=https://prvkmzstyedepvlbppyo.supabase.co

# Anon key (pública, safe para frontend)
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Service role key (admin, bypass RLS)
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Uso:**
- `SUPABASE_KEY` - Endpoints normais
- `SUPABASE_SERVICE_ROLE_KEY` - OAuth tokens (protegido por RLS)

---

### 2. YouTube Data API v3 (20 Keys)

```bash
# Keys de mineração (rotação automática)
YOUTUBE_API_KEY_3=AIzaSyAxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
YOUTUBE_API_KEY_4=AIzaSyAxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
YOUTUBE_API_KEY_5=AIzaSyAxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
YOUTUBE_API_KEY_6=AIzaSyAxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
YOUTUBE_API_KEY_7=AIzaSyAxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
YOUTUBE_API_KEY_8=AIzaSyAxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
YOUTUBE_API_KEY_9=AIzaSyAxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
YOUTUBE_API_KEY_10=AIzaSyAxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
YOUTUBE_API_KEY_21=AIzaSyAxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
YOUTUBE_API_KEY_22=AIzaSyAxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
YOUTUBE_API_KEY_23=AIzaSyAxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
YOUTUBE_API_KEY_24=AIzaSyAxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
YOUTUBE_API_KEY_25=AIzaSyAxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
YOUTUBE_API_KEY_26=AIzaSyAxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
YOUTUBE_API_KEY_27=AIzaSyAxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
YOUTUBE_API_KEY_28=AIzaSyAxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
YOUTUBE_API_KEY_29=AIzaSyAxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
YOUTUBE_API_KEY_30=AIzaSyAxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
YOUTUBE_API_KEY_31=AIzaSyAxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
YOUTUBE_API_KEY_32=AIzaSyAxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Quota:**
- 10,000 units/dia por key
- Total: 200,000 units/dia

---

### 3. Google Sheets API (Service Account)

```bash
# Credenciais Service Account (JSON em string única)
GOOGLE_SHEETS_CREDENTIALS={"type":"service_account","project_id":"youtube-dashboard-123","private_key_id":"abc123...","private_key":"-----BEGIN PRIVATE KEY-----\n...","client_email":"sheets@project.iam.gserviceaccount.com",...}

# Credenciais para upload (separado)
GOOGLE_SHEETS_CREDENTIALS_2={"type":"service_account","project_id":"youtube-upload-456","private_key_id":"def456...","private_key":"-----BEGIN PRIVATE KEY-----\n...","client_email":"upload-sheets@project.iam.gserviceaccount.com",...}
```

**IMPORTANTE:**
- JSON completo em string única
- Sem quebras de linha no meio (apenas dentro de `private_key`)
- Railway aceita strings longas (não tem limite de tamanho)

---

### 4. Transcription Server

```bash
# Servidor M5 (transcrições)
TRANSCRIPTION_SERVER_URL=https://transcription.2growai.com.br
```

---

### 5. Scheduler Configuration

```bash
# Horário da coleta principal (UTC)
COLLECTION_HOUR=5  # 5 AM UTC = 2 AM BRT

# Timezone (para logs)
TZ=America/Sao_Paulo
```

---

### 6. Upload Worker Configuration

```bash
# Habilitar/desabilitar worker
UPLOAD_WORKER_ENABLED=true

# Intervalo entre verificações (segundos)
UPLOAD_WORKER_INTERVAL_SECONDS=120  # 2 minutos

# Máximo de vídeos por batch
UPLOAD_WORKER_BATCH_SIZE=5

# Max erros consecutivos antes de desligar
UPLOAD_WORKER_MAX_ERRORS=5

# Recursos mínimos (MB)
UPLOAD_WORKER_MIN_FREE_MEMORY_MB=200
UPLOAD_WORKER_MIN_FREE_DISK_MB=500

# Delay inicial (segundos)
UPLOAD_WORKER_STARTUP_DELAY=180  # 3 minutos
```

---

### 7. Logging

```bash
# Diretório de logs
LOG_DIR=./logs

# Level de logging
LOG_LEVEL=INFO  # DEBUG | INFO | WARNING | ERROR
```

---

### 8. Railway Internal

```bash
# Port do servidor (Railway injeta automaticamente)
PORT=8000  # Detectado pelo Railway

# Ambiente
ENVIRONMENT=production  # production | development
```

---

## Build Configuration

### 1. Railway Settings

**Build Command:**
```bash
pip install -r requirements.txt --break-system-packages
```

**Start Command:**
```bash
python main.py
```

**Python Version:** 3.11 (detectado via requirements.txt)

**Watch Paths:** (Auto-deploy em mudanças)
```
*.py
requirements.txt
```

---

### 2. requirements.txt

**Arquivo:** `D:\ContentFactory\youtube-dashboard-backend\requirements.txt`

```txt
fastapi==0.104.1
uvicorn==0.24.0
supabase==2.0.3
aiohttp==3.9.1
google-api-python-client==2.108.0
google-auth==2.25.2
google-auth-oauthlib==1.2.0
google-auth-httplib2==0.2.0
gspread==5.12.0
gdown==4.7.1
apscheduler==3.10.4
psutil==5.9.6
python-dotenv==1.0.0
```

**Nota:** `--break-system-packages` necessário no Railway para evitar conflitos

---

### 3. Procfile (Opcional)

**Arquivo:** `D:\ContentFactory\youtube-dashboard-backend\Procfile`

```
web: python main.py
```

**Nota:** Railway detecta automaticamente o comando de start, Procfile é opcional

---

## CI/CD Flow

### 1. Fluxo Completo

```
┌──────────────┐
│ Git Push     │
│ (main branch)│
└──────┬───────┘
       │
       ↓
┌──────────────┐
│ GitHub       │
│ Webhook      │
└──────┬───────┘
       │
       ↓
┌──────────────┐
│ Railway      │
│ Build Start  │
└──────┬───────┘
       │
       ↓
┌──────────────┐
│ Install Deps │
│ (pip install)│
└──────┬───────┘
       │
       ↓
┌──────────────┐
│ Health Check │
│ (GET /health)│
└──────┬───────┘
       │
       ↓
┌──────────────┐
│ Deploy Live  │
│ (zero downtime)
└──────────────┘
```

**Tempo típico:** 2-3 minutos (do push ao deploy)

---

### 2. Deploy Logs

**Railway → Deployments → Select deploy → Logs**

```bash
# Logs típicos de deploy bem-sucedido
Building...
  pip install -r requirements.txt --break-system-packages
  Successfully installed fastapi-0.104.1 uvicorn-0.24.0 ...

Starting...
  python main.py

Logs:
  INFO:     Started server process [1]
  INFO:     Waiting for application startup.
  🚀 YouTube collector initialized with 20 API keys
  📊 Total quota disponível: 200,000 units/dia
  📅 Próxima coleta: 2024-01-11 05:00:00 UTC
  INFO:     Application startup complete.
  INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

### 3. Health Checks

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy"
}
```

**Railway verifica automaticamente:**
- Se servidor responde em `$PORT`
- Se `/health` retorna 200
- Deploy só é marcado como "Live" após health check passar

---

## Monitoring

### 1. Railway Dashboard

**Metrics disponíveis:**
- CPU usage (%)
- Memory usage (MB)
- Network (in/out)
- Response times

**Acesso:** Railway → Project → Service → Metrics

---

### 2. Logs em Tempo Real

**Railway → Service → Logs**

**Filtros úteis:**
```bash
# Erros apenas
grep ERROR

# Coletas
grep "COLETA"

# Upload worker
grep "📤"

# Notificações
grep "🔔"

# OAuth
grep "OAuth"
```

---

### 3. Application Logs

**Arquivo:** `main.py`

**Logging configurado:**
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler()  # Railway captura stdout
    ]
)

logger = logging.getLogger(__name__)
```

**Logs importantes:**
```bash
# Startup
"🚀 YouTube collector initialized with 20 API keys"
"📊 Total quota disponível: 200,000 units/dia"
"📅 Próxima coleta: 2024-01-11 05:00:00 UTC"

# Coleta
"🔄 INICIANDO COLETA DE DADOS"
"✅ COLETA FINALIZADA - 234 vídeos coletados"

# Upload worker
"📤 UPLOAD QUEUE WORKER INICIADO"
"✅ 3 uploads concluídos, ❌ 0 falhas"

# OAuth
"✅ Token renovado com sucesso"
"❌ Erro OAuth: Invalid Grant"

# Notificações
"🔔 69 notificações criadas"
```

---

### 4. Alertas

**Railway não tem alertas built-in.**

**Soluções:**
1. **UptimeRobot** (free) - Ping `/health` a cada 5 min
2. **Sentry** (free tier) - Error tracking
3. **Custom webhook** - Enviar notificação no Slack/Discord em erros

**Exemplo UptimeRobot:**
```
Monitor type: HTTP(s)
URL: https://youtube-dashboard-backend-production.up.railway.app/health
Interval: 5 minutes
Alert contacts: Email/SMS/Slack
```

---

## Rollback

### 1. Via Railway Dashboard

**Railway → Deployments → Select previous deploy → Redeploy**

**Processo:**
1. Identifica deploy anterior (working)
2. Clica em "..." → Redeploy
3. Railway faz novo deploy com código anterior
4. Zero downtime (mantém deploy atual até novo estar pronto)

**Tempo:** ~2-3 minutos

---

### 2. Via Git

**Reverter commit:**
```bash
# 1. Identificar commit anterior
git log --oneline
# 2cfb051 fix: Handle None values (atual - com erro)
# 653b7eb fix: Handle None inscritos (anterior - working)

# 2. Reverter para commit anterior
git revert 2cfb051

# 3. Push para trigger deploy
git push origin main
```

---

### 3. Hotfix (Emergência)

**Se sistema está 100% down:**

```bash
# 1. Criar branch de hotfix
git checkout -b hotfix/critical-error

# 2. Fix crítico (ex: remover código que quebra startup)
# Editar arquivos...

# 3. Commit e push direto
git add .
git commit -m "hotfix: Remove código com erro crítico"
git push origin hotfix/critical-error

# 4. Fazer Railway apontar para branch hotfix
Railway → Settings → Source → Branch: hotfix/critical-error

# 5. Após estabilizar, merge para main
git checkout main
git merge hotfix/critical-error
git push origin main

# 6. Railway apontar de volta para main
Railway → Settings → Source → Branch: main
```

---

### 4. Desabilitar Features

**Via ENV vars (sem deploy):**

```bash
# Desabilitar upload worker
Railway → Variables → UPLOAD_WORKER_ENABLED=false
Railway → Restart

# Desabilitar coleta automática
# (Comentar código ou adicionar env var)
SCHEDULER_ENABLED=false
```

**Vantagem:** Não precisa fazer deploy de código novo

---

## Troubleshooting Railway

### 1. Deploy Falha no Build

**Sintomas:**
```
Error: Command failed: pip install -r requirements.txt
```

**Causas:**
- Dependência não existe
- Versão incompatível
- Network timeout

**Solução:**
```bash
# 1. Testar localmente
pip install -r requirements.txt

# 2. Lock versions
pip freeze > requirements.txt

# 3. Push
git add requirements.txt
git commit -m "fix: Lock dependency versions"
git push
```

---

### 2. Aplicação Crasha no Startup

**Sintomas:**
```
Application failed to start
Exit code: 1
```

**Causas:**
- Import error
- Missing env var
- Database connection error

**Debug:**
```bash
# 1. Ver logs completos
Railway → Logs → Filter: ERROR

# 2. Verificar traceback
# "ModuleNotFoundError: No module named 'xxx'"
# "KeyError: 'YOUTUBE_API_KEY_3'"

# 3. Fix e deploy
```

---

### 3. Out of Memory

**Sintomas:**
```
Container killed (OOMKilled)
Exit code: 137
```

**Causas:**
- Upload de vídeos grandes
- Memory leak
- Múltiplos processos simultâneos

**Solução:**
```bash
# 1. Upgrade Railway plan (mais RAM)
Railway → Settings → Plan → Pro ($20/mês = 8GB RAM)

# 2. Reduzir batch size
UPLOAD_WORKER_BATCH_SIZE=3  # Era 5

# 3. Adicionar memory limits no código
import resource
resource.setrlimit(resource.RLIMIT_AS, (2 * 1024 * 1024 * 1024, -1))  # 2GB max
```

---

### 4. Database Connection Timeout

**Sintomas:**
```
Error: Connection timeout to Supabase
```

**Causa:** Supabase bloqueou IP ou quota excedida

**Solução:**
```bash
# 1. Verificar Supabase dashboard
Supabase → Project → Database → Connection pooling

# 2. Verificar API rate limits
Supabase → Project → Settings → API

# 3. Adicionar retry logic
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def query_supabase():
    return db.supabase.table("...").select("*").execute()
```

---

### 5. Environment Variables Não Carregam

**Sintomas:**
```
KeyError: 'YOUTUBE_API_KEY_3'
```

**Causa:** Env var não configurada ou typo no nome

**Solução:**
```bash
# 1. Verificar Railway
Railway → Variables → Verificar se existe YOUTUBE_API_KEY_3

# 2. Verificar typo no código
# ❌ os.environ.get("YOUTUBE_API_KEY3")  # Faltou underscore
# ✅ os.environ.get("YOUTUBE_API_KEY_3")

# 3. Restart após adicionar vars
Railway → Restart
```

---

## Best Practices Railway

### 1. Staging Environment

**Criar ambiente de teste:**
```
Railway → New Service → youtube-dashboard-staging
Settings → Source → Branch: staging

# Workflow
main (production) ← merge ← staging (testing) ← feature branches
```

---

### 2. Secrets Management

**Nunca commitar secrets:**
```bash
# .gitignore
.env
*.json  # Service account keys
credentials/
```

**Usar Railway Variables para tudo sensível**

---

### 3. Cost Optimization

**Railway cobra por:**
- Execution time (CPU usage)
- Memory usage
- Network egress (upload de vídeos consome)

**Otimizações:**
```bash
# 1. Desligar services não usados
Railway → Service → Settings → Sleep after inactivity

# 2. Limitar upload batch
UPLOAD_WORKER_BATCH_SIZE=3

# 3. Cleanup de logs antigos
# (Railway não cobra por logs, mas ocupa espaço)
```

**Estimativa mensal:**
- Hobby plan ($5/mês): 500 horas execution + $5 crédito
- Pro plan ($20/mês): Ilimitado + 8GB RAM

---

**Referências:**
- Railway Docs: https://docs.railway.app
- Railway Status: https://status.railway.app

---

**Última atualização:** 2024-01-12

# 📤 SISTEMA DE UPLOAD DIÁRIO AUTOMÁTICO

## 📋 VISÃO GERAL

Sistema que automatiza o upload de vídeos para YouTube, fazendo **1 upload por dia por canal** após a coleta diária de dados (~5:30-6:00 AM).

### Características Principais:
- ✅ **1 vídeo por canal por dia** (controle total)
- 💰 **Prioriza canais monetizados** (maior ROI)
- 🔁 **Retry automático** às 6:30 e 7:00 AM
- 📊 **Dashboard visual** em tempo real (localhost:5002)
- ⚠️ **Alertas** para canais sem vídeos disponíveis
- 🔒 **Proteção contra duplicatas** (não sobe 2x o mesmo vídeo)
- 📈 **Logs detalhados** de todas operações

---

## 🚀 COMO USAR

### 1️⃣ CONFIGURAÇÃO INICIAL

#### A) Executar SQL no Supabase:
```bash
# Arquivo: scripts/database/001_add_upload_automatico.sql
# Execute no SQL Editor do Supabase
```

#### B) Configurar variáveis no Railway:
```env
DAILY_UPLOAD_ENABLED=true
GOOGLE_SHEETS_CREDENTIALS_2={"type":"service_account",...}

# Opcional - desabilitar sistema antigo:
UPLOAD_WORKER_ENABLED=false
SCANNER_ENABLED=false
```

### 2️⃣ ADICIONAR CANAIS

Use o novo wizard atualizado:
```bash
python scripts-temp/add_canal_wizard_v2.py
```

O wizard vai perguntar:
1. **Channel ID** (UCxxxxxxxxx)
2. **Nome do canal**
3. **URL da planilha** ⭐ NOVO - Obrigatório!
4. **Canal monetizado?** (s/n) - Para priorização
5. **Língua e subnicho**
6. **Credenciais OAuth** (Client ID/Secret)

### 3️⃣ TESTAR O SISTEMA

```bash
# Menu interativo de teste
python test_daily_upload.py

Opções:
1. Listar canais configurados
2. Testar 1 canal específico
3. Testar múltiplos canais
4. Verificar planilha
5. Executar upload completo
```

### 4️⃣ MONITORAR VIA DASHBOARD

```bash
# Iniciar dashboard local
python dashboard_daily_uploads.py

# Acessar no navegador
http://localhost:5002
```

**Dashboard mostra:**
- Status em tempo real de cada canal
- Estatísticas do dia (sucesso/erro/sem vídeo)
- Alertas de problemas
- Botões de ação (retry, parar, etc)
- Auto-refresh a cada 1 segundo

---

## ⚙️ COMO FUNCIONA

### Fluxo de Execução:

```
5:30 AM - Coleta diária termina
    ↓
5:45 AM - Sistema detecta fim da coleta
    ↓
Para cada canal (monetizados primeiro):
    1. Verifica se já fez upload hoje
    2. Abre planilha do Google Sheets
    3. Busca primeiro vídeo com status="done"
    4. Valida colunas K e L (devem estar vazias)
    5. Faz upload para YouTube (privado)
    6. Registra resultado no banco
    ↓
6:30 AM - Retry 1 (canais com erro)
    ↓
7:00 AM - Retry 2 (última tentativa)
```

### Validação de Vídeo Pronto:
- **Coluna J** (Status) = "done"
- **Coluna K** (Post) = vazio
- **Coluna L** (Published Date) = vazio
- **Coluna M** (Drive URL) = preenchido
- **Coluna O** (Upload) = vazio ou contém "Erro"

---

## 📁 ARQUIVOS DO SISTEMA

### Arquivos Principais:
```
daily_uploader.py           # Sistema principal de upload diário
dashboard_daily_uploads.py  # Dashboard visual (localhost:5002)
add_canal_wizard_v2.py      # Wizard atualizado com spreadsheet
test_daily_upload.py        # Script de teste interativo
integrate_daily_upload.py   # Instruções de integração com main.py
```

### SQL/Banco de Dados:
```
scripts/database/001_add_upload_automatico.sql  # Cria tabelas necessárias
```

### Tabelas Criadas:
- **yt_channels** → Coluna `upload_automatico` (BOOLEAN)
- **yt_upload_daily_logs** → Log de cada execução diária
- **yt_canal_upload_diario** → Status por canal por dia

---

## 🔧 INTEGRAÇÃO COM MAIN.PY

### Adicionar no início do main.py:
```python
from daily_uploader import schedule_daily_uploader

# Variável de controle
DAILY_UPLOAD_ENABLED = os.getenv("DAILY_UPLOAD_ENABLED", "false").lower() == "true"
```

### Adicionar no startup:
```python
if DAILY_UPLOAD_ENABLED:
    asyncio.create_task(schedule_daily_uploader())
    logger.info("✅ Sistema de upload diário ATIVADO")
```

---

## 🎯 COMANDOS RÁPIDOS

### Teste Rápido:
```bash
# Testar 3 canais
python test_daily_upload.py
# Escolher opção 3
```

### Dashboard:
```bash
# Terminal 1
python dashboard_daily_uploads.py

# Terminal 2 (navegador)
start http://localhost:5002
```

### Adicionar Canal:
```bash
python scripts-temp/add_canal_wizard_v2.py
```

---

## 📊 MÉTRICAS E LOGS

### Onde verificar logs:

1. **Terminal/Console** - Logs em tempo real
2. **Dashboard** - Visual em localhost:5002
3. **Banco de dados:**
   - `yt_upload_daily_logs` - Resumo diário
   - `yt_canal_upload_diario` - Detalhes por canal
   - `yt_upload_queue` - Fila de uploads

### Queries úteis:
```sql
-- Ver execuções de hoje
SELECT * FROM yt_upload_daily_logs
WHERE data = CURRENT_DATE
ORDER BY tentativa_numero;

-- Ver status de cada canal hoje
SELECT * FROM yt_canal_upload_diario
WHERE data = CURRENT_DATE
ORDER BY channel_name;

-- Canais com erro
SELECT channel_name, erro_mensagem, tentativa_numero
FROM yt_canal_upload_diario
WHERE data = CURRENT_DATE AND status = 'erro';
```

---

## ⚠️ TROUBLESHOOTING

### Problema: "Canal sem vídeo disponível"
**Solução:**
- Verificar planilha do canal
- Confirmar que tem vídeos com status="done"
- Verificar colunas K e L (devem estar vazias)

### Problema: "Quota exceeded"
**Solução:**
- Normal se muitos uploads simultâneos
- Sistema fará retry automático
- Verificar quota no Google Cloud Console

### Problema: "Invalid credentials"
**Solução:**
- Token OAuth expirou
- Re-autorizar canal com wizard
- Verificar Client ID/Secret

### Problema: Dashboard não carrega
**Solução:**
```bash
# Verificar se está rodando
python dashboard_daily_uploads.py

# Verificar porta 5002
netstat -an | findstr 5002
```

---

## 💡 DICAS

### Para máxima eficiência:
1. **Sempre configure canais monetizados** com is_monetized=true
2. **Mantenha planilhas organizadas** - vídeos prontos no topo
3. **Use o dashboard** para monitorar em tempo real
4. **Teste com poucos canais** antes de escalar

### Botões importantes do Dashboard:
- **[🔄 Forçar Agora]** - Executa fora do horário
- **[🔁 Retry Erros]** - Reprocessa todos com erro
- **[🛑 Parar Tudo]** - Emergência

---

## 📈 PRÓXIMAS MELHORIAS (Roadmap)

- [ ] Notificações via Telegram/Discord
- [ ] Suporte a múltiplos vídeos por canal (configurável)
- [ ] Priorização por performance do vídeo anterior
- [ ] Auto-detecção de melhor horário de upload
- [ ] Integração com sistema de thumbnails

---

## 📞 SUPORTE

Se encontrar problemas:
1. Verifique os logs no terminal
2. Consulte o dashboard (localhost:5002)
3. Execute o teste: `python test_daily_upload.py`
4. Verifique as tabelas no Supabase

---

**Desenvolvido em:** 02/02/2025
**Versão:** 1.0.0
**Status:** ✅ Pronto para produção
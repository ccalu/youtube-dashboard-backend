# COMANDOS RAPIDOS - SISTEMA DE UPLOAD

## DASHBOARD

### Acessar Dashboard v2 (Online - Principal)
```
# Acesso direto pelo navegador (nao precisa rodar nada local)
https://youtube-dashboard-backend-production.up.railway.app/dash-upload
```

### Iniciar Dashboard Local (Legado)
```bash
# Dashboard v1 (porta 5006)
python dash_upload_final.py

# Acessar no navegador
http://localhost:5006
```

### Parar Dashboard Local
```
Ctrl + C (no terminal)
```

---

## UPLOAD MANUAL

### Upload Individual
```bash
# Upload de um canal especifico
python forcar_upload_manual_fixed.py --canal "Nome do Canal"

# Exemplos reais
python forcar_upload_manual_fixed.py --canal "Grandes Mansoes"
```

### Upload em Massa
```bash
# Todos os canais
python forcar_upload_manual_fixed.py --todos

# Apenas monetizados
python daily_uploader.py --apenas-monetizados
```

---

## VERIFICACOES

### Status do Sistema
```bash
# Verificar tokens OAuth
python check_oauth_definitivo.py

# Testar API do dashboard v2 (Railway)
curl https://youtube-dashboard-backend-production.up.railway.app/api/dash-upload/status

# Testar API do dashboard local (v1)
curl http://localhost:5006/api/status
```

---

## CORRECOES

### Problemas com Token OAuth
```bash
# Verificar todos os tokens
python check_oauth_definitivo.py

# Refazer OAuth de um canal (wizard interativo)
python add_canal_wizard_v3.py
```

---

## BANCO DE DADOS

### Queries Uteis (Supabase)
```sql
-- Uploads de hoje
SELECT * FROM yt_canal_upload_diario
WHERE data = CURRENT_DATE
ORDER BY hora_processamento DESC;

-- Canais com erro
SELECT * FROM yt_canal_upload_diario
WHERE data = CURRENT_DATE
AND status = 'erro';

-- Historico completo de um canal
SELECT * FROM yt_canal_upload_historico
WHERE channel_id = 'UC...'
ORDER BY data DESC, hora_processamento DESC;
```

---

## EMERGENCIAS

### Dashboard v2 (Railway) Nao Abre
```bash
# Verificar se Railway esta no ar
curl https://youtube-dashboard-backend-production.up.railway.app/health

# Se nao responder, verificar Railway dashboard em railway.app
```

### Dashboard Local (v1) Nao Abre
```bash
# Verificar se porta esta em uso
netstat -ano | findstr :5006

# Matar processo na porta
taskkill /F /PID [PID_DO_PROCESSO]

# Reiniciar
python dash_upload_final.py
```

### Matar Todos os Python
```bash
tasklist | findstr python
taskkill /F /PID [PID]
```

---

## DEPLOY (Railway)

### Deploy Manual
```bash
git add .
git commit -m "Update: descricao"
git push origin main
# Railway faz deploy automatico apos push
```

---

## ALIASES UTEIS (PowerShell)
```powershell
# Adicionar ao perfil do PowerShell ($PROFILE)
function dash { python dash_upload_final.py }
function upload-canal { param($nome) python forcar_upload_manual_fixed.py --canal $nome }
```

---

*Ultima atualizacao: 13/02/2026*

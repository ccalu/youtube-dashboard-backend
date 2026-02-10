# 🚀 COMANDOS RÁPIDOS - SISTEMA DE UPLOAD

## 🖥️ DASHBOARD

### Iniciar Dashboard
```bash
# Dashboard principal (porta 5006)
python dashboard_teste_5006.py

# Acessar no navegador
http://localhost:5006
```

### Parar Dashboard
```
Ctrl + C (no terminal)
```

---

## 📤 UPLOAD MANUAL

### Upload Individual
```bash
# Upload de um canal específico
python forcar_upload_manual.py --canal "Nome do Canal"

# Exemplos reais
python forcar_upload_manual.py --canal "Grandes Mansões"
python forcar_upload_manual.py --canal "الممالك المظلمة"
```

### Upload em Massa
```bash
# Todos os canais
python forcar_upload_manual.py --todos

# Apenas monetizados
python daily_uploader.py --apenas-monetizados

# Apenas desmonetizados
python daily_uploader.py --apenas-desmonetizados
```

---

## ✅ VERIFICAÇÕES

### Status do Sistema
```bash
# Verificar uploads de hoje
python verificar_uploads_hoje.py

# Verificar tokens OAuth
python check_oauth_definitivo.py

# Testar conexão Supabase
python test_supabase.py
```

### Verificar Canal Específico
```bash
# Status de um canal
python verificar_canal_status.py --canal "Nome do Canal"

# Histórico de uploads
python historico_uploads.py --canal "Nome do Canal" --dias 7
```

---

## 🔧 CORREÇÕES

### Problemas com Token OAuth
```bash
# Verificar todos os tokens
python check_oauth_definitivo.py

# Refazer OAuth de um canal (wizard interativo)
python add_canal_wizard_v3.py
```

### Atualizar Status Manualmente
```bash
# Marcar upload como sucesso
python atualizar_status_manual.py --canal "Nome do Canal" --status sucesso

# Marcar como erro
python atualizar_status_manual.py --canal "Nome do Canal" --status erro
```

### Limpar Uploads com Erro
```bash
# Retry em todos com erro
python retry_uploads_erro.py

# Limpar fila de upload
python limpar_fila_upload.py
```

---

## 📊 RELATÓRIOS

### Gerar Relatórios
```bash
# Relatório do dia
python relatorio_uploads_hoje.py

# Relatório semanal
python relatorio_semanal.py

# Exportar para CSV
python exportar_uploads.py --formato csv --dias 30
```

---

## 🗄️ BANCO DE DADOS

### Queries Úteis (Supabase)
```sql
-- Uploads de hoje
SELECT * FROM yt_canal_upload_diario
WHERE data = CURRENT_DATE
ORDER BY upload_time DESC;

-- Canais com erro
SELECT * FROM yt_canal_upload_diario
WHERE data = CURRENT_DATE
AND status = 'erro';

-- Estatísticas por subnicho
SELECT
    cm.subnicho,
    COUNT(*) as total,
    SUM(CASE WHEN ud.status = 'sucesso' THEN 1 ELSE 0 END) as sucessos
FROM canais_monitorados cm
LEFT JOIN yt_canal_upload_diario ud ON cm.nome_canal = ud.channel_name
WHERE ud.data = CURRENT_DATE
GROUP BY cm.subnicho;
```

---

## 🆘 EMERGÊNCIAS

### Dashboard Não Abre
```bash
# Verificar se porta está em uso
netstat -ano | findstr :5006

# Matar processo na porta
taskkill /F /PID [PID_DO_PROCESSO]

# Reiniciar
python dashboard_teste_5006.py
```

### Upload Travado
```bash
# Parar todos os uploads
Ctrl + C

# Limpar fila
python limpar_fila_upload.py

# Reiniciar com canal específico
python forcar_upload_manual.py --canal "Nome do Canal"
```

### Banco Não Responde
```bash
# Testar conexão
python test_supabase.py

# Verificar credenciais
echo %SUPABASE_URL%
echo %SUPABASE_SERVICE_ROLE_KEY%
```

---

## 📝 LOGS

### Ver Logs
```bash
# Logs de hoje
type upload_logs\2026-02-10_upload.log

# Últimas 50 linhas
powershell -command "Get-Content upload_logs\2026-02-10_upload.log -Tail 50"

# Buscar erros
findstr /i "error" upload_logs\2026-02-10_upload.log
```

---

## 🔄 PROCESSOS EM BACKGROUND

### Ver Processos Rodando
```bash
# Ver processos Python
tasklist | findstr python

# Ver detalhado
wmic process where "name='python.exe'" get ProcessId,CommandLine
```

### Matar Processos
```bash
# Matar por PID
taskkill /F /PID 1234

# Matar todos os Python
taskkill /F /IM python.exe
```

---

## 🚦 DEPLOY (Railway)

### Deploy Manual
```bash
# Commit e push
git add .
git commit -m "Update: descrição"
git push origin main

# Railway faz deploy automático após push
```

### Ver Logs Railway
```
1. Acessar Railway Dashboard
2. Selecionar projeto
3. Aba "Deployments"
4. Clicar no deploy atual
5. Ver logs em tempo real
```

---

## 💡 DICAS

### Aliases Úteis (PowerShell)
```powershell
# Adicionar ao perfil do PowerShell
notepad $PROFILE

# Adicionar estas linhas:
function dash { python dashboard_teste_5006.py }
function upload-todos { python forcar_upload_manual.py --todos }
function upload-canal { param($nome) python forcar_upload_manual.py --canal $nome }
function ver-hoje { python verificar_uploads_hoje.py }
```

### Uso dos Aliases
```powershell
dash                        # Inicia dashboard
upload-todos               # Upload de todos
upload-canal "Grandes Mansões"  # Upload específico
ver-hoje                   # Ver uploads de hoje
```

---

*Referência rápida criada para uso diário do sistema*
*Mantenha este arquivo aberto para consulta rápida*
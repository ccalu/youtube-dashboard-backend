# 🚀 Dashboard Upload Launcher - Guia de Uso

## Resumo
Launcher universal que inicia automaticamente o Dashboard de Upload (Flask) e o Backend API (FastAPI) com um único comando. Compatível com Windows, macOS e Linux.

## 📋 Arquivo Principal
`start_dashboard_completo.py`

## 🎯 Como Usar

### Windows (PowerShell/CMD):
```powershell
python start_dashboard_completo.py
```

### macOS/Linux (Terminal):
```bash
python3 start_dashboard_completo.py
# ou
python start_dashboard_completo.py
```

## ✨ Funcionalidades

1. **Inicialização Automática:**
   - Inicia Backend FastAPI na porta 8000
   - Aguarda backend estar pronto
   - Inicia Dashboard Flask na porta 5006
   - Abre navegador automaticamente

2. **Detecção de Conflitos:**
   - Verifica se as portas estão em uso
   - Tenta liberar portas automaticamente
   - Mostra mensagens claras de status

3. **Monitoramento Contínuo:**
   - Detecta se algum processo cai
   - Mostra logs em tempo real
   - Filtra logs desnecessários

4. **Shutdown Limpo:**
   - Ctrl+C encerra ambos os processos
   - Fecha portas corretamente
   - Sem processos órfãos

## 📍 URLs Disponíveis

Após iniciar:
- **Backend API:** http://localhost:8000
- **Dashboard:** http://localhost:5006

## 🔧 Solução de Problemas

### Porta 8000 já em uso:
```powershell
# Windows - Matar processo na porta 8000
netstat -aon | findstr :8000
taskkill /F /PID [PID_DO_PROCESSO]

# Mac/Linux
lsof -i :8000
kill -9 [PID_DO_PROCESSO]
```

### Porta 5006 já em uso:
```powershell
# Windows
netstat -aon | findstr :5006
taskkill /F /PID [PID_DO_PROCESSO]

# Mac/Linux
lsof -i :5006
kill -9 [PID_DO_PROCESSO]
```

### Erro de encoding (Windows):
O launcher já configura UTF-8 automaticamente, mas se houver problemas:
```powershell
chcp 65001
set PYTHONIOENCODING=utf-8
python start_dashboard_completo.py
```

## 🎯 Alternativas de Uso

### Opção 1: Launcher Unificado (Recomendado)
```bash
python start_dashboard_completo.py
```
- ✅ Um comando apenas
- ✅ Gerenciamento automático
- ✅ Logs unificados

### Opção 2: Iniciar Manualmente (Debug)
```bash
# Terminal 1 - Backend
python main.py

# Terminal 2 - Dashboard
python dash_upload_final.py
```
- ✅ Controle individual
- ✅ Logs separados
- ❌ Mais trabalhoso

### Opção 3: Dashboard Apontando para Railway
Editar `dash_upload_final.py` linha 390:
```javascript
// DE:
const response = await fetch('http://localhost:8000/api/yt-upload/force/' + channelId

// PARA:
const response = await fetch('https://youtube-dashboard-backend-production.up.railway.app/api/yt-upload/force/' + channelId
```
- ✅ Backend sempre online
- ✅ Não precisa rodar backend local
- ❌ Logs ficam no Railway

## 📊 Status do Sistema

Quando tudo estiver rodando corretamente:
```
======================================================================
✅ SISTEMA COMPLETO RODANDO!
======================================================================
📍 URLs DISPONÍVEIS:
   🔧 Backend API:  http://localhost:8000
   📊 Dashboard:    http://localhost:5006

📍 STATUS:
   ✅ Botão de upload forçado funcional
   ✅ Histórico de uploads disponível
   ✅ Sistema pronto para uso!
======================================================================
```

## 🔄 Processo de Upload Forçado

1. Abrir dashboard: http://localhost:5006
2. Clicar no botão 📤 em qualquer canal
3. Confirmar upload
4. Sistema automaticamente:
   - Busca próximo vídeo "done" na planilha
   - Faz download do Google Drive
   - Upload para YouTube
   - Atualiza planilha
   - Registra no histórico

## 🛠️ Requisitos

- Python 3.7+
- Dependências instaladas (`pip install -r requirements.txt`)
- Arquivo `.env` configurado com:
  - SUPABASE_URL
  - SUPABASE_SERVICE_ROLE_KEY
  - GOOGLE_SHEETS_CREDENTIALS_2

## 📝 Logs

Os logs são exibidos em tempo real no terminal:
- `[Backend]` - Logs do FastAPI
- `[Dashboard]` - Logs do Flask

Logs filtrados automaticamente:
- Requisições estáticas (/static, /favicon.ico)
- Status checks frequentes (/api/status)

## ✅ Testado Em

- Windows 10/11 (PowerShell)
- macOS (Terminal.app, iTerm2)
- Linux Ubuntu/Debian

## 📌 Observações Importantes

1. **OAuth Tokens:** Armazenados no Supabase, acessíveis tanto local quanto Railway
2. **Google Sheets:** Credenciais devem estar no `.env` local
3. **YouTube API Keys:** Não necessárias para upload (usa OAuth)
4. **Histórico:** Nova tabela `yt_canal_upload_historico` preserva múltiplos uploads/dia

## 🆘 Suporte

Se encontrar problemas:
1. Verificar se as portas estão livres
2. Confirmar que `.env` está configurado
3. Testar iniciar manualmente primeiro
4. Verificar logs de erro no terminal

---

**Última atualização:** 10/02/2026
**Autor:** Claude
**Versão:** 1.0.0
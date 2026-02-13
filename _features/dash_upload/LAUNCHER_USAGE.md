# Dashboard Upload - Guia de Uso

## Resumo
O Dashboard de Upload tem 2 versoes:
1. **v2 (Railway)** - Acesso online, integrado no main.py (PRINCIPAL)
2. **v1 (Local)** - Flask na porta 5006 + launcher (LEGADO)

---

## OPCAO 1: Dashboard v2 Online (Recomendado)

### Acesso
Nao precisa rodar nada local. Basta acessar:
```
https://youtube-dashboard-backend-production.up.railway.app/dash-upload
```

### Vantagens
- Acessa de qualquer lugar (celular, outro PC, socio)
- Sempre atualizado (deploy automatico)
- Sem necessidade de Python/terminal local

---

## OPCAO 2: Dashboard Local + Launcher (Legado)

### Arquivo Principal
`start_dashboard_completo.py`

### Windows (PowerShell/CMD):
```powershell
python start_dashboard_completo.py
```

### macOS/Linux (Terminal):
```bash
python3 start_dashboard_completo.py
```

### Funcionalidades do Launcher
1. **Inicializacao Automatica:**
   - Inicia Backend FastAPI na porta 8000
   - Aguarda backend estar pronto
   - Inicia Dashboard Flask na porta 5006
   - Abre navegador automaticamente

2. **Deteccao de Conflitos:**
   - Verifica se as portas estao em uso
   - Tenta liberar portas automaticamente

3. **Monitoramento Continuo:**
   - Detecta se algum processo cai
   - Mostra logs em tempo real

4. **Shutdown Limpo:**
   - Ctrl+C encerra ambos os processos
   - Fecha portas corretamente

### URLs Locais
- **Backend API:** http://localhost:8000
- **Dashboard v2 (via backend local):** http://localhost:8000/dash-upload
- **Dashboard v1 (Flask):** http://localhost:5006

### Alternativa: Iniciar Manualmente (Debug)
```bash
# Terminal 1 - Backend
python main.py

# Terminal 2 - Dashboard v1 (opcional)
python dash_upload_final.py
```

## Requisitos

- Python 3.7+
- Dependencias instaladas (`pip install -r requirements.txt`)
- Arquivo `.env` configurado com:
  - SUPABASE_URL
  - SUPABASE_SERVICE_ROLE_KEY
  - GOOGLE_SHEETS_CREDENTIALS_2

## Observacoes Importantes

1. **OAuth Tokens:** Armazenados no Supabase, acessiveis tanto local quanto Railway
2. **Google Sheets:** Credenciais devem estar no `.env` local
3. **YouTube API Keys:** Nao necessarias para upload (usa OAuth)
4. **Historico:** Tabela `yt_canal_upload_historico` preserva multiplos uploads/dia

---

**Ultima atualizacao:** 13/02/2026

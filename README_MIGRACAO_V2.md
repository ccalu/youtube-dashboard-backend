# 🚀 MIGRAÇÃO PARA ARQUITETURA V2.0

## 📋 RESUMO DA MUDANÇA

### **ANTES (V1.0):**
```
1 proxy = 1 Client ID/Secret = 4 canais
```

### **DEPOIS (V2.0):**
```
1 canal = 1 Client ID/Secret único
```

---

## ✅ POR QUE MIGRAR?

### **1. Isolamento total**
- 1 canal suspenso = 0 impacto nos outros
- YouTube não consegue conectar canais

### **2. Contingência máxima**
- Se 1 projeto cair → 1 canal offline
- V1.0: 1 projeto cair → 4 canais offline

### **3. Segurança**
- Credenciais isoladas por canal
- Tokens OAuth únicos
- Impossível cruzamento de dados

---

## ⚠️ IMPACTO: NENHUM!

**Sans Limites continua funcionando 100%:**
- ✅ Código tem fallback automático
- ✅ Tokens OAuth já existem
- ✅ Upload não será afetado

---

## 📝 PASSO A PASSO (15 minutos)

### **FASE 1: Executar Migration SQL** ⏱️ 5 min

**1. Abrir Supabase:**
- URL: https://supabase.com/dashboard
- Projeto: youtube-dashboard

**2. Ir em SQL Editor:**
- Menu lateral → SQL Editor
- Clicar "New Query"

**3. Copiar migration:**
- Arquivo: `migrations/add_channel_credentials.sql`
- Colar TODO o conteúdo no editor

**4. Executar:**
- Clicar "Run" (ou Ctrl+Enter)

**5. Validar output:**
```
[OK] Tabela yt_channel_credentials criada com sucesso
[OK] Foreign key configurada corretamente
[OK] Índice criado com sucesso
[OK] Credenciais do Sans Limites migradas com sucesso
[OK] Total de credenciais: 1
```

**Se aparecer "Total: 0" → OK** (Sans Limites será migrado depois)

---

### **FASE 2: Deploy Código** ⏱️ 5 min

**Automático via GitHub → Railway:**
- Commit já foi feito
- Railway deployou automaticamente
- Verificar logs: https://railway.app

**Validar logs Railway:**
```
[channel_id] ✅ Usando credenciais isoladas do canal
```

**OU (fallback Sans Limites):**
```
[channel_id] ⚠️ Usando credenciais do proxy (DEPRECATED)
```

---

### **FASE 3: Migrar Sans Limites** ⏱️ 5 min (OPCIONAL)

**Se migration automática falhou:**

**1. Buscar credenciais atuais:**
```sql
SELECT client_id, client_secret
FROM yt_proxy_credentials
WHERE proxy_name = 'proxy_c0000_1';
```

**2. Inserir em yt_channel_credentials:**
```sql
INSERT INTO yt_channel_credentials (channel_id, client_id, client_secret)
VALUES (
  'UCbB1WtTqBWYdSk3JE6iRNRw',
  'COPIAR_CLIENT_ID_AQUI',
  'COPIAR_CLIENT_SECRET_AQUI'
)
ON CONFLICT (channel_id) DO NOTHING;
```

**3. Validar:**
```sql
SELECT * FROM yt_channel_credentials
WHERE channel_id = 'UCbB1WtTqBWYdSk3JE6iRNRw';
```

**Deve retornar 1 linha.**

---

## 🧪 VALIDAÇÃO COMPLETA

### **1. Testar upload Sans Limites:**
- Adicionar linha teste na planilha
- Marcar J="done"
- Verificar logs Railway

**Log esperado:**
```
[UCbB1WtTqBWYdSk3JE6iRNRw] ✅ Usando credenciais isoladas do canal
[UCbB1WtTqBWYdSk3JE6iRNRw] 🔑 Token ainda válido
[UCbB1WtTqBWYdSk3JE6iRNRw] ✅ Upload completo
```

**Se aparecer warning DEPRECATED → OK** (sistema funcionando, só não migrou)

---

### **2. Adicionar novo canal:**

**Rodar wizard atualizado:**
```bash
python add_canal_wizard.py
```

**Wizard V2.0 vai pedir:**
```
[1/5] DADOS DO CANAL
- Channel ID
- Nome do canal
- Língua (seleção numérica)
- Subnicho (seleção numérica)
- Playlist ID (opcional)

[2/5] CREDENCIAIS GOOGLE CLOUD
- Client ID (do projeto Google Cloud ÚNICO desse canal)
- Client Secret

[3/5] IDENTIFICAÇÃO DO PROXY
- Proxy name (ex: proxy_c0008_1)

[4/5] ADICIONANDO NO SUPABASE
- Salva canal
- Salva credenciais OAuth isoladas

[5/5] AUTORIZACAO OAUTH
- Gera URL
- Você autoriza no navegador do proxy
- Cola código
- Wizard salva tokens
```

---

## 📊 ESTRUTURA FINAL

### **Tabelas Supabase:**

**`yt_channels`:** (8 canais)
```
channel_id | channel_name | proxy_name    | lingua | subnicho
UC...Rw    | Sans Limites | proxy_c0000_1 | fr     | mentalidade_...
UC...new1  | Novo Canal 1 | proxy_c0008_1 | pt     | dark_history
UC...new2  | Novo Canal 2 | proxy_c0008_1 | es     | war_stories
...
```

**`yt_channel_credentials`:** (NOVA - credenciais isoladas)
```
channel_id | client_id                              | client_secret
UC...Rw    | 123-abc.apps.googleusercontent.com    | GOCSPX-xxx
UC...new1  | 456-def.apps.googleusercontent.com    | GOCSPX-yyy
UC...new2  | 789-ghi.apps.googleusercontent.com    | GOCSPX-zzz
```

**`yt_proxy_credentials`:** (DEPRECATED - manter para fallback)
```
proxy_name     | client_id                           | client_secret
proxy_c0000_1  | 123-abc.apps.googleusercontent.com | GOCSPX-xxx
proxy_c0003_1  | ...                                 | ...
```

**`yt_oauth_tokens`:** (tokens únicos por canal)
```
channel_id | access_token | refresh_token | token_expiry
UC...Rw    | ya29....     | 1//0...       | 2025-12-22 12:00
UC...new1  | ya29....     | 1//0...       | 2025-12-22 13:00
```

---

## 🔄 WORKFLOW COMPLETO

### **Para cada novo canal:**

**1. Google Cloud Console** (navegador do proxy)
- Criar projeto único: `canal-dark-history-c0008-1`
- Ativar YouTube Data API v3
- Criar OAuth Client ID (Desktop app)
- Copiar Client ID + Secret

**2. Wizard Python** (seu PC)
```bash
python add_canal_wizard.py
```
- Informar dados do canal
- Colar Client ID/Secret ÚNICO
- Informar proxy_name
- Autorizar OAuth (navegador do proxy)

**3. Planilha Google Sheets**
- Criar/copiar planilha
- Configurar aba Config
- Adicionar Apps Script

**4. Testar**
- Adicionar linha teste
- Verificar logs Railway
- Verificar YouTube Studio

---

## ⚡ ROLLBACK (se necessário)

**Se algo der errado:**

**1. Remover tabela:**
```sql
DROP TABLE IF EXISTS yt_channel_credentials CASCADE;
```

**2. Git revert:**
```bash
git revert HEAD
git push origin main
```

**3. Railway redeploy:**
- Deploy automático do commit anterior

---

## 📞 TROUBLESHOOTING

### **Erro: "Canal sem credenciais"**

**Causa:** Canal não tem credenciais em `yt_channel_credentials` nem `yt_proxy_credentials`

**Solução:**
```sql
-- Verificar se existe em alguma tabela
SELECT * FROM yt_channel_credentials WHERE channel_id = 'UCxxx...';
SELECT * FROM yt_proxy_credentials WHERE proxy_name = 'proxy_c0000_1';

-- Se não existir: usar wizard para adicionar
python add_canal_wizard.py
```

---

### **Erro: "Foreign key constraint"**

**Causa:** Tentou inserir credenciais de canal que não existe em `yt_channels`

**Solução:**
```sql
-- Primeiro adicionar canal em yt_channels
INSERT INTO yt_channels (...) VALUES (...);

-- Depois adicionar credenciais
INSERT INTO yt_channel_credentials (...) VALUES (...);
```

---

### **Warning: "Usando credenciais do proxy (DEPRECATED)"**

**Causa:** Canal está usando fallback (credenciais de `yt_proxy_credentials`)

**Solução (OPCIONAL):**
```sql
-- Migrar para credenciais isoladas
INSERT INTO yt_channel_credentials (channel_id, client_id, client_secret)
SELECT
  'CHANNEL_ID_AQUI',
  client_id,
  client_secret
FROM yt_proxy_credentials
WHERE proxy_name = 'proxy_c0000_1';
```

**Ou deixar como está** - sistema funciona perfeitamente com fallback.

---

## ✅ CHECKLIST FINAL

- [ ] Migration SQL executada com sucesso
- [ ] Railway deployou código novo
- [ ] Sans Limites testado (upload funciona)
- [ ] Logs Railway mostram credenciais isoladas OU fallback
- [ ] Novo canal adicionado via wizard V2.0 (opcional)
- [ ] Novo canal testado (upload funciona)

---

## 🎯 PRÓXIMOS PASSOS

**Depois da migração:**

1. **Adicionar 51 canais restantes** usando wizard V2.0
2. **Cada canal com projeto Google Cloud próprio**
3. **Isolamento total garantido**
4. **Contingência máxima estabelecida**

---

**Criado por:** Claude Code
**Data:** 22/12/2024
**Versão:** 2.0 (Arquitetura isolada por canal)

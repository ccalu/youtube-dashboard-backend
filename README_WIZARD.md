# 🧙 Guia: Usar Wizards OAuth em Qualquer PC

Sistema de wizards para adicionar canais YouTube ao sistema de upload automatizado.

---

## 📋 Pré-requisitos

1. **Python 3.8+** instalado
2. **Git** instalado (opcional - se quiser clonar repositório)
3. **Credenciais Supabase** (URL + Key)

---

## ⚙️ Setup Inicial (5 minutos)

### **1. Obter o código**

**Opção A: Clonar repositório**
```bash
git clone https://github.com/ccalu/youtube-dashboard-backend.git
cd youtube-dashboard-backend
```

**Opção B: Copiar arquivos manualmente**
- Copiar pasta `youtube-dashboard-backend` para o PC
- Abrir terminal nessa pasta

### **2. Instalar dependências**

```bash
pip install -r requirements.txt
```

**Se der erro "externally-managed-environment" (Linux/Mac):**
```bash
pip install --break-system-packages supabase requests python-dotenv
```

### **3. Criar arquivo de configuração (.env)**

Criar arquivo `.env` na raiz da pasta com:

```env
SUPABASE_URL=https://prvkmzstyedepvlbppyo.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Onde pegar as credenciais:**
1. Abrir Supabase no navegador
2. Ir em **Settings** → **API**
3. Copiar:
   - **Project URL** → `SUPABASE_URL`
   - **anon public** key → `SUPABASE_KEY`

### **4. Testar conexão**

```bash
python validate_before_migration.py
```

**Deve mostrar:**
```
[OK] Total de canais: 8
[OK] Sans Limites configurado corretamente
[OK] 5 proxies cadastrados
```

Se aparecer erros de conexão, verificar:
- Arquivo `.env` está na raiz da pasta
- Credenciais estão corretas
- Internet está conectada

---

## 🎯 Usar os Wizards

### **Wizard 1: Setup Proxy Completo (proxy + 4 canais)**

**Quando usar:** Adicionar novo proxy com 4 canais de uma vez

**Comando:**
```bash
python setup_novo_proxy.py
```

**O que ele faz:**
1. Pede credenciais do proxy (proxy_name, client_id, client_secret)
2. Salva proxy no Supabase (`yt_proxy_credentials`)
3. Pede dados de 1-4 canais (channel_id, nome, língua, subnicho, playlist)
4. Salva canais no Supabase (`yt_channels`)
5. Para cada canal:
   - Gera URL de autorização OAuth
   - Você abre URL no navegador do proxy
   - Autoriza acesso
   - Copia código
   - Cola no wizard
   - Wizard troca código por tokens
   - Salva tokens no Supabase (`yt_oauth_tokens`)
6. Valida todos os tokens
7. Mostra relatório final

**Exemplo de uso:**
```
Nome do proxy: proxy_c0009_1
Client ID: 123456789-abc...apps.googleusercontent.com
Client Secret: GOCSPX-xxx...

Quantos canais adicionar? 4

--- CANAL 1/4 ---
Channel ID: UCxxxxxxxxxxxxxxxxxxxxxx
Nome do canal: Dark History PT
Lingua: pt
Subnicho: dark_history
Playlist ID: PLxxxxxxxxxxxxxxxxxxxxxx

[OK] Canal adicionado!

Abra esta URL no navegador do proxy:
https://accounts.google.com/o/oauth2/v2/auth?client_id=...

Cole o código de autorização: 4/0AeanS...

[OK] Token salvo com sucesso!
[OK] Token validado!

... (repete para canais 2, 3, 4)

[SUCESSO] Todos os 4 canais estão prontos para upload!
```

---

### **Wizard 2: Adicionar 1 Canal em Proxy Existente**

**Quando usar:** Adicionar canal avulso em proxy que já existe

**Comando:**
```bash
python add_canal_wizard.py
```

**O que ele faz:**
1. Lista proxies existentes no Supabase
2. Você escolhe qual proxy usar
3. Pede dados do canal
4. Salva canal no Supabase
5. OAuth completo (igual wizard 1)

**Exemplo de uso:**
```
[OK] 5 proxies encontrados:

[1] proxy_c0000_1 (3 canais)
[2] proxy_c0003_1 (1 canal)
[3] proxy_c0005_1 (2 canais)
[4] proxy_c0005_2 (1 canal)
[5] proxy_c0008_1 (1 canal)

Escolha o proxy (1-5): 2

[OK] Proxy selecionado: proxy_c0003_1

Channel ID: UCyyyyyyyyyyyyyyyyyyyyyy
Nome do canal: New Channel Name
Lingua: es
Subnicho: war_stories
Playlist ID: PLyyyyyyyyyyyyyyyyyyyyyy

[OK] Canal adicionado ao proxy_c0003_1!

Abra esta URL no navegador do proxy:
https://accounts.google.com/o/oauth2/v2/auth?client_id=...

Cole o código de autorização: 4/0Aean...

[OK] Token salvo e validado!
[SUCESSO] Canal pronto para upload!
```

---

## 🔧 Troubleshooting

### **Erro: "Module not found: supabase"**

**Solução:**
```bash
pip install supabase requests python-dotenv
```

### **Erro: "SUPABASE_URL not found"**

**Causa:** Arquivo `.env` não foi criado ou está em local errado

**Solução:**
1. Verificar que arquivo `.env` existe na raiz da pasta
2. Abrir arquivo e verificar que tem `SUPABASE_URL=...` e `SUPABASE_KEY=...`
3. Rodar wizard novamente

### **Erro: "Supabase connection failed"**

**Causas possíveis:**
- Internet desconectada
- Credenciais incorretas no `.env`
- Firewall bloqueando conexão

**Solução:**
1. Testar internet: `ping google.com`
2. Verificar credenciais no `.env`
3. Testar conexão: `python validate_before_migration.py`

### **Erro: "Proxy já existe"**

**Causa:** Tentou criar proxy com nome que já existe

**Solução:**
- Wizard pergunta se quer usar o existente
- Escolher "sim" para usar as credenciais já cadastradas
- Ou escolher "não" e usar nome diferente (ex: `proxy_c0009_2`)

### **Erro: "Canal já existe"**

**Causa:** Canal com esse `channel_id` já está no banco

**Solução:**
- Verificar se canal realmente existe: rodar `validate_before_migration.py`
- Se existe e quer atualizar: deletar do Supabase manualmente primeiro
- Se erro: usar `channel_id` diferente

### **Erro: "Token inválido" após autorização**

**Causas possíveis:**
- Código OAuth copiado incorretamente
- Código expirou (válido por 10 minutos)
- Client ID/Secret incorretos

**Solução:**
1. Gerar nova URL (wizard gera automaticamente)
2. Copiar código completo (4/0Aean...)
3. Colar imediatamente no wizard
4. Se persistir: verificar Client ID/Secret do proxy no Google Cloud Console

---

## 📝 Notas Importantes

### **Wizards são ferramentas locais**
- Salvam dados **direto no Supabase** (banco de dados)
- **NÃO precisa commit** no Git após usar
- Pode usar em qualquer PC com Python + `.env`

### **OAuth é por canal**
- Cada canal precisa autorizar individualmente
- Tokens ficam salvos no Supabase (`yt_oauth_tokens`)
- Railway renova automaticamente quando expiram

### **Segurança**
- **NUNCA commitar arquivo `.env`** no Git (contém credenciais)
- Arquivo `.env` está em `.gitignore` (protegido)
- Credenciais no Supabase são criptografadas

### **Múltiplos PCs**
- Pode copiar repositório + `.env` para vários PCs
- Todos os PCs acessam MESMO banco Supabase
- Não há conflito - wizards salvam direto no banco

---

## 🎯 Workflow Completo

**Para adicionar novos canais ao sistema:**

1. **Criar projeto Google Cloud** (no proxy)
   - Ativar YouTube Data API v3
   - Criar credenciais OAuth 2.0
   - Configurar redirect_uri: `urn:ietf:wg:oauth:2.0:oob`
   - Anotar Client ID e Client Secret

2. **Rodar wizard** (neste PC)
   ```bash
   python setup_novo_proxy.py
   ```

3. **Autorizar canais** (no proxy)
   - Abrir URLs geradas pelo wizard
   - Login com conta Google do canal
   - Autorizar acesso
   - Copiar código

4. **Validar**
   - Wizard testa tokens automaticamente
   - Verificar relatório final: todos ✅

5. **Testar upload**
   - Adicionar vídeo teste na planilha Google Sheets
   - Marcar J="done"
   - Verificar logs Railway
   - Verificar vídeo no YouTube Studio (rascunho)

---

## 📞 Suporte

**Se tiver problemas:**
1. Rodar `validate_before_migration.py` e enviar output
2. Verificar logs de erro completos
3. Verificar credenciais `.env`
4. Verificar conexão Supabase

**Documentação adicional:**
- Sistema de upload: Ver documentação no repositório
- Google OAuth: https://developers.google.com/identity/protocols/oauth2
- Supabase: https://supabase.com/docs

---

**Criado por:** Claude Code
**Data:** 22/12/2024
**Versão:** 1.0

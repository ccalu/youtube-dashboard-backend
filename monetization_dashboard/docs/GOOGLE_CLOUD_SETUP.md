# Google Cloud Console - Setup para Novo Proxy

## Passo a Passo Completo

### 1. Abrir o Proxy

1. Abre o **AdsPower**
2. Inicia o perfil do proxy que vai configurar
3. Aguarda o navegador abrir

---

### 2. Acessar Google Cloud Console

1. Acessa: https://console.cloud.google.com
2. Faz login com a **conta Google do proxy** (se pedir)

---

### 3. Criar Projeto

1. Clica no **seletor de projeto** (topo da pagina, ao lado do logo Google Cloud)
2. Clica em **"New Project"**
3. Nome do projeto: `Dashboard` (ou qualquer nome)
4. Clica **"Create"**
5. Aguarda criar e seleciona o projeto

---

### 4. Habilitar APIs

1. Menu lateral → **"APIs & Services"** → **"Enable APIs and Services"**
2. Na barra de busca, digita: `YouTube Data API v3`
3. Clica no resultado e clica **"Enable"**
4. Volta e busca: `YouTube Analytics API`
5. Clica no resultado e clica **"Enable"**

**APIs necessarias:**
- YouTube Data API v3
- YouTube Analytics API

---

### 5. Configurar Consent Screen

1. Menu lateral → **"APIs & Services"** → **"OAuth consent screen"**
   (ou "Google Auth Platform" → "Branding")
2. User Type: **External** → Create
3. Preenche:
   - **App name:** Dashboard
   - **User support email:** seleciona o email da conta
   - **Developer contact email:** mesmo email
4. Clica **"Save and Continue"**
5. Scopes: pode pular → **"Save and Continue"**
6. Test users: **Add Users** → adiciona o email da conta → Save
7. **"Save and Continue"** até finalizar

---

### 6. Criar Credenciais OAuth

1. Menu lateral → **"APIs & Services"** → **"Credentials"**
2. Clica **"+ Create Credentials"** → **"OAuth client ID"**
3. Application type: **Desktop app**
4. Name: `Dashboard`
5. Clica **"Create"**

---

### 7. Copiar Credenciais

Vai aparecer um popup com:
- **Client ID:** `123456789-xxxxx.apps.googleusercontent.com`
- **Client Secret:** `GOCSPX-xxxxxx`

**IMPORTANTE:** Copia e salva essas duas informacoes!

---

### 8. Adicionar Test User (se necessario)

Se der erro "Access blocked" ao autorizar:

1. Menu lateral → **"Google Auth Platform"** (ou "OAuth consent screen")
2. Clica em **"Audience"** (ou "Test users")
3. **"Add users"**
4. Adiciona o email da conta Google do proxy
5. Save

---

## Proximos Passos

Depois de ter o Client ID e Client Secret:

1. Manda para o Claude:
   - Client ID
   - Client Secret
   - Nome do proxy
   - Nome(s) do(s) canal(is)

2. Claude gera a URL de OAuth

3. Abre a URL no AdsPower, seleciona a Brand Account (canal)

4. Manda a URL de retorno para o Claude

5. Canal adicionado!

---

## Resumo Visual

```
[AdsPower]
    |
    v
[Google Cloud Console]
    |
    ├── Criar Projeto
    ├── Habilitar APIs (YouTube Data + Analytics)
    ├── Configurar Consent Screen
    ├── Criar OAuth Credentials
    └── Adicionar Test User
    |
    v
[Client ID + Client Secret]
    |
    v
[Claude gera URL OAuth]
    |
    v
[Autorizar no AdsPower]
    |
    v
[Canal adicionado ao Dashboard!]
```

---

## Troubleshooting

### Erro "Access blocked"
- Adicione o email como Test User (passo 8)

### Erro "API not enabled"
- Verifique se habilitou as duas APIs (passo 4)

### Erro "invalid_client"
- Client ID ou Secret incorretos
- Verifique se copiou corretamente

### Erro "redirect_uri_mismatch"
- Na criacao do OAuth, o tipo deve ser "Desktop app"

---

**Ultima atualizacao:** 09/12/2025

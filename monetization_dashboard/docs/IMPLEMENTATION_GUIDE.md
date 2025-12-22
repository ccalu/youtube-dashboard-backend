# Monetization Dashboard - Guia de Implementacao

**Data:** 08/12/2025
**Status:** MVP Funcional
**Canal Teste:** Reis Perversos (UCV9aMsA0swcuExud2tZSlUg)

---

## 1. Objetivo

Criar um dashboard para monitorar metricas de monetizacao de todos os canais do YouTube da empresa, mantendo **segregacao de IP** (cada conta Google acessada apenas pelo seu proxy designado no AdsPower).

---

## 2. Problema Inicial

### 2.1 Restricao de Proxy
O proxy SOCKS5 do AdsPower **bloqueia** `*.googleapis.com` para chamadas programaticas (Python/requests), mas o **navegador dentro do AdsPower** consegue acessar normalmente.

### 2.2 Tentativas Anteriores que Falharam

| Abordagem | Resultado | Motivo |
|-----------|-----------|--------|
| Python + SOCKS5 proxy | ERRO | Proxy bloqueia googleapis.com |
| Service Account | NAO TESTADO | Mesmo problema de proxy |
| Playwright + AdsPower | PARCIAL | Complexo demais, timeouts |
| `flow.run_local_server()` | ERRADO | Abre navegador local, nao no proxy |

---

## 3. Solucao Implementada

### 3.1 Arquitetura Final

```
[AdsPower/Proxy]          [Windows M4 / Railway]         [Supabase]
      |                           |                          |
      | 1. OAuth manual           |                          |
      | (usuario abre URL         |                          |
      |  no navegador do proxy)   |                          |
      |                           |                          |
      | 2. Copia codigo           |                          |
      |    de autorizacao ------->|                          |
      |                           |                          |
      |                           | 3. Troca codigo          |
      |                           |    por tokens            |
      |                           |    (SEM proxy)           |
      |                           |                          |
      |                           | 4. Chama YouTube         |
      |                           |    Analytics API         |
      |                           |    (tokens NAO sao       |
      |                           |     IP-bound)            |
      |                           |                          |
      |                           | 5. Salva metricas ------>|
      |                           |                          |
```

### 3.2 Por Que Funciona

1. **OAuth e feito UMA VEZ** dentro do proxy (navegador AdsPower)
2. **Tokens (access_token/refresh_token) NAO sao vinculados a IP**
3. Depois de obter os tokens, podemos chamar a API de **qualquer lugar** (Railway, GitHub Actions, Windows local)
4. O refresh_token permite renovar o access_token indefinidamente

---

## 4. Descoberta Critica: Brand Accounts

### 4.1 O Problema
Ao autenticar com `jamesjohnson2451@gmail.com`:
- `mine=true` retornava **vazio** (conta Gmail nao tem canal proprio)
- `managedByMe=true` retornava **403 Forbidden**
- API de Analytics retornava **403 Forbidden**

### 4.2 A Solucao
Os canais do YouTube estao em **Brand Accounts** (contas de marca) vinculadas ao Gmail.

**Fluxo correto:**
1. Gerar URL OAuth com `prompt=select_account consent`
2. Usuario abre URL no AdsPower
3. Na tela "Choose an account", **selecionar a Brand Account** (ex: "Reis Perversos"), NAO o Gmail
4. Autorizar o app
5. Copiar codigo da URL de retorno

### 4.3 URL de OAuth Correta

```
https://accounts.google.com/o/oauth2/auth?
  client_id=624181268142-srjb1vjbcd0ticg2fm42sdic9lm3g7cq.apps.googleusercontent.com
  &redirect_uri=http://localhost
  &response_type=code
  &scope=https://www.googleapis.com/auth/youtube.readonly
         https://www.googleapis.com/auth/yt-analytics.readonly
         https://www.googleapis.com/auth/yt-analytics-monetary.readonly
  &access_type=offline
  &prompt=select_account consent
```

---

## 5. Estrutura do Banco de Dados (Supabase)

### 5.1 Tabelas Criadas

```sql
-- Canais
CREATE TABLE yt_channels (
    id SERIAL PRIMARY KEY,
    channel_id TEXT UNIQUE NOT NULL,
    channel_name TEXT,
    proxy_name TEXT,
    is_monetized BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Metricas diarias
CREATE TABLE yt_daily_metrics (
    id SERIAL PRIMARY KEY,
    channel_id TEXT NOT NULL,
    date DATE NOT NULL,
    revenue DECIMAL(10,2),
    views INTEGER,
    rpm DECIMAL(10,4),
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(channel_id, date)
);

-- Tokens OAuth
CREATE TABLE yt_oauth_tokens (
    id SERIAL PRIMARY KEY,
    channel_id TEXT UNIQUE NOT NULL,
    access_token TEXT,
    refresh_token TEXT,
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Logs de coleta
CREATE TABLE yt_collection_logs (
    id SERIAL PRIMARY KEY,
    channel_id TEXT,
    status TEXT,
    message TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 6. Scripts Criados

### 6.1 Arquivos Principais

| Arquivo | Funcao |
|---------|--------|
| `config.py` | Credenciais Supabase e Google OAuth |
| `oauth_brand_account.py` | Gera URL OAuth com prompt de selecao de conta |
| `exchange_and_test.py` | Troca codigo por tokens e testa API |
| `save_metrics_simple.py` | Busca metricas e salva no Supabase |
| `refresh_and_test.py` | Renova token expirado e testa |

### 6.2 Fluxo de Uso

```bash
# 1. Gerar URL OAuth
python oauth_brand_account.py

# 2. Usuario abre URL no AdsPower, autoriza, copia URL de retorno

# 3. Trocar codigo (editar CODE no script)
python exchange_and_test.py

# 4. Salvar metricas
python save_metrics_simple.py
```

---

## 7. Resultados do Canal Teste

### 7.1 Reis Perversos

| Metrica | Valor |
|---------|-------|
| Channel ID | UCV9aMsA0swcuExud2tZSlUg |
| Inscritos | 3,650 |
| Views Nov 2025 | 258,663 |
| Views Dez 1-6 | 183,553 |
| Receita Dez 1-6 | $184.88 |
| RPM medio | $1.01 |
| Melhor dia | 06/12: $78.40 (70k views) |

### 7.2 Observacoes
- Canal foi monetizado em **01/12/2025**
- Crescimento explosivo: 155 views/dia (Nov 1) -> 70,000 views/dia (Dec 6)
- 36 dias de dados historicos salvos no Supabase

---

## 8. Credenciais e Configuracao

### 8.1 Google Cloud Project
- **Project ID:** dash-480401
- **Client ID:** 624181268142-srjb1vjbcd0ticg2fm42sdic9lm3g7cq.apps.googleusercontent.com
- **APIs habilitadas:**
  - YouTube Data API v3
  - YouTube Analytics API v2

### 8.2 Supabase
- **URL:** https://prvkmzstyedepvlbppyo.supabase.co
- **Projeto:** Compartilhado com outros sistemas

### 8.3 AdsPower Profile
- **Profile:** C000.1 - PT - 03 - 04 - 05 - 06
- **Proxy IP:** 92.113.114.92

---

## 9. Proximos Passos

### 9.1 Imediato
- [ ] Fazer OAuth para os outros 3 canais monetizados
- [ ] Criar script de coleta automatica (cron)

### 9.2 Curto Prazo
- [ ] Deploy no Railway ou GitHub Actions
- [ ] Criar dashboard Streamlit

### 9.3 Medio Prazo
- [ ] Alertas de queda de receita
- [ ] Comparativo entre canais
- [ ] Projecoes de receita mensal

---

## 10. Troubleshooting

### 10.1 Token Expirado (401 Unauthorized)
```python
# Usar refresh_token para obter novo access_token
resp = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "refresh_token": refresh_token,
    "grant_type": "refresh_token"
})
new_access_token = resp.json()["access_token"]
```

### 10.2 403 Forbidden na API
- Verificar se autenticou com **Brand Account** (nao Gmail)
- Verificar se o canal pertence a conta autenticada
- Verificar se APIs estao habilitadas no Google Cloud

### 10.3 Codigo OAuth Expirado
- Codigos OAuth expiram em **~5 minutos**
- Codigos so podem ser usados **UMA VEZ**
- Se expirar, gerar nova URL e refazer o processo

---

## 11. Referencias

- [YouTube Analytics API](https://developers.google.com/youtube/analytics)
- [YouTube Data API v3](https://developers.google.com/youtube/v3)
- [Google OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)
- [Supabase Docs](https://supabase.com/docs)

---

**Documento criado por:** Claude Code
**Ultima atualizacao:** 08/12/2025

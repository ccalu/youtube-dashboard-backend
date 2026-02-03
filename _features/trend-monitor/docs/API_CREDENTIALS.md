# Como Obter Credenciais das APIs

## Resumo

| API | Credencial Necessaria | Custo | Tempo |
|-----|----------------------|-------|-------|
| Google Trends | Nenhuma | Gratis | - |
| YouTube | API Key | Gratis | 5 min |
| Reddit | Client ID + Secret | Gratis | 3 min |
| Hacker News | Nenhuma | Gratis | - |

---

## YouTube Data API v3

### Passo a Passo

1. **Acessar Google Cloud Console**
   - https://console.cloud.google.com/

2. **Criar Projeto**
   - Clique em "Select a project" > "New Project"
   - Nome: `trend-monitor` (ou qualquer nome)
   - Clique "Create"

3. **Ativar API**
   - Menu lateral > "APIs & Services" > "Library"
   - Buscar "YouTube Data API v3"
   - Clicar "Enable"

4. **Criar Chave de API**
   - Menu lateral > "APIs & Services" > "Credentials"
   - Clicar "Create Credentials" > "API Key"
   - Copiar a chave gerada

5. **Configurar no .env**
   ```
   YOUTUBE_API_KEY=AIzaSy...sua-chave-aqui
   ```

### Limites (Gratis)
- 10.000 unidades/dia
- Cada requisicao de trending = ~1 unidade
- Suficiente para ~7 paises × 50 videos = 350 requisicoes

---

## Reddit API (PRAW)

### Passo a Passo

1. **Acessar Reddit Apps**
   - https://www.reddit.com/prefs/apps
   - (Precisa estar logado no Reddit)

2. **Criar Aplicativo**
   - Scroll ate "developed applications"
   - Clique "create another app..."
   - Preencher:
     - Nome: `TrendMonitor`
     - Tipo: **script**
     - Redirect URI: `http://localhost:8080`
   - Clique "create app"

3. **Copiar Credenciais**
   - **Client ID**: String abaixo do nome do app (ex: `abc123xyz`)
   - **Client Secret**: Campo "secret"

4. **Configurar no .env**
   ```
   REDDIT_CLIENT_ID=abc123xyz
   REDDIT_CLIENT_SECRET=xyz789abc...
   REDDIT_USER_AGENT=TrendMonitor/1.0 by SeuUsername
   ```

### Limites (Gratis)
- 60 requisicoes/minuto
- Sem limite diario
- Suficiente para monitoramento continuo

---

## Google Trends

**Nao precisa de credencial!**

A biblioteca `pytrends` faz scraping automatico do Google Trends.

```python
from pytrends.request import TrendReq
pytrends = TrendReq(hl='en-US', tz=360)
```

### Limites
- ~100 requisicoes/hora (rate limiting automatico)
- Pode dar erro 429 se exceder

### Dicas
- Usar delays entre requisicoes
- Nao fazer muitas requisicoes em sequencia

---

## Hacker News

**Nao precisa de credencial!**

API publica e gratuita:
- https://hacker-news.firebaseio.com/v0/

### Endpoints
```
/topstories.json     # IDs das top stories
/newstories.json     # IDs das novas stories
/item/{id}.json      # Detalhes de um item
```

### Limites
- Sem limite documentado
- Usar com moderacao

---

## Verificar Configuracao

Apos configurar o `.env`, teste:

```bash
# Teste com coleta real
python main.py

# Se der erro de credencial, verificar:
cat .env | grep -v "^#"
```

## Seguranca

**IMPORTANTE:**
- Nunca commitar o arquivo `.env` no Git
- Arquivo `.gitignore` ja inclui `.env`
- Usar variaveis de ambiente em producao

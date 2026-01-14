# Instalacao e Configuracao

## Requisitos

- Python 3.9 ou superior
- pip (gerenciador de pacotes)
- Conexao com internet

## Passo a Passo

### 1. Ambiente Virtual (Recomendado)

```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows
```

### 2. Instalar Dependencias

```bash
pip install -r requirements.txt
```

**Dependencias principais:**
- `pytrends` - Google Trends (scraping)
- `praw` - Reddit API
- `google-api-python-client` - YouTube API
- `supabase` - Banco de dados na nuvem
- `jinja2` - Templates HTML
- `python-dotenv` - Variaveis de ambiente

### 3. Configurar Credenciais

```bash
# Copiar template
cp .env.example .env

# Editar com suas credenciais
nano .env  # ou qualquer editor
```

**Conteudo do .env:**
```
# Supabase (opcional - se nao configurar, usa SQLite)
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua-chave-anon

# YouTube (obrigatorio para coleta real)
YOUTUBE_API_KEY=sua-chave-api

# Reddit (obrigatorio para coleta real)
REDDIT_CLIENT_ID=seu-client-id
REDDIT_CLIENT_SECRET=seu-client-secret
REDDIT_USER_AGENT=TrendMonitor/1.0
```

### 4. Testar Instalacao

```bash
# Teste com dados mock (nao usa APIs)
python main.py --mock
```

**Saida esperada:**
```
TREND MONITOR - Inicializado
Data: 2025-01-13
Modo: MOCK
...
EXECUCAO FINALIZADA
Status: SUCESSO
Dashboard: output/trends-dashboard-2025-01-13.html
```

### 5. Verificar Dashboard

Abra o arquivo HTML gerado no navegador:
```bash
open output/trends-dashboard-*.html  # Mac
xdg-open output/trends-dashboard-*.html  # Linux
```

## Problemas Comuns

### Erro: ModuleNotFoundError

```bash
# Verificar se ambiente esta ativo
which python  # Deve mostrar caminho do venv

# Reinstalar dependencias
pip install -r requirements.txt
```

### Erro: SSL/TLS com pytrends

```bash
pip install --upgrade pytrends certifi
```

### Erro: Credenciais invalidas

Verificar se o arquivo `.env` esta na raiz do projeto e contem as credenciais corretas.

## Proximos Passos

1. [Obter credenciais das APIs](API_CREDENTIALS.md)
2. [Configurar Supabase](SUPABASE_SETUP.md)
3. [Entender o dashboard](DASHBOARD.md)

# Configuracao do Supabase

## O que e Supabase?

Banco de dados PostgreSQL na nuvem com:
- Dashboard web para visualizar dados
- API REST automatica
- Backup automatico
- Free tier generoso (500MB, 50K rows)

## Criar Projeto

### 1. Criar Conta
- Acesse https://supabase.com/
- Clique "Start your project"
- Login com GitHub (recomendado)

### 2. Criar Novo Projeto
- Clique "New Project"
- Preencher:
  - Nome: `trend-monitor`
  - Senha do banco: (guarde em local seguro)
  - Regiao: Mais proxima de voce
- Clique "Create new project"
- Aguarde ~2 minutos para provisionar

### 3. Copiar Credenciais
- Acesse: Settings > API
- Copiar:
  - **Project URL**: `https://xxx.supabase.co`
  - **anon public key**: `eyJhbGci...`

### 4. Configurar no .env
```
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Criar Tabelas

### Via SQL Editor

1. Acesse: SQL Editor (menu lateral)
2. Clique "New query"
3. Cole o SQL abaixo
4. Clique "Run"

```sql
-- =============================================
-- TREND MONITOR - Schema do Banco
-- =============================================

-- Tabela 1: Todos os trends coletados
CREATE TABLE IF NOT EXISTS trends (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    source TEXT NOT NULL,
    country TEXT DEFAULT 'global',
    language TEXT DEFAULT 'en',
    volume INTEGER DEFAULT 0,
    url TEXT,
    hn_url TEXT,
    permalink TEXT,
    subreddit TEXT,
    channel_title TEXT,
    author TEXT,
    num_comments INTEGER DEFAULT 0,
    collected_at TIMESTAMPTZ NOT NULL,
    collected_date DATE NOT NULL,
    raw_data JSONB,
    UNIQUE(title, source, collected_date)
);

-- Tabela 2: Padroes detectados (evergreen, crescente)
CREATE TABLE IF NOT EXISTS trend_patterns (
    id SERIAL PRIMARY KEY,
    title_normalized TEXT NOT NULL UNIQUE,
    first_seen DATE NOT NULL,
    last_seen DATE NOT NULL,
    days_active INTEGER DEFAULT 1,
    total_volume BIGINT DEFAULT 0,
    avg_volume INTEGER DEFAULT 0,
    sources_found TEXT,
    countries_found TEXT,
    is_evergreen BOOLEAN DEFAULT FALSE,
    is_growing BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabela 3: Metadados de coleta
CREATE TABLE IF NOT EXISTS collections (
    id SERIAL PRIMARY KEY,
    collected_date DATE UNIQUE NOT NULL,
    collected_at TIMESTAMPTZ NOT NULL,
    total_trends INTEGER DEFAULT 0,
    sources_used JSONB,
    countries_collected JSONB,
    status TEXT DEFAULT 'completed'
);

-- Indices para performance
CREATE INDEX IF NOT EXISTS idx_trends_source ON trends(source);
CREATE INDEX IF NOT EXISTS idx_trends_country ON trends(country);
CREATE INDEX IF NOT EXISTS idx_trends_date ON trends(collected_date);
CREATE INDEX IF NOT EXISTS idx_patterns_evergreen ON trend_patterns(is_evergreen);
CREATE INDEX IF NOT EXISTS idx_patterns_days ON trend_patterns(days_active DESC);

-- =============================================
-- Verificar criacao
-- =============================================
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public';
```

### Verificar Tabelas

Apos rodar o SQL, deve aparecer:
```
trends
trend_patterns
collections
```

---

## Testar Conexao

```bash
# Ativar ambiente
source venv/bin/activate

# Teste rapido
python -c "
from supabase import create_client
import os
from dotenv import load_dotenv
load_dotenv()

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
client = create_client(url, key)

# Testar leitura
result = client.table('trends').select('*').limit(1).execute()
print('Conexao OK!')
print(f'Trends no banco: verificar no dashboard')
"
```

---

## Visualizar Dados

### Via Dashboard
1. Acesse seu projeto no Supabase
2. Menu lateral > Table Editor
3. Selecione a tabela (trends, patterns, etc)

### Consultas Uteis

```sql
-- Total de trends por fonte
SELECT source, COUNT(*) as total
FROM trends
GROUP BY source
ORDER BY total DESC;

-- Trends evergreen (aparecem 7+ dias)
SELECT title_normalized, days_active, first_seen, last_seen
FROM trend_patterns
WHERE is_evergreen = TRUE
ORDER BY days_active DESC;

-- Coletas realizadas
SELECT collected_date, total_trends, status
FROM collections
ORDER BY collected_date DESC
LIMIT 10;
```

---

## Fallback SQLite

Se o Supabase nao estiver configurado (sem SUPABASE_URL/KEY no .env), o sistema usa automaticamente SQLite local:

```
data/trends.db
```

Isso permite:
- Desenvolver offline
- Testar sem nuvem
- Backup local automatico

---

## Limites do Free Tier

| Recurso | Limite Gratis |
|---------|---------------|
| Armazenamento | 500 MB |
| Linhas | ~50.000 |
| Requisicoes | Ilimitado |
| Projetos | 2 |

Para o Trend Monitor, isso e suficiente para:
- ~6 meses de coleta diaria
- ~900 trends/dia × 180 dias = 162.000 rows

Se precisar mais, considere:
- Limpar dados antigos periodicamente
- Upgrade para plano pago ($25/mes)

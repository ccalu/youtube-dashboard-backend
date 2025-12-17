# Setup Rápido - Sistema Financeiro

## Passo 1: Criar Tabelas no Supabase (2 minutos)

1. Acesse: https://supabase.com/dashboard/project/prvkmzstyedepvlbppyo/editor/sql

2. Clique em "+ New Query"

3. Cole este SQL completo:

```sql
-- TABELA: CATEGORIAS
CREATE TABLE financeiro_categorias (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('receita', 'despesa')),
    cor VARCHAR(7),
    icon VARCHAR(50),
    ativo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- TABELA: LANÇAMENTOS
CREATE TABLE financeiro_lancamentos (
    id SERIAL PRIMARY KEY,
    categoria_id INTEGER REFERENCES financeiro_categorias(id) ON DELETE SET NULL,
    valor DECIMAL(12,2) NOT NULL,
    data DATE NOT NULL,
    descricao TEXT,
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('receita', 'despesa')),
    recorrencia VARCHAR(20) CHECK (recorrencia IN ('fixa', 'unica') OR recorrencia IS NULL),
    usuario VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- TABELA: TAXAS
CREATE TABLE financeiro_taxas (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    percentual DECIMAL(5,2) NOT NULL CHECK (percentual >= 0 AND percentual <= 100),
    aplica_sobre VARCHAR(50) NOT NULL DEFAULT 'receita_bruta',
    ativo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- TABELA: METAS
CREATE TABLE financeiro_metas (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(200) NOT NULL,
    tipo VARCHAR(50) NOT NULL CHECK (tipo IN ('receita', 'lucro_liquido')),
    valor_objetivo DECIMAL(12,2) NOT NULL CHECK (valor_objetivo > 0),
    periodo_inicio DATE NOT NULL,
    periodo_fim DATE NOT NULL CHECK (periodo_fim > periodo_inicio),
    ativo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ÍNDICES
CREATE INDEX idx_lancamentos_data ON financeiro_lancamentos(data);
CREATE INDEX idx_lancamentos_tipo ON financeiro_lancamentos(tipo);
CREATE INDEX idx_lancamentos_recorrencia ON financeiro_lancamentos(recorrencia);
CREATE INDEX idx_lancamentos_categoria ON financeiro_lancamentos(categoria_id);
CREATE INDEX idx_metas_periodo ON financeiro_metas(periodo_inicio, periodo_fim);
```

4. Clique em "RUN" (ou pressione Ctrl+Enter)

5. Deve aparecer "Success. No rows returned"

---

## Passo 2: Rodar Setup Python (1 minuto)

No PowerShell:

```powershell
cd D:\ContentFactory\youtube-dashboard-backend
python setup_financeiro.py
```

**Isso vai:**
- Criar 8 categorias (YouTube AdSense, Ferramentas, Salários, etc)
- Criar taxa de 3% (Imposto)
- Sincronizar receita YouTube dos últimos 90 dias
- Mostrar overview financeiro

---

## Pronto!

API financeira 100% funcionando com:
- 27 endpoints REST
- Categorias, Lançamentos, Taxas, Metas
- Overview e Gráficos
- Integração YouTube automática
- Export CSV

---

## Testar (opcional):

```powershell
python test_financeiro.py
```

## Deploy:

```powershell
git add .
git commit -m "feat: Sistema financeiro completo"
git push origin main
```

Railway faz auto-deploy automaticamente!

-- ============================================
-- SISTEMA FINANCEIRO - TABELAS
-- ============================================
-- Criado: 2024-12-17
-- Descrição: Tabelas para gestão financeira
-- (categorias, lançamentos, taxas, metas)
-- ============================================

-- CATEGORIAS DE RECEITAS/DESPESAS
CREATE TABLE IF NOT EXISTS financeiro_categorias (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('receita', 'despesa')),
    cor VARCHAR(7),              -- hex color (#FF0000)
    icon VARCHAR(50),            -- nome do ícone
    ativo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- LANÇAMENTOS FINANCEIROS (receitas e despesas)
CREATE TABLE IF NOT EXISTS financeiro_lancamentos (
    id SERIAL PRIMARY KEY,
    categoria_id INTEGER REFERENCES financeiro_categorias(id) ON DELETE SET NULL,
    valor DECIMAL(12,2) NOT NULL,
    data DATE NOT NULL,
    descricao TEXT,
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('receita', 'despesa')),
    recorrencia VARCHAR(20) CHECK (recorrencia IN ('fixa', 'unica') OR recorrencia IS NULL),
    usuario VARCHAR(100),              -- quem criou
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- TAXAS E IMPOSTOS
CREATE TABLE IF NOT EXISTS financeiro_taxas (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    percentual DECIMAL(5,2) NOT NULL CHECK (percentual >= 0 AND percentual <= 100),
    aplica_sobre VARCHAR(50) NOT NULL DEFAULT 'receita_bruta',
    ativo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- METAS FINANCEIRAS
CREATE TABLE IF NOT EXISTS financeiro_metas (
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

-- ÍNDICES PARA PERFORMANCE
CREATE INDEX IF NOT EXISTS idx_lancamentos_data ON financeiro_lancamentos(data);
CREATE INDEX IF NOT EXISTS idx_lancamentos_tipo ON financeiro_lancamentos(tipo);
CREATE INDEX IF NOT EXISTS idx_lancamentos_recorrencia ON financeiro_lancamentos(recorrencia);
CREATE INDEX IF NOT EXISTS idx_lancamentos_categoria ON financeiro_lancamentos(categoria_id);
CREATE INDEX IF NOT EXISTS idx_metas_periodo ON financeiro_metas(periodo_inicio, periodo_fim);

-- TRIGGER PARA UPDATED_AT
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_financeiro_categorias_updated_at BEFORE UPDATE ON financeiro_categorias
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_financeiro_lancamentos_updated_at BEFORE UPDATE ON financeiro_lancamentos
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_financeiro_taxas_updated_at BEFORE UPDATE ON financeiro_taxas
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_financeiro_metas_updated_at BEFORE UPDATE ON financeiro_metas
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- COMENTÁRIOS NAS TABELAS
COMMENT ON TABLE financeiro_categorias IS 'Categorias de receitas e despesas';
COMMENT ON TABLE financeiro_lancamentos IS 'Todos os lançamentos financeiros (receitas e despesas)';
COMMENT ON TABLE financeiro_taxas IS 'Taxas e impostos aplicados sobre receitas';
COMMENT ON TABLE financeiro_metas IS 'Metas financeiras (receita ou lucro líquido)';

COMMENT ON COLUMN financeiro_lancamentos.recorrencia IS 'fixa=recorrente todo mês, unica=pontual (apenas para despesas)';
COMMENT ON COLUMN financeiro_taxas.aplica_sobre IS 'Base de cálculo da taxa (receita_bruta, receita_liquida, etc)';

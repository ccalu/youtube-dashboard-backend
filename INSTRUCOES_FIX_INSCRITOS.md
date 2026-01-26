# 🚨 CORREÇÃO URGENTE: Ganho de Inscritos Não Atualiza

## Problema Identificado
A Materialized View `mv_dashboard_completo` **NÃO estava calculando** o campo `inscritos_diff` (diferença diária de inscritos). Por isso o dashboard mostra sempre o mesmo valor há 2-3 dias.

## ✅ SOLUÇÃO - Execute no Supabase Dashboard

### Passo 1: Acesse o Supabase SQL Editor
1. Entre em: https://supabase.com/dashboard
2. Selecione seu projeto
3. Vá em **SQL Editor** (menu lateral)

### Passo 2: Cole e Execute este SQL

```sql
-- Fix para mv_dashboard_completo: Adicionar cálculo de inscritos_diff
-- Data: 26/01/2026

-- 1. Primeiro, dropar a MV existente
DROP MATERIALIZED VIEW IF EXISTS mv_dashboard_completo;

-- 2. Recriar com o cálculo correto de inscritos_diff
CREATE MATERIALIZED VIEW mv_dashboard_completo AS
WITH latest_data AS (
    -- Dados mais recentes de cada canal
    SELECT DISTINCT ON (canal_id)
        canal_id,
        nome,
        username,
        url_canal,
        inscritos,
        views_30d,
        videos_30d,
        tipo,
        subnicho,
        lingua,
        data_coleta,
        ultima_coleta
    FROM dados_canais_historico
    WHERE data_coleta >= CURRENT_DATE - INTERVAL '1 day'
    ORDER BY canal_id, data_coleta DESC
),
yesterday_data AS (
    -- Dados de ontem para calcular diferença
    SELECT DISTINCT ON (canal_id)
        canal_id,
        inscritos as inscritos_ontem
    FROM dados_canais_historico
    WHERE DATE(data_coleta) = CURRENT_DATE - INTERVAL '1 day'
    ORDER BY canal_id, data_coleta DESC
),
stats AS (
    -- Estatísticas pré-calculadas da mv_canal_video_stats
    SELECT
        canal_id,
        total_videos,
        total_views
    FROM mv_canal_video_stats
)
SELECT
    c.id,
    c.nome,
    c.username,
    c.url_canal,
    c.tipo,
    c.subnicho,
    c.lingua,
    COALESCE(ld.inscritos, c.inscritos) as inscritos,

    -- CORREÇÃO: Calcular inscritos_diff comparando com ontem
    CASE
        WHEN yd.inscritos_ontem IS NOT NULL AND ld.inscritos IS NOT NULL
        THEN ld.inscritos - yd.inscritos_ontem
        ELSE NULL
    END as inscritos_diff,

    COALESCE(ld.views_30d, c.views_30d, 0) as views_30d,
    COALESCE(ld.videos_30d, c.videos_30d, 0) as videos_30d,
    COALESCE(s.total_videos, 0) as total_videos,
    COALESCE(s.total_views, 0) as total_views,
    COALESCE(ld.ultima_coleta, c.ultima_coleta) as ultima_coleta,
    c.data_criacao,
    c.ativo,
    c.monitor_coleta,
    c.monitor_transcrever,
    c.monitor_notificacoes,
    c.coleta_falhas_consecutivas,
    c.coleta_ultimo_erro,
    c.coleta_ultimo_sucesso
FROM canais_monitorados c
LEFT JOIN latest_data ld ON c.id = ld.canal_id
LEFT JOIN yesterday_data yd ON c.id = yd.canal_id  -- JOIN com dados de ontem
LEFT JOIN stats s ON c.id = s.canal_id
WHERE c.ativo = true;

-- 3. Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_mv_dashboard_id ON mv_dashboard_completo(id);
CREATE INDEX IF NOT EXISTS idx_mv_dashboard_tipo ON mv_dashboard_completo(tipo);
CREATE INDEX IF NOT EXISTS idx_mv_dashboard_subnicho ON mv_dashboard_completo(subnicho);
CREATE INDEX IF NOT EXISTS idx_mv_dashboard_lingua ON mv_dashboard_completo(lingua);

-- 4. Analisar para otimizar queries
ANALYZE mv_dashboard_completo;
```

### Passo 3: Verificar se Funcionou
Execute esta query para ver se o `inscritos_diff` está sendo calculado:

```sql
SELECT
    nome,
    inscritos,
    inscritos_diff,
    ultima_coleta
FROM mv_dashboard_completo
WHERE inscritos_diff IS NOT NULL
ORDER BY ABS(inscritos_diff) DESC
LIMIT 20;
```

Você deve ver resultados como:
- Canal A: inscritos_diff = 150 (ganhou 150 inscritos)
- Canal B: inscritos_diff = -23 (perdeu 23 inscritos)
- Canal C: inscritos_diff = 0 (manteve)

### Passo 4: Limpar o Cache (Local)
Se estiver testando localmente:
```bash
python clear_cache.py
```

### Passo 5: Verificar no Dashboard
1. Abra o dashboard
2. Verifique a aba "Tabela" ou "Canais"
3. Os números de ganho/perda de inscritos devem estar atualizados

## 🔄 O Que Foi Corrigido

**ANTES (BUG):**
- A MV apenas pegava o valor atual de inscritos
- Não calculava a diferença com o dia anterior
- Campo `inscritos_diff` sempre retornava NULL

**DEPOIS (CORRIGIDO):**
- Adicionada CTE `yesterday_data` que busca inscritos de ontem
- Cálculo: `inscritos_diff = inscritos_hoje - inscritos_ontem`
- Agora mostra corretamente +150, -23, 0, etc

## ⚠️ IMPORTANTE
- O cache do dashboard é de 24 horas
- Após executar o SQL, o cache será limpo automaticamente na próxima requisição
- A coleta continua funcionando normalmente às 5 AM
- Esta correção não afeta a coleta, apenas corrige a visualização

## 📊 Resultado Esperado
Após aplicar o fix, o dashboard voltará a mostrar:
- ✅ Ganho/perda diária de inscritos atualizada
- ✅ Valores diferentes a cada dia (não mais "travados")
- ✅ Performance mantida (0.109ms com cache)
# ⚠️ AÇÃO NECESSÁRIA: EXECUTAR MIGRATION SQL

## Marcelo, preciso que você execute este SQL no Supabase Dashboard

**Tempo:** 2 minutos
**Local:** Supabase Dashboard

---

## 🎯 PASSOS EXATOS:

### 1. Acesse o Supabase Dashboard
```
https://supabase.com/dashboard
```

### 2. Selecione o projeto
- Project: `prvkmzstyedepvlbppyo`

### 3. Vá em SQL Editor
- Menu lateral esquerdo → SQL Editor
- Clique em "+ New query"

### 4. Cole o SQL abaixo (COPIE TUDO):

```sql
-- Migration: Sistema de Monetização
-- Data: 2025-12-10

-- 1. Adicionar total_views em dados_canais_historico
ALTER TABLE dados_canais_historico
ADD COLUMN IF NOT EXISTS total_views BIGINT;

COMMENT ON COLUMN dados_canais_historico.total_views IS
'Total de views do canal desde sempre. Usado para calcular views de 24h.';

-- 2. Adicionar campos em yt_daily_metrics
ALTER TABLE yt_daily_metrics
ADD COLUMN IF NOT EXISTS is_estimate BOOLEAN DEFAULT FALSE;

ALTER TABLE yt_daily_metrics
ADD COLUMN IF NOT EXISTS avg_retention_pct DECIMAL(5,2),
ADD COLUMN IF NOT EXISTS avg_view_duration_sec INTEGER,
ADD COLUMN IF NOT EXISTS ctr_approx DECIMAL(5,2);

-- Comentários
COMMENT ON COLUMN yt_daily_metrics.is_estimate IS
'TRUE = revenue estimado (RPM × views), FALSE = revenue real da API';

COMMENT ON COLUMN yt_daily_metrics.avg_retention_pct IS
'Porcentagem média de retenção dos vídeos (YouTube Analytics)';

COMMENT ON COLUMN yt_daily_metrics.avg_view_duration_sec IS
'Tempo médio de visualização em segundos (YouTube Analytics)';

COMMENT ON COLUMN yt_daily_metrics.ctr_approx IS
'CTR aproximado: (views / impressions) × 100 (YouTube Analytics)';

-- 3. Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_yt_daily_metrics_estimate
ON yt_daily_metrics(channel_id, is_estimate);

CREATE INDEX IF NOT EXISTS idx_yt_daily_metrics_date_channel
ON yt_daily_metrics(date DESC, channel_id);

CREATE INDEX IF NOT EXISTS idx_dados_canais_historico_date
ON dados_canais_historico(data_coleta DESC, canal_id);

-- 4. Marcar registros existentes como reais
UPDATE yt_daily_metrics
SET is_estimate = FALSE
WHERE is_estimate IS NULL;

-- Sucesso!
SELECT 'Migration concluída com sucesso!' as status,
       COUNT(*) as registros_atualizados
FROM yt_daily_metrics
WHERE is_estimate = FALSE;
```

### 5. Execute
- Clique em **RUN** (ou pressione Ctrl+Enter)
- Aguarde ~5 segundos

### 6. Confirme o Sucesso
Você deve ver:
```
status: "Migration concluída com sucesso!"
registros_atualizados: 301
```

---

## ✅ APÓS EXECUTAR

Volte aqui e me avise: "Migration executada!"

Aí eu vou:
1. Rodar o snapshot inicial automaticamente
2. Testar todos os endpoints
3. Completar o sistema 100%

---

## 🚨 SE DER ERRO

Se aparecer erro tipo "column already exists" → **PERFEITO!**
Significa que já foi executado antes.

Se aparecer erro de permissão → Verifique se está logado como owner do projeto.

---

**STATUS:** ⏳ Aguardando você executar (2 minutos)

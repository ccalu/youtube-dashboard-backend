# 05 - Database Schema Completo

## Índice
1. [Visão Geral](#visão-geral)
2. [Sistema de Mineração](#sistema-de-mineração)
3. [Sistema de Notificações](#sistema-de-notificações)
4. [Sistema de Monetização](#sistema-de-monetização)
5. [Sistema de Upload](#sistema-de-upload)
6. [Sistema Financeiro](#sistema-financeiro)
7. [Indexes e Performance](#indexes-e-performance)
8. [Queries Comuns](#queries-comuns)

---

## Visão Geral

**Database:** Supabase PostgreSQL 15+
**Total de Tabelas:** 27
**Tamanho Aproximado:** 5-10 GB (Jan 2025)

### Organização por Módulo

```
┌─────────────────────────────────────────────────────────────┐
│ MINERAÇÃO (6 tabelas)                                      │
├─────────────────────────────────────────────────────────────┤
│ • canais_monitorados          - 263 canais ativos          │
│ • dados_canais_historico      - Histórico diário (~78k)    │
│ • videos_historico            - Vídeos coletados (~500k)   │
│ • coletas_historico           - Logs de coleta (~1.2k)     │
│ • favoritos                   - Canais/vídeos favoritos    │
│ • transcriptions              - Cache de transcrições      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ NOTIFICAÇÕES (2 tabelas)                                   │
├─────────────────────────────────────────────────────────────┤
│ • notificacoes                - Alertas de vídeos virais   │
│ • regras_notificacoes         - Configuração de marcos     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ MONETIZAÇÃO (11 tabelas)                                   │
├─────────────────────────────────────────────────────────────┤
│ • yt_channels                 - Canais monetizados (16)    │
│ • yt_oauth_tokens             - Access/refresh tokens      │
│ • yt_proxy_credentials        - Client ID/secret (proxy)   │
│ • yt_channel_credentials      - Client ID/secret (isolado) │
│ • yt_daily_metrics            - Revenue diário (~5k)       │
│ • yt_country_metrics          - Revenue por país (~800)    │
│ • yt_video_metrics            - Revenue por vídeo (~2k)    │
│ • yt_video_daily              - Histórico vídeos (~10k)    │
│ • yt_traffic_summary          - Fontes de tráfego          │
│ • yt_search_analytics         - Termos de busca            │
│ • yt_suggested_sources        - Vídeos que recomendam      │
│ • yt_demographics             - Idade e gênero             │
│ • yt_device_metrics           - Dispositivos               │
│ • yt_collection_logs          - Logs coleta OAuth          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ UPLOAD AUTOMÁTICO (1 tabela)                               │
├─────────────────────────────────────────────────────────────┤
│ • yt_upload_queue             - Fila de uploads (~100)     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ FINANCEIRO (4 tabelas)                                     │
├─────────────────────────────────────────────────────────────┤
│ • financeiro_categorias       - Categorias de lançamentos  │
│ • financeiro_lancamentos      - Receitas e despesas        │
│ • financeiro_taxas            - Histórico de câmbio        │
│ • financeiro_metas            - Metas mensais              │
└─────────────────────────────────────────────────────────────┘
```

---

## Sistema de Mineração

### 1. canais_monitorados

**Descrição:** Canais monitorados (minerados + nossos)

```sql
CREATE TABLE canais_monitorados (
    id SERIAL PRIMARY KEY,
    nome_canal VARCHAR(200) NOT NULL,
    url_canal TEXT NOT NULL UNIQUE,
    nicho VARCHAR(100) DEFAULT '',
    subnicho VARCHAR(100) NOT NULL,
    lingua VARCHAR(50) DEFAULT 'English',
    tipo VARCHAR(20) DEFAULT 'minerado',  -- 'minerado' ou 'nosso'
    status VARCHAR(20) DEFAULT 'ativo',   -- 'ativo' ou 'inativo'
    ultima_coleta TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_canais_status ON canais_monitorados(status);
CREATE INDEX idx_canais_tipo ON canais_monitorados(tipo);
CREATE INDEX idx_canais_subnicho ON canais_monitorados(subnicho);
CREATE INDEX idx_canais_ultima_coleta ON canais_monitorados(ultima_coleta);
```

**Campos Importantes:**
- `tipo`: Diferencia canais minerados (referência) vs nossos (operação)
- `lingua`: pt, en, es, fr, de, ar, ko, etc.
- `subnicho`: "História Antiga", "Biografias", "Guerras", etc.
- `url_canal`: YouTube URL completa (normalizada)

**Dados Atuais (Jan 2025):**
- Total: 263 canais ativos
- Minerados: 209 (79%)
- Nossos: 54 (21%)
- Línguas: 8 diferentes

**Query Comum:**
```sql
-- Buscar canais ativos para coleta
SELECT * FROM canais_monitorados
WHERE status = 'ativo'
ORDER BY ultima_coleta ASC NULLS FIRST;
```

### 2. dados_canais_historico

**Descrição:** Histórico diário de métricas dos canais

```sql
CREATE TABLE dados_canais_historico (
    id SERIAL PRIMARY KEY,
    canal_id INTEGER NOT NULL REFERENCES canais_monitorados(id) ON DELETE CASCADE,
    data_coleta DATE NOT NULL,
    views_30d INTEGER DEFAULT 0,
    views_15d INTEGER DEFAULT 0,
    views_7d INTEGER DEFAULT 0,
    inscritos INTEGER DEFAULT 0,
    videos_publicados_7d INTEGER DEFAULT 0,
    engagement_rate DECIMAL(5,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(canal_id, data_coleta)
);

-- Indexes
CREATE INDEX idx_historico_canal ON dados_canais_historico(canal_id);
CREATE INDEX idx_historico_data ON dados_canais_historico(data_coleta DESC);
CREATE INDEX idx_historico_canal_data ON dados_canais_historico(canal_id, data_coleta DESC);
```

**Campos Calculados:**
- `views_30d/15d/7d`: Total de views nos últimos X dias
- `engagement_rate`: (likes + comments) / views * 100
- `videos_publicados_7d`: Vídeos novos na última semana

**Retenção:** 60 dias (cleanup automático)

**Query Comum:**
```sql
-- Histórico dos últimos 7 dias de um canal
SELECT * FROM dados_canais_historico
WHERE canal_id = 123
AND data_coleta >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY data_coleta DESC;

-- Calcular diferença de inscritos (hoje vs ontem)
WITH dados AS (
    SELECT
        canal_id,
        data_coleta,
        inscritos,
        LAG(inscritos) OVER (PARTITION BY canal_id ORDER BY data_coleta) AS inscritos_ontem
    FROM dados_canais_historico
    WHERE data_coleta >= CURRENT_DATE - INTERVAL '2 days'
)
SELECT
    canal_id,
    data_coleta,
    inscritos,
    inscritos - inscritos_ontem AS inscritos_diff
FROM dados
WHERE data_coleta = CURRENT_DATE;
```

### 3. videos_historico

**Descrição:** Histórico de vídeos coletados (últimos 30 dias por canal)

```sql
CREATE TABLE videos_historico (
    id SERIAL PRIMARY KEY,
    canal_id INTEGER NOT NULL REFERENCES canais_monitorados(id) ON DELETE CASCADE,
    video_id VARCHAR(20) NOT NULL,
    titulo TEXT NOT NULL,
    url_video TEXT NOT NULL,
    data_publicacao TIMESTAMP NOT NULL,
    data_coleta DATE NOT NULL,
    views_atuais INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comentarios INTEGER DEFAULT 0,
    duracao INTEGER DEFAULT 0,  -- em segundos
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(video_id, data_coleta)
);

-- Indexes
CREATE INDEX idx_videos_canal ON videos_historico(canal_id);
CREATE INDEX idx_videos_publicacao ON videos_historico(data_publicacao DESC);
CREATE INDEX idx_videos_coleta ON videos_historico(data_coleta DESC);
CREATE INDEX idx_videos_id ON videos_historico(video_id);
CREATE INDEX idx_videos_canal_coleta ON videos_historico(canal_id, data_coleta DESC);
```

**Importante:**
- `video_id`: YouTube video ID (11 caracteres)
- Snapshot diário: mesmo vídeo pode ter múltiplas entradas
- Útil para calcular crescimento de views ao longo do tempo

**Query Comum:**
```sql
-- Vídeos mais recentes (última coleta)
SELECT DISTINCT ON (video_id)
    video_id,
    titulo,
    views_atuais,
    data_publicacao
FROM videos_historico
ORDER BY video_id, data_coleta DESC;

-- Top 10 vídeos por views (últimos 7 dias)
SELECT
    v.titulo,
    v.views_atuais,
    c.nome_canal
FROM videos_historico v
JOIN canais_monitorados c ON v.canal_id = c.id
WHERE v.data_publicacao >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY v.views_atuais DESC
LIMIT 10;
```

### 4. coletas_historico

**Descrição:** Log de todas as coletas executadas

```sql
CREATE TABLE coletas_historico (
    id SERIAL PRIMARY KEY,
    data_inicio TIMESTAMP NOT NULL,
    data_fim TIMESTAMP,
    status VARCHAR(20) NOT NULL,  -- 'em_progresso', 'sucesso', 'erro'
    canais_total INTEGER DEFAULT 0,
    canais_sucesso INTEGER DEFAULT 0,
    canais_erro INTEGER DEFAULT 0,
    videos_coletados INTEGER DEFAULT 0,
    requisicoes_usadas INTEGER DEFAULT 0,
    duracao_segundos INTEGER DEFAULT 0,
    mensagem_erro TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index
CREATE INDEX idx_coletas_data ON coletas_historico(data_inicio DESC);
CREATE INDEX idx_coletas_status ON coletas_historico(status);
```

**Status:**
- `em_progresso`: Coleta rodando
- `sucesso`: Completada com sucesso
- `erro`: Falhou (quota esgotada, timeout, etc.)

**Cleanup:**
- Coletas "travadas" (>2h) são marcadas como erro automaticamente
- Ver: `database.cleanup_stuck_collections()`

**Query Comum:**
```sql
-- Últimas 10 coletas
SELECT
    id,
    data_inicio,
    status,
    canais_sucesso,
    canais_erro,
    videos_coletados,
    duracao_segundos
FROM coletas_historico
ORDER BY data_inicio DESC
LIMIT 10;

-- Estatísticas do dia
SELECT
    COUNT(*) as total_coletas,
    SUM(canais_sucesso) as canais_ok,
    SUM(videos_coletados) as videos_total,
    AVG(duracao_segundos) as duracao_media
FROM coletas_historico
WHERE data_inicio >= CURRENT_DATE
AND status = 'sucesso';
```

### 5. favoritos

**Descrição:** Canais e vídeos marcados como favoritos

```sql
CREATE TABLE favoritos (
    id SERIAL PRIMARY KEY,
    tipo VARCHAR(20) NOT NULL,  -- 'canal' ou 'video'
    item_id INTEGER NOT NULL,   -- canais_monitorados.id ou videos_historico.id
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(tipo, item_id)
);

-- Index
CREATE INDEX idx_favoritos_tipo ON favoritos(tipo);
```

**Query Comum:**
```sql
-- Canais favoritos
SELECT c.*
FROM favoritos f
JOIN canais_monitorados c ON f.item_id = c.id
WHERE f.tipo = 'canal';
```

### 6. transcriptions

**Descrição:** Cache de transcrições de vídeos

```sql
CREATE TABLE transcriptions (
    id SERIAL PRIMARY KEY,
    video_id VARCHAR(20) NOT NULL UNIQUE,
    transcription TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index
CREATE INDEX idx_transcriptions_video ON transcriptions(video_id);
```

**Uso:**
- Cache para servidor M5 (transcrição via WhisperAI)
- Evita reprocessar mesmos vídeos

---

## Sistema de Notificações

### 7. regras_notificacoes

**Descrição:** Regras configuráveis de notificação

```sql
CREATE TABLE regras_notificacoes (
    id SERIAL PRIMARY KEY,
    nome_regra VARCHAR(100) NOT NULL,
    views_minimas INTEGER NOT NULL,
    periodo_dias INTEGER NOT NULL,
    ativa BOOLEAN DEFAULT TRUE,
    tipo_canal VARCHAR(20) DEFAULT 'ambos',  -- 'nosso', 'minerado', 'ambos'
    subnichos TEXT[],  -- Array de subnichos (NULL = todos)
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index
CREATE INDEX idx_regras_ativa ON regras_notificacoes(ativa);
CREATE INDEX idx_regras_views ON regras_notificacoes(views_minimas);
```

**Regras Padrão:**
```sql
INSERT INTO regras_notificacoes (nome_regra, views_minimas, periodo_dias, subnichos) VALUES
('10k em 24h', 10000, 1, NULL),
('50k em 7d', 50000, 7, NULL),
('100k em 30d', 100000, 30, NULL);
```

**Exemplo com Subnichos:**
```sql
-- Notificar apenas subnicho "História Antiga" que atingir 50k/7d
INSERT INTO regras_notificacoes (nome_regra, views_minimas, periodo_dias, subnichos) VALUES
('História 50k/7d', 50000, 7, ARRAY['História Antiga']);
```

### 8. notificacoes

**Descrição:** Notificações geradas automaticamente

```sql
CREATE TABLE notificacoes (
    id SERIAL PRIMARY KEY,
    video_id VARCHAR(20) NOT NULL,
    canal_id INTEGER NOT NULL REFERENCES canais_monitorados(id) ON DELETE CASCADE,
    nome_video TEXT NOT NULL,
    nome_canal VARCHAR(200) NOT NULL,
    tipo_canal VARCHAR(20) DEFAULT 'minerado',
    views_atingidas INTEGER NOT NULL,
    periodo_dias INTEGER NOT NULL,
    tipo_alerta VARCHAR(50) NOT NULL,  -- ex: '50k_7d', '100k_30d'
    mensagem TEXT NOT NULL,
    vista BOOLEAN DEFAULT FALSE,
    data_disparo TIMESTAMP DEFAULT NOW(),
    data_vista TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_notif_vista ON notificacoes(vista);
CREATE INDEX idx_notif_canal ON notificacoes(canal_id);
CREATE INDEX idx_notif_video ON notificacoes(video_id);
CREATE INDEX idx_notif_data ON notificacoes(data_disparo DESC);
CREATE INDEX idx_notif_tipo_canal ON notificacoes(tipo_canal);
```

**Lógica Anti-Duplicação:**
- Máximo 1 notificação não vista por vídeo
- Permite elevação (10k → 50k → 100k)
- Não re-notifica se já viu marco maior

**Query Comum:**
```sql
-- Notificações não vistas
SELECT * FROM notificacoes
WHERE vista = FALSE
ORDER BY data_disparo DESC;

-- Marcar todas como vistas
UPDATE notificacoes
SET vista = TRUE, data_vista = NOW()
WHERE vista = FALSE;

-- Notificações por subnicho (JOIN)
SELECT n.*, c.subnicho
FROM notificacoes n
JOIN canais_monitorados c ON n.canal_id = c.id
WHERE c.subnicho = 'História Antiga'
AND n.vista = FALSE;
```

---

## Sistema de Monetização

### 9. yt_channels

**Descrição:** Canais monetizados (nossos 16 canais)

```sql
CREATE TABLE yt_channels (
    id SERIAL PRIMARY KEY,
    channel_id VARCHAR(24) NOT NULL UNIQUE,  -- UCxxxxxxxxxxxxxxxxxx
    channel_name VARCHAR(200) NOT NULL,
    is_monetized BOOLEAN DEFAULT TRUE,
    proxy_name VARCHAR(50),  -- Nome do proxy (se usar)
    lingua VARCHAR(10) DEFAULT 'pt',
    subnicho VARCHAR(100),
    default_playlist_id VARCHAR(34),  -- Playlist para uploads
    total_subscribers INTEGER DEFAULT 0,
    total_videos INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index
CREATE INDEX idx_yt_channels_monetized ON yt_channels(is_monetized);
CREATE INDEX idx_yt_channels_proxy ON yt_channels(proxy_name);
```

**Proxy System:**
- 1 proxy pode autorizar múltiplos canais
- Alternativa: credenciais isoladas por canal

### 10. yt_oauth_tokens

**Descrição:** Tokens OAuth por canal (RLS protegido)

```sql
CREATE TABLE yt_oauth_tokens (
    id SERIAL PRIMARY KEY,
    channel_id VARCHAR(24) NOT NULL UNIQUE REFERENCES yt_channels(channel_id) ON DELETE CASCADE,
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- RLS (Row Level Security)
ALTER TABLE yt_oauth_tokens ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role only" ON yt_oauth_tokens
    FOR ALL USING (auth.role() = 'service_role');

-- Index
CREATE INDEX idx_oauth_channel ON yt_oauth_tokens(channel_id);
```

**Segurança:**
- Apenas `service_role_key` pode acessar
- Anon key não tem permissão (RLS)

### 11. yt_proxy_credentials

**Descrição:** Credenciais OAuth do proxy (RLS protegido)

```sql
CREATE TABLE yt_proxy_credentials (
    id SERIAL PRIMARY KEY,
    proxy_name VARCHAR(50) NOT NULL UNIQUE,
    client_id TEXT NOT NULL,
    client_secret TEXT NOT NULL,
    redirect_uri TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- RLS
ALTER TABLE yt_proxy_credentials ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role only" ON yt_proxy_credentials
    FOR ALL USING (auth.role() = 'service_role');
```

### 12. yt_channel_credentials

**Descrição:** Credenciais OAuth isoladas por canal (RLS protegido)

```sql
CREATE TABLE yt_channel_credentials (
    id SERIAL PRIMARY KEY,
    channel_id VARCHAR(24) NOT NULL UNIQUE REFERENCES yt_channels(channel_id) ON DELETE CASCADE,
    client_id TEXT NOT NULL,
    client_secret TEXT NOT NULL,
    redirect_uri TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- RLS
ALTER TABLE yt_channel_credentials ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role only" ON yt_channel_credentials
    FOR ALL USING (auth.role() = 'service_role');
```

### 13. yt_daily_metrics

**Descrição:** Métricas diárias de monetização

```sql
CREATE TABLE yt_daily_metrics (
    id SERIAL PRIMARY KEY,
    channel_id VARCHAR(24) NOT NULL REFERENCES yt_channels(channel_id) ON DELETE CASCADE,
    date DATE NOT NULL,
    revenue DECIMAL(10,2) DEFAULT 0.00,  -- USD
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    subscribers_gained INTEGER DEFAULT 0,
    subscribers_lost INTEGER DEFAULT 0,
    watch_time_minutes INTEGER DEFAULT 0,
    rpm DECIMAL(10,2) DEFAULT 0.00,  -- Revenue per mille
    avg_view_duration_sec DECIMAL(10,2),
    avg_retention_pct DECIMAL(5,2),
    is_estimate BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(channel_id, date)
);

-- Indexes
CREATE INDEX idx_daily_channel ON yt_daily_metrics(channel_id);
CREATE INDEX idx_daily_date ON yt_daily_metrics(date DESC);
CREATE INDEX idx_daily_channel_date ON yt_daily_metrics(channel_id, date DESC);
```

**Importante:**
- YouTube Analytics tem delay de 2-3 dias para revenue
- `is_estimate`: FALSE = dado real da API

**Query Comum:**
```sql
-- Revenue total dos últimos 30 dias
SELECT
    channel_id,
    SUM(revenue) as revenue_usd,
    SUM(views) as views_total,
    AVG(rpm) as rpm_medio
FROM yt_daily_metrics
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
AND is_estimate = FALSE
GROUP BY channel_id;
```

### 14. yt_country_metrics

**Descrição:** Métricas por país

```sql
CREATE TABLE yt_country_metrics (
    id SERIAL PRIMARY KEY,
    channel_id VARCHAR(24) NOT NULL REFERENCES yt_channels(channel_id) ON DELETE CASCADE,
    date DATE NOT NULL,
    country_code VARCHAR(2) NOT NULL,  -- BR, US, PT, etc.
    views INTEGER DEFAULT 0,
    revenue DECIMAL(10,2) DEFAULT 0.00,  -- USD
    watch_time_minutes INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(channel_id, date, country_code)
);

-- Indexes
CREATE INDEX idx_country_channel ON yt_country_metrics(channel_id);
CREATE INDEX idx_country_date ON yt_country_metrics(date DESC);
CREATE INDEX idx_country_code ON yt_country_metrics(country_code);
```

**Query Comum:**
```sql
-- Top 5 países por revenue (últimos 30 dias)
SELECT
    country_code,
    SUM(revenue) as revenue_total,
    SUM(views) as views_total
FROM yt_country_metrics
WHERE channel_id = 'UCxxx'
AND date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY country_code
ORDER BY revenue_total DESC
LIMIT 5;
```

### 15. yt_video_metrics

**Descrição:** Métricas acumuladas por vídeo

```sql
CREATE TABLE yt_video_metrics (
    id SERIAL PRIMARY KEY,
    channel_id VARCHAR(24) NOT NULL REFERENCES yt_channels(channel_id) ON DELETE CASCADE,
    video_id VARCHAR(20) NOT NULL,
    title TEXT,
    revenue DECIMAL(10,2) DEFAULT 0.00,  -- USD (lifetime)
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    subscribers_gained INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(channel_id, video_id)
);

-- Indexes
CREATE INDEX idx_video_metrics_channel ON yt_video_metrics(channel_id);
CREATE INDEX idx_video_metrics_video ON yt_video_metrics(video_id);
CREATE INDEX idx_video_metrics_revenue ON yt_video_metrics(revenue DESC);
```

### 16. yt_video_daily

**Descrição:** Histórico diário por vídeo

```sql
CREATE TABLE yt_video_daily (
    id SERIAL PRIMARY KEY,
    channel_id VARCHAR(24) NOT NULL REFERENCES yt_channels(channel_id) ON DELETE CASCADE,
    video_id VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    title TEXT,
    revenue DECIMAL(10,2) DEFAULT 0.00,  -- USD (do dia)
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    subscribers_gained INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(channel_id, video_id, date)
);

-- Indexes
CREATE INDEX idx_video_daily_channel ON yt_video_daily(channel_id);
CREATE INDEX idx_video_daily_video ON yt_video_daily(video_id);
CREATE INDEX idx_video_daily_date ON yt_video_daily(date DESC);
```

### 17-22. Analytics Avançado

```sql
-- 17. yt_traffic_summary (fontes de tráfego)
CREATE TABLE yt_traffic_summary (
    id SERIAL PRIMARY KEY,
    channel_id VARCHAR(24) NOT NULL REFERENCES yt_channels(channel_id) ON DELETE CASCADE,
    date DATE NOT NULL,
    source_type VARCHAR(50) NOT NULL,  -- YT_SEARCH, YT_RELATED, etc.
    views INTEGER DEFAULT 0,
    watch_time_minutes INTEGER DEFAULT 0,
    percentage DECIMAL(5,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(channel_id, date, source_type)
);

-- 18. yt_search_analytics (termos de busca)
CREATE TABLE yt_search_analytics (
    id SERIAL PRIMARY KEY,
    channel_id VARCHAR(24) NOT NULL REFERENCES yt_channels(channel_id) ON DELETE CASCADE,
    date DATE NOT NULL,
    search_term TEXT NOT NULL,
    views INTEGER DEFAULT 0,
    percentage_of_search DECIMAL(5,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(channel_id, date, search_term)
);

-- 19. yt_suggested_sources (vídeos que recomendam)
CREATE TABLE yt_suggested_sources (
    id SERIAL PRIMARY KEY,
    channel_id VARCHAR(24) NOT NULL REFERENCES yt_channels(channel_id) ON DELETE CASCADE,
    date DATE NOT NULL,
    source_video_id VARCHAR(20) NOT NULL,
    source_video_title TEXT,
    source_channel_name VARCHAR(200),
    views_generated INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(channel_id, date, source_video_id)
);

-- 20. yt_demographics (idade e gênero)
CREATE TABLE yt_demographics (
    id SERIAL PRIMARY KEY,
    channel_id VARCHAR(24) NOT NULL REFERENCES yt_channels(channel_id) ON DELETE CASCADE,
    date DATE NOT NULL,
    age_group VARCHAR(20) NOT NULL,  -- age13-17, age18-24, etc.
    gender VARCHAR(10) NOT NULL,     -- male, female
    views INTEGER DEFAULT 0,
    watch_time_minutes INTEGER DEFAULT 0,
    percentage DECIMAL(5,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(channel_id, date, age_group, gender)
);

-- 21. yt_device_metrics (dispositivos)
CREATE TABLE yt_device_metrics (
    id SERIAL PRIMARY KEY,
    channel_id VARCHAR(24) NOT NULL REFERENCES yt_channels(channel_id) ON DELETE CASCADE,
    date DATE NOT NULL,
    device_type VARCHAR(50) NOT NULL,  -- MOBILE, DESKTOP, TV, TABLET
    views INTEGER DEFAULT 0,
    watch_time_minutes INTEGER DEFAULT 0,
    percentage DECIMAL(5,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(channel_id, date, device_type)
);

-- 22. yt_collection_logs (logs de coleta)
CREATE TABLE yt_collection_logs (
    id SERIAL PRIMARY KEY,
    channel_id VARCHAR(24) NOT NULL REFERENCES yt_channels(channel_id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL,  -- 'success', 'error'
    message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Sistema de Upload

### 23. yt_upload_queue

**Descrição:** Fila de uploads automáticos

```sql
CREATE TABLE yt_upload_queue (
    id SERIAL PRIMARY KEY,
    channel_id VARCHAR(24) NOT NULL REFERENCES yt_channels(channel_id) ON DELETE CASCADE,
    spreadsheet_id VARCHAR(100) NOT NULL,
    video_url TEXT NOT NULL,
    titulo TEXT NOT NULL,
    descricao TEXT NOT NULL,
    lingua VARCHAR(10) DEFAULT 'pt',
    status VARCHAR(20) DEFAULT 'pending',  -- pending, processing, completed, failed
    video_id VARCHAR(20),  -- Preenchido após upload
    upload_date TIMESTAMP,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    position INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_upload_queue_channel ON yt_upload_queue(channel_id);
CREATE INDEX idx_upload_queue_status ON yt_upload_queue(status);
CREATE INDEX idx_upload_queue_position ON yt_upload_queue(position);
```

**Estados:**
- `pending`: Na fila
- `processing`: Sendo processado
- `completed`: Upload OK
- `failed`: Falhou (3 tentativas)

**Query Comum:**
```sql
-- Próximo item da fila
SELECT * FROM yt_upload_queue
WHERE status = 'pending'
ORDER BY position ASC, created_at ASC
LIMIT 1;

-- Estatísticas de hoje
SELECT
    status,
    COUNT(*) as total
FROM yt_upload_queue
WHERE created_at >= CURRENT_DATE
GROUP BY status;
```

---

## Sistema Financeiro

### 24. financeiro_categorias

**Descrição:** Categorias de lançamentos

```sql
CREATE TABLE financeiro_categorias (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    tipo VARCHAR(20) NOT NULL,  -- 'receita' ou 'despesa'
    cor VARCHAR(20),
    icon VARCHAR(50),
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Categorias padrão
INSERT INTO financeiro_categorias (nome, tipo, cor) VALUES
('YouTube AdSense', 'receita', '#ff0000'),
('Monetização Extra', 'receita', '#00ff00'),
('Equipe', 'despesa', '#0000ff'),
('Infraestrutura', 'despesa', '#ff00ff'),
('Marketing', 'despesa', '#ffff00');
```

### 25. financeiro_lancamentos

**Descrição:** Lançamentos financeiros manuais

```sql
CREATE TABLE financeiro_lancamentos (
    id SERIAL PRIMARY KEY,
    categoria_id INTEGER NOT NULL REFERENCES financeiro_categorias(id),
    tipo VARCHAR(20) NOT NULL,  -- 'receita' ou 'despesa'
    descricao TEXT NOT NULL,
    valor_usd DECIMAL(10,2) NOT NULL,
    valor_brl DECIMAL(10,2) NOT NULL,
    taxa_cambio DECIMAL(10,4) NOT NULL,
    data DATE NOT NULL,
    canal_id VARCHAR(24) REFERENCES yt_channels(channel_id),  -- Opcional
    recorrencia VARCHAR(20) DEFAULT 'unica',  -- unica, mensal, anual
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_lancamentos_categoria ON financeiro_lancamentos(categoria_id);
CREATE INDEX idx_lancamentos_data ON financeiro_lancamentos(data DESC);
CREATE INDEX idx_lancamentos_tipo ON financeiro_lancamentos(tipo);
CREATE INDEX idx_lancamentos_canal ON financeiro_lancamentos(canal_id);
```

**Query Comum:**
```sql
-- Lucro do mês
SELECT
    SUM(CASE WHEN tipo = 'receita' THEN valor_brl ELSE 0 END) as receitas,
    SUM(CASE WHEN tipo = 'despesa' THEN valor_brl ELSE 0 END) as despesas,
    SUM(CASE WHEN tipo = 'receita' THEN valor_brl ELSE -valor_brl END) as lucro
FROM financeiro_lancamentos
WHERE data >= DATE_TRUNC('month', CURRENT_DATE)
AND data < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month';
```

### 26. financeiro_taxas

**Descrição:** Histórico de taxas de câmbio

```sql
CREATE TABLE financeiro_taxas (
    id SERIAL PRIMARY KEY,
    data DATE NOT NULL UNIQUE,
    taxa_usd_brl DECIMAL(10,4) NOT NULL,
    fonte VARCHAR(50) DEFAULT 'AwesomeAPI',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index
CREATE INDEX idx_taxas_data ON financeiro_taxas(data DESC);
```

### 27. financeiro_metas

**Descrição:** Metas mensais

```sql
CREATE TABLE financeiro_metas (
    id SERIAL PRIMARY KEY,
    mes DATE NOT NULL UNIQUE,  -- Primeiro dia do mês
    meta_receita_brl DECIMAL(10,2) NOT NULL,
    meta_despesa_brl DECIMAL(10,2) NOT NULL,
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Materialized Views (Otimização 23/01/2026)

### Performance Alcançada
- **Dashboard:** 3000ms → 0.109ms (**27,522x mais rápido!**)
- **Com cache:** < 1ms (instantâneo)

### 1. mv_canal_video_stats

**Descrição:** Pré-calcula estatísticas de vídeos por canal

```sql
CREATE MATERIALIZED VIEW mv_canal_video_stats AS
SELECT
    v.canal_id,
    COUNT(*) as total_videos,
    SUM(v.views_atuais) as total_views,
    MAX(v.data_publicacao) as ultimo_video,
    AVG(v.views_atuais) as media_views
FROM videos_historico v
GROUP BY v.canal_id;

-- Index único para refresh CONCURRENTLY
CREATE UNIQUE INDEX idx_mv_canal_video_stats_canal_id
ON mv_canal_video_stats(canal_id);
```

### 2. mv_dashboard_completo

**Descrição:** Consolida TODOS dados do dashboard em uma tabela

```sql
CREATE MATERIALIZED VIEW mv_dashboard_completo AS
WITH latest_data AS (
    -- Dados mais recentes de cada canal
    SELECT DISTINCT ON (canal_id)
        canal_id, inscritos, views_30d, views_7d, videos_publicados, data_coleta
    FROM dados_canais_historico
    WHERE data_coleta >= CURRENT_DATE - INTERVAL '7 days'
    ORDER BY canal_id, data_coleta DESC
)
SELECT
    c.*,                           -- Todos campos de canais_monitorados
    ld.inscritos,                  -- Métricas atuais
    ld.views_30d as views_totais,
    ld.videos_publicados,
    -- Cálculos de growth (7 e 30 dias)
    COALESCE(ld.views_30d - wd.views_7d, 0) as views_diff_7d,
    COALESCE(ld.views_30d - md.views_30d, 0) as views_diff_30d,
    -- Estatísticas de vídeos
    COALESCE(vs.total_videos, 0) as total_videos,
    COALESCE(vs.total_views, 0) as total_video_views
FROM canais_monitorados c
LEFT JOIN latest_data ld ON c.id = ld.canal_id
LEFT JOIN week_ago_data wd ON c.id = wd.canal_id
LEFT JOIN month_ago_data md ON c.id = md.canal_id
LEFT JOIN mv_canal_video_stats vs ON c.id = vs.canal_id
WHERE c.status = 'ativo';

-- Indexes para performance
CREATE UNIQUE INDEX idx_mv_dashboard_canal_id ON mv_dashboard_completo(canal_id);
CREATE INDEX idx_mv_dashboard_tipo ON mv_dashboard_completo(tipo);
CREATE INDEX idx_mv_dashboard_subnicho ON mv_dashboard_completo(subnicho);
```

### 3. Função de Refresh Automático

```sql
CREATE OR REPLACE FUNCTION refresh_all_dashboard_mvs()
RETURNS TABLE(mv_name TEXT, status TEXT, rows_affected INTEGER)
AS $$
BEGIN
    -- Refresh MV de vídeos
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_canal_video_stats;

    -- Refresh MV principal do dashboard
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_dashboard_completo;

    -- Retorna status
    RETURN QUERY
    SELECT 'MVs atualizadas'::TEXT, 'SUCCESS'::TEXT,
           (SELECT COUNT(*)::INTEGER FROM mv_dashboard_completo);
END;
$$ LANGUAGE plpgsql;
```

### Uso no Backend

**database.py:**
```python
async def get_dashboard_from_mv(self, tipo=None, subnicho=None):
    """Busca dados da MV ao invés de paginar 368k registros"""
    query = self.supabase.table("mv_dashboard_completo").select("*")
    # Aplica filtros e retorna instantaneamente
```

**main.py:**
```python
# Cache de 24h implementado
dashboard_cache = {}
CACHE_DURATION = timedelta(hours=24)

# Primeiro acesso: busca da MV e cria cache
# Próximos acessos: servido do cache < 1ms
```

---

## Indexes e Performance

### Indexes Críticos

```sql
-- Canais (mais consultado)
CREATE INDEX idx_canais_status_tipo ON canais_monitorados(status, tipo);

-- Histórico (queries temporais)
CREATE INDEX idx_historico_canal_data_views ON dados_canais_historico(canal_id, data_coleta DESC, views_30d DESC);

-- Vídeos (busca por publicação)
CREATE INDEX idx_videos_publicacao_views ON videos_historico(data_publicacao DESC, views_atuais DESC);

-- Notificações (filtragem)
CREATE INDEX idx_notif_vista_data ON notificacoes(vista, data_disparo DESC);

-- Monetização (agregações)
CREATE INDEX idx_daily_channel_date_revenue ON yt_daily_metrics(channel_id, date DESC, revenue DESC);
```

### Vacuum e Maintenance

```sql
-- Vacuum automático (Supabase gerencia)
-- Mas pode forçar manualmente:
VACUUM ANALYZE canais_monitorados;
VACUUM ANALYZE dados_canais_historico;
VACUUM ANALYZE videos_historico;
```

---

## Queries Comuns

### 1. Dashboard Home

```sql
-- Estatísticas gerais
SELECT
    COUNT(*) FILTER (WHERE tipo = 'minerado') as canais_minerados,
    COUNT(*) FILTER (WHERE tipo = 'nosso') as canais_nossos,
    (SELECT COUNT(*) FROM videos_historico WHERE data_coleta = CURRENT_DATE) as videos_hoje,
    (SELECT COUNT(*) FROM notificacoes WHERE vista = FALSE) as notificacoes_nao_vistas
FROM canais_monitorados
WHERE status = 'ativo';
```

### 2. Top Canais por Performance

```sql
SELECT
    c.nome_canal,
    c.subnicho,
    h.views_30d,
    h.inscritos,
    h.engagement_rate,
    ROUND((h.views_30d::DECIMAL / NULLIF(h.inscritos, 0)) * 100, 2) as score
FROM canais_monitorados c
JOIN dados_canais_historico h ON c.id = h.canal_id
WHERE h.data_coleta = (
    SELECT MAX(data_coleta) FROM dados_canais_historico WHERE canal_id = c.id
)
AND c.status = 'ativo'
AND c.tipo = 'minerado'
ORDER BY score DESC
LIMIT 20;
```

### 3. Vídeos Virais (Últimos 7 Dias)

```sql
WITH latest_videos AS (
    SELECT DISTINCT ON (video_id)
        video_id,
        titulo,
        views_atuais,
        data_publicacao,
        canal_id
    FROM videos_historico
    WHERE data_publicacao >= CURRENT_DATE - INTERVAL '7 days'
    ORDER BY video_id, data_coleta DESC
)
SELECT
    lv.titulo,
    lv.views_atuais,
    c.nome_canal,
    c.subnicho
FROM latest_videos lv
JOIN canais_monitorados c ON lv.canal_id = c.id
WHERE lv.views_atuais >= 10000
ORDER BY lv.views_atuais DESC
LIMIT 50;
```

### 4. Revenue por Canal (Mês Atual)

```sql
SELECT
    ch.channel_name,
    ch.subnicho,
    SUM(dm.revenue) as revenue_usd,
    SUM(dm.revenue) * 5.50 as revenue_brl_estimado,
    SUM(dm.views) as views_total,
    ROUND(AVG(dm.rpm), 2) as rpm_medio
FROM yt_daily_metrics dm
JOIN yt_channels ch ON dm.channel_id = ch.channel_id
WHERE dm.date >= DATE_TRUNC('month', CURRENT_DATE)
AND dm.is_estimate = FALSE
GROUP BY ch.channel_name, ch.subnicho
ORDER BY revenue_usd DESC;
```

### 5. Crescimento de Inscritos (Últimos 30 Dias)

```sql
WITH dados_30d AS (
    SELECT
        canal_id,
        data_coleta,
        inscritos,
        LAG(inscritos) OVER (PARTITION BY canal_id ORDER BY data_coleta) as inscritos_anterior
    FROM dados_canais_historico
    WHERE data_coleta >= CURRENT_DATE - INTERVAL '30 days'
)
SELECT
    c.nome_canal,
    c.tipo,
    MAX(d.inscritos) as inscritos_atual,
    MAX(d.inscritos) - MIN(d.inscritos) as crescimento_30d,
    ROUND((MAX(d.inscritos)::DECIMAL - MIN(d.inscritos)) / NULLIF(MIN(d.inscritos), 0) * 100, 2) as crescimento_pct
FROM dados_30d d
JOIN canais_monitorados c ON d.canal_id = c.id
WHERE c.tipo = 'nosso'
GROUP BY c.nome_canal, c.tipo
ORDER BY crescimento_30d DESC;
```

---

## Backup e Restore

### Backup Automático (Supabase)

```bash
# Backups diários automáticos (Supabase gerencia)
# Retenção: 7 dias (plano gratuito)
```

### Backup Manual

```bash
# Via Supabase Dashboard
# Project Settings > Backups > Create Backup

# Ou via pg_dump (se tiver acesso direto)
pg_dump -h db.xxx.supabase.co -U postgres -d postgres > backup.sql
```

### Restore

```bash
# Via Supabase Dashboard
# Project Settings > Backups > Restore from Backup

# Ou via psql
psql -h db.xxx.supabase.co -U postgres -d postgres < backup.sql
```

---

## Referências

- **Supabase Docs:** https://supabase.com/docs/guides/database
- **PostgreSQL Docs:** https://www.postgresql.org/docs/
- **PostgREST Docs:** https://postgrest.org/

**Documentos Relacionados:**
- `04_ARQUITETURA_SISTEMA.md` - Visão geral da arquitetura
- `06_YOUTUBE_COLLECTOR.md` - Coleta de dados
- `09_MONETIZACAO_SISTEMA.md` - Sistema OAuth

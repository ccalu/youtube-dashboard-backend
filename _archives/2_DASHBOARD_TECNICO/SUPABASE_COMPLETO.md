# SUPABASE - CEREBRO DA CONTENT FACTORY

## ACESSO RAPIDO

```
URL:       https://prvkmzstyedepvlbppyo.supabase.co
Dashboard: https://supabase.com/dashboard/project/prvkmzstyedepvlbppyo
Anon Key:  eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBydmttenN0eWVkZXB2bGJwcHlvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQxNDY3MTQsImV4cCI6MjA1OTcyMjcxNH0.T0aspHrF0tz1G6iVOBIO3zgvs1g5vvQcb25jhGriQGo
```

---

## VISAO GERAL (Janeiro 2025)

| Metrica | Valor |
|---------|-------|
| **Total de Canais Monitorados** | 344 |
| **Canais Nossos** | 51 |
| **Canais Minerados** | 293 |
| **Canais Monetizados** | 16 |
| **Videos Coletados** | ~400.000 |
| **Subnichos Ativos** | 10 |
| **Idiomas Monitorados** | 11 |

---

## DUAS TABELAS PRINCIPAIS

O sistema tem duas tabelas de canais com propositos diferentes:

### 1. canais_monitorados (Mineracao)

**Proposito:** Monitorar TODOS os canais (nossos + concorrentes)
**Total:** 344 canais (51 nossos + 293 minerados)

```sql
-- Estrutura
CREATE TABLE canais_monitorados (
    id SERIAL PRIMARY KEY,
    nome_canal VARCHAR(200) NOT NULL,
    url_canal TEXT NOT NULL UNIQUE,
    subnicho VARCHAR(100) NOT NULL,
    lingua VARCHAR(50) DEFAULT 'English',
    tipo VARCHAR(20) DEFAULT 'minerado',  -- 'nosso' ou 'minerado'
    status VARCHAR(20) DEFAULT 'ativo',
    ultima_coleta TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 2. yt_channels (Monetizacao)

**Proposito:** Gerenciar canais NOSSOS para coleta OAuth (revenue, analytics)
**Total:** 52 canais (16 monetizados ativos)

```sql
-- Estrutura
CREATE TABLE yt_channels (
    id SERIAL PRIMARY KEY,
    channel_id VARCHAR(24) NOT NULL UNIQUE,  -- UCxxxxx
    channel_name VARCHAR(200) NOT NULL,
    is_monetized BOOLEAN DEFAULT TRUE,
    subnicho VARCHAR(100),
    lingua VARCHAR(10),
    total_subscribers INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Diferenca entre elas

| Aspecto | canais_monitorados | yt_channels |
|---------|-------------------|-------------|
| **Usa para** | Mineracao (coleta publica) | Monetizacao (OAuth) |
| **Contem** | Nossos + Concorrentes | So nossos |
| **Coleta** | YouTube API publica | YouTube Analytics API (OAuth) |
| **Dados** | Views, likes, titulos | Revenue, RPM, demographics |
| **Autenticacao** | API Key | OAuth tokens |

---

## SUBNICHOS E DISTRIBUICAO

| Subnicho | Total | Nossos | Minerados |
|----------|-------|--------|-----------|
| Psicologia & Mindset | 68 | 6 | 62 |
| Relatos de Guerra | 65 | 9 | 56 |
| Historias Sombrias | 63 | 12 | 51 |
| Empreendedorismo | 32 | 6 | 26 |
| Conspiracao | 25 | 0 | 25 |
| Misterios | 23 | 6 | 17 |
| Guerras e Civilizacoes | 20 | 7 | 13 |
| Pessoas Desaparecidas | 19 | 0 | 19 |
| Terror | 16 | 5 | 11 |
| Noticias e Atualidade | 13 | 0 | 13 |

---

## IDIOMAS MONITORADOS

| Lingua | Canais |
|--------|--------|
| Ingles | 202 |
| Espanhol | 57 |
| Portugues | 26 |
| Frances | 25 |
| Italiano | 20 |
| Alemao | 4 |
| Coreano | 3 |
| Russo | 3 |
| Japones | 2 |
| Arabe | 1 |
| Turco | 1 |

---

## NOSSOS 51 CANAIS

### EMPREENDEDORISMO (6)
| ID | Nome | URL | Lingua |
|----|------|-----|--------|
| 860 | Financial Dynasties | @FinancialDynasties | Ingles |
| 861 | Dinastias Financieras | @DinastiasFinancieras | Espanhol |
| 862 | Dinastie Finanziarie | @DinastieFinanziarie | Italiano |
| 863 | Dynasties Financieres | UCdNsmU5wcXG1d313tXdu3Ug | Frances |
| 864 | Reis do Capital | @ArquitetosdoPoderYT | Portugues |
| 878 | Konige des Kapitals | @KonigedesKapitals | Alemao |

### GUERRAS E CIVILIZACOES (7)
| ID | Nome | URL | Lingua |
|----|------|-----|--------|
| 871 | Fallen Empires | @FallenEmpiresYT | Ingles |
| 872 | El Legado Eterno | @ElLegadoEternoYT | Espanhol |
| 873 | Asche der Imperien | @AschederImperien | Alemao |
| 874 | Empires Dechus | @EmpiresDechus | Frances |
| 875 | Imperios Caidos | @ImperiosCaidosYT | Portugues |
| 876 | Imperi Caduti | @ImperiCaduti | Italiano |
| 877 | 제국의 몰락 | @제국의몰락YT | Coreano |

### HISTORIAS SOMBRIAS (12)
| ID | Nome | URL | Lingua |
|----|------|-----|--------|
| 271 | Tales of Antiquity | @TalesofAntiquityt | Ingles |
| 272 | Verborgene Geschichten | @VerborgeneGeschichtenYT | Alemao |
| 274 | Chroniques Anciennes | @ChroniquesAnciennesfr | Frances |
| 78 | Relatos Oscuros | @RelatosOscurosYTV | Espanhol |
| 79 | Leggende Sinistre | @LeggendeSinistre | Italiano |
| 81 | Contes Sinistres | @ContesSinistres | Frances |
| 276 | Sombras da Historia | @brSombrasdaHistoria | Portugues |
| 390 | Reis Perversos | @ReisPerversos | Portugues |
| 460 | Tainy Proshlogo | @TyomnyeSkazaniya | Russo |
| 762 | 古代の物語 | @Kodainomonogatari | Japones |
| 835 | 그림자의 왕국 | @GeurimjauiWangguk | Coreano |
| 836 | الأساطير المحرمة | UCw609uQ15kHcmAXh-wBhajw | Arabe |

### MISTERIOS (6)
| ID | Nome | URL | Lingua |
|----|------|-----|--------|
| 668 | Archived Mysteries | @Archivedmysteriesyt | Ingles |
| 669 | Enigmas Reales | @EnigmasRealesyt | Espanhol |
| 672 | Misterios Arquivados | @MisteriosArquivadosyt | Portugues |
| 688 | Chroniques du Mystere | @ChroniquesduMystereyt | Frances |
| 865 | Misteri Archiviati | @MisteriArchiviati | Italiano |
| 866 | Нераскрытые Тайны | UC2X74_c3YXEIuJp4Lr22MoA | Russo |

### PSICOLOGIA & MINDSET (6)
| ID | Nome | URL | Lingua |
|----|------|-----|--------|
| 437 | Stick to the Plan | @SticktothePlanYT | Ingles |
| 455 | El Camino | @ElCaminoYTV | Espanhol |
| 456 | Kural Yok | @KuralYokYT | Turco |
| 644 | Sans Limites | @SansLimitesyt | Frances |
| 645 | Traccia Interiore | @TracciaInteriore | Italiano |
| 646 | O Essencial | @OEssencialytv | Portugues |

### RELATOS DE GUERRA (9)
| ID | Nome | URL | Lingua |
|----|------|-----|--------|
| 64 | Forgotten Frontlines | @ForgottenFrontlinesYT | Ingles |
| 65 | Batallas Silenciadas | @BatallasSilenciadas | Espanhol |
| 66 | Kriegsstimmen | @Kriegsstimmen | Alemao |
| 68 | Fronti Dimenticati | @FrontiDimenticati | Italiano |
| 264 | Archives de Guerre | @ArchivesdeGuerreYT | Frances |
| 389 | Cronicas da Guerra | @CronicasDaGuerraYT | Portugues |
| 459 | Golosa Voyny | @GolosaVoyny | Russo |
| 879 | 전쟁 기록관 | @yt0493-i9e | Coreano |
| 880 | 戦争記録館 | @戦争記録館-yt | Japones |

### TERROR (5)
| ID | Nome | URL | Lingua |
|----|------|-----|--------|
| 85 | The Whispering Fear | @TheWhisperingFear | Ingles |
| 86 | Historias Malditas | @HistoriasMalditasYT | Espanhol |
| 87 | Il Sussurro del Terrore | @IlSussurroDelTerrore | Italiano |
| 90 | Ne Eteins Pas la Lumiere | @NeEteinsPaslaLumiere | Frances |
| 388 | Relatos Obscuros | @ApenasUmPesadeloYT | Portugues |

---

## REGRAS DE NOTIFICACAO

| ID | Nome | Views Min | Periodo | Status |
|----|------|-----------|---------|--------|
| 7 | 7k em 24h | 7.000 | 1 dia | Ativa |
| 8 | 15k em 5 dias | 15.000 | 5 dias | Ativa |
| 9 | 50k em 15 dias | 50.000 | 15 dias | Ativa |
| 10 | 200k em 30 dias | 200.000 | 30 dias | Ativa |
| 14 | Clonar Tema (nosso) | 5.000 | 7 dias | Ativa |

---

## TODAS AS TABELAS (28 total)

```
MINERACAO (6 tabelas)
├── canais_monitorados         → Canais YouTube (344)
├── dados_canais_historico     → Metricas diarias
├── videos_historico           → Videos coletados (~400k)
├── coletas_historico          → Logs de coleta
├── favoritos                  → Canais/videos favoritos
└── transcriptions             → Cache de transcricoes

NOTIFICACOES (2 tabelas)
├── regras_notificacoes        → Regras configuraveis
└── notificacoes               → Alertas gerados

MONETIZACAO (14 tabelas)
├── yt_channels                → Canais monetizados (52)
├── yt_oauth_tokens            → Access/refresh tokens (RLS)
├── yt_proxy_credentials       → Client ID/secret proxy (RLS)
├── yt_channel_credentials     → Client ID/secret por canal (RLS)
├── yt_daily_metrics           → Revenue diario
├── yt_country_metrics         → Revenue por pais
├── yt_video_metrics           → Revenue por video
├── yt_video_daily             → Historico diario videos
├── yt_traffic_summary         → Fontes de trafego
├── yt_search_analytics        → Termos de busca
├── yt_suggested_sources       → Videos que recomendam
├── yt_demographics            → Idade e genero
├── yt_device_metrics          → Dispositivos
└── yt_collection_logs         → Logs coleta OAuth

UPLOAD (1 tabela)
└── yt_upload_queue            → Fila de uploads

FINANCEIRO (4 tabelas)
├── financeiro_categorias      → Categorias
├── financeiro_lancamentos     → Receitas/despesas
├── financeiro_taxas           → Cambio
└── financeiro_metas           → Metas mensais

ANALYTICS (1 tabela)
└── subniche_trends_snapshot   → Tendencias por subnicho
```

---

## QUERIES MAIS USADAS

### Listar Nossos Canais
```sql
SELECT id, nome_canal, url_canal, subnicho, lingua
FROM canais_monitorados
WHERE tipo = 'nosso' AND status = 'ativo'
ORDER BY subnicho, lingua;
```

### Atualizar Nome de Canal
```sql
UPDATE canais_monitorados
SET nome_canal = 'Novo Nome'
WHERE id = 123;
```

### Atualizar Subnicho
```sql
UPDATE canais_monitorados
SET subnicho = 'Terror'
WHERE id = 123;
```

### Estatisticas por Subnicho
```sql
SELECT
    subnicho,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE tipo = 'nosso') as nossos,
    COUNT(*) FILTER (WHERE tipo = 'minerado') as minerados
FROM canais_monitorados
WHERE status = 'ativo'
GROUP BY subnicho
ORDER BY total DESC;
```

### Notificacoes Pendentes
```sql
SELECT * FROM notificacoes
WHERE vista = FALSE
ORDER BY data_disparo DESC;
```

---

## ACESSO VIA PYTHON

```python
from supabase import create_client

SUPABASE_URL = "https://prvkmzstyedepvlbppyo.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Buscar canais
response = supabase.table("canais_monitorados").select("*").execute()
canais = response.data

# Filtrar nossos
nossos = supabase.table("canais_monitorados").select("*").eq("tipo", "nosso").execute()

# Atualizar
supabase.table("canais_monitorados").update({
    "nome_canal": "Novo Nome"
}).eq("id", 123).execute()
```

---

## SEGURANCA

### Tabelas Protegidas (RLS)

Estas tabelas exigem `SERVICE_ROLE_KEY`:
- `yt_oauth_tokens`
- `yt_proxy_credentials`
- `yt_channel_credentials`

```python
# Para tabelas protegidas
supabase_admin = create_client(SUPABASE_URL, SERVICE_ROLE_KEY)
```

### Nunca Expor
- SERVICE_ROLE_KEY em codigo publico
- Tokens OAuth
- Client secrets

---

## TROUBLESHOOTING

| Erro | Solucao |
|------|---------|
| "No API key provided" | Verificar SUPABASE_KEY |
| "JWT expired" | Refresh automatico ou verificar SERVICE_ROLE_KEY |
| "permission denied" | Usar SERVICE_ROLE_KEY para tabelas RLS |
| "duplicate key value" | Usar upsert() ao inves de insert() |

---

**Documento consolidado**: Janeiro 2025
**Fonte**: SUPABASE_GUIA_COMPLETO.md + SUPABASE_CEREBRO_OPERACAO.md
**Autor**: Claude Code

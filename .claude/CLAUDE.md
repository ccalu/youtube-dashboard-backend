# DASHBOARD DE MINERAÇÃO - Backend Python

## 📍 VOCÊ ESTÁ NO: Backend do Dashboard de Mineração
**Localização:** D:\ContentFactory\youtube-dashboard-backend
**Linguagem:** Python (FastAPI)
**Deploy:** Railway

## 🎯 O QUE ESTE BACKEND FAZ:
API REST que gerencia coleta de dados YouTube, notificações e transcrições.

## 📂 ARQUIVOS PRINCIPAIS:
- `main.py` - FastAPI app + endpoints (1122 linhas)
- `collector.py` - YouTube collector + rotação de API keys (727 linhas)
- `notifier.py` - Sistema de notificações inteligente (394 linhas)
- `database.py` - Client Supabase + queries
- `requirements.txt` - Dependências Python

## 🔗 INTEGRAÇÕES:
- **Supabase:** PostgreSQL (credenciais em .env)
- **YouTube API:** 20 keys (KEY_3 a 10 + KEY_21 a 32) - NÃO ESTÃO AQUI! (Railway)
- **Servidor M5:** https://transcription.2growai.com.br

## ⚠️ CREDENCIAIS LOCAIS (.env):
- `SUPABASE_URL` - Configurado ✅
- `SUPABASE_KEY` - Configurado ✅
- `YOUTUBE_API_KEY_X` - NÃO configuradas localmente (só Railway)

**IMPORTANTE:**
- Para testar localmente: precisa configurar pelo menos 1 YouTube API key
- Para produção: usar Railway (já tem tudo configurado)
- Arquivo .env está em .gitignore (não sobe pro GitHub)

## 🚀 RODAR LOCALMENTE:
```bash
# Instalar dependências
pip install -r requirements.txt --break-system-packages

# Rodar servidor
python main.py
```

**Porta:** 8000 (local) ou PORT env var (Railway)

## 📊 ENDPOINTS PRINCIPAIS:

### Canais & Vídeos:
- `GET /api/canais` - Lista canais minerados (com filtros)
- `GET /api/canais-tabela` - **NOVO!** Nossos canais agrupados por subnicho (para aba Tabela)
- `GET /api/videos` - Lista vídeos (com filtros)
- `POST /api/canais` - Adiciona novo canal

### Notificações:
- `GET /api/notificacoes` - Lista notificações (com filtros)
- `POST /api/force-notifier` - Força disparo manual de notificações
- `PATCH /api/notificacoes/{id}/vista` - Marca notificação como vista
- `POST /api/notificacoes/marcar-todas-vistas` - Marca todas como vistas

### Análise:
- `GET /api/subniche-trends` - Tendências por subnicho
- `GET /api/system-stats` - Estatísticas do sistema

Ver documentação completa em: D:\ContentFactory\.claude\DASHBOARD_MINERACAO.md

## 🔧 PARA CLAUDE CODE:
- Você pode ler/editar código Python
- Testar conexão Supabase (tem credenciais)
- NÃO pode testar coleta YouTube (faltam API keys locais)
- Pode criar novos endpoints
- Pode melhorar lógica existente
- SEMPRE fazer backup antes de mudanças grandes

## 🆕 ATUALIZAÇÕES RECENTES (22/01/2026):

### 0. sync.py v4.0 - Verificação Obrigatória de Documentação
**Arquivo:** `sync.py`

- ✅ Novo passo [0/7]: Verifica se docs foram atualizados ANTES de commitar
- ✅ Mapeamento código → documentação (main.py → 08_API_ENDPOINTS, etc.)
- ✅ Alerta visual se docs estão faltando
- ✅ Pergunta confirmação antes de continuar sem docs
- ✅ Lista docs obrigatórios: `.claude/CLAUDE.md`, `CHANGELOG.md`

**Workflow obrigatório:**
```
1. Alterar código
2. ATUALIZAR DOCS (.claude/CLAUDE.md, CHANGELOG.md, 2_DASHBOARD_TECNICO/*.md)
3. python sync.py
4. Railway deploya
```

### 1. Bug Fix: Colisão de Variável `offset` (CRÍTICO)
**Arquivo:** `database.py` (linhas 342, 348, 359)
**Função:** `get_canais_with_filters()`

- **Problema:** Variável `offset` do loop de paginação sobrescrevia o parâmetro `offset` da função
- **Sintoma:** API `/api/canais` retornava `[]` (array vazio)
- **Solução:** Renomeada para `pagination_offset`
- **Commit:** `8bd8777`

### 2. Bug Fix: Cálculo de `inscritos_diff`
**Arquivo:** `database.py` (linhas 427-429)

- **Problema:** Assumia que `datas_disponiveis[1]` era "ontem", mas podia ser de vários dias atrás
- **Sintoma:** `inscritos_diff` mostrava diferença errada ou nula
- **Solução:** Agora busca especificamente a data de ontem: `data_ontem_str = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()`
- **Commit:** `809e596`

### 3. Bug Fix: Paginação do Histórico
**Arquivo:** `database.py`

- **Problema:** Query não buscava todos os registros do histórico
- **Solução:** Corrigida lógica de paginação para buscar todos os records
- **Commit:** `79de42f`

### 4. Campos de Views Growth/Diff
**Endpoint:** `GET /api/canais`

Novos campos disponíveis (calculados automaticamente):
- `views_growth_7d` - Crescimento % de views nos últimos 7 dias
- `views_growth_30d` - Crescimento % de views nos últimos 30 dias
- `views_diff_7d` - Diferença absoluta de views (7 dias)
- `views_diff_30d` - Diferença absoluta de views (30 dias)

**Status Atual:**
- 300 canais ativos retornando dados
- 228 canais com `views_growth_7d`
- 287 canais com `inscritos_diff`

---

## 📜 ATUALIZAÇÕES ANTERIORES (17/01/2026):

### 1. Otimização do Sistema de Coleta (50% menos API calls)
**Arquivos:** `collector.py`, `main.py`, `database.py`

- ✅ `get_canal_data()` agora retorna tuple `(stats, videos)` - elimina duplicação
- ✅ Timeout aumentado de 30s para 60s
- ✅ Economia de ~50% da quota diária

### 2. Tracking de Falhas de Coleta
**Novos campos em `canais_monitorados`:**
- `coleta_falhas_consecutivas` (INTEGER)
- `coleta_ultimo_erro` (TEXT)
- `coleta_ultimo_sucesso` (TIMESTAMP)

**Novas funções em `database.py`:**
- `marcar_coleta_sucesso()` - reseta contador de falhas
- `marcar_coleta_falha()` - incrementa contador e salva erro
- `get_canais_problematicos()` - lista canais com falhas

### 3. Novos Endpoints de Diagnóstico
- `GET /api/canais/problematicos` - Lista canais com erros de coleta
- `GET /api/canais/sem-coleta-recente` - Canais sem coleta nos últimos X dias

### 4. Melhorias no Endpoint `/api/coletas/historico`
Agora retorna:
```json
{
  "historico": [...],
  "canais_com_erro": {
    "total": 8,
    "lista": [
      {
        "nome": "Canal X",
        "subnicho": "Terror",
        "tipo": "nosso",
        "erro": "Dados não salvos",
        "lingua": "portuguese",
        "url_canal": "https://youtube.com/@..."
      }
    ]
  },
  "quota_info": {
    "videos_coletados": 6029,
    ...
  }
}
```

### 5. Limpeza de Canais
- Deletados 24 canais problemáticos (22 minerados inativos + 2 com URL inválida)
- Total atual: **305 canais ativos**

---

## 📜 ATUALIZAÇÕES ANTERIORES (02/12/2025):

### 1. Nova Feature: Aba "Tabela" (Nossos Canais)
**Endpoint:** `GET /api/canais-tabela`
- Retorna canais `tipo="nosso"` agrupados por subnicho
- Ordenação por desempenho: **melhor → menor → zero → nulo**
- Response inclui: `inscritos`, `inscritos_diff` (ganho ontem→hoje), `ultima_coleta`
- Frontend pronto: `frontend-code/TabelaCanais.tsx` (366 linhas, mobile-first)
- Documentação: `INTEGRACAO_ABA_TABELA.md`

**Lógica de Ordenação:**
- Categoria 0: Positivos (+35, +10, +2...) - Melhor no topo
- Categoria 1: Negativos (-5, -10...) - Perdas
- Categoria 2: Zero (0) - Sem mudança
- Categoria 3: Null (--) - Sem dados, sempre no final
- Tiebreaker: Maior número de inscritos

### 2. Sistema de Notificações - Bugs Corrigidos
**Arquivo:** `notifier.py`
- ✅ Query SQL otimizada (dados em uma query só)
- ✅ Filtro de subnicho case-insensitive
- ✅ Permite re-notificação para milestones maiores
- **Status:** 100% funcional (69 notificações criadas no teste)

### 3. Expansão de API Keys
**Arquivo:** `collector.py`
- ✅ Adicionadas 8 novas chaves (KEY_25 a KEY_32)
- ✅ Total: 20 chaves (antes: 12)
- ✅ Capacidade +67% (~2M requisições/dia)
- **Configuração:** Railway (variáveis de ambiente)

### 4. Arquivos de Referência Criados:
- `frontend-code/TabelaCanais.tsx` - Componente React completo
- `INTEGRACAO_ABA_TABELA.md` - Guia de integração Lovable
- `FIX_ORDENACAO_TABELA.md` - Documentação técnica do sorting
- `VALIDACAO_API_KEYS.md` - Validação das 8 novas chaves

## 🎯 INTEGRAÇÃO FUTURA:
Este backend será integrado com o Sistema Musical (D:\ContentFactory\music_queue_system)

Para documentação completa do Dashboard, consulte:
`D:\ContentFactory\.claude\DASHBOARD_MINERACAO.md`

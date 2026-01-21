# 🎯 SISTEMA DE DESCOBERTA INTELIGENTE DE CANAIS FACELESS
## Documentação Completa - Content Factory

**Data:** 21 de Janeiro de 2026
**Versão:** 1.0 - Especificação Final Aprovada
**Status:** Planejamento Completo - Pronto para Implementação

---

## 📚 ÍNDICE

1. [Contexto e Histórico](#1-contexto-e-histórico)
2. [Problema Identificado](#2-problema-identificado)
3. [Solução Proposta](#3-solução-proposta)
4. [Iterações e Ajustes](#4-iterações-e-ajustes)
5. [Especificação Técnica Final](#5-especificação-técnica-final)
6. [Descoberta de Canais](#6-descoberta-de-canais)
7. [Análise Inteligente (GPT-4)](#7-análise-inteligente-gpt-4)
8. [Detecção de Tendências](#8-detecção-de-tendências)
9. [Interface do Usuário](#9-interface-do-usuário)
10. [Arquitetura do Sistema](#10-arquitetura-do-sistema)
11. [Schema do Banco de Dados](#11-schema-do-banco-de-dados)
12. [Custos e Viabilidade](#12-custos-e-viabilidade)
13. [Resumo Executivo](#13-resumo-executivo)
14. [Perguntas para Discussão](#14-perguntas-para-discussão)
15. [Roadmap de Implementação](#15-roadmap-de-implementação)

---

## 1. CONTEXTO E HISTÓRICO

### 1.1 Origem da Conversa

**Objetivo inicial:** Criar sistema de mineração automática de canais similar ao NextLev.

**Evolução da discussão:**
- Iniciou com ideia de integrar API do NextLev
- Descoberto que NextLev não tem API pública confiável
- Pivotou para sistema próprio usando YouTube API + GPT
- Iterações múltiplas para refinar escopo e realismo
- Especificação final focada em viabilidade e praticidade

### 1.2 Contexto do Negócio

**Content Factory - Operação Atual:**
- **50 canais faceless** próprios operando
- **263 canais** monitorados (50 nossos + 213 concorrentes)
- **500K vídeos** coletados historicamente
- **10+ idiomas** de operação
- **100-130 vídeos/dia** de capacidade produtiva

**Subnichos Ativos (10):**
1. Terror (16 canais totais)
2. Mistérios (23 canais)
3. Histórias Sombrias (63 canais)
4. Relatos de Guerra (65 canais)
5. Guerras e Civilizações (20 canais)
6. Psicologia & Mindset (68 canais)
7. Empreendedorismo (32 canais)
8. Conspiração (25 canais - minerados)
9. Pessoas Desaparecidas (19 canais - minerados)
10. Notícias e Atualidade (13 canais - minerados)

**Subnichos Principais (7):**
- Relatos de Guerra ⚔️
- Guerras e Civilizações 🏛️
- Empreendedorismo 💼
- Terror 👻
- Mistérios 🔍
- Psicologia e Mindset 🧠
- Histórias Sombrias 💀

### 1.3 Recursos Disponíveis

**APIs e Quotas:**
- **YouTube Data API v3:** 20 chaves (KEY_3-10, KEY_21-32)
  - Quota: 200.000 units/dia por conjunto
  - Total disponível: ~6.000.000 units/mês
  - Uso atual: ~15% (sobra 85%)

- **GPT-4 (OpenAI):** 1.000.000 tokens/dia GRÁTIS
  - Total semanal: 7.000.000 tokens
  - Uso atual sistema comentários: ~10-15%
  - Sobra: ~85-90%

**Infraestrutura:**
- Backend: Python FastAPI (Railway)
- Database: Supabase PostgreSQL
- Frontend: React/TypeScript (Lovable)
- Servidor de Transcrição: M5 (próprio)

### 1.4 Definições Importantes

**Canal Faceless:**
- **Definição:** Canal YouTube sem pessoa aparecendo
- **Características:**
  - Narração por IA (ElevenLabs, etc)
  - Imagens/vídeos gerados por IA ou stock footage
  - Pode ter vídeos curtos (2-3 takes) gerados por IA (Heygen)
  - Temas: Histórias, terror, mistérios, civilizações, guerras, etc.

**Canal NÃO Faceless:**
- Vlogs (pessoa aparece)
- Gameplays com webcam
- Reviews com apresentador
- Conteúdo que PRECISA filmagem (futebol, esportes)
- Tutoriais práticos com pessoa

---

## 2. PROBLEMA IDENTIFICADO

### 2.1 Situação Atual

**Descoberta de Canais:**
- ✅ **100% manual** usando NextLev
- ✅ Busca manual no YouTube um por um
- ✅ Cellibs faz mineração ocasional
- ❌ Não é sistemático
- ❌ Não é escalável
- ❌ Perde oportunidades

**Detecção de Tendências:**
- ❌ Não existe processo automatizado
- ❌ Descoberta reativa (após tendência consolidada)
- ❌ Sem previsão de micro-nichos emergentes
- ❌ Janelas de oportunidade perdidas

**Limitações do NextLev:**
- ❌ Ferramenta manual (necessita ação humana)
- ❌ Não tem API pública documentada
- ❌ Dados genéricos (não personalizado)
- ❌ Não integra com sistemas internos
- ❌ Custo: $13/mês (pequeno, mas recorrente)

### 2.2 Impacto no Negócio

**Oportunidades Perdidas:**
- Novos micro-nichos surgem e descobrem tarde
- Concorrentes entram primeiro em tendências
- Tempo humano gasto em pesquisa manual
- Decisões sem dados suficientes

**Exemplo Real:**
```
Micro-nicho "Terror Japonês" começa a viralizar
│
├─ Dia 1-7: Primeiros vídeos viralizando (5-10 canais)
├─ Dia 8-15: Tendência consolidando (15-20 canais)
├─ Dia 16-30: Saturação começa
│
└─ Content Factory descobre: Dia 25-30 (TARDE!)
    Resultado: Janela de oportunidade perdida
```

### 2.3 O Que Precisa Mudar

**De:**
- ⚪ Descoberta manual e ocasional
- ⚪ Reativo (após tendências consolidadas)
- ⚪ Sem dados estruturados
- ⚪ Dependente de tempo humano

**Para:**
- 🟢 Descoberta automática e contínua
- 🟢 Preditivo (antes de saturar)
- 🟢 Dados estruturados e validáveis
- 🟢 Sistema 24/7 trabalhando

---

## 3. SOLUÇÃO PROPOSTA

### 3.1 Visão Geral

**Nome:** Sistema de Descoberta Inteligente de Canais Faceless

**Objetivo:**
Criar um "radar de mercado" que funciona 24/7 descobrindo:
1. Canais faceless similares aos nossos
2. Micro-nichos emergentes
3. Tendências viralizando AGORA
4. Tendências que vão viralizar em 10-15 dias

**Princípio:**
Sistema ASSISTENTE, não substituto. Cellibs sempre valida antes de adicionar.

### 3.2 Pilares do Sistema

**PILAR 1: Descoberta Multi-Fonte**
- Featured Channels Network (YouTube API)
- Keyword Clusters (análise de dados internos)
- Google Trends Integration

**PILAR 2: Análise Inteligente**
- GPT-4 analisa cada canal descoberto
- Classifica por nicho/subnicho/micronichos
- Score de confiança e viabilidade
- Comparação com canais de referência

**PILAR 3: Interface Validável**
- UI limpa para aprovação rápida
- Evidências visíveis (thumbnails, títulos, métricas)
- Links para verificação manual
- 1 clique para adicionar ao dashboard

### 3.3 Fluxo Completo

```
┌─────────────────────────────────────────────────┐
│  DISCOVERY ENGINE (roda 3x/semana)              │
│  ├─ Featured Channels                           │
│  ├─ Keyword Clusters                            │
│  └─ Google Trends                               │
└─────────────────┬───────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────┐
│  FILTROS BÁSICOS (Python)                       │
│  ├─ >1000 inscritos                             │
│  ├─ Pelo menos 1 vídeo >5K views                │
│  ├─ Upload ativo (<7 dias)                      │
│  └─ Remove: gameplay, futebol, etc              │
└─────────────────┬───────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────┐
│  ANÁLISE GPT-4 (batch de 50-100 canais)        │
│  ├─ Descrição do canal                          │
│  ├─ Últimos 10-15 títulos                       │
│  ├─ Padrões vs canais de referência             │
│  └─ Score + classificação                       │
└─────────────────┬───────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────┐
│  BANCO DE DADOS (Supabase)                      │
│  ├─ Tabela: canais_descobertos                  │
│  ├─ Tabela: videos_canais_descobertos           │
│  └─ Tabela: tendencias_emergentes               │
└─────────────────┬───────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────┐
│  INTERFACE (Dashboard - Nova Aba)               │
│  ├─ Filtros por subnicho                        │
│  ├─ Cards de canais descobertos                 │
│  ├─ Modal detalhado (thumbs + análise)          │
│  └─ Botão: Adicionar ao Dashboard               │
└─────────────────┬───────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────┐
│  CELLIBS VALIDA                                 │
│  ├─ Revisa canais sugeridos                     │
│  ├─ Verifica evidências                         │
│  ├─ Aprova/Rejeita                              │
│  └─ Adiciona ao monitoramento                   │
└─────────────────────────────────────────────────┘
```

---

## 4. ITERAÇÕES E AJUSTES

### 4.1 Primeira Proposta (Rejeitada)

**Problemas identificados:**

1. **Análise de Thumbnails Visual**
   - Proposta: Análise de cor de pele em thumbnails
   - Feedback: "Muito básica, muitos falsos positivos"
   - Decisão: ❌ CORTADO

2. **Audience Overlap (Menções em Comentários)**
   - Proposta: Minerar @mentions de outros canais
   - Feedback: "Raro ter menções úteis, não compensa"
   - Decisão: ❌ CORTADO

3. **Análise de Transcrições**
   - Proposta: GPT analisa narrativa dos vídeos
   - Feedback: "Overkill, Arthur já faz isso manualmente"
   - Decisão: ❌ CORTADO

4. **Social Listening (Reddit/Twitter/TikTok)**
   - Proposta: Monitorar redes sociais
   - Feedback: "Muito ruído, pouco sinal útil"
   - Decisão: ❌ CORTADO (só Reddit em consideração)

5. **Suposições sobre Formato**
   - Proposta: GPT inferir formato de produção
   - Feedback: "GPT não vê vídeos, não pode supor formato"
   - Decisão: ✅ AJUSTADO - Só análise de texto

### 4.2 Ajustes Realizados

**AJUSTE 1: Filtros de Upload**
```
ANTES: Upload ativo (1 vídeo/mês)
DEPOIS: Upload ativo (1 vídeo nos últimos 7 dias)
MOTIVO: Garantir canais realmente ativos
```

**AJUSTE 2: Análise GPT Realista**
```
ANTES: GPT analisa thumbnails, formato, qualidade visual
DEPOIS: GPT analisa APENAS descrição + títulos + padrões textuais
MOTIVO: GPT não vê vídeos, evitar suposições falsas
```

**AJUSTE 3: Keyword Expansion**
```
ANTES: Limitado a keywords já detectadas
DEPOIS: GPT expande para termos similares/relacionados
MOTIVO: Descobrir nichos adjacentes, não só replicar
```

**AJUSTE 4: Foco em Tendências Dual**
```
ANTES: Só previsão futura (10-15 dias)
DEPOIS: Viralizando AGORA + Previsão futura
MOTIVO: Não perder oportunidades imediatas
```

**AJUSTE 5: Subnichos do Banco**
```
ANTES: Inventar/supor subnichos
DEPOIS: Usar os 10 subnichos REAIS do banco de dados
MOTIVO: Alinhamento com operação real
```

**AJUSTE 6: Botões Realistas na UI**
```
ANTES: [CRIAR CANAL NESSE NICHO] (Claude não faz isso)
DEPOIS: [VER CANAIS] [ADICIONAR AO MONITORAMENTO]
MOTIVO: Só funcionalidades viáveis
```

### 4.3 Correções de Escopo

**Features REMOVIDAS (não agregam valor):**
- ❌ Visual Similarity Search (complexo, impreciso)
- ❌ Comment Mining de menções
- ❌ Análise de transcrições
- ❌ Monitoramento Twitter/TikTok
- ❌ Shorts analysis (vocês não fazem shorts)

**Features MANTIDAS (essenciais):**
- ✅ Featured Channels Network
- ✅ Keyword Clusters
- ✅ Google Trends
- ✅ Análise GPT-4 (descrição + títulos)
- ✅ UI limpa e validável

---

## 5. ESPECIFICAÇÃO TÉCNICA FINAL

### 5.1 Requisitos Funcionais

**RF01 - Descoberta de Canais**
- Sistema DEVE descobrir 50-100 canais por execução
- Sistema DEVE filtrar canais >1000 inscritos
- Sistema DEVE verificar upload ativo (<7 dias)
- Sistema DEVE remover canais de gameplay/futebol

**RF02 - Análise Inteligente**
- Sistema DEVE usar GPT-4 para análise
- Sistema DEVE classificar nicho/subnicho/micronichos
- Sistema DEVE calcular score 0-100
- Sistema DEVE comparar com canais de referência

**RF03 - Detecção de Tendências**
- Sistema DEVE detectar keyword clusters emergentes
- Sistema DEVE integrar Google Trends
- Sistema DEVE identificar tendências AGORA + futuro (10-15 dias)
- Sistema DEVE calcular janela de oportunidade

**RF04 - Interface**
- Sistema DEVE ter filtros por subnicho
- Sistema DEVE mostrar thumbnails dos vídeos
- Sistema DEVE ter modal detalhado
- Sistema DEVE ter botão "adicionar ao dashboard"

**RF05 - Validação**
- Sistema DEVE permitir aprovação/rejeição manual
- Sistema DEVE mostrar evidências (thumbs, títulos, métricas)
- Sistema DEVE ter links para YouTube/Social Blade
- Sistema NÃO DEVE adicionar canais sem validação humana

### 5.2 Requisitos Não-Funcionais

**RNF01 - Performance**
- Execução completa em <30 minutos
- Análise GPT em batch (50-100 canais)
- UI responsiva (<2s para carregar)

**RNF02 - Confiabilidade**
- Sistema isolado (não quebra dashboard atual)
- Fallback se GPT falhar (skip análise)
- Logs detalhados de todas operações

**RNF03 - Segurança**
- Sem credenciais em código (env vars)
- Rate limiting YouTube API
- Validação de inputs

**RNF04 - Manutenibilidade**
- Código modular e documentado
- Schema versionado
- Testes unitários para filtros

### 5.3 Restrições e Limitações

**Limitações Técnicas:**
- GPT não vê vídeos (só texto)
- GPT pode ter falsos positivos (20-30%)
- YouTube API tem rate limits
- Precisão ~70-80% (não 100%)

**Limitações de Negócio:**
- Cellibs DEVE validar antes de adicionar
- Não substitui análise humana
- Não funciona para nichos fora do escopo faceless

---

## 6. DESCOBERTA DE CANAIS

### 6.1 Featured Channels Network

**Como Funciona:**

1. **Seed:** Seus 50 canais próprios
2. **Busca:** Para cada canal, YouTube API retorna "featured channels"
3. **Expansão:** Para cada featured, busca seus featured (profundidade 2-3)
4. **Resultado:** Rede de 200-500 canais similares

**Implementação:**

```python
# discovery/discovery_engine.py

async def descobrir_via_featured_channels(seed_channels, depth=2):
    """
    Crawler de Featured Channels

    Args:
        seed_channels: Lista de channel_ids dos seus 50 canais
        depth: Profundidade do crawl (padrão: 2)

    Returns:
        Set de channel_ids descobertos
    """

    discovered = set()
    to_explore = set(seed_channels)
    explored = set()

    for level in range(depth):
        new_batch = set()

        for channel_id in to_explore:
            if channel_id in explored:
                continue

            # YouTube API: channels.list part=brandingSettings
            response = youtube.channels().list(
                part='brandingSettings',
                id=channel_id
            ).execute()

            # Extrai featured channels
            if response['items']:
                branding = response['items'][0].get('brandingSettings', {})
                channel_settings = branding.get('channel', {})
                featured = channel_settings.get('featuredChannelsUrls', [])

                # Resolve URLs para channel_ids
                for channel_url in featured:
                    # Parse @handle ou channel/UC...
                    channel_id_feat = resolve_channel_url(channel_url)

                    if channel_id_feat and channel_id_feat not in discovered:
                        discovered.add(channel_id_feat)
                        new_batch.add(channel_id_feat)

            explored.add(channel_id)

        # Próximo nível
        to_explore = new_batch

    return discovered
```

**Custo YouTube API:**
- `channels.list` = 1 unit por canal
- 50 canais seed × 2 níveis = ~100-200 units
- **Total:** ~200 units por execução

**Limitações:**
- Nem todos canais têm featured channels configurados
- Alguns featured podem não ser faceless (filtro posterior)
- Profundidade >3 pode trazer canais muito distantes

### 6.2 Keyword Cluster Detection

**Como Funciona:**

1. **Fonte de Dados:** Títulos dos 263 canais monitorados + seus vídeos destacados
2. **Extração:** TF-IDF para identificar keywords frequentes
3. **Clustering:** Detecta quando 5+ vídeos usam mesmas keywords em 15 dias
4. **Validação GPT:** Verifica se cluster é tendência real ou coincidência
5. **Expansão GPT:** Gera keywords similares/relacionadas
6. **Busca:** YouTube search com keywords expandidas

**Implementação:**

```python
# discovery/trend_detector.py

def detectar_keyword_clusters():
    """
    Analisa títulos de vídeos e detecta clusters emergentes
    """

    # 1. BUSCA VÍDEOS RECENTES (últimos 30 dias)
    query = """
        SELECT
            v.titulo,
            v.views,
            v.publicado_em,
            c.subnicho
        FROM videos v
        JOIN canais_monitorados c ON c.channel_id = v.channel_id
        WHERE v.publicado_em > NOW() - INTERVAL '30 days'
          AND v.views > 10000
        ORDER BY v.publicado_em DESC
    """

    videos = db.execute(query)

    # 2. EXTRAI KEYWORDS (TF-IDF simplificado)
    from collections import Counter
    import re

    # Stopwords PT-BR
    stopwords = ['de', 'da', 'do', 'em', 'na', 'no', 'para', 'com',
                 'por', 'que', 'mais', 'top', 'como', 'sobre']

    all_keywords = []
    video_keywords = {}  # {video_id: [keywords]}

    for video in videos:
        # Remove pontuação e converte para minúsculas
        titulo_limpo = re.sub(r'[^\w\s]', '', video.titulo.lower())

        # Extrai palavras (mínimo 4 letras)
        words = [w for w in titulo_limpo.split()
                 if len(w) >= 4 and w not in stopwords]

        all_keywords.extend(words)
        video_keywords[video.id] = words

    # 3. IDENTIFICA KEYWORDS FREQUENTES
    keyword_counts = Counter(all_keywords)

    # 4. DETECTA CLUSTERS (keywords que aparecem juntas)
    clusters = []

    for kw, count in keyword_counts.most_common(100):
        # Busca vídeos com essa keyword
        videos_com_kw = [v for v in videos
                         if kw in v.titulo.lower()]

        # Filtra últimos 15 dias
        from datetime import datetime, timedelta
        cutoff = datetime.now() - timedelta(days=15)
        videos_recentes = [v for v in videos_com_kw
                          if v.publicado_em > cutoff]

        # SE 5+ vídeos em 15 dias = CLUSTER EMERGENTE!
        if len(videos_recentes) >= 5:
            # Calcula crescimento
            videos_30d = videos_com_kw
            videos_15d = videos_recentes

            crescimento = (len(videos_15d) / len(videos_30d)) * 100 \
                         if len(videos_30d) > 0 else 0

            clusters.append({
                'keyword': kw,
                'videos_15d': len(videos_15d),
                'videos_30d': len(videos_30d),
                'crescimento': crescimento,
                'avg_views': sum(v.views for v in videos_recentes) / len(videos_recentes),
                'videos': videos_recentes[:10]  # Top 10
            })

    return clusters


def expandir_keywords_gpt(cluster):
    """
    GPT expande keywords para termos similares
    """

    prompt = f"""
Keyword detectada em cluster emergente: "{cluster['keyword']}"

Contexto:
- {cluster['videos_15d']} vídeos nos últimos 15 dias
- Crescimento: {cluster['crescimento']}%
- Views médias: {cluster['avg_views']:,.0f}

Exemplos de títulos:
{chr(10).join([f'- {v.titulo}' for v in cluster['videos'][:5]])}

EXPANDA essa keyword para termos SIMILARES e RELACIONADOS:
- Sinônimos
- Variações de idioma (PT, EN, ES)
- Termos relacionados ao mesmo tema
- Máximo 10 keywords

REGRAS:
- Mantenha tema central
- Foco em faceless (histórias, mistérios, terror, etc)
- Evite termos de gameplay/futebol

Responda JSON array de strings:
["keyword1", "keyword2", ...]
"""

    response = gpt_call(prompt, max_tokens=500)
    expanded = json.loads(response)

    return expanded


def buscar_canais_por_keywords(keywords_expandidas):
    """
    Busca canais no YouTube usando keywords expandidas
    """

    canais_encontrados = []

    for keyword in keywords_expandidas:
        # YouTube API: search.list (CARA: 100 units!)
        # Usar com MODERAÇÃO (só 1x por semana)

        results = youtube.search().list(
            q=keyword,
            type='channel',
            part='snippet',
            maxResults=25,
            relevanceLanguage='pt'  # ou outros idiomas
        ).execute()

        for item in results.get('items', []):
            channel_id = item['snippet']['channelId']
            canais_encontrados.append(channel_id)

    # Remove duplicatas
    return list(set(canais_encontrados))
```

**Custo YouTube API:**
- Análise de dados: 0 units (banco interno)
- `search.list`: 100 units por keyword
- ~5 keywords expandidas = 500 units
- **Frequência:** 1x por semana (não diário)

**Exemplo Real:**

```
CLUSTER DETECTADO:
Keyword: "japão"

Vídeos recentes (últimos 15 dias):
- "Mistérios do Japão que você não conhece"
- "Lendas Japonesas assustadoras"
- "História sombria do Japão feudal"
- "Terror japonês: Aokigahara"
- "Casos paranormais no Japão"
- ... (12 vídeos totais)

Crescimento: +180% (6 vídeos em 30d → 12 em 15d)

GPT EXPANDE:
[
  "japanese horror",
  "terror asiático",
  "lendas japonesas",
  "mistérios orientais",
  "asian mystery",
  "horror stories japan",
  "terror japones",
  "misterios asiaticos",
  "japanese urban legends",
  "yokai stories"
]

BUSCA YOUTUBE com keywords expandidas →
Descobre 15-25 canais sobre o tema
```

### 6.3 Google Trends Integration

**Como Funciona:**

1. **Monitoramento:** Lista de keywords relacionadas aos subnichos
2. **API Gratuita:** pytrends (interface não-oficial mas funcional)
3. **Análise:** Detecta termos crescendo 200-300%
4. **Timing:** Prevê quando vai viralizar no YouTube
5. **Validação GPT:** Confirma se é viável para faceless

**Implementação:**

```python
# discovery/trend_detector.py

from pytrends.request import TrendReq

def monitorar_google_trends():
    """
    Monitora tendências no Google relacionadas aos subnichos
    """

    # Inicializa pytrends
    pytrends = TrendReq(hl='pt-BR', tz=360)

    # Keywords de cada subnicho
    keywords_subnichos = {
        'Terror': ['terror', 'horror stories', 'histórias de terror'],
        'Mistério': ['mistério', 'mystery', 'casos não resolvidos'],
        'História': ['história', 'civilizações antigas', 'guerras'],
        # ... outros subnichos
    }

    tendencias_detectadas = []

    for subnicho, keywords in keywords_subnichos.items():
        # Busca interesse ao longo do tempo (últimos 90 dias)
        pytrends.build_payload(keywords, timeframe='today 3-m')

        # Interest over time
        data = pytrends.interest_over_time()

        for keyword in keywords:
            if keyword not in data.columns:
                continue

            # Calcula crescimento (últimos 7 dias vs 30 dias antes)
            recente = data[keyword].tail(7).mean()
            anterior = data[keyword].iloc[-37:-7].mean()

            if anterior > 0:
                crescimento = ((recente - anterior) / anterior) * 100
            else:
                crescimento = 0

            # SE crescimento >200% = TENDÊNCIA!
            if crescimento > 200:
                tendencias_detectadas.append({
                    'keyword': keyword,
                    'subnicho': subnicho,
                    'crescimento': crescimento,
                    'interesse_atual': recente,
                    'previsao': 'Alta probabilidade de viralizar no YouTube em 10-15 dias'
                })

    return tendencias_detectadas


def validar_tendencia_gpt(tendencia):
    """
    GPT valida se tendência é viável para faceless
    """

    prompt = f"""
Tendência detectada no Google Trends:

Keyword: "{tendencia['keyword']}"
Subnicho: {tendencia['subnicho']}
Crescimento: {tendencia['crescimento']:.1f}%

ANALISE:

1. É viável para canal FACELESS?
   - Dá para fazer com narração + imagens/vídeos IA?
   - Ou precisa filmagem/gameplay?

2. Potencial no YouTube?
   - Tema funciona em formato de vídeo?
   - Há demanda de audiência?

3. Janela de oportunidade?
   - Tendência passageira ou duradoura?
   - Saturação já começou?

4. Recomendação
   - Entrar agora?
   - Monitorar?
   - Ignorar?

Responda JSON:
{{
  "viavel_faceless": true/false,
  "potencial_youtube": 0-100,
  "janela_dias": 10-30,
  "saturacao": "baixa" | "média" | "alta",
  "recomendacao": "entrar" | "monitorar" | "ignorar",
  "justificativa": "..."
}}
"""

    response = gpt_call(prompt, max_tokens=800)
    analise = json.loads(response)

    return analise
```

**Custo:**
- pytrends: API gratuita (não-oficial)
- GPT validação: ~800 tokens por tendência
- **Total:** R$ 0 (dentro da quota GPT)

**Limitações:**
- pytrends pode ter rate limiting (usar com moderação)
- Dados não são 100% precisos (estimativas)
- Previsão de "10-15 dias" é empírica, não exata

---

## 7. ANÁLISE INTELIGENTE (GPT-4)

### 7.1 Prompt Completo para Análise de Canal

**Contexto:** Para cada canal descoberto, GPT-4 faz análise completa.

**Prompt Template:**

```python
def gerar_prompt_analise_canal(canal_data, canais_referencia):
    """
    Gera prompt completo para GPT-4 analisar canal

    Args:
        canal_data: Dados do canal (descrição, títulos, métricas)
        canais_referencia: Lista dos 50 canais próprios

    Returns:
        String do prompt
    """

    prompt = f"""
Você é um especialista em análise de canais YouTube faceless.

═══════════════════════════════════════════════════════
CANAL ANALISADO
═══════════════════════════════════════════════════════

Nome: {canal_data['nome']}
Channel ID: {canal_data['channel_id']}
URL: https://youtube.com/@{canal_data['handle']}

Inscritos: {canal_data['inscritos']:,}
Vídeos publicados: {canal_data['video_count']}
Data de criação: {canal_data['criado_em']}

DESCRIÇÃO DO CANAL:
{canal_data['descricao']}

ÚLTIMOS 15 TÍTULOS:
{formatar_titulos(canal_data['ultimos_titulos'])}

MÉTRICAS DOS ÚLTIMOS 10 VÍDEOS:
{formatar_metricas_videos(canal_data['ultimos_videos'])}

═══════════════════════════════════════════════════════
SEUS CANAIS DE REFERÊNCIA (50 canais que funcionam)
═══════════════════════════════════════════════════════

{formatar_canais_referencia(canais_referencia)}

═══════════════════════════════════════════════════════
ANÁLISE REQUERIDA
═══════════════════════════════════════════════════════

1. É FACELESS? (confiança 0-100)

   BUSQUE EVIDÊNCIAS NA DESCRIÇÃO:
   ✓ "narração por IA", "AI voice", "inteligência artificial"
   ✓ "histórias fictícias", "conteúdo gerado", "gerado por IA"
   ✓ "storytelling", "documentary style", "narrated stories"
   ✓ Disclaimers sobre ferramentas de IA
   ✓ "sem apresentador", "faceless", "no face"

   BUSQUE CONTRA-INDICAÇÕES:
   ✗ "apresentador", "host", "eu apresento"
   ✗ Menção a nome de pessoa física como host
   ✗ "meu canal", "comigo", "neste vídeo eu"
   ✗ "vlogs", "minha vida", "react"

2. CLASSIFICAÇÃO

   a) Nicho principal (ex: Terror, Mistério, História)

   b) Subnicho específico (ex: "Terror Psicológico Brasileiro")
      - Seja ESPECÍFICO, não genérico
      - Identifique micronicho dentro do nicho

   c) Micronichos trabalhados (análise dos títulos)
      - Quais temas/formatos recorrentes?
      - Exemplos: "casos paranormais", "lendas urbanas", "mistérios não resolvidos"

3. SIMILARIDADE COM SEUS CANAIS

   a) Compare TÍTULOS e TEMAS com os canais de referência

   b) Qual subnicho dos seus é mais similar?
      Opções: Terror, Mistérios, Histórias Sombrias, Relatos de Guerra,
              Guerras e Civilizações, Psicologia & Mindset, Empreendedorismo,
              Conspiração, Pessoas Desaparecidas

   c) Score de fit (0-100) com o subnicho mais próximo

   d) Qual canal específico de referência é mais similar?

4. PADRÕES DETECTADOS

   a) Títulos seguem estrutura similar aos seus canais?
      - Usa números? ("TOP 5", "7 CASOS")
      - Usa gatilhos? ("NUNCA", "CHOCANTE", "VERDADE")
      - Estrutura: pergunta/afirmação/lista?

   b) Temas são compatíveis com seus subnichos?

   c) Linguagem/tom similar?
      - Formal ou informal?
      - Dramático ou neutro?
      - Clickbait ou informativo?

5. VIABILIDADE DE REPLICAÇÃO

   Baseado APENAS em descrição e títulos, este canal:

   a) Parece ser replicável com narração IA + imagens/vídeos IA?

   b) Requer recursos que vocês NÃO TÊM?
      - Gameplay contínuo
      - Filmagem de esportes
      - Apresentador obrigatório

   c) É viável para operação faceless?

═══════════════════════════════════════════════════════
RESPONDA EM JSON (sem comentários)
═══════════════════════════════════════════════════════

{{
  "is_faceless": true | false,
  "confianca_faceless": 0-100,
  "evidencias_faceless": [
    "Descrição menciona 'narração por IA'",
    "Títulos seguem padrão impessoal",
    "Sem menção a apresentador"
  ],

  "nicho": "Terror",
  "subnicho": "Terror Psicológico Brasileiro",
  "micronichos": [
    "casos paranormais urbanos",
    "lendas brasileiras",
    "histórias de cemitérios"
  ],

  "fit_subnicho_nome": "Histórias Sombrias",
  "fit_score": 94,
  "canal_referencia_similar": "Dark Tales BR",

  "padroes_titulos": {{
    "usa_numeros": true,
    "usa_gatilhos": true,
    "estrutura_principal": "Afirmação dramática + contexto"
  }},

  "viavel_replicar": true,
  "recursos_necessarios": [
    "Narração IA (ElevenLabs)",
    "Imagens geradas (MidJourney/DALL-E)",
    "B-roll stock footage"
  ],

  "score_total": 92,

  "analise_textual": "Canal 100% faceless. Descrição menciona
  explicitamente 'narração por inteligência artificial' e 'histórias
  fictícias baseadas em lendas'. Últimos 15 títulos seguem padrão
  narrativo impessoal, sem menção a apresentador.

  Nicho: Terror Psicológico com foco em casos brasileiros (São Paulo,
  Rio). Diferencial: Pesquisa histórica detalhada de cada caso.

  Alta similaridade (94%) com subnicho 'Histórias Sombrias' do
  portfólio, especialmente com o canal 'Dark Tales BR'. Padrões de
  título quase idênticos.

  VIÁVEL PARA REPLICAÇÃO: SIM. Conseguem produzir com infraestrutura
  atual (narração IA + imagens geradas + b-roll). Não requer filmagem
  ou gameplay.",

  "recomendacao": "ADICIONAR IMEDIATAMENTE"
}}

═══════════════════════════════════════════════════════
REGRAS IMPORTANTES
═══════════════════════════════════════════════════════

❌ NÃO FAÇA SUPOSIÇÕES sobre:
   - Como são os vídeos visualmente (você não vê os vídeos)
   - Formato de produção específico
   - Qualidade visual ou de edição
   - Se tem pessoa aparecendo ou não (só inferência textual)

✅ BASE SUA ANÁLISE APENAS EM:
   - Texto da descrição
   - Padrões nos títulos
   - Comparação com canais de referência
   - Evidências textuais explícitas

✅ SEJA HONESTO sobre confiança:
   - Se descrição não tem evidências claras = confiança baixa
   - Se contra-indicações presentes = is_faceless: false
   - Se ambíguo = confiança média (50-70)
"""

    return prompt
```

### 7.2 Formato de Resposta Esperado

**Exemplo de Resposta GPT:**

```json
{
  "is_faceless": true,
  "confianca_faceless": 95,
  "evidencias_faceless": [
    "Descrição do canal menciona 'narração gerada por inteligência artificial'",
    "Disclaimer: 'Conteúdo criado com ferramentas de IA'",
    "Todos os 15 títulos são impessoais, sem menção a apresentador",
    "Não há menção a 'eu', 'comigo', 'meu canal' em nenhum lugar"
  ],

  "nicho": "Terror",
  "subnicho": "Terror Psicológico Urbano Brasileiro",
  "micronichos": [
    "casos paranormais em São Paulo",
    "lendas urbanas brasileiras",
    "histórias de cemitérios",
    "assombrações em prédios abandonados"
  ],

  "fit_subnicho_nome": "Histórias Sombrias",
  "fit_score": 94,
  "canal_referencia_similar": "Dark Tales BR",

  "padroes_titulos": {
    "usa_numeros": true,
    "usa_gatilhos": true,
    "estrutura_principal": "Afirmação dramática + contexto geográfico",
    "exemplos": [
      "O Mistério da Casa Abandonada em SP",
      "Caso Paranormal que Aterrorizou o Rio",
      "A Lenda Urbana Mais Sombria do Brasil"
    ]
  },

  "viavel_replicar": true,
  "recursos_necessarios": [
    "Narração IA (ElevenLabs ou similar)",
    "Imagens geradas por IA (MidJourney/DALL-E)",
    "B-roll de locais urbanos (stock footage)",
    "Efeitos sonoros (biblioteca gratuita)"
  ],

  "score_total": 92,

  "analise_textual": "Canal 100% faceless com alta qualidade de produção aparente (baseado em descrição profissional e consistência de uploads).

Descrição do canal deixa EXPLÍCITO o uso de IA: 'Narração gerada por inteligência artificial' e 'Histórias fictícias baseadas em lendas e relatos urbanos brasileiros'.

Nicho: Terror Psicológico com foco geográfico (Brasil, especialmente SP e RJ). Diferencial identificado: Pesquisa histórica de cada local mencionado, dando autenticidade às histórias fictícias.

Padrões de título MUITO similares ao canal 'Dark Tales BR' do portfólio:
- Estrutura: Afirmação dramática + local específico
- Uso de gatilhos: 'mistério', 'caso', 'nunca resolvido', 'aterrorizou'
- Números em 40% dos títulos ('5 casos...', 'TOP 7...')

Micronichos identificados nos títulos:
1. Casos paranormais urbanos (60% dos vídeos)
2. Lendas urbanas brasileiras (25%)
3. Histórias de cemitérios e locais abandonados (15%)

VIABILIDADE: ALTA. Canal não requer filmagem ou gameplay. Formato é 100% compatível com estrutura de produção atual da Content Factory. Conseguem replicar com:
- Narração IA (já usam)
- Imagens geradas (já têm acesso)
- B-roll urbano (stock gratuito disponível)

Crescimento do canal (+35% em 30 dias) sugere que encontrou product-market fit. Upload consistente (5 vídeos/semana) indica operação profissional.

Score de fit com 'Histórias Sombrias': 94/100
Motivo: Nicho idêntico, padrões de título quase iguais, audiência sobreposta.",

  "recomendacao": "ADICIONAR IMEDIATAMENTE",
  "motivo_recomendacao": "Canal com todas características desejadas: faceless confirmado, nicho alinhado, crescimento forte, formato replicável, sem competição direta no portfólio atual."
}
```

### 7.3 Custo por Análise

**Tokens por Canal:**
- Input: ~2000 tokens (dados do canal + prompt)
- Output: ~1000 tokens (análise completa)
- **Total:** ~3000 tokens por canal

**Batch de 100 Canais:**
- 100 × 3000 = 300.000 tokens
- Com 1M tokens/dia disponível = sobra 700K

**Frequência:**
- 3x por semana
- 300K tokens × 3 = 900K tokens/semana
- Quota semanal: 7M tokens
- **Uso: 13%** ✅

---

## 8. DETECÇÃO DE TENDÊNCIAS

### 8.1 Algoritmo de Detecção

**Entrada:**
- Títulos de vídeos dos últimos 30 dias (263 canais monitorados)
- Performance (views) de cada vídeo
- Nossos vídeos que se destacaram (>média)

**Processo:**

```python
def detectar_tendencias_completo():
    """
    Sistema completo de detecção de tendências

    Combina:
    1. Análise de keywords (títulos)
    2. Google Trends
    3. Performance dos nossos vídeos
    """

    # ========================================
    # PARTE 1: KEYWORD CLUSTERS
    # ========================================

    clusters = detectar_keyword_clusters()
    # Retorna: [{keyword, videos_15d, crescimento, ...}]

    # ========================================
    # PARTE 2: GOOGLE TRENDS
    # ========================================

    trends_google = monitorar_google_trends()
    # Retorna: [{keyword, crescimento, subnicho, ...}]

    # ========================================
    # PARTE 3: NOSSOS VÍDEOS DESTACADOS
    # ========================================

    query = """
        SELECT v.titulo, v.views, v.publicado_em
        FROM videos v
        JOIN canais_monitorados c ON c.channel_id = v.channel_id
        WHERE c.tipo = 'nosso'
          AND v.publicado_em > NOW() - INTERVAL '30 days'
          AND v.views > (
              SELECT AVG(views) * 1.5
              FROM videos
              WHERE channel_id = v.channel_id
          )
        ORDER BY v.views DESC
        LIMIT 50
    """

    nossos_destaques = db.execute(query)

    # Extrai keywords dos destaques
    keywords_destaques = extrair_keywords(nossos_destaques)

    # ========================================
    # PARTE 4: CONSOLIDAÇÃO COM GPT
    # ========================================

    prompt = f"""
Você é analista de tendências de mercado YouTube.

DADOS COLETADOS:

1. KEYWORD CLUSTERS (últimos 15 dias):
{formatar_clusters(clusters)}

2. GOOGLE TRENDS (crescimento >200%):
{formatar_trends(trends_google)}

3. NOSSOS VÍDEOS DESTACADOS (performance acima da média):
{formatar_destaques(nossos_destaques, keywords_destaques)}

ANALISE E IDENTIFIQUE:

1. TENDÊNCIAS VIRALIZANDO AGORA
   - O que está performando BEM neste momento
   - Baseado em: nossos vídeos + clusters recentes
   - Janela: 0-7 dias

2. TENDÊNCIAS FUTURAS (10-15 dias)
   - O que VAI viralizar em breve
   - Baseado em: Google Trends + clusters emergentes
   - Janela: 10-15 dias

3. MICRO-NICHOS EMERGENTES
   - Clusters de 5+ canais novos
   - Temas específicos dentro dos subnichos
   - Saturação: baixa/média/alta

4. OPORTUNIDADES DE EXPANSÃO
   - Temas relacionados aos subnichos atuais
   - Com demanda mas baixa oferta
   - Viáveis para faceless

PARA CADA TENDÊNCIA:
- Nome/descrição
- Tipo: AGORA | FUTURO | MICRO-NICHO | EXPANSÃO
- Subnicho relacionado
- Crescimento %
- Janela de oportunidade (dias)
- Saturação estimada
- Canais detectados (se aplicável)
- Recomendação de ação

Responda JSON array de tendências.
"""

    response = gpt_call(prompt, max_tokens=3000)
    tendencias = json.loads(response)

    # ========================================
    # PARTE 5: SALVAR NO BANCO
    # ========================================

    for tend in tendencias:
        db.insert('tendencias_emergentes', {
            'nome_tendencia': tend['nome'],
            'tipo': tend['tipo'],
            'crescimento_percentual': tend['crescimento'],
            'janela_dias': tend['janela'],
            'urgencia': calcular_urgencia(tend),
            'descricao': tend['descricao'],
            'recomendacao': tend['recomendacao'],
            'detectada_em': 'NOW()',
            'expira_em': calcular_expiracao(tend)
        })

    return tendencias
```

### 8.2 Exemplo de Tendência Detectada

**JSON Output:**

```json
{
  "tendencias": [
    {
      "nome": "Terror Japonês Moderno",
      "tipo": "MICRO-NICHO",
      "subnicho_relacionado": "Terror",
      "crescimento": 180,
      "janela_oportunidade_dias": 20,
      "saturacao": "baixa",
      "urgencia": "alta",

      "dados_detectados": {
        "keyword_cluster": {
          "keyword": "japão",
          "videos_15d": 12,
          "crescimento": 200
        },
        "google_trends": {
          "keyword": "japanese urban legends",
          "crescimento": 320,
          "regiao": "Brasil"
        },
        "canais_novos": 7
      },

      "canais_identificados": [
        {
          "nome": "Japanese Horror Stories",
          "channel_id": "UC...",
          "inscritos": 120000,
          "views_media": 65000
        },
        {
          "nome": "Dark Stories Japan",
          "channel_id": "UC...",
          "inscritos": 85000,
          "views_media": 48000
        }
        // ... mais 5 canais
      ],

      "analise": "Micro-nicho emergente com forte crescimento.

      DADOS:
      - 7 canais novos surgiram nos últimos 30 dias
      - Keyword 'japão' cresceu 200% em títulos (12 vídeos em 15 dias)
      - Google Trends mostra 'japanese urban legends' +320% no Brasil
      - Média 60K views/vídeo (acima da média do nicho Terror)

      OPORTUNIDADE:
      - Baixa competição em PT-BR (só 2 canais estabelecidos)
      - Alta demanda (Google Trends confirma)
      - Tema trending no TikTok migrando para YouTube
      - Formato 100% faceless viável

      JANELA:
      - Estimativa: 15-30 dias antes de saturar
      - Recomendação: Entrar AGORA

      SATURAÇÃO ATUAL: BAIXA
      - Poucos canais estabelecidos
      - Demanda > Oferta
      - Concorrência ainda não percebeu",

      "recomendacao": "AÇÃO IMEDIATA: Criar canal 'Mistérios do Japão' em PT-BR. Produzir 10 vídeos em 2 semanas para tomar território. Considerar também ES e EN para alcance global.",

      "keywords_sugeridas": [
        "mistérios do japão",
        "lendas japonesas",
        "terror japonês",
        "histórias assustadoras do japão",
        "yokai",
        "aokigahara",
        "casos paranormais japão"
      ]
    },

    {
      "nome": "História Medieval em Espanhol",
      "tipo": "GAP DE MERCADO",
      "subnicho_relacionado": "Guerras e Civilizações",
      "crescimento": 85,
      "janela_oportunidade_dias": 45,
      "saturacao": "baixa",
      "urgencia": "média",

      "dados_detectados": {
        "google_trends": {
          "keyword": "historia medieval",
          "crescimento": 150,
          "regiao": "Espanha + Latam"
        },
        "demanda_estimada": "5M buscas/mês",
        "oferta_atual": "3 canais grandes"
      },

      "analise": "Gap de mercado identificado: alta demanda, baixa oferta.

      DEMANDA:
      - 5M buscas mensais no Google (ES)
      - Interesse crescendo +150%
      - Público faminto por conteúdo

      OFERTA ATUAL:
      - Apenas 3 canais estabelecidos em ES
      - Frequência baixa (1 vídeo/semana)
      - Não estão atendendo toda demanda

      OPORTUNIDADE:
      - Demanda 5x maior que oferta
      - Janela maior (45 dias) - menos urgente
      - Potencial para dominação rápida",

      "recomendacao": "Lançar canal 'Leyendas Medievales' (ES). Frequência: 3 vídeos/semana para dominar. Colaboração com 'Historia Oculta' (cross-promo).",

      "keywords_sugeridas": [
        "historia medieval",
        "leyendas medievales",
        "edad media",
        "caballeros medievales",
        "castillos abandonados",
        "guerras medievales"
      ]
    }
  ]
}
```

### 8.3 Interface de Tendências

**UI Component:**

```
┌────────────────────────────────────────────────────┐
│  🔥 TENDÊNCIAS EMERGENTES                          │
└────────────────────────────────────────────────────┘

┌─ URGENTE (Janela <15 dias) ──────────────────────┐
│                                                    │
│  🇯🇵 Terror Japonês Moderno                        │
│  Tipo: Micro-Nicho Emergente | Terror            │
│                                                    │
│  📈 +180% crescimento (30 dias)                   │
│  📊 7 canais novos | 60K views médios             │
│  ⏰ Janela: 15-20 dias | Saturação: BAIXA         │
│                                                    │
│  💡 ANÁLISE:                                       │
│  Cluster detectado: 12 vídeos em 15 dias sobre    │
│  o tema. Google Trends +320%. Baixa competição    │
│  em PT-BR. Alta viabilidade faceless.             │
│                                                    │
│  🎯 RECOMENDAÇÃO:                                  │
│  Criar canal dedicado "Mistérios do Japão" (PT).  │
│  Produzir 10 vídeos em 2 semanas.                │
│                                                    │
│  [VER 7 CANAIS] [ADICIONAR AO MONITORAMENTO]      │
│                                                    │
└────────────────────────────────────────────────────┘

┌─ OPORTUNIDADES (Janela 30-45 dias) ──────────────┐
│                                                    │
│  🏰 História Medieval (Espanhol)                  │
│  Tipo: Gap de Mercado | Guerras e Civilizações   │
│                                                    │
│  📊 5M buscas/mês | 3 canais ativos              │
│  📈 +150% demanda | Saturação: BAIXA              │
│  ⏰ Janela: 45 dias                               │
│                                                    │
│  [VER ANÁLISE COMPLETA]                           │
│                                                    │
└────────────────────────────────────────────────────┘

┌─ VIRALIZANDO AGORA ──────────────────────────────┐
│                                                    │
│  🔥 "True Crime Brasil"                           │
│  15 vídeos viralizaram (últimos 7 dias)          │
│  Média 120K views | Seus vídeos: 2 neste tema    │
│                                                    │
│  💡 AÇÃO: Produzir mais neste tema AGORA          │
│                                                    │
│  [VER VÍDEOS VIRAIS] [VER NOSSOS VÍDEOS]         │
│                                                    │
└────────────────────────────────────────────────────┘
```

---

## 9. INTERFACE DO USUÁRIO

### 9.1 Estrutura da Nova Aba

**Localização:** Dashboard atual → Nova aba "Descoberta"

**Layout:**

```
┌─────────────────────────────────────────────────────┐
│  DASHBOARD DE MINERAÇÃO                             │
│  [Tabela] [Nossos Canais] [Minerados] [Notif]      │
│  [Monetização] [Financeiro] [DESCOBERTA] ← NOVO     │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  🔍 DESCOBERTA DE CANAIS FACELESS                   │
│                                                     │
│  📊 Última execução: Hoje, 03:00                   │
│  ✅ 87 canais analisados                           │
│  ⭐ 23 qualificados (score >70)                    │
│  🔥 2 micro-nichos emergentes                      │
│                                                     │
└─────────────────────────────────────────────────────┘

┌─ FILTROS ────────────────────────────────────────────┐
│  [Todos]  [Terror]  [Mistérios]  [Histórias Sombrias]│
│  [Relatos de Guerra]  [Guerras e Civilizações]       │
│  [Psicologia & Mindset]  [Empreendedorismo]          │
│  [Conspiração]  [Pessoas Desaparecidas]              │
└──────────────────────────────────────────────────────┘

┌─ CANAIS DESCOBERTOS (Terror) ────────────────────────┐
│                                                       │
│  📺 Histórias Sombrias BR        Score: 92/100      │
│  28K subs | 5 vídeos/sem | Terror Psicológico       │
│  [🔗 CANAL] [VER DETALHES] [✅ ADD] [❌ SKIP]       │
│                                                       │
│  📺 Dark Mysteries PT            Score: 88/100      │
│  45K subs | 3 vídeos/sem | Terror Japonês           │
│  [🔗 CANAL] [VER DETALHES] [✅ ADD] [❌ SKIP]       │
│                                                       │
│  📺 Relatos Macabros             Score: 85/100      │
│  32K subs | 4 vídeos/sem | Terror Urbano BR         │
│  [🔗 CANAL] [VER DETALHES] [✅ ADD] [❌ SKIP]       │
│                                                       │
│  [CARREGAR MAIS...]                                  │
│                                                       │
└───────────────────────────────────────────────────────┘

┌─ TENDÊNCIAS EMERGENTES ──────────────────────────────┐
│  [VER TODAS TENDÊNCIAS →]                            │
└───────────────────────────────────────────────────────┘
```

### 9.2 Modal Detalhado do Canal

**Ao clicar "VER DETALHES":**

```
┌──────────────────────────────────────────────────────┐
│  📺 Histórias Sombrias BR                   [X Fechar]│
├──────────────────────────────────────────────────────┤
│                                                      │
│  🔗 youtube.com/@historiassombrasbr                  │
│  📊 Score: 92/100                                   │
│                                                      │
├──────────────────────────────────────────────────────┤
│  📊 MÉTRICAS                                         │
│  👥 28.453 inscritos (+35% em 30d) 📈               │
│  📹 Upload: 5 vídeos/semana                         │
│  👁️ Views: 52.300/vídeo (média últimos 10)         │
│  📅 Último upload: Há 1 dia                         │
│  ⭐ Engagement: Alto (estimado)                     │
│                                                      │
├──────────────────────────────────────────────────────┤
│  🎯 CLASSIFICAÇÃO                                    │
│  Nicho: Terror                                       │
│  Subnicho: Terror Psicológico Brasileiro            │
│  Micronichos:                                        │
│  • Casos paranormais urbanos                        │
│  • Lendas brasileiras                               │
│  • Histórias de cemitérios                          │
│                                                      │
│  ✅ Fit com seus subnichos:                         │
│  • Histórias Sombrias: 94%                          │
│  • Similar a: Dark Tales BR                         │
│                                                      │
├──────────────────────────────────────────────────────┤
│  💡 ANÁLISE GPT-4                                    │
│                                                      │
│  ✅ Faceless: 95% confiança                         │
│                                                      │
│  Evidências:                                         │
│  • Descrição menciona "narração por IA"             │
│  • Disclaimer de conteúdo gerado com ferramentas IA │
│  • Títulos impessoais (sem menção a apresentador)   │
│                                                      │
│  Análise:                                            │
│  "Canal 100% faceless com produção profissional.    │
│   Descrição explícita sobre uso de IA. Nicho        │
│   Terror Psicológico focado em casos brasileiros.   │
│   Alta similaridade com 'Dark Tales BR' em          │
│   estilo e temas. Formato viável para replicação    │
│   com narração IA + imagens geradas."               │
│                                                      │
│  [EXPANDIR ANÁLISE COMPLETA]                        │
│                                                      │
├──────────────────────────────────────────────────────┤
│  📹 ÚLTIMOS 10 VÍDEOS                                │
│                                                      │
│  ┌──────────────────────────────────────────────┐  │
│  │ [THUMB]  O Mistério da Casa Abandonada       │  │
│  │          65.2K views | 2 dias | 12:34        │  │
│  │          [▶️ ASSISTIR NO YOUTUBE]            │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
│  ┌──────────────────────────────────────────────┐  │
│  │ [THUMB]  Caso Não Resolvido: A Garota...    │  │
│  │          58.1K views | 4 dias | 15:22        │  │
│  │          [▶️ ASSISTIR NO YOUTUBE]            │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
│  ┌──────────────────────────────────────────────┐  │
│  │ [THUMB]  História Real de Terror em SP      │  │
│  │          71.5K views | 6 dias | 11:45        │  │
│  │          [▶️ ASSISTIR NO YOUTUBE]            │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
│  [VER MAIS 7 VÍDEOS]                                │
│                                                      │
├──────────────────────────────────────────────────────┤
│  📊 PERFORMANCE                                      │
│  • 6/10 vídeos >50K views                           │
│  • Crescimento: +35% (30 dias)                      │
│  • Retenção: Alta (estimado)                        │
│  • Engagement: Acima da média                       │
│                                                      │
├──────────────────────────────────────────────────────┤
│  🔗 LINKS DE VERIFICAÇÃO                            │
│  [📺 VER CANAL]  [📊 SOCIAL BLADE]  [📈 NOXINFLUENCER]│
│                                                      │
├──────────────────────────────────────────────────────┤
│  [✅ ADICIONAR AO DASHBOARD]  [❌ IGNORAR]          │
│  [💾 SALVAR PARA DEPOIS]  [📝 ADICIONAR NOTA]       │
└──────────────────────────────────────────────────────┘
```

### 9.3 Componentes React (Referência)

**Arquivo:** `frontend/DiscoveryTab.tsx`

```typescript
// Estrutura básica dos componentes

interface CanalDescoberto {
  id: number;
  channel_id: string;
  nome_canal: string;
  url_canal: string;

  inscritos: number;
  videos_recentes: number;
  media_views: number;
  upload_frequency: string;

  nicho: string;
  subnicho: string;
  micronichos: string[];

  fit_subnicho: string;
  fit_score: number;

  is_faceless: boolean;
  confianca_faceless: number;
  analise_gpt: string;

  score_total: number;
  status: 'pendente' | 'aprovado' | 'ignorado';
}

interface Video {
  video_id: string;
  titulo: string;
  thumbnail_url: string;
  views: number;
  publicado_em: string;
  duracao: string;
}

// Componente principal
export function DiscoveryTab() {
  const [canais, setCanais] = useState<CanalDescoberto[]>([]);
  const [filtroSubnicho, setFiltroSubnicho] = useState<string>('Todos');
  const [loading, setLoading] = useState(true);

  // Fetch canais descobertos
  useEffect(() => {
    fetchCanaisDescobertos();
  }, [filtroSubnicho]);

  return (
    <div className="discovery-tab">
      <Header />
      <Filtros onFilterChange={setFiltroSubnicho} />
      <CanaisList canais={canais} />
      <TendenciasSection />
    </div>
  );
}

// Card de canal
export function CanalCard({ canal }: { canal: CanalDescoberto }) {
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <div className="canal-card">
      <div className="canal-header">
        <h3>{canal.nome_canal}</h3>
        <span className="score">Score: {canal.score_total}/100</span>
      </div>

      <div className="canal-metrics">
        {canal.inscritos.toLocaleString()} subs |
        {canal.upload_frequency} |
        {canal.subnicho}
      </div>

      <div className="canal-actions">
        <button onClick={() => window.open(canal.url_canal)}>
          🔗 CANAL
        </button>
        <button onClick={() => setModalOpen(true)}>
          VER DETALHES
        </button>
        <button onClick={() => adicionarCanal(canal.id)}>
          ✅ ADD
        </button>
        <button onClick={() => ignorarCanal(canal.id)}>
          ❌ SKIP
        </button>
      </div>

      {modalOpen && (
        <CanalModal canal={canal} onClose={() => setModalOpen(false)} />
      )}
    </div>
  );
}

// Modal detalhado
export function CanalModal({ canal, onClose }) {
  const [videos, setVideos] = useState<Video[]>([]);

  useEffect(() => {
    fetchVideosCanal(canal.id);
  }, []);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <ModalHeader canal={canal} onClose={onClose} />
        <MetricasSection canal={canal} />
        <ClassificacaoSection canal={canal} />
        <AnaliseGPTSection canal={canal} />
        <VideosSection videos={videos} />
        <PerformanceSection canal={canal} />
        <LinksSection canal={canal} />
        <ActionsSection canal={canal} onClose={onClose} />
      </div>
    </div>
  );
}
```

---

## 10. ARQUITETURA DO SISTEMA

### 10.1 Estrutura de Diretórios

```
youtube-dashboard-backend/          (ATUAL - NÃO MEXE)
├── main.py                         (FastAPI - endpoints atuais)
├── collector.py                    (coleta YouTube)
├── notifier.py                     (notificações)
├── database.py                     (client Supabase)
├── requirements.txt
│
├── discovery/                      (NOVO - ISOLADO)
│   ├── __init__.py
│   ├── discovery_engine.py        # Descoberta de canais
│   ├── intelligence_analyzer.py   # Análise GPT
│   ├── trend_detector.py          # Detecção de tendências
│   ├── discovery_database.py      # Queries específicas
│   ├── discovery_routes.py        # Endpoints API
│   └── utils.py                   # Funções auxiliares
│
├── frontend/                       (NOVO ou INTEGRADO)
│   ├── components/
│   │   ├── DiscoveryTab.tsx
│   │   ├── CanalCard.tsx
│   │   ├── CanalModal.tsx
│   │   ├── TendenciasSection.tsx
│   │   └── Filtros.tsx
│   └── hooks/
│       ├── useCanaisDescobertos.ts
│       └── useTendencias.ts
│
└── docs/
    └── SISTEMA_DESCOBERTA_CANAIS_COMPLETO.md  ← ESTE ARQUIVO
```

### 10.2 Integração com Sistema Atual

**main.py (atualizado):**

```python
# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Rotas atuais
from notifier import router as notifier_router
from monetization_endpoints import router as monetization_router

# NOVA: Rotas de descoberta
from discovery.discovery_routes import router as discovery_router

app = FastAPI(title="YouTube Dashboard Backend")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rotas atuais (não mexe)
app.include_router(notifier_router, prefix="/api")
app.include_router(monetization_router, prefix="/api")

# NOVA: Rotas de descoberta
app.include_router(discovery_router, prefix="/api/discovery")

@app.get("/")
def read_root():
    return {
        "message": "YouTube Dashboard API",
        "version": "2.0",
        "features": ["notificacoes", "monetizacao", "discovery"]
    }
```

### 10.3 Endpoints da API

**Descoberta de Canais:**

```
GET  /api/discovery/canais
     Lista canais descobertos
     Params: ?subnicho=Terror&status=pendente&limit=50

GET  /api/discovery/canais/{id}
     Detalhes de um canal específico

POST /api/discovery/canais/{id}/aprovar
     Aprova canal e adiciona ao monitoramento

POST /api/discovery/canais/{id}/ignorar
     Marca canal como ignorado

POST /api/discovery/canais/{id}/salvar
     Salva para revisar depois
```

**Tendências:**

```
GET  /api/discovery/tendencias
     Lista tendências emergentes
     Params: ?urgencia=alta&tipo=micro-nicho

GET  /api/discovery/tendencias/{id}
     Detalhes de uma tendência

GET  /api/discovery/tendencias/{id}/canais
     Canais relacionados a uma tendência
```

**Execução:**

```
POST /api/discovery/executar
     Dispara execução manual do sistema
     (normalmente roda via cron 3x/semana)

GET  /api/discovery/status
     Status da última execução
     Returns: {
       ultima_execucao: "2026-01-21T03:00:00",
       canais_analisados: 87,
       canais_qualificados: 23,
       tendencias_detectadas: 2,
       status: "completo"
     }
```

### 10.4 Fluxo de Dados

```
┌─────────────────────────────────────────────────┐
│  SCHEDULER (APScheduler)                        │
│  Cron: 3x/semana (seg, qua, sex às 3h)        │
└────────────────┬────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────┐
│  discovery_engine.py                            │
│  ├─ descobrir_via_featured_channels()           │
│  ├─ detectar_keyword_clusters()                 │
│  └─ monitorar_google_trends()                   │
└────────────────┬────────────────────────────────┘
                 ↓
         [100-200 channel_ids]
                 ↓
┌─────────────────────────────────────────────────┐
│  FILTROS (Python)                               │
│  ├─ >1000 subs?                                 │
│  ├─ >5K views em algum vídeo?                   │
│  ├─ Upload ativo?                               │
│  └─ Remove gameplay/futebol                     │
└────────────────┬────────────────────────────────┘
                 ↓
          [50-100 channel_ids]
                 ↓
┌─────────────────────────────────────────────────┐
│  intelligence_analyzer.py                       │
│  ├─ Para cada canal:                            │
│  │   ├─ Busca descrição + títulos               │
│  │   ├─ Chama GPT-4 (batch)                     │
│  │   └─ Salva resultado no banco                │
│  └─ Retorna canais qualificados                 │
└────────────────┬────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────┐
│  SUPABASE (PostgreSQL)                          │
│  ├─ Tabela: canais_descobertos                  │
│  ├─ Tabela: videos_canais_descobertos           │
│  └─ Tabela: tendencias_emergentes               │
└────────────────┬────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────┐
│  FRONTEND (React)                               │
│  ├─ Fetch: GET /api/discovery/canais            │
│  ├─ Renderiza cards                             │
│  └─ Usuário valida e aprova                     │
└────────────────┬────────────────────────────────┘
                 ↓
         [Aprovar canal]
                 ↓
┌─────────────────────────────────────────────────┐
│  POST /api/discovery/canais/{id}/aprovar        │
│  ├─ Move para canais_monitorados                │
│  ├─ Collector passa a coletar                   │
│  └─ Notifier inclui nas regras                  │
└─────────────────────────────────────────────────┘
```

---

## 11. SCHEMA DO BANCO DE DADOS

### 11.1 Tabelas Novas

**Tabela: `canais_descobertos`**

```sql
CREATE TABLE canais_descobertos (
    -- IDs
    id SERIAL PRIMARY KEY,
    channel_id TEXT UNIQUE NOT NULL,

    -- Info básica
    nome_canal TEXT NOT NULL,
    url_canal TEXT,
    handle TEXT,

    -- Métricas
    inscritos INTEGER,
    video_count INTEGER,
    videos_recentes INTEGER,       -- Últimos 30 dias
    maior_views_30d INTEGER,        -- Maior views de 1 vídeo
    media_views INTEGER,            -- Média últimos 10 vídeos
    upload_frequency TEXT,          -- "5/semana", "3/semana"
    ultimo_upload TIMESTAMP,
    criado_em TIMESTAMP,            -- Data criação do canal

    -- Classificação
    nicho TEXT,
    subnicho TEXT,
    micronichos TEXT[],             -- Array de micronichos

    -- Fit com operação
    fit_subnicho TEXT,              -- Nome do subnicho mais similar
    fit_score INTEGER,              -- 0-100
    canal_referencia_similar TEXT,  -- "Dark Tales BR"

    -- Análise GPT
    is_faceless BOOLEAN,
    confianca_faceless INTEGER,     -- 0-100
    evidencias_faceless TEXT[],     -- Array de evidências
    viavel_replicar BOOLEAN,
    recursos_necessarios TEXT[],
    analise_gpt TEXT,               -- Análise completa (longa)
    analise_resumida TEXT,          -- Resumo curto

    -- Score
    score_total INTEGER,            -- 0-100

    -- Metadados
    metodo_descoberta TEXT,         -- "featured_channels", "keyword_cluster", "google_trends"
    descoberto_via TEXT,            -- "Terror Japonês cluster" ou channel_id do seed
    status TEXT DEFAULT 'pendente', -- pendente/aprovado/ignorado/salvo

    -- Timestamps
    descoberto_em TIMESTAMP DEFAULT NOW(),
    revisado_em TIMESTAMP,
    revisado_por TEXT,

    -- Notas
    notas TEXT                      -- Cellibs pode adicionar notas
);

-- Índices para performance
CREATE INDEX idx_canais_descobertos_status ON canais_descobertos(status);
CREATE INDEX idx_canais_descobertos_subnicho ON canais_descobertos(subnicho);
CREATE INDEX idx_canais_descobertos_score ON canais_descobertos(score_total DESC);
CREATE INDEX idx_canais_descobertos_descoberto_em ON canais_descobertos(descoberto_em DESC);
```

**Tabela: `videos_canais_descobertos`**

```sql
CREATE TABLE videos_canais_descobertos (
    id SERIAL PRIMARY KEY,
    canal_descoberto_id INTEGER NOT NULL REFERENCES canais_descobertos(id) ON DELETE CASCADE,

    video_id TEXT NOT NULL,
    titulo TEXT,
    thumbnail_url TEXT,

    views INTEGER,
    likes INTEGER,
    comentarios INTEGER,

    publicado_em TIMESTAMP,
    duracao TEXT,               -- "12:34"

    ordem INTEGER,              -- 1-10 (últimos 10 vídeos)

    coletado_em TIMESTAMP DEFAULT NOW(),

    UNIQUE(canal_descoberto_id, video_id)
);

CREATE INDEX idx_videos_descobertos_canal ON videos_canais_descobertos(canal_descoberto_id);
```

**Tabela: `tendencias_emergentes`**

```sql
CREATE TABLE tendencias_emergentes (
    id SERIAL PRIMARY KEY,

    -- Identificação
    nome_tendencia TEXT NOT NULL,
    tipo TEXT NOT NULL,             -- "AGORA", "FUTURO", "MICRO-NICHO", "GAP"
    subnicho_relacionado TEXT,

    -- Dados da tendência
    crescimento_percentual INTEGER,
    canais_detectados INTEGER,
    videos_virais INTEGER,
    janela_dias INTEGER,            -- Janela de oportunidade
    saturacao TEXT,                 -- "baixa", "média", "alta"
    urgencia TEXT,                  -- "baixa", "média", "alta"

    -- Análise
    descricao TEXT,
    analise_completa TEXT,
    recomendacao TEXT,
    keywords_sugeridas TEXT[],

    -- Dados de detecção
    dados_detectados JSONB,         -- JSON com dados brutos

    -- Status
    status TEXT DEFAULT 'ativa',    -- ativa/monitorando/expirada/aproveitada

    -- Timestamps
    detectada_em TIMESTAMP DEFAULT NOW(),
    expira_em TIMESTAMP,            -- Calculado: detectada_em + janela_dias
    atualizada_em TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tendencias_status ON tendencias_emergentes(status);
CREATE INDEX idx_tendencias_urgencia ON tendencias_emergentes(urgencia);
CREATE INDEX idx_tendencias_tipo ON tendencias_emergentes(tipo);
```

**Tabela: `canais_tendencia`** (relação N:N)

```sql
CREATE TABLE canais_tendencia (
    id SERIAL PRIMARY KEY,
    tendencia_id INTEGER NOT NULL REFERENCES tendencias_emergentes(id) ON DELETE CASCADE,
    canal_descoberto_id INTEGER NOT NULL REFERENCES canais_descobertos(id) ON DELETE CASCADE,

    adicionado_em TIMESTAMP DEFAULT NOW(),

    UNIQUE(tendencia_id, canal_descoberto_id)
);

CREATE INDEX idx_canais_tendencia_tendencia ON canais_tendencia(tendencia_id);
CREATE INDEX idx_canais_tendencia_canal ON canais_tendencia(canal_descoberto_id);
```

### 11.2 Views Úteis

**View: Canais Pendentes de Revisão**

```sql
CREATE VIEW canais_pendentes_revisao AS
SELECT
    cd.id,
    cd.nome_canal,
    cd.subnicho,
    cd.score_total,
    cd.inscritos,
    cd.media_views,
    cd.upload_frequency,
    cd.is_faceless,
    cd.confianca_faceless,
    cd.descoberto_em,
    COUNT(v.id) as videos_count
FROM canais_descobertos cd
LEFT JOIN videos_canais_descobertos v ON v.canal_descoberto_id = cd.id
WHERE cd.status = 'pendente'
GROUP BY cd.id
ORDER BY cd.score_total DESC, cd.descoberto_em DESC;
```

**View: Tendências Urgentes**

```sql
CREATE VIEW tendencias_urgentes AS
SELECT
    t.*,
    COUNT(ct.canal_descoberto_id) as canais_count
FROM tendencias_emergentes t
LEFT JOIN canais_tendencia ct ON ct.tendencia_id = t.id
WHERE t.status = 'ativa'
  AND t.urgencia = 'alta'
  AND t.expira_em > NOW()
GROUP BY t.id
ORDER BY t.janela_dias ASC, t.crescimento_percentual DESC;
```

### 11.3 Migração

**Arquivo:** `database/migrations/005_add_discovery_tables.sql`

```sql
-- Migration: Sistema de Descoberta de Canais
-- Data: 21/01/2026
-- Versão: 1.0

BEGIN;

-- Canais descobertos
CREATE TABLE IF NOT EXISTS canais_descobertos (
    -- [Schema completo acima]
);

-- Vídeos dos canais descobertos
CREATE TABLE IF NOT EXISTS videos_canais_descobertos (
    -- [Schema completo acima]
);

-- Tendências emergentes
CREATE TABLE IF NOT EXISTS tendencias_emergentes (
    -- [Schema completo acima]
);

-- Relação canais-tendências
CREATE TABLE IF NOT EXISTS canais_tendencia (
    -- [Schema completo acima]
);

-- Views
CREATE OR REPLACE VIEW canais_pendentes_revisao AS
-- [Schema completo acima]

CREATE OR REPLACE VIEW tendencias_urgentes AS
-- [Schema completo acima]

COMMIT;
```

---

## 12. CUSTOS E VIABILIDADE

### 12.1 Análise Detalhada de Custos

**YouTube Data API v3:**

| Operação | Units | Frequência | Total/mês |
|----------|-------|------------|-----------|
| Featured Channels | 200 | 3x/sem × 4 | 2.400 |
| Keyword Search | 500 | 1x/sem × 4 | 2.000 |
| Channel Details | 100 | 3x/sem × 4 | 1.200 |
| Video Details | 100 | 3x/sem × 4 | 1.200 |
| **TOTAL** | - | - | **6.800** |

**Quota Disponível:** 6.000.000 units/mês
**Uso do Sistema:** 6.800 units/mês
**Percentual:** **0.11%** ✅
**Sobra:** 99.89%

---

**GPT-4 (OpenAI):**

| Operação | Tokens | Frequência | Total/mês |
|----------|--------|------------|-----------|
| Análise de canais (100/execução) | 300K | 3x/sem × 4 | 3.600.000 |
| Expansão de keywords | 10K | 1x/sem × 4 | 40.000 |
| Validação de tendências | 20K | 3x/sem × 4 | 240.000 |
| Consolidação de tendências | 15K | 3x/sem × 4 | 180.000 |
| **TOTAL** | - | - | **4.060.000** |

**Quota Disponível:** 30.000.000 tokens/mês (1M/dia × 30)
**Uso do Sistema:** 4.060.000 tokens/mês
**Percentual:** **13.5%** ✅
**Sobra:** 86.5%

---

**APIs Gratuitas:**

- ✅ Google Trends (pytrends): R$ 0
- ✅ Social Blade scraping: R$ 0 (se implementado)

---

**Custo Total Mensal: R$ 0** 🎉

### 12.2 Viabilidade Técnica

**Recursos Necessários:**

| Recurso | Disponível | Necessário | Viável? |
|---------|------------|------------|---------|
| YouTube API quota | 6M/mês | 7K/mês | ✅ SIM (0.11%) |
| GPT-4 tokens | 30M/mês | 4M/mês | ✅ SIM (13.5%) |
| Supabase storage | 8GB | +100MB | ✅ SIM |
| Railway compute | Atual | +5% | ✅ SIM |

**Conclusão:** Sistema 100% viável com recursos atuais. Zero custo adicional.

### 12.3 Escalabilidade

**Se precisar escalar:**

- 2x frequência (6x/semana): 27% quota GPT (ainda viável)
- 2x canais analisados (200/execução): 27% quota GPT
- 10x frequência: Começaria a custar ~$20-30/mês em GPT

**Mas:** Com 3x/semana e 100 canais/execução = mais que suficiente

---

## 13. RESUMO EXECUTIVO

### 13.1 Para o Sócio (Micha/Arthur/João Gabriel)

**O QUE ESTAMOS CONSTRUINDO:**

Um sistema automático que descobre canais faceless e tendências emergentes 24/7, eliminando 90% da pesquisa manual atual.

**COMO FUNCIONA (SIMPLES):**

1. **Descoberta:** Sistema busca canais similares aos nossos usando 3 fontes
   - Featured Channels (rede de canais relacionados)
   - Keyword Clusters (temas viralizando)
   - Google Trends (previsão de tendências)

2. **Análise:** GPT-4 analisa cada canal descoberto
   - É faceless? (confiança 0-100)
   - Qual nicho/subnicho?
   - Dá para replicar?
   - Score total (0-100)

3. **Validação:** Interface limpa para Cellibs revisar
   - Vê thumbnails, títulos, métricas
   - 1 clique para aprovar ou ignorar
   - Adiciona ao dashboard atual

**RESULTADOS ESPERADOS:**

- **50-80 canais novos** por semana (qualificados)
- **2-3 tendências emergentes** por mês
- **Detecção ANTES dos concorrentes** (10-15 dias antecipação)
- **90% menos tempo** em pesquisa manual

**CUSTO:**

- R$ 0 (tudo dentro das quotas gratuitas atuais)

**PRAZO:**

- 2 dias para sistema completo (MVP funcional)

### 13.2 Benefícios por Departamento

**Para Cellibs (Inteligência):**
- Automatiza descoberta de canais
- Dados estruturados e validáveis
- Detecção preditiva de tendências
- Interface rápida para validação

**Para Micha (Desenvolvimento de Conteúdo):**
- Alertas de temas viralizando AGORA
- Recomendações de títulos baseadas em trends
- Identificação de micro-nichos específicos
- Keywords expandidas para busca

**Para João Gabriel (Distribuição):**
- Referências de thumbnails de sucesso
- Canais similares para benchmarking
- Tendências visuais identificadas

**Para Arthur (Copy):**
- Padrões de título que funcionam
- Estruturas de storytelling validadas
- Temas com alta demanda comprovada

---

## 14. PERGUNTAS PARA DISCUSSÃO

### 14.1 Filtros e Escopo

**Q1: Subnichos**
Os 10 subnichos do banco são todos ativos para descoberta?
- Terror
- Mistérios
- Histórias Sombrias
- Relatos de Guerra
- Guerras e Civilizações
- Psicologia & Mindset
- Empreendedorismo
- Conspiração (só minerado, incluir?)
- Pessoas Desaparecidas (só minerado, incluir?)
- Notícias e Atualidade (só minerado, incluir?)

**Ou focar só nos 7 principais que produzem?**

---

**Q2: Idiomas**
Descobrir canais em TODOS os idiomas que operam (10+) ou focar em PT-BR inicialmente?

Opções:
- A) Só PT-BR (simplifica análise GPT)
- B) PT-BR + ES + EN (principais)
- C) Todos os 10+ idiomas

---

**Q3: Threshold de Inscritos**
Filtro atual: >1000 inscritos (monetizados)

Ajustar para:
- A) Manter 1000
- B) Aumentar para 5000 (mais estabelecidos)
- C) Diminuir para 500 (pegar emergentes antes)

---

### 14.2 Análise e Validação

**Q4: Análise GPT**
Além de descrição e títulos, que outros dados ajudariam a identificar faceless com mais precisão?

Ideias:
- Comentários dos vídeos (verificar se mencionam apresentador)
- About page / links sociais
- Thumbnails (GPT Vision - limitado mas pode ajudar)

---

**Q5: Tempo de Validação**
Quanto tempo conseguem dedicar para validar canais descobertos por semana?

- A) 15-20 min (revisar ~20 canais top)
- B) 30-45 min (revisar ~50 canais)
- C) 1h+ (revisar 80-100 canais)

Isso define quantos canais mostrar por execução.

---

**Q6: Falsos Positivos**
Sistema vai ter ~20-30% de falsos positivos (canais que GPT acha faceless mas não são).

Preferência:
- A) Conservador (mostra menos canais, maior precisão)
- B) Agressivo (mostra mais canais, aceita falsos positivos)

---

### 14.3 Funcionalidades

**Q7: Notificações**
Querem receber alerta quando:
- Tendência urgente detectada (janela <15 dias)?
- Cluster emergente com >10 canais novos?
- Canal com score >95 descoberto?

Via:
- Telegram bot
- Email
- Notificação no dashboard

---

**Q8: Expansão de Subnichos**
Sistema deve sugerir novos subnichos que vocês NÃO operam ainda mas têm demanda?

Exemplo: "Finanças Pessoais" tem alta demanda, baixa competição, viável faceless

- A) Sim, queremos explorar novos nichos
- B) Não, focar só nos 7-10 atuais

---

**Q9: Integração com Sistema Musical**
Faz sentido integrar descoberta com sistema de produção?

Exemplo: Detecta tendência → Sugere criar vídeo → Cellibs aprova → Sistema Musical produz

- A) Sim, integrar no futuro
- B) Não, manter separado

---

### 14.4 Interface e UX

**Q10: Dashboard**
Preferência de implementação:

- A) Aba integrada no dashboard atual (mais simples)
- B) Dashboard separado (mais isolado)

---

**Q11: Filtros Adicionais na UI**
Além de subnicho, quais filtros seriam úteis?

- Score (>90, >80, >70)
- Crescimento (>20%, >50%)
- Tamanho (micro: <50K, médio: 50-200K, grande: >200K)
- Idioma
- Data de descoberta

---

**Q12: Ações em Batch**
Seria útil aprovar/ignorar múltiplos canais de uma vez?

- Checkbox + "Aprovar selecionados"
- "Aprovar todos >90"
- "Ignorar todos <70"

---

### 14.5 Priorização

**Q13: Ordem de Prioridade**
Como priorizar canais na listagem?

Opções:
- A) Score total (padrão atual)
- B) Crescimento %
- C) Fit com subnicho
- D) Combinação ponderada

---

**Q14: MVP**
Para MVP (primeira versão), focar em:

- A) Descoberta de canais (essencial)
- B) Descoberta + Tendências
- C) Sistema completo

---

### 14.6 Expansão Futura

**Q15: Análise de Comentários**
Vale adicionar análise de comentários dos canais descobertos?

Para identificar:
- Sentimento da audiência
- Demandas não atendidas
- Confirmação se é faceless (menções a apresentador)

**Custo:** ~50K tokens extras/execução

---

**Q16: Reddit Integration**
Vale adicionar monitoramento de subreddits específicos?

Subreddits úteis:
- r/horror, r/mystery, r/UnresolvedMysteries
- r/history, r/WarCollege
- r/GetMotivated (Psicologia & Mindset)

**Esforço:** Médio
**ROI:** Baixo a médio

---

## 15. ROADMAP DE IMPLEMENTAÇÃO

### 15.1 Cronograma Proposto

**DIA 1:**
- ✅ Criar estrutura de diretórios `discovery/`
- ✅ Schema do banco (migration 005)
- ✅ `discovery_engine.py` (featured channels)
- ✅ Testes básicos de descoberta
- **Output:** Consegue descobrir 50+ canais

**DIA 2:**
- ✅ `intelligence_analyzer.py` (análise GPT)
- ✅ `discovery_database.py` (queries)
- ✅ `discovery_routes.py` (endpoints API)
- ✅ Testes de análise
- ✅ Deploy Railway
- **Output:** Sistema funcional backend completo

**DIA 3 (se necessário):**
- ✅ Frontend: DiscoveryTab.tsx
- ✅ Componentes: CanalCard, CanalModal
- ✅ Integração frontend-backend
- ✅ Testes end-to-end
- **Output:** Sistema completo funcional

### 15.2 Fases de Rollout

**FASE 1: MVP (Dias 1-2)**
- Descoberta via Featured Channels
- Análise GPT básica
- UI simples (lista + modal)
- **Objetivo:** Validar conceito

**FASE 2: Intelligence (Semana 2)**
- Keyword Clusters
- Google Trends
- Tendências emergentes
- UI melhorada
- **Objetivo:** Sistema completo

**FASE 3: Refinamento (Semana 3-4)**
- Ajustes baseados em feedback
- Otimizações de performance
- Features adicionais (se solicitadas)
- **Objetivo:** Produção estável

### 15.3 Critérios de Sucesso

**Métricas de Produto:**
- ✅ Descobre 50+ canais/execução (qualificados)
- ✅ Precisão >70% (faceless real)
- ✅ Tempo de validação <30 min
- ✅ Zero custo adicional

**Métricas de Negócio:**
- ✅ 10+ canais novos adicionados/mês
- ✅ 2+ tendências aproveitadas/mês
- ✅ First-mover advantage (antes concorrentes)
- ✅ 90% redução tempo pesquisa manual

**Métricas Técnicas:**
- ✅ Uptime >99%
- ✅ Latência API <2s
- ✅ Zero breaking changes no sistema atual
- ✅ Logs completos de todas operações

---

## 16. NOTAS FINAIS

### 16.1 Limitações Conhecidas

**Técnicas:**
- GPT não vê vídeos (apenas texto)
- Precisão ~70-80% (não 100%)
- Falsos positivos inevitáveis (20-30%)
- YouTube API rate limits (respeitados)

**De Negócio:**
- Validação humana sempre necessária
- Não substitui análise estratégica
- Focado em faceless (não serve para outros nichos)

### 16.2 Decisões Arquiteturais

**Por que código separado (`discovery/`)?**
- Isolamento (não quebra sistema atual)
- Manutenibilidade
- Facilita testes
- Pode virar micro-serviço no futuro

**Por que GPT-4 e não modelo próprio?**
- GPT-4 já funciona bem (não precisa treinar)
- Quota gratuita suficiente
- Flexibilidade (ajusta prompts facilmente)
- Modelo próprio = meses de desenvolvimento + dados de treino

**Por que 3x/semana e não diário?**
- Balanceamento: frequência suficiente vs custo
- Cellibs tem tempo para validar
- Mercado não muda tanto diariamente
- Sobra quota para escalar se necessário

### 16.3 Próximos Passos Imediatos

1. **Validar spec com o time** (este documento)
2. **Responder perguntas** da seção 14
3. **Ajustar** baseado em feedback
4. **Implementar** (1-2 dias)
5. **Testar** com dados reais (1 dia)
6. **Deploy** produção
7. **Monitorar** primeira semana
8. **Iterar** baseado em uso real

---

## 17. APÊNDICES

### 17.1 Glossário

**Canal Faceless:** Canal YouTube sem pessoa aparecendo. Usa narração IA + imagens/vídeos gerados.

**Micro-nicho:** Segmento específico dentro de um nicho maior. Ex: "Terror Japonês" dentro de "Terror".

**Keyword Cluster:** Conjunto de keywords relacionadas que aparecem frequentemente juntas em títulos virais.

**Featured Channels:** Canais destacados na página de um canal YouTube (configurado pelo criador).

**Google Trends:** Ferramenta do Google que mostra interesse de busca ao longo do tempo.

**Score:** Pontuação 0-100 que indica qualidade/relevância de um canal descoberto.

**Janela de Oportunidade:** Período estimado (em dias) antes de um nicho saturar.

### 17.2 Referências Técnicas

**YouTube Data API v3:**
- Documentação: https://developers.google.com/youtube/v3
- Quota calculator: https://developers.google.com/youtube/v3/determine_quota_cost
- Rate limits: 10.000 units/dia por projeto

**GPT-4 (OpenAI):**
- Modelos: gpt-4, gpt-4-turbo
- Pricing: https://openai.com/pricing
- Best practices: https://platform.openai.com/docs/guides/gpt-best-practices

**Pytrends:**
- GitHub: https://github.com/GeneralMills/pytrends
- Uso: Interface não-oficial para Google Trends
- Limitações: Rate limiting não documentado

### 17.3 Ferramentas Externas Úteis

**Social Blade:**
- URL: https://socialblade.com
- Uso: Verificar crescimento histórico de canais
- Custo: Gratuito (dados públicos)

**Noxinfluencer:**
- URL: https://www.noxinfluencer.com
- Uso: Estimativas de receita, engagement
- Custo: Gratuito

**VidIQ / TubeBuddy:**
- Extensões Chrome para análise de vídeos
- Útil para análise manual de concorrentes

---

## 📌 CONCLUSÃO

Este documento contém **TODA** a especificação do Sistema de Descoberta Inteligente de Canais Faceless, incluindo:

- ✅ Contexto completo do negócio
- ✅ Problema identificado e solução proposta
- ✅ Todas as iterações e ajustes feitos
- ✅ Especificação técnica detalhada
- ✅ Código de referência (prompts GPT, algoritmos)
- ✅ Schema completo do banco de dados
- ✅ Mockups de interface
- ✅ Análise de custos e viabilidade
- ✅ Perguntas pendentes para discussão
- ✅ Roadmap de implementação

**Objetivo:** Qualquer pessoa (ou Claude no futuro) que ler este documento conseguirá:
1. Entender EXATAMENTE o que foi discutido
2. Implementar o sistema conforme especificado
3. Tomar decisões alinhadas com as definições aqui

**Versão:** 1.0 - Especificação Final Aprovada
**Data:** 21 de Janeiro de 2026
**Autores:** Cellibs + Claude Code

---

**FIM DO DOCUMENTO**

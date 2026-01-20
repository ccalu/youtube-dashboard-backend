# PROMPT COMPLETO PARA LOVABLE - SISTEMA DE COMENTÁRIOS COM GPT

**COPIE TODO ESTE CONTEÚDO E COLE NO LOVABLE**

---

## VISÃO GERAL DO SISTEMA

O Dashboard de Mineração agora possui um sistema completo de análise de comentários com GPT-4. Este sistema:
- Coleta comentários apenas dos canais tipo="nosso" (35 canais próprios)
- Analisa com GPT-4o-mini (sentimento, prioridade, insights)
- Armazena tudo no Supabase
- Fornece estatísticas detalhadas via API
- Suporta coleta incremental (economiza 60% da quota após primeira coleta)

---

## NOVOS ENDPOINTS DA API

### 1. ENDPOINT DE ESTATÍSTICAS DE COMENTÁRIOS

```typescript
GET /api/comments/stats
```

**Resposta:**
```json
{
  "global_stats": {
    "total_channels_analyzed": 35,
    "total_videos_with_comments": 248,
    "total_comments": 12456,
    "total_gpt_analyzed": 11234,
    "gpt_coverage_percent": 90.2,
    "sentiment_distribution": {
      "positive": 8234,
      "negative": 2456,
      "neutral": 544,
      "positive_percent": 73.3,
      "negative_percent": 21.9,
      "neutral_percent": 4.8
    },
    "priority_distribution": {
      "high": 234,
      "medium": 1456,
      "low": 9544,
      "high_percent": 2.1,
      "medium_percent": 13.0,
      "low_percent": 84.9
    },
    "last_collection": "2024-01-19T05:00:00Z",
    "next_collection": "2024-01-20T05:00:00Z"
  },
  "channel_breakdown": [
    {
      "canal_id": 123,
      "nome_canal": "Histórias Sombrias",
      "subnicho": "Terror",
      "tipo": "nosso",
      "stats": {
        "total_videos": 45,
        "total_comments": 1234,
        "analyzed_comments": 1180,
        "coverage_percent": 95.6,
        "sentiment": {
          "positive": 890,
          "negative": 234,
          "neutral": 56
        },
        "avg_sentiment_score": 72.5,
        "high_priority_count": 12,
        "problems_detected": 8,
        "last_video_date": "2024-01-18T10:00:00Z"
      }
    }
  ],
  "recent_insights": [
    {
      "canal_nome": "Terror Urbano",
      "video_title": "A Casa Abandonada",
      "comment_preview": "O áudio está muito baixo...",
      "insight": "Problema técnico detectado - áudio",
      "priority": "high",
      "sentiment": "negative",
      "created_at": "2024-01-19T08:30:00Z"
    }
  ],
  "collection_metrics": {
    "last_run_duration_minutes": 45,
    "videos_processed": 89,
    "comments_collected": 2345,
    "gpt_api_calls": 156,
    "gpt_tokens_used": 285000,
    "percentual_limite_diario": 28.5,
    "errors_count": 2,
    "success_rate": 97.8
  }
}
```

### 2. ENDPOINT DE ENGAJAMENTO POR CANAL

```typescript
GET /api/canais/{canalId}/engagement
```

**Nota:** Este endpoint já está documentado na seção da Aba Engajamento abaixo.

---

## SISTEMA DE LOGS DE COLETA (NOVO! USANDO TOKENS)

### 3. ENDPOINTS DE LOGS DE COLETA

O sistema agora registra logs detalhados de cada coleta de comentários, incluindo uso de tokens GPT:

```typescript
GET /api/comments/logs?limit=10
```

**Resposta:** Lista dos últimos logs de coleta com detalhes de tokens usados

```typescript
GET /api/comments/logs/summary?days=7
```

**Resposta:** Resumo estatístico dos últimos N dias incluindo:
- Total de tokens usados
- Percentual médio do limite diário (1M tokens gratuitos)
- Taxa de sucesso
- Tempo médio de execução

```typescript
GET /api/comments/logs/{collection_id}
```

**Resposta:** Log detalhado de uma coleta específica

### IMPORTANTE: SISTEMA DE TOKENS

O sistema agora usa o limite gratuito de 1M tokens/dia do GPT-4o-mini:
- **Capacidade:** ~17.391 comentários/dia
- **Uso estimado:** ~285.000 tokens (28.5% do limite) para ~5.000 comentários
- **Custo:** $0 (gratuito dentro do limite)
- **Cálculo:** ~37.5 tokens input + ~20 tokens output por comentário

---

## INTERFACES TYPESCRIPT COMPLETAS

Adicione estas interfaces no arquivo de tipos do frontend:

```typescript
// ========== INTERFACES PARA SISTEMA DE COMENTÁRIOS ==========

interface CommentStats {
  global_stats: {
    total_channels_analyzed: number;
    total_videos_with_comments: number;
    total_comments: number;
    total_gpt_analyzed: number;
    gpt_coverage_percent: number;
    sentiment_distribution: SentimentDistribution;
    priority_distribution: PriorityDistribution;
    last_collection: string;
    next_collection: string;
  };
  channel_breakdown: ChannelCommentBreakdown[];
  recent_insights: RecentInsight[];
  collection_metrics: CollectionMetrics;
}

interface SentimentDistribution {
  positive: number;
  negative: number;
  neutral: number;
  positive_percent: number;
  negative_percent: number;
  neutral_percent: number;
}

interface PriorityDistribution {
  high: number;
  medium: number;
  low: number;
  high_percent: number;
  medium_percent: number;
  low_percent: number;
}

interface ChannelCommentBreakdown {
  canal_id: number;
  nome_canal: string;
  subnicho: string;
  tipo: string;
  stats: {
    total_videos: number;
    total_comments: number;
    analyzed_comments: number;
    coverage_percent: number;
    sentiment: {
      positive: number;
      negative: number;
      neutral: number;
    };
    avg_sentiment_score: number;
    high_priority_count: number;
    problems_detected: number;
    last_video_date: string;
  };
}

interface RecentInsight {
  canal_nome: string;
  video_title: string;
  comment_preview: string;
  insight: string;
  priority: 'high' | 'medium' | 'low';
  sentiment: 'positive' | 'negative' | 'neutral';
  created_at: string;
}

interface CollectionMetrics {
  last_run_duration_minutes: number;
  videos_processed: number;
  comments_collected: number;
  gpt_api_calls: number;
  gpt_tokens_used: number;
  percentual_limite_diario: number;
  errors_count: number;
  success_rate: number;
}

// ========== INTERFACES PARA ABA ENGAJAMENTO ==========

interface EngagementData {
  summary: {
    total_comments: number;
    positive_count: number;
    negative_count: number;
    positive_pct: number;
    negative_pct: number;
    actionable_count: number;
    problems_count: number;
  };
  videos: VideoEngagement[];
  problems_grouped: ProblemsGrouped;
}

interface VideoEngagement {
  video_id: string;
  video_title: string;
  published_days_ago: number;
  views: number;
  total_comments: number;
  positive_count: number;
  negative_count: number;
  has_problems: boolean;
  problem_count: number;
  sentiment_score: number;
  positive_comments: CommentData[];
  negative_comments: CommentData[];
}

interface CommentData {
  comment_id: string;
  author_name: string;
  comment_text_pt: string;
  comment_text_original?: string;
  is_translated: boolean;
  original_language?: string;
  like_count: number;
  insight_text: string;
  problem_type?: string;
  suggested_action?: string;
  published_at: string;
}

interface ProblemsGrouped {
  audio: ProblemData[];
  video: ProblemData[];
  content: ProblemData[];
  technical: ProblemData[];
}

interface ProblemData {
  video_title: string;
  author: string;
  text_pt: string;
  specific_issue: string;
  suggested_action: string;
}
```

---

## COMPONENTE: DASHBOARD DE COMENTÁRIOS

Crie um novo componente para exibir as estatísticas de comentários no dashboard principal:

```tsx
// src/components/CommentsDashboard.tsx

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  MessageSquare,
  TrendingUp,
  AlertTriangle,
  Clock,
  DollarSign,
  BarChart3,
  ThumbsUp,
  ThumbsDown
} from 'lucide-react';

export function CommentsDashboard() {
  const [stats, setStats] = useState<CommentStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCommentStats();
  }, []);

  const fetchCommentStats = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/comments/stats`);
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Erro ao carregar estatísticas:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div>Carregando estatísticas de comentários...</div>;
  }

  if (!stats) {
    return <div>Erro ao carregar estatísticas</div>;
  }

  return (
    <div className="space-y-6">
      {/* Cards de Resumo */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <MessageSquare className="w-4 h-4" />
              Total Comentários
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.global_stats.total_comments.toLocaleString()}
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {stats.global_stats.total_videos_with_comments} vídeos
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              Análise GPT
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.global_stats.gpt_coverage_percent.toFixed(1)}%
            </div>
            <Progress
              value={stats.global_stats.gpt_coverage_percent}
              className="mt-2"
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <ThumbsUp className="w-4 h-4 text-green-500" />
              Sentimento Geral
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2">
              <Badge variant="outline" className="text-green-500">
                {stats.global_stats.sentiment_distribution.positive_percent.toFixed(0)}% +
              </Badge>
              <Badge variant="outline" className="text-red-500">
                {stats.global_stats.sentiment_distribution.negative_percent.toFixed(0)}% -
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <DollarSign className="w-4 h-4" />
              Custo GPT
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${stats.collection_metrics.estimated_cost_usd.toFixed(2)}
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {stats.collection_metrics.gpt_tokens_used.toLocaleString()} tokens
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs com Detalhes */}
      <Tabs defaultValue="channels" className="w-full">
        <TabsList className="grid grid-cols-3 w-full">
          <TabsTrigger value="channels">Canais</TabsTrigger>
          <TabsTrigger value="insights">Insights Recentes</TabsTrigger>
          <TabsTrigger value="metrics">Métricas de Coleta</TabsTrigger>
        </TabsList>

        {/* Tab: Canais */}
        <TabsContent value="channels">
          <Card>
            <CardHeader>
              <CardTitle>Análise por Canal</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {stats.channel_breakdown
                  .sort((a, b) => b.stats.total_comments - a.stats.total_comments)
                  .slice(0, 10)
                  .map(channel => (
                    <div
                      key={channel.canal_id}
                      className="flex items-center justify-between p-3 border rounded-lg"
                    >
                      <div className="flex-1">
                        <h4 className="font-medium">{channel.nome_canal}</h4>
                        <div className="flex gap-2 mt-1">
                          <Badge variant="outline" className="text-xs">
                            {channel.subnicho}
                          </Badge>
                          <span className="text-xs text-gray-500">
                            {channel.stats.total_comments} comentários
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <div className="text-sm font-medium">
                            {channel.stats.avg_sentiment_score.toFixed(0)}%
                          </div>
                          <div className="text-xs text-gray-500">
                            Sentimento
                          </div>
                        </div>
                        {channel.stats.high_priority_count > 0 && (
                          <Badge variant="destructive" className="text-xs">
                            {channel.stats.high_priority_count} urgente
                          </Badge>
                        )}
                      </div>
                    </div>
                  ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab: Insights Recentes */}
        <TabsContent value="insights">
          <Card>
            <CardHeader>
              <CardTitle>Insights Recentes (Últimas 24h)</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {stats.recent_insights.map((insight, idx) => (
                  <div
                    key={idx}
                    className={`p-3 border rounded-lg ${
                      insight.priority === 'high'
                        ? 'border-red-500 bg-red-900/10'
                        : 'border-gray-700'
                    }`}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h4 className="font-medium text-sm">
                          {insight.canal_nome}
                        </h4>
                        <p className="text-xs text-gray-500">
                          {insight.video_title}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        <Badge
                          variant={insight.priority === 'high' ? 'destructive' : 'default'}
                          className="text-xs"
                        >
                          {insight.priority}
                        </Badge>
                        <Badge
                          variant="outline"
                          className={`text-xs ${
                            insight.sentiment === 'positive'
                              ? 'text-green-500'
                              : 'text-red-500'
                          }`}
                        >
                          {insight.sentiment}
                        </Badge>
                      </div>
                    </div>
                    <p className="text-sm text-gray-300 mb-1">
                      "{insight.comment_preview}"
                    </p>
                    <p className="text-xs text-yellow-500">
                      💡 {insight.insight}
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab: Métricas de Coleta */}
        <TabsContent value="metrics">
          <Card>
            <CardHeader>
              <CardTitle>Métricas da Última Coleta</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-3">
                  <div>
                    <p className="text-sm text-gray-500">Duração</p>
                    <p className="text-lg font-medium">
                      {stats.collection_metrics.last_run_duration_minutes} minutos
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Vídeos Processados</p>
                    <p className="text-lg font-medium">
                      {stats.collection_metrics.videos_processed}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Comentários Coletados</p>
                    <p className="text-lg font-medium">
                      {stats.collection_metrics.comments_collected}
                    </p>
                  </div>
                </div>
                <div className="space-y-3">
                  <div>
                    <p className="text-sm text-gray-500">Taxa de Sucesso</p>
                    <p className="text-lg font-medium">
                      {stats.collection_metrics.success_rate}%
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Chamadas GPT</p>
                    <p className="text-lg font-medium">
                      {stats.collection_metrics.gpt_api_calls}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Erros</p>
                    <p className="text-lg font-medium">
                      {stats.collection_metrics.errors_count}
                    </p>
                  </div>
                </div>
              </div>

              <div className="mt-6 p-3 bg-blue-900/20 border border-blue-700 rounded-lg">
                <p className="text-sm">
                  <Clock className="w-4 h-4 inline mr-1" />
                  Próxima coleta: {new Date(stats.global_stats.next_collection).toLocaleString()}
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

---

## ADICIONAR ABA "ENGAJAMENTO" NO MODAL ANALYTICS

### IMPORTANTE: APENAS PARA CANAIS tipo="nosso"

A aba "Engajamento" deve aparecer APENAS para canais próprios (tipo="nosso").

### MODIFICAÇÕES NO ARQUIVO ModalAnalytics.tsx

#### 1. ATUALIZAR TABSLIST

```tsx
<TabsList className={`grid ${canal?.tipo === 'nosso' ? 'grid-cols-6' : 'grid-cols-5'} w-full px-6 bg-gray-800 border-b border-gray-700`}>
  <TabsTrigger value="overview">Visão Geral</TabsTrigger>
  <TabsTrigger value="metrics">Métricas</TabsTrigger>
  <TabsTrigger value="videos">Top Vídeos</TabsTrigger>
  <TabsTrigger value="patterns">Padrões</TabsTrigger>
  <TabsTrigger value="diagnostics">Diagnóstico</TabsTrigger>
  {canal?.tipo === 'nosso' && (
    <TabsTrigger value="engagement">💬 Engajamento</TabsTrigger>
  )}
</TabsList>
```

#### 2. ADICIONAR IMPORTS

```tsx
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { Button } from '@/components/ui/button';
import { MessageSquare, ThumbsUp, ThumbsDown } from 'lucide-react';
```

#### 3. ADICIONAR ESTADOS

```tsx
const [engagementData, setEngagementData] = useState<EngagementData | null>(null);
const [engagementLoading, setEngagementLoading] = useState(false);
const [showMoreVideos, setShowMoreVideos] = useState<{[key: string]: boolean}>({});
```

#### 4. ADICIONAR USEEFFECT E FUNÇÃO

```tsx
useEffect(() => {
  if (isOpen && canalId && activeTab === 'engagement' && canal?.tipo === 'nosso') {
    fetchEngagementData();
  }
}, [isOpen, canalId, activeTab, canal?.tipo]);

const fetchEngagementData = async () => {
  setEngagementLoading(true);

  try {
    const response = await fetch(
      `${import.meta.env.VITE_API_URL}/api/canais/${canalId}/engagement`
    );

    if (!response.ok) {
      throw new Error('Erro ao carregar dados de engajamento');
    }

    const result = await response.json();
    setEngagementData(result);
  } catch (err) {
    console.error('Erro ao buscar engagement:', err);
    setEngagementData(null);
  } finally {
    setEngagementLoading(false);
  }
};
```

#### 5. ADICIONAR TAB CONTENT COMPLETA

```tsx
{/* ============================================ */}
{/* TAB: ENGAJAMENTO (COMENTÁRIOS)              */}
{/* APENAS PARA CANAIS tipo="nosso"            */}
{/* ============================================ */}
{canal?.tipo === 'nosso' && (
<TabsContent value="engagement" className="p-6 space-y-4">
  {engagementLoading ? (
    // Loading state
    <div className="space-y-4">
      <Skeleton className="h-32 w-full" />
      <Skeleton className="h-64 w-full" />
      <Skeleton className="h-48 w-full" />
    </div>
  ) : engagementData ? (
    <>
      {/* ========== RESUMO EXECUTIVO ========== */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Card Total Comentários */}
        <Card className="bg-gray-800 border-gray-700">
          <CardContent className="p-4">
            <div className="text-2xl font-bold">
              {engagementData.summary.total_comments}
            </div>
            <p className="text-sm text-gray-400">Total Comentários</p>
          </CardContent>
        </Card>

        {/* Card Positivos */}
        <Card className="bg-green-900/20 border-green-700">
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-green-400">
              {engagementData.summary.positive_count}
              <span className="text-sm ml-1">
                ({engagementData.summary.positive_pct.toFixed(1)}%)
              </span>
            </div>
            <p className="text-sm text-gray-400">Positivos</p>
          </CardContent>
        </Card>

        {/* Card Negativos */}
        <Card className="bg-red-900/20 border-red-700">
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-red-400">
              {engagementData.summary.negative_count}
              <span className="text-sm ml-1">
                ({engagementData.summary.negative_pct.toFixed(1)}%)
              </span>
            </div>
            <p className="text-sm text-gray-400">Negativos</p>
          </CardContent>
        </Card>

        {/* Card Ação Necessária */}
        <Card className="bg-yellow-900/20 border-yellow-700">
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-yellow-400">
              {engagementData.summary.actionable_count}
            </div>
            <p className="text-sm text-gray-400">Ação Necessária</p>
          </CardContent>
        </Card>
      </div>

      {/* ========== ANÁLISE POR VÍDEO - ACCORDIONS ========== */}
      <Card className="bg-gray-800 border-gray-700">
        <CardHeader>
          <CardTitle className="text-xl">🎥 Comentários por Vídeo</CardTitle>
        </CardHeader>
        <CardContent>
          <Accordion type="multiple" className="space-y-2">
            {engagementData.videos.slice(0, 10).map((video, index) => (
              <AccordionItem
                key={video.video_id}
                value={`video-${index}`}
                className="border border-gray-700 rounded-lg bg-gray-900/50"
              >
                <AccordionTrigger className="px-4 hover:no-underline">
                  <div className="flex flex-col md:flex-row md:justify-between md:items-start w-full mr-4 gap-2">
                    <div className="text-left flex-1">
                      <h4 className="font-semibold text-sm md:text-base">
                        {video.video_title}
                      </h4>
                      <p className="text-xs md:text-sm text-gray-400 mt-1">
                        📅 {video.published_days_ago}d atrás •
                        👁️ {formatNumber(video.views)} views •
                        💬 {video.total_comments} comentários
                      </p>
                    </div>
                    <div className="flex gap-2 flex-wrap">
                      {video.has_problems && (
                        <Badge variant="destructive" className="text-xs">
                          {video.problem_count} problema{video.problem_count > 1 ? 's' : ''}
                        </Badge>
                      )}
                      <Badge
                        variant="outline"
                        className={`text-xs ${
                          video.sentiment_score > 0
                            ? 'text-green-400 border-green-700'
                            : 'text-red-400 border-red-700'
                        }`}
                      >
                        {video.sentiment_score > 0 ? '😊' : '😟'}{' '}
                        {Math.abs(video.sentiment_score).toFixed(1)}%
                      </Badge>
                    </div>
                  </div>
                </AccordionTrigger>

                <AccordionContent className="px-4 pb-4">
                  <Tabs defaultValue="positive" className="w-full">
                    <TabsList className="grid grid-cols-2 w-full">
                      <TabsTrigger value="positive">
                        <ThumbsUp className="w-4 h-4 mr-1" />
                        Positivos ({video.positive_count})
                      </TabsTrigger>
                      <TabsTrigger value="negative">
                        <ThumbsDown className="w-4 h-4 mr-1" />
                        Negativos ({video.negative_count})
                      </TabsTrigger>
                    </TabsList>

                    {/* ===== TAB COMENTÁRIOS POSITIVOS ===== */}
                    <TabsContent value="positive" className="mt-4 space-y-3">
                      {video.positive_comments.length > 0 ? (
                        <>
                          {video.positive_comments
                            .slice(0, showMoreVideos[video.video_id] ? 10 : 3)
                            .map((comment) => (
                              <div
                                key={comment.comment_id}
                                className="bg-green-900/10 border border-green-800/30 rounded-lg p-3"
                              >
                                <div className="flex justify-between items-start mb-2">
                                  <span className="font-medium text-sm">
                                    {comment.author_name}
                                  </span>
                                  <span className="text-xs text-gray-500">
                                    👍 {comment.like_count}
                                  </span>
                                </div>

                                <p className="text-sm mb-2">
                                  {comment.comment_text_pt}
                                </p>

                                {comment.is_translated && (
                                  <p className="text-xs text-gray-500 italic">
                                    🌐 Traduzido de: {comment.original_language?.toUpperCase()}
                                  </p>
                                )}

                                {comment.insight_text && (
                                  <div className="mt-2 pt-2 border-t border-gray-700">
                                    <p className="text-xs text-green-400">
                                      💡 {comment.insight_text}
                                    </p>
                                  </div>
                                )}
                              </div>
                            ))}

                          {/* Botão Ver Mais */}
                          {video.positive_comments.length > 3 &&
                            !showMoreVideos[video.video_id] && (
                              <Button
                                variant="ghost"
                                size="sm"
                                className="w-full text-green-400 hover:text-green-300"
                                onClick={() =>
                                  setShowMoreVideos({
                                    ...showMoreVideos,
                                    [video.video_id]: true,
                                  })
                                }
                              >
                                Ver mais {video.positive_comments.length - 3}{' '}
                                comentários positivos
                              </Button>
                            )}
                        </>
                      ) : (
                        <p className="text-sm text-gray-500 text-center py-4">
                          Nenhum comentário positivo encontrado
                        </p>
                      )}
                    </TabsContent>

                    {/* ===== TAB COMENTÁRIOS NEGATIVOS ===== */}
                    <TabsContent value="negative" className="mt-4 space-y-3">
                      {video.negative_comments.length > 0 ? (
                        video.negative_comments.map((comment) => (
                          <div
                            key={comment.comment_id}
                            className="bg-red-900/10 border border-red-800/30 rounded-lg p-3"
                          >
                            <div className="flex justify-between items-start mb-2">
                              <span className="font-medium text-sm">
                                {comment.author_name}
                              </span>
                              <div className="flex gap-2 items-center">
                                {comment.problem_type && (
                                  <Badge variant="destructive" className="text-xs">
                                    {comment.problem_type}
                                  </Badge>
                                )}
                                <span className="text-xs text-gray-500">
                                  👍 {comment.like_count}
                                </span>
                              </div>
                            </div>

                            <p className="text-sm mb-2">
                              {comment.comment_text_pt}
                            </p>

                            {comment.is_translated && (
                              <p className="text-xs text-gray-500 italic">
                                🌐 Traduzido de: {comment.original_language?.toUpperCase()}
                              </p>
                            )}

                            <div className="mt-2 pt-2 border-t border-gray-700 space-y-1">
                              <p className="text-xs text-red-400">
                                💡 {comment.insight_text}
                              </p>
                              {comment.suggested_action && (
                                <p className="text-xs text-yellow-400">
                                  → Ação: {comment.suggested_action}
                                </p>
                              )}
                            </div>
                          </div>
                        ))
                      ) : (
                        <p className="text-sm text-gray-500 text-center py-4">
                          Nenhum comentário negativo encontrado
                        </p>
                      )}
                    </TabsContent>
                  </Tabs>
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>

          {/* Nota sobre limite de vídeos */}
          {engagementData.videos.length > 10 && (
            <p className="text-xs text-gray-500 text-center mt-4">
              Mostrando os 10 vídeos mais recentes de {engagementData.videos.length} totais
            </p>
          )}
        </CardContent>
      </Card>

      {/* ========== PROBLEMAS AGRUPADOS POR CATEGORIA ========== */}
      {engagementData.summary.problems_count > 0 && (
        <Card className="bg-gray-800 border-gray-700">
          <CardHeader>
            <CardTitle>⚠️ Problemas Detectados</CardTitle>
            <p className="text-sm text-gray-400">
              Análise de {engagementData.summary.problems_count} problemas identificados
            </p>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="audio">
              <TabsList className="grid grid-cols-2 md:grid-cols-4 w-full">
                <TabsTrigger value="audio" className="text-xs md:text-sm">
                  🔊 Áudio ({engagementData.problems_grouped.audio.length})
                </TabsTrigger>
                <TabsTrigger value="video" className="text-xs md:text-sm">
                  📹 Vídeo ({engagementData.problems_grouped.video.length})
                </TabsTrigger>
                <TabsTrigger value="content" className="text-xs md:text-sm">
                  📝 Conteúdo ({engagementData.problems_grouped.content.length})
                </TabsTrigger>
                <TabsTrigger value="technical" className="text-xs md:text-sm">
                  🔧 Técnico ({engagementData.problems_grouped.technical.length})
                </TabsTrigger>
              </TabsList>

              {/* Conteúdo das tabs de problemas */}
              {Object.entries(engagementData.problems_grouped).map(
                ([type, problems]) => (
                  <TabsContent
                    key={type}
                    value={type}
                    className="mt-4 space-y-3"
                  >
                    {problems.length > 0 ? (
                      <>
                        {problems.slice(0, 5).map((problem, idx) => (
                          <div
                            key={idx}
                            className="bg-red-900/20 border border-red-700 rounded-lg p-3"
                          >
                            <div className="flex flex-col md:flex-row md:justify-between md:items-start gap-2 mb-2">
                              <div className="flex-1">
                                <p className="font-medium text-sm">
                                  {problem.video_title}
                                </p>
                                <p className="text-xs text-gray-400">
                                  Reportado por: {problem.author}
                                </p>
                              </div>
                              <Badge variant="destructive" className="text-xs self-start">
                                {type.toUpperCase()}
                              </Badge>
                            </div>
                            <p className="text-sm mb-2 text-gray-300">
                              "{problem.text_pt}"
                            </p>
                            <div className="flex items-start gap-2">
                              <span className="text-xs text-yellow-400">→</span>
                              <p className="text-xs text-yellow-400">
                                {problem.suggested_action}
                              </p>
                            </div>
                          </div>
                        ))}

                        {problems.length > 5 && (
                          <p className="text-xs text-gray-500 text-center">
                            +{problems.length - 5} problemas adicionais nesta categoria
                          </p>
                        )}
                      </>
                    ) : (
                      <div className="text-center py-8">
                        <p className="text-sm text-gray-500">
                          Nenhum problema deste tipo detectado
                        </p>
                        <p className="text-xs text-gray-600 mt-1">
                          Excelente! Continue mantendo a qualidade
                        </p>
                      </div>
                    )}
                  </TabsContent>
                )
              )}
            </Tabs>
          </CardContent>
        </Card>
      )}
    </>
  ) : (
    // Estado vazio - sem dados
    <Card className="bg-gray-800 border-gray-700">
      <CardContent className="p-8 text-center">
        <MessageSquare className="w-12 h-12 mx-auto mb-4 text-gray-600" />
        <h3 className="text-lg font-semibold mb-2">
          Ainda não há dados de engajamento
        </h3>
        <p className="text-gray-400">
          Os comentários dos vídeos ainda não foram coletados.
        </p>
        <p className="text-sm text-gray-500 mt-2">
          Execute a coleta de comentários no backend para ver análises detalhadas.
        </p>
      </CardContent>
    </Card>
  )}
</TabsContent>
)}
```

---

## ESTRUTURA DE TABELAS NO SUPABASE

### Tabelas Criadas:

1. **video_comments** - Armazena todos os comentários coletados
2. **video_comments_summary** - Resumo agregado por vídeo
3. **gpt_analysis_metrics** - Métricas de uso da API do GPT
4. **canais_monitorados** - Atualizada com campo `ultimo_comentario_coletado`

### Campos Importantes:

#### video_comments:
- comment_id (PK)
- video_id
- canal_id
- author_name
- comment_text
- comment_text_pt (traduzido)
- original_language
- sentiment_score (-100 a 100)
- sentiment_category (positive/negative/neutral)
- priority_score (0-100)
- insight_text
- problem_type (audio/video/content/technical)
- suggested_action
- is_channel_owner (boolean)
- published_at
- analyzed_at

#### video_comments_summary:
- video_id (PK)
- canal_id
- total_comments
- analyzed_count
- positive_count
- negative_count
- neutral_count
- avg_sentiment_score
- high_priority_count
- problems_count

#### gpt_analysis_metrics:
- execution_date
- total_requests
- total_tokens_input
- total_tokens_output
- estimated_cost_usd
- success_rate

#### canais_monitorados (campo novo):
- ultimo_comentario_coletado (TIMESTAMP)
- total_comentarios_coletados (INTEGER)

---

## INFORMAÇÕES TÉCNICAS DO SISTEMA

### Coleta Diária:
- **Horário:** 5:00 AM (Brasil)
- **Duração:** ~45-120 minutos
- **Canais:** 305 total (270 minerados + 35 nossos)
- **Comentários:** Apenas dos 35 canais "nossos"

### Otimizações Implementadas:
1. **Batch Size:** 15 comentários por vez (reduzido de 20)
2. **Timeout:** 2 horas máximo por coleta
3. **Retry Logic:** 3 tentativas para falhas do GPT
4. **Coleta Incremental:** Após primeira coleta, só busca novos comentários
5. **Economia:** ~60% da quota após primeira coleta completa

### Custos Estimados:
- **GPT-4o-mini:** $0.15/1M input, $0.60/1M output
- **Custo diário:** ~$0.35-0.50
- **Custo mensal:** ~$10-15

### APIs Utilizadas:
- YouTube Data API v3 (comentários)
- OpenAI GPT-4o-mini (análise)
- Supabase (armazenamento)

---

## CONFIGURAÇÃO DE AMBIENTE

Adicione estas variáveis no Lovable se ainda não existirem:

```env
VITE_API_URL=https://sua-api.railway.app
```

---

## PRÓXIMOS PASSOS PARA IMPLEMENTAÇÃO

1. **Implementar Dashboard de Comentários:**
   - Adicionar o componente CommentsDashboard em uma nova página ou aba
   - Criar rota `/comments` ou adicionar como aba no dashboard principal

2. **Integrar Aba Engajamento:**
   - Modificar ModalAnalytics.tsx com o código fornecido
   - Testar com canais tipo="nosso"

3. **Adicionar Filtros:**
   - Filtro por subnicho
   - Filtro por período
   - Filtro por prioridade

4. **Notificações:**
   - Alertas para comentários de alta prioridade
   - Resumo diário de insights

5. **Exportação:**
   - Botão para exportar relatório de comentários
   - CSV com análise detalhada

---

## TESTE DA IMPLEMENTAÇÃO

### Para testar o Dashboard de Comentários:
1. Acesse a página de comentários
2. Verifique se as estatísticas carregam
3. Navegue entre as abas
4. Teste responsividade mobile

### Para testar a Aba Engajamento:
1. Abra Modal Analytics de um canal tipo="nosso"
2. Clique na aba "💬 Engajamento"
3. Verifique accordions dos vídeos
4. Teste tabs positivo/negativo
5. Verifique problemas agrupados

---

## NOTAS IMPORTANTES

- Sistema coleta às 5 AM automaticamente
- Primeira coleta será completa (todos comentários)
- Próximas coletas serão incrementais (apenas novos)
- Comentários são traduzidos automaticamente para PT
- GPT analisa sentimento, prioridade e gera insights
- Problemas são categorizados automaticamente
- Dashboard atualiza após cada coleta
- Coleta incremental economiza 60% da quota diária
- Sistema tem retry automático para falhas do GPT
- Timeout de segurança de 2 horas por coleta

---

## HISTÓRICO DE ATUALIZAÇÕES

### 19/01/2026 - Sistema de Comentários com GPT
- Implementado sistema completo de análise de comentários
- Integração com GPT-4o-mini para análise de sentimento
- Coleta incremental para economia de quota
- Batch size otimizado para 15 comentários
- Retry logic com 3 tentativas
- Timeout de segurança de 2 horas
- Novo endpoint `/api/comments/stats`
- Novo endpoint `/api/canais/{id}/engagement`
- Dashboard de comentários completo
- Aba Engajamento no Modal Analytics

### Versões Anteriores
- Sistema de notificações inteligente
- Aba Tabela para canais nossos
- Expansão de API keys
- Tracking de falhas de coleta

---

**FIM DO PROMPT - COPIAR TODO O CONTEÚDO ACIMA E COLAR NO LOVABLE**
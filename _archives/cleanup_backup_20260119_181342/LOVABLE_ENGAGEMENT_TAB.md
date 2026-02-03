# 💬 INSTRUÇÕES: Adicionar Nova Aba "Engajamento" no Modal Analytics

## CONTEXTO
Adicione uma 6ª aba no Modal Analytics para mostrar análise de comentários dos vídeos do canal. A aba deve ter design limpo com acordeões colapsáveis para evitar poluição visual.

## PASSO 1: Atualizar o número de tabs no ModalAnalytics.tsx

### Localize a TabsList e mude de 5 para 6 colunas:
```tsx
<TabsList className="grid grid-cols-6 w-full px-6 bg-gray-800 border-b border-gray-700">
  <TabsTrigger value="overview">Visão Geral</TabsTrigger>
  <TabsTrigger value="metrics">Métricas</TabsTrigger>
  <TabsTrigger value="videos">Top Vídeos</TabsTrigger>
  <TabsTrigger value="patterns">Padrões</TabsTrigger>
  <TabsTrigger value="diagnostics">Diagnóstico</TabsTrigger>
  <TabsTrigger value="engagement">💬 Engajamento</TabsTrigger> {/* NOVA ABA */}
</TabsList>
```

## PASSO 2: Adicionar Interfaces TypeScript

### Adicione estas interfaces no início do arquivo (após as interfaces existentes):

```typescript
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
  videos: Array<{
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
    positive_comments: Array<Comment>;
    negative_comments: Array<Comment>;
  }>;
  problems_grouped: {
    audio: Array<Problem>;
    video: Array<Problem>;
    content: Array<Problem>;
    technical: Array<Problem>;
  };
}

interface Comment {
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

interface Problem {
  video_title: string;
  author: string;
  text_pt: string;
  specific_issue: string;
  suggested_action: string;
}
```

## PASSO 3: Adicionar Estado e Fetch de Dados

### No componente, adicione o estado para engagement:
```tsx
const [engagementData, setEngagementData] = useState<EngagementData | null>(null);
const [engagementLoading, setEngagementLoading] = useState(false);
const [showMoreVideos, setShowMoreVideos] = useState<{[key: string]: boolean}>({});
```

### Adicione o fetch de dados no useEffect existente ou crie um novo:
```tsx
useEffect(() => {
  if (isOpen && canalId && activeTab === 'engagement') {
    fetchEngagementData();
  }
}, [isOpen, canalId, activeTab]);

const fetchEngagementData = async () => {
  setEngagementLoading(true);

  try {
    const response = await fetch(`${import.meta.env.VITE_API_URL}/api/canais/${canalId}/engagement`);

    if (!response.ok) {
      throw new Error('Erro ao carregar dados de engajamento');
    }

    const result = await response.json();
    setEngagementData(result);
  } catch (err) {
    console.error('Erro ao buscar engagement:', err);
  } finally {
    setEngagementLoading(false);
  }
};
```

## PASSO 4: Adicionar imports necessários

### Adicione estes imports no topo do arquivo:
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

## PASSO 5: Adicionar a Nova Tab Content

### Adicione este código dentro do ScrollArea, após a última TabsContent:

```tsx
{/* Tab: Engajamento (Comentários) */}
<TabsContent value="engagement" className="p-6 space-y-4">
  {engagementLoading ? (
    <div className="space-y-4">
      <Skeleton className="h-32 w-full" />
      <Skeleton className="h-64 w-full" />
      <Skeleton className="h-48 w-full" />
    </div>
  ) : engagementData ? (
    <>
      {/* Resumo Executivo */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-gray-800 border-gray-700">
          <CardContent className="p-4">
            <div className="text-2xl font-bold">{engagementData.summary.total_comments}</div>
            <p className="text-sm text-gray-400">Total Comentários</p>
          </CardContent>
        </Card>

        <Card className="bg-green-900/20 border-green-700">
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-green-400">
              {engagementData.summary.positive_count}
              <span className="text-sm ml-1">({engagementData.summary.positive_pct}%)</span>
            </div>
            <p className="text-sm text-gray-400">Positivos</p>
          </CardContent>
        </Card>

        <Card className="bg-red-900/20 border-red-700">
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-red-400">
              {engagementData.summary.negative_count}
              <span className="text-sm ml-1">({engagementData.summary.negative_pct}%)</span>
            </div>
            <p className="text-sm text-gray-400">Negativos</p>
          </CardContent>
        </Card>

        <Card className="bg-yellow-900/20 border-yellow-700">
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-yellow-400">
              {engagementData.summary.actionable_count}
            </div>
            <p className="text-sm text-gray-400">Ação Necessária</p>
          </CardContent>
        </Card>
      </div>

      {/* Análise por Vídeo - Accordion */}
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
                  <div className="flex justify-between items-start w-full mr-4">
                    <div className="text-left">
                      <h4 className="font-semibold">{video.video_title}</h4>
                      <p className="text-sm text-gray-400">
                        📅 {video.published_days_ago} dias atrás •
                        👁️ {formatNumber(video.views)} views •
                        💬 {video.total_comments} comentários
                      </p>
                    </div>
                    <div className="flex gap-2">
                      {video.has_problems && (
                        <Badge variant="destructive" size="sm">
                          {video.problem_count} problemas
                        </Badge>
                      )}
                      <Badge
                        variant="outline"
                        className={video.sentiment_score > 0 ? 'text-green-400' : 'text-red-400'}
                      >
                        {video.sentiment_score > 0 ? '😊' : '😟'} {Math.abs(video.sentiment_score)}%
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

                    {/* Comentários Positivos */}
                    <TabsContent value="positive" className="mt-4 space-y-3">
                      {video.positive_comments.length > 0 ? (
                        video.positive_comments.slice(0, showMoreVideos[video.video_id] ? 10 : 3).map((comment) => (
                          <div
                            key={comment.comment_id}
                            className="bg-green-900/10 border border-green-800/30 rounded-lg p-3"
                          >
                            <div className="flex justify-between items-start mb-2">
                              <span className="font-medium text-sm">{comment.author_name}</span>
                              <span className="text-xs text-gray-500">👍 {comment.like_count}</span>
                            </div>

                            <p className="text-sm mb-2">{comment.comment_text_pt}</p>
                            {comment.is_translated && (
                              <p className="text-xs text-gray-500 italic">
                                Traduzido de: {comment.original_language}
                              </p>
                            )}

                            {comment.insight_text && (
                              <div className="mt-2 pt-2 border-t border-gray-700">
                                <p className="text-xs text-green-400">💡 {comment.insight_text}</p>
                              </div>
                            )}
                          </div>
                        ))
                      ) : (
                        <p className="text-sm text-gray-500">Nenhum comentário positivo encontrado</p>
                      )}

                      {video.positive_comments.length > 3 && !showMoreVideos[video.video_id] && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="w-full"
                          onClick={() => setShowMoreVideos({...showMoreVideos, [video.video_id]: true})}
                        >
                          Ver mais {video.positive_comments.length - 3} comentários
                        </Button>
                      )}
                    </TabsContent>

                    {/* Comentários Negativos */}
                    <TabsContent value="negative" className="mt-4 space-y-3">
                      {video.negative_comments.length > 0 ? (
                        video.negative_comments.map((comment) => (
                          <div
                            key={comment.comment_id}
                            className="bg-red-900/10 border border-red-800/30 rounded-lg p-3"
                          >
                            <div className="flex justify-between items-start mb-2">
                              <span className="font-medium text-sm">{comment.author_name}</span>
                              <div className="flex gap-2">
                                {comment.problem_type && (
                                  <Badge variant="destructive" size="sm">
                                    {comment.problem_type}
                                  </Badge>
                                )}
                                <span className="text-xs text-gray-500">👍 {comment.like_count}</span>
                              </div>
                            </div>

                            <p className="text-sm mb-2">{comment.comment_text_pt}</p>
                            {comment.is_translated && (
                              <p className="text-xs text-gray-500 italic">
                                Traduzido de: {comment.original_language}
                              </p>
                            )}

                            <div className="mt-2 pt-2 border-t border-gray-700">
                              <p className="text-xs text-red-400">💡 {comment.insight_text}</p>
                              {comment.suggested_action && (
                                <p className="text-xs text-yellow-400 mt-1">
                                  → Ação: {comment.suggested_action}
                                </p>
                              )}
                            </div>
                          </div>
                        ))
                      ) : (
                        <p className="text-sm text-gray-500">Nenhum comentário negativo encontrado</p>
                      )}
                    </TabsContent>
                  </Tabs>
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </CardContent>
      </Card>

      {/* Problemas Agrupados */}
      {engagementData.summary.problems_count > 0 && (
        <Card className="bg-gray-800 border-gray-700">
          <CardHeader>
            <CardTitle>⚠️ Problemas Detectados</CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="audio">
              <TabsList className="grid grid-cols-4 w-full">
                <TabsTrigger value="audio">
                  🔊 Áudio ({engagementData.problems_grouped.audio.length})
                </TabsTrigger>
                <TabsTrigger value="video">
                  📹 Vídeo ({engagementData.problems_grouped.video.length})
                </TabsTrigger>
                <TabsTrigger value="content">
                  📝 Conteúdo ({engagementData.problems_grouped.content.length})
                </TabsTrigger>
                <TabsTrigger value="technical">
                  🔧 Técnico ({engagementData.problems_grouped.technical.length})
                </TabsTrigger>
              </TabsList>

              {/* Tab de cada tipo de problema */}
              {Object.entries(engagementData.problems_grouped).map(([type, problems]) => (
                <TabsContent key={type} value={type} className="mt-4 space-y-3">
                  {problems.length > 0 ? (
                    problems.slice(0, 5).map((problem, idx) => (
                      <div key={idx} className="bg-red-900/20 border border-red-700 rounded-lg p-3">
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <p className="font-medium text-sm">{problem.video_title}</p>
                            <p className="text-xs text-gray-400">Por: {problem.author}</p>
                          </div>
                          <Badge variant="destructive" size="sm">{type}</Badge>
                        </div>
                        <p className="text-sm mb-2">{problem.text_pt}</p>
                        <p className="text-xs text-yellow-400">→ {problem.suggested_action}</p>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-gray-500">Nenhum problema deste tipo detectado</p>
                  )}
                </TabsContent>
              ))}
            </Tabs>
          </CardContent>
        </Card>
      )}
    </>
  ) : (
    <Card className="bg-gray-800 border-gray-700">
      <CardContent className="p-8 text-center">
        <MessageSquare className="w-12 h-12 mx-auto mb-4 text-gray-600" />
        <p className="text-gray-400">
          Ainda não há dados de engajamento disponíveis.
          Execute a coleta de comentários para ver análises.
        </p>
      </CardContent>
    </Card>
  )}
</TabsContent>
```

## CONFIGURAÇÕES IMPORTANTES

### 1. Responsividade Mobile
- No mobile (<768px), mude grid-cols-4 para grid-cols-2 nos cards de resumo
- Accordions funcionam naturalmente bem em mobile
- Tabs dentro dos accordions devem manter 2 colunas

### 2. Cores Consistentes
- Mantenha o padrão de cores do dashboard:
  - Background: `bg-gray-900`, `bg-gray-800`
  - Bordas: `border-gray-700`
  - Positivo: `bg-green-900/10`, `border-green-800/30`
  - Negativo: `bg-red-900/10`, `border-red-800/30`
  - Ação necessária: `bg-yellow-900/20`, `text-yellow-400`

### 3. Performance
- Limite inicial de 10 vídeos no accordion
- Mostra 3 comentários por padrão, expande para 10 com botão "Ver mais"
- Lazy loading dos dados quando a aba é selecionada

## RESULTADO ESPERADO

1. **Nova aba "💬 Engajamento"** aparece como 6ª opção
2. **Design limpo** com accordions colapsáveis
3. **Organização por vídeo** com tabs positivo/negativo
4. **Problemas agrupados** por categoria
5. **100% responsivo** mobile/desktop
6. **Dados em tempo real** do endpoint `/api/canais/{id}/engagement`

## TESTE RÁPIDO

1. Abra o Modal Analytics de qualquer canal "nosso"
2. Clique na aba "💬 Engajamento"
3. Verifique se os dados carregam
4. Teste expandir/colapsar os accordions
5. Teste alternar entre comentários positivos/negativos
6. Verifique responsividade redimensionando a janela

---

## FIM DAS INSTRUÇÕES

Implementação estimada: 15-20 minutos
Resultado: Sistema completo de análise de comentários integrado ao dashboard
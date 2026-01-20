# PROMPT COMPLETO PARA LOVABLE - ABA ENGAJAMENTO

**COPIE TODO ESTE CONTEÚDO E COLE NO LOVABLE**

---

## ADICIONAR ABA "ENGAJAMENTO" NO MODAL ANALYTICS

Preciso adicionar uma 6ª aba chamada "Engajamento" no Modal Analytics para exibir análise de comentários dos vídeos do canal. O design deve ser limpo com accordions colapsáveis.

### CONTEXTO
- O Modal Analytics já existe em `src/components/ModalAnalytics.tsx`
- Atualmente tem 5 abas: Visão Geral, Métricas, Top Vídeos, Padrões, Diagnóstico
- Preciso adicionar a 6ª aba: Engajamento
- O backend já tem o endpoint pronto: `GET /api/canais/{canalId}/engagement`

### EXEMPLO DE RESPOSTA DO ENDPOINT

```json
{
  "summary": {
    "total_comments": 245,
    "positive_count": 180,
    "negative_count": 42,
    "positive_pct": 73.5,
    "negative_pct": 17.1,
    "actionable_count": 12,
    "problems_count": 15
  },
  "videos": [
    {
      "video_id": "abc123",
      "video_title": "História de Terror Assustadora",
      "published_days_ago": 3,
      "views": 45000,
      "total_comments": 89,
      "positive_count": 67,
      "negative_count": 12,
      "has_problems": true,
      "problem_count": 3,
      "sentiment_score": 82.5,
      "positive_comments": [
        {
          "comment_id": "xyz789",
          "author_name": "João Silva",
          "comment_text_pt": "Vídeo excelente! A narração está perfeita!",
          "comment_text_original": "Great video! Perfect narration!",
          "is_translated": true,
          "original_language": "en",
          "like_count": 45,
          "insight_text": "[ELOGIO] Narração aprovada - manter padrão",
          "published_at": "2024-01-15T10:30:00Z"
        }
      ],
      "negative_comments": [
        {
          "comment_id": "abc456",
          "author_name": "Maria Santos",
          "comment_text_pt": "O áudio está muito baixo, não consigo ouvir",
          "comment_text_original": "O áudio está muito baixo, não consigo ouvir",
          "is_translated": false,
          "original_language": "pt",
          "like_count": 12,
          "insight_text": "[PROBLEMA] Áudio com volume baixo",
          "problem_type": "audio",
          "suggested_action": "Verificar configurações de áudio na próxima gravação",
          "published_at": "2024-01-15T09:15:00Z"
        }
      ]
    }
  ],
  "problems_grouped": {
    "audio": [
      {
        "video_title": "História de Terror #45",
        "author": "Pedro Costa",
        "text_pt": "Som muito baixo no início",
        "specific_issue": "Volume baixo",
        "suggested_action": "Ajustar ganho do microfone"
      }
    ],
    "video": [],
    "content": [],
    "technical": []
  }
}
```

---

## MUDANÇAS NECESSÁRIAS NO ARQUIVO

### 1. ATUALIZAR TABSLIST

**IMPORTANTE:** A aba "Engajamento" deve aparecer APENAS para canais tipo="nosso" (canais próprios).

Localize a `TabsList` e modifique para mostrar condicionalmente a 6ª aba:

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

### 2. ADICIONAR IMPORTS

No topo do arquivo, adicione estes imports se ainda não existirem:

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

### 3. ADICIONAR INTERFACES TYPESCRIPT

Adicione estas interfaces após as interfaces existentes no arquivo:

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
    positive_comments: Array<CommentData>;
    negative_comments: Array<CommentData>;
  }>;
  problems_grouped: {
    audio: Array<ProblemData>;
    video: Array<ProblemData>;
    content: Array<ProblemData>;
    technical: Array<ProblemData>;
  };
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

interface ProblemData {
  video_title: string;
  author: string;
  text_pt: string;
  specific_issue: string;
  suggested_action: string;
}
```

### 4. ADICIONAR ESTADOS

No componente, adicione estes estados junto com os outros estados:

```tsx
const [engagementData, setEngagementData] = useState<EngagementData | null>(null);
const [engagementLoading, setEngagementLoading] = useState(false);
const [showMoreVideos, setShowMoreVideos] = useState<{[key: string]: boolean}>({});
```

### 5. ADICIONAR USEEFFECT E FUNÇÃO DE FETCH

Adicione este useEffect e função:

```tsx
// useEffect para carregar dados quando aba Engajamento é selecionada
// APENAS para canais tipo="nosso"
useEffect(() => {
  if (isOpen && canalId && activeTab === 'engagement' && canal?.tipo === 'nosso') {
    fetchEngagementData();
  }
}, [isOpen, canalId, activeTab, canal?.tipo]);

// Função para buscar dados de engajamento
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

### 6. ADICIONAR NOVA TAB CONTENT

Adicione este código após a última `TabsContent` (depois da aba Diagnóstico):

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

## RESUMO DAS ALTERAÇÕES

### O que foi adicionado:
1. **Nova aba** "💬 Engajamento" na TabsList (mudança de 5 para 6 colunas) - **APENAS para canais tipo="nosso"**
2. **Validação de tipo** - A aba só aparece para canais próprios (tipo="nosso")
3. **3 interfaces TypeScript**: EngagementData, CommentData, ProblemData
3. **3 estados React**: engagementData, engagementLoading, showMoreVideos
4. **1 useEffect** para carregar dados quando aba é selecionada
5. **1 função** fetchEngagementData para buscar dados do backend
6. **Imports necessários**: Accordion, Button, ícones
7. **TabContent completa** com toda a interface de engajamento

### Funcionalidades implementadas:
- 📊 **Resumo executivo** com 4 cards de métricas
- 📹 **Accordions colapsáveis** para cada vídeo (máx 10)
- 👍👎 **Tabs separadas** para comentários positivos e negativos
- 🔍 **Botão "Ver mais"** para expandir de 3 para 10 comentários
- ⚠️ **Seção de problemas** agrupados por categoria (áudio/vídeo/conteúdo/técnico)
- 🌐 **Indicador de tradução** mostra língua original
- 📱 **100% responsivo** (mobile-first design)
- ⚡ **Carregamento lazy** (só busca dados quando aba é aberta)
- 💡 **Insights e ações** sugeridas para cada problema

### Design:
- Usa o mesmo padrão visual do dashboard (gray-800, gray-700)
- Cards com cores temáticas (verde para positivo, vermelho para negativo)
- Accordions com bordas sutis e hover states
- Badges para indicar problemas e sentimento
- Ícones para melhor visualização

---

## TESTE

Para testar a implementação:

1. Abra o Modal Analytics de qualquer canal "nosso"
2. Clique na nova aba "💬 Engajamento"
3. Verifique se os dados carregam corretamente
4. Teste expandir/colapsar os accordions dos vídeos
5. Alterne entre comentários positivos e negativos
6. Teste o botão "Ver mais" para expandir comentários
7. Navegue pelas categorias de problemas
8. Teste em diferentes tamanhos de tela (mobile/tablet/desktop)

---

## NOTAS IMPORTANTES

- O endpoint `/api/canais/{id}/engagement` precisa estar funcionando no backend
- As tabelas `video_comments` e `video_comments_summary` precisam existir no Supabase
- O sistema identifica automaticamente a língua dos comentários
- Comentários traduzidos mostram indicador 🌐 com a língua original
- Limite de 10 vídeos nos accordions para melhor performance
- Máximo de 10 comentários mostrados por vídeo (3 inicial + 7 com botão)
- Máximo de 5 problemas mostrados por categoria

---

**FIM DO PROMPT - COPIAR TODO O CONTEÚDO ACIMA E COLAR NO LOVABLE**
# Integração da Nova Aba "Comentários" no Dashboard

## Resumo
Nova aba "Comentários" na seção **Ferramentas** do dashboard para gerenciar respostas aos comentários dos canais monetizados.

## Objetivo
Permitir que a equipe visualize e copie respostas únicas e humanizadas para comentários dos canais monetizados, garantindo que cada resposta seja diferente para evitar detecção de bots.

## Localização no Dashboard
- **Seção:** Ferramentas
- **Nome da Aba:** Comentários
- **Posição:** Após as abas existentes em Ferramentas

## Endpoint da API
```
GET /api/comments/management
```

### Query Parameters (opcionais)
- `canal_id`: ID específico do canal
- `limit`: Número máximo de comentários por vídeo (padrão: 10)
- `sentiment`: Filtrar por sentimento (positive/negative/neutral)
- `requires_response`: Se true, apenas comentários que precisam resposta

## Estrutura da Resposta JSON

```json
{
  "success": true,
  "canais": [
    {
      "id": 645,
      "nome": "王の影 (new)",
      "url": "https://youtube.com/@...",
      "total_videos": 3,
      "videos": [
        {
          "id": "abc123",
          "titulo": "Título do Vídeo",
          "views": 15000,
          "data_publicacao": "2026-01-25",
          "url": "https://youtube.com/watch?v=abc123",
          "total_comments": 10,
          "comments": [
            {
              "comment_id": "xyz789",
              "author_name": "João Silva",
              "comment_text_original": "Great video! Keep it up!",
              "comment_text_pt": "Ótimo vídeo! Continue assim!",
              "like_count": 45,
              "published_at": "2026-01-25T10:30:00Z",
              "sentiment_category": "positive",
              "sentiment_indicator": "🟢",
              "priority_score": 75,
              "requires_response": true,
              "suggested_reply": "Thanks so much João! More coming soon 🔥"
            }
          ]
        }
      ]
    }
  ],
  "total_comments": 87,
  "total_responses_generated": 87
}
```

## Campos Importantes dos Comentários

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `comment_text_original` | string | Texto original do comentário |
| `comment_text_pt` | string | Tradução em português (se aplicável) |
| `sentiment_indicator` | string | Emoji indicador: 🟢 positivo, 🟡 neutro, 🔴 negativo, ⭐ alto engajamento |
| `suggested_reply` | string | **RESPOSTA ÚNICA E HUMANIZADA** para copiar |
| `priority_score` | number | 0-100, quanto maior mais urgente |
| `requires_response` | boolean | Se precisa de resposta |

## Layout Sugerido

### Estrutura em Accordion
```
🎬 Canal: [Nome do Canal]
└── 📹 Vídeo: [Título] • [Views] views • [Data]
    └── 💬 Comentários ([Total])
        └── [Lista de comentários com respostas]
```

### Card de Comentário
```
┌─────────────────────────────────────────┐
│ [🟢] @João Silva • ❤️ 45 • há 2 horas   │
│─────────────────────────────────────────│
│ Comentário:                             │
│ "Great video! Keep it up!"              │
│                                         │
│ Resposta Sugerida:                      │
│ "Thanks so much João! More coming 🔥"   │
│                                         │
│ [📋 Copiar Resposta]                    │
└─────────────────────────────────────────┘
```

## Funcionalidades Essenciais

### 1. Botão "Copiar Resposta"
- Copia o texto de `suggested_reply` para a área de transferência
- Mostrar toast de confirmação: "Resposta copiada!"
- Cada resposta é ÚNICA - nunca se repete

### 2. Filtros (Header da Aba)
- Dropdown para selecionar canal específico
- Filtro por sentimento (Todos/Positivos/Negativos/Neutros)
- Checkbox "Apenas que precisam resposta"

### 3. Indicadores Visuais
- 🟢 Comentários positivos (elogios)
- 🟡 Comentários neutros (perguntas)
- 🔴 Comentários negativos (críticas)
- ⭐ Comentários com alto engajamento (>100 likes)

### 4. Ordenação
- Por padrão: Priority Score (maior primeiro)
- Opções: Data, Likes, Sentimento

## Componente React Exemplo

```tsx
import React, { useState, useEffect } from 'react';
import { Card, Button, Badge, Accordion, toast } from '@/components/ui';

export function CommentsTab() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchComments();
  }, []);

  const fetchComments = async () => {
    try {
      const response = await fetch('/api/comments/management');
      const result = await response.json();
      setData(result);
    } catch (error) {
      toast.error('Erro ao carregar comentários');
    } finally {
      setLoading(false);
    }
  };

  const copyResponse = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Resposta copiada!');
  };

  if (loading) return <div>Carregando comentários...</div>;

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold">
          Gestão de Comentários - Canais Monetizados
        </h2>
        <Badge variant="secondary">
          {data?.total_comments || 0} comentários
        </Badge>
      </div>

      <Accordion type="single" collapsible>
        {data?.canais?.map((canal) => (
          <AccordionItem key={canal.id} value={`canal-${canal.id}`}>
            <AccordionTrigger>
              <div className="flex justify-between w-full">
                <span>🎬 {canal.nome}</span>
                <span className="text-sm text-muted">
                  {canal.total_videos} vídeos
                </span>
              </div>
            </AccordionTrigger>
            <AccordionContent>
              {canal.videos.map((video) => (
                <div key={video.id} className="mb-4">
                  <h4 className="font-medium mb-2">
                    📹 {video.titulo}
                  </h4>
                  <div className="space-y-3">
                    {video.comments.map((comment) => (
                      <Card key={comment.comment_id} className="p-4">
                        <div className="flex justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span>{comment.sentiment_indicator}</span>
                            <span className="font-medium">
                              @{comment.author_name}
                            </span>
                            <span className="text-sm text-muted">
                              ❤️ {comment.like_count}
                            </span>
                          </div>
                        </div>

                        <div className="mb-3">
                          <p className="text-sm mb-1 text-muted">Comentário:</p>
                          <p className="italic">{comment.comment_text_pt || comment.comment_text_original}</p>
                        </div>

                        <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded">
                          <p className="text-sm mb-1 font-medium">Resposta Sugerida:</p>
                          <p className="mb-2">{comment.suggested_reply}</p>
                          <Button
                            size="sm"
                            onClick={() => copyResponse(comment.suggested_reply)}
                          >
                            📋 Copiar Resposta
                          </Button>
                        </div>
                      </Card>
                    ))}
                  </div>
                </div>
              ))}
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>
    </div>
  );
}
```

## Notas Importantes

### Unicidade das Respostas
- **CRÍTICO:** Cada resposta retornada pelo endpoint é ÚNICA
- O sistema garante variação em:
  - Estrutura da frase
  - Emojis utilizados
  - Pontuação
  - Comprimento
  - Tom (formal/informal)

### Performance
- Endpoint reseta cache de respostas a cada requisição
- Limite de 10 comentários por vídeo para resposta rápida
- Máximo de 5 vídeos por canal

### Mobile Responsiveness
- Cards devem ser 100% width em mobile
- Botões touch-friendly (min 44px altura)
- Texto legível sem zoom

## Próximos Passos

1. Implementar componente `CommentsTab.tsx`
2. Adicionar rota na seção Ferramentas
3. Adicionar item no menu de navegação
4. Testar com dados reais
5. Adicionar loading states e error handling

## Suporte
Em caso de dúvidas sobre a integração, verificar:
- Endpoint funcionando: `GET /api/comments/management`
- Console para erros de CORS ou autenticação
- Respostas sempre únicas (nunca repetidas)
## Otimizar Performance da Aba Comentarios

### Problemas Identificados

1. **Abertura da aba bloqueada**: Linhas 396-402 mostram um spinner global que bloqueia TODA a renderizacao ate ambas as queries (`comments-summary` + `monetized-channels-comments`) terminarem
2. **Prefetch incompleto**: O `prefetchComments` no sidebar so carrega `comments-summary` e `monetized-channels-comments`, mas nao esta sendo chamado no botao "Comentarios" dentro de Ferramentas (ja esta, mas o staleTime de 1h pode estar expirado)
3. **Modal de videos sem skeleton**: Ao clicar "Ver Comentarios", o modal abre e mostra spinner ate a API responder
4. **Modal de comentarios sem skeleton**: Mesmo problema ao abrir um video
5. **Codigo morto**: `collectMutation` (linhas 171-188) e import `RefreshCw` ainda existem, adicionando peso ao bundle
6. **Re-renders desnecessarios**: Constantes `SUBNICHE_ORDER`, `LAST_SUBNICHE` e `normalizeStr` definidas dentro do componente, recriadas a cada render

### Solucao em 4 Partes

**Parte 1 - Renderizacao progressiva (eliminar bloqueio)**

- Remover o `if (loadingSummary || loadingChannels) return spinner` (linhas 396-402)
- Cards de resumo: mostrar skeletons individuais enquanto `summary` carrega
- Lista de canais: mostrar skeleton groups enquanto `channels` carrega
- Resultado: a tela aparece imediato com placeholders

**Parte 2 - Skeletons nos modais**

- Modal de videos: substituir o `Loader2` (linha 564-567) por skeleton cards com thumbnail placeholder + linhas de texto
- Modal de comentarios: substituir o `Loader2` (linha 677-680) por skeleton cards imitando layout de comentario

**Parte 3 - Prefetch mais agressivo nos modais**

- Ao abrir o modal de videos de um canal, fazer prefetch dos comentarios dos 3 primeiros videos (os mais recentes) para que ao clicar num video, os comentarios ja estejam em cache
- Usar `onSuccess` da query de videos para disparar prefetch dos primeiros videos

**Parte 4 - Limpeza e micro-otimizacoes**

- Remover `collectMutation` e import `RefreshCw` (codigo morto)
- Mover `SUBNICHE_ORDER`, `LAST_SUBNICHE` e `normalizeStr` para fora do componente (constantes estaticas)
- Adicionar `DialogDescription` nos modais para eliminar os warnings de acessibilidade do console

### Detalhes Tecnicos

**CommentsTab.tsx - Renderizacao progressiva dos cards:**

```typescript
// ANTES: bloqueio total
if (loadingSummary || loadingChannels) return <Loader2 />

// DEPOIS: cada secao independente
<div className="grid grid-cols-3 gap-3">
  {loadingSummary ? (
    <>
      <Skeleton className="h-20 rounded-lg" />
      <Skeleton className="h-20 rounded-lg" />
      <Skeleton className="h-20 rounded-lg" />
    </>
  ) : (
    // cards reais
  )}
</div>

// Lista de canais
{loadingChannels ? (
  Array.from({ length: 4 }).map((_, i) => (
    <SkeletonSubnichoCard key={i} />
  ))
) : (
  // collapsibles reais
)}
```

**CommentsTab.tsx - Prefetch de comentarios ao carregar videos:**

```typescript
const { data: videos } = useQuery({
  queryKey: ['channel-videos-comments', selectedChannel?.id],
  queryFn: () => apiService.getVideosWithComments(selectedChannel!.id),
  enabled: !!selectedChannel,
  // ...
});

// Prefetch dos primeiros 3 videos quando a lista carrega
useEffect(() => {
  if (videos && videos.length > 0) {
    videos.slice(0, 3).forEach(video => {
      queryClient.prefetchQuery({
        queryKey: ['video-comments', video.video_id, 1],
        queryFn: () => apiService.getCommentsPaginated(video.video_id, 1),
        staleTime: 1000 * 60 * 30,
      });
    });
  }
}, [videos, queryClient]);
```

**CommentsTab.tsx - Skeleton para modal de videos:**

```typescript
// Em vez de Loader2 spinner
{loadingVideos && !videos ? (
  <div className="space-y-2 pr-4">
    {Array.from({ length: 5 }).map((_, i) => (
      <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-card/50">
        <Skeleton className="w-24 h-16 rounded flex-shrink-0" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-3 w-1/2" />
        </div>
      </div>
    ))}
  </div>
) : ( ... )}
```

### Arquivos Modificados

- `src/components/comments/CommentsTab.tsx` - todas as otimizacoes acima  
  
  

  Canais Monetizados na aba comentarios mude para - Nossos Canais
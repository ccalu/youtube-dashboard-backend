# Integração da Nova Aba "Comentários" no Lovable

## 1. Adicionar Nova Aba no Menu

No componente principal do dashboard, adicione a nova aba "Comentários" na seção de Tools:

```tsx
// Em src/pages/Dashboard.tsx ou equivalente
const tabs = [
  // ... outras abas existentes
  { id: 'tools', label: 'Tools', icon: Settings },
  { id: 'comments', label: 'Comentários', icon: MessageSquare }, // NOVA ABA
  // ...
];
```

## 2. Importar e Usar o Componente

### Passo 1: Copiar o componente
Copie o arquivo `CommentsTab.tsx` para `src/components/CommentsTab.tsx`

### Passo 2: Importar no Dashboard
```tsx
import CommentsTab from '@/components/CommentsTab';
```

### Passo 3: Adicionar ao switch de renderização
```tsx
{activeTab === 'comments' && <CommentsTab />}
```

## 3. Atualizar o Backend URL

No arquivo `CommentsTab.tsx`, atualize as chamadas de API para usar a URL do Railway:

```tsx
// Substitua todas as ocorrências de '/api' por sua URL do Railway
const API_URL = 'https://youtube-dashboard-backend-production.up.railway.app/api';

// Exemplo:
const response = await fetch(`${API_URL}/comentarios/resumo`);
```

## 4. Endpoints Disponíveis

### GET /api/comentarios/resumo
Retorna estatísticas gerais dos comentários

### GET /api/comentarios/monetizados
Lista canais monetizados com contagem de comentários

### GET /api/canais/{id}/videos-com-comentarios
Lista vídeos de um canal com contagem de comentários

### GET /api/videos/{video_id}/comentarios-paginados?page=1
Busca comentários paginados de um vídeo

### PATCH /api/comentarios/{id}/marcar-respondido
Marca um comentário como respondido

## 5. Funcionalidades Implementadas

✅ Cards de resumo com estatísticas
✅ Lista de canais monetizados
✅ Modal de vídeos ao clicar em um canal
✅ Modal de comentários ao clicar em um vídeo
✅ Paginação de comentários (10 por página)
✅ Botão de copiar resposta sugerida
✅ Marcar comentário como respondido
✅ Indicação visual de comentários respondidos (fundo verde)
✅ Exibição de traduções quando disponíveis
✅ Contadores de likes e data de publicação

## 6. Estilos e Responsividade

O componente foi desenvolvido com:
- Tailwind CSS para estilização
- Design mobile-first responsivo
- Modais adaptativos para diferentes tamanhos de tela
- Ícones do Lucide React

## 7. Estados e Carregamento

O componente gerencia:
- Loading states durante requisições
- Mensagens quando não há dados
- Feedback visual ao copiar texto
- Atualização automática após marcar como respondido

## 8. Fluxo de Navegação

1. **Tela Principal:** Lista de canais monetizados
2. **Clique no Canal:** Abre modal com vídeos do canal
3. **Clique no Vídeo:** Abre modal com comentários paginados
4. **Ações no Comentário:**
   - Copiar resposta sugerida
   - Marcar como respondido
5. **Fechar Modal:** Botão X ou clicar fora

## 9. Teste Local

Para testar antes do deploy:

1. Adicione o componente ao Lovable
2. Configure a URL do backend
3. Verifique se os endpoints estão funcionando
4. Teste a navegação entre canais → vídeos → comentários
5. Teste copiar resposta e marcar como respondido

## 10. Deploy

Após integrar e testar:

1. Commit das mudanças no Lovable
2. O deploy é automático
3. Verifique em produção

## Observações Importantes

- Os endpoints só retornam dados de canais com subnicho "Monetizados"
- Comentários já respondidos aparecem com fundo verde
- A paginação mostra 10 comentários por página
- As respostas são geradas automaticamente pelo sistema backend
- O botão "Marcar como Respondido" atualiza o banco em tempo real
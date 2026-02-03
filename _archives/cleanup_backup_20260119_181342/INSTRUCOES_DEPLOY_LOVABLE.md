# 📋 INSTRUÇÕES PARA ADICIONAR O MODAL ANALYTICS NO LOVABLE

## PASSO 1: Adicionar o novo componente

1. **Crie um novo arquivo:** `components/ModalAnalytics.tsx`
2. **Cole o código do arquivo:** `frontend-code/ModalAnalytics.tsx` (589 linhas)

## PASSO 2: Modificar a tabela de canais

### No arquivo onde está a tabela "Nossos Canais", adicione:

#### 1. Importe os componentes necessários:
```tsx
import { ChartBar } from 'lucide-react';
import { ModalAnalytics } from './ModalAnalytics';
```

#### 2. Adicione os estados:
```tsx
const [analyticsModalOpen, setAnalyticsModalOpen] = useState(false);
const [selectedCanalId, setSelectedCanalId] = useState<number | null>(null);
```

#### 3. Adicione os handlers:
```tsx
const handleOpenAnalytics = (canalId: number) => {
  setSelectedCanalId(canalId);
  setAnalyticsModalOpen(true);
};

const handleCloseAnalytics = () => {
  setAnalyticsModalOpen(false);
  setSelectedCanalId(null);
};
```

#### 4. Na célula de ações da tabela, adicione o novo ícone APÓS o ícone ExternalLink:
```tsx
<Button
  variant="ghost"
  size="icon"
  onClick={() => handleOpenAnalytics(canal.id)}
  title="Ver Analytics"
>
  <ChartBar className="h-4 w-4" />
</Button>
```

**Ordem dos ícones:**
1. ExternalLink (Acessar canal) - já existe
2. **ChartBar (Ver Analytics)** - NOVO
3. Edit (Editar) - já existe
4. Trash2 (Excluir) - já existe

#### 5. No final do componente, antes do fechamento, adicione o modal:
```tsx
{/* Modal de Analytics */}
{selectedCanalId && (
  <ModalAnalytics
    canalId={selectedCanalId}
    isOpen={analyticsModalOpen}
    onClose={handleCloseAnalytics}
  />
)}
```

## PASSO 3: Verificar as dependências

O modal usa os seguintes componentes do shadcn/ui:
- Dialog
- Tabs
- Card
- Badge
- Skeleton
- ScrollArea
- Alert
- Button

Se algum não estiver instalado no Lovable, será necessário adicionar.

## PASSO 4: Testar

1. Navegue até a aba "Nossos Canais"
2. Clique no ícone ChartBar de qualquer canal
3. O modal deve abrir com loading
4. Dados devem carregar do endpoint `/api/canais/{canal_id}/analytics`
5. Teste todas as 5 tabs
6. Teste responsividade (mobile/desktop)

## 📝 OBSERVAÇÕES IMPORTANTES:

1. **URL da API:** O modal usa `import.meta.env.VITE_API_URL` - certifique-se que está configurado
2. **Responsividade:** O modal é 100% responsivo - teste em diferentes tamanhos
3. **Performance:** O modal carrega todos os dados de uma vez - pode demorar 1-2 segundos para canais grandes
4. **Emojis:** Usamos emojis dentro do modal para melhor visualização

## ✅ CHECKLIST DE VALIDAÇÃO:

- [ ] Migration aplicada no Supabase com sucesso
- [ ] Componente ModalAnalytics.tsx criado
- [ ] Ícone ChartBar adicionado na tabela
- [ ] Estados e handlers configurados
- [ ] Modal renderizando no final do componente
- [ ] Endpoint respondendo corretamente
- [ ] Todas as 5 tabs funcionando
- [ ] Responsividade mobile testada
- [ ] Sem erros no console

## 🚀 RESULTADO ESPERADO:

Ao clicar no ícone de analytics (ChartBar):
1. Modal abre com skeleton loading
2. Faz request para `/api/canais/{canal_id}/analytics`
3. Mostra dados organizados em 5 tabs:
   - Visão Geral
   - Métricas
   - Top Vídeos
   - Padrões
   - Diagnóstico
4. 100% responsivo
5. Visual consistente com o dashboard

## 🆘 SUPORTE:

Se encontrar algum problema:
1. Verifique o console do navegador para erros
2. Confirme que a migration foi aplicada no Supabase
3. Teste o endpoint direto: `{API_URL}/api/canais/1/analytics`
4. Verifique se o backend no Railway está atualizado
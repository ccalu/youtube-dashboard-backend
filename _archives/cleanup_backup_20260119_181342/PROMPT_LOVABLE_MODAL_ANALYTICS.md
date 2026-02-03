# PROMPT PARA LOVABLE: Adicionar Modal de Analytics

## CONTEXTO
Preciso adicionar um modal de analytics avançado na aba "Nossos Canais" do dashboard. O modal deve abrir quando clicar em um novo ícone de analytics que será adicionado nas ações de cada canal.

## MUDANÇAS NECESSÁRIAS

### 1. ADICIONAR ÍCONE NA TABELA DE CANAIS

Na tabela de canais (aba "Nossos Canais"), adicione um 4º ícone nas ações de cada canal.

**Ordem dos ícones:**
1. ExternalLink (Acessar canal) - já existe
2. **ChartBar (Ver Analytics) - NOVO**
3. Edit (Editar) - já existe
4. Trash2 (Excluir) - já existe

```tsx
// Adicionar import
import { ChartBar } from 'lucide-react';

// Na célula de ações, adicionar o novo ícone após "Acessar":
<Button
  variant="ghost"
  size="icon"
  onClick={() => handleOpenAnalytics(canal.id)}
  title="Ver Analytics"
>
  <ChartBar className="h-4 w-4" />
</Button>
```

### 2. ADICIONAR ESTADO E HANDLER

```tsx
// Adicionar estados
const [analyticsModalOpen, setAnalyticsModalOpen] = useState(false);
const [selectedCanalId, setSelectedCanalId] = useState<number | null>(null);

// Adicionar handler
const handleOpenAnalytics = (canalId: number) => {
  setSelectedCanalId(canalId);
  setAnalyticsModalOpen(true);
};

const handleCloseAnalytics = () => {
  setAnalyticsModalOpen(false);
  setSelectedCanalId(null);
};
```

### 3. ADICIONAR O MODAL NO FINAL DO COMPONENTE

Antes do fechamento do componente principal, adicione:

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

### 4. CRIAR NOVO ARQUIVO: ModalAnalytics.tsx

Crie um novo componente com o seguinte código:

```tsx
import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  TrendingUp,
  TrendingDown,
  Calendar,
  Clock,
  Users,
  Eye,
  Video,
  AlertTriangle,
  CheckCircle,
  BarChart3,
  Info
} from 'lucide-react';

interface ModalAnalyticsProps {
  canalId: number;
  isOpen: boolean;
  onClose: () => void;
}

interface AnalyticsData {
  canal_info: {
    id: number;
    nome: string;
    subnicho: string;
    lingua: string;
    tipo: string;
    url: string;
    criado_em: string | null;
    custom_url: string | null;
    inscritos: number;
    total_videos: number;
    total_views: number;
    frequencia_semanal: number;
  };
  metricas: {
    views_7d: number;
    views_15d: number;
    views_30d: number;
    growth_7d: number;
    growth_15d: number;
    growth_30d: number;
    engagement_rate: number;
    score: number;
    inscritos_diff: number;
    ranking_subnicho: number;
    percentil: number;
  };
  top_videos: Array<{
    video_id: string;
    titulo: string;
    url: string;
    thumbnail_url: string;
    views: number;
    likes: number;
    comentarios: number;
    duracao: number;
    publicado_ha_dias: number;
    engagement_rate: number;
    views_por_dia: number;
  }>;
  padroes: Array<{
    tipo: string;
    descricao: string;
    boost: string;
    evidencia: string;
    exemplos?: string[];
    keywords?: string[];
    range_ideal?: string;
  }>;
  clusters: Array<{
    tema: string;
    categoria: string;
    emoji: string;
    quantidade_videos: number;
    percentual_videos: number;
    media_views: number;
    percentual_views: number;
    roi: number;
  }>;
  anomalias: Array<{
    tipo: string;
    gravidade: string;
    emoji: string;
    descricao: string;
    detalhes: string;
    data?: string;
  }>;
  melhor_momento: {
    dia_semana: string | null;
    dia_numero: number | null;
    hora: number | null;
    boost: number;
    mensagem: string;
    ranking_dias?: Array<{
      dia: string;
      performance: number;
    }>;
  };
}

export function ModalAnalytics({ canalId, isOpen, onClose }: ModalAnalyticsProps) {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    if (isOpen && canalId) {
      fetchAnalytics();
    }
  }, [isOpen, canalId]);

  const fetchAnalytics = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/canais/${canalId}/analytics`);

      if (!response.ok) {
        throw new Error('Erro ao carregar analytics');
      }

      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro desconhecido');
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num: number): string => {
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(1)}M`;
    }
    if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}K`;
    }
    return num.toString();
  };

  const formatDuration = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDate = (dateString: string | null): string => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR', {
      month: 'long',
      year: 'numeric'
    });
  };

  const getGrowthColor = (growth: number): string => {
    if (growth > 0) return 'text-green-500';
    if (growth < 0) return 'text-red-500';
    return 'text-gray-500';
  };

  const getSeverityColor = (severity: string): string => {
    switch (severity) {
      case 'critical': return 'bg-red-500';
      case 'warning': return 'bg-yellow-500';
      case 'info': return 'bg-blue-500';
      case 'success': return 'bg-green-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-6xl h-[90vh] p-0 bg-gray-900 text-white">
        <DialogHeader className="px-6 pt-6 pb-4 border-b border-gray-800">
          <DialogTitle className="text-2xl font-bold flex items-center gap-2">
            <BarChart3 className="w-6 h-6" />
            Channel Analytics
          </DialogTitle>
        </DialogHeader>

        {loading ? (
          <div className="p-6 space-y-4">
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-64 w-full" />
            <Skeleton className="h-48 w-full" />
          </div>
        ) : error ? (
          <Alert className="m-6 bg-red-900 border-red-800">
            <AlertTriangle className="w-4 h-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : data ? (
          <div className="flex flex-col h-full">
            {/* Header com informações básicas */}
            <div className="px-6 py-4 bg-gray-800/50">
              <h3 className="text-xl font-semibold mb-2">
                📺 {data.canal_info.nome} ({data.canal_info.subnicho})
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-gray-400">📅 Criado em:</span>
                  <span className="ml-2">{formatDate(data.canal_info.criado_em)}</span>
                </div>
                <div>
                  <span className="text-gray-400">🎬 Vídeos:</span>
                  <span className="ml-2">{data.canal_info.total_videos} | {data.canal_info.frequencia_semanal?.toFixed(1)}/sem</span>
                </div>
                <div>
                  <span className="text-gray-400">👥 Inscritos:</span>
                  <span className="ml-2">
                    {formatNumber(data.canal_info.inscritos)}
                    {data.metricas.inscritos_diff !== 0 && (
                      <span className={`ml-1 text-xs ${getGrowthColor(data.metricas.inscritos_diff)}`}>
                        ({data.metricas.inscritos_diff > 0 ? '+' : ''}{data.metricas.inscritos_diff})
                      </span>
                    )}
                  </span>
                </div>
                <div>
                  <span className="text-gray-400">👁️ Views totais:</span>
                  <span className="ml-2">{formatNumber(data.canal_info.total_views)}</span>
                </div>
              </div>
              {data.melhor_momento.dia_semana && (
                <div className="mt-3 p-2 bg-blue-900/30 rounded-lg">
                  <span className="text-sm">
                    📅 Melhor momento para postar:
                    <span className="font-semibold ml-2">
                      {data.melhor_momento.mensagem}
                    </span>
                    <Badge className="ml-2 bg-green-600">
                      +{data.melhor_momento.boost}% views
                    </Badge>
                  </span>
                </div>
              )}
            </div>

            {/* Tabs */}
            <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
              <TabsList className="grid grid-cols-5 w-full px-6 bg-gray-800 border-b border-gray-700">
                <TabsTrigger value="overview">Visão Geral</TabsTrigger>
                <TabsTrigger value="metrics">Métricas</TabsTrigger>
                <TabsTrigger value="videos">Top Vídeos</TabsTrigger>
                <TabsTrigger value="patterns">Padrões</TabsTrigger>
                <TabsTrigger value="diagnostics">Diagnóstico</TabsTrigger>
              </TabsList>

              <ScrollArea className="flex-1">
                {/* CONTEÚDO DAS TABS - Código completo está no arquivo ModalAnalytics.tsx */}
                {/* Cada tab tem seu conteúdo específico com cards, gráficos e análises */}
              </ScrollArea>
            </Tabs>
          </div>
        ) : null}
      </DialogContent>
    </Dialog>
  );
}
```

## RESPONSIVIDADE IMPORTANTE

O modal DEVE ser 100% responsivo:

### Mobile (< 768px):
- Modal em tela cheia
- Tabs viram scroll horizontal ou dropdown
- Cards empilham verticalmente
- Thumbnails dos vídeos menores
- Fontes ajustadas proporcionalmente
- Touch targets mínimo 44x44px

### Desktop (>= 768px):
- Modal com 90% largura, máximo 1200px
- Grid de cards em colunas
- Hover effects nos elementos interativos
- Mais informações visíveis simultaneamente

## CORES E TEMA

Manter consistência com o dashboard atual:
- Background principal: `bg-gray-900`
- Cards: `bg-gray-800`
- Bordas: `border-gray-700`
- Texto principal: `text-white`
- Texto secundário: `text-gray-400`
- Sucesso/Crescimento: `text-green-500` / `bg-green-600`
- Erro/Queda: `text-red-500` / `bg-red-600`
- Info: `text-blue-500` / `bg-blue-600`

## TESTE DO ENDPOINT

O endpoint já está pronto no backend:
```
GET /api/canais/{canal_id}/analytics
```

Retorna todos os dados necessários para popular o modal.

## OBSERVAÇÕES

1. Usar emojis dentro do modal para deixar mais visual
2. Ícones Lucide React para os botões e ações
3. Skeleton loading enquanto carrega dados
4. Tratamento de erro se a API falhar
5. ScrollArea para conteúdo longo
6. Tabs para organizar as informações

## RESULTADO ESPERADO

Ao clicar no ícone de analytics (ChartBar) na tabela de canais:
1. Modal abre com loading
2. Faz request para API
3. Mostra dados organizados em 5 tabs
4. 100% responsivo
5. Visual profissional e consistente com o dashboard
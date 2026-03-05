// src/components/AnalysisTab.tsx
import { useQuery } from '@tanstack/react-query';
import { apiService } from '@/services/api';
import { SubnicheTrendsCard } from './SubnicheTrendsCard';
// import { KeywordsRanking } from './KeywordsRanking';
import { TitlePatternsCarousel } from './TitlePatternsCarousel';
import { TopChannelsCarousel } from './TopChannelsCarousel';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle } from 'lucide-react';
import type { SubnichesResponse } from '@/types/analysis';

export function AnalysisTab() {
  // ⚡ OTIMIZAÇÃO: Carregamento paralelo - não bloqueia renderização dos componentes
  const { data: subnichesData, isLoading, error } = useQuery<SubnichesResponse>({
    queryKey: ['subniches'],
    queryFn: () => apiService.getSubniches(),
    staleTime: 30 * 60 * 1000, // 30 minutos - dados mudam pouco
    gcTime: 60 * 60 * 1000, // 1 hora de cache
  });

  const subniches = subnichesData?.subniches || [];

  // ⚡ OTIMIZAÇÃO: Renderiza componentes imediatamente para carregamento paralelo
  // Mesmo durante loading, os componentes são renderizados e fazem suas próprias chamadas
  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Erro ao carregar dados de análise. Tente recarregar a página.
        </AlertDescription>
      </Alert>
    );
  }

  if (!isLoading && subniches.length === 0) {
    return (
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Nenhum subniche encontrado. Adicione canais primeiro para ver análises.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* ⚡ Card de Tendências - Novo */}
      <SubnicheTrendsCard />
      
      {/* ⚡ OTIMIZAÇÃO: Componentes renderizam imediatamente com subniches (mesmo vazio durante loading) */}
      {/* Cada componente tem seu próprio skeleton e carrega em paralelo */}
      <TopChannelsCarousel subniches={subniches} />
      <TitlePatternsCarousel subniches={subniches} />
      {/* <KeywordsRanking subniches={subniches} /> */}
    </div>
  );
}

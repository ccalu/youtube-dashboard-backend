import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useToast } from '@/hooks/use-toast';
import { 
  financeiroApi, 
  PeriodoFinanceiro, 
  Lancamento,
  Categoria,
  Meta,
} from '@/services/financeiroApi';
import { FinanceiroFiltroPeriodo } from './FinanceiroFiltroPeriodo';
import { FinanceiroOverviewCards } from './FinanceiroOverviewCards';
import { FinanceiroGraficoReceitaDespesas } from './FinanceiroGraficoReceitaDespesas';
import { FinanceiroDespesasCard } from './FinanceiroDespesasCard';
import { FinanceiroMetas } from './FinanceiroMetas';
import { FinanceiroProjecaoCard } from './FinanceiroProjecaoCard';
import { FinanceiroComparacaoCard } from './FinanceiroComparacaoCard';

export function FinanceiroTab() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  
  const [periodo, setPeriodo] = useState<PeriodoFinanceiro>('30d');

  // Queries
  const { data: overview, isLoading: isLoadingOverview } = useQuery({
    queryKey: ['financeiro-overview', periodo],
    queryFn: () => financeiroApi.getOverview(periodo),
  });

  const { data: graficoData, isLoading: isLoadingGrafico } = useQuery({
    queryKey: ['financeiro-grafico', periodo],
    queryFn: () => financeiroApi.getGraficoReceitaDespesas(periodo),
  });

  const { data: breakdownData, isLoading: isLoadingBreakdown } = useQuery({
    queryKey: ['financeiro-breakdown', periodo],
    queryFn: () => financeiroApi.getBreakdownDespesas(periodo),
  });

  const { data: lancamentosData, isLoading: isLoadingLancamentos } = useQuery({
    queryKey: ['financeiro-lancamentos', periodo],
    queryFn: () => financeiroApi.getLancamentos({ periodo }),
  });

  const { data: categoriasData, isLoading: isLoadingCategorias } = useQuery({
    queryKey: ['financeiro-categorias'],
    queryFn: () => financeiroApi.getCategorias(),
  });

  const { data: metasData, isLoading: isLoadingMetas } = useQuery({
    queryKey: ['financeiro-metas', periodo],
    queryFn: () => financeiroApi.getMetas(periodo),
  });

  // NEW V3: Projeção do Mês
  const { data: projecaoData, isLoading: isLoadingProjecao } = useQuery({
    queryKey: ['financeiro-projecao'],
    queryFn: () => financeiroApi.getProjecaoMes(),
  });

  // Taxa de Câmbio
  const { data: taxaCambioData } = useQuery({
    queryKey: ['financeiro-taxa-cambio'],
    queryFn: () => financeiroApi.getTaxaCambio(),
    staleTime: 5 * 60 * 1000, // 5 min
  });

  // NEW V3: Comparação Mensal
  const { data: comparacaoData, isLoading: isLoadingComparacao } = useQuery({
    queryKey: ['financeiro-comparacao'],
    queryFn: () => financeiroApi.getComparacaoMensal(6),
  });

  // Filter only despesas from lancamentos
  const despesasLancamentos = lancamentosData?.lancamentos?.filter(l => l.tipo === 'despesa') || [];

  // Mutations - Lançamentos
  const createLancamentoMutation = useMutation({
    mutationFn: financeiroApi.createLancamento,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['financeiro-lancamentos'] });
      queryClient.invalidateQueries({ queryKey: ['financeiro-overview'] });
      queryClient.invalidateQueries({ queryKey: ['financeiro-grafico'] });
      queryClient.invalidateQueries({ queryKey: ['financeiro-breakdown'] });
      queryClient.invalidateQueries({ queryKey: ['financeiro-projecao'] });
      queryClient.invalidateQueries({ queryKey: ['financeiro-comparacao'] });
      toast({ title: 'Despesa criada com sucesso!' });
    },
    onError: () => {
      toast({ title: 'Erro ao criar despesa', variant: 'destructive' });
    },
  });

  const updateLancamentoMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Lancamento> }) => 
      financeiroApi.updateLancamento(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['financeiro-lancamentos'] });
      queryClient.invalidateQueries({ queryKey: ['financeiro-overview'] });
      queryClient.invalidateQueries({ queryKey: ['financeiro-grafico'] });
      queryClient.invalidateQueries({ queryKey: ['financeiro-breakdown'] });
      toast({ title: 'Despesa atualizada com sucesso!' });
    },
    onError: () => {
      toast({ title: 'Erro ao atualizar despesa', variant: 'destructive' });
    },
  });

  const deleteLancamentoMutation = useMutation({
    mutationFn: financeiroApi.deleteLancamento,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['financeiro-lancamentos'] });
      queryClient.invalidateQueries({ queryKey: ['financeiro-overview'] });
      queryClient.invalidateQueries({ queryKey: ['financeiro-grafico'] });
      queryClient.invalidateQueries({ queryKey: ['financeiro-breakdown'] });
      toast({ title: 'Despesa excluída com sucesso!' });
    },
    onError: () => {
      toast({ title: 'Erro ao excluir despesa', variant: 'destructive' });
    },
  });

  // Mutations - Categorias
  const createCategoriaMutation = useMutation({
    mutationFn: financeiroApi.createCategoria,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['financeiro-categorias'] });
      toast({ title: 'Categoria criada com sucesso!' });
    },
    onError: () => {
      toast({ title: 'Erro ao criar categoria', variant: 'destructive' });
    },
  });

  // Mutations - Metas
  const createMetaMutation = useMutation({
    mutationFn: financeiroApi.createMeta,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['financeiro-metas'] });
      toast({ title: 'Meta criada com sucesso!' });
    },
    onError: () => {
      toast({ title: 'Erro ao criar meta', variant: 'destructive' });
    },
  });

  const updateMetaMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Meta> }) => 
      financeiroApi.updateMeta(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['financeiro-metas'] });
      toast({ title: 'Meta atualizada com sucesso!' });
    },
    onError: () => {
      toast({ title: 'Erro ao atualizar meta', variant: 'destructive' });
    },
  });

  const deleteMetaMutation = useMutation({
    mutationFn: financeiroApi.deleteMeta,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['financeiro-metas'] });
      toast({ title: 'Meta excluída com sucesso!' });
    },
    onError: () => {
      toast({ title: 'Erro ao excluir meta', variant: 'destructive' });
    },
  });

  return (
    <div className="space-y-6">
      {/* Header with 💲 Financeiro + [📅] [⚖️] [📁] */}
      <FinanceiroFiltroPeriodo 
        periodo={periodo} 
        onPeriodoChange={setPeriodo} 
      />

      {/* Overview Cards (4 cards uniformes) */}
      <FinanceiroOverviewCards 
        data={overview || null} 
        isLoading={isLoadingOverview} 
      />

      {/* Row 1: Metas (33%) + Projeção (33%) + Comparação (33%) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <FinanceiroMetas
          metas={metasData?.metas || []}
          isLoading={isLoadingMetas}
          onSave={async (data) => { await createMetaMutation.mutateAsync(data); }}
          onUpdate={async (id, data) => { await updateMetaMutation.mutateAsync({ id, data }); }}
          onDelete={async (id) => { await deleteMetaMutation.mutateAsync(id); }}
        />
        
        <FinanceiroProjecaoCard
          data={projecaoData || null}
          isLoading={isLoadingProjecao}
          taxaCambio={taxaCambioData?.taxa}
        />
        
        <FinanceiroComparacaoCard
          data={comparacaoData || null}
          isLoading={isLoadingComparacao}
        />
      </div>

      {/* Row 2: Gráfico (50%) + Despesas (50%) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <FinanceiroGraficoReceitaDespesas 
          data={graficoData || []} 
          isLoading={isLoadingGrafico} 
        />
        
        <FinanceiroDespesasCard
          despesas={despesasLancamentos}
          breakdown={breakdownData?.por_categoria || []}
          categorias={categoriasData?.categorias || []}
          isLoading={isLoadingBreakdown || isLoadingLancamentos || isLoadingCategorias}
          onAddDespesa={async (data) => { await createLancamentoMutation.mutateAsync(data); }}
          onEditDespesa={async (id, data) => { await updateLancamentoMutation.mutateAsync({ id, data }); }}
          onDeleteDespesa={async (id) => { await deleteLancamentoMutation.mutateAsync(id); }}
          onCreateCategoria={async (data) => { await createCategoriaMutation.mutateAsync(data); }}
        />
      </div>
    </div>
  );
}

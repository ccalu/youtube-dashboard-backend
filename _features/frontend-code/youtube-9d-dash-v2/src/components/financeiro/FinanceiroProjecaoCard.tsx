import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { ProjecaoMes } from '@/services/financeiroApi';
import { TrendingUp, Calendar, Calculator, Target } from 'lucide-react';

interface FinanceiroProjecaoCardProps {
  data: ProjecaoMes | null;
  isLoading: boolean;
  taxaCambio?: number;
}

const formatCurrency = (value: number, currency: 'BRL' | 'USD' = 'BRL') => {
  return new Intl.NumberFormat(currency === 'BRL' ? 'pt-BR' : 'en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
  }).format(value);
};

const getProgressColor = (percent: number) => {
  if (percent >= 70) return { bg: 'bg-green-500', border: 'border-green-500' };
  if (percent >= 31) return { bg: 'bg-orange-500', border: 'border-orange-500' };
  return { bg: 'bg-red-500', border: 'border-red-500' };
};

export function FinanceiroProjecaoCard({ data, isLoading, taxaCambio }: FinanceiroProjecaoCardProps) {
  if (isLoading) {
    return (
      <Card className="bg-card border-border/50 h-full">
        <CardHeader className="pb-2">
          <Skeleton className="h-5 w-32" />
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <Skeleton className="h-14 w-full" />
            <div className="grid grid-cols-2 gap-2">
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </div>
            <Skeleton className="h-14 w-full" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data) {
    return (
      <Card className="bg-card border-border/50 h-full">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <TrendingUp className="h-4 w-4 text-green-500" />
            Projeção do Mês
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-6 text-muted-foreground text-sm">
            Carregando projeção...
          </div>
        </CardContent>
      </Card>
    );
  }

  const progressPercent = Math.round((data.dias_decorridos / data.dias_total) * 100);
  const progressColors = getProgressColor(progressPercent);
  const effectiveTaxaCambio = taxaCambio || data.taxa_cambio;

  return (
    <Card className="bg-card border-border/50 h-full">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-base">
            <TrendingUp className="h-4 w-4 text-green-500" />
            Projeção do Mês
          </CardTitle>
          <span className="text-xs text-muted-foreground font-medium">
            {data.mes_nome}
          </span>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Grid com Média Diária e Progresso - Em cima */}
        <div className="grid grid-cols-2 gap-2">
          <div className="bg-gradient-to-r from-purple-500/15 to-purple-600/15 border border-purple-500/25 rounded-lg p-2.5">
            <div className="flex items-center gap-1.5 mb-0.5">
              <Calculator className="h-3 w-3 text-purple-400" />
              <span className="text-[10px] text-purple-300">Média Diária</span>
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-bold text-white">
                {formatCurrency(data.media_diaria)}
              </span>
              {effectiveTaxaCambio && (
                <span className="text-[10px] text-purple-300/80">
                  ({formatCurrency(data.media_diaria / effectiveTaxaCambio, 'USD')})
                </span>
              )}
            </div>
          </div>
          <div className="bg-gradient-to-r from-amber-500/15 to-amber-600/15 border border-amber-500/25 rounded-lg p-2.5">
            <div className="flex items-center gap-1.5 mb-0.5">
              <Calendar className="h-3 w-3 text-amber-400" />
              <span className="text-[10px] text-amber-300">Progresso</span>
            </div>
            <span className="text-sm font-bold text-white">
              {data.dias_decorridos}/{data.dias_total}
            </span>
            <span className="text-[10px] text-muted-foreground ml-1">
              ({data.dias_restantes} dias rest.)
            </span>
          </div>
        </div>

        {/* Total Até Hoje - Abaixo */}
        <div className="bg-gradient-to-r from-blue-500/15 to-blue-600/15 border border-blue-500/25 rounded-lg p-3">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-xs text-blue-300 font-medium">💵 TOTAL ATÉ HOJE</span>
            <span className="text-lg font-bold text-white">
              {formatCurrency(data.total_ate_hoje)}
            </span>
          </div>
          {/* Progress bar with dynamic color */}
          <div className="w-full h-2 bg-muted/30 rounded-full overflow-hidden">
            <div 
              className={`h-full ${progressColors.bg} transition-all duration-300`}
              style={{ width: `${progressPercent}%` }}
            />
          </div>
          <div className="text-[10px] text-muted-foreground text-right mt-1">
            {progressPercent}% do mês
          </div>
        </div>

        {/* Projeção Fim do Mês - Compacto */}
        <div className="bg-gradient-to-r from-green-500/20 to-emerald-600/20 border border-green-500/30 rounded-lg p-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <Target className="h-4 w-4 text-green-400" />
              <span className="text-xs font-semibold text-green-300 uppercase">
                Projeção Fim do Mês
              </span>
            </div>
            <span className="text-xl font-bold text-green-400">
              {formatCurrency(data.projecao_mes)}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

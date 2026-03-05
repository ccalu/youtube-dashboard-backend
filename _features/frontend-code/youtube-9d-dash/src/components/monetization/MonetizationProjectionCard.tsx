import React from 'react';
import { Card } from '@/components/ui/card';
import { TrendingUp, TrendingDown, Calendar } from 'lucide-react';

interface ProjectionCardProps {
  data: {
    projection_monthly: {
      value: number;
      growth_vs_last_month: number;
    };
    comparison_period?: {
      current_period_revenue: number;
      previous_period_revenue: number;
      growth_pct: number;
      period_days: number;
    };
    comparison_7d?: {
      current_period_revenue: number;
      previous_period_revenue: number;
      growth_pct: number;
    };
  };
  loading: boolean;
  period?: string;
  periodLabel?: string;
}

const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value || 0);
};

export const MonetizationProjectionCard: React.FC<ProjectionCardProps> = ({
  data,
  loading,
  period = '7d',
  periodLabel,
}) => {
  if (loading) {
    return (
      <Card className="p-4 border-0">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-muted rounded w-40" />
          <div className="h-20 bg-muted rounded" />
          <div className="h-16 bg-muted rounded" />
        </div>
      </Card>
    );
  }

  // Use comparison_period se disponível, senão fallback para comparison_7d
  const comparison = data.comparison_period || data.comparison_7d || {
    current_period_revenue: 0,
    previous_period_revenue: 0,
    growth_pct: 0,
  };

  const isPositiveGrowth = comparison.growth_pct >= 0;

  // Gera label dinâmico baseado no período
  const getComparisonTitle = () => {
    if (periodLabel) return `Comparação ${periodLabel}`;
    if (data.comparison_period?.period_days) {
      return `Comparação ${data.comparison_period.period_days} dias`;
    }
    switch (period) {
      case '24h': return 'Comparação 24 horas';
      case '3d': return 'Comparação 3 dias';
      case '7d': return 'Comparação 7 dias';
      case '15d': return 'Comparação 15 dias';
      case '30d': return 'Comparação 30 dias';
      case 'total': return 'Comparação Total';
      case 'month': return `Comparação ${periodLabel || 'do mês'}`;
      default: return 'Comparação';
    }
  };

  return (
    <Card className="p-3 sm:p-4 border-0">
      <div className="space-y-3 sm:space-y-4">
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 sm:w-5 sm:h-5 text-primary" />
          <h3 className="text-base sm:text-lg font-semibold">Projeção & Performance</h3>
        </div>

        <div className="space-y-2">
          <h4 className="text-xs sm:text-sm font-medium text-white">{getComparisonTitle()}</h4>
          <div className={`p-2 border rounded-lg ${isPositiveGrowth ? 'bg-green-500/10 border-green-500/20' : 'bg-red-500/10 border-red-500/20'}`}>
            <div className="flex items-center justify-between gap-2">
              <div className="min-w-0">
                <p className="text-[10px] sm:text-xs text-white/80">Atual</p>
                <p className={`text-sm sm:text-base font-bold truncate ${isPositiveGrowth ? 'text-green-600' : 'text-red-600'}`}>
                  {formatCurrency(comparison.current_period_revenue)}
                </p>
              </div>
              <div className="text-center flex-shrink-0">
                {isPositiveGrowth ? (
                  <TrendingUp className="w-4 h-4 sm:w-5 sm:h-5 text-green-600 mx-auto" />
                ) : (
                  <TrendingDown className="w-4 h-4 sm:w-5 sm:h-5 text-red-600 mx-auto" />
                )}
                <span
                  className={`text-xs sm:text-sm font-bold ${
                    isPositiveGrowth ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {isPositiveGrowth ? '+' : ''}
                  {comparison.growth_pct.toFixed(1)}%
                </span>
              </div>
              <div className="text-right min-w-0">
                <p className="text-[10px] sm:text-xs text-white/80">Anterior</p>
                <p className="text-sm sm:text-base font-bold text-red-600 truncate">
                  {formatCurrency(comparison.previous_period_revenue)}
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-2">
          <h4 className="text-xs sm:text-sm font-medium text-white">
            Projeção Mensal <span className="font-normal text-muted-foreground">({new Date().toLocaleDateString('pt-BR', { month: 'long' }).charAt(0).toUpperCase() + new Date().toLocaleDateString('pt-BR', { month: 'long' }).slice(1)})</span>
          </h4>
          <div className="p-2 sm:p-3 border rounded-lg bg-green-500/10 border-green-500/20">
            <div className="flex items-center justify-between gap-1 sm:gap-2">
              <p className="text-lg sm:text-2xl font-bold text-green-600">
                {formatCurrency(data.projection_monthly.value)}
              </p>
              {data.projection_monthly.growth_vs_last_month >= 0 ? (
                <TrendingUp className="w-4 h-4 sm:w-5 sm:h-5 text-green-600" />
              ) : (
                <TrendingDown className="w-4 h-4 sm:w-5 sm:h-5 text-red-600" />
              )}
              <span
                className={`text-xs sm:text-sm font-medium ${
                  data.projection_monthly.growth_vs_last_month >= 0
                    ? 'text-green-600'
                    : 'text-red-600'
                }`}
              >
                {data.projection_monthly.growth_vs_last_month >= 0 ? '+' : ''}
                {data.projection_monthly.growth_vs_last_month.toFixed(1)}% vs {(() => {
                  const now = new Date();
                  const lastMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1);
                  return lastMonth.toLocaleDateString('pt-BR', { month: 'short' }).replace('.', '');
                })()}
              </span>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
};

import React from 'react';
import { Card } from '@/components/ui/card';
import { TrendingUp, TrendingDown, BarChart3 } from 'lucide-react';

interface BestWorstDayCardProps {
  data: {
    best_day: {
      date: string;
      revenue: number;
    };
    worst_day: {
      date: string;
      revenue: number;
    };
  };
  loading: boolean;
  period: string;
  month: string | null;
}

const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value || 0);
};

const formatDate = (dateString: string): string => {
  if (!dateString || dateString === "N/A") return "N/A";
  try {
    const date = new Date(dateString + 'T12:00:00');
    return date.toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  } catch {
    return dateString;
  }
};

const getPeriodLabel = (period: string, month: string | null): string => {
  if (month) {
    const [year, monthNum] = month.split('-');
    const monthNames = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
    return `${monthNames[parseInt(monthNum) - 1]} ${year}`;
  }
  const labels: Record<string, string> = {
    '24h': '24 horas',
    '3d': '3 dias',
    '7d': '7 dias',
    '15d': '15 dias',
    '30d': '30 dias',
    'total': 'Total',
  };
  return labels[period] || period;
};

export const MonetizationBestWorstDayCard: React.FC<BestWorstDayCardProps> = ({
  data,
  loading,
  period,
  month,
}) => {
  if (loading) {
    return (
      <Card className="p-4 border-0">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-muted rounded w-48" />
          <div className="h-16 bg-muted rounded" />
          <div className="h-16 bg-muted rounded" />
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-3 sm:p-4 border-0">
      <div className="space-y-3 sm:space-y-4">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-4 h-4 sm:w-5 sm:h-5 text-primary" />
          <h3 className="text-base sm:text-lg font-semibold">
            Melhor/Pior Dia <span className="text-xs sm:text-sm font-normal text-muted-foreground">({getPeriodLabel(period, month)})</span>
          </h3>
        </div>

        <div className="grid grid-cols-2 gap-2 sm:gap-3">
          <div className="p-2 border border-green-500/20 bg-green-500/5 rounded-lg flex items-center justify-between">
            <div className="min-w-0">
              <div className="flex items-center gap-1">
                <TrendingUp className="w-3 h-3 sm:w-4 sm:h-4 text-green-600 flex-shrink-0" />
                <span className="text-xs sm:text-sm text-green-600 font-semibold">Melhor</span>
              </div>
              <span className="text-[10px] sm:text-xs text-white/80">{formatDate(data.best_day.date)}</span>
            </div>
            <p className="text-sm sm:text-base font-bold text-green-600 flex-shrink-0 ml-2">
              {formatCurrency(data.best_day.revenue)}
            </p>
          </div>

          <div className="p-2 border border-red-500/20 bg-red-500/5 rounded-lg flex items-center justify-between">
            <div className="min-w-0">
              <div className="flex items-center gap-1">
                <TrendingDown className="w-3 h-3 sm:w-4 sm:h-4 text-red-600 flex-shrink-0" />
                <span className="text-xs sm:text-sm text-red-600 font-semibold">Pior</span>
              </div>
              <span className="text-[10px] sm:text-xs text-white/80">{formatDate(data.worst_day.date)}</span>
            </div>
            <p className="text-sm sm:text-base font-bold text-red-600 flex-shrink-0 ml-2">
              {formatCurrency(data.worst_day.revenue)}
            </p>
          </div>
        </div>
      </div>
    </Card>
  );
};

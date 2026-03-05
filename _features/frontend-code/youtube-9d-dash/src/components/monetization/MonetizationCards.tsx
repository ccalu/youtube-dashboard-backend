import React from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown, DollarSign, BarChart3, Clock } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Revenue24hData {
  real: {
    date_formatted: string;
    revenue: number;
    badge: 'real' | 'estimate';
  };
  estimate: {
    date_formatted: string;
    revenue: number;
    badge: 'real' | 'estimate';
  };
}

interface MonetizationCardsProps {
  data: {
    total_monetized_channels: number;
    daily_avg: {
      revenue: number;
      growth_rate: number;
      trend: string;
    };
    rpm_avg: number;
    total_revenue: number;
  };
  revenue24h: Revenue24hData | null;
  loading?: boolean;
  period: string;
  month: string | null;
  typeFilter: 'real_estimate' | 'real_only';
}

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  trend?: {
    value: number;
    label: string;
  };
  colorClass?: string;
  iconBgClass?: string;
}

const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  trend,
  colorClass = 'text-primary',
  iconBgClass,
}) => {
  const isPositiveTrend = trend && trend.value >= 0;

  return (
    <Card className="p-3 border-0 hover:shadow-lg transition-shadow">
      <div className="flex items-center justify-between gap-3">
        <div className="space-y-1 flex-1">
          <p className="text-xs font-medium text-muted-foreground">{title}</p>
          <p className={cn('text-2xl font-bold', colorClass)}>{value}</p>
          {subtitle && (
            <p className="text-xs text-muted-foreground">{subtitle}</p>
          )}
          {trend && (
            <div className="flex items-center gap-1 text-xs">
              {isPositiveTrend ? (
                <TrendingUp className="w-3 h-3 text-green-500" />
              ) : (
                <TrendingDown className="w-3 h-3 text-red-500" />
              )}
              <span
                className={cn(
                  'font-semibold',
                  isPositiveTrend ? 'text-green-600' : 'text-red-600'
                )}
              >
                {isPositiveTrend ? '+' : ''}
                {trend.value.toFixed(1)}%
              </span>
              <span className="text-muted-foreground text-xs">{trend.label}</span>
            </div>
          )}
        </div>
        <div
          className={cn(
            'p-2 rounded-xl shadow-sm',
            iconBgClass || (
              colorClass === 'text-green-600' ? 'bg-gradient-to-br from-green-500/20 to-green-500/5' :
              colorClass === 'text-blue-600' ? 'bg-gradient-to-br from-blue-500/20 to-blue-500/5' :
              colorClass === 'text-purple-600' ? 'bg-gradient-to-br from-purple-500/20 to-purple-500/5' :
              colorClass === 'text-yellow-600' ? 'bg-gradient-to-br from-yellow-500/20 to-yellow-500/5' :
              'bg-gradient-to-br from-primary/20 to-primary/5'
            )
          )}
        >
          {icon}
        </div>
      </div>
    </Card>
  );
};

const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value || 0);
};

const getPeriodLabel = (period: string, month: string | null): string => {
  if (month) {
    const [year, monthNum] = month.split('-');
    const monthNames = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
    return `${monthNames[parseInt(monthNum) - 1]} ${year}`;
  }
  const labels: Record<string, string> = {
    '24h': 'vs 24h atrás',
    '3d': 'vs 3d atrás',
    '7d': 'vs 7d atrás',
    '15d': 'vs 15d atrás',
    '30d': 'vs 30d atrás',
    'total': 'vs período anterior',
  };
  return labels[period] || 'vs anterior';
};

export const MonetizationCards: React.FC<MonetizationCardsProps> = ({
  data,
  revenue24h,
  loading = false,
  period,
  month,
  typeFilter,
}) => {
  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i} className="p-4 border-0 animate-pulse">
            <div className="space-y-3">
              <div className="h-4 bg-muted rounded w-24" />
              <div className="h-8 bg-muted rounded w-32" />
              <div className="h-3 bg-muted rounded w-20" />
            </div>
          </Card>
        ))}
      </div>
    );
  }

  // Select revenue 24h data based on typeFilter
  const revenue24hDisplay = revenue24h 
    ? (typeFilter === 'real_only' ? revenue24h.real : revenue24h.estimate)
    : null;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
      {/* Revenue 24h Card */}
      <Card className="p-3 border-0 hover:shadow-lg transition-shadow">
        <div className="flex items-center justify-between gap-3">
          <div className="space-y-1 flex-1">
            <p className="text-xs font-medium text-muted-foreground">Revenue 24h</p>
            {revenue24hDisplay ? (
              <>
                <p className="text-2xl font-bold text-green-600">
                  {formatCurrency(revenue24hDisplay.revenue)}
                </p>
                <div className="flex items-center gap-2">
                  <Badge
                    variant={revenue24hDisplay.badge === 'real' ? 'default' : 'secondary'}
                    className={cn(
                      'text-[10px] px-1.5 py-0',
                      revenue24hDisplay.badge === 'real' 
                        ? 'bg-green-600 text-white' 
                        : 'bg-yellow-500 text-black'
                    )}
                  >
                    {revenue24hDisplay.badge === 'real' ? 'Real' : 'Estimado'}
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    {revenue24hDisplay.date_formatted}
                  </span>
                </div>
              </>
            ) : (
              <p className="text-lg text-muted-foreground">-</p>
            )}
          </div>
          <div className="p-2 rounded-xl shadow-sm bg-gradient-to-br from-blue-500/20 to-blue-500/5">
            <Clock className="w-5 h-5 text-blue-600" />
          </div>
        </div>
      </Card>

      <StatCard
        title="RPM Médio"
        value={formatCurrency(data.rpm_avg)}
        subtitle="por 1K views"
        icon={<BarChart3 className="w-5 h-5 text-yellow-500" />}
        colorClass="text-green-600"
        iconBgClass="bg-gradient-to-br from-yellow-500/20 to-yellow-500/5"
      />

      <StatCard
        title="Média Diária"
        value={formatCurrency(data.daily_avg.revenue)}
        icon={<TrendingUp className="w-5 h-5 text-green-600" />}
        trend={{
          value: data.daily_avg.growth_rate,
          label: getPeriodLabel(period, month),
        }}
        colorClass="text-green-600"
      />

      <StatCard
        title="Total Revenue"
        value={formatCurrency(data.total_revenue)}
        subtitle={month ? getPeriodLabel(period, month) : "período selecionado"}
        icon={<DollarSign className="w-5 h-5 text-green-600" />}
        colorClass="text-green-600"
      />
    </div>
  );
};
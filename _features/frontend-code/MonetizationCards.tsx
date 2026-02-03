import React from 'react';
import { Card } from '@/components/ui/card';
import { TrendingUp, TrendingDown, DollarSign, BarChart3, Users, Zap } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * MONETIZATION CARDS - 4 Cards Superiores
 *
 * Cards:
 * 1. Canais Monetizados (total_monetized_channels)
 * 2. Média Diária + Taxa de Crescimento (daily_avg + growth_rate)
 * 3. RPM Médio (rpm_avg)
 * 4. Total Revenue (total_revenue)
 */

interface MonetizationCardsProps {
  data: {
    total_monetized_channels: number;
    daily_avg: {
      views: number;
      revenue: number;
      rpm: number;
    };
    growth_rate: number;
    rpm_avg: number;
    total_revenue: number;
  };
  loading?: boolean;
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
}

const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  trend,
  colorClass = 'text-primary',
}) => {
  const isPositiveTrend = trend && trend.value >= 0;

  return (
    <Card className="p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between">
        <div className="space-y-2 flex-1">
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <p className={cn('text-3xl font-bold', colorClass)}>{value}</p>
          {subtitle && (
            <p className="text-xs text-muted-foreground">{subtitle}</p>
          )}
          {trend && (
            <div className="flex items-center gap-1 text-sm">
              {isPositiveTrend ? (
                <TrendingUp className="w-4 h-4 text-green-500" />
              ) : (
                <TrendingDown className="w-4 h-4 text-red-500" />
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
            'p-3 rounded-lg',
            colorClass === 'text-green-600' && 'bg-green-500/10',
            colorClass === 'text-blue-600' && 'bg-blue-500/10',
            colorClass === 'text-purple-600' && 'bg-purple-500/10',
            colorClass === 'text-yellow-600' && 'bg-yellow-500/10',
            colorClass === 'text-primary' && 'bg-primary/10'
          )}
        >
          {icon}
        </div>
      </div>
    </Card>
  );
};

const formatNumber = (num: number): string => {
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`;
  }
  if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`;
  }
  return num.toLocaleString('pt-BR');
};

const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
};

export const MonetizationCards: React.FC<MonetizationCardsProps> = ({
  data,
  loading = false,
}) => {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i} className="p-6 animate-pulse">
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

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Card 1: Canais Monetizados */}
      <StatCard
        title="Canais Monetizados"
        value={data.total_monetized_channels}
        subtitle="canais ativos"
        icon={<Users className="w-6 h-6 text-blue-600" />}
        colorClass="text-blue-600"
      />

      {/* Card 2: Média Diária + Taxa de Crescimento */}
      <StatCard
        title="Média Diária"
        value={formatCurrency(data.daily_avg.revenue)}
        subtitle={`${formatNumber(data.daily_avg.views)} views · RPM ${formatCurrency(
          data.daily_avg.rpm
        )}`}
        icon={<BarChart3 className="w-6 h-6 text-green-600" />}
        trend={{
          value: data.growth_rate,
          label: 'vs período anterior',
        }}
        colorClass="text-green-600"
      />

      {/* Card 3: RPM Médio */}
      <StatCard
        title="RPM Médio"
        value={formatCurrency(data.rpm_avg)}
        subtitle="revenue por 1.000 views"
        icon={<Zap className="w-6 h-6 text-yellow-600" />}
        colorClass="text-yellow-600"
      />

      {/* Card 4: Total Revenue */}
      <StatCard
        title="Total Revenue"
        value={formatCurrency(data.total_revenue)}
        subtitle="período selecionado"
        icon={<DollarSign className="w-6 h-6 text-purple-600" />}
        colorClass="text-purple-600"
      />
    </div>
  );
};

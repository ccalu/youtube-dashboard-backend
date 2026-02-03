import React from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { TrendingUp, TrendingDown, Calendar, Eye, Clock } from 'lucide-react';

/**
 * ANALYTICS CARD - Card de Analytics
 *
 * Features:
 * - Projeções 7d/15d/30d
 * - Melhores/Piores dias (revenue)
 * - Retention e CTR médios
 * - Análise por dia da semana
 */

interface AnalyticsCardProps {
  data: {
    projections: {
      days_7: number;
      days_15: number;
      days_30: number;
    };
    best_day: {
      date: string;
      revenue: number;
    };
    worst_day: {
      date: string;
      revenue: number;
    };
    avg_retention_pct: number | null;
    avg_ctr: number | null;
    day_of_week_analysis: Array<{
      day_name: string;
      avg_revenue: number;
    }>;
  };
  loading: boolean;
}

const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
};

const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
  });
};

const DAY_NAMES_PT: { [key: string]: string } = {
  Monday: 'Segunda',
  Tuesday: 'Terça',
  Wednesday: 'Quarta',
  Thursday: 'Quinta',
  Friday: 'Sexta',
  Saturday: 'Sábado',
  Sunday: 'Domingo',
};

export const AnalyticsCard: React.FC<AnalyticsCardProps> = ({
  data,
  loading,
}) => {
  if (loading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-muted rounded w-32" />
          <div className="h-24 bg-muted rounded" />
          <div className="h-32 bg-muted rounded" />
        </div>
      </Card>
    );
  }

  // Prepare chart data
  const chartData = data.day_of_week_analysis.map((item) => ({
    day: DAY_NAMES_PT[item.day_name] || item.day_name,
    revenue: item.avg_revenue,
  }));

  // Find best day color
  const maxRevenue = Math.max(...chartData.map((d) => d.revenue));

  return (
    <Card className="p-6">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center gap-2">
          <Calendar className="w-5 h-5 text-primary" />
          <h3 className="text-lg font-semibold">Analytics</h3>
        </div>

        {/* Projections */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-muted-foreground">
            Projeções de Revenue
          </h4>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm">Próximos 7 dias</span>
              <span className="text-sm font-semibold text-blue-600">
                {formatCurrency(data.projections.days_7)}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Próximos 15 dias</span>
              <span className="text-sm font-semibold text-blue-600">
                {formatCurrency(data.projections.days_15)}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Próximos 30 dias</span>
              <span className="text-sm font-semibold text-blue-600">
                {formatCurrency(data.projections.days_30)}
              </span>
            </div>
          </div>
        </div>

        {/* Best/Worst Days */}
        <div className="grid grid-cols-2 gap-3">
          {/* Best Day */}
          <div className="p-3 border border-green-500/20 bg-green-500/5 rounded-lg">
            <div className="flex items-center gap-1 mb-2">
              <TrendingUp className="w-3 h-3 text-green-600" />
              <span className="text-xs text-green-600 font-medium">
                Melhor Dia
              </span>
            </div>
            <p className="text-xs text-muted-foreground mb-1">
              {formatDate(data.best_day.date)}
            </p>
            <p className="text-lg font-bold text-green-600">
              {formatCurrency(data.best_day.revenue)}
            </p>
          </div>

          {/* Worst Day */}
          <div className="p-3 border border-red-500/20 bg-red-500/5 rounded-lg">
            <div className="flex items-center gap-1 mb-2">
              <TrendingDown className="w-3 h-3 text-red-600" />
              <span className="text-xs text-red-600 font-medium">
                Pior Dia
              </span>
            </div>
            <p className="text-xs text-muted-foreground mb-1">
              {formatDate(data.worst_day.date)}
            </p>
            <p className="text-lg font-bold text-red-600">
              {formatCurrency(data.worst_day.revenue)}
            </p>
          </div>
        </div>

        {/* Retention & CTR */}
        {(data.avg_retention_pct !== null || data.avg_ctr !== null) && (
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-muted-foreground">
              Métricas de Engajamento
            </h4>

            {data.avg_retention_pct !== null && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Eye className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm">Retenção Média</span>
                  </div>
                  <span className="text-sm font-semibold">
                    {data.avg_retention_pct.toFixed(1)}%
                  </span>
                </div>
                <Progress value={data.avg_retention_pct} className="h-2" />
              </div>
            )}

            {data.avg_ctr !== null && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm">CTR Médio</span>
                  </div>
                  <span className="text-sm font-semibold">
                    {data.avg_ctr.toFixed(1)}%
                  </span>
                </div>
                <Progress value={data.avg_ctr} className="h-2" />
              </div>
            )}
          </div>
        )}

        {/* Day of Week Analysis */}
        {chartData.length > 0 && (
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-muted-foreground">
              Revenue por Dia da Semana
            </h4>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="day"
                  tick={{ fontSize: 11 }}
                  angle={-45}
                  textAnchor="end"
                  height={60}
                />
                <YAxis tick={{ fontSize: 11 }} tickFormatter={(value) => `$${value}`} />
                <Tooltip
                  formatter={(value: any) => [formatCurrency(value), 'Revenue Médio']}
                  contentStyle={{
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    border: 'none',
                    borderRadius: '8px',
                    color: '#fff',
                  }}
                />
                <Bar
                  dataKey="revenue"
                  fill="#22c55e"
                  radius={[4, 4, 0, 0]}
                  opacity={0.8}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </Card>
  );
};

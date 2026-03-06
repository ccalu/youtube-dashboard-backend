import React, { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Trophy, Zap, DollarSign } from 'lucide-react';
import { cn } from '@/lib/utils';

interface TopPerformersCardProps {
  data: {
    top_rpm: Array<{
      channel_id: string;
      channel_name: string;
      avg_rpm: number;
      total_revenue: number;
    }>;
    top_revenue: Array<{
      channel_id: string;
      channel_name: string;
      total_revenue: number;
      avg_rpm: number;
    }>;
  };
  loading: boolean;
  period: string;
  month: string | null;
}

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

const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value || 0);
};

const MEDALS = ['🥇', '🥈', '🥉'];
const COLORS = [
  'bg-yellow-500/30 border-yellow-500/50',
  'bg-gray-400/30 border-gray-400/50',
  'bg-orange-500/30 border-orange-500/50',
];

interface PerformerItemProps {
  rank: number;
  channelName: string;
  value: number;
  label: string;
}

const PerformerItem: React.FC<PerformerItemProps> = ({
  rank,
  channelName,
  value,
  label,
}) => {
  const isFirst = rank === 0;

  return (
    <div
      className={cn(
        'p-2 border-2 rounded-lg transition-all hover:scale-105',
        COLORS[rank],
        isFirst && 'ring-2 ring-yellow-500/50 shadow-lg'
      )}
    >
      <div className="flex items-center gap-2">
        <div className="text-xl">{MEDALS[rank]}</div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1">
            <h4
              className={cn(
                'font-semibold truncate text-foreground text-sm'
              )}
            >
              {channelName}
            </h4>
            {isFirst && <span className="text-sm">🔥</span>}
          </div>
        </div>

        <div className="text-right">
          <span className={cn('font-bold text-foreground', isFirst ? 'text-base' : 'text-sm')}>
            {formatCurrency(value || 0)}
          </span>
        </div>
      </div>
    </div>
  );
};

export const MonetizationTopPerformersCard: React.FC<TopPerformersCardProps> = ({
  data,
  loading,
  period,
  month,
}) => {
  const [activeTab, setActiveTab] = useState<'rpm' | 'revenue'>('revenue');

  if (loading) {
    return (
      <Card className="p-6 border-0">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-muted rounded w-32" />
          <div className="h-20 bg-muted rounded" />
          <div className="h-20 bg-muted rounded" />
          <div className="h-20 bg-muted rounded" />
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-3 sm:p-4 border-0">
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <Trophy className="w-4 h-4 sm:w-5 sm:h-5 text-yellow-600" />
          <h3 className="text-base sm:text-lg font-semibold">
            Top Performers <span className="text-xs sm:text-sm font-normal text-muted-foreground">({getPeriodLabel(period, month)})</span>
          </h3>
        </div>

        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'rpm' | 'revenue')}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="revenue" className="text-xs">
              <DollarSign className="w-3 h-3 mr-1" />
              Por Revenue
            </TabsTrigger>
            <TabsTrigger value="rpm" className="text-xs">
              <Zap className="w-3 h-3 mr-1" />
              Por RPM
            </TabsTrigger>
          </TabsList>

          <TabsContent value="rpm" className="space-y-2 mt-3">
            {data.top_rpm.slice(0, 3).map((channel, index) => (
              <PerformerItem
                key={channel.channel_id}
                rank={index}
                channelName={channel.channel_name}
                value={channel.avg_rpm || 0}
                label="RPM"
              />
            ))}

            {data.top_rpm.length === 0 && (
              <div className="text-center py-8 text-muted-foreground text-sm">
                Sem dados disponíveis para o período selecionado
              </div>
            )}
          </TabsContent>

          <TabsContent value="revenue" className="space-y-2 mt-3">
            {data.top_revenue.slice(0, 3).map((channel, index) => (
              <PerformerItem
                key={channel.channel_id}
                rank={index}
                channelName={channel.channel_name}
                value={channel.total_revenue || 0}
                label="Revenue"
              />
            ))}

            {data.top_revenue.length === 0 && (
              <div className="text-center py-8 text-muted-foreground text-sm">
                Sem dados disponíveis para o período selecionado
              </div>
            )}
          </TabsContent>
        </Tabs>

      </div>
    </Card>
  );
};
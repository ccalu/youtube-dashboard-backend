import React, { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Trophy, Zap, DollarSign } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * TOP PERFORMERS CARD - Top 3 Canais
 *
 * Features:
 * - Top 3 por RPM (podium style 🥇🥈🥉)
 * - Top 3 por Revenue
 * - Tabs para alternar entre os dois
 * - Visual destacado para #1
 */

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
}

const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
};

const MEDALS = ['🥇', '🥈', '🥉'];
const COLORS = [
  'bg-yellow-500/10 border-yellow-500/30 text-yellow-700',
  'bg-gray-400/10 border-gray-400/30 text-gray-700',
  'bg-orange-500/10 border-orange-500/30 text-orange-700',
];

interface PerformerItemProps {
  rank: number;
  channelName: string;
  primaryValue: number;
  primaryLabel: string;
  secondaryValue: number;
  secondaryLabel: string;
}

const PerformerItem: React.FC<PerformerItemProps> = ({
  rank,
  channelName,
  primaryValue,
  primaryLabel,
  secondaryValue,
  secondaryLabel,
}) => {
  const isFirst = rank === 0;

  return (
    <div
      className={cn(
        'p-4 border-2 rounded-lg transition-all hover:scale-105',
        COLORS[rank],
        isFirst && 'ring-2 ring-yellow-500/50 shadow-lg'
      )}
    >
      <div className="flex items-start gap-3">
        {/* Medal */}
        <div className="text-3xl">{MEDALS[rank]}</div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Channel Name */}
          <div className="flex items-center gap-2 mb-2">
            <h4
              className={cn(
                'font-semibold truncate',
                isFirst ? 'text-base' : 'text-sm'
              )}
            >
              {channelName}
            </h4>
            {isFirst && (
              <Badge variant="outline" className="text-xs bg-yellow-500/20">
                TOP 1
              </Badge>
            )}
          </div>

          {/* Primary Value */}
          <div className="mb-1">
            <span
              className={cn(
                'font-bold',
                isFirst ? 'text-xl' : 'text-lg'
              )}
            >
              {formatCurrency(primaryValue)}
            </span>
            <span className="text-xs text-muted-foreground ml-2">
              {primaryLabel}
            </span>
          </div>

          {/* Secondary Value */}
          <div className="text-xs text-muted-foreground">
            {formatCurrency(secondaryValue)} {secondaryLabel}
          </div>
        </div>
      </div>
    </div>
  );
};

export const TopPerformersCard: React.FC<TopPerformersCardProps> = ({
  data,
  loading,
}) => {
  const [activeTab, setActiveTab] = useState<'rpm' | 'revenue'>('rpm');

  if (loading) {
    return (
      <Card className="p-6">
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
    <Card className="p-6">
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center gap-2">
          <Trophy className="w-5 h-5 text-yellow-600" />
          <h3 className="text-lg font-semibold">Top Performers</h3>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'rpm' | 'revenue')}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="rpm" className="text-xs">
              <Zap className="w-3 h-3 mr-1" />
              Por RPM
            </TabsTrigger>
            <TabsTrigger value="revenue" className="text-xs">
              <DollarSign className="w-3 h-3 mr-1" />
              Por Revenue
            </TabsTrigger>
          </TabsList>

          {/* Top 3 RPM */}
          <TabsContent value="rpm" className="space-y-3 mt-4">
            {data.top_rpm.slice(0, 3).map((channel, index) => (
              <PerformerItem
                key={channel.channel_id}
                rank={index}
                channelName={channel.channel_name}
                primaryValue={channel.avg_rpm}
                primaryLabel="RPM médio"
                secondaryValue={channel.total_revenue}
                secondaryLabel="revenue total"
              />
            ))}

            {data.top_rpm.length === 0 && (
              <div className="text-center py-8 text-muted-foreground text-sm">
                Sem dados disponíveis para o período selecionado
              </div>
            )}
          </TabsContent>

          {/* Top 3 Revenue */}
          <TabsContent value="revenue" className="space-y-3 mt-4">
            {data.top_revenue.slice(0, 3).map((channel, index) => (
              <PerformerItem
                key={channel.channel_id}
                rank={index}
                channelName={channel.channel_name}
                primaryValue={channel.total_revenue}
                primaryLabel="revenue total"
                secondaryValue={channel.avg_rpm}
                secondaryLabel="RPM médio"
              />
            ))}

            {data.top_revenue.length === 0 && (
              <div className="text-center py-8 text-muted-foreground text-sm">
                Sem dados disponíveis para o período selecionado
              </div>
            )}
          </TabsContent>
        </Tabs>

        {/* Fun Fact */}
        {data.top_rpm.length > 0 && data.top_revenue.length > 0 && (
          <div className="pt-4 border-t">
            <p className="text-xs text-muted-foreground text-center">
              {data.top_rpm[0].channel_id === data.top_revenue[0].channel_id ? (
                <>
                  <span className="font-semibold text-yellow-600">
                    {data.top_rpm[0].channel_name}
                  </span>{' '}
                  lidera em RPM e Revenue! 🏆
                </>
              ) : (
                <>
                  Maior RPM:{' '}
                  <span className="font-semibold">
                    {data.top_rpm[0].channel_name}
                  </span>{' '}
                  • Maior Revenue:{' '}
                  <span className="font-semibold">
                    {data.top_revenue[0].channel_name}
                  </span>
                </>
              )}
            </p>
          </div>
        )}
      </div>
    </Card>
  );
};

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card } from '@/components/ui/card';
import { MonetizationCards } from './MonetizationCards';
import { MonetizationChannelsList } from './MonetizationChannelsList';
import { MonetizationFilterBar } from './MonetizationFilterBar';
import { TrophyModalButton, TargetModalButton } from './MonetizationModals';
import { AdvancedAnalyticsButton } from './AdvancedAnalyticsModal';
import { Loader2 } from 'lucide-react';

interface FilterState {
  period: '24h' | '3d' | '7d' | '15d' | '30d' | 'total' | 'custom';
  language: 'all' | 'pt' | 'es' | 'en' | 'de' | 'fr';
  subnicho: string | null;
  typeFilter: 'real_estimate' | 'real_only';
  month: string | null; // formato: "2024-11"
  customStart?: string | null;
  customEnd?: string | null;
}

interface SummaryData {
  total_monetized_channels: number;
  daily_avg: {
    revenue: number;
    growth_rate: number;
    trend: string;
  };
  rpm_avg: number;
  total_revenue: number;
}

interface ChannelsData {
  subnichos: Array<{
    name: string;
    color: string;
    channels: Array<{
      channel_id: string;
      name: string;
      subnicho?: string;
      language: string;
      period_total: {
        revenue: number;
        views: number;
        rpm: number;
        last_update: string;
        last_update_formatted: string;
        badge: 'real' | 'estimate';
      };
    }>;
  }>;
}

interface AnalyticsData {
  projection_monthly: {
    value: number;
    growth_vs_last_month: number;
  };
  comparison_period: {
    current_period_revenue: number;
    previous_period_revenue: number;
    growth_pct: number;
    period_days: number;
  };
  // Keep backward compatibility with comparison_7d
  comparison_7d?: {
    current_period_revenue: number;
    previous_period_revenue: number;
    growth_pct: number;
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
  avg_view_duration_sec: number | null;
}

interface TopPerformersData {
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
}

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

const API_BASE = 'https://youtube-dashboard-backend-production.up.railway.app';

const fetchMonetizationData = async (filters: FilterState) => {
  const params = new URLSearchParams({
    period: filters.month ? 'total' : filters.period, // Se mês selecionado, usar total
    type_filter: filters.typeFilter,
  });

  if (filters.language !== 'all') {
    params.append('language', filters.language);
  }

  if (filters.subnicho) {
    params.append('subnicho', filters.subnicho);
  }

  if (filters.month) {
    params.append('month', filters.month);
  }

  // Período customizado: adicionar start_date e end_date
  if (filters.period === 'custom' && filters.customStart && filters.customEnd) {
    params.append('start_date', filters.customStart);
    params.append('end_date', filters.customEnd);
  }

  // Add cache buster to ensure fresh data
  params.append('_t', Date.now().toString());

  const [summaryRes, channelsRes, analyticsRes, topPerformersRes, revenue24hRes] = await Promise.all([
    fetch(`${API_BASE}/api/monetization/summary?${params}`),
    fetch(`${API_BASE}/api/monetization/channels?${params}`),
    fetch(`${API_BASE}/api/monetization/analytics?${params}`),
    fetch(`${API_BASE}/api/monetization/top-performers?${params}`),
    fetch(`${API_BASE}/api/monetization/revenue-24h`),
  ]);

  // Summary and channels are required - throw error if they fail
  if (!summaryRes.ok || !channelsRes.ok) {
    throw new Error('Erro ao buscar dados do servidor');
  }

  const [summary, channels] = await Promise.all([
    summaryRes.json(),
    channelsRes.json(),
  ]);

  // Analytics and topPerformers are optional - use defaults if they fail
  let analytics: AnalyticsData | null = null;
  let topPerformers: TopPerformersData | null = null;
  let revenue24h: Revenue24hData | null = null;

  if (analyticsRes.ok) {
    try {
      analytics = await analyticsRes.json();
    } catch (e) {
    }
  }

  if (topPerformersRes.ok) {
    try {
      topPerformers = await topPerformersRes.json();
    } catch (e) {
    }
  }

  if (revenue24hRes.ok) {
    try {
      revenue24h = await revenue24hRes.json();
    } catch (e) {
    }
  }

  return { summary, channels, analytics, topPerformers, revenue24h };
};

export const MonetizationTab: React.FC = () => {
  const [filters, setFilters] = useState<FilterState>({
    period: 'total',
    language: 'all',
    subnicho: null,
    typeFilter: 'real_only',
    month: null,
  });

  // QueryKey inclui todos os filtros para garantir que a query seja refeita quando qualquer filtro muda
  const queryKey = ['monetization-data', {
    period: filters.month ? 'total' : filters.period,
    language: filters.language,
    subnicho: filters.subnicho,
    typeFilter: filters.typeFilter,
    month: filters.month,
    customStart: filters.customStart,
    customEnd: filters.customEnd,
  }];

  const { data, isLoading, error, refetch } = useQuery({
    queryKey,
    queryFn: () => fetchMonetizationData(filters),
    staleTime: 0, // Sempre buscar dados frescos quando filtros mudam
    gcTime: 5 * 60 * 1000,
    refetchOnMount: true,
  });

  const handleFilterChange = (newFilters: Partial<FilterState>) => {
    setFilters((prev) => ({ ...prev, ...newFilters }));
  };

  if (isLoading && !data) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-muted-foreground">Carregando dados de monetização...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-96">
        <Card className="p-6 max-w-md">
          <div className="text-center">
            <p className="text-red-500 font-semibold mb-2">Erro ao carregar dados</p>
            <p className="text-sm text-muted-foreground mb-4">{error instanceof Error ? error.message : 'Erro desconhecido'}</p>
            <button
              onClick={() => refetch()}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
            >
              Tentar Novamente
            </button>
          </div>
        </Card>
      </div>
    );
  }

  const summaryData = data?.summary as SummaryData | undefined;
  const channelsData = data?.channels as ChannelsData | undefined;
  const analyticsData = data?.analytics as AnalyticsData | undefined;
  const topPerformersData = data?.topPerformers as TopPerformersData | undefined;
  const revenue24hData = data?.revenue24h as Revenue24hData | undefined;

  return (
    <div className="space-y-4 sm:space-y-6 pb-8">
      <MonetizationFilterBar
        filters={filters}
        onFilterChange={handleFilterChange}
        loading={isLoading}
      />

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_auto] gap-3">
        {summaryData && (
          <MonetizationCards 
            data={summaryData} 
            revenue24h={revenue24hData || null} 
            loading={isLoading} 
            period={filters.period}
            month={filters.month}
            typeFilter={filters.typeFilter}
          />
        )}
        
        {/* Analytics card with emoji buttons */}
        <Card className="border-0 p-3 hover:shadow-lg transition-shadow bg-emerald-400/25 border border-emerald-500/30">
          <div className="flex flex-col sm:flex-row items-center sm:items-start gap-2 sm:gap-3 h-full">
            <div className="space-y-1 text-center sm:text-left w-full sm:w-auto">
              <p className="text-xs font-medium text-muted-foreground">Analytics</p>
              <div className="flex items-center justify-center sm:justify-start gap-6 sm:gap-4 py-1">
                <TrophyModalButton
                  analyticsData={analyticsData || null}
                  topPerformersData={topPerformersData || null}
                  channelsData={channelsData || null}
                  loading={isLoading}
                  period={filters.period}
                  month={filters.month}
                />
                <TargetModalButton
                  analyticsData={analyticsData || null}
                  loading={isLoading}
                  period={filters.month ? 'month' : filters.period}
                  month={filters.month}
                />
                <AdvancedAnalyticsButton
                  period={filters.period}
                  subnicho={filters.subnicho}
                  lingua={filters.language !== 'all' ? filters.language : null}
                />
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Channels list */}
      {channelsData && (
        <MonetizationChannelsList
          data={channelsData}
          loading={isLoading}
          typeFilter={filters.typeFilter}
          month={filters.month}
          period={filters.period}
        />
      )}

      {isLoading && data && (
        <div className="fixed bottom-4 right-4 bg-background border border-border rounded-lg shadow-lg p-3 flex items-center gap-2">
          <Loader2 className="w-4 h-4 animate-spin text-primary" />
          <span className="text-sm text-muted-foreground">Atualizando...</span>
        </div>
      )}
    </div>
  );
};
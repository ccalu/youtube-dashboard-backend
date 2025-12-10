import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { MonetizationCards } from './MonetizationCards';
import { ChannelsList } from './ChannelsList';
import { AnalyticsCard } from './AnalyticsCard';
import { TopPerformersCard } from './TopPerformersCard';
import { FilterBar } from './FilterBar';
import { Loader2 } from 'lucide-react';

/**
 * MONETIZATION TAB - Container Principal
 *
 * Estrutura:
 * - FilterBar (período, idioma, subnicho, toggle real/estimate)
 * - MonetizationCards (4 cards superiores)
 * - Grid 2 colunas:
 *   - Left: ChannelsList (agrupada por subnicho)
 *   - Right: AnalyticsCard + TopPerformersCard
 *
 * API Base: https://youtube-dashboard-backend-production.up.railway.app
 * Endpoints:
 *   GET /api/monetization/summary
 *   GET /api/monetization/channels
 *   GET /api/monetization/analytics
 *   GET /api/monetization/top-performers
 */

interface FilterState {
  period: '24h' | '3d' | '7d' | '15d' | '30d' | 'total';
  language: 'all' | 'pt' | 'es' | 'en' | 'de' | 'fr';
  subnicho: string | null;
  typeFilter: 'real_estimate' | 'real_only';
}

interface SummaryData {
  total_monetized_channels: number;
  daily_avg: {
    views: number;
    revenue: number;
    rpm: number;
  };
  growth_rate: number;
  rpm_avg: number;
  total_revenue: number;
}

interface ChannelsData {
  [subnicho: string]: Array<{
    channel_id: string;
    channel_name: string;
    subnicho: string;
    language: string;
    last_3_days: Array<{
      date: string;
      views: number;
      revenue: number;
      rpm: number;
      is_estimate: boolean;
    }>;
  }>;
}

interface AnalyticsData {
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
  avg_retention_pct: number;
  avg_ctr: number;
  day_of_week_analysis: Array<{
    day_name: string;
    avg_revenue: number;
  }>;
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

const API_BASE = 'https://youtube-dashboard-backend-production.up.railway.app';

export const MonetizationTab: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [filters, setFilters] = useState<FilterState>({
    period: 'total',
    language: 'all',
    subnicho: null,
    typeFilter: 'real_estimate',
  });

  const [summaryData, setSummaryData] = useState<SummaryData | null>(null);
  const [channelsData, setChannelsData] = useState<ChannelsData | null>(null);
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [topPerformersData, setTopPerformersData] = useState<TopPerformersData | null>(null);

  // Fetch all data when filters change
  useEffect(() => {
    fetchAllData();
  }, [filters]);

  const fetchAllData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Build query params
      const params = new URLSearchParams({
        period: filters.period,
        type_filter: filters.typeFilter,
      });

      if (filters.language !== 'all') {
        params.append('language', filters.language);
      }

      if (filters.subnicho) {
        params.append('subnicho', filters.subnicho);
      }

      // Fetch all endpoints in parallel
      const [summaryRes, channelsRes, analyticsRes, topPerformersRes] = await Promise.all([
        fetch(`${API_BASE}/api/monetization/summary?${params}`),
        fetch(`${API_BASE}/api/monetization/channels?${params}`),
        fetch(`${API_BASE}/api/monetization/analytics?${params}`),
        fetch(`${API_BASE}/api/monetization/top-performers?${params}`),
      ]);

      if (!summaryRes.ok || !channelsRes.ok || !analyticsRes.ok || !topPerformersRes.ok) {
        throw new Error('Erro ao buscar dados do servidor');
      }

      const [summary, channels, analytics, topPerformers] = await Promise.all([
        summaryRes.json(),
        channelsRes.json(),
        analyticsRes.json(),
        topPerformersRes.json(),
      ]);

      setSummaryData(summary);
      setChannelsData(channels);
      setAnalyticsData(analytics);
      setTopPerformersData(topPerformers);
    } catch (err) {
      console.error('Erro ao buscar dados:', err);
      setError(err instanceof Error ? err.message : 'Erro desconhecido');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (newFilters: Partial<FilterState>) => {
    setFilters((prev) => ({ ...prev, ...newFilters }));
  };

  if (loading && !summaryData) {
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
            <p className="text-sm text-muted-foreground mb-4">{error}</p>
            <button
              onClick={fetchAllData}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
            >
              Tentar Novamente
            </button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-8">
      {/* Filter Bar */}
      <FilterBar
        filters={filters}
        onFilterChange={handleFilterChange}
        loading={loading}
      />

      {/* Top Cards (4 cards principais) */}
      {summaryData && (
        <MonetizationCards data={summaryData} loading={loading} />
      )}

      {/* Main Grid: Channels List + Analytics/Top Performers */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Channels List (2/3 width) */}
        <div className="lg:col-span-2">
          {channelsData && (
            <ChannelsList
              data={channelsData}
              loading={loading}
              typeFilter={filters.typeFilter}
            />
          )}
        </div>

        {/* Right Column: Analytics + Top Performers (1/3 width) */}
        <div className="space-y-6">
          {analyticsData && (
            <AnalyticsCard data={analyticsData} loading={loading} />
          )}

          {topPerformersData && (
            <TopPerformersCard data={topPerformersData} loading={loading} />
          )}
        </div>
      </div>

      {/* Loading Overlay (when refetching) */}
      {loading && summaryData && (
        <div className="fixed bottom-4 right-4 bg-background border border-border rounded-lg shadow-lg p-3 flex items-center gap-2">
          <Loader2 className="w-4 h-4 animate-spin text-primary" />
          <span className="text-sm text-muted-foreground">Atualizando...</span>
        </div>
      )}
    </div>
  );
};

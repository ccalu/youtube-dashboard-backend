import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { MonetizationBestWorstDayCard } from './MonetizationBestWorstDayCard';
import { MonetizationTopPerformersCard } from './MonetizationTopPerformersCard';
import { MonetizationProjectionCard } from './MonetizationProjectionCard';
import { MonetizationQualityMetrics } from './MonetizationQualityMetrics';
import { obterCorSubnicho } from '@/utils/subnichoColors';
import { getSubnichoEmoji } from '@/utils/subnichoEmojis';
import { Loader2 } from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

interface AnalyticsData {
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

interface SubnichoRevenueItem {
  name: string;
  revenue: number;
  percentage: number;
  color: string;
}

interface TrophyModalProps {
  analyticsData: AnalyticsData | null;
  topPerformersData: TopPerformersData | null;
  channelsData: ChannelsData | null;
  loading: boolean;
  period: string;
  month: string | null;
}

interface TargetModalProps {
  analyticsData: AnalyticsData | null;
  loading: boolean;
  period: string;
  month: string | null;
}

// getSubnichoEmoji now imported from @/utils/subnichoEmojis

const getMonthLabel = (month: string): string => {
  const [year, monthNum] = month.split('-');
  const monthNames = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
  return `${monthNames[parseInt(monthNum) - 1]} ${year}`;
};

const SubnichoRevenueDistribution: React.FC<{ channelsData: ChannelsData | null; loading: boolean; period: string; month: string | null }> = ({
  channelsData,
  loading,
  period,
  month,
}) => {
  if (loading) {
    return (
      <Card className="border-0">
        <CardContent className="p-4 flex items-center justify-center">
          <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  if (!channelsData || !channelsData.subnichos) {
    return null;
  }

  // Calculate revenue per subnicho with channel count
  const subnichoRevenues: (SubnichoRevenueItem & { channelCount: number })[] = channelsData.subnichos
    .map((sub) => {
      const totalRevenue = sub.channels.reduce((acc, ch) => acc + (ch.period_total?.revenue || 0), 0);
      return {
        name: sub.name,
        revenue: totalRevenue,
        percentage: 0,
        color: sub.color || obterCorSubnicho(sub.name).fundo,
        channelCount: sub.channels.length,
      };
    })
    .filter((item) => item.revenue > 0);

  const totalRevenue = subnichoRevenues.reduce((acc, item) => acc + item.revenue, 0);

  // Calculate percentages
  subnichoRevenues.forEach((item) => {
    item.percentage = totalRevenue > 0 ? (item.revenue / totalRevenue) * 100 : 0;
  });

  // Sort by revenue descending
  subnichoRevenues.sort((a, b) => b.revenue - a.revenue);

  const periodLabel = month ? getMonthLabel(month) : (period === 'total' ? 'Total' : period === '24h' ? '24h' : `${period.replace('d', '')} dias`);

  return (
    <Card className="border-0">
      <CardHeader className="pb-2 px-3 sm:px-4 pt-3 sm:pt-4">
        <CardTitle className="text-sm sm:text-base font-semibold">
          📊 Distribuição por Subnicho <span className="font-normal text-muted-foreground">({periodLabel})</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="p-3 sm:p-4 pt-0 space-y-2 sm:space-y-3">
        {subnichoRevenues.map((item) => {
          const cores = obterCorSubnicho(item.name);
          const emoji = getSubnichoEmoji(item.name);
          return (
            <div
              key={item.name}
              className="rounded-lg p-2 sm:p-3"
              style={{
                backgroundColor: cores.fundo + '25',
                borderLeft: `3px solid ${cores.borda}`,
              }}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-medium text-xs sm:text-sm truncate">
                  <span className="mr-1">{emoji}</span>
                  {item.name} <span className="font-normal text-muted-foreground">({item.channelCount})</span>
                </span>
                <div className="flex items-center gap-1.5 sm:gap-2 flex-shrink-0">
                  <span className="font-bold text-xs sm:text-sm text-green-500">${item.revenue.toFixed(2)}</span>
                  <span 
                    className="text-[10px] sm:text-xs px-1.5 sm:px-2 py-0.5 rounded-full font-bold text-white"
                    style={{ backgroundColor: cores.borda }}
                  >
                    {item.percentage.toFixed(1)}%
                  </span>
                </div>
              </div>
              {/* Progress bar */}
              <div className="mt-2 h-1.5 bg-background/30 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-300"
                  style={{
                    width: `${item.percentage}%`,
                    backgroundColor: cores.borda,
                  }}
                />
              </div>
            </div>
          );
        })}
        
        {/* Total - improved design */}
        <div className="mt-3 sm:mt-4 p-2 sm:p-3 rounded-lg bg-gradient-to-r from-green-500/10 to-green-500/5 border border-green-500/20">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 sm:gap-2">
              <span className="text-base sm:text-lg">💰</span>
              <span className="font-semibold text-xs sm:text-sm">Revenue Total</span>
            </div>
            <span className="font-bold text-lg sm:text-xl text-green-500">${totalRevenue.toFixed(2)}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export const TrophyModalButton: React.FC<TrophyModalProps> = ({
  analyticsData,
  topPerformersData,
  channelsData,
  loading,
  period,
  month,
}) => {
  const [open, setOpen] = useState(false);
  
  // Generate display label for period/month
  const getDisplayPeriod = () => {
    if (month) return getMonthLabel(month);
    return period;
  };

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="text-2xl sm:text-3xl hover:scale-110 transition-transform cursor-pointer"
        title="Top Performers & Melhor/Pior Dia"
      >
        🏆
      </button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-hidden [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
          <DialogHeader>
            <DialogTitle className="text-lg sm:text-xl">🏆 Top Performers & Análise {month && <span className="text-sm font-normal text-muted-foreground">({getMonthLabel(month)})</span>}</DialogTitle>
          </DialogHeader>
          <div className="space-y-3 mt-2 max-h-[calc(85vh-80px)] overflow-y-auto [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
            {analyticsData ? (
              <MonetizationBestWorstDayCard data={analyticsData} loading={loading} period={getDisplayPeriod()} month={month} />
            ) : (
              <Card className="border-0 bg-amber-500/10 border border-amber-500/30">
                <CardContent className="p-4">
                  <p className="text-sm text-amber-600">
                    ⚠️ Dados de melhor/pior dia não disponíveis para este período.
                  </p>
                </CardContent>
              </Card>
            )}
            {topPerformersData ? (
              <MonetizationTopPerformersCard data={topPerformersData} loading={loading} period={getDisplayPeriod()} month={month} />
            ) : (
              <Card className="border-0 bg-amber-500/10 border border-amber-500/30">
                <CardContent className="p-4">
                  <p className="text-sm text-amber-600">
                    ⚠️ Dados de top performers não disponíveis para este período.
                  </p>
                </CardContent>
              </Card>
            )}
            <SubnichoRevenueDistribution channelsData={channelsData} loading={loading} period={getDisplayPeriod()} month={month} />
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};

const API_BASE = 'https://youtube-dashboard-backend-production.up.railway.app';

interface OverallChartData {
  date: string;
  revenue: number;
  views: number;
}

interface OverallChartProps {
  month: string | null;
  period: string;
}

const OverallMonetizationChart: React.FC<OverallChartProps> = ({ month, period }) => {
  const [chartData, setChartData] = useState<OverallChartData[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ totalRevenue: 0, totalDays: 0, avgDaily: 0 });

  useEffect(() => {
    fetchOverallData();
  }, [month, period]);

  const fetchOverallData = async () => {
    setLoading(true);
    try {
      // Build query params
      const params = new URLSearchParams();
      if (month) {
        params.append('month', month);
      } else if (period && period !== 'total' && period !== 'month') {
        params.append('period', period);
      }
      // Cache buster
      params.append('_t', Date.now().toString());
      
      // Fetch config to get all monetized channels
      const configRes = await fetch(`${API_BASE}/api/monetization/config`);
      const config = await configRes.json();
      
      if (!config.channels || config.channels.length === 0) {
        setLoading(false);
        return;
      }

      // Calculate date range based on filters
      let startDate: Date | null = null;
      let endDate: Date = new Date();
      
      if (month) {
        const [year, monthNum] = month.split('-');
        startDate = new Date(parseInt(year), parseInt(monthNum) - 1, 1);
        endDate = new Date(parseInt(year), parseInt(monthNum), 0); // Last day of month
      } else if (period === 'monetizacao') {
        // Período de monetização baseado na lógica do backend
        const today = new Date();
        const currentDay = today.getDate();
        
        if (currentDay >= 13) {
          // Depois do dia 13: período do mês passado até este mês
          startDate = new Date(today.getFullYear(), today.getMonth() - 1, 13);
          endDate = new Date(today.getFullYear(), today.getMonth(), 12);
        } else {
          // Antes do dia 13: período de 2 meses atrás até mês passado
          startDate = new Date(today.getFullYear(), today.getMonth() - 2, 13);
          endDate = new Date(today.getFullYear(), today.getMonth() - 1, 12);
        }
      } else if (period && period !== 'total') {
        const days = parseInt(period.replace('d', '').replace('h', ''));
        if (period === '24h') {
          startDate = new Date();
          startDate.setDate(startDate.getDate() - 1);
        } else {
          startDate = new Date();
          startDate.setDate(startDate.getDate() - days);
        }
      } else {
        // For 'total', find earliest monetization start date
        const startDates = config.channels
          .map((ch: any) => ch.monetization_start_date)
          .filter(Boolean)
          .map((d: string) => new Date(d + 'T12:00:00'));
        
        if (startDates.length > 0) {
          startDate = new Date(Math.min(...startDates.map((d: Date) => d.getTime())));
          startDate.setDate(startDate.getDate() - 1);
        }
      }

      // Fetch history for all channels with filters
      const queryString = params.toString();
      const historyPromises = config.channels.map((ch: any) =>
        fetch(`${API_BASE}/api/monetization/channel/${ch.channel_id}/history${queryString ? `?${queryString}` : ''}`)
          .then(res => res.json())
          .catch(() => null)
      );

      const histories = await Promise.all(historyPromises);

      // Aggregate data by date
      const dateMap = new Map<string, { revenue: number; views: number }>();

      histories.forEach((history: any) => {
        if (!history?.history) return;
        history.history.forEach((item: any) => {
          const itemDate = new Date(item.date + 'T12:00:00');
          const shouldInclude = !startDate || itemDate >= startDate;
          const beforeEnd = itemDate <= endDate;
          
          if (shouldInclude && beforeEnd) {
            const existing = dateMap.get(item.date) || { revenue: 0, views: 0 };
            dateMap.set(item.date, {
              revenue: existing.revenue + (item.revenue || 0),
              views: existing.views + (item.views || 0),
            });
          }
        });
      });

      // Convert to array and sort by date
      const aggregatedData = Array.from(dateMap.entries())
        .map(([date, data]) => ({
          date,
          revenue: data.revenue,
          views: data.views,
        }))
        .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

      setChartData(aggregatedData);

      // Calculate stats
      const totalRevenue = aggregatedData.reduce((acc, d) => acc + d.revenue, 0);
      const totalDays = aggregatedData.length;
      const avgDaily = totalDays > 0 ? totalRevenue / totalDays : 0;
      setStats({ totalRevenue, totalDays, avgDaily });
    } catch (err) {
      console.error('Error fetching overall data:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString + 'T12:00:00');
    return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
  };

  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value);
  };

  if (loading) {
    return (
      <Card className="border-0">
        <CardContent className="p-4 flex items-center justify-center">
          <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  if (chartData.length === 0) {
    return null;
  }

  const displayData = chartData.map((item) => ({
    date: formatDate(item.date),
    revenue: item.revenue,
  }));

  return (
    <Card className="border-0">
      <CardHeader className="pb-2 px-3 sm:px-4 pt-3 sm:pt-4">
        <CardTitle className="text-sm sm:text-base font-semibold">
          📈 Revenue Geral <span className="font-normal text-muted-foreground">(Todos os Canais)</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="p-3 sm:p-4 pt-0 space-y-3">
        {/* Stats */}
        <div className="grid grid-cols-3 gap-2">
          <div className="p-2 rounded-lg bg-green-500/10 text-center">
            <p className="text-[10px] sm:text-xs text-muted-foreground">Total</p>
            <p className="text-xs sm:text-sm font-bold text-green-500">{formatCurrency(stats.totalRevenue)}</p>
          </div>
          <div className="p-2 rounded-lg bg-blue-500/10 text-center">
            <p className="text-[10px] sm:text-xs text-muted-foreground">Dias</p>
            <p className="text-xs sm:text-sm font-bold text-blue-500">{stats.totalDays}</p>
          </div>
          <div className="p-2 rounded-lg bg-yellow-500/10 text-center">
            <p className="text-[10px] sm:text-xs text-muted-foreground">Média/Dia</p>
            <p className="text-xs sm:text-sm font-bold text-yellow-500">{formatCurrency(stats.avgDaily)}</p>
          </div>
        </div>

        {/* Chart */}
        <div className="h-[180px] sm:h-[220px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={displayData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis
                dataKey="date"
                angle={-45}
                textAnchor="end"
                height={50}
                tick={{ fontSize: 9 }}
                stroke="rgba(255,255,255,0.5)"
              />
              <YAxis
                tick={{ fontSize: 9 }}
                tickFormatter={(value) => `$${value}`}
                width={40}
                stroke="rgba(255,255,255,0.5)"
              />
              <Tooltip
                formatter={(value: any) => [formatCurrency(value), 'Revenue']}
                contentStyle={{
                  backgroundColor: 'rgba(0, 0, 0, 0.9)',
                  border: '1px solid rgba(34, 197, 94, 0.3)',
                  borderRadius: '8px',
                  color: '#fff',
                  fontSize: '12px',
                }}
              />
              <Line
                type="monotone"
                dataKey="revenue"
                stroke="#22c55e"
                strokeWidth={2}
                dot={{ r: 2, fill: '#22c55e' }}
                activeDot={{ r: 4, fill: '#22c55e' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
};

export const TargetModalButton: React.FC<TargetModalProps> = ({
  analyticsData,
  loading,
  period,
  month,
}) => {
  const [open, setOpen] = useState(false);

  // Gera label do período para exibição
  const getPeriodLabel = () => {
    if (month) {
      const [year, monthNum] = month.split('-');
      const date = new Date(parseInt(year), parseInt(monthNum) - 1, 1);
      return date.toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' });
    }
    switch (period) {
      case '24h': return '24 horas';
      case '3d': return '3 dias';
      case '7d': return '7 dias';
      case '15d': return '15 dias';
      case '30d': return '30 dias';
      case 'total': return 'Todo período';
      case 'monetizacao': return 'Período 13-13';
      default: return period;
    }
  };

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="text-2xl sm:text-3xl hover:scale-110 transition-transform cursor-pointer"
        title="Projeção & Performance"
      >
        🎯
      </button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="w-[95vw] max-w-2xl max-h-[90vh] overflow-y-auto [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
          <DialogHeader>
            <DialogTitle className="text-lg sm:text-xl">🎯 Projeção & Performance</DialogTitle>
          </DialogHeader>
          <div className="mt-4 space-y-4">
            {analyticsData ? (
              <MonetizationProjectionCard 
                data={analyticsData} 
                loading={loading} 
                period={period}
                periodLabel={getPeriodLabel()}
              />
            ) : (
              <Card className="border-0 bg-amber-500/10 border border-amber-500/30">
                <CardContent className="p-4">
                  <p className="text-sm text-amber-600">
                    ⚠️ Dados de projeção não disponíveis para o período "{getPeriodLabel()}".
                  </p>
                </CardContent>
              </Card>
            )}
            <OverallMonetizationChart month={month} period={period} />
            <MonetizationQualityMetrics month={month} period={period} />
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};

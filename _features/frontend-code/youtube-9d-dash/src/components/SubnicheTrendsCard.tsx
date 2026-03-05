import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { apiService } from '@/services/api';
import { obterCorSubnicho } from '@/utils/subnichoColors';

interface SubnicheTrend {
  subnicho: string;
  total_videos: number;
  avg_views: number;
  engagement_rate: number;
  trend_percent: number;
  period_days: number;
}

interface TrendsData {
  '7d': SubnicheTrend[];
  '15d': SubnicheTrend[];
  '30d': SubnicheTrend[];
}

type SortColumn = 'subnicho' | 'total_videos' | 'avg_views' | 'trend_percent' | 'engagement_rate';
type SortDirection = 'asc' | 'desc' | null;

export function SubnicheTrendsCard() {
  const [trendsData, setTrendsData] = useState<TrendsData | null>(null);
  const [selectedPeriod, setSelectedPeriod] = useState<'7d' | '15d' | '30d'>('30d');
  const [sortColumn, setSortColumn] = useState<SortColumn>('avg_views');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totals, setTotals] = useState<{ '7d': number; '15d': number; '30d': number } | null>(null);

  useEffect(() => {
    fetchTrends();
  }, []);

  const fetchTrends = async () => {
    try {
      setLoading(true);
      const response = await apiService.getSubnicheTrends();

      if (response.success) {
        setTrendsData(response.data);
        setTotals({
          '7d': response.total_7d,
          '15d': response.total_15d,
          '30d': response.total_30d
        });
      } else {
        setError('Erro ao carregar tendências');
      }
    } catch (err) {
      console.error('Erro ao carregar trends:', err);
      setError('Erro ao conectar com o servidor');
    } finally {
      setLoading(false);
    }
  };

  const getCurrentTrends = (): SubnicheTrend[] => {
    if (!trendsData) return [];
    return trendsData[selectedPeriod] || [];
  };

  const handleSort = (column: SortColumn) => {
    if (sortColumn === column) {
      // Ciclo: desc → asc → null (padrão)
      if (sortDirection === 'desc') {
        setSortDirection('asc');
      } else if (sortDirection === 'asc') {
        setSortDirection(null);
        setSortColumn('avg_views'); // Volta ao padrão
      }
    } else {
      setSortColumn(column);
      setSortDirection('desc');
    }
  };

  const getSortedTrends = (): SubnicheTrend[] => {
    const trends = [...getCurrentTrends()];

    if (sortDirection === null) {
      // Padrão: avg_views desc
      return trends.sort((a, b) => b.avg_views - a.avg_views);
    }

    return trends.sort((a, b) => {
      let aValue: any = a[sortColumn];
      let bValue: any = b[sortColumn];

      // Para subnicho, ordenar alfabeticamente
      if (sortColumn === 'subnicho') {
        aValue = aValue.toLowerCase();
        bValue = bValue.toLowerCase();
        return sortDirection === 'desc'
          ? bValue.localeCompare(aValue)
          : aValue.localeCompare(bValue);
      }

      // Para números, ordenar numericamente
      if (sortDirection === 'desc') {
        return (bValue || 0) - (aValue || 0);
      } else {
        return (aValue || 0) - (bValue || 0);
      }
    });
  };

  const formatNumber = (num: number): string => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'k';
    }
    return num.toString();
  };

  const getTrendIcon = (percent: number) => {
    if (percent > 5) return <TrendingUp className="w-4 h-4 text-green-500" />;
    if (percent < -5) return <TrendingDown className="w-4 h-4 text-red-500" />;
    return <Minus className="w-4 h-4 text-gray-500" />;
  };

  const getTrendText = (percent: number): string => {
    if (percent > 0) return `+${percent.toFixed(1)}%`;
    return `${percent.toFixed(1)}%`;
  };

  const getSortIcon = (column: SortColumn) => {
    if (sortColumn !== column || sortDirection === null) return '⬍';
    return sortDirection === 'desc' ? '🔽' : '🔼';
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>📊 Tendências por Subniche</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center p-8">
            <div className="text-gray-500">Carregando...</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>📊 Tendências por Subniche</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center p-8 text-red-500">{error}</div>
        </CardContent>
      </Card>
    );
  }

  const sortedTrends = getSortedTrends();

  return (
    <Card>
      <CardHeader className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <CardTitle className="text-base sm:text-lg">📊 Tendências por Subniche</CardTitle>
        <div className="flex gap-1 sm:gap-2">
          <Button
            variant={selectedPeriod === '7d' ? 'default' : 'outline'}
            size="sm"
            className="text-xs sm:text-sm px-2 sm:px-3"
            onClick={() => setSelectedPeriod('7d')}
          >
            7d
          </Button>
          <Button
            variant={selectedPeriod === '15d' ? 'default' : 'outline'}
            size="sm"
            className="text-xs sm:text-sm px-2 sm:px-3"
            onClick={() => setSelectedPeriod('15d')}
          >
            15d
          </Button>
          <Button
            variant={selectedPeriod === '30d' ? 'default' : 'outline'}
            size="sm"
            className="text-xs sm:text-sm px-2 sm:px-3"
            onClick={() => setSelectedPeriod('30d')}
          >
            30d
          </Button>
        </div>
      </CardHeader>
      <CardContent className="p-2 sm:p-6">
        {/* Desktop Table */}
        <div className="hidden sm:block overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border">
                <th
                  onClick={() => handleSort('subnicho')}
                  className="text-left p-3 cursor-pointer hover:bg-muted/50 transition-colors bg-background"
                >
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-foreground">Subniche</span>
                    <span className="text-xs opacity-50">{getSortIcon('subnicho')}</span>
                  </div>
                </th>
                <th
                  onClick={() => handleSort('total_videos')}
                  className="text-right p-3 cursor-pointer hover:bg-muted/50 transition-colors bg-background"
                >
                  <div className="flex items-center justify-end gap-2">
                    <span className="font-semibold text-foreground">Vídeos</span>
                    <span className="text-xs opacity-50">{getSortIcon('total_videos')}</span>
                  </div>
                </th>
                <th
                  onClick={() => handleSort('avg_views')}
                  className="text-right p-3 cursor-pointer hover:bg-muted/50 transition-colors bg-background"
                >
                  <div className="flex items-center justify-end gap-2">
                    <span className="font-semibold text-foreground">Views Médias</span>
                    <span className="text-xs opacity-50">{getSortIcon('avg_views')}</span>
                  </div>
                </th>
                <th
                  onClick={() => handleSort('trend_percent')}
                  className="text-right p-3 cursor-pointer hover:bg-muted/50 transition-colors bg-background"
                >
                  <div className="flex items-center justify-end gap-2">
                    <span className="font-semibold text-foreground">Tendência</span>
                    <span className="text-xs opacity-50">{getSortIcon('trend_percent')}</span>
                  </div>
                </th>
                <th
                  onClick={() => handleSort('engagement_rate')}
                  className="text-right p-3 cursor-pointer hover:bg-muted/50 transition-colors bg-background"
                >
                  <div className="flex items-center justify-end gap-2">
                    <span className="font-semibold text-foreground">Engagement</span>
                    <span className="text-xs opacity-50">{getSortIcon('engagement_rate')}</span>
                  </div>
                </th>
              </tr>
            </thead>
            <tbody>
              {sortedTrends.map((trend) => {
                const cores = obterCorSubnicho(trend.subnicho);
                const color = cores.fundo;
                const backgroundColor = `${color}40`;

                  return (
                    <tr
                      key={trend.subnicho}
                      className="border-b border-border hover:brightness-110 transition-all"
                      style={{ backgroundColor }}
                    >
                    <td className="p-3">
                      <div className="flex items-center gap-2">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: color }}
                        />
                        <span className="font-medium">{trend.subnicho}</span>
                      </div>
                    </td>
                    <td className="p-3 text-right text-white font-medium">{trend.total_videos}</td>
                    <td className="p-3 text-right font-semibold">
                      {formatNumber(trend.avg_views)}
                    </td>
                    <td className="p-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {getTrendIcon(trend.trend_percent)}
                        <span className="font-medium">{getTrendText(trend.trend_percent)}</span>
                      </div>
                    </td>
                    <td className="p-3 text-right text-white font-medium">
                      {trend.engagement_rate.toFixed(2)}%
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Mobile Cards */}
        <div className="sm:hidden space-y-2">
          {sortedTrends.map((trend) => {
            const cores = obterCorSubnicho(trend.subnicho);
            const color = cores.fundo;
            const backgroundColor = `${color}40`;

            return (
              <div
                key={trend.subnicho}
                className="p-3 rounded-lg border"
                style={{ backgroundColor, borderColor: cores.borda }}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full flex-shrink-0"
                      style={{ backgroundColor: color }}
                    />
                    <span className="font-semibold text-sm">{trend.subnicho}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    {getTrendIcon(trend.trend_percent)}
                    <span className="text-xs font-medium">{getTrendText(trend.trend_percent)}</span>
                  </div>
                </div>
                <div className="flex items-center justify-between text-xs text-foreground">
                  <span>📹 {trend.total_videos} vídeos</span>
                  <span>👁 {formatNumber(trend.avg_views)} views</span>
                  <span>📊 {trend.engagement_rate.toFixed(1)}%</span>
                </div>
              </div>
            );
          })}
        </div>

        {sortedTrends.length === 0 && (
          <div className="text-center p-8 text-gray-500">
            Nenhum dado disponível para o período selecionado
          </div>
        )}
      </CardContent>
    </Card>
  );
}

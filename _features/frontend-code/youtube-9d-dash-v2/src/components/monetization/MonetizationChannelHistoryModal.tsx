import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { Loader2, Download, TrendingUp } from 'lucide-react';

interface ChannelHistoryModalProps {
  open: boolean;
  channelId: string;
  channelName: string;
  onClose: () => void;
  month: string | null;
  period: string;
}

interface HistoryData {
  channel_id: string;
  channel_name: string;
  history: Array<{
    date: string;
    views: number;
    revenue: number;
    rpm: number;
    is_estimate: boolean;
  }>;
  stats: {
    total_days: number;
    total_revenue: number;
    avg_rpm: number;
  };
}

const API_BASE = 'https://youtube-dashboard-backend-production.up.railway.app';

const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
};

const formatNumber = (num: number): string => {
  return num.toLocaleString('pt-BR');
};

const formatDate = (dateString: string): string => {
  const date = new Date(dateString + 'T12:00:00');
  return date.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
};

export const MonetizationChannelHistoryModal: React.FC<ChannelHistoryModalProps> = ({
  open,
  channelId,
  channelName,
  onClose,
  month,
  period,
}) => {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<HistoryData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [visibleRows, setVisibleRows] = useState(15);

  useEffect(() => {
    if (open && channelId) {
      fetchHistory();
    }
  }, [open, channelId, month, period]);

  const fetchHistory = async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (month) {
        params.append('month', month);
      } else if (period && period !== 'total') {
        params.append('period', period);
      }
      // Cache buster
      params.append('_t', Date.now().toString());
      
      const queryString = params.toString();
      const url = `${API_BASE}/api/monetization/channel/${channelId}/history${queryString ? `?${queryString}` : ''}`;
      
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error('Erro ao buscar histórico');
      }

      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro desconhecido');
    } finally {
      setLoading(false);
    }
  };

  // Filter history to start from when channel was monetized (include 1 day before first revenue)
  const getFilteredHistory = () => {
    if (!data?.history) return [];
    
    // History comes sorted by date desc, so reverse to find first day with revenue
    const reversedHistory = [...data.history].reverse();
    
    // Find first index where revenue > 0
    const firstRevenueIndex = reversedHistory.findIndex(item => item.revenue > 0);
    
    if (firstRevenueIndex === -1) return data.history; // No revenue found, show original order (desc)
    
    // Include 1 day before first revenue if available
    const startIndex = Math.max(0, firstRevenueIndex - 1);
    
    // Return in desc order (most recent first) for table display
    return reversedHistory.slice(startIndex).reverse();
  };

  const filteredHistory = getFilteredHistory();

  const handleLoadMore = () => {
    setVisibleRows((prev) => Math.min(prev + 15, filteredHistory.length));
  };

  const handleDownloadCSV = () => {
    if (!filteredHistory.length) return;

    const headers = ['Data', 'Views', 'Revenue (USD)', 'RPM (USD)', 'Tipo'];
    const rows = filteredHistory.map((row) => [
      row.date,
      row.views,
      row.revenue.toFixed(2),
      row.rpm.toFixed(2),
      row.is_estimate ? 'Estimativa' : 'Real',
    ]);

    const csv = [headers, ...rows].map((row) => row.join(',')).join('\n');

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `${channelName.replace(/\s+/g, '_')}_historico.csv`;
    link.click();
  };

  const chartData = [...filteredHistory].reverse().map((item) => ({
    date: formatDate(item.date),
    revenue: item.revenue,
    rpm: item.rpm,
    isEstimate: item.is_estimate,
  }));

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="w-[95vw] max-w-6xl max-h-[90vh] overflow-y-auto p-3 sm:p-6">
        <DialogHeader>
          <DialogTitle className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <span className="text-sm sm:text-base truncate">📅 Histórico: {channelName}</span>
            {data && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleDownloadCSV}
                className="w-full sm:w-auto text-xs sm:text-sm"
              >
                <Download className="w-3 h-3 sm:w-4 sm:h-4 mr-1 sm:mr-2" />
                CSV
              </Button>
            )}
          </DialogTitle>
        </DialogHeader>

        {loading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
          </div>
        )}

        {error && (
          <div className="text-center py-8">
            <p className="text-red-500 mb-4">{error}</p>
            <Button onClick={fetchHistory}>Tentar Novamente</Button>
          </div>
        )}

        {data && !loading && (
          <div className="space-y-4 sm:space-y-6">
            {data.stats && (
              <div className="grid grid-cols-3 gap-2 sm:gap-4">
                <div className="p-2 sm:p-4 border rounded-lg">
                  <p className="text-[10px] sm:text-sm text-muted-foreground mb-0.5 sm:mb-1">
                    Total Revenue
                  </p>
                  <p className="text-sm sm:text-2xl font-bold text-green-600">
                    {formatCurrency(data.stats.total_revenue || 0)}
                  </p>
                </div>
                <div className="p-2 sm:p-4 border rounded-lg">
                  <p className="text-[10px] sm:text-sm text-muted-foreground mb-0.5 sm:mb-1">RPM Médio</p>
                  <p className="text-sm sm:text-2xl font-bold text-yellow-600">
                    {formatCurrency(data.stats.avg_rpm || 0)}
                  </p>
                </div>
                <div className="p-2 sm:p-4 border rounded-lg">
                  <p className="text-[10px] sm:text-sm text-muted-foreground mb-0.5 sm:mb-1">Total Dias</p>
                  <p className="text-sm sm:text-2xl font-bold text-blue-600">
                    {data.stats.total_days || 0}
                  </p>
                </div>
              </div>
            )}

            <div className="border rounded-lg p-2 sm:p-4">
              <h4 className="text-xs sm:text-sm font-semibold mb-2 sm:mb-4 flex items-center gap-2">
                <TrendingUp className="w-3 h-3 sm:w-4 sm:h-4" />
                Revenue ao Longo do Tempo
              </h4>
              <ResponsiveContainer width="100%" height={200} className="sm:!h-[300px]">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="date"
                    angle={-45}
                    textAnchor="end"
                    height={60}
                    tick={{ fontSize: 9 }}
                    className="sm:text-xs"
                  />
                  <YAxis
                    yAxisId="left"
                    tick={{ fontSize: 9 }}
                    tickFormatter={(value) => `$${value}`}
                    width={35}
                  />
                  <YAxis
                    yAxisId="right"
                    orientation="right"
                    tick={{ fontSize: 9 }}
                    tickFormatter={(value) => `$${value}`}
                    width={35}
                    className="hidden sm:block"
                  />
                  <Tooltip
                    formatter={(value: any, name: string) => {
                      if (name === 'revenue') return [formatCurrency(value), 'Revenue'];
                      if (name === 'rpm') return [formatCurrency(value), 'RPM'];
                      return [value, name];
                    }}
                    contentStyle={{
                      backgroundColor: 'rgba(0, 0, 0, 0.8)',
                      border: 'none',
                      borderRadius: '8px',
                      color: '#fff',
                      fontSize: '12px',
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: '10px' }} />
                  <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="revenue"
                    stroke="#22c55e"
                    strokeWidth={2}
                    dot={{ r: 2 }}
                    name="Revenue"
                  />
                  <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="rpm"
                    stroke="#eab308"
                    strokeWidth={2}
                    dot={{ r: 2 }}
                    name="RPM"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="border rounded-lg overflow-hidden">
              {/* Mobile view - compact rows */}
              <div className="sm:hidden">
                {/* Header row */}
                <div className="grid grid-cols-5 gap-1 p-2 bg-muted/50 border-b text-[9px] font-semibold text-muted-foreground text-center">
                  <div>Data</div>
                  <div>Views</div>
                  <div>Revenue</div>
                  <div>RPM</div>
                  <div>Tipo</div>
                </div>
                {/* Data rows */}
                <div className="divide-y divide-border">
                  {filteredHistory.slice(0, visibleRows).map((row, index) => (
                    <div key={index} className="grid grid-cols-5 gap-1 p-2 text-[10px] text-center items-center">
                      <div className="font-medium">{formatDate(row.date).slice(0, 5)}</div>
                      <div>{formatNumber(row.views)}</div>
                      <div className="font-semibold text-green-600">{formatCurrency(row.revenue)}</div>
                      <div className="text-yellow-600">${(row.rpm || 0).toFixed(2)}</div>
                      <div>
                        {row.is_estimate ? (
                          <Badge variant="outline" className="bg-yellow-500/10 text-yellow-600 border-yellow-500/20 text-[8px] px-1 py-0">
                            Est.
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="bg-green-500/10 text-green-600 border-green-500/20 text-[8px] px-1 py-0">
                            Real
                          </Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Desktop view - table */}
              <Table className="hidden sm:table">
                <TableHeader>
                  <TableRow>
                    <TableHead>Data</TableHead>
                    <TableHead className="text-right">Views</TableHead>
                    <TableHead className="text-right">Revenue</TableHead>
                    <TableHead className="text-right">RPM</TableHead>
                    <TableHead className="text-center">Tipo</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredHistory.slice(0, visibleRows).map((row, index) => (
                    <TableRow key={index}>
                      <TableCell className="font-medium">{formatDate(row.date)}</TableCell>
                      <TableCell className="text-right">
                        {formatNumber(row.views)}
                      </TableCell>
                      <TableCell className="text-right font-semibold text-green-600">
                        {formatCurrency(row.revenue)}
                      </TableCell>
                      <TableCell className="text-right text-yellow-600">
                        ${(row.rpm || 0).toFixed(2)}
                      </TableCell>
                      <TableCell className="text-center">
                        {row.is_estimate ? (
                          <Badge
                            variant="outline"
                            className="bg-yellow-500/10 text-yellow-600 border-yellow-500/20 text-[10px]"
                          >
                            Est.
                          </Badge>
                        ) : (
                          <Badge
                            variant="outline"
                            className="bg-green-500/10 text-green-600 border-green-500/20 text-[10px]"
                          >
                            Real
                          </Badge>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {visibleRows < filteredHistory.length && (
                <div className="p-3 sm:p-4 border-t text-center">
                  <Button onClick={handleLoadMore} variant="outline" size="sm" className="text-xs sm:text-sm">
                    Carregar Mais (+15 dias)
                  </Button>
                  <p className="text-[10px] sm:text-xs text-muted-foreground mt-2">
                    Mostrando {visibleRows} de {filteredHistory.length} dias
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

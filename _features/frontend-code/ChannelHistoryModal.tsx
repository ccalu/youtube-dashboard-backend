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

/**
 * CHANNEL HISTORY MODAL - Modal com Histórico Completo
 *
 * Features:
 * - Gráfico de linha (revenue ao longo do tempo)
 * - Tabela paginada (15 dias iniciais + "Carregar Mais")
 * - Stats resumo (Total Revenue, Avg RPM, Total Days)
 * - Download CSV (bonus)
 */

interface ChannelHistoryModalProps {
  open: boolean;
  channelId: string;
  channelName: string;
  onClose: () => void;
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
  const date = new Date(dateString);
  return date.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
};

export const ChannelHistoryModal: React.FC<ChannelHistoryModalProps> = ({
  open,
  channelId,
  channelName,
  onClose,
}) => {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<HistoryData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [visibleRows, setVisibleRows] = useState(15);

  useEffect(() => {
    if (open && channelId) {
      fetchHistory();
    }
  }, [open, channelId]);

  const fetchHistory = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_BASE}/api/monetization/channel/${channelId}/history`
      );

      if (!response.ok) {
        throw new Error('Erro ao buscar histórico');
      }

      const result = await response.json();
      setData(result);
    } catch (err) {
      console.error('Erro ao buscar histórico:', err);
      setError(err instanceof Error ? err.message : 'Erro desconhecido');
    } finally {
      setLoading(false);
    }
  };

  const handleLoadMore = () => {
    setVisibleRows((prev) => Math.min(prev + 15, data?.history.length || 0));
  };

  const handleDownloadCSV = () => {
    if (!data) return;

    const headers = ['Data', 'Views', 'Revenue (USD)', 'RPM (USD)', 'Tipo'];
    const rows = data.history.map((row) => [
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

  // Prepare chart data (reverse to show oldest first)
  const chartData = data
    ? [...data.history]
        .reverse()
        .map((item) => ({
          date: formatDate(item.date),
          revenue: item.revenue,
          rpm: item.rpm,
          isEstimate: item.is_estimate,
        }))
    : [];

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            <span>Histórico: {channelName}</span>
            {data && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleDownloadCSV}
                className="ml-4"
              >
                <Download className="w-4 h-4 mr-2" />
                Download CSV
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
          <div className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 border rounded-lg">
                <p className="text-sm text-muted-foreground mb-1">
                  Total Revenue
                </p>
                <p className="text-2xl font-bold text-green-600">
                  {formatCurrency(data.stats.total_revenue)}
                </p>
              </div>
              <div className="p-4 border rounded-lg">
                <p className="text-sm text-muted-foreground mb-1">RPM Médio</p>
                <p className="text-2xl font-bold text-yellow-600">
                  {formatCurrency(data.stats.avg_rpm)}
                </p>
              </div>
              <div className="p-4 border rounded-lg">
                <p className="text-sm text-muted-foreground mb-1">Total Dias</p>
                <p className="text-2xl font-bold text-blue-600">
                  {data.stats.total_days}
                </p>
              </div>
            </div>

            {/* Chart */}
            <div className="border rounded-lg p-4">
              <h4 className="text-sm font-semibold mb-4 flex items-center gap-2">
                <TrendingUp className="w-4 h-4" />
                Revenue ao Longo do Tempo
              </h4>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="date"
                    angle={-45}
                    textAnchor="end"
                    height={80}
                    tick={{ fontSize: 12 }}
                  />
                  <YAxis
                    yAxisId="left"
                    tick={{ fontSize: 12 }}
                    tickFormatter={(value) => `$${value}`}
                  />
                  <YAxis
                    yAxisId="right"
                    orientation="right"
                    tick={{ fontSize: 12 }}
                    tickFormatter={(value) => `$${value}`}
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
                    }}
                  />
                  <Legend />
                  <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="revenue"
                    stroke="#22c55e"
                    strokeWidth={2}
                    dot={{ r: 3 }}
                    name="Revenue"
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="rpm"
                    stroke="#eab308"
                    strokeWidth={2}
                    dot={{ r: 3 }}
                    name="RPM"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Table */}
            <div className="border rounded-lg overflow-hidden">
              <Table>
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
                  {data.history.slice(0, visibleRows).map((row, index) => (
                    <TableRow key={index}>
                      <TableCell>{formatDate(row.date)}</TableCell>
                      <TableCell className="text-right">
                        {formatNumber(row.views)}
                      </TableCell>
                      <TableCell className="text-right font-semibold">
                        {formatCurrency(row.revenue)}
                      </TableCell>
                      <TableCell className="text-right">
                        {formatCurrency(row.rpm)}
                      </TableCell>
                      <TableCell className="text-center">
                        {row.is_estimate ? (
                          <Badge
                            variant="outline"
                            className="bg-yellow-500/10 text-yellow-600 border-yellow-500/20"
                          >
                            Estimativa
                          </Badge>
                        ) : (
                          <Badge
                            variant="outline"
                            className="bg-green-500/10 text-green-600 border-green-500/20"
                          >
                            Real
                          </Badge>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Load More Button */}
              {visibleRows < data.history.length && (
                <div className="p-4 border-t text-center">
                  <Button onClick={handleLoadMore} variant="outline">
                    Carregar Mais (+15 dias)
                  </Button>
                  <p className="text-xs text-muted-foreground mt-2">
                    Mostrando {visibleRows} de {data.history.length} dias
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

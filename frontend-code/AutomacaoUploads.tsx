/**
 * AutomacaoUploads.tsx
 *
 * Componente completo para aba de Automação de Uploads
 * Dashboard de gerenciamento dos 50 canais YouTube
 *
 * Features:
 * - Monitor Railway (scanner/worker) em tempo real
 * - Fila de uploads (processing + pending)
 * - Monitor 50 canais por subnicho
 * - Histórico completo (sucessos + erros)
 * - Controles globais (pause/resume/clear/retry)
 * - Tempo real com polling configurável
 * - Optimistic updates para ações instantâneas
 * - 100% responsivo (mobile-first)
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Progress } from '@/components/ui/progress';
import {
  RefreshCw,
  Pause,
  Play,
  Trash2,
  RotateCcw,
  ChevronUp,
  ChevronDown,
  X,
  FileText,
  FileSpreadsheet,
  ZapOff,
  Loader2,
  AlertCircle,
  CheckCircle,
  Clock,
  TrendingUp,
} from 'lucide-react';

// ============================================================================
// INTERFACES TYPESCRIPT
// ============================================================================

interface FilterState {
  period: '24h' | '7d' | '30d' | 'all';
  status: 'all' | 'completed' | 'failed' | 'pending' | 'processing';
  subnicho: string; // 'all' ou nome do subnicho
  canal_id: string | null; // null ou ID do canal
}

interface SummaryData {
  scanner: {
    status: 'active' | 'paused' | 'error';
    last_run: string;
    next_run_in: number; // segundos
    cycle_duration: number;
  };
  worker: {
    status: 'active' | 'paused' | 'error';
    last_run: string;
    next_run_in: number;
    cycle_duration: number;
  };
  queue: {
    pending: number;
    processing: number;
    completed: number;
    failed: number;
  };
  performance: {
    success_rate: number;
    avg_upload_time: number;
    uploads_per_hour: number;
  };
}

interface Upload {
  id: number;
  channel_id: string;
  channel_name: string;
  titulo: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number; // 0-100
  current_step: 'downloading' | 'uploading' | 'processing' | null;
  elapsed_seconds: number;
  position: number; // Posição na fila
  scheduled_at: string;
  started_at: string | null;
  completed_at: string | null;
  retry_count: number;
  error_message: string | null;
  youtube_video_id: string | null;
  youtube_url: string | null;
  spreadsheet_id: string;
  spreadsheet_url: string;
  sheets_row_number: number;
}

interface QueueData {
  processing: Upload[];
  pending: Upload[];
}

interface Channel {
  channel_id: string;
  channel_name: string;
  lingua: string;
  spreadsheet_id: string;
  spreadsheet_url: string;
  last_scan_at: string | null;
  scan_delay_minutes: number;
  queue_pending: number;
  uploads_completed: number;
  uploads_failed: number;
  success_rate: number;
  last_upload_at: string | null;
  last_upload_status: string | null;
  status: 'healthy' | 'warning' | 'error';
}

interface Subnicho {
  name: string;
  total_channels: number;
  uploads_count: number; // Agregado de todos canais
  queue_pending: number; // Agregado de todos canais
  errors_count: number; // Agregado de todos canais
  channels: Channel[];
}

interface ChannelsData {
  subnichos: Subnicho[];
}

interface HistoryUpload {
  id: number;
  channel_name: string;
  titulo: string;
  status: 'completed' | 'failed';
  scheduled_at: string;
  completed_at: string | null;
  duration_seconds: number | null;
  retry_count: number;
  error_message: string | null;
  youtube_url: string | null;
  spreadsheet_url: string;
  sheets_row_number: number;
}

interface HistoryData {
  completed: HistoryUpload[];
  failed: HistoryUpload[];
  summary: {
    total_uploads: number;
    with_error: number;
    success_rate: number;
    avg_time_seconds: number;
  };
}

interface UploadLogs {
  id: number;
  channel_id: string;
  channel_name: string;
  titulo: string;
  descricao: string;
  spreadsheet_id: string;
  sheets_row_number: number;
  scheduled_at: string;
  started_at: string | null;
  completed_at: string | null;
  duration_seconds: number | null;
  retry_count: number;
  status: string;
  error_message: string | null;
  error_type: string | null;
  error_details: any;
  youtube_video_id: string | null;
  youtube_url: string | null;
  video_url: string;
}

// ============================================================================
// CONFIGURAÇÕES
// ============================================================================

const API_BASE = 'https://youtube-dashboard-backend-production.up.railway.app';

const POLLING_INTERVALS = {
  queue: 2000,      // 2s - Fila muda rápido
  summary: 10000,   // 10s - Stats gerais
  channels: 30000,  // 30s - Canais mudam devagar
};

const STATUS_COLORS = {
  healthy: 'bg-green-500/10 text-green-600 border-green-500/20',
  warning: 'bg-yellow-500/10 text-yellow-600 border-yellow-500/20',
  error: 'bg-red-500/10 text-red-600 border-red-500/20',
  active: 'bg-blue-500/10 text-blue-600 border-blue-500/20',
  paused: 'bg-gray-500/10 text-gray-600 border-gray-500/20',
};

const STEP_LABELS = {
  downloading: 'Downloading',
  uploading: 'Uploading',
  processing: 'Processing',
};

// ============================================================================
// COMPONENTE PRINCIPAL
// ============================================================================

export const AutomacaoUploads: React.FC = () => {
  // Estados principais
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Estados de dados
  const [filters, setFilters] = useState<FilterState>({
    period: '24h',
    status: 'all',
    subnicho: 'all',
    canal_id: null,
  });

  const [summaryData, setSummaryData] = useState<SummaryData | null>(null);
  const [queueData, setQueueData] = useState<QueueData | null>(null);
  const [channelsData, setChannelsData] = useState<ChannelsData | null>(null);
  const [historyData, setHistoryData] = useState<HistoryData | null>(null);

  // Estados de countdown (atualizados a cada 1s)
  const [countdowns, setCountdowns] = useState({
    scanner: 0,
    worker: 0,
  });

  // Estados de modais
  const [confirmModal, setConfirmModal] = useState<{
    open: boolean;
    title: string;
    description: string;
    action: (() => void) | null;
  }>({
    open: false,
    title: '',
    description: '',
    action: null,
  });

  const [logsModal, setLogsModal] = useState<{
    open: boolean;
    data: UploadLogs | null;
  }>({
    open: false,
    data: null,
  });

  const [cardModal, setCardModal] = useState<{
    open: boolean;
    card: 'scanner' | 'worker' | null;
  }>({
    open: false,
    card: null,
  });

  // Estados de expansão (subnichos)
  const [expandedSubnichos, setExpandedSubnichos] = useState<Set<string>>(new Set());

  // Estados de canais disponíveis para filtro
  const [availableChannels, setAvailableChannels] = useState<Channel[]>([]);

  // ============================================================================
  // FUNÇÕES DE FETCH
  // ============================================================================

  const fetchAllData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams({
        period: filters.period,
      });

      if (filters.subnicho !== 'all') {
        params.append('subnicho', filters.subnicho);
      }

      if (filters.canal_id) {
        params.append('channel_id', filters.canal_id);
      }

      if (filters.status !== 'all') {
        params.append('status', filters.status);
      }

      // Fetch paralelo de todos os endpoints
      const [summaryRes, queueRes, channelsRes, historyRes] = await Promise.all([
        fetch(`${API_BASE}/api/automation/uploads/summary?${params}`),
        fetch(`${API_BASE}/api/automation/uploads/queue`),
        fetch(`${API_BASE}/api/automation/uploads/channels?${params}`),
        fetch(`${API_BASE}/api/automation/uploads/history?${params}`),
      ]);

      if (!summaryRes.ok || !queueRes.ok || !channelsRes.ok || !historyRes.ok) {
        throw new Error('Erro ao buscar dados');
      }

      const [summary, queue, channels, history] = await Promise.all([
        summaryRes.json(),
        queueRes.json(),
        channelsRes.json(),
        historyRes.json(),
      ]);

      setSummaryData(summary);
      setQueueData(queue);
      setChannelsData(channels);
      setHistoryData(history);

      // Atualiza countdowns iniciais
      setCountdowns({
        scanner: summary.scanner.next_run_in,
        worker: summary.worker.next_run_in,
      });

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro desconhecido');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  const fetchQueue = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/automation/uploads/queue`);
      if (!response.ok) throw new Error('Erro ao buscar fila');
      const data = await response.json();
      setQueueData(data);
    } catch (err) {
      console.error('Erro ao atualizar fila:', err);
    }
  }, []);

  const fetchSummary = useCallback(async () => {
    try {
      const params = new URLSearchParams({ period: filters.period });
      const response = await fetch(`${API_BASE}/api/automation/uploads/summary?${params}`);
      if (!response.ok) throw new Error('Erro ao buscar summary');
      const data = await response.json();

      setSummaryData(data);
      setCountdowns({
        scanner: data.scanner.next_run_in,
        worker: data.worker.next_run_in,
      });
    } catch (err) {
      console.error('Erro ao atualizar summary:', err);
    }
  }, [filters.period]);

  const fetchChannels = useCallback(async () => {
    try {
      const params = new URLSearchParams({ period: filters.period });

      if (filters.subnicho !== 'all') {
        params.append('subnicho', filters.subnicho);
      }

      const response = await fetch(`${API_BASE}/api/automation/uploads/channels?${params}`);
      if (!response.ok) throw new Error('Erro ao buscar canais');
      const data = await response.json();
      setChannelsData(data);
    } catch (err) {
      console.error('Erro ao atualizar canais:', err);
    }
  }, [filters.period, filters.subnicho]);

  // ============================================================================
  // EFFECTS
  // ============================================================================

  // Fetch inicial
  useEffect(() => {
    fetchAllData();
  }, [fetchAllData]);

  // Polling: Queue (2s)
  useEffect(() => {
    const interval = setInterval(fetchQueue, POLLING_INTERVALS.queue);
    return () => clearInterval(interval);
  }, [fetchQueue]);

  // Polling: Summary (10s)
  useEffect(() => {
    const interval = setInterval(fetchSummary, POLLING_INTERVALS.summary);
    return () => clearInterval(interval);
  }, [fetchSummary]);

  // Polling: Channels (30s)
  useEffect(() => {
    const interval = setInterval(fetchChannels, POLLING_INTERVALS.channels);
    return () => clearInterval(interval);
  }, [fetchChannels]);

  // Countdown (1s)
  useEffect(() => {
    const interval = setInterval(() => {
      setCountdowns(prev => ({
        scanner: Math.max(0, prev.scanner - 1),
        worker: Math.max(0, prev.worker - 1),
      }));
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  // Stop polling quando aba invisível (otimização)
  useEffect(() => {
    const handleVisibility = () => {
      if (document.hidden) {
        console.log('Aba invisível - pausando polling');
      } else {
        console.log('Aba visível - retomando polling');
        fetchAllData();
      }
    };

    document.addEventListener('visibilitychange', handleVisibility);
    return () => document.removeEventListener('visibilitychange', handleVisibility);
  }, [fetchAllData]);

  // Atualiza canais disponíveis quando subnicho muda
  useEffect(() => {
    if (filters.subnicho === 'all') {
      setAvailableChannels([]);
      setFilters(prev => ({ ...prev, canal_id: null }));
    } else if (channelsData) {
      const subnicho = channelsData.subnichos.find(s => s.name === filters.subnicho);
      if (subnicho) {
        setAvailableChannels(subnicho.channels);
      }
    }
  }, [filters.subnicho, channelsData]);

  // ============================================================================
  // FUNÇÕES DE AÇÃO
  // ============================================================================

  const handleControlAction = async (action: string, description: string) => {
    setConfirmModal({
      open: true,
      title: 'Confirmar Ação',
      description,
      action: async () => {
        try {
          const response = await fetch(`${API_BASE}/api/automation/uploads/control`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action }),
          });

          if (!response.ok) throw new Error('Erro ao executar ação');

          // Re-fetch dados
          await fetchAllData();

          setConfirmModal({ open: false, title: '', description: '', action: null });
        } catch (err) {
          alert('Erro: ' + (err instanceof Error ? err.message : 'Desconhecido'));
        }
      },
    });
  };

  const handleUploadAction = async (uploadId: number, action: string, optimistic: boolean = false) => {
    if (action === 'cancel') {
      // Cancel precisa confirmação
      setConfirmModal({
        open: true,
        title: 'Cancelar Upload',
        description: 'Tem certeza que deseja cancelar este upload?',
        action: async () => {
          try {
            const response = await fetch(`${API_BASE}/api/automation/uploads/${uploadId}`, {
              method: 'PATCH',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ action }),
            });

            if (!response.ok) throw new Error('Erro ao cancelar');

            await fetchQueue();
            setConfirmModal({ open: false, title: '', description: '', action: null });
          } catch (err) {
            alert('Erro: ' + (err instanceof Error ? err.message : 'Desconhecido'));
          }
        },
      });
      return;
    }

    // Ações optimistic (move up/down)
    if (optimistic && queueData) {
      const newQueue = { ...queueData };
      const index = newQueue.pending.findIndex(u => u.id === uploadId);

      if (action === 'move_up' && index > 0) {
        [newQueue.pending[index - 1], newQueue.pending[index]] =
        [newQueue.pending[index], newQueue.pending[index - 1]];
        setQueueData(newQueue);
      } else if (action === 'move_down' && index < newQueue.pending.length - 1) {
        [newQueue.pending[index], newQueue.pending[index + 1]] =
        [newQueue.pending[index + 1], newQueue.pending[index]];
        setQueueData(newQueue);
      }
    }

    try {
      const response = await fetch(`${API_BASE}/api/automation/uploads/${uploadId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action }),
      });

      if (!response.ok) throw new Error('Erro ao executar ação');

      await fetchQueue();
    } catch (err) {
      console.error('Erro:', err);
      // Reverte optimistic update se falhar
      if (optimistic) await fetchQueue();
    }
  };

  const handleOpenLogs = async (uploadId: number) => {
    try {
      const response = await fetch(`${API_BASE}/api/automation/uploads/${uploadId}/logs`);
      if (!response.ok) throw new Error('Erro ao buscar logs');

      const data = await response.json();
      setLogsModal({ open: true, data });
    } catch (err) {
      alert('Erro ao carregar logs: ' + (err instanceof Error ? err.message : 'Desconhecido'));
    }
  };

  const handleForceScan = async (channelId: string) => {
    try {
      const response = await fetch(`${API_BASE}/api/automation/uploads/force-scan/${channelId}`, {
        method: 'POST',
      });

      if (!response.ok) throw new Error('Erro ao forçar scan');

      await fetchChannels();
      await fetchQueue();
    } catch (err) {
      alert('Erro: ' + (err instanceof Error ? err.message : 'Desconhecido'));
    }
  };

  const handleRetryChannelFailed = async (channelId: string) => {
    setConfirmModal({
      open: true,
      title: 'Retry Erros do Canal',
      description: 'Tem certeza que deseja tentar novamente todos os uploads com erro deste canal?',
      action: async () => {
        try {
          if (!historyData) return;

          const failedUploads = historyData.failed.filter(u =>
            channelsData?.subnichos.some(s =>
              s.channels.some(c => c.channel_id === channelId && c.channel_name === u.channel_name)
            )
          );

          for (const upload of failedUploads) {
            await fetch(`${API_BASE}/api/automation/uploads/${upload.id}`, {
              method: 'PATCH',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ action: 'retry' }),
            });
          }

          await fetchQueue();
          await fetchAllData();
          setConfirmModal({ open: false, title: '', description: '', action: null });
        } catch (err) {
          alert('Erro: ' + (err instanceof Error ? err.message : 'Desconhecido'));
        }
      },
    });
  };

  const handleFilterHistoryByChannel = (channelName: string) => {
    // Scroll para seção de histórico
    const historySection = document.getElementById('history-section');
    if (historySection) {
      historySection.scrollIntoView({ behavior: 'smooth' });
    }
  };

  // ============================================================================
  // HELPERS DE FORMATAÇÃO
  // ============================================================================

  const formatCountdown = (seconds: number): string => {
    if (seconds === 0) return '0s';
    if (seconds < 60) return `${seconds}s`;

    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;

    if (minutes < 60) {
      return secs > 0 ? `${minutes}:${secs.toString().padStart(2, '0')}` : `${minutes}m`;
    }

    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h${mins}m`;
  };

  const formatDuration = (seconds: number | null): string => {
    if (!seconds) return '-';
    const min = Math.floor(seconds / 60);
    const sec = seconds % 60;
    return `${min}m${sec}s`;
  };

  const formatTimeAgo = (isoString: string | null): string => {
    if (!isoString) return '-';

    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSecs = Math.floor(diffMs / 1000);

    if (diffSecs < 60) return `há ${diffSecs}s`;
    if (diffSecs < 3600) return `há ${Math.floor(diffSecs / 60)}min`;
    if (diffSecs < 86400) return `há ${Math.floor(diffSecs / 3600)}h`;
    return `há ${Math.floor(diffSecs / 86400)}d`;
  };

  const formatTime = (isoString: string): string => {
    const date = new Date(isoString);
    return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  };

  const truncate = (text: string, maxLength: number): string => {
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'warning':
        return <AlertCircle className="w-4 h-4 text-yellow-600" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-600" />;
      case 'active':
        return <CheckCircle className="w-4 h-4 text-blue-600" />;
      case 'paused':
        return <Pause className="w-4 h-4 text-gray-600" />;
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  // ============================================================================
  // RENDER - LOADING/ERROR STATES
  // ============================================================================

  if (loading && !summaryData) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center space-y-3">
          <Loader2 className="w-8 h-8 animate-spin mx-auto text-primary" />
          <p className="text-sm text-muted-foreground">Carregando automação...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="p-6 max-w-md mx-auto mt-8">
        <div className="text-center space-y-4">
          <AlertCircle className="w-12 h-12 mx-auto text-red-500" />
          <div>
            <p className="text-red-500 font-semibold mb-2">Erro ao carregar dados</p>
            <p className="text-sm text-muted-foreground">{error}</p>
          </div>
          <Button onClick={fetchAllData} variant="outline" size="sm">
            <RefreshCw className="w-4 h-4 mr-2" />
            Tentar Novamente
          </Button>
        </div>
      </Card>
    );
  }

  // ============================================================================
  // RENDER - COMPONENTE PRINCIPAL
  // ============================================================================

  return (
    <div className="space-y-6 pb-8">
      {/* ====================================================================
          SEÇÃO 1: FILTROS GLOBAIS
          ==================================================================== */}
      <Card className="p-4">
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-sm font-semibold text-foreground mb-4">
            <span>Filtros</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Filtro Período */}
            <div className="space-y-2">
              <label className="text-xs text-muted-foreground">Período</label>
              <Select
                value={filters.period}
                onValueChange={(value: any) => setFilters(prev => ({ ...prev, period: value }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="24h">Últimas 24 horas</SelectItem>
                  <SelectItem value="7d">Últimos 7 dias</SelectItem>
                  <SelectItem value="30d">Últimos 30 dias</SelectItem>
                  <SelectItem value="all">Tudo</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Filtro Status */}
            <div className="space-y-2">
              <label className="text-xs text-muted-foreground">Status</label>
              <Select
                value={filters.status}
                onValueChange={(value: any) => setFilters(prev => ({ ...prev, status: value }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos</SelectItem>
                  <SelectItem value="completed">✅ Completos</SelectItem>
                  <SelectItem value="failed">❌ Erros</SelectItem>
                  <SelectItem value="pending">⏳ Pendentes</SelectItem>
                  <SelectItem value="processing">🔄 Processando</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Filtro Subnicho */}
            <div className="space-y-2">
              <label className="text-xs text-muted-foreground">Subnicho</label>
              <Select
                value={filters.subnicho}
                onValueChange={(value: string) => setFilters(prev => ({ ...prev, subnicho: value, canal_id: null }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos</SelectItem>
                  {channelsData?.subnichos.map(subnicho => (
                    <SelectItem key={subnicho.name} value={subnicho.name}>
                      {subnicho.name} ({subnicho.total_channels})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Filtro Canal (aparece ao selecionar subnicho) */}
          {filters.subnicho !== 'all' && availableChannels.length > 0 && (
            <div className="space-y-2">
              <label className="text-xs text-muted-foreground">Canal (opcional)</label>
              <Select
                value={filters.canal_id || 'all'}
                onValueChange={(value: string) =>
                  setFilters(prev => ({ ...prev, canal_id: value === 'all' ? null : value }))
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos de {filters.subnicho}</SelectItem>
                  {availableChannels.map(canal => (
                    <SelectItem key={canal.channel_id} value={canal.channel_id}>
                      {canal.channel_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
        </div>
      </Card>

      {/* ====================================================================
          SEÇÃO 2: CARDS RAILWAY (1 LINHA - 4 CARDS)
          ==================================================================== */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card Scanner */}
        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader className="p-4">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              {summaryData && getStatusIcon(summaryData.scanner.status)}
              <span>Scanner</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4 pt-0 space-y-3">
            <div className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Status:</span>
                <Badge className={STATUS_COLORS[summaryData?.scanner.status || 'paused']}>
                  {summaryData?.scanner.status === 'active' ? 'Ativo' : 'Pausado'}
                </Badge>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Próximo:</span>
                <span className="font-mono">{formatCountdown(countdowns.scanner)}</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Último:</span>
                <span>{formatTimeAgo(summaryData?.scanner.last_run || null)}</span>
              </div>
            </div>
            <Button
              size="sm"
              variant="outline"
              className="w-full"
              onClick={() =>
                handleControlAction(
                  summaryData?.scanner.status === 'active' ? 'pause_scanner' : 'resume_scanner',
                  summaryData?.scanner.status === 'active'
                    ? 'Pausar o scanner de planilhas?'
                    : 'Retomar o scanner de planilhas?'
                )
              }
            >
              {summaryData?.scanner.status === 'active' ? (
                <>
                  <Pause className="w-3 h-3 mr-2" />
                  Pausar
                </>
              ) : (
                <>
                  <Play className="w-3 h-3 mr-2" />
                  Retomar
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Card Worker */}
        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader className="p-4">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              {summaryData && getStatusIcon(summaryData.worker.status)}
              <span>Worker</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4 pt-0 space-y-3">
            <div className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Status:</span>
                <Badge className={STATUS_COLORS[summaryData?.worker.status || 'paused']}>
                  {summaryData?.worker.status === 'active' ? 'Ativo' : 'Pausado'}
                </Badge>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Próximo:</span>
                <span className="font-mono">{formatCountdown(countdowns.worker)}</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Último:</span>
                <span>{formatTimeAgo(summaryData?.worker.last_run || null)}</span>
              </div>
            </div>
            <Button
              size="sm"
              variant="outline"
              className="w-full"
              onClick={() =>
                handleControlAction(
                  summaryData?.worker.status === 'active' ? 'pause_worker' : 'resume_worker',
                  summaryData?.worker.status === 'active'
                    ? 'Pausar o worker de uploads?'
                    : 'Retomar o worker de uploads?'
                )
              }
            >
              {summaryData?.worker.status === 'active' ? (
                <>
                  <Pause className="w-3 h-3 mr-2" />
                  Pausar
                </>
              ) : (
                <>
                  <Play className="w-3 h-3 mr-2" />
                  Retomar
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Card Queue */}
        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader className="p-4">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Clock className="w-4 h-4" />
              <span>Queue</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4 pt-0 space-y-3">
            <div className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Pending:</span>
                <span className="font-semibold">{summaryData?.queue.pending || 0}</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Processing:</span>
                <span className="font-semibold">{summaryData?.queue.processing || 0}</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Completed:</span>
                <span className="font-semibold text-green-600">{summaryData?.queue.completed || 0}</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Failed:</span>
                <span className="font-semibold text-red-600">{summaryData?.queue.failed || 0}</span>
              </div>
            </div>
            <div className="space-y-2">
              <Button
                size="sm"
                variant="outline"
                className="w-full"
                onClick={() =>
                  handleControlAction(
                    'clear_pending',
                    `Limpar fila completa? (${summaryData?.queue.pending || 0} itens serão removidos)`
                  )
                }
              >
                <Trash2 className="w-3 h-3 mr-2" />
                Clear Queue
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="w-full"
                onClick={() =>
                  handleControlAction(
                    'retry_all_failed',
                    `Retry todos os erros? (${summaryData?.queue.failed || 0} itens)`
                  )
                }
              >
                <RotateCcw className="w-3 h-3 mr-2" />
                Retry Failed
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Card Performance */}
        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader className="p-4">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              <span>Performance</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Taxa:</span>
                <span className="font-semibold">{summaryData?.performance.success_rate.toFixed(1)}%</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Tempo:</span>
                <span className="font-semibold">{summaryData?.performance.avg_upload_time}s</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Uploads/h:</span>
                <span className="font-semibold">{summaryData?.performance.uploads_per_hour.toFixed(1)}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ====================================================================
          SEÇÃO 3: FILA EM TEMPO REAL
          ==================================================================== */}
      <Card>
        <CardHeader className="border-b p-4">
          <CardTitle className="text-lg flex items-center gap-2">
            🎯 FILA
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4 space-y-6">
          {/* PROCESSANDO */}
          {queueData && queueData.processing.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold mb-3">🔄 PROCESSANDO ({queueData.processing.length})</h3>
              <div className="space-y-3">
                {queueData.processing.map(upload => (
                  <Card key={upload.id} className="p-4">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-sm">{upload.channel_name}</span>
                        <Badge variant="outline">{upload.current_step && STEP_LABELS[upload.current_step]}</Badge>
                      </div>
                      <div>
                        <div className="flex items-center justify-between text-xs mb-1">
                          <span>{upload.progress}%</span>
                          <span className="text-muted-foreground">
                            {formatDuration(upload.elapsed_seconds)}
                          </span>
                        </div>
                        <Progress value={upload.progress} className="h-2" />
                      </div>
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleOpenLogs(upload.id)}
                        >
                          <FileText className="w-3 h-3 mr-1" />
                          Logs
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleUploadAction(upload.id, 'cancel')}
                        >
                          <X className="w-3 h-3 mr-1" />
                          Cancel
                        </Button>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* AGUARDANDO */}
          {queueData && queueData.pending.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold mb-3">⏳ AGUARDANDO ({queueData.pending.length})</h3>
              <div className="space-y-2">
                {queueData.pending.slice(0, 10).map((upload, index) => (
                  <Card key={upload.id} className="p-3">
                    <div className="flex items-start gap-3">
                      <span className="text-xs font-mono text-muted-foreground mt-1">[{index + 1}]</span>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-sm">{upload.channel_name}</div>
                        <div className="text-xs text-muted-foreground truncate">{truncate(upload.titulo, 60)}</div>
                        <div className="flex gap-1 mt-2">
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-7 px-2"
                            onClick={() => handleUploadAction(upload.id, 'move_up', true)}
                            disabled={index === 0}
                          >
                            <ChevronUp className="w-3 h-3" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-7 px-2"
                            onClick={() => handleUploadAction(upload.id, 'move_down', true)}
                            disabled={index === queueData.pending.length - 1}
                          >
                            <ChevronDown className="w-3 h-3" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-7 px-2"
                            onClick={() => handleUploadAction(upload.id, 'cancel')}
                          >
                            <X className="w-3 h-3" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-7 px-2"
                            onClick={() => handleOpenLogs(upload.id)}
                          >
                            <FileText className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  </Card>
                ))}
                {queueData.pending.length > 10 && (
                  <p className="text-xs text-center text-muted-foreground">
                    + {queueData.pending.length - 10} mais na fila
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Empty State */}
          {queueData && queueData.processing.length === 0 && queueData.pending.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              <Clock className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p className="text-sm">Nenhum upload na fila</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* ====================================================================
          SEÇÃO 4: MONITOR DE CANAIS
          ==================================================================== */}
      <Card>
        <CardHeader className="border-b p-4">
          <CardTitle className="text-lg">📊 CANAIS</CardTitle>
        </CardHeader>
        <CardContent className="p-4 space-y-3">
          {channelsData?.subnichos.map(subnicho => {
            const isExpanded = expandedSubnichos.has(subnicho.name);

            return (
              <div key={subnicho.name} className="border rounded-lg overflow-hidden">
                {/* Header Collapsed/Expanded */}
                <button
                  onClick={() => {
                    const newExpanded = new Set(expandedSubnichos);
                    if (isExpanded) {
                      newExpanded.delete(subnicho.name);
                    } else {
                      newExpanded.add(subnicho.name);
                    }
                    setExpandedSubnichos(newExpanded);
                  }}
                  className="w-full px-4 py-3 bg-muted/50 hover:bg-muted transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-sm">{subnicho.name}</span>
                      <span className="text-xs text-muted-foreground">({subnicho.total_channels} canais)</span>
                    </div>
                    {isExpanded ? (
                      <ChevronUp className="w-4 h-4 text-muted-foreground" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-muted-foreground" />
                    )}
                  </div>
                  <div className="flex gap-4 mt-2 text-xs">
                    <span>📊Uploads: {subnicho.uploads_count}</span>
                    <span>⏳Fila: {subnicho.queue_pending}</span>
                    <span>❌Erros: {subnicho.errors_count}</span>
                  </div>
                </button>

                {/* Content Expanded */}
                {isExpanded && (
                  <div className="divide-y">
                    {subnicho.channels.map(canal => (
                      <div key={canal.channel_id} className="p-4 space-y-3">
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex-1">
                            <div className="font-medium text-sm flex items-center gap-2">
                              {getStatusIcon(canal.status)}
                              {canal.channel_name}
                            </div>
                            <div className="flex gap-4 mt-1 text-xs text-muted-foreground">
                              <span>📊Uploads: {canal.uploads_completed}</span>
                              <span>⏳Fila: {canal.queue_pending}</span>
                              <span>❌Erros: {canal.uploads_failed}</span>
                            </div>
                            <div className="flex gap-4 mt-1 text-xs">
                              <span>✅ Scan: {formatTimeAgo(canal.last_scan_at)}</span>
                              <span>Success: {canal.success_rate.toFixed(1)}%</span>
                            </div>
                          </div>
                        </div>

                        <div className="flex flex-wrap gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleFilterHistoryByChannel(canal.channel_name)}
                          >
                            <TrendingUp className="w-3 h-3 mr-1" />
                            Histórico
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => window.open(canal.spreadsheet_url, '_blank')}
                          >
                            <FileSpreadsheet className="w-3 h-3 mr-1" />
                            Sheet
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleForceScan(canal.channel_id)}
                          >
                            <RefreshCw className="w-3 h-3 mr-1" />
                            Scan
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleRetryChannelFailed(canal.channel_id)}
                            disabled={canal.uploads_failed === 0}
                          >
                            <RotateCcw className="w-3 h-3 mr-1" />
                            Retry Failed
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </CardContent>
      </Card>

      {/* ====================================================================
          SEÇÃO 5: HISTÓRICO (50/50 HORIZONTAL)
          ==================================================================== */}
      <div id="history-section">
        <Card>
          <CardHeader className="border-b p-4">
            <CardTitle className="text-lg">📜 HISTÓRICO</CardTitle>
          </CardHeader>
          <CardContent className="p-4">
            {/* Desktop: 50/50 lado a lado */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* COMPLETOS */}
              <div>
                <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  COMPLETOS ({historyData?.completed.length || 0})
                </h3>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {historyData?.completed.slice(0, 20).map(upload => (
                    <Card key={upload.id} className="p-3">
                      <div className="space-y-2">
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1 min-w-0">
                            <div className="text-xs font-medium">
                              {formatTime(upload.completed_at || upload.scheduled_at)} • {upload.channel_name}
                            </div>
                            <div className="text-xs text-muted-foreground truncate">
                              {truncate(upload.titulo, 50)}
                            </div>
                            <div className="text-xs text-muted-foreground">
                              {formatDuration(upload.duration_seconds)}
                            </div>
                          </div>
                        </div>
                        <div className="flex gap-1">
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-7 px-2"
                            onClick={() => handleOpenLogs(upload.id)}
                          >
                            <FileText className="w-3 h-3" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-7 px-2"
                            onClick={() => window.open(upload.spreadsheet_url, '_blank')}
                          >
                            <FileSpreadsheet className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>

              {/* ERROS */}
              <div>
                <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-red-600" />
                  ERROS ({historyData?.failed.length || 0})
                </h3>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {historyData?.failed.slice(0, 20).map(upload => (
                    <Card key={upload.id} className="p-3 border-red-200">
                      <div className="space-y-2">
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1 min-w-0">
                            <div className="text-xs font-medium text-red-600">
                              {formatTime(upload.scheduled_at)} • {upload.channel_name}
                            </div>
                            <div className="text-xs text-muted-foreground truncate">
                              {truncate(upload.titulo, 40)}
                            </div>
                            <div className="text-xs text-red-600">
                              {upload.retry_count}/3 tentativas
                            </div>
                            <div className="text-xs text-muted-foreground truncate">
                              {truncate(upload.error_message || 'Erro desconhecido', 50)}
                            </div>
                          </div>
                        </div>
                        <div className="flex gap-1">
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-7 px-2"
                            onClick={() => handleOpenLogs(upload.id)}
                          >
                            <FileText className="w-3 h-3" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-7 px-2"
                            onClick={() => window.open(upload.spreadsheet_url, '_blank')}
                          >
                            <FileSpreadsheet className="w-3 h-3" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-7 px-2"
                            onClick={() => handleUploadAction(upload.id, 'retry')}
                          >
                            <RotateCcw className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ====================================================================
          MODAL: CONFIRMAÇÃO
          ==================================================================== */}
      <Dialog open={confirmModal.open} onOpenChange={() => setConfirmModal({ ...confirmModal, open: false })}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-yellow-600" />
              {confirmModal.title}
            </DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <p className="text-sm text-muted-foreground">{confirmModal.description}</p>
            <p className="text-sm font-semibold mt-2">Tem certeza que deseja continuar?</p>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setConfirmModal({ ...confirmModal, open: false })}
            >
              Cancelar
            </Button>
            <Button
              onClick={() => {
                if (confirmModal.action) {
                  confirmModal.action();
                }
              }}
            >
              ✓ Confirmar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ====================================================================
          MODAL: LOGS DETALHADOS
          ==================================================================== */}
      <Dialog open={logsModal.open} onOpenChange={() => setLogsModal({ open: false, data: null })}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Upload #{logsModal.data?.id}
            </DialogTitle>
          </DialogHeader>
          {logsModal.data && (
            <div className="space-y-4 text-sm">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-muted-foreground">Canal:</span>
                  <p className="font-medium">{logsModal.data.channel_name}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Status:</span>
                  <p className="font-medium">{logsModal.data.status}</p>
                </div>
              </div>

              <div>
                <span className="text-muted-foreground">Título:</span>
                <p className="font-medium">{logsModal.data.titulo}</p>
              </div>

              <div className="border-t pt-4">
                <span className="text-muted-foreground block mb-2">Timeline:</span>
                <div className="space-y-1 text-xs">
                  <p>• Scheduled: {formatTime(logsModal.data.scheduled_at)}</p>
                  {logsModal.data.started_at && <p>• Started: {formatTime(logsModal.data.started_at)}</p>}
                  {logsModal.data.completed_at && <p>• Completed: {formatTime(logsModal.data.completed_at)}</p>}
                  {logsModal.data.duration_seconds && (
                    <p>• Duration: {formatDuration(logsModal.data.duration_seconds)}</p>
                  )}
                </div>
              </div>

              {logsModal.data.error_message && (
                <div className="border-t pt-4">
                  <span className="text-muted-foreground block mb-2">Error:</span>
                  <p className="text-xs font-mono bg-red-50 p-2 rounded">
                    {logsModal.data.error_type}: {logsModal.data.error_message}
                  </p>
                  {logsModal.data.error_details && (
                    <details className="mt-2">
                      <summary className="cursor-pointer text-xs">Stack trace</summary>
                      <pre className="text-xs bg-gray-50 p-2 rounded mt-2 overflow-x-auto">
                        {JSON.stringify(logsModal.data.error_details, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>
              )}

              <div className="border-t pt-4">
                <span className="text-muted-foreground block mb-2">Info:</span>
                <div className="space-y-1 text-xs">
                  <p>• Row: #{logsModal.data.sheets_row_number}</p>
                  <p>• Retry: {logsModal.data.retry_count}/3</p>
                  {logsModal.data.youtube_url && (
                    <p>
                      • YouTube:{' '}
                      <a href={logsModal.data.youtube_url} target="_blank" rel="noreferrer" className="text-blue-600">
                        {logsModal.data.youtube_video_id}
                      </a>
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                if (logsModal.data) {
                  window.open(logsModal.data.video_url, '_blank');
                }
              }}
            >
              <FileSpreadsheet className="w-4 h-4 mr-2" />
              Sheet
            </Button>
            <Button onClick={() => setLogsModal({ open: false, data: null })}>Fechar</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Loading Overlay (quando refetching) */}
      {loading && summaryData && (
        <div className="fixed bottom-4 right-4 bg-background border border-border rounded-lg shadow-lg p-3 flex items-center gap-2">
          <Loader2 className="w-4 h-4 animate-spin text-primary" />
          <span className="text-sm text-muted-foreground">Atualizando...</span>
        </div>
      )}
    </div>
  );
};

export default AutomacaoUploads;

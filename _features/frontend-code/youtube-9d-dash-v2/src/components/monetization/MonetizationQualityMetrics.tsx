import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { obterCorSubnicho } from '@/utils/subnichoColors';
import { getSubnichoEmoji } from '@/utils/subnichoEmojis';
import { Loader2 } from 'lucide-react';

const API_BASE = 'https://youtube-dashboard-backend-production.up.railway.app';

interface ChannelMetric {
  name: string;
  retention: number | null;
  avg_duration_sec: number | null;
  total_views: number;
  performance: 'good' | 'medium' | 'low';
  language?: string;
}

interface SubnicheMetric {
  name: string;
  channel_count: number;
  avg_retention: number | null;
  performance: 'good' | 'medium' | 'low';
  channels: ChannelMetric[];
}

interface QualityMetricsData {
  period: {
    start: string;
    end: string;
  };
  subnichios: SubnicheMetric[];
}

interface MonetizationQualityMetricsProps {
  month: string | null;
  period: string;
}

const normalizeString = (str: string) => 
  str.toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');

// getSubnichoEmoji now imported from @/utils/subnichoEmojis

const getLanguageFlag = (lingua: string | null | undefined): string => {
  if (!lingua) return '🌐';
  const normalized = lingua.toLowerCase().trim();
  const flagMap: Record<string, string> = {
    'portuguese': '🇧🇷',
    'português': '🇧🇷',
    'portugues': '🇧🇷',
    'pt': '🇧🇷',
    'english': '🇺🇸',
    'en': '🇺🇸',
    'spanish': '🇪🇸',
    'espanhol': '🇪🇸',
    'es': '🇪🇸',
    'german': '🇩🇪',
    'alemão': '🇩🇪',
    'alemao': '🇩🇪',
    'de': '🇩🇪',
    'french': '🇫🇷',
    'francês': '🇫🇷',
    'frances': '🇫🇷',
    'fr': '🇫🇷',
    'italian': '🇮🇹',
    'italiano': '🇮🇹',
    'it': '🇮🇹',
    'russian': '🇷🇺',
    'russo': '🇷🇺',
    'ru': '🇷🇺',
    'polish': '🇵🇱',
    'polonês': '🇵🇱',
    'polones': '🇵🇱',
    'pl': '🇵🇱',
    'turkish': '🇹🇷',
    'turco': '🇹🇷',
    'tr': '🇹🇷',
    'korean': '🇰🇷',
    'coreano': '🇰🇷',
    'ko': '🇰🇷',
    'arabic': '🇸🇦',
    'árabe': '🇸🇦',
    'arabe': '🇸🇦',
    'ar': '🇸🇦',
  };
  return flagMap[normalized] || '🌐';
};

const getRetentionColor = (retention: number | null): string => {
  if (retention === null || retention === undefined) return 'text-muted-foreground';
  if (retention > 40) return 'text-green-500';
  if (retention >= 25) return 'text-yellow-500';
  return 'text-red-500';
};

const getPerformanceBadge = (performance: 'good' | 'medium' | 'low') => {
  const config = {
    good: { label: 'Bom', className: 'bg-green-500/20 text-green-500 border-green-500/30' },
    medium: { label: 'Médio', className: 'bg-yellow-500/20 text-yellow-500 border-yellow-500/30' },
    low: { label: 'Baixo', className: 'bg-red-500/20 text-red-500 border-red-500/30' },
  };
  const { label, className } = config[performance] || config.low;
  return (
    <Badge variant="outline" className={`text-xs ${className}`}>
      {label}
    </Badge>
  );
};

export const MonetizationQualityMetrics: React.FC<MonetizationQualityMetricsProps> = ({ month, period }) => {
  const [data, setData] = useState<QualityMetricsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchQualityMetrics();
  }, [month, period]);

  const fetchQualityMetrics = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (month) {
        params.append('month', month);
      } else if (period) {
        params.append('period', period);
      }
      params.append('_t', Date.now().toString());

      const response = await fetch(`${API_BASE}/api/monetization/quality-metrics?${params}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch quality metrics');
      }
      
      const result = await response.json();
      setData(result);
    } catch (err) {
      console.error('Error fetching quality metrics:', err);
      setError('Erro ao carregar métricas de qualidade');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card className="border-0">
        <CardContent className="p-4 flex items-center justify-center">
          <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
          <span className="ml-2 text-sm text-muted-foreground">Carregando métricas...</span>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="border-0">
        <CardContent className="p-4 text-center text-muted-foreground">
          <p>{error}</p>
        </CardContent>
      </Card>
    );
  }

  if (!data || !data.subnichios || data.subnichios.length === 0) {
    return (
      <Card className="border-0">
        <CardContent className="p-4 sm:p-6 text-center">
          <p className="text-muted-foreground">Nenhum dado de qualidade disponível para este período</p>
          <p className="text-sm mt-2 text-muted-foreground/70">
            As métricas de retenção serão coletadas nos próximos dias
          </p>
        </CardContent>
      </Card>
    );
  }

  const formatPeriod = () => {
    if (!data.period) return '';
    const formatDate = (dateStr: string) => {
      const date = new Date(dateStr + 'T12:00:00');
      return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
    };
    return `${formatDate(data.period.start)} - ${formatDate(data.period.end)}`;
  };

  return (
    <Card className="border-0">
      <CardHeader className="pb-2 px-3 sm:px-4 pt-3 sm:pt-4">
        <CardTitle className="text-sm sm:text-base font-semibold">
          📊 Métricas de Retenção por Subnicho
        </CardTitle>
        {data.period && (
          <p className="text-xs text-muted-foreground mt-1">{formatPeriod()}</p>
        )}
      </CardHeader>
      <CardContent className="p-3 sm:p-4 pt-0 space-y-3">
        {data.subnichios.map((subniche) => {
          const cores = obterCorSubnicho(subniche.name);

          return (
            <div
              key={subniche.name}
              className="rounded-lg p-3 sm:p-4 border"
              style={{
                backgroundColor: cores.fundo + '40',
                borderColor: cores.borda,
              }}
            >
              {/* Header do Subnicho */}
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-lg">{getSubnichoEmoji(subniche.name)}</span>
                  <h4 className="font-semibold text-sm sm:text-base text-foreground">
                    {subniche.name}
                  </h4>
                  {getPerformanceBadge(subniche.performance)}
                </div>
                <Badge
                  variant="secondary"
                  className="text-xs border font-semibold"
                  style={{
                    backgroundColor: `${cores.fundo}40`,
                    color: 'white',
                    borderColor: cores.borda,
                  }}
                >
                  {subniche.channel_count}
                </Badge>
              </div>

              {/* Lista de Canais */}
              <div className="space-y-2">
                {subniche.channels.map((channel, idx) => (
                  <div
                    key={`${subniche.name}-${channel.name}-${idx}`}
                    className="flex flex-col sm:flex-row sm:items-center sm:justify-between py-2 px-3 bg-background/60 rounded-lg gap-2"
                  >
                    {/* Nome do Canal com Bandeira */}
                    <div className="flex items-center gap-2 min-w-0 flex-1">
                      <span className="text-base flex-shrink-0">
                        {getLanguageFlag(channel.language)}
                      </span>
                      <span className="text-sm font-medium truncate">
                        {channel.name}
                      </span>
                    </div>

                    {/* Métricas */}
                    <div className="flex items-center gap-3 text-sm ml-6 sm:ml-0">
                      {/* Retenção */}
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs text-muted-foreground">Retenção:</span>
                        <span className={`font-semibold ${getRetentionColor(channel.retention)}`}>
                          {channel.retention !== null && channel.retention !== undefined
                            ? `${channel.retention.toFixed(1)}%`
                            : '--'}
                        </span>
                      </div>
                      
                      {/* Badge de Performance */}
                      {getPerformanceBadge(channel.performance)}
                    </div>
                  </div>
                ))}
              </div>

              {/* Média do Subnicho */}
              <div 
                className="mt-3 pt-3 border-t rounded-lg p-2"
                style={{ 
                  borderColor: cores.borda + '50',
                  backgroundColor: 'rgba(0,0,0,0.2)'
                }}
              >
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium text-foreground">📊 Retenção média:</span>
                  <span 
                    className={`font-bold text-base px-2 py-0.5 rounded ${
                      subniche.avg_retention !== null && subniche.avg_retention > 40 
                        ? 'bg-green-500/20 text-green-400' 
                        : subniche.avg_retention !== null && subniche.avg_retention >= 25 
                          ? 'bg-yellow-500/20 text-yellow-400' 
                          : 'bg-red-500/20 text-red-400'
                    }`}
                  >
                    {subniche.avg_retention !== null && subniche.avg_retention !== undefined
                      ? `${subniche.avg_retention.toFixed(1)}%`
                      : '--'}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
};

import React, { useState } from 'react';
import { Card } from '@/components/ui/card';
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
import { ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ChannelHistoryModal } from './ChannelHistoryModal';

/**
 * CHANNELS LIST - Lista de Canais Agrupados por Subnicho
 *
 * Features:
 * - Agrupamento por subnicho (collapsible)
 * - Últimos 3 dias visíveis
 * - Badges: 🟢 Real | 🟡 Estimativa
 * - Bandeiras de idioma
 * - Botão "Ver Histórico" → modal
 */

interface ChannelsListProps {
  data: {
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
  };
  loading: boolean;
  typeFilter: 'real_estimate' | 'real_only';
}

const LANGUAGE_FLAGS: { [key: string]: string } = {
  pt: '🇧🇷',
  es: '🇪🇸',
  en: '🇺🇸',
  de: '🇩🇪',
  fr: '🇫🇷',
};

const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
};

const formatNumber = (num: number): string => {
  if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`;
  }
  return num.toLocaleString('pt-BR');
};

const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  const dayBeforeYesterday = new Date(today);
  dayBeforeYesterday.setDate(dayBeforeYesterday.getDate() - 2);

  if (date.toDateString() === today.toDateString()) {
    return 'Hoje';
  } else if (date.toDateString() === yesterday.toDateString()) {
    return 'Ontem';
  } else if (date.toDateString() === dayBeforeYesterday.toDateString()) {
    return 'Anteontem';
  }

  return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
};

interface SubnichoSectionProps {
  subnicho: string;
  channels: ChannelsListProps['data'][string];
  typeFilter: string;
  onOpenHistory: (channelId: string, channelName: string) => void;
}

const SubnichoSection: React.FC<SubnichoSectionProps> = ({
  subnicho,
  channels,
  typeFilter,
  onOpenHistory,
}) => {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="border rounded-lg overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="w-full px-4 py-3 bg-muted/50 hover:bg-muted transition-colors flex items-center justify-between"
      >
        <div className="flex items-center gap-2">
          <span className="font-semibold text-sm">{subnicho}</span>
          <Badge variant="outline" className="text-xs">
            {channels.length} {channels.length === 1 ? 'canal' : 'canais'}
          </Badge>
        </div>
        {collapsed ? (
          <ChevronDown className="w-4 h-4 text-muted-foreground" />
        ) : (
          <ChevronUp className="w-4 h-4 text-muted-foreground" />
        )}
      </button>

      {/* Content */}
      {!collapsed && (
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[200px]">Canal</TableHead>
                <TableHead className="text-center">D-1</TableHead>
                <TableHead className="text-center">D-2</TableHead>
                <TableHead className="text-center">D-3</TableHead>
                <TableHead className="text-center">Ações</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {channels.map((channel) => (
                <TableRow key={channel.channel_id}>
                  {/* Canal Name + Language */}
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <span className="text-lg">
                        {LANGUAGE_FLAGS[channel.language] || '🌐'}
                      </span>
                      <div className="flex flex-col">
                        <span className="font-medium text-sm">
                          {channel.channel_name}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {channel.language.toUpperCase()}
                        </span>
                      </div>
                    </div>
                  </TableCell>

                  {/* Last 3 Days Data */}
                  {[0, 1, 2].map((index) => {
                    const dayData = channel.last_3_days[index];

                    if (!dayData) {
                      return (
                        <TableCell key={index} className="text-center">
                          <span className="text-xs text-muted-foreground">
                            --
                          </span>
                        </TableCell>
                      );
                    }

                    // Skip if typeFilter is real_only and this is an estimate
                    if (typeFilter === 'real_only' && dayData.is_estimate) {
                      return (
                        <TableCell key={index} className="text-center">
                          <span className="text-xs text-muted-foreground">
                            --
                          </span>
                        </TableCell>
                      );
                    }

                    return (
                      <TableCell key={index} className="text-center">
                        <div className="flex flex-col gap-1">
                          {/* Date + Badge */}
                          <div className="flex items-center justify-center gap-1">
                            <span className="text-xs text-muted-foreground">
                              {formatDate(dayData.date)}
                            </span>
                            {dayData.is_estimate ? (
                              <Badge
                                variant="outline"
                                className="text-xs bg-yellow-500/10 text-yellow-600 border-yellow-500/20"
                              >
                                Est
                              </Badge>
                            ) : (
                              <Badge
                                variant="outline"
                                className="text-xs bg-green-500/10 text-green-600 border-green-500/20"
                              >
                                Real
                              </Badge>
                            )}
                          </div>

                          {/* Revenue */}
                          <span className="text-sm font-semibold">
                            {formatCurrency(dayData.revenue)}
                          </span>

                          {/* Views + RPM */}
                          <div className="text-xs text-muted-foreground space-y-0.5">
                            <div>{formatNumber(dayData.views)} views</div>
                            <div>RPM {formatCurrency(dayData.rpm)}</div>
                          </div>
                        </div>
                      </TableCell>
                    );
                  })}

                  {/* Actions */}
                  <TableCell className="text-center">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() =>
                        onOpenHistory(channel.channel_id, channel.channel_name)
                      }
                      className="text-xs"
                    >
                      <ExternalLink className="w-3 h-3 mr-1" />
                      Ver Histórico
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
};

export const ChannelsList: React.FC<ChannelsListProps> = ({
  data,
  loading,
  typeFilter,
}) => {
  const [historyModal, setHistoryModal] = useState<{
    open: boolean;
    channelId: string;
    channelName: string;
  }>({
    open: false,
    channelId: '',
    channelName: '',
  });

  const handleOpenHistory = (channelId: string, channelName: string) => {
    setHistoryModal({ open: true, channelId, channelName });
  };

  const handleCloseHistory = () => {
    setHistoryModal({ open: false, channelId: '', channelName: '' });
  };

  if (loading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-muted rounded w-48" />
          <div className="h-32 bg-muted rounded" />
          <div className="h-32 bg-muted rounded" />
        </div>
      </Card>
    );
  }

  const subnichos = Object.keys(data).sort();

  if (subnichos.length === 0) {
    return (
      <Card className="p-8 text-center">
        <p className="text-muted-foreground">
          Nenhum canal encontrado com os filtros selecionados.
        </p>
      </Card>
    );
  }

  return (
    <>
      <Card className="p-6">
        <div className="space-y-4">
          {/* Header */}
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Canais Monetizados</h3>
            <Badge variant="outline">
              {subnichos.reduce((acc, s) => acc + data[s].length, 0)} canais
            </Badge>
          </div>

          {/* Subnicho Sections */}
          <div className="space-y-3">
            {subnichos.map((subnicho) => (
              <SubnichoSection
                key={subnicho}
                subnicho={subnicho}
                channels={data[subnicho]}
                typeFilter={typeFilter}
                onOpenHistory={handleOpenHistory}
              />
            ))}
          </div>
        </div>
      </Card>

      {/* History Modal */}
      <ChannelHistoryModal
        open={historyModal.open}
        channelId={historyModal.channelId}
        channelName={historyModal.channelName}
        onClose={handleCloseHistory}
      />
    </>
  );
};

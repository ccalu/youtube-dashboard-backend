import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ChevronDown, ChevronUp, DollarSign } from 'lucide-react';
import { MonetizationChannelHistoryModal } from './MonetizationChannelHistoryModal';
import { obterCorSubnicho } from '@/utils/subnichoColors';
import { getSubnichoEmoji } from '@/utils/subnichoEmojis';

interface PeriodTotal {
  revenue: number;
  views: number;
  rpm: number;
  last_update: string;
  last_update_formatted: string;
  badge: 'real' | 'estimate';
}

interface Channel {
  channel_id: string;
  name: string;
  subnicho?: string;
  language: string;
  period_total: PeriodTotal;
}

interface SubnichoGroup {
  name: string;
  color: string;
  channels: Channel[];
}

interface ChannelsListProps {
  data: {
    subnichos: SubnichoGroup[];
  };
  loading: boolean;
  typeFilter: 'real_estimate' | 'real_only';
  month: string | null;
  period: string;
}

const LANGUAGE_FLAGS: { [key: string]: string } = {
  pt: '🇧🇷',
  es: '🇪🇸',
  en: '🇺🇸',
  de: '🇩🇪',
  fr: '🇫🇷',
  ko: '🇰🇷',
  ar: '🇸🇦',
  ja: '🇯🇵',
  portuguese: '🇧🇷',
  português: '🇧🇷',
  english: '🇺🇸',
  ingles: '🇺🇸',
  inglês: '🇺🇸',
  spanish: '🇪🇸',
  espanhol: '🇪🇸',
  german: '🇩🇪',
  alemão: '🇩🇪',
  french: '🇫🇷',
  francês: '🇫🇷',
  korean: '🇰🇷',
  coreano: '🇰🇷',
  arabic: '🇸🇦',
  árabe: '🇸🇦',
  arabe: '🇸🇦',
  japanese: '🇯🇵',
  japones: '🇯🇵',
  japonês: '🇯🇵',
};

const normalizeString = (str: string) =>
  str.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');

const SUBNICHE_ORDER = [
  'historias sombrias',
  'relatos de guerra',
  'terror',
  'historias aleatorias',
  'contos familiares',
  'stickman',
  'misterios',
  'desmonetizado', // Sempre por último
];

// getSubnichoEmoji now imported from @/utils/subnichoEmojis

const getLanguageFlag = (language: string): string => {
  const normalized = language.toLowerCase().trim();
  return LANGUAGE_FLAGS[normalized] || '🌐';
};

const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value || 0);
};

const formatNumber = (num: number): string => {
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`;
  }
  if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`;
  }
  return num.toLocaleString('pt-BR');
};

interface SubnichoSectionProps {
  subnichoGroup: SubnichoGroup;
  typeFilter: string;
  onOpenHistory: (channelId: string, channelName: string) => void;
  animationDelay?: number;
}

const SubnichoSection: React.FC<SubnichoSectionProps> = ({
  subnichoGroup,
  typeFilter,
  onOpenHistory,
  animationDelay = 0,
}) => {
  const [collapsed, setCollapsed] = useState(true);
  const cores = obterCorSubnicho(subnichoGroup.name);
  const color = cores.fundo;
  const emoji = getSubnichoEmoji(subnichoGroup.name);

  // Filter channels based on typeFilter and calculate totals
  const filteredChannels = subnichoGroup.channels.filter(channel => {
    if (!channel.period_total) return false;
    if (typeFilter === 'real_only' && channel.period_total.badge === 'estimate') return false;
    return true;
  });

  const totalRevenue = filteredChannels.reduce(
    (acc, channel) => acc + (channel.period_total?.revenue || 0),
    0
  );

  const totalViews = filteredChannels.reduce(
    (acc, channel) => acc + (channel.period_total?.views || 0),
    0
  );

  // Get latest update date from channels
  const latestUpdate = filteredChannels.reduce((latest, channel) => {
    const channelDate = channel.period_total?.last_update_formatted;
    return channelDate || latest;
  }, '');

  // Sort channels by revenue descending
  const sortedChannels = [...filteredChannels].sort(
    (a, b) => (b.period_total?.revenue || 0) - (a.period_total?.revenue || 0)
  );

  if (sortedChannels.length === 0) return null;

  return (
    <Card 
      className="overflow-hidden bg-card border-border opacity-0 animate-fade-in-up"
      style={{ animationDelay: `${animationDelay}ms` }}
    >
      <CardHeader
        className="border-b-2 p-3 sm:p-4 cursor-pointer"
        style={{
          backgroundColor: `${color}15`,
          borderBottomColor: color,
        }}
        onClick={() => setCollapsed(!collapsed)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 sm:gap-3">
            <span className="text-base sm:text-xl flex-shrink-0">{emoji}</span>
            <CardTitle className="text-base sm:text-lg truncate">{subnichoGroup.name}</CardTitle>
            <Badge
              variant="secondary"
              className="text-xs border"
              style={{
                backgroundColor: `${color}25`,
                color: color,
                borderColor: color,
              }}
            >
              {sortedChannels.length} {sortedChannels.length === 1 ? 'canal' : 'canais'}
            </Badge>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-green-600 hidden sm:block">
              {formatCurrency(totalRevenue)}
            </span>
            {collapsed ? (
              <ChevronDown className="w-5 h-5 text-muted-foreground" />
            ) : (
              <ChevronUp className="w-5 h-5 text-muted-foreground" />
            )}
          </div>
        </div>
      </CardHeader>

      {!collapsed && (
        <CardContent className="p-0">
          {/* Mobile summary row */}
          <div 
            className="sm:hidden p-3 border-b border-border"
            style={{ backgroundColor: `${color}10` }}
          >
            <div className="grid grid-cols-3 gap-2 text-center">
              <div>
                <div className="text-[10px] text-muted-foreground font-medium">Data</div>
                <div className="text-xs font-semibold text-foreground">{latestUpdate || 'N/A'}</div>
              </div>
              <div>
                <div className="text-[10px] text-muted-foreground font-medium">Views Total</div>
                <div className="text-xs font-semibold text-foreground">{formatNumber(totalViews)}</div>
              </div>
              <div>
                <div className="text-[10px] text-muted-foreground font-medium">Revenue Total</div>
                <div className="text-xs font-semibold text-green-600">{formatCurrency(totalRevenue)}</div>
              </div>
            </div>
          </div>
          
          <div className="p-2 sm:p-3 flex flex-col gap-3">
            {sortedChannels.map((channel, index) => {
              const pt = channel.period_total;
              
              return (
                <div
                  key={channel.channel_id}
                  className="p-3 sm:p-4 hover:bg-muted/50 transition-colors rounded-lg border-2"
                  style={{
                    borderColor: `${color}50`,
                    backgroundColor: `${color}08`,
                  }}
                >
                  {/* Top row: position, name, total revenue, button */}
                  <div className="flex items-center gap-2 sm:gap-3">
                    {/* Position number */}
                    <div
                      className="w-6 h-6 sm:w-7 sm:h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
                      style={{
                        backgroundColor: `${color}20`,
                        color: color,
                        border: `2px solid ${color}`,
                      }}
                    >
                      {index + 1}
                    </div>

                    {/* Channel name and language */}
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-sm sm:text-base text-foreground flex items-center gap-2">
                        <span className="text-base sm:text-lg">{getLanguageFlag(channel.language)}</span>
                        <span className="truncate">{channel.name}</span>
                      </div>
                    </div>

                    {/* Total Revenue */}
                    <div
                      className="flex items-center px-2 sm:px-3 py-1 rounded-md"
                      style={{
                        backgroundColor: 'hsl(142.1 76.2% 36.3% / 0.15)',
                      }}
                    >
                      <span className="text-xs sm:text-sm font-semibold text-green-600">
                        {formatCurrency(pt?.revenue || 0)}
                      </span>
                    </div>

                    {/* History button */}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onOpenHistory(channel.channel_id, channel.name)}
                      className="w-8 h-8 p-0 flex items-center justify-center flex-shrink-0 hover:bg-primary/10"
                      title="Ver Histórico"
                    >
                      <span className="text-base">📅</span>
                    </Button>
                  </div>

                  {/* Bottom row: period summary */}
                  {pt && (
                    <div className="mt-3 ml-8 sm:ml-10">
                      <div className="grid grid-cols-4 gap-2 sm:gap-4 text-[10px] sm:text-xs">
                        {/* Last Update */}
                        <div>
                          <div className="font-semibold text-muted-foreground mb-0.5">Dia</div>
                          <div className="text-foreground font-medium">{pt.last_update_formatted || 'N/A'}</div>
                        </div>
                        
                        {/* Views */}
                        <div>
                          <div className="font-semibold text-muted-foreground mb-0.5">Views</div>
                          <div className="text-foreground font-medium">{formatNumber(pt.views)}</div>
                        </div>
                        
                        {/* RPM */}
                        <div>
                          <div className="font-semibold text-muted-foreground mb-0.5">RPM</div>
                          <div className="text-yellow-600 font-medium">${(pt.rpm || 0).toFixed(2)}</div>
                        </div>
                        
                        {/* Badge */}
                        <div>
                          <div className="font-semibold text-muted-foreground mb-0.5">Status</div>
                          <Badge
                            variant={pt.badge === 'real' ? 'default' : 'secondary'}
                            className="text-[9px] sm:text-[10px] px-1.5 py-0"
                          >
                            {pt.badge === 'real' ? 'Real' : 'Estimado'}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      )}
    </Card>
  );
};

export const MonetizationChannelsList: React.FC<ChannelsListProps> = ({
  data,
  loading,
  typeFilter,
  month,
  period,
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
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="p-6">
            <div className="animate-pulse space-y-4">
              <div className="h-6 bg-muted rounded w-48" />
              <div className="h-16 bg-muted rounded" />
              <div className="h-16 bg-muted rounded" />
            </div>
          </Card>
        ))}
      </div>
    );
  }

  const subnichos = data?.subnichos || [];

  // Filter channels based on typeFilter before counting
  const filteredSubnichos = subnichos.map(s => ({
    ...s,
    channels: s.channels.filter(c => {
      if (!c.period_total) return false;
      if (typeFilter === 'real_only' && c.period_total.badge === 'estimate') return false;
      return true;
    })
  })).filter(s => s.channels.length > 0);

  const totalChannels = filteredSubnichos.reduce((acc, s) => acc + s.channels.length, 0);

  if (filteredSubnichos.length === 0) {
    return (
      <Card className="p-8 text-center">
        <p className="text-muted-foreground">
          Nenhum canal encontrado com os filtros selecionados.
        </p>
      </Card>
    );
  }

  // Sort subnichos by fixed order
  const sortedSubnichos = [...filteredSubnichos].sort((a, b) => {
    const normalizedA = normalizeString(a.name);
    const normalizedB = normalizeString(b.name);
    const indexA = SUBNICHE_ORDER.findIndex(s => normalizeString(s) === normalizedA);
    const indexB = SUBNICHE_ORDER.findIndex(s => normalizeString(s) === normalizedB);
    if (indexA === -1 && indexB === -1) return 0;
    if (indexA === -1) return 1;
    if (indexB === -1) return -1;
    return indexA - indexB;
  });

  // Calculate grand total revenue
  const grandTotalRevenue = sortedSubnichos.reduce((acc, subnichoGroup) => {
    return acc + subnichoGroup.channels.reduce((channelAcc, channel) => {
      return channelAcc + (channel.period_total?.revenue || 0);
    }, 0);
  }, 0);

  return (
    <>
      {/* Header card */}
      <Card className="bg-card border-border mb-4">
        <CardHeader className="p-3 sm:p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <DollarSign className="w-4 h-4 sm:w-5 sm:h-5 text-green-600" />
              <CardTitle className="text-sm sm:text-base">Canais Monetizados</CardTitle>
            </div>
            {/* Mobile: stacked badges on right */}
            <div className="sm:hidden flex flex-col items-end gap-0.5">
              <Badge variant="secondary" className="text-[10px]">
                {totalChannels} canais
              </Badge>
              <Badge variant="secondary" className="text-[10px]">
                {sortedSubnichos.length} subnichos
              </Badge>
            </div>
            {/* Desktop: inline badges only */}
            <div className="hidden sm:flex items-center gap-2">
              <Badge variant="secondary" className="text-xs">
                {totalChannels} canais
              </Badge>
              <Badge variant="secondary" className="text-xs">
                {sortedSubnichos.length} subnichos
              </Badge>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Subniche groups */}
      <div className="space-y-4">
        {sortedSubnichos.map((subnichoGroup, index) => (
          <SubnichoSection
            key={subnichoGroup.name}
            subnichoGroup={subnichoGroup}
            typeFilter={typeFilter}
            onOpenHistory={handleOpenHistory}
            animationDelay={index * 60}
          />
        ))}
      </div>

      <MonetizationChannelHistoryModal
        open={historyModal.open}
        channelId={historyModal.channelId}
        channelName={historyModal.channelName}
        onClose={handleCloseHistory}
        month={month}
        period={period}
      />
    </>
  );
};

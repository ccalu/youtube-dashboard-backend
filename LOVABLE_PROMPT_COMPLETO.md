# 🎯 PROMPT COMPLETO - INTEGRAÇÃO ABA MONETIZAÇÃO

**Data:** 10/12/2025
**Status:** Sistema 100% funcional - Pronto para integração

---

## 📋 CONTEXTO

Você precisa integrar uma nova aba "Monetização" no dashboard YouTube existente no Lovable. O backend está **100% pronto e funcional** no Railway. Você só precisa criar os componentes React e integrar na estrutura existente.

---

## 🌐 BACKEND - INFORMAÇÕES

**Base URL (Produção):**
```
https://youtube-dashboard-backend-production.up.railway.app
```

**8 Endpoints REST disponíveis:**

1. `GET /api/monetization/config` - Lista canais monetizados
2. `GET /api/monetization/summary` - Cards principais (total canais, média diária, RPM, revenue)
3. `GET /api/monetization/channels` - Lista de canais agrupados por subnicho (últimos 3 dias)
4. `GET /api/monetization/analytics` - Analytics (projeções, melhores/piores dias, etc)
5. `GET /api/monetization/top-performers` - Top 3 canais (por RPM e por Revenue)
6. `GET /api/monetization/by-language` - Dados agrupados por idioma
7. `GET /api/monetization/by-subnicho` - Dados agrupados por subnicho
8. `GET /api/monetization/channel/:channelId/history` - Histórico completo de um canal

**Query Parameters (todos os endpoints suportam):**
- `period`: "24h" | "3d" | "7d" | "15d" | "30d" | "total" (padrão: "7d")
- `language`: "pt" | "es" | "en" | "de" | "fr" | "all" (padrão: "all")
- `subnicho`: string (opcional)
- `type_filter`: "real_estimate" | "real_only" (padrão: "real_estimate")

---

## 📦 COMPONENTES REACT - CÓDIGO COMPLETO

### 1. MonetizationTab.tsx (Container Principal)

```typescript
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
```

---

### 2. FilterBar.tsx (Barra de Filtros)

```typescript
import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Calendar, Globe, Tag, Filter } from 'lucide-react';

/**
 * FILTER BAR - Barra de Filtros Globais
 *
 * Controles:
 * 1. Período: 24h | 3d | 7d | 15d | 30d | Total
 * 2. Idioma: Todos | PT | ES | EN | DE | FR
 * 3. Subnicho: Dropdown dinâmico (busca do backend)
 * 4. Toggle: Real + Estimativa | Somente Real
 */

interface FilterBarProps {
  filters: {
    period: '24h' | '3d' | '7d' | '15d' | '30d' | 'total';
    language: 'all' | 'pt' | 'es' | 'en' | 'de' | 'fr';
    subnicho: string | null;
    typeFilter: 'real_estimate' | 'real_only';
  };
  onFilterChange: (filters: Partial<FilterBarProps['filters']>) => void;
  loading?: boolean;
}

interface SubnichoOption {
  label: string;
  value: string;
}

const API_BASE = 'https://youtube-dashboard-backend-production.up.railway.app';

const PERIOD_OPTIONS = [
  { label: 'Últimas 24h', value: '24h' },
  { label: 'Últimos 3 dias', value: '3d' },
  { label: 'Últimos 7 dias', value: '7d' },
  { label: 'Últimos 15 dias', value: '15d' },
  { label: 'Últimos 30 dias', value: '30d' },
  { label: 'Todo Período', value: 'total' },
];

const LANGUAGE_OPTIONS = [
  { label: 'Todos os Idiomas', value: 'all', flag: '🌐' },
  { label: 'Português', value: 'pt', flag: '🇧🇷' },
  { label: 'Espanhol', value: 'es', flag: '🇪🇸' },
  { label: 'Inglês', value: 'en', flag: '🇺🇸' },
  { label: 'Alemão', value: 'de', flag: '🇩🇪' },
  { label: 'Francês', value: 'fr', flag: '🇫🇷' },
];

export const FilterBar: React.FC<FilterBarProps> = ({
  filters,
  onFilterChange,
  loading = false,
}) => {
  const [subnichoOptions, setSubnichoOptions] = useState<SubnichoOption[]>([]);
  const [loadingSubnichos, setLoadingSubnichos] = useState(true);

  // Fetch available subnichos from config endpoint
  useEffect(() => {
    fetchSubnichos();
  }, []);

  const fetchSubnichos = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/monetization/config`);
      if (!response.ok) throw new Error('Erro ao buscar subnichos');

      const data = await response.json();

      // Extract unique subnichos
      const uniqueSubnichos = Array.from(
        new Set(data.channels.map((c: any) => c.subnicho))
      ).sort();

      setSubnichoOptions(
        uniqueSubnichos.map((s: string) => ({
          label: s,
          value: s,
        }))
      );
    } catch (error) {
      console.error('Erro ao buscar subnichos:', error);
    } finally {
      setLoadingSubnichos(false);
    }
  };

  const handlePeriodChange = (value: string) => {
    onFilterChange({ period: value as FilterBarProps['filters']['period'] });
  };

  const handleLanguageChange = (value: string) => {
    onFilterChange({ language: value as FilterBarProps['filters']['language'] });
  };

  const handleSubnichoChange = (value: string) => {
    onFilterChange({ subnicho: value === 'all' ? null : value });
  };

  const handleTypeFilterToggle = (checked: boolean) => {
    onFilterChange({ typeFilter: checked ? 'real_only' : 'real_estimate' });
  };

  return (
    <Card className="p-4">
      <div className="flex flex-col gap-4">
        {/* Header */}
        <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
          <Filter className="w-4 h-4" />
          <span>Filtros</span>
        </div>

        {/* Filters Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Period Filter */}
          <div className="space-y-2">
            <Label className="text-xs text-muted-foreground flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              Período
            </Label>
            <Select value={filters.period} onValueChange={handlePeriodChange}>
              <SelectTrigger disabled={loading}>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {PERIOD_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Language Filter */}
          <div className="space-y-2">
            <Label className="text-xs text-muted-foreground flex items-center gap-1">
              <Globe className="w-3 h-3" />
              Idioma
            </Label>
            <Select value={filters.language} onValueChange={handleLanguageChange}>
              <SelectTrigger disabled={loading}>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {LANGUAGE_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    <span className="flex items-center gap-2">
                      <span>{option.flag}</span>
                      <span>{option.label}</span>
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Subnicho Filter */}
          <div className="space-y-2">
            <Label className="text-xs text-muted-foreground flex items-center gap-1">
              <Tag className="w-3 h-3" />
              Subnicho
            </Label>
            <Select
              value={filters.subnicho || 'all'}
              onValueChange={handleSubnichoChange}
            >
              <SelectTrigger disabled={loading || loadingSubnichos}>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos os Subnichos</SelectItem>
                {subnichoOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Type Filter Toggle */}
          <div className="space-y-2">
            <Label className="text-xs text-muted-foreground">
              Tipo de Dados
            </Label>
            <div className="flex items-center gap-2 h-10 px-3 border border-input rounded-md bg-background">
              <Switch
                id="type-filter"
                checked={filters.typeFilter === 'real_only'}
                onCheckedChange={handleTypeFilterToggle}
                disabled={loading}
              />
              <Label
                htmlFor="type-filter"
                className="text-sm cursor-pointer select-none"
              >
                {filters.typeFilter === 'real_only' ? (
                  <span className="flex items-center gap-1">
                    <span className="text-green-500">●</span>
                    Somente Real
                  </span>
                ) : (
                  <span className="flex items-center gap-1">
                    <span className="text-yellow-500">●</span>
                    Real + Estimativa
                  </span>
                )}
              </Label>
            </div>
          </div>
        </div>

        {/* Active Filters Summary */}
        {(filters.language !== 'all' || filters.subnicho || filters.typeFilter === 'real_only') && (
          <div className="flex items-center gap-2 text-xs">
            <span className="text-muted-foreground">Filtros ativos:</span>
            <div className="flex flex-wrap gap-1">
              {filters.language !== 'all' && (
                <span className="px-2 py-1 bg-primary/10 text-primary rounded">
                  {LANGUAGE_OPTIONS.find(l => l.value === filters.language)?.label}
                </span>
              )}
              {filters.subnicho && (
                <span className="px-2 py-1 bg-primary/10 text-primary rounded">
                  {filters.subnicho}
                </span>
              )}
              {filters.typeFilter === 'real_only' && (
                <span className="px-2 py-1 bg-green-500/10 text-green-600 rounded">
                  Somente dados reais
                </span>
              )}
              <Button
                variant="ghost"
                size="sm"
                onClick={() =>
                  onFilterChange({
                    language: 'all',
                    subnicho: null,
                    typeFilter: 'real_estimate',
                  })
                }
                className="h-6 px-2 text-xs"
              >
                Limpar
              </Button>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};
```

---

### 3. MonetizationCards.tsx (4 Cards Superiores)

```typescript
import React from 'react';
import { Card } from '@/components/ui/card';
import { TrendingUp, TrendingDown, DollarSign, BarChart3, Users, Zap } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * MONETIZATION CARDS - 4 Cards Superiores
 *
 * Cards:
 * 1. Canais Monetizados (total_monetized_channels)
 * 2. Média Diária + Taxa de Crescimento (daily_avg + growth_rate)
 * 3. RPM Médio (rpm_avg)
 * 4. Total Revenue (total_revenue)
 */

interface MonetizationCardsProps {
  data: {
    total_monetized_channels: number;
    daily_avg: {
      views: number;
      revenue: number;
      rpm: number;
    };
    growth_rate: number;
    rpm_avg: number;
    total_revenue: number;
  };
  loading?: boolean;
}

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  trend?: {
    value: number;
    label: string;
  };
  colorClass?: string;
}

const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  trend,
  colorClass = 'text-primary',
}) => {
  const isPositiveTrend = trend && trend.value >= 0;

  return (
    <Card className="p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between">
        <div className="space-y-2 flex-1">
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <p className={cn('text-3xl font-bold', colorClass)}>{value}</p>
          {subtitle && (
            <p className="text-xs text-muted-foreground">{subtitle}</p>
          )}
          {trend && (
            <div className="flex items-center gap-1 text-sm">
              {isPositiveTrend ? (
                <TrendingUp className="w-4 h-4 text-green-500" />
              ) : (
                <TrendingDown className="w-4 h-4 text-red-500" />
              )}
              <span
                className={cn(
                  'font-semibold',
                  isPositiveTrend ? 'text-green-600' : 'text-red-600'
                )}
              >
                {isPositiveTrend ? '+' : ''}
                {trend.value.toFixed(1)}%
              </span>
              <span className="text-muted-foreground text-xs">{trend.label}</span>
            </div>
          )}
        </div>
        <div
          className={cn(
            'p-3 rounded-lg',
            colorClass === 'text-green-600' && 'bg-green-500/10',
            colorClass === 'text-blue-600' && 'bg-blue-500/10',
            colorClass === 'text-purple-600' && 'bg-purple-500/10',
            colorClass === 'text-yellow-600' && 'bg-yellow-500/10',
            colorClass === 'text-primary' && 'bg-primary/10'
          )}
        >
          {icon}
        </div>
      </div>
    </Card>
  );
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

const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
};

export const MonetizationCards: React.FC<MonetizationCardsProps> = ({
  data,
  loading = false,
}) => {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i} className="p-6 animate-pulse">
            <div className="space-y-3">
              <div className="h-4 bg-muted rounded w-24" />
              <div className="h-8 bg-muted rounded w-32" />
              <div className="h-3 bg-muted rounded w-20" />
            </div>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Card 1: Canais Monetizados */}
      <StatCard
        title="Canais Monetizados"
        value={data.total_monetized_channels}
        subtitle="canais ativos"
        icon={<Users className="w-6 h-6 text-blue-600" />}
        colorClass="text-blue-600"
      />

      {/* Card 2: Média Diária + Taxa de Crescimento */}
      <StatCard
        title="Média Diária"
        value={formatCurrency(data.daily_avg.revenue)}
        subtitle={`${formatNumber(data.daily_avg.views)} views · RPM ${formatCurrency(
          data.daily_avg.rpm
        )}`}
        icon={<BarChart3 className="w-6 h-6 text-green-600" />}
        trend={{
          value: data.growth_rate,
          label: 'vs período anterior',
        }}
        colorClass="text-green-600"
      />

      {/* Card 3: RPM Médio */}
      <StatCard
        title="RPM Médio"
        value={formatCurrency(data.rpm_avg)}
        subtitle="revenue por 1.000 views"
        icon={<Zap className="w-6 h-6 text-yellow-600" />}
        colorClass="text-yellow-600"
      />

      {/* Card 4: Total Revenue */}
      <StatCard
        title="Total Revenue"
        value={formatCurrency(data.total_revenue)}
        subtitle="período selecionado"
        icon={<DollarSign className="w-6 h-6 text-purple-600" />}
        colorClass="text-purple-600"
      />
    </div>
  );
};
```

---

### 4. ChannelsList.tsx (Lista de Canais)

**ARQUIVO MUITO GRANDE - Vou colocar no próximo bloco**

```typescript
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
```

---

### 5. ChannelHistoryModal.tsx (Modal Histórico Completo)

```typescript
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
```

---

### 6. AnalyticsCard.tsx (Analytics e Projeções)

```typescript
import React from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { TrendingUp, TrendingDown, Calendar, Eye, Clock } from 'lucide-react';

interface AnalyticsCardProps {
  data: {
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
    avg_retention_pct: number | null;
    avg_ctr: number | null;
    day_of_week_analysis: Array<{
      day_name: string;
      avg_revenue: number;
    }>;
  };
  loading: boolean;
}

const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
};

const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
  });
};

const DAY_NAMES_PT: { [key: string]: string } = {
  Monday: 'Segunda',
  Tuesday: 'Terça',
  Wednesday: 'Quarta',
  Thursday: 'Quinta',
  Friday: 'Sexta',
  Saturday: 'Sábado',
  Sunday: 'Domingo',
};

export const AnalyticsCard: React.FC<AnalyticsCardProps> = ({
  data,
  loading,
}) => {
  if (loading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-muted rounded w-32" />
          <div className="h-24 bg-muted rounded" />
          <div className="h-32 bg-muted rounded" />
        </div>
      </Card>
    );
  }

  const chartData = data.day_of_week_analysis.map((item) => ({
    day: DAY_NAMES_PT[item.day_name] || item.day_name,
    revenue: item.avg_revenue,
  }));

  const maxRevenue = Math.max(...chartData.map((d) => d.revenue));

  return (
    <Card className="p-6">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center gap-2">
          <Calendar className="w-5 h-5 text-primary" />
          <h3 className="text-lg font-semibold">Analytics</h3>
        </div>

        {/* Projections */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-muted-foreground">
            Projeções de Revenue
          </h4>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm">Próximos 7 dias</span>
              <span className="text-sm font-semibold text-blue-600">
                {formatCurrency(data.projections.days_7)}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Próximos 15 dias</span>
              <span className="text-sm font-semibold text-blue-600">
                {formatCurrency(data.projections.days_15)}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Próximos 30 dias</span>
              <span className="text-sm font-semibold text-blue-600">
                {formatCurrency(data.projections.days_30)}
              </span>
            </div>
          </div>
        </div>

        {/* Best/Worst Days */}
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 border border-green-500/20 bg-green-500/5 rounded-lg">
            <div className="flex items-center gap-1 mb-2">
              <TrendingUp className="w-3 h-3 text-green-600" />
              <span className="text-xs text-green-600 font-medium">
                Melhor Dia
              </span>
            </div>
            <p className="text-xs text-muted-foreground mb-1">
              {formatDate(data.best_day.date)}
            </p>
            <p className="text-lg font-bold text-green-600">
              {formatCurrency(data.best_day.revenue)}
            </p>
          </div>

          <div className="p-3 border border-red-500/20 bg-red-500/5 rounded-lg">
            <div className="flex items-center gap-1 mb-2">
              <TrendingDown className="w-3 h-3 text-red-600" />
              <span className="text-xs text-red-600 font-medium">
                Pior Dia
              </span>
            </div>
            <p className="text-xs text-muted-foreground mb-1">
              {formatDate(data.worst_day.date)}
            </p>
            <p className="text-lg font-bold text-red-600">
              {formatCurrency(data.worst_day.revenue)}
            </p>
          </div>
        </div>

        {/* Retention & CTR */}
        {(data.avg_retention_pct !== null || data.avg_ctr !== null) && (
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-muted-foreground">
              Métricas de Engajamento
            </h4>

            {data.avg_retention_pct !== null && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Eye className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm">Retenção Média</span>
                  </div>
                  <span className="text-sm font-semibold">
                    {data.avg_retention_pct.toFixed(1)}%
                  </span>
                </div>
                <Progress value={data.avg_retention_pct} className="h-2" />
              </div>
            )}

            {data.avg_ctr !== null && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm">CTR Médio</span>
                  </div>
                  <span className="text-sm font-semibold">
                    {data.avg_ctr.toFixed(1)}%
                  </span>
                </div>
                <Progress value={data.avg_ctr} className="h-2" />
              </div>
            )}
          </div>
        )}

        {/* Day of Week Analysis */}
        {chartData.length > 0 && (
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-muted-foreground">
              Revenue por Dia da Semana
            </h4>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="day"
                  tick={{ fontSize: 11 }}
                  angle={-45}
                  textAnchor="end"
                  height={60}
                />
                <YAxis tick={{ fontSize: 11 }} tickFormatter={(value) => `$${value}`} />
                <Tooltip
                  formatter={(value: any) => [formatCurrency(value), 'Revenue Médio']}
                  contentStyle={{
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    border: 'none',
                    borderRadius: '8px',
                    color: '#fff',
                  }}
                />
                <Bar
                  dataKey="revenue"
                  fill="#22c55e"
                  radius={[4, 4, 0, 0]}
                  opacity={0.8}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </Card>
  );
};
```

---

### 7. TopPerformersCard.tsx (Top 3 Campeões)

```typescript
import React, { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Trophy, Zap, DollarSign } from 'lucide-react';
import { cn } from '@/lib/utils';

interface TopPerformersCardProps {
  data: {
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
  };
  loading: boolean;
}

const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
};

const MEDALS = ['🥇', '🥈', '🥉'];
const COLORS = [
  'bg-yellow-500/10 border-yellow-500/30 text-yellow-700',
  'bg-gray-400/10 border-gray-400/30 text-gray-700',
  'bg-orange-500/10 border-orange-500/30 text-orange-700',
];

interface PerformerItemProps {
  rank: number;
  channelName: string;
  primaryValue: number;
  primaryLabel: string;
  secondaryValue: number;
  secondaryLabel: string;
}

const PerformerItem: React.FC<PerformerItemProps> = ({
  rank,
  channelName,
  primaryValue,
  primaryLabel,
  secondaryValue,
  secondaryLabel,
}) => {
  const isFirst = rank === 0;

  return (
    <div
      className={cn(
        'p-4 border-2 rounded-lg transition-all hover:scale-105',
        COLORS[rank],
        isFirst && 'ring-2 ring-yellow-500/50 shadow-lg'
      )}
    >
      <div className="flex items-start gap-3">
        <div className="text-3xl">{MEDALS[rank]}</div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <h4
              className={cn(
                'font-semibold truncate',
                isFirst ? 'text-base' : 'text-sm'
              )}
            >
              {channelName}
            </h4>
            {isFirst && (
              <Badge variant="outline" className="text-xs bg-yellow-500/20">
                TOP 1
              </Badge>
            )}
          </div>

          <div className="mb-1">
            <span
              className={cn(
                'font-bold',
                isFirst ? 'text-xl' : 'text-lg'
              )}
            >
              {formatCurrency(primaryValue)}
            </span>
            <span className="text-xs text-muted-foreground ml-2">
              {primaryLabel}
            </span>
          </div>

          <div className="text-xs text-muted-foreground">
            {formatCurrency(secondaryValue)} {secondaryLabel}
          </div>
        </div>
      </div>
    </div>
  );
};

export const TopPerformersCard: React.FC<TopPerformersCardProps> = ({
  data,
  loading,
}) => {
  const [activeTab, setActiveTab] = useState<'rpm' | 'revenue'>('rpm');

  if (loading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-muted rounded w-32" />
          <div className="h-20 bg-muted rounded" />
          <div className="h-20 bg-muted rounded" />
          <div className="h-20 bg-muted rounded" />
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Trophy className="w-5 h-5 text-yellow-600" />
          <h3 className="text-lg font-semibold">Top Performers</h3>
        </div>

        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'rpm' | 'revenue')}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="rpm" className="text-xs">
              <Zap className="w-3 h-3 mr-1" />
              Por RPM
            </TabsTrigger>
            <TabsTrigger value="revenue" className="text-xs">
              <DollarSign className="w-3 h-3 mr-1" />
              Por Revenue
            </TabsTrigger>
          </TabsList>

          <TabsContent value="rpm" className="space-y-3 mt-4">
            {data.top_rpm.slice(0, 3).map((channel, index) => (
              <PerformerItem
                key={channel.channel_id}
                rank={index}
                channelName={channel.channel_name}
                primaryValue={channel.avg_rpm}
                primaryLabel="RPM médio"
                secondaryValue={channel.total_revenue}
                secondaryLabel="revenue total"
              />
            ))}

            {data.top_rpm.length === 0 && (
              <div className="text-center py-8 text-muted-foreground text-sm">
                Sem dados disponíveis para o período selecionado
              </div>
            )}
          </TabsContent>

          <TabsContent value="revenue" className="space-y-3 mt-4">
            {data.top_revenue.slice(0, 3).map((channel, index) => (
              <PerformerItem
                key={channel.channel_id}
                rank={index}
                channelName={channel.channel_name}
                primaryValue={channel.total_revenue}
                primaryLabel="revenue total"
                secondaryValue={channel.avg_rpm}
                secondaryLabel="RPM médio"
              />
            ))}

            {data.top_revenue.length === 0 && (
              <div className="text-center py-8 text-muted-foreground text-sm">
                Sem dados disponíveis para o período selecionado
              </div>
            )}
          </TabsContent>
        </Tabs>

        {data.top_rpm.length > 0 && data.top_revenue.length > 0 && (
          <div className="pt-4 border-t">
            <p className="text-xs text-muted-foreground text-center">
              {data.top_rpm[0].channel_id === data.top_revenue[0].channel_id ? (
                <>
                  <span className="font-semibold text-yellow-600">
                    {data.top_rpm[0].channel_name}
                  </span>{' '}
                  lidera em RPM e Revenue! 🏆
                </>
              ) : (
                <>
                  Maior RPM:{' '}
                  <span className="font-semibold">
                    {data.top_rpm[0].channel_name}
                  </span>{' '}
                  • Maior Revenue:{' '}
                  <span className="font-semibold">
                    {data.top_revenue[0].channel_name}
                  </span>
                </>
              )}
            </p>
          </div>
        )}
      </div>
    </Card>
  );
};
```

---

## 🎯 INSTRUÇÕES DE INTEGRAÇÃO

1. **Criar os 7 componentes:**
   - `MonetizationTab.tsx` (container principal)
   - `FilterBar.tsx`
   - `MonetizationCards.tsx`
   - `ChannelsList.tsx`
   - `ChannelHistoryModal.tsx`
   - `AnalyticsCard.tsx`
   - `TopPerformersCard.tsx`

2. **Adicionar dependências:**
   - `recharts` (já deve estar instalado)
   - Todos os componentes shadcn/ui necessários já devem existir

3. **Integrar no TabBar:**
   - Adicionar nova tab "Monetização" no componente principal
   - Importar `<MonetizationTab />` e renderizar quando ativa

4. **Testar:**
   - Abrir aba Monetização
   - Verificar se os 4 cards carregam
   - Testar filtros (período, idioma, subnicho)
   - Abrir modal de histórico de um canal
   - Verificar responsividade mobile

---

## 📊 DADOS ESPERADOS

- **7 canais monetizados**
- **301 registros históricos** (desde 26/10/2025)
- **Revenue total: $2,043.88**
- **Média diária: $44.43**
- **RPM médio: $1.11**

---

## ✅ CHECKLIST FINAL

- [ ] Todos os 7 componentes criados
- [ ] Tab "Monetização" adicionada
- [ ] Filtros funcionando corretamente
- [ ] Cards exibindo dados
- [ ] Lista de canais agrupada por subnicho
- [ ] Modal de histórico abrindo
- [ ] Gráficos renderizando (Recharts)
- [ ] Responsivo (mobile + desktop)
- [ ] Sem erros no console

---

**IMPORTANTE:** O backend está 100% funcional. Qualquer erro será no frontend. Verifique:
1. URL da API está correta: `https://youtube-dashboard-backend-production.up.railway.app`
2. Todos os componentes shadcn/ui estão instalados
3. Recharts está instalado
4. Imports estão corretos

---

**Data:** 10/12/2025
**Status:** Pronto para implementação!
**Bug do período:** ✅ Corrigido (top-performers agora respeita o filtro de período)


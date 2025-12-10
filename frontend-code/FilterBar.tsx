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

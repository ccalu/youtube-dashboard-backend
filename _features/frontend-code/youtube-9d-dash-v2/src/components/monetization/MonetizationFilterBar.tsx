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
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Calendar, Globe, Tag, Filter, BarChart3 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface FilterBarProps {
  filters: {
    period: '24h' | '3d' | '7d' | '15d' | '30d' | 'total' | 'custom';
    language: 'all' | 'pt' | 'es' | 'en' | 'de' | 'fr';
    subnicho: string | null;
    typeFilter: 'real_estimate' | 'real_only';
    month: string | null;
    customStart?: string | null;
    customEnd?: string | null;
  };
  onFilterChange: (filters: Partial<FilterBarProps['filters']>) => void;
  loading?: boolean;
}

interface SubnichoOption {
  label: string;
  value: string;
}

interface LanguageOption {
  label: string;
  value: string;
  flag: string;
}

const API_BASE = 'https://youtube-dashboard-backend-production.up.railway.app';

const PERIOD_OPTIONS = [
  { label: 'Últimas 24h', value: '24h' },
  { label: 'Últimos 3 dias', value: '3d' },
  { label: 'Últimos 7 dias', value: '7d' },
  { label: 'Últimos 15 dias', value: '15d' },
  { label: 'Últimos 30 dias', value: '30d' },
  { label: 'Todo Período', value: 'total' },
  { label: '📅 Período Customizado', value: 'custom' },
];

const LANGUAGE_FLAGS: { [key: string]: string } = {
  pt: '🇧🇷',
  es: '🇪🇸',
  en: '🇺🇸',
  de: '🇩🇪',
  fr: '🇫🇷',
  ko: '🇰🇷',
  ar: '🇸🇦',
  portuguese: '🇧🇷',
  português: '🇧🇷',
  english: '🇺🇸',
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
};

const LANGUAGE_NAMES: { [key: string]: string } = {
  pt: 'Português',
  es: 'Espanhol',
  en: 'Inglês',
  de: 'Alemão',
  fr: 'Francês',
  portuguese: 'Português',
  português: 'Português',
  english: 'Inglês',
  spanish: 'Espanhol',
  espanhol: 'Espanhol',
  german: 'Alemão',
  alemão: 'Alemão',
  french: 'Francês',
  francês: 'Francês',
};

// Gerar opções de mês (últimos 12 meses)
const generateMonthOptions = () => {
  const months = [];
  const now = new Date();
  for (let i = 0; i < 12; i++) {
    const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const value = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
    const label = date.toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' });
    months.push({ value, label: label.charAt(0).toUpperCase() + label.slice(1) });
  }
  return months;
};

const MONTH_OPTIONS = generateMonthOptions();

export const MonetizationFilterBar: React.FC<FilterBarProps> = ({
  filters,
  onFilterChange,
  loading = false,
}) => {
  const [subnichoOptions, setSubnichoOptions] = useState<SubnichoOption[]>([]);
  const [languageOptions, setLanguageOptions] = useState<LanguageOption[]>([
    { label: 'Todos Idiomas', value: 'all', flag: '' }
  ]);
  const [loadingSubnichos, setLoadingSubnichos] = useState(true);
  const [customPeriodModalOpen, setCustomPeriodModalOpen] = useState(false);
  const [customStart, setCustomStart] = useState('');
  const [customEnd, setCustomEnd] = useState('');

  useEffect(() => {
    fetchSubnichos();
  }, []);

  const fetchSubnichos = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/monetization/config`);
      if (!response.ok) throw new Error('Erro ao buscar configuração');

      const data = await response.json();

      // Extrair subnichos únicos
      const uniqueSubnichos = Array.from(
        new Set(data.channels.map((c: any) => c.subnicho))
      ).sort();

      setSubnichoOptions(
        uniqueSubnichos.map((s: string) => ({
          label: s,
          value: s,
        }))
      );

      // Extrair idiomas únicos
      const uniqueLanguages = Array.from(
        new Set(data.channels.map((c: any) => c.lingua))
      ).sort();

      const languagesWithFlags = uniqueLanguages.map((lang: string) => ({
        label: LANGUAGE_NAMES[lang] || lang.toUpperCase(),
        value: lang,
        flag: LANGUAGE_FLAGS[lang] || '🌐'
      }));

      setLanguageOptions([
        { label: 'Todos Idiomas', value: 'all', flag: '' },
        ...languagesWithFlags
      ]);

    } catch (error) {
    } finally {
      setLoadingSubnichos(false);
    }
  };

  const handlePeriodChange = (value: string) => {
    if (value === 'custom') {
      setCustomPeriodModalOpen(true);
    } else {
      onFilterChange({ 
        period: value as FilterBarProps['filters']['period'],
        customStart: null,
        customEnd: null
      });
    }
  };

  const handleApplyCustomPeriod = () => {
    if (customStart && customEnd) {
      onFilterChange({
        period: 'custom',
        customStart,
        customEnd
      });
      setCustomPeriodModalOpen(false);
    }
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

  const handleMonthChange = (value: string) => {
    if (value === 'all') {
      onFilterChange({ month: null });
    } else {
      onFilterChange({ month: value });
    }
  };

  return (
    <Card className="p-3 border-0 animate-fade-in">
      <div className="flex flex-col gap-3 transition-all duration-300">
        <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
          <Filter className="w-4 h-4" />
          <span>Filtros</span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <div className="space-y-1">
            <Label className="text-xs text-muted-foreground flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              Período
            </Label>
            <Select 
              value={filters.period} 
              onValueChange={handlePeriodChange}
              disabled={loading || !!filters.month}
            >
              <SelectTrigger className={cn("h-9", filters.month && "opacity-50")}>
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

          <div className="space-y-1">
            <Label className="text-xs text-muted-foreground flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              Mês
            </Label>
            <Select 
              value={filters.month || 'all'} 
              onValueChange={handleMonthChange}
              disabled={loading}
            >
              <SelectTrigger className="h-9">
                <SelectValue placeholder="Selecionar mês" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos</SelectItem>
                {MONTH_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1">
            <Label className="text-xs text-muted-foreground flex items-center gap-1">
              <Globe className="w-3 h-3" />
              Idioma
            </Label>
            <Select value={filters.language} onValueChange={handleLanguageChange}>
              <SelectTrigger disabled={loading} className="h-9">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {languageOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    <span className="flex items-center gap-2">
                      {option.flag && <span>{option.flag}</span>}
                      <span>{option.label}</span>
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1">
            <Label className="text-xs text-muted-foreground flex items-center gap-1">
              <Tag className="w-3 h-3" />
              Subnicho
            </Label>
            <Select
              value={filters.subnicho || 'all'}
              onValueChange={handleSubnichoChange}
            >
              <SelectTrigger disabled={loading || loadingSubnichos} className="h-9">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos</SelectItem>
                {subnichoOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1">
            <Label className="text-xs text-muted-foreground flex items-center gap-1">
              <BarChart3 className="w-3 h-3" />
              Dados
            </Label>
            <Button
              variant="outline"
              onClick={() => handleTypeFilterToggle(filters.typeFilter === 'real_estimate')}
              disabled={loading}
              className={cn(
                "w-full justify-start gap-2 h-9 transition-colors",
                filters.typeFilter === 'real_only' 
                  ? "bg-green-500/20 border-green-500/50 hover:bg-green-500/30" 
                  : "bg-yellow-500/20 border-yellow-500/50 hover:bg-yellow-500/30"
              )}
            >
              <div className={cn(
                "w-2 h-2 rounded-full",
                filters.typeFilter === 'real_only' ? "bg-green-500" : "bg-yellow-500"
              )} />
              <span className="text-xs">
                {filters.typeFilter === 'real_only' ? 'Real' : 'Real + Est.'}
              </span>
            </Button>
          </div>
        </div>

        {(filters.language !== 'all' || filters.subnicho || filters.typeFilter === 'real_only' || filters.month) && (
          <div className="flex items-center gap-2 text-xs">
            <span className="text-muted-foreground">Filtros ativos:</span>
            <div className="flex flex-wrap gap-1">
              {filters.month && (
                <span className="px-2 py-1 bg-blue-500/10 text-blue-600 rounded">
                  {MONTH_OPTIONS.find(m => m.value === filters.month)?.label || filters.month}
                </span>
              )}
              {filters.language !== 'all' && (
                <span className="px-2 py-1 bg-primary/10 text-primary rounded">
                  {languageOptions.find(l => l.value === filters.language)?.label}
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
                    month: null,
                  })
                }
                className="h-6 px-2 text-xs"
              >
                Limpar
              </Button>
            </div>
          </div>
        )}

        {filters.period === 'custom' && filters.customStart && filters.customEnd && (
          <div className="flex items-center gap-2 p-3 rounded-lg bg-blue-500/20 border border-blue-500/30">
            <span className="text-xl">📅</span>
            <div className="flex flex-col text-sm">
              <span className="font-medium text-foreground">
                Período customizado: {new Date(filters.customStart + 'T12:00:00').toLocaleDateString('pt-BR')} até {new Date(filters.customEnd + 'T12:00:00').toLocaleDateString('pt-BR')}
              </span>
              <Button
                variant="link"
                size="sm"
                onClick={() => setCustomPeriodModalOpen(true)}
                className="h-auto p-0 text-xs text-blue-400"
              >
                Alterar período
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Modal de período customizado */}
      <Dialog open={customPeriodModalOpen} onOpenChange={setCustomPeriodModalOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Calendar className="w-5 h-5 text-white" />
              Período Customizado
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Data Inicial</Label>
              <Input
                type="date"
                value={customStart}
                onChange={(e) => setCustomStart(e.target.value)}
              />
            </div>
            
            <div className="space-y-2">
              <Label>Data Final</Label>
              <Input
                type="date"
                value={customEnd}
                onChange={(e) => setCustomEnd(e.target.value)}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setCustomPeriodModalOpen(false)}>
              Cancelar
            </Button>
            <Button 
              onClick={handleApplyCustomPeriod}
              disabled={!customStart || !customEnd}
            >
              Aplicar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
};
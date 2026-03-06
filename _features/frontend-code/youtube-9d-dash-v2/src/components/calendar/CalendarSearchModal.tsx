import { useState } from 'react';
import { Search, X } from 'lucide-react';
import { format } from 'date-fns';
import { cn } from '@/lib/utils';
import { calendarApiService } from '@/services/calendarApi';
import {
  CalendarEvent,
  SOCIOS,
  CATEGORIAS,
  getSocioByKey,
  getCategoriaByKey,
  MONTHS_PT,
} from '@/types/calendar';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { Calendar } from '@/components/ui/calendar';
import { CalendarIcon } from 'lucide-react';

interface CalendarSearchModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelectDate: (date: string) => void;
}

export function CalendarSearchModal({ open, onOpenChange, onSelectDate }: CalendarSearchModalProps) {
  const [query, setQuery] = useState('');
  const [selectedAuthors, setSelectedAuthors] = useState<string[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [dateFrom, setDateFrom] = useState<Date | undefined>();
  const [dateTo, setDateTo] = useState<Date | undefined>();
  const [results, setResults] = useState<CalendarEvent[]>([]);
  const [searched, setSearched] = useState(false);
  const [loading, setLoading] = useState(false);

  const toggleAuthor = (key: string) => {
    setSelectedAuthors(prev =>
      prev.includes(key) ? prev.filter(a => a !== key) : [...prev, key]
    );
  };

  const toggleCategory = (key: string) => {
    setSelectedCategories(prev =>
      prev.includes(key) ? prev.filter(c => c !== key) : [...prev, key]
    );
  };

  const handleSearch = async () => {
    setLoading(true);
    setSearched(true);
    try {
      const res = await calendarApiService.searchEvents({
        query: query.trim() || undefined,
        authors: selectedAuthors.length > 0 ? selectedAuthors : undefined,
        categories: selectedCategories.length > 0 ? selectedCategories : undefined,
        date_from: dateFrom ? format(dateFrom, 'yyyy-MM-dd') : undefined,
        date_to: dateTo ? format(dateTo, 'yyyy-MM-dd') : undefined,
      });
      setResults(res.events || res.results || []);
    } catch (error) {
      console.error('Erro na busca:', error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setQuery('');
    setSelectedAuthors([]);
    setSelectedCategories([]);
    setDateFrom(undefined);
    setDateTo(undefined);
    setResults([]);
    setSearched(false);
  };

  const handleResultClick = (event: CalendarEvent) => {
    onOpenChange(false);
    onSelectDate(event.event_date);
  };

  const categoryFilters = [
    ...CATEGORIAS.map(c => ({ key: c.key, label: c.label, emoji: c.emoji, color: c.color })),
    { key: 'monetizacao', label: 'Monetização', emoji: '💸', color: 'green' as const },
    { key: 'desmonetizacao', label: 'Desmonetização', emoji: '❌', color: 'rose' as const },
  ];

  const colorStyles: Record<string, { active: string; inactive: string }> = {
    yellow: { active: 'border-yellow-500 bg-yellow-500/15 text-yellow-300', inactive: 'border-yellow-500/30 hover:border-yellow-500/60 text-yellow-400/70' },
    blue: { active: 'border-blue-500 bg-blue-500/15 text-blue-300', inactive: 'border-blue-500/30 hover:border-blue-500/60 text-blue-400/70' },
    emerald: { active: 'border-emerald-500 bg-emerald-500/15 text-emerald-300', inactive: 'border-emerald-500/30 hover:border-emerald-500/60 text-emerald-400/70' },
    red: { active: 'border-red-500 bg-red-500/15 text-red-300', inactive: 'border-red-500/30 hover:border-red-500/60 text-red-400/70' },
    green: { active: 'border-green-500 bg-green-500/15 text-green-300', inactive: 'border-green-500/30 hover:border-green-500/60 text-green-400/70' },
    rose: { active: 'border-rose-500 bg-rose-500/15 text-rose-300', inactive: 'border-rose-500/30 hover:border-rose-500/60 text-rose-400/70' },
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="w-[95vw] max-w-2xl max-h-[90vh] p-0">
        <DialogHeader className="px-6 pt-6 pb-2">
          <DialogTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Buscar Eventos
          </DialogTitle>
          <DialogDescription>Filtre por texto, autor, categoria ou período.</DialogDescription>
        </DialogHeader>

        <ScrollArea className="max-h-[75vh] px-6 pb-6">
          <div className="space-y-4">
            {/* Text search */}
            <div className="space-y-1.5">
              <Label className="text-sm">Buscar por texto</Label>
              <Input
                value={query}
                onChange={e => setQuery(e.target.value)}
                placeholder="Buscar em títulos e descrições..."
                onKeyDown={e => e.key === 'Enter' && handleSearch()}
              />
            </div>

            {/* Author filter */}
            <div className="space-y-1.5">
              <Label className="text-sm">Filtrar por autor</Label>
              <div className="flex flex-wrap gap-2">
                {SOCIOS.map(s => (
                  <label
                    key={s.key}
                    className={cn(
                      'flex items-center gap-1.5 px-3 py-1.5 rounded-lg border cursor-pointer transition-all text-sm',
                      selectedAuthors.includes(s.key)
                        ? 'border-primary bg-primary/10 text-primary'
                        : 'border-border hover:border-primary/50'
                    )}
                  >
                    <Checkbox
                      checked={selectedAuthors.includes(s.key)}
                      onCheckedChange={() => toggleAuthor(s.key)}
                      className="sr-only"
                    />
                    <span>{s.emoji}</span>
                    <span>{s.name}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Category filter */}
            <div className="space-y-1.5">
              <Label className="text-sm">Filtrar por categoria</Label>
              <div className="flex flex-wrap gap-2">
                {categoryFilters.map(c => {
                  const isActive = selectedCategories.includes(c.key);
                  const style = colorStyles[c.color] || colorStyles.yellow;
                  return (
                    <label
                      key={c.key}
                      className={cn(
                        'flex items-center gap-1.5 px-3 py-1.5 rounded-lg border cursor-pointer transition-all text-sm',
                        isActive ? style.active : style.inactive
                      )}
                    >
                      <Checkbox
                        checked={isActive}
                        onCheckedChange={() => toggleCategory(c.key)}
                        className="sr-only"
                      />
                      <span>{c.emoji}</span>
                      <span>{c.label}</span>
                    </label>
                  );
                })}
              </div>
            </div>

            {/* Date range */}
            <div className="flex flex-wrap gap-3">
              <div className="space-y-1.5">
                <Label className="text-sm">De</Label>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button variant="outline" className={cn('w-[130px] justify-start text-left text-xs h-8', !dateFrom && 'text-muted-foreground')}>
                      <CalendarIcon className="mr-1.5 h-3.5 w-3.5 shrink-0" />
                      {dateFrom ? format(dateFrom, 'dd/MM/yyyy') : 'Início'}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0 z-[60]" align="start" side="bottom" sideOffset={4}>
                    <Calendar mode="single" selected={dateFrom} onSelect={setDateFrom} initialFocus className={cn("p-2 pointer-events-auto text-xs [&_.rdp-cell]:h-7 [&_.rdp-cell]:w-7 [&_.rdp-day]:h-7 [&_.rdp-day]:w-7 [&_.rdp-head_cell]:w-7 [&_.rdp-caption_label]:text-xs [&_.rdp-nav_button]:h-6 [&_.rdp-nav_button]:w-6")} />
                  </PopoverContent>
                </Popover>
              </div>
              <div className="space-y-1.5">
                <Label className="text-sm">Até</Label>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button variant="outline" className={cn('w-[130px] justify-start text-left text-xs h-8', !dateTo && 'text-muted-foreground')}>
                      <CalendarIcon className="mr-1.5 h-3.5 w-3.5 shrink-0" />
                      {dateTo ? format(dateTo, 'dd/MM/yyyy') : 'Fim'}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0 z-[60]" align="start" side="bottom" sideOffset={4}>
                    <Calendar mode="single" selected={dateTo} onSelect={setDateTo} initialFocus className={cn("p-2 pointer-events-auto text-xs [&_.rdp-cell]:h-7 [&_.rdp-cell]:w-7 [&_.rdp-day]:h-7 [&_.rdp-day]:w-7 [&_.rdp-head_cell]:w-7 [&_.rdp-caption_label]:text-xs [&_.rdp-nav_button]:h-6 [&_.rdp-nav_button]:w-6")} />
                  </PopoverContent>
                </Popover>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-2">
              <Button onClick={handleSearch} disabled={loading} className="gap-1.5">
                <Search className="h-4 w-4" />
                {loading ? 'Buscando...' : 'Buscar'}
              </Button>
              <Button variant="outline" onClick={handleClear}>
                Limpar
              </Button>
            </div>

            {/* Results */}
            {searched && (
              <div className="space-y-2 pt-2 border-t border-border/50">
                <p className="text-sm text-muted-foreground">
                  {results.length === 0 ? 'Nenhum resultado encontrado.' : `${results.length} resultado${results.length > 1 ? 's' : ''}`}
                </p>
                {results.map(event => {
                  const socio = getSocioByKey(event.created_by);
                  const eventDate = new Date(event.event_date + 'T12:00:00');
                  return (
                    <button
                      key={event.id}
                      onClick={() => handleResultClick(event)}
                      className="w-full text-left p-3 rounded-lg border border-border/50 bg-card/50 hover:bg-accent/50 transition-colors"
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs text-muted-foreground">
                          {format(eventDate, 'dd/MM/yyyy')}
                        </span>
                        {socio && <span className="text-xs">{socio.emoji} {socio.name}</span>}
                        {(event.event_type === 'monetizacao' || event.event_type === 'monetization') && <Badge className="bg-green-500/20 text-green-400 border-green-500/30 text-[10px]">💸</Badge>}
                        {(event.event_type === 'desmonetizacao' || event.event_type === 'demonetization' || event.event_type === 'desmonetization') && <Badge className="bg-red-500/20 text-red-400 border-red-500/30 text-[10px]">❌</Badge>}
                      </div>
                      <p className="text-sm font-medium text-foreground">{event.title}</p>
                      {event.description && (
                        <p className="text-xs text-muted-foreground mt-0.5 line-clamp-1">{event.description}</p>
                      )}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}

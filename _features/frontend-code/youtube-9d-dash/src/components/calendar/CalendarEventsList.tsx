import { useMemo, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { Pencil, Trash2 } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { calendarApiService } from '@/services/calendarApi';
import {
  CalendarEvent,
  CalendarMonthResponse,
  MONTHS_PT,
  WEEKDAYS_PT_FULL,
  getSocioByKey,
  getCategoriaByKey,
} from '@/types/calendar';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { CalendarEventModal } from './CalendarEventModal';

interface CalendarEventsListProps {
  eventsMap: CalendarMonthResponse;
  currentYear: number;
  currentMonth: number;
}

const isMonetizacao = (t: string) => t === 'monetizacao' || t === 'monetization';
const isDesmonetizacao = (t: string) => t === 'desmonetizacao' || t === 'demonetization' || t === 'desmonetization';

function getEventCategoryEmoji(event: CalendarEvent): { emoji: string; bgClass: string } {
  if (isMonetizacao(event.event_type)) {
    return { emoji: '💸', bgClass: 'bg-green-500/20' };
  }
  if (isDesmonetizacao(event.event_type)) {
    return { emoji: '❌', bgClass: 'bg-red-500/20' };
  }
  const cat = getCategoriaByKey(event.category || 'geral');
  if (cat) {
    const bgColors: Record<string, string> = {
      yellow: 'bg-yellow-500/20',
      blue: 'bg-blue-500/20',
      emerald: 'bg-emerald-500/20',
      red: 'bg-red-500/20',
    };
    return { emoji: cat.emoji, bgClass: bgColors[cat.color] || bgColors.yellow };
  }
  return { emoji: '📋', bgClass: 'bg-muted' };
}

function formatDateLabel(dateStr: string): string {
  const d = new Date(dateStr + 'T12:00:00');
  const dayNum = d.getDate();
  const weekday = WEEKDAYS_PT_FULL[d.getDay()].slice(0, 3);
  return `${weekday}, ${dayNum}`;
}

// Get the primary category emoji for a date group header
function getDateCategoryEmojis(events: CalendarEvent[]): string {
  const emojis = new Set<string>();
  events.forEach(e => {
    const info = getEventCategoryEmoji(e);
    emojis.add(info.emoji);
  });
  return [...emojis].join('');
}

// Distribute date groups into 4 columns, max 5 items per group per column
type DateGroup = { dateStr: string; events: CalendarEvent[] };

function distributeIntoColumns(dates: DateGroup[]): DateGroup[][] {
  const DATES_PER_COL = 3;
  const columns: DateGroup[][] = [];
  for (let i = 0; i < dates.length; i += DATES_PER_COL) {
    columns.push(dates.slice(i, i + DATES_PER_COL));
  }
  return columns.length > 0 ? columns : [[]];
}

export function CalendarEventsList({ eventsMap, currentYear, currentMonth }: CalendarEventsListProps) {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [editingEvent, setEditingEvent] = useState<CalendarEvent | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  // Sort dates ascending, filter only dates with events
  const sortedDates: DateGroup[] = useMemo(() => {
    return Object.keys(eventsMap)
      .filter(date => eventsMap[date].length > 0)
      .sort((a, b) => a.localeCompare(b))
      .map(date => ({ dateStr: date, events: eventsMap[date] }));
  }, [eventsMap]);

  const columns = useMemo(() => distributeIntoColumns(sortedDates), [sortedDates]);

  const handleDelete = async (id: number) => {
    try {
      await calendarApiService.deleteEvent(id);
      await queryClient.invalidateQueries({ queryKey: ['calendar-events'] });
      toast({ title: 'Evento deletado com sucesso!' });
      setDeletingId(null);
    } catch (error) {
      toast({
        title: 'Erro ao deletar evento',
        description: error instanceof Error ? error.message : 'Tente novamente',
        variant: 'destructive',
      });
    }
  };

  if (sortedDates.length === 0) {
    return (
      <div className="flex gap-3">
        <div className="hidden sm:block min-w-[130px]" />
        <Card className="p-4 bg-card border-border/50 flex-1">
          <p className="text-sm text-muted-foreground text-center py-4">Nenhum evento neste mês.</p>
        </Card>
      </div>
    );
  }

  return (
    <>
      <div className="flex gap-3">
        {/* Spacer to align with legend sidebar */}
        <div className="hidden sm:block min-w-[130px]" />

        <Card className="p-3 sm:p-4 bg-card border-border/50 flex-1">
          <h3 className="text-sm font-semibold text-foreground mb-3">📋 Eventos do Mês</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 divide-x divide-border/30">
            {columns.slice(0, 4).map((col, colIdx) => (
              <div key={colIdx} className="space-y-3 px-4 first:pl-0 last:pr-0">
                {col.map(({ dateStr, events }) => (
                  <div key={dateStr}>
                    <div className="flex items-center gap-1.5 mb-1">
                      <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                        {formatDateLabel(dateStr)}
                      </span>
                      <span className="text-xs leading-none">{getDateCategoryEmojis(events)}</span>
                    </div>
                    <div className="space-y-0 border-l-2 border-border/40 pl-2">
                      {events.map(event => {
                        const socio = getSocioByKey(event.created_by);
                        return (
                          <div
                            key={event.id}
                            className="flex items-center gap-1.5 px-1.5 py-0.5 group"
                          >
                            {socio && <span className="text-xs shrink-0">{socio.emoji}</span>}
                            <span
                              role="button"
                              onClick={() => setEditingEvent(event)}
                              className="text-xs text-foreground truncate cursor-pointer hover:text-primary hover:underline transition-colors"
                            >
                              {event.title}
                            </span>
                            <span
                              role="button"
                              onClick={() => setDeletingId(event.id)}
                              className="p-0.5 rounded hover:bg-destructive/10 text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
                            >
                              <Trash2 className="h-2.5 w-2.5" />
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Edit modal */}
      <CalendarEventModal
        open={!!editingEvent}
        onOpenChange={open => { if (!open) setEditingEvent(null); }}
        event={editingEvent}
        currentYear={currentYear}
        currentMonth={currentMonth}
      />

      {/* Delete confirmation */}
      <AlertDialog open={deletingId !== null} onOpenChange={() => setDeletingId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Deletar evento?</AlertDialogTitle>
            <AlertDialogDescription>
              Esta ação não pode ser desfeita. O evento será removido permanentemente.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              onClick={() => deletingId && handleDelete(deletingId)}
            >
              Deletar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

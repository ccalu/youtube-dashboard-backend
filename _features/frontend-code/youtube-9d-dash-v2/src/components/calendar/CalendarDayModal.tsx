import { useState, useMemo } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { Plus, Pencil, Trash2 } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { calendarApiService } from '@/services/calendarApi';
import {
  CalendarEvent,
  WEEKDAYS_PT_FULL,
  MONTHS_PT,
  getSocioByKey,
  getCategoriaByKey,
  EVENT_TYPES,
} from '@/types/calendar';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
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
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';

interface CalendarDayModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  date: string; // "YYYY-MM-DD"
  events: CalendarEvent[];
  onAddEvent: () => void;
  onEditEvent: (event: CalendarEvent) => void;
}

export function CalendarDayModal({
  open,
  onOpenChange,
  date,
  events,
  onAddEvent,
  onEditEvent,
}: CalendarDayModalProps) {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [deletingId, setDeletingId] = useState<number | null>(null);

  // Format date in Portuguese
  const d = new Date(date + 'T12:00:00');
  const dayOfWeek = WEEKDAYS_PT_FULL[d.getDay()];
  const dayNum = d.getDate();
  const monthName = MONTHS_PT[d.getMonth()];
  const year = d.getFullYear();
  const formattedDate = `${dayOfWeek}, ${dayNum} de ${monthName} de ${year}`;

  const isMonetizacao = (t: string) => t === 'monetizacao' || t === 'monetization';
  const isDesmonetizacao = (t: string) => t === 'desmonetizacao' || t === 'demonetization' || t === 'desmonetization';

  // Sort events by category order: urgente > monetizacao > desmonetizacao > desenvolvimento > financeiro > geral
  const sortedEvents = useMemo(() => {
    const getOrder = (e: CalendarEvent) => {
      if (isMonetizacao(e.event_type)) return 1;
      if (isDesmonetizacao(e.event_type)) return 2;
      const cat = e.category || 'geral';
      const catOrder: Record<string, number> = { urgente: 0, desenvolvimento: 3, financeiro: 4, geral: 5 };
      return catOrder[cat] ?? 99;
    };
    return [...events].sort((a, b) => getOrder(a) - getOrder(b));
  }, [events]);

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

  const getEventTypeBadge = (event: CalendarEvent) => {
    if (isMonetizacao(event.event_type)) {
      return <Badge className="bg-green-500/20 text-green-400 border-green-500/30 text-xs">💸 Monetização</Badge>;
    }
    if (isDesmonetizacao(event.event_type)) {
      return <Badge className="bg-red-500/20 text-red-400 border-red-500/30 text-xs">❌ Desmonetização</Badge>;
    }
    const cat = getCategoriaByKey(event.category || 'geral');
    if (cat) {
      const catColors: Record<string, string> = {
        yellow: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
        blue: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
        emerald: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
        red: 'bg-red-500/20 text-red-400 border-red-500/30',
      };
      const colorClass = catColors[cat.color] || catColors.yellow;
      return <Badge className={`${colorClass} text-xs`}>{cat.emoji} {cat.label}</Badge>;
    }
    return null;
  };

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="w-[95vw] max-w-2xl max-h-[90vh] p-0">
          <DialogHeader className="px-6 pt-6 pb-2">
            <DialogTitle className="text-lg">{formattedDate}</DialogTitle>
            <DialogDescription>
              {events.length === 0
                ? 'Nenhum evento neste dia.'
                : `${events.length} evento${events.length > 1 ? 's' : ''} registrado${events.length > 1 ? 's' : ''}.`
              }
            </DialogDescription>
          </DialogHeader>

          <div className="px-6 pb-2">
            <Button size="sm" onClick={onAddEvent} className="gap-1.5">
              <Plus className="h-4 w-4" />
              Adicionar Evento
            </Button>
          </div>

          <ScrollArea className="max-h-[60vh] px-6 pb-6">
            <div className="space-y-3">
              {sortedEvents.map(event => {
                const socio = getSocioByKey(event.created_by);
                return (
                  <div
                    key={event.id}
                    className="p-3 sm:p-4 rounded-lg border border-border/50 bg-card/50 space-y-2"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap mb-1">
                          {socio && (
                            <span className="text-sm font-medium">
                              {socio.emoji} {socio.name}
                            </span>
                          )}
                          {getEventTypeBadge(event)}
                        </div>
                        <h4 className="font-semibold text-foreground text-sm sm:text-base">{event.title}</h4>
                        {event.description && (
                          <p className="text-sm text-muted-foreground mt-1 whitespace-pre-wrap">{event.description}</p>
                        )}
                      </div>

                      <div className="flex items-center gap-1 shrink-0">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={() => onEditEvent(event)}
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-destructive hover:text-destructive"
                          onClick={() => setDeletingId(event.id)}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </ScrollArea>
        </DialogContent>
      </Dialog>

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

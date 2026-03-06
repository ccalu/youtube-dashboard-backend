import { useState, useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { format } from 'date-fns';
import { CalendarIcon } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useToast } from '@/hooks/use-toast';
import { calendarApiService } from '@/services/calendarApi';
import {
  CalendarEvent,
  SOCIOS,
  CATEGORIAS,
  EVENT_TYPES,
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
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { Calendar } from '@/components/ui/calendar';

interface CalendarEventModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  event?: CalendarEvent | null;
  defaultDate?: string; // "YYYY-MM-DD"
  currentYear: number;
  currentMonth: number;
}

export function CalendarEventModal({
  open,
  onOpenChange,
  event,
  defaultDate,
  currentYear,
  currentMonth,
}: CalendarEventModalProps) {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const isEditing = !!event;

  const [createdBy, setCreatedBy] = useState('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [eventDate, setEventDate] = useState<Date | undefined>();
  const [eventType, setEventType] = useState('normal');
  const [category, setCategory] = useState('geral');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (open) {
      if (event) {
        setCreatedBy(event.created_by);
        setTitle(event.title);
        setDescription(event.description || '');
        setEventDate(new Date(event.event_date + 'T12:00:00'));
        setEventType(event.event_type || 'normal');
        setCategory(event.category || 'geral');
      } else {
        setCreatedBy('');
        setTitle('');
        setDescription('');
        setEventDate(defaultDate ? new Date(defaultDate + 'T12:00:00') : new Date());
        setEventType('normal');
        setCategory('geral');
      }
    }
  }, [open, event, defaultDate]);

  const handleSave = async () => {
    if (!createdBy) {
      toast({ title: 'Selecione um sócio', variant: 'destructive' });
      return;
    }
    if (!title.trim()) {
      toast({ title: 'Título é obrigatório', variant: 'destructive' });
      return;
    }
    if (!eventDate) {
      toast({ title: 'Data é obrigatória', variant: 'destructive' });
      return;
    }

    setSaving(true);
    try {
      const dateStr = format(eventDate, 'yyyy-MM-dd');
      const payload = {
        title: title.trim(),
        description: description.trim() || undefined,
        event_date: dateStr,
        created_by: createdBy,
        event_type: eventType,
        category: eventType === 'normal' ? category : undefined,
      };

      if (isEditing && event) {
        await calendarApiService.updateEvent(event.id, payload);
        toast({ title: 'Evento atualizado com sucesso!' });
      } else {
        await calendarApiService.createEvent(payload);
        toast({ title: 'Evento criado com sucesso!' });
      }

      await queryClient.invalidateQueries({ queryKey: ['calendar-events'] });
      onOpenChange(false);
    } catch (error) {
      console.error('Erro ao salvar evento:', error);
      toast({
        title: 'Erro ao salvar evento',
        description: error instanceof Error ? error.message : 'Tente novamente',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="w-[95vw] max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{isEditing ? 'Editar Evento' : 'Novo Evento'}</DialogTitle>
          <DialogDescription>
            {isEditing ? 'Atualize as informações do evento.' : 'Preencha os dados do novo evento.'}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 mt-2">
          {/* Sócio */}
          <div className="space-y-2">
            <Label className="text-sm font-medium">Sócio *</Label>
            <RadioGroup value={createdBy} onValueChange={setCreatedBy} className="flex flex-wrap gap-2">
              {SOCIOS.map(s => (
                <label
                  key={s.key}
                  className={cn(
                    'flex items-center gap-1.5 px-3 py-2 rounded-lg border cursor-pointer transition-all text-sm',
                    createdBy === s.key
                      ? 'border-primary bg-primary/10 text-primary font-medium'
                      : 'border-border hover:border-primary/50'
                  )}
                >
                  <RadioGroupItem value={s.key} className="sr-only" />
                  <span>{s.emoji}</span>
                  <span>{s.name}</span>
                </label>
              ))}
            </RadioGroup>
          </div>

          {/* Date */}
          <div className="space-y-2">
            <Label className="text-sm font-medium">Data *</Label>
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  className={cn(
                    'w-full justify-start text-left font-normal',
                    !eventDate && 'text-muted-foreground'
                  )}
                >
                  <CalendarIcon className="mr-2 h-4 w-4" />
                  {eventDate ? format(eventDate, 'dd/MM/yyyy') : 'Selecionar data'}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-auto p-0" align="start">
                <Calendar
                  mode="single"
                  selected={eventDate}
                  onSelect={setEventDate}
                  initialFocus
                  className={cn("p-3 pointer-events-auto")}
                />
              </PopoverContent>
            </Popover>
          </div>

          {/* Title */}
          <div className="space-y-2">
            <Label className="text-sm font-medium">Título *</Label>
            <Input
              value={title}
              onChange={e => setTitle(e.target.value)}
              placeholder="Ex: Reunião de planejamento"
              maxLength={200}
            />
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label className="text-sm font-medium">Descrição</Label>
            <Textarea
              value={description}
              onChange={e => setDescription(e.target.value)}
              placeholder="Detalhes do evento (opcional)"
              rows={3}
            />
          </div>

          {/* Event Type */}
          <div className="space-y-2">
            <Label className="text-sm font-medium">Tipo</Label>
            <RadioGroup value={eventType} onValueChange={setEventType} className="flex flex-wrap gap-2">
              {EVENT_TYPES.map(t => (
                <label
                  key={t.key}
                  className={cn(
                    'flex items-center gap-1.5 px-3 py-2 rounded-lg border cursor-pointer transition-all text-sm',
                    eventType === t.key
                      ? 'border-primary bg-primary/10 text-primary font-medium'
                      : 'border-border hover:border-primary/50'
                  )}
                >
                  <RadioGroupItem value={t.key} className="sr-only" />
                  {'emoji' in t && t.emoji && <span>{t.emoji}</span>}
                  <span>{t.label}</span>
                </label>
              ))}
            </RadioGroup>
          </div>

          {/* Category (only for normal type) */}
          {eventType === 'normal' && (
            <div className="space-y-2">
              <Label className="text-sm font-medium">Categoria</Label>
              <RadioGroup value={category} onValueChange={setCategory} className="flex flex-wrap gap-2">
                {CATEGORIAS.map(c => {
                  const isActive = category === c.key;
                  const colors: Record<string, { active: string; inactive: string }> = {
                    yellow: { active: 'border-yellow-500 bg-yellow-500/15 text-yellow-300 font-medium', inactive: 'border-yellow-500/30 hover:border-yellow-500/60 text-yellow-400/70' },
                    blue: { active: 'border-blue-500 bg-blue-500/15 text-blue-300 font-medium', inactive: 'border-blue-500/30 hover:border-blue-500/60 text-blue-400/70' },
                    emerald: { active: 'border-emerald-500 bg-emerald-500/15 text-emerald-300 font-medium', inactive: 'border-emerald-500/30 hover:border-emerald-500/60 text-emerald-400/70' },
                    red: { active: 'border-red-500 bg-red-500/15 text-red-300 font-medium', inactive: 'border-red-500/30 hover:border-red-500/60 text-red-400/70' },
                  };
                  const style = colors[c.color] || colors.yellow;
                  return (
                    <label
                      key={c.key}
                      className={cn(
                        'flex items-center gap-1.5 px-3 py-2 rounded-lg border cursor-pointer transition-all text-sm',
                        isActive ? style.active : style.inactive
                      )}
                    >
                      <RadioGroupItem value={c.key} className="sr-only" />
                      <span>{c.emoji}</span>
                      <span>{c.label}</span>
                    </label>
                  );
                })}
              </RadioGroup>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => onOpenChange(false)} disabled={saving}>
              Cancelar
            </Button>
            <Button onClick={handleSave} disabled={saving}>
              {saving ? 'Salvando...' : isEditing ? 'Atualizar' : 'Criar Evento'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

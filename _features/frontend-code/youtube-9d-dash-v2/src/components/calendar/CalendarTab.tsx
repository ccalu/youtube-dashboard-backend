import { useState, useMemo, useCallback } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { ChevronLeft, ChevronRight, Plus, Search } from 'lucide-react';
import { calendarApiService } from '@/services/calendarApi';
import { CalendarEvent, MONTHS_PT, WEEKDAYS_PT, SOCIOS, CATEGORIAS, EVENT_TYPES } from '@/types/calendar';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useIsMobile } from '@/hooks/use-mobile';
import { CalendarDayCell } from './CalendarDayCell';
import { CalendarDayModal } from './CalendarDayModal';
import { CalendarEventModal } from './CalendarEventModal';
import { CalendarSearchModal } from './CalendarSearchModal';
import { CalendarEventsList } from './CalendarEventsList';

export function CalendarTab() {
  const isMobile = useIsMobile();
  const queryClient = useQueryClient();
  const now = new Date();

  const [currentYear, setCurrentYear] = useState(now.getFullYear());
  const [currentMonth, setCurrentMonth] = useState(now.getMonth() + 1); // 1-indexed

  // Modals
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [eventModalOpen, setEventModalOpen] = useState(false);
  const [editingEvent, setEditingEvent] = useState<CalendarEvent | null>(null);
  const [searchOpen, setSearchOpen] = useState(false);

  // Fetch month events
  const { data: monthData, isLoading } = useQuery({
    queryKey: ['calendar-events', currentYear, currentMonth],
    queryFn: () => calendarApiService.getMonth(currentYear, currentMonth),
    staleTime: 1000 * 60 * 5,
    refetchOnMount: 'always',
  });

  const eventsMap = monthData || {};

  // Build calendar grid
  const calendarDays = useMemo(() => {
    const firstDay = new Date(currentYear, currentMonth - 1, 1);
    const lastDay = new Date(currentYear, currentMonth, 0);
    const startDow = firstDay.getDay(); // 0=Sun
    const daysInMonth = lastDay.getDate();

    // Previous month fill
    const prevMonthLastDay = new Date(currentYear, currentMonth - 1, 0).getDate();
    const days: { day: number; month: number; year: number; isCurrentMonth: boolean }[] = [];

    for (let i = startDow - 1; i >= 0; i--) {
      const d = prevMonthLastDay - i;
      const m = currentMonth - 1 <= 0 ? 12 : currentMonth - 1;
      const y = currentMonth - 1 <= 0 ? currentYear - 1 : currentYear;
      days.push({ day: d, month: m, year: y, isCurrentMonth: false });
    }

    // Current month
    for (let d = 1; d <= daysInMonth; d++) {
      days.push({ day: d, month: currentMonth, year: currentYear, isCurrentMonth: true });
    }

    // Next month fill (to complete 6 rows)
    const remaining = 42 - days.length;
    for (let d = 1; d <= remaining; d++) {
      const m = currentMonth + 1 > 12 ? 1 : currentMonth + 1;
      const y = currentMonth + 1 > 12 ? currentYear + 1 : currentYear;
      days.push({ day: d, month: m, year: y, isCurrentMonth: false });
    }

    return days;
  }, [currentYear, currentMonth]);

  const todayStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;

  const getDateStr = (d: { day: number; month: number; year: number }) =>
    `${d.year}-${String(d.month).padStart(2, '0')}-${String(d.day).padStart(2, '0')}`;

  const getEventsForDate = (dateStr: string): CalendarEvent[] => eventsMap[dateStr] || [];

  // Navigation
  const goToPrevMonth = () => {
    if (currentMonth === 1) {
      setCurrentMonth(12);
      setCurrentYear(y => y - 1);
    } else {
      setCurrentMonth(m => m - 1);
    }
  };

  const goToNextMonth = () => {
    if (currentMonth === 12) {
      setCurrentMonth(1);
      setCurrentYear(y => y + 1);
    } else {
      setCurrentMonth(m => m + 1);
    }
  };

  const goToToday = () => {
    setCurrentYear(now.getFullYear());
    setCurrentMonth(now.getMonth() + 1);
  };

  // Day click
  const handleDayClick = useCallback((dateStr: string) => {
    setSelectedDate(dateStr);
  }, []);

  // Open create event modal
  const handleAddEvent = useCallback((date?: string) => {
    setEditingEvent(null);
    setEventModalOpen(true);
    if (date) setSelectedDate(date);
  }, []);

  // Open edit event modal
  const handleEditEvent = useCallback((event: CalendarEvent) => {
    setEditingEvent(event);
    setSelectedDate(null); // close day modal
    setEventModalOpen(true);
  }, []);

  // Search result navigates to that date's month
  const handleSearchSelectDate = useCallback((dateStr: string) => {
    const [y, m] = dateStr.split('-').map(Number);
    setCurrentYear(y);
    setCurrentMonth(m);
    // Open day modal after a tick to let query update
    setTimeout(() => setSelectedDate(dateStr), 200);
  }, []);

  const selectedEvents = selectedDate ? getEventsForDate(selectedDate) : [];

  // Year options
  const yearOptions = Array.from({ length: 7 }, (_, i) => now.getFullYear() - 2 + i);

  return (
    <div className="space-y-4">
      {/* Header */}
      <Card className="p-3 sm:p-4 bg-card border-border/50">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <h2 className="text-lg sm:text-xl font-bold text-foreground">📅 Calendário</h2>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {/* Month/Year nav */}
            <div className="flex items-center gap-1">
              <Button variant="ghost" size="icon" className="h-8 w-8" onClick={goToPrevMonth}>
                <ChevronLeft className="h-4 w-4" />
              </Button>

              <Select value={String(currentMonth)} onValueChange={v => setCurrentMonth(Number(v))}>
                <SelectTrigger className="w-[120px] h-8 text-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {MONTHS_PT.map((m, i) => (
                    <SelectItem key={i} value={String(i + 1)}>{m}</SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={String(currentYear)} onValueChange={v => setCurrentYear(Number(v))}>
                <SelectTrigger className="w-[80px] h-8 text-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {yearOptions.map(y => (
                    <SelectItem key={y} value={String(y)}>{y}</SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Button variant="ghost" size="icon" className="h-8 w-8" onClick={goToNextMonth}>
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>

            <Button variant="outline" size="sm" onClick={goToToday} className="h-8 text-xs">
              Hoje
            </Button>

            <Button size="sm" onClick={() => handleAddEvent()} className="h-8 gap-1">
              <Plus className="h-3.5 w-3.5" />
              {!isMobile && 'Novo Evento'}
            </Button>

            <Button variant="outline" size="sm" onClick={() => setSearchOpen(true)} className="h-8 gap-1">
              <Search className="h-3.5 w-3.5" />
              {!isMobile && 'Buscar'}
            </Button>
          </div>
        </div>
      </Card>

      {/* Calendar Grid + Legend */}
      <div className="flex gap-3">
        {/* Legend sidebar */}
        <Card className="hidden sm:flex flex-col gap-4 p-3 bg-card border-border/50 min-w-[130px] self-start">
          <div className="space-y-1.5">
            <span className="font-semibold text-[11px] uppercase tracking-wider text-foreground/60">Categorias</span>
            {CATEGORIAS.map(cat => (
              <div key={cat.key} className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
                <div className={`h-2 w-2 rounded-full shrink-0 ${
                  cat.color === 'yellow' ? 'bg-yellow-500' :
                  cat.color === 'blue' ? 'bg-blue-500' :
                  cat.color === 'emerald' ? 'bg-emerald-500' : 'bg-red-500'
                }`} />
                {cat.label}
              </div>
            ))}
            <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
              💸 Monetização
            </div>
            <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
              ❌ Desmonetização
            </div>
          </div>
          <div className="border-t border-border/30 pt-3 space-y-1.5">
            <span className="font-semibold text-[11px] uppercase tracking-wider text-foreground/60">Sócios</span>
            {SOCIOS.map(s => (
              <div key={s.key} className="text-[11px] text-muted-foreground">{s.emoji} {s.name}</div>
            ))}
          </div>
        </Card>

        {/* Calendar */}
        <Card className="p-2 sm:p-4 bg-card border-border/50 flex-1">
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
            </div>
          ) : (
            <>
              <div className="grid grid-cols-7 gap-0.5 sm:gap-1 mb-1">
                {WEEKDAYS_PT.map(wd => (
                  <div key={wd} className="text-center text-xs sm:text-sm font-semibold text-muted-foreground py-2 bg-muted/50 rounded-md border border-border">
                    {isMobile ? wd.charAt(0) : wd}
                  </div>
                ))}
              </div>
              <div className="grid grid-cols-7 gap-0.5 sm:gap-1">
                {calendarDays.map((d, i) => {
                  const dateStr = getDateStr(d);
                  const events = getEventsForDate(dateStr);
                  const isToday = dateStr === todayStr;
                  return (
                    <CalendarDayCell
                      key={i}
                      day={d.day}
                      dateStr={dateStr}
                      isCurrentMonth={d.isCurrentMonth}
                      isToday={isToday}
                      events={events}
                      onClick={() => handleDayClick(dateStr)}
                    />
                  );
                })}
              </div>
            </>
          )}
        </Card>
      </div>

      {/* Day Modal */}
      {selectedDate && (
        <CalendarDayModal
          open={!!selectedDate}
          onOpenChange={open => { if (!open) setSelectedDate(null); }}
          date={selectedDate}
          events={selectedEvents}
          onAddEvent={() => {
            setSelectedDate(null);
            handleAddEvent(selectedDate);
          }}
          onEditEvent={handleEditEvent}
        />
      )}

      {/* Create/Edit Event Modal */}
      <CalendarEventModal
        open={eventModalOpen}
        onOpenChange={setEventModalOpen}
        event={editingEvent}
        defaultDate={selectedDate || undefined}
        currentYear={currentYear}
        currentMonth={currentMonth}
      />

      {/* Search Modal */}
      <CalendarSearchModal
        open={searchOpen}
        onOpenChange={setSearchOpen}
        onSelectDate={handleSearchSelectDate}
      />

      {/* Events List */}
      {!isLoading && (
        <CalendarEventsList
          eventsMap={eventsMap}
          currentYear={currentYear}
          currentMonth={currentMonth}
        />
      )}
    </div>
  );
}

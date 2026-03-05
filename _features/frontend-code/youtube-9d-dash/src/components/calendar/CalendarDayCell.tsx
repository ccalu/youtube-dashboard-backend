import { CalendarEvent, getSocioByKey, getCategoriaByKey } from '@/types/calendar';

interface CalendarDayCellProps {
  day: number;
  dateStr: string;
  isCurrentMonth: boolean;
  isToday: boolean;
  events: CalendarEvent[];
  onClick: () => void;
}

const dotColorMap: Record<string, string> = {
  yellow: 'bg-yellow-500',
  blue: 'bg-blue-500',
  emerald: 'bg-emerald-500',
  red: 'bg-red-500',
  green: 'bg-green-500',
  rose: 'bg-rose-500',
};

function isMonetizacao(type: string) {
  return type === 'monetizacao' || type === 'monetization';
}
function isDesmonetizacao(type: string) {
  return type === 'desmonetizacao' || type === 'demonetization' || type === 'desmonetization';
}

function getEventColorKey(event: CalendarEvent): string {
  if (isMonetizacao(event.event_type) || isDesmonetizacao(event.event_type)) return '';
  const cat = getCategoriaByKey(event.category || 'geral');
  return cat?.color || 'yellow';
}

const colorOrder = ['red', 'green', 'rose', 'blue', 'emerald', 'yellow'];

export function CalendarDayCell({ day, isCurrentMonth, isToday, events, onClick }: CalendarDayCellProps) {
  const uniqueAuthors = [...new Set(events.map(e => e.created_by))];
  const authorEmojis = uniqueAuthors
    .slice(0, 4)
    .map(key => getSocioByKey(key)?.emoji || '👤');

  const hasMonetizacao = events.some(e => isMonetizacao(e.event_type));
  const hasDesmonetizacao = events.some(e => isDesmonetizacao(e.event_type));

  // Group dots by color and sort by priority (exclude monetização/desmonetização)
  const sortedDots = events.length > 0
    ? [...events]
        .map(e => getEventColorKey(e))
        .filter(c => c !== '')
        .sort((a, b) => colorOrder.indexOf(a) - colorOrder.indexOf(b))
    : [];

  return (
    <button
      onClick={onClick}
      className={`
        relative flex flex-col items-start p-1 sm:p-2 min-h-[52px] sm:min-h-[80px] border border-border transition-all duration-150
        hover:bg-accent/50 hover:border-primary/30 cursor-pointer rounded-md
        ${isCurrentMonth ? 'bg-card' : 'bg-muted/20 opacity-60'}
        ${isToday ? 'ring-2 ring-inset ring-primary bg-primary/5' : ''}
      `}
    >
      <span className={`text-xs sm:text-sm font-medium leading-none ${
        isToday ? 'text-primary font-bold' : isCurrentMonth ? 'text-foreground' : 'text-muted-foreground'
      }`}>
        {day}
      </span>

      {events.length > 0 && (
        <div className="flex flex-col items-center justify-center gap-0.5 mt-auto w-full flex-1">
          <div className="flex items-center justify-center gap-1 flex-wrap">
            {authorEmojis.map((emoji, i) => (
              <span key={i} className="text-lg sm:text-xl leading-none">{emoji}</span>
            ))}
            {hasMonetizacao && <span className="text-lg sm:text-xl leading-none">💸</span>}
            {hasDesmonetizacao && <span className="text-lg sm:text-xl leading-none">❌</span>}
          </div>

          {sortedDots.length > 0 && (
            <div className="flex items-center justify-center gap-0.5">
              {sortedDots.slice(0, 6).map((color, i) => (
                <div key={i} className={`h-1.5 w-1.5 sm:h-2 sm:w-2 rounded-full ${dotColorMap[color] || dotColorMap.yellow}`} />
              ))}
              {sortedDots.length > 6 && (
                <span className="text-[9px] sm:text-xs text-muted-foreground font-medium">+{sortedDots.length - 6}</span>
              )}
            </div>
          )}
        </div>
      )}
    </button>
  );
}
